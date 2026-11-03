// TIMESTAMP START 2026-11-02T20:27:45-05:00 | REVISION R004866
const assert=require('node:assert/strict'),A=require('../src/floor-foundation.js'),m=require('../src/model-data.json'),snapshot=JSON.stringify(m),r=A.build(m);
assert.equal(JSON.stringify(m),snapshot);assert.equal(r.piers.length,9);assert.equal(r.members.filter(p=>p.kind==='beam').length,8);assert.equal(r.members.filter(p=>p.kind==='joist').length,21);assert.equal(r.distances.length,36);assert(r.piers.every(p=>Math.abs(p.embedDepthM-1.8288)<1e-10&&Math.abs(p.topY_M-p.gradeY_M-.6096)<1e-10));assert(!r.grate.active);
for(let k=0;k<8;k++){const p=m.parts.find(p=>p.id==='P'+k);assert.equal(r.piers[k].centerM[0],p.center[0]);assert.equal(r.piers[k].centerM[2],p.center[2]);const q=r.piers[(k+4)%8];assert(Math.hypot(r.piers[k].localX_M+q.localX_M,r.piers[k].localZ_M+q.localZ_M)<1e-8);}
const moved=JSON.parse(snapshot);moved.parts.find(p=>p.id==='P0').center[0]+=.1;assert.notEqual(A.build(moved).distances[0].lengthM,r.distances[0].lengthM);assert(A.settingOutSVG(r).includes('6ft below-grade'));assert(!/NaN|undefined/.test(A.settingOutSVG(r)));console.log('PASS:9actualcenterlines,36distances,symmetry,selectedmeshchange,no mutations,sixfootembedment,deferredgrate');

assert.equal(r.bearingStands.length,8);assert(r.bearingStands.every(s=>s.bottomY_M===r.piers[0].topY_M&&s.topY_M===0&&s.clearBeamWidthM>.14));

// TIMESTAMP START 2026-11-02T20:27:45-05:00 | REVISION R004866
for(const j of r.members.filter(p=>p.kind==='joist')){
 assert.equal(j.widthM,2*.0254);assert.equal(j.depthM,6*.0254);
 const dx=j.endM[0]-j.startM[0],dz=j.endM[2]-j.startM[2];assert(Math.abs(dx*r.joistDirectionM[2]-dz*r.joistDirectionM[0])<1e-9);
}
const solids=require('../src/floor-foundation-solids.json').parts;
for(const pier of r.piers){const below=solids.find(p=>p.id===pier.id+'-BELOW');assert(below.underground&&below.displayOpacity>0&&below.displayOpacity<1);const ys=below.vertices.map(v=>v[1]);assert(Math.abs(Math.max(...ys)-pier.gradeY_M)<1e-9);assert(Math.abs(Math.max(...ys)-Math.min(...ys)-6*.3048)<1e-9);}
// TIMESTAMP END 2026-11-02T20:27:45-05:00 | REVISION R004866
// TIMESTAMP END 2026-11-02T20:27:45-05:00 | REVISION R004866
