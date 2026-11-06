# TIMESTAMP START 2026-11-05T15:44:02+00:00 | REVISION R000051
"""Current source membership and actual native mass properties remain consistent."""
from pathlib import Path
import hashlib,json,sys,unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from prepare_primary_auxiliary import VARIANTS,derive
from audit_revised_joinery import native_solid
ROOT=Path(__file__).resolve().parents[1]
class PrimaryAuxiliary(unittest.TestCase):
 def test_every_current_member_is_counted_once_and_hashes_match(self):
  report=json.loads((ROOT/'docs/primary-model-audit.json').read_text());self.assertEqual(report['status'],'PASS')
  for variant,(model_name,materials_name,load_name) in VARIANTS.items():
   raw=(ROOT/'src'/model_name).read_bytes();model=json.loads(raw);materials=json.loads((ROOT/'src'/materials_name).read_text());loads=json.loads((ROOT/'src'/load_name).read_text());digest=hashlib.sha256(raw).hexdigest()
   self.assertEqual(materials['source_sha256'],digest);self.assertEqual(loads['source_model_sha256'],digest);self.assertEqual(report['variants'][variant]['source_model_sha256'],digest)
   ids=[pid for group in materials['groups'] for pid in group['member_ids']];self.assertEqual(len(ids),len(set(ids)));self.assertEqual(set(ids),{p['id'] for p in model['parts']})
   timbers={p['id'] for p in model['parts'] if p.get('is_timber')};self.assertEqual(len(timbers),129);self.assertEqual({p['id'] for p in loads['members']},timbers)
   self.assertTrue(loads['baseline_pressure_disabled']);self.assertEqual(loads['issues'],[])
   byid={p['id']:p for p in model['parts']}
   for member in loads['members']:
    solid=native_solid(byid[member['id']]);self.assertGreater(member['volume_m3'],0);self.assertLess(abs(solid.volume()-member['volume_m3']),1e-6*.0254**3)
    self.assertTrue(np.isfinite(member['centroid_m']).all())
 def test_new_real_member_is_never_dropped_by_legacy_group_template(self):
  model=json.loads((ROOT/'src/model-data.json').read_text());part=dict(model['parts'][0]);part['id']='ADVERSARIAL-NEW-MEMBER';model['parts'].append(part)
  materials,loads=derive(model,'isolated-regression');self.assertEqual(materials['timber_count'],130);self.assertIn(part['id'],{p['id'] for p in loads['members']});self.assertEqual(sum(part['id'] in g['member_ids'] for g in materials['groups']),1)
# TIMESTAMP START 2026-11-05T16:50:20+00:00 | REVISION R000055
class PrimaryBuildContract(unittest.TestCase):
 def test_current_build_contract_and_corrupt_inventory(self):
  from validate_primary_auxiliary import validate,validate_membership
  import copy
  variants=validate(ROOT);self.assertEqual(set(variants),{'baseline','proposed','top-entry'})
  data=variants['top-entry'];bad=copy.deepcopy(data['loads']);bad['members']=bad['members'][:-1]
  with self.assertRaisesRegex(AssertionError,'counted exactly once'):validate_membership(data['model'],data['materials'],bad)
  bad=copy.deepcopy(data['materials']);bad['groups'][0]['member_ids'].append(bad['groups'][0]['member_ids'][0])
  with self.assertRaisesRegex(AssertionError,'membership'):validate_membership(data['model'],bad,data['loads'])
# TIMESTAMP END 2026-11-05T16:50:20+00:00 | REVISION R000055
if __name__=='__main__':unittest.main()
# TIMESTAMP END 2026-11-05T15:44:02+00:00 | REVISION R000051
