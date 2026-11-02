// TIMESTAMP START 2026-11-01T22:47:54-05:00 | REVISION R004654
const CAVITIES=__CAVITY_JSON__;
let showHollows=true,hollowMode='removed',hollowXray=true,edgeMeasurementsOn=false;
const cavityMeshCache=new Map(),edgeMeasurementCache=new Map();
const edgeMeasurementLabels=[];
function appendEdgeMeasurements(host,p){
 if(!edgeMeasurementCache.has(p.id))edgeMeasurementCache.set(p.id,edgeMeasurementData(p));
 const measurements=edgeMeasurementCache.get(p.id),box=document.createElement('details'),summary=document.createElement('summary');box.dataset.inspectorKey='edgeLengths';summary.textContent='All edge lengths and face angles · '+measurements.length;box.appendChild(summary);
 const note=document.createElement('p');note.textContent='Inside = angle through the timber material at the edge; over 180° marks a concave corner. Planes = the smaller angle between the two face planes. These are different from the cut-to-axis angles above. Values describe the current geometric surfaces, not a saw setup.';box.appendChild(note);
 const toggle=document.createElement('button');toggle.textContent='Show small edge measurements';toggle.onclick=()=>{edgeMeasurementsOn=true;$('showEdgeMeasurements').checked=true;requestRender();};box.appendChild(toggle);
 const wrap=document.createElement('div');wrap.className='angle-table';wrap.setAttribute('tabindex','0');wrap.setAttribute('aria-label','All edge measurements for '+p.id);const table=document.createElement('table'),head=document.createElement('thead'),row=document.createElement('tr');
 for(const title of ['Edge','Length (in)','Inside','Planes']){const th=document.createElement('th');th.textContent=title;th.setAttribute('scope','col');row.appendChild(th);}head.appendChild(row);table.appendChild(head);const body=document.createElement('tbody');
 for(const e of measurements){const tr=document.createElement('tr');tr.dataset.edgeId=e.id;tr.title=edgeMeasurementDescription(e);for(const value of [e.id,num(e.length_in,3),e.interiorAngleDeg==null?'Unverified':angleText(e.interiorAngleDeg),e.planeAngleDeg==null?'Undefined':angleText(e.planeAngleDeg)]){const td=document.createElement('td');td.textContent=value;tr.appendChild(td);}body.appendChild(tr);}table.appendChild(body);wrap.appendChild(table);box.appendChild(wrap);
 const downloadButton=document.createElement('button');downloadButton.textContent='Download '+p.id+' edge measurements';downloadButton.onclick=()=>{const rows=[['Timber_ID','Edge_ID','Length_in','Interior_material_angle_deg','Acute_plane_angle_deg','Normal_angle_deg','Definition'],...measurements.map(e=>[p.id,e.id,e.length_in,e.interiorAngleDeg??'Unverified',e.planeAngleDeg??'Undefined',e.normalAngleDeg??'Undefined',edgeMeasurementDescription(e)])];download(p.id+'-edge-measurements.csv',rows.map(r=>r.map(csvCell).join(',')).join('\r\n'),'text/csv');};box.appendChild(downloadButton);host.appendChild(box);
}
function cavityRecords(){
 if(!showHollows)return [];
 return parts.filter(p=>selectedPartIds.has(p.id)&&isShown(p)).map(p=>({p,data:CAVITIES.parts[p.id],kind:hollowMode})).filter(r=>r.data&&r.data[r.kind]?.triangles.length);
}
function cavityRenderMesh(p,kind){
 const key=p.id+':'+kind;if(cavityMeshCache.has(key))return cavityMeshCache.get(key);
 const mesh=CAVITIES.parts[p.id]?.[kind];if(!mesh)return null;
 const raw=[],edgeRaw=[];
 for(const tri of mesh.triangles){const vv=tri.map(i=>mesh.vertices[i]),n=unit(cross(vsub(vv[1],vv[0]),vsub(vv[2],vv[0])));for(const v of vv)raw.push(...v,...n);}
 for(const edge of mesh.edges)for(const i of edge)edgeRaw.push(...mesh.vertices[i],0,1,0);
 const result={mesh,count:raw.length/6,edgeCount:edgeRaw.length/6,buffer:gl&&raw.length?buildBuffer(raw):null,edgeBuffer:gl&&edgeRaw.length?buildBuffer(edgeRaw):null};cavityMeshCache.set(key,result);return result;
}
function drawCavityVolumes(){
 const records=cavityRecords();if(!records.length)return;
 const fill=hollowMode==='unfilled'?[1,.12,.65]:[1,.82,.12],edge=hollowMode==='unfilled'?[.8,.0,.28]:[1,.35,.02];
 if(gl){
  gl.enable(gl.BLEND);gl.blendFunc(gl.SRC_ALPHA,gl.ONE_MINUS_SRC_ALPHA);gl.depthMask(false);if(hollowXray)gl.disable(gl.DEPTH_TEST);
  try{for(const {p,kind} of records){const m=cavityRenderMesh(p,kind);if(!m||!m.count)continue;
   gl.uniform3fv(loc.translation,offset(p));gl.uniform3fv(loc.color,fill);gl.uniform1f(loc.opacity,hollowXray?.48:.55);gl.uniform1f(loc.lineMode,1);bind(m.buffer);gl.drawArrays(gl.TRIANGLES,0,m.count);
   gl.uniform3fv(loc.color,edge);gl.uniform1f(loc.opacity,.95);gl.uniform1f(loc.lineMode,1);bind(m.edgeBuffer);gl.drawArrays(gl.LINES,0,m.edgeCount);
  }}finally{gl.enable(gl.DEPTH_TEST);gl.depthMask(true);gl.disable(gl.BLEND);gl.uniform1f(loc.opacity,1);gl.uniform1f(loc.lineMode,1);}
 }else if(fallback){
  // The fallback draws these overlays as X-rays; its status explains that limit.
  const faces=[];for(const {p,kind} of records){const m=cavityRenderMesh(p,kind),off=offset(p);for(const tri of m.mesh.triangles){const vv=tri.map(i=>vadd(m.mesh.vertices[i],off)),pp=vv.map(project);if(pp.every(Boolean))faces.push({pp,normal:unit(cross(vsub(vv[1],vv[0]),vsub(vv[2],vv[0]))),distance:pp.reduce((s,q)=>s+q.distance,0)/3});}}
  faces.sort((a,b)=>b.distance-a.distance);for(const f of faces){const c=surfaceDisplayColor(fill,f.normal);fallback.beginPath();f.pp.forEach((q,i)=>i?fallback.lineTo(q.x,q.y):fallback.moveTo(q.x,q.y));fallback.closePath();fallback.fillStyle='rgba('+c.map(v=>Math.round(v*255)).join(',')+',.24)';fallback.fill();}
  fallback.strokeStyle=cssColor(edge);fallback.lineWidth=1;for(const {p,kind} of records){const m=cavityRenderMesh(p,kind),off=offset(p);for(const e of m.mesh.edges){const pp=e.map(i=>project(vadd(m.mesh.vertices[i],off)));if(pp.some(q=>!q))continue;fallback.beginPath();fallback.moveTo(pp[0].x,pp[0].y);fallback.lineTo(pp[1].x,pp[1].y);fallback.stroke();}}
 }
}
function updateHollowStatus(){
 const host=$('hollowStatus');if(!Object.keys(CAVITIES.parts||{}).length){host.textContent='R01 contact geometry replaces the former fitted prototype. No current cavity-volume audit is assigned.';return;}if(!selected){host.textContent='Select a timber to reveal its recess volumes.';return;}
 const d=CAVITIES.parts[selected];if(!d){host.textContent='No verified cavity data for this timber.';return;}
 const removed=d.removed.volume_m3*1e6,empty=d.unfilled.volume_m3*1e6;
// TIMESTAMP START 2026-11-01T23:35:16-05:00 | REVISION R004670
 if(hollowMode==='removed')host.textContent=selected+': '+num(removed,2)+' cm³ of modeled recesses/notches. Amber shows removed stock, not extra wood. Complete cavity occupancy has not been independently verified.';
 else host.textContent=selected+': diagnostic residual '+num(empty,3)+' cm³. This calculation is not certified as an internal gap or harmless trimming; review against the mating geometry.';
// TIMESTAMP END 2026-11-01T23:35:16-05:00 | REVISION R004670
 if(explode>0)host.textContent+=' Classification refers to the assembled model; this view is exploded.';
 if(!gl)host.textContent+=' In 2D fallback, hollow volumes are always shown as X-rays.';
}
function updateEdgeMeasurementLabels(){
 for(const label of edgeMeasurementLabels)label.style.display='none';
 if(!edgeMeasurementsOn||!selected)return;
 const p=partById.get(selected);if(!p||!isShown(p))return;
 if(!edgeMeasurementCache.has(p.id))edgeMeasurementCache.set(p.id,edgeMeasurementData(p));
 const measurements=edgeMeasurementCache.get(p.id),candidates=[];
 for(const m of measurements){const a=project(vadd(m.a,offset(p))),b=project(vadd(m.b,offset(p))),q=project(vadd(m.midpoint,offset(p)));if(!a||!b||!q||q.x<10||q.x>width-10||q.y<55||q.y>height-20)continue;const span=Math.hypot(a.x-b.x,a.y-b.y);if(span<14||!edgeMeasurementVisible(p,m.midpoint))continue;candidates.push({m,q,span});}
 candidates.sort((a,b)=>b.span-a.span);const occupied=[];let count=0;
 for(const {m,q} of candidates){
  if(count>=32)break;const text=edgeMeasurementText(m),half=Math.min(150,Math.max(50,text.length*2.8));const rect={l:q.x-half,r:q.x+half,t:q.y-9,b:q.y+9};if(rect.l<8||rect.r>width-8||rect.t<55||rect.b>height-20)continue;if(occupied.some(r=>rect.l<r.r&&rect.r>r.l&&rect.t<r.b&&rect.b>r.t))continue;
  let label=edgeMeasurementLabels[count];if(!label){label=document.createElement('div');label.className='edge-measurement-label';labelLayer.appendChild(label);edgeMeasurementLabels.push(label);}
  label.textContent=text;label.title=edgeMeasurementDescription(m);label.style.left=q.x+'px';label.style.top=q.y+'px';label.style.display='block';occupied.push(rect);count++;
 }
}
function edgeMeasurementVisible(owner,midpoint){
 const target=vadd(midpoint,offset(owner)),delta=vsub(target,basis.eye),distance=length(delta);if(distance<1e-5)return false;
 const direction=vmul(delta,1/distance),limit=distance-1e-5;
 for(const p of parts){
  if(!isShown(p)||selectionAlpha(p)<1)continue;
  const origin=vsub(basis.eye,offset(p)),bounds=fittedBounds.get(p.id);let near=0,far=limit;
  if(bounds){for(let k=0;k<3;k++){if(Math.abs(direction[k])<1e-12){if(origin[k]<bounds.min[k]-1e-6||origin[k]>bounds.max[k]+1e-6){far=-1;break;}}else{let a=(bounds.min[k]-1e-6-origin[k])/direction[k],b=(bounds.max[k]+1e-6-origin[k])/direction[k];if(a>b)[a,b]=[b,a];near=Math.max(near,a);far=Math.min(far,b);if(near>far)break;}}if(near>far)continue;}
  for(const tri of p.triangles||[]){const hit=triangleHit(origin,direction,...tri.map(i=>p.vertices[i]));if(hit!=null&&hit<limit)return false;}
 }
 return true;
}
$('showHollows').onchange=e=>{showHollows=e.target.checked;updateHollowStatus();requestRender();};
$('hollowMode').onchange=e=>{hollowMode=e.target.value==='unfilled'?'unfilled':'removed';updateHollowStatus();requestRender();};
$('hollowXray').onchange=e=>{hollowXray=e.target.checked;requestRender();};
$('showEdgeMeasurements').onchange=e=>{edgeMeasurementsOn=e.target.checked;requestRender();};


// TIMESTAMP END 2026-11-01T22:47:54-05:00 | REVISION R004654
