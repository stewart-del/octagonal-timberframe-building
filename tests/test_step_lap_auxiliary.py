"""Selected-model derived data invariants. No contact demand/capacity inference."""
from pathlib import Path
import hashlib,json,sys
import numpy as np
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from step_lap import solid,volume_centroid,close_bounds
from step_lap_auxiliary import generate
# TIMESTAMP START 2026-11-02T10:08:03-05:00 | REVISION R004759
from audit_cavity_fit import assert_equivalent_report
# TIMESTAMP END 2026-11-02T10:08:03-05:00 | REVISION R004759
I=.0254
raw=(R/'src/step-lap-proposed-model.json').read_bytes();sha=hashlib.sha256(raw).hexdigest();model=json.loads(raw);parts={p['id']:p for p in model['parts']};S={p['id']:solid(p) for p in model['parts'] if p['is_timber']}
load=json.loads((R/'src/step-lap-proposed-load-review.json').read_text());cav=json.loads((R/'src/step-lap-proposed-cavities.json').read_text());mat=json.loads((R/'src/step-lap-proposed-material-groups.json').read_text());fit=json.loads((R/'src/step-lap-proposed-enclosure-fit.json').read_text());proposal=json.loads((R/'src/step-lap-proposal.json').read_text());old=json.loads((R/'src/cavity-data.json').read_text())
assert load['source_model_sha256']==cav['source_model_sha256']==fit['source_model_sha256']==mat['source_sha256']==sha
# TIMESTAMP START 2026-11-02T13:42:10-05:00 | REVISION R004782
import subprocess
fit_ids=json.loads(subprocess.check_output(['node','-e',"const s=require('./src/schematic-walls.js'),m=JSON.parse(require('fs').readFileSync(0,'utf8'));process.stdout.write(JSON.stringify(s.build(m.parts,{applyFit:false}).components.filter(p=>['rail','wall','floor'].includes(p.schematicKind)).map(p=>p.id)))"],input=raw,cwd=R))
assert len(load['members'])==104 and set(fit['parts'])==set(fit_ids)
assert sum('-rail-jamb-' in name for name in fit_ids)==12
# TIMESTAMP END 2026-11-02T13:42:10-05:00 | REVISION R004782
# TIMESTAMP START 2026-11-02T10:08:03-05:00 | REVISION R004759
assert cav['available'] is True and cav['summary']['complete'] is True
assert set(cav['parts'])==set(S) and len(cav['parts'])==104
assert cav['baseline_model_sha256']==proposal['baseline_model_sha256']==old['source_model_sha256']
assert cav['baseline_cavity_sha256']==hashlib.sha256((R/'src/cavity-data.json').read_bytes()).hexdigest()
assert cav['proposal_sha256']==hashlib.sha256((R/'src/step-lap-proposal.json').read_bytes()).hexdigest()
assert cav['transfer_count']==24
assert 'validation_hold' not in cav
for name,record in cav['parts'].items():
 assert 'removed' in record and 'unfilled' not in record and 'occupied_volume_m3' not in record,name
 if record['removed']['triangles']:
  assert record['removed']['volume_m3']>0,name
# TIMESTAMP END 2026-11-02T10:08:03-05:00 | REVISION R004759
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
# TIMESTAMP START 2026-11-02T10:08:03-05:00 | REVISION R004759
# Committed floats may differ by platform roundoff. Preserve all published data
# after the check, including on failure; repeated generation must be byte-stable.
files=[R/'src'/('step-lap-proposed-'+n+'.json') for n in ['load-review','cavities','material-groups']]
before=[p.read_bytes() for p in files]
try:
 generate()
 generated=[p.read_bytes() for p in files]
 for path,previous,current in zip(files,before,generated):
  assert_equivalent_report(json.loads(previous),json.loads(current),path.name)
 generate()
 assert generated==[p.read_bytes() for p in files]
finally:
 for path,original in zip(files,before):path.write_bytes(original)
assert before==[p.read_bytes() for p in files]
# TIMESTAMP END 2026-11-02T10:08:03-05:00 | REVISION R004759
assert (R/'src/step-lap-proposed-model.json').read_bytes()==raw
# TIMESTAMP START 2026-11-02T10:08:03-05:00 | REVISION R004759
# TIMESTAMP START 2026-11-02T13:42:10-05:00 | REVISION R004782
print('PASS: proposed104 applied self-weight volumes/centroids, source-bound inventory/cavities/complete enclosure components; matching removed-only cavity exports; pressure/contact markers withheld; deterministic auxiliary generation')
# TIMESTAMP END 2026-11-02T13:42:10-05:00 | REVISION R004782
# TIMESTAMP END 2026-11-02T10:08:03-05:00 | REVISION R004759
