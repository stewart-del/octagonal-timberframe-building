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

const viewerSource=require('fs').readFileSync(require('path').join(__dirname,'../src/viewer.template.html'),'utf8');
assert(viewerSource.includes('id="roomLayers" open'));
assert(viewerSource.indexOf('id="roomLayers"')<viewerSource.indexOf('id="browsePieces"'));

for(const w of walls){assert.strictEqual(w.frameFit.endClearance,0);assert.strictEqual(w.frameFit.topClearance,0);const beam=model.parts.find(p=>p.id==='B'+w.postIds[0].slice(1));assert(Math.abs(w.height-Math.min(...beam.vertices.map(v=>v[1])))<1e-9);assert.strictEqual(w.base,0);}

// TIMESTAMP START 2026-11-02T13:42:10-05:00 | REVISION R004782
const rawLayout=lib.build(model.parts,{applyFit:false});
const role=require('../src/display-presets.js');
assert.equal(rawLayout.components.filter(p=>p.framingRole==='jamb').length,12);
assert.equal(rawLayout.components.filter(p=>p.framingRole==='header').length,6);
assert.equal(rawLayout.components.filter(p=>p.framingRole==='sill').length,5);
for(const wall of rawLayout.walls){
 const pieces=rawLayout.components.filter(p=>p.face===wall.face&&['wall','rail'].includes(p.schematicKind));
 const area=pieces.reduce((sum,p)=>{const [a,b,c,d]=p.localBounds;return sum+(b-a)*(d-c);},0);
 const aperture=wall.opening?wall.opening.width*(wall.opening.top-wall.opening.bottom):0;
 assert(Math.abs(area-(wall.width*(wall.height-wall.base)-aperture))<1e-10,wall.face+' fills its complete rectangle outside the opening');
 for(let i=0;i<pieces.length;i++)for(let j=i+1;j<pieces.length;j++){
  const a=pieces[i].localBounds,b=pieces[j].localBounds;
  assert(Math.min(a[1],b[1])-Math.max(a[0],b[0])<=1e-10||Math.min(a[3],b[3])-Math.max(a[2],b[2])<=1e-10,pieces[i].id+' overlaps '+pieces[j].id);
 }
 if(!wall.opening)continue;
 const o=wall.opening,w=o.width/2;
 assert.deepEqual([o.bottom,o.top],wall.face==='W'?[0,2.10]:wall.face==='E'?[.75,1.95]:[1,1.85]);
 assert.equal(o.width,wall.face==='W'?.95:wall.width*(wall.face==='E'?.65:.30));
 const frames=pieces.filter(p=>p.framingRole);
 for(const side of ['left','right']){
  const jamb=frames.find(p=>p.id==='SCHEM-'+wall.face+'-rail-jamb-'+side);assert(jamb);
  assert.deepEqual(jamb.localBounds,side==='left'?[-w-.1524,-w,wall.base+.1524,wall.height,-.0762,.0762]:[w,w+.1524,wall.base+.1524,wall.height,-.0762,.0762]);
 }
 for(const p of frames){assert.equal(role.role(p),'wallStructure');assert(role.included(p,'skeleton'));assert(Math.hypot(...p.exploded_offset)>0);assert.equal(p.is_timber,false);assert(p.connectionStatus.includes('unresolved'));}
 assert.equal(frames.some(p=>p.framingRole==='sill'),wall.face!=='W');
}
console.log('PASS: exact 12 jambs/6 headers/5 sills, preserved six clear openings, complete disjoint wall rectangles, Skeleton role and nonzero explosion offsets');
// TIMESTAMP END 2026-11-02T13:42:10-05:00 | REVISION R004782
