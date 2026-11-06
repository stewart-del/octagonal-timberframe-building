// TIMESTAMP START 2026-11-06T01:19:41+00:00 | REVISION R000080
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const source=fs.readFileSync(process.env.VIEWER_DETAIL_SOURCE||path.join(__dirname,'../src/viewer.template.html'),'utf8'),end='// TIMESTAMP END 2026-11-05T06:13:38+00:00 | REVISION R000027';
const extract=start=>{const a=source.indexOf(start);assert(a>=0);const b=source.indexOf(end,a);assert(b>a);return source.slice(a,b);};
async function main(){
 const ownedEdges=new Float32Array([3]),oldEdges=new Float32Array([1]),newEdges=new Float32Array([2]),cache=new Map([['OWNED',ownedEdges],['LAZY',oldEdges]]),owned={id:'OWNED',replaceExisting:true,vertices:[[30,0,0]],triangles:[]},lazy={id:'LAZY',detail_ref:'LAZY',vertices:[[10,0,0]],triangles:[]};let calls=0,renders=0;
 const detail={parts:{OWNED:{vertices:[[99,0,0]],triangles:[]},LAZY:{vertices:[[20,0,0]],triangles:[]}},meshCache:new Map([['OWNED',new Float32Array([99])],['LAZY',newEdges]])};
 const foundation={parts:[{id:'OWNED',detail_ref:'OWNED',vertices:[[1,0,0]],triangles:[]},{id:'LAZY',detail_ref:'LAZY',vertices:[[10,0,0]],triangles:[]}],architecture:{parts:[owned]}};
 const context=vm.createContext({Set,Promise,Error,FLOOR_FOUNDATION_DATA:foundation,SAVED_MODEL_CONTEXT:{meshCache:cache},MODEL_CONTEXT:{parametric:false,meshCache:cache},schematicParts:[owned,lazy],meshParts:[],requestRender:()=>renders++,OctagonSiteLoader:{ensureDetail:async()=>{calls++;return detail;}}});
 vm.runInContext(extract('async function loadFoundationDetail(){')+extract('let physicalDetailPromise=null;'),context);
 await Promise.all([context.ensurePhysicalDetail(),context.ensurePhysicalDetail(),context.ensurePhysicalDetail()]);assert.equal(calls,1);assert.equal(renders,1);assert.equal(owned.vertices[0][0],30);assert.equal(foundation.parts[0].vertices[0][0],1);assert.equal(lazy.vertices[0][0],20);assert.equal(foundation.parts[1].vertices[0][0],20);assert.strictEqual(cache.get('OWNED'),ownedEdges);assert.strictEqual(cache.get('LAZY'),newEdges);assert(!lazy.detail_ref);await context.ensurePhysicalDetail();assert.equal(calls,1);
 console.log(JSON.stringify({pass:true,currentOverlayPreserved:true,ownedEdgesPreserved:true,canonicalDetailUpgraded:true,concurrentAndRepeatedLoads:1}));
}
main().catch(error=>{console.error(error);process.exitCode=1;});
// TIMESTAMP END 2026-11-06T01:19:41+00:00 | REVISION R000080
