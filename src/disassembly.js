// TIMESTAMP START 2026-11-02T15:57:59-05:00 | REVISION R004811
/* Playback of audited rigid translations. This module never invents a path. */
(function(root){
'use strict';
const zero=()=>[0,0,0],add=(a,b)=>a.map((v,k)=>v+b[k]);
function create(plan,sceneIds){
 if(!plan||!['PASS','PARTIAL'].includes(plan.status)||!Array.isArray(plan.stages))throw Error('A verified disassembly plan is required');
 const known=new Set(sceneIds),tracks=new Map(),ends=new Map();
 const stages=plan.stages.map((stage,index)=>{
  const motions=stage.motions||[{member_ids:stage.member_ids,delta_m:stage.delta_m}],seen=new Set();
  for(const move of motions){
   if(!Array.isArray(move.member_ids)||!move.member_ids.length||!Array.isArray(move.delta_m)||move.delta_m.length!==3||!move.delta_m.every(Number.isFinite))throw Error('Invalid disassembly motion '+stage.id);
   for(const id of move.member_ids){
    if(!known.has(id)||seen.has(id))throw Error('Unknown or repeated moving piece '+id);
    seen.add(id);const from=ends.get(id)||zero(),to=add(from,move.delta_m);
    if(!tracks.has(id))tracks.set(id,[]);
    tracks.get(id).push({index,from:from.slice(),to:to.slice(),delta:move.delta_m.slice()});ends.set(id,to);
   }
  }
  // TIMESTAMP START 2026-11-03T07:02:34-05:00 | REVISION R004905
  for(const id of known){if(!id.endsWith('-BELOW')||!known.has(id.slice(0,-6))||!(id.startsWith('PIER-')||id.startsWith('MUD-SUPPORT-')))continue;
   const delta=pid=>motions.find(move=>move.member_ids.includes(pid))?.delta_m||zero(),a=delta(id),b=delta(id.slice(0,-6));
   if(a.some((x,k)=>x!==b[k]))throw Error('A continuous column cannot split at grade: '+id);
  }
  if((plan.anchored_ids||[]).some(id=>seen.has(id)))throw Error('The central anchors must remain fixed');
  // TIMESTAMP END 2026-11-03T07:02:34-05:00 | REVISION R004905
  return {...stage,motions,member_ids:[...seen]};
 });
 const count=stages.length,clamp=p=>Math.max(0,Math.min(1,Number.isFinite(p)?p:0));
 function offset(id,progress){
  const position=clamp(progress)*count,track=tracks.get(id);if(!track)return zero();
  let out=zero();
  for(const segment of track){
   if(position<=segment.index)break;
   const fraction=Math.min(1,position-segment.index);
   out=segment.from.map((v,k)=>v+segment.delta[k]*fraction);
   if(fraction<1)break;
  }
  return out;
 }
 function state(progress){
  const p=clamp(progress),completed=Math.min(count,Math.floor(p*count+1e-10)),index=Math.min(count-1,completed);
  return {progress:p,count,completed,stage:index>=0?stages[index]:null,assembled:p===0,finished:p===1,status:plan.status,blocked:plan.blocked||[]};
 }
 function next(progress,direction=1,predicate=()=>true){
  if(!count)return 0;
  const position=clamp(progress)*count;
  if(direction>0){for(let k=Math.floor(position+1e-9);k<count;k++)if(stages[k].member_ids.some(predicate))return (k+1)/count;return 1;}
  for(let k=Math.ceil(position-1e-9)-1;k>=0;k--)if(stages[k].member_ids.some(predicate))return k/count;
  return 0;
 }
 return {offset,state,next,stages,count,blocked:plan.blocked||[],excluded:plan.excluded||[]};
}
root.OctagonDisassembly={create};if(typeof module!=='undefined'&&module.exports)module.exports=root.OctagonDisassembly;
})(typeof globalThis!=='undefined'?globalThis:this);
// TIMESTAMP END 2026-11-02T15:57:59-05:00 | REVISION R004811
