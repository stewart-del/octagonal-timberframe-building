from pathlib import Path
import hashlib,json,sys,numpy as np
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from step_lap import solid,volume_centroid,close_bounds
from top_entry_auxiliary import generate
raw=(R/'src/top-entry-proposed-model.json').read_bytes();sha=hashlib.sha256(raw).hexdigest();model=json.loads(raw);parts={p['id']:p for p in model['parts']};S={k:solid(p) for k,p in parts.items() if p['is_timber']}
load=json.loads((R/'src/top-entry-proposed-load-review.json').read_text());mat=json.loads((R/'src/top-entry-proposed-material-groups.json').read_text());cav=json.loads((R/'src/top-entry-proposed-cavities.json').read_text());fit=json.loads((R/'src/top-entry-proposed-enclosure-fit.json').read_text())
assert load['source_model_sha256']==cav['source_model_sha256']==fit['source_model_sha256']==mat['source_sha256']==sha
assert len(load['members'])==104 and len(fit['parts'])==48 and load['issues']==[] and load['baseline_pressure_disabled']
assert fit['source_module_sha256']==hashlib.sha256((R/'src/schematic-walls.js').read_bytes()).hexdigest()
assert not cav['available'] and not cav['parts'] and 'follow-on' in cav['repair_status']
for p in load['members']:
 q=volume_centroid(S[p['id']]);assert abs(q['volume_m3']-p['volume_m3'])<1e-12;assert np.linalg.norm(np.array(q['centroid_m'])-p['centroid_m'])<1e-10
for name,p in fit['parts'].items():
 if '-rail' not in name:continue
 s=solid(dict(p,id=name))
 for tid,t in S.items():
  if close_bounds(s,t):assert (s^t).volume()<1e-10,(name,tid)
files=[R/'src'/('top-entry-proposed-'+x+'.json') for x in ['load-review','material-groups','cavities']];before=[p.read_bytes() for p in files];generate();assert before==[p.read_bytes() for p in files]
assert (R/'src/top-entry-proposed-model.json').read_bytes()==raw
print('PASS: top-entry model-bound104 selfweights, inventory,48 enclosure fits and explicit pending cavity repair; no stale pressures/contact markers')
