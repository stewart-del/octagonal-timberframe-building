// TIMESTAMP START 2026-11-03T13:30:29-05:00 | REVISION R005026
(function(root){
'use strict';
function requested(search){const query=new URLSearchParams(search);return OctagonParametric.parameters({wallHeightIn:query.has('wallHeight')?query.get('wallHeight'):undefined,pitch:query.has('pitch')?query.get('pitch'):undefined});}
function selectionURL(href,parameters){const url=new URL(href);for(const key of ['wallHeight','pitch'])url.searchParams.delete(key);if(parameters?.changed){url.searchParams.set('wallHeight',String(parameters.wallHeightIn));url.searchParams.set('pitch',String(parameters.pitch));}url.hash='';return url.href;}
function bind(context,document,location){
 const $=id=>document.getElementById(id),cfg=context.parameters||OctagonParametric.parameters();
 $('wallHeight').value=cfg.wallHeightIn.toFixed(3);$('roofPitch').value=String(cfg.pitch);$('wallHeight').min=String(OctagonParametric.BASE_WALL);
 const summary=()=>{$('parameterDimensions').textContent='Main radial rise over the 135 in post-center run: '+(135*Number($('roofPitch').value)/12).toFixed(2)+' in. Cupola and porch: 4:12.';};summary();
 $('roofPitch').oninput=summary;
 $('applyDimensions').onclick=()=>{try{const next=OctagonParametric.parameters({wallHeightIn:Number($('wallHeight').value),pitch:Number($('roofPitch').value)});$('parameterStatus').textContent='Rebuilding members and matching recesses…';location.assign(selectionURL(location.href,next));}catch(error){$('parameterStatus').textContent=error.message;}};
 $('resetDimensions').onclick=()=>location.assign(selectionURL(location.href,null));
 $('parameterStatus').textContent=context.parametric?'Current dimensions applied to the model, recesses, plans and measurements.':'Saved design dimensions.';
// TIMESTAMP START 2026-11-03T16:17:49-05:00 | REVISION R005051
 if(context.parametric){for(const id of ['modelVariantAssembled','modelVariantExploded','joineryReview','openStepLap'])if($(id))$(id).hidden=true;}
// TIMESTAMP END 2026-11-03T16:17:49-05:00 | REVISION R005051
}
async function generate(rawContext,savedContext,config,apis){
 const [{default:Module},source]=await Promise.all([import('./vendor/manifold.js'),fetch('./parametric-source.json').then(r=>{if(!r.ok)throw Error('Could not load parametric source');return r.json();})]);
 const M=await Module({locateFile:()=>new URL('./vendor/manifold.wasm',window.location.href).href});M.setup();
 const result=OctagonParametric.layouts(savedContext,OctagonParametric.core(rawContext,config,source,M),M,apis);
 const bytes=new TextEncoder().encode(JSON.stringify({model:result.model,components:result.components})),hash=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)),v=>v.toString(16).padStart(2,'0')).join('');
 const model=result.model;model.generatedLayouts={schematic:result.schematicLayout,mudroom:result.mudroomLayout};
 const label='Wall '+config.wallHeightIn.toFixed(2)+' in · main roof '+config.pitch+':12';
 return {...savedContext,model,sha256:hash,label,parameters:config,parametric:true,parametricLayouts:result,
  status:label+' · regenerated geometry',wallJoinery:result.wallJoinery,
  exportPrefix:'PARAMETRIC-'+config.wallHeightIn+'in-'+config.pitch+'pitch-',cavityAuditPassed:false,
  cavities:{available:true,parts:result.cavities,status:'Recesses regenerated from current stock and mating members; saved-dimension audit does not apply.'},
  loadReview:{...savedContext.loadReview,source_model_sha256:hash,issues:[],members:model.parts.filter(p=>p.is_timber).map(p=>({id:p.id,volume_m3:p.fit_geometry.volume_m3,centroid_m:p.parametricCentroid}))},pressureAvailable:false,contactMarkersAvailable:false};
}
const api={requested,selectionURL,bind,generate};root.OctagonParametricControls=api;if(typeof module!=='undefined'&&module.exports)module.exports=api;
})(typeof globalThis!=='undefined'?globalThis:this);
// TIMESTAMP END 2026-11-03T13:30:29-05:00 | REVISION R005026
