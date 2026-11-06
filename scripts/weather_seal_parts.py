# TIMESTAMP START 2026-11-06T01:13:10+00:00 | REVISION R000079
"""Default air-seal candidates and negative-only current porch fascia seats.

Old film and wood snapshots are evidence only. Fresh owner integration must
check actual copper, wall wrap, current stock and complete physical contacts.
"""
from pathlib import Path
from functools import lru_cache
import base64,copy,gzip,hashlib,json,re
import numpy as np
from audit_cavity_fit import inspect_mesh
from audit_revised_joinery import native_solid
from cupola_joinery_recipe import I,TOL,amount,diff
from floor_closure_parts import cut_current_lower
ROOT=Path(__file__).resolve().parents[1];FIXTURE=ROOT/'scripts/fixtures/weather-seal-inputs.json.gz'
SOURCE_HASHES={'physical-eave-seals.json.gz':'5d009bf4d48da9ac419c1faae89dc78b015edff9252a7ce34017973642203f32','apex-rissan-transition.json.gz':'0a6bc727656c39d8758c600981da21738ac3d16197c09cbb51a97959b8d39f56','upper-porch-boot-delta-v2.json.gz':'ae33e73ac2f3833237c03fe91d715912b251defac3f94e20b7a06fc39b5bf7ce'}
def sha(raw):return hashlib.sha256(raw).hexdigest()
@lru_cache(maxsize=1)
def inputs():
 descriptor=json.loads(gzip.decompress(FIXTURE.read_bytes()));assert descriptor['schema']=='octagon-frozen-weather-seal-candidates-1'and set(descriptor['files'])==set(SOURCE_HASHES);result={}
 for name,row in descriptor['files'].items():
  raw=base64.b64decode(row['base64'],validate=True);assert len(raw)==row['bytes']and sha(raw)==row['sha256']==SOURCE_HASHES[name],('Changed weather candidate source',name);result[name]=json.loads(gzip.decompress(raw))
 return {'eave':result['physical-eave-seals.json.gz'],'apex':result['apex-rissan-transition.json.gz'],'boot':result['upper-porch-boot-delta-v2.json.gz']}
def verify_default(data=None):
 from closure_core_parts import inputs as core_inputs,verify_default as core_default
 data=data or inputs();core=core_inputs();core_default(core);assert data['boot']['sourceFrozen74SHA256']==SOURCE_HASHES['physical-eave-seals.json.gz'];original=next(row for row in core['manifest']['completeBundleFiles']if row['path']=='assets/closure-final-raw-wood-patch.json.gz');assert original['sha256']==data['boot']['sourceCoreSHA256'],'Weather seats refer to a different raw enclosure';return True
def build(data=None):
 data=data or inputs();verify_default(data);boot=data['boot'];parts=copy.deepcopy(data['eave']['parts']);assert len(parts)==74;trim_receipts=[]
 for pid,part in boot['replaceFrozenEaveSealParts'].items():
  assert pid in parts;before=native_solid(parts[pid]);after=native_solid(part);assert amount(after-before)<=TOL,('A field trim may not add material to an old strip',pid);trim_receipts.append({'id':pid,'removedIn3':amount(before-after)/I**3});parts[pid]=copy.deepcopy(part)
 for pid in boot['removeFrozenEaveSealIds']:assert pid in parts;del parts[pid]
 for family in [boot['add_parts'],data['apex']['parts']]:
  assert not set(parts)&set(family),'Weather pieces must retain distinct physical IDs';parts.update(copy.deepcopy(family))
 assert len(parts)==108
 for pid,p in parts.items():
  assert p['id']==pid;proof=inspect_mesh(np.asarray(p['vertices']),np.asarray(p['triangles'],np.uint64),True);assert proof['status']=='PASS',('Invalid actual weather strip boundary',pid,proof['failures']);product=p.get('product')
  if isinstance(product,str):
   code=re.search(r'#([^\s,]+)',product);p['productSpecification']={'manufacturer':'SIGA','name':product,'partNumber':code.group(1)if code else None,'installation':p.get('attachment','Site-fitted adhesive field fold; actual substrate acceptance required')}
  p['stock_parent_id']=p.get('stock_parent_id','WEATHER-TAPE-CUT-'+pid)
 return {'parts':list(parts.values()),'stockRecordOverrides_REFERENCE_ONLY':copy.deepcopy(boot['sourceStockRecordOverrides']),'report':{'status':'BOUNDED_DEFAULT_CANDIDATE_ONLY','individualParts':108,'originalEaveParts':74,'retiredEaveIds':boot['removeFrozenEaveSealIds'],'trimmedEaveParts':trim_receipts,'newPorchBootParts':20,'apexParts':16,'canonicalPrimaryChanged':False,'currentCopperAndWholeSceneReadbackRequired':True,'sources':SOURCE_HASHES,'generatorSha256':sha(Path(__file__).read_bytes()),'remainingInterfaces':data['eave']['remainingInterfaces']+boot['remainingInterfaces'],'wholeBuildingReady':False}}
def compose_fascia(current,data=None):
 data=data or inputs();verify_default(data);parts=dict(current);receipts=[]
 from closure_core_parts import inputs as core_inputs
 frame=np.asarray(next(row['basis']for row in core_inputs()['frames']['mainFaces']if row['face']=='W'));axes={key:frame[:,index].tolist()for index,key in enumerate(['axis','width','depth'])}
 for pid,tool in data['boot']['requiredAdditionalNewFasciaCutTools'].items():
  assert pid.startswith('BOX-MAIN-W-FASCIA-')and pid in parts,('No current new fascia recipient',pid);original=parts[pid];part,receipt=cut_current_lower({**original,'stock_frame':original.get('stock_frame',axes)},[tool])
  if 'stock_frame'not in original:part.pop('stock_frame',None)
  parts[pid]={**part,'porchAirBootNegativeSeatComposedOnCurrent':True};receipts.append(receipt)
 return {'parts':parts,'receipts':receipts,'oldFasciaSnapshotsSubstituted':False}
# TIMESTAMP END 2026-11-06T01:13:10+00:00 | REVISION R000079
