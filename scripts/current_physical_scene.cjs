// TIMESTAMP START 2026-11-05T21:07:06+00:00 | REVISION R000065
'use strict';
/* Current assembled product projection; construction lifetimes are separate. */
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),assert=require('node:assert/strict');
const ROOT=path.resolve(__dirname,'..'),C=require('../src/current-cache-bindings.js'),W=require('../src/wall-joinery.js'),A=require('../src/architecture.js'),P=require('../src/physical-parts.js'),roles=require('../src/display-presets.js'),floor=require('../src/floor-foundation.js'),walls=require('../src/schematic-walls.js'),roof=require('../src/roof-coverings.js'),porch=require('../src/mudroom.js');
// Capture the actual loaded implementation, including its lazy roof dependency.
require('../src/mudroom-roof.js');
const hash=raw=>crypto.createHash('sha256').update(raw).digest('hex'),digest=file=>hash(fs.readFileSync(file));
const loadedSources=Object.fromEntries(Object.keys(require.cache).filter(file=>file.startsWith(ROOT+path.sep)&&file.endsWith('.js')||file===__filename).map(file=>[file,digest(file)]));
const names={baseline:['model-data.json','enclosure-fit.json'],proposed:['step-lap-proposed-model.json','step-lap-proposed-enclosure-fit.json'],'top-entry':['top-entry-proposed-model.json','top-entry-proposed-enclosure-fit.json']};
function compose({variant='top-entry',architecturePath=path.join(ROOT,'src/architectural-solids.json'),allowStaging=false}={}){
 assert(Object.hasOwn(names,variant),'Unknown physical model variant');
 for(const [file,expected]of Object.entries(loadedSources))assert.equal(digest(file),expected,'Loaded scene implementation changed: '+file);
 const owner=C.verifiedNode(ROOT),sources=new Map(Object.entries(owner.repositoryInputs).map(([file,sha])=>[path.join(ROOT,file),sha]));
 for(const row of Object.entries(loadedSources))sources.set(...row);
 function read(file){file=path.resolve(file);const raw=fs.readFileSync(file),sha=hash(raw);if(sources.has(file))assert.equal(sources.get(file),sha,'Scene source changed during composition: '+file);sources.set(file,sha);return JSON.parse(raw);}
 function physical(file){file=path.resolve(file);const metadata=read(file),directory=path.dirname(file),archives=[...(metadata.geometryArchives||[]),...(metadata.partArchives||[]),...(metadata.geometryArchive?[{path:metadata.geometryArchive,sha256:metadata.geometryArchiveSha256}]:[])];
  for(const archive of archives){assert(!path.isAbsolute(archive.path)&&!archive.path.split(/[\\/]/).includes('..'),'Physical archive must stay beside its metadata');const absolute=path.resolve(directory,archive.path),sha=digest(absolute);assert.equal(sha,archive.sha256,'Physical archive changed');sources.set(absolute,sha);}
  return P.resolveSourceData(metadata,directory);
 }
 architecturePath=path.resolve(architecturePath);const architecture=physical(architecturePath),staging=architecture.status!=='PASS';
 assert.equal(architecture.schema,'octagon-articulated-architecture-1','Unknown architectural source schema');
 assert(!staging||(allowStaging&&architecture.status==='STAGING_INCOMPLETE_DO_NOT_PUBLISH'),'Final physical architecture is not ready; use explicit staging only for independent work');
 const [modelName,enclosureName]=names[variant],base=read(path.join(ROOT,'src',modelName)),enclosure=C.attach(read(path.join(ROOT,'src',enclosureName)),'enclosure-'+variant,variant,owner),fit=C.attach(read(path.join(ROOT,'src/wall-joinery-fit.json')).variants[variant],'wall',variant,owner),foundation=physical(path.join(ROOT,'src/floor-foundation-solids.json')),porchFit=C.attach(read(path.join(ROOT,'src/mudroom-joinery-fit.json')),'porch',variant,owner),context={id:variant,sha256:owner.models[variant],cacheOwnership:owner};
 for(const [cache,key]of [[enclosure,'enclosure-'+variant],[fit,'wall'],[porchFit,'porch']])assert(C.matches(cache,context,key),'No current cache applicability: '+key);
 assert.equal(architecture.sourceFloorSha256,owner.caches.floor,'Architecture was composed over a different actual floor');
 const previous={enclosure:global.OCTAGON_ENCLOSURE_FIT,porch:global.MUDROOM_JOINERY_FIT};let composed;
 try{
  global.OCTAGON_ENCLOSURE_FIT=enclosure;global.MUDROOM_JOINERY_FIT=porchFit;
  const model=A.applyModel(W.applyModel(base,fit),architecture),legacy=[...roof.build(model).components,...floor.roomLayout(model,W.applyLayout(walls.build(model.parts),fit),foundation).components,...porch.build(model).components];
  composed=A.compose(model,legacy,architecture);
 }finally{
  if(previous.enclosure===undefined)delete global.OCTAGON_ENCLOSURE_FIT;else global.OCTAGON_ENCLOSURE_FIT=previous.enclosure;
  if(previous.porch===undefined)delete global.MUDROOM_JOINERY_FIT;else global.MUDROOM_JOINERY_FIT=previous.porch;
 }
 const all=[...composed.model.parts,...composed.components],lookup=new Map(all.map(p=>[p.id,p]));assert.equal(lookup.size,all.length,'Duplicate scene actor');
 const included=all.filter(p=>roles.included(p,'complete')),excluded=all.filter(p=>!roles.included(p,'complete')).map(p=>{
  if(p.windowReference){const parent=lookup.get(p.unitId);assert(parent?.isPurchasedAssemblyProxy&&parent.collisionEnvelopeOnly&&roles.included(parent,'complete'),'Window appearance reference lacks its physical purchased envelope');return {id:p.id,reason:'Planar appearance reference; physical purchased unit retained',physical:false,physicalParentId:parent.id};}
  return {id:p.id,reason:roles.role(p),physical:false};
 });
 for(const part of included)assert(!part.windowReference,'Appearance surface cannot replace a physical product');
 const serialized=A.serializeScene(included);
 for(const [file,expected]of sources)assert.equal(digest(file),expected,'Scene source changed during composition: '+file);
 const sourceNames=Object.fromEntries(Array.from(sources,([file,sha])=>[file.startsWith(ROOT+path.sep)?path.relative(ROOT,file).split(path.sep).join('/'):file,sha]).sort(([a],[b])=>a.localeCompare(b)));
 return {...serialized,excluded,sources:sourceNames,projection:{schema:'octagon-current-assembled-projection-1',variant,currentModelSha256:owner.models[variant],bindingSha256:owner.bindingSha256,architectureStatus:architecture.status,architectureSource:architecturePath,staging,scope:'Assembled product projection only; all included physical actors retained. Temporary forming stock, material birth and complete construction route require their separate lifecycle composition.',wholeBuildingReady:false,physicalActorCount:included.length,excludedReferenceCount:excluded.length}};
}
module.exports={compose};
if(require.main===module){const variant=process.argv[2]||'top-entry',architecturePath=process.argv[3]||undefined;process.stdout.write(JSON.stringify(compose({variant,architecturePath,allowStaging:process.argv.includes('--staging')})));}
// TIMESTAMP END 2026-11-05T21:07:06+00:00 | REVISION R000065
