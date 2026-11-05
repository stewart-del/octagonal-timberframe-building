// TIMESTAMP START 2026-11-05T04:09:58+00:00 | REVISION R000018
/* Quantities follow the installed model, independently of display/explode state. */
(function(root){
'use strict';
const I=.0254,FT=12*I,YD3=27*FT**3;
const num=(value,places=3)=>Number(value.toFixed(places)).toLocaleString('en-US',{maximumFractionDigits:places});
// TIMESTAMP START 2026-11-05T08:49:48+00:00 | REVISION R000037
function meshVolume(part){
 const origin=part.vertices[0],v=part.vertices.map(p=>p.map((x,i)=>x-origin[i]));let volume=0;
 for(const [ia,ib,ic] of part.triangles){const a=v[ia],b=v[ib],c=v[ic];volume+=(a[0]*(b[1]*c[2]-b[2]*c[1])+a[1]*(b[2]*c[0]-b[0]*c[2])+a[2]*(b[0]*c[1]-b[1]*c[0]))/6;}
 if(!(volume>0&&Number.isFinite(volume)))throw Error('Invalid concrete occupied mesh: '+part.id);return volume;
}
// TIMESTAMP END 2026-11-05T08:49:48+00:00 | REVISION R000037
function build(foundation,porch,{allowance=.10,tubeStockLengthM=12*FT,actualTubeDiameterM=null}={}){
 if(!(allowance>=0&&allowance<=1))throw Error('Concrete allowance must be between zero and one');
 const columns=foundation.piers.map(p=>{
  const diameterM=actualTubeDiameterM??p.diameterM,lengthM=p.aboveGradeM+p.embedDepthM;
  if(!(diameterM>0&&lengthM>0&&tubeStockLengthM>=lengthM))throw Error('Invalid tube diameter or stock shorter than cut length');
  return {id:p.id,area:'Main building',shape:'round',diameterM,lengthM,aboveGradeM:p.aboveGradeM,belowGradeM:p.embedDepthM,centerM:[p.centerM[0],p.gradeY_M,p.centerM[2]],topY_M:p.topY_M,bottomY_M:p.gradeY_M-p.embedDepthM,netVolumeM3:Math.PI*diameterM**2*lengthM/4,form:'Sonotube round concrete form',stockLengthM:tubeStockLengthM,offcutM:tubeStockLengthM-lengthM,diameterBasis:actualTubeDiameterM==null?'Nominal modeled diameter; confirm actual inside diameter':'User-entered actual inside diameter'};
 });
 const supportParts=porch.components.filter(p=>p.mudroomRole==='foundation');
 const ids=[...new Set(supportParts.map(p=>p.id.replace(/-BELOW$/,'')))];
 for(const id of ids){
  const zones=supportParts.filter(p=>p.id===id||p.id===id+'-BELOW'),above=zones.find(p=>!p.underground),below=zones.find(p=>p.underground);
  if(zones.length!==2||!above||!below)throw Error('Missing continuous porch column zone: '+id);
  const a=above.localBounds,b=below.localBounds;
  if(Math.abs(a[2]-b[3])>1e-9||[0,1,4,5].some(k=>Math.abs(a[k]-b[k])>1e-9))throw Error('Discontinuous porch column: '+id);
  const widthM=a[1]-a[0],depthM=a[5]-a[4],lengthM=a[3]-b[2];
  columns.push({id,area:'Porch',shape:'rectangular',widthM,depthM,lengthM,aboveGradeM:a[3]-a[2],belowGradeM:b[3]-b[2],centerM:[above.center[0],a[2],above.center[2]],topY_M:a[3],bottomY_M:b[2],netVolumeM3:widthM*depthM*lengthM,form:'Square forms; not a round Sonotube'});
 }
// TIMESTAMP START 2026-11-05T08:49:48+00:00 | REVISION R000037
 const total=items=>items.reduce((sum,p)=>sum+p.netVolumeM3,0),columnVolumeM3=total(columns);
 const pours=porch.components.filter(p=>['floor','stair'].includes(p.mudroomRole)&&p.material.startsWith('cast-in-place concrete')).map(p=>{
  const b=p.localBounds;return {id:p.id,name:p.name,area:p.mudroomRole==='stair'?'Exterior stairs and landings':'Porch pan and drain channel',shape:'formed mesh',dimensionsM:[b[1]-b[0],b[3]-b[2],b[5]-b[4]],netVolumeM3:meshVolume(p),form:'Shared pan/stair formwork; component boundaries partition one pour',volumeBasis:'Actual closed occupied mesh; slope, drain and outlet voids retained'};
 });
 if(!pours.length)throw Error('Missing modeled porch-pan concrete');
 const panVolumeM3=total(pours.filter(p=>p.area==='Porch pan and drain channel')),stairVolumeM3=total(pours.filter(p=>p.area==='Exterior stairs and landings')),netVolumeM3=columnVolumeM3+panVolumeM3+stairVolumeM3;
 return {columns,pours,allowance,columnVolumeM3,panVolumeM3,stairVolumeM3,netVolumeM3,orderVolumeM3:netVolumeM3*(1+allowance),mainVolumeM3:total(columns.filter(p=>p.area==='Main building')),porchVolumeM3:total(columns.filter(p=>p.area==='Porch')),tubeCount:columns.filter(p=>p.shape==='round').length,tubeStockLengthM,totalTubeOffcutM:columns.reduce((s,p)=>s+(p.offcutM||0),0),squareColumnFormSideAreaM2:columns.filter(p=>p.shape==='rectangular').reduce((s,p)=>s+2*(p.widthM+p.depthM)*p.lengthM,0),basis:'All modeled column, porch-pan, channel, stair and landing concrete. Above/below-grade display zones count once as continuous columns. Round columns use πd²L/4; square columns use width × depth × length. Pan/stair quantities integrate the actual sloped occupied meshes and exclude drain/outlet voids. Adjacent mesh pieces partition the pour; they are not separate forms.',exclusions:'Enlarged footings or bell bases, grade beams, over-excavation, reinforcement and concrete mix details remain unspecified and are excluded. Pan, stair and support reinforcement/capacity require design.',designStatus:'Geometry takeoff, not foundation sizing. Verify soils, frost depth, bearing, reinforcement, concrete strength, anchors and bracing before ordering.'};
// TIMESTAMP END 2026-11-05T08:49:48+00:00 | REVISION R000037
}
function quantity(volumeM3){return num(volumeM3/YD3,4)+' yd³ / '+num(volumeM3/FT**3,3)+' ft³ / '+num(volumeM3,4)+' m³';}
function section(p){return p.shape==='round'?num(p.diameterM/I)+' in diameter':num(p.widthM/I)+' × '+num(p.depthM/I)+' in square';}
function csv(report){
// TIMESTAMP START 2026-11-05T08:49:48+00:00 | REVISION R000037
 const rows=[['ID','Area','Form','Section or bounding dimensions (in)','Total length (in)','Above grade (in)','Below grade (in)','Net concrete (yd3)','Net concrete (m3)','Stock length (ft)','Offcut (ft)'],...report.columns.map(p=>[p.id,p.area,p.form,section(p),p.lengthM/I,p.aboveGradeM/I,p.belowGradeM/I,p.netVolumeM3/YD3,p.netVolumeM3,p.stockLengthM?p.stockLengthM/FT:'',p.offcutM?p.offcutM/FT:'']),...report.pours.map(p=>[p.id,p.area,p.form,p.dimensionsM.map(x=>num(x/I,5)).join(' × '),'','','',p.netVolumeM3/YD3,p.netVolumeM3,'','']),['TOTAL COLUMNS','','','','','','',report.columnVolumeM3/YD3,report.columnVolumeM3],['TOTAL PAN AND CHANNEL','','','','','','',report.panVolumeM3/YD3,report.panVolumeM3],['TOTAL STAIRS AND LANDINGS','','','','','','',report.stairVolumeM3/YD3,report.stairVolumeM3],['TOTAL MODELED CONCRETE','','','','','','',report.netVolumeM3/YD3,report.netVolumeM3],['ORDER WITH '+num(report.allowance*100)+'% ALLOWANCE','','','','','','',report.orderVolumeM3/YD3,report.orderVolumeM3]];
// TIMESTAMP END 2026-11-05T08:49:48+00:00 | REVISION R000037
 return rows.map(row=>row.map(value=>'"'+String(typeof value==='number'?Number(value.toFixed(8)):value).replace(/"/g,'""')+'"').join(',')).join('\r\n')+'\r\n';
}
function render(host,report,document){
 host.replaceChildren();
 const add=(tag,text,parent=host)=>{const el=document.createElement(tag);el.textContent=text;parent.appendChild(el);return el;};
 add('h3','Forms and concrete · '+report.columns.length+' continuous columns');
// TIMESTAMP START 2026-11-05T08:49:48+00:00 | REVISION R000037
 add('p','Net modeled concrete: '+quantity(report.netVolumeM3));
// TIMESTAMP END 2026-11-05T08:49:48+00:00 | REVISION R000037
 add('p','Order allowance '+num(report.allowance*100)+'%: '+quantity(report.orderVolumeM3));
// TIMESTAMP START 2026-11-05T08:49:48+00:00 | REVISION R000037
 add('p','Main columns: '+quantity(report.mainVolumeM3)+'. Porch columns: '+quantity(report.porchVolumeM3)+'.');
 add('p','Porch pan and channel: '+quantity(report.panVolumeM3)+'. Exterior stairs and landings: '+quantity(report.stairVolumeM3)+'.');
// TIMESTAMP END 2026-11-05T08:49:48+00:00 | REVISION R000037
 const round=report.columns.filter(p=>p.shape==='round'),example=round[0];
 if(example)add('p',round.length+' round forms, '+section(example)+': cut each to '+num(example.lengthM/I)+' inches from '+num(report.tubeStockLengthM/FT)+'-foot stock. Each leaves '+num(example.offcutM/FT)+' feet; total offcut '+num(report.totalTubeOffcutM/FT)+' feet. '+example.diameterBasis+'.');
 add('p',report.columns.filter(p=>p.shape==='rectangular').length+' porch columns need square forms.');
 const table=add('table',''),head=add('thead','',table),hr=add('tr','',head);
 for(const label of ['Pier / form','Section','Full pour length','Exposed / buried','Net concrete'])add('th',label,hr);
 const body=add('tbody','',table);
 for(const p of report.columns){const tr=add('tr','',body);for(const value of [p.id+' · '+p.form,section(p),num(p.lengthM/I,5)+' in',num(p.aboveGradeM/I,5)+' / '+num(p.belowGradeM/I)+' in',num(p.netVolumeM3/YD3,6)+' yd³'])add('td',value,tr);}
// TIMESTAMP START 2026-11-05T08:49:48+00:00 | REVISION R000037
 add('h4','Pan, channel, stairs and landings');
 const poursTable=add('table',''),poursHead=add('thead','',poursTable),poursRow=add('tr','',poursHead);
 for(const label of ['Piece','Maximum bounding width × height × depth','Net concrete'])add('th',label,poursRow);
 const poursBody=add('tbody','',poursTable);
 for(const p of report.pours){const row=add('tr','',poursBody);for(const value of [p.id+' · '+p.name,p.dimensionsM.map(x=>num(x/I,5)).join(' × ')+' in',num(p.netVolumeM3/YD3,6)+' yd³'])add('td',value,row);}
// TIMESTAMP END 2026-11-05T08:49:48+00:00 | REVISION R000037
 add('p',report.basis);add('p',report.exclusions);add('p',report.designStatus);
 const link=add('a','Sonoco round-form dimensions and pouring instructions');link.href='https://www.sonoco.com/sites/default/files/files/Sonotube%C2%AE%20Round%20Concrete%20Forms%20product%20brochure.pdf';link.target='_blank';link.rel='noopener';
}
const api={build,quantity,section,csv,render};root.OctagonFoundationTakeoff=api;if(typeof module!=='undefined'&&module.exports)module.exports=api;
})(typeof globalThis!=='undefined'?globalThis:this);
// TIMESTAMP END 2026-11-05T04:09:58+00:00 | REVISION R000018
