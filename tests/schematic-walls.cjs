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
 // TIMESTAMP START 2026-11-02T18:32:34-05:00 | REVISION R004834
 assert.deepEqual([o.bottom,o.top],wall.face==='W'?[0,2.10]:wall.face==='E'?[.75,1.85]:[1,1.85]);
 // TIMESTAMP END 2026-11-02T18:32:34-05:00 | REVISION R004834
 assert.equal(o.width,wall.face==='W'?.95:wall.width*(wall.face==='E'?.65:.30));
 const frames=pieces.filter(p=>p.framingRole);
 for(const side of ['left','right']){
  const jamb=frames.find(p=>p.id==='SCHEM-'+wall.face+'-rail-jamb-'+side);assert(jamb);
  // TIMESTAMP START 2026-11-02T18:40:43-05:00 | REVISION R004837
// TIMESTAMP START 2026-11-02T20:31:01-05:00 | REVISION R004867
  const inner=wall.face==='W'?.0254:.0508,depth=[inner,inner+.1016];
  assert.deepEqual(jamb.localBounds,side==='left'?[-w-.1016,-w,wall.base+.1524,wall.height,...depth]:[w,w+.1016,wall.base+.1524,wall.height,...depth]);
// TIMESTAMP END 2026-11-02T20:31:01-05:00 | REVISION R004867
  // TIMESTAMP END 2026-11-02T18:40:43-05:00 | REVISION R004837
 }
 for(const p of frames){assert.equal(role.role(p),'wallStructure');assert(role.included(p,'skeleton'));assert(Math.hypot(...p.exploded_offset)>0);assert.equal(p.is_timber,false);assert(p.connectionStatus.includes('unresolved'));}
 assert.equal(frames.some(p=>p.framingRole==='sill'),wall.face!=='W');
}
console.log('PASS: exact 12 jambs/6 headers/5 sills, preserved six clear openings, complete disjoint wall rectangles, Skeleton role and nonzero explosion offsets');
// TIMESTAMP END 2026-11-02T13:42:10-05:00 | REVISION R004782

// TIMESTAMP START 2026-11-02T14:35:15-05:00 | REVISION R004794
for(const filename of ['model-data.json','step-lap-proposed-model.json','top-entry-proposed-model.json']){
 const variant=JSON.parse(fs.readFileSync(__dirname+'/../src/'+filename)),layout=lib.build(variant.parts,{applyFit:false});
 for(const wall of layout.walls){
  // TIMESTAMP START 2026-11-02T18:32:34-05:00 | REVISION R004834
  const expectedBottom=wall.face==='W'?2.10:1.85;
  // TIMESTAMP END 2026-11-02T18:32:34-05:00 | REVISION R004834
  const girts=layout.components.filter(p=>p.face===wall.face&&p.id.startsWith('SCHEM-'+wall.face+'-rail3-'));
  assert(girts.length,wall.face+' retains its upper girt');
  for(const p of girts)assert.deepEqual(p.localBounds.slice(2,4),[expectedBottom,expectedBottom+.1524]);
  if(wall.face==='W'){
   assert.equal(wall.opening.top,2.10,'Do not lower the existing doorway to enlarge the wall band');
   continue;
  }
  const bandBottom=expectedBottom+.1524,bandMid=(bandBottom+wall.height)/2;
  assert(wall.height-bandBottom>.15,wall.face+' has a visible infill band below the main beam');
  assert(layout.components.some(p=>p.face===wall.face&&p.schematicKind==='wall'&&p.localBounds[0]<0&&p.localBounds[1]>0&&p.localBounds[2]<bandMid&&p.localBounds[3]>bandMid),wall.face+' band contains infill above the window head');
  if(wall.opening){
   const head=layout.components.find(p=>p.face===wall.face&&p.framingRole==='header');
   assert.deepEqual(head.localBounds.slice(2,4),[expectedBottom,bandBottom],'Upper girt and header form one level without a second stacked rail');
  }
 }
}
console.log('PASS: all three variants retain a visible upper wall band on seven faces; window heads align with girts and west doorway stays 2.10 m clear');
// TIMESTAMP END 2026-11-02T14:35:15-05:00 | REVISION R004794

// TIMESTAMP START 2026-11-02T18:13:09-05:00 | REVISION R004829
const unsplit=lib.build(model.parts,{applyFit:false,splitInfill:false});
const splitBoards=rawLayout.components.filter(p=>p.panelAssemblyId),parents=[...new Set(splitBoards.map(p=>p.panelAssemblyId))];
assert.equal(parents.length,14);assert.equal(splitBoards.length,28);
assert.equal(rawLayout.components.length,unsplit.components.length+14);
for(const parent of parents){
 const original=unsplit.components.find(p=>p.id===parent),children=splitBoards.filter(p=>p.panelAssemblyId===parent);
 const low=children.find(p=>p.panelSeamPart==='lower'),high=children.find(p=>p.panelSeamPart==='upper');
 assert.deepEqual(low.localBounds,[...original.localBounds.slice(0,3),64*.0254,...original.localBounds.slice(4)]);
 assert.deepEqual(high.localBounds,[...original.localBounds.slice(0,2),64*.0254,...original.localBounds.slice(3)]);
 assert.equal(low.localBounds[3],high.localBounds[2]);
 assert.equal(low.panelSeamY_M,64*.0254);assert.equal(high.panelSeamY_M,64*.0254);
}
console.log('PASS:14 real horizontal panel seams,28 separately selectable boards, unchanged complete panel envelopes');
// TIMESTAMP END 2026-11-02T18:13:09-05:00 | REVISION R004829

// TIMESTAMP START 2026-11-02T18:40:43-05:00 | REVISION R004837
for(const p of rawLayout.components){
 const west=p.face==='W',infill=west?[.03095,.05]:[.08255,.1016],frame=west?[.0254,.0762]:[.0508,.1016],sill=west?[-.0762,.0762]:[-.0508,.1016];
 if(p.schematicKind==='wall')assert.deepEqual(p.localBounds.slice(4),infill,p.id+' is three-quarter-inch infill behind the braces');
// TIMESTAMP START 2026-11-02T20:31:01-05:00 | REVISION R004867
 if(p.schematicKind==='rail')assert.deepEqual(p.localBounds.slice(4),p.framingRole==='jamb'?[frame[0],frame[0]+.1016]:p.id.includes('-rail0-')?sill:frame,p.id+' preserves sill ledges, 4×4 jambs and recessed horizontal rails');
// TIMESTAMP END 2026-11-02T20:31:01-05:00 | REVISION R004867
 if(p.panelAssemblyId)assert.deepEqual(p.unsplitLocalBounds.slice(4),infill);
}
for(const connection of rawLayout.railConnections){
 const wall=rawLayout.walls.find(w=>w.face===connection.face),post=model.parts.find(p=>p.id===wall.postIds[0]),other=model.parts.find(p=>p.id===wall.postIds[1]);
 const origin=post.center.map((x,i)=>(x+other.center[i])/2);
 const depth=connection.center.reduce((sum,x,i)=>sum+(x-origin[i])*wall.normal[i],0);
 const bottomSill=connection.railId.includes('-rail0-');
 const expectedDepth=wall.face==='W'?(bottomSill?0:.0508):(bottomSill?.0254:.0762);
 assert(Math.abs(depth-expectedDepth)<1e-12);assert(Math.abs(connection.depth-(bottomSill?.1524:.0508))<1e-12);
}
console.log('PASS: recessed two-by-six secondary frames, three-quarter-inch infill, and connection markers follow their actual depths');
// TIMESTAMP END 2026-11-02T18:40:43-05:00 | REVISION R004837
