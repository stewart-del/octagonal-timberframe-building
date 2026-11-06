# TIMESTAMP START 2026-11-05T21:07:06+00:00 | REVISION R000065
"""Scene source mutation and the unchanged native scene import contract."""
from pathlib import Path
import hashlib,sys,tempfile,unittest
import numpy as np
import manifold3d as m
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from current_physical_scene import assert_current_sources,KERNEL_SOURCES
from plan_architectural_disassembly import scene_from_payload,check_stage,apply_stage
class CurrentPhysicalScene(unittest.TestCase):
 def test_current_checker_is_byte_identical(self):assert_current_sources(KERNEL_SOURCES)
 def test_source_mutation_rejected(self):
  with tempfile.TemporaryDirectory() as directory:
   path=Path(directory)/'stock.json';path.write_bytes(b'actual source stock');sources={'stock.json':hashlib.sha256(path.read_bytes()).hexdigest()};assert_current_sources(sources,directory);path.write_bytes(b'changed source stock')
   with self.assertRaisesRegex(AssertionError,'source changed'):assert_current_sources(sources,directory)
 def test_real_parked_actor_is_retained_by_native_scene_contract(self):
  mesh=m.Manifold.cube([.1,.1,.1]).to_mesh64();cube={'vertices':np.asarray(mesh.vert_properties)[:,:3].tolist(),'triangles':np.asarray(mesh.tri_verts).tolist()}
  raw={'parts':[{'id':'A',**cube},{'id':'B','mesh_instance':{'prototype':'cube','transform':[[1,0,0,.5],[0,1,0,0],[0,0,1,0]]}}],'prototypes':{'cube':cube}}
  scene=scene_from_payload('fixture',raw);proof=check_stage(scene,['B'],[.5,0,0]);self.assertEqual(proof['status'],'PASS');apply_stage(scene,['B'],[.5,0,0],proof)
  self.assertEqual(set(scene.parts),{'A','B'});self.assertEqual(set(scene.solids),{'A','B'});blocked=check_stage(scene,['A'],[1.,0,0]);self.assertEqual(blocked['status'],'BLOCKED');self.assertTrue(any(p['obstacle_id']=='B' and p['obstacle_parked'] for p in blocked['collisions']))
if __name__=='__main__':unittest.main()
# TIMESTAMP END 2026-11-05T21:07:06+00:00 | REVISION R000065
