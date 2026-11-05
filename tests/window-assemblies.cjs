// TIMESTAMP START 2026-11-05T17:09:28+00:00 | REVISION R000057
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),W=require('../src/window-assemblies.js'),inventory=require('../src/component-inventory.js');
const data=JSON.parse(fs.readFileSync(process.argv[2]||'/workspace/timberframe-next-step/window-assemblies-composed.json')),references=data.parts.filter(p=>p.windowReference),units=data.opening.units;
assert.equal(data.parts.length,70);assert.equal(units.length,14);assert.equal(references.length,56);
for(const unit of units){
 const moving=references.find(p=>p.id===unit.unitId+'-SASH'),closed=W.pose(moving,0),opened=W.pose(moving,1);for(let i=0;i<closed.length;i++)for(let k=0;k<3;k++)assert(Math.abs(closed[i][k]-moving.vertices[i][k])<1e-12);
 for(const i of [2,3])assert(Math.hypot(...closed[i].map((x,k)=>x-opened[i][k]))<1e-12,'Published top edge stays on the display hinge axis');
 const normal=unit.localFrame3x4.map(row=>row[2]),outward=opened[0].reduce((sum,x,k)=>sum+(x-closed[0][k])*normal[k],0);assert(Math.abs(outward/.0254-5.88)<1e-10);
 const screen=references.find(p=>p.id===unit.unitId+'-SCREEN');assert.deepEqual(W.pose(screen,1),W.pose(screen,0));assert.equal(unit.manufacturerMaximumAngle,null);assert.equal(unit.factoryFourBarTrajectoryAvailable,false);
 assert.throws(()=>W.pose(moving,1.1));
}
const report=inventory.build(data.parts);assert.equal(report.installedItems,28);assert.equal(report.rows.filter(r=>r.material==='OEM insect-screen assembly').length,14);assert.equal(report.rows.filter(r=>r.material==='Purchased Andersen A-Series awning assembly').length,14);assert(report.rows.every(r=>r.dimensionsIn.length>=2));
const nodes=new Map(),node=()=>({children:[],value:'',textContent:'',appendChild(p){this.children.push(p);},replaceChildren(){this.children=[];}}),document={getElementById:id=>{if(!nodes.has(id))nodes.set(id,node());return nodes.get(id);},createElement:node};let received=[];const controls=W.bind(document,units,(ids,value)=>received.push({ids,value}));nodes.get('windowOpening').value='.4';nodes.get('windowOpening').oninput();assert.equal(received.at(-1).ids.length,14);controls.select(units[0].unitId);assert.equal(nodes.get('windowOpening').value,'0.4');nodes.get('windowOpening').value='.8';nodes.get('windowOpening').oninput();assert.deepEqual(received.at(-1).ids,[units[0].unitId]);assert.equal(controls.states.get(units[1].unitId),.4);controls.close();assert(Array.from(controls.states.values()).every(v=>v===0));
console.log(JSON.stringify({pass:true,purchasedUnits:14,separateScreens:14,referenceOnlyServicePartsNotDoubleBought:true,independentOpening:true,topFixedBottomOut:true,actualMaximumAngleNotInvented:true}));
// TIMESTAMP END 2026-11-05T17:09:28+00:00 | REVISION R000057
