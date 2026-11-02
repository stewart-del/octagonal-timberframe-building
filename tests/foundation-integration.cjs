const assert=require('node:assert/strict'),fs=require('node:fs'),F=require('../src/floor-foundation.js'),W=require('../src/schematic-walls.js'),solid=require('../src/floor-foundation-solids.json'),C=require('../src/cut-face-analysis.js');
for(const name of ['model-data.json','step-lap-proposed-model.json','top-entry-proposed-model.json']){
 const model=require('../src/'+name),base=W.build(model.parts),room=F.roomLayout(model,base,solid);
 assert.equal(room.components.filter(p=>p.schematicKind==='floorAssembly').length,139);assert.equal(room.components.filter(p=>p.id.startsWith('PIER-')).length,9);assert(!room.components.some(p=>['grate','footer'].includes(p.schematicKind)));
 const sample=room.components.find(p=>p.id==='FLOOR-BEAM-0'),report=C.analysePart(sample,{revision:name});assert.equal(report.frame,null);assert(report.faces.length>0);assert(report.faces.every(f=>f.angles.miterDeg===null));
 const revised=JSON.parse(JSON.stringify(model));revised.parts.find(p=>p.id==='P0').center[0]+=.1;assert.throws(()=>F.roomLayout(revised,base,solid),/stale/);
}
console.log('PASS:139runtime floor solids in all three selected models,9piers,no grate/footer,geometrycutanalysisunknownaxes,postchangeinvalidates');
