// TIMESTAMP START 2026-11-05T13:07:26+00:00 | REVISION R000043
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const source=fs.readFileSync(path.join(__dirname,'../src/runtime-loader.js'),'utf8');
function detail(){const header=Buffer.from(JSON.stringify({schema:'octagon-occupied-detail-1',parts:{commonWood:{vertices:[[9,8,7]],triangles:[]}},meshRanges:{commonWood:[0,6]}})),padding=Buffer.alloc((-header.length)&3,32),size=Buffer.alloc(4);size.writeUInt32LE(header.length+padding.length);return Buffer.concat([size,header,padding,Buffer.from(new Float32Array([9,8,7,6,5,4]).buffer)]);}
async function run(){
 const calls=new Map(),manifest={common:'common.json',commonMesh:'common-edges.bin',variants:{'top-entry':'top.json',proposed:'proposed.json'},meshBuffers:{'top-entry':'top.bin',proposed:'proposed.bin'},detail:'detail.bin'},location={href:'https://viewer.test/'};
 const context=vm.createContext({URL,Map,Promise,Float32Array,Uint8Array,DataView,TextDecoder,Response,DecompressionStream,Number,Error,console,location,document:{getElementById:()=>null},fetch:async url=>{
  const name=new URL(url).pathname.slice(1);calls.set(name,(calls.get(name)||0)+1);
  if(name==='detail.bin')return new Response(detail());
  if(name.endsWith('.bin'))return new Response(new Float32Array(name==='common-edges.bin'?[1,2,3,4,5,6]:name==='proposed.bin'?[11,12,13,14,15,16]:[21,22,23,24,25,26]));
  if(name==='common.json')return new Response(JSON.stringify({foundation:{parts:[]},commonMeshRanges:{commonWood:[0,6]}}));
  return new Response(JSON.stringify({meshRanges:{primary:[0,6]},variants:{[name==='top.json'?'top-entry':'proposed']:{}}}));
 }});
 vm.runInContext(source,context);const api=context.OctagonSiteLoader,first=await api.configure(manifest);assert.equal(calls.size,4);assert.equal(first.meshCache.size,2);
 location.href='https://viewer.test/?model=proposed';const second=await api.configure(manifest);assert.strictEqual(first.meshCache.get('commonWood'),second.meshCache.get('commonWood'),'Common decoded drawing buffers are reused');assert.notStrictEqual(first.meshCache.get('primary'),second.meshCache.get('primary'));
 const occupied=await api.ensureDetail();location.href='https://viewer.test/';const third=await api.configure(manifest);assert.strictEqual(third.meshCache.get('commonWood'),occupied.meshCache.get('commonWood'),'Returning models retain the upgraded occupied-detail edges');assert.strictEqual(await api.ensureDetail(),occupied,'One decoded detail bundle across model changes');
 for(const count of calls.values())assert.equal(count,1);assert.equal(calls.size,7);assert.equal(api.detailReady,true);
 console.log(JSON.stringify({pass:true,initialRequests:4,sharedDataDownloads:1,sharedEdgeDownloads:1,decodedSharedBuffersReused:true,selectedEdgesIndependent:true,detailDownloadsAndDecodes:1,returnToPriorModelAdditionalRequests:0}));
}
run().catch(error=>{console.error(error);process.exitCode=1;});
// TIMESTAMP END 2026-11-05T13:07:26+00:00 | REVISION R000043
