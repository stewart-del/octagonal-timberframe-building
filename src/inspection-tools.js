// Measured model angles and inventory. Does not modify the saved model.
const MATERIALS=__MATERIALS_JSON__;
const materialByPart=new Map();
for(const group of MATERIALS.groups||[])for(const id of group.member_ids)materialByPart.set(id,group);
const deg=value=>value*180/Math.PI;
const cleanAngle=value=>Math.abs(value)<.00001?0:value;
const angleText=value=>value==null||!Number.isFinite(value)?'Unresolved':num(cleanAngle(value),2)+'°';
function stockFrame(p){
 if(p.stock_frame&&['axis','width','depth'].every(k=>Array.isArray(p.stock_frame[k])&&p.stock_frame[k].length===3&&p.stock_frame[k].every(Number.isFinite)))return Object.fromEntries(['axis','width','depth'].map(k=>[k,unit(p.stock_frame[k])]));
 const axis=unit(vsub(p.axis_end,p.axis_start));
 const cap=(p.reference_end_faces||[]).find(f=>f.id===p.id+'-A');
 if(length(axis)<.99||!cap?.vertices||cap.vertices.length<2)return null;
 const edge=vsub(cap.vertices[1],cap.vertices[0]);
 const width=vsub(edge,vmul(axis,dot(edge,axis)));
 if(length(width)<1e-8)return null;
 return {axis,width:unit(width),depth:unit(cross(axis,unit(width)))};
}
function surfaceAngles(p,f){
 const axis=unit(vsub(p.axis_end,p.axis_start)),normal=unit(f.normal);
 const offSquare=deg(Math.acos(Math.max(0,Math.min(1,Math.abs(dot(axis,normal))))));
 const frame=stockFrame(p);
 if(!frame)return {offSquare,planeToAxis:90-offSquare,yaw:null,tilt:null};
 let components=[dot(normal,frame.axis),dot(normal,frame.width),dot(normal,frame.depth)].map(v=>Math.abs(v)<1e-8?0:v);
 if(components.find(v=>v!==0)<0)components=components.map(v=>-v);
 const [a,w,d]=components,plan=Math.hypot(a,w);
 return {offSquare,planeToAxis:90-offSquare,yaw:plan>1e-8?deg(Math.atan2(w,a)):null,tilt:deg(Math.atan2(d,plan))};
}
function recordedAngles(p){
 const a=angle(p),vertical=Math.abs(a.axis_inclination_deg-90)<.001;
 return [
  ['Member inclination to horizontal',angleText(a.axis_inclination_deg)],
  ['Plan direction in model X/Z',a.azimuth_deg==null?(vertical?'Not applicable · vertical':'Unresolved'):angleText(a.azimuth_deg)],
  ['End A reference · off square',angleText(a.display_end_A_off_square_deg)],
  ['End B reference · off square',angleText(a.display_end_B_off_square_deg)],
  ['End A reference · plane to axis',a.display_end_A_off_square_deg==null?'Unresolved':angleText(90-a.display_end_A_off_square_deg)],
  ['End B reference · plane to axis',a.display_end_B_off_square_deg==null?'Unresolved':angleText(90-a.display_end_B_off_square_deg)],
  ['Reference vertical bevel',a.modeled_vertical_bevel_deg==null?'Not assigned':angleText(a.modeled_vertical_bevel_deg)],
  ['Equal-ring plan miter assumption',a.conditional_plan_miter_off_square_deg==null?'Not assigned':angleText(a.conditional_plan_miter_off_square_deg)],
  ['Fabrication end A cut',angleText(a.fabrication_end_A_cut_deg)],
  ['Fabrication end B cut',angleText(a.fabrication_end_B_cut_deg)],
  ['Fabrication bevel',angleText(a.fabrication_bevel_deg)]
 ];
}
function materialMemberLabel(p){
 const g=materialByPart.get(p.id);
 return g?g.id+' · '+(g.member_ids.indexOf(p.id)+1)+' of '+g.quantity:'';
}
function appendAnglePanel(host,p){
 const panel=document.createElement('section');panel.className='angle-panel';panel.id='selectedAngles';
 const refs=document.createElement('details'),refSummary=document.createElement('summary');refs.dataset.inspectorKey='referenceAngles';refSummary.textContent='Reference angles · member axis & A/B ends';refs.appendChild(refSummary);
 for(const [label,value] of recordedAngles(p))addMetric(refs,label,value);
 const note=document.createElement('p');note.className='description';note.textContent='End A/B values describe this revision’s reference planes. Contact surfaces are measured separately. Housing, tenon and fastening details are not assigned by these geometric measurements.';refs.appendChild(note);panel.appendChild(refs);
 const surfaces=document.createElement('details'),heading=document.createElement('summary');surfaces.dataset.inspectorKey='surfaceAngles';heading.textContent='Contact-plane angles · recorded surfaces';surfaces.appendChild(heading);
 const legend=document.createElement('p');legend.className='description';legend.textContent='Off sq = plane angle from a square end. Yaw = normal rotation toward stock width. Tilt = normal rotation toward stock depth. A → B follows the timber axis. These geometric angles are not saw settings.';surfaces.appendChild(legend);
 const wrap=document.createElement('div');wrap.className='angle-table';wrap.setAttribute('tabindex','0');wrap.setAttribute('aria-label','Scrollable angle table for '+p.id);
 const table=document.createElement('table'),head=document.createElement('thead'),hr=document.createElement('tr');
 for(const text of ['Surface / reference','Off sq','Yaw','Tilt']){const th=document.createElement('th');th.textContent=text;th.setAttribute('scope','col');hr.appendChild(th);}head.appendChild(hr);table.appendChild(head);
 const body=document.createElement('tbody');
 const faces=cuts.filter(f=>f.part_id===p.id).sort((a,b)=>Number(b.reference)-Number(a.reference)||a.id.localeCompare(b.id,undefined,{numeric:true}));
 for(const f of faces){const values=surfaceAngles(p,f),row=document.createElement('tr');row.dataset.cutId=f.id;
  const td=document.createElement('td'),button=document.createElement('button');button.className='angle-cut';button.dataset.cutId=f.id;button.setAttribute('aria-pressed','false');button.textContent=f.id;button.setAttribute('aria-label','Inspect '+f.id+'; '+angleText(values.offSquare)+' off square');button.onclick=()=>selectCut(f);td.appendChild(button);row.appendChild(td);
  for(const key of ['offSquare','yaw','tilt']){const cell=document.createElement('td');cell.textContent=values[key]==null?'Undefined':angleText(values[key]);row.appendChild(cell);}body.appendChild(row);
 }table.appendChild(body);wrap.appendChild(table);surfaces.appendChild(wrap);
 const exportButton=document.createElement('button');exportButton.textContent='Download '+p.id+' angles';exportButton.onclick=()=>download(p.id+'-model-angles.csv',anglesCSV(p),'text/csv');surfaces.appendChild(exportButton);
 const axes=document.createElement('details'),summary=document.createElement('summary');summary.textContent='Angle reference axes and sign convention';axes.appendChild(summary);
 const frame=stockFrame(p);const explanation=document.createElement('p');explanation.textContent='The local stock frame uses the generator’s explicit axis, width and depth directions. Axis runs A → B. For legacy records without an explicit frame, width is recovered from the first End A cap edge and depth is axis × width. The first nonzero normal component (axis, width, depth) is made positive; opposite normals describe the same plane. Yaw is undefined for a normal entirely along depth. Plane-to-axis angle = 90° minus off-square angle.';axes.appendChild(explanation);
 if(frame)for(const [name,vector] of Object.entries(frame))addMetric(axes,name+' (model X/Y/Z)',vector.map(v=>num(v,4)).join(', '));surfaces.appendChild(axes);panel.appendChild(surfaces);host.appendChild(panel);
}
function anglesCSV(p){
 const rows=[['Piece_ID','Record','Category','Off_square_deg','Plane_to_axis_deg','Normal_yaw_deg','Normal_tilt_deg','Value','Status']];
 if(p.fabrication_dimensions_valid===false){rows.push([p.id,'Display assembly','NOT FABRICATION','','','','','','No cut drilling weld screw or erection dimensions validated']);return rows.map(row=>row.map(csvCell).join(',')).join('\r\n');}
 for(const [label,value] of recordedAngles(p))rows.push([p.id,label,'Recorded model reference','','','','',value,'R01 geometry / fabrication unresolved']);
 for(const f of cuts.filter(f=>f.part_id===p.id)){const a=surfaceAngles(p,f);rows.push([p.id,f.id,f.reference?'R01 end reference':'Contact surface',a.offSquare,a.planeToAxis,a.yaw??'Undefined',a.tilt??'Undefined','','Measured model geometry; not saw settings']);}
 return rows.map(row=>row.map(csvCell).join(',')).join('\r\n');
}
function setScheduleHead(labels){const row=$('scheduleHead');row.replaceChildren();for(const label of labels){const th=document.createElement('th');th.textContent=label;th.setAttribute('scope','col');row.appendChild(th);}}
function showScheduleDialog(){
 if(typeof releaseMouseLook==='function')releaseMouseLook();
 $('scheduleModal').classList.add('open');document.querySelector('header').inert=true;document.querySelector('main').inert=true;clearMovement();$('closeSchedule').focus();updateNavigationStatus();
}
// TIMESTAMP START 2026-11-04T19:33:21+00:00 | REVISION R000014
function materialsCSV(){
 const rows=[['Type','Quantity','Family','Nominal_width_in','Nominal_depth_in','Nominal_axis_length_ft','Total_nominal_axis_ft','Nominal_board_feet','Existing_piece_IDs_in_number_order','Grouping_basis','Status','Minimum_blank_length_including_tenons_in','Blank_length_rounded_quarter_in','Blank_board_feet']];
 for(const g of MATERIALS.groups){const p=partById.get(g.representative_id),stock=OctagonJoineryDimensions.blank(p);rows.push([g.id,g.quantity,g.label||groupMap.get(p.group)?.label||p.group,(p.fabrication_dimensions_valid===false&&!isTimber(p))?'':widthIn(p),(p.fabrication_dimensions_valid===false&&!isTimber(p))?'':depthIn(p),(p.fabrication_dimensions_valid===false&&!isTimber(p))?'':lengthFt(p),(p.fabrication_dimensions_valid===false&&!isTimber(p))?'':g.quantity*lengthFt(p),isTimber(p)?g.quantity*widthIn(p)*depthIn(p)*lengthFt(p)/12:'',g.member_ids.join(' | '),g.method||MATERIALS.method||'R01 repeated geometry',(p.fabrication_dimensions_valid===false&&!isTimber(p))?'DISPLAY ONLY: reference span 90 in; 4 in strap depth; 14 in total outer-leg height. Thickness holes positions welds screws and elevation NOT fabrication specifications':isTimber(p)?'Geometric stock includes modeled tenons; add cutting and dressing allowances':'Non-timber visualization; stock dimensions unresolved',stock?.minimumLengthIn??'',stock?.quarterInchLengthIn??'',stock?g.quantity*stock.widthIn*stock.depthIn*stock.quarterInchLengthIn/144:'']);}
 return rows.map(row=>row.map(csvCell).join(',')).join('\r\n');
}
function openMaterials(){
 scheduleReturnFocus=document.activeElement;$('scheduleTitle').textContent='Materials · R01 component groups';
 setScheduleHead(['Type','Quantity','Member family','Nominal section','Nominal axis length each','Numbered pieces · original IDs','Matching basis','Blank length · tenons included']);
 const note=$('scheduleNote');note.replaceChildren();const text=document.createElement('span');text.textContent=MATERIALS.groups.length+' component groups · '+parts.filter(isTimber).length+' timber members. Metal and roof-envelope components are separate groups. Original timber IDs and A/B directions are retained. Blank lengths include the actual tenon tips and are rounded up to ¼ in. Add cutting and dressing allowances.';note.appendChild(text);
 const exportButton=document.createElement('button');exportButton.textContent='Download materials CSV';exportButton.onclick=()=>download('octagon-grouped-materials.csv',materialsCSV(),'text/csv');note.appendChild(exportButton);
 const body=$('scheduleRows');body.replaceChildren();
 for(const g of MATERIALS.groups){const p=partById.get(g.representative_id),row=document.createElement('tr');row.dataset.materialId=g.id;
  for(const value of [g.id,String(g.quantity),g.label||groupMap.get(p.group)?.label||clean(p.group),(p.fabrication_dimensions_valid===false&&!isTimber(p))?'Not a stock section':num(widthIn(p),2)+' × '+num(depthIn(p),2)+' in',(p.fabrication_dimensions_valid===false&&!isTimber(p))?'90 in owner reference overall span':feet(lengthFt(p))]){const td=document.createElement('td');td.textContent=value;row.appendChild(td);}
  const members=document.createElement('td');members.className='material-members';g.member_ids.forEach((id,i)=>{const button=document.createElement('button');button.textContent=String(i+1).padStart(2,'0')+' · '+id;button.setAttribute('aria-label',g.id+' piece '+(i+1)+': inspect '+id);button.onclick=()=>{closeSchedule(false);selectPart(id);focusPart(partById.get(id));canvas.focus();};members.appendChild(button);});row.appendChild(members);
  const basis=document.createElement('td');basis.textContent=g.status||g.method||'Repeated R01 geometry; fabrication unresolved';row.appendChild(basis);const stock=OctagonJoineryDimensions.blank(p),blankCell=document.createElement('td');blankCell.textContent=stock?num(stock.quarterInchLengthIn,2)+' in':'Not a stock member';row.appendChild(blankCell);body.appendChild(row);
 }showScheduleDialog();
}
// TIMESTAMP END 2026-11-04T19:33:21+00:00 | REVISION R000014
$('materialsButton').onclick=openMaterials;

