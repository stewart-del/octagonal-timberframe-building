// TIMESTAMP START 2026-11-05T02:50:53+00:00 | REVISION R000017
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const result={errors:[],cases:[]};
(async()=>{
 const browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',headless:true,args:['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 try{
  for(const mobile of [false,true]){
   const page=await browser.newPage({viewport:mobile?{width:390,height:844}:{width:1440,height:1000},isMobile:mobile,hasTouch:mobile});
   page.on('pageerror',e=>result.errors.push(e.message));
   await page.goto(process.env.PREVIEW_URL||'http://127.0.0.1:8766/');
   await page.waitForFunction(()=>window.octagonViewer,null,{timeout:60000});
   for(const mode of ['disassembly','assembly','sphere']){
    await page.evaluate(mode=>octagonViewer.setMotion(mode,0),mode);
    const count=await page.evaluate(mode=>mode==='assembly'?octagonViewer.motion.assemblyCount:mode==='sphere'?20:octagonViewer.motion.count,mode);
    const steps=Math.min(32,count-1);
    for(let k=1;k<=steps;k++){
     await page.locator('#disassemblyNext').click();
     const actual=Number(await page.locator('#explode').inputValue());
     assert(Math.abs(actual-k*100/count)<=.005000001,`${mobile?'Mobile':'Desktop'} ${mode}: click ${k} must reach the next boundary; got ${actual}`);
    }
    for(let k=steps-1;k>=0;k--){
     await page.locator('#disassemblyPrevious').click();
     const actual=Number(await page.locator('#explode').inputValue());
     assert(Math.abs(actual-k*100/count)<=.005000001,`${mode}: previous must reverse every step`);
    }
    assert(await page.locator('#disassemblyPrevious').isDisabled());
    await page.evaluate(mode=>octagonViewer.setMotion(mode,1),mode);
    assert(await page.locator('#disassemblyNext').isDisabled());
    result.cases.push({mobile,mode,forward:steps,backward:steps,count});
   }
   await page.close();
  }
  assert.deepEqual(result.errors,[]);result.pass=true;
 }finally{
  if(process.env.QA_OUTPUT)fs.writeFileSync(process.env.QA_OUTPUT,JSON.stringify(result,null,2));
  await browser.close();
 }
 console.log(JSON.stringify(result));
})().catch(error=>{console.error(error);process.exitCode=1;});
// TIMESTAMP END 2026-11-05T02:50:53+00:00 | REVISION R000017
