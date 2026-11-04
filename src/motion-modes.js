// TIMESTAMP START 2026-11-03T13:32:57-05:00 | REVISION R005027
(function(root){
'use strict';
function create(plan,disassembly,parts,{center=[0,1.2,0],sequenceAvailable=true}={}){
 // TIMESTAMP START 2026-11-03T15:52:59-05:00 | REVISION R005041
 // TIMESTAMP START 2026-11-03T16:49:21-05:00 | REVISION R005060
 const byId=new Map(parts.map(p=>[p.id,p])),count=plan.stages.length,anchors=new Set(plan.anchored_ids||[]);
 // Reverse the certified trajectories. A component appears immediately before
 // its first reverse movement; every subsequent movement retains that path.
 const assemblyStages=plan.stages.slice().reverse().map(stage=>({...stage,motions:(stage.motions||[stage]).map(m=>({...m,delta_m:m.delta_m.map(v=>-v)}))}));
 const assemblyTracks=new Map();assemblyStages.forEach((stage,index)=>{for(const m of stage.motions)for(const id of m.member_ids)if(!assemblyTracks.has(id))assemblyTracks.set(id,{index});});
 const assemblyCount=assemblyStages.length,assemblyAvailable=sequenceAvailable&&plan.status==='PASS',clamp=p=>Math.max(0,Math.min(1,p));
 // TIMESTAMP END 2026-11-03T16:49:21-05:00 | REVISION R005060
 const columnId=id=>id.endsWith('-BELOW')&&byId.has(id.slice(0,-6))?id.slice(0,-6):id;
 function sphereOffset(id,p){
  if(anchors.has(id))return [0,0,0];const q=byId.get(columnId(id));if(!q)return [0,0,0];
  const v=q.center||q.label_position||[0,0,0],d=v.map((x,i)=>x-center[i]);
  return d.map(x=>x*p*.72);
 }
 function offset(id,p,mode='disassembly'){
  if(mode==='sphere')return sphereOffset(id,p);
  if(!sequenceAvailable)return [0,0,0];
  // TIMESTAMP START 2026-11-03T15:52:59-05:00 | REVISION R005041
  // TIMESTAMP START 2026-11-03T15:57:47-05:00 | REVISION R005043
  // TIMESTAMP START 2026-11-03T16:49:21-05:00 | REVISION R005060
  if(mode==='assembly')return assemblyAvailable?disassembly.offset(id,1-clamp(p)):[0,0,0];
  // TIMESTAMP END 2026-11-03T16:49:21-05:00 | REVISION R005060
  // TIMESTAMP END 2026-11-03T15:57:47-05:00 | REVISION R005043
  return disassembly.offset(id,p);
  // TIMESTAMP END 2026-11-03T15:52:59-05:00 | REVISION R005041
 }
 function shown(id,p,mode='disassembly'){
  // TIMESTAMP START 2026-11-03T15:52:59-05:00 | REVISION R005041
  if(mode!=='assembly'||!assemblyAvailable)return true;
  if(anchors.has(id))return true;
  const t=assemblyTracks.get(id);return t?p*assemblyCount>=t.index-1e-9:p>=1;
  // TIMESTAMP END 2026-11-03T15:52:59-05:00 | REVISION R005041
 }
 function next(p,direction,mode,predicate){
  if(mode==='sphere')return Math.max(0,Math.min(1,p+direction*.05));
  // TIMESTAMP START 2026-11-03T15:52:59-05:00 | REVISION R005041
  if(mode==='assembly')return assemblyCount?clamp((direction>0?Math.floor(p*assemblyCount+1e-9)+1:Math.ceil(p*assemblyCount-1e-9)-1)/assemblyCount):0;
  // TIMESTAMP END 2026-11-03T15:52:59-05:00 | REVISION R005041
  return disassembly.next(p,direction,predicate);
 }
 // TIMESTAMP START 2026-11-03T15:52:59-05:00 | REVISION R005041
 return {offset,shown,next,sequenceAvailable,assemblyAvailable,count,assemblyCount,assemblyStages};
 // TIMESTAMP END 2026-11-03T15:52:59-05:00 | REVISION R005041
}
const api={create};root.OctagonMotionModes=api;if(typeof module!=='undefined'&&module.exports)module.exports=api;
})(typeof globalThis!=='undefined'?globalThis:this);
// TIMESTAMP END 2026-11-03T13:32:57-05:00 | REVISION R005027
