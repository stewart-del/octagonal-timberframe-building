// TIMESTAMP START 2026-11-05T04:29:18+00:00 | REVISION R000022
(function(root){
'use strict';
function hydrate(part,prototypes){
 if(!part.mesh_instance)return part;
 const instance=part.mesh_instance,prototype=prototypes[instance.prototype];
 if(!prototype||!prototype.vertices?.length||!prototype.triangles?.length)throw Error('Missing physical prototype '+instance.prototype);
 const matrix=instance.transform;
 if(matrix.length!==3||matrix.some(row=>row.length!==4||row.some(n=>!Number.isFinite(n))))throw Error('Invalid physical transform '+part.id);
 let vertices;
// TIMESTAMP START 2026-11-05T09:01:08+00:00 | REVISION R000039
 const result={...(prototype.fastener_spec&&!part.fastener_spec?{fastener_spec:prototype.fastener_spec}:{}),...part,triangles:prototype.triangles,faces:prototype.triangles};
// TIMESTAMP END 2026-11-05T09:01:08+00:00 | REVISION R000039
 Object.defineProperty(result,'instancePrototype',{value:prototype});
 Object.defineProperty(result,'vertices',{enumerable:true,get:()=>vertices??(vertices=prototype.vertices.map(v=>matrix.map(row=>row[0]*v[0]+row[1]*v[1]+row[2]*v[2]+row[3])))});
 return result;
}
// TIMESTAMP START 2026-11-08T21:51:01-05:00 | REVISION R000001
const prototypeDrawingEdges=new WeakMap(),instanceDrawingEdges=new WeakMap();
function triangleBuffer(part){
 const vertices=part.vertices||[],triangles=part.triangles||[],values=new Float32Array(triangles.length*18);let at=0;
 for(const triangle of triangles){
  const a=vertices[triangle[0]],b=vertices[triangle[1]],c=vertices[triangle[2]];if(!a||!b||!c)continue;
  const ab0=b[0]-a[0],ab1=b[1]-a[1],ab2=b[2]-a[2],ac0=c[0]-a[0],ac1=c[1]-a[1],ac2=c[2]-a[2];
  let n0=ab1*ac2-ab2*ac1,n1=ab2*ac0-ab0*ac2,n2=ab0*ac1-ab1*ac0;const scale=1/(Math.hypot(n0,n1,n2)||1);n0*=scale;n1*=scale;n2*=scale;
  for(let corner=0;corner<3;corner++){const point=vertices[triangle[corner]];values[at++]=point[0];values[at++]=point[1];values[at++]=point[2];values[at++]=n0;values[at++]=n1;values[at++]=n2;}
 }
 return at===values.length?values:values.subarray(0,at);
}
function drawingEdges(part,featureEdges){
 if(!part.mesh_instance)return featureEdges(part.vertices||[],part.triangles||[]);
 const instance=part.mesh_instance,prototype=part.instancePrototype,matrix=instance.transform;
 if(!prototype)throw Error('Missing physical prototype '+instance.prototype);
 // Rigid transforms preserve the prototype's feature angles and segments.
 // Recompute from occupied world vertices if a future instance adds scaling.
 const rigid=matrix.every((a,i)=>matrix.every((b,j)=>Math.abs(a.slice(0,3).reduce((sum,n,k)=>sum+n*b[k],0)-(i===j?1:0))<1e-10));
 if(!rigid)return featureEdges(part.vertices||[],part.triangles||[]);
 const values=matrix.flat(),previous=instanceDrawingEdges.get(part);
 if(previous?.prototype===prototype&&previous.featureEdges===featureEdges&&values.every((n,i)=>n===previous.matrix[i]))return previous.edges;
 let cached=prototypeDrawingEdges.get(prototype);
 if(!cached||cached.featureEdges!==featureEdges){cached={featureEdges,edges:featureEdges(prototype.vertices,prototype.triangles)};prototypeDrawingEdges.set(prototype,cached);}
 const source=cached.edges,edges=new Float64Array(source.length);
 for(let i=0;i<source.length;i+=6){for(let row=0;row<3;row++)edges[i+row]=matrix[row][0]*source[i]+matrix[row][1]*source[i+1]+matrix[row][2]*source[i+2]+matrix[row][3];edges[i+4]=1;}
 instanceDrawingEdges.set(part,{prototype,featureEdges,matrix:values,edges});return edges;
}
function createRenderer(gl,{fragmentShader,featureEdges}){
 const extension=gl.getExtension('ANGLE_instanced_arrays'),transformQualifier=extension?'attribute':'uniform';
 // Shared prototype buffers also serve WebGL implementations without ANGLE.
 const vertexShader=`attribute vec3 position;attribute vec3 normal;${transformQualifier} vec4 transform0;${transformQualifier} vec4 transform1;${transformQualifier} vec4 transform2;uniform mat4 viewProjection;varying vec3 N;varying vec3 W;void main(){vec4 p=vec4(position,1.0);W=vec3(dot(transform0,p),dot(transform1,p),dot(transform2,p));N=vec3(dot(transform0.xyz,normal),dot(transform1.xyz,normal),dot(transform2.xyz,normal));gl_Position=viewProjection*vec4(W,1.0);}`;
// TIMESTAMP END 2026-11-08T21:51:01-05:00 | REVISION R000001
 function shader(type,source){const value=gl.createShader(type);gl.shaderSource(value,source);gl.compileShader(value);if(!gl.getShaderParameter(value,gl.COMPILE_STATUS))throw Error(gl.getShaderInfoLog(value));return value;}
 const program=gl.createProgram();gl.attachShader(program,shader(gl.VERTEX_SHADER,vertexShader));gl.attachShader(program,shader(gl.FRAGMENT_SHADER,fragmentShader));gl.linkProgram(program);if(!gl.getProgramParameter(program,gl.LINK_STATUS))throw Error(gl.getProgramInfoLog(program));
// TIMESTAMP START 2026-11-08T21:51:01-05:00 | REVISION R000001
 const attributes=Object.fromEntries(['position','normal',...(extension?['transform0','transform1','transform2']:[])].map(name=>[name,gl.getAttribLocation(program,name)])),uniforms=Object.fromEntries(['viewProjection','color','lineMode','opacity','surfaceContrast',...(!extension?['transform0','transform1','transform2']:[])].map(name=>[name,gl.getUniformLocation(program,name)]));
 const records=[],templates=new Map(),instanceBuffer=extension?gl.createBuffer():null;
// TIMESTAMP END 2026-11-08T21:51:01-05:00 | REVISION R000001
// TIMESTAMP START 2026-11-08T21:51:01-05:00 | REVISION R000001
 function buffer(data){const value=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,value);gl.bufferData(gl.ARRAY_BUFFER,data instanceof Float32Array?data:new Float32Array(data),gl.STATIC_DRAW);return value;}
// TIMESTAMP END 2026-11-08T21:51:01-05:00 | REVISION R000001
 function register(part){
  const key=part.mesh_instance.prototype,prototype=part.instancePrototype;
  if(!templates.has(key)){
   const raw=[];
   for(const triangle of prototype.triangles){const [a,b,c]=triangle.map(index=>prototype.vertices[index]),ab=b.map((n,i)=>n-a[i]),ac=c.map((n,i)=>n-a[i]),normal=[ab[1]*ac[2]-ab[2]*ac[1],ab[2]*ac[0]-ab[0]*ac[2],ab[0]*ac[1]-ab[1]*ac[0]],length=Math.hypot(...normal)||1;for(const point of [a,b,c])raw.push(...point,...normal.map(n=>n/length));}
   const edges=featureEdges(prototype.vertices,prototype.triangles);
   templates.set(key,{prototype,buffer:buffer(raw),edgeBuffer:buffer(edges),count:raw.length/6,edgeCount:edges.length/6});
  }
  records.push(part);
 }
 function draw({viewProjection,isShown,offset,color,opacity,edges,edgeColor,highlighted,surfaceContrast,pass}){
  const batches=new Map();
  for(const part of records){
   if(!isShown(part))continue;const alpha=opacity(part);if((pass==='opaque')!==(alpha===1))continue;
   const tint=color(part),key=part.mesh_instance.prototype+'|'+tint.join(',')+'|'+alpha+'|'+highlighted(part);let batch=batches.get(key);
   if(!batch){batch={template:templates.get(part.mesh_instance.prototype),tint,alpha,highlighted:highlighted(part),values:[]};batches.set(key,batch);}
   const delta=offset(part),matrix=part.mesh_instance.transform;
   for(let row=0;row<3;row++)batch.values.push(matrix[row][0],matrix[row][1],matrix[row][2],matrix[row][3]+delta[row]);
  }
  if(!batches.size)return;
  gl.useProgram(program);gl.uniformMatrix4fv(uniforms.viewProjection,false,viewProjection);gl.uniform1f(uniforms.surfaceContrast,surfaceContrast?1:0);
// TIMESTAMP START 2026-11-08T21:51:01-05:00 | REVISION R000001
  function bindMesh(value){gl.bindBuffer(gl.ARRAY_BUFFER,value);for(const [name,start] of [['position',0],['normal',12]]){const location=attributes[name];gl.enableVertexAttribArray(location);extension?.vertexAttribDivisorANGLE(location,0);gl.vertexAttribPointer(location,3,gl.FLOAT,false,24,start);}}
  function submit(batch,mode,count){
   if(extension){extension.drawArraysInstancedANGLE(mode,0,count,batch.values.length/12);return;}
   for(let at=0;at<batch.values.length;at+=12){for(let row=0;row<3;row++)gl.uniform4fv(uniforms['transform'+row],batch.values.slice(at+row*4,at+row*4+4));gl.drawArrays(mode,0,count);}
  }
// TIMESTAMP END 2026-11-08T21:51:01-05:00 | REVISION R000001
  try{
   for(const batch of batches.values()){
// TIMESTAMP START 2026-11-08T21:51:01-05:00 | REVISION R000001
    if(extension){gl.bindBuffer(gl.ARRAY_BUFFER,instanceBuffer);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array(batch.values),gl.DYNAMIC_DRAW);
     for(let row=0;row<3;row++){const location=attributes['transform'+row];gl.enableVertexAttribArray(location);gl.vertexAttribPointer(location,4,gl.FLOAT,false,48,row*16);extension.vertexAttribDivisorANGLE(location,1);}}
// TIMESTAMP END 2026-11-08T21:51:01-05:00 | REVISION R000001
    gl.uniform3fv(uniforms.color,batch.tint);gl.uniform1f(uniforms.opacity,batch.alpha);gl.uniform1f(uniforms.lineMode,0);bindMesh(batch.template.buffer);gl.enable(gl.POLYGON_OFFSET_FILL);gl.polygonOffset(1,1);
// TIMESTAMP START 2026-11-08T21:51:01-05:00 | REVISION R000001
    try{submit(batch,gl.TRIANGLES,batch.template.count);}finally{gl.disable(gl.POLYGON_OFFSET_FILL);}
    if(edges||batch.highlighted){gl.uniform3fv(uniforms.color,edgeColor(batch.highlighted));gl.uniform1f(uniforms.lineMode,1);bindMesh(batch.template.edgeBuffer);submit(batch,gl.LINES,batch.template.edgeCount);}
// TIMESTAMP END 2026-11-08T21:51:01-05:00 | REVISION R000001
   }
// TIMESTAMP START 2026-11-08T21:51:01-05:00 | REVISION R000001
  }finally{if(extension)for(let row=0;row<3;row++){const location=attributes['transform'+row];extension.vertexAttribDivisorANGLE(location,0);gl.disableVertexAttribArray(location);}}
// TIMESTAMP END 2026-11-08T21:51:01-05:00 | REVISION R000001
 }
 return {register,draw,get count(){return records.length;},get templateCount(){return templates.size;}};
}
// TIMESTAMP START 2026-11-05T05:14:11+00:00 | REVISION R000024
const sourceCache=new WeakMap();
// TIMESTAMP START 2026-11-05T09:01:08+00:00 | REVISION R000039
// TIMESTAMP START 2026-11-05T14:38:03+00:00 | REVISION R000047
function resolveSourceData(data,directory){
 const archives=data.geometryArchives||(data.geometryArchive?[{path:data.geometryArchive,sha256:data.geometryArchiveSha256}]:[]),partArchives=data.partArchives||[];
 if((!archives.length&&!partArchives.length)||(data.geometryResolved&&(!partArchives.length||data.partsResolved)))return data;
 if(data.geometryArchives&&data.geometryArchive)throw Error('Ambiguous physical archive declaration');
 if(sourceCache.has(data))return sourceCache.get(data);
 if(typeof require!=='function'||!directory)throw Error('Build must resolve compressed physical source data before browser publication');
 const fs=require('node:fs'),path=require('node:path'),zlib=require('node:zlib'),crypto=require('node:crypto'),geometry={};
 function read(archive,kind){const raw=fs.readFileSync(path.join(directory,archive.path));if(crypto.createHash('sha256').update(raw).digest('hex')!==archive.sha256)throw Error('Physical '+kind+' archive changed');return JSON.parse(zlib.gunzipSync(raw));}
 let parts=data.parts||[];
 if(partArchives.length){
  if(Object.hasOwn(data,'parts'))throw Error('Ambiguous inline and archived part records');
  const ids=new Set();parts=[];
  for(const archive of partArchives){const decoded=read(archive,'part');if(decoded.schema!=='octagon-physical-part-records-1'||decoded.parts.length!==archive.count)throw Error('Invalid physical part archive');for(const part of decoded.parts){if(ids.has(part.id))throw Error('Repeated physical part across archives');ids.add(part.id);parts.push(part);}}
 }
 for(const archive of archives){
  const decoded=read(archive,'mesh').parts;
  for(const [id,value]of Object.entries(decoded)){if(Object.hasOwn(geometry,id))throw Error('Repeated physical geometry across archives');geometry[id]=value;}
 }
 const result={...data,geometryResolved:true,...(partArchives.length?{partsResolved:true}:{}),parts:parts.map(p=>{
  if(!p.geometry_ref)return p;
  if(p.geometry_ref!==p.id||!geometry[p.id])throw Error('Missing occupied mesh '+p.id);
  const part={...p,...geometry[p.id]};delete part.geometry_ref;return part;
 })};sourceCache.set(data,result);return result;
}
// TIMESTAMP END 2026-11-05T14:38:03+00:00 | REVISION R000047
// TIMESTAMP END 2026-11-05T09:01:08+00:00 | REVISION R000039

// TIMESTAMP END 2026-11-05T05:14:11+00:00 | REVISION R000024
// TIMESTAMP START 2026-11-05T06:06:56+00:00 | REVISION R000026
const boundsCache=new WeakMap(),prototypeBounds=new WeakMap();
function rawBounds(vertices){
 const min=[Infinity,Infinity,Infinity],max=[-Infinity,-Infinity,-Infinity];
 for(const p of vertices)for(let k=0;k<3;k++){min[k]=Math.min(min[k],p[k]);max[k]=Math.max(max[k],p[k]);}
 const corners=Array.from({length:8},(_,bits)=>min.map((v,k)=>(bits&(1<<k))?max[k]:v));return {min,max,corners};
}
function bounds(part){
 const version=part.mesh_instance||part.vertices,cached=boundsCache.get(part);if(cached?.version===version)return cached.value;
 let value;
 if(part.mesh_instance){
  const prototype=part.instancePrototype;if(!prototypeBounds.has(prototype))prototypeBounds.set(prototype,rawBounds(prototype.vertices));
  const matrix=part.mesh_instance.transform;value=rawBounds(prototypeBounds.get(prototype).corners.map(p=>matrix.map(row=>row[0]*p[0]+row[1]*p[1]+row[2]*p[2]+row[3])));
 }else value=rawBounds(part.vertices||[]);
 boundsCache.set(part,{version,value});return value;
}
function rayBounds(origin,direction,box,delta=[0,0,0],limit=Infinity){
 let near=0,far=limit;
 for(let k=0;k<3;k++){
  const lo=box.min[k]+delta[k],hi=box.max[k]+delta[k];
  if(Math.abs(direction[k])<1e-15){if(origin[k]<lo||origin[k]>hi)return false;continue;}
  let a=(lo-origin[k])/direction[k],b=(hi-origin[k])/direction[k];if(a>b)[a,b]=[b,a];near=Math.max(near,a);far=Math.min(far,b);if(near>far)return false;
 }
 return far>=0;
}
function createBatchRenderer(gl,{fragmentShader}){
 // A shared draw retains each piece's own vertex range, motion and selection.
 // This changes rendering submission only; occupied meshes remain separate.
 if(!gl.getExtension('OES_element_index_uint'))return null;
 const vs=`attribute vec3 position;attribute vec3 normal;attribute vec3 delta;attribute vec4 tint;attribute vec4 edgeTint;uniform mat4 viewProjection;uniform mediump float lineMode;varying vec3 N;varying vec3 W;varying vec4 paint;void main(){W=position+delta;N=normal;paint=mix(tint,edgeTint,lineMode);gl_Position=paint.a<=0.0?vec4(2.0,2.0,2.0,1.0):viewProjection*vec4(W,1.0);}`;
 const fs=fragmentShader.replace('uniform vec3 color;','varying vec4 paint;uniform float pass;').replace('uniform float opacity;','').replace('void main(){','void main(){if(paint.a<=0.0||(pass<0.5&&paint.a<1.0)||(pass>0.5&&paint.a>=1.0))discard;vec3 color=paint.rgb;float opacity=paint.a;');
 function shader(type,source){const s=gl.createShader(type);gl.shaderSource(s,source);gl.compileShader(s);if(!gl.getShaderParameter(s,gl.COMPILE_STATUS))throw Error(gl.getShaderInfoLog(s));return s;}
 const program=gl.createProgram();gl.attachShader(program,shader(gl.VERTEX_SHADER,vs));gl.attachShader(program,shader(gl.FRAGMENT_SHADER,fs));gl.linkProgram(program);if(!gl.getProgramParameter(program,gl.LINK_STATUS))throw Error(gl.getProgramInfoLog(program));
 const a=Object.fromEntries(['position','normal','delta','tint','edgeTint'].map(n=>[n,gl.getAttribLocation(program,n)])),u=Object.fromEntries(['viewProjection','lineMode','surfaceContrast','pass'].map(n=>[n,gl.getUniformLocation(program,n)]));
 const rows=[],byId=new Map(),indices=gl.createBuffer();let dirty=true,drawCalls=0,stateUploads=0;
 function storage(){return {geometry:gl.createBuffer(),state:gl.createBuffer(),values:null,count:0};}
 const faces=storage(),lines=storage();
 function register(part,raw,edges){
  if(byId.has(part.id))throw Error('Repeated batched piece '+part.id);
// TIMESTAMP START 2026-11-08T21:51:01-05:00 | REVISION R000001
  // Viewer-owned typed buffers are immutable until replace supplies new ones.
  const row={part,raw:raw instanceof Float32Array?raw:new Float32Array(raw),edges:edges instanceof Float32Array?edges:new Float32Array(edges),state:null};rows.push(row);byId.set(part.id,row);dirty=true;
// TIMESTAMP END 2026-11-08T21:51:01-05:00 | REVISION R000001
 }
// TIMESTAMP START 2026-11-08T21:51:01-05:00 | REVISION R000001
 function replace(part,raw,edges){const row=byId.get(part.id);if(!row)throw Error('Unknown batched piece '+part.id);row.raw=raw instanceof Float32Array?raw:new Float32Array(raw);row.edges=edges instanceof Float32Array?edges:new Float32Array(edges);dirty=true;}
// TIMESTAMP END 2026-11-08T21:51:01-05:00 | REVISION R000001
 function rebuild(){
  for(const [store,key,range] of [[faces,'raw','faceRange'],[lines,'edges','edgeRange']]){
   const count=rows.reduce((sum,r)=>sum+r[key].length,0),values=new Float32Array(count);let start=0;
   for(const row of rows){values.set(row[key],start);row[range]=[start/6,row[key].length/6];start+=row[key].length;row.state=null;}
   store.count=count/6;store.values=new Float32Array(store.count*11);
   gl.bindBuffer(gl.ARRAY_BUFFER,store.geometry);gl.bufferData(gl.ARRAY_BUFFER,values,gl.STATIC_DRAW);
   gl.bindBuffer(gl.ARRAY_BUFFER,store.state);gl.bufferData(gl.ARRAY_BUFFER,store.values,gl.DYNAMIC_DRAW);
  }
  dirty=false;
 }
 function update(options){
  const changed=[];
  for(const row of rows){const p=row.part,shown=options.isShown(p),highlight=shown&&options.highlighted(p),alpha=shown?options.opacity(p):0;
   const tint=options.color(p),edge=options.edgeColor(highlight),delta=options.offset(p),state=new Float32Array([...delta,...tint,alpha,...edge,alpha&&(options.edges||highlight)?alpha:0]);
   if(row.state&&state.every((v,i)=>v===row.state[i]))continue;
   row.state=state;changed.push(row);
   for(const [store,range] of [[faces,'faceRange'],[lines,'edgeRange']]){const [start,count]=row[range];for(let v=start;v<start+count;v++)store.values.set(state,v*11);}
  }
  // Adjacent changed ranges share an upload. Orbit-only frames upload nothing.
  for(const [store,range] of [[faces,'faceRange'],[lines,'edgeRange']]){
   gl.bindBuffer(gl.ARRAY_BUFFER,store.state);let first=null,end=null;
   const flush=()=>{if(first!==null&&end>first){gl.bufferSubData(gl.ARRAY_BUFFER,first*44,store.values.subarray(first*11,end*11));stateUploads++;}};
   for(const row of changed){const [start,count]=row[range];if(first===null){first=start;end=start+count;}else if(start===end)end+=count;else{flush();first=start;end=start+count;}}
   flush();
  }
 }
 function bind(store){
  gl.bindBuffer(gl.ARRAY_BUFFER,store.geometry);for(const [name,size,start] of [['position',3,0],['normal',3,12]]){gl.enableVertexAttribArray(a[name]);gl.vertexAttribPointer(a[name],size,gl.FLOAT,false,24,start);}
  gl.bindBuffer(gl.ARRAY_BUFFER,store.state);for(const [name,size,start] of [['delta',3,0],['tint',4,12],['edgeTint',4,28]]){gl.enableVertexAttribArray(a[name]);gl.vertexAttribPointer(a[name],size,gl.FLOAT,false,44,start);}
 }
 function draw(options){
  if(dirty)rebuild();update(options);
  const ghost=options.pass==='ghost',active=rows.filter(r=>r.state[6]>0&&(ghost?r.state[6]<1:r.state[6]===1));if(!active.length)return;
  if(ghost)active.sort((x,y)=>options.distance(y.part)-options.distance(x.part));
  gl.useProgram(program);gl.uniformMatrix4fv(u.viewProjection,false,options.viewProjection);gl.uniform1f(u.surfaceContrast,options.surfaceContrast?1:0);gl.uniform1f(u.pass,ghost?1:0);
  function submit(store,range,mode){
   bind(store);
   if(ghost){const count=active.reduce((sum,r)=>sum+r[range][1],0),order=new Uint32Array(count);let at=0;for(const r of active){const [start,n]=r[range];for(let k=0;k<n;k++)order[at++]=start+k;}gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER,indices);gl.bufferData(gl.ELEMENT_ARRAY_BUFFER,order,gl.DYNAMIC_DRAW);gl.drawElements(mode,count,gl.UNSIGNED_INT,0);}
   else gl.drawArrays(mode,0,store.count);
   drawCalls++;
  }
  try{
   gl.uniform1f(u.lineMode,0);gl.enable(gl.POLYGON_OFFSET_FILL);gl.polygonOffset(1,1);
   try{submit(faces,'faceRange',gl.TRIANGLES);}finally{gl.disable(gl.POLYGON_OFFSET_FILL);}
   if(options.edges||active.some(r=>options.highlighted(r.part))){gl.uniform1f(u.lineMode,1);submit(lines,'edgeRange',gl.LINES);}
  }finally{for(const n of ['delta','tint','edgeTint'])gl.disableVertexAttribArray(a[n]);}
 }
 return {register,replace,draw,get count(){return rows.length;},get stats(){return {pieces:rows.length,vertices:faces.count,drawCalls,stateUploads};}};
}
// TIMESTAMP START 2026-11-08T21:51:01-05:00 | REVISION R000001
const api={hydrate,triangleBuffer,drawingEdges,createRenderer,createBatchRenderer,resolveSourceData,bounds,rayBounds};root.OctagonPhysicalParts=api;if(typeof module!=='undefined'&&module.exports)module.exports=api;
// TIMESTAMP END 2026-11-08T21:51:01-05:00 | REVISION R000001
// TIMESTAMP END 2026-11-05T06:06:56+00:00 | REVISION R000026
})(typeof globalThis!=='undefined'?globalThis:this);
// TIMESTAMP END 2026-11-05T04:29:18+00:00 | REVISION R000022
