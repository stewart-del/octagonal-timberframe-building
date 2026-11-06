# TIMESTAMP START 2026-11-06T01:19:41+00:00 | REVISION R000080
"""Loading old canonical detail must preserve newer physical overlays."""
from pathlib import Path
import copy,sys,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from build_runtime import split_foundation_detail
class RuntimeDetailOwnership(unittest.TestCase):
 def test_current_overlay_is_not_a_canonical_detail_download(self):
  old={'vertices':[[1,0,0]],'triangles':[]};outer={'vertices':[[2,0,0]],'triangles':[]};fresh={'vertices':[[3,0,0]],'triangles':[]};parts=[{'id':pid,**old,'display_mesh':outer}for pid in ['OWNED','LAZY']];foundation={'parts':parts,'architecture':{'parts':[{'id':'OWNED','replaceExisting':True,**fresh}]}};before=copy.deepcopy(foundation);initial,detail=split_foundation_detail(foundation);self.assertEqual(foundation,before);self.assertEqual(set(detail),{'LAZY'});self.assertNotIn('detail_ref',initial['parts'][0]);self.assertEqual(initial['parts'][1]['detail_ref'],'LAZY');self.assertEqual(initial['architecture']['parts'][0]['vertices'],fresh['vertices']);self.assertEqual(detail['LAZY']['vertices'],old['vertices'])
 def test_legacy_detail_still_works_without_architectural_replacements(self):
  foundation={'parts':[{'id':'A','vertices':[[1,0,0]],'triangles':[],'display_mesh':{'vertices':[[2,0,0]],'triangles':[]}}]};initial,detail=split_foundation_detail(foundation);self.assertEqual(initial['parts'][0]['vertices'],[[2,0,0]]);self.assertEqual(detail['A']['vertices'],[[1,0,0]])
 def test_archived_owners_must_be_resolved(self):
  with self.assertRaisesRegex(ValueError,'Resolve architectural owners'):split_foundation_detail({'parts':[],'architecture':{'partArchives':[{'path':'owners.json.gz'}]}})
if __name__=='__main__':unittest.main()
# TIMESTAMP END 2026-11-06T01:19:41+00:00 | REVISION R000080
