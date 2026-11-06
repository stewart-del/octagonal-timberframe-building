// TIMESTAMP START 2026-11-05T04:51:00+00:00 | REVISION R000023
/* Visibility semantics only. Never changes model coordinates or structural claims. */
(function(root){
'use strict';
const PRESETS={complete:'Complete',skeleton:'Skeleton',foundation:'Foundation & Posts',floor:'Floor Assembly'};
// TIMESTAMP START 2026-11-02T14:22:13-05:00 | REVISION R004792
// TIMESTAMP START 2026-11-02T17:13:08-05:00 | REVISION R004818
// TIMESTAMP START 2026-11-05T12:40:59+00:00 | REVISION R000041
const roles=new Set(['mudroom','temporary','deferred','reference','foundation','floorStructure','floorFinish','wallStructure','wall','shelf','cupolaWindow','roofCover','post','frame','ceilingPanel','jointFastener','roofStructure']);
// TIMESTAMP END 2026-11-05T12:40:59+00:00 | REVISION R000041
// TIMESTAMP END 2026-11-02T17:13:08-05:00 | REVISION R004818
// TIMESTAMP END 2026-11-02T14:22:13-05:00 | REVISION R004792
function role(p){
 if(p.temporary===true)return 'temporary';
 if(p.schematicKind==='grate'||p.deferred===true)return 'deferred';
 if(roles.has(p.displayRole))return p.displayRole;
 if(['metal_spacers','temporary_fixture'].includes(p.group))return 'temporary';
 if(p.group==='roof_envelope')return 'reference';
 if(p.schematicKind==='roofCover')return 'roofCover';
 if(p.schematicKind==='floorAssembly'){
  if(p.material==='concrete'||/^PIER-/.test(p.id)||/^POST-BEARING-STAND-/.test(p.id))return 'foundation';
  if(p.material==='strand-woven bamboo'||/^FLOOR-BAMBOO-/.test(p.id))return 'floorFinish';
  return 'floorStructure';
 }
 if(p.schematicKind==='floor')return 'floorFinish';
 if(p.schematicKind==='rail')return 'wallStructure';
 if(['wall','shelf','cupolaWindow'].includes(p.schematicKind))return p.schematicKind;
 if(['perimeter_posts','cupola_posts'].includes(p.group))return 'post';
 if(p.group==='cupola_plywood')return 'ceilingPanel';
 // TIMESTAMP START 2026-11-02T17:13:08-05:00 | REVISION R004818
 if(p.group==='joinery_pegs')return 'jointFastener';
 // TIMESTAMP END 2026-11-02T17:13:08-05:00 | REVISION R004818
 return p.schematic?'wall':'frame';
}
// TIMESTAMP START 2026-11-02T20:27:45-05:00 | REVISION R004866
function included(p,preset){const r=role(p);if((p.id==='M-TMP'||p.showWithTemporaryConnector)&&preset==='complete')return true;if(['temporary','deferred','reference'].includes(r))return false;
// TIMESTAMP END 2026-11-02T20:27:45-05:00 | REVISION R004866
 if(preset==='complete')return true;
 // TIMESTAMP START 2026-11-02T17:13:08-05:00 | REVISION R004818
 // TIMESTAMP START 2026-11-02T20:19:08-05:00 | REVISION R004863
 // TIMESTAMP START 2026-11-03T07:01:25-05:00 | REVISION R004903
// TIMESTAMP START 2026-11-05T12:40:59+00:00 | REVISION R000041
 if(preset==='skeleton')return ['foundation','floorStructure','wallStructure','post','frame','jointFastener','roofStructure'].includes(r)||(r==='mudroom'&&['foundation','framing','floor','stair'].includes(p.mudroomRole));
// TIMESTAMP END 2026-11-05T12:40:59+00:00 | REVISION R000041
 // TIMESTAMP END 2026-11-03T07:01:25-05:00 | REVISION R004903
 // TIMESTAMP END 2026-11-02T20:19:08-05:00 | REVISION R004863
 // TIMESTAMP END 2026-11-02T17:13:08-05:00 | REVISION R004818
 if(preset==='foundation')return ['foundation','post'].includes(r);
 if(preset==='floor')return ['foundation','floorStructure','floorFinish'].includes(r);
 throw Error('Unknown display preset '+preset);
}
const api={PRESETS,role,included};root.OctagonDisplayPresets=api;if(typeof module!=='undefined'&&module.exports)module.exports=api;
})(typeof globalThis!=='undefined'?globalThis:this);

// TIMESTAMP END 2026-11-05T04:51:00+00:00 | REVISION R000023
