// Offline scripted DOM/WebGL integration tests. No browser or network access.
// Focus and events are simulated, including the real registered document/window handlers.
const fs=require('fs'),vm=require('vm');
const data=JSON.parse(fs.readFileSync(__dirname+'/embedded-model.json','utf8'));
const html=fs.readFileSync(__dirname+'/../src/viewer.template.html','utf8');
const callbacks=[];let documentMock,windowMock;
class EventTargetMock{
 constructor(){this.handlers={};this.listeners={};}
 addEventListener(type,fn){(this.handlers[type]??=[]).push(fn);this.listeners[type]=e=>this.emit(type,e);}
 emit(type,event={}){const e={type,target:this,defaultPrevented:false,cancelBubble:false,preventDefault(){this.defaultPrevented=true},stopPropagation(){this.cancelBubble=true},...event};for(const fn of this.handlers[type]||[])fn(e);return e;}
}
class El extends EventTargetMock{
 constructor(tag='div'){super();this.tagName=tag.toUpperCase();this.children=[];this.style={};this.dataset={};this.attributes={};this.checked=false;this.value='';this.textContent='';this.width=0;this.height=0;this.className='';this.contentEditable='inherit';this.classList={add:(...xs)=>{this.className=[...new Set([...this.className.split(/\s+/).filter(Boolean),...xs])].join(' ')},remove:(...xs)=>{this.className=this.className.split(/\s+/).filter(x=>!xs.includes(x)).join(' ')},contains:x=>this.className.split(/\s+/).includes(x),toggle:(x,force)=>{const add=force===undefined?!this.classList.contains(x):force;this.classList[add?'add':'remove'](x);return add}};}
 contains(el){return this===el||this.children.some(c=>c.contains?.(el))}
 get isConnected(){return this===documentMock?.body||!!this.parentElement?.isConnected}
 querySelectorAll(s){const out=[];const visit=n=>{for(const c of n.children){if(s==='[data-focus-key]'?!!c.dataset?.focusKey:c.tagName==='BUTTON'&&!c.disabled)out.push(c);visit(c)}};visit(this);return out}
 append(...xs){for(const x of xs)this.appendChild(x)}
 appendChild(x){this.children.push(x);if(x&&typeof x==='object')x.parentElement=this;return x}
 replaceChildren(...xs){let active=documentMock?.activeElement,removedActive=false;while(active){if(this.children.includes(active)){removedActive=true;break}active=active.parentElement}for(const child of this.children)child.parentElement=null;this.children=[];this.append(...xs);if(removedActive)documentMock.body.focus()}
 setAttribute(k,v){this.attributes[k]=String(v);if(k==='id')this.id=String(v);if(k==='class')this.className=String(v);if(k==='contenteditable')this.contentEditable=String(v)}
 getAttribute(k){return k in this.attributes?this.attributes[k]:null}
 hasAttribute(k){return k in this.attributes}
 removeAttribute(k){delete this.attributes[k]}
 getBoundingClientRect(){return {width:800,height:600,left:0,top:0}}
 get offsetWidth(){return this.className.includes('detail')?180:36}
 get offsetHeight(){return this.className.includes('detail')?64:20}
 setPointerCapture(){}releasePointerCapture(){}
 focus(){if(documentMock.activeElement===this)return;const old=documentMock.activeElement;old?.emit?.('blur',{relatedTarget:this});documentMock.activeElement=this;documentMock.emit('focusout',{target:old,relatedTarget:this});this.emit('focus',{relatedTarget:old});documentMock.emit('focusin',{target:this,relatedTarget:old});}
 blur(){if(documentMock.activeElement===this)documentMock.body.focus()}
 click(){this.focus();const e=this.emit('click');this.onclick?.(e);return e}
 getContext(type){return type==='webgl'?gl:null}
}
const noop=()=>{};
const gl=new Proxy({COMPILE_STATUS:1,LINK_STATUS:2,ARRAY_BUFFER:3,FLOAT:4,LINES:5,TRIANGLES:6,COLOR_BUFFER_BIT:1,DEPTH_BUFFER_BIT:2,createShader:()=>({}),createProgram:()=>({}),createBuffer:()=>({}),getShaderParameter:()=>true,getProgramParameter:()=>true,getAttribLocation:()=>0,getUniformLocation:()=>({})},{get(t,k){return k in t?t[k]:noop}});
const els=new Map();
function get(id){if(!els.has(id)){const escaped=id.replace(/[.*+?^${}()|[\]\\]/g,'\\$&');const match=html.match(new RegExp('<([a-zA-Z0-9-]+)\\b[^>]*\\bid="'+escaped+'"[^>]*>'));const el=new El(match?.[1]||'div');el.id=id;const attrs=match?.[0]||'';for(const a of attrs.matchAll(/\b([\w-]+)="([^"]*)"/g))el.setAttribute(a[1],a[2]);el.checked=/\bchecked\b/.test(attrs);el.value=el.getAttribute('value')||'';els.set(id,el);documentMock?.body?.appendChild(el)}return els.get(id)}
documentMock=new EventTargetMock();Object.assign(documentMock,{getElementById:get,querySelector:t=>get("document-"+t),createElement:t=>new El(t),body:new El('body'),hidden:false,hasFocus:()=>windowMock.focused});documentMock.activeElement=documentMock.body;
windowMock=new EventTargetMock();Object.assign(windowMock,{devicePixelRatio:1,location:{hash:''},focused:true});
get('model-data').textContent=JSON.stringify(data);get('scene').parentElement=new El();
function testKey(key,target=documentMock.activeElement,options={}){return documentMock.emit('keydown',{key,target,...options})}
function testKeyUp(key,options={}){return windowMock.emit('keyup',{key,target:documentMock.activeElement,...options})}
function testFrame(time){const current=callbacks.splice(0);for(const cb of current)cb(time)}
function testWindowBlur(){windowMock.focused=false;windowMock.emit('blur')}
function testWindowFocus(){windowMock.focused=true;windowMock.emit('focus')}
const context={console,Float32Array,Map,Set,Math,Number,String,JSON,Blob,setTimeout:noop,queueMicrotask:fn=>fn(),URL:{createObjectURL:()=>'',revokeObjectURL:noop},window:windowMock,document:documentMock,requestAnimationFrame:cb=>{callbacks.push(cb);return callbacks.length},ResizeObserver:class{observe(){}},testKey,testKeyUp,testFrame,testWindowBlur,testWindowFocus,testCallbackCount:name=>callbacks.filter(cb=>cb.name===name).length};
vm.createContext(context);
const script=fs.readFileSync(__dirname+'/viewer-script-check.js','utf8');
const test=`
function assert(condition,message){if(!condition)throw Error(message)}
function closeEnough(a,b,tolerance=1e-8){return length(vsub(a,b))<=tolerance}
function assertNoKeyCapture(key,target,options={}){const result=testKey(key,target,options);assert(!result.defaultPrevented,'Protected key must not be captured: '+key);assert(navKeys.size===0,'Protected key must not move camera: '+key)}
function descendants(el){return [el,...el.children.flatMap(x=>descendants(x))]}
function findAction(text){return descendants($('selection')).find(el=>el.tagName==='BUTTON'&&el.textContent===text)}
canvas.focus();
const cubeV=[[0,0,0],[1,0,0],[1,1,0],[0,1,0],[0,0,1],[1,0,1],[1,1,1],[0,1,1]];const cubeT=[[0,2,1],[0,3,2],[4,5,6],[4,6,7],[0,1,5],[0,5,4],[1,2,6],[1,6,5],[2,3,7],[2,7,6],[3,0,4],[3,4,7]];if(featureEdges(cubeV,cubeT).length/12!==12)throw Error('Feature edges must suppress cube face diagonals');
if(detailOn!==false)throw Error('Expanded labels must default off to avoid clutter');
if(parts.filter(isTimber).length!==96)throw Error('Expected 96 retained timber pieces');
if(parts.some(p=>/^J[0-7]-1$/.test(p.id)))throw Error('Retired center rafters remain');
if(parts.some(p=>p.temporary&&isShown(p)))throw Error('Temporary components must start hidden');
render();
const centerProjection=project(camera.target);
if(Math.abs(centerProjection.x-width/2)>0.01||Math.abs(centerProjection.y-height/2)>0.01)throw Error('Projection center incorrect');
for(const p of parts.filter(p=>visible.has(p.group)))for(const v of p.vertices){const q=project(v);if(!q||q.x<0||q.x>width||q.y<0||q.y>height)throw Error('Fit model clips visible geometry');}
for(let i=0;i<250;i++)testKey('-',canvas);
if(camera.distance>100)throw Error('Keyboard zoom out exceeds limit');
for(let i=0;i<250;i++)testKey('+',canvas);
if(camera.distance<.12)throw Error('Keyboard zoom in exceeds limit');
selectPart('P0');if(selected!=='P0')throw Error('Selection failed');
if(num(null)!=='—')throw Error('Null angle displayed as a numeric cut');
const ring=parts.find(p=>p.id==='B0');
if(labelText(ring).some(x=>x.includes('R03')))throw Error('Historical R03 labels remain active');
const p=parts.find(p=>p.id==='R0');focusPart(p);if(length(vsub(camera.target,fittedCenter(p)))>1e-8)throw Error('Focus failed');
explode=1;if(length(vsub(position(p),p.center))<0.01)throw Error('Explosion failed');
visible.add('TEMPORARY_WORKS');render();openSchedule();
if($('scheduleRows').children.length!==parts.length)throw Error('Missing schedule rows');$('closeSchedule').click();
isolatedId='B0';if(parts.filter(isShown).length!==1)throw Error('Isolation must show exactly one piece');render();selectPart('R0');if(isolatedId!=='R0'||parts.filter(isShown).length!==1)throw Error('Isolation must follow selection');$('allPermanent').onclick();if(isolatedId!==null||parts.filter(isShown).length!==parts.filter(p=>defaultGroups().some(g=>g.id===p.group)).length)throw Error('Restore permanent frame failed');
$('hidePieces').onclick();if(parts.filter(isShown).length!==0)throw Error('Hide all failed');
selectPart('B0');if(parts.filter(isShown).length!==1)throw Error('Selecting hidden piece must reveal it only');
$('allPermanent').onclick();isolatedId='B0';renderList();
const row=$('partList').children.find(row=>row.children[1]?.children[0]?.textContent==='B1');
if(!row)throw Error('Per-piece checkbox missing');row.children[0].checked=true;row.children[0].listeners.change();
if(parts.filter(isShown).length!==2)throw Error('Checkbox from isolation must not reveal unrelated pieces');
if(cuts.filter(f=>f.reference).length!==parts.reduce((n,p)=>n+(p.reference_end_faces||[]).length,0))throw Error('Missing current end references');
const cut=cuts.find(f=>f.part_id==='J0-0'&&f.mate_part_id==='R0'&&!f.reference);if(!cut)throw Error('Missing short-rafter hip contact plane');
selectCut(cut);if(selected!==cut.part_id||selectedCut!==cut.id||!showCutFaces)throw Error('Cut selection failed');
render();if(!cutVisible(cut))throw Error('Selected cut must be visible');
cutExplode=1;if(length(vsub(cutOffset(cut),offset(partById.get(cut.part_id))))<.55)throw Error('Cut separation failed');
faceCut(cut);if(isolatedId!==cut.part_id||parts.filter(isShown).length!==1)throw Error('Face cut must isolate owner');render();const cutCenter=project(camera.target);if(Math.abs(cutCenter.x-width/2)>.01||Math.abs(cutCenter.y-height/2)>.01)throw Error('Face cut center wrong');
if(cut.mate_part_id&&partById.has(cut.mate_part_id)){showMatingPair(cut);if(parts.filter(isShown).length!==2||explode!==0||cutExplode!==0)throw Error('Mating pair must be assembled in isolation');}
showEndRefs=true;const ref=cuts.find(f=>f.reference&&f.part_id===selected);if(!cutVisible(ref))throw Error('Integrated end reference missing');
$('allPermanent').onclick();fitModel();render();
window.location={hash:'#part=P0&isolate=1'};applyHash();if(selected!=='P0'||isolatedId!=='P0'||parts.filter(isShown).length!==1)throw Error('Isolated hash link failed');window.location.hash='#R0';applyHash();if(selected!=='R0'||isolatedId!==null)throw Error('Simple hash link failed');


// Free mode now explicitly focuses the canvas; separately verify BUTTON-focused WASD.
$('allPermanent').click();fitModel();const orbitBefore=orbitBasis();$('freeNav').click();
assert(navigation==='free','Free button must enable Free mode');assert($('navigationStatus').textContent.includes('WASD active'),'Active keyboard status must be visible');
assert(document.activeElement===canvas,'Free button should focus the canvas');$('freeNav').focus();
assert(closeEnough(freeBasis().eye,orbitBefore.eye)&&closeEnough(freeBasis().forward,orbitBefore.forward),'Mode switch must preserve camera');
assert((document.handlers.keydown||[]).length>0,'Keyboard routing must be registered on document');
const freeStart=fly.eye.slice();const freeDown=testKey('w');
assert(freeDown.defaultPrevented&&navKeys.has('w'),'W must activate with Free button focused');
for(let i=0;i<8;i++)testKey('w',document.activeElement,{repeat:true});
assert(testCallbackCount('flyTick')===1,'Repeated keydown must not create competing animation loops');
testFrame(1000);testFrame(1050);testKeyUp('w');
assert(Math.abs(length(vsub(fly.eye,freeStart))-flySpeed*.05)<1e-8,'Actual frame-driven WASD has wrong distance');
assert(navKeys.size===0,'Keyup must stop movement');testFrame(1100);
const stopEye=fly.eye.slice();testFrame(1150);assert(closeEnough(fly.eye,stopEye),'Camera continued after keyup');
const diagonalStart=fly.eye.slice();testKey('w');testKey('d');advanceFly(.05);testKeyUp('w');testKeyUp('d');assert(Math.abs(length(vsub(fly.eye,diagonalStart))-flySpeed*.05)<1e-8,'Diagonal speed not normalized');
const shiftStart=fly.eye.slice();testKey('w',document.activeElement,{shiftKey:true});advanceFly(.05);assert(Math.abs(length(vsub(fly.eye,shiftStart))-flySpeed*.15)<1e-8,'Shift must accelerate 3x');testKeyUp('Shift',{shiftKey:false});const normalStart=fly.eye.slice();advanceFly(.05);testKeyUp('w');assert(Math.abs(length(vsub(fly.eye,normalStart))-flySpeed*.05)<1e-8,'Releasing Shift must restore normal speed');
const verticalStart=fly.eye.slice();testKey('e');advanceFly(.05);testKeyUp('e');assert(Math.abs(fly.eye[1]-verticalStart[1]-flySpeed*.05)<1e-8&&Math.abs(fly.eye[0]-verticalStart[0])<1e-8&&Math.abs(fly.eye[2]-verticalStart[2])<1e-8,'E must move vertically up');testKey('q');advanceFly(.05);testKeyUp('q');assert(closeEnough(fly.eye,verticalStart),'Q must reverse vertical movement');
// Guards check both event target and focused element; editable ancestry includes an empty attribute.
const protectedTargets=['input','select','textarea'].map(t=>document.createElement(t));
for(const attr of ['true','','plaintext-only']){const parent=document.createElement('div');parent.setAttribute('contenteditable',attr);const child=document.createElement('span');parent.appendChild(child);protectedTargets.push(child)}
for(const target of protectedTargets){$('freeNav').focus();testKey('w');target.focus();assert(navKeys.size===0,'Entering form must cancel held motion');assert($('navigationStatus').textContent.includes('paused'),'Typing must show paused status');assertNoKeyCapture('w',target);assertNoKeyCapture('w',canvas);$('freeNav').focus();assertNoKeyCapture('w',target)}
$('freeNav').focus();for(const modifier of ['ctrlKey','altKey','metaKey']){testKey('w');assertNoKeyCapture('w',document.activeElement,{[modifier]:true});testKeyUp('w')}
assertNoKeyCapture('w',document.activeElement,{isComposing:true});
// Normal interface buttons and body remain navigation-ready; input sliders deliberately pause.
$('resetView').click();const buttonEye=fly.eye.slice();testKey('a');advanceFly(.05);testKeyUp('a');assert(length(vsub(fly.eye,buttonEye))>0,'Button focus must not disable Free WASD');
document.body.focus();const bodyEye=fly.eye.slice();testKey('s');advanceFly(.05);testKeyUp('s');assert(length(vsub(fly.eye,bodyEye))>0,'Body focus must not disable Free WASD');
$('flySpeed').focus();assertNoKeyCapture('w',$('flySpeed'));$('freeNav').click();
// Window blur and modal guards clear held movement and require a fresh key press after returning.
testKey('w');testWindowBlur();assert($('navigationStatus').textContent.includes('paused'),'Blur must show paused status');assertNoKeyCapture('w',document.activeElement);assert(navKeys.size===0,'Window blur must clear held keys');const blurredEye=fly.eye.slice();advanceFly(.05);assert(closeEnough(fly.eye,blurredEye),'Blurred camera must stop');testWindowFocus();assert(navKeys.size===0,'Window focus must not resurrect held keys');testKey('w');assert(navKeys.has('w'),'WASD must resume after focus');testKeyUp('w');
testKey('w');$('scheduleButton').click();assert(navKeys.size===0,'Opening schedule must stop movement');assert($('navigationStatus').textContent.includes('paused'),'Schedule must show paused status');assertNoKeyCapture('w',document.activeElement);$('closeSchedule').click();const modalEye=fly.eye.slice();testKey('w');advanceFly(.05);testKeyUp('w');assert(length(vsub(fly.eye,modalEye))>0,'Closing schedule must restore WASD while button focused');
testKey('w');document.hidden=true;document.emit('visibilitychange');assert(navKeys.size===0,'Hidden document must clear keys');document.hidden=false;document.emit('visibilitychange');
$('orbitNav').click();const noFly=orbitBasis().eye.slice();const orbitW=testKey('w');advanceFly(.05);assert(!navKeys.size&&closeEnough(orbitBasis().eye,noFly),'WASD must not move Orbit mode');$('freeNav').click();
// Existing Free mode precision, pan, wheel, drag and reset behavior.
const focusPiece=parts.find(p=>p.id==='B0');focusPart(focusPiece);assert(navigation==='free','Focus changed Free mode');matrix();const fp=project(fittedCenter(focusPiece));assert(Math.abs(fp.x-width/2)<.01&&Math.abs(fp.y-height/2)<.01,'Free focus failed');
faceCut(cut);assert(navigation==='free','Cut focus changed Free mode');matrix();const cf=project(vadd(cut.center,cutOffset(cut)));assert(Math.abs(cf.x-width/2)<.01&&Math.abs(cf.y-height/2)<.01,'Free cut focus failed');
const wheelBefore=fly.eye.slice();canvas.listeners.wheel({deltaY:-100,preventDefault(){}});assert(length(vsub(fly.eye,wheelBefore))>.01,'Free wheel must move camera');
const yawBefore=fly.yaw;canvas.listeners.pointerdown({pointerId:1,clientX:100,clientY:100});canvas.listeners.pointermove({pointerId:1,clientX:120,clientY:105});canvas.listeners.pointerup({pointerId:1,clientX:120,clientY:105});assert(fly.yaw!==yawBefore,'Free drag must look');
const panBefore=fly.eye.slice();canvas.listeners.pointerdown({pointerId:2,clientX:100,clientY:100});canvas.listeners.pointermove({pointerId:2,clientX:120,clientY:105,shiftKey:true});canvas.listeners.pointerup({pointerId:2,clientX:120,clientY:105});assert(length(vsub(fly.eye,panBefore))>.01,'Free shift-pan failed');
// General view switches preserve both position and direction without an inspection pivot.
$('allPermanent').click();fitModel();const freeBeforeOrbit=freeBasis();$('orbitNav').click();assert(closeEnough(orbitBasis().eye,freeBeforeOrbit.eye)&&closeEnough(orbitBasis().forward,freeBeforeOrbit.forward),'Returning to Orbit must preserve view');
$('freeNav').click();fitModel();assert(navigation==='free'&&closeEnough(freeBasis().eye,orbitBasis().eye),'Reset Free view failed');$('orbitNav').click();
// Individual-piece inspection: exact current fitted bounds, explicit center marker and local orbit.
explode=.35;selectPart('B0');const inspectPiece=partById.get('B0');const expectedCenter=[0,1,2].map(k=>(Math.min(...inspectPiece.vertices.map(v=>v[k]))+Math.max(...inspectPiece.vertices.map(v=>v[k])))/2+offset(inspectPiece)[k]);assert(closeEnough(fittedCenter(inspectPiece),expectedCenter),'Fitted center must be actual bounding-box center with explode offset');
const isolateButton=findAction('Isolate & center');assert(isolateButton,'Missing Isolate & center control');isolateButton.click();assert(parts.filter(isShown).length===1&&isShown(inspectPiece),'Isolate & center must show exactly selected piece');assert(navigation==='orbit'&&closeEnough(camera.target,expectedCenter),'Isolate & center must set local Orbit pivot');
render();assert(!$('pieceCenter').hidden&&$('pieceCenterLabel').textContent.includes('B0'),'Isolated fitted center marker must be visible and identified');matrix();const centerView=project(expectedCenter);assert(Math.abs(centerView.x-width/2)<.01&&Math.abs(centerView.y-height/2)<.01,'Isolated center must be centered');
for(const end of ['A','B']){selectPart(inspectPiece.id);const endButton=findAction('Inspect End '+end);assert(endButton,'Missing end '+end+' inspection control');endButton.click();assert(navigation==='free'&&parts.filter(isShown).length===1,'End inspection must isolate and enable Free mode');assert(flySpeed<=.02&&flySpeed>=.01,'End inspection must choose fine travel speed');assert(!isTypingTarget(document.activeElement),'End action must leave navigation-ready focus');const axis=unit(inspectPiece.axis_direction||vsub(inspectPiece.axis_end,inspectPiece.axis_start)),center=fittedCenter(inspectPiece),projections=inspectPiece.vertices.map(v=>dot(vsub(vadd(v,offset(inspectPiece)),center),axis)),eyeProjection=dot(vsub(fly.eye,center),axis);assert(end==='A'?eyeProjection<Math.min(...projections):eyeProjection>Math.max(...projections),'End eye must lie outside fitted axial extent');assert(dot(freeBasis().forward,axis)*(end==='A'?1:-1)>.999999,'End view must look inward along piece axis');const endEye=fly.eye.slice();testKey('w');advanceFly(.05);testKeyUp('w');assert(length(vsub(fly.eye,endEye))>0,'WASD must work immediately after end '+end+' button');const beforeOrbit=fly.eye.slice();$('orbitNav').click();assert(closeEnough(orbitBasis().eye,beforeOrbit),'Local Orbit switch must preserve eye position');assert(closeEnough(camera.target,fittedCenter(inspectPiece)),'Local Orbit must pivot at fitted piece center');}
$('freeNav').click();isolateAndCenter(inspectPiece);assert(navigation==='free','Isolate & center must preserve Free mode');matrix();const freeCentered=project(fittedCenter(inspectPiece));assert(Math.abs(freeCentered.x-width/2)<.01&&Math.abs(freeCentered.y-height/2)<.01,'Free Isolate & center must center selected solid');
for(const id of ['P0','R0'])for(const end of ['A','B']){const member=partById.get(id);inspectEnd(member,end);const axis=unit(member.axis_direction||vsub(member.axis_end,member.axis_start));assert(fly.eye.every(Number.isFinite)&&freeBasis().right.every(Number.isFinite)&&length(freeBasis().right)>.999999,'End view must remain well-defined for vertical and sloped members');assert(dot(freeBasis().forward,axis)*(end==='A'?1:-1)>.999999,'End look direction incorrect for '+id+' '+end);matrix();const q=project(fittedCenter(member));assert(q&&Math.abs(q.x-width/2)<.01&&Math.abs(q.y-height/2)<.01,'End view must frame member center for '+id+' '+end);} $('flySpeed').value='.01';$('flySpeed').oninput({target:$('flySpeed')});assert(flySpeed===.01,'Fine speed must allow 0.01 m/s');
// Adaptive clipping preserves overview depth precision while admitting close inspection.
const clipPiece=parts.find(isShown);assert(clipPiece,'Need visible piece for near-plane checks');assert(nearClipForEye(fittedCenter(clipPiece))===.0005,'Near clip must reach 0.5 mm floor inside piece bounds');assert(nearClipForEye([1000,1000,1000])===.05,'Near clip must cap at 50 mm for distant overview');
// Explode translates the local Orbit pivot but never drags the independent Free camera.
$('orbitNav').click();isolateAndCenter(inspectPiece);const beforeExplodePivot=camera.target.slice(),beforeExplodeEye=orbitBasis().eye.slice(),beforeExplodeCenter=fittedCenter(inspectPiece);$('explode').value='75';$('explode').oninput({target:$('explode')});const explodeDelta=vsub(fittedCenter(inspectPiece),beforeExplodeCenter);assert(length(explodeDelta)>0,'Explode test must move piece');assert(closeEnough(camera.target,vadd(beforeExplodePivot,explodeDelta))&&closeEnough(orbitBasis().eye,vadd(beforeExplodeEye,explodeDelta)),'Orbit must follow exploded selected-piece center');assert(closeEnough(camera.target,fittedCenter(inspectPiece)),'Orbit pivot must remain at fitted center after exploding');
$('freeNav').click();const independentEye=fly.eye.slice();$('explode').value='20';$('explode').oninput({target:$('explode')});assert(closeEnough(fly.eye,independentEye),'Explode must not move independent Free camera');assert(closeEnough(inspectionPivot,fittedCenter(inspectPiece)),'Free inspection pivot must track exploded piece for later Orbit');
console.log(JSON.stringify({test_method:'offline mocked DOM/WebGL; no browser UI',actual_document_keyboard_handlers:true,free_button_focused_wasd:true,frame_driven_wasd:true,repeated_key_single_animation_loop:true,keyboard_keyup_stops:true,typing_and_editable_ancestry_guards:true,focused_input_guard:true,modifier_and_composition_guards:true,button_and_body_navigation:true,window_blur_and_focus:true,modal_keyboard_guard:true,visibility_cleanup:true,orbit_wasd_inactive:true,free_normalized_speed:true,shift_speed_released:true,vertical_qe:true,free_focus:true,free_pan_zoom:true,mode_view_continuity:true,fitted_center:true,isolate_and_center:true,end_a_and_b_inspection:true,vertical_and_sloped_end_views:true,navigation_status_feedback:true,end_buttons_wasd:true,local_orbit_pivot:true,fine_speed_0_01:true,adaptive_near_clip_bounds:true,explode_local_orbit_pivot:true,explode_free_camera_independent:true,feature_edges_suppress_coplanar:true,piece_isolation:true,per_piece_checkboxes:true,hide_all:true,cut_selection:true,cut_separation:true,normal_cut_view:true,mating_pair_view:true,part_deep_links:true,end_reference_count:cuts.filter(f=>f.reference).length,parts:parts.length,temporary_hidden_by_default:true,projection_center:true,fit_model_contains_geometry:true,keyboard_zoom_limits:true,r01_reference_labels:true,selection:true,focus:true,explosion:true,schedule_rows:$('scheduleRows').children.length,network_dependencies:false},null,2));
`;
vm.runInContext(script+'\n'+test,context);

