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
  const findId=(node,id)=>node.id===id?node:node.children.map(c=>findId(c,id)).find(Boolean);
  const nodes=new Map();document={root:new Element(),hidden:false,activeElement:null,getElementById:id=>nodes.get(id)||findId(document.root,id),createElement:tag=>new Element(tag),addEventListener:(k,f)=>(listeners[k]??=[]).push(f),querySelector:tag=>nodes.get(tag)};
  const ids=[...source.matchAll(/\$\('([^']+)'\)/g)].map(m=>m[1]);ids.push('model-data','header','main','scene','labels','orbitNav','freeNav');
  for(const id of new Set(ids)){if(id==='cutDetail')continue;const el=new Element(id==='scene'?'canvas':id==='search'?'input':/Button|closeSchedule|Nav$/.test(id)?'button':'div');el.id=id;nodes.set(id,el);document.root.appendChild(el);}
  nodes.get('scheduleModal').append(nodes.get('closeSchedule'),nodes.get('scheduleNote'),nodes.get('scheduleHead'),nodes.get('scheduleRows'));
  nodes.get('main').append(nodes.get('scene'));nodes.get('model-data').textContent=JSON.stringify(model);
  document.activeElement=nodes.get('scene');
  const window={devicePixelRatio:1,location:{hash:''},addEventListener:(k,f)=>(windowListeners[k]??=[]).push(f)};
  let queued=[];const requestAnimationFrame=f=>{queued.push(f);};
  const assertions=[];
  const tests=`
    const check=(condition,message)=>{if(!condition)throw Error(message);assertions.push(message);};
    const key=(value,target=$('freeNav'),extra={})=>({key:value,target,shiftKey:false,preventDefault(){this.prevented=true;},...extra});
    const walk=el=>[el,...el.children.flatMap(walk)];
    const expectedDefault=parts.filter(p=>defaultGroups().some(g=>g.id===p.group));
    check(parts.filter(isTimber).length===96,'R01 retains 96 timber IDs');
    check(parts.filter(p=>p.group==='radial_rafters').length===8&&parts.filter(p=>p.group==='secondary_approx').length===16,'Roof contains eight hips and sixteen short rafters');
    check(!parts.some(p=>/^J[0-7]-1$/.test(p.id)),'All eight midpoint rafters are retired');
    check(!parts.some(p=>p.temporary&&isShown(p)),'Temporary fixture is hidden initially');
    check(parts.filter(isShown).length===expectedDefault.length,'Initial view respects current default group visibility');
    setNavigation('free');$('freeNav').focus();const before=fly.eye.slice();const w=key('w');navKeyDown(w);check(navKeys.has('w')&&w.prevented,'WASD works after a viewer button');advanceFly(.05);check(length(vsub(fly.eye,before))>0,'Travel changes the camera');navKeyUp(key('w'));check(navKeys.size===0,'Key release stops travel');
    $('search').focus();const typed=key('w',$('search'));navKeyDown(typed);check(navKeys.size===0&&!typed.prevented,'Typing does not move camera');
    const nested=document.createElement('span'),editable=document.createElement('div');editable.setAttribute('contenteditable','true');editable.append(nested);check(isTypingTarget(nested),'Nested editable content blocks navigation');
    $('search').focus();$('freeNav').onclick();check(document.activeElement===canvas,'Free mode releases previous input focus');
    const shortcut=key('w',canvas,{ctrlKey:true});navKeyDown(shortcut);check(navKeys.size===0&&!shortcut.prevented,'Ctrl+W remains a browser shortcut');
    renderList();let button=$('partList').querySelectorAll('[data-focus-key]').find(x=>x.dataset.focusKey==='select:P0');button.focus();selectPart('P0');check(document.activeElement.dataset.focusKey==='select:P0'&&document.activeElement.isConnected,'Piece selection retains keyboard focus');
    let tick=$('partList').querySelectorAll('[data-focus-key]').find(x=>x.dataset.focusKey==='show:P0');tick.focus();tick.checked=false;tick.events.change[0]();check(document.activeElement.dataset.focusKey==='show:P0'&&!isShown(partById.get('P0')),'Visibility toggle retains focus and hides its member');
    const trigger=$('scheduleButton');trigger.focus();openSchedule();check(document.querySelector('main').inert&&document.activeElement===$('closeSchedule'),'Schedule isolates focus from background');
    const scheduleButtons=$('scheduleModal').querySelectorAll('button');check(scheduleButtons.length===parts.length+1,'Schedule has one inspection button per component');
    scheduleButtons.at(-1).focus();const tab={key:'Tab',shiftKey:false,preventDefault(){this.prevented=true;}};for(const f of listeners.keydown||[])f(tab);check(tab.prevented&&document.activeElement===$('closeSchedule'),'Tab wraps at end of schedule');
    const escape={key:'Escape',preventDefault(){}};for(const f of listeners.keydown||[])f(escape);check(!document.querySelector('main').inert&&document.activeElement===trigger,'Escape restores schedule focus and background');
    const joint=cuts.find(f=>f.part_id==='J0-0'&&!f.reference&&f.mate_part_id==='R0');check(!!joint,'R01 short rafter has hip contact face');
    for(const part of parts.filter(isTimber)){const sf=stockFrame(part),source=part.stock_frame;check(!!sf&&!!source&&['axis','width','depth'].every(k=>length(vsub(sf[k],unit(source[k])))<1e-9),'Explicit stock axes retained for '+part.id);}
    const alpha=Math.PI/8,pn=(1/3)/Math.cos(alpha),expectedOffSquare=Math.acos(Math.sin(alpha)/Math.sqrt(1+pn*pn))*180/Math.PI;
    check(Math.abs(surfaceAngles(partById.get('J0-0'),joint).offSquare-expectedOffSquare)<1e-7,'J0-0 hip-side compound contact angle agrees with independent octagon slope geometry');
    selectCut(joint);faceCut(joint);check(inspectionPartId==='J0-0'&&inspectionCutId===joint.id&&length(vsub(inspectionPivot,vadd(joint.center,cutOffset(joint))))<1e-9,'Cut inspection uses actual contact plane center');
    setNavigation('free');inspectEnd(partById.get('P0'),'A');check(inspectionCutId===null&&inspectionPartId==='P0'&&Number.isFinite(fly.yaw)&&Number.isFinite(fly.pitch),'End A resets cut pivot and handles vertical member');inspectEnd(partById.get('R0'),'B');check(flySpeed===.02&&inspectionPartId==='R0','End B uses fine travel speed');
    const verticalAngles=recordedAngles(partById.get('P0'));
    check(verticalAngles.find(r=>r[0]==='Plan direction in model X/Z')[1].includes('Not applicable'),'Vertical plan direction is not invented as zero');
    check(verticalAngles.filter(r=>r[0].startsWith('Fabrication')).every(r=>r[1]==='Unresolved'),'Unavailable fabrication angles remain unresolved');
    check(cuts.every(f=>{const a=surfaceAngles(partById.get(f.part_id),f);return Number.isFinite(a.offSquare)&&a.offSquare>=0&&a.offSquare<=90&&Math.abs(a.offSquare+a.planeToAxis-90)<1e-8;}),'All contact and reference faces expose finite complementary plane angles');
    selectPart('J0-0');const angleRows=walk($('selection')).filter(el=>el.tagName==='TR'&&el.dataset.cutId);
    check(angleRows.length===cuts.filter(f=>f.part_id==='J0-0').length,'Selected rafter exposes all contact and reference angle rows');
    angleRows.at(-1).children[0].children[0].focus();angleRows.at(-1).children[0].children[0].onclick();check(selectedCut===angleRows.at(-1).dataset.cutId,'Angle row selects exact face ID');check(document.activeElement.dataset.cutId===selectedCut&&document.activeElement.isConnected,'Angle inspection preserves keyboard focus');
    const inventory=MATERIALS.groups.flatMap(g=>g.member_ids);
    check(inventory.length===parts.length&&new Set(inventory).size===parts.length&&parts.every(p=>inventory.includes(p.id)),'Materials inventory covers current components exactly once');
    check(MATERIALS.groups.every(g=>g.quantity===g.member_ids.length),'Material quantities agree with membership');
    $('materialsButton').focus();openMaterials();check($('scheduleRows').children.length===MATERIALS.groups.length,'Materials dialog lists current groups');
    check($('scheduleRows').querySelectorAll('button').length===parts.length,'Materials includes an inspection button for every component');
    check(inventory.every(id=>materialsCSV().includes(id)),'Materials CSV includes current IDs');closeSchedule();check(document.activeElement===$('materialsButton'),'Materials dialog restores focus');
    setNavigation('orbit');$('allPermanent').onclick();explode=0;selectPart('P0');selectPart('B0',true);
    check(selectedPartIds.size===2&&selectionAlpha(partById.get('R0'))===.14,'Shift selection ghosts unrelated members');
    selectPart('B0',true);check(selectedPartIds.size===1&&selected==='P0','Shift click toggles membership');selectPart('P0',true);check(selected===null&&selectedPartIds.size===0,'Last-member toggle clears selection');
    showMatingPair(joint);check(selectedPartIds.size===2&&selectedPartIds.has('J0-0')&&selectedPartIds.has('R0')&&parts.filter(isShown).length===2,'Contact pair view isolates rafter and receiving hip');
    faceCut(joint);check(selectedPartIds.size===1&&selectedPartIds.has('J0-0'),'Contact-face inspection selects only its owner');
    $('reviewCorner').onclick();check(parts.filter(isShown).map(p=>p.id).sort().join(',')===['R0','J0-0','J7-2'].sort().join(','),'Rafter-joint shortcut shows both rafters at R0');
    check(selected==='J0-0'&&navigation==='orbit'&&showCutFaces,'Rafter-joint shortcut activates contact inspection');
    check(length(vsub(camera.target,joint.center))<1e-9,'Rafter-joint shortcut centers actual contact plane');
    $('roofPlan').onclick();check(camera.phi>1.5&&parts.filter(isShown).filter(p=>p.group==='secondary_approx').length===16,'Roof-plan shortcut shows all sixteen short rafters from above');
    check(!parts.some(p=>p.temporary&&isShown(p)),'Roof-plan shortcut excludes temporary fixture');
    $('restoreFrame').onclick();check(selected===null&&selectedCut===null&&selectedPartIds.size===0&&inspectionPivot===null,'Restore frame clears selection and inspection pivots');
    check(parts.filter(isShown).length===expectedDefault.length&&isolatedId===null,'Restore frame follows current default groups');
    check(!$('cornerFindings').open&&$('cornerContext').hidden,'Restore frame exits joint context');
    return assertions;
  `;
  const run=new Function('document','window','requestAnimationFrame','setTimeout','ResizeObserver','assertions','windowListeners','listeners',source+'\n'+tests);
  return run(document,window,requestAnimationFrame,()=>{},undefined,assertions,windowListeners,listeners);
}
if(typeof module!=='undefined'){
  module.exports={runViewerTests};
  if(require.main===module){const fs=require('node:fs');const html=fs.readFileSync(process.argv[2]||'index.html','utf8');const model=JSON.parse(html.match(/<script[^>]*id="model-data"[^>]*>([\s\S]*?)<\/script>/)[1]);const source=html.split("<script>\n'use strict';\n")[1].split('</script>')[0];console.log(JSON.stringify({passed:runViewerTests(source,model)},null,2));}
}

