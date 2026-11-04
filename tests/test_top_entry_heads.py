# TIMESTAMP START 2026-11-03T17:00:04-05:00 | REVISION R005063
"""Verify current open head seats and full continuous vertical removal."""
from pathlib import Path
import hashlib,itertools,json,sys
import numpy as np
import manifold3d as m
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from audit_revised_joinery import native_solid as solid
from step_lap import I,contacts,close_bounds,volume_centroid
from audit_cavity_fit import inspect_mesh,arrays
from top_entry_heads import vertical_sweep
source=json.loads((R/'src/step-lap-proposed-model.json').read_text());model=json.loads((R/'src/top-entry-proposed-model.json').read_text());proposal=json.loads((R/'src/top-entry-proposal.json').read_text())
parts={p['id']:p for p in model['parts']};before={p['id']:p for p in source['parts']};S={pid:solid(p) for pid,p in parts.items() if p['is_timber']}
assert len(S)==112 and set(parts)-set(before)=={f'CP{k}' for k in range(8)}
assert proposal['baseline_model_sha256']==hashlib.sha256((R/'src/step-lap-proposed-model.json').read_bytes()).hexdigest()
assert len(proposal['interfaces'])==16
for interface in proposal['interfaces']:
 a,b=interface['owner'],interface['receiver'];p=parts[a];s=S[a]
 assert inspect_mesh(*arrays(p),require_single=True)['status']=='PASS'
 face=contacts(s,S[b]);bearing=sum(f['area_in2'] for f in face if f['normal_on_rafter'][1]<-.01)
 assert abs(bearing-22.03581266897)<1e-6,(a,b,'bearing area')
 assert not any(f['normal_on_rafter'][1]>.01 and f['area_in2']>.001 for f in face)
 assert s.min_gap(S[b],.01)<1e-8
 # A full vertical swept surface is checked against every other actual timber.
 cover=vertical_sweep(s,24*I);bound=len(p['triangles'])*1e-15/I**3
 for other,t in S.items():
  if other==a:continue
  amount=sum(max(0.,(cell^t).volume()/I**3) for cell in cover if close_bounds(cell,t))+bound
  assert amount<1e-6,(a,other,'blocked insertion',amount)
for member in model['proposed_member_volume_centroids']:
 q=volume_centroid(S[member['id']]);assert abs(q['volume_m3']-member['volume_m3'])<1e-12
 assert np.linalg.norm(np.asarray(q['centroid_m'])-member['centroid_m'])<1e-10
box=m.Manifold.cube((I,I,I));obstacle=box.translate((0,10*I,0))
assert (box^obstacle).volume()==0 and (box.translate((0,24*I,0))^obstacle).volume()==0
assert sum((cell^obstacle).volume() for cell in vertical_sweep(box,24*I))>.9*I**3
assert proposal['geometry_audit']['capacity_checked'] is False
print('PASS: 16 current open head seats, actual bearing areas, 24-inch continuous insertion, current mass data and intermediate-obstacle guard')
# TIMESTAMP END 2026-11-03T17:00:04-05:00 | REVISION R005063
