/* Boot-time model choice: no mixed meshes, load centroids, cavity overlays or exports. */
(function(root){
'use strict';
function requestedId(search=''){for(const pair of String(search).replace(/^\?/,'').split('&')){const [key,value]=pair.split('=');try{if(decodeURIComponent(key)==='model')return decodeURIComponent(value||'')==='baseline'?'baseline':'proposed';}catch(e){/* Invalid query defaults to proposed. */}}return 'proposed';}
function selectionURL(href,id){if(!['baseline','proposed'].includes(id))throw new Error('Unknown model variant');const url=new URL(href);url.searchParams.set('model',id);return url.href;}
function context(variants,search=''){
 const id=requestedId(search),v=variants[id];if(!v?.model||!v.sha256)throw new Error('Selected model data is unavailable: '+id);
 const isProposed=id==='proposed',sha=v.sha256;
 if(v.loadReview?.source_model_sha256!==sha)throw new Error('Selected model self-weight data is stale: '+id);
 if(v.materials?.source_sha256!==sha)throw new Error('Selected model inventory is stale: '+id);
 if(v.enclosureFit?.source_model_sha256!==sha)throw new Error('Selected model enclosure clearance data is stale: '+id);
 if(v.cavities&&v.cavities.source_model_sha256!==sha)throw new Error('Selected model cavity data is stale: '+id);
 const loadReview=isProposed?{...v.loadReview,issues:[]}:v.loadReview;
// TIMESTAMP START 2026-11-02T10:08:20-05:00 | REVISION R004760
 const cavityAuditPassed=v.cavities?.fit_audit?.status==='PASS';
 const cavityAvailable=cavityAuditPassed&&v.cavities.available!==false&&Object.keys(v.cavities.parts||{}).length>0;
 const cavities=cavityAvailable?{...v.cavities,available:true}:{source_model_sha256:sha,parts:{},available:false,status:'Recess overlay unavailable: the selected model has no complete passing cavity-fit audit. No overlay from another model is substituted.'};
 const label=isProposed?'Proposed step-lap model':'Saved baseline model';
 const fitStatus=cavityAvailable?'cavity-fit audit passed':'cavity-fit audit unavailable';
 return {...v,id,isProposed,label,loadReview,cavities,cavityAuditPassed:cavityAvailable,pressureAvailable:!isProposed,contactMarkersAvailable:!isProposed,exportPrefix:isProposed?'PROPOSED-NOT-FABRICATION-':'BASELINE-',status:(isProposed?'Proposed step-lap joinery':'Saved baseline')+' · '+fitStatus+(isProposed?'; not fabrication approved':'; not construction approved')};
// TIMESTAMP END 2026-11-02T10:08:20-05:00 | REVISION R004760
}
function exportName(selected,name){return name.startsWith('PROPOSED-NOT-FABRICATION-')||name.startsWith('BASELINE-')?name:selected.exportPrefix+name;}
function bind(selected,{document,location,beforeChange=()=>{}}){
 const $=id=>document.getElementById(id),select=$('modelVariant');
 if(select){select.value=selected.id;select.onchange=()=>{if(select.value===selected.id)return;if(!['baseline','proposed'].includes(select.value)){select.value=selected.id;return;}beforeChange();location.assign(selectionURL(location.href,select.value));};}
 const status=$('modelVariantStatus');if(status)status.textContent=selected.status;
 const badge=$('modelRevisionBadge');if(badge)badge.textContent=selected.isProposed?'Proposed step-lap':'Saved baseline';
// TIMESTAMP START 2026-11-02T10:08:20-05:00 | REVISION R004760
 const plan=$('plansRevision');if(plan)plan.textContent=selected.status;
 const auditLink=$('cavityFitAuditLink');if(auditLink)auditLink.href='downloads/'+(selected.isProposed?'step-lap-proposed-cavity-fit-audit.json':'cavity-fit-audit.json');
// TIMESTAMP END 2026-11-02T10:08:20-05:00 | REVISION R004760
 for(const [id,mode] of [['modelVariantAssembled','assembled'],['modelVariantExploded','exploded']])if($(id)){$(id).href='downloads/'+(selected.isProposed?'Octagon-PROPOSED-step-lap-':'Octagon-R01-')+mode+'.glb';$(id).download=selected.exportPrefix+mode+'.glb';}
 if(selected.isProposed){
  for(const id of ['hypotheticalSeat','hypotheticalReaction'])if($(id))$(id).disabled=true;
  if($('hypotheticalSeat')){$('hypotheticalSeat').innerHTML='<option value="">Unavailable for proposed joints</option>';$('hypotheticalSeat').value='';}
  if($('hypotheticalPressure'))$('hypotheticalPressure').textContent='Unavailable for proposed joints: baseline 64/12 in² pressure shortcuts are disabled. Reactions and capacities remain unsolved.';
  if($('loadIssueDetail'))$('loadIssueDetail').textContent='Baseline contact warning markers are disabled for this model. Their absence does not establish restraint or capacity; use the proposed joint review.';
 }
// TIMESTAMP START 2026-11-02T10:08:20-05:00 | REVISION R004760
 for(const id of ['showHollows','hollowXray'])if($(id))$(id).disabled=!selected.cavities.available;
 if(!selected.cavities.available){if($('showHollows'))$('showHollows').checked=false;if($('hollowStatus'))$('hollowStatus').textContent=selected.cavities.status;}
 else if($('hollowStatus')&&!$('hollowStatus').textContent)$('hollowStatus').textContent=selected.label+': independent cavity-fit audit passed. Select a timber to reveal its matching recesses.';
// TIMESTAMP END 2026-11-02T10:08:20-05:00 | REVISION R004760
 return selected;
}
root.OctagonModelVariants={requestedId,selectionURL,context,exportName,bind};
})(typeof globalThis!=='undefined'?globalThis:this);
