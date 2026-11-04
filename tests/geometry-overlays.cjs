// Reads the production helper and tests it with deterministic DOM/GL doubles.
// No browser, screenshot, or model geometry rewrite is involved.
const fs=require('node:fs'),path=require('node:path');
const candidates=[path.resolve(__dirname,'../src/viewer.template.html'),path.resolve(__dirname,'../site/src/viewer.template.html')];
const templatePath=process.argv[2]||candidates.find(p=>fs.existsSync(p));
if(!templatePath)throw Error('Pass viewer.template.html as the first argument.');
const template=fs.readFileSync(templatePath,'utf8');
const helperPath=path.resolve(path.dirname(templatePath),'geometry-overlays.js');
// TIMESTAMP START 2026-11-02T09:43:39-05:00 | REVISION R004757
const source=fs.readFileSync(helperPath,'utf8');
const TimberEdgeMeasurements=require(path.resolve(path.dirname(templatePath),'edge-measurements.js'));
// TIMESTAMP END 2026-11-02T09:43:39-05:00 | REVISION R004757
const raySource=template.match(/^function triangleHit\([^\n]+$/m)?.[0];
if(!raySource)throw Error('Missing production triangleHit function');
new Function('return ('+raySource+')');
if(source.split('__CAVITY_JSON__').length!==2)throw Error('Expected one cavity-data insertion point');
// TIMESTAMP START 2026-11-02T09:43:39-05:00 | REVISION R004757
const result=new Function('template','TimberEdgeMeasurements',`
// TIMESTAMP END 2026-11-02T09:43:39-05:00 | REVISION R004757
// TIMESTAMP START 2026-11-03T17:20:17-05:00 | REVISION R005073
const MODEL_CONTEXT={parametric:false};
// TIMESTAMP END 2026-11-03T17:20:17-05:00 | REVISION R005073
const passed=[],failed=[],check=(yes,msg)=>{(yes?passed:failed).push(msg)};
const vadd=(a,b)=>a.map((x,i)=>x+b[i]),vsub=(a,b)=>a.map((x,i)=>x-b[i]),vmul=(a,s)=>a.map(x=>x*s),length=a=>Math.hypot(...a),dot=(a,b)=>a.reduce((s,x,i)=>s+x*b[i],0),unit=a=>vmul(a,1/(length(a)||1)),cross=(a,b)=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];
const triangle={vertices:[[0,0,0],[1,0,0],[0,1,0]],triangles:[[0,1,2]],edges:[[0,1],[1,2],[2,0]],volume_m3:.001};
// TIMESTAMP START 2026-11-02T09:43:39-05:00 | REVISION R004757
const data={parts:{A:{removed:triangle},B:{removed:triangle}},fit_audit:{status:'PASS'}};
// TIMESTAMP END 2026-11-02T09:43:39-05:00 | REVISION R004757
const parts=['A','B','C'].map((id,i)=>({id,displacement:[i*2,0,0],vertices:[],triangles:[]})),partById=new Map(parts.map(p=>[p.id,p]));
// TIMESTAMP START 2026-11-02T15:06:05-05:00 | REVISION R004799
const schematicParts=[];
// TIMESTAMP END 2026-11-02T15:06:05-05:00 | REVISION R004799
const selectedPartIds=new Set(['A','B']);let selected='B',explode=0,width=900,height=650,renderRequests=0;
const hidden=new Set(),ghosts=new Set(),isShown=p=>!hidden.has(p.id),selectionAlpha=p=>ghosts.has(p.id)?.14:1,offset=p=>vmul(p.displacement,explode);
const basis={eye:[0,0,5]},fittedBounds=new Map(parts.map(p=>[p.id,{min:[0,0,0],max:[0,0,0]}]));
const num=(n,d=2)=>Number(n).toFixed(d),angleText=n=>num(n,2)+'°';
function element(tag){return {tagName:tag.toUpperCase(),children:[],style:{},dataset:{},textContent:'',checked:false,value:'',appendChild(e){this.children.push(e);return e},setAttribute(n,v){this[n]=v}}}
// TIMESTAMP START 2026-11-02T09:43:39-05:00 | REVISION R004757
const elements=new Map(['showHollows','hollowXray','showEdgeMeasurements','hollowStatus'].map(id=>[id,element('input')]));
// TIMESTAMP END 2026-11-02T09:43:39-05:00 | REVISION R004757
const $=id=>elements.get(id),document={createElement:element},labelLayer=element('div'),requestRender=()=>renderRequests++;
const downloads=[],download=(...args)=>downloads.push(args),csvCell=x=>'"'+String(x).replaceAll('"','""')+'"';
let edgeCalls=0,edgeFixtures=[];
const edgeMeasurementData=p=>{edgeCalls++;return edgeFixtures.map(x=>({...x,timber_id:p.id}))},edgeMeasurementText=e=>e.id+' | '+e.length_in+' in | 90° inside',edgeMeasurementDescription=e=>e.timber_id+' '+e.id+' prototype only';
const makeEdge=(id,x,y,span=100)=>({id,a:[x-span/2,y,0],b:[x+span/2,y,0],midpoint:[x,y,0],length_in:1,interiorAngleDeg:90,planeAngleDeg:90,normalAngleDeg:90});
const project=v=>v[2]<0?null:{x:v[0],y:v[1],distance:10+v[2]},cssColor=c=>'rgb('+c.map(x=>Math.round(x*255)).join(',')+')',surfaceDisplayColor=c=>c;
let depthTest=true,depthMask=true,blend=false,opacity=1,lineMode=1,bound=null,translation=[0,0,0],log=[],throwDraw=false,nextBuffer=0;
let gl={BLEND:'BLEND',DEPTH_TEST:'DEPTH_TEST',SRC_ALPHA:'SRC',ONE_MINUS_SRC_ALPHA:'DEST',TRIANGLES:'TRIANGLES',LINES:'LINES',
 enable(cap){if(cap===this.BLEND)blend=true;if(cap===this.DEPTH_TEST)depthTest=true},disable(cap){if(cap===this.BLEND)blend=false;if(cap===this.DEPTH_TEST)depthTest=false},blendFunc(){},depthMask(v){depthMask=v},uniform3fv(k,v){if(k==='translation')translation=[...v]},uniform1f(k,v){if(k==='opacity')opacity=v;if(k==='lineMode')lineMode=v},
 drawArrays(type,start,count){log.push({type,count,depthTest,depthMask,blend,opacity,lineMode,translation:[...translation],bound});if(throwDraw)throw Error('draw failure')}};
const originalGL=gl,loc={translation:'translation',color:'color',opacity:'opacity',lineMode:'lineMode'},buildBuffer=raw=>({id:++nextBuffer,raw:[...raw]}),bind=b=>bound=b;
let fallback={beginPath(){},moveTo(){},lineTo(){},closePath(){},fill(){log.push({fallbackFill:this.fillStyle})},stroke(){log.push({fallbackStroke:this.strokeStyle})},globalAlpha:1};
${raySource}
${source.replace('__CAVITY_JSON__','data')}
check(showHollows&&hollowXray&&!edgeMeasurementsOn&&hollowMode==='removed','Overlay defaults match selected recesses with optional edge text off');
check(template.includes('id="showHollows" checked')&&template.includes('id="hollowXray" checked')&&template.includes('id="showEdgeMeasurements">'),'HTML checkbox defaults match helper state');
check(template.indexOf('drawCavityVolumes();')<template.indexOf('  drawCutFaces();')&&template.includes('updateEdgeMeasurementLabels();')&&template.includes('updateHollowStatus();'),'Render integrates cavities before cut overlays and refreshes labels/status');
check(cavityRecords().map(r=>r.p.id).join(',')==='A,B','Recess records include every selected visible timber');
hidden.add('A');check(cavityRecords().map(r=>r.p.id).join(',')==='B','Hidden selected timber does not receive cavity overlays');hidden.clear();
selectedPartIds.add('C');check(cavityRecords().length===2,'Missing cavity records do not cause phantom shapes');selectedPartIds.delete('C');
// TIMESTAMP START 2026-11-02T09:43:39-05:00 | REVISION R004757
check(!template.includes('id="hollowMode"')&&hollowMode==='removed','Invalid residual mode is absent from the UI and only removed-stock cavities are selected');
updateHollowStatus();check($('hollowStatus').textContent.includes('Independent cavity-fit audit passed.'),'Verified audit status appears with the removed-only fixture');
delete data.fit_audit;updateHollowStatus();check($('hollowStatus').textContent.includes('Independent cavity-fit audit is not attached.')&&!$('hollowStatus').textContent.includes('audit passed'),'Missing audit metadata does not claim verification');
data.fit_audit={status:'PASS'};
// TIMESTAMP END 2026-11-02T09:43:39-05:00 | REVISION R004757
$('showHollows').onchange({target:{checked:false}});check(!showHollows&&cavityRecords().length===0,'Master toggle hides all cavity records');
log=[];drawCavityVolumes();check(log.length===0,'Hidden cavities perform no GL draw');
$('showHollows').onchange({target:{checked:true}});log=[];explode=.5;drawCavityVolumes();
check(log.length===4&&log.every(x=>x.blend&&!x.depthMask&&!x.depthTest),'X-ray draws selected cavity fill/edges with blending and without depth writes/tests');
// TIMESTAMP START 2026-11-02T09:43:39-05:00 | REVISION R004757
check(log.filter(x=>x.type==='TRIANGLES').every(x=>x.opacity===.48)&&log.filter(x=>x.type==='LINES').every(x=>x.opacity===.95&&x.lineMode===1),'Cavity fills and unlit boundaries use intended opacities');
// TIMESTAMP END 2026-11-02T09:43:39-05:00 | REVISION R004757
check(log[2].translation[0]===1,'Cavity meshes follow the selected timber exploded offset');
check(depthTest&&depthMask&&!blend&&opacity===1&&lineMode===1,'Successful overlay leaves clean state for cut surfaces');
const cached=cavityRenderMesh(parts[0],'removed'),buffers=nextBuffer;check(cached===cavityRenderMesh(parts[0],'removed')&&nextBuffer===buffers,'Cavity render buffers are cached without rebuilding geometry');
// TIMESTAMP START 2026-11-02T09:43:39-05:00 | REVISION R004757
$('hollowXray').onchange({target:{checked:false}});log=[];drawCavityVolumes();check(log.every(x=>x.depthTest)&&log.filter(x=>x.type==='TRIANGLES').every(x=>x.opacity===.55),'Disabling X-ray respects timber depth and selects normal overlay opacity');
// TIMESTAMP END 2026-11-02T09:43:39-05:00 | REVISION R004757
throwDraw=true;let threw=false;try{drawCavityVolumes()}catch(e){threw=true}throwDraw=false;check(threw&&depthTest&&depthMask&&!blend&&opacity===1&&lineMode===1,'A failed draw restores all shared GL state');
selectedPartIds.clear();log=[];drawCavityVolumes();check(!log.length,'No selection draws no cavities');selectedPartIds.add('A');selectedPartIds.add('B');
gl=null;log=[];drawCavityVolumes();updateHollowStatus();check(log.some(x=>x.fallbackFill)&&log.some(x=>x.fallbackStroke)&&$('hollowStatus').textContent.includes('always shown as X-rays'),'2D fallback draws cavity fill/edges and discloses its X-ray limitation');gl=originalGL;
selected='A';explode=1;updateHollowStatus();check($('hollowStatus').textContent.includes('1000.00 cm³')&&$('hollowStatus').textContent.includes('this view is exploded'),'Cavity status uses cubic-centimetre conversion and assembled-model caveat');
selected=null;updateHollowStatus();check($('hollowStatus').textContent.includes('Select a timber'),'Clearing selection resets cavity status');selected='A';explode=0;
// TIMESTAMP START 2026-11-02T15:06:05-05:00 | REVISION R004799
const porchMesh={...triangle,vertices:triangle.vertices.map(v=>[v[0]+3,v[1],v[2]]),volume_m3:.002};
const porch={id:'MUD-JOIST-TEST',schematicKind:'mudroom',displacement:[3,2,-1],vertices:[],triangles:[],joineryCavity:{removed:porchMesh,fit_audit:{status:'PASS'}}};
schematicParts.push(porch);partById.set(porch.id,porch);
data.parts[porch.id]={removed:triangle};
data.available=false;data.status='Top-entry main recesses remain held.';
selected=porch.id;selectedPartIds.clear();selectedPartIds.add('A');selectedPartIds.add(porch.id);explode=.75;
check(cavityRecords().length===1&&cavityRecords()[0].p===porch,'Verified porch recesses remain selectable while main-model cavities stay unavailable');
check(cavityRenderMesh(porch,'removed').mesh.vertices===porchMesh.vertices,'Part-bound porch cavity data takes precedence over a global record with the same ID');
check(cavityRenderMesh(parts[0],'removed')===null,'A previously cached main cavity stays unavailable during the main-model hold');
log=[];drawCavityVolumes();
check(log.length===2&&log.every(x=>x.translation.join(',')==='2.25,1.5,-0.75'),'Porch cavity fill and feature edges follow the selected exploded piece');
updateHollowStatus();
// TIMESTAMP START 2026-11-03T06:44:16-05:00 | REVISION R004894
check($('hollowStatus').textContent.includes('2000.00 cm³')&&$('hollowStatus').textContent.includes('Joint geometry-fit audit passed.')&&$('hollowStatus').textContent.includes('Structural capacity remains unverified.')&&$('hollowStatus').textContent.includes('this view is exploded'),'Porch status identifies its own geometry audit and retains structural and assembled-state limits');
// TIMESTAMP END 2026-11-03T06:44:16-05:00 | REVISION R004894
check(data.available===false&&data.status==='Top-entry main recesses remain held.','Porch inspection never changes main-model cavity availability or status');
hidden.add(porch.id);check(cavityRecords().length===0,'Hidden porch pieces do not produce cavity overlays');hidden.delete(porch.id);
showHollows=false;check(cavityRecords().length===0,'The cavity master toggle also controls porch recesses');showHollows=true;
porch.joineryCavity.fit_audit.status='FAIL';updateHollowStatus();
check(cavityRecords().length===0&&cavityRenderMesh(porch,'removed')===null&&$('hollowStatus').textContent.includes('awaits a passing fit audit'),'Unverified porch data cannot reuse cached geometry or claim a passed audit');
porch.joineryCavity.fit_audit.status='PASS';selected='A';updateHollowStatus();
check($('hollowStatus').textContent==='Top-entry main recesses remain held.','Selecting a main timber restores its unavailable-cavity status');
selected=null;updateHollowStatus();check($('hollowStatus').textContent==='Top-entry main recesses remain held.','Clearing the porch selection preserves the main-model hold');
delete data.available;delete data.status;delete data.parts[porch.id];schematicParts.length=0;partById.delete(porch.id);
selectedPartIds.clear();selectedPartIds.add('A');selectedPartIds.add('B');selected='A';explode=0;
// TIMESTAMP END 2026-11-02T15:06:05-05:00 | REVISION R004799
edgeFixtures=[makeEdge('E001',300,150),makeEdge('E002',310,150),makeEdge('E003',550,250),makeEdge('E004',600,450,5),{...makeEdge('E005',700,500),midpoint:[700,500,-1]}];
updateEdgeMeasurementLabels();check(!edgeMeasurementLabels.length,'Edge text off by default allocates no labels');
$('showEdgeMeasurements').onchange({target:{checked:true}});updateEdgeMeasurementLabels();
let shown=edgeMeasurementLabels.filter(x=>x.style.display==='block');check(shown.length===2,'Edge labels cull overlaps, very short spans and clipped points');
check(shown.every(x=>x.textContent.includes('90° inside')&&x.title.startsWith('A ')),'Edge text includes measurement semantics and original active timber ID');
const calls=edgeCalls;updateEdgeMeasurementLabels();check(edgeCalls===calls,'Repeated label renders reuse immutable edge measurements');
hidden.add('A');updateEdgeMeasurementLabels();check(edgeMeasurementLabels.every(x=>x.style.display==='none'),'Hiding active timber clears all prior edge labels');hidden.clear();
$('showEdgeMeasurements').onchange({target:{checked:false}});updateEdgeMeasurementLabels();check(edgeMeasurementLabels.every(x=>x.style.display==='none'),'Turning edge text off clears all labels');
const host=element('div');appendEdgeMeasurements(host,parts[0]);const panel=host.children[0],buttons=panel.children.filter(e=>e.tagName==='BUTTON');
const table=panel.children.find(e=>e.tagName==='DIV').children[0],body=table.children.find(e=>e.tagName==='TBODY');
check(body.children.length===edgeFixtures.length&&body.children.map(r=>r.dataset.edgeId).join(',')===edgeFixtures.map(e=>e.id).join(','),'Full selected-piece table includes every edge even when canvas labels are culled');
check(table.children[0].children[0].children.map(e=>e.textContent).join('|')==='Edge|Length (in)|Inside|Planes','Full edge table separates length, material-side and acute plane measurements');
buttons[0].onclick();check(edgeMeasurementsOn&&$('showEdgeMeasurements').checked,'Selected-piece action synchronizes global edge-text checkbox');
buttons[1].onclick();check(downloads.length===1&&downloads[0][0]==='A-edge-measurements.csv'&&downloads[0][1].includes('"A","E001"')&&downloads[0][1].includes('prototype only'),'Edge CSV retains timber and edge IDs with prototype definitions');
edgeMeasurementCache.delete('A');edgeFixtures=[makeEdge('LEFT',15,150),makeEdge('RIGHT',width-15,350),makeEdge('CENTER',450,500)];updateEdgeMeasurementLabels();shown=edgeMeasurementLabels.filter(x=>x.style.display==='block');
check(shown.length===1&&shown[0].textContent.startsWith('CENTER'),'Viewport-side edge labels remain fully readable instead of being clipped');

// Independently specified cube rays exercise actual production visibility code.
const cubeVertices=[[-1,-1,-1],[1,-1,-1],[1,1,-1],[-1,1,-1],[-1,-1,1],[1,-1,1],[1,1,1],[-1,1,1]],cubeTriangles=[[0,2,1],[0,3,2],[4,5,6],[4,6,7],[0,1,5],[0,5,4],[3,7,6],[3,6,2],[0,4,7],[0,7,3],[1,2,6],[1,6,5]];
function setMesh(part,vertices){part.vertices=vertices;part.triangles=cubeTriangles;fittedBounds.set(part.id,{min:[0,1,2].map(k=>Math.min(...vertices.map(v=>v[k]))),max:[0,1,2].map(k=>Math.max(...vertices.map(v=>v[k])))});}
setMesh(parts[0],cubeVertices);hidden.add('B');explode=0;basis.eye=[0,0,5];
check(edgeMeasurementVisible(parts[0],[1,0,1]),'Front cube edge remains visible at its own surface boundary');
check(!edgeMeasurementVisible(parts[0],[1,0,-1]),'Rear cube edge is hidden by the owner front surface');
setMesh(parts[1],cubeVertices.map(v=>[.5+v[0]*.25,v[1]*.25,3+v[2]*.5]));hidden.delete('B');
check(!edgeMeasurementVisible(parts[0],[1,0,1]),'Other opaque timber blocks a rear measurement anchor');
ghosts.add('B');check(edgeMeasurementVisible(parts[0],[1,0,1]),'Translucent context does not suppress a readable selected edge');ghosts.clear();
parts[0].displacement=[5,0,0];explode=1;basis.eye=[5,0,5];
check(edgeMeasurementVisible(parts[0],[1,0,1])&&!edgeMeasurementVisible(parts[0],[1,0,-1]),'Visibility rays respect owner and occluder exploded offsets');

// TIMESTAMP START 2026-11-02T09:43:39-05:00 | REVISION R004757
check(renderRequests===6,'Each of the six exercised user toggles/actions schedules a renderer update');
// TIMESTAMP END 2026-11-02T09:43:39-05:00 | REVISION R004757
return {passed,failed};
// TIMESTAMP START 2026-11-02T09:43:39-05:00 | REVISION R004757
`)(template,TimberEdgeMeasurements);
// TIMESTAMP END 2026-11-02T09:43:39-05:00 | REVISION R004757
console.log(JSON.stringify({method:'Production overlay helper in a deterministic DOM/GL state harness; no browser',source:helperPath,passed:result.passed.length,failed:result.failed.length,assertions:result.passed,failures:result.failed},null,2));
if(result.failed.length)process.exitCode=1;
