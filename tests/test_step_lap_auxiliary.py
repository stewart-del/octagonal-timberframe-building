"""Selected-model derived data invariants. No contact demand/capacity inference."""
from pathlib import Path
import hashlib,json,sys
import numpy as np
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from step_lap import solid,volume_centroid,close_bounds
from step_lap_auxiliary import generate
I=.0254
raw=(R/'src/step-lap-proposed-model.json').read_bytes();sha=hashlib.sha256(raw).hexdigest();model=json.loads(raw);parts={p['id']:p for p in model['parts']};S={p['id']:solid(p) for p in model['parts'] if p['is_timber']}
load=json.loads((R/'src/step-lap-proposed-load-review.json').read_text());cav=json.loads((R/'src/step-lap-proposed-cavities.json').read_text());mat=json.loads((R/'src/step-lap-proposed-material-groups.json').read_text());fit=json.loads((R/'src/step-lap-proposed-enclosure-fit.json').read_text());proposal=json.loads((R/'src/step-lap-proposal.json').read_text());old=json.loads((R/'src/cavity-data.json').read_text())
assert load['source_model_sha256']==cav['source_model_sha256']==fit['source_model_sha256']==mat['source_sha256']==sha
assert len(load['members'])==104 and len(fit['parts'])==48
assert cav['available'] is False and cav['parts']=={} and cav['summary']['complete'] is False
assert 'No baseline overlay substituted' in cav['status']
assert fit['source_module_sha256']==hashlib.sha256((R/'src/schematic-walls.js').read_bytes()).hexdigest()
assert load['issues']==[] and load['baseline_pressure_disabled'] is True
for p in load['members']:
 actual=volume_centroid(S[p['id']]);assert abs(actual['volume_m3']-p['volume_m3'])<1e-12
 assert np.linalg.norm(np.asarray(actual['centroid_m'])-p['centroid_m'])<1e-10
for name,p in fit['parts'].items():
 if '-rail' not in name:continue
 s=solid(dict(p,id=name))
 for tid,t in S.items():
  if close_bounds(s,t):assert (s^t).volume()<1e-10,(name,tid)
files=[R/'src'/('step-lap-proposed-'+n+'.json') for n in ['load-review','cavities','material-groups']];before=[p.read_bytes() for p in files];generate();assert before==[p.read_bytes() for p in files]
assert (R/'src/step-lap-proposed-model.json').read_bytes()==raw
print('PASS: proposed104 applied self-weight volumes/centroids, source-bound inventory/cavities/48 enclosure components; cavity overlays explicitly unavailable; no stale overlay; pressure/contact markers withheld; deterministic auxiliary generation')
