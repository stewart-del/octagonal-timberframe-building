const fs=require('fs'),assert=require('assert');
require('../src/edge-measurements.js');require('../src/schematic-walls.js');require('../src/architectural-plans.js');
const model=JSON.parse(fs.readFileSync(process.argv[2]||require('path').join(__dirname,'../src/model-data.json'))),api=global.OctagonPlans;
const hash=require('crypto').createHash('sha256').update(JSON.stringify(model)).digest('hex');
for(const view of ['top','side']){const d=api.drawing(model,{view});assert(d.parts.every(p=>p.material!=='steel'&&p.material!=='surface'&&!p.temporary));assert(d.parts.some(p=>p.material==='plywood'));assert(!/NaN|Infinity|undefined/.test(d.svg));assert(d.svg.includes('NOT CONSTRUCTION APPROVED'));assert(!/<polygon|<rect/.test(d.svg),'No shaded solid geometry');const axis=view==='top'?2:1;assert(d.svg.includes(api.measure(d.bounds.size[0])));assert(d.svg.includes(api.measure(d.bounds.size[axis])));fs.writeFileSync('/tmp/octagon-'+view+'-plan.svg',d.svg);}
const aids=api.drawing(model,{view:'side',aids:true,hidden:true});assert(aids.parts.some(p=>p.material==='steel'));assert(!aids.parts.some(p=>p.material==='surface'));assert(aids.svg.includes('construction aids included'));assert(aids.svg.includes('Dashed gray'));
assert.deepStrictEqual(api.project([2,3,4],'top'),[2,-4,3]);assert.deepStrictEqual(api.project([2,3,4],'side'),[2,-3,4]);assert.equal(hash,require('crypto').createHash('sha256').update(JSON.stringify(model)).digest('hex'));
console.log('PASS: canonical mesh orthographic projections, conditional bounds, default exclusions, temporary inclusion, pure non-mutating geometry, SVG output');
const topAxes=api.drawing(model,{view:'top'}).svg;
assert(topAxes.includes('+Z ↑ (model axis)'));
assert(!topAxes.includes('+Z ↓'));

for(const kind of ['wall','shelf','cupolaWindow']){const opts={view:'top',walls:kind==='wall',shelves:kind==='shelf',cupolaWindows:kind==='cupolaWindow'},d=api.drawing(model,opts);assert(d.parts.some(p=>p.schematicKind===kind));assert(!d.parts.some(p=>p.schematicKind&&!(kind==='wall'?['wall','rail','footer']:[kind]).includes(p.schematicKind)));}
for(const view of ['top','side']){const d=api.drawing(model,{view,walls:true,shelves:true,cupolaWindows:true,hidden:true});fs.writeFileSync('/tmp/octagon-walls-'+view+'.svg',d.svg);assert(d.svg.includes('cupola windows ON'));}
assert(api.drawing(model,{view:'top'}).svg.includes('Site bearing unverified'));
console.log('PASS: three independent schematic plan layers, shared design compass, unchanged canonical geometry');

const floor=api.drawing(model,{view:'top',floor:true});assert(floor.parts.filter(p=>p.schematicKind==='floor').length===8);assert(floor.parts.filter(p=>p.schematicKind==='floorAssembly').length===139);assert(!floor.parts.some(p=>p.schematicKind&&!['floor','floorAssembly'].includes(p.schematicKind)));assert(floor.svg.includes('floor/grate ON'));

// Provenance must be visible in the exported sheet, not only an internal cache key.
for(const view of ['top','side']){const sheet=api.drawing(model,{view,modelHash:hash});assert(sheet.svg.includes('Model SHA-256: '+hash));assert(sheet.svg.includes(view==='top'?'Sheet GEOM-TOP':'Sheet GEOM-SIDE'));}
