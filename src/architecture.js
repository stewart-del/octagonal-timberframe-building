// TIMESTAMP START 2026-11-05T12:40:59+00:00 | REVISION R000041
/* Individual physical products; repeated metal meshes and specs are shared. */
(function(root){
'use strict';
const cache=new WeakMap();
function resolve(data){if(!data)return null;const physical=typeof OctagonPhysicalParts!=='undefined'?OctagonPhysicalParts:require('./physical-parts.js');return physical.resolveSourceData(data,typeof __dirname==='string'?__dirname:null);}
function components(data){
 data=resolve(data);if(!data)return [];if(cache.has(data))return cache.get(data);
 const physical=typeof OctagonPhysicalParts!=='undefined'?OctagonPhysicalParts:require('./physical-parts.js');
 const result=data.parts.map(part=>{const center=part.center||[0,0,0],length=Math.hypot(center[0],center[2])||1,normal=part.removal_normal||[center[0]/length,.65,center[2]/length];return physical.hydrate({...part,label_position:center,exploded_offset:part.exploded_offset||normal.map((x,k)=>x*3+(k===1?1:0))},data.prototypes||{});});
 cache.set(data,result);return result;
}
function applyModel(model,data){
 data=resolve(data);if(!data)return model;
 const removed=new Set(data.primaryRemoveIds||[]);return {...model,parts:model.parts.filter(p=>!removed.has(p.id)),architectureRevision:data.revision};
}
function compose(model,legacy,data){
 data=resolve(data);if(!data)return {model,components:legacy};
 const kinds=new Set(data.replaceSchematicKinds||[]),explicit=new Set(data.replaceSchematicIds||[]);
// TIMESTAMP START 2026-11-05T16:27:06+00:00 | REVISION R000053
 const overlays=new Set(components(data).filter(p=>p.replaceExisting).map(p=>p.id));
 const kept=legacy.filter(p=>overlays.has(p.id)||(!kinds.has(p.schematicKind)&&!explicit.has(p.id)&&!(data.replacePorchRoof&&(p.mudroomRoof||p.roofLayer||p.mudroomRole==='roof'))));
// TIMESTAMP END 2026-11-05T16:27:06+00:00 | REVISION R000053
 const fitted=applyModel(model,data),primary=new Map(fitted.parts.map(p=>[p.id,p])),indices=new Map(kept.map((p,i)=>[p.id,i])),added=[];
 const ids=new Set([...fitted.parts,...kept].map(p=>p.id));
 for(const p of components(data)){
  if(p.replaceExisting){
   if(primary.has(p.id))throw Error('Architectural component overlay cannot silently replace primary joinery '+p.id);
   if(!indices.has(p.id))throw Error('Missing original component for physical overlay '+p.id);
   kept[indices.get(p.id)]=p;continue;
  }
  if(ids.has(p.id))throw Error('Duplicate physical architectural piece '+p.id);ids.add(p.id);added.push(p);
 }
 return {model:fitted,components:[...kept,...added]};
}
// TIMESTAMP START 2026-11-05T12:40:59+00:00 | REVISION R000041
function serializeScene(parts){
 const prototypes={},records=parts.map(part=>{
  if(!part.mesh_instance)return part;
  const name=part.mesh_instance.prototype,prototype=part.instancePrototype;
  if(!prototype)throw Error('Unresolved physical prototype '+part.id);
  if(prototypes[name]&&prototypes[name]!==prototype&&JSON.stringify(prototypes[name])!==JSON.stringify(prototype))throw Error('Conflicting physical prototype '+name);
  prototypes[name]=prototype;const record={};
  // Do not touch lazy world vertices while crossing the Node/Python boundary.
  // Every actual transform and shared triangle is retained without expansion.
  for(const key of Object.keys(part))if(!['vertices','triangles','faces'].includes(key))record[key]=part[key];
  return record;
 });return {parts:records,prototypes};
}
// TIMESTAMP END 2026-11-05T12:40:59+00:00 | REVISION R000041
// TIMESTAMP START 2026-11-05T13:19:15+00:00 | REVISION R000044
function intendedFastenerContact(fastener,receiver){
 const metal=/\b(steel|metal|stainless|galvanized|brass|bronze|copper)\b/i,receiving=/wood|timber|pine|fir|cedar|bamboo|plywood|plytanium|sheathing|SmartSide|membrane|underlayment|roofing felt|CedarBreather|breather mat|adhesive tape|weatherstrip|elastomeric/i;
 return !!((fastener.intentionalFastenerPenetration||fastener.intentionalWoodPenetration)&&fastener.is_fastener&&['nail','screw'].includes(fastener.fastenerKind)&&metal.test(fastener.material||'')&&fastener.receiverIds?.includes(receiver.id)&&!receiver.is_fastener&&!metal.test(receiver.material||'')&&(receiver.is_timber||receiving.test(receiver.material||'')));
}
// TIMESTAMP END 2026-11-05T13:19:15+00:00 | REVISION R000044

const api={resolve,components,applyModel,compose,serializeScene,intendedFastenerContact,intendedWoodContact:intendedFastenerContact};root.OctagonArchitecture=api;if(typeof module!=='undefined'&&module.exports)module.exports=api;
})(typeof globalThis!=='undefined'?globalThis:this);
// TIMESTAMP END 2026-11-05T12:40:59+00:00 | REVISION R000041
