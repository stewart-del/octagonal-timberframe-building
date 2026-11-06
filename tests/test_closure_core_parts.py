# TIMESTAMP START 2026-11-05T21:51:55+00:00 | REVISION R000068
"""Current-source closure stock, negative cuts and conservative hardware state."""
from pathlib import Path
import copy,gzip,json,sys,unittest
import numpy as np
import manifold3d as m
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from closure_core_parts import inputs,verify_default,compose_wood,compose_stock,hardware,shape,mesh,amount,diff,union,native_solid,I,TOL
from audit_cavity_fit import inspect_mesh
from physical_contacts import permitted_withdrawal
class ClosureCore(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.data=inputs();cls.templates={**cls.data['wood']['replace_new_envelope_parts'],**cls.data['wood']['add_parts']};payload=json.loads(gzip.decompress((ROOT/'scripts/fixtures/architectural-inputs.json.gz').read_bytes()));raw=json.loads(payload['files']['wall_wood']['content'])['add_parts'];del payload
  assert len(raw)==567
  for pid in cls.data['wood']['requiredAdditionalNewEnvelopeCutTools']:
   assert all(raw[pid][key]==cls.data['receivers']['parts'][pid][key] for key in ['vertices','triangles']),pid
  cls.original={**raw,**cls.data['receivers']['parts']};cls.current=compose_wood({'parts':cls.original},cls.data);cls.parts=cls.current['parts'];cls.solids={pid:shape(cls.parts[pid]) for pid in cls.templates}
 def test_every_current_closure_body_and_actual_stock_partition(self):
  self.assertEqual(len(self.templates),315);self.assertEqual(sum(bool(p.get('closureCorePiece')) for p in self.parts.values()),315);self.assertEqual(self.current['closureCoreComposition']['receiverCount'],75);self.assertFalse(self.current['closureCoreComposition']['primarySnapshotsOverwritten'])
  for pid in self.templates:
   p=self.parts[pid];self.assertEqual(inspect_mesh(np.asarray(p['vertices']),np.asarray(p['triangles'],np.uint64),True)['status'],'PASS',pid);self.assertLessEqual(diff(self.solids[pid],shape(self.templates[pid])),TOL,pid)
  for pid in self.data['receivers']['protectedIDs']:self.assertEqual(self.original[pid],self.parts[pid],pid)
  exported=compose_stock(self.parts,self.data);records={**exported['newStock'],**exported['sourceStockRecordOverrides']};self.assertEqual(len(exported['newStock']),222);self.assertEqual(len(exported['sourceStockRecordOverrides']),68);self.assertEqual(exported['serializedWasteComposition']['stockCount'],290)
  for sid,row in records.items():
   for pid in row['children']:
    if pid not in self.solids:self.solids[pid]=shape(self.parts[pid])
   # TIMESTAMP START 2026-11-05T23:39:11+00:00 | REVISION R000073
   blank=shape(row['blank']);installed=union([self.solids[pid] for pid in row['children']]);separate='declared_exterior_offcut_pieces' in row;meshes=row['declared_exterior_offcut_pieces'] if separate else [row['declared_exterior_offcut']];pieces=[native_solid(q) for q in meshes if q['triangles']];offcut=union(pieces);self.assertLessEqual(amount(installed-blank),TOL,(sid,'outside actual stock'));self.assertLessEqual(diff(blank,installed+offcut),TOL,(sid,'stock partition'));self.assertFalse(row['nailScrewBoresApplied'])
   for q in meshes:
    if q['triangles']:self.assertEqual(inspect_mesh(np.asarray(q['vertices']),np.asarray(q['triangles'],np.uint64),separate)['status'],'PASS',sid)
   # TIMESTAMP END 2026-11-05T23:39:11+00:00 | REVISION R000073
 def test_idempotence_protected_hosts_extra_void_and_missing_child(self):
  second=compose_wood(self.current,self.data)
  for pid in self.templates:self.assertLessEqual(diff(shape(second['parts'][pid]),self.solids[pid]),TOL,pid)
  bad={'parts':dict(self.parts)};del bad['parts']['ENV-W-PLY-00-PIECE-01']
  with self.assertRaisesRegex(AssertionError,'never restore reference wood'):compose_wood(bad,self.data)
  pid='ENV-E-FRAME-RO1-SILL-SEG0';p=self.parts[pid];s=self.solids[pid];vertices=np.asarray(p['vertices']);selected=None
  for indices in p['triangles']:
   triangle=vertices[indices]
   if np.linalg.norm(np.cross(triangle[1]-triangle[0],triangle[2]-triangle[0]))<1e-10:continue
   center=triangle.mean(0);tool=m.Manifold.cube([.03125*I]*3).translate((center-.015625*I).tolist());candidate=s-tool
   if amount(s^tool)>TOL and len([c for c in candidate.decompose() if c.volume()>TOL])==1:selected=candidate;break
  self.assertIsNotNone(selected);extra={'parts':dict(self.parts)};extra['parts'][pid]={**p,**mesh(selected)};after=compose_wood(extra,self.data);self.assertLessEqual(diff(selected,shape(after['parts'][pid])),TOL,'A later current cavity must not be filled from a saved reference')
 def test_actual_hardware_identities_and_no_inferred_causal_exemptions(self):
  value=hardware(self.data);self.assertEqual(len(value['parts']),9415);self.assertEqual(len(value['retainedIds']),7434);self.assertEqual(len(value['newIds']),1981);self.assertEqual(len(value['prototypes']),12)
  for p in value['parts']:
   # TIMESTAMP START 2026-11-05T22:31:25+00:00 | REVISION R000069
   self.assertTrue(p['is_fastener']);self.assertIn(p['fastenerKind'],['nail','screw']);self.assertTrue(p['receiverIds']);self.assertTrue(p['withdrawalReceiverIds']);self.assertTrue(set(p['withdrawalReceiverIds'])<=set(p['receiverIds']));matrix=np.asarray(p['mesh_instance']['transform']);self.assertLess(np.max(abs(matrix[:,:3].T@matrix[:,:3]-np.eye(3))),1e-10,p['id']);self.assertAlmostEqual(np.linalg.det(matrix[:,:3]),1.,places=10)
   for later in p['removalPrerequisites']:self.assertFalse(permitted_withdrawal(p,{'id':later,'material':'wood'},p['withdrawal_direction']))
   # TIMESTAMP END 2026-11-05T22:31:25+00:00 | REVISION R000069
  with self.assertRaisesRegex(AssertionError,'Closure default source changed'):verify_default(self.data,read_source=lambda path:(ROOT/path).read_bytes()+b'\n' if path=='src/top-entry-proposed-model.json' else (ROOT/path).read_bytes())
if __name__=='__main__':unittest.main()
# TIMESTAMP END 2026-11-05T21:51:55+00:00 | REVISION R000068
