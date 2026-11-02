/* Current-mesh planar cut-face measurements. No fabrication or structural approval. */
(function(root){
'use strict';
const add=(a,b)=>a.map((x,i)=>x+b[i]),sub=(a,b)=>a.map((x,i)=>x-b[i]),mul=(a,s)=>a.map(x=>x*s),dot=(a,b)=>a.reduce((s,x,i)=>s+x*b[i],0),cross=(a,b)=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]],len=a=>Math.hypot(...a),unit=a=>mul(a,1/len(a)),deg=x=>x*180/Math.PI,clamp=x=>Math.max(-1,Math.min(1,x));
const cache=new Map();
const definitions={offSquare:'Acute angle between plane normal and stock longitudinal axis:0° is square end;90° is parallel to the axis.',miter:'Geometric yaw of the canonical plane normal toward +stock width from +axis, atan2(nWidth,nAxis). Not a machine miter setting.',bevel:'Geometric normal tilt toward +stock depth, atan2(nDepth,hypot(nAxis,nWidth)). Not a machine bevel setting.',dihedral:'Adjacent-plane acute angle; material-side interior/reflex angle only when the edge analyser verifies closed consistent topology. No self-intersection certification.',location:'Coordinates relative to the recorded axis_start in the validated stock frame. Current fitted-envelope bounds, not original blank or machining datums.',scope:'Planar mesh patches only. A plane is not necessarily a manufacturing operation. Curves are faceted/unresolved; kerf, tool access, tolerances, assembly and safety are not inferred.'};
function fingerprint(s){let h=2166136261;for(let i=0;i<s.length;i++)h=Math.imul(h^s.charCodeAt(i),16777619);return (h>>>0).toString(16).padStart(8,'0');}
function frameFor(p){
 const f=p.stock_frame;if(!f||!['axis','width','depth'].every(k=>Array.isArray(f[k])&&f[k].length===3&&f[k].every(Number.isFinite)&&len(f[k])>1e-10))return null;
 const out=Object.fromEntries(['axis','width','depth'].map(k=>[k,unit(f[k])]));
 if(Math.max(Math.abs(dot(out.axis,out.width)),Math.abs(dot(out.axis,out.depth)),Math.abs(dot(out.width,out.depth)))>1e-5)return null;
 return {...out,origin:Array.isArray(p.axis_start)&&p.axis_start.every(Number.isFinite)?p.axis_start.slice():[0,0,0],originStatus:Array.isArray(p.axis_start)?'Recorded A reference, not verified machining datum':'World origin fallback; machining datum unknown',handedness:dot(cross(out.axis,out.width),out.depth)};
}
function sharesEdge(a,b,tol){
 for(let i=0;i<3;i++)for(let j=0;j<3;j++){
  const x=a[i],u=sub(a[(i+1)%3],x),L=len(u),v=sub(b[(j+1)%3],b[j]);if(L<tol||len(v)<tol)continue;
  const d=mul(u,1/L);if(len(cross(d,unit(v)))>1e-7||len(cross(sub(b[j],x),d))>tol)continue;
  const lo=Math.min(dot(sub(b[j],x),d),dot(sub(b[(j+1)%3],x),d)),hi=Math.max(dot(sub(b[j],x),d),dot(sub(b[(j+1)%3],x),d));
  if(Math.min(L,hi)-Math.max(0,lo)>tol)return true;
 }return false;
}
function analysePart(part,options={}){
 const key=JSON.stringify([part.id,part.vertices,part.triangles,part.stock_frame,part.axis_start,part.material,part.fabrication_dimensions_valid,options.revision||null,options.parameters||null]);
 if(cache.has(key))return cache.get(key);
 const tol=1e-7,V=part.vertices||[],T=part.triangles||[],frame=frameFor(part),warnings=[],planes=[];let skipped=0;
 if(!frame)warnings.push('Validated orthogonal stock frame unavailable: local miter/bevel and machining reference coordinates omitted.');
 if(part.fabrication_dimensions_valid===false||part.material==='steel'||part.material==='surface')warnings.push('Non-fabrication/possibly faceted component: planar facet measurements are not curved-surface cuts or a fabrication schedule.');
 function local(v){const q=sub(v,frame.origin);return [dot(q,frame.axis),dot(q,frame.width),dot(q,frame.depth)];}
 const bounds=frame&&V.length?{min:[0,1,2].map(i=>Math.min(...V.map(v=>local(v)[i]))),max:[0,1,2].map(i=>Math.max(...V.map(v=>local(v)[i])))}:null;
 for(let index=0;index<T.length;index++){
  const points=T[index].map(i=>V[i]);if(points.length!==3||points.some(p=>!p||!p.every(Number.isFinite))){skipped++;continue;}
  let n=cross(sub(points[1],points[0]),sub(points[2],points[0])),area=len(n)/2;if(area<1e-14){skipped++;continue;}n=unit(n);
  const first=n.find(v=>Math.abs(v)>1e-10);if(first<0)n=mul(n,-1);const d=dot(n,points[0]);
  let plane=planes.find(p=>dot(p.normal,n)>1-1e-12&&Math.abs(p.offset-d)<tol);
  if(!plane){plane={normal:n,offset:d,tris:[]};planes.push(plane);}plane.tris.push({index,points,area,center:mul(add(add(...points.slice(0,2)),points[2]),1/3)});
 }
 const patches=[];
 for(const plane of planes){const remaining=new Set(plane.tris.map((_,i)=>i));while(remaining.size){const seed=remaining.values().next().value,queue=[seed],group=[];remaining.delete(seed);while(queue.length){const i=queue.pop();group.push(plane.tris[i]);for(const j of remaining)if(sharesEdge(plane.tris[i].points,plane.tris[j].points,tol)){remaining.delete(j);queue.push(j);}}patches.push({...plane,tris:group});}}
 patches.sort((a,b)=>{for(let i=0;i<3;i++){const d=a.normal[i]-b.normal[i];if(Math.abs(d)>1e-10)return d;}if(Math.abs(a.offset-b.offset)>tol)return a.offset-b.offset;const ca=a.tris[0].center,cb=b.tris[0].center;for(let i=0;i<3;i++)if(Math.abs(ca[i]-cb[i])>tol)return ca[i]-cb[i];return 0;});
 const triangleFace=new Map(),faces=patches.map((p,i)=>{
  const id=String(part.id)+'-F'+String(i+1).padStart(3,'0'),area=p.tris.reduce((s,t)=>s+t.area,0),centroid=p.tris.reduce((s,t)=>add(s,mul(t.center,t.area/area)),[0,0,0]),points=p.tris.flatMap(t=>t.points);
  p.tris.forEach(t=>triangleFace.set(t.index,id));let nLocal=null,angles={offSquareDeg:null,miterDeg:null,bevelDeg:null},classification='Planar mesh patch; stock reference unavailable',localBounds=null,insets=null;
  if(frame){nLocal=[dot(p.normal,frame.axis),dot(p.normal,frame.width),dot(p.normal,frame.depth)].map(x=>Math.abs(x)<1e-10?0:x);if(nLocal.find(x=>x!==0)<0)nLocal=nLocal.map(x=>-x);const[a,w,d]=nLocal,plan=Math.hypot(a,w);angles={offSquareDeg:deg(Math.acos(clamp(Math.abs(a)))),miterDeg:plan>1e-10?deg(Math.atan2(w,a)):null,bevelDeg:deg(Math.atan2(d,plan))};
   localBounds={min:[0,1,2].map(k=>Math.min(...points.map(v=>local(v)[k]))),max:[0,1,2].map(k=>Math.max(...points.map(v=>local(v)[k])))};
   insets={fromEnvelopeMinM:localBounds.min.map((x,k)=>x-bounds.min[k]),fromEnvelopeMaxM:localBounds.max.map((x,k)=>bounds.max[k]-x)};
   const axis=nLocal.findIndex(x=>Math.abs(Math.abs(x)-1)<1e-7),onEnvelope=axis>=0&&(Math.abs(localBounds.min[axis]-bounds.min[axis])<tol||Math.abs(localBounds.max[axis]-bounds.max[axis])<tol);
   classification=axis>=1&&onEnvelope?'Stock-aligned fitted-envelope surface (uncut status unverified)':axis===0?(onEnvelope?'End plane at fitted envelope':'Internal shoulder/step plane'):axis>=1?'Recess/step plane parallel to stock face':'Oblique fitted face / cut candidate';
  }
  return {id,partId:String(part.id),classification,normal:p.normal,planeOffsetM:p.offset,localNormal:nLocal,angles,areaM2:area,centroidM:centroid,localCentroidM:frame?local(centroid):null,localBounds,insets,triangleIndices:p.tris.map(t=>t.index),vertices:points,depthStatus:'Insets are from current fitted-envelope faces; actual cut depth from original stock is unknown.',contactStatus:'No mating-contact inference: current piece mesh alone cannot establish its mate or capacity.'};
 });
 const edgeAPI=root.TimberEdgeMeasurements||(typeof require==='function'?require('./edge-measurements.js'):null);let edges=[],topology=null;
 if(edgeAPI){const e=edgeAPI.analyse(V,T);topology=e.topology;edges=e.edges.map((x,i)=>({...x,id:String(part.id)+'-D'+String(i+1).padStart(3,'0'),faceIds:[...new Set(x.adjacentTriangleIndices.map(t=>triangleFace.get(t)).filter(Boolean))]}));}
 else warnings.push('Dihedral analyser unavailable; adjacent edge measurements omitted.');
 if(skipped)warnings.push(skipped+' invalid/degenerate triangles omitted.');
 warnings.push('Face IDs belong to this geometry revision and may change when geometry changes.','Complete manufacturing-cut coverage is not established. Meshes do not identify the original blank, curved operations or concealed/unmodeled work.');
 const result={partId:String(part.id),revision:options.revision||null,parameters:options.parameters||null,geometryFingerprint:fingerprint(key),frame,referenceFaces:bounds?{bounds,labels:['A/min axis envelope','B/max axis envelope','−width envelope','+width envelope','−depth envelope','+depth envelope']}:null,faces,edges,topology,validTriangleCount:T.length-skipped,skippedTriangleCount:skipped,warnings,definitions};
 cache.set(key,result);if(cache.size>128)cache.delete(cache.keys().next().value);return result;
}
function analyseModel(model,options={}){const meta={...options,revision:options.revision||model.revision||null};return {revision:meta.revision,parameters:meta.parameters||null,parts:(model.parts||[]).map(p=>analysePart(p,meta)),definitions,scope:'Current supplied model only; all planar face records, not a verified manufacturing cut list.'};}
async function analyseModelAsync(model,options={},yieldControl=()=>new Promise(resolve=>setTimeout(resolve,0))){const meta={...options,revision:options.revision||model.revision||null},parts=[];for(const p of model.parts||[]){if(options.isCancelled?.())return null;parts.push(analysePart(p,meta));await yieldControl();}if(options.isCancelled?.())return null;return {revision:meta.revision,parameters:meta.parameters||null,parts,definitions,scope:'Current supplied model only; all planar face records, not a verified manufacturing cut list.'};}
function toCSV(report){const reports=report.parts||[report],rows=[['revision','geometry_fingerprint','piece','face','classification','off_square_deg','normal_miter_yaw_deg','normal_bevel_tilt_deg','area_m2','local_axis_m','local_width_m','local_depth_m','cut_depth_status','contact_status']];for(const p of reports)for(const f of p.faces)rows.push([p.revision,p.geometryFingerprint,p.partId,f.id,f.classification,f.angles.offSquareDeg,f.angles.miterDeg,f.angles.bevelDeg,f.areaM2,...(f.localCentroidM||[null,null,null]),f.depthStatus,f.contactStatus]);return rows.map(r=>r.map(v=>'"'+String(v??'').replaceAll('"','""')+'"').join(',')).join('\r\n');}
const api={analysePart,analyseModel,analyseModelAsync,toCSV,definitions};root.OctagonCutFaces=api;if(typeof module!=='undefined'&&module.exports)module.exports=api;
})(typeof globalThis!=='undefined'?globalThis:this);
