# TIMESTAMP START 2026-11-06T00:29:52+00:00 | REVISION R000075
"""Check declared removal vectors against actual headed fastener geometry.

This is a source contract before motion planning, not a replacement numeric
collision kernel. A rotation cannot retain a stale source withdrawal vector.
"""
import copy,hashlib,re
import numpy as np
METAL=re.compile(r'\b(steel|metal|stainless|galvanized|brass|bronze|copper)\b',re.I)
PRODUCT=re.compile(r'RSS|WSV|T\d+(?:SN|PCS|ARN)|\b(?:nail|screw)\b',re.I)
# These three exact source products contain a nominal shank cylinder only.
# Their immutable source construction puts the head at z=0 and drives into +Z:
# closure-core-terminal-v1/recipes/{finish_lap_siding,closure_hardware,
# export_closure_hardware_instances}.py. A cylinder cannot reveal head polarity;
# never infer that polarity from an instance's possibly stale declared vector.
NOMINAL_SHANK_CONVENTIONS={
 'd62ca23e0f71c4a5333e989b96266b779e2c2623435111678e618f42294aa5a7':('T8PCS10',[0,0,-1]),
 'cbd07b5fe3453b64522345b2727885ad7cfffce438a653b07968f888b205919a':('T8PCS10',[0,0,-1]),
 'e4ce706ef92672fc8149a5d7d854749615d9be5869654a47bbc323708abb486c':('T10A325CNJ',[0,0,-1])}
def geometry_hash(record):return hashlib.sha256(np.asarray(record['vertices'],dtype='<f8').tobytes()+np.asarray(record['triangles'],dtype='<u8').tobytes()).hexdigest()
def shaft_axis(record):
 vertices=np.asarray(record['vertices'],float);assert vertices.ndim==2 and vertices.shape[1]==3 and len(vertices)>=8 and np.isfinite(vertices).all(),'Missing finite physical fastener vertices';centred=vertices-vertices.mean(0);values,vectors=np.linalg.eigh(centred.T@centred);assert values[-1]>1.2*max(values[-2],1e-30),'Physical headed fastener has no unambiguous shaft axis';return centred,vectors[:,-1]
def fastener_kind(part):
 if not part.get('is_fastener') or not METAL.search(part.get('material','')):return None
 explicit=part.get('fastenerKind') or part.get('fastener_kind')
 if explicit:return explicit if explicit in ['nail','screw'] else None
 spec=part.get('fastenerSpec') or part.get('fastener_spec') or {};name=' '.join([str(part.get('name','')),str(spec.get('partNumber','')),str(spec.get('product',''))])
 if not PRODUCT.search(name):return None
 return 'nail' if re.search(r'\bnail\b|T\d+(?:SN|PCS|ARN)',name,re.I) else 'screw'
def physical_head_axis(record):
 centred,axis=shaft_axis(record);along=centred@axis;span=float(np.ptp(along));radius=np.linalg.norm(centred-along[:,None]*axis,axis=1);maximum=float(radius.max());assert span>0 and maximum>0;head=along[radius>=maximum*.98];head_centre=float(np.mean(head)-(along.min()+along.max())/2);assert abs(head_centre)>.05*span,'Physical head end is ambiguous';return axis*(1 if head_centre>0 else -1)
def prototype_withdrawal_axis(record):
 convention=NOMINAL_SHANK_CONVENTIONS.get(geometry_hash(record))
 if convention is None:return physical_head_axis(record),'modeled head'
 product,direction=convention;spec=record.get('fastenerSpec') or record.get('fastener_spec') or {};assert spec.get('partNumber')==product,'Nominal shank product does not match its source convention';_,axis=shaft_axis(record);expected=np.asarray(direction,float);assert abs(float(axis@expected))>1-1e-12,'Nominal cylinder physical shaft differs from source convention';return expected,'exact source-bound nominal shank convention; physical head profile unavailable'
def bridge_contact_metadata(parts):
 """Derive only the exact source-named GRK bridge screw wood recipient."""
 lookup={p['id']:p for p in parts};result=[];annotated=[]
 for original in parts:
  geometry=original.get('screw_geometry',{});spec=original.get('fastenerSpec',{});wood=geometry.get('receiver')
  if original.get('parentId')!='M-TMP' or not str(spec.get('partNumber','')).startswith('14221') or not wood:result.append(original);continue
  assert original.get('is_fastener') and METAL.search(original.get('material','')) and re.fullmatch(r'[CT][0-7]',wood) and wood in original['receiverIds'] and lookup[wood].get('is_timber'),'Bridge screw lacks an exact current source wood recipient';part=copy.copy(original);part.update(fastenerKind='screw',intentionalFastenerPenetration=True,withdrawalReceiverIds=[wood],physicalContactMetadataSource='Exact primary bridge screw_geometry.receiver; steel still requires its real clearance hole');result.append(part);annotated.append(part['id'])
 return result,annotated
def audit(parts,prototypes):
 cache={};checked=0;failures=[];counts={'instances':0,'directMeshes':0,'sourceBoundNominalShankInstances':0}
 for part in parts:
  kind=fastener_kind(part)
  if kind is None:continue
  checked+=1
  try:
   instance=part.get('mesh_instance')
   if instance:
    counts['instances']+=1;name=instance['prototype'];assert name in prototypes,'Missing physical product prototype'
    if name not in cache:cache[name]=prototype_withdrawal_axis(prototypes[name])
    local,evidence=cache[name];counts['sourceBoundNominalShankInstances']+=int(evidence.startswith('exact source-bound'));matrix=np.asarray(instance['transform'],float);assert matrix.shape==(3,4) and np.isfinite(matrix).all() and np.max(abs(matrix[:,:3].T@matrix[:,:3]-np.eye(3)))<1e-10 and abs(np.linalg.det(matrix[:,:3])-1)<1e-10,'Non-rigid physical fastener transform';expected=matrix[:,:3]@local
   else:counts['directMeshes']+=1;expected=physical_head_axis(part)
   expected=expected/np.linalg.norm(expected);declared=np.asarray(part.get('withdrawal_direction',[]),float);assert declared.shape==(3,) and np.isfinite(declared).all() and np.linalg.norm(declared)>0,'Missing finite declared withdrawal direction';declared=declared/np.linalg.norm(declared);error=float(np.linalg.norm(expected-declared));dot=float(np.clip(expected@declared,-1,1))
   if error>1e-8:failures.append({'id':part['id'],'reason':'Declared withdrawal differs from physical head/shaft direction','angularDifferenceDegrees':float(np.degrees(np.arccos(dot))),'expectedWithdrawalDirection':expected.tolist(),'declaredWithdrawalDirection':declared.tolist()})
  except (AssertionError,KeyError,ValueError,np.linalg.LinAlgError) as error:failures.append({'id':part['id'],'reason':str(error)})
 return {'status':'PASS' if not failures else 'BLOCKED','checkedHeadedFasteners':checked,'sharedPrototypeAxes':len(cache),**counts,'failures':failures,'directionSerializationErrorLimit':1e-8,'solidCollisionToleranceChanged':False,'scope':'Physical shaft direction and modeled-head or exact source-convention polarity only; nominal cylinders do not prove factory head geometry. Current receiving purchase, access, full sweeps and lifetimes require independent checks.'}
# TIMESTAMP END 2026-11-06T00:29:52+00:00 | REVISION R000075
