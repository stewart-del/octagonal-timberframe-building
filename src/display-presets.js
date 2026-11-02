/* Visibility semantics only. Never changes model coordinates or structural claims. */
(function(root){
'use strict';
const PRESETS={complete:'Complete',skeleton:'Skeleton',foundation:'Foundation & Posts',floor:'Floor Assembly'};
const roles=new Set(['temporary','deferred','reference','foundation','floorStructure','floorFinish','wallStructure','wall','shelf','cupolaWindow','roofCover','post','frame','ceilingPanel']);
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
 return p.schematic?'wall':'frame';
}
function included(p,preset){const r=role(p);if(['temporary','deferred','reference'].includes(r))return false;
 if(preset==='complete')return true;
 if(preset==='skeleton')return ['foundation','floorStructure','wallStructure','post','frame'].includes(r);
 if(preset==='foundation')return ['foundation','post'].includes(r);
 if(preset==='floor')return ['foundation','floorStructure','floorFinish'].includes(r);
 throw Error('Unknown display preset '+preset);
}
const api={PRESETS,role,included};root.OctagonDisplayPresets=api;if(typeof module!=='undefined'&&module.exports)module.exports=api;
})(typeof globalThis!=='undefined'?globalThis:this);
