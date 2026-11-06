// TIMESTAMP START 2026-11-05T04:18:09+00:00 | REVISION R000020
// TIMESTAMP START 2026-11-02T14:21:43-05:00 | REVISION R004791
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),crypto=require('node:crypto'),mudroom=require('../src/mudroom.js'),walls=require('../src/schematic-walls.js');
const near=(a,b,e=1e-9)=>assert(Math.abs(a-b)<e,`${a} != ${b}`);
const dot=(a,b)=>a.reduce((s,x,i)=>s+x*b[i],0),cross=(a,b)=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];
function volume(p){return p.triangles.reduce((sum,t)=>sum+dot(p.vertices[t[0]],cross(p.vertices[t[1]],p.vertices[t[2]]))/6,0);}
function plane(p,upper){const v=p.localVertices,a=v[upper?3:0],b=v[upper?2:1],c=v[upper?7:4],x=(b[1]-a[1])/(b[0]-a[0]),z=(c[1]-a[1])/(c[2]-a[2]);return [x,z,a[1]-x*a[0]-z*a[2]];}
const evaluate=(p,x,z)=>p[0]*x+p[1]*z+p[2];
// Exact convex vertical-prism test: partition their common footprint at both
// upper/lower plane crossover lines, then check every resulting polygon vertex.
function overlapDepth(a,b){
 const aa=a.localBounds,bb=b.localBounds,x0=Math.max(aa[0],bb[0]),x1=Math.min(aa[1],bb[1]),z0=Math.max(aa[4],bb[4]),z1=Math.min(aa[5],bb[5]);
 if(x1-x0<1e-10||z1-z0<1e-10||Math.min(aa[3],bb[3])-Math.max(aa[2],bb[2])<1e-10)return 0;
 const low=[plane(a,false),plane(b,false)],high=[plane(a,true),plane(b,true)],lines=[low[0].map((v,i)=>v-low[1][i]),high[0].map((v,i)=>v-high[1][i])],points=[[x0,z0],[x1,z0],[x1,z1],[x0,z1]];
 const add=(x,z)=>{if(Number.isFinite(x)&&Number.isFinite(z)&&x>=x0-1e-10&&x<=x1+1e-10&&z>=z0-1e-10&&z<=z1+1e-10)points.push([x,z]);};
 for(const [a,b,c] of lines){if(Math.abs(b)>1e-12)for(const x of [x0,x1])add(x,-(a*x+c)/b);if(Math.abs(a)>1e-12)for(const z of [z0,z1])add(-(b*z+c)/a,z);}
 const [l,m]=lines,det=l[0]*m[1]-m[0]*l[1];if(Math.abs(det)>1e-12)add((l[1]*m[2]-m[1]*l[2])/det,(m[0]*l[2]-l[0]*m[2])/det);
 return Math.max(0,...points.map(([x,z])=>Math.min(...high.map(p=>evaluate(p,x,z)))-Math.max(...low.map(p=>evaluate(p,x,z)))));
}
let pairs=0;
for(const filename of ['model-data.json','step-lap-proposed-model.json','top-entry-proposed-model.json']){
 // TIMESTAMP START 2026-11-02T15:00:19-05:00 | REVISION R004797
 const path=__dirname+'/../src/'+filename,before=fs.readFileSync(path),model=JSON.parse(before),snapshot=JSON.stringify(model),r=mudroom.build(model,{applyJoinery:false}),d=r.dimensions,byId=Object.fromEntries(r.components.map(p=>[p.id,p]));
 // TIMESTAMP END 2026-11-02T15:00:19-05:00 | REVISION R004797
 near(d.clearWidthM,8*.3048);near(d.clearDepthM,8*.3048);near(d.backFloorY_M,-6*.0254);near(d.frontFloorY_M,-8*.0254);near(d.floorSlope,1/48);near(d.clearAisleM,5*.3048);
 assert.equal(JSON.stringify(model),snapshot,'Building the addition must not mutate source geometry');assert.deepEqual(fs.readFileSync(path),before);
 assert.equal(new Set(r.components.map(p=>p.id)).size,r.components.length);assert.equal(new Set(r.components.map(p=>JSON.stringify(p.exploded_offset))).size,r.components.length);
 // TIMESTAMP START 2026-11-02T15:00:19-05:00 | REVISION R004797
 const prisms=r.components.filter(p=>p.localVertices?.length===8&&p.triangles.length===12&&p.mudroomRole!=='roof');
 for(const p of prisms){
 // TIMESTAMP END 2026-11-02T15:00:19-05:00 | REVISION R004797
  assert(p.schematic&&p.schematicKind==='mudroom'&&p.displayRole==='mudroom');assert(p.exploded_offset.every(Number.isFinite)&&Math.hypot(...p.exploded_offset)>0);assert(volume(p)>1e-10,p.id+' has nonpositive volume');
  assert(p.vertices.every(v=>v.every(Number.isFinite)),p.id+' invalid vertices');
  const edges=new Map();for(const t of p.triangles)for(let k=0;k<3;k++){const a=t[k],b=t[(k+1)%3],key=[Math.min(a,b),Math.max(a,b)].join(',');const value=edges.get(key)||[0,0];value[0]++;value[1]+=a<b?1:-1;edges.set(key,value);}
  assert([...edges.values()].every(([count,direction])=>count===2&&direction===0),p.id+' is not a closed oriented solid');
  for(const upper of [false,true])for(const k of upper?[2,3,6,7]:[0,1,4,5]){const v=p.localVertices[k];near(v[1],evaluate(plane(p,upper),v[0],v[2]));}
  for(let k=0;k<8;k++)r.local(p.vertices[k]).forEach((v,i)=>near(v,p.localVertices[k][i]));
 }
 // TIMESTAMP START 2026-11-02T15:00:19-05:00 | REVISION R004797
 const architectural=prisms.filter(p=>!p.joineryBlank);
 for(let i=0;i<architectural.length;i++)for(let j=i+1;j<architectural.length;j++){pairs++;assert(overlapDepth(architectural[i],architectural[j])<1e-9,`Overlap ${architectural[i].id} / ${architectural[j].id}`);}
 // TIMESTAMP END 2026-11-02T15:00:19-05:00 | REVISION R004797
 assert.equal(r.components.filter(p=>/^MUD-BENCH-[LR]$/.test(p.id)).length,2);assert.equal(r.components.filter(p=>/^MUD-SHOE-SHELF-/.test(p.id)).length,2);assert.equal(r.components.filter(p=>/^MUD-HOOK-[LR]-\d$/.test(p.id)).length,6);
 assert(!r.components.some(p=>p.mudroomRole==='wall'||/^MUD-(WALL|WINDOW|DOOR|FRONT-JAMB|REAR-CLOSURE|BACKREST)/.test(p.id)),'Open porch must have no enclosure, glazing, door or separate bench backs');
 assert(r.components.filter(p=>p.mudroomScreen).every(p=>p.mudroomRoof),'Roof cutaway must retain the open porch guards and posts');
// TIMESTAMP START 2026-11-02T20:31:01-05:00 | REVISION R004867
 for(const p of r.components.filter(p=>/^MUD-(POST-|ENTRY-GUARD-POST-)/.test(p.id))){near(p.localBounds[1]-p.localBounds[0],4*.0254);near(p.localBounds[5]-p.localBounds[4],4*.0254);}
 for(const p of r.components.filter(p=>p.underground)){near(p.localBounds[3]-p.localBounds[2],6*.3048);near(p.displayOpacity,.28);}
// TIMESTAMP END 2026-11-02T20:31:01-05:00 | REVISION R004867
 near(d.entryWidthM,.95);near(byId['MUD-ENTRY-GUARD-POST-R'].localBounds[0]-byId['MUD-ENTRY-GUARD-POST-L'].localBounds[1],d.entryWidthM);
 for(const side of ['L','R']){
  const bench=byId['MUD-BENCH-'+side],guard=byId['MUD-GUARD-TOP-'+side],pickets=r.components.filter(p=>p.id.startsWith('MUD-GUARD-PICKET-'+side+'-')).sort((a,b)=>a.localBounds[4]-b.localBounds[4]);
  // TIMESTAMP START 2026-11-02T15:00:19-05:00 | REVISION R004797
// TIMESTAMP START 2026-11-03T17:20:17-05:00 | REVISION R005073
  near(guard.localBounds[3]-bench.localBounds[3],18*.0254);near(guard.localBounds[1]-guard.localBounds[0],4*.0254);
// TIMESTAMP END 2026-11-03T17:20:17-05:00 | REVISION R005073
  // TIMESTAMP END 2026-11-02T15:00:19-05:00 | REVISION R004797
  assert(pickets.every(p=>p.localBounds[2]<bench.localBounds[3]&&p.localBounds[3]>bench.localBounds[3]),'Railing must continue below and above bench seat');
  for(let i=1;i<pickets.length;i++)assert(pickets[i].localBounds[4]-pickets[i-1].localBounds[5]<=d.maxGuardPicketGapM+1e-9,'Side railing gap exceeds chosen proposal');
  assert(pickets[0].localBounds[4]-guard.localBounds[4]<=d.maxGuardPicketGapM+1e-9);assert(guard.localBounds[5]-pickets.at(-1).localBounds[5]<=d.maxGuardPicketGapM+1e-9);
 }
 const grate=r.components.filter(p=>/^MUD-GRATE-BAR-/.test(p.id));assert.equal(grate.length,96);const first=grate[0].localBounds,second=grate[1].localBounds;near(second[0]-first[1],.5*.0254);
 const channel=r.components.filter(p=>/^MUD-CHANNEL-/.test(p.id)),outlet=d.drainOutletCenter;assert(channel.every(p=>!(outlet[0]>p.localBounds[0]&&outlet[0]<p.localBounds[1]&&outlet[2]>p.localBounds[4]&&outlet[2]<p.localBounds[5])),'Drain outlet is a real void');
 for(const p of r.components.filter(p=>/^MUD-BENCH-LEG-[LR]-/.test(p.id)))for(const v of [p.localVertices[0],p.localVertices[1],p.localVertices[4],p.localVertices[5]])near(v[1],r.floorHeight(v[2]));
 const stepTops=[d.frontFloorY_M,...Array.from({length:5},(_,i)=>byId['MUD-STEP-'+i].localBounds[3]),d.gradeY_M];for(let i=1;i<stepTops.length;i++)near(stepTops[i-1]-stepTops[i],d.stairRiserM);assert(d.stairRiserM<7*.0254);near(d.stairTreadM,12*.0254);
 const oldFloor=walls.build(model.parts).components.find(p=>p.id==='SCHEM-FLOOR-SECTOR-2'),finishEdge=Math.max(...oldFloor.vertices.map(v=>r.local(v)[2]));near(byId['MUD-THRESHOLD-CAP'].localBounds[4],finishEdge);near(byId['MUD-THRESHOLD-CAP'].localBounds[3],0);near(byId['MUD-THRESHOLD-RISER'].localBounds[2],byId['MUD-FLOOR'].localBounds[2]);
 // TIMESTAMP START 2026-11-02T15:00:19-05:00 | REVISION R004797
 const rafters=r.components.filter(p=>/^MUD-RAFTER-[LR]-/.test(p.id));assert.equal(rafters.length,10);near(d.roofRafterDepthM,5.5*.0254);near(d.roofRafterWidthM,3.5*.0254);assert.equal(r.components.filter(p=>/^MUD-ROOF-TIE-/.test(p.id)).length,4);
 assert(rafters.every(p=>p.joineryBlank&&p.mudroomRoof));
 // TIMESTAMP END 2026-11-02T15:00:19-05:00 | REVISION R004797
 assert(r.components.filter(p=>p.mudroomScreen).some(p=>p.mudroomRole==='roof'));assert(r.components.filter(p=>/^MUD-BENCH-[LR]$/.test(p.id)).every(p=>!p.mudroomScreen));
 // TIMESTAMP START 2026-11-02T15:00:19-05:00 | REVISION R004797
 // TIMESTAMP START 2026-11-02T21:55:01-05:00 | REVISION R004881
 near(d.roofHighY_M,2.9745342078732953);near(d.roofPitch,1/3);assert(d.minimumInteriorRoofHeightM>2.1);assert(r.notes.some(s=>s.includes('not specified')));
 // TIMESTAMP END 2026-11-02T21:55:01-05:00 | REVISION R004881
 // TIMESTAMP END 2026-11-02T15:00:19-05:00 | REVISION R004797
 assert.equal(crypto.createHash('sha256').update(fs.readFileSync(path)).digest('hex'),crypto.createHash('sha256').update(before).digest('hex'));
}
console.log(`PASS: open covered porch, three variants, ${pairs} exact prism pair tests, closed solids, clear aisle, open grate/outlet, benches backed by railings and equal stairs.`);
// TIMESTAMP END 2026-11-02T14:21:43-05:00 | REVISION R004791

// TIMESTAMP END 2026-11-05T04:18:09+00:00 | REVISION R000020
