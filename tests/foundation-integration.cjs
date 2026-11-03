// TIMESTAMP START 2026-11-02T20:27:45-05:00 | REVISION R004866
const assert=require('node:assert/strict'),fs=require('node:fs'),F=require('../src/floor-foundation.js'),W=require('../src/schematic-walls.js'),solid=require('../src/floor-foundation-solids.json'),C=require('../src/cut-face-analysis.js');
for(const name of ['model-data.json','step-lap-proposed-model.json','top-entry-proposed-model.json']){
 const model=require('../src/'+name),base=W.build(model.parts),room=F.roomLayout(model,base,solid);
// TIMESTAMP START 2026-11-03T12:04:27-05:00 | REVISION R005002
 assert.equal(room.components.filter(p=>p.schematicKind==='floorAssembly').length,105);assert.equal(room.components.filter(p=>p.id.startsWith('PIER-')).length,34);assert(!room.components.some(p=>['grate','footer'].includes(p.schematicKind)));
// TIMESTAMP END 2026-11-03T12:04:27-05:00 | REVISION R005002
 const sample=room.components.find(p=>p.id==='FLOOR-BEAM-0'),report=C.analysePart(sample,{revision:name});assert.equal(report.frame,null);assert(report.faces.length>0);assert(report.faces.every(f=>f.angles.miterDeg===null));
 const revised=JSON.parse(JSON.stringify(model));revised.parts.find(p=>p.id==='P0').center[0]+=.1;assert.throws(()=>F.roomLayout(revised,base,solid),/stale/);
}
// TIMESTAMP START 2026-11-03T12:04:27-05:00 | REVISION R005002
console.log('PASS:105 runtime floor solids in all three selected models,17 piers and 17 underground columns,no grate/footer,geometrycutanalysisunknownaxes,postchangeinvalidates');
// TIMESTAMP END 2026-11-03T12:04:27-05:00 | REVISION R005002

// TIMESTAMP END 2026-11-02T20:27:45-05:00 | REVISION R004866

// TIMESTAMP START 2026-11-02T21:09:01-05:00 | REVISION R004877
const source=fs.readFileSync(__dirname+'/../src/viewer.template.html','utf8'),alphaSource=source.match(/function selectionAlpha\(p\) \{([\s\S]*?)\n\}/)[1];
const selectedPartIds=new Set(),isSelectedMember=p=>selectedPartIds.has(p.id);let showHollows=false;
const alpha=new Function('p','selectedPartIds','isSelectedMember','showHollows',alphaSource);
const porch=require('../src/mudroom.js').build(require('../src/top-entry-proposed-model.json')).components;
const buried=[...solid.parts,...porch].filter(p=>p.underground),above=[...solid.parts,...porch].filter(p=>p.id.startsWith('PIER-')||p.mudroomRole==='foundation').filter(p=>!p.underground);
// TIMESTAMP START 2026-11-03T12:04:27-05:00 | REVISION R005002
assert.equal(buried.length,21);
// TIMESTAMP END 2026-11-03T12:04:27-05:00 | REVISION R005002
for(const p of buried){assert.equal(p.displayOpacity,.28);assert.equal(alpha(p,selectedPartIds,isSelectedMember,false),.28);selectedPartIds.add(p.id);assert.equal(alpha(p,selectedPartIds,isSelectedMember,true),.28);selectedPartIds.clear();}
for(const p of above)assert.equal(alpha(p,selectedPartIds,isSelectedMember,false),1);
// TIMESTAMP START 2026-11-03T12:04:27-05:00 | REVISION R005002
console.log('PASS: all twenty-one buried columns remain transparent, including selection; above-grade supports remain opaque');
// TIMESTAMP END 2026-11-03T12:04:27-05:00 | REVISION R005002
// TIMESTAMP END 2026-11-02T21:09:01-05:00 | REVISION R004877
