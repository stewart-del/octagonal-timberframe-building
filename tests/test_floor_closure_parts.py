# TIMESTAMP START 2026-11-05T23:26:47+00:00 | REVISION R000072
"""Current 3mm cork is cut compositionally without filling earlier voids."""
from pathlib import Path
import copy,hashlib,json,os,sys,unittest
import numpy as np
import manifold3d as manifold
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from floor_closure_parts import inputs,cut_current_lower,I,TOL,diff,native_solid
from audit_cavity_fit import inspect_mesh
class FloorClosure(unittest.TestCase):
 def test_all_eight_current_cork_sheets_keep_thickness_and_are_idempotent(self):
  source=inputs()['corkImportBlocker'];before=copy.deepcopy(source);receipts=[]
  for pid,part in source['canonicalSourceParts_UNCHANGED'].items():
   with self.subTest(pid=pid):
    derived,receipt=cut_current_lower(part,source['requiredCutToolsInOrder']);self.assertEqual(receipt['status'],'PASS');self.assertEqual(inspect_mesh(np.asarray(derived['vertices']),np.asarray(derived['triangles'],np.uint64),True)['status'],'PASS');self.assertAlmostEqual(float(np.ptp(np.asarray(derived['vertices'])[:,1])),.003,places=12);self.assertEqual(derived['volumeM3'],derived['volume_m3']);self.assertLess(derived['volumeM3'],native_solid(part).volume());self.assertLessEqual(max(receipt['attempts'][-1][key] for key in ['worldDifferenceIn3','localDifferenceIn3','absoluteVolumeDeltaIn3','addedOutsideOriginalIn3']),1e-6)
    twice,second=cut_current_lower(derived,source['requiredCutToolsInOrder']);self.assertEqual(second['status'],'UNCHANGED_NO_MATERIAL_CONTACT');self.assertLessEqual(diff(native_solid(derived),native_solid(twice)),TOL);receipts.append(receipt)
  self.assertEqual(len(receipts),8);self.assertEqual(source,before);self.assertFalse(inputs()['manifest']['readyForCompleteImport'])
  if os.environ.get('FLOOR_CORK_REPORT'):Path(os.environ['FLOOR_CORK_REPORT']).write_text(json.dumps({'status':'PASS','scope':'Eight current cork seats only; not a complete floor or assembly proof','receipts':receipts},indent=2)+'\n')
 def test_current_extra_void_is_preserved(self):
  part=copy.deepcopy(inputs()['corkImportBlocker']['canonicalSourceParts_UNCHANGED']['FLOOR-CORK-00-00']);v=np.asarray(part['vertices']);centre=v.mean(0);probe=manifold.Manifold.cube([.01,.01,.01],True).translate(centre.tolist());original=native_solid(part);cut=original-probe;mesh=cut.to_mesh64();part.update(vertices=np.asarray(mesh.vert_properties)[:,:3].tolist(),triangles=np.asarray(mesh.tri_verts).tolist());derived,_=cut_current_lower(part,inputs()['corkImportBlocker']['requiredCutToolsInOrder']);self.assertLessEqual(abs((native_solid(derived)^probe).volume()),TOL);self.assertLess(native_solid(derived).volume(),original.volume())
 def test_cut_that_splits_a_current_actor_requires_new_identities(self):
  cube=manifold.Manifold.cube([1,1,1]);mesh=cube.to_mesh64();part={'id':'SOURCE','vertices':np.asarray(mesh.vert_properties)[:,:3].tolist(),'triangles':np.asarray(mesh.tri_verts).tolist(),'stock_frame':{'axis':[1,0,0],'width':[0,1,0],'depth':[0,0,1]}};tool=manifold.Manifold.cube([.1,2,2]).translate([.45,-.5,-.5]).to_mesh64();record={'vertices':np.asarray(tool.vert_properties)[:,:3].tolist(),'triangles':np.asarray(tool.tri_verts).tolist()}
  with self.assertRaisesRegex(AssertionError,'split a current actor'):cut_current_lower(part,[record])
if __name__=='__main__':unittest.main()
# TIMESTAMP END 2026-11-05T23:26:47+00:00 | REVISION R000072
