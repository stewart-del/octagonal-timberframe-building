// TIMESTAMP START 2026-11-04T23:48:03+00:00 | REVISION R000012
// TIMESTAMP START 2026-11-03T12:04:27-05:00 | REVISION R005002
const fs=require('node:fs');
// Reuse the viewer's DOM/WebGL harness, then exercise the current integrated
// selection and picking code rather than duplicating its implementation.
const harness=fs.readFileSync(__dirname+'/check_viewer.cjs','utf8').split('const test=`')[0];
const checks=`
function check(value,message){if(!value)throw Error(message)}
window.location.search='';
const floorMembers=schematicParts.filter(p=>['floor','floorAssembly'].includes(p.schematicKind));
// TIMESTAMP START 2026-11-04T19:48:56+00:00 | REVISION R000004
check(floorMembers.length===FLOOR_FOUNDATION_DATA.parts.length+8,'Every structural/foundation zone, underlayment sheet and bamboo sector must exist');
const firstSheet=floorMembers.find(p=>p.floorRole==='underlayment_sheet');check(!!firstSheet,'Underlayment sheets exist');
// TIMESTAMP END 2026-11-04T19:48:56+00:00 | REVISION R000004
for(const p of floorMembers){
 isolatedId=null;selectPart(p.id);
 check(selected===logicalPieceId(p.id),'Selection failed for '+p.id);
 check(partById.has(p.id),'Inspection registry excludes '+p.id);
 check(isShown(p),'Selection did not enable correct floor layer for '+p.id);
 const text=node=>node.textContent+' '+node.children.map(text).join(' ');
 check(!/undefined|NaN/.test(text($('selection'))),'Invalid floor inspector for '+p.id);
}
// TIMESTAMP START 2026-11-04T19:48:56+00:00 | REVISION R000004
for(const id of ['SCHEM-FLOOR-SECTOR-0','FLOOR-BAMBOO-CENTER-0',firstSheet.id,'FLOOR-JOIST-NS-E0','FLOOR-BEAM-0','FLOOR-CENTRAL-HUB','PIER-MID-0','PIER-MID-0-BELOW']){
// TIMESTAMP END 2026-11-04T19:48:56+00:00 | REVISION R000004
 const p=partById.get(id);isolateAndCenter(p);matrix();
 const triangle=p.triangles[0].map(i=>vadd(p.vertices[i],offset(p))),center=triangle.reduce((a,b)=>vadd(a,vmul(b,1/3)),[0,0,0]),point=project(center);
 check(point,'Projected floor surface missing '+id);selected=null;selectedPartIds.clear();pick(point.x,point.y);
 check(selected===logicalPieceId(id),'Ray picking failed for '+id);
}
const lower=partById.get('PIER-MID-0-BELOW');selectPart(lower.id);
check(columnSegments(lower).length===2,'Midpoint pier must select both opacity zones');
check(Math.abs(columnBounds(lower).max[1]-columnBounds(lower).min[1]-8*.3048)<1e-9,'Full midpoint column height');
selectPart('FLOOR-BEAM-0');selectPart('FLOOR-JOIST-NS-E0',true);
check(selectedPartIds.size===2,'Floor shift-selection must retain both members');
isolatedId=null;renderList();
check($('partList').children.some(row=>row.children.some(b=>b.dataset.focusKey==='select:FLOOR-BEAM-0')),'Floor members must also be selectable in the list');
console.log('PASS: every floor component selects; finish/subfloor/joists/beams/hub/piers ray-pick; midpoint piers stay continuous');
`;
new Function('require','__dirname',harness+'\nvm.runInContext(script+"\\n"+'+JSON.stringify(checks)+',context);')(require,__dirname);
// TIMESTAMP END 2026-11-03T12:04:27-05:00 | REVISION R005002

// TIMESTAMP END 2026-11-04T23:48:03+00:00 | REVISION R000012
