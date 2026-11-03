'use strict';
const assert=require('node:assert'),api=require('../src/display-presets.js');
const examples={temporary:{id:'M-TMP',temporary:true,material:'steel'},foundation:{id:'PIER-0',schematicKind:'floorAssembly',material:'concrete'},stand:{id:'POST-BEARING-STAND-0-HEAD',schematicKind:'floorAssembly',material:'steel proposal'},cleat:{id:'future-cleat',displayRole:'floorStructure'},joist:{id:'FLOOR-JOIST-0-1',schematicKind:'floorAssembly',material:'wood'},finish:{id:'FLOOR-BAMBOO-CENTER-0',schematicKind:'floorAssembly',material:'strand-woven bamboo'},rail:{schematicKind:'rail'},wall:{schematicKind:'wall'},shelf:{schematicKind:'shelf'},window:{schematicKind:'cupolaWindow'},roof:{schematicKind:'roofCover'},post:{group:'cupola_posts'},grate:{schematicKind:'grate'},reference:{group:'roof_envelope'},ply:{group:'cupola_plywood'},frame:{group:'braces',is_timber:true}};
// TIMESTAMP START 2026-11-02T20:27:45-05:00 | REVISION R004866
for(const key of ['temporary','grate','reference'])for(const preset of Object.keys(api.PRESETS))assert.equal(api.included(examples[key],preset),key==='temporary'&&preset==='complete');
// TIMESTAMP END 2026-11-02T20:27:45-05:00 | REVISION R004866
for(const key of ['foundation','stand','cleat','joist','rail','post','frame'])assert(api.included(examples[key],'skeleton'),key);
for(const key of ['finish','wall','shelf','window','roof','ply'])assert(!api.included(examples[key],'skeleton'),key);
for(const key of ['foundation','stand','post'])assert(api.included(examples[key],'foundation'));
for(const key of ['frame','roof','joist'])assert(!api.included(examples[key],'foundation'));
for(const key of ['foundation','stand','joist','finish','cleat'])assert(api.included(examples[key],'floor'));
const fs=require('fs'),model=JSON.parse(fs.readFileSync(__dirname+'/../src/model-data.json')),solids=JSON.parse(fs.readFileSync(__dirname+'/../src/floor-foundation-solids.json'));
// TIMESTAMP START 2026-11-02T20:27:45-05:00 | REVISION R004866
assert(model.parts.filter(p=>api.included(p,'complete')).every(p=>!p.temporary||p.id==='M-TMP'));
assert(api.included(model.parts.find(p=>p.id==='M-TMP'),'complete'));
// TIMESTAMP END 2026-11-02T20:27:45-05:00 | REVISION R004866
assert(solids.parts.every(p=>api.included(p,'complete')));
assert(solids.parts.filter(p=>api.role(p)==='floorFinish').length>0);
console.log('PASS: semantic permanent-building presets, independent foundations/structure/finish, temporary and deferred exclusions');
// TIMESTAMP START 2026-11-02T20:19:08-05:00 | REVISION R004863
const porch=require('../src/mudroom.js').build(model).components;
for(const prefix of ['MUD-POST-','MUD-RAFTER-','MUD-BRACE-','MUD-PEG-','MUD-SUPPORT-']){
 const members=porch.filter(p=>p.id.startsWith(prefix));assert(members.length>0,prefix);assert(members.every(p=>api.included(p,'skeleton')),prefix);
}
assert(porch.filter(p=>p.roofLayer||p.mudroomRole==='furniture').every(p=>!api.included(p,'skeleton')));
assert(porch.every(p=>api.included(p,'complete')));
console.log('PASS: actual porch posts, rafters, braces, pegs and supports remain in Skeleton');
// TIMESTAMP END 2026-11-02T20:19:08-05:00 | REVISION R004863

// TIMESTAMP START 2026-11-03T07:01:25-05:00 | REVISION R004903
for(const role of ['floor','stair']){const rows=porch.filter(p=>p.mudroomRole===role);assert(rows.length>0);assert(rows.every(p=>api.included(p,'skeleton')),role);}
// TIMESTAMP END 2026-11-03T07:01:25-05:00 | REVISION R004903
