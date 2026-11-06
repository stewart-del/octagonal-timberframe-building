# TIMESTAMP START 2026-11-06T03:14:49+00:00 | REVISION R000083
"""An explicitly unfinished export never becomes a completed route certificate."""
from pathlib import Path
import hashlib,json,sys,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from review_publication import load_architecture,unavailable_plans,notice_html,NOTICE

class ReviewPublication(unittest.TestCase):
 def fixture(self,root,status='STAGING_INCOMPLETE_DO_NOT_PUBLISH'):
  for name in ['scripts/prepare_architecture.py','scripts/fixtures/architectural-inputs.json.gz','src/floor-foundation-solids.json']:
   p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(name.encode())
  data={'schema':'octagon-articulated-architecture-1','status':status,'source_generator_sha256':hashlib.sha256((root/'scripts/prepare_architecture.py').read_bytes()).hexdigest(),'source_fixture_sha256':hashlib.sha256((root/'scripts/fixtures/architectural-inputs.json.gz').read_bytes()).hexdigest(),'sourceFloorSha256':hashlib.sha256((root/'src/floor-foundation-solids.json').read_bytes()).hexdigest(),'parts':[{'id':'ACTUAL-BOARD','vertices':[[0,0,0]],'triangles':[]}],'prototypes':{}}
  for name in ['architectural-solids.json','review-architectural-solids.json']:(root/'src'/name).write_text(json.dumps(data))
  return data
 def test_progress_mode_retains_original_incomplete_status_and_final_gate(self):
  with tempfile.TemporaryDirectory()as directory:
   root=Path(directory);source=self.fixture(root);data=load_architecture(root,True);self.assertEqual(data['status'],source['status']);self.assertFalse(data['publication']['constructionComplete']);self.assertFalse(data['publication']['orderedMotionQualified']);self.assertEqual(data['parts'],source['parts']);self.assertIn('Work in progress',notice_html(True));self.assertEqual(notice_html(False),'')
   with self.assertRaisesRegex(AssertionError,'not ready for final'):load_architecture(root)
 def test_changed_export_source_cannot_publish_as_current(self):
  with tempfile.TemporaryDirectory()as directory:
   root=Path(directory);self.fixture(root);(root/'scripts/prepare_architecture.py').write_text('changed source')
   with self.assertRaisesRegex(AssertionError,'generator changed'):load_architecture(root,True)
 def test_unavailable_current_routes_never_reuse_legacy_pass(self):
  plans=unavailable_plans()
  for plan in plans['variants'].values():self.assertEqual(plan['status'],'PARTIAL');self.assertEqual(plan['verification']['status'],'UNAVAILABLE');self.assertEqual(plan['stages'],[]);self.assertEqual(plan['moved_ids'],[])
 def test_normal_release_still_requires_pass(self):
  with tempfile.TemporaryDirectory()as directory:
   root=Path(directory);self.fixture(root,'PASS');self.assertEqual(load_architecture(root)['status'],'PASS')
   with self.assertRaisesRegex(AssertionError,'explicit incomplete'):load_architecture(root,True)

if __name__=='__main__':unittest.main()
# TIMESTAMP END 2026-11-06T03:14:49+00:00 | REVISION R000083
