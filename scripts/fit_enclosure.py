# TIMESTAMP START 2026-11-02T13:44:32-05:00 | REVISION R004784
"""Fit display wall framing/infill/floor around unchanged timber and footing solids.
Not a proposed structural joint or connection-capacity analysis.
"""
# TIMESTAMP END 2026-11-02T13:44:32-05:00 | REVISION R004784
from pathlib import Path
import argparse,json,subprocess,hashlib
import numpy as np
import manifold3d as m
# TIMESTAMP START 2026-11-02T18:13:09-05:00 | REVISION R004829
from step_lap import regular_boundary
from audit_cavity_fit import inspect_mesh
FIT_TOLERANCE_M3=1e-6*.0254**3
def normalize_boundary(shape):
 before=shape
 pieces=[q for q in shape.decompose() if abs(q.volume())>1e-16]
 assert pieces and all(q.volume()>0 for q in pieces),'Inverted enclosure material'
 shape=m.Manifold.batch_boolean(pieces,m.OpType.Add) if len(pieces)>1 else pieces[0]
 raw=shape.to_mesh64()
 if inspect_mesh(np.asarray(raw.vert_properties)[:,:3],np.asarray(raw.tri_verts),require_single=False)['status']!='PASS':
  shape=regular_boundary(shape)
 raw=shape.to_mesh64();report=inspect_mesh(np.asarray(raw.vert_properties)[:,:3],np.asarray(raw.tri_verts),require_single=False)
 assert report['status']=='PASS',report['failures']
 error=abs((before-shape).volume())+abs((shape-before).volume())
 assert error<FIT_TOLERANCE_M3,('Enclosure normalization changed occupied material',error)
 return shape,{'status':'PASS','symmetric_volume_difference_m3':error,'raw_surface_status':report['status']}
# TIMESTAMP END 2026-11-02T18:13:09-05:00 | REVISION R004829
R=Path(__file__).resolve().parents[1]
ap=argparse.ArgumentParser();ap.add_argument('--model',default='src/model-data.json');ap.add_argument('--output',default='src/enclosure-fit.json');args=ap.parse_args()
model_path=(R/args.model).resolve();raw=model_path.read_bytes();model=json.loads(raw)
components=json.loads(subprocess.check_output(['node','-e',"const m=require(process.argv[1]),s=require('./src/schematic-walls.js');process.stdout.write(JSON.stringify(s.build(m.parts,{applyFit:false}).components))",str(model_path)],cwd=R))
def solid(p):
 s=m.Manifold(m.Mesh64(np.asarray(p['vertices'],dtype=float),np.asarray(p['triangles'],dtype=np.uint64))).set_tolerance(1e-9)
 assert str(s.status())=='Error.NoError',p['id']
 return s
def overlap(a,b):
 x,y=a.bounding_box(),b.bounding_box();return all(x[i+3]>y[i]+1e-10 and y[i+3]>x[i]+1e-10 for i in range(3))
# TIMESTAMP START 2026-11-02T17:45:34-05:00 | REVISION R004824
timbers={p['id']:solid(p) for p in model['parts'] if p['is_timber'] or p.get('group')=='joinery_pegs'};footers={p['id']:solid(p) for p in components if p['schematicKind']=='footer'}
# TIMESTAMP END 2026-11-02T17:45:34-05:00 | REVISION R004824
# TIMESTAMP START 2026-11-02T18:45:37-05:00 | REVISION R004840
# Revert R004838: optional porch solids must not cut the standalone enclosure.
# The west wall instead remains inside its original porch-independent envelope.
# TIMESTAMP END 2026-11-02T18:45:37-05:00 | REVISION R004840
# TIMESTAMP START 2026-11-02T16:10:36-05:00 | REVISION R004814
foundation_path=R/'src/floor-foundation-solids.json'
foundation_raw=foundation_path.read_bytes();foundation=json.loads(foundation_raw)
floor_obstacles={**footers,**{p['id']:solid(p) for p in foundation['parts']}}
# TIMESTAMP END 2026-11-02T16:10:36-05:00 | REVISION R004814
# TIMESTAMP START 2026-11-02T13:44:32-05:00 | REVISION R004784
data={'source_model_sha256':hashlib.sha256(raw).hexdigest(),'source_module_sha256':hashlib.sha256((R/'src/schematic-walls.js').read_bytes()).hexdigest(),'status':'Visualization clearance fit only; wall framing joints, foundations and floor support undesigned.','parts':{}}
# TIMESTAMP START 2026-11-02T18:45:37-05:00 | REVISION R004840
# Removed the optional porch dependency introduced by R004838.
# TIMESTAMP END 2026-11-02T18:45:37-05:00 | REVISION R004840
# TIMESTAMP START 2026-11-02T16:10:36-05:00 | REVISION R004814
data['source_foundation_sha256']=hashlib.sha256(foundation_raw).hexdigest()
# TIMESTAMP END 2026-11-02T16:10:36-05:00 | REVISION R004814
for p in components:
 # TIMESTAMP START 2026-11-02T15:33:07-05:00 | REVISION R004807
 if p['schematicKind'] not in ['rail','wall','floor','shelf']:continue
 # TIMESTAMP END 2026-11-02T15:33:07-05:00 | REVISION R004807
 s=solid(p);before=s.volume();hits=[]
# TIMESTAMP START 2026-11-02T16:10:36-05:00 | REVISION R004814
 # TIMESTAMP START 2026-11-02T18:45:37-05:00 | REVISION R004840
 for name,t in (timbers if p['schematicKind']!='floor' else floor_obstacles).items():
 # TIMESTAMP END 2026-11-02T18:45:37-05:00 | REVISION R004840
# TIMESTAMP END 2026-11-02T16:10:36-05:00 | REVISION R004814
  if not overlap(s,t):continue
  amount=(s^t).volume()
  if amount>1e-12:s=s-t;hits.append({'part':name,'removed_m3':amount})
 # TIMESTAMP START 2026-11-02T15:33:07-05:00 | REVISION R004807
 # Through cuts can detach tiny board-end offcuts. Keep the connected shelf
 # middle, with every discarded offcut explicitly exported for the stock audit.
 offcuts=[]
 if p['schematicKind']=='shelf':
  # TIMESTAMP START 2026-11-02T18:13:09-05:00 | REVISION R004829
  shelf_pieces=s.decompose();kept=max(shelf_pieces,key=lambda item:item.volume())
  for component in shelf_pieces:
  # TIMESTAMP END 2026-11-02T18:13:09-05:00 | REVISION R004829
   if component is kept:continue
   # TIMESTAMP START 2026-11-02T19:00:59-05:00 | REVISION R004846
   # Match the boundary normalizer's zero-volume threshold; these numerical
   # surfaces are not physical offcuts. The kept shelf mesh is unchanged.
   if abs(component.volume())<=1e-16:continue
   # TIMESTAMP END 2026-11-02T19:00:59-05:00 | REVISION R004846
   offcut=component.to_mesh64()
   offcuts.append({'vertices':np.asarray(offcut.vert_properties)[:,:3].tolist(),
                   'triangles':np.asarray(offcut.tri_verts).tolist(),
                   'volume_m3':component.volume(),
                   'reason':'Detached end offcut after exact full-depth brace clearance; outside retained connected shelf middle.'})
  s=kept
 # TIMESTAMP END 2026-11-02T15:33:07-05:00 | REVISION R004807
 assert str(s.status())=='Error.NoError' and s.volume()>0,p['id']
 # TIMESTAMP START 2026-11-02T18:13:09-05:00 | REVISION R004829
 boundary_audit=None
 if p['schematicKind'] in ['wall','rail','shelf']:s,boundary_audit=normalize_boundary(s)
 # TIMESTAMP END 2026-11-02T18:13:09-05:00 | REVISION R004829
 mesh=s.to_mesh64();v=np.asarray(mesh.vert_properties)[:,:3];tris=mesh.tri_verts
# TIMESTAMP START 2026-11-02T16:10:36-05:00 | REVISION R004814
 # TIMESTAMP START 2026-11-02T18:45:37-05:00 | REVISION R004840
 for name,t in (timbers if p['schematicKind']!='floor' else floor_obstacles).items():
 # TIMESTAMP END 2026-11-02T18:45:37-05:00 | REVISION R004840
# TIMESTAMP END 2026-11-02T16:10:36-05:00 | REVISION R004814
  if overlap(s,t):assert (s^t).volume()<1e-10,(p['id'],name)
 data['parts'][p['id']]={'vertices':v.tolist(),'triangles':tris.tolist(),'center':((v.min(0)+v.max(0))/2).tolist(),'source_volume_m3':before,'fitted_volume_m3':s.volume(),'clearance_cuts':hits,'connected_components':len(s.decompose())}
 # TIMESTAMP START 2026-11-02T18:13:09-05:00 | REVISION R004829
 if boundary_audit:data['parts'][p['id']]['boundary_audit']=boundary_audit
 if p.get('panelAssemblyId'):data['parts'][p['id']].update(panelAssemblyId=p['panelAssemblyId'],panelSeamY_M=p['panelSeamY_M'],panelSeamPart=p['panelSeamPart'])
 # TIMESTAMP END 2026-11-02T18:13:09-05:00 | REVISION R004829
 # TIMESTAMP START 2026-11-02T15:33:07-05:00 | REVISION R004807
 if p['schematicKind']=='shelf':data['parts'][p['id']]['discarded_end_offcuts']=offcuts
 # TIMESTAMP END 2026-11-02T15:33:07-05:00 | REVISION R004807
# TIMESTAMP START 2026-11-02T18:13:09-05:00 | REVISION R004829
parents={p['panelAssemblyId'] for p in components if p.get('panelAssemblyId')}
unsplit=json.loads(subprocess.check_output(['node','-e',"const m=require(process.argv[1]),s=require('./src/schematic-walls.js');process.stdout.write(JSON.stringify(s.build(m.parts,{applyFit:false,splitInfill:false}).components))",str(model_path)],cwd=R))
data['panel_seams']={}
for p in unsplit:
 if p['id'] not in parents:continue
 expected=solid(p)
 # TIMESTAMP START 2026-11-02T18:45:37-05:00 | REVISION R004840
 for obstacle in timbers.values():
 # TIMESTAMP END 2026-11-02T18:45:37-05:00 | REVISION R004840
  if overlap(expected,obstacle):expected=expected-obstacle
 expected,_=normalize_boundary(expected)
 ids=[q['id'] for q in components if q.get('panelAssemblyId')==p['id']]
 children=[solid(dict(data['parts'][pid],id=pid)) for pid in ids]
 # TIMESTAMP START 2026-11-04T20:06:20+00:00 | REVISION R000007
 lower=m.Manifold.batch_boolean([shape for pid,shape in zip(ids,children) if next(p for p in components if p['id']==pid)['panelSeamPart']=='lower'],m.OpType.Add)
 upper=m.Manifold.batch_boolean([shape for pid,shape in zip(ids,children) if next(p for p in components if p['id']==pid)['panelSeamPart']=='upper'],m.OpType.Add)
 assembled=lower+upper
 # TIMESTAMP END 2026-11-04T20:06:20+00:00 | REVISION R000007
 error=abs((expected-assembled).volume())+abs((assembled-expected).volume())
 # TIMESTAMP START 2026-11-04T20:06:20+00:00 | REVISION R000007
 intersection=abs((lower^upper).volume())
 assert len(children)>=2 and error<FIT_TOLERANCE_M3 and intersection<FIT_TOLERANCE_M3,p['id']
 # TIMESTAMP END 2026-11-04T20:06:20+00:00 | REVISION R000007
 data['panel_seams'][p['id']]={'status':'PASS','child_ids':ids,'plane_y_m':64*.0254,
  'original_fitted_volume_m3':expected.volume(),'reassembled_volume_m3':assembled.volume(),
  'symmetric_volume_difference_m3':error,'child_overlap_m3':intersection,
  'construction':'Two separate boards sharing an exact plane; no material gap, added material or changed external panel envelope.'}
assert len(data['panel_seams'])==14
(R/args.output).write_text(json.dumps(data,separators=(',',':'))+'\n')
# TIMESTAMP END 2026-11-02T18:13:09-05:00 | REVISION R004829
# TIMESTAMP START 2026-11-02T15:33:07-05:00 | REVISION R004807
print('Fitted',len(data['parts']),'wall framing/infill/floor/shelf components; source model untouched'
# TIMESTAMP END 2026-11-02T15:33:07-05:00 | REVISION R004807
      ,'model SHA',data['source_model_sha256'])

# TIMESTAMP END 2026-11-02T13:44:32-05:00 | REVISION R004784
