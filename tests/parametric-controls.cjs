// TIMESTAMP START 2026-11-05T16:01:12+00:00 | REVISION R000052
// TIMESTAMP START 2026-11-05T14:18:42+00:00 | REVISION R000046
'use strict';
const assert=require('node:assert/strict');
global.OctagonParametric=require('../src/parametric-model.js');
const C=require('../src/parametric-controls.js'),P=global.OctagonParametric;
(async()=>{
 assert.equal(P.parameters({pitch:8,cupolaPitch:3}).cupolaPitch,8,'Legacy independent pitch values must not detach the cupola');
 const saved=P.parameters();assert.equal(saved.changed,false);assert.equal(saved.cupolaLiftIn,10);assert.equal(saved.cupolaPitch,4);
 for(const request of [{cupolaLiftIn:8.99},{cupolaLiftIn:36.01}])assert.throws(()=>P.parameters(request));
 const cfg=C.requested('?model=top-entry&wallHeight=96&pitch=5&cupolaLift=18&cupolaPitch=6');assert.equal(cfg.cupolaLiftIn,18);assert.equal(cfg.cupolaPitch,5);assert(cfg.changed);
 const changed=new URL(C.selectionURL('https://example.test/?model=proposed&keep=yes#piece',cfg));assert.equal(changed.searchParams.get('model'),'proposed');assert.equal(changed.searchParams.get('keep'),'yes');assert.equal(changed.searchParams.get('cupolaLift'),'18');assert.equal(changed.searchParams.has('cupolaPitch'),false);assert.equal(changed.hash,'');
 const reset=new URL(C.selectionURL(changed.href,saved));for(const key of ['wallHeight','pitch','cupolaLift','cupolaPitch'])assert(!reset.searchParams.has(key));assert.equal(reset.searchParams.get('model'),'proposed');
 const nodes=new Map(),document={getElementById:id=>{if(!nodes.has(id))nodes.set(id,{value:'',disabled:false,textContent:''});return nodes.get(id);}},get=document.getElementById;
 const slider=get('explode');slider.disabled=false;slider.value='41.5';let calls=0,received;
 C.bind({parameters:cfg,parametric:true},document,{href:changed.href,assign(){throw Error('Validation must precede any navigation');}},{apply:async value=>{calls++;received=value;if(calls===1)throw Error('Observed generation failure');}});
 assert.equal(get('cupolaLift').value,'18');assert(get('parameterDimensions').textContent.includes('5:12'));
 get('cupolaLift').value='0';await get('applyDimensions').onclick();assert.equal(calls,0);assert.equal(slider.value,'41.5');assert.equal(slider.disabled,false);
 get('cupolaLift').value='24';await get('applyDimensions').onclick();assert.equal(received.cupolaLiftIn,24);assert(get('parameterStatus').textContent.includes('Current dimensions remain available'));assert.equal(slider.value,'41.5');assert.equal(slider.disabled,false);assert.equal(get('applyDimensions').disabled,false);
 await get('applyDimensions').onclick();assert.equal(calls,2);await get('resetDimensions').onclick();assert.equal(received.changed,false);assert.equal(received.cupolaLiftIn,10);assert.equal(received.cupolaPitch,4);
 // TIMESTAMP START 2026-11-05T20:50:09+00:00 | REVISION R000064
 const minimumNodes=new Map(),minimumDocument={getElementById:id=>{if(!minimumNodes.has(id))minimumNodes.set(id,{value:'',disabled:false,textContent:''});return minimumNodes.get(id);}};let minimumApplied;
 C.bind({parameters:saved,parametric:false},minimumDocument,{href:'https://example.test/',assign(){throw Error('Use the transactional callback');}},{apply:async value=>{minimumApplied=value;}});
 assert.equal(Number(minimumDocument.getElementById('wallHeight').value),P.BASE_WALL,'The saved minimum must survive a control round trip');
 minimumDocument.getElementById('cupolaLift').value='18';await minimumDocument.getElementById('applyDimensions').onclick();assert(minimumApplied,'Changing only cupola height must be accepted');assert.equal(minimumApplied.wallHeightIn,P.BASE_WALL);assert.equal(minimumApplied.cupolaLiftIn,18);
 // TIMESTAMP END 2026-11-05T20:50:09+00:00 | REVISION R000064
 console.log('PASS: three dimension controls, shared roof pitch and URL state, cupola height limits, reset, validation before generation, failed generation preserves the existing slider. Full generated motion is checked separately.');
})().catch(error=>{console.error(error);process.exitCode=1;});
// TIMESTAMP END 2026-11-05T14:18:42+00:00 | REVISION R000046

// TIMESTAMP END 2026-11-05T16:01:12+00:00 | REVISION R000052
