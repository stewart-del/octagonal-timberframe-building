const fs=require('node:fs'),assert=require('node:assert/strict'),path=require('node:path');
const root=path.resolve(__dirname,'..');
const src=fs.readFileSync(path.join(root,'src/geometry-overlays.js'),'utf8');
const start=src.indexOf('function cavityDisplayMesh('),end=src.indexOf('\nfunction cavityRenderMesh(',start);
assert(start>=0&&end>start);
const vsub=(a,b)=>a.map((x,i)=>x-b[i]),dot=(a,b)=>a.reduce((s,x,i)=>s+x*b[i],0),cross=(a,b)=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]],length=a=>Math.hypot(...a),unit=a=>a.map(x=>x/length(a));
const clean=new Function('vsub','dot','cross','length','unit',src.slice(start,end)+';return cavityDisplayMesh;')(vsub,dot,cross,length,unit);
const edges=require('../src/edge-measurements.js');
const cavity=JSON.parse(fs.readFileSync(path.join(root,'src/cavity-data.json'),'utf8'));
const original=JSON.stringify(cavity),results=[],cleaned={};
for(const [id,record] of Object.entries(cavity.parts)){
 cleaned[id]={};
 for(const kind of ['removed','unfilled']){
  const before=record[kind],result=kind==='removed'?clean(before):{mesh:before,removedComponents:[]};cleaned[id][kind]=result.mesh;
  assert.deepEqual(result.mesh.vertices,before.vertices);
  const omitted=new Set(result.removedComponents.flat());
  assert.deepEqual(result.mesh.triangles,before.triangles.filter((_,i)=>!omitted.has(i)));
  if(result.removedComponents.length)results.push({id,kind,omittedTriangles:[...omitted],componentCount:result.removedComponents.length});
 }
}
assert.equal(JSON.stringify(cavity),original,'Source cavity records must not mutate');
const cupola=results.filter(x=>/^C[0-7]$/.test(x.id)&&x.kind==='removed');
assert.equal(cupola.length,8);assert(cupola.every(x=>x.omittedTriangles.length===4&&x.componentCount===1));
const tiny={vertices:[[0,0,0],[1,0,0],[0,1,0],[0,0,1e-16]],triangles:[[0,2,1],[0,1,3],[1,2,3],[2,0,3]]};
assert.deepEqual(clean(tiny).mesh.triangles,tiny.triangles,'Even tiny positive-volume closed shells remain');
const planarOpen={vertices:[[0,0,0],[1,0,0],[0,1,0]],triangles:[[0,1,2]]};
assert.deepEqual(clean(planarOpen).mesh.triangles,planarOpen.triangles,'Open diagnostic surfaces remain');
const cube={vertices:[[0,0,0],[1,0,0],[1,1,0],[0,1,0],[0,0,1],[1,0,1],[1,1,1],[0,1,1]],triangles:[[0,2,1],[0,3,2],[4,5,6],[4,6,7],[0,1,5],[0,5,4],[1,2,6],[1,6,5],[2,3,7],[2,7,6],[3,0,4],[3,4,7]]};
assert.equal(edges.featureEdges(cube.vertices,cube.triangles).length/12,12,'No coplanar cube diagonals drawn');
assert(src.includes('edgeRaw=TimberEdgeMeasurements.featureEdges(mesh.vertices,mesh.triangles)'));
assert(!src.includes('for(const e of m.mesh.edges)'),'Fallback must use feature edges too');
if(process.env.CAVITY_DISPLAY_OUTPUT)fs.writeFileSync(process.env.CAVITY_DISPLAY_OUTPUT,JSON.stringify(cleaned));
console.log(JSON.stringify({passed:true,scope:'Display-only removal of closed planar exact-zero-volume shells; source geometry unchanged',removed:results},null,2));
