// TIMESTAMP START 2026-11-03T13:59:01-05:00 | REVISION R005033
const assert=require('node:assert/strict');
const api=require('../src/joinery-dimensions.js');
const context={model:{tenon_schedule:[{id:'test',donor:'K0-C',receiver:'P0',projection_m:.0762,width_m:.0254,height_m:.0762,connector:{vertices:[[0,0,0],[.0762,.0254,.0762]]},insertion_direction:[1,0,0]}]}};
const [tenon]=api.entries('K0-C',context);
assert(Math.abs(tenon.depthIn-3)<1e-10);assert(Math.abs(tenon.measuredDepthIn-3)<1e-10);assert.equal(tenon.widthIn,1);assert(Math.abs(tenon.heightIn-3)<1e-10);
assert.deepEqual(api.entries('P0',context),[],'Receiving mortises must not be mislabeled as that post’s projecting tenons');
console.log('PASS: selected-piece tenons distinguish donor and receiver and expose exact modeled dimensions');
// TIMESTAMP END 2026-11-03T13:59:01-05:00 | REVISION R005033

// TIMESTAMP START 2026-11-04T19:33:21+00:00 | REVISION R000014
for(const filename of ['model-data.json','step-lap-proposed-model.json','top-entry-proposed-model.json']){
 const model=require('../src/'+filename),byId=new Map(model.parts.map(p=>[p.id,p]));
 for(let k=0;k<8;k++){
  for(const suffix of ['A','B','C']){
   const p=byId.get('K'+k+'-'+suffix),stock=api.blank(p),expected=suffix==='C'?56.59539344318516:48.03099242694665;
   assert(Math.abs(stock.minimumLengthIn-expected)<1e-6);
   assert.equal(stock.quarterInchLengthIn,suffix==='C'?56.75:48.25);
   assert(Math.abs(stock.widthIn-2)<1e-7&&Math.abs(stock.depthIn-6)<1e-7);
   assert.equal(api.entries(p.id,{model}).length,2);
   for(const row of api.entries(p.id,{model}))assert(Math.abs(row.measuredDepthIn-3)<1e-6);
  }
  assert.equal(byId.get('K'+k+'-C').axis_start[1]/.0254,44);
 }
 for(const p of model.parts.filter(p=>p.is_timber)){
  const stock=api.blank(p);assert(stock&&stock.quarterInchLengthIn+.000001>=stock.minimumLengthIn,p.id+' tenon tip omitted from blank');
  const axis=p.stock_frame.axis,norm=Math.hypot(...axis),q=p.vertices.map(v=>v.reduce((sum,x,i)=>sum+x*axis[i]/norm,0));
  assert(Math.abs(stock.minimumLengthIn-(Math.max(...q)-Math.min(...q))/.0254)<1e-7);
 }
 const nodes=[],doc={createElement:tag=>({tag,children:[],appendChild(n){this.children.push(n)},append(...items){this.children.push(...items)}})},host={appendChild:n=>nodes.push(n)};
 api.render(host,'K0-C',{model},doc);const text=JSON.stringify(nodes);
 assert(text.includes('56.595')&&text.includes('56.75 in')&&text.includes('tenons included'));
}
assert.equal(api.blank({vertices:[[0,0,0]]}),null,'Unknown stock frame must not invent a blank');
console.log('PASS: all three variants; every timber blank encloses actual mesh; 48.25 in outer and 56.75 in inward 2x6 braces include both three-inch tenons; inspector shows actual stock length');
// TIMESTAMP END 2026-11-04T19:33:21+00:00 | REVISION R000014
