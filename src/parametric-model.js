// TIMESTAMP START 2026-11-04T23:23:25+00:00 | REVISION R000011
// TIMESTAMP START 2026-11-03T13:09:36-05:00 | REVISION R005024
/* Parameterized stock and complementary joints. All dimensions are nominal geometry. */
(function(root){
'use strict';
const I=.0254,C=Math.cos(Math.PI/8),BASE_P=1/3,BASE_WALL=89.03615129287599;
const add=(a,b)=>a.map((v,i)=>v+b[i]),sub=(a,b)=>a.map((v,i)=>v-b[i]),mul=(a,s)=>a.map(v=>v*s),dot=(a,b)=>a.reduce((s,v,i)=>s+v*b[i],0),cross=(a,b)=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]],unit=a=>mul(a,1/Math.hypot(...a));
const clone=x=>JSON.parse(JSON.stringify(x)),radial=k=>[Math.cos(k*Math.PI/4),0,-Math.sin(k*Math.PI/4)],tangent=k=>[-Math.sin(k*Math.PI/4),0,-Math.cos(k*Math.PI/4)];
function parameters(input={}){
 let wallHeightIn=Number(input.wallHeightIn??BASE_WALL);const pitch=Number(input.pitch??4);if(Math.abs(wallHeightIn-BASE_WALL)<.0005)wallHeightIn=BASE_WALL;
 if(!Number.isFinite(wallHeightIn)||wallHeightIn<BASE_WALL-1e-7||wallHeightIn>144)throw Error('Wall height must be between '+BASE_WALL.toFixed(3)+' and 144 inches.');
 if(!Number.isFinite(pitch)||pitch<3||pitch>8)throw Error('Main roof pitch must be between 3:12 and 8:12.');
 return {wallHeightIn,pitch,changed:Math.abs(wallHeightIn-BASE_WALL)>1e-7||Math.abs(pitch-4)>1e-9};
}
function createKernel(module){
 const {Manifold,Mesh}=module,owned=[];
 const keep=s=>{owned.push(s);return s;};
 const key=v=>v.map(Math.fround).join(',');
 const from=p=>{const exact=new Map(p.vertices.map(v=>[key(v),v]));const imported=keep(new Manifold(new Mesh({numProp:3,vertProperties:new Float32Array(p.vertices.flat()),triVerts:new Uint32Array(p.triangles.flat()),tolerance:1e-9})));return keep(imported.warpBatch((vs,count)=>{for(let i=0;i<count;i++){const v=exact.get(key(Array.from(vs.slice(3*i,3*i+3))));if(v)vs.set(v,3*i);}}));};
 const hull=points=>keep(Manifold.hull(points));
 const plus=(a,b)=>keep(a.add(b)),minus=(a,b)=>keep(a.subtract(b)),intersect=(a,b)=>keep(a.intersect(b));
 const trim=(s,n,k)=>keep(s.trimByPlane(unit(n),k/Math.hypot(...n)));
 const band=(s,n,lo,hi)=>trim(trim(s,n,lo),mul(n,-1),-hi);
 const move=(s,v)=>keep(s.translate(v));
 const union=shapes=>shapes.length?keep(Manifold.union(shapes)):keep(new Manifold(new Mesh({numProp:3,vertProperties:new Float32Array(),triVerts:new Uint32Array()})));
 function raw(s){
  const exact=new Map();const captured=keep(s.warpBatch((vs,count)=>{for(let i=0;i<count;i++){const v=Array.from(vs.slice(3*i,3*i+3));exact.set(key(v),v);}}));
  const m=captured.getMesh(),vertices=Array.from({length:m.vertProperties.length/m.numProp},(_,i)=>{const v=Array.from(m.vertProperties.slice(i*m.numProp,i*m.numProp+3));return exact.get(key(v))||v;}),triangles=Array.from({length:m.triVerts.length/3},(_,i)=>Array.from(m.triVerts.slice(i*3,i*3+3)));
  if(s.status()!=='NoError')throw Error('Invalid parametric solid: '+s.status());
  return {vertices,triangles,faces:triangles,volume_m3:s.volume()};
 }
 function pack(s){
  const data=raw(s);if(!data.triangles.length)return data;
  const groups=[],tol=1e-8,scale=1e6;
  for(const tri of data.triangles){const points=tri.map(i=>data.vertices[i]),normal=cross(sub(points[1],points[0]),sub(points[2],points[0]));if(Math.hypot(...normal)<1e-13)continue;let n=unit(normal);const max=n.reduce((best,v,i)=>Math.abs(v)>Math.abs(n[best])?i:best,0);if(n[max]<0)n=mul(n,-1);
   let g=groups.find(q=>Math.hypot(...sub(n,q.n))<1e-8&&points.every(v=>Math.abs(dot(sub(v,q.origin),q.n))<tol));
   if(!g){const ei=n.reduce((best,v,i)=>Math.abs(v)<Math.abs(n[best])?i:best,0),e=[0,0,0];e[ei]=1;const u=unit(cross(n,e));g={n,origin:points[0],u,v:cross(n,u),contours:[]};groups.push(g);}
   g.contours.push(points.map(p=>[dot(sub(p,g.origin),g.u)*scale,dot(sub(p,g.origin),g.v)*scale]));
  }
  const vertices=[],regions=[];
  function weld(p){let i=vertices.findIndex(v=>Math.hypot(...sub(v,p))<tol);if(i<0){i=vertices.length;vertices.push(p);}return i;}
  for(const g of groups)for(const [sign,rule]of [[1,'Positive'],[-1,'Negative']]){const cs=new module.CrossSection(g.contours,rule);try{if(cs.isEmpty())continue;const loops=cs.toPolygons().map(poly=>poly.map(p=>weld(add(g.origin,add(mul(g.u,p[0]/scale),mul(g.v,p[1]/scale))))));regions.push({g,sign,loops});}finally{cs.delete();}}
  const triangles=[];
  for(const {g,sign,loops}of regions){const contours=[],ids=[];for(const loop of loops){const split=[];for(let j=0;j<loop.length;j++){const start=loop[j],end=loop[(j+1)%loop.length],a=vertices[start],edge=sub(vertices[end],a),len=dot(edge,edge);if(len<tol*tol)continue;const middle=[];for(let k=0;k<vertices.length;k++){const t=dot(sub(vertices[k],a),edge)/len;if(t>1e-10&&t<1-1e-10&&Math.hypot(...sub(vertices[k],add(a,mul(edge,t))))<tol)middle.push([t,k]);}split.push(start,...middle.sort((a,b)=>a[0]-b[0]).map(q=>q[1]));}ids.push(...split);contours.push(split.map(i=>[dot(sub(vertices[i],g.origin),g.u),dot(sub(vertices[i],g.origin),g.v)]));}
   for(const tri of module.triangulate(contours,1e-12,false)){const t=tri.map(i=>ids[i]);triangles.push(sign>0?t:t.reverse());}
  }
  return {vertices,triangles,faces:triangles,volume_m3:data.volume_m3};
 }
 function convex(planes){
  const points=[];
  for(let a=0;a<planes.length;a++)for(let b=a+1;b<planes.length;b++)for(let c=b+1;c<planes.length;c++){
   const [p,q,r]=[planes[a],planes[b],planes[c]],det=dot(p.n,cross(q.n,r.n));if(Math.abs(det)<1e-10)continue;
   const v=mul(add(add(mul(cross(q.n,r.n),p.k),mul(cross(r.n,p.n),q.k)),mul(cross(p.n,q.n),r.k)),1/det);
   if(planes.every(p=>dot(p.n,v)<=p.k+1e-8))points.push(v);
  }
  if(points.length<4)throw Error('Parameter produces an empty stock envelope');return hull(points);
 }
 function overlaps(a,b,margin=1e-7){const x=a.boundingBox(),y=b.boundingBox();return x.min.every((v,i)=>x.max[i]>y.min[i]+margin&&y.max[i]>v+margin);}
 return {from,hull,plus,minus,intersect,trim,band,move,union,pack,raw,convex,overlaps,dispose(){for(const s of owned.reverse())s.delete();}};
}
function shiftedPart(part,map){
 const p=clone(part);p.vertices=p.vertices.map(map);
 // TIMESTAMP START 2026-11-03T16:50:27-05:00 | REVISION R005061
 for(const key of ['geometry_planes_inches','proposed_stock_planes_inches'])if(p[key])p[key]=p[key].map(plane=>{
  const n=[plane.normal[0],plane.normal[2],-plane.normal[1]],point=mul(n,plane.constant*I/dot(n,n));
  return {...plane,constant:dot(n,map(point))/I};
 });
 // TIMESTAMP END 2026-11-03T16:50:27-05:00 | REVISION R005061
 for(const key of ['axis_start','axis_end','center','label_position'])if(p[key])p[key]=map(p[key]);
 for(const key of ['reference_end_faces','joint_cut_faces'])p[key]=[];
 return p;
}
function metrics(p){
 const vs=p.vertices,c=vs.reduce((a,v)=>add(a,mul(v,1/vs.length)),[0,0,0]);p.center=p.axis_start&&p.axis_end?mul(add(p.axis_start,p.axis_end),.5):(p.center||c);p.label_position=p.center;
 let vol=0,moment=[0,0,0];for(const [a,b,d]of p.triangles){const v=dot(sub(vs[a],c),cross(sub(vs[b],c),sub(vs[d],c)))/6;vol+=v;moment=add(moment,mul(add(add(sub(vs[a],c),sub(vs[b],c)),sub(vs[d],c)),v/4));}
 p.fit_geometry={...p.fit_geometry,volume_m3:Math.abs(vol)};p.parametricCentroid=add(c,mul(moment,1/vol));
 if(p.axis_start&&p.axis_end){const axis=unit(sub(p.axis_end,p.axis_start)),length=Math.hypot(...sub(p.axis_end,p.axis_start));p.axis_direction=axis;p.angles={...p.angles,axis_inclination_deg:Math.asin(Math.abs(axis[1]))*180/Math.PI,display_end_A_off_square_deg:null,display_end_B_off_square_deg:null};p.dimensions={...p.dimensions,length_m:length,length_ft:length/.3048,length_display:(length/I).toFixed(3)+' in'};p.nominal_dimensions={...p.dimensions};p.fitted_axial_extent_inches=(Math.max(...vs.map(v=>dot(v,axis)))-Math.min(...vs.map(v=>dot(v,axis))))/I;}
 return p;
}
function core(context,input,source,module){
 const config=parameters(input),base=context.model,prepared=source.variants[context.id];
 if(prepared.source_model_sha256!==context.sha256)throw Error('Parametric receiver source does not match this model');
 const kernel=createKernel(module),K=kernel,{from,plus,minus,intersect,trim,band,move,union,pack,convex}=K;
 try{
  const dh=(config.wallHeightIn-BASE_WALL)*I,pitch=config.pitch/12,H=90*I+dh,
   crown=H+176*I*pitch+5*I+10*I*Math.sqrt(1+pitch*pitch),
   cupShift=dh+135*I*(pitch-BASE_P)+5*I*(Math.sqrt(1+pitch*pitch)-Math.sqrt(1+BASE_P*BASE_P));
  // TIMESTAMP START 2026-11-03T15:42:57-05:00 | REVISION R005038
  const P=Object.fromEntries(base.parts.map(p=>[p.id,p])),parts={},S={},stocks={},cavityBlanks={},cavities={},partMaps={};
  // TIMESTAMP START 2026-11-03T16:50:27-05:00 | REVISION R005061
  const jointVoids={},roofTongues={};
  // TIMESTAMP END 2026-11-03T16:50:27-05:00 | REVISION R005061
  // TIMESTAMP END 2026-11-03T15:42:57-05:00 | REVISION R005038
  for(const original of base.parts){
   const pid=original.id;
   let map=v=>add(v,[0,dh,0]);
   if(/^P[0-7]$/.test(pid))map=v=>add(v,[0,v[1]>I?dh:0,0]);
   if(/^C[0-7]$/.test(pid))map=v=>add(v,[0,v[1]>120*I?cupShift:dh,0]);
   if(/^(CR|CC|L|PLY|ENV-CUP)/.test(pid)||pid==='M-SP0')map=v=>add(v,[0,cupShift,0]);
   // TIMESTAMP START 2026-11-03T15:42:57-05:00 | REVISION R005038
   partMaps[pid]=map;
   // TIMESTAMP START 2026-11-03T16:50:27-05:00 | REVISION R005061
   if(prepared.roof_receiver_voids[pid])jointVoids[pid]=from(shiftedPart(prepared.roof_receiver_voids[pid],map));
   // TIMESTAMP END 2026-11-03T16:50:27-05:00 | REVISION R005061
   // TIMESTAMP END 2026-11-03T15:42:57-05:00 | REVISION R005038
   const restored=prepared.roof_receivers[pid];parts[pid]=shiftedPart(restored?{...original,...restored}:original,map);
   if(prepared.cavity_blanks[pid])cavityBlanks[pid]=from(shiftedPart(prepared.cavity_blanks[pid],map));
   if(!/^(R[0-7]|J[0-7]-[02])$/.test(pid))S[pid]=from(parts[pid]);
  }
  // Roof stock is rebuilt from its planes. Width/depth remain actual stock sizes;
  // no existing notch or facet is stretched to simulate a different pitch.
  for(const original of base.parts.filter(q=>/^(R[0-7]|J[0-7]-[02])$/.test(q.id))){
   const pid=original.id,isHip=pid[0]==='R',k=Number(pid[1]),n=radial(isHip?k:k+.5),slope=isHip?pitch:pitch/C,depth=(isHip?10:8)*I;
   const planes=original.geometry_planes_inches.map(q=>({n:[q.normal[0],q.normal[2],-q.normal[1]],k:q.constant*I,end:q.end}));
   for(const q of planes)if(Math.abs(q.n[1])>.9){const sign=Math.sign(q.n[1]);q.n=mul(add(mul(n,slope),[0,1,0]),sign);q.k=sign*(crown-(sign<0?depth*Math.sqrt(1+slope*slope):0));}
   stocks[pid]=convex(planes);S[pid]=stocks[pid];
   const axisY=v=>crown-slope*dot(v,n)-depth/2*Math.sqrt(1+slope*slope);
   const next=parts[pid];next.axis_start=[original.axis_start[0],axisY(original.axis_start),original.axis_start[2]];next.axis_end=[original.axis_end[0],axisY(original.axis_end),original.axis_end[2]];
   const axis=unit(sub(next.axis_end,next.axis_start)),w=original.stock_frame.width,d=unit(cross(w,axis));next.stock_frame={axis,width:w,depth:d[1]<0?mul(d,-1):d};next.geometry_planes_inches=planes.map(q=>({normal:[q.n[0],-q.n[2],q.n[1]],constant:q.k/I,end:q.end}));
   // TIMESTAMP START 2026-11-03T16:50:27-05:00 | REVISION R005061
   next.proposed_stock_planes_inches=clone(next.geometry_planes_inches);next.proposed_stock_planes_inches.find(q=>q.end==='B').constant+=isHip||context.id!=='top-entry'?3:2;
   // TIMESTAMP END 2026-11-03T16:50:27-05:00 | REVISION R005061
   next.source_geometry_metadata={...next.source_geometry_metadata,roof_reference:{radial_pitch:pitch,roof_reference_pitch:slope},display_height_H_in:H/I};
  }
  const receiverBlanks={...S},roofIds=Object.keys(stocks),step=context.id!=='baseline',topEntry=context.id==='top-entry';
  // Birdsmouth shoulders, with the existing shallow perimeter step tongues.
  for(const pid of roofIds){
   const k=Number(pid[1]),isHip=pid[0]==='R',receiver=isHip?'P'+k:'B'+k,stock=stocks[pid],w=parts[pid].stock_frame.width;
   const others=isHip?['P'+k,'B'+k,'B'+((k+7)%8)]:['B'+k];
   // TIMESTAMP START 2026-11-03T16:50:27-05:00 | REVISION R005061
   const cut=union(others.map(id=>receiverBlanks[id]));let finished=minus(stock,cut);jointVoids[pid]=intersect(stock,cut);
   // TIMESTAMP END 2026-11-03T16:50:27-05:00 | REVISION R005061
   if(step){const top=Math.max(...parts[receiver].vertices.map(v=>v[1])),center=dot(parts[pid].axis_start,w),width=(isHip?4:2)*I,engage=(isHip?.5:1)*I;
    const tongue=intersect(band(band(stock,[0,1,0],top-engage,top),w,center-width/2,center+width/2),receiverBlanks[receiver]);
    // TIMESTAMP START 2026-11-03T16:50:27-05:00 | REVISION R005061
    finished=plus(finished,tongue);S[receiver]=minus(S[receiver],tongue);
    jointVoids[pid]=minus(jointVoids[pid],tongue);jointVoids[receiver]=plus(jointVoids[receiver],tongue);
    // TIMESTAMP END 2026-11-03T16:50:27-05:00 | REVISION R005061
   }
   S[pid]=finished;
  }
  // TIMESTAMP START 2026-11-03T15:42:57-05:00 | REVISION R005038
  // Three-inch hip tenons retain clearance below the lower cupola ring.
  for(let k=0;k<8;k++){
   const id='R'+k,post='C'+k,r=radial(k),w=tangent(k),d=parts[id].stock_frame.depth;
   let tongue=intersect(move(stocks[id],mul(r,-3*I)),receiverBlanks[post]);
   const end=parts[id].axis_end,center=dot(end,d);
   const halfHeight=Math.min(3*I,3.25*I*d[1]);
   tongue=band(band(tongue,w,-(8/6)*I,(8/6)*I),d,center-halfHeight,center+halfHeight);
   // TIMESTAMP START 2026-11-03T16:50:27-05:00 | REVISION R005061
   roofTongues[id]=tongue;S[id]=plus(S[id],plus(tongue,move(tongue,mul(r,.0001))));
   jointVoids[post]=plus(jointVoids[post],intersect(S[post],S[id]));S[post]=minus(S[post],S[id]);
   // TIMESTAMP END 2026-11-03T16:50:27-05:00 | REVISION R005061
  }
  // TIMESTAMP END 2026-11-03T15:42:57-05:00 | REVISION R005038
  // Upper short-rafter noses and their receiver void use the same fresh solid.
  for(const pid of roofIds.filter(id=>id[0]==='J')){
   const k=Number(pid[1]),hip='R'+(pid.endsWith('-0')?k:(k+1)%8),w=parts[hip].stock_frame.width,d=parts[hip].stock_frame.depth;
   // TIMESTAMP START 2026-11-03T16:50:27-05:00 | REVISION R005061
   const side=dot(P[pid].axis_end,w)>0?1:-1,normal=mul(w,side);
   const fullPlanes=parts[pid].proposed_stock_planes_inches.map(q=>({n:[q.normal[0],q.normal[2],-q.normal[1]],k:q.constant*I}));
   const extended=topEntry?plus(stocks[pid],move(stocks[pid],mul(normal,-2*I))):convex(fullPlanes);
   // TIMESTAMP END 2026-11-03T16:50:27-05:00 | REVISION R005061
   let nose=intersect(extended,move(stocks[hip],mul(normal,.01*I)));
   if(topEntry){nose=trim(nose,d,dot(parts[hip].axis_end,d)+I);nose=band(nose,normal,2*I,4.01*I);}
   else {const jw=parts[pid].stock_frame.width,jd=parts[pid].stock_frame.depth,end=parts[pid].axis_end;nose=band(band(nose,jw,dot(jw,end)-(4/6)*I,dot(jw,end)+(4/6)*I),jd,dot(jd,end)-3*I,dot(jd,end)+3*I);}
   // TIMESTAMP START 2026-11-03T16:50:27-05:00 | REVISION R005061
   if(!topEntry)roofTongues[pid]=intersect(nose,stocks[hip]);
   S[pid]=plus(S[pid],nose);
   // TIMESTAMP END 2026-11-03T16:50:27-05:00 | REVISION R005061
   const inside=intersect(nose,stocks[hip]);let cutter=inside;
   if(topEntry){const vertices=K.raw(inside).vertices;cutter=K.hull([...vertices,...vertices.map(v=>add(v,[0,24*I,0]))]);}
   // TIMESTAMP START 2026-11-03T16:50:27-05:00 | REVISION R005061
   jointVoids[hip]=plus(jointVoids[hip],intersect(S[hip],cutter));S[hip]=minus(S[hip],cutter);
   // TIMESTAMP END 2026-11-03T16:50:27-05:00 | REVISION R005061
  }
// TIMESTAMP START 2026-11-03T16:17:49-05:00 | REVISION R005051
  const tenonSchedule=(base.tenon_schedule||[]).map(j=>{
   const next=clone(j),map=partMaps[j.donor];
   if(next.face_center)next.face_center=map(next.face_center);
   // TIMESTAMP START 2026-11-04T20:12:02+00:00 | REVISION R000019
   if(next.bearing_direction&&Number.isFinite(next.bearing_coordinate_m))next.bearing_coordinate_m+=dot(next.bearing_direction,sub(next.face_center,j.face_center));
   // TIMESTAMP END 2026-11-04T20:12:02+00:00 | REVISION R000019
   for(const key of ['connector','cutting_tool'])if(next[key])next[key].vertices=next[key].vertices.map(map);
   // TIMESTAMP START 2026-11-03T16:50:27-05:00 | REVISION R005061
   if(roofTongues[j.donor]){
    const id=j.donor,tongue=roofTongues[id],d=parts[id].stock_frame.depth,w=parts[id].stock_frame.width;
    next.connector=pack(tongue);delete next.cutting_tool;
    const extent=axis=>{const coordinates=next.connector.vertices.map(v=>dot(v,axis));return Math.max(...coordinates)-Math.min(...coordinates);};
    next.height_m=extent(d);next.width_m=extent(w);next.height_direction=d;next.width_direction=w;next.face_center=parts[id].axis_end.slice();
   }
   // TIMESTAMP END 2026-11-03T16:50:27-05:00 | REVISION R005061
   return next;
  });
// TIMESTAMP END 2026-11-03T16:17:49-05:00 | REVISION R005051
  const diagnostics=[];
  for(let k=0;k<8;k++)for(const [a,b]of [['P'+k,'R'+k],['B'+k,'J'+k+'-0']])diagnostics.push([a,b,intersect(S[a],S[b]).volume()/I**3]);
  const seeds={};
  function familyMesh(pid,cavity=false){
   const match=pid.match(/^([PBCRJ])([0-7])(.*)$/),seed=match?match[1]+'0'+match[3]:pid,key=seed+(cavity?'-void':'');
   if(!seeds[key])seeds[key]=cavity?pack(jointVoids[seed]||minus(stocks[seed]||cavityBlanks[seed],S[seed])):pack(S[seed]);
   const data=seeds[key];if(!match||match[2]==='0')return data;const theta=Number(match[2])*Math.PI/4,c=Math.cos(theta),s=Math.sin(theta);
   return {...data,vertices:data.vertices.map(([x,y,z])=>[c*x+s*z,y,-s*x+c*z])};
  }
  for(const pid of Object.keys(parts)){
   const changed=/^([PBCR][0-7]|J[0-7]-[02])$/.test(pid);
   parts[pid]=metrics({...parts[pid],...(changed?familyMesh(pid):{})});
   // TIMESTAMP START 2026-11-03T15:42:57-05:00 | REVISION R005038
   if(parts[pid].is_timber){const saved=context.cavities?.parts?.[pid]?.removed;cavities[pid]={removed:changed||!saved?familyMesh(pid,true):{...clone(saved),vertices:saved.vertices.map(partMaps[pid])}};}
   // TIMESTAMP END 2026-11-03T15:42:57-05:00 | REVISION R005038
  }
  const model={...clone(base),parts:base.parts.map(p=>parts[p.id]),parameters:config,revision:'PARAMETRIC-'+context.id+'-'+config.wallHeightIn+'-'+config.pitch,
// TIMESTAMP START 2026-11-03T16:17:49-05:00 | REVISION R005051
   source_dimensions:{...base.source_dimensions,main_radial_pitch:pitch,short_normal_pitch:pitch/C,display_height_H_in:H/I},parametric_revision:'R005024',tenon_schedule:tenonSchedule};
// TIMESTAMP END 2026-11-03T16:17:49-05:00 | REVISION R005051
  delete model.proposed_member_volume_centroids;
  return {model,cavities,config,cupShift,dh,diagnostics};
 }finally{K.dispose();}
}
function layouts(context,result,module,apis){
 const {model,dh}=result,K=createKernel(module),{from,plus,minus,intersect,pack,union,hull}=K;
 try{
  const primary=Object.fromEntries(model.parts.filter(p=>p.is_timber||p.is_fastener).map(p=>[p.id,p])),shapes=Object.fromEntries(Object.entries(primary).map(([id,p])=>[id,from(p)]));
  const layout=apis.walls.build(model.parts,{applyFit:false}),floorKinds=new Set(['floor','floorAssembly','grate','footer']);
  const walls=layout.components.filter(p=>['rail','wall','shelf'].includes(p.schematicKind)),wallShapes={};
  for(const p of layout.components){
   if(floorKinds.has(p.schematicKind)){const old=context.enclosureFit.parts[p.id];if(old)Object.assign(p,clone(old));continue;}
   if(!walls.includes(p))continue;
   let s=from(p);for(const t of Object.values(shapes))if(K.overlaps(s,t))s=minus(s,t);
   if(p.schematicKind==='shelf'){const pieces=s.decompose();try{const kept=pieces.reduce((a,b)=>a.volume()>b.volume()?a:b);Object.assign(p,pack(kept));s=from(p);}finally{for(const piece of pieces)piece.delete();}}
   wallShapes[p.id]=s;
  }
  const records={...primary,...Object.fromEntries(walls.map(p=>[p.id,p]))},original={...shapes,...wallShapes},additions={},cutters={},jointIds={},joints=[];
  for(const id of Object.keys(records)){additions[id]=[];cutters[id]=[];jointIds[id]=[];}
  // Door/window opening datums and wall-rail sections remain fixed. Their
  // interlocking tongues are reused rigidly; receiver openings are recut.
  for(const joint of context.wallJoinery.joints){
   if(!original[joint.donor]||!original[joint.receiver])throw Error('Missing wall-joint member '+joint.id);
   const tongue=from(joint.tongue),direction=joint.withdrawal_direction,points=joint.tongue.vertices,sweep=hull([...points,...points.map(v=>add(v,mul(direction,.5)))]);
   additions[joint.donor].push(tongue);cutters[joint.receiver].push(sweep);jointIds[joint.donor].push(joint.id);jointIds[joint.receiver].push(joint.id);joints.push(clone(joint));
  }
  const fitted={},patches={};
  for(const [id,s]of Object.entries(original)){
   const added=union(additions[id]),stock=plus(s,added),final=minus(stock,union(cutters[id]));fitted[id]=final;
   const removed=minus(stock,final),geometry=pack(final);if(geometry.volume_m3<=0)throw Error('The selected dimensions remove '+id);
   const oldVoid=result.cavities[id]?.removed,allRemoved=oldVoid?.triangles?.length?plus(from(oldVoid),removed):removed;
   patches[id]={...geometry,wallJoineryJointIds:jointIds[id],joineryCavity:{removed:pack(allRemoved),fit_audit:{status:'GENERATED'}},wallJoineryAdded:pack(added),wallJoineryRemoved:pack(removed),connectionStatus:'Interlocking geometry regenerated for current dimensions.'};
   Object.assign(records[id],patches[id]);metrics(records[id]);
   if(primary[id])result.cavities[id]={removed:pack(allRemoved)};
  }
  const wallJoinery={status:'PASS',joints,primary_parts:Object.fromEntries(Object.keys(primary).map(id=>[id,patches[id]])),wall_parts:Object.fromEntries(walls.map(p=>[p.id,patches[p.id]])),verification:{scope:'Regenerated nominal wall joints; assembled geometry checked separately',capacity_verified:false}};
  const schematic=apis.floor.roomLayout(model,layout,apis.foundationData);
  const oldPorch=apis.porch.build(context.model),porch=apis.porch.build(model,{applyJoinery:false}),dy=porch.dimensions.roofHighY_M-oldPorch.dimensions.roofHighY_M;
  const oldById=new Map(oldPorch.components.map(p=>[p.id,p]));
  function porchPart(p){
   const map=v=>add(v,[0,v[1]>44*I?dy:0,0]),q=shiftedPart(p,map);
   for(const key of ['joineryStock'])if(q[key])q[key]={...q[key],vertices:q[key].vertices.map(map)};
   if(q.joineryCavity)q.joineryCavity={...q.joineryCavity,removed:{...q.joineryCavity.removed,vertices:q.joineryCavity.removed.vertices.map(map)}};
   if(q.localVertices)q.localVertices=q.localVertices.map(map);if(q.localBounds){q.localBounds[2]=map([0,q.localBounds[2],0])[1];q.localBounds[3]=map([0,q.localBounds[3],0])[1];}
   return q;
  }
  porch.components=porch.components.map(p=>oldById.get(p.id)?.joineryStock?porchPart({...p,...oldById.get(p.id)}):p);
  const ids=new Set(porch.components.map(p=>p.id));porch.components.push(...oldPorch.components.filter(p=>!ids.has(p.id)&&p.mudroomRole==='framing').map(porchPart));
  porch.joinery={...oldPorch.joinery,verification:{...oldPorch.joinery.verification,status:'PARAMETRIC',scope:'Rigid porch roof and joints; extended post shafts; regenerated roof intersection'}};
  result.schematicLayout=schematic;result.mudroomLayout=porch;result.wallJoinery=wallJoinery;
  result.components=[...schematic.components,...apis.roof.build(model).components,...porch.components];
  return result;
 }finally{K.dispose();}
}
const api={parameters,core,layouts,createKernel,metrics,shiftedPart,BASE_WALL};root.OctagonParametric=api;if(typeof module!=='undefined'&&module.exports)module.exports=api;
})(typeof globalThis!=='undefined'?globalThis:this);
// TIMESTAMP END 2026-11-03T13:09:36-05:00 | REVISION R005024

// TIMESTAMP END 2026-11-04T23:23:25+00:00 | REVISION R000011
