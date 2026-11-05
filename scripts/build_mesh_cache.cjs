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
const input=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
const identifier=Object.keys(input.variants)[0],value=input.variants[identifier];
const fit=input.wallJoinery.variants[identifier],model=joinery.applyModel(value.model,fit);
const foundation=require('../src/floor-foundation-solids.json');
const walls=OctagonFloorFoundation.roomLayout(model,joinery.applyLayout(TimberSchematicWalls.build(model.parts),fit),foundation);
const parts=[...model.parts,...walls.components,...roof.build(model).components,...porch.build(model).components];
const ranges={},buffers=[];
let offset=0;
for(const part of parts){
 if(ranges[part.id])throw Error('Duplicate mesh cache identifier: '+part.id);
 // Only positions travel over the network; every line vertex has normal [0,1,0].
 const raw=TimberEdgeMeasurements.featureEdges(part.vertices||[],part.triangles||[]);
 const values=new Float32Array(raw.filter((value,index)=>index%6<3));
 ranges[part.id]=[offset,values.length];offset+=values.length;
 buffers.push(Buffer.from(values.buffer));
}
fs.writeFileSync(process.argv[3]+'.bin',Buffer.concat(buffers));
fs.writeFileSync(process.argv[3]+'.json',JSON.stringify(ranges));
// TIMESTAMP END 2026-11-04T19:29:44+00:00 | REVISION R000002
// TIMESTAMP END 2026-11-04T20:33:26+00:00 | REVISION R000023

// TIMESTAMP END 2026-11-04T23:23:25+00:00 | REVISION R000011
