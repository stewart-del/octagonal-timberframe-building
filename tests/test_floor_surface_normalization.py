# TIMESTAMP START 2026-11-05T08:36:47+00:00 | REVISION R000035
"""Regression cases exercise real failed bores, strict boundaries and live inputs."""
import copy,sys,unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from floor_surface_normalization import load_fixture,normalize_one,difference,TOL,I
from audit_revised_joinery import native_solid
from audit_cavity_fit import inspect_mesh

class FloorSurfaceNormalization(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.parts={p['id']:p for p in load_fixture()['parts']}
 def test_real_failure_families(self):
  for pid in ['FLOOR-RIM-1','FLOOR-BLOCKING-08-07','POST-BEARING-STAND-2-SIDE1','FLOOR-EDGE-LEDGER-E-1-N+1']:
   with self.subTest(id=pid):
    original=self.parts[pid]
    before=inspect_mesh(np.asarray(original['vertices']),np.asarray(original['triangles']),require_single=True)
    self.assertEqual(before['status'],'FAIL')
    record,proof=normalize_one(original)
    self.assertEqual(proof['status'],'PASS')
    self.assertEqual(inspect_mesh(np.asarray(record['vertices']),np.asarray(record['triangles']),require_single=True)['status'],'PASS')
    self.assertLessEqual(difference(native_solid(original),native_solid(record)),TOL)
    self.assertLessEqual(proof['local_symmetric_difference_m3'],TOL)
 def test_current_geometry_is_never_reset_to_fixture(self):
  original=self.parts['FLOOR-BLOCKING-08-07'];moved=copy.deepcopy(original);offset=np.array([.017,.023,-.019])
  moved['vertices']=(np.asarray(moved['vertices'])+offset).tolist();moved['center']=(np.asarray(moved['center'])+offset).tolist()
  record,proof=normalize_one(moved)
  self.assertEqual(proof['status'],'PASS')
  self.assertLessEqual(difference(native_solid(moved),native_solid(record)),TOL)
  self.assertGreater(difference(native_solid(original),native_solid(record)),1000*TOL)

if __name__=='__main__':unittest.main()
# TIMESTAMP END 2026-11-05T08:36:47+00:00 | REVISION R000035
