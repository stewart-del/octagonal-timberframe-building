"""Selected-model self-weight and inventory; no stale pressure/contact overlays."""
from pathlib import Path
import hashlib,json
from step_lap import solid,volume_centroid
R=Path(__file__).resolve().parents[1]
def write(name,data):(R/'src'/name).write_text(json.dumps(data,separators=(',',':'))+'\n')
def generate():
 raw=(R/'src/top-entry-proposed-model.json').read_bytes();sha=hashlib.sha256(raw).hexdigest();model=json.loads(raw)
 load=json.loads((R/'src/step-lap-proposed-load-review.json').read_text());load.update(source_model_sha256=sha,model_revision='top-entry-proposed',members=[dict(id=p['id'],**volume_centroid(solid(p))) for p in model['parts'] if p['is_timber']],issues=[],baseline_pressure_disabled=True,status='Applied self-weight from selected top-entry geometry. Reactions/capacity unsolved; old contact markers and fixed-area pressure shortcuts not used.')
 write('top-entry-proposed-load-review.json',load)
 materials=json.loads((R/'src/step-lap-proposed-material-groups.json').read_text());materials.update(source_sha256=sha,model_revision='top-entry-proposed',scope='Selected top-entry model generation families; nominal references only, not a fabrication schedule. Longer J stock and uncut hip blanks required by trial geometry.')
 for group in materials['groups']:
  if any(k.startswith(('J','R')) for k in group['member_ids']):group['status']='Proposed top-entry heads; inspect selected raw-stock requirements, no fabrication interchangeability claim'
 write('top-entry-proposed-material-groups.json',materials)
 cavity={'schema_version':'top-entry-cavities-1','source_model_sha256':sha,'parts':{},'available':False,'summary':{'complete':False,'part_count':0},'status':'Removed-stock and unfilled-gap overlays are awaiting independent repair/validation for this selected model. No legacy cutter mask substituted. Actual timber cuts remain visible.','repair_status':'Required follow-on work, not completed or permanently unavailable. Verify evidence-backed original stock minus final solid, owner disjointness, stock reconstruction and separate assembly-unfilled classification.'}
 write('top-entry-proposed-cavities.json',cavity)
 print('Top-entry auxiliary source',sha,'timber volume',sum(p['volume_m3'] for p in load['members']))
if __name__=='__main__':generate()
