// TIMESTAMP START 2026-11-02T20:56:29-05:00 | REVISION R004874
/* Orthographic line drawings from canonical assembled meshes. Not fabrication plans. */
(function(root){
'use strict';
if(typeof module!=='undefined'&&module.exports&&!root.OctagonFloorFoundation)root.OctagonFloorFoundation=require('./floor-foundation.js');
const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const temporary=p=>p.temporary||p.material==='steel'||/tempor|metal_spacer|erection/.test(p.group);
// TIMESTAMP START 2026-11-03T07:12:33-05:00 | REVISION R004914
const included=(p,aids)=>p.material!=='surface'&&p.group!=='roof_envelope'&&(!temporary(p)||(aids&&p.id==='M-TMP'));
// TIMESTAMP END 2026-11-03T07:12:33-05:00 | REVISION R004914
const project=(v,view)=>view==='top'?[v[0],-v[2],v[1]]:[v[0],-v[1],v[2]];
const measure=m=>(m/.0254).toFixed(2)+' in / '+m.toFixed(3)+' m';
function bounds(parts){const lo=[Infinity,Infinity,Infinity],hi=[-Infinity,-Infinity,-Infinity];for(const p of parts)for(const v of p.vertices)for(let k=0;k<3;k++){lo[k]=Math.min(lo[k],v[k]);hi[k]=Math.max(hi[k],v[k]);}return {lo,hi,size:lo.map((v,i)=>hi[i]-v)};}
// TIMESTAMP START 2026-11-02T20:56:29-05:00 | REVISION R004874
const dot=(a,b)=>a.reduce((total,x,i)=>total+x*b[i],0),unit=a=>a.map(x=>x/Math.hypot(...a));
function axialLength(part){const axis=unit(part.axis_end.map((x,i)=>x-part.axis_start[i])),q=part.vertices.map(v=>dot(v,axis));return Math.max(...q)-Math.min(...q);}
// TIMESTAMP START 2026-11-03T07:17:50-05:00 | REVISION R004916
const degrees=radians=>(radians*180/Math.PI).toFixed(2)+'°';
function memberInclination(p){const d=p.axis_end.map((x,i)=>x-p.axis_start[i]);return degrees(Math.atan2(Math.abs(d[1]),Math.hypot(d[0],d[2])));}
function memberSection(p){return p.dimensions.section_display||p.dimensions.width_in+' × '+p.dimensions.depth_in+' in';}
// TIMESTAMP END 2026-11-03T07:17:50-05:00 | REVISION R004916
function measurements(model,porch=false){
 const parts=model.parts,byId=Object.fromEntries(parts.map(p=>[p.id,p])),F=root.OctagonFloorFoundation.build(model);
 const roofAPI=typeof TimberRoofCoverings!=='undefined'?TimberRoofCoverings:require('./roof-coverings.js');
 const porchAPI=typeof OctagonMudroom!=='undefined'?OctagonMudroom:require('./mudroom.js');
 const n=root.TimberSchematicWalls.orientation.north,e=root.TimberSchematicWalls.orientation.east;
 const span=(pieces,axis)=>{const q=pieces.flatMap(p=>p.vertices.map(v=>dot(v,axis)));return Math.max(...q)-Math.min(...q);};
// TIMESTAMP START 2026-11-03T13:32:57-05:00 | REVISION R005027
 if(porch){const layout=model.generatedLayouts?.mudroom||porchAPI.build(model),d=layout.dimensions,roof=typeof OctagonMudroomRoof!=='undefined'?OctagonMudroomRoof.spec(model):require('./mudroom-roof.js').spec(model);
// TIMESTAMP END 2026-11-03T13:32:57-05:00 | REVISION R005027
  const p=layout.components.find(p=>p.id==='MUD-RAFTER-L-2'),axis=unit([roof.tangent[0],roof.pitch,roof.tangent[2]]),q=p.vertices.map(v=>dot(v,axis));
// TIMESTAMP START 2026-11-03T07:17:50-05:00 | REVISION R004916
  return {rows:[['Clear floor width',d.clearWidthM],['Clear floor depth',d.clearDepthM],['Roof span across eaves',2*roof.halfWidthM],['Gable rise: eave to ridge',roof.halfWidthM*roof.pitch],['Gable horizontal run',roof.halfWidthM],['Gable pitch',String(roof.pitch*12)+' : 12'],['Gable roof angle',degrees(Math.atan(roof.pitch))],['Porch post section','4 × 4 in'],['Porch rafter section',(p.stockWidthM/.0254).toFixed(2)+' × '+(p.stockDepthM/.0254).toFixed(2)+' in'],['Middle rafter overall axial length',Math.max(...q)-Math.min(...q)],['Ridge above main finished floor',roof.ridgeRoofTopY_M],['Porch floor fall, rear to front',d.backFloorY_M-d.frontFloorY_M],['Stair rise per step',d.stairRiserM],['Stair tread depth',d.stairTreadM],['Underground column depth',6*.3048]],roofSection:{run:roof.halfWidthM,rise:roof.halfWidthM*roof.pitch,span:2*roof.halfWidthM,angle:degrees(Math.atan(roof.pitch)),slopeLength:Math.hypot(roof.halfWidthM,roof.halfWidthM*roof.pitch),endLabel:'Ridge'},floor:F,axis:roof.tangent,normal:roof.outward};}
// TIMESTAMP END 2026-11-03T07:17:50-05:00 | REVISION R004916
 const posts=parts.filter(p=>p.group==='perimeter_posts'),radial=unit([byId.P0.center[0],0,byId.P0.center[2]]),roof=roofAPI.build(model).components.filter(p=>p.material==='cedar'&&p.roof_face===0),v=roof.flatMap(p=>p.vertices),q=v.map(p=>dot(p,n)),near=Math.min(...q),far=Math.max(...q),heightAt=x=>Math.max(...v.filter((p,i)=>Math.abs(q[i]-x)<1e-7).map(p=>p[1])),low=heightAt(far),high=heightAt(near);
 const centers=posts.map(p=>dot(p.center,radial));
// TIMESTAMP START 2026-11-02T21:09:01-05:00 | REVISION R004877
// TIMESTAMP START 2026-11-03T07:17:50-05:00 | REVISION R004916
 return {rows:[['Outside posts: opposite corners',span(posts,radial)],['Opposite post centerlines',Math.max(...centers)-Math.min(...centers)],['Outside frame: east–west',span(posts,e)],['Roof rise: eave to cupola junction',high-low],['Roof-face horizontal run',far-near],['Roof-face pitch',((high-low)/(far-near)*12).toFixed(3)+' : 12'],['Roof-face angle',degrees(Math.atan2(high-low,far-near))],['Main roof span across opposite eaves',2*far],['Main hip R0 overall axial length',axialLength(byId.R0)],['Short rafter J0-0 overall axial length',axialLength(byId['J0-0'])],['Cupola rafter CR0 overall axial length',axialLength(byId.CR0)],['Main eave above finished floor',low],['Cupola rafter peak above finished floor',Math.max(...parts.filter(p=>p.group==='cupola_rafters').flatMap(p=>p.vertices.map(v=>v[1])))],['Cupola clear inside diameter',2*Math.min(...byId.C0.vertices.map(v=>dot(v,radial)))],['Finished floor above reference grade',-F.piers[0].gradeY_M],['Pier top above reference grade',F.piers[0].aboveGradeM],['Underground column depth',F.piers[0].embedDepthM],['Full floor joist section','2 × 6 in; north–south'],['Main hip R0 inclination',memberInclination(byId.R0)],['Short rafter J0-0 inclination',memberInclination(byId['J0-0'])],['Cupola rafter CR0 inclination',memberInclination(byId.CR0)],['Radial tie T0 overall axial length',axialLength(byId.T0)],['Main post P0 overall axial length',axialLength(byId.P0)],['Main post / cupola post sections','8 × 8 in / 6 × 6 in'],['Hip R0 / tie T0 sections',memberSection(byId.R0)+' / '+memberSection(byId.T0)],['Short rafter J0-0 section',memberSection(byId['J0-0'])],['Octagon sector / interior plan angles','45.00° / 135.00°']],roofSection:{run:far-near,rise:high-low,span:2*far,angle:degrees(Math.atan2(high-low,far-near)),slopeLength:Math.hypot(far-near,high-low),endLabel:'Cupola junction'},floor:F,axis:e,normal:n};
// TIMESTAMP END 2026-11-03T07:17:50-05:00 | REVISION R004916
// TIMESTAMP END 2026-11-02T21:09:01-05:00 | REVISION R004877
}

// TIMESTAMP END 2026-11-02T20:56:29-05:00 | REVISION R004874
const layouts=new WeakMap(),results=new WeakMap();
// TIMESTAMP START 2026-11-02T14:22:13-05:00 | REVISION R004792
function* drawSteps(model,{view='top',aids=false,hidden=false,walls=false,shelves=false,cupolaWindows=false,floor=false,roofCover=false,mudroom=false,modelHash=''}={}){
// TIMESTAMP END 2026-11-02T14:22:13-05:00 | REVISION R004792
// TIMESTAMP START 2026-11-02T21:09:01-05:00 | REVISION R004877
// TIMESTAMP START 2026-11-03T13:32:57-05:00 | REVISION R005027
 let schematic=model.generatedLayouts?.schematic||layouts.get(model);if(!schematic){schematic=root.TimberSchematicWalls?.build(model.parts);if(schematic&&model.wallJoinery){const W=root.OctagonWallJoinery||(typeof require==='function'?require('./wall-joinery.js'):null);schematic=W.applyLayout(schematic,model.wallJoinery);}if(schematic&&root.OctagonFloorFoundation){const f=typeof FLOOR_FOUNDATION_DATA!=='undefined'?FLOOR_FOUNDATION_DATA:(typeof require==='function'?require('./floor-foundation-solids.json'):null);if(f)schematic=root.OctagonFloorFoundation.roomLayout(model,schematic,f);}if(schematic)layouts.set(model,schematic);}
// TIMESTAMP END 2026-11-03T13:32:57-05:00 | REVISION R005027
// TIMESTAMP END 2026-11-02T21:09:01-05:00 | REVISION R004877
 const roofAPI=typeof TimberRoofCoverings!=='undefined'?TimberRoofCoverings:(typeof require==='function'?require('./roof-coverings.js'):null);
 const layout=schematic,extras=(layout?.components||[]).filter(p=>p.schematicKind==='shelf'?shelves:p.schematicKind==='cupolaWindow'?cupolaWindows:['floor','floorAssembly'].includes(p.schematicKind)?floor:walls);
// TIMESTAMP START 2026-11-02T14:22:13-05:00 | REVISION R004792
 const mudroomAPI=typeof OctagonMudroom!=='undefined'?OctagonMudroom:(typeof require==='function'?require('./mudroom.js'):null);
 // TIMESTAMP START 2026-11-02T20:56:29-05:00 | REVISION R004874
const metrics=measurements(model,mudroom),north=metrics.normal,east=metrics.axis;
 const projection=v=>view==='top'?[dot(v,east),-dot(v,north),v[1]]:[dot(v,east),-v[1],dot(v,north)];
 // TIMESTAMP START 2026-11-02T22:13:32-05:00 | REVISION R004886
// TIMESTAMP START 2026-11-03T13:32:57-05:00 | REVISION R005027
 const parts=mudroom?(model.generatedLayouts?.mudroom||mudroomAPI.build(model)).components.filter(p=>roofCover||!p.roofLayer):[...model.parts.filter(p=>included(p,aids)),...extras,...(roofCover&&roofAPI?roofAPI.build(model).components:[])],b=bounds(parts),axis=view==='top'?2:1;
// TIMESTAMP END 2026-11-03T13:32:57-05:00 | REVISION R005027
 // TIMESTAMP END 2026-11-02T22:13:32-05:00 | REVISION R004886
// TIMESTAMP END 2026-11-02T20:56:29-05:00 | REVISION R004874
// TIMESTAMP END 2026-11-02T14:22:13-05:00 | REVISION R004792
 const all=parts.flatMap(p=>p.vertices.map(v=>projection(v))),lo=[Math.min(...all.map(v=>v[0])),Math.min(...all.map(v=>v[1]))],hi=[Math.max(...all.map(v=>v[0])),Math.max(...all.map(v=>v[1]))];
 const s=Math.min(760/(hi[0]-lo[0]),490/(hi[1]-lo[1])),ox=500-(lo[0]+hi[0])*s/2,oy=345-(lo[1]+hi[1])*s/2;
 const pt=v=>[ox+v[0]*s,oy+v[1]*s],line=(a,z,cls)=>`<path class="${cls}" d="M${a[0].toFixed(3)},${a[1].toFixed(3)}L${z[0].toFixed(3)},${z[1].toFixed(3)}"/>`;
 // Spatially indexed frontmost triangle depth. Split edges for approximate hidden-line display.
 const grid=new Map(),N=48,cell=v=>[Math.max(0,Math.min(N-1,Math.floor((v[0]-lo[0])/(hi[0]-lo[0])*N))),Math.max(0,Math.min(N-1,Math.floor((v[1]-lo[1])/(hi[1]-lo[1])*N)))];
 for(const p of parts)for(const t of p.triangles){const q=t.map(i=>projection(p.vertices[i]));const den=(q[1][1]-q[2][1])*(q[0][0]-q[2][0])+(q[2][0]-q[1][0])*(q[0][1]-q[2][1]);if(Math.abs(den)<1e-12)continue;const a=cell([Math.min(...q.map(v=>v[0])),Math.min(...q.map(v=>v[1]))]),z=cell([Math.max(...q.map(v=>v[0])),Math.max(...q.map(v=>v[1]))]);for(let x=a[0];x<=z[0];x++)for(let y=a[1];y<=z[1];y++){const k=x+':'+y;if(!grid.has(k))grid.set(k,[]);grid.get(k).push({q,den});}yield;}
 const obscured=v=>{for(const {q,den} of grid.get(cell(v).join(':'))||[]){const u=((q[1][1]-q[2][1])*(v[0]-q[2][0])+(q[2][0]-q[1][0])*(v[1]-q[2][1]))/den,w=((q[2][1]-q[0][1])*(v[0]-q[2][0])+(q[0][0]-q[2][0])*(v[1]-q[2][1]))/den;if(u>=-1e-8&&w>=-1e-8&&u+w<=1+1e-8&&u*q[0][2]+w*q[1][2]+(1-u-w)*q[2][2]>v[2]+2e-5)return true;}return false;};
 let solid=[],behind=[];
 for(const p of parts){let segs=[],back=[];for(const e of root.TimberEdgeMeasurements.edgeMeasurementReport(p).edges){const a=projection(e.a),z=projection(e.b),len=Math.hypot(z[0]-a[0],z[1]-a[1]);if(len<1e-8)continue;const count=Math.max(1,Math.ceil(len*s/6));let start=0,prev=null;for(let k=0;k<count;k++){const at=f=>a.map((v,i)=>v+(z[i]-v)*f),hide=obscured(at((k+.5)/count));if(prev!==null&&hide!==prev){(prev?back:segs).push(line(pt(at(start/count)),pt(at(k/count)),temporary(p)?'aid':prev?'hidden':'edge'));start=k;}prev=hide;if(k===count-1)(hide?back:segs).push(line(pt(at(start/count)),pt(z),temporary(p)?'aid':hide?'hidden':'edge'));}}solid.push(`<g><title>${esc(p.id+' — '+p.name)}</title>${segs.join('')}</g>`);if(hidden)behind.push(`<g><title>${esc(p.id+' hidden edges')}</title>${back.join('')}</g>`);yield;}
 const x0=ox+lo[0]*s,x1=ox+hi[0]*s,y0=oy+lo[1]*s,y1=oy+hi[1]*s;
 const hdim=(y,label)=>line([x0,y1],[x0,y+8],'dim')+line([x1,y1],[x1,y+8],'dim')+line([x0,y],[x1,y],'dim')+`<text x="500" y="${y-7}" text-anchor="middle">${esc(label)}</text>`;
 const vdim=(x,label)=>line([x0,y0],[x-8,y0],'dim')+line([x0,y1],[x-8,y1],'dim')+line([x,y0],[x,y1],'dim')+`<text transform="translate(${x-8},${(y0+y1)/2}) rotate(-90)" text-anchor="middle">${esc(label)}</text>`;
 const scaleM=2,scaleX=130,scaleY=680;
 // TIMESTAMP START 2026-11-02T20:56:29-05:00 | REVISION R004874
let compass='';if(view==='top'&&!mudroom){const v=projection(north),cx=840,cy=130;
// TIMESTAMP END 2026-11-02T20:56:29-05:00 | REVISION R004874
// TIMESTAMP START 2026-11-03T08:08:16-05:00 | REVISION R004938
compass=line([cx,cy],[cx+v[0]*48,cy+v[1]*48],'dim')+`<text x="${cx+v[0]*54}" y="${cy+v[1]*54}">N</text><text x="765" y="180" class="small">Site north: P0–P1</text><text x="765" y="196" class="small">Porch / door face west</text>`;}
// TIMESTAMP END 2026-11-03T08:08:16-05:00 | REVISION R004938
 // TIMESTAMP START 2026-11-02T20:56:29-05:00 | REVISION R004874
// TIMESTAMP START 2026-11-03T08:08:16-05:00 | REVISION R004938
const title=(mudroom?'PORCH':'MAIN BUILDING')+(view==='top'?' — PLAN':mudroom?' — WEST ELEVATION':' — NORTH ELEVATION');
// TIMESTAMP END 2026-11-03T08:08:16-05:00 | REVISION R004938
// TIMESTAMP START 2026-11-03T07:17:50-05:00 | REVISION R004916
 const metricTop=1114,sheetHeight=metricTop+Math.ceil(metrics.rows.length/2)*43+45;
 const metricRows=metrics.rows.map(([label,value],i)=>{const x=i%2?525:35,y=metricTop+Math.floor(i/2)*43;return `<text x="${x}" y="${y}" class="small">${esc(label)}</text><text x="${x}" y="${y+18}" class="value">${esc(typeof value==='number'?measure(value):value)}</text>`;}).join('');
 const rs=metrics.roofSection,profileScale=Math.min(340/rs.run,125/rs.rise),rx=110+rs.run*profileScale,ry=1000-rs.rise*profileScale;
 const roofSketch=`<g aria-label="Dimensioned roof section"><text x="35" y="806" class="subtitle">${mudroom?'PORCH GABLE':'MAIN ROOF FACE'} — DIMENSIONED HALF SECTION</text><text x="35" y="828" class="small">Eave to ${esc(rs.endLabel.toLowerCase())}; true profile proportions. Actual timber lengths and sections are listed below.</text>${line([110,1000],[rx,ry],'edge')}${line([110,1000],[rx,1000],'dim')}${line([rx,1000],[rx,ry],'dim')}${line([110,1012],[110,1048],'dim')}${line([rx,1012],[rx,1048],'dim')}${line([110,1038],[rx,1038],'dim')}${line([105,1033],[115,1043],'dim')}${line([rx-5,1033],[rx+5,1043],'dim')}${line([rx+15,ry],[rx+45,ry],'dim')}${line([rx+15,1000],[rx+45,1000],'dim')}${line([rx+35,ry],[rx+35,1000],'dim')}${line([rx+30,ry-5],[rx+40,ry+5],'dim')}${line([rx+30,995],[rx+40,1005],'dim')}<text x="${(110+rx)/2}" y="1062" text-anchor="middle" class="value">Run ${esc(measure(rs.run))}</text><text x="515" y="933" class="small">Vertical rise</text><text x="515" y="952" class="value">${esc(measure(rs.rise))}</text><text x="110" y="971" class="value">${esc(rs.angle)}</text><text x="${rx}" y="${ry-14}" text-anchor="middle" class="small">${esc(rs.endLabel)}</text><text x="560" y="865" class="small">Roof surface slope length</text><text x="560" y="885" class="value">${esc(measure(rs.slopeLength))}</text><text x="560" y="1003" class="small">Full roof span across opposite eaves</text><text x="560" y="1023" class="value">${esc(measure(rs.span))}</text></g>`;

// TIMESTAMP END 2026-11-03T07:17:50-05:00 | REVISION R004916
// TIMESTAMP END 2026-11-02T20:56:29-05:00 | REVISION R004874
// TIMESTAMP START 2026-11-02T14:22:13-05:00 | REVISION R004792
// TIMESTAMP START 2026-11-03T07:17:50-05:00 | REVISION R004916
// TIMESTAMP START 2026-11-03T08:08:16-05:00 | REVISION R004938
 return {parts,bounds:b,measurements:metrics,svg:`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 ${sheetHeight}" role="img" aria-label="${title}" style="background:white"><style>text{font:13px system-ui,sans-serif;fill:#172b31}.edge{stroke:#172b31;stroke-width:.85;fill:none}.hidden{stroke:#8b9397;stroke-width:.6;stroke-dasharray:3 3;fill:none}.aid{stroke:#8d5c21;stroke-width:1;stroke-dasharray:5 3;fill:none}.dim{stroke:#52636b;stroke-width:.65;fill:none}.title{font-size:20px;font-weight:700}.small{font-size:11px}.value{font-size:14px;font-weight:600}.subtitle{font-size:15px;font-weight:700}</style><text x="35" y="32" class="title">${title}</text><text x="35" y="55">${esc(model.revision||'Current model')} · ${parts.length} components · assembled geometry · ${aids?'illustrative construction aids included (dashed brown)':'timber + plywood; no construction aids'}</text><text x="35" y="91" class="small">Walls/openings ${walls?'ON':'OFF'} · bookshelves ${shelves?'ON':'OFF'} · cupola windows ${cupolaWindows?'ON':'OFF'} · floor ${floor?'ON':'OFF'} · porch ${mudroom?'ON':'OFF'} · added loads excluded from self-weight.</text><text x="35" y="75" class="small">Mesh-derived dimensions; source assumptions remain provisional. NOT CONSTRUCTION APPROVED.</text>${behind.join('')}${solid.join('')}${compass}${hdim(y1+42,(mudroom?'Porch projected width: ':'Main roof/frame projected width: ')+measure(hi[0]-lo[0]))}${vdim(x0-45,(view==='top'?(mudroom?'Porch depth':'Main north–south envelope'):'Shown vertical extent')+': '+measure(hi[1]-lo[1]))}<text x="850" y="665">${mudroom?'Site south →':'Site east →'}</text><text x="850" y="684">${view==='top'?(mudroom?'Site west ↑':'Site north ↑'):'+Y ↑ (vertical)'}</text>${line([scaleX,scaleY],[scaleX+scaleM*s,scaleY],'edge')}${line([scaleX,scaleY-5],[scaleX,scaleY+5],'edge')}${line([scaleX+scaleM*s,scaleY-5],[scaleX+scaleM*s,scaleY+5],'edge')}<text x="${scaleX+scaleM*s/2}" y="${scaleY-9}" text-anchor="middle">2 m graphical scale</text><text x="35" y="714" class="small">Screen/print size varies: use written dimensions and scale bar, never a presumed paper scale.</text><text x="35" y="733" class="small">${hidden?'Dashed gray: sampled hidden feature edges.':'Hidden feature edges suppressed.'} Hidden-line clipping is sampled; no mesh diagonals. Steel holes/sections are illustrative, not fabrication data.</text><text x="35" y="752" class="small">Sheet ${view==='top'?'GEOM-TOP':'GEOM-SIDE'} · written dimensions: inches / metres · selected model revision ${esc(model.revision||'unspecified')}</text><text x="35" y="771" class="small">Model SHA-256: ${esc(modelHash||model.source_model_sha256||'not supplied')}</text>${roofSketch}<text x="35" y="1090" class="subtitle">FRAME AND MEMBER DIMENSIONS</text>${metricRows}<text x="35" y="${sheetHeight-15}" class="small">Floor and height datum: main finished floor = 0.000 m. Main-building dimensions exclude the porch.</text></svg>`};
// TIMESTAMP END 2026-11-03T08:08:16-05:00 | REVISION R004938
// TIMESTAMP END 2026-11-03T07:17:50-05:00 | REVISION R004916
// TIMESTAMP END 2026-11-02T14:22:13-05:00 | REVISION R004792
}
// TIMESTAMP START 2026-11-02T14:22:13-05:00 | REVISION R004792
function cache(model,options){let c=results.get(model);if(!c){c=new Map();results.set(model,c);}const key=JSON.stringify([options.modelHash||model.source_model_sha256||model.revision||'identity',options.view||'top',!!options.aids,!!options.hidden,!!options.walls,!!options.shelves,!!options.cupolaWindows,!!options.floor,!!options.roofCover,!!options.mudroom]);return {c,key};}
// TIMESTAMP END 2026-11-02T14:22:13-05:00 | REVISION R004792
function drawing(model,options={}){const {c,key}=cache(model,options);if(c.has(key))return c.get(key);const it=drawSteps(model,options);let v;do{v=it.next();}while(!v.done);c.set(key,v.value);return v.value;}
async function drawingAsync(model,options={},schedule=()=>new Promise(resolve=>setTimeout(resolve,0))){const {c,key}=cache(model,options);if(c.has(key))return c.get(key);const it=drawSteps(model,options);let v,started=Date.now();while(!(v=it.next()).done){if(Date.now()-started>=8){await schedule();if(options.isCancelled?.())return null;started=Date.now();}}if(options.isCancelled?.())return null;c.set(key,v.value);return v.value;}
root.OctagonPlans={drawing,drawingAsync,bounds,included,project,measure,measurements,axialLength};
})(typeof globalThis!=='undefined'?globalThis:this);

// TIMESTAMP END 2026-11-02T20:56:29-05:00 | REVISION R004874
