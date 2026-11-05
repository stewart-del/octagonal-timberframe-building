# TIMESTAMP START 2026-11-05T16:27:06+00:00 | REVISION R000053
"""Compose real porch roof stock/cuts into fresh fitted default frame members."""
from pathlib import Path
import copy,gzip,hashlib,json,re
import numpy as np
import manifold3d as m
from audit_revised_joinery import native_solid
from cupola_joinery_recipe import native_record
from physical_contacts import METAL
from floor_surface_normalization import regular_local
ROOT=Path(__file__).resolve().parents[1]
FIXTURE=ROOT/'scripts/fixtures/porch-roof-inputs.json.gz'
TOL=1e-6*.0254**3

def load_inputs():
 raw=FIXTURE.read_bytes();data=json.loads(gzip.decompress(raw));assert data['schema']=='source-bound-porch-roof-inputs-1';values={}
 for key,record in data['files'].items():
  assert hashlib.sha256(record['content'].encode()).hexdigest()==record['content_sha256'],('Porch input changed',key)
  values[key]=json.loads(record['content'])
 return values,hashlib.sha256(raw).hexdigest()
def diff(a,b):return max(0.,float((a-b).volume()))+max(0.,float((b-a).volume()))
def union(parts):return m.Manifold.batch_boolean(parts,m.OpType.Add) if parts else m.Manifold()
def build(original_parts):
 inputs,fixture_hash=load_inputs();patch=inputs['patch'];original={p['id']:p for p in original_parts};reference={p['id']:p for p in inputs['original_frame']['parts']};parts=[];proofs=[];prototypes={};joint_by_peg={j.get('peg_id'):j for j in inputs['fitted_joinery']['joints'] if j.get('peg_id')};stocks=inputs['stocks'];frames={r['id']:r['actual_stock_frame'] for r in inputs['frames']['records']}
 origin=np.asarray(inputs['layout']['origin']);tangent=np.asarray(inputs['layout']['tangent']);outward=np.asarray(inputs['layout']['outward']);basis=np.column_stack([tangent,[0.,1.,0.],outward])
 def local(record):
  return m.Manifold(m.Mesh64(np.array((np.asarray(record['vertices'])-origin)@basis/.0254,order='C'),np.array(record['triangles'],np.uint64,order='C')))
 def world(shape):return shape.transform(np.column_stack([basis*.0254,origin]).tolist())
 def enrich(p):
  p=copy.deepcopy(p);pid=p['id'];p.pop('faces',None);p.pop('edges',None)
  if pid in frames:p['stock_frame']=frames[pid]
  if pid in stocks:
   stock=stocks[pid];p['stockLengthIn']=stock['minimum_finished_blank_length_in'];p['stockSectionIn']=stock['actual_section_in'];p['stock_parent_id']=pid+'-STOCK';p['capacity_verified']=False
  if p.get('vertices'):
   points=np.asarray(p['vertices'])-origin;coordinates=np.column_stack([points@tangent,points[:,1],points@outward]);bounds=np.column_stack([coordinates.min(0),coordinates.max(0)]).flatten().tolist();p['localBounds']=bounds
  p.setdefault('name',pid);p.setdefault('material','wood');p['mudroomRoof']=True
  if p.get('is_fastener'):
   source=original.get(p.get('source_id'),{})
   if source.get('withdrawal_direction'):p.setdefault('withdrawal_direction',source['withdrawal_direction'])
   if source.get('dimensions'):p.setdefault('dimensions',copy.deepcopy(source['dimensions']))
   if not p.get('receiverIds'):
    joint=joint_by_peg.get(pid);assert joint,('Missing physical peg recipients',pid);p['receiverIds']=[joint['donor'],joint['receiver']]
   p.setdefault('parentId',p['receiverIds'][0]);p.setdefault('withdrawalReceiverIds',p['receiverIds'])
   if not METAL.search(p['material']):
    if p.get('vertices') and p.get('withdrawal_direction'):
     axis=np.asarray(p['withdrawal_direction'],float);axis/=np.linalg.norm(axis);p.setdefault('actual_length_in',float(np.ptp(np.asarray(p['vertices'])@axis)/.0254));p.setdefault('withdrawal_distance_m',p['actual_length_in']*.0254+.0254)
    p['fastenerKind']='wooden peg';p['intentionalFastenerPenetration']=False
    p.setdefault('fastenerSpec',{'manufacturer':'Site-made hardwood peg','partNumber':'PORCH-PEG-'+str(p.get('nominal_diameter_in',.5)),'majorDiameterIn':p.get('nominal_diameter_in',.5),'lengthIn':p.get('actual_length_in'),'material':'Hardwood; species/capacity to specify','installation':'Actual matching transverse timber bores; not a nail or screw penetration exemption.'})
   else:
    code=str(p.get('fastenerSpec',{}).get('partNumber',''));p['fastenerKind']='screw' if 'RSS' in p['name'] or code=='12285' else 'nail';p['intentionalFastenerPenetration']=True
  return p
 def fresh(pid):
  assert pid in original and pid in reference,('Missing original porch frame actor',pid)
  before=native_solid(original[pid]);expected=native_solid(reference[pid]);error=diff(before,expected);assert error<=TOL,(pid,'Refusing to overwrite newer fitted porch geometry',error)
  return before,error
 # Replay only source-compatible default construction inputs. The original
 # local cutter records retain the exact generating numbers; roundtripping
 # them through world metres can introduce false cofacial membranes.
 for pid,record in reference.items():
  assert pid in original and all(original[pid][k]==record[k] for k in ['vertices','triangles']),('Porch source changed; regenerate local recipe before applying it',pid)
 current_primary={p['id']:p for p in json.loads((ROOT/'src/top-entry-proposed-model.json').read_text())['parts']}
 for p in inputs['influential_primary']['parts']:
  assert all(current_primary[p['id']][k]==p[k] for k in ['vertices','triangles']),('Adjacent primary source changed; regenerate porch recipe',p['id'])
 local_recipe=inputs['local_recipe'];assert local_recipe['origin_world_m']==origin.tolist() and local_recipe['basis_world_columns']==basis.tolist()
 def from_local(record):return m.Manifold(m.Mesh64(np.array(record['vertices'],float,order='C'),np.array(record['triangles'],np.uint64,order='C')))
 existing_ids=set(patch['host_cutting_tools'])&set(reference)
 for pid in sorted(existing_ids):
  before,input_error=fresh(pid);normalization=None
  if pid in local_recipe['plates']:
   row=local_recipe['plates'][pid];low=np.asarray(row['full_stock_box_min_local_in']);high=np.asarray(row['full_stock_box_max_local_in']);blank=m.Manifold.cube((high-low).tolist(),True).translate(((low+high)/2).tolist())
   voids=[from_local(q['geometry']) for q in row['donor_and_peg_tools_local']]
   voids.extend(from_local(q['geometry']).trim_by_plane([0.,-1.,0.],-q['clip_to_y_at_most_in']) for q in row['body_tools_local'])
   shape=blank-union(voids)
   for q in row['ordered_host_tools_local']:shape=shape-from_local(q['geometry'])
   clean=regular_local(shape,1e-10/.0254);cleanup=diff(clean,shape);assert cleanup<=1e-6,(pid,'Local boundary changed occupied wood',cleanup)
   assert abs(clean.volume()-shape.volume())<=1e-6,(pid,'Local boundary changed signed volume')
   normalization={'method':'Original generating-inch signed planar boundary before world transform','occupied_difference_in3':cleanup,'plane_weld_distance_m':1e-10};shape=world(clean)
  else:
   shape=local(original[pid])
   for q in patch['host_cutting_tools'][pid]:shape=shape-local(q['tool'])
   shape=world(shape)
  record=native_record(shape,single=True);target=patch['receiver_readback_snapshots_for_local_proof_only'].get(pid);reference_error=None
  if target:
   reference_error=diff(native_solid(record),native_solid(target));assert reference_error<=TOL,(pid,'Fresh recipe disagrees with source-bound reference',reference_error)
   assert abs(record['volume_m3']-native_solid(target).volume())<=TOL,(pid,'Fresh recipe signed volume disagrees')
  p={**original[pid],**patch['existing_host_stock_metadata'].get(pid,{}),**record,'replaceExisting':True};parts.append(enrich(p));proofs.append({'id':pid,'input_difference_m3':input_error,'output_volume_m3':record['volume_m3'],'reference_difference_m3':reference_error,'boundary_normalization':normalization})
 for pid,geometry in patch['replace_fasteners'].items():
  before,input_error=fresh(pid);p={**original[pid],**geometry,'replaceExisting':True};parts.append(enrich(p));proofs.append({'id':pid,'input_difference_m3':input_error,'output_volume_m3':native_solid(geometry).volume()})
 for p in [*patch['add_parts'].values(),*patch['add_fasteners'].values(),*inputs['decks']['parts']]:parts.append(enrich(p))
 for package in [inputs['fixed']['prototypes'],inputs['nails']['prototypes']]:
  for name,record in package.items():
   if name in prototypes:
    a=prototypes[name].get('metal',prototypes[name]);b=record.get('metal',record)
    assert all(a[k]==b[k] for k in ['vertices','triangles']),('Conflicting porch prototypes',name)
   else:prototypes[name]=record
 for p in [*inputs['fixed']['instances'],*inputs['nails']['instances']]:parts.append(enrich(p))
 ids=[p['id'] for p in parts];assert len(ids)==len(set(ids)),'Duplicate porch roof actor'
 stock_checks=[]
 for p in parts:
  if p['id'] not in stocks:continue
  blank=native_solid(stocks[p['id']]['raw_blank']);occupied=native_solid(p);outside=max(0.,float((occupied-blank).volume()));assert outside<=TOL,(p['id'],'Outside independently supplied raw stock',outside)
  stock_checks.append({'id':p['id'],'outside_blank_m3':outside})
 return {'parts':parts,'prototypes':prototypes,'appendJoints':patch['append_joint_records'],'stock':stocks,'report':{'status':'PASS','scope':'Fresh fitted-host composition, input ownership and independent raw-stock containment only. Complete scene/static, auxiliary cavities and installation paths require their separate final checks.','fixture_sha256':fixture_hash,'generator_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'host_composition':proofs,'stock_checks':stock_checks,'new_and_replacement_records':len(parts),'connection_instances':len(inputs['fixed']['instances'])+len(inputs['nails']['instances'])},'releaseEvidence':inputs['release'],'originalReleaseEvidence':inputs['original_release']}
# TIMESTAMP END 2026-11-05T16:27:06+00:00 | REVISION R000053
