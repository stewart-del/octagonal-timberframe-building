// TIMESTAMP START 2026-11-02T13:42:47-05:00 | REVISION R004783
'use strict';
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const source=fs.readFileSync(__dirname+'/../src/viewer.template.html','utf8');
const walls=require('../src/schematic-walls.js'),presets=require('../src/display-presets.js');
function extract(name){
 const match=new RegExp('^function '+name+'\\(','m').exec(source);assert(match,name);
 const start=match.index,opening=source.indexOf('{',start);let depth=0,quote=null,comment=null,escaped=false;
 for(let i=opening;i<source.length;i++){
  const c=source[i],n=source[i+1];
  if(comment==='line'){if(c==='\n')comment=null;continue;}
  if(comment==='block'){if(c==='*'&&n==='/'){comment=null;i++;}continue;}
  if(quote){if(escaped)escaped=false;else if(c==='\\')escaped=true;else if(c===quote)quote=null;continue;}
  if(c==='/'&&n==='/'){comment='line';i++;continue;}if(c==='/'&&n==='*'){comment='block';i++;continue;}
  if(c==="'"||c==='"'||c==='`'){quote=c;continue;}
  if(c==='{')depth++;if(c==='}'&&--depth===0)return source.slice(start,i+1);
 }
 throw Error('Unterminated '+name);
}
function node(){return {children:[],textContent:'',append(...xs){this.children.push(...xs);},appendChild(x){this.children.push(x);},replaceChildren(...xs){this.children=xs;}};}
const sub=(a,b)=>a.map((v,i)=>v-b[i]),add=(a,b)=>a.map((v,i)=>v+b[i]),mul=(a,s)=>a.map(v=>v*s),length=a=>Math.hypot(...a);
let verified=0;
for(const filename of ['model-data.json','step-lap-proposed-model.json','top-entry-proposed-model.json']){
 const model=require('../src/'+filename),layout=walls.build(model.parts),framing=layout.components.filter(p=>p.schematicKind==='rail'),jambs=framing.filter(p=>p.framingRole==='jamb');
 assert.equal(jambs.length,12);assert(framing.every(p=>presets.included(p,'skeleton')));
 assert(framing.every(p=>length(p.exploded_offset)>0),'Every framing component must move');
 assert.equal(new Set(framing.map(p=>JSON.stringify(p.exploded_offset))).size,framing.length,'Separate pieces need distinct displacements');
 const selectedPartIds=new Set(),host=node(),context={parts:model.parts,schematicParts:layout.components,selectedPartIds,selected:null,selectedCut:null,inspectionPartId:null,inspectionCutId:null,inspectionPivot:null,isolatedId:null,explode:0,showHollows:true,hiddenPieces:new Set(),visible:new Set(model.parts.map(p=>p.group)),wallStructureEnabled:true,
  layerShown:p=>context.wallStructureEnabled,canonicalPartId:id=>id,vsub:sub,vadd:add,vmul:mul,length,unit:a=>mul(a,1/(length(a)||1)),offset:p=>mul(p.exploded_offset||[0,0,0],context.explode),
  document:{createElement:node},$:()=>host,num:(v,n)=>v.toFixed(n),addMetric:(p,k,v)=>p.append({textContent:k+': '+v}),
  syncDisplayControls(){},renderList(){},syncFocusButton(){},syncIsolationButton(){},focusSelectedParts(){},requestRender(){},togglePieceFocus(){},togglePieceIsolation(){},cutAngleView:{openPiece(){}},
  clearPieceSelection(){selectedPartIds.clear();context.selected=null;},matrix(){},width:800,height:600,aspect:4/3,basis:{eye:[0,0,20],forward:[0,0,-1],right:[1,0,0],up:[0,1,0]},cutMeshes:[],triangleHit:()=>null};
 vm.createContext(context);
// TIMESTAMP START 2026-11-03T07:26:01-05:00 | REVISION R004920
 for(const name of ['logicalPieceId','isColumn','columnSegments','columnBounds','isShown','isSelectedMember','selectionAlpha','selectedSetBounds','selectWallFraming','selectPart','pick'])vm.runInContext(extract(name),context);
// TIMESTAMP END 2026-11-03T07:26:01-05:00 | REVISION R004920
 const first=jambs[0],second=jambs[1];
 for(const amount of [0,.25,.75,1]){context.explode=amount;for(const p of framing){assert(context.isShown(p));assert.deepEqual(context.offset(p),mul(p.exploded_offset,amount));}}
 context.hiddenPieces.add(first.id);assert(!context.isShown(first));context.hiddenPieces.clear();
 context.isolatedId=first.id;assert(context.isShown(first));assert(!context.isShown(second));context.isolatedId=null;
 context.selectPart(first.id);assert.equal(context.selected,first.id);assert.equal(context.selectionAlpha(first),.38);
 assert(host.children.some(p=>p.textContent==='Active wall framing'));
 assert(JSON.stringify(host).includes('structural capacity remain unverified'));
 context.selectPart(second.id,true);assert.equal(selectedPartIds.size,2);assert.equal(context.selectedSetBounds().members.length,2);
 context.selectPart(second.id,true);assert.equal(context.selected,first.id);assert.equal(selectedPartIds.size,1);
 context.selectPart(first.id,true);assert.equal(context.selected,null);assert.equal(selectedPartIds.size,0);
 // Removing a canonical timber from a mixed selection must return to the jamb inspector.
 selectedPartIds.add(first.id);selectedPartIds.add(model.parts[0].id);context.selected=model.parts[0].id;
 context.selectPart(model.parts[0].id,true);assert.equal(context.selected,first.id);assert.equal(selectedPartIds.size,1);
 assert(host.children.some(p=>p.textContent==='Active wall framing'));
 // Exercise the live ray-picking candidate path using only an actual jamb mesh.
 context.parts=[];context.schematicParts=[first];context.triangleHit=()=>1;context.pick(400,300);assert.equal(context.selected,first.id);
 verified+=framing.length;
}
assert(source.includes('const pivotPart=partById.get(inspectionPartId)'),'Exploding follows a selected framing pivot');
assert(source.includes('Wall framing<!-- TIMESTAMP END'),'Layer label includes vertical framing');
console.log('PASS: '+verified+' framing records across three models; selectable jambs, Shift-toggle, transparency, focus bounds, isolation and simultaneous distinct explosion.');
// TIMESTAMP END 2026-11-02T13:42:47-05:00 | REVISION R004783
