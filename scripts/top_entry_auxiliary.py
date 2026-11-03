"""Selected-model self-weight and inventory; no stale pressure/contact overlays."""
from pathlib import Path
import hashlib,json
from step_lap import solid,volume_centroid
R=Path(__file__).resolve().parents[1]
def write(name,data):(R/'src'/name).write_text(json.dumps(data,separators=(',',':'))+'\n')
def generate():
 raw=(R/'src/top-entry-proposed-model.json').read_bytes();sha=hashlib.sha256(raw).hexdigest();model=json.loads(raw)
 load=json.loads((R/'src/step-lap-proposed-load-review.json').read_text());load.update(source_model_sha256=sha,model_revision='top-entry-proposed',members=[dict(id=p['id'],**volume_centroid(solid(p))) for p in model['parts'] if p['is_timber']],issues=[],baseline_pressure_disabled=True,status='Applied self-weight from selected top-entry geometry. Reactions/capacity unsolved; old contact markers and fixed-area pressure shortcuts not used.')
 # TIMESTAMP START 2026-11-02T17:13:18-05:00 | REVISION R004819
 pegs=[p for p in model['parts'] if p.get('group')=='joinery_pegs']
 load['fasteners']=[dict(id=p['id'],**volume_centroid(solid(p))) for p in pegs]
 load['fastener_scope']='Separate physical peg quantities; excluded from the displayed primary-structural-timber subtotal, as are porch, enclosure, roof and floor loads.'
 # TIMESTAMP END 2026-11-02T17:13:18-05:00 | REVISION R004819
 write('top-entry-proposed-load-review.json',load)
 materials=json.loads((R/'src/step-lap-proposed-material-groups.json').read_text());materials.update(source_sha256=sha,model_revision='top-entry-proposed',scope='Selected top-entry model generation families; nominal references only, not a fabrication schedule. Longer J stock and uncut hip blanks required by trial geometry.')
 for group in materials['groups']:
  if any(k.startswith(('J','R')) for k in group['member_ids']):group['status']='Proposed top-entry heads; inspect selected raw-stock requirements, no fabrication interchangeability claim'
 # TIMESTAMP START 2026-11-02T17:13:18-05:00 | REVISION R004819
 peg_ids={p['id'] for p in pegs}
 materials['groups']=[g for g in materials['groups'] if not set(g['member_ids'])&peg_ids]
 if pegs:
  number=max((g['number'] for g in materials['groups']),default=0)+1
  materials['groups'].append({'id':f'M{number:02d}','number':number,'quantity':len(pegs),'member_ids':[p['id'] for p in pegs],
   'representative_id':pegs[0]['id'],'family':'joinery_pegs','label':'Removable wooden joint pegs',
   'status':'Physical joint fasteners; inspect individual lengths and bores, not a fabrication interchangeability group.','method':'explicit physical fastener inventory'})
 materials.update(item_count=len(model['parts']),group_count=len(materials['groups']),timber_count=sum(p['is_timber'] for p in model['parts']))
 # TIMESTAMP END 2026-11-02T17:13:18-05:00 | REVISION R004819
 write('top-entry-proposed-material-groups.json',materials)
 # TIMESTAMP START 2026-11-02T17:13:18-05:00 | REVISION R004819
 # Cavity generation and its independent readback audit are owned by
 # export_top_entry_cavities.py. Never overwrite them with an empty placeholder.
 # A changed source remains stale until that explicit export passes; build.py
 # rejects stale geometry or audits instead of borrowing another model's mask.
 # TIMESTAMP END 2026-11-02T17:13:18-05:00 | REVISION R004819
 print('Top-entry auxiliary source',sha,'timber volume',sum(p['volume_m3'] for p in load['members']))
if __name__=='__main__':generate()
