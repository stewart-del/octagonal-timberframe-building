// TIMESTAMP START 2026-11-02T21:09:01-05:00 | REVISION R004877
const assert=require('node:assert/strict'),W=require('../src/wall-joinery.js'),fits=require('../src/wall-joinery-fit.json');
for(const [id,name] of [['baseline','model-data.json'],['proposed','step-lap-proposed-model.json'],['top-entry','top-entry-proposed-model.json']]){
 const original=require('../src/'+name),snapshot=JSON.stringify(original),fit=fits.variants[id],model=W.applyModel(original,fit);
 assert.equal(model.parts.length,original.parts.length);
 for(const p of model.parts){if(fit.primary_parts[p.id])assert.deepEqual(p.vertices,fit.primary_parts[p.id].vertices);else assert.equal(p,original.parts.find(q=>q.id===p.id));}
 const layout=W.applyLayout(require('../src/schematic-walls.js').build(model.parts),fit);
 for(const [pid,patch] of Object.entries(fit.wall_parts))assert.deepEqual(layout.components.find(p=>p.id===pid).vertices,patch.vertices);
 assert.equal(snapshot,JSON.stringify(original));
}
console.log('PASS: wall joint overlays patch selected primary and wall meshes without mutating canonical variants');
// TIMESTAMP END 2026-11-02T21:09:01-05:00 | REVISION R004877
