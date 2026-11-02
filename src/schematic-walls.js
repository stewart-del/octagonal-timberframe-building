/* Provisional design layout only; not source dimensions, structural infill or site north. */
const TimberSchematicWalls=(()=>{
 const orientation={status:'Provisional design compass; site north unverified',north:[Math.cos(Math.PI/8),0,-Math.sin(Math.PI/8)],east:[Math.sin(Math.PI/8),0,Math.cos(Math.PI/8)],faceNames:['N','NW','W','SW','S','SE','E','NE'],northFacePostIds:['P0','P1']};
 const names=orientation.faceNames;
 const usage={N:'Solid wall + bookshelves',NW:'Small window',W:'Door',SW:'Small window',S:'Solid wall + bookshelves',SE:'Small window',E:'Large window',NE:'Small window'};
 const triangles=[[0,2,1],[0,3,2],[4,5,6],[4,6,7],[0,1,5],[0,5,4],[1,2,6],[1,6,5],[2,3,7],[2,7,6],[3,0,4],[3,4,7]];
 function build(parts){
  const components=[],walls=[];
  for(let k=0;k<8;k++){
   const a=parts.find(p=>p.id==='P'+k).center,b=parts.find(p=>p.id==='P'+((k+1)%8)).center;
   const dx=b[0]-a[0],dz=b[2]-a[2],span=Math.hypot(dx,dz),u=[dx/span,0,dz/span],center=[(a[0]+b[0])/2,0,(a[2]+b[2])/2],r=Math.hypot(center[0],center[2]),out=[center[0]/r,0,center[2]/r];
   // 150mm end clearance and 100mm envelope thickness are schematic assumptions.
   const width=span-.30,height=2.20,base=.10,dir=names[k],kind=usage[dir];
   const world=(x,y,z)=>[center[0]+u[0]*x+out[0]*z,y,center[2]+u[2]*x+out[2]*z];
   function box(label,x0,x1,y0,y1,z0=-.05,z1=.05,color=[.88,.86,.75]){
    if(x1<=x0||y1<=y0)return;
    const vertices=[[x0,y0,z0],[x1,y0,z0],[x1,y1,z0],[x0,y1,z0],[x0,y0,z1],[x1,y0,z1],[x1,y1,z1],[x0,y1,z1]].map(v=>world(...v));
    components.push({id:'SCHEM-'+dir+'-'+label,name:dir+' '+label+' (schematic)',schematic:true,schematicKind:label.startsWith('shelf')?'shelf':'wall',face:dir,localBounds:[x0,x1,y0,y1,z0,z1],group:'schematic_walls',material:'schematic',is_timber:false,vertices,triangles,center:world((x0+x1)/2,(y0+y1)/2,(z0+z1)/2),color,exploded_offset:[0,0,0]});
   }
   let opening=null;
   if(kind==='Door')opening={width:.95,bottom:base,top:2.10};
   else if(kind.includes('window'))opening={width:width*(dir==='E'?.65:.30),bottom:dir==='E'?.75:1.0,top:dir==='E'?1.95:1.85};
   if(opening){
    const w=opening.width/2;
    box('left',-width/2,-w,base,height);box('right',w,width/2,base,height);box('below',-w,w,base,opening.bottom);box('above',-w,w,opening.top,height);
   }else box('solid',-width/2,width/2,base,height);
   if(dir==='N'||dir==='S'){
    // Unloaded schematic built-ins only; no book mass or capacity is implied.
    const sw=width*.80/2;
    box('shelf-sideL',-sw,-sw+.025,base,1.95,-.35,-.05,[.60,.43,.27]);box('shelf-sideR',sw-.025,sw,base,1.95,-.35,-.05,[.60,.43,.27]);
    for(let j=0;j<6;j++)box('shelf'+j,-sw,sw,base+j*.35,base+j*.35+.025,-.35,-.05,[.67,.49,.31]);
   }
   walls.push({face:dir,postIds:['P'+k,'P'+((k+1)%8)],usage:kind,width,height,base,opening,center:world(0,1.15,.06),normal:out});
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
  return {components,walls,cupolaWindows,compass:'Provisional design compass: P0–P1 is N; site/geographic north is unverified.'};
 }
 return {build,orientation};
})();
if(typeof module!=='undefined'&&module.exports)module.exports=TimberSchematicWalls;

if(typeof globalThis!=='undefined')globalThis.TimberSchematicWalls=TimberSchematicWalls;
