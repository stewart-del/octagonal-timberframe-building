from pathlib import Path
import hashlib,json,sys,numpy as np
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from step_lap import solid,volume_centroid,close_bounds
from top_entry_auxiliary import generate
# TIMESTAMP START 2026-11-02T13:16:28-05:00 | REVISION R004781
from audit_cavity_fit import assert_equivalent_report
# TIMESTAMP END 2026-11-02T13:16:28-05:00 | REVISION R004781
raw=(R/'src/top-entry-proposed-model.json').read_bytes();sha=hashlib.sha256(raw).hexdigest();model=json.loads(raw);parts={p['id']:p for p in model['parts']};S={k:solid(p) for k,p in parts.items() if p['is_timber']}
load=json.loads((R/'src/top-entry-proposed-load-review.json').read_text());mat=json.loads((R/'src/top-entry-proposed-material-groups.json').read_text());cav=json.loads((R/'src/top-entry-proposed-cavities.json').read_text());fit=json.loads((R/'src/top-entry-proposed-enclosure-fit.json').read_text())
assert load['source_model_sha256']==cav['source_model_sha256']==fit['source_model_sha256']==mat['source_sha256']==sha
# TIMESTAMP START 2026-11-02T13:42:10-05:00 | REVISION R004782
import subprocess
# TIMESTAMP START 2026-11-02T15:33:07-05:00 | REVISION R004807
fit_ids=json.loads(subprocess.check_output(['node','-e',"const s=require('./src/schematic-walls.js'),m=JSON.parse(require('fs').readFileSync(0,'utf8'));process.stdout.write(JSON.stringify(s.build(m.parts,{applyFit:false}).components.filter(p=>['rail','wall','floor','shelf'].includes(p.schematicKind)).map(p=>p.id)))"],input=raw,cwd=R))
# TIMESTAMP END 2026-11-02T15:33:07-05:00 | REVISION R004807
# TIMESTAMP START 2026-11-02T15:15:55-05:00 | REVISION R004802
assert len(load['members'])==112 and set(fit['parts'])==set(fit_ids) and load['issues']==[] and load['baseline_pressure_disabled']
# TIMESTAMP END 2026-11-02T15:15:55-05:00 | REVISION R004802
assert sum('-rail-jamb-' in name for name in fit_ids)==12
# TIMESTAMP END 2026-11-02T13:42:10-05:00 | REVISION R004782
assert fit['source_module_sha256']==hashlib.sha256((R/'src/schematic-walls.js').read_bytes()).hexdigest()
# TIMESTAMP START 2026-11-02T17:13:18-05:00 | REVISION R004819
assert cav['available'] and set(cav['parts'])==set(S)
assert {p['id'] for p in load['fasteners']}=={p['id'] for p in model['parts'] if p.get('group')=='joinery_pegs'}
# TIMESTAMP END 2026-11-02T17:13:18-05:00 | REVISION R004819
for p in load['members']:
 q=volume_centroid(S[p['id']]);assert abs(q['volume_m3']-p['volume_m3'])<1e-12;assert np.linalg.norm(np.array(q['centroid_m'])-p['centroid_m'])<1e-10
for name,p in fit['parts'].items():
 # TIMESTAMP START 2026-11-02T15:33:07-05:00 | REVISION R004807
 if '-rail' not in name and '-shelf' not in name:continue
 # TIMESTAMP END 2026-11-02T15:33:07-05:00 | REVISION R004807
 s=solid(dict(p,id=name))
 for tid,t in S.items():
  if close_bounds(s,t):assert (s^t).volume()<1e-10,(name,tid)
# TIMESTAMP START 2026-11-02T13:16:28-05:00 | REVISION R004781
# Require strict structure and bounded numeric roundoff across platforms, exact
# repeated generation locally, and restoration of source bytes even on failure.
# TIMESTAMP START 2026-11-02T17:13:18-05:00 | REVISION R004819
files=[R/'src'/('top-entry-proposed-'+x+'.json') for x in ['load-review','material-groups']]
# TIMESTAMP END 2026-11-02T17:13:18-05:00 | REVISION R004819
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
# TIMESTAMP END 2026-11-02T13:16:28-05:00 | REVISION R004781
assert (R/'src/top-entry-proposed-model.json').read_bytes()==raw
# TIMESTAMP START 2026-11-02T13:42:10-05:00 | REVISION R004782
# TIMESTAMP START 2026-11-02T15:15:55-05:00 | REVISION R004802
# TIMESTAMP START 2026-11-02T17:13:18-05:00 | REVISION R004819
print('PASS: top-entry112 primary weights, separate peg quantities, physical inventory, enclosure fits and actual source-bound cavity records')
# TIMESTAMP END 2026-11-02T17:13:18-05:00 | REVISION R004819
# TIMESTAMP END 2026-11-02T15:15:55-05:00 | REVISION R004802
# TIMESTAMP END 2026-11-02T13:42:10-05:00 | REVISION R004782
