const fs=require('node:fs'),path=require('node:path');
const candidates=[path.resolve(__dirname,'../src/viewer.template.html'),path.resolve(__dirname,'../site/src/viewer.template.html')];
const templatePath=process.argv[2]||candidates.find(p=>fs.existsSync(p));
if(!templatePath)throw Error('Pass the current viewer.template.html path as the first argument.');
const source=fs.readFileSync(templatePath,'utf8');
const edgeCandidates=[path.resolve(path.dirname(templatePath),'edge-measurements.js'),path.resolve(__dirname,'edge-measurements.js'),path.resolve(__dirname,'../analysis-tools/edge-measurements.js')];
const edgePath=edgeCandidates.find(p=>fs.existsSync(p));
if(!edgePath)throw Error('Cannot find edge-measurements.js beside the template or test tools.');
const TimberEdgeMeasurements=require(edgePath);

function extractFunction(text,name){
  const matches=[...text.matchAll(new RegExp('^function '+name+'\\(', 'gm'))];
  if(matches.length!==1)throw Error('Expected one function '+name);
  const start=matches[0].index,opening=text.indexOf('{',start);
  let depth=0,quote=null,comment=null,escaped=false;
  for(let i=opening;i<text.length;i++){
    const c=text[i],n=text[i+1];
    if(comment==='line'){if(c==='\n')comment=null;continue;}
    if(comment==='block'){if(c==='*'&&n==='/'){comment=null;i++;}continue;}
    if(quote){if(escaped){escaped=false;continue;}if(c==='\\'){escaped=true;continue;}if(c===quote)quote=null;continue;}
    if(c==='/'&&n==='/'){comment='line';i++;continue;}
    if(c==='/'&&n==='*'){comment='block';i++;continue;}
    if(c==="'"||c==='"'||c==='`'){quote=c;continue;}
    if(c==='{')depth++;
    if(c==='}'&&--depth===0){const fn=text.slice(start,i+1);new Function('return ('+fn+')');return fn;}
  }
  throw Error('Unterminated '+name);
}
const names=['surfaceDisplayColor','memberEdgeColor','fallbackFaceEdges','featureEdges','render'];
const functions=names.map(name=>extractFunction(source,name)).join('\n');
const results=new Function('source','TimberEdgeMeasurements',`
const passed=[],check=(yes,msg)=>{if(!yes)throw Error(msg);passed.push(msg)};
const vadd=(a,b)=>a.map((x,i)=>x+b[i]),vsub=(a,b)=>a.map((x,i)=>x-b[i]),vmul=(a,s)=>a.map(x=>x*s),dot=(a,b)=>a.reduce((s,x,i)=>s+x*b[i],0),length=a=>Math.hypot(...a),unit=a=>vmul(a,1/(length(a)||1)),cross=(a,b)=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];
let highContrast=true,edgesOn=true;
const fallbackFeatureCache=new Map();
let requested=true,VP=[],program={},loc={opacity:'opacity',lineMode:'lineMode',color:'color',translation:'translation',viewProjection:'VP',surfaceContrast:'surfaceContrast'};
let depth=true,blend=false,polygon=false,opacity=1,bound=null,log=[],throwOn=null;
const gl={BLEND:'BLEND',POLYGON_OFFSET_FILL:'POLYGON',SRC_ALPHA:'SRC',ONE_MINUS_SRC_ALPHA:'ONE_MINUS',COLOR_BUFFER_BIT:1,DEPTH_BUFFER_BIT:2,LINES:'LINES',TRIANGLES:'TRIANGLES',
 depthMask(v){depth=v},enable(cap){if(cap===this.BLEND)blend=true;if(cap===this.POLYGON_OFFSET_FILL)polygon=true},disable(cap){if(cap===this.BLEND)blend=false;if(cap===this.POLYGON_OFFSET_FILL)polygon=false},polygonOffset(f,u){log.push(['bias',f,u])},clear(){},useProgram(){},uniformMatrix4fv(){},uniform3fv(){},uniform1f(k,v){if(k==='opacity')opacity=v;if(k==='surfaceContrast')log.push(['contrast',v])},blendFunc(){},
 drawArrays(type){log.push(['draw',bound,type,depth,blend,polygon,opacity]);if(type===this.TRIANGLES&&bound===throwOn)throw Error('draw failure')}};
const bind=b=>bound=b,gridBuffer='GRID',gridCount=2,basis={eye:[0,0,50]},matrix=()=>{};
const meshParts=[{part:{id:'A'},buffer:'A',edgeBuffer:'Aedge',count:3,edgeCount:2},{part:{id:'G'},buffer:'G',edgeBuffer:'Gedge',count:3,edgeCount:2}];
const isShown=()=>true,isSelectedMember=p=>p.id==='A',selectionAlpha=p=>p.id==='A'?1:.14,offset=()=>[0,0,0],fittedCenter=()=>[0,0,0],groupColor=()=>[.5,.4,.3];
let afterCuts=null,afterCavity=null;
const drawCavityVolumes=()=>afterCavity={depth,blend,polygon,opacity},updateEdgeMeasurementLabels=()=>{},updateHollowStatus=()=>{},updateLoadReview=()=>{},drawCutFaces=()=>afterCuts={depth,blend,polygon,opacity},updateLabels=()=>{},updateEndLabels=()=>{},updateCutLabel=()=>{},updatePieceCenter=()=>{},fallback=null;
${functions}
check(source.includes('edgesOn=true,highContrast=true')&&source.includes('id="wireframe" checked')&&source.includes('id="surfaceContrast" checked'),'Feature edges and high contrast start enabled');
check(source.includes('uniform float surfaceContrast')&&source.includes('mix(lit,color,lineMode)'),'Surface shader exposes contrast and leaves line overlay colors unlit');
const normals=[[1,0,0],[-1,0,0],[0,1,0],[0,-1,0],[0,0,1],[0,0,-1]],base=[.5,.4,.3];
const ordinary=normals.map(n=>surfaceDisplayColor(base,n,false)),bright=normals.map(n=>surfaceDisplayColor(base,n,true));
check(bright.every((c,i)=>c.every((v,k)=>v>ordinary[i][k]&&v>=0&&v<=1)),'Every axial face is brighter than regular mode with bounded RGB');
const means=bright.map(c=>c.reduce((s,x)=>s+x,0)/3),oldMeans=ordinary.map(c=>c.reduce((s,x)=>s+x,0)/3);
check(Math.max(...means)-Math.min(...means)>Math.max(...oldMeans)-Math.min(...oldMeans),'Axial faces have a wider orientation-driven tonal range');
check(JSON.stringify(surfaceDisplayColor(base,[0,1,0]))===JSON.stringify(surfaceDisplayColor(base,[0,5,0])),'Lighting depends on normalized face orientation');
check(normals.every(n=>{const c=surfaceDisplayColor([.12,.62,.75],n);return c[2]>c[1]&&c[1]>c[0]}),'Selection lighting preserves distinct cyan channel ordering');
check(memberEdgeColor(false).every((x,i)=>x<bright[0][i])&&memberEdgeColor(true)[2]>memberEdgeColor(true)[0],'Feature edges contrast with timber and retain selected cyan');
const cube={id:'CUBE',vertices:[[0,0,0],[1,0,0],[1,1,0],[0,1,0],[0,0,1],[1,0,1],[1,1,1],[0,1,1]],triangles:[[0,2,1],[0,3,2],[4,5,6],[4,6,7],[0,1,5],[0,5,4],[3,7,6],[3,6,2],[0,4,7],[0,7,3],[1,2,6],[1,6,5]]};
check(featureEdges(cube.vertices,cube.triangles).length===12*12,'Feature extraction keeps twelve cube edges');
const faceSegments=cube.triangles.flatMap(t=>fallbackFaceEdges(cube,t));
check(faceSegments.length===24&&faceSegments.every(([a,b])=>length(vsub(a,b))===1),'Fallback clips true features to faces and suppresses mesh diagonals');
const again=fallbackFaceEdges(cube,cube.triangles[0]);check(again===fallbackFaceEdges(cube,cube.triangles[0]),'Fallback caches immutable feature geometry');
render();
const draws=log.filter(x=>x[0]==='draw');
check(draws.filter(x=>x[2]==='TRIANGLES').every(x=>x[5])&&draws.filter(x=>x[2]==='LINES').every(x=>!x[5]),'Polygon offset applies only during filled member surfaces');
check(draws.some(x=>x[1]==='G'&&!x[3]&&x[4]&&x[6]===.14),'Polygon bias preserves translucent context blending');
check(afterCavity.depth&&!afterCavity.blend&&!afterCavity.polygon&&afterCavity.opacity===1,'Cavity overlays receive restored GL state');
check(afterCuts.depth&&!afterCuts.blend&&!afterCuts.polygon&&afterCuts.opacity===1,'Cut overlays receive restored GL state');
for(const id of ['A','G']){throwOn=id;try{render()}catch(e){};check(!polygon&&depth&&!blend,'Thrown '+id+' fill restores polygon and shared GL state')}
throwOn=null;highContrast=false;log=[];render();check(log.some(x=>x[0]==='contrast'&&x[1]===0),'Regular mode sends zero contrast uniform');
return passed;
`)(source,TimberEdgeMeasurements);
console.log(JSON.stringify({method:'Actual template functions; normal math and renderer state without browser',source:templatePath,passed:results.length,assertions:results},null,2));

