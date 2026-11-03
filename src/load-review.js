// Preliminary applied-load visualization, not a structural solver.
const LOAD_REVIEW=__LOAD_REVIEW_JSON__;
let loadReviewOn=false,loadDensity=780;
const loadArrowElements=new Map(),loadIssueElements=new Map();
function timberGravity(member,density=loadDensity){const mass=member.volume_m3*density,force=mass*9.80665;return {mass_kg:mass,force_N:force,force_lbf:force/4.4482216152605};}
function gravityArrowWidth(forceN){return 1+Math.sqrt(Math.max(0,forceN))/12;}
function loadReviewRows(){return LOAD_REVIEW.members.map(member=>{const p=partById.get(member.id);return {member,p,...timberGravity(member),point:p?vadd(member.centroid_m,offset(p)):member.centroid_m};});}
function loadReviewTotals(){const rows=loadReviewRows(),sum=rr=>rr.reduce((s,r)=>s+r.force_N,0);return {total_N:sum(rows),visible_N:sum(rows.filter(r=>r.p&&isShown(r.p))),visible_count:rows.filter(r=>r.p&&isShown(r.p)).length};}
function hypotheticalPressure(reactionN,areaIn2){if(reactionN===''||!Number.isFinite(Number(reactionN))||Number(reactionN)<0||!Number.isFinite(Number(areaIn2))||Number(areaIn2)<=0)return null;return {MPa:Number(reactionN)/(Number(areaIn2)*645.16),psi:Number(reactionN)/4.4482216152605/Number(areaIn2)};}
function updateHypotheticalPressure(){const value=hypotheticalPressure($('hypotheticalReaction').value,$('hypotheticalSeat').value);$('hypotheticalPressure').textContent=value?'Hypothetical average only: '+num(value.MPa,4)+' MPa / '+num(value.psi,2)+' psi. Actual reaction remains unknown.':'N/A — actual joint reaction is unknown.';}
function showLoadIssue(issue){$('loadIssueDetail').textContent=issue.owner+(issue.mate?' / '+issue.mate:'')+' · '+issue.title+' — '+(issue.classification==='missing_restraint'?'Missing modeled restraint at the indicated pair. ':'Capacity/details unverified. ')+issue.reason;}
function initLoadReview(){
 const host=$('loadReviewOverlay'),listedFamilies=new Set();
 for(const member of LOAD_REVIEW.members){const el=document.createElement('div');el.className='gravity-arrow';el.setAttribute('aria-hidden','true');host.appendChild(el);loadArrowElements.set(member.id,el);}
 for(const issue of LOAD_REVIEW.issues){const marker=document.createElement('button');marker.className='load-issue-marker'+(issue.classification==='capacity_unknown'?' capacity-unknown':'');marker.textContent='!';marker.setAttribute('aria-label',issue.title+': '+issue.reason);marker.title=issue.owner+(issue.mate?' / '+issue.mate:'')+' · '+issue.title;marker.onclick=()=>showLoadIssue(issue);host.appendChild(marker);loadIssueElements.set(issue.id,marker);if(!listedFamilies.has(issue.family)){listedFamilies.add(issue.family);const item=document.createElement('button'),count=LOAD_REVIEW.issues.filter(i=>i.family===issue.family).length;item.textContent='! '+issue.title+' ('+count+' markers)';item.onclick=()=>showLoadIssue(issue);$('loadIssueList').appendChild(item);}}
 $('loadDensity').value='780';$('hypotheticalSeat').value='64';$('hypotheticalReaction').value='';
 $('showLoadReview').onchange=()=>{loadReviewOn=!!$('showLoadReview').checked;updateLoadReview();requestRender();};
 $('loadDensity').onchange=()=>{const density=Number($('loadDensity').value);if([520,600,780,900].includes(density))loadDensity=density;updateLoadReview();requestRender();};
 $('hypotheticalReaction').oninput=updateHypotheticalPressure;$('hypotheticalSeat').onchange=updateHypotheticalPressure;updateHypotheticalPressure();
}
function updateLoadReview(){
 $('loadReviewOverlay').hidden=!loadReviewOn;$('loadReviewViewportLegend').hidden=!loadReviewOn;$('loadReviewControls').hidden=!loadReviewOn;
 if(!loadReviewOn){for(const el of [...loadArrowElements.values(),...loadIssueElements.values()])el.style.display='none';return;}
// TIMESTAMP START 2026-11-02T15:19:38-05:00 | REVISION R004803
 const totals=loadReviewTotals();$('loadReviewSummary').textContent='Assumed '+loadDensity+' kg/m³ · ALL '+LOAD_REVIEW.members.length+' timbers: '+num(totals.total_N/1000,2)+' kN / '+num(totals.total_N/4.4482216152605,0)+' lbf. Visible '+totals.visible_count+': '+num(totals.visible_N/1000,2)+' kN.';
// TIMESTAMP END 2026-11-02T15:19:38-05:00 | REVISION R004803
 let selectedText='Select a timber for its applied self-weight.';
 for(const row of loadReviewRows()){
  const el=loadArrowElements.get(row.member.id);el.style.display='none';if(selected===row.member.id)selectedText=row.member.id+' assumed self-weight: '+num(row.force_N,1)+' N / '+num(row.force_lbf,1)+' lbf ('+num(row.mass_kg,1)+' kg).';
  if(!row.p||!isShown(row.p))continue;const a=project(row.point),b=project(vadd(row.point,[0,-.8,0]));if(!a||!b||a.x<0||a.x>width||a.y<0||a.y>height)continue;const dx=b.x-a.x,dy=b.y-a.y,span=Math.hypot(dx,dy);if(span<2)continue;
  el.style.display='block';el.style.left=a.x+'px';el.style.top=a.y+'px';el.style.width=span+'px';el.style.height=gravityArrowWidth(row.force_N)+'px';el.style.transform='translateY(-50%) rotate('+Math.atan2(dy,dx)+'rad)';el.title=row.member.id+': '+num(row.force_N,1)+' N downward, applied self-weight only';
 }
 $('loadReviewSelected').textContent=selectedText;
 for(const issue of LOAD_REVIEW.issues){const el=loadIssueElements.get(issue.id),owner=partById.get(issue.owner),mate=partById.get(issue.mate),p=owner&&isShown(owner)?owner:mate&&isShown(mate)?mate:null;el.style.display='none';if(!p)continue;const q=project(vadd(issue.point_m,offset(p)));if(!q||q.x<12||q.x>width-12||q.y<12||q.y>height-12)continue;el.style.left=q.x+'px';el.style.top=q.y+'px';el.style.display='block';}
}
