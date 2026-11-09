// TIMESTAMP START 2026-11-08T21:51:47-05:00 | REVISION R000001
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),zlib=require('node:zlib'),crypto=require('node:crypto'),vm=require('node:vm'),{spawnSync}=require('node:child_process');
const root=path.resolve(__dirname,'..'),dist=path.join(root,'dist');
const transport=require('../src/runtime-transport.js');
if(process.argv[2]==='digest'){
 const filename=process.argv[3],raw=zlib.gunzipSync(fs.readFileSync(filename));
 const value=filename.endsWith('.pack.gz')?transport.decode(raw):JSON.parse(raw.toString());
 console.log(crypto.createHash('sha256').update(JSON.stringify(value)).digest('hex'));
 process.exit(0);
}
const html=fs.readFileSync(path.join(dist,'index.html'),'utf8');
const manifest=JSON.parse(html.match(/<script[^>]*id="site-assets"[^>]*>([\s\S]*?)<\/script>/)[1]);
assert(html.indexOf('charset="utf-8"')<1024,'Early downloads preserve browser UTF-8 detection');
assert(html.indexOf('OctagonSiteLoader.configure(')<html.indexOf('<link rel="stylesheet"'),'Selected downloads begin before stylesheet blocking');
assert(html.indexOf('OctagonRuntimeTransport=')<html.indexOf('OctagonSiteLoader.configure('),'Lossless decoder precedes the loader');
assert.equal((html.match(/<script defer src=/g)||[]).length,1,'Viewer script executes once');
assert(!html.includes('id="model-data"'),'Page shell does not contain another copy of the model');
for(const file of [manifest.common,...Object.values(manifest.variants)])assert(file.endsWith('.pack.gz'));
const allAssets=[manifest.runtime,manifest.common,manifest.commonMesh,manifest.study,manifest.detail,...Object.values(manifest.variants),...Object.values(manifest.meshBuffers)].filter(Boolean);
for(const file of allAssets)assert(fs.existsSync(path.join(dist,file)),file);
const css=html.match(/<link rel="stylesheet" href="([^"]+)"/)[1];
const bytes=file=>fs.statSync(path.join(dist,file)).size;
const sizes=Object.fromEntries(Object.keys(manifest.variants).map(id=>[id,Buffer.byteLength(html)+[manifest.runtime,css,manifest.common,manifest.commonMesh,manifest.variants[id],manifest.meshBuffers[id]].reduce((total,file)=>total+bytes(file),0)]));

function digest(filename){const result=spawnSync(process.execPath,[__filename,'digest',filename],{encoding:'utf8',maxBuffer:1024*1024});assert.equal(result.status,0,result.stderr);return result.stdout.trim();}
const before=process.env.OCTAGON_BEFORE_DIRECTORY;
if(before){
 const priorHTML=fs.readFileSync(path.join(before,'live-before.html'),'utf8'),prior=JSON.parse(priorHTML.match(/<script[^>]*id="site-assets"[^>]*>([\s\S]*?)<\/script>/)[1]);
 for(const [name,oldFile,newFile]of [['common',prior.common,manifest.common],['top-entry',prior.variants['top-entry'],manifest.variants['top-entry']]]){
  assert.equal(digest(path.join(before,'before-assets',oldFile)),digest(path.join(dist,newFile)),'Every decoded value matches the previously published '+name+' payload');
 }
 const previous=JSON.parse(fs.readFileSync(path.join(before,'before-assets.json')));
 const oldSize=Buffer.byteLength(priorHTML)+previous.reduce((sum,item)=>sum+item.bytes,0);
 assert(sizes['top-entry']<oldSize*.85,'Default startup transfer shrinks by at least 15 percent');
 console.log(JSON.stringify({beforeBytes:oldSize,afterBytes:sizes['top-entry'],reductionPercent:100*(1-sizes['top-entry']/oldSize),decodedPublishedDataUnchanged:true}));
}

async function checkLoader(){
 // Synthetic binary fixtures exercise the actual loader without reloading the
 // entire 30,000-part scene for a promise/cache behavior test.
 const header=Buffer.from(JSON.stringify({schema:'octagon-mesh-transport-1',byteLength:0,value:{meshRanges:{},commonMeshRanges:{}}}));
 const padding=Buffer.alloc((-(4+header.length))&7,32),length=Buffer.alloc(4);length.writeUInt32LE(header.length+padding.length);
 const packed=Buffer.concat([length,header,padding]),calls=new Map();let failures=1;
 const context=vm.createContext({URL,Map,WeakMap,Promise,ArrayBuffer,Float32Array,Uint8Array,DataView,TextDecoder,Response,DecompressionStream,Number,Error,console,location:{href:'https://octagon.test/?model=proposed'},document:{getElementById:()=>null},fetch:async url=>{
  const name=new URL(url).pathname;calls.set(name,(calls.get(name)||0)+1);
  if(name.includes('retry')&&failures-- >0)return new Response(null,{status:503});
  return new Response(name.includes('.pack')?zlib.gzipSync(packed):new Uint8Array(0));
 }});
 vm.runInContext(fs.readFileSync(path.join(root,'src/runtime-transport.js'),'utf8')+'\n'+fs.readFileSync(path.join(root,'src/runtime-loader.js'),'utf8'),context);
 const api=context.OctagonSiteLoader,testManifest={common:'common.pack.gz',commonMesh:'common.bin',variants:{baseline:'baseline.pack.gz',proposed:'proposed.pack.gz','top-entry':'top.pack.gz'},meshBuffers:{proposed:'proposed.bin'},study:'study.pack.gz',detail:'detail.bin'};
 await api.configure(testManifest);assert.equal(calls.size,4);assert(!calls.has('/baseline.pack.gz'));assert(!calls.has('/top.pack.gz'));assert(!calls.has('/study.pack.gz'));assert(!calls.has('/detail.bin'));
 assert.strictEqual(api.loadJSON('common.pack.gz'),api.loadJSON('common.pack.gz'));await api.loadJSON('common.pack.gz');assert.equal(calls.get('/common.pack.gz'),1);
 await assert.rejects(api.loadJSON('retry.pack.gz'),/503/);await api.loadJSON('retry.pack.gz');assert.equal(calls.get('/retry.pack.gz'),2);
 console.log(JSON.stringify({pass:true,initialBytes:sizes,selectedModelRequests:4,optionalDataDeferred:true,concurrentReadsDeduplicated:true,failedRequestsRetry:true}));
}
checkLoader().catch(error=>{console.error(error);process.exitCode=1;});
// TIMESTAMP END 2026-11-08T21:51:47-05:00 | REVISION R000001
