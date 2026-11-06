// TIMESTAMP START 2026-11-04T20:00:49+00:00 | REVISION R000006
/* Playback follows the certified paths; invisible off-site preparation takes no screen time. */
(function(root){
'use strict';
// TIMESTAMP START 2026-11-06T02:18:27+00:00 | REVISION R000081
function inspectAssembly(plan,parts){
 const byId=new Map(parts.map(p=>[p.id,p])),anchors=new Set(plan.anchored_ids||[]),first=new Map(),referenced=new Set(),fixed=new Set(anchors),invalidFixed=[];
 for(const [id,owner]of Object.entries(plan.construction?.fixed_member_owner_ids||{})){if(anchors.has(owner)&&byId.has(id))fixed.add(id);else invalidFixed.push(id);}
 plan.stages.forEach((stage,index)=>{for(const m of stage.motions||[stage])for(const id of m.member_ids){referenced.add(id);if(!first.has(id))first.set(id,index);}});
 const visual=p=>p.windowReference&&p.referenceAssemblyId&&byId.get(p.referenceAssemblyId)?.isPurchasedAssemblyProxy;
 const physical=parts.filter(p=>!visual(p)),missing=physical.filter(p=>!first.has(p.id)&&!fixed.has(p.id)).map(p=>p.id),unknown=[...referenced].filter(id=>!byId.has(id));
 const wall=new Set(physical.filter(p=>!p.isPurchasedAssemblyProxy&&['wall','wallStructure'].includes(p.displayRole)).map(p=>p.id));
 for(const p of physical)if(p.is_fastener&&(wall.has(p.parentId)||p.group==='wall_joinery_pegs'))wall.add(p.id);
 const count=plan.stages.length,install=new Map(),invalidInstall=[];
 for(const id of wall){const explicit=plan.construction?.individual_install_release_stage_by_piece?.[id],index=explicit??first.get(id);if(index===undefined)continue;
  if(!Number.isInteger(index)||index<0||index>=count||!(plan.stages[index].motions||[plan.stages[index]]).some(m=>m.member_ids.includes(id))){invalidInstall.push(id);continue;}install.set(id,count-1-index);
 }
 const grouped=new Map();for(const [id,index]of install){if(!grouped.has(index))grouped.set(index,[]);grouped.get(index).push(id);}
 const collective=[...grouped].filter(([,ids])=>ids.length>1).map(([assemblyStage,ids])=>({assemblyStage,ids})),posts=physical.filter(p=>/^P[0-7]$/.test(p.id)),postOrder=[],fasteningOrder=[],sidingOrder=[];
 for(const id of wall){const p=byId.get(id),step=install.get(id);if(step===undefined)continue;
  if(p.is_fastener){for(const parent of new Set([p.parentId,...p.assemblyPrerequisiteWoodIds||[]].filter(q=>wall.has(q))))if(!install.has(parent)||install.get(parent)>=step)fasteningOrder.push({id,receiverId:parent});}
  else if(p.displayRole==='wallStructure'){for(const post of posts)if(!first.has(post.id)||count-1-first.get(post.id)>=step)postOrder.push({id,postId:post.id});}
 }
 const courses=new Map();for(const id of wall){const p=byId.get(id);if(p.is_fastener||!(p.installationLayer==='siding'||p.sidingCourse!==undefined||p.wallRole==='siding'))continue;const face=p.wallFace||p.face,course=p.sidingCourse??p.course;
  if(typeof face!=='string'||!Number.isInteger(course)||!install.has(id)){sidingOrder.push({id,reason:'Missing actual siding face, course or installation step'});continue;}
  if(!courses.has(face))courses.set(face,new Map());const rows=courses.get(face);if(!rows.has(course))rows.set(course,[]);rows.get(course).push(id);
 }
 for(const [face,rows]of courses){let lower=-Infinity;for(const [course,ids]of [...rows].sort((a,b)=>a[0]-b[0])){const start=Math.min(...ids.map(id=>install.get(id)));if(start<=lower)sidingOrder.push({face,course,reason:'Upper siding must follow the lower boards and their fasteners'});const owners=new Set(ids),fasteners=physical.filter(p=>p.is_fastener&&owners.has(p.parentId));lower=Math.max(lower,...ids.map(id=>install.get(id)),...fasteners.map(p=>install.get(p.id)??Infinity));}}
 const declared=new Set(plan.physical_ids||[]),routeMissing=plan.status==='PARTIAL'?missing.filter(id=>!declared.has(id)):missing,routeCoverageComplete=!unknown.length&&!routeMissing.length&&!invalidFixed.length;
 return {status:routeCoverageComplete&&!missing.length&&!collective.length&&!postOrder.length&&!fasteningOrder.length&&!sidingOrder.length&&!invalidInstall.length?'PASS':'BLOCKED',routeCoverageComplete,missingPieceIds:missing,unknownStageIds:unknown,invalidFixedMemberIds:invalidFixed,wallPieceCount:wall.size,collectiveWallInstallations:collective,postOrderViolations:postOrder,fasteningOrderViolations:fasteningOrder,sidingOrderViolations:sidingOrder,invalidIndividualInstallIds:invalidInstall,scope:'Coverage and construction order only; this does not certify physical paths or structural capacity.'};
}
// TIMESTAMP END 2026-11-06T02:18:27+00:00 | REVISION R000081
function create(plan,disassembly,parts,{center=[0,1.2,0],sequenceAvailable=true}={}){
 const byId=new Map(parts.map(p=>[p.id,p])),count=plan.stages.length,anchors=new Set(plan.anchored_ids||[]);
 const reverse=plan.stages.slice().reverse().map((stage,index)=>({...stage,source_stage_index:count-1-index,motions:(stage.motions||[stage]).map(m=>({...m,delta_m:m.delta_m.map(v=>-v)}))}));
 const rawTracks=new Map();
 reverse.forEach((stage,index)=>{for(const m of stage.motions)for(const id of m.member_ids)if(!rawTracks.has(id))rawTracks.set(id,{index});});
 for(const [id,index] of Object.entries(plan.construction?.release_stage_by_piece||{}))rawTracks.set(id,{index:count-1-index});
 for(const [id,index] of Object.entries(plan.construction?.anchor_appearance_release_stage||{}))rawTracks.set(id,{index:count-1-index});
 // TIMESTAMP START 2026-11-06T02:18:27+00:00 | REVISION R000081
 for(const [id,index] of Object.entries(plan.construction?.individual_install_release_stage_by_piece||{})){const appearance=count-1-index;rawTracks.set(id,{index:Math.min(rawTracks.get(id)?.index??Infinity,appearance)});}
 // TIMESTAMP END 2026-11-06T02:18:27+00:00 | REVISION R000081
 // Skip a preparation stage only when every moving component is still hidden.
 // Visible components remain stationary through each omitted time interval.
 const indices=reverse.flatMap((stage,index)=>!plan.construction||stage.motions.some(m=>m.member_ids.some(id=>(rawTracks.get(id)?.index??Infinity)<=index))?[index]:[]);
 const assemblyStages=indices.map(index=>reverse[index]),assemblyCount=assemblyStages.length;
 const assemblyTracks=new Map([...rawTracks].map(([id,track])=>[id,{index:indices.findIndex(index=>index>=track.index)}]));
 // TIMESTAMP START 2026-11-06T02:18:27+00:00 | REVISION R000081
 const assemblyCoverage=inspectAssembly(plan,parts);sequenceAvailable=sequenceAvailable&&assemblyCoverage.routeCoverageComplete;
 const assemblyAvailable=sequenceAvailable&&plan.status==='PASS'&&assemblyCoverage.status==='PASS',clamp=p=>Math.max(0,Math.min(1,Number.isFinite(p)?p:0));
 // TIMESTAMP END 2026-11-06T02:18:27+00:00 | REVISION R000081
 function rawPosition(p){
  const position=clamp(p)*assemblyCount;if(position>=assemblyCount)return count;
  const index=Math.floor(position);return (indices[index]??count)+(position-index);
 }
 function phaseAt(progress,mode){
  const ranges=plan.construction?.reverse_phases;if(!ranges||mode==='sphere')return '';
  const position=mode==='assembly'?count-1-Math.floor(rawPosition(progress)):Math.floor(clamp(progress)*count);
  const stage=Math.min(count-1,Math.max(0,position));
  const name=Object.entries(ranges).find(([,range])=>stage>=range[0]&&stage<range[1])?.[0];
  // TIMESTAMP START 2026-11-06T02:18:27+00:00 | REVISION R000081
  return {finish:'Finish flooring',windows:'Windows',walls:'Wall framing, plywood and siding',porch:'Porch',roof:'Roof',trusses:'Individual trusses',cupola:'Central cupola',ties:'Cross-beams and eight-L connector',posts:'Posts and bare framing','post-caps':'Post-bearing caps',underlayment:'4 × 8 underlayment sheets','floor-supports':'Floor supports',foundations:'Concrete foundations',compact:'Compact exploded arrangement'}[name]||'';
  // TIMESTAMP END 2026-11-06T02:18:27+00:00 | REVISION R000081
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
  // TIMESTAMP START 2026-11-06T02:18:27+00:00 | REVISION R000081
  if((anchors.has(id)||anchors.has(plan.construction?.fixed_member_owner_ids?.[id]))&&!assemblyTracks.has(id))return true;
  // TIMESTAMP END 2026-11-06T02:18:27+00:00 | REVISION R000081
  // TIMESTAMP START 2026-11-06T02:18:27+00:00 | REVISION R000081
  const track=assemblyTracks.get(id);return !!(track&&track.index>=0&&clamp(p)*assemblyCount>=track.index-1e-9);
  // TIMESTAMP END 2026-11-06T02:18:27+00:00 | REVISION R000081
 }
 function next(p,direction,mode,predicate){
  if(mode==='sphere')return clamp(p+direction*.05);
  if(mode==='assembly')return assemblyCount?clamp((direction>0?Math.floor(p*assemblyCount+1e-9)+1:Math.ceil(p*assemblyCount-1e-9)-1)/assemblyCount):0;
  return disassembly.next(p,direction,predicate);
 }
 // TIMESTAMP START 2026-11-06T02:18:27+00:00 | REVISION R000081
 return {offset,shown,next,phaseAt,sequenceAvailable,assemblyAvailable,assemblyCoverage,count,assemblyCount,assemblyStages};
 // TIMESTAMP END 2026-11-06T02:18:27+00:00 | REVISION R000081
}
// TIMESTAMP START 2026-11-06T02:18:27+00:00 | REVISION R000081
const api={create,inspectAssembly};root.OctagonMotionModes=api;if(typeof module!=='undefined'&&module.exports)module.exports=api;
// TIMESTAMP END 2026-11-06T02:18:27+00:00 | REVISION R000081
})(typeof globalThis!=='undefined'?globalThis:this);
// TIMESTAMP END 2026-11-04T20:00:49+00:00 | REVISION R000006
