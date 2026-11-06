# TIMESTAMP START 2026-11-05T14:08:26+00:00 | REVISION R000045
"""Read exact current floor products and test actual occupied contact geometry."""
import sys
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from physical_data import read_physical_json
from plan_architectural_disassembly import scene_from_payload,audit_initial_scene,sweep_cover,VOLUME_TOLERANCE_M3

d=read_physical_json(R/'src/floor-foundation-solids.json');scene=scene_from_payload('floor',d);ss=scene.solids
report=audit_initial_scene(scene)
assert report['status']=='PASS',report['collisions'][:12]
assert report['overlap_tolerance_m3']==1e-6*.0254**3
keys=list(ss);boxes=np.asarray([ss[pid].bounding_box() for pid in keys]);contacts={pid:[] for pid in keys}
# The distance check includes touching boxes; the independent overlap audit
# above retains its original strict positive-volume threshold.
for i,a in enumerate(keys):
 candidates=np.flatnonzero(np.all(boxes[i,:3]-1e-8<boxes[i+1:,3:],axis=1)&np.all(boxes[i,3:]+1e-8>boxes[i+1:,:3],axis=1))+i+1
 for j in candidates:
  b=keys[int(j)]
  if ss[a].min_gap(ss[b],.00001)<1e-7:contacts[a].append(b);contacts[b].append(a)
# Clearance-fit hardwood pins intentionally have .001in radial clearance.
# Prove that exact declared bore size engages both actual joint members;
# never count an arbitrary nearby piece or relax the occupied overlap rule.
clearance_fits=[]
for pid,adjacent in contacts.items():
 if adjacent:continue
 part=scene.parts[pid]
 if part.get('material')!='hardwood peg':continue
 diameter=part.get('diameter_in');bore=part.get('modeled_bore_diameter_in')
 assert diameter and bore and diameter<bore<=diameter+.0020000001,(pid,'Missing finite peg/bore clearance')
 clearance=(bore-diameter)*.0254/2
 vertices=np.asarray(part['vertices'],float);center=vertices.mean(0);values,vectors=np.linalg.eigh((vertices-center).T@(vertices-center));axis=vectors[:,-1]
 axial=np.outer((vertices-center)@axis,axis);radial=vertices-center-axial
 probe_vertices=center+axial+radial*(bore/diameter)
 import manifold3d as m
 probe=m.Manifold(m.Mesh64(probe_vertices,np.asarray(part['triangles'],np.uint64)))
 assert str(probe.status())=='Error.NoError' and probe.volume()>0,pid
 receivers=part.get('receiverIds',[]);assert len(receivers)==2,(pid,'Peg must cross donor and receiver')
 for receiver in receivers:
  gap=ss[pid].min_gap(ss[receiver],2*clearance)
  assert 0<=gap<=clearance+1e-7,(pid,receiver,'Actual radial gap exceeds declared bore clearance',gap,clearance)
  assert probe.min_gap(ss[receiver],.00001)<1e-7,(pid,receiver,'Declared bore size fails to engage actual joint member')
 clearance_fits.append(pid)
isolated=[pid for pid,adjacent in contacts.items() if not adjacent and pid not in clearance_fits]
assert not isolated,('Unconnected occupied floor component',isolated)
print('PASS',len(clearance_fits),'finite-clearance hardwood pins engage both actual receiving bore walls at declared diameter',flush=True)
print('PASS',len(keys),'positive solids;',report['pair_checks'],'native intersections at original1e-6in3 tolerance; each touches another; contact is not capacity approval',flush=True)
for pid,s in ss.items():
 if not pid.startswith('FLOOR-JOIST-'):continue
 sweep,account=sweep_cover(s,[0,.17,0])
 for plate,q in ss.items():
  if plate.startswith('POST-BEARING-STAND-') and '-SIDE' in plate:
   assert (sweep^q).volume()+account['discarded_prism_volume_m3']<VOLUME_TOLERANCE_M3,(pid,plate)
print('PASS: actual north-south joists clear the open sideplate slots after their fasteners and headplates are removed')
# TIMESTAMP END 2026-11-05T14:08:26+00:00 | REVISION R000045
