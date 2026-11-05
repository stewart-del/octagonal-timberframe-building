// TIMESTAMP START 2026-11-05T06:53:24+00:00 | REVISION R000030
'use strict';
const assert=require('node:assert/strict'),inventory=require('../src/component-inventory.js');
const spec={manufacturer:'Maker',partNumber:'REAL-1',lengthIn:2.5,majorDiameterIn:.131,headDiameterIn:.285,installation:'Two at each end'};
const pieces=[{id:'nail-a',is_fastener:true,fastenerSpec:spec,receiverIds:['panel','joist'],parentId:'panel'},{id:'nail-b',is_fastener:true,fastenerSpec:spec},{id:'PIER-C',material:'concrete'},{id:'PIER-C-BELOW',underground:true,material:'concrete'},{id:'retired',group:'roof_envelope'},
 {id:'plank-a',floorRole:'finish_plank',volumeM3:.375*.0254*.3048**2*20,flooringProduct:{sku:'10041002',productCode:'QCDSBAMSDT5',nominalThicknessIn:.375,cartonAreaSqFt:20.48,installation:'Floating'}},
 {id:'plank-b',floorRole:'finish_plank',stock_parent_id:'plank-a',volumeM3:.375*.0254*.3048**2*5,flooringProduct:{sku:'10041002',productCode:'QCDSBAMSDT5',nominalThicknessIn:.375,cartonAreaSqFt:20.48,installation:'Floating'}}];
const report=inventory.build(pieces);
assert.equal(report.rows.length,6);assert.equal(report.installedItems,5);assert.equal(report.fasteners,2);
assert.equal(report.products.find(p=>p.partNumber==='REAL-1').quantity,2);
assert.equal(report.products.find(p=>p.partNumber==='QCDSBAMSDT5').stockPieceCount,1,'Cut fragments must not purchase their source blank twice');
assert.equal(report.rows.find(p=>p.id==='PIER-C-BELOW').segmentOf,'PIER-C');
assert(Math.abs(report.flooring.installedAreaSqFt-25)<1e-10);assert.equal(report.flooring.cartons,2);
const csv=inventory.csv(report);assert(csv.includes('REAL-1'));assert(csv.includes('panel | joist'));assert(csv.includes('PIER-C-BELOW'));assert(!csv.includes('retired'));
assert.throws(()=>inventory.build([pieces[0],pieces[0]]),/Duplicate inventory/);
assert.throws(()=>inventory.build(pieces,{wastePercent:-1}),/allowance/);
// TIMESTAMP START 2026-11-05T12:40:59+00:00 | REVISION R000041
const inherited=inventory.build([{id:'shared-prototype-nail',is_fastener:true,fastener_spec:{manufacturer:'Actual maker',partNumber:'NAIL-SHARED',nominalUnderHeadLengthIn:2.5,shankDiameterIn:.131,headDiameterIn:.285}},{id:'CEDAR-1',stockLengthIn:18,stockSectionIn:[6,.45],material:'cedar'}]);
const rss=inventory.row({id:'ACTUAL-RSS',is_fastener:true,fastener_spec:{partNumber:'14221',underHeadLengthIn:3.12,majorDiameterIn:.276,headDiameterIn:.62}});assert.deepEqual(rss.dimensionsIn,[3.12,.276,.62]);
assert.equal(inherited.products.find(p=>p.partNumber==='NAIL-SHARED').quantity,1);assert.deepEqual(inherited.rows[0].dimensionsIn,[2.5,.131,.285]);assert.deepEqual(inherited.rows[1].dimensionsIn,[18,6,.45]);assert(inventory.csv(inherited).includes('NAIL-SHARED'));
// TIMESTAMP END 2026-11-05T12:40:59+00:00 | REVISION R000041
const cork=inventory.build([{id:'cork-a',floorRole:'finish_underlayment',stock_parent_id:'cut-1',rollStock:{cutLengthM:6,rollLengthM:8},product:{manufacturer:'Test supplier',partNumber:'Test 3mm roll'}},{id:'cork-b',floorRole:'finish_underlayment',stock_parent_id:'cut-1',rollStock:{cutLengthM:6,rollLengthM:8},product:{manufacturer:'Test supplier',partNumber:'Test 3mm roll'}},{id:'cork-c',floorRole:'finish_underlayment',stock_parent_id:'cut-2',rollStock:{cutLengthM:5,rollLengthM:8},product:{manufacturer:'Test supplier',partNumber:'Test 3mm roll'}}]);
assert.equal(cork.underlayment.rolls,2);assert.equal(cork.underlayment.totalCutLengthM,11);assert(cork.underlayment.rollCutPlan.every(p=>p.remainingM>=0));
console.log(JSON.stringify({pass:true,allPhysicalPieces:true,hiddenFastenersItemized:true,productCounts:true,pierSegmentsCountedOnce:true,cutStockParentsCountedOnce:true,flooringCartons:true,duplicateIdsRejected:true}));
// TIMESTAMP END 2026-11-05T06:53:24+00:00 | REVISION R000030
