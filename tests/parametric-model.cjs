// TIMESTAMP START 2026-11-03T13:09:36-05:00 | REVISION R005024
const fs=require('fs'),path=require('path'),assert=require('assert/strict');
async function run(){
 const root=path.resolve(__dirname,'..'),api=require('../src/parametric-model.js'),source=require('../src/parametric-source.json'),id=process.argv[2]||'top-entry',pitch=Number(process.argv[3]||5),height=Number(process.argv[4]||96);
 const prefix=id==='baseline'?'':id==='proposed'?'step-lap-proposed-':'top-entry-proposed-',model=require('../src/'+(prefix?prefix+'model.json':'model-data.json'));
 const M=await (await import('../public/vendor/manifold.js')).default({locateFile:()=>path.join(root,'public/vendor/manifold.wasm')});M.setup();
 global.OCTAGON_ENCLOSURE_FIT=require('../src/'+prefix+'enclosure-fit.json');global.MUDROOM_JOINERY_FIT=require('../src/mudroom-joinery-fit.json');
 const walls=require('../src/schematic-walls.js'),floor=require('../src/floor-foundation.js'),roof=require('../src/roof-coverings.js'),porch=require('../src/mudroom.js');
 // TIMESTAMP START 2026-11-03T16:50:27-05:00 | REVISION R005061
 const context={cavities:require('../src/'+(prefix?prefix+'cavities.json':'cavity-data.json')),id,sha256:source.variants[id].source_model_sha256,model,enclosureFit:global.OCTAGON_ENCLOSURE_FIT,wallJoinery:require('../src/wall-joinery-fit.json').variants[id]};
 // TIMESTAMP END 2026-11-03T16:50:27-05:00 | REVISION R005061
 const original=JSON.stringify(model),result=api.core(context,{pitch,wallHeightIn:height},source,M);
 if(!process.argv.includes('--core'))api.layouts(context,result,M,{walls,floor,roof,porch,foundationData:require('../src/floor-foundation-solids.json')});
 assert.equal(JSON.stringify(model),original,'source model must remain immutable');
 const p=Object.fromEntries(result.model.parts.map(p=>[p.id,p]));
 assert(Math.abs((Math.min(...p.B0.vertices.map(v=>v[1]))/.0254)-height)<1e-6);
 assert(Math.abs(Math.abs((p.R0.axis_end[1]-p.R0.axis_start[1])/(p.R0.axis_end[0]-p.R0.axis_start[0]))*12-pitch)<1e-8);
 assert(Math.abs(Math.abs((p.CR0.axis_end[1]-p.CR0.axis_start[1])/(p.CR0.axis_end[0]-p.CR0.axis_start[0]))*12-4)<1e-8);
 for(const id of ['P0','R0','J0-0','C0'])assert.equal(p[id].dimensions.width_in,model.parts.find(p=>p.id===id).dimensions.width_in);
 assert.throws(()=>api.parameters({pitch:0}));assert.throws(()=>api.parameters({wallHeightIn:0}));
 const out='/tmp/octagon-parameter-'+id+'-'+pitch+'-'+height+'.json';fs.writeFileSync(out,JSON.stringify(result));console.log(JSON.stringify({id,pitch,height,parts:result.model.parts.length,components:result.components?.length,output:out}));
}
run().catch(error=>{console.error(error);process.exitCode=1;});
// TIMESTAMP END 2026-11-03T13:09:36-05:00 | REVISION R005024
