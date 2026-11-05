// TIMESTAMP START 2026-11-04T23:48:03+00:00 | REVISION R000012
// TIMESTAMP START 2026-11-04T23:23:25+00:00 | REVISION R000011
// TIMESTAMP START 2026-11-04T20:33:26+00:00 | REVISION R000023
// TIMESTAMP START 2026-11-04T19:27:13+00:00 | REVISION R000001
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
// TIMESTAMP START 2026-11-04T19:29:44+00:00 | REVISION R000002
const zlib=require('node:zlib');
const readJSON=filename=>JSON.parse(zlib.gunzipSync(fs.readFileSync(filename)));
// TIMESTAMP END 2026-11-04T19:29:44+00:00 | REVISION R000002
const root=path.resolve(__dirname,'..'),dist=path.join(root,'dist');
const html=fs.readFileSync(path.join(dist,'index.html'),'utf8');
const manifest=JSON.parse(html.match(/<script[^>]*id="site-assets"[^>]*>([\s\S]*?)<\/script>/)[1]);
const loader=fs.readFileSync(path.join(root,'src/runtime-loader.js'),'utf8');
const bytes=p=>fs.statSync(path.join(dist,p)).size;
assert(Buffer.byteLength(html)<50000,'The page shell stays below 50 kB');
assert(!html.includes('id="model-data"'),'The shell must not embed a second model');
assert.equal((html.match(/<script defer src=/g)||[]).length,1,'The shared runtime loads once');
assert(fs.readFileSync(path.join(dist,'_headers'),'utf8').includes('max-age=31536000, immutable'));
for(const filename of [manifest.common,manifest.study,manifest.runtime,...Object.values(manifest.variants)])assert(fs.existsSync(path.join(dist,filename)));

async function check(search,expected){
 const calls=new Map(),errors=[],status={textContent:''};let failNext=false;
 const context=vm.createContext({URL,Map,Promise,Float32Array,Uint8Array,Response,DecompressionStream,Number,Error,console:{error:e=>errors.push(e)},location:{href:'https://model.test/'+search},
  document:{getElementById:()=>status},fetch:async url=>{
   const relative=new URL(url).pathname.slice(1);calls.set(relative,(calls.get(relative)||0)+1);
   if(failNext){failNext=false;return new Response(null,{status:503});}
   const data=fs.readFileSync(path.join(dist,relative));
   return new Response(data);
  }});
 vm.runInContext(loader,context);
 const api=context.OctagonSiteLoader,data=await api.configure(manifest);
 assert.deepEqual(Object.keys(data.variants),[expected]);
 assert.deepEqual(Object.keys(data.wallJoinery.variants),[expected]);
 assert.deepEqual(Object.keys(data.disassembly.variants),[expected]);
 assert.equal(data.variants[expected].sha256,data.wallJoinery.variants[expected].source_model_sha256);
 assert(!calls.has(manifest.study),'Earlier study waits until requested');
 assert.equal(calls.size,3,'Startup fetches shared data, one model and its drawing edges');
 const first=api.loadJSON(manifest.common),second=api.loadJSON(manifest.common);
 assert.strictEqual(first,second,'Concurrent readers share the same promise');
 assert.strictEqual(await first,await second,'The JSON is parsed once');
 assert.equal(calls.get(manifest.common),1);
 const lazy=api.loadJSON(manifest.study);assert.strictEqual(lazy,api.loadJSON(manifest.study));await lazy;
 assert.equal(calls.get(manifest.study),1);
 const shared=readJSON(path.join(dist,manifest.common));
 assert.deepEqual(JSON.parse(JSON.stringify(data.foundation)),shared.foundation);
 // TIMESTAMP START 2026-11-04T19:29:44+00:00 | REVISION R000002
 require('../src/edge-measurements.js');
 const joinery=require('../src/wall-joinery.js');
 const fitted=joinery.applyModel(data.variants[expected].model,data.wallJoinery.variants[expected]);
 for(const id of ['P0','K0-A','R0']){
  const part=fitted.parts.find(p=>p.id===id),cached=data.meshCache.get(id);
  const current=new Float32Array(TimberEdgeMeasurements.featureEdges(part.vertices,part.triangles));
  assert.deepEqual(Array.from(cached),Array.from(current),'Cached GPU edges match the current algorithm exactly: '+id);
 }
 // TIMESTAMP START 2026-11-04T19:48:56+00:00 | REVISION R000004
 assert(data.disassembly.variants[expected].physical_ids.every(id=>data.meshCache.has(id)),'Every physical piece has its matching drawing-edge cache');
 // TIMESTAMP END 2026-11-04T19:48:56+00:00 | REVISION R000004
 // TIMESTAMP START 2026-11-04T23:37:08+00:00 | REVISION R000031
 const sheets=data.foundation.parts.filter(p=>p.floorRole==='underlayment_sheet');
 assert.equal(sheets.length,28,'The runtime must load every installed cut sheet');
 assert(!data.meshCache.has('FLOOR-SUBFLOOR'),'The obsolete single floor slab must be absent');
 for(const sheet of sheets){
  const current=new Float32Array(TimberEdgeMeasurements.featureEdges(sheet.vertices,sheet.triangles));
  assert.deepEqual(Array.from(data.meshCache.get(sheet.id)),Array.from(current),'Exact cached sheet edges: '+sheet.id);
 }
 assert.equal(data.meshCache.size,expected==='top-entry'?1295:1287);
 // TIMESTAMP END 2026-11-04T23:37:08+00:00 | REVISION R000031
 // TIMESTAMP END 2026-11-04T19:29:44+00:00 | REVISION R000002
 failNext=true;
 const retryURL=manifest.study+'?retry-test';
 await assert.rejects(api.loadJSON(retryURL),/503/);
 await api.loadJSON(retryURL);
 assert.equal(calls.get(manifest.study),3,'A failed request is evicted so a retry can succeed');
 assert.equal(errors.length,0);
 return {id:expected,initialBytes:Buffer.byteLength(html)+bytes(manifest.common)+bytes(manifest.runtime)+bytes(manifest.variants[expected])+bytes(manifest.meshBuffers[expected]),parts:data.meshCache.size};
}
(async()=>{
 const results=[];
 for(const [search,id] of [['','top-entry'],['?model=baseline','baseline'],['?model=proposed','proposed'],['?model=invalid','top-entry']])results.push(await check(search,id));
 const before=fs.statSync(path.join(root,'index.html')).size;
 for(const result of results)assert(result.initialBytes<before*.5,'Startup payload stays under half of the offline export');
 console.log(JSON.stringify({pass:true,results,checks:'selected data only; concurrent and repeated loads deduplicated; failed loads retry; exact cached drawing edges'}));
})().catch(error=>{console.error(error);process.exitCode=1;});
// TIMESTAMP END 2026-11-04T19:27:13+00:00 | REVISION R000001
// TIMESTAMP END 2026-11-04T20:33:26+00:00 | REVISION R000023

// TIMESTAMP END 2026-11-04T23:23:25+00:00 | REVISION R000011

// TIMESTAMP END 2026-11-04T23:48:03+00:00 | REVISION R000012
