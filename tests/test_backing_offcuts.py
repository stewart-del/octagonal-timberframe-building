# TIMESTAMP START 2026-11-05T08:52:17+00:00 | REVISION R000038
"""Actual baseline R5 wedges retain removed material without cofacial membranes."""
import gzip,json,math,sys,unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from closed_backing_offcuts import closed_stopped_backing_offcuts,occupied_difference,INCH as I,VOLUME_TOLERANCE_M3 as TOL
from audit_cavity_fit import inspect_mesh
from audit_revised_joinery import native_solid
ROOT=Path(__file__).resolve().parents[1]
class BackingOffcuts(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  frozen=json.loads(gzip.decompress((ROOT/'scripts/fixtures/roof-structure-inputs.json.gz').read_bytes()))
  model=json.loads(frozen['files']['model-data.json']['content']);p=next(p for p in model['parts'] if p['id']=='R5');cls.shape=native_solid(p);k=5;cls.r=np.array([math.cos(k*math.pi/4),0.,-math.sin(k*math.pi/4)]);w=np.asarray(p['stock_frame']['width']);cls.c=next(q['constant'] for q in p['proposed_stock_planes_inches'] if q['normal'][2]>.9)*I;cls.normals=[np.array([0.,1.,0.])+cls.r/3+w*math.tan(math.pi/8)/3,np.array([0.,1.,0.])+cls.r/3-w*math.tan(math.pi/8)/3]
  backed=cls.shape
  for n in cls.normals:backed=backed.trim_by_plane((-n/np.linalg.norm(n)).tolist(),-cls.c/np.linalg.norm(n))
  cls.removed=(cls.shape-backed).trim_by_plane(cls.r.tolist(),45*I)
 def test_closed_actual_source_wedges(self):
  r=closed_stopped_backing_offcuts(self.shape,self.normals,self.c,self.r,45*I,inspect_mesh,native_solid,self.removed)
  self.assertEqual(len(r['pieces']),2);self.assertEqual(r['receipt']['status'],'PASS')
  actual=native_solid(r['combined_closed_record']);self.assertLessEqual(occupied_difference(actual,self.removed),TOL)
  for p in r['pieces']:self.assertEqual(inspect_mesh(np.asarray(p['vertices']),np.asarray(p['triangles']),require_single=True)['status'],'PASS')
 def test_missing_removed_material_rejected(self):
  wrong=self.removed.translate([0,.01,0])
  with self.assertRaisesRegex(AssertionError,'Removed material differs'):
   closed_stopped_backing_offcuts(self.shape,self.normals,self.c,self.r,45*I,inspect_mesh,native_solid,wrong)
if __name__=='__main__':unittest.main()
# TIMESTAMP END 2026-11-05T08:52:17+00:00 | REVISION R000038
