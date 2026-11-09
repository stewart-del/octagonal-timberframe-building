// TIMESTAMP START 2026-11-08T21:52:44-05:00 | REVISION R000001
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),{performance}=require('node:perf_hooks');
const {decode}=require('../src/runtime-transport.js');
const REF='$octagonMesh',SCHEMA='octagon-mesh-transport-1';
function envelope(value,binary=Buffer.alloc(0),patch={}){
 const raw=Buffer.from(JSON.stringify({schema:SCHEMA,byteLength:binary.length,value,...patch})),padding=Buffer.alloc((-(4+raw.length))&7,32),length=Buffer.alloc(4);
 length.writeUInt32LE(raw.length+padding.length);return Buffer.concat([length,raw,padding,binary]);
}
function reference(kind='f64',offset=0,rows=1,columns=3){return {[REF]:[kind,offset,rows,columns]};}

if(process.argv[2]==='--check'){
 const source=fs.readFileSync(process.argv[3],'utf8'),transport=fs.readFileSync(0);
 let start=performance.now();const expected=JSON.parse(source),parseMs=performance.now()-start;
 start=performance.now();const actual=decode(transport),decodeMs=performance.now()-start;
 assert.deepStrictEqual(actual,expected);
 assert.equal(JSON.stringify(actual),JSON.stringify(expected),'Property and array ordering is retained');
 console.log(JSON.stringify({pass:true,sourceBytes:Buffer.byteLength(source),transportBytes:transport.length,parseMs,decodeMs}));
}else{
 const bytes=Buffer.alloc(24);bytes.writeDoubleLE(-0,0);bytes.writeDoubleLE(1.0000000000000002,8);bytes.writeDoubleLE(5e-324,16);
 const value=decode(envelope({one:{vertices:reference()},two:{vertices:reference()}} ,bytes));
 assert(Object.is(value.one.vertices[0][0],-0));
 assert.equal(value.one.vertices[0][1],1.0000000000000002);assert.equal(value.one.vertices[0][2],5e-324);
 assert.notStrictEqual(value.one.vertices,value.two.vertices);assert.notStrictEqual(value.one.vertices[0],value.two.vertices[0]);
 value.one.vertices[0][1]=99;assert.equal(value.two.vertices[0][1],1.0000000000000002,'Repeated ranges remain independently mutable');
 const indices=Buffer.alloc(12);indices.writeUInt32LE(4294967295,8);
 assert.deepStrictEqual(decode(envelope({triangles:reference('u32')},indices)).triangles,[[0,0,4294967295]]);
 const aligned=envelope({vertices:reference()},bytes),unaligned=Buffer.concat([Buffer.alloc(1),aligned]).subarray(1);
 assert.deepStrictEqual(decode(unaligned),decode(aligned),'Buffer views need not start on an aligned native address');
 assert.deepStrictEqual(decode(aligned.buffer.slice(aligned.byteOffset,aligned.byteOffset+aligned.length)),decode(aligned));
 assert.throws(()=>decode('not bytes'),/buffer/);
 for(const count of [0,1,2,3])assert.throws(()=>decode(Buffer.alloc(count)),/Incomplete/);
 const wrongLength=Buffer.from(aligned);wrongLength.writeUInt32LE(7,0);assert.throws(()=>decode(wrongLength),/header length/);
 const tooLong=Buffer.from(aligned);tooLong.writeUInt32LE(0xfffffff4,0);assert.throws(()=>decode(tooLong),/header length/);
 const wrongJSON=Buffer.from(aligned);wrongJSON[4]=0xff;assert.throws(()=>decode(wrongJSON),/JSON header/);
 assert.throws(()=>decode(envelope(null,Buffer.alloc(0),{schema:'unknown'})),/schema/);
 for(const byteLength of [-1,0.5,1,Number.MAX_SAFE_INTEGER])assert.throws(()=>decode(envelope(null,Buffer.alloc(0),{byteLength})),/body length/);
 assert.throws(()=>decode(aligned.subarray(0,-1)),/body length/);
 assert.throws(()=>decode(Buffer.concat([aligned,Buffer.alloc(1)])),/body length/);
 for(const ref of [reference('f32'),reference('u32'),reference('f64',-8),reference('f64',4),reference('f64',24),reference('f64',0,0),reference('f64',0,-1),reference('f64',0,1.1),reference('f64',0,Number.MAX_SAFE_INTEGER),reference('f64',0,2),reference('f64',0,1,2),{[REF]:['f64',0,1]},{[REF]:['f64',0,1,3],extra:true}]){
  assert.throws(()=>decode(envelope({vertices:ref},bytes)),/mesh transport/);
 }
 assert.throws(()=>decode(envelope({other:reference()},bytes)),/numeric type/);
 for(const number of [NaN,Infinity,-Infinity]){const invalid=Buffer.from(bytes);invalid.writeDoubleLE(number,0);assert.throws(()=>decode(envelope({vertices:reference()},invalid)),/Non-finite/);}
 console.log(JSON.stringify({pass:true,checks:'Float64 precision and signed zero; Uint32 extremes; independent repeated meshes; aligned and unaligned views; malformed headers, types, ranges and truncation rejected'}));
}
// TIMESTAMP END 2026-11-08T21:52:44-05:00 | REVISION R000001
