const assert=require('node:assert/strict'),fs=require('node:fs'),lib=require('../src/schematic-walls.js');
const model=JSON.parse(fs.readFileSync(__dirname+'/../src/model-data.json')),before=JSON.stringify(model),a=lib.build(model.parts);
assert.equal(JSON.stringify(model),before);
const of=k=>a.components.filter(p=>p.schematicKind===k);
assert.equal(of('floor').length,8);assert.equal(of('footer').length,8);assert.equal(of('grate').length,2);assert.equal(a.railConnections.length,64);
assert(of('rail').length>=32);assert(of('shelf').every(p=>['N','S'].includes(p.face)));assert(of('shelf').every(p=>!p.id.includes('side')));
// TIMESTAMP START 2026-11-02T18:40:43-05:00 | REVISION R004837
for(const shelf of of('shelf'))assert.deepEqual(shelf.localBounds.slice(4),[-.40,.0508],'Shelf back meets the recessed rail inner face while preserving its front edge');
// TIMESTAMP END 2026-11-02T18:40:43-05:00 | REVISION R004837
for(const p of a.components){assert(p.vertices.flat().every(Number.isFinite));assert(!p.is_timber);}
for(const p of of('floor')){
 assert.equal(p.material,'strand-woven bamboo');assert(Math.max(...p.vertices.map(v=>v[1]))===0);assert(Math.abs(Math.min(...p.vertices.map(v=>v[1]))+.01905)<1e-12);
 assert(p.vertices.every(v=>Math.hypot(v[0],v[2])>=.45-1e-10));
 assert(p.triangles.length>100,'Concentric strip geometry, not an opaque slab');
}
for(let k=0;k<8;k++){
 const post=model.parts.find(p=>p.id==='P'+k),footer=of('footer')[k];
 assert.equal(Math.max(...footer.vertices.map(v=>v[1])),Math.min(...post.vertices.map(v=>v[1])));
}
for(const p of of('rail')){
 const w=a.walls.find(w=>w.face===p.face),[x0,x1,y0,y1]=p.localBounds;
 if(w.opening){const o=w.opening;assert(x1<=-o.width/2+1e-10||x0>=o.width/2-1e-10||y1<=o.bottom+1e-10||y0>=o.top-1e-10,'Rails must not seal apertures');}
}
assert(of('grate').every(p=>p.material==='metal'));assert(a.railConnections.every(p=>p.status.includes('unresolved')));
console.log('PASS:8 patterned bamboo sectors, open grate,8 footers, substantial segmented rails, integrated shelves, no canonical mutation or load credit');

const html=fs.readFileSync(__dirname+'/../src/viewer.template.html','utf8');for(const id of ['schematicWalls','schematicShelves','schematicFloor','schematicCupolaWindows'])assert(html.includes('<label class=\"checkline\"><input id=\"'+id+'\"'));
