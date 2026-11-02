/* Separate model-derived face-detail screen. No geometry edits or saw-setting inference. */
(function(root){
'use strict';
const fmt=(n,d=3)=>Number.isFinite(n)?n.toFixed(d):'—';
function createController({document,analysis,getModel,getOptions,save,release,onOpen,onClose}){
 const $=id=>document.getElementById(id);let report=null,piece=null,returnFocus=null,request=0;
 const el=(tag,text)=>{const e=document.createElement(tag);if(text!==undefined)e.textContent=String(text);return e;};
 const addCell=(row,value)=>row.appendChild(el('td',value));
 function sketch(part,face){
  const host=$('cutFaceSketch');host.replaceChildren();if(!part||!face)return;
  // Projection only: uses the same selected assembled mesh; all angles come from analysis.
  const project=v=>[.70710678*(v[0]-v[2]),.33129458*(v[0]+v[2])-.8834522*v[1]],q=part.vertices.map(project);
  const xs=q.map(v=>v[0]),ys=q.map(v=>v[1]),lo=[Math.min(...xs),Math.min(...ys)],hi=[Math.max(...xs),Math.max(...ys)],scale=Math.min(550/Math.max(hi[0]-lo[0],1e-9),230/Math.max(hi[1]-lo[1],1e-9));
  const point=v=>[300+(v[0]-(hi[0]+lo[0])/2)*scale,135+(v[1]-(hi[1]+lo[1])/2)*scale].map(x=>x.toFixed(2)).join(',');
  const ns='http://www.w3.org/2000/svg',svg=document.createElementNS(ns,'svg');svg.setAttribute('viewBox','0 0 600 270');svg.setAttribute('role','img');svg.setAttribute('aria-label',part.id+' selected mesh face '+face.id);
  const selected=new Set(face.triangleIndices);for(const highlight of [false,true])for(let i=0;i<part.triangles.length;i++){if(selected.has(i)!==highlight)continue;const polygon=document.createElementNS(ns,'polygon');polygon.setAttribute('points',part.triangles[i].map(j=>point(q[j])).join(' '));polygon.setAttribute('fill',highlight?'#b45122':'#dde5e2');polygon.setAttribute('fill-opacity',highlight?'0.9':'0.15');polygon.setAttribute('stroke',highlight?'#7b2d12':'#536a70');polygon.setAttribute('stroke-width',highlight?'1.5':'.5');svg.appendChild(polygon);}
  host.appendChild(svg);host.appendChild(el('p',face.id+' · highlighted planar face; transparent model context, not a section cut.'));
 }
 function renderPiece(partId){
  const model=getModel();piece=model.parts.find(p=>p.id===partId);if(!piece)throw Error('Selected member is no longer in this model');report=analysis.analysePart(piece,getOptions());
  $('cutAnglesTitle').textContent=partId+' · Cut angles';$('cutAnglesSummary').textContent=getOptions().revision+' · '+report.faces.length+' planar faces · geometry '+report.geometryFingerprint;
  const host=$('cutAnglesContent');host.replaceChildren();const table=el('table'),thead=el('thead'),header=el('tr');for(const label of ['Face / location','Type','Off square °','Normal miter °','Normal bevel °','Area in²','Local center A / W / D (in)'])header.appendChild(el('th',label));thead.appendChild(header);table.appendChild(thead);const body=el('tbody');
  for(const face of report.faces){const row=el('tr'),cell=el('td'),button=el('button',face.id);button.className='cut-face-select';button.onclick=()=>{sketch(piece,face);for(const b of body.querySelectorAll('button'))b.setAttribute('aria-pressed',b===button?'true':'false');};button.setAttribute('aria-pressed','false');cell.appendChild(button);row.appendChild(cell);addCell(row,face.classification);for(const v of [face.angles.offSquareDeg,face.angles.miterDeg,face.angles.bevelDeg])addCell(row,fmt(v));addCell(row,fmt(face.areaM2/(.0254*.0254)));addCell(row,face.localCentroidM?face.localCentroidM.map(v=>fmt(v/.0254)).join(' / '):'No stock reference');body.appendChild(row);}table.appendChild(body);host.appendChild(table);
  const details=el('details'),summary=el('summary','Adjacent-face angles & reference details');details.appendChild(summary);const defs=el('p',Object.values(report.definitions).join(' '));details.appendChild(defs);details.appendChild(el('p',(report.referenceFaces?.labels||[]).join(' · ')));for(const warning of report.warnings||[])details.appendChild(el('p',warning));
  const edges=el('table'),head=el('tr');for(const v of ['Edge','Faces','Plane angle °','Material interior °','Length in'])head.appendChild(el('th',v));edges.appendChild(head);for(const edge of report.edges||[]){const row=el('tr');for(const value of [edge.id,(edge.faceIds||[]).join(' / '),fmt(edge.planeAngleDeg),fmt(edge.interiorAngleDeg),fmt(edge.length_m/.0254)])addCell(row,value);edges.appendChild(row);}details.appendChild(edges);host.appendChild(details);sketch(piece,report.faces[0]);
 }
 function showAllReport(result){
  piece=null;report=result;$('cutAnglesTitle').textContent='Complete model cut-face list';$('cutAnglesSummary').textContent=getOptions().revision+' · '+report.parts.length+' components · '+report.parts.reduce((n,p)=>n+p.faces.length,0)+' planar faces';$('cutFaceSketch').replaceChildren();
  const host=$('cutAnglesContent');host.replaceChildren();const table=el('table'),head=el('tr');for(const label of ['Piece','Planar faces','Stock reference','View'])head.appendChild(el('th',label));table.appendChild(head);for(const p of report.parts){const row=el('tr');addCell(row,p.partId);addCell(row,p.faces.length);addCell(row,p.frame?'Recorded local axes':'Unavailable');const td=el('td'),button=el('button','Cut angles · '+p.partId);button.onclick=()=>{load(p.partId);$('cutAnglesScroll').scrollTop=0;};td.appendChild(button);row.appendChild(td);table.appendChild(row);}host.appendChild(table);
 }
 function renderAll(){showAllReport(analysis.analyseModel(getModel(),getOptions()));}
 async function load(partId){const token=++request;report=null;$('cutAnglesCSV').disabled=true;$('cutAnglesJSON').disabled=true;$('cutAnglesSummary').textContent='Calculating current model faces…';$('cutAnglesContent').replaceChildren();$('cutFaceSketch').replaceChildren();await new Promise(resolve=>setTimeout(resolve,0));if(token!==request)return;try{if(partId)renderPiece(partId);else{const currentModel=getModel();let completed=0;const result=await analysis.analyseModelAsync(currentModel,{...getOptions(),isCancelled:()=>token!==request},async()=>{completed++;if(token===request)$('cutAnglesSummary').textContent='Calculating current model faces… '+completed+' / '+currentModel.parts.length+' components';await new Promise(resolve=>setTimeout(resolve,0));});if(!result||token!==request)return;showAllReport(result);}$('cutAnglesCSV').disabled=false;$('cutAnglesJSON').disabled=false;}catch(error){if(token===request){$('cutAnglesSummary').textContent='Unable to calculate current geometry: '+error.message;report=null;}}}
 function open(partId){returnFocus=document.activeElement;release();$('cutAnglesModal').classList.add('open');$('cutAnglesModal').setAttribute('aria-hidden','false');onOpen();$('closeCutAngles').focus();load(partId);}
 function close(){request++;if(!$('cutAnglesModal').classList.contains('open'))return;$('cutAnglesModal').classList.remove('open');$('cutAnglesModal').setAttribute('aria-hidden','true');onClose();release();(returnFocus?.isConnected?returnFocus:$('allCutAngles')).focus();}
 $('allCutAngles').onclick=()=>open();$('cutAnglesAll').onclick=()=>load();$('closeCutAngles').onclick=close;
 $('cutAnglesCSV').onclick=()=>{if(report)save('modeled-cut-faces'+(piece?'-'+piece.id:'-all')+'.csv',analysis.toCSV(report),'text/csv');};
 $('cutAnglesJSON').onclick=()=>{if(report)save('modeled-cut-faces'+(piece?'-'+piece.id:'-all')+'.json',JSON.stringify(report,null,2),'application/json');};
 $('cutAnglesModal').onclick=e=>{if(e.target===$('cutAnglesModal'))close();};
 document.addEventListener('keydown',e=>{if(!$('cutAnglesModal').classList.contains('open'))return;if(e.key==='Escape'){e.preventDefault();close();}else if(e.key==='Tab'){const items=[...$('cutAnglesModal').querySelectorAll('button:not([disabled]),summary')],first=items[0],last=items[items.length-1];if(e.shiftKey&&document.activeElement===first){e.preventDefault();last.focus();}else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first.focus();}}});
 return {openPiece:open,openAll:()=>open(),close,renderPiece,renderAll,load,getReport:()=>report};
}
root.OctagonCutAngleView={createController};if(typeof module!=='undefined'&&module.exports)module.exports=root.OctagonCutAngleView;
})(typeof globalThis!=='undefined'?globalThis:this);
