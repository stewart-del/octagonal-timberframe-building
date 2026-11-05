# TIMESTAMP START 2026-11-05T19:06:47+00:00 | REVISION R000061
"""Hash-bound physical cupola roof, original stock and separate causal nails.

The fixed authored field forms are preserved as source geometry. Only actual
new drip-edge metal bores are derived here; no old bored wood is substituted.
Dynamic retiling and full-building motion retain their separate gates.
"""
from pathlib import Path
import base64,copy,gzip,hashlib,json
import numpy as np
from audit_revised_joinery import native_solid
from audit_cavity_fit import inspect_mesh
from cupola_joinery_recipe import native_record
from floor_surface_normalization import normalize_one
ROOT=Path(__file__).resolve().parents[1];FIXTURE=ROOT/'scripts/fixtures/cupola-roof-inputs.json.gz';I=.0254;TOL=1e-6*I**3

def inputs():
 data=json.loads(gzip.decompress(FIXTURE.read_bytes()));assert data['schema']=='frozen-physical-cupola-roof-1';files={}
 for name,row in data['files'].items():
  raw=base64.b64decode(row['content'],validate=True) if row['encoding']=='base64' else row['content'].encode();assert hashlib.sha256(raw).hexdigest()==row['sha256'],('Changed frozen cupola roof source',name);files[name]=raw
 assert hashlib.sha256(files['manifest.json']).hexdigest()==data['manifest_sha256'];return files

def decoded(files,name):
 raw=files[name];return json.loads(gzip.decompress(raw) if name.endswith('.gz') else raw)
def basis(n):
 n=np.asarray(n,float);n/=np.linalg.norm(n);x=np.cross(n,np.eye(3)[np.argmin(abs(n))]);x/=np.linalg.norm(x);return np.column_stack([x,np.cross(n,x),n])
def overlaps(a,b):return bool(np.all(a[:3]<b[3:]+1e-10) and np.all(b[:3]<a[3:]+1e-10))
def build(model_path=None):
 model_path=Path(model_path or ROOT/'src/model-data.json');files=inputs();manifest=decoded(files,'manifest.json');guard=next(r for r in manifest['input_guards'] if r['path']=='inputs/current-model-data.json');assert hashlib.sha256(model_path.read_bytes()).hexdigest()==guard['sha256'],'Changed primary default requires regenerated cupola roof'
 model=json.loads(model_path.read_text());primary={p['id']:p for p in model['parts'] if p.get('is_timber')};wood=decoded(files,manifest['assets']['physical-wood']['path'])['parts'];copper=decoded(files,manifest['assets']['physical-copper']['path'])['parts'];aux=decoded(files,manifest['assets']['aux-instances']['path'])['instances'];roof8d=decoded(files,manifest['assets']['roof8d-instances']['path'])['instances'];auxprotos=decoded(files,manifest['assets']['aux-prototypes']['path'])['prototypes'];proto8=decoded(files,manifest['assets']['roof8d-prototype']['path'])['prototypes']['FLOOR-8DHDGPT'];prototypes={};tools={}
 for code,row in auxprotos.items():prototypes['CUP-'+code]=row['metal'];tools['CUP-'+code]=row['bore_tool']
 prototypes['CUP-8DHDGPT']=proto8
 # The cutting prototype has its own explicit identity; never use a shaft-only
 # approximation in place of the real pointed/head cutter.
 cutter_data=decoded(files,manifest['assets']['roof8d-cutting-prototype']['path']);tools['CUP-8DHDGPT']=next(iter(cutter_data['prototypes'].values()))
 fields=[p for p in decoded(files,'inputs/roof-physical-layers-candidate/cupola-membrane-checkpoint.json.gz')['parts'] if p['id'].startswith('VDSA-CUP')]
 starters=[p for p in decoded(files,'inputs/roof-eave-starter-candidate/parts.json')['parts'] if 'CUP' in p['id']]
 drips=[p for p in decoded(files,'inputs/roof-edge-flashing-candidate/drip-parts.json')['parts'] if 'CUP' in p['id']]
 driprows=[p for p in decoded(files,'inputs/roof-edge-flashing-candidate/drip-nails-rays.json')['nails'] if 'CUP' in p['id']]
 assert (len(wood),len(copper),len(aux),len(roof8d),len(fields),len(starters),len(drips),len(driprows))==(16,57,104,128,16,16,8,40)
 metadata=decoded(files,manifest['assets']['Exterior-material-semantic-update']['path'])['part_metadata_updates'];parts=[]
 for original in wood+copper+fields+starters:
  p=copy.deepcopy(original);pid=p['id'];p.setdefault('name',pid);p['constructionPhase']='Cupola roof';p['capacity_verified']=False
  if pid.startswith('VDSA-'):p['material']=p['material']+' membrane'
  if pid.startswith('CUP-ROOF-DECK-'):p.update(copy.deepcopy(metadata[pid]));p['publishedDimensionsIn']=[47.875,95.875,.703]
  if pid.startswith('CUP-COPPER-BATTEN-') and not pid.startswith('CUP-COPPER-BATTEN-CAP-'):p.update(stockSectionIn=[1.5,1.5],stockLengthIn=next(r['length_in'] for r in decoded(files,manifest['assets']['copper-and-batten-stock']['path'])['stock'] if r.get('installed_id')==pid),stock_frame={'axis':(basis([-np.cos(int(pid.rsplit('-',1)[1])*np.pi/4),1/3,np.sin(int(pid.rsplit('-',1)[1])*np.pi/4)])[:,2]).tolist()})
  parts.append(p)
 nails=[]
 for original in aux+roof8d:
  p=copy.deepcopy(original);p['name']='Cupola roof nail '+p['id'];p['parentId']=p.get('parentId',p.get('owner'));isaux=p['id'] in set(manifest['replace_aux_same_id_104']);key='CUP-'+p['sku'] if isaux else 'CUP-8DHDGPT';p['mesh_instance']={'prototype':key,'transform':p['mesh_instance']['transform']};p['material']='Type316 stainless steel' if isaux else p['fastenerSpec']['material'];p['fastenerKind']='nail';p['is_fastener']=True;p['intentionalFastenerPenetration']=True;p['withdrawalReceiverIds']=list(p.get('causalReceivingIds',p['receiverIds']));p['removalPrerequisites']=list(p.get('extractionBlockedBy',[]))
  if isaux:
   p['fastenerSpec']={'manufacturer':'Simpson Strong-Tie','partNumber':p['sku'],'lengthIn':p['length_in'],'shankDiameterIn':p['diameter_in'],'headDiameterIn':p['head_diameter_in'],'material':p['material'],'geometryProfile':auxprotos[p['sku']]['profile_scope'],'procurementStatus':p.get('procurement_scope')};p['withdrawal_direction']=p['outward_normal'];p['withdrawal_distance_m']=(p['length_in']+1)*I
  nails.append(p)
 for row in driprows:
  normal=np.asarray(row['outward_normal']);rotation=basis(normal)@basis([0,0,1]).T;transform=np.column_stack([rotation,np.asarray(row['head_in'])*I]);nails.append({'id':row['id'],'name':'Cupola drip-edge nail '+row['id'],'parentId':row['owner'],'material':'Type316 stainless steel','is_fastener':True,'fastenerKind':'nail','intentionalFastenerPenetration':True,'mesh_instance':{'prototype':'CUP-T311ARN1','transform':transform.tolist()},'receiverIds':list(row['receiver_ids']),'withdrawalReceiverIds':list(row['receiver_ids']),'withdrawal_direction':normal.tolist(),'withdrawal_distance_m':(row['length_in']+1)*I,'fastenerSpec':{'manufacturer':'Simpson Strong-Tie','partNumber':'T311ARN1','lengthIn':1.25,'shankDiameterIn':.120,'headDiameterIn':.34375,'material':'Type316 stainless steel','geometryProfile':auxprotos['T311ARN1']['profile_scope']}})
 # Real metal holes, including cupola sheathing nail heads meeting the drip.
 native_tools={key:native_solid(p) for key,p in tools.items()};placed_tools=[]
 for nail in nails:
  matrix=np.asarray(nail['mesh_instance']['transform']);tool=native_tools[nail['mesh_instance']['prototype']].transform(matrix.tolist());placed_tools.append((nail['id'],tool,np.asarray(tool.bounding_box())))
 receipts=[]
 for original in drips:
  p=copy.deepcopy(original);before=native_solid(p);shape=before;box=np.asarray(before.bounding_box());count=0
  for pid,tool,tbox in placed_tools:
   if overlaps(box,tbox) and max(0.,float((before^tool).volume()))>1e-12*I**3:shape=shape-tool;count+=1
  normalization=None
  try:record=native_record(shape,single=True)
  except AssertionError:
   mm=shape.to_mesh64();raw={**p,'vertices':np.asarray(mm.vert_properties)[:,:3].tolist(),'triangles':np.asarray(mm.tri_verts).tolist()};record,normalization=normalize_one(raw,inspect_mesh(np.asarray(raw['vertices']),np.asarray(raw['triangles'],np.uint64),True))
  p.update(record);p.update(name='Cupola copper drip edge',freshNailHoleCount=count);parts.append(p);receipts.append({'id':p['id'],'actual_hole_tools':count,'removed_volume_m3':max(0.,float((before-native_solid(p)).volume())),'boundary_normalization':normalization})
 # Keep static flexible contacts distinct from actual earlier embed receivers.
 targets={p['id']:native_solid(p) for p in [*primary.values(),*parts] if 'copper' not in p.get('material','').lower()};bounds={pid:np.asarray(s.bounding_box()) for pid,s in targets.items()};flex=set(p['id'] for p in fields+starters)
 for nail in nails:
  matrix=np.asarray(nail['mesh_instance']['transform']);body=native_solid(prototypes[nail['mesh_instance']['prototype']]).transform(matrix.tolist());box=np.asarray(body.bounding_box());contacts=[]
  for pid,target in targets.items():
   if overlaps(box,bounds[pid]) and max(0.,float((body^target).volume()))>TOL:contacts.append(pid)
  old=set(nail['receiverIds']);nail['receiverIds']=sorted(old|set(contacts));later=[]
  for pid in contacts:
   if pid not in flex:continue
   if nail['id'].startswith('CUP-ROOF-DECK-8D-') or (nail['id'].startswith('CU-DRIP-') and pid in {p['id'] for p in fields}):later.append(pid)
   else:nail['withdrawalReceiverIds'].append(pid)
  nail['withdrawalReceiverIds']=sorted(set(nail['withdrawalReceiverIds']));nail['removalPrerequisites']=sorted(set(nail.get('removalPrerequisites',[])+later));parts.append(nail)
 assert len(parts)==385 and len({p['id'] for p in parts})==385
 return {'parts':parts,'prototypes':prototypes,'removeIds':manifest['retire_only_old_roof_screw_ids'],'replaceIds':manifest['replace_same_id_physical_parts']+manifest['replace_aux_same_id_104'],'stock':decoded(files,manifest['assets']['copper-and-batten-stock']['path']),'report':{'status':'PASS','scope':'Frozen authored physical roof composition and fresh real drip metal holes. Full assembled interference, stock, source-bound construction motion and parameter retiling remain independent checks.','fixture_sha256':hashlib.sha256(FIXTURE.read_bytes()).hexdigest(),'generator_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'manifest_sha256':hashlib.sha256(files['manifest.json']).hexdigest(),'model_sha256':guard['sha256'],'parts':385,'physical_copper':65,'roof_deck_nails':128,'aux_batten_cleat_apex_nails':104,'drip_nails':40,'roof_deck_panels':8,'ceiling_WSV_untouched':128,'drip_hole_composition':receipts}}
# TIMESTAMP END 2026-11-05T19:06:47+00:00 | REVISION R000061
