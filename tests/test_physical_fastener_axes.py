# TIMESTAMP START 2026-11-06T00:29:52+00:00 | REVISION R000075
"""The physical head determines sign; a relocated shaft determines direction."""
from pathlib import Path
import copy,math,sys,unittest
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from physical_fastener_axes import audit,physical_head_axis,bridge_contact_metadata,prototype_withdrawal_axis
def nail(dense_head=False):
 rings=[(.15,z) for z in np.linspace(0,.035,101 if dense_head else 2)]+[(.05,.035),(.05,1.285),(.001,1.405)];vertices=[[radius*math.cos(k*math.pi/8),radius*math.sin(k*math.pi/8),z] for radius,z in rings for k in range(16)];return {'vertices':vertices,'triangles':[]}
def instance(direction,matrix=None):return {'id':'N','is_fastener':True,'fastenerKind':'nail','material':'steel','withdrawal_direction':direction,'mesh_instance':{'prototype':'N','transform':matrix or [[1,0,0,0],[0,1,0,0],[0,0,1,0]]}}
class PhysicalAxes(unittest.TestCase):
 def test_real_core_prototypes_require_exact_shank_conventions(self):
  from closure_core_parts import hardware,inputs
  actual=hardware(inputs());proof=audit(actual['parts'],actual['prototypes']);self.assertEqual(proof['status'],'PASS');self.assertEqual(proof['checkedHeadedFasteners'],9415);self.assertEqual(proof['sourceBoundNominalShankInstances'],6811)
  cylinder=actual['prototypes']['WALL-PROTO-T8PCS10'];axis,evidence=prototype_withdrawal_axis(cylinder);self.assertEqual(axis.tolist(),[0,0,-1]);self.assertIn('source-bound',evidence)
  unknown=copy.deepcopy(cylinder);unknown['vertices'][0][0]+=1e-12
  with self.assertRaisesRegex(AssertionError,'ambiguous'):prototype_withdrawal_axis(unknown)
  wrong=copy.deepcopy(cylinder);wrong['fastenerSpec']['partNumber']='OTHER'
  with self.assertRaisesRegex(AssertionError,'product'):prototype_withdrawal_axis(wrong)
 def test_head_end_uses_physical_extent_even_with_dense_head_vertices(self):
  for dense in [False,True]:self.assertLess(np.linalg.norm(physical_head_axis(nail(dense))-[0,0,-1]),1e-12);self.assertEqual(audit([instance([0,0,-1])],{'N':nail(dense)})['status'],'PASS')
 def test_rotation_cannot_keep_the_original_direction_and_reversed_sign_fails(self):
  a=math.pi/3;matrix=[[math.cos(a),0,math.sin(a),2],[0,1,0,3],[-math.sin(a),0,math.cos(a),4]];expected=(-np.asarray(matrix)[:,2]).tolist();self.assertEqual(audit([instance(expected,matrix)],{'N':nail()})['status'],'PASS')
  bad=audit([instance([0,0,-1],matrix)],{'N':nail()});self.assertEqual(bad['status'],'BLOCKED');self.assertAlmostEqual(bad['failures'][0]['angularDifferenceDegrees'],60,places=7);opposite=audit([instance((-np.asarray(expected)).tolist(),matrix)],{'N':nail()});self.assertEqual(opposite['status'],'BLOCKED');self.assertAlmostEqual(opposite['failures'][0]['angularDifferenceDegrees'],180,places=6)
 def test_direct_world_mesh_and_missing_direction(self):
  p={'id':'WORLD','is_fastener':True,'fastenerKind':'screw','material':'steel','withdrawal_direction':[0,0,-1],**nail()};self.assertEqual(audit([p],{})['status'],'PASS');del p['withdrawal_direction'];self.assertEqual(audit([p],{})['status'],'BLOCKED')
 def test_only_source_named_bridge_wood_gets_contact_metadata(self):
  screw={'id':'M-TMP-SCREW-0-1','parentId':'M-TMP','is_fastener':True,'material':'steel','receiverIds':['C0','M-TMP'],'screw_geometry':{'receiver':'C0'},'fastenerSpec':{'partNumber':'14221 / RSS5/16x3-1/8'}};parts=[{'id':'C0','is_timber':True},{'id':'M-TMP','material':'steel'},screw];before=copy.deepcopy(parts);result,ids=bridge_contact_metadata(parts);self.assertEqual(parts,before);self.assertEqual(ids,[screw['id']]);self.assertEqual(result[-1]['withdrawalReceiverIds'],['C0']);self.assertTrue(result[-1]['intentionalFastenerPenetration']);self.assertEqual(result[-1]['receiverIds'],['C0','M-TMP'])
  bad=copy.deepcopy(parts);bad[-1]['screw_geometry']['receiver']='OTHER'
  with self.assertRaises(AssertionError):bridge_contact_metadata(bad)
if __name__=='__main__':unittest.main()
# TIMESTAMP END 2026-11-06T00:29:52+00:00 | REVISION R000075
