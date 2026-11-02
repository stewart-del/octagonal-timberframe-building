"""Source-bind self-weight, inventory and explicit cavity-display hold to proposed meshes.
No baseline contact demand/pressure assertions are carried into this model.
"""
from pathlib import Path
import hashlib,json
from step_lap import solid,volume_centroid
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
 # Independent non-CSG winding tests found inherited masks inside owner wood.
 # Direct baseline triangle volumes match metadata; raw volume disagreement
 # was a re-import artifact, separate from the confirmed overlap.
 cavity={'schema_version':'proposed-step-lap-cavities-1','source_model_sha256':sha,'parts':{},'available':False,'summary':{'complete':False,'part_count':0},'status':'Recess overlay unavailable for proposed model while independent mask validation is unresolved. No baseline overlay substituted. Actual timber geometry and applied self-weight are checked separately.','baseline_model_sha256':proposal['baseline_model_sha256'],'validation_hold':{'scope':'Cavity visualization only, not a failure of actual proposed timber meshes.','reason':'Independent winding-number sampling confirms inherited P0/C0 removed-mask points inside owner wood (13 of 7,533 and 111 of 2,896 sampled inside-mask points). Raw triangle-volume integration agrees saved metadata; re-import Boolean instability is a separate issue.','required':'Independently verify changed owner-disjoint recess masks and occupied/unfilled classification before enabling.'}}
 write('step-lap-proposed-cavities.json',cavity)
 print('Bound proposed loads/materials and explicit cavity hold to',sha)
if __name__=='__main__':generate()
