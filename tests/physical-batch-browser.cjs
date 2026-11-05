// TIMESTAMP START 2026-11-05T06:06:56+00:00 | REVISION R000026
'use strict';
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const root=path.resolve(__dirname,'..');
const physical=require('../src/physical-parts.js');
const prototype={vertices:[[-.2,-.4,-.7],[.3,-.4,-.7],[0,.5,-.7],[0,0,.8]],triangles:[[0,2,1],[0,1,3],[1,2,3],[2,0,3]]};
const transform=[[.8,0,.6,4],[0,1,0,3],[-.6,0,.8,-2]],part=physical.hydrate({id:'bounded-instance',mesh_instance:{prototype:'shape',transform}},{shape:prototype});
const bound=physical.bounds(part);
for(const v of part.vertices)for(let k=0;k<3;k++)assert(v[k]>=bound.min[k]-1e-12&&v[k]<=bound.max[k]+1e-12);
for(const tri of part.triangles){const center=tri.map(i=>part.vertices[i]).reduce((a,p)=>a.map((v,k)=>v+p[k]/3),[0,0,0]);assert(physical.rayBounds(center.map(v=>v+1),[-1,-1,-1],bound));}
assert(!physical.rayBounds([100,100,100],[1,0,0],bound));
const ordinary={vertices:[[0,0,0],[1,1,1]]};assert.equal(physical.bounds(ordinary).max[0],1);ordinary.vertices=[[0,0,0],[2,2,2]];assert.equal(physical.bounds(ordinary).max[0],2,'Detailed-mesh replacement invalidates cached bounds');
(async()=>{
 const browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||undefined,headless:true,args:['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 try{
  const page=await browser.newPage();const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.setContent('<canvas width="512" height="512"></canvas>');
  await page.addScriptTag({content:fs.readFileSync(path.join(root,'src/physical-parts.js'),'utf8')});
  const fragmentShader=fs.readFileSync(path.join(root,'src/viewer.template.html'),'utf8').match(/fs:`([^`]+)`/)[1];
  const result=await page.evaluate(fragmentShader=>{
   const gl=document.querySelector('canvas').getContext('webgl',{preserveDrawingBuffer:true});if(!gl)throw Error('WebGL unavailable');
   const renderer=OctagonPhysicalParts.createBatchRenderer(gl,{fragmentShader});if(!renderer)throw Error('32-bit element indices unavailable');
   const parts=[];const square=(x,y)=>[x,y,0,0,0,1,x+.04,y,0,0,0,1,x,y+.04,0,0,0,1,x+.04,y,0,0,0,1,x+.04,y+.04,0,0,0,1,x,y+.04,0,0,0,1];
   for(let k=0;k<1024;k++){const x=-.96+(k%32)*.06,y=-.96+Math.floor(k/32)*.06,p={id:'piece-'+k,x,y};parts.push(p);const raw=square(x,y);renderer.register(p,raw,[]);}
   const hidden=new Set(),shift=new Map(),selected=new Set(),alpha=new Map(),VP=new Float32Array([1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1]);
   const options={viewProjection:VP,isShown:p=>!hidden.has(p.id),offset:p=>shift.get(p.id)||[0,0,0],color:p=>selected.has(p.id)?[0,0,1]:[1,0,0],opacity:p=>alpha.get(p.id)??1,edges:false,edgeColor:()=>[0,0,0],highlighted:()=>false,surfaceContrast:false,distance:p=>Number(p.id.slice(6)),pass:'opaque'};
   function draw(){gl.clearColor(1,1,1,1);gl.clear(gl.COLOR_BUFFER_BIT|gl.DEPTH_BUFFER_BIT);gl.disable(gl.BLEND);renderer.draw({...options,pass:'opaque'});gl.enable(gl.BLEND);gl.blendFunc(gl.SRC_ALPHA,gl.ONE_MINUS_SRC_ALPHA);renderer.draw({...options,pass:'ghost'});gl.finish();}
   function pixel(x,y){const a=new Uint8Array(4);gl.readPixels(Math.round((x+1)*256),Math.round((y+1)*256),1,1,gl.RGBA,gl.UNSIGNED_BYTE,a);return Array.from(a);}
   const at=k=>pixel(parts[k].x+.015,parts[k].y+.015),red=p=>p[0]>60&&p[1]<5&&p[2]<5,white=p=>p.slice(0,3).every(v=>v>250);
   draw();if(!red(at(0))||!red(at(777)))throw Error('Initial batch pixels absent');
   const first=renderer.stats;draw();const orbit=renderer.stats;if(orbit.stateUploads!==first.stateUploads)throw Error('Unchanged frame uploaded per-piece state');
   hidden.add('piece-0');selected.add('piece-777');shift.set('piece-500',[.025,0,0]);alpha.set('piece-100',.25);draw();
   if(!white(at(0)))throw Error('Hidden member still drawn');
   const blue=at(777);if(!(blue[2]>60&&blue[0]<5))throw Error('Individual selection tint absent');
   if(!white(at(500))||!red(pixel(parts[500].x+.05,parts[500].y+.015)))throw Error('Individual translation absent');
   const ghost=at(100);if(!(ghost[1]>180&&ghost[1]<205&&ghost[2]===ghost[1]))throw Error('Ghost opacity or pass ordering failed');
   renderer.replace(parts[0],square(parts[0].x,parts[0].y),[]);draw();if(!white(at(0)))throw Error('Rebuilt geometry lost hidden state');
   const error=gl.getError();if(error!==gl.NO_ERROR)throw Error('WebGL error '+error);
   return {pass:true,pieces:parts.length,first,orbit,final:renderer.stats,hidden:true,selected:true,translated:true,ghost:true,geometryRefresh:true,glError:error};
  },fragmentShader);
  assert.deepEqual(errors,[]);assert(result.first.drawCalls<=2,'Opaque batch should use at most two submissions');console.log(JSON.stringify(result));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
// TIMESTAMP END 2026-11-05T06:06:56+00:00 | REVISION R000026
