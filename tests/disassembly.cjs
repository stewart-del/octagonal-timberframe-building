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
