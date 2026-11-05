// TIMESTAMP START 2026-11-04T23:23:25+00:00 | REVISION R000011
// TIMESTAMP START 2026-11-04T20:33:26+00:00 | REVISION R000023
// TIMESTAMP START 2026-11-04T19:41:08+00:00 | REVISION R000003
'use strict';
// Run against a preview serving dist/ with its _headers cache policy applied.
// Supply PLAYWRIGHT_MODULE, CHROMIUM_PATH, PREVIEW_URL and QA_OUTPUT as needed.
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const fs=require('node:fs'),assert=require('node:assert/strict');
const origin=process.env.PREVIEW_URL||'http://127.0.0.1:8766/';
const output=process.env.QA_OUTPUT;
const result={errors:[],switches:[]};
const resources=()=>performance.getEntriesByType('resource').filter(r=>r.name.includes('/assets/')).map(r=>({name:r.name,transfer:r.transferSize}));
(async()=>{
 const browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',headless:true,
  args:['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 try{
  const page=await browser.newPage({viewport:{width:1440,height:1000}}),requests=[];
  page.on('pageerror',e=>result.errors.push(e.message));
  page.on('console',m=>{if(m.type()==='error')result.errors.push(m.text());});
  page.on('request',r=>requests.push(r.url()));
  await page.goto(origin);
  await page.waitForFunction(()=>window.octagonViewer,null,{timeout:60000});
  result.coldMs=await page.evaluate(()=>performance.now());
  assert.equal(await page.evaluate(()=>octagonViewer.context.id),'top-entry');
  assert(!requests.some(url=>/model-baseline|model-proposed|earlier-joint-study|manifold|parametric-source/.test(url)));
  assert.equal(requests.length,new Set(requests).size,'Startup requests each asset once');
  await page.locator('[data-focus-key="select:P0"]').click();
  assert((await page.locator('#selection').innerText()).includes('P0'));
  // TIMESTAMP START 2026-11-05T01:24:05+00:00 | REVISION R000013
  const sheets=await page.evaluate(()=>octagonViewer.schematicParts.filter(p=>p.floorRole==='underlayment_sheet').map(p=>p.id));
  assert.equal(sheets.length,28);
  await page.locator('[data-focus-key="select:'+sheets[0]+'"]').click();
  assert((await page.locator('#selection').innerText()).includes(sheets[0]));
  assert.equal(await page.locator('a[href="review/underlayment-sheets.svg"]').count(),1);
  // TIMESTAMP END 2026-11-05T01:24:05+00:00 | REVISION R000013
  for(const mode of ['sphere','assembly','disassembly']){
   await page.selectOption('#motionMode',mode);
   await page.evaluate(()=>{const slider=document.getElementById('explode');slider.value='35';slider.dispatchEvent(new Event('input',{bubbles:true}));});
  }
  await page.evaluate(()=>octagonViewer.setMotion('disassembly',0));
  await page.click('#plansButton');
  await page.waitForSelector('#plansTop svg',{timeout:60000});
  await page.waitForSelector('#plansSide svg',{timeout:60000});
  await page.click('#closePlans');
  await page.evaluate(async()=>{const button=document.getElementById('openStepLap');await Promise.all([button.onclick(),button.onclick()]);});
  await page.click('#closeStepLap');await page.click('#openStepLap');await page.click('#closeStepLap');
  result.studyRequests=requests.filter(x=>x.includes('earlier-joint-study')).length;
  assert.equal(result.studyRequests,1,'Repeated and concurrent study opens load it once');
  for(const id of ['baseline','proposed','top-entry']){
   await page.selectOption('#modelVariant',id);
   await page.waitForURL(url=>url.searchParams.get('model')===id);
   await page.waitForFunction(id=>window.octagonViewer?.context.id===id,id,{timeout:60000});
   const entry={id,readyMs:await page.evaluate(()=>performance.now()),resources:await page.evaluate(resources)};
   result.switches.push(entry);
   assert(entry.resources.filter(r=>/viewer\.|shared-data/.test(r.name)).every(r=>r.transfer===0),'Model switching reuses shared cached assets');
  }
  await page.reload();await page.waitForFunction(()=>window.octagonViewer,null,{timeout:60000});
  result.warm={readyMs:await page.evaluate(()=>performance.now()),resources:await page.evaluate(resources)};
  assert(result.warm.resources.every(r=>r.transfer===0),'Reload reuses all startup assets');
  console.log('Selection, motion, plans, model switching, deferred study and cache reuse: passed');
  await page.fill('#wallHeight','96');await page.fill('#roofPitch','5');await page.click('#applyDimensions');
  await page.waitForURL(url=>url.searchParams.get('pitch')==='5');
  await page.waitForFunction(()=>window.octagonViewer?.context.parametric,null,{timeout:120000});
  result.parametric=await page.evaluate(()=>({id:octagonViewer.context.id,parameters:octagonViewer.context.parameters,readyMs:performance.now()}));
  assert.equal(result.parametric.parameters.pitch,5);assert.equal(result.parametric.parameters.wallHeightIn,96);
  console.log('Changed dimensions with optional geometry engine: passed');
  const mobile=await browser.newPage({viewport:{width:390,height:844},isMobile:true,hasTouch:true});
  mobile.on('pageerror',e=>result.errors.push(e.message));
  mobile.on('console',m=>{if(m.type()==='error')result.errors.push(m.text());});
  await mobile.goto(origin);await mobile.waitForFunction(()=>window.octagonViewer,null,{timeout:60000});
  result.mobile=await mobile.evaluate(()=>({width:innerWidth,scrollWidth:document.documentElement.scrollWidth,
   canvasWidth:document.getElementById('scene').getBoundingClientRect().width,compass:document.querySelector('.axis-key').textContent,readyMs:performance.now()}));
  assert(result.mobile.scrollWidth<=result.mobile.width);assert(result.mobile.canvasWidth>300);
  await mobile.locator('#scene').scrollIntoViewIfNeeded();
  if(output)await mobile.screenshot({path:output.replace(/\.json$/,'.mobile.png')});
  assert.deepEqual(result.errors,[]);result.pass=true;
 }finally{
  if(output)fs.writeFileSync(output,JSON.stringify(result,null,2));
  await browser.close();
 }
 console.log(JSON.stringify(result));
})().catch(error=>{console.error(error);process.exitCode=1;});
// TIMESTAMP END 2026-11-04T19:41:08+00:00 | REVISION R000003
// TIMESTAMP END 2026-11-04T20:33:26+00:00 | REVISION R000023

// TIMESTAMP END 2026-11-04T23:23:25+00:00 | REVISION R000011
