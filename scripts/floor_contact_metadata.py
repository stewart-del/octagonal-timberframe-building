# TIMESTAMP START 2026-11-06T02:53:16+00:00 | REVISION R000082
"""Exact source-bound recipients for wall fasteners through earlier floor layers."""
from pathlib import Path
from functools import lru_cache
import copy,gzip,hashlib,json,math
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
FIXTURE=ROOT/'scripts/fixtures/floor-contact-metadata.json.gz'
FIXTURE_SHA='ade7b983bc517ff0bf310342acfeb013d4aa88a67aa7224bc61e5a14bd3e0dc5'

def digest(value):
 def numbers(item):
  if isinstance(item,bool):return item
  if isinstance(item,(int,float)):
   result=float(item);assert math.isfinite(result);return 0.0 if result==0 else result
  if isinstance(item,list):return [numbers(child)for child in item]
  if isinstance(item,dict):return {key:numbers(child)for key,child in item.items()}
  return item
 return hashlib.sha256(json.dumps(numbers(value),sort_keys=True,separators=(',',':')).encode()).hexdigest()

def geometry_hash(part):
 """Bind exact occupied coordinates and topology independently of JSON numbers."""
 vertices=np.asarray(part['vertices'],dtype='<f8').copy();vertices[vertices==0]=0
 triangles=np.asarray(part['triangles'],dtype='<u8')
 return hashlib.sha256(vertices.tobytes()+triangles.tobytes()).hexdigest()

def descriptor(part):
 result={key:part[key]for key in ['parentId','mesh_instance','withdrawal_direction','withdrawal_distance_m']}
 result['fastenerSpec']=part.get('fastenerSpec')or part['fastener_spec']
 return result

@lru_cache(maxsize=1)
def inputs():
 from closure_core_parts import MANIFEST_SHA as CORE_SHA,CAUSAL_DELTA_SHA
 from floor_closure_parts import inputs as floor_inputs,MANIFEST_SHA as FLOOR_SHA
 raw=FIXTURE.read_bytes();assert hashlib.sha256(raw).hexdigest()==FIXTURE_SHA,'Floor contact fixture changed';data=json.loads(gzip.decompress(raw));assert data['schema']=='octagon-current-floor-to-wall-fastener-contacts-1'
 assert data['frozenFloorManifestSha256']==FLOOR_SHA and data['frozenCoreManifestSha256']==CORE_SHA and data['frozenCoreCausalSha256']==CAUSAL_DELTA_SHA,'Floor contact source family changed'
 floor=floor_inputs();order=floor['filmsGapAndAdditionalNegativeTools']['assemblyOrder'];assert data['floorAssemblyOrder']==order and digest(order)==data['floorAssemblyOrderSha256'],'Floor before wall installation order changed'
 assert len(data['positiveNativeContactReceipts'])==688 and len(data['fasteners'])==446 and len(data['receivers'])==59
 assert all(row['nativeOverlapIn3']>data['unchangedToleranceIn3']==1e-6 for row in data['positiveNativeContactReceipts'])
 return data

def apply(parts,receivers,prototypes,data=None):
 """Append only explicit contacts after checking every current source actor."""
 data=data or inputs();lookup={part['id']:part for part in parts};assert len(lookup)==len(parts),'Duplicate wall fastener identity';assert set(data['fasteners'])<=set(lookup),'Missing wall fastener contact source'
 for pid,expected in data['prototypes'].items():
  assert pid in prototypes and geometry_hash(prototypes[pid])==expected,('Wall fastener prototype changed',pid)
 for rid,row in data['receivers'].items():
  assert rid in receivers and geometry_hash(receivers[rid])==row['geometrySha256'] and receivers[rid]['material']==row['material'],('Floor contact receiver changed',rid)
 result=[]
 for part in parts:
  row=data['fasteners'].get(part['id'])
  if row is None:result.append(part);continue
  actual=descriptor(part);assert actual==row['sourceDescriptor']and digest(actual)==row['sourceDescriptorSha256'],('Wall fastener pose or product changed',part['id'])
  assert set(row['sourceReceiverIds'])<=set(part['receiverIds']),'Existing wall recipients removed'
  earlier=set(row['earlierReceiverIds']);assert earlier<=set(data['receivers'])and not earlier&set(part.get('removalPrerequisites',[])),('Earlier floor contact conflicts with a later cover',part['id'])
  updated=copy.deepcopy(part);updated['receiverIds']=list(dict.fromkeys([*part['receiverIds'],*sorted(earlier)]));updated['withdrawalReceiverIds']=list(dict.fromkeys([*part['withdrawalReceiverIds'],*sorted(earlier)]));updated['assemblyPrerequisiteMaterialIds']=sorted(set(part.get('assemblyPrerequisiteMaterialIds',[]))|earlier);updated['assemblyPrerequisiteWoodIds']=sorted(set(part.get('assemblyPrerequisiteWoodIds',[]))|{rid for rid in earlier if data['receivers'][rid]['earlierMaterialKind']=='wood'});updated['floorEarlierReceiverIds']=sorted(earlier);updated['floorContactMetadataSha256']=FIXTURE_SHA;assert descriptor(updated)==actual;result.append(updated)
 return {'parts':result,'report':{'status':'EXACT_EARLIER_FLOOR_RECIPIENTS_APPLIED','fixtureSha256':FIXTURE_SHA,'fasteners':446,'contactRelations':688,'receivers':59,'productsPosesAndGeometryChanged':False,'laterCoverPrerequisitesChanged':False,'headSealQualification':'Any new piercing still needs its own physical sealed cover; weather sealing and full motion remain unqualified.','wholeBuildingReady':False}}
# TIMESTAMP END 2026-11-06T02:53:16+00:00 | REVISION R000082
