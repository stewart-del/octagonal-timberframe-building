// TIMESTAMP START 2026-11-05T13:19:15+00:00 | REVISION R000044
'use strict';
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),A=require('../src/architecture.js'),P=require('../src/physical-parts.js');
const file=process.argv[2]||path.join(__dirname,'../src/architectural-solids.json'),data=P.resolveSourceData(JSON.parse(fs.readFileSync(file)),path.dirname(file));
const pieces=A.components(data);assert.strictEqual(A.components(data),pieces);assert.equal(pieces.length,data.parts.length);assert.equal(new Set(pieces.map(p=>p.id)).size,pieces.length);
const cedar=pieces.filter(p=>p.material==='cedar');assert(cedar.length>4000);for(const p of cedar){const own=pieces.filter(q=>q.is_fastener&&q.parentId===p.id);assert.equal(own.length,2,'Each individual cedar leaf owns two actual nails: '+p.id);}
const instance=pieces.find(p=>p.mesh_instance);assert.equal(typeof Object.getOwnPropertyDescriptor(instance,'vertices').get,'function');assert(instance.fastener_spec&&instance.volumeM3>0);
const compact=A.serializeScene(pieces),compactInstance=compact.parts.find(p=>p.id===instance.id);assert(!Object.hasOwn(compactInstance,'vertices'));assert(!Object.hasOwn(compactInstance,'triangles'));assert.strictEqual(compact.prototypes[instance.mesh_instance.prototype],instance.instancePrototype);assert.deepEqual(compactInstance.mesh_instance,instance.mesh_instance);
for(const p of pieces.filter(p=>p.is_fastener)){assert(p.withdrawalReceiverIds.length>0);assert(p.withdrawalReceiverIds.every(id=>p.receiverIds.includes(id)));}
const starter=pieces.find(p=>p.id==='CEDAR-MAIN0-C00-S000-N1');assert(starter.receiverIds.includes('CEDAR-MAIN0-C01-S000'));assert(!starter.withdrawalReceiverIds.includes('CEDAR-MAIN0-C01-S000'),'Later covering must block earlier nail extraction');
// TIMESTAMP START 2026-11-05T22:31:25+00:00 | REVISION R000069
assert.equal(data.closureCoreComposition.causalHardwareMetadataStatus,'SOURCE_BOUND_EARLIER_WOOD_AND_LATER_COVERS_APPLIED');
const closureFasteners=pieces.filter(p=>p.causalMetadataStatus==='SOURCE_BOUND_EARLIER_WOOD_AND_LATER_COVERS_APPLIED');assert.equal(closureFasteners.length,9415);
for(const p of closureFasteners){assert(p.causalSourcePoseSha256&&p.assemblyPrerequisiteWoodIds.length);assert(p.withdrawalReceiverIds.every(id=>!p.removalPrerequisites.includes(id)));}
const sidingNails=closureFasteners.filter(p=>/^LAP-[A-Z]+-\d+-/.test(p.parentId));assert.equal(sidingNails.length,2849);assert.equal(sidingNails.filter(p=>p.removalPrerequisites.some(id=>{const a=/^LAP-([A-Z]+)-(\d+)-/.exec(p.parentId),b=/^LAP-([A-Z]+)-(\d+)-/.exec(id);return b&&a[1]===b[1]&&Number(b[2])>Number(a[2]);})).length,2302);
// TIMESTAMP END 2026-11-05T22:31:25+00:00 | REVISION R000069
// TIMESTAMP START 2026-11-05T22:52:56+00:00 | REVISION R000070
assert.equal(data.mainRoofBarrierComposition.parts,85);assert.equal(data.mainRoofBarrierStock.roll_count,5);assert.equal(data.mainRoofBarrierStock.cuts.length,73);assert.equal(data.mainRoofBarrierComposition.currentGPSeatComposition.length,8);
assert.equal(pieces.filter(p=>p.parentRollId&&p.id.startsWith('VDSA-')&&!p.id.startsWith('VDSA-CUP-')).length,85);
// TIMESTAMP END 2026-11-05T22:52:56+00:00 | REVISION R000070
const model={parts:[{id:'P0'},{id:'PLY'}]},legacy=[{id:'OLD-WALL',schematicKind:'wall'},{id:'OLD-ROOF',schematicKind:'roofCover'},{id:'KEEP-RAIL',schematicKind:'rail'},{id:'OLD-PORCH-ROOF',mudroomRoof:true}];
const overlays=pieces.filter(p=>p.replaceExisting),overlayLegacy=overlays.map(p=>({id:p.id,schematicKind:p.schematicKind,material:p.material,oldGeometry:true}));
// TIMESTAMP START 2026-11-05T16:27:06+00:00 | REVISION R000053
// TIMESTAMP START 2026-11-05T17:43:13+00:00 | REVISION R000059
assert.equal(overlays.length,86,'Floor, porch-roof, stair and cast-pan hosts are composed exactly once');assert.equal(data.woodStairComposition.original_wood_overlays.length,4);assert.equal(data.woodStairTakeoff.linearStockCount,43);assert.equal(pieces.filter(p=>/^WOOD-STAIR-STRINGER-[1-4]$/.test(p.id)&&p.stockSectionIn?.[0]===1.5&&p.stockSectionIn?.[1]===11.25).length,4);
// TIMESTAMP END 2026-11-05T17:43:13+00:00 | REVISION R000059
// TIMESTAMP START 2026-11-05T19:06:47+00:00 | REVISION R000061
assert.equal(data.hostOverlayProofs.length,50);assert.equal(data.porchRoofComposition.host_composition.length,14);assert.equal(data.drainGrateComposition.host_composition.length,18);
assert.equal(data.cupolaRoofComposition.parts,385);assert.equal(pieces.filter(p=>p.id.startsWith('CUP-ROOF-DECK-8D-')).length,128);assert(!pieces.some(p=>p.id.startsWith('CUP-DECK-SCREW-')));assert.equal(pieces.filter(p=>p.id.startsWith('CU-DRIP-CUP-EAVE-')&&!p.is_fastener).length,8);
// TIMESTAMP START 2026-11-05T23:02:22+00:00 | REVISION R000071
assert.equal(data.cupolaRoofComposition.bearingCorrection.correctedNailPoses,48);assert.equal(data.cupolaRoofComposition.bearingCorrection.replacementCu,17);
for(const p of pieces.filter(p=>p.id.startsWith('CU-DRIP-CUP-EAVE-')&&!p.is_fastener))assert.equal(p.freshNailHoleCount,5);
// TIMESTAMP END 2026-11-05T23:02:22+00:00 | REVISION R000071
for(const p of pieces.filter(p=>p.mesh_instance))assert(data.prototypes[p.mesh_instance.prototype]);
assert.equal(new Set(pieces.filter(p=>p.mesh_instance).map(p=>p.mesh_instance.prototype)).size,Object.keys(data.prototypes).length,'Every shared prototype is used');
// TIMESTAMP END 2026-11-05T19:06:47+00:00 | REVISION R000061
const roofPegs=pieces.filter(p=>p.id.startsWith('MUD-ROOF-PEG-')||p.id.startsWith('MUD-PEG-PJ-'));assert.equal(roofPegs.length,10);assert(roofPegs.every(p=>p.vertices.length>3&&p.fastener_spec&&p.fastenerKind==='wooden peg'&&!p.intentionalFastenerPenetration));
// TIMESTAMP END 2026-11-05T16:27:06+00:00 | REVISION R000053
assert.throws(()=>A.compose(model,legacy,data),/Missing original component/);
const composed=A.compose(model,[...legacy,...overlayLegacy],data);
for(const p of overlays){const actual=composed.components.filter(q=>q.id===p.id);assert.equal(actual.length,1);assert.strictEqual(actual[0],p);assert(!actual[0].oldGeometry);}
assert(!composed.model.parts.some(p=>p.id==='PLY'));assert(composed.components.some(p=>p.id==='KEEP-RAIL'));assert(!composed.components.some(p=>p.id==='OLD-WALL'||p.id==='OLD-ROOF'||p.id==='OLD-PORCH-ROOF'));assert.throws(()=>A.compose(model,composed.components,data),/Duplicate/);
const nail={id:'N',material:'stainless steel',is_fastener:true,fastenerKind:'nail',intentionalFastenerPenetration:true,receiverIds:['WOOD','MEMBRANE','STEEL','PEG']};
assert(A.intendedFastenerContact(nail,{id:'WOOD',material:'timber'}));assert(!A.intendedFastenerContact({...nail,fastenerKind:'plate'},{id:'WOOD',material:'timber'}));assert(A.intendedFastenerContact(nail,{id:'MEMBRANE',material:'roofing felt membrane'}));assert(!A.intendedFastenerContact(nail,{id:'STEEL',material:'steel'}));assert(!A.intendedFastenerContact(nail,{id:'PEG',material:'hardwood',is_fastener:true}));assert(!A.intendedFastenerContact(nail,{id:'OTHER',material:'wood'}));
assert.equal(data.windowSchedule.units.length,14);assert(data.windowSchedule.units.every(p=>p.published.frame.length===2&&p.published.screen.length===2));
console.log(JSON.stringify({pass:true,individualPieces:pieces.length,cedarPieces:cedar.length,sharedPrototypes:Object.keys(data.prototypes).length,actualOwnedNails:true,lazyHardware:true,legacyPiecesRetired:true,strictContactPolicy:true,realWindowUnits:14}));
// TIMESTAMP END 2026-11-05T13:19:15+00:00 | REVISION R000044
