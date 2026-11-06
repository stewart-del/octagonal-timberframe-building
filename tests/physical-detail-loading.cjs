// TIMESTAMP START 2026-11-05T06:13:38+00:00 | REVISION R000027
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),zlib=require('node:zlib');
const loader=fs.readFileSync(path.join(__dirname,'../src/runtime-loader.js'),'utf8');
function bundle({badRange=false,badSchema=false}={}){
 const data={schema:badSchema?'incorrect':'octagon-occupied-detail-1',parts:{wood:{vertices:[[1,2,3],[4,5,6],[7,8,9]],triangles:[[0,1,2]]}},meshRanges:{wood:[0,badRange?12:6]}};
 let header=Buffer.from(JSON.stringify(data));header=Buffer.concat([header,Buffer.alloc((-header.length)&3,32)]);
 const size=Buffer.alloc(4);size.writeUInt32LE(header.length);return zlib.gzipSync(Buffer.concat([size,header,Buffer.from(new Float32Array([1,2,3,4,5,6]).buffer)]));
}
async function run(){
 const manifest={common:'common.json',variants:{'top-entry':'top.json'},meshBuffers:{'top-entry':'edges.bin'},detail:'detail.bin.gz'},calls=new Map();let fail=false,detail=bundle();
 const context=vm.createContext({URL,Map,Promise,Float32Array,Uint8Array,DataView,TextDecoder,Response,DecompressionStream,Number,Error,console,location:{href:'https://viewer.test/'},document:{getElementById:()=>null},fetch:async url=>{
  const name=new URL(url).pathname.slice(1);calls.set(name,(calls.get(name)||0)+1);
  if(name===manifest.detail){if(fail){fail=false;return new Response(null,{status:503});}return new Response(detail);}
  return new Response(name==='edges.bin'?new Uint8Array(0):JSON.stringify(name==='top.json'?{variants:{'top-entry':{}},meshRanges:{}}:{foundation:{parts:[]}}));
 }});
 vm.runInContext(loader,context);const api=context.OctagonSiteLoader;await api.configure(manifest);
 assert.equal(calls.size,3);assert(!calls.has(manifest.detail),'Concealed occupied geometry must not load during startup');
 fail=true;await assert.rejects(api.ensureDetail(),/503/);assert.equal(api.detailReady,false);
 const a=api.ensureDetail(),b=api.ensureDetail();assert.strictEqual(a,b,'Concurrent motion and inspection share one detail promise');
 const value=await a;assert.strictEqual(value,await b);assert.equal(api.detailReady,true);assert.strictEqual(await api.ensureDetail(),value);
 assert.deepEqual(JSON.parse(JSON.stringify(value.parts.wood.vertices)),[[1,2,3],[4,5,6],[7,8,9]]);
 assert.deepEqual(Array.from(value.meshCache.get('wood')),[1,2,3,0,1,0,4,5,6,0,1,0]);assert.equal(calls.get(manifest.detail),2,'One failed attempt and one successful detail download');
 for(const fixture of [{badRange:true},{badSchema:true}]){
  detail=bundle(fixture);await api.configure({...manifest,detail:'detail.bin.gz?'+JSON.stringify(fixture)});await assert.rejects(api.ensureDetail(),/Invalid drawing-edge cache|Unknown occupied-mesh detail format/);
 }
 console.log(JSON.stringify({pass:true,startupRequests:3,successfulDetailRequests:1,concurrentAndRepeatedReadsDeduplicated:true,failedRequestRetry:true,exactOccupiedArraysAndEdges:true,malformedDetailsRejected:true}));
}
run().catch(e=>{console.error(e);process.exitCode=1;});
// TIMESTAMP END 2026-11-05T06:13:38+00:00 | REVISION R000027
