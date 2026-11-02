"""Independent selected-geometry invariants; no structural/erection approval."""
from pathlib import Path
import collections,hashlib,itertools,json,sys
import numpy as np
import manifold3d as m
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from step_lap import I,solid,contacts,volume_centroid,close_bounds,section,original_stock
from top_entry_heads import vertical_sweep,build_all
from regeneration_equivalence import assert_equivalent,test_guard
from mesh_regeneration_equivalence import normalize_planar_retriangulation,test_mesh_guard,normalize_section_diagrams,test_section_guard
raw=(R/'src/step-lap-proposed-model.json').read_bytes();source=json.loads(raw);sha=hashlib.sha256(raw).hexdigest();D=json.loads((R/'src/top-entry-proposal.json').read_text());F=json.loads((R/'src/top-entry-proposed-model.json').read_text())
B={p['id']:p for p in source['parts']};P={p['id']:p for p in F['parts']};changed={f'R{k}' for k in range(8)}|{f'J{k}-{s}' for k in range(8) for s in ['0','2']};S={k:solid(p) for k,p in P.items() if p['is_timber']}
assert sha==D['source_model_sha256']==F['top_entry_review']['source_model_sha256']
assert len(S)==104 and set(B)==set(P) and len(changed)==24
assert len(D['interfaces'])==16 and {x['id'] for x in D['interfaces']}=={f'J{k}-0_R{k}' for k in range(8)}|{f'J{k}-2_R{(k+1)%8}' for k in range(8)}
for name,p in P.items():
 if name not in changed:assert p==B[name],name;continue
 for key in ['axis_start','axis_end','axis_direction','stock_frame','exploded_offset','nominal_dimensions']:
  assert p[key]==B[name][key],(name,key)
 assert p['fabrication_dimensions_valid'] is False and p['reference_end_faces']==p['joint_cut_faces']==[]
 assert str(S[name].status())=='Error.NoError' and len(S[name].decompose())==1,name
 edges=collections.Counter(tuple(sorted((t[i],t[(i+1)%3]))) for t in p['triangles'] for i in range(3));assert all(n==2 for n in edges.values()),name
 # Direct source halfspaces, independent of the producer's hull reconstruction.
 v=np.asarray(p['vertices']);v=np.column_stack((v[:,0],-v[:,2],v[:,1]))/I
 planes=p.get('proposed_stock_planes_inches',p['geometry_planes_inches'])
 for plane in planes:assert np.max(v@plane['normal']-plane['constant'])<1e-6,(name,'raw stock')
 bay=int(name[1]);radial=np.array([np.cos(bay*np.pi/4),0,-np.sin(bay*np.pi/4)])
 before=solid(B[name]).trim_by_plane(tuple(radial),100*I);after=S[name].trim_by_plane(tuple(radial),100*I)
 assert abs((before-after).volume())/I**3<1e-6 and abs((after-before).volume())/I**3<1e-6,(name,'perimeter foot changed')
count=0;worst=0.
for a,b in itertools.combinations(S,2):
 if not ({a,b}&changed):continue
 count+=1
 if not close_bounds(S[a],S[b]):continue
 amount=max(0.,(S[a]^S[b]).volume()/I**3);worst=max(worst,amount);assert amount<1e-6,(a,b,'interference',amount)
assert count==2196
for v in D['interfaces']:
 a,b=v['owner'],v['receiver'];faces=contacts(S[a],S[b]);bearing=sum(f['area_in2'] for f in faces if f['normal_on_rafter'][1]<-.01)
 assert abs(bearing-22.03581266897)<1e-6,(a,b,'bearing area')
 assert not any(f['normal_on_rafter'][1]>.01 and f['area_in2']>.001 for f in faces),(a,b,'closed upper retaining face')
 assert S[a].min_gap(S[b],.01)<1e-8
 assert abs(v['stock_extension_along_J_axis_in']-5.55601152397475)<1e-10
 for p in v['proposed_parts']:assert p==P[p['id']]
 # Verify each actual generated member, not only copied seed sweep metadata.
 cover=vertical_sweep(S[a],24*I);omission_bound=len(P[a]['triangles'])*1e-15/I**3
 for other,t in S.items():
  if other==a:continue
  upper=sum(max(0.,(prism^t).volume()/I**3) for prism in cover if close_bounds(prism,t))+omission_bound
  assert upper<1e-6,(a,other,'continuous vertical insertion obstruction',upper)
# Guard the sweep test itself: endpoints are clear but an intermediate block is hit.
box=m.Manifold.cube((I,I,I));obstacle=box.translate((0,10*I,0))
assert (box^obstacle).volume()==0 and (box.translate((0,24*I,0))^obstacle).volume()==0
assert sum((p^obstacle).volume() for p in vertical_sweep(box,24*I))>I**3*.9
assert len(D['geometry_audit']['perimeter_preservation'])==24
assert not D['geometry_audit']['interferences'] and not D['geometry_audit']['lost_neighbor_contacts']
assert len(D['geometry_audit']['continuous_vertical_sweeps'])==16 and all(not x['interferences'] for x in D['geometry_audit']['continuous_vertical_sweeps'])
assert D['geometry_audit']['capacity_checked'] is False and 'NOT FABRICATION' in F['status']
volume=sum(volume_centroid(s)['volume_m3'] for s in S.values());assert abs(volume-D['proposed_timber_volume_m3'])<1e-11 and abs(volume-6.293660066069135)<1e-11
assert len(F['proposed_member_volume_centroids'])==104
for p in F['proposed_member_volume_centroids']:
 q=volume_centroid(S[p['id']]);assert abs(q['volume_m3']-p['volume_m3'])<1e-12;assert np.linalg.norm(np.array(q['centroid_m'])-p['centroid_m'])<1e-10
# Regeneration is slow (all contacts/sweeps); CI includes it so the
# saved data remains reproducible without touching any production source file.
test_guard();test_mesh_guard();test_section_guard();generated,model=(json.loads(json.dumps(x)) for x in build_all(source,sha))
# A BLAS-dependent last bit may choose another diagonal on the same plane.
# Normalize only after exact feature-edge identity, oriented plane/area/centroid,
# manifold/connectedness and tight volume/vertex checks prove the same surface.
print('Planar regeneration:',normalize_planar_retriangulation(generated,D),normalize_planar_retriangulation(model,F))
normalize_section_diagrams(generated,D);normalize_section_diagrams(model,F)
assert_equivalent(generated,D,('top_entry',));assert_equivalent(model,F,('top_entry_model',))
assert (R/'src/step-lap-proposed-model.json').read_bytes()==raw
print('PASS: all16 upper heads,2196 pairs, full24in insertion coverage,24 unchanged lower feet, raw-stock bounds,104 weights/centroids and bounded regeneration; worst overlap in3',worst)
