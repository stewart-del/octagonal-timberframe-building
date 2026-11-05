# TIMESTAMP START 2026-11-05T22:31:25+00:00 | REVISION R000069
"""Pose-bound embed recipients and later covers across9415 distinct fasteners."""
from pathlib import Path
import ast,copy,re,sys,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from closure_core_parts import inputs,causal_inputs,hardware,apply_causal_metadata,source_pose
from physical_contacts import permitted_withdrawal
class ClosureCausal(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.core=inputs();cls.delta=causal_inputs();cls.original={p['id']:p for p in [*cls.core['retained']['instances'],*cls.core['hardware']['instances']]};cls.parts=hardware(cls.core)['parts']
 def test_all_poses_static_lists_and_earlier_recipient_constraints(self):
  self.assertEqual(len(self.parts),9415);later_count=0
  for p in self.parts:
   original=self.original[p['id']];row=self.delta['fasteners'][p['id']];self.assertEqual(source_pose(p),source_pose(original));self.assertEqual(p['receiverIds'],original['receiverIds']);self.assertEqual(p['withdrawalReceiverIds'],row['withdrawalReceiverIds']);self.assertTrue(p['withdrawalReceiverIds']);self.assertTrue(set(p['withdrawalReceiverIds'])<=set(p['receiverIds']));self.assertFalse(set(p['withdrawalReceiverIds'])&set(p['removalPrerequisites']))
   for later in row['laterStaticContactIds']+row['laterHeadCoverIds']:
    later_count+=1;self.assertIn(later,p['removalPrerequisites']);self.assertFalse(permitted_withdrawal(p,{'id':later,'material':'wood'},p['withdrawal_direction']))
  self.assertGreater(later_count,2302)
 def test_upper_siding_courses_never_become_lower_nail_exemptions(self):
  count=0;covered=0;pattern=re.compile(r'^LAP-([A-Z]+)-(\d+)-')
  for p in self.parts:
   parent=pattern.match(p['parentId'])
   if not parent:continue
   count+=1;face,course=parent.group(1),int(parent.group(2))
   for rid in p['withdrawalReceiverIds']:
    other=pattern.match(rid)
    if other and other.group(1)==face:self.assertLessEqual(int(other.group(2)),course,(p['id'],rid))
   if any((m:=pattern.match(rid)) and m.group(1)==face and int(m.group(2))>course for rid in p['removalPrerequisites']):covered+=1
  self.assertEqual(count,2849);self.assertEqual(covered,2302)
 def test_changed_pose_rejected_and_new_static_contact_preserved_without_exemption(self):
  original=next(iter(self.original.values()));bad=copy.deepcopy(original);bad['mesh_instance']['transform'][0][3]+=.001
  with self.assertRaisesRegex(AssertionError,'source pose changed'):apply_causal_metadata(bad,self.delta)
  new=copy.deepcopy(original);new['receiverIds'].append('LATER-NEW-FILM');before=copy.deepcopy(new['receiverIds']);result=apply_causal_metadata(new,self.delta);self.assertEqual(result['receiverIds'],before);self.assertNotIn('LATER-NEW-FILM',result['withdrawalReceiverIds']);self.assertFalse(permitted_withdrawal(result,{'id':'LATER-NEW-FILM','material':'membrane'},result['withdrawal_direction']))
 def test_cladding_visibility_and_closure_phases_follow_their_actual_owners(self):
  tree=ast.parse((ROOT/'scripts/prepare_architecture.py').read_text());function=next(node for node in ast.walk(tree) if isinstance(node,ast.FunctionDef) and node.name=='wall_properties');scope={};exec(compile(ast.Module(body=[function],type_ignores=[]),'wall_properties','exec'),scope);classify=scope['wall_properties']
  for part in [{'id':'LAP-N-02-01','material':'LP SmartSide lap siding'},{'id':'ENV-W-DOOR-TRIM','material':'LP SmartSide540 trim'}]:self.assertEqual(classify(part)[:3],('Main siding','wall','wall'))
  for pid,phase in [('BOX-PORCH-W-SOFFIT','Porch eave closures after porch roof'),('BOX-CUP-N-FASCIA','Cupola eave closures'),('BOX-MAIN-N-SOFFIT','Main wall roof-edge closures after porch')]:self.assertEqual(classify({'id':pid,'material':'wood'})[0],phase)
if __name__=='__main__':unittest.main()
# TIMESTAMP END 2026-11-05T22:31:25+00:00 | REVISION R000069
