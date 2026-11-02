const assert=require('assert'),fs=require('fs'),roof=require('../src/roof-coverings.js');
for(const name of ['model-data','step-lap-proposed-model','top-entry-proposed-model']){
 if(!fs.existsSync('src/'+name+'.json'))continue;
 const model=JSON.parse(fs.readFileSync('src/'+name+'.json')),before=JSON.stringify(model),r=roof.build(model);
 assert.equal(JSON.stringify(model),before);assert.equal(r.components.filter(p=>p.material==='copper').length,8);
 assert(r.components.filter(p=>p.material==='cedar').reduce((s,p)=>s+p.tile_count,0)>1000);assert(new Set(r.components.map(p=>p.id)).size===r.components.length);
 for(const p of r.components){assert(p.schematicKind==='roofCover'&&!p.temporary&&!p.is_timber);const volume=p.triangles.reduce((s,t)=>{const [a,b,c]=t.map(i=>p.vertices[i]);return s+(a[0]*(b[1]*c[2]-b[2]*c[1])+a[1]*(b[2]*c[0]-b[0]*c[2])+a[2]*(b[0]*c[1]-b[1]*c[0]))/6;},0);assert(volume>0,p.id);assert(p.vertices.every(v=>v.every(Number.isFinite)));assert(p.triangles.every(t=>t.every(i=>i>=0&&i<p.vertices.length)));}
 assert.equal(r.assumptions.added_load_included,false);console.log(name,r.components.length,'covering pieces,8copper faces');
}
