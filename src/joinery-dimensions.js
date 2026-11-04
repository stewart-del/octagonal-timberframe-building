// TIMESTAMP START 2026-11-03T13:59:01-05:00 | REVISION R005033
(function(root){
'use strict';
const I=.0254,dot=(a,b)=>a.reduce((s,x,i)=>s+x*b[i],0);
function span(vertices,axis){const p=vertices.map(v=>dot(v,axis));return Math.max(...p)-Math.min(...p);}
function entries(id,{model,porch,wall}={}){
 const joints=[...(model?.tenon_schedule||[]),...(porch?.joinery?.joints||[]),...(wall?.joints||[])];
 return joints.filter(j=>j.donor===id&&(j.projection_m!=null||j.tenon_projection_m!=null||j.engagement_m!=null)).map(j=>{
  const mesh=j.connector||j.tongue,axis=j.insertion_direction||j.insertion_direction_world;
  const depth=j.projection_m??j.tenon_projection_m??j.engagement_m;
  const widths=j.tenon_cross_section_m||[j.width_m??j.neck_width_m,j.height_m];
  return {id:j.id,receiver:j.receiver,shape:j.shape||j.family,depthIn:depth/I,widthIn:widths[0]/I,heightIn:widths[1]/I,headWidthIn:j.head_width_m==null?null:j.head_width_m/I,measuredDepthIn:mesh?.vertices?.length&&axis?span(mesh.vertices,axis)/I:null};
 });
}
function render(host,id,context,document){
 const rows=entries(id,context);if(!rows.length)return;
 const section=document.createElement('section');section.className='tenon-dimensions';
 const title=document.createElement('h3');title.textContent='Tenon dimensions';section.appendChild(title);
 const fmt=value=>Number(value.toFixed(3)).toString();
 for(const row of rows){
  const item=document.createElement('div');item.className='metric';
  const label=document.createElement('span');label.textContent='Into '+row.receiver;
  const value=document.createElement('strong');
  const cross=[row.widthIn,row.heightIn].filter(Number.isFinite);
  value.textContent=(cross.length?cross.map(fmt).join(' × ')+' in · ':'')+fmt(row.depthIn)+' in deep';
  item.append(label,value);section.appendChild(item);
  if(row.headWidthIn!=null){const note=document.createElement('small');note.textContent='Dovetail head width '+fmt(row.headWidthIn)+' in';section.appendChild(note);}
 }
 host.appendChild(section);
}
const api={entries,render};if(typeof module!=='undefined'&&module.exports)module.exports=api;root.OctagonJoineryDimensions=api;
})(typeof globalThis!=='undefined'?globalThis:this);
// TIMESTAMP END 2026-11-03T13:59:01-05:00 | REVISION R005033
