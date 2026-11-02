'use strict';
const assert=require('node:assert');
require('../src/model-variants.js');
// TIMESTAMP START 2026-11-02T10:08:20-05:00 | REVISION R004760
const api=global.OctagonModelVariants,fixture=id=>({model:{parts:[{id:'P0',vertices:[[id==='baseline'?1:2,0,0]],triangles:[]}]},sha256:id,loadReview:{source_model_sha256:id,members:[{id:'P0',volume_m3:id==='baseline'?1:2,centroid_m:[id==='baseline'?1:2,0,0]}],issues:[{id:'baseline-location'}]},materials:{source_sha256:id,groups:[]},enclosureFit:{source_model_sha256:id,source_module_sha256:'test',parts:{}},cavities:{source_model_sha256:id,parts:{P0:{removed:{vertices:[[0,0,0]],triangles:[],volume_m3:0}}},available:true,fit_audit:{status:'PASS',summary:{}}}}),variants={baseline:fixture('baseline'),proposed:fixture('proposed')},before=JSON.stringify(variants);
// TIMESTAMP END 2026-11-02T10:08:20-05:00 | REVISION R004760
assert.equal(api.requestedId(''),'proposed');assert.equal(api.requestedId('?model=baseline'),'baseline');assert.equal(api.requestedId('?model=other'),'proposed');
for(const id of ['baseline','proposed']){const c=api.context(variants,'?model='+id);assert.equal(c.model.parts[0].vertices[0][0],id==='baseline'?1:2);assert.equal(c.loadReview.members[0].volume_m3,id==='baseline'?1:2);assert.equal(c.loadReview.issues.length,id==='baseline'?1:0);assert.equal(c.pressureAvailable,id==='baseline');assert.equal(c.contactMarkersAvailable,id==='baseline');assert(api.exportName(c,'model.json').startsWith(c.exportPrefix));assert.equal(api.exportName(c,'PROPOSED-NOT-FABRICATION-pair.svg'),'PROPOSED-NOT-FABRICATION-pair.svg');}
for(const key of ['loadReview','materials','cavities','enclosureFit']){const bad=JSON.parse(before);bad.proposed[key][key==='materials'?'source_sha256':'source_model_sha256']='baseline';assert.throws(()=>api.context(bad),/stale/);}
// TIMESTAMP START 2026-11-02T10:08:20-05:00 | REVISION R004760
const withoutCavities=JSON.parse(before);delete withoutCavities.proposed.cavities;assert.equal(api.context(withoutCavities).cavities.available,false);assert.deepEqual(api.context(withoutCavities).cavities.parts,{});
for(const id of ['baseline','proposed']){
 const checked=api.context(variants,'?model='+id);assert(checked.cavityAuditPassed&&checked.cavities.available);assert(checked.status.includes('cavity-fit audit passed'));
 for(const status of ['FAIL',undefined]){const unaudited=JSON.parse(before);unaudited[id].cavities.fit_audit.status=status;const c=api.context(unaudited,'?model='+id);assert(!c.cavities.available&&!c.cavityAuditPassed);assert.deepEqual(c.cavities.parts,{});assert(c.status.includes('audit unavailable'));}
 const missing=JSON.parse(before);delete missing[id].cavities.fit_audit;assert(!api.context(missing,'?model='+id).cavities.available);
 const disabled=JSON.parse(before);disabled[id].cavities.available=false;assert(!api.context(disabled,'?model='+id).cavities.available);
}
// TIMESTAMP END 2026-11-02T10:08:20-05:00 | REVISION R004760
assert.equal(api.selectionURL('https://example.test/view?other=1#part=P0&isolate=1','baseline'),'https://example.test/view?other=1&model=baseline#part=P0&isolate=1');assert.throws(()=>api.selectionURL('https://example.test','other'));
// TIMESTAMP START 2026-11-02T10:08:20-05:00 | REVISION R004760
const nodes=new Map(['modelVariant','modelVariantStatus','modelRevisionBadge','plansRevision','cavityFitAuditLink','hypotheticalSeat','hypotheticalReaction','hypotheticalPressure','loadIssueDetail','showHollows','hollowXray','hollowStatus'].map(id=>[id,{id,textContent:'',value:'',checked:true,disabled:false}])),document={getElementById:id=>nodes.get(id)},visits=[],location={href:'https://example.test/view?other=1#part=P0',assign:url=>visits.push(url)},changes=[];
// TIMESTAMP END 2026-11-02T10:08:20-05:00 | REVISION R004760
api.bind(api.context(variants),{document,location,beforeChange:()=>changes.push('change')});assert.equal(nodes.get('modelVariant').value,'proposed');assert(nodes.get('hypotheticalSeat').disabled);assert(nodes.get('hypotheticalPressure').textContent.includes('disabled'));assert(nodes.get('loadIssueDetail').textContent.includes('disabled'));
nodes.get('modelVariant').onchange();assert.equal(visits.length,0);nodes.get('modelVariant').value='bad';nodes.get('modelVariant').onchange();assert.equal(visits.length,0);assert.equal(nodes.get('modelVariant').value,'proposed');nodes.get('modelVariant').value='baseline';nodes.get('modelVariant').onchange();assert.equal(visits.length,1);assert.equal(changes.length,1);assert(visits[0].includes('model=baseline')&&visits[0].endsWith('#part=P0'));
// TIMESTAMP START 2026-11-02T10:08:20-05:00 | REVISION R004760
api.bind(api.context(withoutCavities),{document,location});assert(nodes.get('showHollows').disabled&&!nodes.get('showHollows').checked);assert.equal(JSON.stringify(variants),before,'Selection does not mutate either source bundle');
for(const id of ['baseline','proposed']){api.bind(api.context(variants,'?model='+id),{document,location});assert(!nodes.get('showHollows').disabled&&!nodes.get('hollowXray').disabled);assert(nodes.get('modelVariantStatus').textContent.includes('cavity-fit audit passed'));assert.equal(nodes.get('cavityFitAuditLink').href,'downloads/'+(id==='proposed'?'step-lap-proposed-cavity-fit-audit.json':'cavity-fit-audit.json'));}
// TIMESTAMP END 2026-11-02T10:08:20-05:00 | REVISION R004760
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
// TIMESTAMP START 2026-11-02T10:08:20-05:00 | REVISION R004760
 check(CAVITIES.available&&CAVITIES.fit_audit.status==='PASS'&&MODEL_CONTEXT.cavityAuditPassed&&showHollows&&!$('showHollows').disabled,'Selected model enables its independently audited recesses');
 check(Object.keys(CAVITIES.parts).length===104&&Object.values(CAVITIES.parts).every(r=>r.removed&&!Object.hasOwn(r,'unfilled')),'Both variants use complete removed-only timber cavity records');
 selectPart('P0');updateHollowStatus();check(cavityRecords().some(r=>r.p.id==='P0')&&$('hollowStatus').textContent.includes('Independent cavity-fit audit passed.'),'Selected timber displays its matching audited cavity and status');
 check($('modelVariantStatus').textContent.includes('cavity-fit audit passed'),'Variant status states the selected-model cavity audit result');
// TIMESTAMP END 2026-11-02T10:08:20-05:00 | REVISION R004760
// TIMESTAMP START 2026-11-02T10:56:59-05:00 | REVISION R004768
 explode=.4;cutExplode=.2;showAllAndUncenter();check(explode===0&&cutExplode===0&&$('explode').value==='0'&&schematicFloorEnabled&&schematicWallsEnabled,'Reset restores assembled geometry and visible room layers');
 document.createElementNS=(namespace,tag)=>document.createElement(tag);
 selectPart('J0-0');const findNode=(n,id)=>n.id===id?n:(n.children||[]).map(c=>findNode(c,id)).find(Boolean);const cutEntry=findNode($('selection'),'pieceCutAngles');check(!!cutEntry,'Current piece offers separate Cut angles button');cutEntry.focus();cutEntry.onclick();check($('cutAnglesModal').classList.contains('open')&&navigationBlocked(canvas),'Cut-angle dialog blocks navigation');cutAngleView.renderPiece('J0-0');const cutReport=cutAngleView.getReport();check(cutReport.partId==='J0-0'&&cutReport.parameters.model_sha256===MODEL_CONTEXT.sha256,'Cut-angle report binds selected model hash');check(JSON.stringify(cutReport)===JSON.stringify(OctagonCutFaces.analysePart(partById.get('J0-0'),{revision:MODEL_CONTEXT.label,parameters:{model_sha256:MODEL_CONTEXT.sha256,model_revision:DATA.revision}})),'Cut-angle UI uses shared current-mesh analysis without independent angles');cutAngleView.renderPiece(schematicParts[0].id);check(cutAngleView.getReport().partId===schematicParts[0].id,'Cut list includes room-layer meshes without inventing stock axes');cutAngleView.close();check(document.activeElement===cutEntry&&!document.querySelector('main').inert,'Cut-angle close restores invoker and background');
 const inspectorText=n=>[n.textContent||'',...(n.children||[]).map(inspectorText)].join(' ');
 for(const timberId of ['J0-0','R0']){selectPart(timberId);const text=inspectorText($('selection'));check(text.includes('Nominal section')&&text.includes('Nominal axis length'),'Timber '+timberId+' retains timber dimensions');check(!text.includes('Owner reference overall span')&&!text.includes('8 radial L straps'),'Timber '+timberId+' never inherits temporary steel fixture metadata');}
 selectPart('M-TMP');check(inspectorText($('selection')).includes('Owner reference overall span')&&inspectorText($('selection')).includes('8 radial L straps'),'Only temporary M-TMP fixture retains its owner-reported steel dimensions');
// TIMESTAMP END 2026-11-02T10:56:59-05:00 | REVISION R004768
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
