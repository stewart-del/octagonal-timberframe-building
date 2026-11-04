// TIMESTAMP START 2026-11-04T20:33:26+00:00 | REVISION R000023
// TIMESTAMP START 2026-11-04T19:27:13+00:00 | REVISION R000001
(function(root){
'use strict';
const pending=new Map();
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
   return type==='json'?response.json():response.arrayBuffer();
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
 const requested=new URL(root.location.href).searchParams.get('model');
 const id=requested==='baseline'||requested==='proposed'?requested:'top-entry';
 // TIMESTAMP START 2026-11-04T19:29:44+00:00 | REVISION R000002
 api.data=Promise.all([resource(manifest.common,'json'),resource(manifest.variants[id],'json'),resource(manifest.meshBuffers[id],'buffer')]).then(([common,selected,buffer])=>{
  const values=new Float32Array(buffer),meshCache=new Map();
  for(const [part,[offset,length]] of Object.entries(selected.meshRanges)){
   if(!Number.isInteger(offset)||!Number.isInteger(length)||offset<0||length<0||offset+length>values.length||length%6)throw Error('Invalid drawing-edge cache');
   const raw=new Float32Array(length*2);
   for(let i=0;i<length;i+=3){const j=i*2;raw[j]=values[offset+i];raw[j+1]=values[offset+i+1];raw[j+2]=values[offset+i+2];raw[j+4]=1;}
   meshCache.set(part,raw);
  }
  return {...common,...selected,meshCache};
 });
 // TIMESTAMP END 2026-11-04T19:29:44+00:00 | REVISION R000002
 api.data.catch(showError);
 return api.data;
}
const api={configure,loadJSON:path=>resource(path,'json'),loadBuffer:path=>resource(path,'buffer'),showError};
root.OctagonSiteLoader=api;
})(globalThis);
// TIMESTAMP END 2026-11-04T19:27:13+00:00 | REVISION R000001
// TIMESTAMP END 2026-11-04T20:33:26+00:00 | REVISION R000023
