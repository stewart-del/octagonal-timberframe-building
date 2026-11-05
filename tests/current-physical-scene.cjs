// TIMESTAMP START 2026-11-05T21:07:06+00:00 | REVISION R000065
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),crypto=require('node:crypto'),{compose}=require('../scripts/current_physical_scene.cjs');
assert.throws(()=>compose({variant:'other'}),/Unknown/);
const architecturePath=process.env.ARCHITECTURE_SOURCE;
if(!architecturePath){assert.throws(()=>compose(),/ENOENT|not ready/);console.log('PASS: missing final architecture cannot become a successful physical projection.');process.exit(0);}
assert.throws(()=>compose({architecturePath}),/not ready/);
const actual=compose({architecturePath,allowStaging:true});assert.equal(actual.projection.staging,true);assert.equal(actual.projection.wholeBuildingReady,false);assert.equal(actual.parts.length,actual.projection.physicalActorCount);
assert.equal(actual.parts.filter(p=>p.isPurchasedAssemblyProxy&&p.collisionEnvelopeOnly).length,14);assert(!actual.parts.some(p=>p.windowReference));assert.equal(actual.excluded.filter(p=>p.physicalParentId).length,56);
const before=process.env.EXPECTED_SCENE&&JSON.parse(fs.readFileSync(process.env.EXPECTED_SCENE));
if(before){
 const fingerprint=scene=>{const data=scene.parts.map(p=>[p.id,p.mesh_instance||{vertices:p.vertices,triangles:p.triangles}]);return crypto.createHash('sha256').update(JSON.stringify([data,scene.prototypes])).digest('hex');};
 assert.equal(fingerprint(actual),fingerprint(before),'Every occupied vertex/triangle and rigid instance must equal the independent current readback');
}
for(const file of ['scripts/current_physical_scene.cjs','src/current-cache-bindings.js','src/wall-joinery.js','src/architecture.js','src/model-data.json','src/wall-joinery-fit.json'])assert(actual.sources[file],file+' omitted from source closure');
if(process.env.OUTPUT_SCENE)fs.writeFileSync(process.env.OUTPUT_SCENE,JSON.stringify(actual));
console.log('PASS: '+actual.parts.length+' exact physical actors, '+Object.keys(actual.prototypes).length+' prototypes, full current source closure, and explicit staging/reference accounting.');
// TIMESTAMP END 2026-11-05T21:07:06+00:00 | REVISION R000065
