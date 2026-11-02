'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const crypto=require('node:crypto');
const {analyse,edgeMeasurementData,edgeMeasurementText,edgeMeasurementDescription,featureEdges}=require('../src/edge-measurements.js');
const near=(a,b,e=1e-7)=>assert.ok(Math.abs(a-b)<e,`${a} != ${b}`);
function cube(){
  return {id:'CUBE',vertices:[[0,0,0],[1,0,0],[1,1,0],[0,1,0],[0,0,1],[1,0,1],[1,1,1],[0,1,1]],
    triangles:[[0,2,1],[0,3,2],[4,5,6],[4,6,7],[0,1,5],[0,5,4],[1,2,6],[1,6,5],[2,3,7],[2,7,6],[3,0,4],[3,4,7]]};
}
const original=cube(),before=JSON.stringify(original),box=analyse(original.vertices,original.triangles);
assert.equal(box.edges.length,12);assert.equal(box.topology.closedConsistent,true);
for(const e of box.edges){near(e.length_m,1);near(e.length_in,1/.0254);near(e.planeAngleDeg,90);near(e.interiorAngleDeg,90);}
assert.equal(JSON.stringify(original),before,'source geometry must remain unchanged');
assert.equal(featureEdges(original.vertices,original.triangles).length,12*12);
assert.equal(edgeMeasurementData(original)[0].timber_id,'CUBE');
assert.equal(edgeMeasurementData(original)[0].id,'E001');
assert.match(edgeMeasurementText(edgeMeasurementData(original)[0]),/90° inside/);
assert.match(edgeMeasurementDescription(edgeMeasurementData(original)[0]),/not saw settings/);

// One face is subdivided with a midpoint on an adjacent face's long edge.
// Both the triangle diagonal and the planar T-junction must disappear.
const tj=cube();tj.vertices.push([.5,0,0]);
tj.triangles=tj.triangles.filter((_,i)=>i!==0&&i!==1);
tj.triangles.push([0,3,8],[8,3,2],[8,2,1]);
const split=analyse(tj.vertices,tj.triangles);
assert.equal(split.edges.length,12);assert.equal(split.topology.closedConsistent,true);
for(const e of split.edges){near(e.length_m,1);near(e.interiorAngleDeg,90);}

// Exact welded coordinates across a cell boundary, still below 1 µm apart.
const duplicates=cube();
duplicates.vertices.push([1+2e-7,0,0]);
duplicates.triangles=duplicates.triangles.map(t=>t.map(i=>i===1?8:i));
const welded=analyse(duplicates.vertices,duplicates.triangles);
assert.equal(welded.edges.length,12);assert.equal(welded.topology.closedConsistent,true);

// Concave L-section extruded in Z; material-side reflex edge must read 270°.
const outline=[[0,0],[2,0],[2,1],[1,1],[1,2],[0,2]];
const concave={vertices:[...outline.map(([x,y])=>[x,y,0]),...outline.map(([x,y])=>[x,y,1])],triangles:[]};
const caps=[[0,1,3],[1,2,3],[0,3,5],[3,4,5]];
for(const t of caps){concave.triangles.push([t[2],t[1],t[0]],t.map(i=>i+6));}
for(let i=0;i<6;i++){const j=(i+1)%6;concave.triangles.push([i,j,j+6],[i,j+6,i+6]);}
const l=analyse(concave.vertices,concave.triangles);
assert.equal(l.edges.length,18);assert.equal(l.topology.closedConsistent,true);
const reflex=l.edges.filter(e=>e.interiorAngleDeg>180);
assert.equal(reflex.length,1);near(reflex[0].interiorAngleDeg,270);near(reflex[0].planeAngleDeg,90);

// Globally reversed winding remains a closed shell and has the same interior.
const reversed=cube();reversed.triangles=reversed.triangles.map(t=>t.slice().reverse());
const inward=analyse(reversed.vertices,reversed.triangles);
assert.equal(inward.topology.closedConsistent,true);
for(const e of inward.edges)near(e.interiorAngleDeg,90);

// Missing or inconsistently wound faces must never claim interior angles.
const open=cube();open.triangles.pop();const openResult=analyse(open.vertices,open.triangles);
assert.equal(openResult.topology.closedConsistent,false);assert.ok(openResult.edges.every(e=>e.interiorAngleDeg===null));
const bad=cube();bad.triangles[0].reverse();const badResult=analyse(bad.vertices,bad.triangles);
assert.equal(badResult.topology.closedConsistent,false);assert.ok(badResult.edges.every(e=>e.interiorAngleDeg===null));

// Coplanar square: only its four open boundary segments, no diagonal.
const square=analyse([[0,0,0],[1,0,0],[1,1,0],[0,1,0]],[[0,1,2],[0,2,3]]);
assert.equal(square.edges.length,4);assert.ok(square.edges.every(e=>e.planeAngleDeg===null));

const modelBytes=fs.readFileSync(path.join(__dirname,'../src/model-data.json'));
const model=JSON.parse(modelBytes);
const statistics=[];
const started=performance.now();
for(const part of model.parts){
  const id=part.id,unchanged=JSON.stringify(part);
  const result=analyse(part.vertices,part.triangles);
  assert.ok(result.edges.length>0);
  assert.ok(result.edges.every(e=>Number.isFinite(e.length_in)&&e.length_in>0));
  assert.ok(result.edges.every(e=>e.planeAngleDeg===null||(e.planeAngleDeg>=0&&e.planeAngleDeg<=90)));
  assert.equal(JSON.stringify(part),unchanged);
  statistics.push({id,edges:result.edges.length,interiorAngles:result.edges.filter(e=>e.interiorAngleDeg!==null).length,
    reflexEdges:result.edges.filter(e=>e.interiorAngleDeg>180).length,
    minLengthIn:Math.min(...result.edges.map(e=>e.length_in)),maxLengthIn:Math.max(...result.edges.map(e=>e.length_in)),
    minPlaneAngleDeg:Math.min(...result.edges.map(e=>e.planeAngleDeg).filter(a=>a!==null)),
    maxPlaneAngleDeg:Math.max(...result.edges.map(e=>e.planeAngleDeg).filter(a=>a!==null)),
    minInteriorAngleDeg:Math.min(...result.edges.map(e=>e.interiorAngleDeg).filter(a=>a!==null)),
    maxInteriorAngleDeg:Math.max(...result.edges.map(e=>e.interiorAngleDeg).filter(a=>a!==null)),...result.topology});
}
console.log('PASS: cube12×90°, T-junction seam suppression, welds, concave270°, reversed winding, unknown open/inconsistent interiors, no planar diagonals, original geometry unchanged.');
const summary={timbers:statistics.length,featureEdges:statistics.reduce((s,x)=>s+x.edges,0),
  interiorAngles:statistics.reduce((s,x)=>s+x.interiorAngles,0),closedConsistentTimbers:statistics.filter(x=>x.closedConsistent).length,
  minimumEdges:Math.min(...statistics.map(x=>x.edges)),maximumEdges:Math.max(...statistics.map(x=>x.edges)),
  reflexEdges:statistics.reduce((s,x)=>s+x.reflexEdges,0),
  minLengthIn:Math.min(...statistics.map(x=>x.minLengthIn)),maxLengthIn:Math.max(...statistics.map(x=>x.maxLengthIn)),
  minPlaneAngleDeg:Math.min(...statistics.map(x=>x.minPlaneAngleDeg)),maxPlaneAngleDeg:Math.max(...statistics.map(x=>x.maxPlaneAngleDeg)),
  minInteriorAngleDeg:Math.min(...statistics.map(x=>x.minInteriorAngleDeg)),maxInteriorAngleDeg:Math.max(...statistics.map(x=>x.maxInteriorAngleDeg)),
  allModelAnalysisMs:performance.now()-started};
console.log(JSON.stringify(summary,null,2));
fs.writeFileSync(path.join(__dirname,'../public/review/edge-model-audit.json'),JSON.stringify({source_sha256:crypto.createHash('sha256').update(modelBytes).digest('hex'),summary,parts:statistics},null,2)+'\n');
