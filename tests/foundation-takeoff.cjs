// TIMESTAMP START 2026-11-05T04:09:58+00:00 | REVISION R000018
'use strict';
const assert=require('node:assert/strict'),F=require('../src/floor-foundation.js'),P=require('../src/mudroom.js'),A=require('../src/foundation-takeoff.js');
// TIMESTAMP START 2026-11-05T08:49:48+00:00 | REVISION R000037
function reportRows(r){return 1+r.columns.length+r.pours.length+5+1;}
// TIMESTAMP END 2026-11-05T08:49:48+00:00 | REVISION R000037
for(const file of ['model-data.json','step-lap-proposed-model.json','top-entry-proposed-model.json']){
 const model=require('../src/'+file),f=F.build(model),porch=P.build(model),before=JSON.stringify({f,porch}),r=A.build(f,porch),ft=.3048;
 assert.equal(JSON.stringify({f,porch}),before);
 assert.equal(r.columns.length,21);assert.equal(r.tubeCount,17);
 assert.equal(new Set(r.columns.map(p=>p.id)).size,21);
 const expectedMain=17*Math.PI*(16/12)**2/4*8;
// TIMESTAMP START 2026-11-05T08:49:48+00:00 | REVISION R000037
 const expectedPorch=4*(10/12)**2*((-.3556)-f.piers[0].gradeY_M+6*ft)/ft;
// TIMESTAMP END 2026-11-05T08:49:48+00:00 | REVISION R000037
 assert(Math.abs(r.mainVolumeM3/ft**3-expectedMain)<1e-9);
 assert(Math.abs(r.porchVolumeM3/ft**3-expectedPorch)<1e-9);
 assert(Math.abs(r.orderVolumeM3-r.netVolumeM3*1.1)<1e-12);
 assert(Math.abs(r.totalTubeOffcutM-17*4*ft)<1e-12);
 assert(r.columns.every(p=>Math.abs(p.belowGradeM-6*ft)<1e-12));
 assert.equal(r.columns.filter(p=>p.shape==='rectangular').length,4);
 const actual=A.build(f,porch,{actualTubeDiameterM:15.75*.0254,allowance:.075});
 assert(Math.abs(actual.mainVolumeM3/r.mainVolumeM3-(15.75/16)**2)<1e-12);
 assert(Math.abs(actual.orderVolumeM3-actual.netVolumeM3*1.075)<1e-12);
 assert.throws(()=>A.build(f,porch,{tubeStockLengthM:7*ft}),/stock shorter/);
 const missing={...porch,components:porch.components.filter(p=>p.id!=='MUD-SUPPORT-L-BACK-BELOW')};
 assert.throws(()=>A.build(f,missing),/Missing continuous/);
// TIMESTAMP START 2026-11-05T08:49:48+00:00 | REVISION R000037
 assert.equal(r.pours.length,25);assert(r.pours.every(p=>!p.id.startsWith('MUD-THRESHOLD')));
 assert(r.panVolumeM3>0&&r.stairVolumeM3>0);
 assert(Math.abs(r.netVolumeM3-r.columnVolumeM3-r.panVolumeM3-r.stairVolumeM3)<1e-12);
 const pan=porch.components.find(p=>p.id==='MUD-FLOOR'),b=pan.localBounds;
 const topAtRear=-6*.0254,topAtFront=topAtRear-(b[5]-b[4])/48;
 const analyticPan=(b[1]-b[0])*(b[5]-b[4])*((topAtRear+topAtFront)/2-b[2]);
 assert(Math.abs(r.pours.find(p=>p.id===pan.id).netVolumeM3-analyticPan)<1e-12);
 const translated={...porch,components:porch.components.map(p=>({...p,vertices:p.vertices.map(v=>v.map((x,k)=>x+[31,-57,19][k]))}))};
 assert(Math.abs(A.build(f,translated).netVolumeM3-r.netVolumeM3)<1e-10);
 const reversed={...porch,components:porch.components.map(p=>p.id===pan.id?{...p,triangles:p.triangles.map(t=>[t[0],t[2],t[1]])}:p)};
 assert.throws(()=>A.build(f,reversed),/Invalid concrete occupied mesh/);
 assert.equal(A.csv(r).split('\r\n').length,reportRows(r));assert(!/NaN|undefined/.test(A.csv(r)));
// TIMESTAMP END 2026-11-05T08:49:48+00:00 | REVISION R000037
 console.log(file, A.quantity(r.netVolumeM3),'net;',A.quantity(r.orderVolumeM3),'with 10%');
}
console.log('PASS: actual continuous pier geometry, nominal/actual diameters, square porch forms, stock/offcuts, allowance, missing-zone rejection, CSV, no mutations.');
// TIMESTAMP END 2026-11-05T04:09:58+00:00 | REVISION R000018
