// TIMESTAMP START 2026-11-02T20:38:50-05:00 | REVISION R004870
(function(root){
'use strict';
function patch(p,fit){const q=fit[p.id];return q?{...p,...q,faces:q.triangles,fit_geometry:{...p.fit_geometry,volume_m3:q.volume_m3}}:p;}
function applyModel(model,fit){if(fit.status!=='PASS')throw Error('Wall joinery is not verified');return {...model,parts:model.parts.map(p=>patch(p,fit.primary_parts)),wall_joinery_revision:'R004870'};}
// TIMESTAMP START 2026-11-05T08:46:05+00:00 | REVISION R000036
function applyLayout(layout,fit){const pegs=fit.locking_pegs||[],ids=new Set(layout.components.map(p=>p.id));if(pegs.some(p=>ids.has(p.id)))throw Error('Wall locking pegs already occur in this layout');return {...layout,components:[...layout.components.map(p=>patch(p,fit.wall_parts)),...pegs]};}
// TIMESTAMP END 2026-11-05T08:46:05+00:00 | REVISION R000036
function applyContext(context,fit){
// TIMESTAMP START 2026-11-05T20:08:59+00:00 | REVISION R000063
 const bindings=typeof OctagonCurrentCacheBindings!=='undefined'?OctagonCurrentCacheBindings:typeof require==='function'?require('./current-cache-bindings.js'):null;
 if(!(bindings?bindings.matches(fit,context,'wall'):context.sha256===fit.source_model_sha256))throw Error('Wall joints are stale for the selected model');
// TIMESTAMP END 2026-11-05T20:08:59+00:00 | REVISION R000063
 return {...context,model:applyModel(context.model,fit),loadReview:{...context.loadReview,
  members:context.loadReview.members.map(p=>fit.primary_parts[p.id]?{...p,...fit.primary_parts[p.id].wallJoineryMass}:p)},
  pressureAvailable:false,contactMarkersAvailable:false,wallJoinery:fit};
}
const api={applyModel,applyLayout,applyContext};root.OctagonWallJoinery=api;if(typeof module!=='undefined'&&module.exports)module.exports=api;
})(typeof globalThis!=='undefined'?globalThis:this);
// TIMESTAMP END 2026-11-02T20:38:50-05:00 | REVISION R004870
