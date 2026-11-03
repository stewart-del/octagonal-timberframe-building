// TIMESTAMP START 2026-11-02T15:12:45-05:00 | REVISION R004801
'use strict';
const assert=require('node:assert/strict'),roof=require('../src/mudroom-roof.js');
const sub=(a,b)=>a.map((v,i)=>v-b[i]),dot=(a,b)=>a.reduce((s,v,i)=>s+v*b[i],0),cross=(a,b)=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]],norm=a=>Math.hypot(...a);
function axes(p){const points=p.localVertices,edges=new Map(),normals=[];for(const t of p.triangles){normals.push(cross(sub(points[t[1]],points[t[0]]),sub(points[t[2]],points[t[0]])));for(let i=0;i<3;i++){const a=t[i],b=t[(i+1)%3],key=[a,b].sort((a,b)=>a-b).join(':');if(!edges.has(key))edges.set(key,sub(points[b],points[a]));}}return {normals,edges:[...edges.values()]};}
function overlaps(a,b){const av=a.localVertices,bv=b.localVertices;for(let k=0;k<3;k++)if(Math.min(...av.map(v=>v[k]))>=Math.max(...bv.map(v=>v[k]))-1e-10||Math.min(...bv.map(v=>v[k]))>=Math.max(...av.map(v=>v[k]))-1e-10)return false;
 const A=axes(a),B=axes(b),tests=[...A.normals,...B.normals,...A.edges.flatMap(x=>B.edges.map(y=>cross(x,y)))];
 for(const axis of tests){const length=norm(axis);if(length<1e-12)continue;const n=axis.map(x=>x/length),aa=av.map(v=>dot(v,n)),bb=bv.map(v=>dot(v,n));if(Math.min(...aa)>=Math.max(...bb)-1e-9||Math.min(...bb)>=Math.max(...aa)-1e-9)return false;}return true;
}
let tested=0;
for(const filename of ['model-data.json','step-lap-proposed-model.json','top-entry-proposed-model.json']){
 const model=require('../src/'+filename),before=JSON.stringify(model),{components:parts,spec:s}=roof.build(model);
 assert.equal(JSON.stringify(model),before);assert.equal(s.pitch,4/12);assert(Math.abs(s.halfWidthM-53.5*.0254)<1e-12);assert(parts.some(p=>p.id==='MUD-ROOF'));
 // TIMESTAMP START 2026-11-02T21:55:01-05:00 | REVISION R004881
 assert(parts.filter(p=>p.roofLayer==='cedar').length>100);assert.equal(parts.filter(p=>p.roofLayer==='flashing').length,4);
 assert(!parts.some(p=>/-(RISER|UPPER|APRON)$/.test(p.id)),'Continuous valley has no stepped fascia risers');
 assert(s.deckBottom(s.halfWidthM)>=s.mainTop(s.mainEaveZ_M)+.001-1e-10,'Full-width porch deck clears the main eave');
 assert(s.junctionZ(s.halfWidthM)<s.mainEaveZ_M,'Both valley ends meet the main roof before its eave');
 // TIMESTAMP END 2026-11-02T21:55:01-05:00 | REVISION R004881
 assert(s.deckBottom(s.halfWidthM)-.1397-(-.2032)>2.28,'Rafter underside retains front headroom');
 assert(s.firstFrameZ_M-3.5*.0254/2>s.mainEaveZ_M,'New frame clears the main eave');
 assert.equal(new Set(parts.map(p=>p.id)).size,parts.length);assert.equal(new Set(parts.map(p=>JSON.stringify(p.exploded_offset))).size,parts.length);
 for(const p of parts){assert(p.mudroomRoof&&p.mudroomScreen&&p.schematicKind==='mudroom');assert(norm(p.exploded_offset)>0);assert(p.volume_m3>0);
  const edges=new Map();for(const t of p.triangles){assert(norm(cross(sub(p.localVertices[t[1]],p.localVertices[t[0]]),sub(p.localVertices[t[2]],p.localVertices[t[0]])))>1e-12);for(let j=0;j<3;j++){const key=[t[j],t[(j+1)%3]].sort((a,b)=>a-b).join(':');edges.set(key,(edges.get(key)||0)+1);}}
  assert([...edges.values()].every(n=>n===2),p.id+' is a closed raw mesh');
  for(const v of p.localVertices){assert(v.every(Number.isFinite));if(v[2]<s.mainEaveZ_M-1e-9)assert(v[1]>=s.mainTop(v[2])-1e-9,p.id+' stays above existing roof');}
 }
 for(let i=0;i<parts.length;i++)for(let j=i+1;j<parts.length;j++){assert(!overlaps(parts[i],parts[j]),parts[i].id+' overlaps '+parts[j].id);tested++;}
}
console.log('PASS: 4:12 gable, closed clipped roof volumes, matching cedar courses, explicit flashing, headroom and '+tested+' non-overlap pairs across three models.');
// TIMESTAMP END 2026-11-02T15:12:45-05:00 | REVISION R004801
