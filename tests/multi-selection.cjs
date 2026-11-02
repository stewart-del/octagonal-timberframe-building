// TIMESTAMP START 2026-11-01T23:01:05-05:00 | REVISION R004657
const fs=require('node:fs');
const path=require('node:path');
const candidates=[path.resolve(__dirname,'../src/viewer.template.html'),path.resolve(__dirname,'../site/src/viewer.template.html')];
const templatePath=process.argv[2]||candidates.find(p=>fs.existsSync(p));
if(!templatePath)throw Error('Pass the current viewer.template.html path as the first argument.');
const template=fs.readFileSync(templatePath,'utf8');
const edgeCandidates=[path.resolve(path.dirname(templatePath),'edge-measurements.js'),path.resolve(__dirname,'edge-measurements.js'),path.resolve(__dirname,'../analysis-tools/edge-measurements.js')];
const edgePath=edgeCandidates.find(p=>fs.existsSync(p));
if(!edgePath)throw Error('Cannot find edge-measurements.js beside the template or test tools.');
const TimberEdgeMeasurements=require(edgePath);


// Extract live function declarations from the integrated template. This scanner
// understands comments and quoted strings; these specific functions do not use
// JavaScript regex literals. A syntax check rejects any incomplete extraction.
function extractFunction(text,name){
  const matcher=new RegExp('^function '+name+'\\(', 'gm');
  const matches=[...text.matchAll(matcher)];
  if(matches.length!==1)throw Error('Expected exactly one integrated function '+name);
  const start=matches[0].index, opening=text.indexOf('{',start);
  let depth=0, quote=null, comment=null, escaped=false;
  for(let i=opening;i<text.length;i++){
    const c=text[i],n=text[i+1];
    if(comment==='line'){if(c==='\n')comment=null;continue;}
    if(comment==='block'){if(c==='*'&&n==='/'){comment=null;i++;}continue;}
    if(quote){if(escaped){escaped=false;continue;}if(c==='\\'){escaped=true;continue;}if(c===quote)quote=null;continue;}
    if(c==='/'&&n==='/'){comment='line';i++;continue;}
    if(c==='/'&&n==='*'){comment='block';i++;continue;}
    if(c==="'"||c==='"'||c==='`'){quote=c;continue;}
    if(c==='{')depth++;
    if(c==='}'&&--depth===0){
      const extracted=text.slice(start,i+1);
      new Function('return ('+extracted+');');
      return extracted;
    }
  }
  throw Error('Unterminated integrated function '+name);
}
const names=['isSelectedMember','selectionAlpha','selectedSetBounds','focusSelectedParts','render','drawFallback','updateLabels','pick','memberEdgeColor','surfaceDisplayColor','fallbackFaceEdges','fallbackSegmentIndex','featureEdges'];
const helper=names.map(name=>extractFunction(template,name)).join('\n\n');
const result=new Function('TimberEdgeMeasurements',"\nconst passed=[],check=(yes,msg)=>{if(!yes)throw Error(msg);passed.push(msg)};\nconst selectedPartIds=new Set(['A','B']);let selected='B',showHollows=false;\nconst vadd=(a,b)=>a.map((x,i)=>x+b[i]),vsub=(a,b)=>a.map((x,i)=>x-b[i]),vmul=(a,s)=>a.map(x=>x*s),length=a=>Math.hypot(...a),unit=a=>vmul(a,1/(length(a)||1)),dot=(a,b)=>a.reduce((s,x,i)=>s+x*b[i],0),cross=(a,b)=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];\nconst schematicParts=[];const parts=['A','B','G','Z'].map((id,i)=>({id,group:'wood',vertices:[[i*5,0,0],[i*5+1,0,0],[i*5,1,0]],triangles:[[0,1,2]],exploded_offset:[i,0,0],center:[i*5+.5,.5,0]}));\nconst offset=p=>p.exploded_offset, fittedCenter=p=>vadd(p.center,offset(p)),isShown=p=>true,groupColor=g=>[.5,.4,.3];\nconst meshParts=parts.map(p=>({part:p,buffer:p.id,edgeBuffer:p.id+'-edge',count:3,edgeCount:2}));\nlet inspectionPartId='OLD',inspectionCutId='OLD-CUT',inspectionPivot=null,aspect=1,focusResult;\nconst clearMovement=()=>{},focusPoint=(center,distance)=>{focusResult={center,distance}},focusPart=p=>{focusResult={single:p.id}},requestRender=()=>{};\nlet requested=true,VP=[],program={},loc={opacity:'opacity',lineMode:'lineMode',color:'color',translation:'translation',viewProjection:'viewProjection',surfaceContrast:'surfaceContrast'};\nconst fallbackFeatureCache=new Map();\nlet depth=true,blend=false,polygon=false,opacity=1,bound=null,log=[],throwOn=null;\nlet gl={BLEND:'BLEND',POLYGON_OFFSET_FILL:'POLYGON',SRC_ALPHA:'SRC',ONE_MINUS_SRC_ALPHA:'ONE_MINUS',COLOR_BUFFER_BIT:1,DEPTH_BUFFER_BIT:2,LINES:'LINES',TRIANGLES:'TRIANGLES',\ndepthMask(v){depth=v;log.push(['depth',v])},disable(cap){if(cap===this.BLEND)blend=false;if(cap===this.POLYGON_OFFSET_FILL)polygon=false},enable(cap){if(cap===this.BLEND)blend=true;if(cap===this.POLYGON_OFFSET_FILL)polygon=true},polygonOffset(f,u){log.push(['bias',f,u])},clear(){},useProgram(){},uniformMatrix4fv(){},uniform3fv(){},uniform1f(k,v){if(k==='opacity')opacity=v},blendFunc(){},\ndrawArrays(type){log.push(['draw',bound,type,depth,blend,opacity,polygon]);if(bound===throwOn)throw Error('test draw failure')}};\nconst bind=b=>bound=b,gridBuffer='GRID',gridCount=2,basis={eye:[0,0,50],forward:[0,0,-1],right:[1,0,0],up:[0,1,0]},matrix=()=>{};\nlet edgesOn=false,highContrast=true,afterCutState=null,afterCavityState=null;\nconst drawCavityVolumes=()=>afterCavityState={depth,blend,polygon,opacity},updateEdgeMeasurementLabels=()=>{},updateHollowStatus=()=>{},updateLoadReview=()=>{},updateSchematicWalls=()=>{},drawCutFaces=()=>afterCutState={depth,blend,polygon,opacity},updateEndLabels=()=>{},updateCutLabel=()=>{},updatePieceCenter=()=>{};\nlet width=900,height=650,dpr=1,labelsOn=false,detailOn=false;\nconst document={createElement:()=>({textContent:''})};\nfor(const p of parts)p._label={style:{},setAttribute(){},replaceChildren(){},appendChild(){},offsetWidth:30,offsetHeight:20};\nconst labelText=p=>[p.id,'A 0','B 0'],project=v=>({x:100+v[0]*10,y:150+v[1],distance:length(vsub(v,basis.eye))});\nlet fallback={setTransform(){},globalAlpha:1,fillRect(){},beginPath(){},lineTo(){},moveTo(){},closePath(){},fill(){log.push(['fill',this.fillStyle])},stroke(){}};\nconst cutMeshes=[],cutVisible=()=>true,cutOffset=()=>[0,0,0],triangleHit=(eye,dir,a)=>a[0]+1;\nconst selectedCalls=[],selectPart=(id,additive)=>selectedCalls.push([id,additive]),selectCut=f=>selectedCalls.push(['cut',f.id]);\n"+helper+"\ncheck(selectionAlpha(parts[0])===1&&selectionAlpha(parts[2])===.14,'Two selected members keep opacity; other members ghost at 0.14');\nrender();\nconst draws=log.filter(x=>x[0]==='draw'&&x[2]==='TRIANGLES');\ncheck(draws.slice(0,2).every(x=>x[3]&&!x[4]&&x[5]===1),'Opaque pass writes depth before ghost pass');\ncheck(draws.slice(2).every(x=>!x[3]&&x[4]&&x[5]===.14),'Ghost pass blends without writing depth');\ncheck(draws[2][1]==='Z'&&draws[3][1]==='G','Ghost members sorted back to front');\ncheck(afterCavityState.depth&&!afterCavityState.blend&&!afterCavityState.polygon&&afterCavityState.opacity===1,'Cavity overlays receive restored depth, blend, bias and opacity state');\ncheck(afterCutState.depth&&!afterCutState.blend&&!afterCutState.polygon&&afterCutState.opacity===1,'Cut overlays receive restored depth, blend, bias and opacity state');\ncheck(draws.every(x=>x[6])&&log.filter(x=>x[0]==='draw'&&x[2]==='LINES').every(x=>!x[6]),'Polygon bias applies only to filled surfaces');\nthrowOn='G';try{render()}catch(e){};check(depth&&!blend&&!polygon&&opacity===1,'Rendering failure also restores ghost GL state and polygon bias');throwOn=null;\nfocusSelectedParts();check(focusResult.center[0]===3.5&&focusResult.center[1]===.5&&inspectionPivot[0]===3.5&&inspectionPartId===null&&inspectionCutId===null,'Set focus frames fitted world bounds including exploded offsets');\nlog=[];drawFallback();check(log.some(x=>x[0]==='fill'&&x[1].endsWith(',0.14)'))&&fallback.globalAlpha===1,'2D fallback uses translucent RGBA and leaves full overlay alpha');\npick(450,325,true);check(selectedCalls.at(-1)[0]==='A'&&selectedCalls.at(-1)[1]===true,'Shift picking forwards additive flag to owner selection');\npick(450,325,false);check(selectedCalls.at(-1)[0]==='A'&&selectedCalls.at(-1)[1]===false,'Plain picking forwards replacement selection');\nselectedPartIds.clear();selectedPartIds.add('A');check(selectionAlpha(parts[2])===1,'Single selection retains full-context opacity');\nselectedPartIds.clear();check(focusSelectedParts()===false,'Empty selection focus is a harmless no-op');\nshowHollows=true;selectedPartIds.add('A');check(selectionAlpha(parts[0])===.38,'Selected timber becomes transparent for cavity inspection');\nreturn passed;\n")(TimberEdgeMeasurements);
console.log(JSON.stringify({method:'Integrated template functions in a pure JavaScript renderer/selection-state harness; no browser',source:templatePath,passed:result.length,assertions:result},null,2));



// TIMESTAMP END 2026-11-01T23:01:05-05:00 | REVISION R004657
