# TIMESTAMP START 2026-11-06T02:53:16+00:00 | REVISION R000082
"""The added earlier contacts never survive changed poses, products or material."""
from pathlib import Path
import copy,sys,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from floor_contact_metadata import inputs,apply,descriptor,FIXTURE,FIXTURE_SHA
from closure_core_parts import hardware
from floor_closure_parts import inputs as floor_inputs
from physical_contacts import contact_kind,permitted_withdrawal

class FloorContacts(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.data=inputs();core=hardware();cls.parts=core['parts'];cls.prototypes=core['prototypes'];floor=floor_inputs();wood=floor['woodAndFirstNegativeTools']['add_parts'];cls.receivers={rid:floor['filmsGapAndAdditionalNegativeTools']['replaceNewEnvelopeParts_READBACK_ONLY'].get(rid,p)for rid,p in wood.items()};cls.receivers.update({**floor['shared229']['parts'],**floor['shared229']['bootParts'],**floor['filmsGapAndAdditionalNegativeTools']['parts']});cls.result=apply(cls.parts,cls.receivers,cls.prototypes)
 def test_all_declared_pairs_keep_source_geometry_and_actual_earlier_material_order(self):
  self.assertEqual(len(self.result['parts']),9415);before={p['id']:p for p in self.parts};after={p['id']:p for p in self.result['parts']};count=0
  for pid,row in self.data['fasteners'].items():
   original=before[pid];actual=after[pid];self.assertEqual(descriptor(original),descriptor(actual));self.assertEqual(actual['removalPrerequisites'],original['removalPrerequisites']);self.assertTrue(set(original['receiverIds'])<=set(actual['receiverIds']))
   for rid in row['earlierReceiverIds']:
    receiver=self.receivers[rid];count+=1;self.assertTrue(contact_kind(actual,receiver));self.assertTrue(permitted_withdrawal(actual,receiver,actual['withdrawal_direction']));self.assertFalse(permitted_withdrawal(actual,receiver,[-v for v in actual['withdrawal_direction']]));self.assertFalse(permitted_withdrawal(actual,receiver,actual['withdrawal_direction'],[0,.001,0]));self.assertIn(rid,actual['assemblyPrerequisiteMaterialIds'])
  self.assertEqual(count,688);self.assertEqual(self.result['report']['fasteners'],446)
  repeated=apply(self.result['parts'],self.receivers,self.prototypes);self.assertEqual(self.result,repeated)
 def test_later_covers_never_gain_the_floor_exemption(self):
  after={p['id']:p for p in self.result['parts']};covered=0
  for pid in self.data['fasteners']:
   part=after[pid]
   for rid in part.get('removalPrerequisites',[]):
    covered+=1;self.assertFalse(permitted_withdrawal(part,{'id':rid,'material':'membrane'},part['withdrawal_direction']))
  self.assertGreater(covered,0)
 def test_all_688_native_contacts_match_the_exact_unmodified_source(self):
  from physical_data import occupied_part
  from audit_revised_joinery import native_solid
  from cupola_joinery_recipe import amount,I
  parts={p['id']:p for p in self.parts};cache={};wood=0;film=0
  for row in self.data['positiveNativeContactReceipts']:
   pid,rid=row['fastener'],row['receiver']
   if pid not in cache:cache[pid]=native_solid(occupied_part(parts[pid],self.prototypes))
   if rid not in cache:cache[rid]=native_solid(self.receivers[rid])
   actual=amount(cache[pid]^cache[rid])/I**3;self.assertGreater(actual,1e-6);self.assertLessEqual(abs(actual-row['nativeOverlapIn3']),1e-6)
   if self.data['receivers'][rid]['earlierMaterialKind']=='wood':wood+=1
   else:film+=1
  self.assertEqual((wood,film),(69,619))
 def test_changed_pose_product_target_or_prototype_requires_new_source_proof(self):
  target=next(iter(self.data['fasteners']));index=next(i for i,p in enumerate(self.parts)if p['id']==target)
  for field in ['pose','product']:
   bad=list(self.parts);bad[index]=copy.deepcopy(bad[index])
   if field=='pose':bad[index]['mesh_instance']['transform'][0][3]+=.001
   else:bad[index]['fastenerSpec']['partNumber']='UNVERIFIED-PRODUCT'
   with self.assertRaisesRegex(AssertionError,'pose or product changed'):apply(bad,self.receivers,self.prototypes)
  rid=next(iter(self.data['receivers']));bad=dict(self.receivers);bad[rid]=copy.deepcopy(bad[rid]);bad[rid]['vertices'][0][0]+=.001
  with self.assertRaisesRegex(AssertionError,'receiver changed'):apply(self.parts,bad,self.prototypes)
  proto=next(iter(self.data['prototypes']));bad=copy.deepcopy(self.prototypes);bad[proto]['vertices'][0][0]+=.001
  with self.assertRaisesRegex(AssertionError,'prototype changed'):apply(self.parts,self.receivers,bad)
  with self.assertRaisesRegex(AssertionError,'Missing wall fastener'):apply([p for p in self.parts if p['id']!=target],self.receivers,self.prototypes)

if __name__=='__main__':unittest.main()
# TIMESTAMP END 2026-11-06T02:53:16+00:00 | REVISION R000082
