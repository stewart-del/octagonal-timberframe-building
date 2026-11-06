// TIMESTAMP START 2026-11-05T20:08:59+00:00 | REVISION R000063
'use strict';
const assert=require('assert/strict'),fs=require('fs'),path=require('path'),C=require('../src/current-cache-bindings.js'),root=path.resolve(__dirname,'..'),owner=C.verifiedNode(root),clone=value=>JSON.parse(JSON.stringify(value));
for(const id of ['baseline','proposed','top-entry']){
 const file=id==='baseline'?'enclosure-fit.json':id==='proposed'?'step-lap-proposed-enclosure-fit.json':'top-entry-proposed-enclosure-fit.json',original=JSON.parse(fs.readFileSync(path.join(root,'src',file))),before=JSON.stringify(original),key='enclosure-'+id,bound=C.attach(original,key,id,owner),context={id,sha256:owner.models[id],cacheOwnership:owner};
 assert(C.matches(bound,context,key));assert.equal(JSON.stringify(original),before);assert.equal(bound.source_model_sha256,original.source_model_sha256);assert(!C.matches(original,context,key));
 for(const mutate of [p=>p.currentSourceBinding.bindingSha256='0'.repeat(64),p=>p.currentSourceBinding.cacheSha256='0'.repeat(64),p=>p.currentSourceBinding.currentModelSha256='0'.repeat(64),p=>p.currentSourceBinding.variant='other']){const bad=clone(bound);mutate(bad);assert(!C.matches(bad,context,key));}
 assert(!C.matches(bound,{...context,sha256:'different generated geometry'},key));assert(!C.matches(bound,{...context,cacheOwnership:undefined},key));assert(!C.matches(bound,{...context,cacheOwnership:{...owner,wholeBuildingReady:true}},key));
}
const W=require('../src/wall-joinery.js'),fits=require('../src/wall-joinery-fit.json');
for(const [id,prefix]of [['baseline',''],['proposed','step-lap-proposed-'],['top-entry','top-entry-proposed-']]){
 const model=require('../src/'+(prefix?prefix+'model.json':'model-data.json')),loadReview=require('../src/'+(prefix?prefix+'load-review.json':'load-review-data.json')),fit=C.attach(fits.variants[id],'wall',id,owner),context={id,sha256:owner.models[id],model,loadReview,cacheOwnership:owner},before=JSON.stringify(model),applied=W.applyContext(context,fit);
 assert.equal(applied.model.parts.length,model.parts.length);assert.equal(JSON.stringify(model),before);assert.strictEqual(applied.wallJoinery,fit);assert.throws(()=>W.applyContext({...context,cacheOwnership:undefined},fit),/stale/);
}
require('../src/model-variants.js');const variants={};
for(const [id,prefix]of [['baseline',''],['proposed','step-lap-proposed-'],['top-entry','top-entry-proposed-']]){
 const original=require('../src/'+(prefix?prefix+'enclosure-fit.json':'enclosure-fit.json'));variants[id]={model:require('../src/'+(prefix?prefix+'model.json':'model-data.json')),sha256:owner.models[id],loadReview:require('../src/'+(prefix?prefix+'load-review.json':'load-review-data.json')),materials:require('../src/'+(prefix?prefix+'material-groups.json':'material-groups.json')),enclosureFit:C.attach(original,'enclosure-'+id,id,owner),cacheOwnership:owner};
}
for(const id of ['baseline','proposed','top-entry']){
 const context=global.OctagonModelVariants.context(variants,'?model='+id);assert.equal(context.sha256,owner.models[id]);assert.equal(context.enclosureFit.currentSourceBinding.currentModelSha256,context.sha256);assert.notEqual(context.enclosureFit.source_model_sha256,context.sha256);
 const bad={...variants,[id]:{...variants[id],cacheOwnership:undefined}};assert.throws(()=>global.OctagonModelVariants.context(bad,'?model='+id),/stale/);
}
assert(!C.matches({},{}));console.log('PASS: current source/cache/proof/variant identities; original headers preserved; no full-building certificate inferred.');
// TIMESTAMP END 2026-11-05T20:08:59+00:00 | REVISION R000063
