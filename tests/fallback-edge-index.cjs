const fs=require('fs'),vm=require('vm'),assert=require('assert/strict'),{performance}=require('perf_hooks');
const source=fs.readFileSync('src/viewer.template.html','utf8');
const code=source.slice(source.indexOf('function fallbackSegmentIndex('),source.indexOf('function drawFallback()'));
const tools=require('../src/edge-measurements.js'),roof=require('../src/roof-coverings.js'),model=require('../src/top-entry-proposed-model.json');
const sub=(a,b)=>a.map((x,i)=>x-b[i]),add=(a,b)=>a.map((x,i)=>x+b[i]),mul=(a,s)=>a.map(x=>x*s),dot=(a,b)=>a.reduce((s,x,i)=>s+x*b[i],0),length=a=>Math.hypot(...a);
function harness(text){const context={fallbackFeatureCache:new Map(),featureEdges:tools.featureEdges,vsub:sub,vadd:add,vmul:mul,dot,length};vm.createContext(context);vm.runInContext(text,context);return context;}
const indexed=harness(code),legacy=harness(code.replace('cached.candidates(tri.map(i=>p.vertices[i]))','cached.segments'));
const parts=[...model.parts.filter(p=>['P0','R0','J0-0','C0'].includes(p.id)),...roof.build(model).components];
let tested=0,allPairs=0,candidatePairs=0,start=performance.now();
for(const p of parts){
 const raw=tools.featureEdges(p.vertices,p.triangles),segments=[];for(let i=0;i<raw.length;i+=12)segments.push([raw.slice(i,i+3),raw.slice(i+6,i+9)]);
 const query=indexed.fallbackSegmentIndex(segments);
 for(let i=0;i<p.triangles.length;i++){
  const tri=p.triangles[i];allPairs+=segments.length;candidatePairs+=query(tri.map(j=>p.vertices[j])).length;
  // Cover every timber triangle and distributed first/middle/last roof triangles.
  if(p.is_timber||i%Math.max(1,Math.floor(p.triangles.length/12))===0||i===p.triangles.length-1){
   assert.equal(JSON.stringify(indexed.fallbackFaceEdges(p,tri)),JSON.stringify(legacy.fallbackFaceEdges(p,tri)),p.id+':'+i);tested++;
  }
 }
}
// Conservative cell boundaries and huge diagonal spans retain valid candidates.
const special=[[[.25,0,0],[.25,1,0]],[[-100,-100,-100],[100,100,100]],[[.250002,0,0],[.250002,1,0]]];
const q=indexed.fallbackSegmentIndex(special);assert.equal(q([[.25,0,0],[.25,.5,0],[.25,0,.1]]).length,3);
assert.equal(q([[-100,-100,-100],[100,100,100],[100,-100,100]]).length,3);
assert(candidatePairs<allPairs*.1,'Spatial screening must substantially reduce checks without changing clipping');
console.log(JSON.stringify({status:'PASS',exactComparedTriangles:tested,allPairs,candidatePairs,reduction:allPairs/candidatePairs,elapsedMs:performance.now()-start,geometryUnchanged:true}));
