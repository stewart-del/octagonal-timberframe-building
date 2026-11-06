# TIMESTAMP START 2026-11-06T01:00:34+00:00 | REVISION R000077
"""Missing directions are declared from geometry without changing hardware."""
from pathlib import Path
import copy,sys,unittest
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from drain_grate_parts import inputs,screw_motion_metadata
from physical_fastener_axes import audit,prototype_withdrawal_axis
class DrainAxes(unittest.TestCase):
 def test_all_sixteen_actual_screws_keep_product_pose_and_recipients(self):
  source=inputs()['patch'];parts=[p for p in source['instances']if p['mesh_instance']['prototype'].startswith('DRAIN-THD')];before=copy.deepcopy(parts);result=[screw_motion_metadata(p,source['prototypes'])for p in parts];self.assertEqual(len(result),16);self.assertEqual(parts,before)
  for old,new in zip(parts,result):
   for key in old:self.assertEqual(old[key],new[key])
   self.assertGreater(new['withdrawal_distance_m'],.0762);new['fastenerKind']='screw';self.assertFalse(new.get('intentionalFastenerPenetration',False))
  self.assertEqual(audit(result,source['prototypes'])['status'],'PASS')
 def test_stale_direction_and_nonrigid_pose_are_rejected(self):
  source=inputs()['patch'];p=copy.deepcopy(next(p for p in source['instances']if p['mesh_instance']['prototype']=='DRAIN-THD37300CS6SS'));p['withdrawal_direction']=np.asarray(p['mesh_instance']['transform'])[:,2].tolist()
  with self.assertRaisesRegex(AssertionError,'physical shaft'):screw_motion_metadata(p,source['prototypes'])
  del p['withdrawal_direction'];p['mesh_instance']['transform'][0][0]*=1.2
  with self.assertRaisesRegex(AssertionError,'rigid'):screw_motion_metadata(p,source['prototypes'])
 def test_floor_nominal_nail_uses_its_own_exact_source_boundary(self):
  from floor_closure_parts import inputs as floor_inputs
  p=floor_inputs()['hardwareInstances']['prototypes']['CLOSURE-HW-T8PCS10-00'];axis,evidence=prototype_withdrawal_axis(p);self.assertEqual(axis.tolist(),[0,0,-1]);self.assertIn('source-bound',evidence);p=copy.deepcopy(p);p['vertices'][0][0]+=1e-12
  with self.assertRaisesRegex(AssertionError,'ambiguous'):prototype_withdrawal_axis(p)
if __name__=='__main__':unittest.main()
# TIMESTAMP END 2026-11-06T01:00:34+00:00 | REVISION R000077
