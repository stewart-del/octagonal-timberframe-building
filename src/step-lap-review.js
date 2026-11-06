// TIMESTAMP START 2026-11-04T23:23:25+00:00 | REVISION R000011
// TIMESTAMP START 2026-11-04T20:33:26+00:00 | REVISION R000023
/* Separate proposed CSG joinery comparison. Never replaces canonical parts or loads. */
(function(root){
'use strict';
const IN=.0254;
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const add=(a,b)=>a.map((v,i)=>v+b[i]),sub=(a,b)=>a.map((v,i)=>v-b[i]),mul=(a,s)=>a.map(v=>v*s),dot=(a,b)=>a.reduce((s,v,i)=>s+v*b[i],0),cross=(a,b)=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]],norm=a=>Math.hypot(...a),unit=a=>norm(a)>1e-12?mul(a,1/norm(a)):[0,0,0];
function localPoint(v,frame){const q=sub(v,frame.origin_m||[0,0,0]);return [dot(q,frame.horizontal||[1,0,0]),dot(q,frame.up||[0,1,0]),dot(q,frame.transverse||[0,0,1])].map(x=>x/IN);}
function localVector(v,frame){return [dot(v,frame.horizontal||[1,0,0]),dot(v,frame.up||[0,1,0]),dot(v,frame.transverse||[0,0,1])];}
function clipPolygon(points,axis,bound,keepBelow){const out=[];if(!points.length)return out;let a=points.at(-1),inside=x=>keepBelow?x[axis]<=bound+1e-8:x[axis]>=bound-1e-8,ia=inside(a);for(const b of points){const ib=inside(b);if(ib!==ia){const t=(bound-a[axis])/(b[axis]-a[axis]);out.push(a.map((v,i)=>v+(b[i]-v)*t));}if(ib)out.push(b);a=b;ia=ib;}return out;}
function cropPolygon(points,bounds){for(let k=0;k<3;k++){points=clipPolygon(points,k,bounds[0][k],false);points=clipPolygon(points,k,bounds[1][k],true);}return points;}
function cropLine(a,b,bounds){let lo=0,hi=1;for(let k=0;k<3;k++){const d=b[k]-a[k];if(Math.abs(d)<1e-12){if(a[k]<bounds[0][k]||a[k]>bounds[1][k])return null;continue;}let x=(bounds[0][k]-a[k])/d,y=(bounds[1][k]-a[k])/d;if(x>y)[x,y]=[y,x];lo=Math.max(lo,x);hi=Math.min(hi,y);if(lo>hi)return null;}return [a.map((v,i)=>v+(b[i]-v)*lo),a.map((v,i)=>v+(b[i]-v)*hi)];}
function projection(p,view){if(view==='top')return [p[0],-p[2],p[1]];if(view==='section')return [p[0],-p[1],p[2]];return [.70710678*(p[0]-p[2]),.33129458*(p[0]+p[2])-.8834522*p[1],.62469505*(p[0]+p[2])+.46852129*p[1]];}
function sectionSegments(points){const out=[];for(let k=0;k<points.length;k++){const a=points[k],b=points[(k+1)%points.length];if(Math.abs(a[2])<1e-8)out.push(a);if((a[2]<-1e-8&&b[2]>1e-8)||(a[2]>1e-8&&b[2]<-1e-8)){const t=-a[2]/(b[2]-a[2]);out.push(a.map((v,i)=>v+(b[i]-v)*t));}}const unique=out.filter((p,i)=>!out.slice(0,i).some(q=>norm(sub(p,q))<1e-7));return unique.length===2?[unique]:[];}
function clippingCaps(part,verts,bounds){const caps=[];for(let axis=0;axis<3;axis++)for(const bound of [bounds[0][axis],bounds[1][axis]]){const links=new Map(),points=new Map(),segments=new Map(),key=p=>p.map(v=>v.toFixed(6)).join(',');
 for(const tri of part.triangles||[]){const hit=[];for(let k=0;k<3;k++){const a=verts[tri[k]],b=verts[tri[(k+1)%3]],da=a[axis]-bound,db=b[axis]-bound;if(Math.abs(da)<1e-8)hit.push(a);if(da*db<0){const t=-da/(db-da);hit.push(a.map((v,i)=>v+(b[i]-v)*t));}}const q=hit.filter((p,i)=>!hit.slice(0,i).some(x=>norm(sub(p,x))<1e-7));if(q.length!==2)continue;const ka=key(q[0]),kb=key(q[1]);if(ka===kb)continue;const edge=[ka,kb].sort().join('|');segments.set(edge,[ka,kb]);points.set(ka,q[0]);points.set(kb,q[1]);}
 for(const [edge,[a,b]] of segments){for(const [x,y] of [[a,b],[b,a]]){if(!links.has(x))links.set(x,[]);links.get(x).push([y,edge]);}}
 const used=new Set();for(const [startEdge,[start,next]] of segments){if(used.has(startEdge))continue;used.add(startEdge);const loop=[points.get(start)],visited=new Set([start]);let current=next,closed=false;for(let i=0;i<=segments.size;i++){if(current===start){closed=true;break;}if(visited.has(current))break;visited.add(current);loop.push(points.get(current));const step=(links.get(current)||[]).find(([,edge])=>!used.has(edge));if(!step)break;used.add(step[1]);current=step[0];}if(closed){const poly=cropPolygon(loop,bounds);if(poly.length>2)caps.push(poly);}}
 }return caps;}
function featureEdges(part,verts){const buckets=new Map();for(const t of part.triangles||[]){const n=unit(cross(sub(verts[t[1]],verts[t[0]]),sub(verts[t[2]],verts[t[0]])));for(let k=0;k<3;k++){const a=t[k],b=t[(k+1)%3],key=[a,b].sort((x,y)=>x-y).join(':');if(!buckets.has(key))buckets.set(key,{a,b,normals:[]});buckets.get(key).normals.push(n);}}return [...buckets.values()].filter(e=>e.normals.length!==2||dot(e.normals[0],e.normals[1])<.9999).map(e=>[verts[e.a],verts[e.b]]);}
function colorShade(hex,n){const light=.72+.28*Math.abs(dot(unit(n),unit([.3,.8,1])));const rgb=hex.match(/[0-9a-f]{2}/ig).map(v=>Math.round(parseInt(v,16)*light));return '#'+rgb.map(v=>v.toString(16).padStart(2,'0')).join('');}
function drawing(variant,{proposed=true,view='iso',explode=false,removed=false,normals=false,standalone=true}={}){
 const frame=variant.local_frame||{},bounds=variant.review_bounds_inches||[[-16,-12,-16],[16,12,16]],source=proposed?variant.proposed_parts:variant.baseline_parts,parts=source||[],polygons=[],edges=[],sections=[];
 const colorById=new Map((variant.member_ids||parts.map(p=>p.id)).map((id,i)=>[id,i?'#c59d68':'#789b92']));
 const records=parts.map(p=>({p,color:colorById.get(p.id)||'#8b9b90',opacity:1,overlay:false}));
 if(proposed&&removed){for(const p of variant.removed_parts||[])records.push({p,color:'#d67c2e',opacity:.55,overlay:true});for(const p of variant.added_parts||[])records.push({p,color:'#4b9b71',opacity:.7,overlay:true});}
 for(const record of records){const {p,color,opacity,overlay}=record,verts=(p.vertices||[]).map(v=>localPoint(v,frame)),member=p.member_id||p.id,offset=explode&&member===variant.member_ids?.[0]?[0,6,0]:[0,0,0];
  for(const t of p.triangles||[]){const raw=t.map(i=>verts[i]);if(raw.some(v=>!v))continue;if(view==='section'){for(const seg of sectionSegments(raw)){const clipped=cropLine(...seg,bounds);if(clipped)sections.push({points:clipped.map(v=>add(v,offset)),color,opacity,overlay});}continue;}const clip=cropPolygon(raw,bounds);if(clip.length<3)continue;const points=clip.map(v=>add(v,offset)),q=points.map(v=>projection(v,view)),n=cross(sub(raw[1],raw[0]),sub(raw[2],raw[0]));polygons.push({q,depth:q.reduce((s,p)=>s+p[2],0)/q.length,color:colorShade(color,n),opacity,overlay});}
  if(view!=='section')for(const cap of clippingCaps(p,verts,bounds)){const q=cap.map(v=>projection(add(v,offset),view)),n=cross(sub(cap[1],cap[0]),sub(cap[2],cap[0]));polygons.push({q,depth:q.reduce((s,p)=>s+p[2],0)/q.length,color:colorShade(color,n),opacity,overlay});}
  if(view!=='section')for(const seg of featureEdges(p,verts)){const clipped=cropLine(...seg,bounds);if(clipped)edges.push({points:clipped.map(v=>add(v,offset)),color:overlay?color:'#33464a',opacity:overlay?.6:.62});}
 }
 polygons.sort((a,b)=>a.depth-b.depth);
 const extent=[];for(const x of [bounds[0][0],bounds[1][0]])for(const y of [bounds[0][1],bounds[1][1]+(explode?6:0)])for(const z of [bounds[0][2],bounds[1][2]])extent.push(projection([x,y,z],view));
 const lo=[Math.min(...extent.map(p=>p[0])),Math.min(...extent.map(p=>p[1]))],hi=[Math.max(...extent.map(p=>p[0])),Math.max(...extent.map(p=>p[1]))],scale=Math.min(500/(hi[0]-lo[0]),330/(hi[1]-lo[1])),ox=280-(lo[0]+hi[0])*scale/2,oy=245-(lo[1]+hi[1])*scale/2;
 const point=p=>{const q=projection(p,view);return [ox+q[0]*scale,oy+q[1]*scale];},xy=q=>`${(ox+q[0]*scale).toFixed(2)},${(oy+q[1]*scale).toFixed(2)}`;
 let body=polygons.map(p=>`<polygon points="${p.q.map(xy).join(' ')}" fill="${p.color}" stroke="${p.color}" stroke-width=".22" opacity="${p.opacity}"/>`).join('');
 const line=(seg,color,width,opacity)=>`<path d="M${point(seg[0]).map(x=>x.toFixed(2)).join(',')}L${point(seg[1]).map(x=>x.toFixed(2)).join(',')}" stroke="${color}" stroke-width="${width}" fill="none" opacity="${opacity}"/>`;
 body+=(view==='section'?sections:edges).map(e=>line(e.points,e.color,view==='section'?(e.overlay?4:2):.65,e.opacity)).join('');
 let normalCount=0;if(proposed&&normals)for(const face of variant.contact_faces||[]){if(!face.centroid_m||!face.normal_on_rafter)continue;const a=add(localPoint(face.centroid_m,frame),explode?[0,6,0]:[0,0,0]),b=add(a,mul(localVector(face.normal_on_rafter,frame),4)),q=point(a),r=point(b);body+=`<path d="M${q.join(',')}L${r.join(',')}" fill="none" stroke="#a84762" stroke-width="2" marker-end="url(#normalArrow)"/><circle cx="${q[0]}" cy="${q[1]}" r="2.3" fill="#a84762"/>`;normalCount++;}
 const title=proposed?(standalone?'PROPOSED STEP-LAP JOINERY':'Proposed'):'Current baseline';const subtitle=view==='section'?'Longitudinal center section through actual meshes':view==='top'?'Top view of cropped mesh geometry':'Isometric mesh view · hidden feature edges included';
 const svg=`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 560 480" role="img" aria-label="${esc(title+' '+variant.title+' '+subtitle)}"><defs><marker id="normalArrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse"><path d="M0 0L10 5L0 10Z" fill="#a84762"/></marker></defs><rect width="560" height="480" fill="#fbfcf9"/><style>text{font-family:Arial,sans-serif;fill:#243d42}.title{font-size:15px;font-weight:bold}.small{font-size:11px}</style><text x="22" y="28" class="title">${title}</text><text x="22" y="49" class="small">${esc(subtitle)}${explode?' · rafter lifted 6 in for inspection':''}</text><g>${body}</g><text x="22" y="435" class="small">${esc((variant.member_ids||[]).join(' + '))} · ${proposed?'real proposed CSG mesh':'unchanged saved mesh'} · local crop, not a full member drawing</text>${standalone?`<text x="22" y="455" class="small">NOT FABRICATION APPROVED · ${normals&&proposed?'Arrows are face normals, not forces':'Geometry comparison only'}</text>`:''}</svg>`;
 return {svg,polygonCount:polygons.length,edgeCount:edges.length,sectionCount:sections.length,normalCount,partCount:parts.length,view};
}
const rounded=v=>typeof v==='number'?Number(v.toFixed(3)).toString():String(v??'');
function flatEntries(value,prefix=''){const out=[];for(const [key,v] of Object.entries(value||{})){const label=(prefix?prefix+' · ':'')+key.replaceAll('_',' ');if(v&&typeof v==='object'&&!Array.isArray(v)){if('value' in v)out.push([label,rounded(v.value)+' '+(v.unit||'')+(v.basis?' — '+v.basis:'')]);}else if(!Array.isArray(v))out.push([label,rounded(v)]);}return out;}
function summaryRows(v){const m=v.measurements||{},rows=flatEntries(v.parameters,'Parameter');
 const pair=(a,b,unit)=>rounded(a)+' → '+rounded(b)+' '+unit;
 if(Number.isFinite(m.baseline_horizontal_bearing_area_in2))rows.push(['Horizontal bearing area · current → proposed',pair(m.baseline_horizontal_bearing_area_in2,m.proposed_horizontal_bearing_area_in2,'in²')]);
 if(Number.isFinite(m.proposed_inclined_contact_area_in2))rows.push(['Proposed inclined contact area',rounded(m.proposed_inclined_contact_area_in2)+' in² — face normal includes a horizontal component']);
 const cheeks=m.transverse_cheek_contacts||[];if(cheeks.length)rows.push(['Opposed transverse cheek contact areas',cheeks.map(c=>rounded(c.area_in2)+' in²').join(' and ')]);
 if(Number.isFinite(m.receiver_removed_volume_in3))rows.push(['Wood removed from receiving timber',rounded(m.receiver_removed_volume_in3)+' in³']);
 if(Number.isFinite(m.rafter_retained_stock_volume_in3))rows.push(['Additional rafter wood retained within original stock',rounded(m.rafter_retained_stock_volume_in3)+' in³']);
 for(const sec of m.remaining_local_sections||[])rows.push([sec.member_id+' named local section · current → proposed',pair(sec.baseline_area_in2,sec.proposed_area_in2,'in²')]);
 if(Array.isArray(m.neighbor_interferences))rows.push(['Recorded neighboring interferences',String(m.neighbor_interferences.length)]);
 return rows;}
function tradeoff(v){const m=v.measurements||{},a=m.baseline_horizontal_bearing_area_in2,b=m.proposed_horizontal_bearing_area_in2,sec=(m.remaining_local_sections||[]).find(s=>s.member_id===v.member_ids?.[1]&&/^P\d+$/.test(s.member_id));let text='';
 if(Number.isFinite(a)&&Number.isFinite(b))text='Horizontal bearing area: '+rounded(a)+' → '+rounded(b)+' in². ';
 if(sec)text+='Post top-band section: '+rounded(sec.baseline_area_in2)+' → '+rounded(sec.proposed_area_in2)+' in². ';
 return text+(sec?'The top-band slice is not the whole-post minimum. ':'Contact is redistributed onto inclined faces. ')+'Area alone establishes neither capacity loss nor gain.';}
function createController(data,{document,save,release=()=>{},onOpen=()=>{},onClose=()=>{}}){
// TIMESTAMP START 2026-11-04T19:27:13+00:00 | REVISION R000001
 if(typeof data==='function'){
  let controller=null,pending=null;
  const button=document.getElementById('openStepLap');
  button.textContent='Earlier joint study';
  const open=()=>{
   if(controller){controller.open();return Promise.resolve(controller);}
   if(pending)return pending;
   button.setAttribute('aria-busy','true');
   pending=Promise.resolve().then(data).then(value=>{
    controller=createController(value,{document,save,release,onOpen,onClose});
    controller.open();return controller;
   }).catch(error=>{
    pending=null;document.getElementById('parameterStatus').textContent='Could not load the earlier joint study. Click to retry. '+error.message;
    return null;
   }).finally(()=>button.removeAttribute('aria-busy'));
   return pending;
  };
  button.onclick=open;
  return {open,close:()=>controller?.close(),set:(...args)=>controller?.set(...args)};
 }
// TIMESTAMP END 2026-11-04T19:27:13+00:00 | REVISION R000001
 const $=id=>document.getElementById(id),state={open:false,variantId:data.variants?.[0]?.id||'',view:'iso',explode:true,removed:false,normals:false};let returnFocus=null;
 const selected=()=>data.variants.find(v=>v.id===state.variantId)||data.variants[0];
 const writeList=(id,items)=>{const host=$(id);host.replaceChildren();for(const text of items){const li=document.createElement('li');li.textContent=text;host.appendChild(li);}};
// TIMESTAMP START 2026-11-03T17:17:55-05:00 | REVISION R005072
 function render(){const v=selected();if(!v)return;const options={view:state.view,explode:state.explode,removed:state.removed,normals:state.normals,standalone:false};$('stepLapCurrent').innerHTML=drawing(v,{...options,proposed:false}).svg;$('stepLapProposed').innerHTML=drawing(v,{...options,proposed:true}).svg;
  $('stepLapState').textContent='Archived perimeter study: these comparison meshes predate the current three-inch tenons and centered braces. Current dimensions are in the main model inspector. '+(v.geometry_status==='REJECTED'?'Candidate interference / geometry issue — do not replicate. ':'')+tradeoff(v);
  $('stepLapState').className='step-lap-state'+(v.geometry_status==='REJECTED'?' warning':'');
  const rows=$('stepLapMetrics');rows.replaceChildren();for(const [label,value] of summaryRows(v)){const tr=document.createElement('tr'),a=document.createElement('td'),b=document.createElement('td');a.textContent=label;b.textContent=value;tr.append(a,b);rows.appendChild(tr);}
  writeList('stepLapLimitations',[...(v.findings||[]),...(data.limitations||[])]);$('stepLapView').value=state.view;$('stepLapPair').value=v.id;$('stepLapExplode').checked=state.explode;$('stepLapRemoved').checked=state.removed;$('stepLapNormals').checked=state.normals;
 }
// TIMESTAMP END 2026-11-03T17:17:55-05:00 | REVISION R005072
 function open(){if(state.open)return;release();returnFocus=document.activeElement;state.open=true;$('stepLapModal').classList.add('open');$('stepLapModal').setAttribute('aria-hidden','false');onOpen();render();$('closeStepLap').focus();}
 function close(){if(!state.open)return;state.open=false;$('stepLapModal').classList.remove('open');$('stepLapModal').setAttribute('aria-hidden','true');onClose();returnFocus?.focus?.();}
 function set(key,value){if(!Object.prototype.hasOwnProperty.call(state,key)||key==='open')return;if(key==='variantId'&&!data.variants.some(v=>v.id===value))return;if(key==='view'&&!['iso','top','section'].includes(value))return;state[key]=value;if(state.open)render();}
 const pairs=$('stepLapPair');pairs.replaceChildren();for(const v of data.variants||[]){const option=document.createElement('option');option.value=v.id;option.textContent=v.title||v.id;pairs.appendChild(option);}
 // TIMESTAMP START 2026-11-03T17:17:55-05:00 | REVISION R005072
 $('openStepLap').textContent='Earlier joint study';
 // TIMESTAMP END 2026-11-03T17:17:55-05:00 | REVISION R005072
 $('openStepLap').onclick=open;$('closeStepLap').onclick=close;$('stepLapPair').onchange=()=>set('variantId',$('stepLapPair').value);$('stepLapView').onchange=()=>set('view',$('stepLapView').value);
 for(const [id,key] of [['stepLapExplode','explode'],['stepLapRemoved','removed'],['stepLapNormals','normals']])$(id).onchange=()=>set(key,$(id).checked);
 $('stepLapReset').onclick=()=>{Object.assign(state,{view:'iso',explode:false,removed:false,normals:false});render();};
 $('stepLapJSON').onclick=()=>{const v=selected();save(`PROPOSED-NOT-FABRICATION-${v.id}.json`,JSON.stringify({schema_version:data.schema_version,status:'PROPOSED STEP-LAP JOINERY — NOT FABRICATION APPROVED',baseline_model_sha256:data.baseline_model_sha256,canonical_model_unchanged:true,limitations:data.limitations,variant:v},null,2),'application/json');};
 $('stepLapSVG').onclick=()=>{const v=selected();save(`PROPOSED-NOT-FABRICATION-${v.id}-${state.view}.svg`,drawing(v,{proposed:true,view:state.view,explode:state.explode,removed:state.removed,normals:state.normals}).svg,'image/svg+xml');};
 $('stepLapModal').onclick=e=>{if(e.target===$('stepLapModal'))close();};
 document.addEventListener('keydown',e=>{if(!state.open)return;if(e.key==='Escape'){e.preventDefault();e.stopPropagation?.();close();}else if(e.key==='Tab'){const focusable=[...$('stepLapModal').querySelectorAll('button,select,input,summary')].filter(e=>!e.disabled),first=focusable[0],last=focusable.at(-1);if(e.shiftKey&&document.activeElement===first){e.preventDefault();last?.focus();}else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first?.focus();}}},true);
 return {state,open,close,set,render,selected};
}
root.OctagonStepLap={drawing,localPoint,projection,cropPolygon,cropLine,sectionSegments,flatEntries,summaryRows,tradeoff,createController};
})(typeof globalThis!=='undefined'?globalThis:this);
// TIMESTAMP END 2026-11-04T20:33:26+00:00 | REVISION R000023

// TIMESTAMP END 2026-11-04T23:23:25+00:00 | REVISION R000011
