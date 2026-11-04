// TIMESTAMP START 2026-11-03T15:52:59-05:00 | REVISION R005041
const assert=require('node:assert/strict'),api=require('../src/motion-modes.js'),disassembly=require('../src/disassembly.js');
const plan={status:'PASS',anchored_ids:['hub'],stages:[
 {member_ids:['floor'],delta_m:[0,.05,0]},
 {member_ids:['roof'],delta_m:[0,.3,0]},
 {member_ids:['floor'],delta_m:[3,0,0]},
 {member_ids:['roof'],delta_m:[0,4,0]},
 {member_ids:['steel'],delta_m:[0,-.15,0]},
 {member_ids:['post'],delta_m:[1,0,0]}
]};
const ids=['hub','floor','roof','steel','post'],parts=ids.map((id,k)=>({id,center:[k,2,0]}));
const movement=disassembly.create(plan,ids),m=api.create(plan,movement,parts,{center:[0,1,0]});
// TIMESTAMP START 2026-11-03T16:49:21-05:00 | REVISION R005060
assert.equal(m.assemblyCount,6);assert(m.shown('post',0,'assembly'));assert(!m.shown('floor',.49,'assembly'));
assert.deepEqual(m.offset('floor',.5,'assembly'),[3,.05,0]);
assert.deepEqual(m.offset('steel',1/6,'assembly'),[0,-.15,0]);assert(!m.shown('roof',.3,'assembly'));
for(const id of ids)for(const progress of [0,.17,.5,.83,1])assert.deepEqual(m.offset(id,progress,'assembly'),movement.offset(id,1-progress),'Assembly must retain the independently checked path');
// TIMESTAMP END 2026-11-03T16:49:21-05:00 | REVISION R005060
for(const id of ids){assert.deepEqual(m.offset(id,1,'assembly'),[0,0,0]);assert(m.shown(id,1,'assembly'));assert.deepEqual(m.offset(id,.34,'disassembly'),movement.offset(id,.34));}
assert.deepEqual(m.offset('hub',1,'sphere'),[0,0,0]);assert.deepEqual(m.offset('post',1,'sphere'),[2.88,.72,0]);
// TIMESTAMP START 2026-11-03T16:49:21-05:00 | REVISION R005060
assert.equal(m.next(.25,1,'assembly'),2/6);assert.equal(m.next(.25,-1,'assembly'),1/6);
// TIMESTAMP END 2026-11-03T16:49:21-05:00 | REVISION R005060
const real=require('../src/disassembly-plan.json').variants['top-entry'],all=real.physical_ids;
const live=api.create(real,disassembly.create(real,all),all.map(id=>({id,center:[0,0,0]})));
const appearance=id=>live.assemblyStages.findIndex(s=>s.motions.some(m=>m.member_ids.includes(id)));
assert(appearance('M-TMP')<appearance('T0'),'Welded support must be present before a tie/truss');
const floorId=all.find(id=>id.startsWith('SCHEM-FLOOR-SECTOR-'));
// TIMESTAMP START 2026-11-03T16:49:21-05:00 | REVISION R005060
const seating=id=>live.assemblyStages.findLastIndex(s=>s.motions.some(m=>m.member_ids.includes(id)));
assert(seating(floorId)>seating('R0'),'Bamboo finish must seat after roof framing');
// TIMESTAMP END 2026-11-03T16:49:21-05:00 | REVISION R005060
for(const id of all){assert(live.shown(id,1,'assembly'));assert(live.offset(id,1,'assembly').every(x=>x===0));}
console.log('PASS: all three modes; appearance and certified insertion paths; fixed anchors; fixture before truss; bamboo seats after roof; complete final building');
// TIMESTAMP END 2026-11-03T15:52:59-05:00 | REVISION R005041
