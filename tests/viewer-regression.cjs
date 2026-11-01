// Browserless regression harness. Uses the actual viewer script with a small DOM stub.
// Node: node viewer-regression.js [index.html]; exports runViewerTests for other JS runtimes.
function runViewerTests(source,model){
  let document;
  const listeners={},windowListeners={};
  class Element{
    constructor(tag='div'){this.tagName=tag.toUpperCase();this.children=[];this.parentElement=null;this.dataset={};this.style={};this.attributes={};this._classes=new Set();this.textContent='';this.value='';this.hidden=false;this.inert=false;this.events={};this.offsetWidth=100;this.offsetHeight=20;this.classList={add:(...s)=>s.forEach(x=>this._classes.add(x)),remove:(...s)=>s.forEach(x=>this._classes.delete(x)),contains:s=>this._classes.has(s)};}
    get className(){return [...this._classes].join(' ');}set className(s){this._classes=new Set(s.split(/\s+/).filter(Boolean));}
    get isConnected(){return this===document.root||!!this.parentElement?.isConnected;}
    appendChild(n){if(n.parentElement)n.parentElement.children=n.parentElement.children.filter(c=>c!==n);this.children.push(n);n.parentElement=this;return n;}
    append(...nodes){nodes.forEach(n=>this.appendChild(n));}
    replaceChildren(...nodes){this.children.forEach(n=>n.parentElement=null);this.children=[];this.append(...nodes);}
    contains(el){return this===el||this.children.some(c=>c.contains(el));}
    setAttribute(k,v){this.attributes[k]=String(v);}getAttribute(k){return this.attributes[k]??null;}
    addEventListener(k,f){(this.events[k]??=[]).push(f);}
    focus(){document.activeElement=this;for(const f of listeners.focusin||[])f({target:this});}
    getBoundingClientRect(){return {width:900,height:650,left:0,top:0};}
    getContext(){return null;}setPointerCapture(){}
    querySelectorAll(selector){const out=[];const match=n=>selector==='[data-focus-key]'?!!n.dataset.focusKey:selector.includes('button')?n.tagName==='BUTTON'&&!n.disabled:false;const walk=n=>{for(const c of n.children){if(match(c))out.push(c);walk(c);}};walk(this);return out;}
  }
  const nodes=new Map();document={root:new Element(),hidden:false,activeElement:null,getElementById:id=>nodes.get(id),createElement:tag=>new Element(tag),addEventListener:(k,f)=>(listeners[k]??=[]).push(f),querySelector:tag=>nodes.get(tag)};
  const ids=[...source.matchAll(/\$\('([^']+)'\)/g)].map(m=>m[1]);ids.push('model-data','header','main','scene','labels','orbitNav','freeNav');
  for(const id of new Set(ids)){const el=new Element(id==='scene'?'canvas':id==='search'?'input':/Button|closeSchedule|Nav$/.test(id)?'button':'div');el.id=id;nodes.set(id,el);document.root.appendChild(el);}
  nodes.get('scheduleModal').append(nodes.get('closeSchedule'),nodes.get('scheduleRows'));
  nodes.get('main').append(nodes.get('scene'));nodes.get('model-data').textContent=JSON.stringify(model);
  document.activeElement=nodes.get('scene');
  const window={devicePixelRatio:1,location:{hash:''},addEventListener:(k,f)=>(windowListeners[k]??=[]).push(f)};
  let queued=[];const requestAnimationFrame=f=>{queued.push(f);};
  const assertions=[];
  const tests=`
    const check=(condition,message)=>{if(!condition)throw Error(message);assertions.push(message);};
    const key=(value,target=$('freeNav'),extra={})=>({key:value,target,shiftKey:false,preventDefault(){this.prevented=true;},...extra});
    const press=e=>navKeyDown(e);
    setNavigation('free');$('freeNav').focus();const before=fly.eye.slice();const w=key('w');press(w);check(navKeys.has('w')&&w.prevented,'WASD works after a viewer button');advanceFly(.05);check(length(vsub(fly.eye,before))>0,'Travel changes the camera');navKeyUp(key('w'));check(navKeys.size===0,'Key release stops travel');
    $('search').focus();const typed=key('w',$('search'));press(typed);check(navKeys.size===0&&!typed.prevented,'Typing keeps W and does not move camera');
    const nested=document.createElement('span'),editable=document.createElement('div');editable.setAttribute('contenteditable','true');editable.append(nested);check(isTypingTarget(nested),'Nested editable content blocks navigation');
    $('search').focus();$('freeNav').onclick();check(document.activeElement===canvas,'Free / WASD explicitly releases previous input focus');
    const shortcut=key('w',canvas,{ctrlKey:true});press(shortcut);check(navKeys.size===0&&!shortcut.prevented,'Ctrl+W remains a browser shortcut');
    $('freeNav').focus();press(key('w'));for(const f of windowListeners.blur||[])f();check(navKeys.size===0,'Window blur clears held movement');for(const f of windowListeners.focus||[])f();
    renderList();let button=$('partList').querySelectorAll('[data-focus-key]').find(x=>x.dataset.focusKey==='select:P0');button.focus();selectPart('P0');check(document.activeElement.dataset.focusKey==='select:P0'&&document.activeElement.isConnected,'Piece selection retains keyboard focus after list rebuild');
    let tick=$('partList').querySelectorAll('[data-focus-key]').find(x=>x.dataset.focusKey==='show:P0');tick.focus();tick.checked=false;tick.events.change[0]();check(document.activeElement.dataset.focusKey==='show:P0'&&!isShown(partById.get('P0')),'Piece visibility toggle retains focus and hides its member');
    const trigger=$('scheduleButton');trigger.focus();openSchedule();check(document.querySelector('main').inert&&document.activeElement===$('closeSchedule'),'Schedule isolates focus from background');
    const scheduleButtons=$('scheduleModal').querySelectorAll('button');check(scheduleButtons.length===105,'Schedule provides a real inspection button for all 104 IDs');
    scheduleButtons.at(-1).focus();const tab={key:'Tab',shiftKey:false,preventDefault(){this.prevented=true;}};for(const f of listeners.keydown||[])f(tab);check(tab.prevented&&document.activeElement===$('closeSchedule'),'Tab wraps at end of schedule');
    const shiftTab={key:'Tab',shiftKey:true,preventDefault(){this.prevented=true;}};for(const f of listeners.keydown||[])f(shiftTab);check(shiftTab.prevented&&document.activeElement===scheduleButtons.at(-1),'Shift-Tab wraps at start of schedule');
    const escape={key:'Escape',preventDefault(){}};for(const f of listeners.keydown||[])f(escape);check(!document.querySelector('main').inert&&document.activeElement===trigger,'Escape restores schedule focus and background');
    openSchedule();$('scheduleModal').onclick({target:$('scheduleModal')});check(document.activeElement===trigger,'Backdrop close restores focus');
    openSchedule();$('scheduleModal').querySelectorAll('button')[2].onclick();check(selected==='B0'&&document.activeElement===canvas&&!$('scheduleModal').classList.contains('open'),'Schedule inspection selects correct ID and focuses canvas');
    focusPart(partById.get('P0'));const f=cuts.find(c=>c.part_id==='R0'&&!c.reference);selectCut(f);faceCut(f);const expected=vadd(f.center,cutOffset(f));check(inspectionPartId==='R0'&&inspectionCutId===f.id&&length(vsub(inspectionPivot,expected))<1e-9,'Cut inspection replaces stale member pivot');matrix();updatePieceCenter();check(length(vsub(inspectionPivot,expected))<1e-9,'Render keeps the cut pivot instead of overwriting it');setNavigation('orbit');check(length(vsub(camera.target,expected))<1e-9,'Free-to-orbit returns to inspected cut');
    setNavigation('free');inspectEnd(partById.get('P0'),'A');check(inspectionCutId===null&&inspectionPartId==='P0'&&Number.isFinite(fly.yaw)&&Number.isFinite(fly.pitch),'End A resets cut pivot and handles a vertical member');inspectEnd(partById.get('R0'),'B');check(flySpeed===.02&&inspectionPartId==='R0','End B uses fine travel speed');
    showReviewMembers(JOINERY_REVIEW.representative_corner.members);check(parts.filter(isShown).map(p=>p.id).sort().join(',')===['P0','B0','B7','T0','R0'].sort().join(','),'Representative corner shows exact existing timber IDs');
    check(parts.length===104&&new Set(parts.map(p=>p.id)).size===104,'All 104 timber IDs remain unique');
    return assertions;
  `;
  const run=new Function('document','window','requestAnimationFrame','setTimeout','ResizeObserver','assertions','windowListeners','listeners',source+'\n'+tests);
  return run(document,window,requestAnimationFrame,()=>{},undefined,assertions,windowListeners,listeners);
}
if(typeof module!=='undefined'){
  module.exports={runViewerTests};
  if(require.main===module){const fs=require('node:fs');const html=fs.readFileSync(process.argv[2]||'index.html','utf8');const model=JSON.parse(html.match(/<script[^>]*id="model-data"[^>]*>([\s\S]*?)<\/script>/)[1]);const source=html.split("<script>\n'use strict';\n")[1].split('</script>')[0];console.log(JSON.stringify({passed:runViewerTests(source,model)},null,2));}
}
