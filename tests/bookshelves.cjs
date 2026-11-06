// TIMESTAMP START 2026-11-05T06:36:54+00:00 | REVISION R000029
'use strict';
const assert=require('node:assert/strict'),data=require('../src/bookshelf-solids.json');
const pieces=new Map(data.parts.map(p=>[p.id,p]));
assert.equal(pieces.size,214);assert.equal(data.joints.length,106);assert.equal(data.replacedSchematicIds.length,12);
assert.equal(data.parts.filter(p=>p.is_fastener).length,146);
assert.equal(data.parts.filter(p=>p.is_joinery_member).length,68);
for(const joint of data.joints){assert(pieces.has(joint.donor)&&pieces.has(joint.receiver));assert(joint.tenon_projection_m>0);}
for(const p of data.parts){
 assert.equal(p.displayRole,'shelf');assert(p.vertices.length&&p.triangles.length);
 if(p.is_fastener){assert(p.fastenerSpec.partNumber);assert(p.receiverIds.length>=2);}
 if(p.id.startsWith('BOOK-SCREW-')){assert.equal(p.fastenerSpec.partNumber,'113077');assert.equal(p.fastenerSpec.lengthIn,2);assert.equal(p.deck_penetration_in,.571);}
 if(p.is_joinery_member){assert(p.joineryStock?.vertices?.length);assert(p.minimum_blank_dimensions_in.every(x=>x>0));}
}
console.log(JSON.stringify({pass:true,pieces:pieces.size,woodMembers:68,pegs:106,cabinetScrews:40,joints:106,retiredSchematicBoards:12,capacityVerified:false}));
// TIMESTAMP END 2026-11-05T06:36:54+00:00 | REVISION R000029
