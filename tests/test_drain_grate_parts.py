# TIMESTAMP START 2026-11-05T16:48:19+00:00 | REVISION R000054
"""Independently inspect the assembled grate, pan and actual hardware holes."""
from pathlib import Path
import copy,sys,unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from drain_grate_parts import inputs,build,TOL
from physical_data import occupied_part
from audit_revised_joinery import native_solid
from audit_cavity_fit import inspect_mesh
class DrainGrates(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.source=inputs();cls.result=build(cls.source['cast']['parts']);cls.parts=[occupied_part(p,cls.result['prototypes']) for p in cls.result['parts']];cls.solids={p['id']:native_solid(p) for p in cls.parts}
 def test_every_solid_and_assembled_contact_is_strict(self):
  rows=[]
  for p in self.parts:
   audit=inspect_mesh(np.asarray(p['vertices']),np.asarray(p['triangles'],np.uint64),True);self.assertEqual(audit['status'],'PASS',p['id']);v=np.asarray(p['vertices']);rows.append((p['id'],v.min(0),v.max(0)))
  pairs=0
  for k,(a,low,high) in enumerate(rows):
   for b,other_low,other_high in rows[k+1:]:
    if np.min(np.minimum(high,other_high)-np.maximum(low,other_low))<=1e-9:continue
    pairs+=1;self.assertLessEqual(max(0.,float((self.solids[a]^self.solids[b]).volume())),TOL,(a,b))
  self.assertGreater(pairs,100)
 def test_purchased_mass_and_cast_quantity_are_not_proxy_mesh_volume(self):
  bought=[p for p in self.parts if p['id'].startswith('DRAIN-NDS253CI-')];self.assertEqual(len(bought),4);self.assertTrue(all(p['publishedPurchasedWeightLb']==7.5 for p in bought));self.assertTrue(all(p['geometryVolumeNotForQuantityMass'] for p in bought));self.assertAlmostEqual(self.result['report']['cast_pan_yd3'],1.614069014,places=8)
  anchor=next(p for p in self.parts if p['id']=='DRAIN-SEAT-BACK-ANCHOR-TAB-0-ANCHOR');self.assertGreater(max(max(0.,float((self.solids[anchor['id']]^native_solid(p)).volume())) for p in self.source['cast']['parts']),TOL,'An omitted actual concrete hole must produce a collision')
 def test_newer_cast_geometry_is_refused(self):
  changed=copy.deepcopy(self.source['cast']['parts']);changed[0]['vertices']=[[x+.01,y,z] for x,y,z in changed[0]['vertices']]
  with self.assertRaisesRegex(AssertionError,'changed cast geometry'):build(changed)
if __name__=='__main__':unittest.main()
# TIMESTAMP END 2026-11-05T16:48:19+00:00 | REVISION R000054
