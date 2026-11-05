// TIMESTAMP START 2026-11-05T16:01:12+00:00 | REVISION R000052
// TIMESTAMP START 2026-11-03T13:30:29-05:00 | REVISION R005026
(function(root){
'use strict';
// TIMESTAMP START 2026-11-05T14:18:42+00:00 | REVISION R000046
function requested(search){const query=new URLSearchParams(search);return OctagonParametric.parameters({wallHeightIn:query.has('wallHeight')?query.get('wallHeight'):undefined,pitch:query.has('pitch')?query.get('pitch'):undefined,cupolaLiftIn:query.has('cupolaLift')?query.get('cupolaLift'):undefined});}
function selectionURL(href,parameters){const url=new URL(href);for(const key of ['wallHeight','pitch','cupolaLift','cupolaPitch'])url.searchParams.delete(key);if(parameters?.changed){for(const [key,value] of [['wallHeight',parameters.wallHeightIn],['pitch',parameters.pitch],['cupolaLift',parameters.cupolaLiftIn]])url.searchParams.set(key,String(value));}url.hash='';return url.href;}
function bind(context,document,location,{apply}={}){
 const $=id=>document.getElementById(id),cfg=context.parameters||OctagonParametric.parameters(),fields={wallHeight:'wallHeightIn',roofPitch:'pitch',cupolaLift:'cupolaLiftIn'};
 // TIMESTAMP START 2026-11-05T20:50:09+00:00 | REVISION R000064
 // Preserve the exact saved minimum when only another dimension is edited.
 for(const [id,key] of Object.entries(fields))$(id).value=String(cfg[key]);
 $('wallHeight').min=String(OctagonParametric.BASE_WALL);
 // TIMESTAMP END 2026-11-05T20:50:09+00:00 | REVISION R000064
 const summary=()=>{$('parameterDimensions').textContent='Main radial rise over the 135 in post-center run: '+(135*Number($('roofPitch').value)/12).toFixed(2)+' in. Main and cupola roofs: '+$('roofPitch').value+':12. Cupola height extension: '+$('cupolaLift').value+' in. Porch roof: 4:12.';};summary();
 for(const id of Object.keys(fields))$(id).oninput=summary;
 let pending=false;
 async function commit(input){
  if(pending)return;let next;try{next=OctagonParametric.parameters(input);}catch(error){$('parameterStatus').textContent=error.message;return;}
  pending=true;for(const id of ['applyDimensions','resetDimensions'])$(id).disabled=true;
  try{if(apply)await apply(next);else location.assign(selectionURL(location.href,next));}
  catch(error){$('parameterStatus').textContent=error.message+' Current dimensions remain available.';}
  finally{pending=false;for(const id of ['applyDimensions','resetDimensions'])$(id).disabled=false;}
 }
 $('applyDimensions').onclick=()=>commit(Object.fromEntries(Object.entries(fields).map(([id,key])=>[key,Number($(id).value)])));
 $('resetDimensions').onclick=()=>commit({});
 $('parameterStatus').textContent=context.parametric?'Current dimensions applied to the model, recesses, plans and measurements.':'Saved design dimensions.';
 if(context.parametric){for(const id of ['modelVariantAssembled','modelVariantExploded','joineryReview','openStepLap'])if($(id))$(id).hidden=true;}
}
let enginePromise,sourcePromise;
function geometryResources(){
 if(!enginePromise)enginePromise=import('./vendor/manifold.js').then(async({default:Module})=>{const M=await Module({locateFile:()=>new URL('./vendor/manifold.wasm',window.location.href).href});M.setup();return M;}).catch(error=>{enginePromise=null;throw error;});
 if(!sourcePromise)sourcePromise=fetch('./parametric-source.json').then(r=>{if(!r.ok)throw Error('Could not load parametric source');return r.json();}).catch(error=>{sourcePromise=null;throw error;});
 return Promise.all([enginePromise,sourcePromise]);
}
// TIMESTAMP END 2026-11-05T14:18:42+00:00 | REVISION R000046
async function generate(rawContext,savedContext,config,apis){
// TIMESTAMP START 2026-11-05T14:18:42+00:00 | REVISION R000046
 const [M,source]=await geometryResources();
// TIMESTAMP END 2026-11-05T14:18:42+00:00 | REVISION R000046
// TIMESTAMP START 2026-11-05T17:19:58+00:00 | REVISION R000058
 const main=OctagonParametric.core(rawContext,config,source,M),cupola=OctagonCupolaParametric.regenerate(main,config,M,OctagonParametric);
 const result=OctagonParametric.layouts(savedContext,cupola,M,apis);
// TIMESTAMP END 2026-11-05T17:19:58+00:00 | REVISION R000058
 const bytes=new TextEncoder().encode(JSON.stringify({model:result.model,components:result.components})),hash=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)),v=>v.toString(16).padStart(2,'0')).join('');
 const model=result.model;model.generatedLayouts={schematic:result.schematicLayout,mudroom:result.mudroomLayout};
// TIMESTAMP START 2026-11-05T14:18:42+00:00 | REVISION R000046
 const label='Wall '+config.wallHeightIn.toFixed(2)+' in · main roof '+config.pitch+':12 · cupola '+config.cupolaLiftIn+' in / '+config.cupolaPitch+':12';
// TIMESTAMP END 2026-11-05T14:18:42+00:00 | REVISION R000046
 return {...savedContext,model,sha256:hash,label,parameters:config,parametric:true,parametricLayouts:result,
  status:label+' · regenerated geometry',wallJoinery:result.wallJoinery,
  // TIMESTAMP START 2026-11-05T14:18:42+00:00 | REVISION R000046
  exportPrefix:'PARAMETRIC-'+config.wallHeightIn+'in-'+config.pitch+'pitch-cupola-'+config.cupolaLiftIn+'in-'+config.cupolaPitch+'pitch-',
// TIMESTAMP END 2026-11-05T14:18:42+00:00 | REVISION R000046
  cavityAuditPassed:false,
  cavities:{available:true,parts:result.cavities,status:'Recesses regenerated from current stock and mating members; saved-dimension audit does not apply.'},
  loadReview:{...savedContext.loadReview,source_model_sha256:hash,issues:[],members:model.parts.filter(p=>p.is_timber).map(p=>({id:p.id,volume_m3:p.fit_geometry.volume_m3,centroid_m:p.parametricCentroid}))},pressureAvailable:false,contactMarkersAvailable:false};
}
const api={requested,selectionURL,bind,generate};root.OctagonParametricControls=api;if(typeof module!=='undefined'&&module.exports)module.exports=api;
})(typeof globalThis!=='undefined'?globalThis:this);
// TIMESTAMP END 2026-11-03T13:30:29-05:00 | REVISION R005026

// TIMESTAMP END 2026-11-05T16:01:12+00:00 | REVISION R000052
