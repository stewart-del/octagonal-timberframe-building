# TIMESTAMP START 2026-11-05T22:52:56+00:00 | REVISION R000070
"""Real roll-sized roof barrier pieces and negative-only cupola GP seats.

Original recipe inputs remain immutable evidence. Current primary timbers,
roof panels and cupola wall recipients are never replaced by those snapshots.
"""
from pathlib import Path,PurePosixPath
from functools import lru_cache
import copy,gzip,hashlib,io,json,tarfile
import numpy as np
from audit_revised_joinery import native_solid
from audit_cavity_fit import inspect_mesh
from cupola_joinery_recipe import native_record,I,TOL,amount,diff
from floor_surface_normalization import normalize_one
ROOT=Path(__file__).resolve().parents[1];FIXTURE=ROOT/'scripts/fixtures/main-roof-membrane-inputs.json'
ARCHIVE_SHA='0e24b13c46182b9465e72dfea808b4d0207202709cc169dd19216af4c9a4dd9d'
V1_SHA='7a335e4641f739c8ae7d2c29ce97237b8ab30c8914b120fbd701b3cfcc958559'
V2_SHA='15821ddaca1e9f576932bae4e15a5130d3aee1c166b35160776a105af25156db'
V1='main-roof-SA-terminal-v1';V2='main-roof-SA-terminal-v2'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def decode(raw,name):return json.loads(gzip.decompress(raw) if name.endswith('.gz') else raw)
@lru_cache(maxsize=1)
def inputs():
 descriptor=json.loads(FIXTURE.read_text());assert descriptor['schema']=='octagon-frozen-main-roof-membrane-1';path=PurePosixPath(descriptor['archive']);assert len(path.parts)==1 and not path.is_absolute();raw=(FIXTURE.parent/str(path)).read_bytes();assert len(raw)==descriptor['bytes'] and sha(raw)==descriptor['sha256']==ARCHIVE_SHA,'Roof membrane source archive changed';files={}
 with tarfile.open(fileobj=io.BytesIO(raw),mode='r|gz') as archive:
  for member in archive:
   name=PurePosixPath(member.name);assert not name.is_absolute() and '..' not in name.parts and name.parts[0] in [V1,V2,'main-roof-SA-owner-evidence'],'Unsafe roof membrane source entry'
   if member.isdir():continue
   assert str(name) not in files,'Repeated roof membrane source entry'
   if member.islnk():
    target=PurePosixPath(member.linkname);assert not target.is_absolute() and '..' not in target.parts and str(target) in files;files[str(name)]=files[str(target)]
   else:assert member.isfile(),'No source symbolic links or special entries';files[str(name)]=archive.extractfile(member).read()
 assert sha(files[V1+'/manifest.json'])==descriptor['v1ManifestSha256']==V1_SHA and sha(files[V2+'/manifest.json'])==descriptor['v2ManifestSha256']==V2_SHA
 for name,expected in descriptor['ownerEvidence'].items():assert sha(files['main-roof-SA-owner-evidence/'+name])==expected,'Corrected reproduction receipt changed'
 manifests={key:json.loads(files[key+'/manifest.json']) for key in [V1,V2]}
 for key,manifest in manifests.items():
  for row in [*manifest['assets'].values(),*manifest['frozen_recipe_import_closure'].values(),*manifest.get('input_guards',[])]:assert sha(files[key+'/'+row['path']])==row['sha256'],('Frozen roof membrane input changed',key,row['path'])
  recipe=manifest.get('reproducer',manifest.get('reproduction_wrapper'));assert sha(files[key+'/'+recipe])==manifest.get('reproducer_sha256',manifest.get('reproduction_wrapper_sha256'))
 v1,v2=manifests[V1],manifests[V2];assert v2['depends_on_immutable_v1']['manifest_sha256']==V1_SHA
 asset=lambda name:decode(files[V2+'/'+v2['assets'][name]['path']],v2['assets'][name]['path'])
 semantic=decode(files[V1+'/'+v1['assets']['Exterior-roof-ply-material-diff']['path']],v1['assets']['Exterior-roof-ply-material-diff']['path'])
 return {'v1':v1,'v2':v2,'parts':asset('actual-85-SA')['parts'],'gpTools':asset('same-eight-NEW-GP-tools')['cutting_tools_by_host'],'gpReference':asset('GP-readback-reference-only')['parts'],'stock':asset('same-five-roll-cut-plan'),'proof':asset('physical-proof'),'plywoodMetadata':semantic['part_metadata_updates'],'retireIds':v1['retire_or_replace_exact_ids']}
def verify_default(data=None,*,read_source=None):
 data=data or inputs();read_source=read_source or (lambda name:(ROOT/name).read_bytes());model=next(row for row in data['v1']['input_guards'] if row['path']=='inputs/current-model-data.json');assert sha(read_source('src/model-data.json'))==model['sha256'],'Changed primary default requires regenerated roof membranes'
 payload=json.loads(gzip.decompress(read_source('scripts/fixtures/architectural-inputs.json.gz')))['files'];guards={row['path']:row['sha256'] for row in data['v1']['input_guards']}
 for key,name in [('main_deck','roof-sheathing-curb-candidate/roof-sheathing-parts.json'),('main_backing','roof-sheathing-curb-candidate/roof-blocking-candidate-patch.json'),('cupola_wood','cupola-copper-candidate/roof-raw-wood.json')]:assert sha(payload[key]['content'].encode())==payload[key]['content_sha256']==guards['inputs/'+name],('Changed roof substrate requires regenerated membranes',key)
 return True
def compose_gp(current,data=None):
 """Cut only current new GP; reject missing or differently split recipients."""
 data=data or inputs();verify_default(data);parts=dict(current);receipts=[]
 for pid,tool in data['gpTools'].items():
  assert pid.startswith('BOX-CUP-') and pid.endswith('-WALL-PLY') and pid in parts,('Missing current new GP recipient',pid);p=parts[pid];before=native_solid(p);cutter=native_solid(tool);after=before-cutter;reference=native_solid(data['gpReference'][pid]);assert amount(after-reference)<=TOL,('Cupola GP exceeds audited roof-barrier seat',pid)
  if amount(before^cutter)<=TOL:record={key:p[key] for key in ['vertices','triangles']};record['volume_m3']=float(before.volume())
  else:
   try:record=native_record(after,single=True)
   except AssertionError:
    raw=after.to_mesh64();candidate={**p,'vertices':np.asarray(raw.vert_properties)[:,:3].tolist(),'triangles':np.asarray(raw.tri_verts).tolist()};record,_=normalize_one(candidate,inspect_mesh(np.asarray(candidate['vertices']),np.asarray(candidate['triangles'],np.uint64),True)['failures'])
  imported=native_solid(record);assert amount(imported-before)<=TOL and diff(imported,after)<=TOL and diff(imported,imported-cutter)<=TOL,('Serialized GP seat changes undeclared material',pid)
  assert inspect_mesh(np.asarray(record['vertices']),np.asarray(record['triangles'],np.uint64),True)['status']=='PASS',('Invalid current GP seat boundary',pid)
  parts[pid]={**p,**record,'roofBarrierNegativeSeatApplied':True};receipts.append({'id':pid,'removedM3':amount(before-imported),'secondApplicationDifferenceM3':diff(imported,imported-cutter),'currentLaterVoidsPreserved':True,'referenceWasNotSubstituted':True})
 return {'parts':parts,'receipts':receipts}
def build(data=None):
 data=data or inputs();verify_default(data);parts=copy.deepcopy(data['parts']);plan=data['stock'];ids={p['id'] for p in parts};assert len(parts)==len(ids)==85 and plan['physical_SA_parts']==85 and len(plan['cuts'])==73 and plan['roll_count']==5 and not plan['missing_stock_bindings'] and not plan['rectangle_overlap_failures'];assert set(plan['part_to_cut'])==ids
 for p in parts:
  cut=next(row for row in plan['cuts'] if row['id']==plan['part_to_cut'][p['id']]);assert p['id'] in cut['installed_ids'];p.update(name='Individual self-adhered roof ice-barrier sheet '+p['id'],parentStockId=cut['id'],stock_parent_id=cut['id'],parentRollId=cut['parentRollId'],stockWidthIn=cut['blank_width_in'],stockLengthIn=cut['blank_length_in'],stockSectionIn=[cut['blank_width_in'],data['v2']['roof_product']['nominal_gauge_in']],product=copy.deepcopy(data['v2']['roof_product']));assert p['stockWidthIn']<=57 and p['stockLengthIn']<=960
 return {'parts':parts,'stock':copy.deepcopy(plan),'gpTools':data['gpTools'],'plywoodMetadata':copy.deepcopy(data['plywoodMetadata']),'retireIds':data['retireIds'],'report':{'status':'BOUNDED_AUTHORED_DEFAULT_GEOMETRY_ONLY','parts':85,'rolls':5,'cutBlanks':73,'generatorSha256':sha(Path(__file__).read_bytes()),'fixtureArchiveSha256':ARCHIVE_SHA,'v1ManifestSha256':V1_SHA,'v2ManifestSha256':V2_SHA,'requiresEnclosureBootDeltaSha256':data['v2']['source_binding']['boot_delta_sha256'],'enclosureBootIntegrated':False,'historicalCombinedProof':data['proof'],'installationOrder':data['v1']['installation_order'],'limits':data['v2']['scope']+['Corrected roof hardware, ventilation mat, felt, copper, cedar seating and whole-scene continuous motion remain independent checks.']}}
# TIMESTAMP END 2026-11-05T22:52:56+00:00 | REVISION R000070
