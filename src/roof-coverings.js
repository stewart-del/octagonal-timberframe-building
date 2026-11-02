/* Model-derived roof appearance. Covering build-up/fasteners and added dead load are not designed. */
const TimberRoofCoverings=(()=>{
 const I=.0254,T=Math.tan(Math.PI/8),C=Math.cos(Math.PI/8);
 const add=(a,b)=>a.map((x,i)=>x+b[i]),mul=(a,s)=>a.map(x=>x*s),dot=(a,b)=>a.reduce((s,x,i)=>s+x*b[i],0);
 function prism(poly,depth){
  const vertices=[...poly,...poly.map(v=>add(v,[0,depth,0]))],n=poly.length,triangles=[];
  for(let j=1;j<n-1;j++){triangles.push([0,j+1,j],[n,n+j,n+j+1]);}
  for(let j=0;j<n;j++){let k=(j+1)%n;triangles.push([j,k,n+k],[j,n+k,n+j]);}
  for(const t of triangles)[t[1],t[2]]=[t[2],t[1]];
  return {vertices,triangles,faces:triangles};
 }
 function clip(poly,axis,bound,keepLess){const result=[];for(let i=0;i<poly.length;i++){const a=poly[i],b=poly[(i+1)%poly.length],da=(keepLess?1:-1)*(a[axis]-bound),db=(keepLess?1:-1)*(b[axis]-bound);if(da<=1e-10)result.push(a);if((da<0&&db>0)||(da>0&&db<0)){const t=da/(da-db);result.push(a.map((v,j)=>v+(b[j]-v)*t));}}return result;}
 function build(model){
  const parts=model.parts||model,byId=Object.fromEntries(parts.map(p=>[p.id,p])),components=[];
  function face(k,cupola){
   const prefix=cupola?'CR':'R',a=byId[prefix+k],b=byId[prefix+((k+1)%8)];
   if(!a||!b)throw new Error('Roof reference member missing');
   const angle=-(k+.5)*Math.PI/4,n=[Math.cos(angle),0,Math.sin(angle)],u=[-n[2],0,n[0]];
   const endpoints=[a.axis_start,a.axis_end],r=endpoints.map(v=>Math.hypot(v[0],v[2]));
   const slope=Math.abs((endpoints[1][1]-endpoints[0][1])/(r[1]-r[0]));
   const outer=Math.max(...r)*C;
   const inner=cupola?0:Math.max(...[byId['C'+k],byId['C'+((k+1)%8)]].flatMap(p=>p.vertices.map(v=>dot(v,n))));
   const refs=[a,b,...(!cupola?[byId['J'+k+'-0'],byId['J'+k+'-2']]:[])].filter(Boolean);
   const intercept=Math.max(...refs.flatMap(p=>p.vertices.map(v=>v[1]+slope*dot(v,n)/C)))+.001;
   const world=([t,q])=>add(add(mul(n,q),mul(u,t)),[0,intercept-slope*q/C,0]);
   const region=inner===0?[[0,0],[-outer*T,outer],[outer*T,outer]]:[[-inner*T,inner],[-outer*T,outer],[outer*T,outer],[inner*T,inner]];
   function part(id,poly,material,color){if(poly.length<3)return;const mesh=prism(poly.map(world),cupola?.001:.004);const center=mesh.vertices.reduce((a,v)=>add(a,mul(v,1/mesh.vertices.length)),[0,0,0]);components.push({...mesh,id,name:cupola?'Copper cupola roof':'Cedar shake course appearance',group:'roof_cover',schematic:true,schematicKind:'roofCover',temporary:false,is_timber:false,material,color,center,label_position:center,exploded_offset:[0,0,0],fabrication_dimensions_valid:false,geometry_purpose:'Roof covering appearance, not a roof assembly or cut specification',notes:['Geometry follows selected rafters. Sheathing, underlayment, flashings, fastening, weatherproofing and added load are not designed.'],roof_face:k});}
   if(cupola){part('ROOF-COPPER-'+k,region,'copper',[.62,.31,.16,1]);return;}
   // Six-inch exposed courses and staggered six-inch widths are appearance choices,
   // not an assertion that a six-inch square is a complete watertight shake.
   let row=0;for(let q=inner;q<outer-1e-9;q+=6*I,row++){
    let strip=clip(clip(region,1,q,false),1,Math.min(outer,q+6*I),true);if(strip.length<3)continue;
    const xmin=Math.min(...strip.map(p=>p[0])),xmax=Math.max(...strip.map(p=>p[0])),offset=(row%2)*3*I;
    let index=0;for(let x=Math.floor((xmin-offset)/(6*I))*6*I+offset;x<xmax;x+=6*I,index++){
      const tile=clip(clip(strip,0,x,false),0,x+6*I,true);if(tile.length<3)continue;
      const tint=((row+index)%3)*.025;part(`ROOF-CEDAR-${k}-${row}-${index}`,tile,'cedar',[.55+tint,.39+tint,.24+tint,1]);
    }
   }
  }
  for(let k=0;k<8;k++){face(k,false);face(k,true);}
  // Batch independent shake patches by face/tint to avoid thousands of selectable rows.
  const batches=new Map(),merged=[];for(const p of components){if(p.material==='copper'){merged.push(p);continue;}const key=p.roof_face+'-'+p.color[0];let b=batches.get(key);if(!b){b={...p,id:'ROOF-CEDAR-'+key,vertices:[],triangles:[],faces:[],tile_count:0};batches.set(key,b);}const n=b.vertices.length;b.vertices.push(...p.vertices);b.triangles.push(...p.triangles.map(t=>t.map(i=>i+n)));b.tile_count++;}for(const b of batches.values()){b.faces=b.triangles;b.center=b.vertices.reduce((a,v)=>add(a,mul(v,1/b.vertices.length)),[0,0,0]);b.label_position=b.center;merged.push(b);}
  return {components:merged,status:'Copper cupola and cedar shake appearance; roofing build-up and loads unresolved',assumptions:{cedar_course_exposure_in:6,cedar_visible_width_in:6,stagger_in:3,physical_overlap_modeled:false,overlap_note:'Staggered exposed-course pattern represents overlapping shakes; concealed lap/build-up is not specified.',copper_display_thickness_m:.001,cedar_display_thickness_m:.004,added_load_included:false}};
 }
 return {build};
})();
if(typeof module!=='undefined')module.exports=TimberRoofCoverings;
