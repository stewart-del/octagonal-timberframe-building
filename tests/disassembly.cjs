// TIMESTAMP START 2026-11-02T15:57:59-05:00 | REVISION R004811
const assert=require('node:assert/strict'),D=require('../src/disassembly.js');
const plan={status:'PARTIAL',stages:[
 {id:'peg',label:'Withdraw locking peg',member_ids:['peg'],delta_m:[0,0,2]},
 {id:'tongue',label:'Slide tongue through its slot',member_ids:['beam'],delta_m:[2,0,0]},
 {id:'park',label:'Move released beam clear',member_ids:['beam'],delta_m:[0,3,0]},
 {id:'pair',label:'Release paired receivers together',motions:[{member_ids:['left'],delta_m:[-1,0,0]},{member_ids:['right'],delta_m:[1,0,0]}]}
],blocked:[{member_ids:['locked'],reason:'Closed opposing sockets'}],excluded:[]};
const api=D.create(plan,['peg','beam','left','right','locked']);
assert.deepEqual(api.offset('beam',.125),[0,0,0]);
assert.deepEqual(api.offset('peg',.125),[0,0,1]);
assert.deepEqual(api.offset('beam',.375),[1,0,0]);
assert.deepEqual(api.offset('beam',.625),[2,1.5,0]);
assert.deepEqual(api.offset('beam',1),[2,3,0]);
assert.deepEqual(api.offset('left',.875),[-.5,0,0]);
assert.deepEqual(api.offset('right',.875),[.5,0,0]);
assert.deepEqual(api.offset('locked',1),[0,0,0]);
assert.deepEqual(api.offset('beam',.375),[1,0,0]);
assert.deepEqual(api.offset('peg',0),[0,0,0]);
assert.equal(api.state(1).status,'PARTIAL');assert.equal(api.state(1).blocked.length,1);
assert.equal(api.next(0,1,id=>id==='beam'),.5);
assert.equal(api.next(.75,-1,id=>id==='beam'),.5);
assert.throws(()=>D.create({...plan,stages:[{member_ids:['missing'],delta_m:[0,1,0]}]},['beam']),/Unknown/);
assert.throws(()=>D.create({...plan,stages:[{motions:[{member_ids:['beam'],delta_m:[1,0,0]},{member_ids:['beam'],delta_m:[0,1,0]}]}]},['beam']),/repeated/);
assert.throws(()=>D.create({...plan,status:'FAILED'},[]),/verified/);
console.log('PASS: peg-first timing, slot withdrawal before lateral parking, coordinated motion, reversible playback, explicit locked pieces and visible-step navigation. Collision proofs belong to the source-bound plan audit.');
// TIMESTAMP END 2026-11-02T15:57:59-05:00 | REVISION R004811

// TIMESTAMP START 2026-11-03T07:02:34-05:00 | REVISION R004905
const columns=['PIER-0','PIER-0-BELOW'];
assert.throws(()=>D.create({status:'PASS',stages:[{id:'split',member_ids:['PIER-0-BELOW'],delta_m:[0,-.12,0]}]},columns),/continuous column/);
assert.throws(()=>D.create({status:'PASS',anchored_ids:['PIER-C'],stages:[{id:'anchor',member_ids:['PIER-C'],delta_m:[0,1,0]}]},['PIER-C']),/anchors/);
const rigid=D.create({status:'PASS',stages:[{id:'column',member_ids:columns,delta_m:[1,0,0]}]},columns);
for(const progress of [0,.1,.5,.9,1])assert.deepEqual(rigid.offset(columns[0],progress),rigid.offset(columns[1],progress));
console.log('PASS: one rigid column across its opaque and transparent rendering zones; fixed center anchors');
// TIMESTAMP END 2026-11-03T07:02:34-05:00 | REVISION R004905

// TIMESTAMP START 2026-11-03T11:58:59-05:00 | REVISION R004997
const saved=require('../src/disassembly-plan.json').variants['top-entry'];
const playback=D.create(saved,saved.physical_ids);
const isFinish=id=>id.startsWith('SCHEM-FLOOR-SECTOR-')||id.startsWith('FLOOR-BAMBOO-CENTER-');
const finishIds=saved.physical_ids.filter(isFinish);
assert.equal(finishIds.length,16);
assert.deepEqual(new Set(playback.stages[0].member_ids),new Set(finishIds));
const trussIds=new Set(Array.from({length:8},(_,k)=>['R'+k,'T'+k,'C'+k]).flat());
// TIMESTAMP START 2026-11-05T01:24:05+00:00 | REVISION R000013
// A disengaged member can travel again while arranging the compact layout.
// The fixture stays until every truss has cleared its installed joint.
const releases=saved.construction.release_stage_by_piece;
for(const id of trussIds)assert(playback.stages[releases[id]].member_ids.includes(id));
const lastTruss=Math.max(...[...trussIds].map(id=>releases[id]));
// TIMESTAMP END 2026-11-05T01:24:05+00:00 | REVISION R000013
const supportStart=playback.stages.findIndex(s=>s.member_ids.includes('M-TMP'));
assert.ok(supportStart>lastTruss,'The eight-L support must remain until every truss member is clear');
for(let i=0;i<=lastTruss;i++)assert.deepEqual(playback.offset('M-TMP',(i+.5)/playback.count),[0,0,0]);
const roofStart=playback.stages.findIndex(s=>s.member_ids.some(id=>id.startsWith('ROOF-')));
for(const id of finishIds){
 assert.equal(playback.offset(id,0)[1],0);
 assert.equal(playback.offset(id,roofStart/playback.count)[1],.05,
  'Bamboo must remain lifted while the roof covering is in place; reverse playback seats it last');
}
for(const id of saved.anchored_ids)assert.deepEqual(playback.offset(id,1),[0,0,0]);
console.log('PASS: bamboo seats after the roof in reverse playback; eight-L support precedes every truss');
// TIMESTAMP END 2026-11-03T11:58:59-05:00 | REVISION R004997
