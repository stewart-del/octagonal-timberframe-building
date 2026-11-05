# TIMESTAMP START 2026-11-05T12:40:59+00:00 | REVISION R000041
"""Assemble exact authored products with shared hardware and unique logical IDs.

User-authorized nail/screw penetration into specified receiving wood is retained.
All other stock, mortises, housings and purchased-assembly limits stay explicit.
A staging dataset cannot pass the final whole-building publication gate.
"""
from pathlib import Path
# TIMESTAMP START 2026-11-05T13:19:15+00:00 | REVISION R000044
import argparse,copy,gzip,hashlib,json,re
# TIMESTAMP END 2026-11-05T13:19:15+00:00 | REVISION R000044
import numpy as np
from physical_data import write_physical_json,read_physical_json
ROOT=Path(__file__).resolve().parents[1]
FIXTURE=ROOT/'scripts/fixtures/architectural-inputs.json.gz'
I=.0254

def sha(raw):return hashlib.sha256(raw).hexdigest()
def load_inputs():
 payload=json.loads(gzip.decompress(FIXTURE.read_bytes()));result={};sources={}
 for key,record in payload['files'].items():
  raw=record['content'].encode();assert sha(raw)==record['content_sha256'],('Authored component input changed',key)
  result[key]=json.loads(raw);sources[key]={k:v for k,v in record.items() if k!='content'}
 return result,sources

def prepare(output):
 inputs,sources=load_inputs();parts=[];prototypes={};allids=set()
 # TIMESTAMP START 2026-11-05T19:06:47+00:00 | REVISION R000061
 from cupola_roof_parts import build as physical_cupola_roof
 cupola_roof=physical_cupola_roof();superseded_cupola=set(cupola_roof['removeIds']+cupola_roof['replaceIds'])
 # TIMESTAMP END 2026-11-05T19:06:47+00:00 | REVISION R000061
 def prototype(name,record):
  physical=record.get('metal',record);value={k:physical[k] for k in ['vertices','triangles']}
  vertex=np.asarray(value['vertices']);faces=np.asarray(value['triangles'],np.int64);value['volumeM3']=physical.get('volumeM3',physical.get('volume_m3')) or float(abs(np.einsum('ij,ij->i',vertex[faces[:,0]],np.cross(vertex[faces[:,1]],vertex[faces[:,2]])).sum()/6))
  if name in prototypes:assert prototypes[name]==value,('Different physical prototypes share an ID',name)
  else:prototypes[name]=value
  return name
 def add(raw,*,phase,role,kind,material=None,color=None):
  p=copy.deepcopy(raw);pid=p['id'];assert pid not in allids,('Duplicate architectural piece',pid);allids.add(pid)
  if p.get('mesh_instance'):
   instance=p['mesh_instance'];mesh=prototypes[instance['prototype']];matrix=np.asarray(instance['transform'],float)
   assert matrix.shape==(3,4) and np.max(abs(matrix[:,:3].T@matrix[:,:3]-np.eye(3)))<1e-10 and abs(np.linalg.det(matrix[:,:3])-1)<1e-10,('Non-rigid product transform',pid)
   vertices=np.asarray(mesh['vertices'])@matrix[:,:3].T+matrix[:,3]
   p.setdefault('volumeM3',mesh['volumeM3'])
  else:vertices=np.asarray(p['vertices'],float)
  assert len(vertices)>3 and np.isfinite(vertices).all(),pid
  center=((vertices.min(0)+vertices.max(0))/2).tolist()
  p.update(schematic=True,schematicKind=kind,displayRole=role,constructionPhase=phase,is_timber=False,center=center,label_position=center,exploded_offset=p.get('withdrawal_translation_m',[0,0,0]))
  p.pop('research_only',None);p.pop('faces',None);p.pop('edges',None)
  if phase.startswith('Porch') or str(p.get('roof','')).startswith('PORCH') or 'PORCH' in pid:
   p.setdefault('mudroomScreen',True)
   if 'roof' in phase.lower() or role in ['roofCover','roofStructure']:p.update(mudroomRoof=True,mudroomRole='roof')
   else:p.setdefault('mudroomRole','furniture')
  if material:p['material']=material
  if color:p['color']=color
  else:p.setdefault('color',[.42,.44,.43] if p.get('is_fastener') else [.64,.46,.29])
  if p.get('fastenerSpec'):p['fastener_spec']=p['fastenerSpec']
  if p.get('is_fastener'):
   spec=p.get('fastenerSpec') or p.get('fastener_spec') or {}
# TIMESTAMP START 2026-11-05T16:27:06+00:00 | REVISION R000053
   if p.get('mesh_instance'):
    mesh_key=p['mesh_instance']['prototype'];prototypes[mesh_key].setdefault('fastener_spec',spec)
# TIMESTAMP END 2026-11-05T16:27:06+00:00 | REVISION R000053
   # Full placement/ray/stock receipts remain exactly once in the immutable
   # authored fixture. Runtime keeps each identity, actual transform, targets,
   # penetration summary and installation movement, with shared product specs.
   retained=['id','name','parentId','parent_id','receiverIds','primaryReceiverId','mesh_instance','material','color','is_fastener','is_timber','schematic','schematicKind','displayRole','constructionPhase','group','center','label_position','exploded_offset','volumeM3','volume_m3','withdrawal_direction','withdrawal_distance_m','withdrawal_translation_m','outward_axis_world','penetrationCheck','minimum_receiving_wood_in','roofRole','roof','course','role','mudroomRoof','mudroomRole','mudroomScreen','requiresAbsentForAxialInsertion','removalPrerequisites']
# TIMESTAMP START 2026-11-05T16:27:06+00:00 | REVISION R000053
   retained+=['vertices','triangles','replaceExisting','fastenerSpec','fastener_spec','stock_frame','stockLengthIn','stockSectionIn','actual_length_in','nominal_diameter_in','dimensions','peg_geometry','axis_direction','localBounds'] if not p.get('mesh_instance') else ['replaceExisting']
# TIMESTAMP END 2026-11-05T16:27:06+00:00 | REVISION R000053
   p={k:v for k,v in p.items() if k in retained};# Exact evidence is indexed by this unique ID in the shared fixture;
   # avoid repeating the fixture name and identity for every fastener.
   p['receiverIds']=list(dict.fromkeys(p.get('receiverIds',[])));assert p['receiverIds'] and all(isinstance(x,str) and x for x in p['receiverIds']),('Fastener lacks actual receivers',pid)
# TIMESTAMP START 2026-11-05T13:19:15+00:00 | REVISION R000044
   code=str(spec.get('partNumber',''));description=' '.join(str(x) for x in [raw.get('name',''),spec.get('product','')])
   kind=raw.get('fastenerKind')
   if not kind:
    if re.search(r'\bnail\b',description,re.I) or re.match(r'^(T7SN7B|T20SNDB|T311ARN1|T8PCS10|8DHDG|16DHDG)',code):kind='nail'
    elif re.search(r'\bscrew\b',description,re.I) or re.match(r'^(WSV|S10\d+WP)',code) or (spec.get('manufacturer')=='GRK' and code in ['14221','14225','14231','12235','12285','113077']):kind='screw'
   p['fastenerKind']=kind or 'other hardware'
# TIMESTAMP START 2026-11-05T16:48:19+00:00 | REVISION R000054
   p['intentionalFastenerPenetration']=raw.get('intentionalFastenerPenetration',kind in ['nail','screw'])
# TIMESTAMP END 2026-11-05T16:48:19+00:00 | REVISION R000054
   # Later incidental head contacts remain static recipients but must be
   # removed before extraction; never turn every contact into an exemption.
   p['withdrawalReceiverIds']=list(dict.fromkeys(raw.get('withdrawalReceiverIds',raw.get('causalReceiverIds',raw.get('receiverIds',[])))))
# TIMESTAMP END 2026-11-05T13:19:15+00:00 | REVISION R000044
   p['penetrationPolicy']='Specified receiving wood only'
  if p.get('volume_m3') is not None:p['volumeM3']=p.pop('volume_m3')
  # Schematic labels and explosion vectors are derived once by the renderer.
  # Keep actual installation directions; do not duplicate derived state.
  p.pop('label_position',None);p.pop('exploded_offset',None);p.pop('penetrationPolicy',None)
  if p.get('is_fastener'):
   outward=p.get('withdrawal_direction') or p.get('outward_axis_world') or p.get('withdrawal_translation_m')
   if outward:
    vector=np.asarray(outward,float);length=np.linalg.norm(vector);assert length>0
    p['withdrawal_direction']=(vector/length).tolist()
    p.setdefault('withdrawal_distance_m',float(np.linalg.norm(p.get('withdrawal_translation_m',vector))))
   p.pop('withdrawal_translation_m',None);p.pop('outward_axis_world',None)
  parts.append(p)
 def matrix(row):return np.asarray(row['world_matrix_column_major'],float).reshape(4,4).T[:3,:4].tolist()
 def add_hardware(key,proto_key,prefix,phase):
  proto=inputs[proto_key].get('prototypes',inputs[proto_key]);names={}
  for key2,value in proto.items():
   if key2.startswith('CUT-'):continue
   names[key2]=prototype(prefix+key2,value)
  for item in inputs[key]['instances']:
   # TIMESTAMP START 2026-11-05T19:06:47+00:00 | REVISION R000061
   if item['id'] in superseded_cupola:continue
   # TIMESTAMP END 2026-11-05T19:06:47+00:00 | REVISION R000061
   p=copy.deepcopy(item)
   if p.get('mesh_instance'):
    q=p['mesh_instance'];p['mesh_instance']={'prototype':names[q['prototype']],'transform':q['transform']}
   else:
    name=p['prototype_id'];p['mesh_instance']={'prototype':names[name],'transform':matrix(p)}
# TIMESTAMP START 2026-11-05T13:19:15+00:00 | REVISION R000044
   p['causalReceiverIds']=list(dict.fromkeys(p.get('receiverIds',[])+[r['id'] for r in p.get('ray_receipts',[])]+[r['id'] for r in p.get('woodRayReceipts',[])]))
# TIMESTAMP END 2026-11-05T13:19:15+00:00 | REVISION R000044
   actual=p.get('actual_bore_hosts') or []
   p['receiverIds']=list(dict.fromkeys(p.get('receiverIds',[])+[r.get('host_id',r.get('id')) for r in actual]+[r['id'] for r in p.get('ray_receipts',[])]))
   p['parentId']=p.get('parentId') or p.get('parent_id') or p.get('owner')
   p['is_fastener']=True;p.setdefault('name',('Roof nail ' if 'NAIL' in p['id'] or 'CEDAR' in p['id'] else 'Individual roof fastener ')+p['id'])
   spec=p.get('fastenerSpec') or p.get('fastener_spec')
   if not spec:
    original=proto.get(p.get('prototype_id'),{});spec={k:v for k,v in original.items() if k not in ['vertices','triangles','edges','metal','bore_tool']};spec.update(manufacturer='Simpson Strong-Tie',partNumber=p.get('prototype_id'),capacity_verified=False)
   p['fastenerSpec']=spec
   add(p,phase=phase,role='roofStructure' if p.get('roofRole')=='backing_to_rafter' else 'roofCover',kind='roofCover',material=p.get('material','Type316 stainless steel'))
 for p in inputs['cedar']['parts']:
  p={**p,'name':'Individual 18 in cedar '+('hip or ridge cap leaf' if p['kind']=='cap_leaf' else 'field shingle'),'stockSectionIn':[p['stock'].get('selected_width_in',p['stock'].get('width_in')),p['stock']['butt_in']],'stockLengthIn':18,'product':{'manufacturer':'CSSB-certified producer to be selected','name':'No.1 edge-grain18in cedar shingle','partNumber':None,'selectedWidthIn':p['stock'].get('selected_width_in',p['stock'].get('width_in')),'profileStatus':'Selected natural shingle layout; explicit tip/profile assumptions retained, no fictitious fixed-width SKU.'}}
  add(p,phase='Porch roof' if p['roof'].startswith('PORCH') else 'Main roof',role='roofCover',kind='roofCover',material='cedar',color=[.62,.43,.27])
 for p in inputs['main_deck']['parts']:add(p,phase='Main roof sheathing',role='roofCover',kind='roofCover',material='Georgia-Pacific Rated Sheathing23/32CAT actual.703in',color=[.78,.64,.41])
 for p in inputs['main_backing']['add_parts'].values():add(p,phase='Main roof backing',role='roofStructure',kind='roofCover',material='wood',color=[.58,.40,.25])
 # TIMESTAMP START 2026-11-05T19:06:47+00:00 | REVISION R000061
 # Canonical backed CR timbers are retained; all physical Cu/wood profiles,
 # weather layers and272 distinct roof nails come from one guarded source.
 for name,record in cupola_roof['prototypes'].items():prototype(name,record)
 for p in cupola_roof['parts']:
  add(p,phase='Cupola roof',role='roofCover',kind='roofCover',material=p['material'])
 # TIMESTAMP END 2026-11-05T19:06:47+00:00 | REVISION R000061
 for p in inputs['valley_copper']['parts']:add(p,phase='Porch roof flashing',role='roofCover',kind='roofCover',material='20oz ASTM B370 copper',color=[.64,.34,.17])
 for p in inputs['ceiling_wood']['parts']:add(p,phase='Cupola ceiling',role='ceilingPanel' if p['id'].startswith('PLY') else 'roofStructure',kind='roofCover',material=p.get('material','wood'))
 add_hardware('cedar_nails','cedar_prototypes','ARCH-CEDAR-','Main and porch roofing')
 add_hardware('roof_aux','roof_aux_prototypes','ARCH-AUX-','Cupola roof and flashing')
 add_hardware('ceiling_screws','ceiling_prototype','ARCH-CEILING-','Cupola ceiling')
 add_hardware('roof_nails','roof_nail_prototypes','ARCH-DECK-','Main and porch roof sheathing')
 for p in inputs['wall_wood']['add_parts'].values():
  lap=p['id'].startswith('LAP-');ply=p['id'].startswith('ENV-') and 'PLY' in p['id']
  add(p,phase='Main siding' if lap else 'Main wall sheathing' if ply else 'Main wall framing',role='wall' if lap or ply else 'wallStructure',kind='wall' if lap or ply else 'rail',material=p.get('material','wood'),color=[.80,.77,.65] if lap else [.68,.52,.34])
 wall=inputs['wall_hardware']
 for key,value in wall['prototypes'].items():prototype(key,value)
 for p in wall['instances']:add(p,phase='Main siding' if p['parentId'].startswith('LAP-') else 'Main wall sheathing and framing',role='wall',kind='wall',material=p['material'])
 # Compose every declared host tool against the CURRENT exact occupied
 # source, preserving all pre-existing floor holes and normalized boundaries.
 # Saved research readbacks are evidence, never replacement source meshes.
 import manifold3d as manifold
 from audit_revised_joinery import native_solid
 from cupola_joinery_recipe import native_record
 floor_path=ROOT/'src/floor-foundation-solids.json';floor=read_physical_json(floor_path);floor_hash=sha(floor_path.read_bytes())
 floor_parts={p['id']:p for p in floor['parts']};tools={};host_proofs=[]
 for key in ['floor_attachments','pier_attachments']:
  package=inputs[key];bindings=package.get('source_hashes',package.get('sourceHashes',{}));expected=[value for path,value in bindings.items() if Path(path).name=='floor-foundation-solids.json'];assert expected==[floor_hash],('Attachment input does not match current occupied floor',key,expected,floor_hash)
  for pid,records in package['host_cutting_tools'].items():tools.setdefault(pid,[]).extend(records)
 delta=inputs['staging_attachment_delta'];updates=delta['fastener_instance_updates']
 for pid,records in delta['head_cutting_tools_override'].items():
  assert pid in tools and len(records)==4,(pid,'Head hole override must replace all four original tools')
  tools[pid]=records
 def updated_instance(original):
  replacement=updates.get(original['id'])
  if not replacement:return original
  old=original['mesh_instance'];new=replacement['mesh_instance'];assert new['prototype'] in [old['prototype'],'ARCH-FLOOR-'+old['prototype']],('Fastener product changed in placement delta',original['id'])
  return {**original,**replacement,'mesh_instance':{**new,'prototype':old['prototype']}}
 for pid,records in tools.items():
  original=floor_parts[pid];solid=native_solid(original);cutters=[native_solid(row['tool']) for row in records]
  assert all(str(s.status())=='Error.NoError' and s.volume()>0 for s in cutters),pid
  cutter=manifold.Manifold.batch_boolean(cutters,manifold.OpType.Add);finished=solid-cutter;removed=float((solid^cutter).volume())
  assert 0<removed<solid.volume()/2,(pid,'Invalid attachment hole removal',removed,solid.volume())
  shape=native_record(finished,single=True);readback=native_solid(shape);tolerance=1e-6*I**3
  assert (readback-solid).volume()<=tolerance and abs((solid-readback).volume()-removed)<=tolerance,(pid,'Host tools changed undeclared material')
  record={**original,**shape,'replaceExisting':True,'geometryChange':'Fresh declared attachment bores/pockets; all earlier source cuts retained'}
  role=original.get('displayRole','floorStructure');add(record,phase='Floor bearing and anchors',role=role,kind=original.get('schematicKind','floorAssembly'),material=original.get('material','wood'))
  host_proofs.append({'id':pid,'sourceGeometrySha256':sha(json.dumps({k:original[k] for k in ['vertices','triangles']},separators=(',',':')).encode()),'toolIds':[row['id'] for row in records],'removedM3':removed,'resultVolumeM3':shape['volume_m3']})
 for key,prefix in [('floor_attachments','ARCH-FLOOR-'),('pier_attachments','ARCH-PIER-')]:
  package=inputs[key];names={name:prototype(prefix+name,record) for name,record in package['prototypes'].items()}
  for p in package.get('add_parts',{}).values():add(p,phase='Floor bearing and anchors',role=p.get('displayRole','floorStructure'),kind='floorAssembly',material=p['material'])
  instances=package['instances']
  if key=='floor_attachments':
   pier_updates=inputs['pier_attachments']['fastener_instance_updates'];assert set(pier_updates)<={p['id'] for p in instances},'Relocated nails must retain their original attachment identities'
   instances=[pier_updates.get(p['id'],p) for p in instances]
  for p in instances:
   p=updated_instance(p);instance=p['mesh_instance'];p={**p,'mesh_instance':{**instance,'prototype':names[instance['prototype']]}}
   add(p,phase='Floor bearing and anchors',role=p.get('displayRole','floorStructure'),kind='floorAssembly',material=p['material'])
# TIMESTAMP START 2026-11-05T16:27:06+00:00 | REVISION R000053
 from porch_roof_parts import build as porch_roof
 import subprocess
 current_porch=json.loads(subprocess.run(['node','-e',"const M=require('./src/mudroom.js'),model=require('./src/top-entry-proposed-model.json');process.stdout.write(JSON.stringify(M.build(model).components));"],cwd=ROOT,check=True,capture_output=True,text=True).stdout)
 porch=porch_roof(current_porch);names={name:prototype('ARCH-PORCH-'+name,record) for name,record in porch['prototypes'].items()}
 for p in porch['parts']:
  if p.get('mesh_instance'):p={**p,'mesh_instance':{**p['mesh_instance'],'prototype':names[p['mesh_instance']['prototype']]}}
  structure=not p['id'].startswith('PORCHR')
  add(p,phase='Porch roof structure' if structure else 'Porch roof sheathing',role='roofStructure' if structure else 'roofCover',kind='roofCover',material=p.get('material','wood'))
 retired=[]
# TIMESTAMP END 2026-11-05T16:27:06+00:00 | REVISION R000053
 for key in ['porch_benches','porch_coats']:
  package=inputs[key];retired.extend(package['remove_ids'])
  for name,record in package['prototypes'].items():prototype(name,record)
  values=package['add_parts'];values=values.values() if isinstance(values,dict) else values
  for p in values:
   stock=package.get('stock',{}).get(p['id'])
   if stock:
    raw=stock['blank_local_in']['vertices'];p={**p,'minimum_blank_dimensions_in':np.ptp(np.asarray(raw,float),axis=0).tolist(),'purchaseBlankLengthIn':stock['purchaseBlankLengthIn']}
   elif p.get('finishedDimensionsIn'):p={**p,'minimum_blank_dimensions_in':p['finishedDimensionsIn']}
   add(p,phase='Porch furnishings',role='mudroom',kind='mudroom',material=p.get('material','wood'))
  for p in package['instances']:
   p=updated_instance(p);add(p,phase='Porch furnishings after main walls' if key=='porch_coats' else 'Porch furnishings',role='mudroom',kind='mudroom',material=p['material'])
# TIMESTAMP START 2026-11-05T16:48:19+00:00 | REVISION R000054
# TIMESTAMP START 2026-11-05T17:43:13+00:00 | REVISION R000059
 from wood_stair_parts import build as wood_stairs
 stairs=wood_stairs(current_porch);retired.extend(stairs['removeIds'])
 for p in stairs['parts']:add(p,phase='Porch wood stairs and landing',role='mudroom',kind='mudroom',material=p['material'])
# TIMESTAMP END 2026-11-05T17:43:13+00:00 | REVISION R000059
 from drain_grate_parts import build as drain_grate,inputs as drain_inputs
 drain=drain_grate(drain_inputs()['cast']['parts']);names={name:prototype('ARCH-'+name,record) for name,record in drain['prototypes'].items()};retired.extend(drain['removeIds'])
 for p in drain['parts']:
  if p.get('mesh_instance'):p={**p,'mesh_instance':{**p['mesh_instance'],'prototype':names[p['mesh_instance']['prototype']]}}
  add(p,phase='Porch cast pan' if p.get('replaceExisting') else 'Porch drainage after cure',role='mudroom',kind='mudroom',material=p['material'])
# TIMESTAMP END 2026-11-05T16:48:19+00:00 | REVISION R000054
# TIMESTAMP START 2026-11-05T17:09:28+00:00 | REVISION R000057
 from window_assemblies import build as window_assemblies
 windows=window_assemblies()
 for p in windows['parts']:add(p,phase=p['constructionPhase'],role=p['displayRole'],kind='windowAssembly',material=p['material'])
# TIMESTAMP END 2026-11-05T17:09:28+00:00 | REVISION R000057
 assert set(updates)<=allids,'Placement delta refers to an absent component'
# TIMESTAMP START 2026-11-05T16:27:06+00:00 | REVISION R000053
# TIMESTAMP START 2026-11-05T16:48:19+00:00 | REVISION R000054
# TIMESTAMP START 2026-11-05T17:09:28+00:00 | REVISION R000057
# TIMESTAMP START 2026-11-05T17:43:13+00:00 | REVISION R000059
 # TIMESTAMP START 2026-11-05T19:06:47+00:00 | REVISION R000061
 used_prototypes={p['mesh_instance']['prototype'] for p in parts if p.get('mesh_instance')}
 prototypes={key:value for key,value in prototypes.items() if key in used_prototypes}
 # TIMESTAMP END 2026-11-05T19:06:47+00:00 | REVISION R000061
 payload={'schema':'octagon-articulated-architecture-1','revision':'R000041','timestamp':'2026-11-05T12:40:59+00:00','status':'STAGING_INCOMPLETE_DO_NOT_PUBLISH','scope':'Independent physical pieces and real hardware; selected nail/screw penetration into specified receiving wood allowed. Cupola stopped backing, revised porch junction, weather layers, window presentation, eave/air closures, forms and complete source-bound motion still require owner integration.','sources':sources,'hostOverlayProofs':host_proofs,'cupolaRoofComposition':cupola_roof['report'],'cupolaRoofStock':cupola_roof['stock'],'porchRoofComposition':porch['report'],'porchRoofJoints':porch['appendJoints'],'porchRoofStock':porch['stock'],'woodStairComposition':stairs['report'],'woodStairStock':stairs['stock'],'woodStairTakeoff':stairs['stockTakeoff'],'woodStairLinearCutPlan':stairs['linearStockCutPlan'],'woodStairJoints':stairs['joints'],'woodStairLayout':stairs['layout'],'drainGrateComposition':drain['report'],'drainGrateStock':drain['stock'],'drainGrateTakeoff':drain['takeoff'],'drainMaintenanceRelease':drain['maintenanceRelease'],'sourceFloorSha256':floor_hash,'source_fixture_sha256':sha(FIXTURE.read_bytes()),'source_generator_sha256':sha(Path(__file__).read_bytes()),'primaryRemoveIds':['PLY'],'replaceSchematicIds':retired,'replaceSchematicKinds':['wall','cupolaWindow','roofCover'],'replacePorchRoof':True,'prototypes':prototypes,'parts':parts,'windowSchedule':inputs['windows'],'windowAssemblies':{k:v for k,v in windows.items() if k!='parts'},'wallStockSource':{'fixtureEntry':'wall_stock','count':len(inputs['wall_stock']['parts'])}}
# TIMESTAMP END 2026-11-05T17:43:13+00:00 | REVISION R000059
# TIMESTAMP END 2026-11-05T17:09:28+00:00 | REVISION R000057
# TIMESTAMP END 2026-11-05T16:48:19+00:00 | REVISION R000054
# TIMESTAMP END 2026-11-05T16:27:06+00:00 | REVISION R000053
# TIMESTAMP START 2026-11-05T14:38:03+00:00 | REVISION R000047
 output.parent.mkdir(parents=True,exist_ok=True);write_physical_json(output,payload,inline_vertex_limit=0,part_archive_limit=8*1024*1024);metadata=json.loads(output.read_text());output.write_text(json.dumps(metadata,separators=(',',':'))+'\n');print('Prepared',len(parts),'individual pieces;',len(prototypes),'shared hardware prototypes;',output,flush=True)
# TIMESTAMP END 2026-11-05T14:38:03+00:00 | REVISION R000047
 return payload
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=ROOT/'src/architectural-solids.json');args=parser.parse_args();prepare(args.output)
# TIMESTAMP END 2026-11-05T12:40:59+00:00 | REVISION R000041
