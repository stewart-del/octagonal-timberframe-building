// TIMESTAMP START 2026-11-01T23:19:38-05:00 | REVISION R004668
// TIMESTAMP START 2026-11-01T23:06:10-05:00 | REVISION R004659
// TIMESTAMP START 2026-11-01T23:01:05-05:00 | REVISION R004657
// Browserless regression harness. Uses the actual viewer script with a small DOM stub.
// Node: node viewer-regression.js [index.html]; exports runViewerTests for other JS runtimes.
function runViewerTests(source,model,{search='?model=baseline',skipLegacy=false}={}){
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
  const nodes=new Map();document={root:new Element(),hidden:false,activeElement:null,getElementById:id=>nodes.get(id)||findId(document.root,id),createElement:tag=>new Element(tag),createElementNS:(ns,tag)=>new Element(tag),addEventListener:(k,f)=>(listeners[k]??=[]).push(f),querySelector:tag=>nodes.get(tag)};
// TIMESTAMP START 2026-11-02T14:22:13-05:00 | REVISION R004792
  const ids=[...source.matchAll(/\$\('([^']+)'\)/g)].map(m=>m[1]);ids.push('layerMudroom','schematicWalls','schematicShelves','schematicCupolaWindows','layerFoundation','layerFloorStructure','layerFloorFinish','layerWallStructure','layerRoofCover','presetComplete','presetSkeleton','presetFoundation','presetFloor','plansTop','plansSide','model-data','header','main','scene','labels','orbitNav','freeNav');
// TIMESTAMP END 2026-11-02T14:22:13-05:00 | REVISION R004792
  for(const id of new Set(ids)){if(id==='cutDetail'||id==='isolatePiece')continue;const el=new Element(id==='scene'?'canvas':id==='search'?'input':/Button|closeSchedule|Nav$/.test(id)?'button':'div');el.id=id;nodes.set(id,el);document.root.appendChild(el);}
  nodes.get('scheduleModal').append(nodes.get('closeSchedule'),nodes.get('scheduleNote'),nodes.get('scheduleHead'),nodes.get('scheduleRows'));
  nodes.get('main').append(nodes.get('scene'));nodes.get('model-data').textContent=JSON.stringify(model);
  document.activeElement=nodes.get('scene');
  const window={devicePixelRatio:1,location:{hash:'',search,href:'https://viewer.test/'+search,assign(url){this.assigned=url;}},addEventListener:(k,f)=>(windowListeners[k]??=[]).push(f)};
  let queued=[];const requestAnimationFrame=f=>{queued.push(f);};
  const assertions=[];
  const tests=`
    const check=(condition,message)=>{if(!condition)throw Error(message);assertions.push(message);};
    const key=(value,target=$('freeNav'),extra={})=>({key:value,target,shiftKey:false,preventDefault(){this.prevented=true;},...extra});
    const walk=el=>[el,...el.children.flatMap(walk)];
    // TIMESTAMP START 2026-11-02T20:27:45-05:00 | REVISION R004866
const expectedDefault=parts.filter(p=>OctagonDisplayPresets.included(p,'complete'));
// TIMESTAMP END 2026-11-02T20:27:45-05:00 | REVISION R004866
// TIMESTAMP START 2026-11-02T15:07:59-05:00 | REVISION R004800
    check(parts.filter(isTimber).length===112,'Current frame includes 24 full-size braces and 112 primary timbers');
// TIMESTAMP END 2026-11-02T15:07:59-05:00 | REVISION R004800
    check(parts.filter(p=>p.group==='radial_rafters').length===8&&parts.filter(p=>p.group==='secondary_approx').length===16,'Roof contains eight hips and sixteen short rafters');
    check(!parts.some(p=>/^J[0-7]-1$/.test(p.id)),'All eight midpoint rafters are retired');
    // TIMESTAMP START 2026-11-02T20:27:45-05:00 | REVISION R004866
check(isShown(partById.get('M-TMP'))&&!isShown(partById.get('M-SP0')),'Complete shows the central welded fixture');
// TIMESTAMP END 2026-11-02T20:27:45-05:00 | REVISION R004866
    check(parts.filter(isShown).length===expectedDefault.length,'Initial view respects current default group visibility');
    check(schematicWallsEnabled&&schematicParts.filter(p=>!['deferred','temporary'].includes(OctagonDisplayPresets.role(p))).every(isShown),'Complete permanent building is visible by default without entering canonical inventory');
// TIMESTAMP START 2026-11-02T14:22:13-05:00 | REVISION R004792
    const mudroomPieces=schematicParts.filter(p=>p.schematicKind==='mudroom');
    check(mudroomPieces.length>20&&mudroomPieces.every(isShown),'Open porch is included in the default complete view');
    check(!mudroomCutaway&&mudroomPieces.filter(p=>p.mudroomScreen).every(isShown),'Porch roof starts visible');
    $('lookInsideMudroom').onclick();
    check(mudroomCutaway&&mudroomPieces.filter(p=>p.mudroomScreen).every(p=>!isShown(p))&&mudroomPieces.filter(p=>!p.mudroomScreen).every(isShown),'Roof control hides only the porch roof assembly');
    check(camera.target.every(Number.isFinite)&&camera.distance>0,'Mudroom view has a valid framing target');
    $('lookInsideMudroom').onclick();check(!mudroomCutaway&&mudroomPieces.every(isShown),'Roof control restores the entire porch');
    $('lookInsideMudroom').onclick();syncDisplayPreset();check($('displayPresetStatus').textContent==='Custom','Cutaway does not falsely report a complete building');
    applyDisplayPreset('complete');check(!mudroomCutaway&&mudroomPieces.every(isShown),'Complete from interior view restores the porch roof');
    $('lookInsideMudroom').onclick();$('resetView').onclick();check(!mudroomCutaway&&mudroomPieces.every(isShown),'Reset from interior view restores the porch roof');
    const bench=mudroomPieces.find(p=>p.mudroomRole==='furniture');
    check(!!bench,'Mudroom furniture exists');selectPart(bench.id);
    check(selected===bench.id&&selectedPartIds.has(bench.id)&&selectionAlpha(bench)===.38,'Mudroom pieces select and reveal transparent geometry');
    check(walk($('selection')).some(el=>el.textContent==='Active porch piece'),'Mudroom selection has a dedicated component inspector');
// TIMESTAMP START 2026-11-02T15:57:59-05:00 | REVISION R004811
    explode=.5/disassembly.count;check(mudroomPieces.every(isShown),'Porch solids stay visible throughout disassembly');
    check(mudroomPieces.some(p=>length(offset(p))>0)&&mudroomPieces.some(p=>length(offset(p))===0),'Released porch pieces move while later stages remain assembled');
// TIMESTAMP END 2026-11-02T15:57:59-05:00 | REVISION R004811
    explode=0;clearPieceSelection();
    selectedPartIds.add(bench.id);selectedPartIds.add('P0');selected='P0';selectPart('P0',true);
    check(selected===bench.id&&selectedPartIds.size===1,'Mixed timber/mudroom selection safely returns to the mudroom inspector');clearPieceSelection();
    // TIMESTAMP START 2026-11-02T20:19:08-05:00 | REVISION R004863
    // TIMESTAMP START 2026-11-03T07:01:25-05:00 | REVISION R004903
    applyDisplayPreset('skeleton');check(mudroomPieces.filter(p=>['framing','foundation','floor','stair'].includes(p.mudroomRole)).every(isShown)&&mudroomPieces.filter(p=>!['framing','foundation','floor','stair'].includes(p.mudroomRole)).every(p=>!isShown(p)),'Skeleton includes porch framing, full supports, floor and stairs');
    // TIMESTAMP END 2026-11-03T07:01:25-05:00 | REVISION R004903
    check(mudroomPieces.some(p=>p.id.startsWith('MUD-RAFTER-')&&isShown(p))&&mudroomPieces.some(p=>p.id.startsWith('MUD-BRACE-')&&isShown(p)),'Skeleton retains porch rafters and knee braces');
    // TIMESTAMP END 2026-11-02T20:19:08-05:00 | REVISION R004863
    applyDisplayPreset('complete');check(mudroomPieces.every(isShown),'Complete restores the whole porch');
// TIMESTAMP START 2026-11-03T07:02:34-05:00 | REVISION R004905
    for(const id of ['PIER-0','PIER-C','MUD-SUPPORT-L-BACK']){
      const top=partById.get(id),below=partById.get(id+'-BELOW');selectPart(below.id);
      check(selected===id&&selectedPartIds.size===1&&isSelectedMember(top)&&isSelectedMember(below),'Either visible zone selects one whole column '+id);
      check(selectionAlpha(below)===.28,'Buried column remains transparent when selected '+id);
      const box=selectedSetBounds();check(box.members.length===2&&box.max[1]-box.min[1]>6*.3048,'Selection bounds include full column '+id);
      togglePieceIsolation(top);check(isShown(top)&&isShown(below)&&!isShown(partById.get('P0')),'Isolation retains both column zones '+id);
      check(Math.abs(inspectionPivot[1]-box.center[1])<1e-9,'Column focus centers full height '+id);
      applyDisplayPreset('complete');selectPart(top.id);selectPart(below.id,true);check(selectedPartIds.size===0,'Shift-click either zone toggles one whole column '+id);
      selectPart(below.id,true);check(inspectionPartId===id,'Shift-select one logical column retains a following focus pivot '+id);clearPieceSelection();
    }
    clearPieceSelection();applyDisplayPreset('complete');

// TIMESTAMP END 2026-11-03T07:02:34-05:00 | REVISION R004905
    // TIMESTAMP START 2026-11-03T07:08:54-05:00 | REVISION R004911
    fitModel();matrix();check(camera.target.every((v,i)=>Math.abs(v-interiorCenter()[i])<1e-9),'Default orbit center is the interior octagonal room center');
    check([...parts,...schematicParts].filter(isShown).every(p=>p.vertices.every(v=>{const q=project(vadd(v,offset(p)));return q&&q.x>0&&q.x<width&&q.y>0&&q.y<height;})),'Default perspective contains every visible building vertex, including porch, stairs and buried columns');
    // TIMESTAMP END 2026-11-03T07:08:54-05:00 | REVISION R004911
    const porchPlan=OctagonPlans.drawing(PLAN_DATA,{view:'top',mudroom:true,roofCover:false});
    check(porchPlan.parts.some(p=>p.id==='MUD-BENCH-L')&&porchPlan.parts.some(p=>p.mudroomRole==='drain'),'Porch plan contains benches and drain');
    // TIMESTAMP START 2026-11-02T22:10:21-05:00 | REVISION R004884
    check(!porchPlan.parts.some(p=>p.roofLayer)&&porchPlan.parts.some(p=>p.id==='MUD-RAFTER-L-2'),'Porch drawings retain roof framing when covering layers are off');
    // TIMESTAMP END 2026-11-02T22:10:21-05:00 | REVISION R004884
    const roofedPlan=OctagonPlans.drawing(PLAN_DATA,{view:'top',mudroom:true,roofCover:true});
    check(roofedPlan.parts.some(p=>p.id==='MUD-ROOF'),'Roofed plan includes the porch roof');
    const withoutPorch=OctagonPlans.drawing(PLAN_DATA,{view:'top',mudroom:false});
    check(!withoutPorch.parts.some(p=>p.schematicKind==='mudroom'),'Porch plan toggle excludes the addition independently');
// TIMESTAMP END 2026-11-02T14:22:13-05:00 | REVISION R004792
    for(const binding of Object.values(displayLayerBindings)){binding[2](false);}syncDisplayControls();
    check(schematicParts.every(p=>fittedCenter(p).every(Number.isFinite)),'Schematic centers support ghost sorting during multi-selection');
    const canonicalCount=parts.length;
    matrix();$('layerWallStructure').checked=true;$('layerWallStructure').onchange();$('schematicWalls').checked=true;$('schematicWalls').onchange();updateSchematicWalls();
    check(schematicParts.filter(p=>['wall','rail','footer'].includes(p.schematicKind)).every(isShown)&&schematicParts.filter(p=>!['wall','rail','footer'].includes(p.schematicKind)).every(p=>!isShown(p))&&parts.length===canonicalCount,'Wall toggle displays only separate provisional layer, not timber/load members');
    // TIMESTAMP START 2026-11-02T13:49:06-05:00 | REVISION R004787
// TIMESTAMP START 2026-11-02T15:57:59-05:00 | REVISION R004811
    explode=.5;updateSchematicWalls();check(schematicParts.filter(p=>layerShown(p)).every(isShown),'Active enclosure layers stay visible during the verified sequence');
// TIMESTAMP END 2026-11-02T15:57:59-05:00 | REVISION R004811
    // TIMESTAMP END 2026-11-02T13:49:06-05:00 | REVISION R004787
    explode=0;isolatedId='P0';check(schematicParts.every(p=>!isShown(p)),'Wall layer stays out of isolated joint inspection');
    isolatedId=null;$('layerWallStructure').checked=false;$('layerWallStructure').onchange();$('schematicWalls').checked=false;$('schematicWalls').onchange();updateSchematicWalls();
    check(schematicParts.every(p=>!isShown(p))&&schematicLabels.every(x=>x.el.style.display==='none'),'Wall toggle off clears geometry and compass labels');
    $('schematicShelves').checked=true;$('schematicShelves').onchange();
    check(schematicParts.filter(p=>p.schematicKind==='shelf').every(isShown)&&schematicParts.filter(p=>p.schematicKind!=='shelf').every(p=>!isShown(p)),'Shelves remain visible with walls and cupola windows off');
    $('schematicCupolaWindows').checked=true;$('schematicCupolaWindows').onchange();
    check(schematicParts.filter(p=>p.schematicKind==='cupolaWindow').every(isShown),'Cupola windows have their own independent toggle');
    $('schematicShelves').checked=false;$('schematicShelves').onchange();
    check(schematicParts.filter(p=>p.schematicKind==='cupolaWindow').every(isShown)&&schematicParts.filter(p=>p.schematicKind==='shelf').every(p=>!isShown(p)),'Turning shelves off preserves cupola windows');
    $('schematicCupolaWindows').checked=false;$('schematicCupolaWindows').onchange();
    $('schematicFloor').checked=true;$('schematicFloor').onchange();check(schematicParts.filter(p=>['floor','floorAssembly'].includes(p.schematicKind)).every(isShown)&&schematicParts.filter(p=>!['floor','floorAssembly'].includes(p.schematicKind)).every(p=>!isShown(p)),'Complete floor and nine piers have an independent toggle with all walls/shelves/windows off');
    check(!schematicParts.some(p=>['grate','footer'].includes(p.schematicKind)),'Deferred grate and legacy short footers are absent from active model');
    // TIMESTAMP START 2026-11-02T20:27:45-05:00 | REVISION R004866
// TIMESTAMP START 2026-11-03T12:11:15-05:00 | REVISION R005013
check(schematicParts.filter(p=>p.id.startsWith('PIER-')&&!p.underground).length===17&&schematicParts.filter(p=>p.id.startsWith('PIER-')&&p.underground).length===17,'Seventeen piers have six-foot underground extensions');
// TIMESTAMP END 2026-11-03T12:11:15-05:00 | REVISION R005013
    check(schematicParts.filter(p=>p.underground).every(p=>selectionAlpha(p)===.28),'Underground columns are translucent');
// TIMESTAMP END 2026-11-02T20:27:45-05:00 | REVISION R004866
    $('pierSettingOut').onclick();check($('pierModal').classList.contains('open')&&$('pierDrawing').innerHTML.includes('PIER-C'),'Setting-out button opens current nine-center SVG');
    $('closePierModal').onclick();check(!$('pierModal').classList.contains('open'),'Setting-out close restores scene');
    openPierSettingOut('PIER-3');check($('pierTitle').textContent.includes('PIER-3'),'Selected pier opens identifiable setting-out screen');closePierSettingOut();
    $('schematicFloor').checked=false;$('schematicFloor').onchange();
    const panel=parts.find(p=>p.id==='PLY');
    check(parts.filter(p=>p.group==='cupola_plywood').length===1&&!!panel,'Plywood is one selectable assembly, not eight display sectors');
// TIMESTAMP START 2026-11-02T15:57:59-05:00 | REVISION R004811
    check(panel.exploded_offset.join(',')==='0,6.2,0','Plywood retains its legacy static export offset independently of sequence playback');
// TIMESTAMP END 2026-11-02T15:57:59-05:00 | REVISION R004811
    selectPart('PLY');check(selected==='PLY'&&selectedPartIds.has('PLY'),'Panel selection has one stable assembly ID');
    clearPieceSelection();
    const aids=parts.filter(p=>p.group==='metal_spacers'||p.group==='temporary_fixture');
    // TIMESTAMP START 2026-11-02T22:10:21-05:00 | REVISION R004884
    check(aids.length===2&&aids.every(p=>p.temporary)&&isShown(partById.get('M-TMP'))&&!isShown(partById.get('M-SP0')),'Complete retains the welded support while the green aid is hidden');
    $('constructionAids').onclick();check(aids.every(p=>!isShown(p)),'The first click hides the visible welded support');
    // TIMESTAMP END 2026-11-02T22:10:21-05:00 | REVISION R004884
    $('constructionAids').onclick();check(aids.every(isShown)&&$('constructionAids').getAttribute('aria-pressed')==='true','Construction-aid control reveals both aids without permanent load credit');
    $('constructionAids').onclick();check(aids.every(p=>!isShown(p))&&$('constructionAids').getAttribute('aria-pressed')==='false','Second construction-aid click hides both aids again');
    const fixture=parts.find(p=>p.id==='M-TMP');
    check(parts.filter(p=>p.group==='temporary_fixture').length===1&&fixture.assembly_quantity===1&&fixture.display_holes.length===24,'Central support is one stable assembly with 24 display holes');
// TIMESTAMP START 2026-11-02T15:57:59-05:00 | REVISION R004811
    check(!isTimber(fixture)&&fixture.exploded_offset.join(',')==='0,-1.5,0','Symbolic temporary support keeps its static export metadata and is not counted as timber');
// TIMESTAMP END 2026-11-02T15:57:59-05:00 | REVISION R004811
    selectPart('M-TMP3');check(selected==='M-TMP'&&selectedPartIds.size===1,'Legacy arm selection resolves to the one support assembly');
    check(walk($('selection')).some(e=>String(e.textContent).includes('NOT drilling')),'Fixture inspector explicitly marks hole thickness and elevation assumptions as not fabrication');
    check(!walk($('selection')).some(e=>e.id==='selectedAngles'||String(e.textContent).includes('edge measurements')),'Fixture suppresses timber angle and edge fabrication-style tools');
    $('isolatePiece').onclick();check(parts.filter(isShown).length===1&&isShown(fixture),'Isolation keeps the welded support together');
    $('isolatePiece').onclick();check(parts.every(p=>isShown(p)===OctagonDisplayPresets.included(p,'complete')),'Second fixture isolation click restores all permanent pieces');
    window.location.hash='#part=M-TMP7&isolate=1';applyHash();check(selected==='M-TMP'&&isolatedId==='M-TMP','Legacy arm deep link resolves to complete isolated support');
    window.location.hash='';$('restoreFrame').onclick();
    const fixtureRow=materialsCSV().split('\\r\\n').find(r=>r.includes('M-TMP'));
    check(fixtureRow.includes('DISPLAY ONLY')&&fixtureRow.includes('NOT fabrication specifications'),'Materials CSV qualifies support reference dimensions and suppresses assumed fabrication numbers');
    selectPart('C0');
    const focusButton=walk($('selection')).find(el=>el.id==='focusPiece');
    const shownBeforeFocus=parts.filter(isShown).map(p=>p.id).join(',');
    focusButton.onclick();
    check(inspectionPartId==='C0'&&focusButton.textContent==='Unfocus piece'&&focusButton.getAttribute('aria-pressed')==='true','Focus button enters focused state and exposes its toggle state');
    focusButton.onclick();
    check(inspectionPartId===null&&inspectionPivot===null&&focusButton.textContent==='Focus piece'&&focusButton.getAttribute('aria-pressed')==='false','Second Focus click clears the pivot and returns to assembly framing');
    check(selected==='C0'&&selectedPartIds.has('C0')&&parts.filter(isShown).map(p=>p.id).join(',')===shownBeforeFocus,'Unfocus preserves selection and visible members');
    focusButton.onclick();fitModel();syncFocusButton();
    check(focusButton.textContent==='Focus piece','Reset clears stale focus button state');
    clearPieceSelection();
    visible.clear();visible.add('cupola_posts');hiddenPieces.add('C1');selectPart('C0');
    $('isolatePiece').onclick();syncIsolationButton();
    check(isolatedId==='C0'&&parts.filter(isShown).length===1&&inspectionPartId==='C0','Isolate first click isolates and centers selected member');
    check($('isolatePiece').textContent==='Show all & uncenter'&&$('isolatePiece').getAttribute('aria-pressed')==='true','Isolation button advertises its reverse action');
    const isolatedDistance=camera.distance;$('isolatePiece').onclick();
    check(isolatedId===null&&hiddenPieces.size===0&&parts.every(p=>isShown(p)===OctagonDisplayPresets.included(p,'complete')),'Second isolate click restores ALL pieces, including previously hidden groups and members');
    // TIMESTAMP START 2026-11-02T20:27:45-05:00 | REVISION R004866
check(isShown(partById.get('M-TMP'))&&parts.filter(p=>(p.temporary&&p.id!=='M-TMP')||p.group==='roof_envelope').every(p=>!isShown(p)),'Restore Complete includes welded fixture and excludes green aid and reference envelope');
// TIMESTAMP END 2026-11-02T20:27:45-05:00 | REVISION R004866
    check(selected===null&&selectedPartIds.size===0&&inspectionPartId===null&&inspectionCutId===null&&inspectionPivot===null,'Second isolate click clears former selection and all inspection centering');
    check(camera.distance>isolatedDistance,'Second isolate click frames the complete model rather than the isolated member');
    selectPart('C0');$('isolatePiece').onclick();$('isolatePiece').onclick();
    check(parts.every(p=>isShown(p)===OctagonDisplayPresets.included(p,'complete'))&&isolatedId===null&&inspectionPivot===null,'Repeated isolate/restore cycles remain reversible');
    inspectEnd(partById.get('C0'),'A');syncIsolationButton();
    check(isolatedId==='C0'&&inspectionPartId==='C0','End inspection remains a one-way isolate operation');
    $('isolatePiece').onclick();check(parts.every(p=>isShown(p)===OctagonDisplayPresets.included(p,'complete'))&&inspectionPartId===null,'Restore all also exits end inspection without a stale pivot');
    visible.clear();visible.add('perimeter_posts');hiddenPieces.add('P1');selectPart('P0');focusPart(partById.get('P0'));
    $('resetView').onclick();
    check(parts.every(p=>isShown(p)===OctagonDisplayPresets.included(p,'complete'))&&isolatedId===null&&hiddenPieces.size===0,'Reset view restores every group and manually hidden member');
    check(selected===null&&selectedPartIds.size===0&&inspectionPivot===null&&inspectionPartId===null&&inspectionCutId===null,'Reset view clears focus and selection');
    isolateAndCenter(partById.get('C0'));$('resetView').onclick();
    check(parts.every(p=>isShown(p)===OctagonDisplayPresets.included(p,'complete'))&&isolatedId===null&&inspectionPivot===null,'Reset view exits isolation and returns to the whole model');
    const resetDistance=camera.distance;$('resetView').onclick();
    check(camera.distance===resetDistance&&parts.every(p=>isShown(p)===OctagonDisplayPresets.included(p,'complete')),'Repeated reset is stable');
    $('restoreFrame').onclick();
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
    selectPart('J0-0');check(!walk($('selection')).some(el=>el.tagName==='TR'),'Main inspector does not dump cut-angle tables');
    const cutButton=walk($('selection')).find(el=>el.id==='pieceCutAngles');check(!!cutButton,'Selected member has a Cut angles entry point');cutButton.focus();cutButton.onclick();
    check($('cutAnglesModal').classList.contains('open')&&navigationBlocked(canvas)&&document.querySelector('main').inert,'Cut-angle screen pauses navigation and isolates input');
    cutAngleView.renderPiece('J0-0');const report=cutAngleView.getReport();check(report.partId==='J0-0'&&report.faces.length>0&&$('cutAnglesContent').children.length>0,'Detail screen lists selected current-mesh planar faces');
    const faceButton=walk($('cutAnglesContent')).find(el=>el.tagName==='BUTTON');faceButton.onclick();check($('cutFaceSketch').children.length>0,'Face selection renders actual mesh projection');
    cutAngleView.close();check(!$('cutAnglesModal').classList.contains('open')&&!document.querySelector('main').inert&&document.activeElement===cutButton,'Closing restores original Cut angles focus');
    const inventory=MATERIALS.groups.flatMap(g=>g.member_ids);
    check(inventory.length===parts.length&&new Set(inventory).size===parts.length&&parts.every(p=>inventory.includes(p.id)),'Materials inventory covers current components exactly once');
    check(MATERIALS.groups.every(g=>g.quantity===g.member_ids.length),'Material quantities agree with membership');
    $('materialsButton').focus();openMaterials();check($('scheduleRows').children.length===MATERIALS.groups.length,'Materials dialog lists current groups');
    check($('scheduleRows').querySelectorAll('button').length===parts.length,'Materials includes an inspection button for every component');
    check(inventory.every(id=>materialsCSV().includes(id)),'Materials CSV includes current IDs');closeSchedule();check(document.activeElement===$('materialsButton'),'Materials dialog restores focus');
    setNavigation('orbit');$('allPermanent').onclick();explode=0;selectPart('P0');selectPart('B0',true);
    check(selectedPartIds.size===2&&selectionAlpha(partById.get('R0'))===.14,'Shift selection ghosts unrelated members');
    selectPart('B0',true);check(selectedPartIds.size===1&&selected==='P0','Shift click toggles membership');selectPart('P0',true);check(selected===null&&selectedPartIds.size===0,'Last-member toggle clears selection');
    // TIMESTAMP START 2026-11-02T13:49:06-05:00 | REVISION R004787
    const jamb=schematicParts.find(p=>p.framingRole==='jamb');selectPart(jamb.id);selectPart('P0',true);selectPart('P0',true);
    check(selected===jamb.id&&selectedPartIds.size===1&&walk($('selection')).some(el=>el.textContent==='Active wall framing'),'Removing a main timber from a mixed selection restores the jamb inspector');
    focusPart(jamb);const jambPivot=inspectionPivot.slice();$('explode').value='50';$('explode').oninput({target:{value:'50'}});
// TIMESTAMP START 2026-11-02T15:57:59-05:00 | REVISION R004811
    check(isShown(jamb)&&length(vsub(inspectionPivot,vadd(jambPivot,offset(jamb))))<1e-12,'Sequential framing motion retains its focused pivot');
// TIMESTAMP END 2026-11-02T15:57:59-05:00 | REVISION R004811
    togglePieceIsolation(jamb);check(isolatedId===jamb.id&&isShown(jamb),'Framing can be isolated while exploded');showAllAndUncenter();
    // TIMESTAMP END 2026-11-02T13:49:06-05:00 | REVISION R004787
    showMatingPair(joint);check(selectedPartIds.size===2&&selectedPartIds.has('J0-0')&&selectedPartIds.has('R0')&&parts.filter(isShown).length===2,'Contact pair view isolates rafter and receiving hip');
    faceCut(joint);check(selectedPartIds.size===1&&selectedPartIds.has('J0-0'),'Contact-face inspection selects only its owner');
    $('reviewCorner').onclick();check(parts.filter(isShown).map(p=>p.id).sort().join(',')===['R0','J0-0','J7-2'].sort().join(','),'Rafter-joint shortcut shows both rafters at R0');
    check(selected==='J0-0'&&navigation==='orbit'&&showCutFaces,'Rafter-joint shortcut activates contact inspection');
    check(length(vsub(camera.target,joint.center))<1e-9,'Rafter-joint shortcut centers actual contact plane');
    $('roofPlan').onclick();check(camera.phi>1.5&&parts.filter(isShown).filter(p=>p.group==='secondary_approx').length===16,'Roof-plan shortcut shows all sixteen short rafters from above');
    check(!parts.some(p=>p.temporary&&isShown(p)),'Roof-plan shortcut excludes temporary fixture');
    $('restoreFrame').onclick();check(selected===null&&selectedCut===null&&selectedPartIds.size===0&&inspectionPivot===null,'Restore frame clears selection and inspection pivots');
    check(parts.filter(isShown).length===parts.filter(p=>OctagonDisplayPresets.included(p,'skeleton')).length&&isolatedId===null,'Restore frame follows Skeleton structural groups');
    check(!$('cornerFindings').open&&$('cornerContext').hidden,'Restore frame exits joint context');
// TIMESTAMP START 2026-11-02T15:07:59-05:00 | REVISION R004800
// TIMESTAMP START 2026-11-02T18:01:36-05:00 | REVISION R004828
    $('reviewP0').onclick();check(selected==='P0'&&parts.filter(p=>isShown(p)&&isTimber(p)).length===8,'P0 close-up restores corner and all three braces');
    check(parts.filter(p=>isShown(p)&&p.group==='joinery_pegs').length===6,'P0 close-up includes its six physical retaining pegs');
// TIMESTAMP END 2026-11-02T18:01:36-05:00 | REVISION R004828
// TIMESTAMP END 2026-11-02T15:07:59-05:00 | REVISION R004800
    // TIMESTAMP START 2026-11-02T22:10:21-05:00 | REVISION R004884
    check(showHollows&&selectionAlpha(partById.get('P0'))===.38&&cavityRecords().some(r=>r.kind==='removed')&&cavityRecords().some(r=>r.kind==='additional_removed'),'Original and complementary wall cavities both display through transparent timber');
    // TIMESTAMP END 2026-11-02T22:10:21-05:00 | REVISION R004884
    $('reviewCupola').onclick();check(selected==='C0'&&parts.filter(isShown).filter(p=>p.group==='cupola_rafters').length===8,'Cupola shortcut includes its eight roof rafters');
// TIMESTAMP START 2026-11-02T15:57:59-05:00 | REVISION R004811
    check(visibleDisassemblyExclusions().length===0,'Cupola shortcut excludes symbolic construction aids');
    $('explode').value='60';$('explode').oninput({target:$('explode')});check(explode===.6,'Restored explode control moves assembly');
// TIMESTAMP END 2026-11-02T15:57:59-05:00 | REVISION R004811
    check(!loadReviewOn,'Load review starts off');
// TIMESTAMP START 2026-11-02T15:07:59-05:00 | REVISION R004800
    check(LOAD_REVIEW.members.length===112&&LOAD_REVIEW.members.every(m=>partById.get(m.id).is_timber),'Load review includes exactly112timbers, no plywood, steel or envelope');
// TIMESTAMP END 2026-11-02T15:07:59-05:00 | REVISION R004800
    const netVolume=LOAD_REVIEW.members.reduce((sum,m)=>sum+m.volume_m3,0);
// TIMESTAMP START 2026-11-02T15:07:59-05:00 | REVISION R004800
    check(Math.abs(netVolume-parts.filter(isTimber).reduce((sum,p)=>sum+Math.abs(p.triangles.reduce((v,t)=>{const a=p.vertices[t[0]],b=p.vertices[t[1]],c=p.vertices[t[2]];return v+(a[0]*(b[1]*c[2]-b[2]*c[1])+a[1]*(b[2]*c[0]-b[0]*c[2])+a[2]*(b[0]*c[1]-b[1]*c[0]))/6;},0)),0))<1e-10,'Applied weight uses verified current net mesh volume');
// TIMESTAMP END 2026-11-02T15:07:59-05:00 | REVISION R004800
    showAllAndUncenter();const initialLoadTotals=loadReviewTotals();
// TIMESTAMP START 2026-11-02T15:07:59-05:00 | REVISION R004800
    check(initialLoadTotals.visible_count===112&&Math.abs(initialLoadTotals.total_N-netVolume*780*9.80665)<1e-8,'Total and visible self-weight use assumed density and SIgravity');
// TIMESTAMP END 2026-11-02T15:07:59-05:00 | REVISION R004800
    const member=LOAD_REVIEW.members.find(m=>m.id==='P0'), low=timberGravity(member,520),high=timberGravity(member,900);
    check(high.force_N>low.force_N&&gravityArrowWidth(high.force_N)>gravityArrowWidth(low.force_N),'Arrow width increases monotonically with force across density scenarios');
    check(length(vsub(member.centroid_m,partById.get('P0').center))>1e-4,'Weight acts at volume centroid rather than nominalmodel center');
    explode=.5;let loadRow=loadReviewRows().find(r=>r.member.id==='P0');
    check(length(vsub(loadRow.point,vadd(member.centroid_m,offset(partById.get('P0')))))<1e-12,'Applied gravity origin follows exploded member offset');
    hiddenPieces.add('P0');visible.delete('radial_rafters');loadReviewOn=true;matrix();updateLoadReview();
    check(loadArrowElements.get('P0').style.display==='none'&&LOAD_REVIEW.members.filter(m=>m.id.startsWith('R')).every(m=>loadArrowElements.get(m.id).style.display==='none'),'Hidden members and disabledgroups have no gravity arrows');
// TIMESTAMP START 2026-11-02T15:07:59-05:00 | REVISION R004800
    const partialTotals=loadReviewTotals();check(partialTotals.visible_count===103&&partialTotals.visible_N<partialTotals.total_N&&partialTotals.total_N===initialLoadTotals.total_N,'Visible subtotal changes but all112total remains stable');
// TIMESTAMP END 2026-11-02T15:07:59-05:00 | REVISION R004800
    check(!$('loadReviewOverlay').hidden&&!$('loadReviewViewportLegend').hidden,'Enabled load review shows overlay and limitation legend');
    loadReviewOn=false;updateLoadReview();check($('loadReviewOverlay').hidden&&[...loadArrowElements.values(),...loadIssueElements.values()].every(el=>el.style.display==='none'),'Toggle off clears all arrows and warning markers');
    check(hypotheticalPressure('',64)===null&&hypotheticalPressure(-1,64)===null&&hypotheticalPressure('bad',12)===null,'Bearing pressure stays unavailable for absent or invalid reactions');
    check(Math.abs(hypotheticalPressure(4448.2216152605,64).psi-15.625)<1e-9,'Hypothetical pressure uses reaction divided by area, not membergravity');
    $('hypotheticalReaction').value='1000';$('hypotheticalSeat').value='12';updateHypotheticalPressure();const pressureBefore=$('hypotheticalPressure').textContent;
    $('loadDensity').value='900';$('loadDensity').onchange();
    check(loadDensity===900&&$('hypotheticalReaction').value==='1000'&&$('hypotheticalPressure').textContent===pressureBefore,'Density scenario changes do not alter hypothetical reactions or bearingpressure');
    $('loadDensity').value='780';$('loadDensity').onchange();$('hypotheticalReaction').value='';updateHypotheticalPressure();
    check(LOAD_REVIEW.issues.every(i=>['missing_restraint','capacity_unknown'].includes(i.classification)),'Issue classifications distinguish missing modeledrestraint from unknowncapacity');
    explode=0;showAllAndUncenter();
    showAllAndUncenter();check(schematicWallsEnabled&&schematicShelvesEnabled&&schematicCupolaWindowsEnabled,'Reset and show-all restore all three schematic layers');
    document.activeElement=$('plansButton');explode=.6;const priorExplode=explode;
    refreshPlans();openPlans();
    check($('plansModal').classList.contains('open')&&document.querySelector('main').inert,'Architectural plans opens a modal and isolates background input');
    check(navigationBlocked(canvas),'Free navigation pauses while plans are open');
    // TIMESTAMP START 2026-11-02T22:10:21-05:00 | REVISION R004884
    check(plansSVG.top.includes('MAIN BUILDING — PLAN')&&plansSVG.side.includes('MAIN BUILDING — NORTH ELEVATION'),'Main-building plan and north elevation are scoped independently of the porch');
    // TIMESTAMP END 2026-11-02T22:10:21-05:00 | REVISION R004884
    check(explode===priorExplode,'Plans never alter the 3D exploded state');
    $('plansZoom').value='2';resizePlans();check($('plansTop').style.width==='200%','Plans zoom scales crisp SVG sheets');
    closePlans();check(!$('plansModal').classList.contains('open')&&!document.querySelector('main').inert&&document.activeElement===$('plansButton'),'Closing plans restores background and invoking focus');
    openPlans();closePlans();check(!$('plansModal').classList.contains('open'),'Repeated plans opening and dismissal is reversible');
    return assertions;
  `;
  const run=new Function('document','window','requestAnimationFrame','setTimeout','ResizeObserver','assertions','windowListeners','listeners',source+'\n'+(skipLegacy?'return assertions;':tests));
  return run(document,window,requestAnimationFrame,()=>{},undefined,assertions,windowListeners,listeners);
}
if(typeof module!=='undefined'){
  module.exports={runViewerTests};
  if(require.main===module){const fs=require('node:fs');const html=fs.readFileSync(process.argv[2]||'index.html','utf8');const model=JSON.parse(html.match(/<script[^>]*id="model-data"[^>]*>([\s\S]*?)<\/script>/)[1]);const source=html.split("<script>\n'use strict';\n")[1].split('</script>')[0];console.log(JSON.stringify({passed:runViewerTests(source,model)},null,2));}
}


// TIMESTAMP END 2026-11-01T23:01:05-05:00 | REVISION R004657

// TIMESTAMP END 2026-11-01T23:06:10-05:00 | REVISION R004659

// TIMESTAMP END 2026-11-01T23:19:38-05:00 | REVISION R004668
