// TIMESTAMP START 2026-11-04T23:48:03+00:00 | REVISION R000012
// TIMESTAMP START 2026-11-02T21:09:01-05:00 | REVISION R004877
const fs=require('fs'),assert=require('node:assert/strict');
require('../src/edge-measurements.js');require('../src/schematic-walls.js');require('../src/architectural-plans.js');
const api=global.OctagonPlans,W=require('../src/wall-joinery.js'),fit=require('../src/wall-joinery-fit.json').variants['top-entry'];
const raw=require('../src/top-entry-proposed-model.json'),model={...W.applyModel(raw,fit),wallJoinery:fit};
const snapshot=JSON.stringify(model),hash=require('crypto').createHash('sha256').update(snapshot).digest('hex');
for(const view of ['top','side']){
 const main=api.drawing(model,{view,floor:true,modelHash:hash}),porch=api.drawing(model,{view,mudroom:true,modelHash:hash});
 assert(main.parts.every(p=>p.schematicKind!=='mudroom'));assert(porch.parts.every(p=>p.schematicKind==='mudroom'));
 // TIMESTAMP START 2026-11-02T22:13:32-05:00 | REVISION R004886
 assert(porch.parts.some(p=>p.id==='MUD-RAFTER-L-2')&&porch.parts.some(p=>p.id==='MUD-PLATE-L'),'Porch framing remains present without covering layers');
 assert(porch.parts.every(p=>!p.roofLayer),'Cover toggle omits only roof skin, deck and flashing');
 // TIMESTAMP END 2026-11-02T22:13:32-05:00 | REVISION R004886
 assert(main.svg.includes('MAIN BUILDING'));assert(porch.svg.includes('PORCH'));assert(!/NaN|Infinity|undefined/.test(main.svg+porch.svg));
 assert(main.svg.includes('Model SHA-256: '+hash));assert(main.svg.includes('NOT CONSTRUCTION APPROVED'));
 assert(!/<polygon|<rect/.test(main.svg),'Sheets use hidden-line geometry');
// TIMESTAMP START 2026-11-03T12:04:27-05:00 | REVISION R005002
 // TIMESTAMP START 2026-11-04T19:48:56+00:00 | REVISION R000004
 assert.equal(main.parts.filter(p=>p.schematicKind==='floorAssembly').length,require('../src/floor-foundation-solids.json').parts.length);
 assert(main.parts.some(p=>p.floorRole==='underlayment_sheet'),'Plans include the separate underlayment sheets');
 // TIMESTAMP END 2026-11-04T19:48:56+00:00 | REVISION R000004
// TIMESTAMP END 2026-11-03T12:04:27-05:00 | REVISION R005002
 assert(main.measurements.rows.some(([k,v])=>k.includes('Underground')&&Math.abs(v-1.8288)<1e-9));
 fs.writeFileSync('/tmp/octagon-main-'+view+'.svg',main.svg);fs.writeFileSync('/tmp/octagon-porch-'+view+'.svg',porch.svg);
}
const measurements=Object.fromEntries(api.measurements(model).rows);
assert(Math.abs(measurements['Outside posts: opposite corners']/.0254-360)<1e-6);
assert(Math.abs(measurements['Opposite post centerlines']/.0254-352)<1e-6);
assert(Math.abs(measurements['Cupola clear inside diameter']/.0254-76)<1e-6);
assert(Math.abs(measurements['Short rafter J0-0 overall axial length']/.0254-139.3864162)<1e-5);
// TIMESTAMP START 2026-11-03T08:08:16-05:00 | REVISION R004938
const sitePlan=api.drawing(model,{view:'top'}).svg;
assert(sitePlan.includes('Site north ↑')&&sitePlan.includes('Porch / door face west'));
assert(!sitePlan.includes('Site bearing unverified'));
const porchLayout=require('../src/mudroom.js').build(model),siteEast=global.TimberSchematicWalls.orientation.east;
assert(Math.abs(porchLayout.outward.reduce((sum,x,i)=>sum-x*siteEast[i],0)-1)<1e-12,'Porch outward is site west');
assert(api.drawing(model,{view:'side',mudroom:true}).svg.includes('WEST ELEVATION'));
// TIMESTAMP END 2026-11-03T08:08:16-05:00 | REVISION R004938
const walls=api.drawing(model,{walls:true});assert(walls.parts.some(p=>p.wallJoineryJointIds&&p.schematicKind==='rail'));
const aids=api.drawing(model,{aids:true,hidden:true});assert(aids.parts.some(p=>p.material==='steel'));assert(aids.svg.includes('Dashed gray'));
for(const kind of ['shelf','cupolaWindow']){const d=api.drawing(model,{shelves:kind==='shelf',cupolaWindows:kind==='cupolaWindow'});assert(d.parts.some(p=>p.schematicKind===kind));}
assert.equal(snapshot,JSON.stringify(model));
console.log('PASS: separate main/porch sheets, compass alignment, exact spans and axial lengths, floor levels, fitted wall joints, provenance and nonmutation');
// TIMESTAMP END 2026-11-02T21:09:01-05:00 | REVISION R004877

// TIMESTAMP START 2026-11-03T07:12:33-05:00 | REVISION R004914
assert(!aids.parts.some(p=>p.id==='M-SP0'||p.group==='metal_spacers'),'Retired construction aid is excluded from plans');
const support=aids.parts.find(p=>p.id==='M-TMP');assert(support);assert.deepEqual(support.vertices,model.parts.find(p=>p.id==='M-TMP').vertices);
assert.equal(support.source_geometry_metadata.revision,'central-support-original-form-raised-3');
assert.equal(support.display_assumptions.steel_thickness_in,.125);assert.equal(support.display_assumptions.top_elevation_in,109);
// TIMESTAMP END 2026-11-03T07:12:33-05:00 | REVISION R004914

// TIMESTAMP START 2026-11-03T07:17:50-05:00 | REVISION R004916
for(const porch of [false,true]){const m=api.measurements(model,porch),r=m.roofSection;assert(r.run>0&&r.rise>0&&r.span>=r.run*2);assert(Math.abs(Math.hypot(r.run,r.rise)-r.slopeLength)<1e-12);assert.equal(r.angle,(Math.atan2(r.rise,r.run)*180/Math.PI).toFixed(2)+'°');const d=api.drawing(model,{view:'side',mudroom:porch});assert(d.svg.includes('DIMENSIONED HALF SECTION')&&d.svg.includes('Vertical rise'));assert(d.svg.includes('class="value"'));}
assert(measurements['Main hip R0 inclination'].endsWith('°'));assert(measurements['Radial tie T0 overall axial length']>0);assert.equal(measurements['Main post / cupola post sections'],'8 × 8 in / 6 × 6 in');

// TIMESTAMP END 2026-11-03T07:17:50-05:00 | REVISION R004916

// TIMESTAMP END 2026-11-04T23:48:03+00:00 | REVISION R000012
