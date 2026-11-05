# TIMESTAMP START 2026-11-05T16:48:19+00:00 | REVISION R000054
"""Real bought grates and custom retention, with cast and drilled solids distinct."""
from pathlib import Path
import copy,gzip,hashlib,json
import numpy as np
from audit_revised_joinery import native_solid
from cupola_joinery_recipe import native_record
from audit_cavity_fit import inspect_mesh
from floor_surface_normalization import normalize_one
ROOT=Path(__file__).resolve().parents[1]
FIXTURE=ROOT/'scripts/fixtures/drain-grate-inputs.json.gz'
TOL=1e-6*.0254**3

def inputs():
 data=json.loads(gzip.decompress(FIXTURE.read_bytes()));assert data['schema']=='frozen-real-grate-inputs-1';result={}
 for key,record in data['files'].items():
  assert hashlib.sha256(record['content'].encode()).hexdigest()==record['sha256'],('Changed grate artifact',key)
  result[key]=json.loads(record['content'])
 return result

def difference(a,b):return max(0.,float((a-b).volume()))+max(0.,float((b-a).volume()))
def build(cast_parts):
 data=inputs();patch=data['patch'];cast={p['id']:p for p in cast_parts};expected={p['id']:p for p in data['cast']['parts']};targets={p['id']:p for p in patch['pan_overlays']};parts=[];proofs=[];cutters=[native_solid(r['tool']) for r in patch['pan_cutting_tools'] if r['stage'].startswith('POST_CURE_')]
 assert len(cutters)==52,'Sixteen drill tools and thirty-six accessible seat milling tools are required'
 for pid,reference in expected.items():
  assert pid in cast,('Missing fresh cast pan member',pid)
  fresh=cast[pid];before=native_solid(fresh);input_error=difference(before,native_solid(reference));assert input_error<=TOL,(pid,'Refusing to replace changed cast geometry',input_error)
  after=before
  for row in data['sill_anchors']['tools'].get(pid,[]):after=after-native_solid(row['tool'])
  for tool in cutters:after=after-tool
  normalization=None
  try:record=native_record(after,single=True)
  except AssertionError:
   mesh=after.to_mesh64();raw={**fresh,'vertices':np.asarray(mesh.vert_properties)[:,:3].tolist(),'triangles':np.asarray(mesh.tri_verts).tolist()};audit=inspect_mesh(np.asarray(raw['vertices']),np.asarray(raw['triangles'],np.uint64),True);record,normalization=normalize_one(raw,audit)
  occupied=native_solid(record);removed=max(0.,float((before-occupied).volume()));error=difference(occupied,native_solid(targets[pid]));assert error<=TOL,(pid,'Declared post-cure tools do not reproduce independently checked pan',error)
  record['volume_m3']=float(occupied.volume())
  assert max(0.,float((occupied-before).volume()))<=TOL,(pid,'Drilling added concrete')
  parts.append({**copy.deepcopy(fresh),**record,'replaceExisting':True,'castVolumeM3':before.volume(),'postCureRemovedM3':removed,'constructionGeometryStages':{'cast':{'fixtureEntry':'cast','partId':pid},'drilled':'Current final occupied geometry'}})
  proofs.append({'id':pid,'input_difference_m3':input_error,'readback_difference_m3':error,'cast_volume_m3':before.volume(),'post_cure_removed_m3':removed,'boundary_normalization':normalization})
 for part in patch['add_parts'].values():
  p=copy.deepcopy(part)
  if p['id'].startswith('DRAIN-NDS253CI-'):
   p['color']=[.16,.17,.17];p['publishedPurchasedWeightLb']=7.5;p['quantityBasis']='One real NDS253CI purchased grate unit; occupied envelope does not reproduce undocumented wave/rib factory geometry.'
  else:p['color']=[.58,.61,.63]
  parts.append(p)
 for part in patch['instances']:
  p=copy.deepcopy(part);p['color']=[.58,.61,.63];p.setdefault('fastenerKind','screw' if 'THD' in p['mesh_instance']['prototype'] else 'other hardware');p['intentionalFastenerPenetration']=False;p.setdefault('withdrawalReceiverIds',p.get('receiverIds',[]));parts.append(p)
 ids=[p['id'] for p in parts];assert len(ids)==len(set(ids));assert sum(p['id'].startswith('DRAIN-NDS253CI-') for p in parts)==4
 cast_volume=sum(p['cast_volume_m3'] for p in proofs);assert abs(cast_volume-1.234044306)<1e-9,('Cast quantity changed',cast_volume)
 return {'parts':parts,'prototypes':patch['prototypes'],'removeIds':patch['removeIds'],'stock':patch['stock'],'takeoff':data['takeoff'],'maintenanceRelease':patch['maintenanceRelease'],'report':{'status':'PASS','scope':'Exact cast-input compatibility, fresh declared post-cure concrete holes and real grate identity only; final whole-building static and construction routes remain separately required.','fixture_sha256':hashlib.sha256(FIXTURE.read_bytes()).hexdigest(),'generator_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'host_composition':proofs,'purchased_grates':4,'published_grate_weight_lb_each':7.5,'cast_pan_m3':cast_volume,'cast_pan_yd3':cast_volume/.764554857984,'existing_sill_anchor_count':len(data['sill_anchors']['schedule']),'all_post_cure_removed_m3':sum(p['post_cure_removed_m3'] for p in proofs),'added_parts_and_hardware':len(parts)-len(proofs),'capacities_qualified':False}}
# TIMESTAMP END 2026-11-05T16:48:19+00:00 | REVISION R000054
