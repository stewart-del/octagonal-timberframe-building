# TIMESTAMP START 2026-11-05T23:02:22+00:00 | REVISION R000071
"""Actual nail head retention and strict metal contacts in the cupola roof."""
from pathlib import Path
import copy,json,sys,unittest
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from cupola_roof_parts import build
from cupola_roof_bearing_parts import inputs,compose,native_solid,diff,TOL
from audit_cavity_fit import inspect_mesh
from physical_contacts import contact_kind,permitted_withdrawal
class CupolaBearing(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.data=inputs();cls.result=build();cls.parts={p['id']:p for p in cls.result['parts']};cls.cu=set(cls.data['originalCu']);cls.nails=set(cls.data['originalNailPoses'])
 def test_same_inventory_real_holes_head_seats_and_later_covers(self):
  self.assertEqual(len(self.parts),385);self.assertEqual(self.result['report']['bearingCorrection']['correctedNailPoses'],48);self.assertEqual(len(self.cu),17)
  for pid in self.cu:
   p=self.parts[pid];self.assertEqual(inspect_mesh(np.asarray(p['vertices']),np.asarray(p['triangles'],np.uint64),True)['status'],'PASS',pid)
   if pid.startswith('CU-DRIP-'):self.assertEqual(p['freshNailHoleCount'],5);self.assertEqual(len(p['actualNailIds']),5)
  for pid in self.nails:
   p=self.parts[pid];self.assertTrue(p['actualHeadBearing']);self.assertGreater(p['minimum_reference_projected_annular_head_area_in2'],0);self.assertTrue(p['removalPrerequisites']);self.assertEqual(p['fastenerSpec']['lengthIn'],p['length_in']);self.assertTrue(set(p['withdrawalReceiverIds'])<=set(p['receiverIds']));self.assertFalse(set(p['withdrawalReceiverIds'])&set(p['removalPrerequisites']))
   for cover in p['removalPrerequisites']:self.assertIn(cover,self.parts);self.assertFalse(permitted_withdrawal(p,self.parts[cover],p['withdrawal_direction']))
 def test_actual_corrected_bodies_against_all_roof_parts_and_current_primary(self):
  primary=[p for p in json.loads((ROOT/'src/top-entry-proposed-model.json').read_text())['parts'] if p.get('is_timber') or p.get('is_fastener')];records={p['id']:p for p in [*primary,*self.result['parts']]};templates={name:native_solid(p) for name,p in self.result['prototypes'].items()};solids={};bounds={}
  for pid,p in records.items():
   solids[pid]=templates[p['mesh_instance']['prototype']].transform(p['mesh_instance']['transform']) if p.get('mesh_instance') else native_solid(p);bounds[pid]=np.asarray(solids[pid].bounding_box())
  checks=0
  for pid in self.cu|self.nails:
   a=bounds[pid]
   for rid,p in records.items():
    if rid==pid:continue
    b=bounds[rid]
    if not np.all(a[:3]<b[3:]) or not np.all(b[:3]<a[3:]):continue
    checks+=1;volume=max(0.,float((solids[pid]^solids[rid]).volume()))
    if volume>TOL:self.assertIsNotNone(contact_kind(records[pid],p),(pid,rid,'prohibited physical overlap in3',volume/.0254**3))
  self.assertGreater(checks,100)
 def test_idempotence_unaffected_identity_and_current_changes_rejected(self):
  second=compose(self.result,self.data);changed=self.cu|self.nails
  for p in self.result['parts']:
   q=next(q for q in second['parts'] if q['id']==p['id'])
   if p['id'] not in changed:self.assertIs(p,q)
   elif p['id'] in self.cu:self.assertLessEqual(diff(native_solid(p),native_solid(q)),TOL)
   else:self.assertEqual(p['mesh_instance'],q['mesh_instance'])
  pid=next(iter(self.cu));bad={**self.result,'parts':[copy.deepcopy(p) if p['id']==pid else p for p in self.result['parts']]};target=next(p for p in bad['parts'] if p['id']==pid);target['vertices']=[[v[0]+.001,*v[1:]] for v in target['vertices']]
  with self.assertRaisesRegex(AssertionError,'Current Cu changed'):compose(bad,self.data)
  pid=next(iter(self.nails));bad={**self.result,'parts':[copy.deepcopy(p) if p['id']==pid else p for p in self.result['parts']]};target=next(p for p in bad['parts'] if p['id']==pid);target['mesh_instance']['transform'][0][3]+=.001
  with self.assertRaisesRegex(AssertionError,'Current nail pose changed'):compose(bad,self.data)
if __name__=='__main__':unittest.main()
# TIMESTAMP END 2026-11-05T23:02:22+00:00 | REVISION R000071
