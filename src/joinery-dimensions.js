// TIMESTAMP START 2026-11-04T23:23:25+00:00 | REVISION R000011
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
// TIMESTAMP START 2026-11-04T19:33:21+00:00 | REVISION R000014
function blank(part){
 if(!part?.stock_frame||!part.vertices?.length||(part.fabrication_dimensions_valid===false&&!part.is_timber))return null;
 const axes=['axis','width','depth'].map(k=>part.stock_frame[k]);
 if(axes.some(v=>!Array.isArray(v)||v.length!==3||!v.every(Number.isFinite)||Math.hypot(...v)<1e-9))return null;
 const [length,width,depth]=axes.map(v=>span(part.vertices,v.map(x=>x/Math.hypot(...v)))/I);
 const reference=part.dimensions?.length_m/I;
 return {minimumLengthIn:length,quarterInchLengthIn:Math.ceil((Math.max(length,Number.isFinite(reference)?reference:0)-1e-7)*4)/4,
  widthIn:Math.max(width,part.dimensions?.width_in||0),depthIn:Math.max(depth,part.dimensions?.depth_in||0)};
}
// TIMESTAMP END 2026-11-04T19:33:21+00:00 | REVISION R000014
function render(host,id,context,document){
// TIMESTAMP START 2026-11-04T19:33:21+00:00 | REVISION R000014
 const rows=entries(id,context),part=context.part||context.model?.parts?.find(p=>p.id===id),stock=blank(part);if(!rows.length&&!stock)return;
// TIMESTAMP END 2026-11-04T19:33:21+00:00 | REVISION R000014
 const section=document.createElement('section');section.className='tenon-dimensions';
// TIMESTAMP START 2026-11-04T19:33:21+00:00 | REVISION R000014
 const title=document.createElement('h3');title.textContent=rows.length?'Tenon dimensions':'Stock dimensions';section.appendChild(title);
// TIMESTAMP END 2026-11-04T19:33:21+00:00 | REVISION R000014
 const fmt=value=>Number(value.toFixed(3)).toString();
 for(const row of rows){
  const item=document.createElement('div');item.className='metric';
  const label=document.createElement('span');label.textContent='Into '+row.receiver;
  const value=document.createElement('strong');
  const cross=[row.widthIn,row.heightIn].filter(Number.isFinite);
// TIMESTAMP START 2026-11-04T19:33:21+00:00 | REVISION R000014
  const housed=row.shape?.includes('squared internal bearing');
  value.textContent=(housed?'Max. profile ':'')+(cross.length?cross.map(fmt).join(' × ')+' in · ':'')+fmt(row.depthIn)+' in deep';
// TIMESTAMP END 2026-11-04T19:33:21+00:00 | REVISION R000014
  item.append(label,value);section.appendChild(item);
// TIMESTAMP START 2026-11-04T19:33:21+00:00 | REVISION R000014
  if(housed){const note=document.createElement('small');note.textContent='Sloping heel; squared end bears against the internal mortise wall.';section.appendChild(note);}
  if(row.shape==='simple square-seated vertical tenon'){const note=document.createElement('small');note.textContent='Plain square tenon, seated upward into the cross beam.';section.appendChild(note);}
// TIMESTAMP END 2026-11-04T19:33:21+00:00 | REVISION R000014
  if(row.headWidthIn!=null){const note=document.createElement('small');note.textContent='Dovetail head width '+fmt(row.headWidthIn)+' in';section.appendChild(note);}
 }
// TIMESTAMP START 2026-11-04T19:33:21+00:00 | REVISION R000014
 if(stock){
  const item=document.createElement('div');item.className='metric';
  const label=document.createElement('span');label.textContent='Minimum blank, tenons included';
  const value=document.createElement('strong');value.textContent=[stock.widthIn,stock.depthIn,stock.minimumLengthIn].map(fmt).join(' × ')+' in';item.append(label,value);section.appendChild(item);
  const note=document.createElement('small');note.textContent='Blank length rounded up to ¼ in: '+fmt(stock.quarterInchLengthIn)+' in. Add your cutting and dressing allowances.';section.appendChild(note);
 }
 if(/^K[0-7]-[AB]$/.test(id)){
  const link=document.createElement('a');link.href='review/brace-shoulders.png';link.textContent='Brace shoulder and mortise detail';link.target='_blank';link.rel='noopener';section.appendChild(link);
 }
 host.appendChild(section);
// TIMESTAMP END 2026-11-04T19:33:21+00:00 | REVISION R000014
}
// TIMESTAMP START 2026-11-04T19:33:21+00:00 | REVISION R000014
const api={entries,blank,render};
// TIMESTAMP END 2026-11-04T19:33:21+00:00 | REVISION R000014
if(typeof module!=='undefined'&&module.exports)module.exports=api;root.OctagonJoineryDimensions=api;
})(typeof globalThis!=='undefined'?globalThis:this);
// TIMESTAMP END 2026-11-03T13:59:01-05:00 | REVISION R005033

// TIMESTAMP END 2026-11-04T23:23:25+00:00 | REVISION R000011
