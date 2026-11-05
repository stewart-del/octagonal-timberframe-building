// TIMESTAMP START 2026-11-04T23:23:25+00:00 | REVISION R000011
// TIMESTAMP START 2026-11-04T20:33:26+00:00 | REVISION R000023
// TIMESTAMP START 2026-11-04T19:29:44+00:00 | REVISION R000002
'use strict';
const fs=require('node:fs');
require('../src/edge-measurements.js');
require('../src/schematic-walls.js');
require('../src/floor-foundation.js');
const roof=require('../src/roof-coverings.js');
const porch=require('../src/mudroom.js');
const joinery=require('../src/wall-joinery.js');
// TIMESTAMP START 2026-11-05T12:40:59+00:00 | REVISION R000041
const architecture=require('../src/architecture.js');
// TIMESTAMP END 2026-11-05T12:40:59+00:00 | REVISION R000041
const input=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
const identifier=Object.keys(input.variants)[0],value=input.variants[identifier];
// TIMESTAMP START 2026-11-05T12:40:59+00:00 | REVISION R000041
const fit=input.wallJoinery.variants[identifier],fittedModel=joinery.applyModel(value.model,fit);
// TIMESTAMP END 2026-11-05T12:40:59+00:00 | REVISION R000041
// TIMESTAMP START 2026-11-05T06:13:38+00:00 | REVISION R000027
const foundation=input.foundation||require('../src/floor-foundation-solids.json');
// TIMESTAMP START 2026-11-05T12:40:59+00:00 | REVISION R000041
const model=architecture.applyModel(fittedModel,foundation.architecture);
// TIMESTAMP END 2026-11-05T12:40:59+00:00 | REVISION R000041
const onlyIds=input.onlyIds?new Set(input.onlyIds):null;
// TIMESTAMP END 2026-11-05T06:13:38+00:00 | REVISION R000027
const walls=OctagonFloorFoundation.roomLayout(model,joinery.applyLayout(TimberSchematicWalls.build(model.parts),fit),foundation);
// TIMESTAMP START 2026-11-05T12:40:59+00:00 | REVISION R000041
const composed=architecture.compose(model,[...walls.components,...roof.build(model).components,...porch.build(model).components],foundation.architecture);
const parts=[...composed.model.parts,...composed.components];
// TIMESTAMP END 2026-11-05T12:40:59+00:00 | REVISION R000041
// TIMESTAMP START 2026-11-05T13:07:26+00:00 | REVISION R000043
const excluded=new Set(input.excludeIds||[]);
// TIMESTAMP END 2026-11-05T13:07:26+00:00 | REVISION R000043
const ranges={},buffers=[];
let offset=0;
for(const part of parts){
 // TIMESTAMP START 2026-11-05T06:13:38+00:00 | REVISION R000027
// TIMESTAMP START 2026-11-05T13:07:26+00:00 | REVISION R000043
 if((onlyIds&&!onlyIds.has(part.id))||excluded.has(part.id)||part.mesh_instance)continue;
 // Instanced hardware computes feature edges once from its shared prototype
 // in the renderer; no repeated world-space nail edge payload is needed.
// TIMESTAMP END 2026-11-05T13:07:26+00:00 | REVISION R000043
 // TIMESTAMP END 2026-11-05T06:13:38+00:00 | REVISION R000027
 if(ranges[part.id])throw Error('Duplicate mesh cache identifier: '+part.id);
 // Only positions travel over the network; every line vertex has normal [0,1,0].
 // TIMESTAMP START 2026-11-05T06:13:38+00:00 | REVISION R000027
// TIMESTAMP START 2026-11-05T13:07:26+00:00 | REVISION R000043
 const raw=TimberEdgeMeasurements.featureEdges(part.vertices||[],part.triangles||[]);
// TIMESTAMP END 2026-11-05T13:07:26+00:00 | REVISION R000043
 // TIMESTAMP END 2026-11-05T06:13:38+00:00 | REVISION R000027
 const values=new Float32Array(raw.filter((value,index)=>index%6<3));
 ranges[part.id]=[offset,values.length];offset+=values.length;
 buffers.push(Buffer.from(values.buffer));
}
fs.writeFileSync(process.argv[3]+'.bin',Buffer.concat(buffers));
fs.writeFileSync(process.argv[3]+'.json',JSON.stringify(ranges));
// TIMESTAMP END 2026-11-04T19:29:44+00:00 | REVISION R000002
// TIMESTAMP END 2026-11-04T20:33:26+00:00 | REVISION R000023

// TIMESTAMP END 2026-11-04T23:23:25+00:00 | REVISION R000011
