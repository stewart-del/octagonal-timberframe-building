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
// TIMESTAMP START 2026-11-04T20:00:49+00:00 | REVISION R000006
const focused={...plan,construction:{release_stage_by_piece:{floor:0,roof:1,steel:4,post:5}}};
const focusedMotion=api.create(focused,disassembly.create(focused,ids),parts);
assert.equal(focusedMotion.assemblyCount,4,'Omit only motions of hidden parts');
assert(focusedMotion.offset('floor',.75,'assembly').every((x,k)=>Math.abs(x-[0,.05,0][k])<1e-12));
assert(!focusedMotion.shown('floor',.749,'assembly'));assert(focusedMotion.shown('floor',.75,'assembly'));
assert.deepEqual(focusedMotion.offset('floor',1,'assembly'),[0,0,0]);
// TIMESTAMP END 2026-11-04T20:00:49+00:00 | REVISION R000006
const real=require('../src/disassembly-plan.json').variants['top-entry'],all=real.physical_ids;
const live=api.create(real,disassembly.create(real,all),all.map(id=>({id,center:[0,0,0]})));
// TIMESTAMP START 2026-11-04T20:00:49+00:00 | REVISION R000006
const appearance=id=>real.construction?.release_stage_by_piece[id]!==undefined?live.assemblyStages.findIndex(s=>s.source_stage_index===real.construction.release_stage_by_piece[id]):live.assemblyStages.findIndex(s=>s.motions.some(m=>m.member_ids.includes(id)));
// TIMESTAMP END 2026-11-04T20:00:49+00:00 | REVISION R000006
assert(appearance('M-TMP')<appearance('T0'),'Welded support must be present before a tie/truss');
const floorId=all.find(id=>id.startsWith('SCHEM-FLOOR-SECTOR-'));
// TIMESTAMP START 2026-11-03T16:49:21-05:00 | REVISION R005060
const seating=id=>live.assemblyStages.findLastIndex(s=>s.motions.some(m=>m.member_ids.includes(id)));
assert(seating(floorId)>seating('R0'),'Bamboo finish must seat after roof framing');
// TIMESTAMP END 2026-11-03T16:49:21-05:00 | REVISION R005060
for(const id of all){assert(live.shown(id,1,'assembly'));assert(live.offset(id,1,'assembly').every(x=>x===0));}
// TIMESTAMP START 2026-11-04T20:00:49+00:00 | REVISION R000006
if(real.construction){
 const phases=real.construction.reverse_phases,N=live.assemblyCount;
 for(const id of all){
  const i=appearance(id);if(i<0||real.anchored_ids.includes(id))continue;
  assert(live.shown(id,(i+.01)/N,'assembly'),id+' must appear at installation');
  if(i>0)assert(!live.shown(id,(i-.01)/N,'assembly'),id+' must stay hidden during off-site preparation');
 }
 assert(appearance('PIER-0')<appearance('FLOOR-BEAM-0'));
 assert(appearance('FLOOR-BEAM-0')<appearance('FLOOR-SUBFLOOR-01'));
 assert(appearance('FLOOR-SUBFLOOR-01')<appearance('P0'));
 assert(appearance('P0')<appearance('T0'));
 assert(appearance('T0')<appearance('R0'));
 assert(appearance('R0')<appearance('MUD-POST-L-BACK'));
 const wall=all.find(id=>id.startsWith('SCHEM-N-infill-'));
 assert(appearance('MUD-POST-L-BACK')<appearance(wall));
 assert(appearance(wall)<appearance('SCHEM-CUP-WINDOW-0-left'));
 assert(appearance('SCHEM-CUP-WINDOW-0-left')<appearance(floorId));
 assert.equal(live.phaseAt((appearance('FLOOR-SUBFLOOR-01')+.5)/N,'assembly'),'4 × 8 underlayment sheets');
 assert(N<real.stages.length,'Hidden preparation should consume no animation time');
 const certified=disassembly.create(real,all);
 for(let i=0;i<N;i++){
  const raw=live.assemblyStages[i].source_stage_index;
  for(const id of all.filter((_,k)=>k%97===0))assert(live.offset(id,(i+.5)/N,'assembly').every((x,k)=>Math.abs(x-certified.offset(id,(raw+.5)/real.stages.length)[k])<1e-10),'Visible motion must use the exact certified segment');
 }
 for(let i=1;i<N;i++){
  const before=(i-1e-7)/N,after=i/N;
  for(const id of all)if(live.shown(id,before,'assembly')&&live.shown(id,after,'assembly')){
   const a=live.offset(id,before,'assembly'),b=live.offset(id,after,'assembly');
   assert(a.every((x,k)=>Math.abs(x-b[k])<1e-5),id+' cannot jump when hidden preparation time is skipped');
  }
 }
 assert.equal(live.phaseAt(.4,'sphere'),'');
}
// TIMESTAMP END 2026-11-04T20:00:49+00:00 | REVISION R000006
console.log('PASS: all three modes; appearance and certified insertion paths; fixed anchors; fixture before truss; bamboo seats after roof; complete final building');
// TIMESTAMP END 2026-11-03T15:52:59-05:00 | REVISION R005041
