'use strict';
const fs=require('fs'),path=require('path'),assert=require('assert'),crypto=require('crypto');
require('../src/step-lap-review.js');
const api=global.OctagonStepLap,data=JSON.parse(fs.readFileSync(path.join(__dirname,'../src/step-lap-proposal.json'))),canonical=fs.readFileSync(path.join(__dirname,'../src/model-data.json'));
const before=JSON.stringify(data),modelBefore=canonical.toString(),sha=crypto.createHash('sha256').update(canonical).digest('hex');
assert.equal(data.baseline_model_sha256,sha);assert.equal(data.canonical_model_unchanged,true);assert(data.variants.length>=2);assert.equal(new Set(data.variants.map(v=>v.id)).size,data.variants.length);
for(const v of data.variants){
 assert(v.baseline_parts.length===2&&v.proposed_parts.length===2);assert(v.member_ids.length===2);
 for(const view of ['iso','top','section'])for(const explode of [false,true]){
  const current=api.drawing(v,{proposed:false,view,explode}),proposed=api.drawing(v,{proposed:true,view,explode,removed:true,normals:true});
  for(const d of [current,proposed]){assert(!/NaN|Infinity|undefined/.test(d.svg));assert(d.svg.includes('NOT FABRICATION APPROVED'));assert(d.partCount===2);if(view==='section')assert(d.sectionCount>0,'Actual section must intersect both member meshes');else assert(d.polygonCount>0);}
  assert.notEqual(current.svg,proposed.svg);if(!explode)fs.writeFileSync(`/tmp/step-lap-${v.id}-${view}.svg`,proposed.svg);
 }
 assert(!api.drawing(v,{standalone:false}).svg.includes('NOT FABRICATION APPROVED'),'On-screen figures should not repeat the overall review notice');
 const contact=api.drawing(v,{normals:true});assert.equal(contact.normalCount,(v.contact_faces||[]).filter(f=>f.centroid_m&&f.normal_on_rafter).length);
}
const postVariant=data.variants.find(v=>/^P\d+$/.test(v.member_ids[1]));
assert(postVariant,'At least one post-seat variant must be reviewed');
const repeatedPost=JSON.parse(JSON.stringify(postVariant));repeatedPost.member_ids[1]='P7';for(const sec of repeatedPost.measurements.remaining_local_sections||[])if(/^P\d+$/.test(sec.member_id))sec.member_id='P7';
assert(api.tradeoff(repeatedPost).includes('Post top-band section:'),'Repeated post summaries must not be hardcoded to P0');
assert.equal(JSON.stringify(data),before,'Rendering must never mutate proposal geometry');
assert.equal(fs.readFileSync(path.join(__dirname,'../src/model-data.json'),'utf8'),modelBefore,'Canonical model must stay byte-identical');
assert(api.localPoint([.0254,.0508,.0762],{origin_m:[0,0,0],horizontal:[1,0,0],up:[0,1,0],transverse:[0,0,1]}).every((v,i)=>Math.abs(v-i-1)<1e-10));
assert(api.cropPolygon([[-2,0,0],[2,0,0],[0,2,0]],[[-1,-1,-1],[1,1,1]]).every(v=>v.every(x=>x>=-1.000001&&x<=1.000001)));
assert.equal(api.sectionSegments([[-1,0,-1],[1,0,1],[0,2,1]]).length,1);
class Element{
 constructor(id,doc){this.id=id;this.doc=doc;this.children=[];this.attrs={};this.value='';this.checked=false;this.disabled=false;this.textContent='';this.innerHTML='';this.className='';this.classList={values:new Set(),add:x=>this.classList.values.add(x),remove:x=>this.classList.values.delete(x),contains:x=>this.classList.values.has(x)};}
 appendChild(e){this.children.push(e);e.parentElement=this;return e;}
 append(...es){es.forEach(e=>this.appendChild(e));}
 replaceChildren(...es){this.children=[];this.append(...es);}
 setAttribute(k,v){this.attrs[k]=v;}
 focus(){this.doc.activeElement=this;}
 querySelectorAll(){return this.children;}
}
const nodes=new Map(),listeners=[];const document={activeElement:null,getElementById:id=>nodes.get(id),createElement:tag=>new Element(tag,document),addEventListener:(event,f)=>listeners.push({event,f})};
for(const id of ['stepLapModal','stepLapCurrent','stepLapProposed','stepLapState','stepLapMetrics','stepLapLimitations','stepLapView','stepLapPair','stepLapExplode','stepLapRemoved','stepLapNormals','closeStepLap','openStepLap','stepLapReset','stepLapJSON','stepLapSVG'])nodes.set(id,new Element(id,document));
const saved=[],events=[];document.activeElement=nodes.get('openStepLap');const controller=api.createController(data,{document,save:(...args)=>saved.push(args),release:()=>events.push('release'),onOpen:()=>events.push('open'),onClose:()=>events.push('close')});
assert(!controller.state.open);controller.open();controller.open();assert(controller.state.open);assert.deepStrictEqual(events,['release','open']);assert.equal(document.activeElement.id,'closeStepLap');
const initial=nodes.get('stepLapProposed').innerHTML;controller.set('explode',true);controller.set('removed',true);controller.set('normals',true);assert.notEqual(initial,nodes.get('stepLapProposed').innerHTML);
controller.set('variantId',data.variants[1].id);controller.set('view','section');assert(nodes.get('stepLapProposed').innerHTML.includes('center section'));controller.set('view','invalid');assert.equal(controller.state.view,'section');controller.set('variantId','missing');assert.equal(controller.state.variantId,data.variants[1].id);
nodes.get('stepLapJSON').onclick();nodes.get('stepLapSVG').onclick();assert(saved.every(([name])=>name.startsWith('PROPOSED-NOT-FABRICATION-')));assert.equal(JSON.parse(saved[0][1]).canonical_model_unchanged,true);assert(saved[1][1].includes('NOT FABRICATION APPROVED'));
controller.close();controller.close();assert(!controller.state.open);assert.equal(document.activeElement.id,'openStepLap');assert.deepStrictEqual(events,['release','open','close']);
controller.open();nodes.get('stepLapReset').onclick();assert.equal(controller.state.view,'iso');assert(!controller.state.explode&&!controller.state.removed&&!controller.state.normals);const escape={key:'Escape',preventDefault(){this.prevented=true;},stopPropagation(){this.stopped=true;}};listeners.find(x=>x.event==='keydown').f(escape);assert(!controller.state.open&&escape.prevented&&escape.stopped);
controller.open();nodes.get('stepLapModal').onclick({target:nodes.get('stepLapModal')});assert(!controller.state.open);assert.equal(JSON.stringify(data),before,'Repeated controls must preserve data');
const template=fs.readFileSync(path.join(__dirname,'../src/viewer.template.html'),'utf8');assert(template.includes("$('stepLapModal').classList.contains('open')"));assert.equal((template.match(/\/\*__STEP_LAP_REVIEW__\*\//g)||[]).length,1);assert(template.includes('baseline force markers are not applied'));assert(template.includes('owner-uploaded timber-frame manual has not been read'));assert(!template.includes('inferred step-lap'));

// Browser-like script classification: JSON data does not execute. Do not obtain the
// controller directly from its source module in this integration regression.
function scriptBlocks(html){return [...html.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script\s*>/gi)].map(([,attrs,body])=>({attrs,body,type:(attrs.match(/\btype\s*=\s*["']([^"']*)["']/i)?.[1]||'').toLowerCase(),id:attrs.match(/\bid\s*=\s*["']([^"']*)["']/i)?.[1]}));}
const executable=b=>['','text/javascript','application/javascript'].includes(b.type);
const templateBlocks=scriptBlocks(template);
assert.equal(templateBlocks.filter(b=>executable(b)&&b.body.includes('/*__STEP_LAP_REVIEW__*/')).length,1,'Step-lap embed marker must be in an executable script');
const html=fs.readFileSync(path.join(__dirname,'../dist/index.html'),'utf8'),blocks=scriptBlocks(html);
for(const b of blocks.filter(b=>b.type==='application/json'))assert.doesNotThrow(()=>JSON.parse(b.body),'Invalid JSON data script: '+b.id);
const embeddedModel=JSON.parse(blocks.find(b=>b.id==='model-data').body);
assert.deepStrictEqual(embeddedModel,JSON.parse(canonical),'Built HTML must use canonical baseline, not proposal');
const runtimeSource=blocks.filter(executable).map(b=>b.body).join('\n');
assert.equal((runtimeSource.match(/const stepLapReview=OctagonStepLap\.createController/g)||[]).length,1,'Executable HTML must bind the comparison controller');
// Reuse the full actual-viewer DOM harness. Add genuine HTML nodes absent from its
// source-ID discovery, then execute only scripts the browser would execute.
const htmlIds=[...html.matchAll(/<[\w-]+\b[^>]*\bid=["']([^"']+)["']/g)].map(m=>m[1]);
const initializeDOM=`'use strict';for(const id of ${JSON.stringify(htmlIds)}){if(!document.getElementById(id)){const el=document.createElement('div');el.id=id;document.root.appendChild(el);}}\n`;
const runtimeChecks=`
 const runtimeCheck=(ok,message)=>{if(!ok)throw Error(message);assertions.push(message);};
 const geometrySnapshot=()=>JSON.stringify(DATA.parts.map(p=>({id:p.id,vertices:p.vertices,triangles:p.triangles,axis_start:p.axis_start,axis_end:p.axis_end,dimensions:p.dimensions})));
 const canonicalSnapshot=geometrySnapshot(),loadSnapshot=JSON.stringify(LOAD_REVIEW),cameraSnapshot=JSON.stringify(camera);
 runtimeCheck(STEP_LAP_PROPOSAL.variants.length===${data.variants.length},'Built proposal variants match current source');
 runtimeCheck(typeof $('openStepLap').onclick==='function','Actual HTML binds Compare proposed joints button');
 runtimeCheck($('stepLapPair').children.length===STEP_LAP_PROPOSAL.variants.length,'Every proposed joint has a runtime selector');
 for(const variant of STEP_LAP_PROPOSAL.variants){
  $('openStepLap').focus();$('openStepLap').onclick();
  runtimeCheck($('stepLapModal').classList.contains('open')&&document.querySelector('main').inert,'Actual button opens comparison and isolates background');
  $('stepLapPair').value=variant.id;$('stepLapPair').onchange();
  runtimeCheck(stepLapReview.selected().id===variant.id&&$('stepLapProposed').innerHTML.includes(variant.member_ids.join(' + ')),'Actual selector renders '+variant.id);
  $('closeStepLap').onclick();
  runtimeCheck(!$('stepLapModal').classList.contains('open')&&!document.querySelector('main').inert&&document.activeElement===$('openStepLap'),'Actual close restores baseline and invoking focus');
 }
 runtimeCheck(geometrySnapshot()===canonicalSnapshot&&JSON.stringify(LOAD_REVIEW)===loadSnapshot,'Runtime comparison preserves canonical geometry and baseline load data');
 runtimeCheck(JSON.stringify(camera)===cameraSnapshot,'Runtime comparison leaves main camera unchanged');
`;
// Avoid a previously required module masking a missing embed in the real page.
delete global.OctagonStepLap;
const runtimeAssertions=require('./viewer-regression.cjs').runViewerTests(initializeDOM+runtimeSource+'\n'+runtimeChecks,embeddedModel,{search:'?model=baseline'});
assert(runtimeAssertions.some(s=>s==='Actual HTML binds Compare proposed joints button'));
console.log(`PASS: ${data.variants.length} actual proposal/baseline mesh pairs, section views, repeated controls and labeled exports; script-type-aware executable-HTML binding; ${runtimeAssertions.length} runtime/viewer assertions; canonical geometry and loads preserved`);
