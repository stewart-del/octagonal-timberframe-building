# TIMESTAMP START 2026-11-05T13:19:15+00:00 | REVISION R000044
"""Declared nail drive contact never permits intersecting timbers or held wood."""
import copy,sys,unittest
from unittest.mock import patch
from pathlib import Path
import numpy as np
import manifold3d as m
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from physical_contacts import intended_penetration,permitted_withdrawal
from plan_architectural_disassembly import Scene,audit_initial_scene,check_stage,scene_from_payload
class PhysicalContacts(unittest.TestCase):
 def fixture(self):
  wood={'id':'WOOD','material':'wood','is_timber':True};nail={'id':'NAIL','material':'Type316 stainless steel','is_fastener':True,'fastenerKind':'nail','intentionalFastenerPenetration':True,'receiverIds':['WOOD'],'withdrawalReceiverIds':['WOOD'],'withdrawal_direction':[0,0,1]}
  solids={'WOOD':m.Manifold.cube([1,1,1]),'NAIL':m.Manifold.cylinder(.2,.01,.01,16).translate([.5,.5,.9])}
  return Scene('test',{'WOOD':wood,'NAIL':nail},solids,{key:np.zeros(3) for key in solids})
 def test_exact_compact_scene_instances_and_rigid_validation(self):
  cube=m.Manifold.cube([1,2,3]).to_mesh64();prototype={'vertices':np.asarray(cube.vert_properties)[:,:3].tolist(),'triangles':np.asarray(cube.tri_verts).tolist()}
  parts=[{'id':'I1','mesh_instance':{'prototype':'SINGLE','transform':[[0,-1,0,4],[1,0,0,5],[0,0,1,6]]}},{'id':'I2','mesh_instance':{'prototype':'SINGLE','transform':[[1,0,0,10],[0,1,0,20],[0,0,1,30]]}}]
  scene=scene_from_payload('test',{'parts':parts,'prototypes':{'SINGLE':prototype}})
  self.assertEqual(len(scene.solids),2);self.assertAlmostEqual(scene.solids['I1'].volume(),6);self.assertTrue(np.allclose(scene.solids['I1'].bounding_box(),[2,5,6,4,6,9]));self.assertNotIn('vertices',scene.parts['I1'])
  bad=copy.deepcopy(parts);bad[0]['mesh_instance']['transform'][0][1]=-2
  with self.assertRaisesRegex(AssertionError,'Non-rigid'):scene_from_payload('test',{'parts':bad,'prototypes':{'SINGLE':prototype}})
 def test_actual_installed_nail_and_axis_withdrawal(self):
  scene=self.fixture();proof=audit_initial_scene(scene);self.assertEqual(proof['status'],'PASS');self.assertEqual(len(proof['intentional_fastener_contacts']),1);self.assertGreater(proof['maximum_intersection_m3'],proof['overlap_tolerance_m3'])
  self.assertEqual(check_stage(scene,['NAIL'],[0,0,.3])['status'],'PASS')
  self.assertEqual(check_stage(scene,['NAIL'],[.3,0,0])['status'],'BLOCKED')
  self.assertEqual(check_stage(scene,['WOOD'],[0,0,-.3])['status'],'BLOCKED')
 def test_sweep_error_budget_and_triangle_accounting_remain_enforced(self):
  from plan_architectural_disassembly import VOLUME_TOLERANCE_M3 as tolerance
  scene=self.fixture();shape=scene.solids['NAIL'];account={'method':'fixture sweep accounting','discarded_prism_volume_m3':tolerance/10,'triangle_prism_count':7}
  with patch('plan_architectural_disassembly.sweep_cover',return_value=(shape,account)):
   proof=check_stage(scene,['NAIL'],[.3,0,0]);self.assertEqual(proof['discarded_sweep_prism_volume_m3'],tolerance/10);self.assertEqual(proof['triangle_prism_count'],7);self.assertEqual(proof['methods'],['fixture sweep accounting'])
  with patch('plan_architectural_disassembly.sweep_cover',return_value=(shape,{**account,'discarded_prism_volume_m3':2*tolerance})):
   with self.assertRaisesRegex(AssertionError,'Accumulated omitted sweep'):check_stage(scene,['NAIL'],[.3,0,0])
 def test_later_covering_blocks_even_declared_static_contact(self):
  scene=self.fixture();nail=scene.parts['NAIL'];nail['receiverIds'].append('LATER')
  scene.parts['LATER']={'id':'LATER','material':'cedar','is_timber':True}
  scene.solids['LATER']=m.Manifold.cube([1,1,.1]).translate([0,0,1.025]);scene.offsets['LATER']=np.zeros(3)
  self.assertTrue(intended_penetration(nail,scene.parts['LATER']))
  self.assertFalse(permitted_withdrawal(nail,scene.parts['LATER'],[0,0,.3]))
  self.assertEqual(check_stage(scene,['NAIL'],[0,0,.3])['status'],'BLOCKED')
  scene.offsets['LATER']=np.array([2,0,0]);self.assertEqual(check_stage(scene,['NAIL'],[0,0,.3])['status'],'PASS')
  del nail['withdrawalReceiverIds'];self.assertFalse(permitted_withdrawal(nail,scene.parts['WOOD'],[0,0,.3]))
 def test_no_wood_wood_metal_or_peg_exception(self):
  scene=self.fixture();nail=scene.parts['NAIL'];wood=scene.parts['WOOD']
  for changed in [{'material':'steel'},{'is_fastener':True,'material':'hardwood peg'},{'id':'UNDECLARED'}]:
   receiver={**wood,**changed};self.assertFalse(intended_penetration(nail,receiver))
  self.assertFalse(intended_penetration({**nail,'fastenerKind':'plate'},wood));self.assertFalse(intended_penetration({**nail,'fastenerKind':'threaded rod'},wood))
  scene.parts['NAIL']={**nail,'material':'wood'};self.assertEqual(audit_initial_scene(scene)['status'],'BLOCKED')
 def test_flexible_weather_layer_only_when_declared(self):
  scene=self.fixture();nail=scene.parts['NAIL'];layer={'id':'FELT','material':'roofing felt membrane'}
  self.assertFalse(intended_penetration(nail,layer));nail={**nail,'receiverIds':['WOOD','FELT']};self.assertTrue(intended_penetration(nail,layer))
  self.assertFalse(permitted_withdrawal(nail,layer,[0,0,.1],[0,0,.1]))
if __name__=='__main__':unittest.main()
# TIMESTAMP END 2026-11-05T13:19:15+00:00 | REVISION R000044
