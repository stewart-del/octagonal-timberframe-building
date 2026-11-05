# TIMESTAMP START 2026-11-05T17:43:13+00:00 | REVISION R000059
"""Real wood stair/landing actors composed without replacing later pan details."""
from pathlib import Path
import copy,gzip,hashlib,json,re
import numpy as np
from audit_revised_joinery import native_solid
from cupola_joinery_recipe import native_record
from floor_surface_normalization import normalize_one
from audit_cavity_fit import inspect_mesh
from prepare_parametric import local_shape,up
ROOT=Path(__file__).resolve().parents[1];FIXTURE=ROOT/'scripts/fixtures/wood-stair-inputs.json.gz';I=.0254;TOL=1e-6*I**3

def inputs():
 raw=FIXTURE.read_bytes();data=json.loads(gzip.decompress(raw));assert data['schema']=='source-bound-real-wood-stairs-1';result={}
 for key,r in data['files'].items():
  assert hashlib.sha256(r['content'].encode()).hexdigest()==r['content_sha256'],('Changed wood stair artifact',key);result[key]=json.loads(r['content'])
 return result

def difference(a,b):return max(0.,float((a-b).volume()))+max(0.,float((b-a).volume()))
def checked_difference(a,b):
 world=difference(a,b);low=np.minimum(np.asarray(a.bounding_box())[:3],np.asarray(b.bounding_box())[:3]);high=np.maximum(np.asarray(a.bounding_box())[3:],np.asarray(b.bounding_box())[3:]);origin=np.rint((low+high)/2);left,lb=local_shape(a,origin);right,rb=local_shape(b,origin);local=difference(left,right);cover=lb['transform_cover_bound_m3']+rb['transform_cover_bound_m3'];return up(local+cover),{'method':'Fixed common integer-metre origin, every actual oriented triangle retained','origin_m':origin.tolist(),'world_difference_m3_diagnostic':world,'local_difference_m3':local,'transform_cover_m3':cover}
def pan_id(pid):return pid=='MUD-FLOOR' or pid.startswith(('MUD-PAN-','MUD-CHANNEL-','MUD-GRATE-SEAT-'))
def build(current_porch):
 data=inputs();stairs=data['stairs'];original={p['id']:p for p in data['original']['porch']['components']};current={p['id']:p for p in current_porch};overlays=set(stairs['sourceOverlayIds']);pre=stairs['receiverPreBoreSolids'];tools=stairs['receiverCutTools'];parts=[];receipts=[];stock_by_piece={pid:row for row in stairs['stockParents'] for pid in row['pieceIds']};cuts={pid:(row,cut) for row in data['stock']['linearStock'] for cut in row['pieces'] for pid in cut['pieceIds']};porch=data['original']['porch'];basis=np.column_stack([porch['axis'],[0.,1.,0.],porch['normal']]);fastener_rows={r['id']:r for r in stairs['fasteners']}
 for pid in sorted(overlays):
  if pan_id(pid):continue
  assert pid in current and pid in original,('Missing original porch wood',pid)
  assert all(current[pid][key]==original[pid][key] for key in ['vertices','triangles']),('Newer porch joinery must be regenerated into wood stairs',pid)
 for source in stairs['parts']:
  pid=source['id']
  # The grate helper owns the immutable cast pan plus every sill/drain bore.
  # Its later post-cure pockets must never be overwritten by these old sheets.
  if pan_id(pid):continue
  p=copy.deepcopy(source);normalization=None
  if pid in pre:
   before=native_solid(pre[pid]);shape=before
   for row in tools.get(pid,[]):shape=shape-native_solid(row['tool'])
   try:record=native_record(shape,single=True)
   except AssertionError:
    mesh=shape.to_mesh64();raw={**p,'vertices':np.asarray(mesh.vert_properties)[:,:3].tolist(),'triangles':np.asarray(mesh.tri_verts).tolist()};audit=inspect_mesh(np.asarray(raw['vertices']),np.asarray(raw['triangles'],np.uint64),True);record,normalization=normalize_one(raw,audit)
   error,comparison=checked_difference(native_solid(record),native_solid(source));assert error<=TOL,(pid,'Fresh individual attachment holes disagree with saved final stair solid',error)
   p.update(record);p['volume_m3']=float(native_solid(record).volume());receipts.append({'id':pid,'cut_tool_count':len(tools.get(pid,[])),'readback_difference_m3':error,'boundary_normalization':normalization,'readback_comparison':comparison})
  stock=stock_by_piece.get(pid)
  if stock:
   p['stock_parent_id']=stock['id'];p['purchaseStock']=stock
   if stock.get('cutEnvelopeIn'):p['minimum_blank_dimensions_in']=stock['cutEnvelopeIn']
  if pid in cuts:
   row,cut=cuts[pid];rotation=np.asarray(cut['installedToStockInches'])[:,:3];p.update(stock_parent_id=row['id'],stockSectionIn=row['actualSectionIn'],stockLengthIn=cut['cutLengthIn'],purchaseBlankLengthIn=row['stockLengthIn'],stockCutStartIn=cut['cutStartIn'],sawKerfIn=row['kerfIn'],stock_frame={'axis':(basis@rotation[2]).tolist(),'width':(basis@rotation[0]).tolist(),'depth':(basis@rotation[1]).tolist()})
  if pid in overlays:p['replaceExisting']=True
  p.setdefault('name',pid);p['mudroomRole']='stair';p['constructionPhase']='Porch wood stairs and landing';p['capacity_verified']=False
  if p.get('is_fastener'):
   assert p.get('receiverIds'),('Stair fastener has no receiver',pid);p.setdefault('parentId',p['receiverIds'][0]);p.setdefault('withdrawalReceiverIds',p['receiverIds']);p['intentionalFastenerPenetration']=False
   base_id=re.sub(r'-(?:NUT|WASHER-[HN])$','',pid);base=fastener_rows.get(base_id,{})
   axis_local=p.get('axisIn',base.get('axisIn'));axis_world=None
   if axis_local is not None:
    axis_world=basis@np.asarray(axis_local,float);axis_world/=np.linalg.norm(axis_world);p.setdefault('axis_direction',axis_world.tolist());sign=1. if pid.endswith(('-NUT','-WASHER-N')) else -1.;p.setdefault('withdrawal_direction',(axis_world*sign).tolist())
   if not p.get('fastenerSpec'):
    diameter=p.get('diameterIn',p.get('nominalDiameterIn'));length=p.get('lengthIn',p.get('nominalLengthIn'));standard=p.get('hardwareStandard');outer=None;inner=None
    if axis_world is not None:
     vertices=np.asarray(p['vertices']);axial=float(np.ptp(vertices@axis_world)/I);center=(vertices.min(0)+vertices.max(0))/2;delta=vertices-center;radii=np.linalg.norm(delta-np.outer(delta@axis_world,axis_world),axis=1)/I;outer=float(radii.max()*2);inner=float(radii.min()*2)
     if pid.endswith('-NUT') or '-WASHER-' in pid:length=axial
    hardwood='hardwood' in p.get('material','').lower();p['fastenerSpec']={'manufacturer':'Shop-made hardwood peg' if hardwood else 'Standard hardware supplier to be selected','partNumber':None,'componentType':p['name'],'standardReference':standard,'nominalThreadIn':None if hardwood else diameter,'majorDiameterIn':diameter,'lengthIn':length,'headDiameterIn':None if hardwood else outer,'insideDiameterIn':inner if '-WASHER-' in pid else None,'material':p['material'],'geometryProfile':standard or 'Actual source-fit occupied hardwood profile. Species/grade and capacity are not assigned.'}
   if not p.get('withdrawal_distance_m') and p['fastenerSpec'].get('lengthIn'):p['withdrawal_distance_m']=(p['fastenerSpec']['lengthIn']+.5)*I
  else:p.setdefault('publishedDimensionsIn',p.get('referenceDimensionsIn'))
  if p.get('is_fastener'):p['color']=[.54,.56,.57] if 'steel' in p['material'].lower() else [.62,.44,.27]
  else:p['color']=[.49,.33,.21] if p.get('is_timber') else [.42,.44,.43]
  parts.append(p)
 assert len(parts)==len({p['id'] for p in parts});assert not any(pan_id(p['id']) for p in parts)
 return {'parts':parts,'removeIds':stairs['removedSourceIds'],'stock':stairs['stockParents'],'stockTakeoff':{key:value for key,value in data['stock'].items() if key not in ['linearStock','plyStock']},'linearStockCutPlan':[{key:value for key,value in row.items() if key not in ['stockEnvelope','discardedOffcutsAndKerf']} for row in data['stock']['linearStock']],'joints':stairs['joints'],'layout':stairs['layout'],'releaseEvidence':data['release'],'report':{'status':'PASS','scope':'Fresh source-compatible stair/landing attachment holes and strict input guards only. Final scene, individual/global motion and capacities remain separate checks.','fixture_sha256':hashlib.sha256(FIXTURE.read_bytes()).hexdigest(),'generator_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'parts':len(parts),'fresh_host_composition':receipts,'original_wood_overlays':sorted(pid for pid in overlays if not pan_id(pid)),'cast_pan_geometry_preserved_by_other_owner':True,'capacity_verified':False}}
# TIMESTAMP END 2026-11-05T17:43:13+00:00 | REVISION R000059
