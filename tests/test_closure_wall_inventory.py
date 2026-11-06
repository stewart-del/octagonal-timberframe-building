# TIMESTAMP START 2026-11-05T23:58:27+00:00 | REVISION R000074
"""Only the two physically obsolete source anchors may disappear."""
from pathlib import Path
import copy,sys,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from closure_core_parts import wall_hardware_inventory,inputs
from prepare_architecture import load_inputs
class WallInventory(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.old=load_inputs()[0]['wall_hardware'];cls.data=inputs()
 def test_actual_7436_source_to_7434_retained_inventory(self):
  old=copy.deepcopy(self.old);result=wall_hardware_inventory(old,self.data);self.assertEqual((result['originalCount'],result['retainedCount']),(7436,7434));self.assertEqual(result['retiredIds'],['FAST-ENV-W-STUD-03-0-06','FAST-ENV-W-STUD-14-0-06']);self.assertEqual(old,self.old)
 def test_unrelated_missing_or_invented_id_rejected(self):
  old={**self.old,'instances':self.old['instances'][1:]}
  with self.assertRaises(AssertionError):wall_hardware_inventory(old,self.data)
  old={**self.old,'instances':[*self.old['instances'],{'id':'UNDECLARED-WALL-ANCHOR'}]}
  with self.assertRaises(AssertionError):wall_hardware_inventory(old,self.data)
 def test_failed_retirement_receipt_rejected(self):
  data={**self.data,'retained':{**self.data['retained'],'freshWestHardwareCheck':{**self.data['retained']['freshWestHardwareCheck'],'status':'BLOCKED'}}}
  with self.assertRaises(AssertionError):wall_hardware_inventory(self.old,data)
if __name__=='__main__':unittest.main()
# TIMESTAMP END 2026-11-05T23:58:27+00:00 | REVISION R000074
