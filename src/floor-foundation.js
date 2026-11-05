// TIMESTAMP START 2026-11-05T05:14:11+00:00 | REVISION R000024
// TIMESTAMP START 2026-11-05T04:26:16+00:00 | REVISION R000021
// TIMESTAMP START 2026-11-05T04:29:18+00:00 | REVISION R000022
// TIMESTAMP START 2026-11-04T23:48:03+00:00 | REVISION R000012
/* Proposed layout only: sizes, supports and elevations require engineering. */
(function(root){
const I=.0254,ft=.3048;
// TIMESTAMP START 2026-11-05T06:36:54+00:00 | REVISION R000029
const CORK_PRODUCT={manufacturer:'WE Cork',name:'WECU Warm & Quiet',partNumber:"XYZ-4'X100'X 3MM",thicknessM:.003,rollWidthM:1.2192,rollLengthM:30.48,rollAreaSqFt:400,installation:'Loose laid 3 mm cork under the floating engineered bamboo; tape and penetration details remain separate.',sourceURL:'https://www.wecork.com/product/warm-and-quiet-cork-underlayment/'};
// TIMESTAMP END 2026-11-05T06:36:54+00:00 | REVISION R000029
const length=(a,b)=>Math.hypot(a[0]-b[0],a[2]-b[2]);
function build(model){
 const posts=Array.from({length:8},(_,k)=>{const p=model.parts.find(x=>x.id==='P'+k);if(!p)throw Error('Missing post P'+k);return p;});
 const center=[posts.reduce((s,p)=>s+p.center[0]/8,0),0,posts.reduce((s,p)=>s+p.center[2]/8,0)];
// TIMESTAMP START 2026-11-02T20:27:45-05:00 | REVISION R004866
 const pts=posts.map(p=>[p.center[0],0,p.center[2]]),finish=0,finishThickness=.375*I,underlay=.003,subfloor=.703*I,joist=6*I,beam=.286;
// TIMESTAMP END 2026-11-02T20:27:45-05:00 | REVISION R004866
 const beamTop=finish-finishThickness-underlay-subfloor-joist,pierTop=beamTop-beam,grade=pierTop-2*ft;
// TIMESTAMP START 2026-11-02T20:27:45-05:00 | REVISION R004866
// TIMESTAMP START 2026-11-03T12:04:27-05:00 | REVISION R005002
 const midpoint=pts.map(p=>p.map((v,i)=>(v+center[i])/2));
 const piers=[...pts,center,...midpoint].map((c,k)=>({id:k===8?'PIER-C':k>8?'PIER-MID-'+(k-9):'PIER-'+k,postId:k<8?posts[k].id:null,ring:k===8?'center':k>8?'midpoint':'outer',beamId:k>8?'FLOOR-BEAM-'+(k-9):null,centerM:c,localX_M:c[0]-center[0],localZ_M:c[2]-center[2],topY_M:pierTop,gradeY_M:grade,aboveGradeM:2*ft,embedDepthM:6*ft,diameterM:.4064,diameterStatus:'16in display assumption, not design',footing:null,anchors:null,capacity:null}));
// TIMESTAMP END 2026-11-03T12:04:27-05:00 | REVISION R005002
// TIMESTAMP END 2026-11-02T20:27:45-05:00 | REVISION R004866
 const bearingStands=piers.slice(0,8).map((p,k)=>{const dx=p.centerM[0]-center[0],dz=p.centerM[2]-center[2],L=Math.hypot(dx,dz);return {id:'POST-BEARING-STAND-'+k,pierId:p.id,postId:p.postId,centerM:p.centerM,axis:[dx/L,0,dz/L],sideAxis:[-dz/L,0,dx/L],bottomY_M:pierTop,topY_M:0,clearBeamWidthM:.16,sidePlateThicknessM:.0127,plateLengthM:.24,headPlateThicknessM:.01905,material:'steel bearing-stand proposal',status:'Two side plates straddle radial floor beam, head plate bears under unchanged post foot. Chosen visualization only; buckling, welds, anchors, corrosion and load capacity undesigned.'};});
 const members=[];
 const member=(id,kind,a,b,width,depth,top)=>members.push({id,kind,startM:[a[0],top-depth/2,a[2]],endM:[b[0],top-depth/2,b[2]],widthM:width,depthM:depth,lengthM:length(a,b),material:kind==='beam'?'wood beam proposal':'wood joist proposal',capacity:null,connection:'Bearing/attachment design unresolved; no fabrication approval'});
 for(let k=0;k<8;k++)member('FLOOR-BEAM-'+k,'beam',center,pts[k],.14,beam,beamTop);
// TIMESTAMP START 2026-11-02T20:27:45-05:00 | REVISION R004866
 // North follows the existing compass: parallel joists at 16 inches on center.
 const north=[Math.cos(Math.PI/8),0,-Math.sin(Math.PI/8)],east=[-north[2],0,north[0]],spacing=16*I;
 const along=(p,v)=>(p[0]-center[0])*v[0]+(p[2]-center[2])*v[2];
 const limit=Math.max(...pts.map(p=>Math.abs(along(p,east))));
 for(let station=-Math.floor((limit-I)/spacing);station<=Math.floor((limit-I)/spacing);station++){
  const e=station*spacing,hits=[];
  for(let k=0;k<8;k++){
   const a=pts[k],b=pts[(k+1)%8],ea=along(a,east),eb=along(b,east);
   if(Math.abs(eb-ea)<1e-10)continue;
   const t=(e-ea)/(eb-ea);if(t>=-1e-10&&t<=1+1e-10)hits.push(along(a,north)+t*(along(b,north)-along(a,north)));
  }
  const point=n=>[center[0]+east[0]*e+north[0]*n,0,center[2]+east[2]*e+north[2]*n];
  if(hits.length>=2)member('FLOOR-JOIST-NS-'+(station<0?'W'+(-station):'E'+station),'joist',point(Math.min(...hits)),point(Math.max(...hits)),2*I,joist,finish-finishThickness-underlay-subfloor);
 }
// TIMESTAMP END 2026-11-02T20:27:45-05:00 | REVISION R004866
// TIMESTAMP START 2026-11-03T12:04:27-05:00 | REVISION R005002
 const distances=[];for(let a=0;a<piers.length;a++)for(let b=a+1;b<piers.length;b++)distances.push({a:piers[a].id,b:piers[b].id,lengthM:length(piers[a].centerM,piers[b].centerM),type:piers[a].ring==='center'||piers[b].ring==='center'?'radius':piers[a].ring!==piers[b].ring?'between rings':b-a===1||b-a===7?'adjacent chord':b-a===4?'opposite':'diagonal'});
// TIMESTAMP END 2026-11-03T12:04:27-05:00 | REVISION R005002
// TIMESTAMP START 2026-11-02T15:21:56-05:00 | REVISION R004804
// TIMESTAMP START 2026-11-02T20:27:45-05:00 | REVISION R004866
// TIMESTAMP START 2026-11-04T23:17:24+00:00 | REVISION R000029
// TIMESTAMP START 2026-11-05T06:36:54+00:00 | REVISION R000029
 return {revision:model.revision||null,sourcePostCenters:pts,originM:center,axes:'North–south follows the model compass; geographic site bearing unassigned',joistDirectionM:north,joistSpacingM:spacing,piers,bearingStands,members,distances,hubProposal:{coreApothemM:.2032,shoulderApothemM:.35,shoulderHeightM:.143,status:'Chosen stepped bearing geometry; shear, splitting and capacity unverified'},joistEndRule:'Parallel full 2 × 6-inch north–south joists, clipped at the octagonal perimeter, above eight radial beams',layers:[{id:'BAMBOO',material:'Morning Star XD Engineered Sedona Trail Bamboo',thicknessM:finishThickness,topY_M:finish,pattern:'Straight parallel floating click rows, staggered ends',product:{sku:'10041002',productCode:'QCDSBAMSDT5',nominalWidthIn:5.125,nominalThicknessIn:.375,maximumSuppliedLengthIn:48,cartonAreaSqFt:20.48,installation:'Floating; no finish-floor nails or substrate screws',expansionGapIn:.5,lengthBasis:'Proposed cut layout; actual random carton-length mix must be measured'},installationGuide:'https://web.archive.org/web/20170215044612/http://www.lumberliquidators.com/assets/images/installation/schon_quickclic_engineered.pdf'},{id:'FLOORPAD',material:'WE Cork WECU Warm & Quiet 3 mm cork underlayment',thicknessM:underlay,topY_M:finish-finishThickness,product:CORK_PRODUCT,specification:{basis:'Original flooring guide permits 3 mm cork; manufacturer table specifies actual 3 mm x100 ft x4 ft rolls,400 ft².'}},{id:'SUBFLOOR',material:'Georgia-Pacific Plytanium Rated Sheathing 23/32 CAT',thicknessM:subfloor,topY_M:finish-finishThickness-underlay,specification:{stockLengthM:95.875*I,stockWidthM:47.875*I,nominalGridLengthM:8*ft,nominalGridWidthM:4*ft,gapM:.125*I,productURL:'https://www.buildgp.com/product/plytanium-plywood-rated-sheathing',staggerM:4*ft,longAxisM:east,shortAxisM:north,edgeRule:'Square-edge panels, 1/8-inch joint gaps. Butt joints on joists; long seams supported by separately modeled blocking. Perimeter and bearing-stand cuts.'}}],grate:{active:false,status:'Deferred by owner; retain only in history/future option'},warnings:['Proposed layout, not sized or approved spans; joists/beams/connections/soil capacity unknown.','Eight proposed steel bearing stands bridge pier tops to unchanged post feet atY0, straddling floor beams; connection/stand capacity remains undesigned. Central beam hub and rim support details require design.','Six feet of below-grade column is shown as requested; frost depth, diameter, footing and anchors remain unverified.','These added materials are excluded from the primary-timber self-weight result.']};
// TIMESTAMP END 2026-11-05T06:36:54+00:00 | REVISION R000029
// TIMESTAMP END 2026-11-04T23:17:24+00:00 | REVISION R000029
// TIMESTAMP END 2026-11-02T20:27:45-05:00 | REVISION R004866
// TIMESTAMP END 2026-11-02T15:21:56-05:00 | REVISION R004804
}
const inches=m=>(m/I).toFixed(3),measure=m=>{const total=m/I,f=Math.floor(total/12);return f+'ft '+(total-f*12).toFixed(3)+'in';};
// TIMESTAMP START 2026-11-02T20:27:45-05:00 | REVISION R004866
// TIMESTAMP START 2026-11-03T12:04:27-05:00 | REVISION R005002
function settingOutSVG(report){const height=690+Math.ceil(report.distances.length/2)*27,r=Math.max(...report.piers.map(p=>Math.hypot(p.localX_M,p.localZ_M))),s=235/r,x=p=>310+p.localX_M*s,y=p=>295-p.localZ_M*s;return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1100 ${height}"><rect width="1100" height="1150" fill="white"/><g fill="#172b31" font-family="sans-serif"><text x="25" y="28" font-size="20">17-pier setting-out — outer and midpoint octagons</text><text x="25" y="50">Origin: building center. Midpoint piers at half radius; porch faces site west.</text><text x="25" y="71">NOT FOUNDATION DESIGN — verify survey, soils, embedment and anchors.</text>${report.piers.map(p=>`<circle cx="${x(p)}" cy="${y(p)}" r="5"/><text x="${x(p)+8}" y="${y(p)-8}" font-size="12">${p.id}</text>`).join('')}<text x="630" y="110">ID / local X / local Z (feet, inches)</text>${report.piers.map((p,i)=>`<text x="630" y="${135+i*24}" font-size="13">${p.id}: X ${p.localX_M<0?'-':''}${measure(Math.abs(p.localX_M))}; Z ${p.localZ_M<0?'-':''}${measure(Math.abs(p.localZ_M))}</text>`).join('')}<text x="25" y="585">All center-to-center distances (not roof dimensions)</text>${report.distances.map((d,i)=>`<text x="${25+(i%2)*535}" y="${610+Math.floor(i/2)*27}" font-size="13">${d.a} → ${d.b} / ${d.type}: ${measure(d.lengthM)}</text>`).join('')}<text x="25" y="${height-25}">Piers:2ft exposed above reference grade; 6ft below-grade column shown. Diagram not a fixed paper scale.</text></g></svg>`;}
// TIMESTAMP END 2026-11-03T12:04:27-05:00 | REVISION R005002
// TIMESTAMP END 2026-11-02T20:27:45-05:00 | REVISION R004866
function assembly(model,solidData){const report=build(model);if(JSON.stringify(report.sourcePostCenters)!==JSON.stringify(solidData.layout.sourcePostCenters))throw Error('Floor solids are stale for selected post centerlines; regenerate before rendering');const physical=typeof OctagonPhysicalParts!=='undefined'?OctagonPhysicalParts:require('./physical-parts.js');solidData=physical.resolveSourceData(solidData,typeof __dirname==='string'?__dirname:null);return {...report,components:solidData.parts.map(p=>physical.hydrate(p,solidData.prototypes||{})),hideLegacyKinds:['floor','grate','footer'],status:'Proposed assembly; structural review required'};}
// TIMESTAMP START 2026-11-05T06:36:54+00:00 | REVISION R000029
function roomLayout(model,base,solidData){const a=assembly(model,solidData),replaced=new Set(solidData.replacedSchematicIds||[]);return {...base,foundation:a,components:[...base.components.filter(p=>!['floor','grate','footer'].includes(p.schematicKind)&&!replaced.has(p.id)),...a.components]};}
// TIMESTAMP END 2026-11-05T06:36:54+00:00 | REVISION R000029
const api={build,assembly,roomLayout,settingOutSVG,measure};root.OctagonFloorFoundation=api;if(typeof module!=='undefined'&&module.exports)module.exports=api;
})(typeof globalThis!=='undefined'?globalThis:this);

// TIMESTAMP END 2026-11-04T23:48:03+00:00 | REVISION R000012

// TIMESTAMP END 2026-11-05T04:29:18+00:00 | REVISION R000022

// TIMESTAMP END 2026-11-05T04:26:16+00:00 | REVISION R000021

// TIMESTAMP END 2026-11-05T05:14:11+00:00 | REVISION R000024
