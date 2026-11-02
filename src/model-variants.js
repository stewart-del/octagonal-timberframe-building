/* Boot-time model choice: no mixed meshes, load centroids, cavity overlays or exports. */
(function(root){
'use strict';
function requestedId(search=''){for(const pair of String(search).replace(/^\?/,'').split('&')){const [key,value]=pair.split('=');try{if(decodeURIComponent(key)==='model')return decodeURIComponent(value||'')==='baseline'?'baseline':decodeURIComponent(value||'')==='proposed'?'proposed':'top-entry';}catch(e){/* Invalid query defaults to top-entry. */}}return 'top-entry';}
function selectionURL(href,id){if(!['baseline','proposed','top-entry'].includes(id))throw new Error('Unknown model variant');const url=new URL(href);url.searchParams.set('model',id);return url.href;}
function context(variants,search=''){
 const id=requestedId(search),v=variants[id];if(!v?.model||!v.sha256)throw new Error('Selected model data is unavailable: '+id);
 const isProposed=id!=='baseline',sha=v.sha256;
 if(v.loadReview?.source_model_sha256!==sha)throw new Error('Selected model self-weight data is stale: '+id);
 if(v.materials?.source_sha256!==sha)throw new Error('Selected model inventory is stale: '+id);
 if(v.enclosureFit?.source_model_sha256!==sha)throw new Error('Selected model enclosure clearance data is stale: '+id);
 if(v.cavities&&v.cavities.source_model_sha256!==sha)throw new Error('Selected model cavity data is stale: '+id);
 const loadReview=isProposed?{...v.loadReview,issues:[]}:v.loadReview;
 const cavityAuditPassed=v.cavities?.fit_audit?.status==='PASS';
 const cavityAvailable=cavityAuditPassed&&v.cavities.available!==false&&Object.keys(v.cavities.parts||{}).length>0;
 const cavities=cavityAvailable?{...v.cavities,available:true}:{source_model_sha256:sha,parts:{},available:false,status:'Recess overlay unavailable: the selected model has no complete passing cavity-fit audit. No overlay from another model is substituted.'};
 const label=id==='top-entry'?'Top-entry head proposal':isProposed?'Perimeter step-lap proposal':'Saved baseline model';
 return {...v,id,isProposed,label,loadReview,cavities,cavityAuditPassed:cavityAvailable,pressureAvailable:!isProposed,contactMarkersAvailable:!isProposed,exportPrefix:id==='top-entry'?'TOP-ENTRY-NOT-FABRICATION-':isProposed?'PROPOSED-NOT-FABRICATION-':'BASELINE-',status:isProposed?label+' · geometry review only, not fabrication approved':'Saved baseline · geometry study, not construction approved'};
}
function exportName(selected,name){return name.startsWith('TOP-ENTRY-NOT-FABRICATION-')||name.startsWith('PROPOSED-NOT-FABRICATION-')||name.startsWith('BASELINE-')?name:selected.exportPrefix+name;}
function bind(selected,{document,location,beforeChange=()=>{}}){
 const $=id=>document.getElementById(id),select=$('modelVariant');
 if(select){select.value=selected.id;select.onchange=()=>{if(select.value===selected.id)return;if(!['baseline','proposed','top-entry'].includes(select.value)){select.value=selected.id;return;}beforeChange();location.assign(selectionURL(location.href,select.value));};}
 const status=$('modelVariantStatus');if(status)status.textContent=selected.status;
 const badge=$('modelRevisionBadge');if(badge)badge.textContent=selected.label;
 const plan=$('plansRevision');if(plan)plan.textContent=selected.status;
 for(const [id,mode] of [['modelVariantAssembled','assembled'],['modelVariantExploded','exploded']])if($(id)){$(id).href='downloads/'+(selected.id==='top-entry'?'Octagon-TOP-ENTRY-':selected.isProposed?'Octagon-PROPOSED-step-lap-':'Octagon-R01-')+mode+'.glb';$(id).download=selected.exportPrefix+mode+'.glb';}
 if(selected.isProposed){
  for(const id of ['hypotheticalSeat','hypotheticalReaction'])if($(id))$(id).disabled=true;
  if($('hypotheticalSeat')){$('hypotheticalSeat').innerHTML='<option value="">Unavailable for proposed joints</option>';$('hypotheticalSeat').value='';}
  if($('hypotheticalPressure'))$('hypotheticalPressure').textContent='Unavailable for proposed joints: baseline 64/12 in² pressure shortcuts are disabled. Reactions and capacities remain unsolved.';
  if($('loadIssueDetail'))$('loadIssueDetail').textContent='Baseline contact warning markers are disabled for this model. Their absence does not establish restraint or capacity; use the proposed joint review.';
 }
 const auditLink=$('cavityFitAuditLink');if(auditLink){auditLink.hidden=!selected.cavityAuditPassed;if(selected.cavityAuditPassed)auditLink.href='downloads/'+(selected.id==='baseline'?'cavity-fit-audit.json':'step-lap-proposed-cavity-fit-audit.json');else auditLink.removeAttribute?.('href');}
 for(const id of ['showHollows','hollowXray'])if($(id))$(id).disabled=!selected.cavities.available;
 if(!selected.cavities.available){if($('showHollows'))$('showHollows').checked=false;if($('hollowStatus'))$('hollowStatus').textContent=selected.cavities.status;}
 else if($('hollowStatus')&&!$('hollowStatus').textContent)$('hollowStatus').textContent=selected.label+': independent cavity-fit audit passed. Select a timber to reveal its matching recesses.';
 return selected;
}
root.OctagonModelVariants={requestedId,selectionURL,context,exportName,bind};
})(typeof globalThis!=='undefined'?globalThis:this);
