# TIMESTAMP START 2026-11-02T10:08:03-05:00 | REVISION R004759
"""Source-bind self-weight, inventory and corrected cavities to proposed meshes.
No baseline contact demand/pressure assertions are carried into this model.
"""
# TIMESTAMP END 2026-11-02T10:08:03-05:00 | REVISION R004759
from pathlib import Path
import hashlib,json
from step_lap import solid,volume_centroid
# TIMESTAMP START 2026-11-02T10:08:03-05:00 | REVISION R004759
from export_step_lap_cavities import generate as generate_cavities
# TIMESTAMP END 2026-11-02T10:08:03-05:00 | REVISION R004759
R=Path(__file__).resolve().parents[1]
def write(name,data):
 (R/'src'/name).write_text(json.dumps(data,separators=(',',':'))+'\n')
def generate():
 raw=(R/'src/step-lap-proposed-model.json').read_bytes();sha=hashlib.sha256(raw).hexdigest();model=json.loads(raw)
 proposal=json.loads((R/'src/step-lap-proposal.json').read_text());parts={p['id']:p for p in model['parts'] if p['is_timber']};solids={k:solid(p) for k,p in parts.items()}
 load=json.loads((R/'src/load-review-data.json').read_text());load.update(source_model_sha256=sha,members=[dict(id=name,**volume_centroid(s)) for name,s in solids.items()],issues=[],baseline_pressure_disabled=True,model_revision='proposed-step-lap',status='Applied self-weight only; selected geometry centroids/volumes. Joint reactions, capacity and contact-derived warning markers unavailable; no baseline 64/12 in2 shortcut.')
 write('step-lap-proposed-load-review.json',load)
 materials=json.loads((R/'src/material-groups.json').read_text());materials.update(source_sha256=sha,model_revision='proposed-step-lap',scope='Selected proposed model generation families; not a fabrication schedule. Changed cuts are not fabrication approved.')
 for group in materials['groups']:
  if any(name in model['proposed_review']['changed_member_ids'] for name in group['member_ids']):group['status']='Proposed step-lap geometry family; no fabrication interchangeability claim'
 write('step-lap-proposed-material-groups.json',materials)
 # TIMESTAMP START 2026-11-02T10:08:03-05:00 | REVISION R004759
 # Preserve the corrected baseline recesses, then apply the actual 24 stock
 # transfers to both mating cavity records. Full fit verification is separate.
 generate_cavities()
 print('Bound proposed loads/materials and matching cavity exports to',sha)
 # TIMESTAMP END 2026-11-02T10:08:03-05:00 | REVISION R004759
if __name__=='__main__':generate()
