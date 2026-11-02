'use strict';
const assert=require('node:assert');
require('../src/model-variants.js');
const api=global.OctagonModelVariants,fixture=id=>({model:{parts:[{id:'P0',vertices:[[id==='baseline'?1:2,0,0]],triangles:[]}]},sha256:id,loadReview:{source_model_sha256:id,members:[{id:'P0',volume_m3:id==='baseline'?1:2,centroid_m:[id==='baseline'?1:2,0,0]}],issues:[{id:'baseline-location'}]},materials:{source_sha256:id,groups:[]},enclosureFit:{source_model_sha256:id,source_module_sha256:'test',parts:{}},cavities:{source_model_sha256:id,parts:{},available:true}}),variants={baseline:fixture('baseline'),proposed:fixture('proposed')},before=JSON.stringify(variants);
assert.equal(api.requestedId(''),'proposed');assert.equal(api.requestedId('?model=baseline'),'baseline');assert.equal(api.requestedId('?model=other'),'proposed');
for(const id of ['baseline','proposed']){const c=api.context(variants,'?model='+id);assert.equal(c.model.parts[0].vertices[0][0],id==='baseline'?1:2);assert.equal(c.loadReview.members[0].volume_m3,id==='baseline'?1:2);assert.equal(c.loadReview.issues.length,id==='baseline'?1:0);assert.equal(c.pressureAvailable,id==='baseline');assert.equal(c.contactMarkersAvailable,id==='baseline');assert(api.exportName(c,'model.json').startsWith(c.exportPrefix));assert.equal(api.exportName(c,'PROPOSED-NOT-FABRICATION-pair.svg'),'PROPOSED-NOT-FABRICATION-pair.svg');}
for(const key of ['loadReview','materials','cavities','enclosureFit']){const bad=JSON.parse(before);bad.proposed[key][key==='materials'?'source_sha256':'source_model_sha256']='baseline';assert.throws(()=>api.context(bad),/stale/);}
const withoutCavities=JSON.parse(before);delete withoutCavities.proposed.cavities;assert.equal(api.context(withoutCavities).cavities.available,false);assert.deepEqual(api.context(withoutCavities).cavities.parts,{});
assert.equal(api.selectionURL('https://example.test/view?other=1#part=P0&isolate=1','baseline'),'https://example.test/view?other=1&model=baseline#part=P0&isolate=1');assert.throws(()=>api.selectionURL('https://example.test','other'));
const nodes=new Map(['modelVariant','modelVariantStatus','modelRevisionBadge','plansRevision','hypotheticalSeat','hypotheticalReaction','hypotheticalPressure','loadIssueDetail','showHollows','hollowMode','hollowXray','hollowStatus'].map(id=>[id,{id,textContent:'',value:'',checked:true,disabled:false}])),document={getElementById:id=>nodes.get(id)},visits=[],location={href:'https://example.test/view?other=1#part=P0',assign:url=>visits.push(url)},changes=[];
api.bind(api.context(variants),{document,location,beforeChange:()=>changes.push('change')});assert.equal(nodes.get('modelVariant').value,'proposed');assert(nodes.get('hypotheticalSeat').disabled);assert(nodes.get('hypotheticalPressure').textContent.includes('disabled'));assert(nodes.get('loadIssueDetail').textContent.includes('disabled'));
nodes.get('modelVariant').onchange();assert.equal(visits.length,0);nodes.get('modelVariant').value='bad';nodes.get('modelVariant').onchange();assert.equal(visits.length,0);assert.equal(nodes.get('modelVariant').value,'proposed');nodes.get('modelVariant').value='baseline';nodes.get('modelVariant').onchange();assert.equal(visits.length,1);assert.equal(changes.length,1);assert(visits[0].includes('model=baseline')&&visits[0].endsWith('#part=P0'));
api.bind(api.context(withoutCavities),{document,location});assert(nodes.get('showHollows').disabled&&!nodes.get('showHollows').checked);assert.equal(JSON.stringify(variants),before,'Selection does not mutate either source bundle');
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),root=path.join(__dirname,'..');
const html=fs.readFileSync(path.join(root,'dist/index.html'),'utf8');
const blocks=[...html.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script>/gi)].map(([,attrs,body])=>({attrs,body,type:attrs.match(/\btype="([^"]+)"/i)?.[1]||''}));
const source=blocks.filter(b=>['','text/javascript','application/javascript'].includes(b.type)).map(b=>b.body).join('\n');
const htmlIds=[...html.matchAll(/<[\w-]+\b[^>]*\bid=["']([^"']+)["']/g)].map(m=>m[1]);
const dom=`'use strict';for(const id of ${JSON.stringify(htmlIds)}){if(!document.getElementById(id)){const el=document.createElement('div');el.id=id;document.root.appendChild(el);}}\n`;
const baseline=JSON.parse(fs.readFileSync(path.join(root,'src/model-data.json')));
const {runViewerTests}=require('./viewer-regression.cjs');
for(const [id,search] of [['proposed',''],['baseline','?model=baseline']]){
 const filename=id==='baseline'?'model-data.json':'step-lap-proposed-model.json',raw=fs.readFileSync(path.join(root,'src',filename)),expected=JSON.parse(raw),sha=crypto.createHash('sha256').update(raw).digest('hex');
 const load=JSON.parse(fs.readFileSync(path.join(root,'src',id==='baseline'?'load-review-data.json':'step-lap-proposed-load-review.json')));
 const checks=`
 const check=(ok,message)=>{if(!ok)throw Error(message);assertions.push(message);};
 check(MODEL_CONTEXT.id===${JSON.stringify(id)},'Boot selects ${id}');
 check(MODEL_CONTEXT.sha256===${JSON.stringify(sha)}&&PLAN_MODEL_HASH===MODEL_CONTEXT.sha256,'Selected model and plan cache use actual source hash');
 check(MODEL_EXPORT_JSON===${JSON.stringify(JSON.stringify(expected,null,2))},'Main JSON export is exact selected source, before display mutation');
 check(JSON.stringify(parts.map(p=>[p.id,p.vertices,p.triangles]))===${JSON.stringify(JSON.stringify(expected.parts.map(p=>[p.id,p.vertices,p.triangles])))},'Actual main 3D meshes are the selected geometry');
 check(JSON.stringify(LOAD_REVIEW.members)===${JSON.stringify(JSON.stringify(load.members))},'All104 self-weight volumes and centroids match selected source');
 check(CAVITIES.source_model_sha256===MODEL_CONTEXT.sha256&&MATERIALS.source_sha256===MODEL_CONTEXT.sha256,'Cavities and inventory share selected source hash');
 if(MODEL_CONTEXT.isProposed){check(CAVITIES.available===false&&!showHollows&&Object.keys(CAVITIES.parts).length===0&&$('showHollows').disabled&&!$('showHollows').checked,'Proposed recess overlay is withheld without baseline substitution');selectPart('P0');updateHollowStatus();check(cavityRecords().length===0&&$('hollowStatus').textContent===CAVITIES.status,'Withheld recess layer remains empty and accurately explained after selection');}
 else {check(CAVITIES.available&&showHollows&&!$('showHollows').disabled,'Saved baseline cavity feature remains unchanged');selectPart('P0');updateHollowStatus();check($('hollowStatus').textContent.includes('may overlap owner wood')&&$('hollowStatus').textContent.includes('not certified empty space'),'Baseline recess display is explicitly diagnostic and unverified');}
 explode=.4;cutExplode=.2;showAllAndUncenter();check(explode===0&&cutExplode===0&&$('explode').value==='0'&&schematicFloorEnabled&&schematicWallsEnabled,'Reset restores assembled geometry and visible room layers');
 const inspectorText=n=>[n.textContent||'',...(n.children||[]).map(inspectorText)].join(' ');
 for(const timberId of ['J0-0','R0']){selectPart(timberId);const text=inspectorText($('selection'));check(text.includes('Nominal section')&&text.includes('Nominal axis length'),'Timber '+timberId+' retains timber dimensions');check(!text.includes('Owner reference overall span')&&!text.includes('8 radial L straps'),'Timber '+timberId+' never inherits temporary steel fixture metadata');}
 selectPart('M-TMP');check(inspectorText($('selection')).includes('Owner reference overall span')&&inspectorText($('selection')).includes('8 radial L straps'),'Only temporary M-TMP fixture retains its owner-reported steel dimensions');
 check(OCTAGON_ENCLOSURE_FIT.source_model_sha256===MODEL_CONTEXT.sha256,'Enclosure fit follows selected source');
 for(const p of schematicParts){const fitted=OCTAGON_ENCLOSURE_FIT.parts[p.id];if(fitted)check(JSON.stringify(p.vertices)===JSON.stringify(fitted.vertices),'Runtime fitted '+p.id+' uses selected clearance mesh');}
 $('schematicFloor').checked=true;$('schematicFloor').onchange();check(schematicParts.filter(p=>['floor','grate'].includes(p.schematicKind)).every(isShown),'Floor/grate toggle retained on selected model');
 check($('modelVariant').value===MODEL_CONTEXT.id,'Selector displays actual boot choice');
 check(LOAD_REVIEW.issues.length===${id==='proposed'?0:load.issues.length},'Contact markers never reuse baseline data on proposal');
 check(!!$('hypotheticalSeat').disabled===MODEL_CONTEXT.isProposed,'Baseline pressure shortcuts disabled on proposal');
 $('hypotheticalReaction').value='1000';updateHypotheticalPressure();
 if(MODEL_CONTEXT.isProposed)check($('hypotheticalPressure').textContent.includes('disabled'),'Direct pressure refresh cannot restore stale shortcut');
 $('plansFloor').checked=true;refreshPlans();check(plansSVG.top.includes(MODEL_CONTEXT.label)&&plansSVG.side.includes(MODEL_CONTEXT.label),'Plan title states selected revision');
 check($('modelVariantAssembled').href.includes(MODEL_CONTEXT.isProposed?'PROPOSED-step-lap':'R01'),'GLB link follows selected geometry');
 const saved=[];download=(name,text,type)=>saved.push([OctagonModelVariants.exportName(MODEL_CONTEXT,name),text,type]);
 $('downloadJSON').onclick();check(saved[0][0].startsWith(MODEL_CONTEXT.exportPrefix)&&saved[0][1]===MODEL_EXPORT_JSON,'Actual export button downloads selected source with revision-qualified name');
 $('modelVariant').value=MODEL_CONTEXT.isProposed?'baseline':'proposed';$('modelVariant').onchange();
 check(window.location.assigned.includes('model='+(MODEL_CONTEXT.isProposed?'baseline':'proposed')),'Actual selector navigates to reversible chosen revision');
 `;
 const results=runViewerTests(dom+source+'\n'+checks,baseline,{search,skipLegacy:true});assert(results.length>=12);
}
// Proposed GLB must advertise the same source and not inherit baseline R01 status.
const proposedRaw=fs.readFileSync(path.join(root,'src/step-lap-proposed-model.json')),proposedParts=JSON.parse(proposedRaw).parts.filter(p=>!p.temporary&&p.group!=='roof_envelope');
for(const view of ['assembled','exploded']){
 const glb=fs.readFileSync(path.join(root,'dist/downloads/Octagon-PROPOSED-step-lap-'+view+'.glb')),length=glb.readUInt32LE(12),meta=JSON.parse(glb.subarray(20,20+length)),binary=28+length;
 assert(meta.extras.status.includes('NOT FABRICATION'));assert.equal(meta.extras.source_model_sha256,crypto.createHash('sha256').update(proposedRaw).digest('hex'));assert.equal(meta.nodes.length,proposedParts.length);
 for(const p of proposedParts){const node=meta.nodes.find(n=>n.name===p.id),mesh=meta.meshes[node.mesh].primitives[0],positions=meta.accessors[mesh.attributes.POSITION],indices=meta.accessors[mesh.indices],pv=meta.bufferViews[positions.bufferView],iv=meta.bufferViews[indices.bufferView];
  assert.equal(positions.count,p.vertices.length);assert.equal(indices.count,p.triangles.length*3);assert.deepStrictEqual(node.translation,view==='exploded'?(p.exploded_offset||[0,0,0]):[0,0,0]);
  p.vertices.flat().forEach((v,i)=>assert(Math.abs(glb.readFloatLE(binary+pv.byteOffset+i*4)-v)<1e-6,p.id+' exported mesh coordinates'));
  p.triangles.flat().forEach((v,i)=>assert.equal(glb.readUInt32LE(binary+iv.byteOffset+i*4),v,p.id+' exported topology'));
 }
}
console.log('PASS: actual default-proposed and baseline runtime meshes, 104 weights/centroids, hash-bound inventory/cavities/plans, reversible selector, no stale pressures/markers and source-matched JSON/GLB exports');
