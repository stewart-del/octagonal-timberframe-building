# TIMESTAMP START 2026-11-05T23:39:11+00:00 | REVISION R000073
"""Strict source ownership and untrusted-candidate separation for stock waste."""
from pathlib import Path
import copy,json,sys,tempfile,unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import closure_stock_waste as W
from closure_core_parts import inputs as core_inputs
class StockWaste(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.source=W.inputs();core=core_inputs()['wood'];cls.parts={**core['replace_new_envelope_parts'],**core['add_parts']};cls.rows={**core['stock'],**core['sourceStockRecordOverrides']}
 def test_only_waste_fields_and_distinct_positive_chunks(self):
  self.assertEqual(len(self.source['asset']['corrections']),188);self.assertEqual(len(self.source['asset']['checkedUnchangedRows']),102);sid='STOCK-W-FUR-01';before=copy.deepcopy(self.rows[sid]);geometry=copy.deepcopy(self.parts);first=W.candidate(sid,self.rows[sid],self.parts);self.assertTrue(first['originalGeometryBindingsMatched']);self.assertTrue(first['requiresFreshCurrentStockReadback']);self.assertFalse(first['originalProofInherited']);self.assertEqual(len(first['fields']['declared_exterior_offcut_pieces']),3);self.assertTrue(set(first['fields'])<=W.ALLOWED);self.assertEqual(before,self.rows[sid]);self.assertEqual(geometry,self.parts)
  first['fields']['declared_exterior_offcut_pieces'][0]['vertices'][0][0]+=.1;second=W.candidate(sid,self.rows[sid],self.parts);self.assertNotEqual(first['fields'],second['fields'],'Caller mutation must not corrupt immutable loaded candidates')
 def test_changed_blanks_or_children_never_inherit_the_original_proof(self):
  sid='STOCK-W-FUR-01';row=copy.deepcopy(self.rows[sid]);row['blank']['vertices'][0][0]+=.001
  with self.assertRaisesRegex(AssertionError,'original waste proof does not apply'):W.candidate(sid,row,self.parts)
  result=W.candidate(sid,row,self.parts,require_exact=False);self.assertFalse(result['originalGeometryBindingsMatched']);self.assertFalse(result['originalProofInherited']);self.assertTrue(result['requiresFreshCurrentStockReadback'])
  child=row['children'][0];parts={**self.parts,child:copy.deepcopy(self.parts[child])};parts[child]['vertices'][0][0]+=.001
  with self.assertRaisesRegex(AssertionError,'original waste proof does not apply'):W.candidate(sid,self.rows[sid],parts)
 def test_corrupt_transport_rejected_without_publishing_a_candidate(self):
  descriptor=json.loads(W.FIXTURE.read_text());raw=(W.FIXTURE.parent/descriptor['archive']).read_bytes();bad=raw[:-1]+bytes([raw[-1]^1])
  with tempfile.TemporaryDirectory() as directory:
   path=Path(directory)/W.FIXTURE.name;path.write_text(json.dumps(descriptor));(path.parent/descriptor['archive']).write_bytes(bad);W.inputs.cache_clear()
   with patch.object(W,'FIXTURE',path):
    with self.assertRaises(AssertionError):W.inputs()
  W.inputs.cache_clear()
if __name__=='__main__':unittest.main()
# TIMESTAMP END 2026-11-05T23:39:11+00:00 | REVISION R000073
