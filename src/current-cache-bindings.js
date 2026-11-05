// TIMESTAMP START 2026-11-05T20:08:59+00:00 | REVISION R000063
/* Separate applicability evidence; original cache headers stay historical. */
(function(root){
'use strict';
const STATUS='PASS_BOUNDED_CURRENT_INPUT_BINDING_ONLY',FIXTURE='807b6eaf5e525ebf90bbd89f4ebfe444092982d250fd9ce6313075b4cffdb8fb',BINDING='b1658b1208dd12cffa8860b10ef136e3f294b6bba40937b37cbf428b933d36f5';
function matches(cache,context,key){
 if(typeof context?.sha256!=='string'||!context.sha256)return false;
 if(cache?.source_model_sha256===context.sha256)return true;
 const proof=cache?.currentSourceBinding,owner=context?.cacheOwnership,id=context?.id;
 return !!(proof&&owner&&owner.status===STATUS&&proof.status===STATUS&&owner.bindingSha256===BINDING&&proof.bindingSha256===BINDING&&owner.fixtureSha256===FIXTURE&&proof.fixtureSha256===FIXTURE&&owner.preserveHistoricalHeaders===true&&proof.preservedHistoricalHeaders===true&&owner.wholeBuildingReady===false&&proof.variant===id&&proof.currentModelSha256===context.sha256&&owner.models?.[id]===context.sha256&&proof.cacheKey===key&&proof.cacheSha256===owner.caches?.[key]&&typeof proof.cacheSha256==='string'&&/^[a-f0-9]{64}$/.test(proof.cacheSha256));
}
function attach(cache,key,variant,owner){
 if(owner?.status!==STATUS||owner.bindingSha256!==BINDING||owner.fixtureSha256!==FIXTURE||!owner.models?.[variant]||!owner.caches?.[key])throw Error('Verified current cache ownership is unavailable');
 if(key.startsWith('enclosure-')&&key!=='enclosure-'+variant)throw Error('Enclosure ownership belongs to another variant');
 return {...cache,currentSourceBinding:{status:STATUS,bindingSha256:BINDING,fixtureSha256:FIXTURE,cacheKey:key,cacheSha256:owner.caches[key],variant,currentModelSha256:owner.models[variant],preservedHistoricalHeaders:true}};
}
function verifiedNode(rootPath){
 if(typeof require!=='function')throw Error('Node source verification is unavailable in the browser');
 const fs=require('fs'),path=require('path'),crypto=require('crypto'),owner=JSON.parse(fs.readFileSync(path.join(rootPath,'src/current-cache-bindings.json'),'utf8')),digestBytes=raw=>crypto.createHash('sha256').update(raw).digest('hex'),digest=file=>digestBytes(fs.readFileSync(path.join(rootPath,file))),archive=fs.readFileSync(path.join(rootPath,'scripts/fixtures/current-cache-binding.tar.gz'));
 if(owner.status!==STATUS||owner.bindingSha256!==BINDING||owner.fixtureSha256!==FIXTURE||digestBytes(archive)!==FIXTURE)throw Error('Current cache native proof package changed');
 const tar=require('zlib').gunzipSync(archive);let binding=null;
 for(let offset=0;offset+512<=tar.length;){const header=tar.subarray(offset,offset+512),name=header.subarray(0,100).toString('utf8').replace(/\0.*$/,''),size=parseInt(header.subarray(124,136).toString('ascii').replace(/\0.*$/,'').trim()||'0',8);if(!Number.isSafeInteger(size)||size<0||offset+512+size>tar.length)throw Error('Invalid native proof archive');if(name==='cache-ownership-audit/current-source-scoped-cache-binding.json'){const raw=tar.subarray(offset+512,offset+512+size);if(digestBytes(raw)!==BINDING)throw Error('Native proof binding changed');binding=JSON.parse(raw.toString('utf8'));break;}offset+=512+Math.ceil(size/512)*512;}
 if(!binding||Object.keys(binding.repositoryInputs||{}).length!==41||Object.keys(owner.repositoryInputs||{}).length!==41)throw Error('Current cache source closure is incomplete');
 for(const [file,expected]of Object.entries(binding.repositoryInputs))if(owner.repositoryInputs[file]!==expected||digest(file)!==expected)throw Error('Current cache source input changed: '+file);
 for(const [id,expected]of Object.entries(binding.acceptedCurrentModelSha256))if(owner.models?.[id]!==expected)throw Error('Current cache model identity changed: '+id);
 const files={floor:'src/floor-foundation-solids.json',wall:'src/wall-joinery-fit.json',porch:'src/mudroom-joinery-fit.json','enclosure-baseline':'src/enclosure-fit.json','enclosure-proposed':'src/step-lap-proposed-enclosure-fit.json','enclosure-top-entry':'src/top-entry-proposed-enclosure-fit.json'};
 for(const [key,file]of Object.entries(files))if(owner.caches?.[key]!==binding.repositoryInputs[file])throw Error('Current cache artifact identity changed: '+key);
 return owner;
}
const api={matches,attach,verifiedNode};root.OctagonCurrentCacheBindings=api;if(typeof module!=='undefined'&&module.exports)module.exports=api;
})(typeof globalThis!=='undefined'?globalThis:this);
// TIMESTAMP END 2026-11-05T20:08:59+00:00 | REVISION R000063
