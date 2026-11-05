# TIMESTAMP START 2026-11-05T20:08:59+00:00 | REVISION R000063
"""Current input/proof identity rejects changed feet, caches and evidence."""
from pathlib import Path
import copy,json,sys,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from current_cache_bindings import verify,load_cache,assert_applies,package,PREFIX
class CurrentCacheBindings(unittest.TestCase):
 def test_actual_inputs_and_historical_headers_remain_unchanged(self):
  descriptor=verify();self.assertEqual(len(descriptor['repositoryInputs']),41);self.assertFalse(descriptor['wholeBuildingReady'])
  for variant in ['baseline','proposed','top-entry']:
   key='enclosure-'+variant;path={'baseline':'enclosure-fit.json','proposed':'step-lap-proposed-enclosure-fit.json','top-entry':'top-entry-proposed-enclosure-fit.json'}[variant];original=json.loads((ROOT/'src'/path).read_text());bound=load_cache(key,variant,descriptor);self.assertTrue(assert_applies(bound,key,variant,descriptor));self.assertEqual(bound['source_model_sha256'],original['source_model_sha256']);self.assertEqual(bound['parts'],original['parts']);self.assertNotEqual(bound['source_model_sha256'],descriptor['models'][variant])
 def test_raised_post_foot_with_unchanged_plan_centers_is_rejected(self):
  model=json.loads((ROOT/'src/model-data.json').read_text());p=next(p for p in model['parts'] if p['id']=='P2');plan=p['center'][::2];p['vertices']=[[v[0],v[1]+.125*.0254,v[2]] for v in p['vertices']];p['center'][1]+=.125*.0254;self.assertEqual(p['center'][::2],plan);changed=json.dumps(model,separators=(',',':')).encode()
  with self.assertRaisesRegex(AssertionError,'Current cache source input changed'):verify(read_source=lambda name:changed if name=='src/model-data.json' else (ROOT/name).read_bytes())
 def test_cache_and_native_evidence_mutations_are_rejected(self):
  with self.assertRaisesRegex(AssertionError,'Current cache source input changed'):verify(read_source=lambda name:(ROOT/name).read_bytes()+(b'\n' if name=='src/floor-foundation-solids.json' else b''))
  def mutate(files):
   key=PREFIX+'floor-current-compatibility-report.json';files[key]+=b'\n';return files
  with self.assertRaisesRegex(AssertionError,'Current cache native evidence changed'):verify(alter_evidence=mutate)
if __name__=='__main__':unittest.main()
# TIMESTAMP END 2026-11-05T20:08:59+00:00 | REVISION R000063
