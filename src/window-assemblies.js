// TIMESTAMP START 2026-11-05T17:09:28+00:00 | REVISION R000057
/* Published dimensions with an explicit top-hung appearance preview. */
(function(root){
'use strict';
function pose(part,fraction){
 if(!Number.isFinite(fraction)||fraction<0||fraction>1)throw Error('Window opening must be from 0 to 1');
 const local=part.windowLocalVertices;if(!local)return part.vertices;
 const pivot=part.windowPivotLocalM,angle=(part.windowMotion==='sash'?fraction:0)*part.maximumIllustrativeAngleDegrees*Math.PI/180,c=Math.cos(angle),s=Math.sin(angle),frame=part.windowFrame3x4;
 return local.map(point=>{const dy=point[1]-pivot[1],dn=point[2]-pivot[2],p=[point[0],pivot[1]+c*dy+s*dn,pivot[2]-s*dy+c*dn];return frame.map(row=>row[0]*p[0]+row[1]*p[1]+row[2]*p[2]+row[3]);});
}
function bind(document,units,onChange){
 const $=id=>document.getElementById(id),selector=$('windowUnit'),slider=$('windowOpening'),output=$('windowOpeningValue'),states=new Map(units.map(u=>[u.unitId,0]));
 selector.replaceChildren();
 for(const [value,label] of [['all','All windows'],...units.map(u=>[u.unitId,u.unitId.replace(/^WIN-/, '')+' · '+u.wholePurchasedUnitModel])]){const option=document.createElement('option');option.value=value;option.textContent=label;selector.appendChild(option);}
 const sync=()=>{const value=selector.value==='all'?0:states.get(selector.value)||0;slider.value=String(value);output.textContent=Math.round(value*100)+'%';};
 selector.value='all';selector.onchange=sync;
 slider.oninput=()=>{const value=Number(slider.value);if(!Number.isFinite(value)||value<0||value>1)return;const ids=selector.value==='all'?Array.from(states.keys()):[selector.value];for(const id of ids)states.set(id,value);output.textContent=Math.round(value*100)+'%';onChange(ids,value);};
 sync();return {select(id){if(states.has(id)){selector.value=id;sync();}},close(){for(const id of states.keys())states.set(id,0);sync();onChange(Array.from(states.keys()),0);},states};
}
function renderSpecification(host,part,document,references){
 const spec=part.windowSpec;if(!spec)return;
 const metric=(label,value)=>{if(value==null)return;const row=document.createElement('div');row.className='metric';const left=document.createElement('span'),right=document.createElement('strong');left.textContent=label;right.textContent=value;row.append(left,right);host.appendChild(row);},size=value=>value?.map(v=>Number(v).toFixed(5).replace(/0+$/,'').replace(/\.$/,'')).join(' × ')+' in';
 metric('Manufacturer',spec.manufacturer);metric('Unit / screen',spec.partNumber);metric('Published frame',size(spec.frameDimensionsIn));metric('Approximate frame depth',spec.frameApproxDepthIn+' in');metric('Published sash',size(spec.sashDimensionsIn));metric('Visible glass',size(spec.publishedVisibleGlassIn));metric('OEM screen',size(spec.screenDimensionsIn));
 const note=document.createElement('p');note.className='description';note.textContent=spec.profileStatus;host.appendChild(note);
 const link=document.createElement('a');link.href=spec.sourceURL;link.target='_blank';link.rel='noopener';link.textContent='Manufacturer dimensions and ordering reference';host.appendChild(link);
 const components=references?.components?.filter(p=>p.unitId===part.unitId)||[];if(components.length){const box=document.createElement('details'),title=document.createElement('summary');title.textContent='Included factory parts and service references';box.appendChild(title);for(const item of components){const entry=document.createElement('details'),heading=document.createElement('summary');heading.textContent=item.id.replace(part.unitId+'-','')+(item.partNumber?' · '+item.partNumber:'');entry.appendChild(heading);const text=document.createElement('p');text.textContent=[item.publishedTrackLengthIn!=null?'Published track: '+item.publishedTrackLengthIn+' in':null,item.geometryStatus||item.outlinePlacement||item.placementStatus,item.orderDescription,item.quantityLimit,'Included components are references for the purchased unit; they are not counted as additional purchases.'].filter(Boolean).join(' ');entry.appendChild(text);box.appendChild(entry);}host.appendChild(box);}
}
const api={pose,bind,renderSpecification};root.OctagonWindowAssemblies=api;if(typeof module!=='undefined'&&module.exports)module.exports=api;
})(typeof globalThis!=='undefined'?globalThis:this);
// TIMESTAMP END 2026-11-05T17:09:28+00:00 | REVISION R000057
