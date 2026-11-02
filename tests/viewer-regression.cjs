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
    check(labelsOn===false,'Model labels default off');
    const verticalAngles=recordedAngles(partById.get('P0'));
    check(verticalAngles.find(r=>r[0]==='Plan direction in model X/Z')[1].includes('Not applicable'),'Vertical plan direction is not invented as zero');
    check(verticalAngles.filter(r=>r[0].startsWith('Fabrication')).every(r=>r[1]==='Unresolved'),'Unavailable fabrication angles stay unresolved');
    const b0=partById.get('B0'),b0ref=cuts.find(f=>f.id==='B0-A'),ba=surfaceAngles(b0,b0ref);
    check(Math.abs(ba.offSquare-22.5)<.001&&Math.abs(ba.yaw-22.5)<.001&&Math.abs(ba.tilt)<.001,'B0 reference has independently expected 22.5 degree miter and zero depth tilt');
    check(recordedAngles(b0).find(r=>r[0]==='Reference vertical bevel')[1]==='0.00°','A recorded zero bevel stays numeric');
    const sf=stockFrame(partById.get('P0'));
    check(length(vsub(sf.width,[1,0,0]))<1e-6&&length(vsub(sf.depth,[0,0,-1]))<1e-6,'Vertical post stock frame follows the saved cap edge');
    check(stockFrame({...b0,reference_end_faces:[]})===null,'Missing stock frame remains unavailable');
    const alongDepth=surfaceAngles(partById.get('P0'),{normal:sf.depth});
    check(alongDepth.yaw===null&&Math.abs(alongDepth.tilt-90)<1e-6,'Depth-only plane normal has undefined yaw');
    check(cuts.every(f=>{const a=surfaceAngles(partById.get(f.part_id),f);return Number.isFinite(a.offSquare)&&a.offSquare>=0&&a.offSquare<=90&&Math.abs(a.offSquare+a.planeToAxis-90)<1e-8;}),'All fitted and reference surfaces have finite complementary plane angles');
    selectPart('R0');const walk=el=>[el,...el.children.flatMap(walk)];
    const angleRows=walk($('selection')).filter(el=>el.tagName==='TR'&&el.dataset.cutId);
    check(angleRows.length===cuts.filter(f=>f.part_id==='R0').length,'Selection exposes an angle row for every cut and end reference');
    angleRows.at(-1).children[0].children[0].focus();angleRows.at(-1).children[0].children[0].onclick();check(selectedCut===angleRows.at(-1).dataset.cutId,'Angle row selects its exact original cut ID');
    check(document.activeElement.dataset.cutId===selectedCut&&document.activeElement.isConnected,'Angle inspection preserves its keyboard focus after rebuilding');
    check($('cutDetail').parentElement.open===true,'Selected cut details open immediately');
    const inventory=MATERIALS.groups.flatMap(g=>g.member_ids);
    check(MATERIALS.groups.length===13&&MATERIALS.groups.every((g,i)=>g.id==='M'+String(i+1).padStart(2,'0')&&g.quantity===8),'Materials types are stably numbered with verified quantities');
    check(inventory.length===104&&new Set(inventory).size===104&&parts.every(p=>inventory.includes(p.id)),'Materials inventory covers all original IDs exactly once');
    check(new Set(['L0-L','L0-S','L0-H'].map(id=>materialByPart.get(id).id)).size===3&&materialByPart.get('K0-A')!==materialByPart.get('K0-B')&&materialByPart.get('J0-0')!==materialByPart.get('J0-2'),'Distinct cupola cuts and handed families are not merged');
    $('materialsButton').focus();openMaterials();check($('scheduleRows').children.length===13,'Materials dialog lists every fitted-shape group');
    const materialButtons=$('scheduleRows').querySelectorAll('button');check(materialButtons.length===104,'Every numbered materials entry retains an inspection button');
    check(materialsCSV().split('\\r\\n').length===14&&inventory.every(id=>materialsCSV().includes(id)),'Materials CSV uses the same groups and IDs as the dialog');
    closeSchedule();check(document.activeElement===$('materialsButton'),'Materials dialog restores its trigger focus');
    openSchedule();check($('scheduleRows').children.length===104,'Individual schedule still works after grouped materials');closeSchedule();
    setNavigation('orbit');$('allPermanent').onclick();explode=0;selectPart('P0');selectPart('B0',true);
    check(selectedPartIds.size===2&&selected==='B0'&&selectionAlpha(partById.get('P0'))===1&&selectionAlpha(b0)===1&&selectionAlpha(partById.get('R0'))===.14,'Shift selection highlights both members and ghosts the rest');
    check(length(vsub(camera.target,selectedSetBounds().center))<1e-8,'Shift selection frames the selected bounds');
    selectCut(cuts.find(f=>f.part_id==='B0'&&!f.reference));check(selectedPartIds.size===2,'Inspecting a selected cut preserves the selected set');
    selectPart('B0',true);check(selectedPartIds.size===1&&selected==='P0','Shift-click toggles membership and keeps a valid primary');
    selectPart('P0',true);check(selected===null&&selectedPartIds.size===0,'Toggling the last member clears selection');
    selectPart('P0');selectPart('B0',true);selectPart('R0');check(selectedPartIds.size===1&&selectedPartIds.has('R0')&&selectionAlpha(b0)===1,'Plain click replaces multi-selection and restores opacity');
    selectPart('P0');selectPart('B0',true);const pairFace=cuts.find(f=>f.part_id==='B0'&&f.mate_part_id&&partById.has(f.mate_part_id));
    showMatingPair(pairFace);check(selectedPartIds.size===2&&selectedPartIds.has(pairFace.part_id)&&selectedPartIds.has(pairFace.mate_part_id)&&parts.filter(isShown).length===2,'Related-pair view synchronizes its exact selected set');
    faceCut(pairFace);check(selectedPartIds.size===1&&selectedPartIds.has(pairFace.part_id)&&parts.filter(isShown).length===1,'Isolate-cut view synchronizes its single selected owner');
    $('reviewCorner').onclick();
    check(parts.filter(isShown).map(p=>p.id).sort().join(',')===['P0','B7','B0','T0','R0'].sort().join(','),'P0 investigation button shows exactly its five original timber IDs');
    check(selected==='R0'&&selectedPartIds.size===1&&selectedPartIds.has('R0')&&navigation==='orbit','P0 investigation activates R0 and exits previous isolation/navigation state');
    const cornerPost=partById.get('P0'),cornerTarget=[cornerPost.axis_end[0],cornerPost.axis_end[1]+.1,cornerPost.axis_end[2]];
    check(length(vsub(camera.target,cornerTarget))<1e-9&&Math.abs(camera.distance-1.7)<1e-9&&length(vsub(inspectionPivot,cornerTarget))<1e-9,'P0 investigation frames the post-top joint at a 1.7 metre viewing distance');
    check($('cornerFindings').open===true&&!$('cornerContext').hidden&&$('cornerContext').textContent.includes('active R0'),'P0 investigation opens its findings and shows the active corner context');
    check($('reviewDetail').children.map(el=>el.textContent).join(' ').includes(JOINERY_REVIEW.representative_corner.finding),'P0 investigation retains its recorded geometric conflict finding');
    const inspectorChildren=$('selection').children,actionIndex=inspectorChildren.findIndex(el=>el.classList.contains('selection-actions')),metricIndex=inspectorChildren.findIndex(el=>el.classList.contains('metric'));
    check(actionIndex>=0&&metricIndex>actionIndex,'Selected-timber actions appear before dimensional metrics');
    const inspectorSurface=()=>walk($('selection')).find(el=>el.tagName==='DETAILS'&&el.dataset.inspectorKey==='surfaceAngles');
    const cutForDisclosure=cuts.find(c=>c.part_id==='R0'&&!c.reference);
    let surfaceDisclosure=inspectorSurface();surfaceDisclosure.open=true;canvas.focus();selectCut(cutForDisclosure);
    check(inspectorSurface()!==surfaceDisclosure&&inspectorSurface().open===true,'Open cut-plane angle disclosure survives selected-cut inspector rebuild');
    surfaceDisclosure=inspectorSurface();surfaceDisclosure.open=false;canvas.focus();selectCut(cutForDisclosure);
    check(inspectorSurface()!==surfaceDisclosure&&inspectorSurface().open===false,'Closed cut-plane angle disclosure stays closed when focus is elsewhere');
    const keyboardCut=walk($('selection')).find(el=>el.tagName==='BUTTON'&&el.dataset.cutId===cutForDisclosure.id);
    for(let ancestor=keyboardCut.parentElement;ancestor&&ancestor!==$('selection');ancestor=ancestor.parentElement)if(ancestor.tagName==='DETAILS')ancestor.open=false;
    keyboardCut.focus();keyboardCut.onclick();
    const restoredAncestors=[];for(let ancestor=document.activeElement.parentElement;ancestor&&ancestor!==$('selection');ancestor=ancestor.parentElement)if(ancestor.tagName==='DETAILS')restoredAncestors.push(ancestor);
    check(document.activeElement!==keyboardCut&&document.activeElement.isConnected&&document.activeElement.dataset.cutId===cutForDisclosure.id,'Keyboard cut activation restores focus to the matching rebuilt control');
    check(restoredAncestors.length>0&&restoredAncestors.every(el=>el.open===true),'Keyboard cut focus reopens every containing inspector disclosure');
    canvas.focus();selectCut(cutForDisclosure);check(inspectorSurface().open===true,'Disclosure opened for keyboard focus remains open on the next rebuild');
    $('restoreFrame').onclick();
    check(selected===null&&selectedCut===null&&selectedPartIds.size===0&&inspectionPartId===null&&inspectionCutId===null&&inspectionPivot===null,'Restore full frame clears active selection and inspection pivots');
    check(parts.filter(isShown).length===104&&hiddenPieces.size===0&&isolatedId===null,'Restore full frame reveals all 104 original permanent timbers');
    check($('cornerContext').hidden&&$('cornerFindings').open===false,'Restore full frame exits the corner investigation context');
    return assertions;
  `;
  const run=new Function('document','window','requestAnimationFrame','setTimeout','ResizeObserver','assertions','windowListeners','listeners',source+'\n'+tests);
  return run(document,window,requestAnimationFrame,()=>{},undefined,assertions,windowListeners,listeners);
}
if(typeof module!=='undefined'){
  module.exports={runViewerTests};
  if(require.main===module){const fs=require('node:fs');const html=fs.readFileSync(process.argv[2]||'index.html','utf8');const model=JSON.parse(html.match(/<script[^>]*id="model-data"[^>]*>([\s\S]*?)<\/script>/)[1]);const source=html.split("<script>\n'use strict';\n")[1].split('</script>')[0];console.log(JSON.stringify({passed:runViewerTests(source,model)},null,2));}
}
