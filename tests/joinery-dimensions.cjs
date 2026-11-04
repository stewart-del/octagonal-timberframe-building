// TIMESTAMP START 2026-11-03T13:59:01-05:00 | REVISION R005033
const assert=require('node:assert/strict');
const api=require('../src/joinery-dimensions.js');
const context={model:{tenon_schedule:[{id:'test',donor:'K0-C',receiver:'P0',projection_m:.0762,width_m:.0254,height_m:.0762,connector:{vertices:[[0,0,0],[.0762,.0254,.0762]]},insertion_direction:[1,0,0]}]}};
const [tenon]=api.entries('K0-C',context);
assert(Math.abs(tenon.depthIn-3)<1e-10);assert(Math.abs(tenon.measuredDepthIn-3)<1e-10);assert.equal(tenon.widthIn,1);assert(Math.abs(tenon.heightIn-3)<1e-10);
assert.deepEqual(api.entries('P0',context),[],'Receiving mortises must not be mislabeled as that post’s projecting tenons');
console.log('PASS: selected-piece tenons distinguish donor and receiver and expose exact modeled dimensions');
// TIMESTAMP END 2026-11-03T13:59:01-05:00 | REVISION R005033
