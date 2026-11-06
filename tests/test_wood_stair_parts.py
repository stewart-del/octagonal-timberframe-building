# TIMESTAMP START 2026-11-05T17:43:13+00:00 | REVISION R000059
"""Actual wood stair stock, hardware dimensions and retained-scene clearance."""
from pathlib import Path
import copy,hashlib,json,os,sys,unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from wood_stair_parts import inputs,build,pan_id,TOL,checked_difference
from physical_data import read_physical_json,occupied_part
from audit_revised_joinery import native_solid
from audit_cavity_fit import inspect_mesh
from physical_contacts import intended_penetration
import manifold3d as m
ROOT=Path(__file__).resolve().parents[1]
class WoodStairs(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.source=inputs();cls.stairs=cls.source['stairs'];stage=Path(os.environ.get('ARCHITECTURE_SOURCE',ROOT/'src/architectural-solids.json'));cls.arch=read_physical_json(stage);ids={p['id'] for p in cls.stairs['parts'] if not pan_id(p['id'])};cls.parts=[p for p in cls.arch['parts'] if p['id'] in ids];cls.byid={p['id']:p for p in cls.parts}
 def test_every_actual_stair_solid_and_stock_cut(self):
  self.assertEqual(len(self.parts),619);self.assertEqual(len(self.byid),619);self.assertEqual(len(self.arch['woodStairComposition']['original_wood_overlays']),4);self.assertEqual(self.arch['woodStairTakeoff']['linearStockCount'],43)
  for p in self.parts:self.assertEqual(inspect_mesh(np.asarray(p['vertices']),np.asarray(p['triangles'],np.uint64),True)['status'],'PASS',p['id'])
  porch=self.source['original']['porch'];B=np.column_stack([porch['axis'],[0.,1.,0.],porch['normal']]);origin=np.asarray(porch['origin'])
  for row in self.source['stock']['linearStock']:
   blank=native_solid(row['stockEnvelope'])
   for cut in row['pieces']:
    matrix=np.asarray(cut['installedToStockInches']);
    for pid in cut['pieceIds']:
     part=self.byid[pid];local=(np.asarray(part['vertices'])-origin)@B/.0254;v=local@matrix[:,:3].T+matrix[:,3];shape=m.Manifold(m.Mesh64(np.array(v,order='C'),np.array(part['triangles'],np.uint64,order='C')));self.assertLessEqual(max(0.,float((shape-blank).volume())),1e-6,pid);self.assertEqual(part['stock_parent_id'],row['id'])
  self.assertEqual(sum(p['id'].startswith('WOOD-STAIR-STRINGER-') and not p.get('is_fastener') for p in self.parts),4)
 def test_real_component_specs_and_conservative_local_comparison(self):
  peg=self.byid['MUD-LANDING-RAIL-L-MUD-ENTRY-GUARD-POST-L-PEG'];self.assertEqual(peg['fastener_spec']['lengthIn'],3.5);self.assertEqual(peg['fastener_spec']['majorDiameterIn'],.25)
  washer=self.byid['WOOD-LANDING-SHOE-L-BACK-POST-BOLT-1-WASHER-H'];self.assertAlmostEqual(washer['fastener_spec']['lengthIn'],.083,places=6);self.assertIsNone(washer['fastener_spec']['partNumber'],'A standard description must not become a fictitious manufacturer SKU')
  cube=m.Manifold.cube([.1,.1,.1]);other=cube.translate([.001,0,0]);error,_=checked_difference(cube,other);self.assertGreater(error,TOL,'Common-frame conditioning must not erase a real solid difference')
 def test_scoped_stair_contacts_against_current_assembled_scene(self):
  path=os.environ.get('STAGED_SCENE');
  if not path:self.skipTest('Set STAGED_SCENE to the actual current composed scene readback')
  data=json.loads(Path(path).read_text());allparts=[occupied_part(p,data.get('prototypes',{})) for p in data['parts']];lookup={p['id']:p for p in allparts};self.assertEqual(len(lookup),len(allparts));bounds=np.array([[*np.asarray(p['vertices']).min(0),*np.asarray(p['vertices']).max(0)] for p in allparts]);solids={};seen=set();pairs=0
  for pid in self.byid:
   p=lookup[pid];v=np.asarray(p['vertices']);low=v.min(0);high=v.max(0)
   for k in np.flatnonzero(np.all(bounds[:,:3]<high-1e-9,axis=1)&np.all(bounds[:,3:]>low+1e-9,axis=1)):
    q=allparts[int(k)];key=tuple(sorted((pid,q['id'])))
    if pid==q['id'] or key in seen:continue
    seen.add(key);pairs+=1
    if intended_penetration(p,q) or intended_penetration(q,p):continue
    for actor in [p,q]:
     if actor['id'] not in solids:solids[actor['id']]=native_solid(actor)
    self.assertLessEqual(max(0.,float((solids[pid]^solids[q['id']]).volume())),TOL,key)
  self.assertGreater(pairs,1000)
if __name__=='__main__':unittest.main()
# TIMESTAMP END 2026-11-05T17:43:13+00:00 | REVISION R000059
