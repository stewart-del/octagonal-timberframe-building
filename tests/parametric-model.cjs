// TIMESTAMP START 2026-11-03T13:09:36-05:00 | REVISION R005024
// TIMESTAMP START 2026-11-05T14:18:42+00:00 | REVISION R000046
const fs=require('fs'),path=require('path'),crypto=require('crypto'),assert=require('assert/strict');
// TIMESTAMP END 2026-11-05T14:18:42+00:00 | REVISION R000046
async function run(){
 const root=path.resolve(__dirname,'..'),api=require('../src/parametric-model.js'),source=require('../src/parametric-source.json'),id=process.argv[2]||'top-entry',pitch=Number(process.argv[3]||5),height=Number(process.argv[4]||96);
 const prefix=id==='baseline'?'':id==='proposed'?'step-lap-proposed-':'top-entry-proposed-',model=require('../src/'+(prefix?prefix+'model.json':'model-data.json'));
 const M=await (await import('../public/vendor/manifold.js')).default({locateFile:()=>path.join(root,'public/vendor/manifold.wasm')});M.setup();
 global.OCTAGON_ENCLOSURE_FIT=require('../src/'+prefix+'enclosure-fit.json');global.MUDROOM_JOINERY_FIT=require('../src/mudroom-joinery-fit.json');
 const walls=require('../src/schematic-walls.js'),floor=require('../src/floor-foundation.js'),roof=require('../src/roof-coverings.js'),porch=require('../src/mudroom.js');
 // TIMESTAMP START 2026-11-03T16:50:27-05:00 | REVISION R005061
 const context={cavities:require('../src/'+(prefix?prefix+'cavities.json':'cavity-data.json')),id,sha256:source.variants[id].source_model_sha256,model,enclosureFit:global.OCTAGON_ENCLOSURE_FIT,wallJoinery:require('../src/wall-joinery-fit.json').variants[id]};
 // TIMESTAMP END 2026-11-03T16:50:27-05:00 | REVISION R005061
// TIMESTAMP START 2026-11-05T14:18:42+00:00 | REVISION R000046
 const input={pitch,wallHeightIn:height,cupolaLiftIn:Number(process.argv.find(v=>v.startsWith('--cupola-lift='))?.split('=')[1]??10)},config=api.parameters(input);
 const sourceFile=path.join(root,'src',prefix?prefix+'model.json':'model-data.json');context.sha256=crypto.createHash('sha256').update(fs.readFileSync(sourceFile)).digest('hex');assert.equal(context.sha256,source.variants[id].source_model_sha256,'Actual selected model must match fresh parametric receiver source');
// TIMESTAMP START 2026-11-05T17:19:58+00:00 | REVISION R000058
 const watched=['src/parametric-model.js','src/cupola-parametric.js','src/parametric-source.json','public/vendor/manifold.js','public/vendor/manifold.wasm',path.relative(root,sourceFile)],digest=file=>crypto.createHash('sha256').update(fs.readFileSync(path.join(root,file))).digest('hex'),generationSources=Object.fromEntries(watched.map(file=>[file,digest(file)]));
 const original=JSON.stringify(model),core=api.core(context,config,source,M);
 if(process.argv.includes('--profile'))console.error('MAIN_CORE',!!core.mainCoreRetained,process.memoryUsage());
 const result=require('../src/cupola-parametric.js').regenerate(core,process.argv.includes('--profile')?{...config,debug:true}:config,M,api);
 if(process.argv.includes('--profile'))console.error('CUPOLA_COMPLETE',process.memoryUsage());
 if(config.pitch===4&&config.wallHeightIn===api.BASE_WALL){assert.equal(core.mainCoreRetained,true);const fingerprint=value=>crypto.createHash('sha256').update(JSON.stringify(value)).digest('hex');assert.equal(fingerprint(core.model.parts),fingerprint(model.parts),'Cupola-only edits retain every saved main member');}
// TIMESTAMP END 2026-11-05T17:19:58+00:00 | REVISION R000058
// TIMESTAMP END 2026-11-05T14:18:42+00:00 | REVISION R000046
 if(!process.argv.includes('--core'))api.layouts(context,result,M,{walls,floor,roof,porch,foundationData:require('../src/floor-foundation-solids.json')});
 assert.equal(JSON.stringify(model),original,'source model must remain immutable');
 const p=Object.fromEntries(result.model.parts.map(p=>[p.id,p]));
 assert(Math.abs((Math.min(...p.B0.vertices.map(v=>v[1]))/.0254)-height)<1e-6);
 assert(Math.abs(Math.abs((p.R0.axis_end[1]-p.R0.axis_start[1])/(p.R0.axis_end[0]-p.R0.axis_start[0]))*12-pitch)<1e-8);
// TIMESTAMP START 2026-11-05T14:18:42+00:00 | REVISION R000046
 assert(Math.abs(Math.abs((p.CR0.axis_end[1]-p.CR0.axis_start[1])/(p.CR0.axis_end[0]-p.CR0.axis_start[0]))*12-config.cupolaPitch)<1e-8);
 // TIMESTAMP START 2026-11-05T16:01:12+00:00 | REVISION R000052
 assert.equal(config.cupolaPitch,config.pitch,'Main and cupola roof pitches must match');
 // TIMESTAMP END 2026-11-05T16:01:12+00:00 | REVISION R000052
 assert.equal(result.cupolaResearch.new_access_peg_ids.length,24);assert(result.cupolaResearch.positive_restraint.every(r=>r.status==='PASS'));
// TIMESTAMP END 2026-11-05T14:18:42+00:00 | REVISION R000046
 for(const id of ['P0','R0','J0-0','C0'])assert.equal(p[id].dimensions.width_in,model.parts.find(p=>p.id===id).dimensions.width_in);
 assert.throws(()=>api.parameters({pitch:0}));assert.throws(()=>api.parameters({wallHeightIn:0}));
// TIMESTAMP START 2026-11-05T17:19:58+00:00 | REVISION R000058
 const out=process.argv.find(v=>v.startsWith('--output='))?.slice(9)||'/tmp/octagon-parameter-'+id+'-'+pitch+'-'+height+'-cupola-'+config.cupolaLiftIn+'.json';
// TIMESTAMP END 2026-11-05T17:19:58+00:00 | REVISION R000058
for(const [file,expected]of Object.entries(generationSources))assert.equal(digest(file),expected,'Source changed during parametric generation: '+file);result.generationSources=generationSources;fs.writeFileSync(out,JSON.stringify(result));console.log(JSON.stringify({id,pitch,height,parts:result.model.parts.length,components:result.components?.length,output:out}));
}
run().catch(error=>{console.error(error);process.exitCode=1;});
// TIMESTAMP END 2026-11-03T13:09:36-05:00 | REVISION R005024
