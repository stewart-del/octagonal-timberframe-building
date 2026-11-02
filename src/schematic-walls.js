/* Provisional design layout only; not source dimensions, structural infill or site north. */
const TimberSchematicWalls=(()=>{
 const orientation={status:'Provisional design compass; site north unverified',north:[Math.cos(Math.PI/8),0,-Math.sin(Math.PI/8)],east:[Math.sin(Math.PI/8),0,Math.cos(Math.PI/8)],faceNames:['N','NW','W','SW','S','SE','E','NE'],northFacePostIds:['P0','P1']};
 const names=orientation.faceNames;
 const usage={N:'Solid wall + bookshelves',NW:'Small window',W:'Door',SW:'Small window',S:'Solid wall + bookshelves',SE:'Small window',E:'Large window',NE:'Small window'};
 const triangles=[[0,2,1],[0,3,2],[4,5,6],[4,6,7],[0,1,5],[0,5,4],[1,2,6],[1,6,5],[2,3,7],[2,7,6],[3,0,4],[3,4,7]];
 function build(parts,{applyFit=true}={}){
  const components=[],walls=[],railConnections=[];
  for(let k=0;k<8;k++){
   const a=parts.find(p=>p.id==='P'+k).center,b=parts.find(p=>p.id==='P'+((k+1)%8)).center;
   const dx=b[0]-a[0],dz=b[2]-a[2],span=Math.hypot(dx,dz),u=[dx/span,0,dz/span],center=[(a[0]+b[0])/2,0,(a[2]+b[2])/2],r=Math.hypot(center[0],center[2]),out=[center[0]/r,0,center[2]/r];
   // Infill terminates at existing post footprints and ring-beam underside, without arbitrary reveal gaps.
   const local=v=>[(v[0]-center[0])*u[0]+(v[2]-center[2])*u[2],(v[0]-center[0])*out[0]+(v[2]-center[2])*out[2]];
   function postBoundary(post,z,towardRight){
    const bottom=Math.min(...post.vertices.map(v=>v[1]));
    const pts=[...new Map(post.vertices.filter(v=>Math.abs(v[1]-bottom)<1e-7).map(v=>{const q=local(v);return[q.map(n=>n.toFixed(9)).join(','),q];})).values()];
    const c=pts.reduce((a,p)=>[a[0]+p[0]/pts.length,a[1]+p[1]/pts.length],[0,0]);pts.sort((a,b)=>Math.atan2(a[1]-c[1],a[0]-c[0])-Math.atan2(b[1]-c[1],b[0]-c[0]));
    const xs=[];for(let i=0;i<pts.length;i++){const a=pts[i],b=pts[(i+1)%pts.length];if(Math.abs(a[1]-z)<1e-9)xs.push(a[0]);if((a[1]-z)*(b[1]-z)<0)xs.push(a[0]+(b[0]-a[0])*(z-a[1])/(b[1]-a[1]));}
    if(!xs.length)throw new Error('Wall section misses post footprint');return towardRight?Math.max(...xs):Math.min(...xs);
   }
   const leftPost=parts.find(p=>p.id==='P'+k),rightPost=parts.find(p=>p.id==='P'+((k+1)%8));
   const left=z=>postBoundary(leftPost,z,true),right=z=>postBoundary(rightPost,z,false);
   const width=right(0)-left(0),height=Math.min(...parts.find(p=>p.id==='B'+k).vertices.map(v=>v[1])),base=Math.max(Math.min(...leftPost.vertices.map(v=>v[1])),Math.min(...rightPost.vertices.map(v=>v[1]))),dir=names[k],kind=usage[dir];
   const world=(x,y,z)=>[center[0]+u[0]*x+out[0]*z,y,center[2]+u[2]*x+out[2]*z];
   // TIMESTAMP START 2026-11-02T13:42:10-05:00 | REVISION R004782
   const railDepth=.1524,railHeight=.1524,lowRail=(dir==='E'?.75:1.0)-railHeight;
   const railLevels=[[base,base+railHeight],[lowRail,lowRail+railHeight],[1.30,1.30+railHeight],[2.10,Math.min(height,2.10+railHeight)]];
   // Partition rectangles before meshing: neighboring wood shares faces, never volume.
   function subtractRect(rect,cut){
    const [x0,x1,y0,y1]=rect,[a,b,c,d]=cut,lo=Math.max(x0,a),hi=Math.min(x1,b),bottom=Math.max(y0,c),top=Math.min(y1,d);
    if(hi<=lo+1e-10||top<=bottom+1e-10)return [rect];
    return [[x0,lo,y0,y1],[hi,x1,y0,y1],[lo,hi,y0,bottom],[lo,hi,top,y1]].filter(([a,b,c,d])=>b>a+1e-10&&d>c+1e-10);
   }
   function subtractAll(rect,cuts){return cuts.reduce((spans,cut)=>spans.flatMap(r=>subtractRect(r,cut)),[rect]);}
   function box(label,x0,x1,y0,y1,z0=-.05,z1=.05,color=[.88,.86,.75],framingRole=null){
    if(x1<=x0||y1<=y0)return;
    const vertices=[[x0,y0,z0],[x1,y0,z0],[x1,y1,z0],[x0,y1,z0],[x0,y0,z1],[x1,y0,z1],[x1,y1,z1],[x0,y1,z1]].map(v=>{if(Math.abs(v[0]+width/2)<1e-8)v[0]=left(v[2]);else if(Math.abs(v[0]-width/2)<1e-8)v[0]=right(v[2]);return world(...v);});
    const isFraming=framingRole!==null,offset=isFraming?out.map((v,i)=>v*(.45+.12*(y0+y1)/height)+u[i]*(x0+x1)*.16+(i===1?(y0+y1-height)*.12:0)):[0,0,0];
    const piece={id:'SCHEM-'+dir+'-'+label,name:dir+' '+label+' (schematic)',schematic:true,schematicKind:isFraming?'rail':label.startsWith('shelf')?'shelf':'wall',face:dir,localBounds:[x0,x1,y0,y1,z0,z1],group:'schematic_walls',material:isFraming?'proposed wood framing':'schematic',is_timber:false,vertices,triangles,center:world((x0+x1)/2,(y0+y1)/2,(z0+z1)/2),color,exploded_offset:offset};
    if(isFraming)Object.assign(piece,{displayRole:'wallStructure',framingRole,connectionStatus:'Proposed wall framing; member sizing, fastening and load capacity unresolved.'});
    components.push(piece);return piece;
   }
   let opening=null;
   if(kind==='Door')opening={width:.95,bottom:base,top:2.10};
   else if(kind.includes('window'))opening={width:width*(dir==='E'?.65:.30),bottom:dir==='E'?.75:1.0,top:dir==='E'?1.95:1.85};
   const framingRects=[],openingRects=opening?[[-opening.width/2,opening.width/2,opening.bottom,opening.top]]:[];
   function frame(label,rect,role){framingRects.push(rect);return box(label,...rect,-railDepth/2,railDepth/2,[.50,.30,.17],role);}
   if(opening){
    const w=opening.width/2;
    frame('rail-jamb-left',[-w-railDepth,-w,base+railHeight,height],'jamb');
    frame('rail-jamb-right',[w,w+railDepth,base+railHeight,height],'jamb');
    frame('rail-header',[-w,w,opening.top,Math.min(height,opening.top+railHeight)],'header');
    if(opening.bottom>base)frame('rail-sill',[-w,w,opening.bottom-railHeight,opening.bottom],'sill');
   }
   // Jambs bear on continuous bottom rails; upper rails stop at jamb faces.
   // Header/sill replace overlapping rail
   // sections, including the 2.4 mm overlap above the large east window.
   for(let level=0;level<railLevels.length;level++){
    const [y0,y1]=railLevels[level];if(y1<=y0)continue;
    const spans=subtractAll([-width/2,width/2,y0,y1],[...openingRects,...framingRects]);
    for(let j=0;j<spans.length;j++){
     const [x0,x1,lo,hi]=spans[j],piece=frame('rail'+level+'-'+j,spans[j],'rail');
     for(const [end,x,postId] of [['A',x0,leftPost.id],['B',x1,rightPost.id]])if(Math.abs(Math.abs(x)-width/2)<1e-8)railConnections.push({face:dir,railId:piece.id,end,postId,center:world(end==='A'?left(0):right(0),(lo+hi)/2,0),height:hi-lo,depth:railDepth,axis:u,normal:out,status:'Rail ends at post face; proposed mating joint and capacity unresolved. Not an installed connection.'});
    }
   }
   // Infill fills only the complement of the aperture and modeled wood framing.
   subtractAll([-width/2,width/2,base,height],[...openingRects,...framingRects]).forEach((rect,i)=>box('infill-'+i,...rect));
   // TIMESTAMP END 2026-11-02T13:42:10-05:00 | REVISION R004782
   if(dir==='N'||dir==='S'){
    // Built-ins span the framing bay and meet the inside of the horizontal rails.
    // No freestanding side cabinet; shelf fastening and book loads are unresolved.
    const sw=width/2-.0127;
    for(let j=0;j<6;j++)box('shelf'+j,-sw,sw,base+.1524+j*.35,base+.1778+j*.35,-.40,-.0762,[.67,.49,.31]);
   }
   walls.push({face:dir,postIds:['P'+k,'P'+((k+1)%8)],usage:kind,width,height,base,opening,center:world(0,1.15,.06),normal:out,frameFit:{endClearance:0,topClearance:0,leftAtFaces:[left(-.05),left(.05)],rightAtFaces:[right(-.05),right(.05)],status:'Infill meets modeled post footprints and beam underside; attachment design unchanged.'}});
  }
  const cupolaWindows=[];
  for(let k=0;k<8;k++){
   const post=parts.find(p=>p.id==='C'+k),next=parts.find(p=>p.id==='C'+((k+1)%8)),low=parts.find(p=>p.id==='L'+k+'-S'),high=parts.find(p=>p.id==='L'+k+'-H');if(!post||!next||!low||!high)continue;
   const a=post.center,b=next.center,dx=b[0]-a[0],dz=b[2]-a[2],span=Math.hypot(dx,dz),u=[dx/span,0,dz/span],c=[(a[0]+b[0])/2,0,(a[2]+b[2])/2],n=Math.hypot(c[0],c[2]),out=[c[0]/n,0,c[2]/n];
   const bottom=Math.max(...low.vertices.map(v=>v[1]))+.0127,top=Math.min(...high.vertices.map(v=>v[1]))-.0127,w=span-.20,t=.0254,depth=.0381;
   const world=(x,y,z)=>[c[0]+u[0]*x+out[0]*z,y,c[2]+u[2]*x+out[2]*z];
   const boxes=[['left',-w/2,-w/2+t,bottom,top],['right',w/2-t,w/2,bottom,top],['sill',-w/2+t,w/2-t,bottom,bottom+t],['head',-w/2+t,w/2-t,top-t,top]];
   for(const [label,x0,x1,y0,y1] of boxes){const vertices=[[x0,y0,-depth/2],[x1,y0,-depth/2],[x1,y1,-depth/2],[x0,y1,-depth/2],[x0,y0,depth/2],[x1,y0,depth/2],[x1,y1,depth/2],[x0,y1,depth/2]].map(v=>world(...v));components.push({id:'SCHEM-CUP-WINDOW-'+k+'-'+label,name:'Cupola window '+(k+1)+' '+label+' (illustrative)',schematic:true,schematicKind:'cupolaWindow',face:names[k],group:'schematic_cupola_windows',material:'schematic',is_timber:false,vertices,triangles,center:world((x0+x1)/2,(y0+y1)/2,0),color:[.72,.81,.83],exploded_offset:[0,0,0]});}
   cupolaWindows.push({face:names[k],postIds:[post.id,next.id],bottom,top,width:w,status:'Illustrative frame only; glazing, ventilation and attachment unverified; no timber cuts.'});
  }
  components.push(...floorAndFooters(parts));
  if(applyFit){const fitted=typeof OCTAGON_ENCLOSURE_FIT!=='undefined'?OCTAGON_ENCLOSURE_FIT:require('./enclosure-fit.json');for(const p of components){const f=fitted.parts[p.id];if(f){p.vertices=f.vertices;p.triangles=f.triangles;p.center=f.center;p.fitStatus='Clearance-trimmed to existing model only; structural connection unresolved';}}}
  return {components,walls,cupolaWindows,railConnections,compass:'Provisional design compass: P0–P1 is N; site/geographic north is unverified.'};
 }

 function floorAndFooters(parts){
  const result=[],R=Math.min(...parts.filter(p=>/^P[0-7]$/.test(p.id)).map(p=>Math.hypot(p.center[0],p.center[2])-.05/Math.cos(Math.PI/8))),inner=.45,thickness=.01905;
  function mesh(id,kind,polygons,y0,y1,color){
   const vertices=[],tris=[];
   for(let poly of polygons){if(poly.reduce((a,p,i)=>a+p[0]*poly[(i+1)%poly.length][1]-poly[(i+1)%poly.length][0]*p[1],0)>0)poly=poly.slice().reverse();const n=poly.length,off=vertices.length;vertices.push(...poly.map(p=>[p[0],y0,p[1]]),...poly.map(p=>[p[0],y1,p[1]]));
    for(let i=1;i<n-1;i++){tris.push([off,off+i+1,off+i],[off+n,off+n+i,off+n+i+1]);}
    for(let i=0;i<n;i++){const j=(i+1)%n;tris.push([off+i,off+j,off+n+j],[off+i,off+n+j,off+n+i]);}
   }
   const center=vertices.reduce((c,v)=>c.map((x,i)=>x+v[i]/vertices.length),[0,0,0]);
   result.push({id,name:id,schematic:true,schematicKind:kind,group:'schematic_'+kind,material:kind==='floor'?'strand-woven bamboo':kind==='grate'?'metal':'foundation illustration',is_timber:false,vertices,triangles:tris,center,color,exploded_offset:[0,0,0]});
  }
  const radial=(r,k)=>[r*Math.cos(k*Math.PI/4),-r*Math.sin(k*Math.PI/4)];
  // Eight radial sectors; successive concentric octagonal strips show board direction.
  const bands=Math.ceil((R-inner)/.15),step=(R-inner)/bands;
  for(let k=0;k<8;k++){
   const polys=[];for(let b=0;b<bands;b++){const lo=inner+b*step+.0007,hi=b===bands-1?R:inner+(b+1)*step-.0007;polys.push([radial(lo,k),radial(hi,k),radial(hi,k+1),radial(lo,k+1)]);}
   mesh('SCHEM-FLOOR-SECTOR-'+k,'floor',polys,-thickness,0,k%2?[.64,.44,.23]:[.70,.51,.29]);
  }
  // Octagonal metal rim and cross bars leave actual air openings; no load/airflow rating.
  const rim=[];for(let k=0;k<8;k++)rim.push([radial(inner-.025,k),radial(inner,k),radial(inner,k+1),radial(inner-.025,k+1)]);
  mesh('SCHEM-CENTER-GRATE-RIM','grate',rim,-.025,0,[.24,.27,.28]);
  const bars=[];for(let k=0;k<8;k++){const a=k*Math.PI/4,u=[Math.cos(a),-Math.sin(a)],v=[-u[1],u[0]],w=.012;bars.push([[v[0]*w,v[1]*w],[u[0]*(inner-.025)+v[0]*w,u[1]*(inner-.025)+v[1]*w],[u[0]*(inner-.025)-v[0]*w,u[1]*(inner-.025)-v[1]*w],[-v[0]*w,-v[1]*w]]);}
  mesh('SCHEM-CENTER-GRATE-BARS','grate',bars,-.025,0,[.29,.32,.33]);
  for(let k=0;k<8;k++){const p=parts.find(p=>p.id==='P'+k),xs=p.vertices.map(v=>v[0]),zs=p.vertices.map(v=>v[2]),minX=Math.min(...xs)-.0254,maxX=Math.max(...xs)+.0254,minZ=Math.min(...zs)-.0254,maxZ=Math.max(...zs)+.0254,y=Math.min(...p.vertices.map(v=>v[1]));mesh('SCHEM-POST-FOOTER-'+k,'footer',[[[minX,minZ],[maxX,minZ],[maxX,maxZ],[minX,maxZ]]],y-.254,y,[.80,.79,.72]);}
  return result;
 }
 return {build,orientation};
})();
if(typeof module!=='undefined'&&module.exports)module.exports=TimberSchematicWalls;

if(typeof globalThis!=='undefined')globalThis.TimberSchematicWalls=TimberSchematicWalls;
