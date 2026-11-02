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
 // TIMESTAMP START 2026-11-02T09:17:47-05:00 | REVISION R004755
 assert(!Object.hasOwn(record,'unfilled'),'Unreliable residual diagnostic meshes must not be exported');
 assert(!Object.hasOwn(record,'occupied_volume_m3'),'Unreliable occupancy volumes must not be exported');
 for(const kind of ['removed']){
  const before=record[kind],result=clean(before);cleaned[id][kind]=result.mesh;
 // TIMESTAMP END 2026-11-02T09:17:47-05:00 | REVISION R004755
  assert.deepEqual(result.mesh.vertices,before.vertices);
  const omitted=new Set(result.removedComponents.flat());
  assert.deepEqual(result.mesh.triangles,before.triangles.filter((_,i)=>!omitted.has(i)));
  if(result.removedComponents.length)results.push({id,kind,omittedTriangles:[...omitted],componentCount:result.removedComponents.length});
 }
}
assert.equal(JSON.stringify(cavity),original,'Source cavity records must not mutate');
// TIMESTAMP START 2026-11-02T08:55:04-05:00 | REVISION R004751
assert.equal(results.length,0,'Corrected cavity exports need no zero-volume display cleanup');
const planarClosed={vertices:[[0,0,0],[1,0,0],[0,1,0],[.2,.2,0]],triangles:[[0,2,1],[0,1,3],[1,2,3],[2,0,3]]};
const syntheticClean=clean(planarClosed);
assert.equal(syntheticClean.removedComponents.length,1,'Synthetic closed planar zero-volume shell removed');
assert.equal(syntheticClean.mesh.triangles.length,0);
// TIMESTAMP END 2026-11-02T08:55:04-05:00 | REVISION R004751
const tiny={vertices:[[0,0,0],[1,0,0],[0,1,0],[0,0,1e-16]],triangles:[[0,2,1],[0,1,3],[1,2,3],[2,0,3]]};
assert.deepEqual(clean(tiny).mesh.triangles,tiny.triangles,'Even tiny positive-volume closed shells remain');
const planarOpen={vertices:[[0,0,0],[1,0,0],[0,1,0]],triangles:[[0,1,2]]};
assert.deepEqual(clean(planarOpen).mesh.triangles,planarOpen.triangles,'Open diagnostic surfaces remain');
const cube={vertices:[[0,0,0],[1,0,0],[1,1,0],[0,1,0],[0,0,1],[1,0,1],[1,1,1],[0,1,1]],triangles:[[0,2,1],[0,3,2],[4,5,6],[4,6,7],[0,1,5],[0,5,4],[1,2,6],[1,6,5],[2,3,7],[2,7,6],[3,0,4],[3,4,7]]};
assert.equal(edges.featureEdges(cube.vertices,cube.triangles).length/12,12,'No coplanar cube diagonals drawn');
assert(src.includes('edgeRaw=TimberEdgeMeasurements.featureEdges(mesh.vertices,mesh.triangles)'));
assert(!src.includes('for(const e of m.mesh.edges)'),'Fallback must use feature edges too');
if(process.env.CAVITY_DISPLAY_OUTPUT)fs.writeFileSync(process.env.CAVITY_DISPLAY_OUTPUT,JSON.stringify(cleaned));
// TIMESTAMP START 2026-11-02T08:55:04-05:00 | REVISION R004751
const hash=file=>require('node:crypto').createHash('sha256').update(fs.readFileSync(path.join(root,file))).digest('hex');
const modelHash=hash('src/model-data.json'),baselineHash='36e53d90ec9abead9a80ce87e61f298c527809818dac82b8e2bbf5bf84b25779';
// TIMESTAMP START 2026-11-02T09:17:47-05:00 | REVISION R004755
const verification={revision:'R004755',timestamp:'2026-11-02T09:17:47-05:00',passed:true,all_cavity_records_checked:Object.keys(cavity.parts).length,
 model_sha256:modelHash,pre_cavity_correction_model_sha256:baselineHash,model_bytes_unchanged:modelHash===baselineHash,cavity_source_sha256:hash('src/cavity-data.json'),
 changed_display_records:results,removed_overlay_components:results,
 scope:'Removed-only source cavities require no display filtering. No residual diagnostic geometry or occupancy volume is exported. Model hash comparison establishes byte identity for this cavity correction only. This test is not a complete cavity-closure or structural certification.',
 renderer_checks:['Source records not mutated','Corrected removed cavities retain every triangle','Synthetic closed planar exact-zero-volume shell removed','Tiny positive-volume shell retained','Open planar diagnostic surface retained','Feature edges used by WebGL and fallback','Cube has twelve feature edges','No residual diagnostic geometry or occupancy volume exported'],
 lower_cupola_regression:'tests/test_joinery.py independently checks all eight raw lower cavity components against the 2 × 2 × 8 inch box and mating timber exports.'};
// TIMESTAMP END 2026-11-02T09:17:47-05:00 | REVISION R004755
if(process.env.CAVITY_VERIFICATION_OUTPUT)fs.writeFileSync(process.env.CAVITY_VERIFICATION_OUTPUT,JSON.stringify(verification,null,2)+'\n');
console.log(JSON.stringify(verification,null,2));
// TIMESTAMP END 2026-11-02T08:55:04-05:00 | REVISION R004751
