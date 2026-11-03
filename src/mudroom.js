// TIMESTAMP START 2026-11-02T14:21:43-05:00 | REVISION R004791
/* Architectural proposal: dimensions and occupied volumes, not structural or plumbing approval. */
(function(root){
'use strict';
const I=.0254,F=12*I;
const triangles=[[0,2,1],[0,3,2],[4,5,6],[4,6,7],[0,1,5],[0,5,4],[1,2,6],[1,6,5],[2,3,7],[2,7,6],[3,0,4],[3,4,7]];
// TIMESTAMP START 2026-11-02T15:00:19-05:00 | REVISION R004797
function build(model,{applyJoinery=true}={}){
// TIMESTAMP END 2026-11-02T15:00:19-05:00 | REVISION R004797
 const parts=model.parts||model,a=parts.find(p=>p.id==='P2'),b=parts.find(p=>p.id==='P3');
 if(!a||!b)throw Error('Mudroom requires the existing P2–P3 doorway bay');
 const origin=[(a.center[0]+b.center[0])/2,0,(a.center[2]+b.center[2])/2],span=Math.hypot(b.center[0]-a.center[0],b.center[2]-a.center[2]),u=[(b.center[0]-a.center[0])/span,0,(b.center[2]-a.center[2])/span],radius=Math.hypot(origin[0],origin[2]),n=[origin[0]/radius,0,origin[2]/radius];
 const world=(x,y,z)=>[origin[0]+u[0]*x+n[0]*z,y,origin[2]+u[2]*x+n[2]*z];
 const local=v=>[(v[0]-origin[0])*u[0]+(v[2]-origin[2])*u[2],v[1],(v[0]-origin[0])*n[0]+(v[2]-origin[2])*n[2]];
// TIMESTAMP START 2026-11-02T20:27:45-05:00 | REVISION R004866
// TIMESTAMP START 2026-11-02T20:31:01-05:00 | REVISION R004867
 const width=8*F,depth=8*F,h=width/2,t=5.5*I,stud=3.5*I,post=4*I,rear=3*I,front=rear+depth,backFloor=-6*I,frontFloor=backFloor-depth/48,grade=-(.01905+.0381+6*I+.286+2*F),slabBottom=backFloor-8*I;
// TIMESTAMP END 2026-11-02T20:31:01-05:00 | REVISION R004867
// TIMESTAMP END 2026-11-02T20:27:45-05:00 | REVISION R004866
 const floorHeight=z=>backFloor-(Math.min(front,Math.max(rear,z))-rear)/48;
 // TIMESTAMP START 2026-11-02T15:00:19-05:00 | REVISION R004797
 const roofAPI=typeof OctagonMudroomRoof!=='undefined'?OctagonMudroomRoof:require('./mudroom-roof.js'),roofSpec=roofAPI.spec(model),rafterDepth=5.5*I,rafterVerticalDepth=rafterDepth*Math.sqrt(1+roofSpec.pitch**2),beamTop=roofSpec.deckBottom(h)-rafterVerticalDepth,beamDepth=5.5*I;
 const roofTop=x=>roofSpec.roofTop(x),roofBottom=x=>roofSpec.deckBottom(x);
 // TIMESTAMP END 2026-11-02T15:00:19-05:00 | REVISION R004797
 const components=[],colors={wood:[.57,.38,.23],wall:[.87,.85,.75],floor:[.58,.62,.60],metal:[.24,.31,.32],roof:[.29,.35,.35],glass:[.58,.78,.80],concrete:[.70,.71,.67]};
 const asFn=value=>typeof value==='function'?value:()=>value;
 function prism(id,name,role,x0,x1,z0,z1,low,high,color,extra={}){
  const lo=asFn(low),hi=asFn(high);
  // Split at function kinks so every emitted prism has planar upper/lower faces.
  if(z0<front-1e-9&&z1>front+1e-9&&[lo,hi].some(f=>[x0,x1].some(x=>Math.abs(f(x,front)-(f(x,z0)+(f(x,z1)-f(x,z0))*(front-z0)/(z1-z0)))>1e-10))){
   prism(id+'-BACK',name,role,x0,x1,z0,front,low,high,color,extra);return prism(id+'-FRONT',name,role,x0,x1,front,z1,low,high,color,extra);
  }
  if(x0<-1e-9&&x1>1e-9&&[lo,hi].some(f=>[z0,z1].some(z=>Math.abs(f(0,z)-(f(x0,z)+(f(x1,z)-f(x0,z))*(-x0)/(x1-x0)))>1e-10))){
   prism(id+'-L',name,role,x0,0,z0,z1,low,high,color,extra);return prism(id+'-R',name,role,0,x1,z0,z1,low,high,color,extra);
  }
  const xz=[[x0,z0],[x1,z0],[x1,z1],[x0,z1]];
  const v=[[x0,lo(x0,z0),z0],[x1,lo(x1,z0),z0],[x1,hi(x1,z0),z0],[x0,hi(x0,z0),z0],[x0,lo(x0,z1),z1],[x1,lo(x1,z1),z1],[x1,hi(x1,z1),z1],[x0,hi(x0,z1),z1]];
  if(!(x1>x0&&z1>z0&&xz.every(([x,z])=>hi(x,z)>lo(x,z)+1e-8)))throw Error('Invalid mudroom solid '+id);
  const vertices=v.map(q=>world(...q)),center=vertices.reduce((c,v)=>c.map((x,i)=>x+v[i]/8),[0,0,0]),k=components.length;
  const displacement=[(x0+x1)*.2,.3+(k%13)*.017,.7+(z0+z1-rear*2)*.14+k*.001];
  const exploded_offset=[u[0]*displacement[0]+n[0]*displacement[2],displacement[1],u[2]*displacement[0]+n[2]*displacement[2]];
  const piece={id:'MUD-'+id,name,schematic:true,schematicKind:'mudroom',displayRole:'mudroom',mudroomRole:role,group:'mudroom',face:'W',material:role==='framing'||role==='furniture'?'proposed timber':role==='floor'?'sealed washdown floor proposal':role==='drain'?'stainless steel drain proposal':'mudroom proposal',is_timber:false,vertices,triangles:triangles.map(q=>q.slice()),localVertices:v,center,label_position:center,color:color||colors.wood,localBounds:[x0,x1,Math.min(...v.map(q=>q[1])),Math.max(...v.map(q=>q[1])),z0,z1],exploded_offset,connectionStatus:'Proposed geometry; support sizing, connections, waterproofing and drainage routing require design.',...extra};
  components.push(piece);return piece;
 }
 // Concrete pan is partitioned around a real linear channel and outlet void.
 const drainWidth=4*I,drainStart=front-drainWidth,drainCenter=(drainStart+front)/2,outlet=3*I,channelTop=x=>frontFloor-.09+Math.abs(x)/96;
 prism('FLOOR','Sloped sealed washdown floor','floor',-h,h,rear,drainStart,slabBottom,(x,z)=>floorHeight(z),colors.floor);
 for(const [side,x0,x1] of [['L',-h-t,-h],['R',h,h+t]])prism('PAN-'+side,'Washdown pan side curb bearing','floor',x0,x1,rear,front+t,slabBottom,(x,z)=>floorHeight(z),colors.floor);
 prism('PAN-FRONT','Mudroom exterior threshold bearing','floor',-h,h,front,front+t,slabBottom,frontFloor,colors.floor);
 for(const [side,x0,x1] of [['L',-h,-outlet/2],['R',outlet/2,h]])prism('CHANNEL-'+side,'Channel bottom sloping to outlet','floor',x0,x1,drainStart,front,slabBottom,(x,z)=>channelTop(x),colors.floor);
 for(const [side,z0,z1] of [['BACK',drainStart,drainCenter-outlet/2],['FRONT',drainCenter+outlet/2,front]])for(const [half,x0,x1] of [['L',-outlet/2,0],['R',0,outlet/2]])prism('CHANNEL-'+side+'-'+half,'Channel outlet surround','floor',x0,x1,z0,z1,slabBottom,(x,z)=>channelTop(x),colors.floor);
 const rail=I/2,grateThickness=I;
 for(const [end,z0,z1] of [['BACK',drainStart,drainStart+rail],['FRONT',front-rail,front]]){
  prism('GRATE-SEAT-'+end,'Drain grate bearing ledge','floor',-h,h,z0,z1,(x,z)=>channelTop(x),(x,z)=>floorHeight(z)-grateThickness,colors.floor);
  prism('GRATE-RAIL-'+end,'Removable drain grate edge','drain',-h,h,z0,z1,(x,z)=>floorHeight(z)-grateThickness,(x,z)=>floorHeight(z),colors.metal);
 }
 const bars=96,barWidth=I/2;
 for(let k=0;k<bars;k++){const x=-h+(k+.5)*width/bars;prism('GRATE-BAR-'+k,'Open drain grate bar '+(k+1),'drain',x-barWidth/2,x+barWidth/2,drainStart+rail,front-rail,(x,z)=>floorHeight(z)-grateThickness,(x,z)=>floorHeight(z),colors.metal);}
 // Four supports touch the slab underside; below-grade footing design is not implied.
 const pier=.254;
// TIMESTAMP START 2026-11-02T20:27:45-05:00 | REVISION R004866
 for(const [side,x] of [['L',-h+.06],['R',h-.06]])for(const [end,z] of [['BACK',rear+.18],['FRONT',front-.18]]){prism('SUPPORT-'+side+'-'+end,'Mudroom floor support proposal','foundation',x-pier/2,x+pier/2,z-pier/2,z+pier/2,grade,slabBottom,colors.concrete);
  prism('SUPPORT-'+side+'-'+end+'-BELOW','Porch support six-foot underground column','foundation',x-pier/2,x+pier/2,z-pier/2,z+pier/2,grade-6*F,grade,colors.concrete,{underground:true,displayOpacity:.28});
 }
// TIMESTAMP END 2026-11-02T20:27:45-05:00 | REVISION R004866
 // A threshold cap bridges the existing floor edge; its under-step meets the pan.
 prism('THRESHOLD-CAP','Level doorway threshold bridge','floor',-.475,.475,-.05,rear,-.01905,0,colors.wood);
 // TIMESTAMP START 2026-11-02T21:06:57-05:00 | REVISION R004876
 prism('THRESHOLD-RISER','Single step up to the main room','floor',-.475,.475,I,rear,slabBottom,-.01905,colors.wood);
 for(const [side,x0,x1] of [['L',-h,-.475],['R',.475,h]])prism('PAN-BACK-'+side,'Washdown pan rear upstand','floor',x0,x1,I,rear,slabBottom,0,colors.floor);
 // TIMESTAMP END 2026-11-02T21:06:57-05:00 | REVISION R004876
 // Open sides: corner posts carry the roof; level guards sit directly behind the benches.
 // TIMESTAMP START 2026-11-02T15:00:19-05:00 | REVISION R004797
 const porchGuardTop=backFloor+38*I,guardRail=3.5*I,picketWidth=1.5*I,maxPicketGap=3.5*I;
 // TIMESTAMP END 2026-11-02T15:00:19-05:00 | REVISION R004797
 for(const [side,x0,x1] of [['L',-h-t,-h],['R',h,h+t]]){
  prism('SILL-'+side,'Porch '+side+' guard base','framing',x0,x1,rear,front+t,(x,z)=>floorHeight(z),(x,z)=>floorHeight(z)+stud,colors.wood);
  // TIMESTAMP START 2026-11-02T15:00:19-05:00 | REVISION R004797
  prism('PLATE-'+side,'Continuous porch roof beam','framing',x0,x1,rear,front+t,beamTop-beamDepth,beamTop,colors.wood);
  // TIMESTAMP END 2026-11-02T15:00:19-05:00 | REVISION R004797
  // TIMESTAMP START 2026-11-02T15:00:19-05:00 | REVISION R004797
// TIMESTAMP START 2026-11-02T20:31:01-05:00 | REVISION R004867
  const postX0=side==='L'?x0:x1-post,postX1=side==='L'?x0+post:x1;
  for(const [end,z0,z1] of [['BACK',rear,rear+post],['FRONT',front+t-post,front+t]])prism('POST-'+side+'-'+end,'Porch full 4 × 4 corner post','framing',postX0,postX1,z0,z1,(x,z)=>floorHeight(z)+stud,beamTop-beamDepth,colors.wood);
// TIMESTAMP END 2026-11-02T20:31:01-05:00 | REVISION R004867
// TIMESTAMP START 2026-11-02T20:31:01-05:00 | REVISION R004867
  const z0=rear+post,z1=front+t-post,length=z1-z0,count=Math.ceil(length/(picketWidth+maxPicketGap)),gap=(length-count*picketWidth)/(count+1),px0=side==='L'?-h-1.5*I:h,px1=side==='L'?-h:h+1.5*I;
// TIMESTAMP END 2026-11-02T20:31:01-05:00 | REVISION R004867
  // TIMESTAMP END 2026-11-02T15:00:19-05:00 | REVISION R004797
  prism('GUARD-TOP-'+side,'Level railing behind side bench','framing',x0,x1,z0,z1,porchGuardTop-guardRail,porchGuardTop,colors.wood);
  for(let k=0;k<count;k++){const z=z0+gap+k*(picketWidth+gap);prism('GUARD-PICKET-'+side+'-'+k,'Porch side railing vertical','framing',px0,px1,z,z+picketWidth,(x,z)=>floorHeight(z)+stud,porchGuardTop-guardRail,colors.wood);}
 }
 // TIMESTAMP START 2026-11-02T15:00:19-05:00 | REVISION R004797
 const frameStations=Array.from({length:5},(_,k)=>roofSpec.firstFrameZ_M+k*(front+t-stud/2-roofSpec.firstFrameZ_M)/4);
 for(let k=0;k<frameStations.length;k++)for(const [side,x0,x1,sign] of [['L',-h-t,3*I,1],['R',-3*I,h+t,-1]]){
  const z=frameStations[k],top=x=>roofSpec.ridgeRoofTopY_M-.024+sign*x*roofSpec.pitch;
  prism('RAFTER-'+side+'-'+k,'Gabled porch rafter blank','framing',x0,x1,z-stud/2,z+stud/2,(x)=>top(x)-rafterVerticalDepth,(x)=>top(x),colors.wood,{mudroomScreen:true,mudroomRoof:true,joineryBlank:true,stockWidthM:stud,stockDepthM:rafterDepth});
 }
 for(let k=0;k<frameStations.length-1;k++){const z=(frameStations[k]+frameStations[k+1])/2;prism('ROOF-TIE-'+k,'Porch transverse roof tie','framing',-h-t,h+t,z-stud/2,z+stud/2,beamTop-beamDepth/2,beamTop+beamDepth/2,colors.wood,{mudroomScreen:true,mudroomRoof:true,joineryBlank:true});}
 // Back remains open to the existing doorway; its original header is preserved.
 // TIMESTAMP END 2026-11-02T15:00:19-05:00 | REVISION R004797
 // TIMESTAMP START 2026-11-02T15:00:19-05:00 | REVISION R004797
 const entryHalf=.475,frontGuardTop=frontFloor+36*I;
 // TIMESTAMP END 2026-11-02T15:00:19-05:00 | REVISION R004797
// TIMESTAMP START 2026-11-02T20:31:01-05:00 | REVISION R004867
 for(const [side,x0,x1] of [['L',-h-t+post,-entryHalf-post],['R',entryHalf+post,h+t-post]]){
// TIMESTAMP END 2026-11-02T20:31:01-05:00 | REVISION R004867
  // TIMESTAMP START 2026-11-02T15:00:19-05:00 | REVISION R004797
// TIMESTAMP START 2026-11-02T20:31:01-05:00 | REVISION R004867
  prism('FRONT-SILL-'+side,'Porch front guard base','framing',side==='L'?-h:entryHalf,side==='L'?-entryHalf:h,front,front+t,frontFloor,frontFloor+stud,colors.wood);
// TIMESTAMP END 2026-11-02T20:31:01-05:00 | REVISION R004867
  // TIMESTAMP END 2026-11-02T15:00:19-05:00 | REVISION R004797
  // TIMESTAMP START 2026-11-02T15:00:19-05:00 | REVISION R004797
  prism('FRONT-GUARD-'+side,'Porch front guard rail','framing',x0,x1,front,front+t,frontGuardTop-guardRail,frontGuardTop,colors.wood);
  // TIMESTAMP END 2026-11-02T15:00:19-05:00 | REVISION R004797
  const length=x1-x0,count=Math.ceil(length/(picketWidth+maxPicketGap)),gap=(length-count*picketWidth)/(count+1);
  // TIMESTAMP START 2026-11-02T15:00:19-05:00 | REVISION R004797
  for(let k=0;k<count;k++){const x=x0+gap+k*(picketWidth+gap);prism('FRONT-PICKET-'+side+'-'+k,'Porch front railing vertical','framing',x,x+picketWidth,front,front+guardRail,frontFloor+stud,frontGuardTop-guardRail,colors.wood);}
  // TIMESTAMP END 2026-11-02T15:00:19-05:00 | REVISION R004797
 }
 // TIMESTAMP START 2026-11-02T15:00:19-05:00 | REVISION R004797
// TIMESTAMP START 2026-11-02T20:31:01-05:00 | REVISION R004867
 for(const [side,x0,x1] of [['L',-entryHalf-post,-entryHalf],['R',entryHalf,entryHalf+post]])prism('ENTRY-GUARD-POST-'+side,'Porch full 4 × 4 railing post beside open stair passage','framing',x0,x1,front+t-post,front+t,frontFloor+stud,frontGuardTop,colors.wood);
// TIMESTAMP END 2026-11-02T20:31:01-05:00 | REVISION R004867
 // TIMESTAMP END 2026-11-02T15:00:19-05:00 | REVISION R004797
 // TIMESTAMP START 2026-11-02T15:00:19-05:00 | REVISION R004797
 prism('HEADER-FRONT','Porch front roof header','framing',-h,h,front,front+t,beamTop-.10,beamTop,colors.wood,{mudroomScreen:true,mudroomRoof:true});
 components.push(...roofAPI.build(model).components);
 // TIMESTAMP END 2026-11-02T15:00:19-05:00 | REVISION R004797
 // Two level benches and lower shoe shelves; legs are scribed to the sloping floor.
 const seatTop=backFloor+18*I,seatThick=1.5*I,benchZ0=rear+10*I,benchZ1=drainStart-8*I,benchDepth=18*I;
 for(const [side,x0,x1] of [['L',-h,-h+benchDepth],['R',h-benchDepth,h]]){
  prism('BENCH-'+side,'Mudroom side bench','furniture',x0,x1,benchZ0,benchZ1,seatTop-seatThick,seatTop,colors.wood);
  const leg=2*I,shelfTop=backFloor+6*I,shelfThick=.75*I;
  for(const [end,z0,z1] of [['BACK',benchZ0,benchZ0+leg],['FRONT',benchZ1-leg,benchZ1]])for(const [edge,lx0,lx1] of [['OUTER',x0,x0+leg],['INNER',x1-leg,x1]]){
   prism('BENCH-LEG-'+side+'-'+end+'-'+edge,'Bench leg seated on sloped floor','furniture',lx0,lx1,z0,z1,(x,z)=>floorHeight(z),shelfTop-shelfThick,colors.wood);
   prism('BENCH-LEG-UPPER-'+side+'-'+end+'-'+edge,'Bench upper leg','furniture',lx0,lx1,z0,z1,shelfTop,seatTop-seatThick,colors.wood);
  }
  // The shelf spans and caps the four lower legs, carrying the upper legs above it.
  prism('SHOE-SHELF-'+side,'Shoe storage under bench','furniture',x0,x1,benchZ0,benchZ1,shelfTop-shelfThick,shelfTop,colors.wood);
  // TIMESTAMP START 2026-11-02T21:06:57-05:00 | REVISION R004876
  const bx0=side==='L'?-h:.475+4*I,bx1=side==='L'?-.475-4*I:h;
  // TIMESTAMP END 2026-11-02T21:06:57-05:00 | REVISION R004876
  prism('COAT-BOARD-'+side,'Wall coat rack','furniture',bx0,bx1,rear,rear+I,1.35,1.50,colors.wood);
  for(let k=0;k<3;k++){const x=bx0+(k+.5)*(bx1-bx0)/3,hook=I/4,z0=rear+I,z1=z0+2*I;prism('HOOK-'+side+'-'+k,'Coat hook','furniture',x-hook/2,x+hook/2,z0,z1,1.40,1.40+hook,colors.metal);prism('HOOK-LIP-'+side+'-'+k,'Coat hook upturn','furniture',x-hook/2,x+hook/2,z1-hook,z1,1.40+hook,1.43,colors.metal);}
 }
 // Supported outside landing and equal stair risers connect the lowered entry to reference grade.
 const landingZ0=front+t,landingZ1=landingZ0+3*F,landingHalf=22*I,riserCount=6,rise=(frontFloor-grade)/riserCount,tread=F,railThickness=1.5*I,guardTop=frontFloor+36*I;
 prism('LANDING','Exterior entry landing','stair',-landingHalf,landingHalf,landingZ0,landingZ1,grade,frontFloor,colors.floor);
 for(let k=0;k<riserCount-1;k++)prism('STEP-'+k,'Exterior step '+(k+1),'stair',-landingHalf,landingHalf,landingZ1+k*tread,landingZ1+(k+1)*tread,grade,frontFloor-(k+1)*rise,colors.floor);
 const stairEnd=landingZ1+(riserCount-1)*tread;
 prism('GROUND-LANDING','Lower exterior landing','stair',-landingHalf,landingHalf,stairEnd,stairEnd+3*F,grade-.05,grade,colors.floor);
 for(const [side,x0,x1] of [['L',-landingHalf,-landingHalf+railThickness],['R',landingHalf-railThickness,landingHalf]]){
  prism('LANDING-RAIL-'+side,'Exterior landing guard rail','stair',x0,x1,landingZ0,landingZ1,guardTop-railThickness,guardTop,colors.wood);
  const count=8,picket=I;
  for(let k=0;k<count;k++){const z=landingZ0+(k+.5)*(landingZ1-landingZ0)/count;prism('LANDING-PICKET-'+side+'-'+k,'Landing guard vertical','stair',x0,x1,z-picket/2,z+picket/2,frontFloor,guardTop-railThickness,colors.wood);}
  const handrailY=z=>guardTop-(z-landingZ1)*rise/tread;
  prism('STAIR-RAIL-'+side,'Exterior stair handrail','stair',x0,x1,landingZ1,stairEnd,(x,z)=>handrailY(z)-railThickness,(x,z)=>handrailY(z),colors.wood);
  for(let k=0;k<riserCount-1;k++)for(let q=0;q<3;q++){const z=landingZ1+(k+(q+.5)/3)*tread;prism('STAIR-PICKET-'+side+'-'+k+'-'+q,'Stair guard vertical','stair',x0,x1,z-picket/2,z+picket/2,frontFloor-(k+1)*rise,(x,z)=>handrailY(z)-railThickness,colors.wood);}
 }
 // TIMESTAMP START 2026-11-02T15:00:19-05:00 | REVISION R004797
 const dimensions={clearWidthM:width,clearDepthM:depth,rearZ_M:rear,frontZ_M:front,backFloorY_M:backFloor,frontFloorY_M:frontFloor,mainFloorY_M:0,floorSlope:1/48,floorFallM:depth/48,wallThicknessM:t,benchDepthM:benchDepth,benchSeatHeightAtBackM:18*I,clearAisleM:width-2*benchDepth,drainWidthM:drainWidth,drainStartZ_M:drainStart,drainOutletSizeM:outlet,drainOutletCenter:[0,channelTop(0),drainCenter],entryWidthM:2*entryHalf,guardTopY_M:porchGuardTop,maxGuardPicketGapM:maxPicketGap,landingDepthM:3*F,stairWidthM:2*landingHalf,stairRiserCount:riserCount,stairRiserM:rise,stairTreadM:tread,gradeY_M:grade,roofPitch:roofSpec.pitch,roofHighY_M:roofSpec.ridgeRoofTopY_M,roofRafterWidthM:stud,roofRafterDepthM:rafterDepth,roofRafterEndBearingM:t,roofBeamTopY_M:beamTop,roofBeamDepthM:beamDepth,roofFrameStations:frameStations,minimumInteriorRoofHeightM:beamTop-beamDepth/2-backFloor,centerM:world(0,(frontFloor+beamTop)/2,(rear+front)/2)};
 // TIMESTAMP END 2026-11-02T15:00:19-05:00 | REVISION R004797
 // TIMESTAMP START 2026-11-02T15:00:19-05:00 | REVISION R004797
 const notes=['Proposed open eight-foot-square covered porch; six-inch step down from the existing room at the doorway.','Sealed floor falls one quarter inch per foot to an open linear grate; channel slopes to a real outlet void. Waterproofing, drain trap, cleanout, lawful discharge and freeze protection are not specified.','The two side benches are level, with the side railings directly behind for back support. Clear central aisle is five feet. Coat racks sit on the existing rear wall and shoe shelves sit beneath the benches.','Traditional joint families are modeled with matched recesses: shouldered mortise-and-tenon posts and rails, face-housed pegged 2 × 6 braces, open roof half-laps and birdsmouth seats. Joint sizes, uplift restraint and capacities remain proposals.','Roof flashing, slab reinforcement, support footings, anchors, handrail profiles, accessibility and code compliance require design. The six equal exterior risers use model reference grade, not a survey.','Porch components are separate from the primary-timber inventory, structural weight calculation and fabrication exports.'];
 // TIMESTAMP END 2026-11-02T15:00:19-05:00 | REVISION R004797
 // TIMESTAMP START 2026-11-02T15:00:19-05:00 | REVISION R004797
 let joinery=null;
 if(applyJoinery){
  const fit=typeof MUDROOM_JOINERY_FIT!=='undefined'?MUDROOM_JOINERY_FIT:(typeof require==='function'?require('./mudroom-joinery-fit.json'):null);
  if(!fit||fit.status!=='PASS')throw Error('Verified porch joinery data is unavailable; regenerate before rendering');
  for(const id of ['P2','P3']){const anchor=parts.find(p=>p.id===id).center;if(!fit.anchors[id]||anchor.some((v,i)=>Math.abs(v-fit.anchors[id][i])>1e-10))throw Error('Porch joinery anchors are stale');}
  for(const p of components){const f=fit.parts[p.id];if(f)Object.assign(p,f);}
  components.push(...fit.added_parts);joinery={joints:fit.joints,assembly:fit.assembly,verification:fit.verification};
 }
 return {components,dimensions,notes,joinery,world,local,floorHeight,roofTop,roofBottom,origin,tangent:u,outward:n};
 // TIMESTAMP END 2026-11-02T15:00:19-05:00 | REVISION R004797
}
const api={build};root.OctagonMudroom=api;if(typeof module!=='undefined'&&module.exports)module.exports=api;
})(typeof globalThis!=='undefined'?globalThis:this);
// TIMESTAMP END 2026-11-02T14:21:43-05:00 | REVISION R004791
