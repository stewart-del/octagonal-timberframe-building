// TIMESTAMP START 2026-11-05T04:18:09+00:00 | REVISION R000020
'use strict';
const assert=require('node:assert/strict'),M=require('../src/mudroom.js'),model=require('../src/top-entry-proposed-model.json'),fit=require('../src/mudroom-joinery-fit.json'),raw=M.build(model,{applyJoinery:false}),I=.0254;
const near=(a,b)=>assert(Math.abs(a-b)<1e-9,`${a} != ${b}`),byId=new Map(raw.components.map(p=>[p.id,p]));
for(const side of ['L','R']){
 const post=byId.get('MUD-POST-'+side+'-FRONT'),sideRail=byId.get('MUD-GUARD-TOP-'+side),frontRail=byId.get('MUD-FRONT-GUARD-'+side),b=post.localBounds;
 near(sideRail.localBounds[0],b[0]);near(sideRail.localBounds[1],b[1]);
 near(frontRail.localBounds[4],b[4]);near(frontRail.localBounds[5],b[5]);
 near(sideRail.localBounds[3],frontRail.localBounds[3]);
 const joints=fit.joints.filter(j=>j.receiver===post.id&&[sideRail.id,frontRail.id].includes(j.donor));
 assert.equal(joints.length,2);
 const ranges=joints.map(j=>{const points=j.connector.vertices.map(raw.local),ys=points.map(v=>v[1]);return [Math.min(...ys),Math.max(...ys)];}).sort((a,b)=>a[0]-b[0]);
 near(ranges[1][0]-ranges[0][1],.75*I);
 for(const j of joints){assert(j.peg_id);near(j.tenon_projection_m,3*I);}
}
const pickets=raw.components.filter(p=>/^MUD-(GUARD-PICKET|FRONT-PICKET)-/.test(p.id));
assert.equal(pickets.length,50);
for(const p of pickets){
 const b=p.localBounds;near(b[1]-b[0],1.5*I);near(b[5]-b[4],1.5*I);
 const joints=fit.joints.filter(j=>j.donor===p.id);assert.equal(joints.length,2);
 for(const j of joints){near(j.tenon_projection_m,I);const ys=j.connector.vertices.map(v=>{const q=raw.local(v);return q[1]-(j.insertion_direction_local[1]<0?raw.floorHeight(q[2]):0);});near(Math.max(...ys)-Math.min(...ys),I);}
}
console.log('PASS: flush perpendicular porch rail bodies, common top datum, internal mortise web, transverse pegs, 50 square pickets with actual one-inch tongues.');
// TIMESTAMP END 2026-11-05T04:18:09+00:00 | REVISION R000020
