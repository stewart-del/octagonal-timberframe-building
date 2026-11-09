// TIMESTAMP START 2026-11-08T21:52:44-05:00 | REVISION R000001
(function(root){
'use strict';
const SCHEMA='octagon-mesh-transport-1',REFERENCE='$octagonMesh';
function decode(input){
 const isBuffer=Object.prototype.toString.call(input)==='[object ArrayBuffer]';
 if(!isBuffer&&!ArrayBuffer.isView(input))throw Error('Invalid mesh transport buffer');
 const bytes=isBuffer?new Uint8Array(input):new Uint8Array(input.buffer,input.byteOffset,input.byteLength);
 if(bytes.byteLength<4)throw Error('Incomplete mesh transport header');
 const view=new DataView(bytes.buffer,bytes.byteOffset,bytes.byteLength),size=view.getUint32(0,true),start=4+size;
 if(size===0||start%8!==0||start>bytes.byteLength)throw Error('Invalid mesh transport header length');
 let header;
 try{header=JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(bytes.subarray(4,start)));}
 catch(_){throw Error('Invalid mesh transport JSON header');}
 if(!header||typeof header!=='object'||Array.isArray(header)||header.schema!==SCHEMA||!Object.hasOwn(header,'value'))throw Error('Unknown mesh transport schema');
 if(!Number.isSafeInteger(header.byteLength)||header.byteLength<0||header.byteLength!==bytes.byteLength-start)throw Error('Invalid mesh transport body length');
 function hydrate(node,key){
  if(!node||typeof node!=='object')return node;
  if(!Array.isArray(node)&&Object.hasOwn(node,REFERENCE)){
   const range=node[REFERENCE];
   if(Object.keys(node).length!==1||!Array.isArray(range)||range.length!==4)throw Error('Invalid mesh transport reference');
   const [kind,offset,rows,columns]=range,width=kind==='f64'?8:kind==='u32'?4:0;
   if(!width||(kind==='f64'?key!=='vertices':!['triangles','faces'].includes(key)))throw Error('Invalid mesh transport numeric type');
   const length=rows*3*width;
   if(columns!==3||!Number.isSafeInteger(offset)||offset<0||offset%width!==0||!Number.isSafeInteger(rows)||rows<=0||!Number.isSafeInteger(length)||offset>header.byteLength||length>header.byteLength-offset)throw Error('Invalid mesh transport numeric range');
   const result=new Array(rows);let position=start+offset;
   for(let row=0;row<rows;row++){
    const values=new Array(3);
    for(let column=0;column<3;column++){
     const number=kind==='f64'?view.getFloat64(position,true):view.getUint32(position,true);
     if(!Number.isFinite(number))throw Error('Non-finite mesh transport coordinate');
     values[column]=number;position+=width;
    }
    result[row]=values;
   }
   return result;
  }
  if(Array.isArray(node)){
   // Scalar rows need no recursive visits or copies. Large unsupported/ragged
   // arrays retain their JSON representation and original ordering.
   for(let index=0;index<node.length;index++)if(node[index]&&typeof node[index]==='object')node[index]=hydrate(node[index]);
  }else{
   for(const name of Object.keys(node))if(node[name]&&typeof node[name]==='object')node[name]=hydrate(node[name],name);
  }
  return node;
 }
 return hydrate(header.value);
}
const api={decode};root.OctagonRuntimeTransport=api;
if(typeof module!=='undefined'&&module.exports)module.exports=api;
})(typeof globalThis!=='undefined'?globalThis:this);
// TIMESTAMP END 2026-11-08T21:52:44-05:00 | REVISION R000001
