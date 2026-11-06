# TIMESTAMP START 2026-11-05T08:46:05+00:00 | REVISION R000036
"""Bore actual fresh wall members and retain each transverse hardwood pin."""
from pathlib import Path
import copy,gzip,hashlib,json
import numpy as np
import manifold3d as m
from audit_revised_joinery import native_solid
from audit_cavity_fit import inspect_mesh
I=.0254;TOL=1e-6*I**3
FIXTURE=Path(__file__).with_name('fixtures')/'wall-locking-pegs.json.gz'
def load(variant):return json.loads(gzip.decompress(FIXTURE.read_bytes()))['variants'][variant]
def union(shapes):return m.Manifold.batch_boolean(shapes,m.OpType.Add) if shapes else m.Manifold()
def attach(variant,final,joints):
 design=load(variant);mapping=design['joint_mapping'];J={j['id']:j for j in joints};pegs=[];cutters={};owners={};checks=[]
 for raw in design['pegs']:
  pid=raw['id'];row=next(x for x in mapping if x['id']==pid);joint=J[row['joint']]
  assert joint['donor']==row['donor'] and joint['receiver']==row['receiver'],('Changed pin joint',pid)
  peg=native_solid(raw);target=[row['donor'],row['receiver']]
  assert all(x in final for x in target),('Missing live pin recipient',pid)
  outside=max(0.,(peg-union([final[x] for x in target])).volume())
  assert outside<=TOL,('Pin does not fit current mating wood',pid,outside)
  tool=next(x for x in design['bore_tools'] if x['id']==pid);assert set(tool['receiverIds'])==set(target)
  for receiver in target:
   cutters.setdefault(receiver,[]).append(native_solid(tool));owners.setdefault(receiver,[]).append(pid)
  vertices=np.asarray(raw['vertices']);center=((vertices.min(0)+vertices.max(0))/2).tolist()
  record={**copy.deepcopy(raw),'name':'Concealed wall transverse hardwood locking peg','schematic':True,'schematicKind':'rail','framingRole':'lockingPeg','group':'wall_locking_pegs','material':'Straight-grained hardwood peg','color':[.71,.51,.28],'is_timber':False,'is_fastener':True,'center':center,'label_position':center,'exploded_offset':[0,0,0],'volumeM3':peg.volume(),'receiverIds':target,'lockingJointId':row['joint'],'face':row['face'],'constructionPhase':'main wall framing','stockSectionIn':[row['diameter_in'],row['diameter_in']],'stockLengthIn':row['quarter_inch_peg_blank_length_in'],'fastener_spec':{'product':'Custom straight-grained hardwood locking peg','diameterIn':row['diameter_in'],'minimumBlankLengthIn':row['minimum_peg_blank_length_in'],'purchaseCutLengthIn':row['quarter_inch_peg_blank_length_in'],'blindBoreDiameterIn':row['matching_bore_diameter_in'],'tipClearanceIn':row['matching_bore_extra_tip_in'],'extractorPilotDiameterIn':1/16,'extractorPilotTotalDepthIn':.25,'extractorPilotPointDegrees':118,'capacityVerified':False},'installation':{'withdrawalDirection':row['withdrawal_direction_world'],'initialWithdrawalDistanceM':row['withdrawal_distance_m'],'toolScrewMaximumInsertionIn':.20,'temporaryExtractorScrew':'Bolt Depot2139 #2 ×3/8in, one reusable tool screw'},'geometry_purpose':'Actual occupied peg with extractor pilot; matching physical bores in current donor and receiver.'}
  pegs.append(record);checks.append({'id':pid,'outside_actual_mating_wood_m3':outside})
 before=dict(final)
 for pid,tools in cutters.items():
  final[pid]=final[pid]-union(tools)
  assert str(final[pid].status())=='Error.NoError' and len(final[pid].decompose())==1,('Peg holes disconnect timber',pid)
 for peg in pegs:
  shape=native_solid(peg);raw=inspect_mesh(np.asarray(peg['vertices']),np.asarray(peg['triangles']),require_single=True)
  assert raw['status']=='PASS',(peg['id'],raw['failures'])
  for pid in peg['receiverIds']:assert max(0.,(shape^final[pid]).volume())<=TOL,('Peg bore residual',peg['id'],pid)
 return pegs,owners,{'status':'PASS','scope':'Fresh current-wood containment, matching bores and individual strict peg boundaries. Whole-building motion and structural capacity remain separate.','fixture_sha256':hashlib.sha256(FIXTURE.read_bytes()).hexdigest(),'helper_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'checks':checks,'reusableRemovalTools':design['reusable_removal_tools'],'capacity_verified':False}
# TIMESTAMP END 2026-11-05T08:46:05+00:00 | REVISION R000036
