# TIMESTAMP START 2026-11-05T19:06:47+00:00 | REVISION R000061
"""Real cupola roof boundaries, distinct nails and bored copper interfaces."""
from pathlib import Path
import copy,hashlib,json,os,sys,tempfile,unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from cupola_roof_parts import inputs,decoded,build,TOL
from physical_data import read_physical_json,occupied_part
from audit_cavity_fit import inspect_mesh
from audit_revised_joinery import native_solid
from physical_contacts import intended_penetration,permitted_withdrawal
ROOT=Path(__file__).resolve().parents[1]
class CupolaRoof(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.files=inputs();cls.manifest=decoded(cls.files,'manifest.json');cls.arch=read_physical_json(Path(os.environ.get('ARCHITECTURE_SOURCE',ROOT/'src/architectural-solids.json')));ids=set(cls.manifest['replace_same_id_physical_parts']+cls.manifest['replace_aux_same_id_104']+cls.manifest['add_roof8d_ids']);cls.parts=[occupied_part(p,cls.arch['prototypes']) for p in cls.arch['parts'] if p['id'] in ids or 'CUP' in p['id'] and p['id'].startswith(('VDSA-','CU-DRIP-'))];cls.byid={p['id']:p for p in cls.parts}
 def test_actual_piece_boundaries_and_nail_purchase_counts(self):
  self.assertEqual(len(self.parts),385);self.assertEqual(len(self.byid),385)
  for p in self.parts:self.assertEqual(inspect_mesh(np.asarray(p['vertices']),np.asarray(p['triangles'],np.uint64),True)['status'],'PASS',p['id'])
  self.assertEqual(sum(p.get('is_fastener',False) for p in self.parts),272);self.assertEqual(sum(p['id'].startswith('CUP-ROOF-DECK-8D-') for p in self.parts),128);self.assertFalse(any(p['id'].startswith('CUP-DECK-SCREW-') for p in self.arch['parts']))
  for k in range(8):
   panel=self.byid[f'CUP-ROOF-DECK-{k}'];self.assertEqual(panel['roofPlywoodProcurementSpec']['requiredStamp']['bondClass'],'EXTERIOR');self.assertEqual(panel['field_trim_blank_in'],[47.875,95.875,.703])
  ceiling_ids=[p['id'] for p in self.arch['parts'] if p.get('constructionPhase')=='Cupola ceiling' and p.get('is_fastener')];self.assertEqual(len(ceiling_ids),128)
 def test_causal_receivers_never_include_later_copper_coverings(self):
  count=0
  for row in decoded(self.files,self.manifest['assets']['aux-instances']['path'])['instances']:
   p=self.byid[row['id']];self.assertTrue(set(row['extractionBlockedBy'])<=set(p['removalPrerequisites']))
   for pid in row['extractionBlockedBy']:
    count+=1;self.assertNotIn(pid,p['withdrawalReceiverIds']);self.assertFalse(permitted_withdrawal(p,self.byid[pid],np.asarray(p['withdrawal_direction'])*p['withdrawal_distance_m']))
  self.assertEqual(count,120)
  with tempfile.TemporaryDirectory() as directory:
   path=Path(directory)/'changed-model.json';path.write_text('{}')
   with self.assertRaisesRegex(AssertionError,'Changed primary default'):build(path)
 def test_scoped_contacts_in_actual_composed_scene(self):
  path=os.environ.get('STAGED_SCENE')
  if not path:self.skipTest('Set STAGED_SCENE to actual current physical readback')
  data=json.loads(Path(path).read_text());records=[occupied_part(p,data.get('prototypes',{})) for p in data['parts']];lookup={p['id']:p for p in records};bounds=np.array([[*np.asarray(p['vertices']).min(0),*np.asarray(p['vertices']).max(0)] for p in records]);solids={};seen=set();checks=0;violations=[]
  for pid in self.byid:
   self.assertIn(pid,lookup);p=lookup[pid];v=np.asarray(p['vertices']);low=v.min(0);high=v.max(0)
   for index in np.flatnonzero(np.all(bounds[:,:3]<high-1e-9,axis=1)&np.all(bounds[:,3:]>low+1e-9,axis=1)):
    q=records[int(index)];key=tuple(sorted([pid,q['id']]))
    if pid==q['id'] or key in seen:continue
    seen.add(key);checks+=1
    if intended_penetration(p,q) or intended_penetration(q,p):continue
    for record in [p,q]:
     if record['id'] not in solids:solids[record['id']]=native_solid(record)
    volume=max(0.,float((solids[pid]^solids[q['id']]).volume()))
    if volume>TOL:violations.append({'a':pid,'b':q['id'],'overlap_m3':volume})
  self.assertFalse(violations,violations[:20]);self.assertGreater(checks,1000)
if __name__=='__main__':unittest.main()
# TIMESTAMP END 2026-11-05T19:06:47+00:00 | REVISION R000061
