# TIMESTAMP START 2026-11-03T17:00:04-05:00 | REVISION R005063
"""Read current perimeter joints from their actual exported occupied material."""
from pathlib import Path
import collections,hashlib,itertools,json,sys
import numpy as np
import manifold3d as m
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from audit_revised_joinery import native_solid as solid
from step_lap import I,close_bounds,regular_boundary,volume_centroid
from audit_cavity_fit import inspect_mesh,arrays,coplanar_surface_overlaps
base=json.loads((R/'src/model-data.json').read_text());full=json.loads((R/'src/step-lap-proposed-model.json').read_text());proposal=json.loads((R/'src/step-lap-proposal.json').read_text())
B={p['id']:p for p in base['parts']};P={p['id']:p for p in full['parts']}
assert set(B)==set(P)
assert proposal['baseline_model_sha256']==hashlib.sha256((R/'src/model-data.json').read_bytes()).hexdigest()
changed={pid for pid in P if P[pid]!=B[pid]}
assert changed==set(full['proposed_review']['changed_member_ids'])==set(proposal['combined_geometry_audit']['changed_member_ids'])
assert changed<={f'{f}{k}' for k in range(8) for f in ['P','B','R']}|{f'J{k}-{side}' for k in range(8) for side in ['0','2']}
shapes={pid:solid(p) for pid,p in P.items() if p['is_timber']}
for pid,s in shapes.items():
 assert inspect_mesh(*arrays(P[pid]),require_single=True)['status']=='PASS',pid
 assert s.volume()>0 and len(s.decompose())==1
for a,b in itertools.combinations(shapes,2):
 if close_bounds(shapes[a],shapes[b]):assert (shapes[a]^shapes[b]).volume()/I**3<1e-6,(a,b)
assert len(proposal['variants'])==24
for joint in proposal['variants']:
 a,b=joint['member_ids'];tool=solid(joint['added_parts'][0]);removed=solid(joint['removed_parts'][0])
 assert tool.volume()/I**3>.01
 assert abs((tool-removed).volume())+abs((removed-tool).volume())<1e-12
 assert (tool-shapes[a]).volume()/I**3<1e-6,(a,'retained toe missing')
 assert (tool^shapes[b]).volume()/I**3<1e-6,(b,'receiving seat not empty')
 assert shapes[a].min_gap(shapes[b],.01)<1e-8,(a,b,'bearing gap')
 assert joint['uplift_retention']=='unresolved'
for member in full['proposed_member_volume_centroids']:
 actual=volume_centroid(shapes[member['id']]);assert abs(actual['volume_m3']-member['volume_m3'])<1e-12
 assert np.linalg.norm(np.asarray(actual['centroid_m'])-member['centroid_m'])<1e-10
# Guard the shared planar boundary repair independently of project geometry.
unit=m.Manifold.cube((.1,.1,.1))
for shift,count in [((.1,0,0),1),((.1,.2,0),2)]:
 original=m.Manifold.compose([unit,unit.translate(shift)]);cleaned=regular_boundary(original);mesh=cleaned.to_mesh64()
 assert coplanar_surface_overlaps(np.asarray(mesh.vert_properties)[:,:3],np.asarray(mesh.tri_verts))['status']=='PASS'
 assert len(cleaned.decompose())==count and abs(cleaned.volume()-.002)<1e-12
 assert abs((cleaned-original).volume())+abs((original-cleaned).volume())<1e-12
print('PASS: 24 current complementary perimeter seats, 112 clean timbers, all physical pairs and current mass data; planar repair guard passes')
# TIMESTAMP END 2026-11-03T17:00:04-05:00 | REVISION R005063
