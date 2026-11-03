// TIMESTAMP START 2026-11-02T15:12:45-05:00 | REVISION R004801
/* Proposed roof geometry. Flashing, fasteners, structure and weatherproofing require design. */
(function(root){
'use strict';
const I=.0254,EPS=1e-10;
const dot=(a,b)=>a.reduce((s,v,i)=>s+v*b[i],0),sub=(a,b)=>a.map((v,i)=>v-b[i]),cross=(a,b)=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]],unit=a=>a.map(v=>v/(Math.hypot(...a)||1));
const mean=vs=>vs.reduce((a,v)=>a.map((x,i)=>x+v[i]/vs.length),[0,0,0]);
const key=v=>v.map(x=>Math.round(x/EPS)).join(',');
function unique(vs){return [...new Map(vs.map(v=>[key(v),v])).values()];}
function spec(model){
 const parts=model.parts||model,a=parts.find(p=>p.id==='P2'),b=parts.find(p=>p.id==='P3');
 if(!a||!b)throw Error('Porch roof requires P2 and P3');
 const origin=[(a.center[0]+b.center[0])/2,0,(a.center[2]+b.center[2])/2],length=Math.hypot(b.center[0]-a.center[0],b.center[2]-a.center[2]);
 const tangent=[(b.center[0]-a.center[0])/length,0,(b.center[2]-a.center[2])/length],radius=Math.hypot(origin[0],origin[2]),outward=[origin[0]/radius,0,origin[2]/radius];
 const world=(x,y,z)=>[origin[0]+tangent[0]*x+outward[0]*z,y,origin[2]+tangent[2]*x+outward[2]*z];
 const local=v=>[dot(sub(v,origin),tangent),v[1],dot(sub(v,origin),outward)];
 // TIMESTAMP START 2026-11-02T21:55:01-05:00 | REVISION R004881
 const pitch=1/3,halfWidthM=48*I+5.5*I,frontZ_M=3*I+96*I+5.5*I;
 const mainAPI=typeof TimberRoofCoverings!=='undefined'?TimberRoofCoverings:require('./roof-coverings.js');
 const hip=parts.find(p=>p.id==='R2'),ends=[hip.axis_start,hip.axis_end],radii=ends.map(v=>Math.hypot(v[0],v[2]));
 const mainSlope=Math.abs((ends[1][1]-ends[0][1])/(radii[1]-radii[0]))/Math.cos(Math.PI/8);
 const mainVertices=mainAPI.build(model).components.filter(p=>p.material==='cedar'&&p.roof_face===2).flatMap(p=>p.vertices.map(local));
 const mainEaveZ_M=Math.max(...mainVertices.map(v=>v[2])),mainTopInterceptM=Math.max(...mainVertices.map(v=>v[1]+mainSlope*v[2]));
 const ridgeRoofTopY_M=mainTopInterceptM-mainSlope*mainEaveZ_M+pitch*halfWidthM+.024+.001;
 // TIMESTAMP END 2026-11-02T21:55:01-05:00 | REVISION R004881
 const roofTop=x=>ridgeRoofTopY_M-Math.abs(x)*pitch,deckTop=x=>roofTop(x)-.004,deckBottom=x=>deckTop(x)-.020,mainTop=z=>mainTopInterceptM-mainSlope*z;
 // TIMESTAMP START 2026-11-02T21:55:01-05:00 | REVISION R004881
 const junctionZ=x=>(mainTopInterceptM-roofTop(x))/mainSlope,transitionX_M=Math.min(halfWidthM,(ridgeRoofTopY_M-mainTop(mainEaveZ_M))/pitch);
 // TIMESTAMP END 2026-11-02T21:55:01-05:00 | REVISION R004881
 return {origin,tangent,outward,world,local,ridgeRoofTopY_M,pitch,halfWidthM,frontZ_M,mainEaveZ_M,mainTopInterceptM,mainSlope,roofTop,deckTop,deckBottom,mainTop,junctionZ,transitionX_M,firstFrameZ_M:.66,cedarThicknessM:.004,deckThicknessM:.020,cedarCourseM:6*I,cedarWidthM:6*I,cedarStaggerM:3*I};
}
// Convex closed polyhedra are clipped as occupied volumes, including cap faces.
function prism(poly,low,high){
 const n=poly.length,bottom=poly.map(([x,z])=>[x,low(x,z),z]),top=poly.map(([x,z])=>[x,high(x,z),z]);
 return [bottom,top,...poly.map((_,i)=>[bottom[i],bottom[(i+1)%n],top[(i+1)%n],top[i]])];
}
function clip(faces,normal,constant){
 const result=[],cap=[];
 for(const face of faces){const poly=[];for(let i=0;i<face.length;i++){
  const a=face[i],b=face[(i+1)%face.length],da=dot(normal,a)+constant,db=dot(normal,b)+constant;
  if(da>=-EPS)poly.push(a);
  if((da>EPS&&db<-EPS)||(da<-EPS&&db>EPS)){
   const t=da/(da-db),v=a.map((x,j)=>x+(b[j]-x)*t);poly.push(v);cap.push(v);
  }else if(Math.abs(da)<=EPS)cap.push(a);
 }
 const clean=unique(poly);if(clean.length>=3)result.push(clean);
 }
 const ring=unique(cap);if(ring.length>=3){const c=mean(ring),n=unit(normal),axis=unit(cross(n,Math.abs(n[1])<.9?[0,1,0]:[1,0,0])),other=cross(n,axis);ring.sort((a,b)=>Math.atan2(dot(sub(a,c),other),dot(sub(a,c),axis))-Math.atan2(dot(sub(b,c),other),dot(sub(b,c),axis)));result.push(ring);}
 return result;
}
function mesh(faces){
 const vertices=unique(faces.flat()),center=mean(vertices),indices=new Map(vertices.map((v,i)=>[key(v),i])),triangles=[];
 for(let face of faces){face=unique(face);if(face.length<3)continue;let normal=null;
  for(let i=1;i<face.length-1&&!normal;i++){const n=cross(sub(face[i],face[0]),sub(face[i+1],face[0]));if(Math.hypot(...n)>1e-12)normal=n;}
  if(!normal)continue;if(dot(normal,sub(mean(face),center))<0)face=face.slice().reverse();
  const ids=face.map(v=>indices.get(key(v)));
  for(let i=1;i<ids.length-1;i++){const t=[ids[0],ids[i],ids[i+1]],n=cross(sub(vertices[t[1]],vertices[t[0]]),sub(vertices[t[2]],vertices[t[0]]));if(Math.hypot(...n)>1e-12)triangles.push(t);}
 }
 let volume=0;for(const [a,b,c] of triangles)volume+=dot(sub(vertices[a],center),cross(sub(vertices[b],center),sub(vertices[c],center)))/6;
 return volume>1e-14?{vertices,triangles,volume_m3:volume}:null;
}
function build(model){
 const s=spec(model),components=[],h=s.halfWidthM,e=s.mainEaveZ_M,z0=s.junctionZ(0)-.001,z1=s.frontZ_M;
 function add(id,name,faces,color,material,metadata={}){
  const m=mesh(faces);if(!m)return;
  const localVertices=m.vertices,vertices=localVertices.map(v=>s.world(...v)),center=mean(vertices),k=components.length,shift=[(k%2?1:-1)*(.35+k*.001),.8+k*.003,1.2+k*.002];
  components.push({id,name,schematic:true,schematicKind:'mudroom',displayRole:'mudroom',mudroomRole:'roof',mudroomScreen:true,mudroomRoof:true,group:'mudroom',face:'W',is_timber:false,material,color,vertices,triangles:m.triangles,localVertices,center,label_position:center,volume_m3:m.volume_m3,localBounds:[Math.min(...localVertices.map(v=>v[0])),Math.max(...localVertices.map(v=>v[0])),Math.min(...localVertices.map(v=>v[1])),Math.max(...localVertices.map(v=>v[1])),Math.min(...localVertices.map(v=>v[2])),Math.max(...localVertices.map(v=>v[2]))],exploded_offset:[s.tangent[0]*shift[0]+s.outward[0]*shift[2],shift[1],s.tangent[2]*shift[0]+s.outward[2]*shift[2]],geometry_purpose:'Proposed covering and junction geometry; not a flashing or fabrication specification',...metadata});
 }
 function cover(id,name,x0,x1,a,b,low,high,color,material,metadata){
  if(x1-x0<EPS||b-a<EPS)return;
  for(const [zone,lo,hi] of [['JUNCTION',a,Math.min(b,e)],['FRONT',Math.max(a,e),b]]){
   if(hi-lo<EPS)continue;let f=prism([[x0,lo],[x1,lo],[x1,hi],[x0,hi]],low,high);
   if(zone==='JUNCTION')f=clip(f,[0,1,s.mainSlope],-s.mainTopInterceptM);
   add(id+'-'+zone,name,f,color,material,metadata);
  }
 }
 for(const [side,a,b] of [['L',-h,0],['R',0,h]]){
  cover('MUD-ROOF-DECK-'+side,'Gabled porch roof deck',a,b,z0,z1,(x)=>s.deckBottom(x),(x)=>s.deckTop(x),[.62,.47,.30],'roof deck proposal',{roofLayer:'deck'});
  let row=0;
  for(let q=0;q<h-EPS;q+=s.cedarCourseM,row++){
   const outer=Math.min(h,q+s.cedarCourseM),x0=side==='L'?-outer:q,x1=side==='L'?-q:outer,stagger=(row%2)*s.cedarStaggerM;
   let index=0;for(let z=Math.floor((z0-stagger)/s.cedarWidthM)*s.cedarWidthM+stagger;z<z1-EPS;z+=s.cedarWidthM,index++){
    const tint=((row+index)%3)*.025;
    cover('MUD-ROOF-CEDAR-'+side+'-'+row+'-'+index,'Cedar shake course matching main roof',x0,x1,Math.max(z,z0),Math.min(z1,z+s.cedarWidthM),(x)=>s.deckTop(x),(x)=>s.roofTop(x),[.55+tint,.39+tint,.24+tint],'cedar',{roofLayer:'cedar',course:row,exposureM:s.cedarCourseM,staggerM:stagger});
   }
  }
 }
 // Replace the first deck ID with the stable selection identifier used by the viewer.
 if(components.length)components[0].id='MUD-ROOF';
 const thickness=.001,lap=.05,c=s.transitionX_M;
 // TIMESTAMP START 2026-11-02T21:55:01-05:00 | REVISION R004881
 // The raised deck clears the main eave across its full width; stepped fascia pieces are removed.
 // TIMESTAMP END 2026-11-02T21:55:01-05:00 | REVISION R004881
 for(const [side,a,b] of [['L',-c,0],['R',0,c]]){
  // Two exactly meeting planar strips follow the roof intersection, one on each roof surface.
  const line=x=>s.junctionZ(x);
  add('MUD-ROOF-FLASH-'+side+'-VALLEY-MAIN','Main-roof junction flashing',prism([[a,line(a)-lap],[b,line(b)-lap],[b,line(b)],[a,line(a)]],(x,z)=>s.mainTop(z),(x,z)=>s.mainTop(z)+thickness),[.39,.43,.43],'metal flashing proposal',{roofLayer:'flashing'});
  add('MUD-ROOF-FLASH-'+side+'-VALLEY-PORCH','Porch-roof junction flashing',prism([[a,line(a)],[b,line(b)],[b,line(b)+lap],[a,line(a)+lap]],(x)=>s.roofTop(x),(x)=>s.roofTop(x)+thickness),[.39,.43,.43],'metal flashing proposal',{roofLayer:'flashing'});
 }
 return {components,spec:s,status:'Proposed 4:12 cedar gable; structural support and final weatherproof junction design remain unresolved.'};
}
const api={spec,build};root.OctagonMudroomRoof=api;if(typeof module!=='undefined'&&module.exports)module.exports=api;
})(typeof globalThis!=='undefined'?globalThis:this);
// TIMESTAMP END 2026-11-02T15:12:45-05:00 | REVISION R004801
