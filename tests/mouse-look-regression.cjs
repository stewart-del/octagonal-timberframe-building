// No browser automation: exercise the actual mouse-look helpers and event guards.
async function runMouseLookTests(html){
  const helper=html.match(/\/\/ MOUSE_LOOK_START([\s\S]*?)\/\/ MOUSE_LOOK_END/);
  if(!helper)throw Error('Mouse-look helpers absent');
  const line=name=>{const hit=html.split('\n').filter(x=>x.startsWith('function '+name+'('));if(hit.length!==1)throw Error('Expected function '+name);return hit[0];};
  const eventLines=html.split('\n').filter(x=>x.startsWith("canvas.addEventListener('pointer")||x.includes("document.addEventListener('pointerlockchange'"));
  const bindings=html.split('\n').find(x=>x.startsWith("$('freeNav').onclick="));
  const support=`
    let navigation='orbit',navigationWindowFocused=true,flySpeed=1.5,flyFast=false,flyLastTime=null,freeFocusDistance=10,inspectionPivot=null;
    const fly={eye:[0,0,10],yaw:0,pitch:0},camera={target:[0,0,0],distance:10,theta:0,phi:0};
    const navKeys=new Set(),pointers=new Map();let dragged=false,startPoint=null,lastPoint=null,lastPinch=null;
    const vadd=(a,b)=>a.map((v,i)=>v+b[i]),vsub=(a,b)=>a.map((v,i)=>v-b[i]),vmul=(a,n)=>a.map(v=>v*n),length=v=>Math.hypot(...v);
    const freeFromOrbit=()=>{},freeBasis=()=>({eye:fly.eye.slice(),forward:[0,0,-1]});
    let renderCount=0,pickCalls=[];const requestRender=()=>renderCount++,pick=(...args)=>pickCalls.push(args);
    const setFlySpeed=()=>{},startFlyTick=()=>{},moveFree=()=>{},matrix=()=>{};const width=900,height=600,basis={right:[1,0,0],up:[0,1,0]};
    const docEvents={},winEvents={};let document;
    const nodes=new Map();function element(id){if(!nodes.has(id)){const classes=new Set();nodes.set(id,{id,tagName:id==='search'?'INPUT':'BUTTON',parentElement:null,style:{},attributes:{},events:{},classList:{add:x=>classes.add(x),remove:x=>classes.delete(x),contains:x=>classes.has(x)},setAttribute(k,v){this.attributes[k]=v;},getAttribute(k){return this.attributes[k]??null;},focus(){document.activeElement=this;},getBoundingClientRect(){return {left:0,top:0};},setPointerCapture(){},addEventListener(k,f){this.events[k]=f;}});}return nodes.get(id);}
    const $=element,canvas=element('scene');canvas.tagName='CANVAS';
    document={pointerLockElement:null,hidden:false,activeElement:canvas,addEventListener(k,f){(docEvents[k]??=[]).push(f);}};
    const window={PointerEvent:function(){},addEventListener(k,f){(winEvents[k]??=[]).push(f);}};
    let exits=0;document.exitPointerLock=()=>{exits++;document.pointerLockElement=null;for(const f of docEvents.pointerlockchange||[])f();};
  `;
  const tests=`
    const passed=[];const check=(ok,message)=>{if(!ok)throw Error(message);passed.push(message);};
    const emit=(name,event={})=>{for(const f of docEvents[name]||[])f(event);};
    const winEmit=name=>{for(const f of winEvents[name]||[])f();};
    const lock=()=>{document.pointerLockElement=canvas;emit('pointerlockchange');};
    check(!docEvents.pointerlockchange?.length||docEvents.pointerlockchange.length===1,'Single pointer-lock change listener');
    check(!!docEvents.pointermove?.length&&!docEvents.mousemove,'Use one movement event path to prevent double rotation');
    requestMouseLook();check(navigation==='free'&&!mouseLookPending&&$('navigationStatus').textContent.includes('unavailable'),'Unsupported pointer lock retains Free/WASD and explains fallback');
    canvas.requestPointerLock=()=>{throw Error('Denied');};requestMouseLook();check(!mouseLookPending&&!mouseLookWanted&&$('navigationStatus').textContent.includes('not enabled'),'Synchronous lock denial is caught');
    canvas.requestPointerLock=()=>Promise.reject(Error('Denied'));await requestMouseLook();check(!mouseLookPending&&!mouseLookWanted,'Promise lock rejection is handled');
    let requests=0;canvas.requestPointerLock=()=>{requests++;};$('freeNav').onclick();requestMouseLook();check(requests===1&&mouseLookPending&&navigation==='free','Explicit Free click requests lock once; repeated pending request is suppressed');
    navKeys.add('w');pointers.set(1,[0,0]);lock();check(isMouseLookLocked()&&!mouseLookPending&&navKeys.size===0&&pointers.size===0&&document.activeElement===canvas,'Lock acquisition clears stale input and focuses canvas');
    check($('mouseLook').textContent==='Release mouse (Esc)'&&$('mouseLook').attributes['aria-pressed']==='true','Mouse-look control reports active lock');
    const yaw=fly.yaw,pitch=fly.pitch;emit('pointermove',{movementX:10,movementY:-20,buttons:0,target:canvas});check(Math.abs(fly.yaw-yaw+.03)<1e-9&&Math.abs(fly.pitch-pitch-.06)<1e-9,'Mouse movement steers without a pressed button');
    emit('pointermove',{movementX:0,movementY:1e9,buttons:0,target:canvas});check(fly.pitch===-1.52,'Mouse-look pitch remains bounded');
    const finiteYaw=fly.yaw;emit('pointermove',{movementX:NaN,movementY:1,target:canvas});check(fly.yaw===finiteYaw&&Number.isFinite(fly.pitch),'Invalid movement deltas are ignored');
    canvas.events.pointerdown({pointerId:1,clientX:10,clientY:10,preventDefault(){}});canvas.events.pointermove({pointerId:1,clientX:30,clientY:30,movementX:20,movementY:20});canvas.events.pointerup({pointerId:1,clientX:30,clientY:30});check(pointers.size===0&&pickCalls.length===0,'Locked pointer events cannot pick or start dragging');
    navKeys.add('w');navKeyDown({key:'Escape'});check(!isMouseLookLocked()&&navKeys.size===0&&!mouseLookWanted&&document.activeElement===$('mouseLook'),'Escape releases capture, stops travel and restores control focus');
    navKeyDown({key:'w',repeat:true,target:$('mouseLook'),preventDefault(){}});check(navKeys.size===0,'Held-key repeat cannot restart travel after Escape');navKeyDown({key:'w',repeat:false,target:$('mouseLook'),preventDefault(){}});check(navKeys.has('w'),'Fresh key press resumes navigation after release');navKeyUp({key:'w'});
    canvas.events.pointerup({pointerId:1,clientX:30,clientY:30});check(pickCalls.length===0,'Trailing unlocked pointer-up cannot accidentally pick');
    canvas.events.pointerdown({pointerId:2,clientX:40,clientY:50});canvas.events.pointerup({pointerId:2,clientX:40,clientY:50,shiftKey:true});check(pickCalls.length===1&&pickCalls[0][0]===40&&pickCalls[0][1]===50,'Unlocked click selection remains available');
    if(sourceHasAdditive)check(pickCalls[0][2]===true,'Shift-click additive selection is preserved');
    requestMouseLook();lock();const exitsBefore=exits;setNavigation('orbit');check(navigation==='orbit'&&!isMouseLookLocked()&&exits===exitsBefore+1,'Orbit mode exits pointer lock');
    requestMouseLook();lock();navKeys.add('w');winEmit('blur');check(!isMouseLookLocked()&&!navigationWindowFocused&&navKeys.size===0,'Blur releases lock and clears held keys');winEmit('focus');
    requestMouseLook();lock();navKeys.add('w');document.hidden=true;emit('visibilitychange');check(!isMouseLookLocked()&&navKeys.size===0,'Hidden document releases capture');document.hidden=false;emit('visibilitychange');
    requestMouseLook();releaseMouseLook();const lateExits=exits;lock();check(!isMouseLookLocked()&&exits===lateExits+1,'Late lock acquisition after cancellation is immediately released');
    requestMouseLook();$('scheduleModal').classList.add('open');$('closeSchedule').focus();lock();check(!isMouseLookLocked()&&document.activeElement===$('closeSchedule'),'Late lock cannot capture or steal focus from an open dialog');$('scheduleModal').classList.remove('open');
    requestMouseLook();emit('pointerlockerror');check(!mouseLookPending&&!mouseLookWanted&&$('navigationStatus').textContent.includes('not enabled'),'Legacy pointerlockerror event is handled');
    const unlockedYaw=fly.yaw;emit('pointermove',{movementX:20,movementY:20,target:canvas});check(fly.yaw===unlockedYaw,'Unlocked movement does not steer the camera');
    return passed;
  `;
  const source=support+helper[1]+['clearMovement','isTypingTarget','navigationBlocked','updateNavigationStatus','setNavigation','navKeyDown','navKeyUp'].map(line).join('\n')+'\n'+eventLines.join('\n')+'\n'+bindings+'\nreturn (async()=>{'+tests+'})();';
  return new Function('sourceHasAdditive',source)(/pick\(e\.clientX-r\.left,e\.clientY-r\.top,!!e\.shiftKey\)/.test(html));
}
if(typeof module!=='undefined'){
  module.exports={runMouseLookTests};
  if(require.main===module){const fs=require('node:fs');runMouseLookTests(fs.readFileSync(process.argv[2],'utf8')).then(passed=>console.log(JSON.stringify({method:'Actual mouse-look code and pointer handlers in a browserless JS harness; native capture/rendering untested.',passed},null,2))).catch(e=>{console.error(e);process.exitCode=1;});}
}

