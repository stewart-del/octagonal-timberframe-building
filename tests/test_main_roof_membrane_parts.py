# TIMESTAMP START 2026-11-05T22:52:56+00:00 | REVISION R000070
"""Authored roll stock, real85sheet boundaries and current GP seat composition."""
from pathlib import Path
import copy,itertools,json,subprocess,sys,unittest
import manifold3d as m
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from main_roof_membrane_parts import inputs,build,compose_gp,verify_default,native_solid,inspect_mesh,I,TOL,amount,diff
from closure_core_parts import inputs as core_inputs,mesh
class MainRoofBarrier(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.data=inputs();cls.result=build(cls.data)
 def test_all_actual_sheet_boundaries_and_original_cut_identities(self):
  self.assertEqual(len(self.result['parts']),85);self.assertEqual(len(self.result['stock']['cuts']),73);self.assertEqual(self.result['stock']['roll_count'],5);original={p['id']:p for p in self.data['parts']}
  for p in self.result['parts']:
   self.assertEqual(p['vertices'],original[p['id']]['vertices']);self.assertEqual(p['triangles'],original[p['id']]['triangles']);self.assertEqual(inspect_mesh(np.asarray(p['vertices']),np.asarray(p['triangles'],np.uint64),True)['status'],'PASS',p['id']);self.assertGreater(native_solid(p).volume(),0);self.assertLessEqual(p['stockWidthIn'],57);self.assertLessEqual(p['stockLengthIn'],960)
  self.assertFalse(self.result['report']['enclosureBootIntegrated']);self.assertEqual(self.data['proof']['intersections'],[]);self.assertEqual(self.data['proof']['raw_failures'],[])
 def test_independent_five_roll_rectangle_layout_and_product_laps(self):
  cuts=self.result['stock']['cuts'];self.assertEqual(len({p['parentRollId'] for p in cuts}),5)
  for p in cuts:
   self.assertGreaterEqual(p['roll_x_in'],0);self.assertGreaterEqual(p['roll_y_in'],0);self.assertLessEqual(p['roll_x_in']+p['blank_width_in'],57+1e-9);self.assertLessEqual(p['roll_y_in']+p['blank_length_in'],960+1e-9)
  for a,b in itertools.combinations(cuts,2):
   if a['parentRollId']!=b['parentRollId']:continue
   width=min(a['roll_x_in']+a['blank_width_in'],b['roll_x_in']+b['blank_width_in'])-max(a['roll_x_in'],b['roll_x_in']);height=min(a['roll_y_in']+a['blank_length_in'],b['roll_y_in']+b['blank_length_in'])-max(a['roll_y_in'],b['roll_y_in']);self.assertFalse(width>1e-9 and height>1e-9,(a['id'],b['id']))
  product=self.data['v2']['roof_product'];self.assertEqual(product['horizontal_lap_min_in'],4);self.assertEqual(product['end_lap_min_in'],6);self.assertEqual(product['corner_lap_min_in'],12)
 def test_current_gp_cut_is_idempotent_and_preserves_a_later_void(self):
  core=core_inputs()['wood'];current=copy.deepcopy({pid:core['add_parts'][pid] for pid in self.data['gpTools']});first=compose_gp(current,self.data);second=compose_gp(first['parts'],self.data)
  for pid in current:
   old=native_solid(current[pid]);new=native_solid(first['parts'][pid]);self.assertLessEqual(amount(new-old),TOL);self.assertLessEqual(diff(new,native_solid(self.data['gpReference'][pid])),TOL);self.assertLessEqual(diff(new,native_solid(second['parts'][pid])),TOL)
  pid=next(iter(current));p=first['parts'][pid];solid=native_solid(p);vertices=np.asarray(p['vertices']);selected=None
  for indices in p['triangles']:
   center=vertices[indices].mean(0);tool=m.Manifold.cube([.03125*I]*3).translate((center-.015625*I).tolist());candidate=solid-tool
   if amount(solid^tool)>TOL and len([c for c in candidate.decompose() if c.volume()>TOL])==1:selected=candidate;break
  self.assertIsNotNone(selected);later=dict(first['parts']);later[pid]={**p,**mesh(selected)};after=compose_gp(later,self.data);self.assertLessEqual(diff(selected,native_solid(after['parts'][pid])),TOL,'A later current cavity must not be filled from a reference')
  missing=dict(current);del missing[pid]
  with self.assertRaisesRegex(AssertionError,'Missing current new GP'):compose_gp(missing,self.data)
 def test_changed_default_is_rejected(self):
  with self.assertRaisesRegex(AssertionError,'Changed primary default'):verify_default(self.data,read_source=lambda name:(ROOT/name).read_bytes()+b'\n' if name=='src/model-data.json' else (ROOT/name).read_bytes())
 def test_existing_inventory_exposes_dimensions_and_counts_each_cut_once(self):
  pieces=[{k:v for k,v in p.items() if k not in ['vertices','triangles']} for p in self.result['parts']];program="const fs=require('node:fs'),I=require('./src/component-inventory.js'),r=I.build(JSON.parse(fs.readFileSync(0,'utf8')));process.stdout.write(JSON.stringify({rows:r.rows.map(p=>({id:p.id,stockParent:p.stockParent,dimensionsIn:p.dimensionsIn})),parents:[...new Set(r.rows.map(p=>p.stockParent))]}));";result=json.loads(subprocess.run(['node','-e',program],cwd=ROOT,input=json.dumps(pieces),capture_output=True,text=True,check=True).stdout);self.assertEqual(len(result['rows']),85);self.assertEqual(len(result['parents']),73)
  for p in result['rows']:self.assertEqual(len(p['dimensionsIn']),3);self.assertEqual(p['dimensionsIn'][2],.025);self.assertTrue(p['stockParent'].startswith('CUT-VDSA-'))
if __name__=='__main__':unittest.main()
# TIMESTAMP END 2026-11-05T22:52:56+00:00 | REVISION R000070
