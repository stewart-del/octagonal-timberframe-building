// TIMESTAMP START 2026-11-05T06:53:24+00:00 | REVISION R000030
(function(root){
'use strict';
const I=.0254;
const csvCell=value=>'"'+String(value??'').replaceAll('"','""')+'"';
// TIMESTAMP START 2026-11-05T17:09:28+00:00 | REVISION R000057
function physical(p){return !!p.countAsPurchasedItem||(!p.deferred&&!['grate','footer'].includes(p.schematicKind)&&p.group!=='roof_envelope'&&p.group!=='metal_spacers'&&p.displayRole!=='reference');}
// TIMESTAMP END 2026-11-05T17:09:28+00:00 | REVISION R000057
function size(p){
// TIMESTAMP START 2026-11-05T17:09:28+00:00 | REVISION R000057
 if(p.publishedDimensionsIn)return p.publishedDimensionsIn.slice();
// TIMESTAMP END 2026-11-05T17:09:28+00:00 | REVISION R000057
// TIMESTAMP START 2026-11-05T12:40:59+00:00 | REVISION R000041
 const fastener=p.fastenerSpec||p.fastener_spec;
 if(fastener)return [fastener.lengthIn??fastener.nominalUnderHeadLengthIn??fastener.underHeadLengthIn??fastener.underheadLengthIn??fastener.finishedLengthIn,fastener.majorDiameterIn??fastener.shankDiameterIn??fastener.diameterIn,fastener.headDiameterIn].map(v=>Number.isFinite(v)?v:null);
 if(p.stockSectionIn&&Number.isFinite(p.stockLengthIn))return [p.stockLengthIn,...p.stockSectionIn];
// TIMESTAMP END 2026-11-05T12:40:59+00:00 | REVISION R000041
 if(p.sheet_stock)return [p.sheet_stock.lengthM/I,p.sheet_stock.widthM/I,p.sheet_stock.thicknessM/I];
 if(p.minimum_blank_dimensions_in)return p.minimum_blank_dimensions_in.slice();
 const d=p.dimensions||{};if(Number.isFinite(d.length_m))return [p.new_stock_requirements?.minimum_blank_length_in??d.length_m/I,d.width_in??d.width_m/I,d.depth_in??d.depth_m/I].map(v=>Number.isFinite(v)?v:null);
 const frame=p.stock_frame;
 if(frame&&p.vertices?.length)return [frame.axis,frame.width,frame.depth].map(axis=>{let lo=Infinity,hi=-Infinity;for(const v of p.vertices){const q=v.reduce((sum,n,k)=>sum+n*axis[k],0);lo=Math.min(lo,q);hi=Math.max(hi,q);}return (hi-lo)/I;});
 return [];
}
function row(p){
// TIMESTAMP START 2026-11-05T12:40:59+00:00 | REVISION R000041
 const spec=p.fastenerSpec||p.fastener_spec||p.productSpecification||p.product||p.flooringProduct||p.windowSpec||{},dimensions=size(p);
// TIMESTAMP END 2026-11-05T12:40:59+00:00 | REVISION R000041
 const parent=p.stock_parent_id||p.foot_gap_parent_id||p.id;
 return {id:p.id,name:p.name||p.id,role:p.floorRole||p.framingRole||p.mudroomRole||p.group||p.schematicKind||'',
  quantity:p.underground?0:1,segmentOf:p.underground?p.id.replace(/-BELOW$/,''):'',stockParent:parent,
  manufacturer:spec.manufacturer||p.manufacturer||'',partNumber:spec.partNumber||spec.productCode||spec.sku||spec.model||'',
  material:p.material||spec.material||'',dimensionsIn:dimensions,
  receiverIds:p.receiverIds||[],parentId:p.parentId||p.assemblyId||'',
  temporary:!!p.temporary,installation:spec.installation||p.installation||p.sequence||'',
  specification:spec,sourceURL:spec.sourceURL||spec.productURL||'',
  geometryStatus:p.geometryProfile||spec.geometryProfile||p.factoryJointGeometry||p.cut_status||p.status||''};
}
function build(parts,{wastePercent=10}={}){
 if(!Number.isFinite(wastePercent)||wastePercent<0||wastePercent>100)throw Error('Waste allowance must be between 0 and 100 percent');
 const ids=new Set(),rows=[];
 for(const p of parts){if(ids.has(p.id))throw Error('Duplicate inventory piece '+p.id);ids.add(p.id);if(physical(p))rows.push(row(p));}
 const groups=new Map();
 for(const r of rows){
  if(!r.quantity)continue;
  const section=r.dimensionsIn.map(v=>v==null?'':Math.ceil(v*4-1e-8)/4);
  const key=r.partNumber?['product',r.manufacturer,r.partNumber].join('|'):['material',r.role,r.material,...section].join('|');
  let group=groups.get(key);
  if(!group){group={id:key,name:r.partNumber||r.role,manufacturer:r.manufacturer,partNumber:r.partNumber,material:r.material,quantity:0,dimensionsIn:r.dimensionsIn,memberIds:[],stockParents:new Set(),installation:r.installation};groups.set(key,group);}
  group.quantity+=r.quantity;group.memberIds.push(r.id);group.stockParents.add(r.stockParent);
 }
 const products=Array.from(groups.values()).map(g=>({...g,stockPieceCount:g.stockParents.size,stockParents:Array.from(g.stockParents)}));
 const cork=parts.filter(p=>p.floorRole==='finish_underlayment'&&p.rollStock),cuts=new Map();let underlayment=null;
 if(cork.length){
  for(const p of cork)cuts.set(p.stock_parent_id,p.rollStock.cutLengthM);
  const stockLength=cork[0].rollStock.rollLengthM,bins=[];
  for(const [id,length] of Array.from(cuts).sort((a,b)=>b[1]-a[1])){
   if(length>stockLength+1e-8)throw Error('Cork cut exceeds the real roll length');
   let bin=bins.find(b=>b.remainingM>=length-1e-8);if(!bin){bin={remainingM:stockLength,cuts:[]};bins.push(bin);}bin.remainingM-=length;bin.cuts.push({id,lengthM:length});
  }
  underlayment={product:cork[0].product,installedPieces:cork.length,rolls:bins.length,rollCutPlan:bins,totalCutLengthM:Array.from(cuts.values()).reduce((a,b)=>a+b,0),basis:'Constructive full-width roll-cut plan; each connected fragment retains its source cut. Trim offcuts remain allowance, not installed cork.'};
 }
 const planks=parts.filter(p=>p.floorRole==='finish_plank'),product=planks.find(p=>p.flooringProduct)?.flooringProduct;
 let flooring=null;
 if(product){const thickness=product.nominalThicknessIn*I,areaM2=planks.reduce((sum,p)=>sum+(p.volumeM3??p.volume_m3??0)/thickness,0),areaSqFt=areaM2/.3048**2;
  flooring={sku:product.sku,productCode:product.productCode,installedPieces:planks.length,installedAreaSqFt:areaSqFt,wastePercent,orderAreaSqFt:areaSqFt*(1+wastePercent/100),cartonAreaSqFt:product.cartonAreaSqFt,
   cartons:Math.ceil(areaSqFt*(1+wastePercent/100)/product.cartonAreaSqFt),lengthBasis:product.lengthBasis,installation:product.installation};}
 return {rows,products,flooring,underlayment,physicalRecords:rows.length,installedItems:rows.reduce((sum,r)=>sum+r.quantity,0),fasteners:parts.filter(p=>physical(p)&&p.is_fastener).length,
  scope:'Installed model quantities. Buried pier records are segments of the same columns. Minimum blank dimensions need cutting/dressing allowance; original random flooring carton lengths remain to be checked.'};
}
function csv(report){
 const head=['Piece_ID','Quantity','Name','Role','Material','Manufacturer','Part_number','Dimensions_in_model_stock_axes_or_fastener_L_shank_head','Stock_parent','Assembly_or_parent','Fastens','Segment_of_continuous_column','Temporary','Installation','Specification_JSON','Geometry_status'];
 return [head,...report.rows.map(r=>[r.id,r.quantity,r.name,r.role,r.material,r.manufacturer,r.partNumber,r.dimensionsIn.map(v=>v==null?'':v.toFixed(5)).join(' x '),r.stockParent,r.parentId,r.receiverIds.join(' | '),r.segmentOf,r.temporary?'yes':'',r.installation,Object.keys(r.specification).length?JSON.stringify(r.specification):'',r.geometryStatus])].map(values=>values.map(csvCell).join(',')).join('\r\n');
}
function productsCSV(report){return [['Product_or_material','Quantity_installed','Stock_parent_count','Manufacturer','Part_number','Material','Dimensions_in','Piece_IDs','Installation'],...report.products.map(g=>[g.name,g.quantity,g.stockPieceCount,g.manufacturer,g.partNumber,g.material,g.dimensionsIn.map(v=>v==null?'':v.toFixed(5)).join(' x '),g.memberIds.join(' | '),g.installation])].map(values=>values.map(csvCell).join(',')).join('\r\n');}
const api={physical,size,row,build,csv,productsCSV};root.OctagonComponentInventory=api;if(typeof module!=='undefined'&&module.exports)module.exports=api;
})(typeof globalThis!=='undefined'?globalThis:this);
// TIMESTAMP END 2026-11-05T06:53:24+00:00 | REVISION R000030
