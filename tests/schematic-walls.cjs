const assert=require('node:assert/strict'),fs=require('node:fs');
const lib=require('../src/schematic-walls.js');const model=JSON.parse(fs.readFileSync(__dirname+'/../src/model-data.json'));const before=JSON.stringify(model);
const {walls,components}=lib.build(model.parts);
assert.equal(JSON.stringify(model),before);assert.equal(walls.length,8);
assert.deepEqual(walls.map(w=>w.face),['N','NW','W','SW','S','SE','E','NE']);
assert.deepEqual(walls.find(w=>w.face==='N').postIds,['P0','P1']);
for(const w of walls){
 assert.equal(w.usage,({N:'Solid wall + bookshelves',S:'Solid wall + bookshelves',E:'Large window',W:'Door'})[w.face]||'Small window');
 assert(w.width>0&&w.height>0);const pieces=components.filter(p=>p.face===w.face&&p.schematicKind!=='cupolaWindow');assert(pieces.length);
 for(const p of pieces){assert(p.schematic&&!p.is_timber);assert(p.vertices.flat().every(Number.isFinite));
  if(w.opening){const [x0,x1,y0,y1]=p.localBounds,o=w.opening;
   // Every solid box must be disjoint from the full clear aperture (not a plaque).
   assert(x1<=-o.width/2+1e-10||x0>=o.width/2-1e-10||y1<=o.bottom+1e-10||y0>=o.top-1e-10,p.id);
  }
 }
 assert.equal(pieces.some(p=>p.id.includes('shelf')),w.face==='N'||w.face==='S');
}
assert(walls.find(w=>w.face==='E').opening.width>walls.find(w=>w.face==='NE').opening.width);
assert.equal(walls.find(w=>w.face==='W').opening.bottom,walls.find(w=>w.face==='W').base);
const n=lib.orientation.north,e=lib.orientation.east;assert(Math.abs(n.reduce((s,x,i)=>s+x*e[i],0))<1e-12);
assert(Math.abs(walls.find(w=>w.face==='N').normal.reduce((s,x,i)=>s+x*n[i],0)-1)<1e-12);
assert(Math.abs(walls.find(w=>w.face==='E').normal.reduce((s,x,i)=>s+x*e[i],0)-1)<1e-12);
console.log('PASS: all8 wall faces, cardinal arrangement, true window/door voids, N/S shelves, shared design compass and unchanged model');

assert.equal(lib.build(model.parts).cupolaWindows.length,8);assert.equal(components.filter(p=>p.schematicKind==='cupolaWindow').length,32);
for(const w of lib.build(model.parts).cupolaWindows){assert(w.top>w.bottom&&w.width>0);}
