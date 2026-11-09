// TIMESTAMP START 2026-11-04T23:23:25+00:00 | REVISION R000011
// TIMESTAMP START 2026-11-04T20:33:26+00:00 | REVISION R000023
// TIMESTAMP START 2026-11-04T19:27:13+00:00 | REVISION R000001
(function(root){
'use strict';
// TIMESTAMP START 2026-11-05T13:07:26+00:00 | REVISION R000043
const pending=new Map(),decodedEdges=new WeakMap(),detailBundles=new Map();
// TIMESTAMP END 2026-11-05T13:07:26+00:00 | REVISION R000043
function resource(path,type){
 const url=new URL(path,root.location.href).href,key=type+':'+url;
 if(!pending.has(key)){
  // TIMESTAMP START 2026-11-04T19:29:44+00:00 | REVISION R000002
  const request=fetch(url,{cache:'force-cache'}).then(async response=>{
   if(!response.ok)throw Error('Could not load model data ('+response.status+')');
   if(new URL(url).pathname.endsWith('.gz')){
    const buffer=await response.arrayBuffer(),magic=new Uint8Array(buffer);
    response=new Response(buffer);
    if(magic[0]===31&&magic[1]===139)response=new Response(response.body.pipeThrough(new DecompressionStream('gzip')));
   }
   // TIMESTAMP START 2026-11-08T21:51:47-05:00 | REVISION R000001
   if(type==='json'&&new URL(url).pathname.endsWith('.pack.gz'))return root.OctagonRuntimeTransport.decode(await response.arrayBuffer());
   return type==='json'?response.json():response.arrayBuffer();
   // TIMESTAMP END 2026-11-08T21:51:47-05:00 | REVISION R000001
  }).catch(error=>{pending.delete(key);throw error;});
  // TIMESTAMP END 2026-11-04T19:29:44+00:00 | REVISION R000002
  pending.set(key,request);
 }
 return pending.get(key);
}
function showError(error){
 const node=root.document.getElementById('parameterStatus');
 if(node)node.textContent='The model could not load. Reload to try again. '+error.message;
 root.console.error(error);
}
function configure(manifest){
 api.manifest=manifest;
 // TIMESTAMP START 2026-11-05T06:13:38+00:00 | REVISION R000027
// TIMESTAMP START 2026-11-05T13:07:26+00:00 | REVISION R000043
 api.detailReady=!manifest.detail;api.detailPromise=detailBundles.get(manifest.detail)||null;
// TIMESTAMP END 2026-11-05T13:07:26+00:00 | REVISION R000043
 // TIMESTAMP END 2026-11-05T06:13:38+00:00 | REVISION R000027
 const requested=new URL(root.location.href).searchParams.get('model');
 const id=requested==='baseline'||requested==='proposed'?requested:'top-entry';
 // TIMESTAMP START 2026-11-04T19:29:44+00:00 | REVISION R000002
// TIMESTAMP START 2026-11-05T13:07:26+00:00 | REVISION R000043
 api.data=Promise.all([resource(manifest.common,'json'),resource(manifest.variants[id],'json'),resource(manifest.meshBuffers[id],'buffer'),manifest.commonMesh?resource(manifest.commonMesh,'buffer'):null]).then(async([common,selected,buffer,sharedBuffer])=>{
  const shared=sharedBuffer?edgeCache(new Float32Array(sharedBuffer),common.commonMeshRanges):new Map();
  const meshCache=new Map([...shared,...edgeCache(new Float32Array(buffer),selected.meshRanges)]);
  if(api.detailPromise){const detail=await api.detailPromise;for(const [key,value]of detail.meshCache)meshCache.set(key,value);api.detailReady=true;}
  return {...common,...selected,meshCache};
 });
// TIMESTAMP END 2026-11-05T13:07:26+00:00 | REVISION R000043
 // TIMESTAMP END 2026-11-04T19:29:44+00:00 | REVISION R000002
 api.data.catch(showError);
 return api.data;
}
// TIMESTAMP START 2026-11-05T06:13:38+00:00 | REVISION R000027
function edgeCache(values,ranges){
// TIMESTAMP START 2026-11-05T13:07:26+00:00 | REVISION R000043
 const cached=decodedEdges.get(ranges);if(cached?.buffer===values.buffer&&cached.byteOffset===values.byteOffset&&cached.length===values.length)return cached.cache;
 const cache=new Map();
// TIMESTAMP END 2026-11-05T13:07:26+00:00 | REVISION R000043
 for(const [part,[offset,length]] of Object.entries(ranges)){
  if(!Number.isInteger(offset)||!Number.isInteger(length)||offset<0||length<0||offset+length>values.length||length%6)throw Error('Invalid drawing-edge cache');
  const raw=new Float32Array(length*2);
  for(let i=0;i<length;i+=3){const j=i*2;raw[j]=values[offset+i];raw[j+1]=values[offset+i+1];raw[j+2]=values[offset+i+2];raw[j+4]=1;}
  cache.set(part,raw);
 }
// TIMESTAMP START 2026-11-05T13:07:26+00:00 | REVISION R000043
 decodedEdges.set(ranges,{buffer:values.buffer,byteOffset:values.byteOffset,length:values.length,cache});
// TIMESTAMP END 2026-11-05T13:07:26+00:00 | REVISION R000043
 return cache;
}
function ensureDetail(){
 if(!api.manifest.detail)return Promise.resolve(null);
// TIMESTAMP START 2026-11-05T13:07:26+00:00 | REVISION R000043
 const detailPath=api.manifest.detail;
 if(!api.detailPromise)api.detailPromise=detailBundles.get(detailPath);
 if(!api.detailPromise){api.detailPromise=resource(detailPath,'buffer').then(buffer=>{
// TIMESTAMP END 2026-11-05T13:07:26+00:00 | REVISION R000043
  if(buffer.byteLength<4)throw Error('Incomplete occupied-mesh detail');
  const size=new DataView(buffer).getUint32(0,true);
  if(size%4||size+4>buffer.byteLength||(buffer.byteLength-size-4)%4)throw Error('Invalid occupied-mesh detail header');
  const data=JSON.parse(new TextDecoder().decode(new Uint8Array(buffer,4,size)));
  if(data.schema!=='octagon-occupied-detail-1')throw Error('Unknown occupied-mesh detail format');
// TIMESTAMP START 2026-11-05T13:07:26+00:00 | REVISION R000043
  const result={...data,meshCache:edgeCache(new Float32Array(buffer,4+size),data.meshRanges)};if(api.manifest.detail===detailPath)api.detailReady=true;return result;
// TIMESTAMP END 2026-11-05T13:07:26+00:00 | REVISION R000043
// TIMESTAMP START 2026-11-05T13:07:26+00:00 | REVISION R000043
 }).catch(error=>{detailBundles.delete(detailPath);if(api.manifest.detail===detailPath)api.detailPromise=null;throw error;});detailBundles.set(detailPath,api.detailPromise);}
 return api.detailPromise;
// TIMESTAMP END 2026-11-05T13:07:26+00:00 | REVISION R000043
}
const api={configure,ensureDetail,loadJSON:path=>resource(path,'json'),loadBuffer:path=>resource(path,'buffer'),showError};
// TIMESTAMP END 2026-11-05T06:13:38+00:00 | REVISION R000027
root.OctagonSiteLoader=api;
})(globalThis);
// TIMESTAMP END 2026-11-04T19:27:13+00:00 | REVISION R000001
// TIMESTAMP END 2026-11-04T20:33:26+00:00 | REVISION R000023

// TIMESTAMP END 2026-11-04T23:23:25+00:00 | REVISION R000011
