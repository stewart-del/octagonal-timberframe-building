// TIMESTAMP START 2026-11-08T21:51:01-05:00 | REVISION R000001
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const physical=require('../src/physical-parts.js'),edgeTools=require('../src/edge-measurements.js');
const source=fs.readFileSync(path.join(__dirname,'../src/viewer.template.html'),'utf8');
const prototype={vertices:[[0,0,0],[1,0,0],[0,2,0],[0,0,3]],triangles:[[0,2,1],[0,1,3],[1,2,3],[2,0,3]]};
const transform=(angle,x=0)=>[[Math.cos(angle),0,Math.sin(angle),x],[0,1,0,2],[-Math.sin(angle),0,Math.cos(angle),-4]];
const instance=(id,angle=0,x=0)=>physical.hydrate({id,schematic:true,mesh_instance:{prototype:'shape',transform:transform(angle,x)}},{shape:prototype});

function legacyTriangleBuffer(part){
 const raw=[],vertices=part.vertices||[];
 for(const tri of part.triangles||[]){const a=vertices[tri[0]],b=vertices[tri[1]],c=vertices[tri[2]];if(!a||!b||!c)continue;
  const ab=b.map((x,i)=>x-a[i]),ac=c.map((x,i)=>x-a[i]),normal=[ab[1]*ac[2]-ab[2]*ac[1],ab[2]*ac[0]-ab[0]*ac[2],ab[0]*ac[1]-ab[1]*ac[0]],scale=1/(Math.hypot(...normal)||1),n=normal.map(x=>x*scale);
  for(const vertex of [a,b,c])raw.push(...vertex,...n);
 }
 return new Float32Array(raw);
}
function bytes(value){return Buffer.from(value.buffer,value.byteOffset,value.byteLength);}
const model=JSON.parse(fs.readFileSync(path.join(__dirname,'../src/top-entry-proposed-model.json'),'utf8'));
let triangles=0;
for(const part of [...model.parts,prototype,{vertices:[[1,2,3]],triangles:[[0,0,0],[0,1,0]]}]){
 assert.deepEqual(bytes(physical.triangleBuffer(part)),bytes(legacyTriangleBuffer(part)),'Positions and normals remain byte-exact: '+(part.id||'fixture'));
 triangles+=(part.triangles||[]).length;
}

function segments(raw){const result=[];for(let i=0;i<raw.length;i+=12){const endpoints=[Array.from(raw.slice(i,i+3)),Array.from(raw.slice(i+6,i+9))].map(point=>point.map(n=>Math.round(n*1e8)).join(',')).sort();result.push(endpoints.join('|'));}return result.sort();}
let edgeCalls=0;const countedEdges=(v,t)=>{edgeCalls++;return edgeTools.featureEdges(v,t);};
for(let i=0;i<2000;i++){
 const part=instance('instance-'+i,i*.071,i*.01),actual=physical.drawingEdges(part,countedEdges);
 assert.strictEqual(physical.drawingEdges(part,countedEdges),actual,'Repeated reads reuse transformed edges');
 if(i%199===0)assert.deepEqual(segments(actual),segments(edgeTools.featureEdges(part.vertices,part.triangles)),'Rigid transformed prototype segments match occupied world geometry');
}
assert.equal(edgeCalls,1,'Thousands of rigid instances analyze one prototype once');
const scaled=instance('scaled');scaled.mesh_instance.transform[0][0]=2;
assert.deepEqual(physical.drawingEdges(scaled,countedEdges),edgeTools.featureEdges(scaled.vertices,scaled.triangles),'Nonrigid future instances retain full world-space analysis');
assert.equal(edgeCalls,2);

function fakeGL(instancing){
 const state={buffers:0,uploads:[],draws:[],sources:[],uniforms:{},instanced:[],divisors:[]};
 const extension={vertexAttribDivisorANGLE:(...args)=>state.divisors.push(args),drawArraysInstancedANGLE:(...args)=>state.instanced.push(args)};
 const names=['COMPILE_STATUS','LINK_STATUS','ARRAY_BUFFER','STATIC_DRAW','DYNAMIC_DRAW','FLOAT','TRIANGLES','LINES','POLYGON_OFFSET_FILL'];
 const gl=Object.fromEntries(names.map((name,i)=>[name,i+1]));
 Object.assign(gl,{getExtension:name=>name==='ANGLE_instanced_arrays'?(instancing?extension:null):null,createShader:()=>({}),shaderSource:(_,text)=>state.sources.push(text),compileShader(){},getShaderParameter:()=>true,createProgram:()=>({}),attachShader(){},linkProgram(){},getProgramParameter:()=>true,getAttribLocation:(_,name)=>({position:0,normal:1,transform0:2,transform1:3,transform2:4}[name]),getUniformLocation:(_,name)=>name,createBuffer:()=>({id:++state.buffers}),bindBuffer(){},bufferData:(_,data)=>state.uploads.push(Array.from(data)),useProgram(){},uniformMatrix4fv(){},uniform1f:(name,value)=>state.uniforms[name]=value,uniform3fv:(name,value)=>state.uniforms[name]=Array.from(value),uniform4fv:(name,value)=>state.uniforms[name]=Array.from(value),enableVertexAttribArray(){},disableVertexAttribArray(){},vertexAttribPointer(){},enable(){},disable(){},polygonOffset(){},drawArrays:(...args)=>state.draws.push({args,uniforms:structuredClone(state.uniforms)})});
 return {gl,state};
}
for(const instancing of [true,false]){
 const {gl,state}=fakeGL(instancing);let analyses=0;
 const renderer=physical.createRenderer(gl,{fragmentShader:'precision mediump float;void main(){gl_FragColor=vec4(1.0);}',featureEdges:(v,t)=>{analyses++;return edgeTools.featureEdges(v,t);}});
 const a=instance('a',.2,1),b=instance('b',.3,4),hidden=instance('hidden',.4,8);for(const part of [a,b,hidden])renderer.register(part);
 assert.equal(renderer.count,3);assert.equal(renderer.templateCount,1);assert.equal(analyses,1);assert.equal(state.buffers,instancing?3:2,'Only shared prototype mesh/edge buffers plus optional instance buffer');
 const options={viewProjection:new Float32Array(16),isShown:p=>p!==hidden,offset:()=>[.25,.5,.75],color:()=>[1,0,0],opacity:()=>1,edges:true,edgeColor:()=>[0,0,0],highlighted:()=>false,surfaceContrast:false,pass:'opaque'};
 renderer.draw(options);
 if(instancing){assert.equal(state.instanced.length,2);assert(state.instanced.every(call=>call[3]===2));assert.equal(state.draws.length,0);assert(state.sources.some(s=>s.includes('attribute vec4 transform0')));}
 else{
  assert.equal(state.draws.length,4);assert.equal(state.instanced.length,0);assert(state.sources.some(s=>s.includes('uniform vec4 transform0')));
  for(let i=0;i<2;i++)for(let row=0;row<3;row++){const matrix=[a,b][i].mesh_instance.transform[row],expected=[...matrix];expected[3]+=[.25,.5,.75][row];assert.deepEqual(state.draws[i].uniforms['transform'+row],expected,'Each independent instance keeps its transform and motion');}
 }
 const before=state.draws.length+state.instanced.length;renderer.draw({...options,pass:'ghost'});assert.equal(state.draws.length+state.instanced.length,before,'Opaque hardware is excluded from ghost pass');
 renderer.draw({...options,isShown:p=>p===b,highlighted:()=>true,color:()=>[0,0,1],opacity:()=>.25,pass:'ghost'});
 if(instancing)assert.equal(state.instanced.at(-1)[3],1,'A selected/isolated instance remains separate from its prototype siblings');
 else{const last=state.draws.at(-2);assert.deepEqual(last.uniforms.color,[0,0,1]);assert.equal(last.uniforms.opacity,.25);assert.equal(state.draws.length,before+2,'Only the visible individual is drawn in the ghost pass');}
}

const loopStart=source.indexOf('for(const p of [...parts,...schematicParts]){',source.indexOf('const physicalRenderer='));
const loopEnd=source.indexOf('const windowUnits=',loopStart),initialization=source.slice(loopStart,loopEnd);
let labels=0,packed=0,computed=0;
const lazy={id:'lazy',schematic:true,mesh_instance:{prototype:'shape',transform:transform(0)},get vertices(){throw Error('Canvas startup must not expand instance vertices');}};
const ordinary={id:'P0',vertices:prototype.vertices,triangles:prototype.triangles};
const context={parts:[ordinary],schematicParts:[lazy],gl:null,physicalRenderer:null,batchRenderer:null,meshParts:[],MODEL_CONTEXT:{parametric:false,meshCache:new Map([['P0',new Float32Array(0)]])},OctagonPhysicalParts:{triangleBuffer(){packed++;throw Error('Unused GPU array');},drawingEdges(){computed++;throw Error('Unused GPU edges');}},featureEdges(){throw Error('Unused feature analysis');},document:{createElement:()=>({dataset:{},addEventListener(){}})},labelLayer:{appendChild(){labels++;}},selectPart(){}};
vm.runInNewContext(initialization,context);assert.equal(labels,1);assert.equal(packed,0);assert.equal(computed,0);assert.equal(context.meshParts.length,0);
context.MODEL_CONTEXT.meshCache.clear();assert.throws(()=>vm.runInNewContext(initialization,context),/Missing drawing edges: P0/,'Ordinary incomplete caches still fail closed');

const fallbackSource=source.slice(source.indexOf('function fallbackSegmentIndex('),source.indexOf('function drawFallback()'));
const sub=(a,b)=>a.map((x,i)=>x-b[i]),add=(a,b)=>a.map((x,i)=>x+b[i]),mul=(a,s)=>a.map(x=>x*s),dot=(a,b)=>a.reduce((n,x,i)=>n+x*b[i],0),length=a=>Math.hypot(...a);
let fallbackAnalyses=0;
const cachedEdges=edgeTools.featureEdges(ordinary.vertices,ordinary.triangles),fallbackContext={fallbackFeatureCache:new Map(),MODEL_CONTEXT:{parametric:false,meshCache:new Map([['P0',cachedEdges]])},OctagonPhysicalParts:physical,featureEdges:(v,t)=>{fallbackAnalyses++;return edgeTools.featureEdges(v,t);},vsub:sub,vadd:add,vmul:mul,dot,length};
vm.runInNewContext(fallbackSource,fallbackContext);for(const tri of ordinary.triangles)fallbackContext.fallbackFaceEdges(ordinary,tri);
assert.equal(fallbackAnalyses,0,'Canvas ordinary meshes reuse downloaded exact feature edges');
ordinary.windowMotion='sash';ordinary.vertices=ordinary.vertices.map(v=>v.map(n=>n+.1));fallbackContext.fallbackFaceEdges(ordinary,ordinary.triangles[0]);assert.equal(fallbackAnalyses,1,'Opening windows recompute their changed geometry');

async function checkBoot({changed=false,generationFails=false,viewerFails=false}={}){
 const boot=source.split('/* PARAMETRIC_BOOT_START */')[1].split('/* PARAMETRIC_BOOT_END */')[0],saved={id:'saved'},generated={id:'generated'},starts=[],errors=[],status={textContent:''};let generatedCount=0;
 const ctx={SAVED_MODEL_CONTEXT:saved,initialModelContext:saved,window:{location:{search:''}},document:{getElementById:()=>status},console:{error:e=>errors.push(e.message)},startViewer:value=>{starts.push(value);if(viewerFails)throw Error('viewer failed');},OctagonParametricControls:{requested:()=>({changed}),generate:async()=>{generatedCount++;if(generationFails)throw Error('generation failed');return generated;}},loadFoundationDetail:async()=>{},TimberSchematicWalls:{},OctagonFloorFoundation:{},TimberRoofCoverings:{},OctagonMudroom:{},FLOOR_FOUNDATION_DATA:{}};
 await vm.runInNewContext(boot,ctx);assert.equal(starts.length,1,'A viewer starts at most once');assert.equal(generatedCount,changed?1:0);
 assert.strictEqual(starts[0],changed&&!generationFails?generated:saved);
 if(viewerFails){assert.deepEqual(errors,['viewer failed']);assert(status.textContent.includes('could not start'));}
 else if(generationFails){assert.deepEqual(errors,['generation failed']);assert(status.textContent.includes('Saved dimensions are shown'));}
 else assert.deepEqual(errors,[]);
}
(async()=>{
 for(const config of [{},{viewerFails:true},{changed:true},{changed:true,generationFails:true},{changed:true,viewerFails:true},{changed:true,generationFails:true,viewerFails:true}])await checkBoot(config);
 console.log(JSON.stringify({pass:true,exactTriangleBuffers:{modelParts:model.parts.length,modelTriangles:model.parts.reduce((sum,p)=>sum+(p.triangles||[]).length,0),totalTrianglesIncludingAdversaries:triangles},sharedPrototypeEdgeAnalyses:1,rigidInstancesChecked:2000,webglInstancedAndUniformFallback:true,individualSelectionVisibilityAndOpacity:true,canvasUnusedGPUAllocations:0,ordinaryMissingCacheRejected:true,canvasCacheReuseAndWindowInvalidation:true,bootRecoveryCases:6}));
})().catch(error=>{console.error(error);process.exitCode=1;});
// TIMESTAMP END 2026-11-08T21:51:01-05:00 | REVISION R000001
