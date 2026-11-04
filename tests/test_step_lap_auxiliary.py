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
# TIMESTAMP START 2026-11-02T15:33:07-05:00 | REVISION R004807
fit_ids=json.loads(subprocess.check_output(['node','-e',"const s=require('./src/schematic-walls.js'),m=JSON.parse(require('fs').readFileSync(0,'utf8'));process.stdout.write(JSON.stringify(s.build(m.parts,{applyFit:false}).components.filter(p=>['rail','wall','floor','shelf'].includes(p.schematicKind)).map(p=>p.id)))"],input=raw,cwd=R))
# TIMESTAMP END 2026-11-02T15:33:07-05:00 | REVISION R004807
# TIMESTAMP START 2026-11-02T15:15:55-05:00 | REVISION R004802
assert len(load['members'])==112 and set(fit['parts'])==set(fit_ids)
# TIMESTAMP END 2026-11-02T15:15:55-05:00 | REVISION R004802
assert sum('-rail-jamb-' in name for name in fit_ids)==12
# TIMESTAMP END 2026-11-02T13:42:10-05:00 | REVISION R004782
# TIMESTAMP START 2026-11-02T10:08:03-05:00 | REVISION R004759
assert cav['available'] is True and cav['summary']['complete'] is True
# TIMESTAMP START 2026-11-02T15:15:55-05:00 | REVISION R004802
assert set(cav['parts'])==set(S) and len(cav['parts'])==112
# TIMESTAMP END 2026-11-02T15:15:55-05:00 | REVISION R004802
# TIMESTAMP START 2026-11-03T17:00:04-05:00 | REVISION R005063
assert proposal['baseline_model_sha256']==old['source_model_sha256']
assert cav['sources']['src/step-lap-proposed-model.json']==sha
for relative,digest in cav['sources'].items():assert hashlib.sha256((R/relative).read_bytes()).hexdigest()==digest
# TIMESTAMP END 2026-11-03T17:00:04-05:00 | REVISION R005063
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
 # TIMESTAMP START 2026-11-02T15:33:07-05:00 | REVISION R004807
 if '-rail' not in name and '-shelf' not in name:continue
 # TIMESTAMP END 2026-11-02T15:33:07-05:00 | REVISION R004807
 s=solid(dict(p,id=name))
 for tid,t in S.items():
  if close_bounds(s,t):assert (s^t).volume()<1e-10,(name,tid)
# TIMESTAMP START 2026-11-02T10:08:03-05:00 | REVISION R004759
# TIMESTAMP START 2026-11-03T17:00:04-05:00 | REVISION R005063
# Regenerate current quantities in an isolated source copy. Historical joint
# proposal generators must never overwrite the revised live models.
import tempfile,shutil
import sync_joinery_sources as current
with tempfile.TemporaryDirectory() as folder:
 old_root=current.ROOT;current.ROOT=Path(folder);shutil.copytree(R/'src',current.ROOT/'src');(current.ROOT/'docs').mkdir()
 try:
  current.auxiliary()
  for name in ['step-lap-proposed-load-review.json','step-lap-proposed-material-groups.json']:
   assert_equivalent_report(json.loads((R/'src'/name).read_text()),json.loads((current.ROOT/'src'/name).read_text()),name)
 finally:current.ROOT=old_root

# TIMESTAMP END 2026-11-03T17:00:04-05:00 | REVISION R005063
assert (R/'src/step-lap-proposed-model.json').read_bytes()==raw
# TIMESTAMP START 2026-11-02T10:08:03-05:00 | REVISION R004759
# TIMESTAMP START 2026-11-02T13:42:10-05:00 | REVISION R004782
# TIMESTAMP START 2026-11-02T15:15:55-05:00 | REVISION R004802
print('PASS: proposed112 applied self-weight volumes/centroids, source-bound inventory/cavities/complete enclosure components; matching removed-only cavity exports; pressure/contact markers withheld; deterministic auxiliary generation')
# TIMESTAMP END 2026-11-02T15:15:55-05:00 | REVISION R004802
# TIMESTAMP END 2026-11-02T13:42:10-05:00 | REVISION R004782
# TIMESTAMP END 2026-11-02T10:08:03-05:00 | REVISION R004759
