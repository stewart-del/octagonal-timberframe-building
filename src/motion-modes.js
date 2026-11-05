// TIMESTAMP START 2026-11-04T20:00:49+00:00 | REVISION R000006
/* Playback follows the certified paths; invisible off-site preparation takes no screen time. */
(function(root){
'use strict';
function create(plan,disassembly,parts,{center=[0,1.2,0],sequenceAvailable=true}={}){
 const byId=new Map(parts.map(p=>[p.id,p])),count=plan.stages.length,anchors=new Set(plan.anchored_ids||[]);
 const reverse=plan.stages.slice().reverse().map((stage,index)=>({...stage,source_stage_index:count-1-index,motions:(stage.motions||[stage]).map(m=>({...m,delta_m:m.delta_m.map(v=>-v)}))}));
 const rawTracks=new Map();
 reverse.forEach((stage,index)=>{for(const m of stage.motions)for(const id of m.member_ids)if(!rawTracks.has(id))rawTracks.set(id,{index});});
 for(const [id,index] of Object.entries(plan.construction?.release_stage_by_piece||{}))rawTracks.set(id,{index:count-1-index});
 for(const [id,index] of Object.entries(plan.construction?.anchor_appearance_release_stage||{}))rawTracks.set(id,{index:count-1-index});
 // Skip a preparation stage only when every moving component is still hidden.
 // Visible components remain stationary through each omitted time interval.
 const indices=reverse.flatMap((stage,index)=>!plan.construction||stage.motions.some(m=>m.member_ids.some(id=>(rawTracks.get(id)?.index??Infinity)<=index))?[index]:[]);
 const assemblyStages=indices.map(index=>reverse[index]),assemblyCount=assemblyStages.length;
 const assemblyTracks=new Map([...rawTracks].map(([id,track])=>[id,{index:indices.findIndex(index=>index>=track.index)}]));
 const assemblyAvailable=sequenceAvailable&&plan.status==='PASS',clamp=p=>Math.max(0,Math.min(1,Number.isFinite(p)?p:0));
 function rawPosition(p){
  const position=clamp(p)*assemblyCount;if(position>=assemblyCount)return count;
  const index=Math.floor(position);return (indices[index]??count)+(position-index);
 }
 function phaseAt(progress,mode){
  const ranges=plan.construction?.reverse_phases;if(!ranges||mode==='sphere')return '';
  const position=mode==='assembly'?count-1-Math.floor(rawPosition(progress)):Math.floor(clamp(progress)*count);
  const stage=Math.min(count-1,Math.max(0,position));
  const name=Object.entries(ranges).find(([,range])=>stage>=range[0]&&stage<range[1])?.[0];
  return {finish:'Finish flooring',windows:'Windows',walls:'Main wall panels',porch:'Porch',roof:'Roof',trusses:'Individual trusses',cupola:'Central cupola',ties:'Cross-beams and eight-L connector',posts:'Posts and bare framing','post-caps':'Post-bearing caps',underlayment:'4 × 8 underlayment sheets','floor-supports':'Floor supports',foundations:'Concrete foundations',compact:'Compact exploded arrangement'}[name]||'';
 }
 const columnId=id=>id.endsWith('-BELOW')&&byId.has(id.slice(0,-6))?id.slice(0,-6):id;
 function sphereOffset(id,p){
  if(anchors.has(id))return [0,0,0];const q=byId.get(columnId(id));if(!q)return [0,0,0];
  const v=q.center||q.label_position||[0,0,0],d=v.map((x,i)=>x-center[i]);return d.map(x=>x*p*.72);
 }
 function offset(id,p,mode='disassembly'){
  if(mode==='sphere')return sphereOffset(id,p);
  if(!sequenceAvailable)return [0,0,0];
  if(mode==='assembly')return assemblyAvailable?disassembly.offset(id,count?1-rawPosition(p)/count:0):[0,0,0];
  return disassembly.offset(id,p);
 }
 function shown(id,p,mode='disassembly'){
  if(mode!=='assembly'||!assemblyAvailable)return true;
  if(anchors.has(id)&&!assemblyTracks.has(id))return true;
  const track=assemblyTracks.get(id);return track&&track.index>=0?clamp(p)*assemblyCount>=track.index-1e-9:p>=1;
 }
 function next(p,direction,mode,predicate){
  if(mode==='sphere')return clamp(p+direction*.05);
  if(mode==='assembly')return assemblyCount?clamp((direction>0?Math.floor(p*assemblyCount+1e-9)+1:Math.ceil(p*assemblyCount-1e-9)-1)/assemblyCount):0;
  return disassembly.next(p,direction,predicate);
 }
 return {offset,shown,next,phaseAt,sequenceAvailable,assemblyAvailable,count,assemblyCount,assemblyStages};
}
const api={create};root.OctagonMotionModes=api;if(typeof module!=='undefined'&&module.exports)module.exports=api;
})(typeof globalThis!=='undefined'?globalThis:this);
// TIMESTAMP END 2026-11-04T20:00:49+00:00 | REVISION R000006
