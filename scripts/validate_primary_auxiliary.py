# TIMESTAMP START 2026-11-05T16:50:20+00:00 | REVISION R000055
"""Build contract for current primary geometry, separate from archived studies."""
from pathlib import Path
import hashlib,json,math
from prepare_primary_auxiliary import VARIANTS

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def validate_membership(model,materials,loads):
 parts=model['parts'];ids=[p['id'] for p in parts];assert len(ids)==len(set(ids)),'Duplicate current primary IDs'
 grouped=[pid for group in materials['groups'] for pid in group['member_ids']]
 assert len(grouped)==len(set(grouped)) and set(grouped)==set(ids),'Primary material membership must cover each current item exactly once'
 assert all(group['quantity']==len(group['member_ids']) for group in materials['groups']),'Material family quantities disagree'
 timber={p['id'] for p in parts if p.get('is_timber')};fasteners={p['id'] for p in parts if p.get('is_fastener') and not p.get('is_timber')}
 for key,expected in [('members',timber),('fasteners',fasteners)]:
  values=loads[key];assert len(values)==len({p['id'] for p in values}) and {p['id'] for p in values}==expected,'Current primary '+key+' must be counted exactly once'
  assert all(math.isfinite(p['volume_m3']) and p['volume_m3']>0 and len(p['centroid_m'])==3 and all(math.isfinite(v) for v in p['centroid_m']) for p in values),'Invalid native primary mass properties'
 assert materials['timber_count']==len(timber) and materials['item_count']==len(ids),'Primary inventory totals disagree'
 assert loads['baseline_pressure_disabled'] is True and loads['issues']==[],'Unsolved primary reactions must not acquire baseline pressure shortcuts'
 return {'timbers':len(timber),'fasteners':len(fasteners),'items':len(ids)}
def validate(root):
 root=Path(root);report=json.loads((root/'docs/primary-model-audit.json').read_text());assert report['status']=='PASS'
 assert report['generator_sha256']==sha(root/'scripts/prepare_primary_auxiliary.py'),'Current primary audit generator changed'
 result={}
 for variant,(model_name,materials_name,loads_name) in VARIANTS.items():
  model_path=root/'src'/model_name;materials_path=root/'src'/materials_name;loads_path=root/'src'/loads_name
  model=json.loads(model_path.read_text());materials=json.loads(materials_path.read_text());loads=json.loads(loads_path.read_text());entry=report['variants'][variant];digest=sha(model_path)
  assert entry['source_model_sha256']==digest==materials['source_sha256']==loads['source_model_sha256'],'Current primary source binding is stale: '+variant
  assert entry['materials_sha256']==sha(materials_path) and entry['loads_sha256']==sha(loads_path),'Current primary native auxiliary proof is stale: '+variant
  counts=validate_membership(model,materials,loads)
  assert counts['timbers']==entry['timber_count']==129 and counts['items']==entry['primary_item_count'] and counts['fasteners']==entry['primary_fastener_count'],'Current primary count audit disagrees: '+variant
  assert abs(sum(p['volume_m3'] for p in loads['members'])-entry['total_primary_timber_volume_m3'])<=1e-6*.0254**3,'Current timber native volume total disagrees'
  result[variant]={'model':model,'materials':materials,'loads':loads,'counts':counts}
 for variant in ['proposed','top-entry']:
  comparison=report['comparisons'][variant];assert comparison['overlap_tolerance_m3']==1e-6*.0254**3
  assert comparison['native_changed_timber_ids']==[p['id'] for p in comparison['changes']]
  assert not comparison['added_timber_ids'] and not comparison['removed_timber_ids'],'Variants must preserve the actual primary timber inventory'
 return result
# TIMESTAMP END 2026-11-05T16:50:20+00:00 | REVISION R000055
