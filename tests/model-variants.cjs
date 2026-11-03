'use strict';
const assert=require('node:assert');
require('../src/model-variants.js');
const api=global.OctagonModelVariants,fixture=id=>({model:{parts:[{id:'P0',vertices:[[id==='baseline'?1:2,0,0]],triangles:[]}]},sha256:id,loadReview:{source_model_sha256:id,members:[{id:'P0',volume_m3:id==='baseline'?1:2,centroid_m:[id==='baseline'?1:2,0,0]}],issues:[{id:'baseline-location'}]},materials:{source_sha256:id,groups:[]},enclosureFit:{source_model_sha256:id,source_module_sha256:'test',parts:{}},cavities:{source_model_sha256:id,parts:{P0:{removed:{triangles:[[0,1,2]]}}},available:true,fit_audit:{status:'PASS'}}}),variants={baseline:fixture('baseline'),proposed:fixture('proposed'),'top-entry':fixture('top-entry')},before=JSON.stringify(variants);
assert.equal(api.requestedId(''),'top-entry');assert.equal(api.requestedId('?model=baseline'),'baseline');assert.equal(api.requestedId('?model=other'),'top-entry');
for(const id of ['baseline','proposed','top-entry']){const c=api.context(variants,'?model='+id);assert.equal(c.model.parts[0].vertices[0][0],id==='baseline'?1:2);assert.equal(c.loadReview.members[0].volume_m3,id==='baseline'?1:2);assert.equal(c.loadReview.issues.length,id==='baseline'?1:0);assert.equal(c.pressureAvailable,id==='baseline');assert.equal(c.contactMarkersAvailable,id==='baseline');assert(api.exportName(c,'model.json').startsWith(c.exportPrefix));assert.equal(api.exportName(c,'PROPOSED-NOT-FABRICATION-pair.svg'),'PROPOSED-NOT-FABRICATION-pair.svg');}
for(const key of ['loadReview','materials','cavities','enclosureFit']){const bad=JSON.parse(before);bad.proposed[key][key==='materials'?'source_sha256':'source_model_sha256']='baseline';assert.throws(()=>api.context(bad,'?model=proposed'),/stale/);}
const withoutCavities=JSON.parse(before);delete withoutCavities.proposed.cavities;assert.equal(api.context(withoutCavities,'?model=proposed').cavities.available,false);assert.deepEqual(api.context(withoutCavities,'?model=proposed').cavities.parts,{});
for(const id of ['baseline','proposed','top-entry']){const unproved=JSON.parse(before);delete unproved[id].cavities.fit_audit;assert.equal(api.context(unproved,'?model='+id).cavities.available,false);assert.deepEqual(api.context(unproved,'?model='+id).cavities.parts,{});unproved[id].cavities.fit_audit={status:'FAIL'};assert.equal(api.context(unproved,'?model='+id).cavities.available,false);}
assert.equal(api.selectionURL('https://example.test/view?other=1#part=P0&isolate=1','baseline'),'https://example.test/view?other=1&model=baseline#part=P0&isolate=1');assert.throws(()=>api.selectionURL('https://example.test','other'));
const nodes=new Map(['modelVariant','modelVariantStatus','modelRevisionBadge','plansRevision','hypotheticalSeat','hypotheticalReaction','hypotheticalPressure','loadIssueDetail','showHollows','hollowMode','hollowXray','hollowStatus'].map(id=>[id,{id,textContent:'',value:'',checked:true,disabled:false}])),document={getElementById:id=>nodes.get(id)},visits=[],location={href:'https://example.test/view?other=1#part=P0',assign:url=>visits.push(url)},changes=[];
api.bind(api.context(variants,'?model=proposed'),{document,location,beforeChange:()=>changes.push('change')});assert.equal(nodes.get('modelVariant').value,'proposed');assert(nodes.get('hypotheticalSeat').disabled);assert(nodes.get('hypotheticalPressure').textContent.includes('disabled'));assert(nodes.get('loadIssueDetail').textContent.includes('disabled'));
nodes.get('modelVariant').onchange();assert.equal(visits.length,0);nodes.get('modelVariant').value='bad';nodes.get('modelVariant').onchange();assert.equal(visits.length,0);assert.equal(nodes.get('modelVariant').value,'proposed');nodes.get('modelVariant').value='baseline';nodes.get('modelVariant').onchange();assert.equal(visits.length,1);assert.equal(changes.length,1);assert(visits[0].includes('model=baseline')&&visits[0].endsWith('#part=P0'));
api.bind(api.context(withoutCavities,'?model=proposed'),{document,location});assert(nodes.get('showHollows').disabled&&!nodes.get('showHollows').checked);assert.equal(JSON.stringify(variants),before,'Selection does not mutate either source bundle');
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),root=path.join(__dirname,'..');
const html=fs.readFileSync(path.join(root,'dist/index.html'),'utf8');
const blocks=[...html.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script>/gi)].map(([,attrs,body])=>({attrs,body,type:attrs.match(/\btype="([^"]+)"/i)?.[1]||''}));
const source=blocks.filter(b=>['','text/javascript','application/javascript'].includes(b.type)).map(b=>b.body).join('\n');
const htmlIds=[...html.matchAll(/<[\w-]+\b[^>]*\bid=["']([^"']+)["']/g)].map(m=>m[1]);
const dom=`'use strict';for(const id of ${JSON.stringify(htmlIds)}){if(!document.getElementById(id)){const el=document.createElement('div');el.id=id;document.root.appendChild(el);}}\n`;
const baseline=JSON.parse(fs.readFileSync(path.join(root,'src/model-data.json')));
const {runViewerTests}=require('./viewer-regression.cjs');
for(const [id,search] of [['top-entry',''],['proposed','?model=proposed'],['baseline','?model=baseline']]){
// TIMESTAMP START 2026-11-03T06:44:16-05:00 | REVISION R004894
 const filename=id==='baseline'?'model-data.json':id==='top-entry'?'top-entry-proposed-model.json':'step-lap-proposed-model.json',raw=fs.readFileSync(path.join(root,'src',filename)),wallFit=require('../src/wall-joinery-fit.json').variants[id],expected=require('../src/wall-joinery.js').applyModel(JSON.parse(raw),wallFit),sha=crypto.createHash('sha256').update(raw).digest('hex');
 const load=JSON.parse(fs.readFileSync(path.join(root,'src',id==='baseline'?'load-review-data.json':id==='top-entry'?'top-entry-proposed-load-review.json':'step-lap-proposed-load-review.json')));
 load.members=load.members.map(p=>wallFit.primary_parts[p.id]?{...p,...wallFit.primary_parts[p.id].wallJoineryMass}:p);
// TIMESTAMP END 2026-11-03T06:44:16-05:00 | REVISION R004894
 const checks=`
 const check=(ok,message)=>{if(!ok)throw Error(message);assertions.push(message);};
 check(MODEL_CONTEXT.id===${JSON.stringify(id)},'Boot selects ${id}');
 check(MODEL_CONTEXT.sha256===${JSON.stringify(sha)}&&PLAN_MODEL_HASH===MODEL_CONTEXT.sha256,'Selected model and plan cache use actual source hash');
 check(MODEL_EXPORT_JSON===${JSON.stringify(JSON.stringify(expected,null,2))},'Main JSON export is exact selected source, before display mutation');
 check(JSON.stringify(parts.map(p=>[p.id,p.vertices,p.triangles]))===${JSON.stringify(JSON.stringify(expected.parts.map(p=>[p.id,p.vertices,p.triangles])))},'Actual main 3D meshes are the selected geometry');
// TIMESTAMP START 2026-11-02T15:19:38-05:00 | REVISION R004803
 check(JSON.stringify(LOAD_REVIEW.members)===${JSON.stringify(JSON.stringify(load.members))},'All 112 self-weight volumes and centroids match selected source');
// TIMESTAMP END 2026-11-02T15:19:38-05:00 | REVISION R004803
 check(CAVITIES.source_model_sha256===MODEL_CONTEXT.sha256&&MATERIALS.source_sha256===MODEL_CONTEXT.sha256,'Cavities and inventory share selected source hash');
// TIMESTAMP START 2026-11-02T17:13:18-05:00 | REVISION R004819
 check(CAVITIES.available&&CAVITIES.fit_audit.status==='PASS'&&showHollows&&!$('showHollows').disabled,'Each selected model requires its own passing cavity audit');
 // TIMESTAMP START 2026-11-03T06:44:16-05:00 | REVISION R004894
 selectPart('P0');updateHollowStatus();check(cavityRecords().length>0&&$('hollowStatus').textContent.includes('Joint geometry-fit audit passed'),'Actual fitted post recess visible through selected timber');
 // TIMESTAMP END 2026-11-03T06:44:16-05:00 | REVISION R004894
 const prior=$('showLabels').checked;$('showLabels').checked=false;$('showLabels').onchange({target:$('showLabels')});check(cavityRecords().length>0,'Labels handler does not hide selected amber');$('showLabels').checked=prior;$('showLabels').onchange({target:$('showLabels')});
 const auditName=MODEL_CONTEXT.id==='baseline'?'cavity-fit-audit.json':MODEL_CONTEXT.id==='top-entry'?'top-entry-cavity-fit-audit.json':'step-lap-proposed-cavity-fit-audit.json';
 check(!$('cavityFitAuditLink').hidden&&$('cavityFitAuditLink').href.includes('downloads/'+auditName),'Selected audit link matches actual model');
// TIMESTAMP START 2026-11-03T06:44:16-05:00 | REVISION R004894
 if(MODEL_CONTEXT.id==='top-entry'){selectPart('R0');updateHollowStatus();check($('hollowStatus').textContent.includes('declared open joint-entry space'),'Open head-entry space is described honestly');selectPart('C0');updateHollowStatus();check(cavityRecords().length>0,'New center dovetail cavity is visible');}
// TIMESTAMP END 2026-11-03T06:44:16-05:00 | REVISION R004894
// TIMESTAMP END 2026-11-02T17:13:18-05:00 | REVISION R004819

 explode=.4;cutExplode=.2;showAllAndUncenter();check(explode===0&&cutExplode===0&&$('explode').value==='0'&&schematicFloorEnabled&&schematicWallsEnabled,'Reset restores assembled geometry and visible room layers');
 const presetCamera=JSON.stringify({camera,fly,navigation});
 for(const key of ['complete','skeleton','foundation','floor']){applyDisplayPreset(key);check(JSON.stringify({camera,fly,navigation})===presetCamera,'Preset '+key+' preserves camera and navigation');check([...parts,...schematicParts].every(p=>isShown(p)===OctagonDisplayPresets.included(p,key)),'Preset '+key+' shows exact permanent semantic layers');check($('displayPresetStatus').textContent.includes(OctagonDisplayPresets.PRESETS[key]),'Preset '+key+' reports active assembled state');}
 applyDisplayPreset('skeleton');$('layerFloorFinish').checked=true;$('layerFloorFinish').onchange();check($('displayPresetStatus').textContent==='Custom'&&schematicParts.filter(p=>OctagonDisplayPresets.role(p)==='floorFinish').every(isShown),'Independent finish toggle creates Custom without locking');
// TIMESTAMP START 2026-11-03T06:44:16-05:00 | REVISION R004894
 $('constructionAids').onclick();check(parts.filter(p=>p.temporary).some(isShown),'Temporary aids remain manually available');showAllAndUncenter();check(isShown(partById.get('M-TMP'))&&!isShown(partById.get('M-SP0'))&&$('displayPresetStatus').textContent.includes('Complete'),'Reset restores Complete with welded support and green aid hidden');
// TIMESTAMP END 2026-11-03T06:44:16-05:00 | REVISION R004894
 document.createElementNS=(namespace,tag)=>document.createElement(tag);
 selectPart('J0-0');const findNode=(n,id)=>n.id===id?n:(n.children||[]).map(c=>findNode(c,id)).find(Boolean);const cutEntry=findNode($('selection'),'pieceCutAngles');check(!!cutEntry,'Current piece offers separate Cut angles button');cutEntry.focus();cutEntry.onclick();check($('cutAnglesModal').classList.contains('open')&&navigationBlocked(canvas),'Cut-angle dialog blocks navigation');cutAngleView.renderPiece('J0-0');const cutReport=cutAngleView.getReport();check(cutReport.partId==='J0-0'&&cutReport.parameters.model_sha256===MODEL_CONTEXT.sha256,'Cut-angle report binds selected model hash');check(JSON.stringify(cutReport)===JSON.stringify(OctagonCutFaces.analysePart(partById.get('J0-0'),{revision:MODEL_CONTEXT.label,parameters:{model_sha256:MODEL_CONTEXT.sha256,model_revision:DATA.revision}})),'Cut-angle UI uses shared current-mesh analysis without independent angles');cutAngleView.renderPiece(schematicParts[0].id);check(cutAngleView.getReport().partId===schematicParts[0].id,'Cut list includes room-layer meshes without inventing stock axes');cutAngleView.close();check(document.activeElement===cutEntry&&!document.querySelector('main').inert,'Cut-angle close restores invoker and background');
 matrix();updateSchematicWalls();check(!labelsOn&&schematicLabels.every(x=>x.el.style.display==='none'),'Initial wall/window/bookshelf annotations are off');
 check(!edgeMeasurementsOn&&!loadReviewOn,'Measurement and load annotations start off');
 $('showLabels').checked=true;$('showLabels').onchange({target:$('showLabels')});updateSchematicWalls();check(schematicLabels.some(x=>x.el.style.display==='block'),'Labels toggle includes wall/opening annotations');
 for(const preset of ['complete','skeleton','foundation','floor']){labelsOn=true;detailOn=true;edgeMeasurementsOn=true;applyDisplayPreset(preset);updateSchematicWalls();check(!labelsOn&&!detailOn&&!edgeMeasurementsOn&&!$('showLabels').checked&&schematicLabels.every(x=>x.el.style.display==='none'),'Preset '+preset+' restores annotation-free view');}
 labelsOn=true;edgeMeasurementsOn=true;showAllAndUncenter();updateSchematicWalls();check(!labelsOn&&!edgeMeasurementsOn&&schematicLabels.every(x=>x.el.style.display==='none'),'Reset restores annotation-free Complete');
 selectPart('R0');inspectionPartId='R0';updatePieceCenter();check($('pieceCenterLabel').hidden,'Selection pivot text obeys Labels toggle');
 const inspectorText=n=>[n.textContent||'',...(n.children||[]).map(inspectorText)].join(' ');
// TIMESTAMP START 2026-11-02T19:03:48-05:00 | REVISION R004848
// TIMESTAMP START 2026-11-02T19:14:55-05:00 | REVISION R004853
 for(const braceId of ['K2-A','K2-B','K2-C']){selectPart(braceId);const text=inspectorText($('selection'));check(text.includes('Actual full-sawn section')&&text.includes('2.00 × 6.00 in'),'Brace '+braceId+' states actual full-sawn dimensions');const proof=findNode($('selection'),'braceSectionProof');check(proof&&proof.href==='review/brace-sections.svg','Brace '+braceId+' links independent mesh-section evidence');}
// TIMESTAMP END 2026-11-02T19:14:55-05:00 | REVISION R004853
// TIMESTAMP END 2026-11-02T19:03:48-05:00 | REVISION R004848
 for(const timberId of ['J0-0','R0']){selectPart(timberId);const text=inspectorText($('selection'));check(text.includes('Nominal section')&&text.includes('Nominal axis length'),'Timber '+timberId+' retains timber dimensions');check(!text.includes('Owner reference overall span')&&!text.includes('8 radial L straps'),'Timber '+timberId+' never inherits temporary steel fixture metadata');}
 selectPart('M-TMP');check(inspectorText($('selection')).includes('Owner reference overall span')&&inspectorText($('selection')).includes('8 radial L straps'),'Only temporary M-TMP fixture retains its owner-reported steel dimensions');
 check(OCTAGON_ENCLOSURE_FIT.source_model_sha256===MODEL_CONTEXT.sha256,'Enclosure fit follows selected source');
// TIMESTAMP START 2026-11-03T06:44:16-05:00 | REVISION R004894
 for(const p of schematicParts){const fitted=MODEL_CONTEXT.wallJoinery.wall_parts[p.id]||OCTAGON_ENCLOSURE_FIT.parts[p.id];if(fitted)check(JSON.stringify(p.vertices)===JSON.stringify(fitted.vertices),'Runtime fitted '+p.id+' uses selected wall joint or clearance mesh');}
// TIMESTAMP END 2026-11-03T06:44:16-05:00 | REVISION R004894
 $('schematicFloor').checked=true;$('schematicFloor').onchange();check(schematicParts.filter(p=>['floor','grate'].includes(p.schematicKind)).every(isShown),'Floor/grate toggle retained on selected model');
 check($('modelVariant').value===MODEL_CONTEXT.id,'Selector displays actual boot choice');
 check(LOAD_REVIEW.issues.length===${id!=='baseline'?0:load.issues.length},'Contact markers never reuse baseline data on proposal');
// TIMESTAMP START 2026-11-03T06:44:16-05:00 | REVISION R004894
 check($('hypotheticalSeat').disabled&&!MODEL_CONTEXT.pressureAvailable,'Old pressure shortcuts stay disabled on the fitted wall models');
// TIMESTAMP END 2026-11-03T06:44:16-05:00 | REVISION R004894
 $('hypotheticalReaction').value='1000';updateHypotheticalPressure();
 if(MODEL_CONTEXT.isProposed)check($('hypotheticalPressure').textContent.includes('disabled'),'Direct pressure refresh cannot restore stale shortcut');
 $('plansFloor').checked=true;refreshPlans();check(plansSVG.top.includes(MODEL_CONTEXT.label)&&plansSVG.side.includes(MODEL_CONTEXT.label),'Plan title states selected revision');
 check($('modelVariantAssembled').href.includes(MODEL_CONTEXT.id==='top-entry'?'TOP-ENTRY':MODEL_CONTEXT.isProposed?'PROPOSED-step-lap':'R01'),'GLB link follows selected geometry');
 const saved=[];download=(name,text,type)=>saved.push([OctagonModelVariants.exportName(MODEL_CONTEXT,name),text,type]);
 $('downloadJSON').onclick();check(saved[0][0].startsWith(MODEL_CONTEXT.exportPrefix)&&saved[0][1]===MODEL_EXPORT_JSON,'Actual export button downloads selected source with revision-qualified name');
 $('modelVariant').value=MODEL_CONTEXT.isProposed?'baseline':'proposed';$('modelVariant').onchange();
 check(window.location.assigned.includes('model='+(MODEL_CONTEXT.isProposed?'baseline':'proposed')),'Actual selector navigates to reversible chosen revision');
 `;
 const results=runViewerTests(dom+source+'\n'+checks,baseline,{search,skipLegacy:true});assert(results.length>=12);
}
// Proposed GLB must advertise the same source and not inherit baseline R01 status.
for(const [modelFile,prefix] of [['step-lap-proposed-model.json','Octagon-PROPOSED-step-lap-'],['top-entry-proposed-model.json','Octagon-TOP-ENTRY-']]){
// TIMESTAMP START 2026-11-03T06:44:16-05:00 | REVISION R004894
const proposedRaw=fs.readFileSync(path.join(root,'src',modelFile)),wallFit=require('../src/wall-joinery-fit.json').variants[modelFile.startsWith('top-entry')?'top-entry':'proposed'],proposedParts=require('../src/wall-joinery.js').applyModel(JSON.parse(proposedRaw),wallFit).parts.filter(p=>!p.temporary&&p.group!=='roof_envelope');
// TIMESTAMP END 2026-11-03T06:44:16-05:00 | REVISION R004894
// TIMESTAMP START 2026-11-02T18:14:42-05:00 | REVISION R004830
const planRaw=fs.readFileSync(path.join(root,'src/disassembly-plan.json')),variant=modelFile.startsWith('top-entry')?'top-entry':'proposed',plan=JSON.parse(planRaw).variants[variant],offsets=new Map(proposedParts.map(p=>[p.id,[0,0,0]]));
for(const stage of plan.stages)for(const motion of stage.motions||[stage])for(const id of motion.member_ids)if(offsets.has(id))offsets.set(id,offsets.get(id).map((v,i)=>v+motion.delta_m[i]));
// TIMESTAMP END 2026-11-02T18:14:42-05:00 | REVISION R004830
for(const view of ['assembled','exploded']){
 const glb=fs.readFileSync(path.join(root,'dist/downloads/'+prefix+view+'.glb')),length=glb.readUInt32LE(12),meta=JSON.parse(glb.subarray(20,20+length)),binary=28+length;
 assert(meta.extras.status.includes('NOT FABRICATION'));assert.equal(meta.extras.source_model_sha256,crypto.createHash('sha256').update(proposedRaw).digest('hex'));assert.equal(meta.nodes.length,proposedParts.length);
 // TIMESTAMP START 2026-11-02T18:14:42-05:00 | REVISION R004830
 assert.equal(meta.extras.disassembly_pose,view==='exploded'?'checked-endpoint':'assembled-start');
 assert.equal(meta.extras.disassembly_plan_sha256,crypto.createHash('sha256').update(planRaw).digest('hex'));assert.equal(meta.extras.disassembly_variant,variant);assert.equal(meta.extras.disassembly_status,plan.status);assert.equal(meta.extras.disassembly_stage_count,plan.stages.length);
 assert.deepStrictEqual(meta.extras.disassembly_held_ids,plan.unmoved_ids.filter(id=>offsets.has(id)).sort());
 // TIMESTAMP END 2026-11-02T18:14:42-05:00 | REVISION R004830
 for(const p of proposedParts){const node=meta.nodes.find(n=>n.name===p.id),mesh=meta.meshes[node.mesh].primitives[0],positions=meta.accessors[mesh.attributes.POSITION],indices=meta.accessors[mesh.indices],pv=meta.bufferViews[positions.bufferView],iv=meta.bufferViews[indices.bufferView];
  // TIMESTAMP START 2026-11-02T18:14:42-05:00 | REVISION R004830
  assert.equal(positions.count,p.vertices.length);assert.equal(indices.count,p.triangles.length*3);assert.deepStrictEqual(node.translation,view==='exploded'?offsets.get(p.id):[0,0,0]);
  // TIMESTAMP END 2026-11-02T18:14:42-05:00 | REVISION R004830
  p.vertices.flat().forEach((v,i)=>assert(Math.abs(glb.readFloatLE(binary+pv.byteOffset+i*4)-v)<1e-6,p.id+' exported mesh coordinates'));
  p.triangles.flat().forEach((v,i)=>assert.equal(glb.readUInt32LE(binary+iv.byteOffset+i*4),v,p.id+' exported topology'));
 }
}
}
// TIMESTAMP START 2026-11-02T15:19:38-05:00 | REVISION R004803
console.log('PASS: actual default top-entry, perimeter proposal and baseline runtime meshes, 112 weights/centroids, hash-bound inventory/cavities/plans, reversible selector, no stale pressures/markers and source-matched JSON/GLB exports');
// TIMESTAMP END 2026-11-02T15:19:38-05:00 | REVISION R004803
