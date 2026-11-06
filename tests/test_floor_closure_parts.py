# TIMESTAMP START 2026-11-05T23:26:47+00:00 | REVISION R000072
"""Current 3mm cork is cut compositionally without filling earlier voids."""
from pathlib import Path
import copy,hashlib,json,os,sys,unittest
import numpy as np
import manifold3d as manifold
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
# TIMESTAMP START 2026-11-06T00:50:22+00:00 | REVISION R000076
from floor_closure_parts import inputs,cut_current_lower,I,TOL,diff,native_solid,amount
# TIMESTAMP END 2026-11-06T00:50:22+00:00 | REVISION R000076
from audit_cavity_fit import inspect_mesh
class FloorClosure(unittest.TestCase):
 def test_all_eight_current_cork_sheets_keep_thickness_and_are_idempotent(self):
  source=inputs()['corkImportBlocker'];before=copy.deepcopy(source);receipts=[]
  for pid,part in source['canonicalSourceParts_UNCHANGED'].items():
   with self.subTest(pid=pid):
    derived,receipt=cut_current_lower(part,source['requiredCutToolsInOrder']);self.assertEqual(receipt['status'],'PASS');self.assertEqual(inspect_mesh(np.asarray(derived['vertices']),np.asarray(derived['triangles'],np.uint64),True)['status'],'PASS');self.assertAlmostEqual(float(np.ptp(np.asarray(derived['vertices'])[:,1])),.003,places=12);self.assertEqual(derived['volumeM3'],derived['volume_m3']);self.assertLess(derived['volumeM3'],native_solid(part).volume());self.assertLessEqual(max(receipt['attempts'][-1][key] for key in ['worldDifferenceIn3','localDifferenceIn3','absoluteVolumeDeltaIn3','addedOutsideOriginalIn3']),1e-6)
    twice,second=cut_current_lower(derived,source['requiredCutToolsInOrder']);self.assertEqual(second['status'],'UNCHANGED_NO_MATERIAL_CONTACT');self.assertLessEqual(diff(native_solid(derived),native_solid(twice)),TOL);receipts.append(receipt)
  self.assertEqual(len(receipts),8);self.assertEqual(source,before);self.assertFalse(inputs()['manifest']['readyForCompleteImport'])
  if os.environ.get('FLOOR_CORK_REPORT'):Path(os.environ['FLOOR_CORK_REPORT']).write_text(json.dumps({'status':'PASS','scope':'Eight current cork seats only; not a complete floor or assembly proof','receipts':receipts},indent=2)+'\n')
 def test_current_extra_void_is_preserved(self):
  part=copy.deepcopy(inputs()['corkImportBlocker']['canonicalSourceParts_UNCHANGED']['FLOOR-CORK-00-00']);v=np.asarray(part['vertices']);centre=v.mean(0);probe=manifold.Manifold.cube([.01,.01,.01],True).translate(centre.tolist());original=native_solid(part);cut=original-probe;mesh=cut.to_mesh64();part.update(vertices=np.asarray(mesh.vert_properties)[:,:3].tolist(),triangles=np.asarray(mesh.tri_verts).tolist());derived,_=cut_current_lower(part,inputs()['corkImportBlocker']['requiredCutToolsInOrder']);self.assertLessEqual(abs((native_solid(derived)^probe).volume()),TOL);self.assertLess(native_solid(derived).volume(),original.volume())
 def test_cut_that_splits_a_current_actor_requires_new_identities(self):
  cube=manifold.Manifold.cube([1,1,1]);mesh=cube.to_mesh64();part={'id':'SOURCE','vertices':np.asarray(mesh.vert_properties)[:,:3].tolist(),'triangles':np.asarray(mesh.tri_verts).tolist(),'stock_frame':{'axis':[1,0,0],'width':[0,1,0],'depth':[0,0,1]}};tool=manifold.Manifold.cube([.1,2,2]).translate([.45,-.5,-.5]).to_mesh64();record={'vertices':np.asarray(tool.vert_properties)[:,:3].tolist(),'triangles':np.asarray(tool.tri_verts).tolist()}
  with self.assertRaisesRegex(AssertionError,'split a current actor'):cut_current_lower(part,[record])
# TIMESTAMP START 2026-11-06T00:50:22+00:00 | REVISION R000076
# Direct invocation is placed after all later integration test classes.
# TIMESTAMP END 2026-11-06T00:50:22+00:00 | REVISION R000076
# TIMESTAMP END 2026-11-05T23:26:47+00:00 | REVISION R000072
# TIMESTAMP START 2026-11-06T00:50:22+00:00 | REVISION R000076
class FloorEnvelopeIntegration(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  from closure_core_parts import inputs as core_inputs,compose_wood,compose_stock
  from main_roof_membrane_parts import compose_gp
  from prepare_architecture import load_inputs
  from floor_closure_parts import compose_envelope,stock_input_data
  raw,_=load_inputs();cls.data=inputs();cls.core=core_inputs();current=compose_wood({'parts':raw['wall_wood']['add_parts']},cls.core);del raw;cls.original=compose_gp(current['parts'])['parts'];cls.before=copy.deepcopy(cls.original);cls.composed=compose_envelope(cls.original,cls.data);cls.parts=cls.composed['parts'];cls.stock_source=stock_input_data(cls.core,cls.data);cls.stock=compose_stock(cls.parts,cls.stock_source)
 def test_actual_envelope_bodies_and_all_current_stock_partitions(self):
  self.assertEqual(self.original,self.before);self.assertEqual(len(self.parts),886);self.assertEqual(len(self.composed['report']['addedIds']),79);self.assertEqual(len(self.composed['report']['currentEnvelopeSeatReceipts']),177);self.assertEqual(self.stock['serializedWasteComposition']['status'],'PASS');self.assertEqual(self.stock['serializedWasteComposition']['stockCount'],488)
  for pid,p in self.parts.items():self.assertEqual(inspect_mesh(np.asarray(p['vertices']),np.asarray(p['triangles'],np.uint64),True)['status'],'PASS',pid)
  for row in self.stock['serializedWasteComposition']['receipts']:
   self.assertFalse(row['historicalProofInherited']);self.assertTrue(row['freshCurrentBlankAndChildrenReadback']);self.assertLessEqual(max(value for key,value in row.items()if key.endswith('M3')),TOL)
  if os.environ.get('FLOOR_AIR_REPORT'):Path(os.environ['FLOOR_AIR_REPORT']).write_text(json.dumps({'status':'PASS','scope':'Actual current envelope negative tools and488 stock rows only','composition':self.composed['report'],'stock':self.stock['serializedWasteComposition']},indent=2)+'\n')
 def test_second_composition_does_not_refill_current_material(self):
  from floor_closure_parts import compose_envelope
  second=compose_envelope(self.parts,self.data);self.assertEqual(second['report']['addedIds'],[])
  for pid in self.parts:self.assertLessEqual(diff(native_solid(self.parts[pid]),native_solid(second['parts'][pid])),TOL,pid)
 def test_all_films_and_source_bound_hardware_with_three_station_delta(self):
  from floor_closure_parts import films,hardware,three_station_inputs
  f=films(self.data);h=hardware(self.data);self.assertEqual(len(f),253);self.assertEqual(len(h['parts']),611);changed=three_station_inputs()['delta']['fastenerReplacements']
  for p in h['parts']:
   self.assertTrue(p['withdrawalReceiverIds']);self.assertFalse(set(p['withdrawalReceiverIds'])&set(p['removalPrerequisites']));self.assertTrue(set(p['withdrawalReceiverIds'])<=set(p['receiverIds']))
   if p['id']in changed:self.assertEqual(p['mesh_instance'],changed[p['id']]['replaceInstance']['mesh_instance'])
  bad={**self.data,'hardwareInstances':{**self.data['hardwareInstances'],'instances':list(self.data['hardwareInstances']['instances'])}};bad['hardwareInstances']['instances'][0]=copy.deepcopy(bad['hardwareInstances']['instances'][0]);bad['hardwareInstances']['instances'][0]['mesh_instance']['transform'][0][3]+=.001
  with self.assertRaisesRegex(AssertionError,'source pose changed'):hardware(bad)
# TIMESTAMP END 2026-11-06T00:50:22+00:00 | REVISION R000076
# TIMESTAMP START 2026-11-06T00:50:22+00:00 | REVISION R000076
@unittest.skipUnless(os.environ.get('FLOOR_SCENE'),'Requires an explicitly exported current composed scene')
class FloorCurrentSceneContacts(unittest.TestCase):
 def test_all_current_floor_closure_contacts_against_complete_assembled_context(self):
  from physical_data import occupied_part
  from physical_contacts import contact_kind
  from current_physical_scene import assert_current_sources,KERNEL_SOURCES
  from floor_closure_parts import films,hardware
  path=Path(os.environ['FLOOR_SCENE']);payload=json.loads(__import__('gzip').decompress(path.read_bytes()));assert_current_sources(KERNEL_SOURCES);assert_current_sources(payload['sources']);parts=payload['parts'];prototypes=payload['prototypes'];lookup={p['id']:p for p in parts};ids=list(lookup);source=inputs();selected=set(source['woodAndFirstNegativeTools']['add_parts'])|set(films(source))|{p['id']for p in hardware(source)['parts']}|set(source['corkImportBlocker']['canonicalSourceParts_UNCHANGED'])|set(source['footTools']['requiredSourceMinusSeatTools']);self.assertEqual(len(selected),955);self.assertTrue(selected<=set(lookup));bounds=[];native={}
  for p in parts:
   if p.get('mesh_instance'):
    instance=p['mesh_instance'];m=np.asarray(instance['transform']);v=np.asarray(prototypes[instance['prototype']]['vertices'])@m[:,:3].T+m[:,3]
   else:v=np.asarray(p['vertices'])
   bounds.append([v.min(0),v.max(0)])
  bounds=np.asarray(bounds);pairs=0;exemptions=0;failures=[];tested=set();largest=0.
  def solid(pid):
   if pid not in native:native[pid]=native_solid(occupied_part(lookup[pid],prototypes))
   return native[pid]
  for a in sorted(selected):
   index=ids.index(a);low,high=bounds[index];near=np.flatnonzero(np.all(bounds[:,1]>low,axis=1)&np.all(bounds[:,0]<high,axis=1))
   for j in near:
    b=ids[j];key=tuple(sorted((a,b)))
    if a==b or key in tested:continue
    tested.add(key)
    if contact_kind(lookup[a],lookup[b]):exemptions+=1;continue
    pairs+=1;overlap=amount(solid(a)^solid(b));largest=max(largest,overlap)
    if overlap>TOL:failures.append({'a':a,'b':b,'overlapIn3':overlap/I**3})
  report={'status':'PASS'if not failures else'BLOCKED','scope':'Contacts involving955 current floor closure actors against the complete assembled projection only; no whole-building route certificate','sceneSha256':hashlib.sha256(path.read_bytes()).hexdigest(),'physicalContextActors':len(parts),'selectedActors':len(selected),'nativeNonexemptPairs':pairs,'sourceDeclaredFastenerPairs':exemptions,'maximumNonexemptOverlapIn3':largest/I**3,'unchangedToleranceIn3':1e-6,'failures':failures}
  if os.environ.get('FLOOR_CONTACT_REPORT'):Path(os.environ['FLOOR_CONTACT_REPORT']).write_text(json.dumps(report,indent=2)+'\n')
  self.assertEqual(failures,[],repr(failures[:20]))
if __name__=='__main__':unittest.main()
# TIMESTAMP END 2026-11-06T00:50:22+00:00 | REVISION R000076
