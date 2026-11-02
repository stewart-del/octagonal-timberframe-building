"""Independent invariants for actual proposed CSG, never structural approval."""
from pathlib import Path
import collections,hashlib,itertools,json,math,sys
import numpy as np
import manifold3d as m
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
# TIMESTAMP START 2026-11-02T10:36:58-05:00 | REVISION R004765
from step_lap import build_proposal,solid,volume_centroid,regular_boundary
from audit_cavity_fit import coplanar_surface_overlaps
# TIMESTAMP END 2026-11-02T10:36:58-05:00 | REVISION R004765
from regeneration_equivalence import assert_equivalent,test_guard
I=.0254;raw=(R/'src/model-data.json').read_bytes();base=json.loads(raw);sha=hashlib.sha256(raw).hexdigest();data=json.loads((R/'src/step-lap-proposal.json').read_text());full=json.loads((R/'src/step-lap-proposed-model.json').read_text())
B={p['id']:p for p in base['parts']};P={p['id']:p for p in full['parts']};changed={f'{family}{k}' for k in range(8) for family in ['B','P','R']}|{f'J{k}-{side}' for k in range(8) for side in ['0','2']}
assert sha=='15fc4fbbbdd520e4d0b332140b0f80daaf8f8b36d112dceac429cab598a4d331','Baseline changed: re-review assumptions and regenerate, never silently rebase'
# The sole accepted baseline change was the seated temporary aid. Freeze every
# other original component independently of the mutable migration report.
proof_raw=(R/'docs/pre-support-baseline-part-hashes.json').read_bytes()
assert hashlib.sha256(proof_raw).hexdigest()=='cbc6bba49f4b8389ffe0780d672aaf4b7bdccdd253825971b1625751dd51885f'
proof=json.loads(proof_raw)
assert set(proof)==set(B)-{'M-TMP'} and len(proof)==114
for name,expected in proof.items():
 assert hashlib.sha256(json.dumps(B[name],sort_keys=True,separators=(',',':')).encode()).hexdigest()==expected,(name,'non-aid baseline changed')
assert data['baseline_model_sha256']==sha and data['canonical_model_unchanged'] is True
assert set(B)==set(P) and len([p for p in full['parts'] if p['is_timber']])==104
for name in B:
 if name not in changed:assert B[name]==P[name],name
 else:
  assert B[name]['vertices']!=P[name]['vertices'] and B[name]['triangles']!=P[name]['triangles']
  for key in ['axis_start','axis_end','axis_direction','stock_frame','exploded_offset','geometry_planes_inches']:
   assert B[name][key]==P[name][key],(name,key)
  assert P[name]['fabrication_dimensions_valid'] is False and not P[name]['reference_end_faces'] and not P[name]['joint_cut_faces']
assert 'NOT FABRICATION APPROVED' in full['status']
assert full['joinery_verification']['status']=='PROPOSED GEOMETRY ONLY'
assert 'load_review_data' not in full and 'cavity_data' not in full
S={p['id']:solid(p) for p in full['parts'] if p['is_timber']}
for name,s in S.items():
 assert str(s.status())=='Error.NoError' and len(s.decompose())==1,name
 if name in changed:
  v=np.asarray(P[name]['vertices']);t=P[name]['triangles'];edges=collections.Counter(tuple(sorted((tri[j],tri[(j+1)%3]))) for tri in t for j in range(3));assert all(c==2 for c in edges.values()),name
# All 3340 pairs affected by any of the 40 changed members are checked independently.
count=0
for a,b in itertools.combinations(S,2):
 if not ({a,b}&changed):continue
 count+=1;aa=S[a].bounding_box();bb=S[b].bounding_box()
 if any(aa[j+3]<bb[j]-1e-9 or bb[j+3]<aa[j]-1e-9 for j in range(3)):continue
 assert (S[a]^S[b]).volume()/I**3<1e-6,(a,b,'interference')
assert count==3340 and not data['combined_geometry_audit']['interferences'] and not data['combined_geometry_audit']['lost_neighbor_contacts']
for v in data['variants']:
 a,b=v['member_ids'];old_a,old_b=solid(B[a]),solid(B[b]);new_a,new_b=S[a],S[b]
 # Authoritative closed tongue/pocket masks avoid unstable subtraction of
 # reimported nearly coplanar faces. Signed whole-solid deltas remain independent.
 added=solid(v['added_parts'][0]);removed=solid(v['removed_parts'][0])
 assert added.volume()/I**3>.01 and removed.volume()/I**3>.01
 assert v['added_parts'][0]['vertices']==v['removed_parts'][0]['vertices']
 assert v['added_parts'][0]['triangles']==v['removed_parts'][0]['triangles']
 assert abs((new_a.volume()-old_a.volume())-added.volume())/I**3<1e-6
 expected=sum(solid(w['removed_parts'][0]).volume() for w in data['variants'] if w['member_ids'][1]==b)
 assert abs((old_b.volume()-new_b.volume())-expected)/I**3<1e-6
 assert abs(v['measurements']['receiver_total_removed_volume_in3']-expected/I**3)<1e-6
 assert v['measurements']['receiver_proposed_pocket_count']==(2 if b.startswith('B') else 1)
 for p in v['proposed_parts']:assert p==P[p['id']]
 # Independent direct original halfspace test, not the producer's hull helper.
 av=np.asarray(added.to_mesh64().vert_properties)[:,:3];source=np.column_stack((av[:,0],-av[:,2],av[:,1]))/I
 for plane in B[a]['geometry_planes_inches']:assert np.max(source@plane['normal']-plane['constant'])<1e-6,(a,'outside original stock')
 width=np.asarray(B[a]['stock_frame']['width']);span=np.ptp(av@width)/I
 assert abs(span-v['parameters']['tongue_width']['value'])<1e-8
 assert abs((v['local_frame']['origin_m'][1]-av[:,1].min())/I-v['parameters']['maximum_additional_engagement']['value'])<1e-8
 # Opposed nonzero cheek areas, no false claim of a mechanical uplift lock.
 cheeks=v['measurements']['transverse_cheek_contacts'];directions={int(np.sign(np.asarray(f['normal_on_rafter'])@width)) for f in cheeks}
 assert directions=={-1,1} and all(f['area_in2']>1 for f in cheeks)
 assert v['uplift_retention']=='unresolved' and v['fastener_detail']=='unresolved'
 profiles=v['cut_profiles'];assert profiles['rafter_retained_tongue_closed_polygons']==profiles['receiver_removed_pocket_closed_polygons']
 assert all(polygon[0]==polygon[-1] and len(polygon)>=4 for polygon in profiles['rafter_retained_tongue_closed_polygons'])
 assert v['source_attachment_id'] is None and v['source_pdf_page'] is None
 for g in v['measurements']['proposed_member_mass_geometry']:
  check=volume_centroid(S[g['member_id']]);assert abs(check['volume_m3']-g['volume_m3'])<1e-12 and np.linalg.norm(np.asarray(check['centroid_m'])-g['centroid_m'])<1e-10
assert len(data['variants'])==24 and len({v['id'] for v in data['variants']})==24
assert {tuple(v['member_ids']) for v in data['variants']}=={(f'J{k}-{side}',f'B{k}') for k in range(8) for side in ['0','2']}|{(f'R{k}',f'P{k}') for k in range(8)}
for v in data['variants']:
 if v['member_ids'][0].startswith('J'):
  assert abs(v['measurements']['proposed_horizontal_bearing_area_in2']-6.45672280493)<1e-7
  assert abs(v['measurements']['proposed_inclined_contact_area_in2']-5.8930445807)<1e-5
  assert 'horizontal component' in ' '.join(v['findings']) and 'capacity loss or gain' in ' '.join(v['findings'])
 else:
  assert abs(v['measurements']['proposed_horizontal_bearing_area_in2']-64)<1e-7
  assert abs(v['measurements']['remaining_local_sections'][1]['proposed_area_in2']-32)<1e-4
 # Independently derive the spatial symmetry, including right-hand J reflection.
 theta=v['bay']*math.pi/4;c,s=math.cos(theta),math.sin(theta);rot=np.array([[c,0,s],[0,1,0],[-s,0,c]])
 if v['handed_reflection']:
  normal=np.array([math.sin(math.pi/8),0,math.cos(math.pi/8)]);rot=rot@(np.eye(3)-2*np.outer(normal,normal))
 seed=next(x for x in data['variants'] if x['id']==v['reference_seed_id']);want=np.asarray(seed['added_parts'][0]['vertices'])@rot.T;actual=np.asarray(v['added_parts'][0]['vertices'])
 assert max(min(np.linalg.norm(actual-q,axis=1)) for q in want)<1e-10
assert sum(v['handed_reflection'] for v in data['variants'])==8
assert not data['combined_geometry_audit']['held_interfaces']
assert data['combined_geometry_audit']['implemented_interface_count']==24
assert abs(data['baseline_timber_volume_m3']-data['proposed_timber_volume_m3'])<1e-10
assert len(full['proposed_member_volume_centroids'])==104
# TIMESTAMP START 2026-11-02T10:36:58-05:00 | REVISION R004765
# Coplanar normalization must cancel a coincident internal face but preserve
# legitimate opposite-facing, disjoint regions on that same support plane.
unit=m.Manifold.cube((.1,.1,.1))
for label,fixture,components in [
 ('touching cubes',m.Manifold.compose([unit,unit.translate((.1,0,0))]),1),
 ('disjoint opposing plane regions',m.Manifold.compose([unit,unit.translate((.1,.2,0))]),2)]:
 cleaned=regular_boundary(fixture);mesh=cleaned.to_mesh64()
 check=coplanar_surface_overlaps(np.asarray(mesh.vert_properties)[:,:3],np.asarray(mesh.tri_verts))
 assert check['status']=='PASS',(label,check)
 assert len(cleaned.decompose())==components,(label,'lost connected region')
 assert abs(cleaned.volume()-.002)<1e-12,(label,'changed occupied volume')
 assert abs((cleaned-fixture).volume())+abs((fixture-cleaned).volume())<1e-12,(label,'changed occupied set')
print('PASS: planar repair cancels hidden coincident faces and retains disjoint opposite-facing surfaces')
# TIMESTAMP END 2026-11-02T10:36:58-05:00 | REVISION R004765

# Regeneration must preserve exact structure/topology/claims and geometry within
# tiny unit-aware roundoff bounds. BLAS CPU dispatch changes last bits, so byte
# equality across machines is not a geometric-equivalence test. Existing
# independent stock/contact/intersection checks above remain unchanged.
test_guard()
# Compare the JSON domain actually emitted by the generator, normalizing
# NumPy float scalars without rounding any value.
ag,fg=(json.loads(json.dumps(x)) for x in build_proposal(base,sha))
for member in fg['parts']:
 if member['id'] in changed:
  surface=coplanar_surface_overlaps(np.asarray(member['vertices']),np.asarray(member['triangles']))
  assert surface['status']=='PASS',(member['id'],'regenerated raw surface overlap',surface)
from mesh_regeneration_equivalence import normalize_planar_retriangulation, test_mesh_guard
test_mesh_guard()
# CPU-dependent triangulation may choose a different diagonal on the same
# oriented planar surface. Retain strict vertices, feature edges, manifold,
# plane areas/centroids and occupied-volume checks before comparing metadata.
print('Planar regeneration:',normalize_planar_retriangulation(ag,data),normalize_planar_retriangulation(fg,full))
print("Regeneration roundoff:",assert_equivalent(ag,data,("proposal",)),assert_equivalent(fg,full,("model",)))
assert (R/'src/model-data.json').read_bytes()==raw
print('PASS: actual complementary tongue/pocket CSG; matched closed profiles; original-stock bounds; all 24 interfaces / 3340 affected pairs clear;104 member volumes/centroids refreshed; baseline exact; no fabricated strength/retention/manual claims')
