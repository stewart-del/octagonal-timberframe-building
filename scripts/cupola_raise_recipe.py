# TIMESTAMP START 2026-11-05T06:23:51+00:00 | REVISION R000028
"""Classify and raise upper cupola stock while preserving lower connections.

Derived from the independently checked ten-inch transform, not a global
height-based vertex remap. Rebuild clean LS stock and relocate its mortises.
"""
from pathlib import Path
import argparse,copy,gzip,hashlib,json,math,re,sys,time
sys.dont_write_bytecode=True
import numpy as np
import manifold3d as m
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from cupola_joinery_recipe import (prototype,native_record,native_solid,existing_stock,
 union,amount,diff,at_most,rotate,empty,I,TOL,UP,volume_centroid)
from cupola_bridge_recipe import generate as bridge
from plan_architectural_disassembly import Scene,check_stage,apply_stage,audit_initial_scene,boxes_overlap
from audit_cavity_fit import inspect_mesh
from step_lap import regular_boundary
DELTA_IN=10.;DELTA=UP*DELTA_IN*I
FILES={'baseline':'model-data.json','proposed':'step-lap-proposed-model.json','top-entry':'top-entry-proposed-model.json'}

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def fingerprint(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def save(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2,default=lambda x:x.item() if hasattr(x,'item') else x)+'\n')
def read(p):return json.loads(p.read_text())
def move_mesh(q):
 q=copy.deepcopy(q)
 if q.get('vertices'):q['vertices']=(np.asarray(q['vertices'])+DELTA).tolist()
 return q
def shift_plane(plane):
 p=copy.deepcopy(plane);p['constant']+=p['normal'][2]*DELTA_IN;return p
def move_record(p):
 q=move_mesh(p)
 for key in ['center','axis_start','axis_end','label_position']:
  if key in q:q[key]=(np.asarray(q[key])+DELTA).tolist()
 for key in ['geometry_planes_inches','proposed_stock_planes_inches']:
  if key in q:q[key]=[shift_plane(v) for v in q[key]]
 if q.get('declared_exterior_cut'):q['declared_exterior_cut']=move_mesh(q['declared_exterior_cut'])
 if q.get('fit_geometry',{}).get('centroid_m'):q['fit_geometry']['centroid_m']=(np.asarray(q['fit_geometry']['centroid_m'])+DELTA).tolist()
 # Historical source metadata uses legacy XYZ-up inches, not world Y-up m.
 for key in ['axis_start','axis_end']:
  if key in q.get('source_geometry_metadata',{}):q['source_geometry_metadata'][key][2]+=DELTA_IN
 return q
def move_joint(j):
 q=copy.deepcopy(j)
 for key in ['connector','cutting_tool','housing']:
  if key in q:q[key]=move_mesh(q[key])
 if 'face_center' in q:q['face_center']=(np.asarray(q['face_center'])+DELTA).tolist()
 if 'flat_seat_y_m' in q:q['flat_seat_y_m']+=DELTA[1]
 return q
def clean_ls(part,joints):
 """Raw 4x6 section, original end shoulders, full uncut integral tongues.

No source R-entry void, and no fragment of a tongue previously clipped by that
void, is reused as the raised ring geometry.
"""
 blank=existing_stock(part);body=blank
 for p in part['geometry_planes_inches']:
  if p.get('end') not in ['A','B']:continue
  n=np.array([p['normal'][0],p['normal'][2],-p['normal'][1]]);ln=np.linalg.norm(n)
  body=body.trim_by_plane((-n/ln).tolist(),-p['constant']*I/ln)
 tools=[native_solid(j.get('cutting_tool',j['connector'])) for j in joints]
 body=body+union(tools)
 # Positive cap extensions remove coincident zero-thickness stock flaps;
 # independently require that they remove no positive occupied stock.
 caps=[]
 for j,tool in zip(joints,tools):
  along=np.asarray(part['stock_frame']['axis'])*(-1 if j['end']=='A' else 1)
  caps.append(tool+tool.translate((along*.05*I).tolist()))
 offcut=blank-(body+union(caps));at_most(diff(blank-body,offcut),part['id']+'LS offcut cap extension')
 return blank,body,offcut

def transform(model,baseline_model,source_sha):
 marker=model.get('upper_cupola_raise10')
 if marker:
  assert marker['raise_in']==DELTA_IN and marker['source_frozen_sha256']==source_sha
  return copy.deepcopy(model),{'idempotent_no_op':True}
 out=copy.deepcopy(model);P={p['id']:p for p in out['parts']};old={p['id']:p for p in model['parts']};S={pid:native_solid(p) for pid,p in old.items() if p.get('triangles')}
 # Baseline frozen LS tools retain the original full 3-inch integral tongues;
 # the top-entry fixture clipped them when making the obsolete hip route.
 full_ls=[copy.deepcopy(j) for j in baseline_model['tenon_schedule'] if re.fullmatch(r'L[0-7]-S',j['donor'])]
 full_ls_byid={j['id']:j for j in full_ls}
 ls0_blank,ls0_body,ls0_offcut=clean_ls(old['L0-S'],[j for j in full_ls if j['donor']=='L0-S'])
 ls0_offcut=native_solid(native_record(ls0_offcut))
 ring_joints=[j for j in model['tenon_schedule'] if re.fullmatch(r'L[0-7]-[SH]',j['donor'])]
 old_tools={pid:union([native_solid(j.get('cutting_tool',j['connector'])) for j in ring_joints if j['receiver']==pid]) for pid in [f'C{k}' for k in range(8)]}
 new_joint_list=[move_joint(full_ls_byid.get(j['id'],j)) if re.fullmatch(r'L[0-7]-[SH]',j['donor']) else copy.deepcopy(j) for j in model['tenon_schedule']]
 new_tools={pid:union([native_solid(j.get('cutting_tool',j['connector'])) for j in new_joint_list if re.fullmatch(r'L[0-7]-[SH]',j['donor']) and j['receiver']==pid]) for pid in old_tools}
 records=[]
 for pid,p in list(P.items()):
  if re.fullmatch(r'(CC|CR)[0-7]|L[0-7]-H',pid) or pid=='PLY':P[pid]=move_record(p)
  elif re.fullmatch(r'L[0-7]-S',pid):
   k=int(pid[1]);blank,body,offcut=rotate(ls0_blank,k),rotate(ls0_body,k),rotate(ls0_offcut,k)
   at_most(diff(blank,existing_stock(p)),pid+'stock family isometry')
   q=move_record(p);q.update(native_record(body.translate(DELTA.tolist()),single=True));q['faces']=q['triangles'];q['declared_exterior_cut']=move_mesh(native_record(offcut));q['fit_geometry']={**q.get('fit_geometry',{}),**volume_centroid(native_solid(q))};P[pid]=q
   records.append({'id':pid,'class':'Rebuild clean raw-stock/end-shoulder/tongue geometry, then translate','restored_obsolete_R_cut_in3':amount(body-S[pid])/I**3,'removed_old_entry_region':pid in out.get('joinery_entry_regions',{})})
 canonical_c=None
 for k in range(8):
  pid=f'C{k}';p=old[pid];q=copy.deepcopy(p);raw=existing_stock(p);removed=raw-S[pid]
  # Distinct lower R mate + declared R-entry tools remain at their original
  # world coordinates, including any overlap with an old ring mortise.
  hip=next(j for j in model['tenon_schedule'] if j['donor']==f'R{k}' and j['receiver']==pid)
  hip_tool=native_solid(hip.get('cutting_tool',hip['connector']))
  entry_record=model.get('joinery_entry_regions',{}).get(pid,{})
  entry=native_solid(entry_record) if entry_record.get('triangles') else empty()
  # Use an explicitly verified, unjointed splice interval between the T-foot
  # and R socket. This is a C-member construction operation, not a global
  # rule assigning vertices by height. The entire raw-stock band must match
  # source occupied wood before the splice is allowed.
  foot=next(j for j in model['tenon_schedule'] if j['donor']==f'T{k}' and j['receiver']==pid)
  foot_top=max(v[1] for v in foot['connector']['vertices'])
  hip_bottom=min(v[1] for v in hip.get('cutting_tool',hip['connector'])['vertices'])
  splice=(foot_top+hip_bottom)/2;bandlo=splice-.01*I;bandhi=splice+.01*I
  band=lambda s:s.trim_by_plane([0,1,0],bandlo).trim_by_plane([0,-1,0],-bandhi)
  at_most(diff(band(S[pid]),band(raw)),pid+'splice band is not clean full-section stock')
  lower=S[pid].trim_by_plane([0,-1,0],-(splice+.005*I))
  fixed_hip=hip_tool+entry+S[f'R{k}']
  old_rebuilt=(lower+raw.trim_by_plane([0,1,0],splice))-fixed_hip-old_tools[pid]
  at_most(diff(old_rebuilt,S[pid]),pid+'classified reconstruction differs from source')
  # Only the top end plane moves. The lower 85-inch stock datum and all four
  # radial/tangent planes are unchanged. Recompute stock from these halfspaces.
  for key in ['geometry_planes_inches','proposed_stock_planes_inches']:
   if key in q:q[key]=[shift_plane(v) if v.get('end')=='B' else copy.deepcopy(v) for v in q[key]]
  q['axis_end']=(np.asarray(q['axis_end'])+DELTA).tolist()
  q['center']=((np.asarray(q['axis_start'])+np.asarray(q['axis_end']))/2).tolist()
  q['label_position']=(np.asarray(q['label_position'])+DELTA/2).tolist()
  if q.get('source_geometry_metadata',{}).get('axis_end'):q['source_geometry_metadata']['axis_end'][2]+=DELTA_IN
  for key in ['dimensions','nominal_dimensions']:
   q[key]['length_m']+=DELTA[1]
   if 'length_ft' in q[key]:q[key]['length_ft']=q[key]['length_m']/.3048
  q['fitted_axial_extent_inches']=p.get('fitted_axial_extent_inches',np.ptp(np.asarray(p['vertices'])[:,1])/I)+DELTA_IN
  newraw=existing_stock(q);shape=(lower+newraw.trim_by_plane([0,1,0],splice))-fixed_hip-new_tools[pid]
  if k==0:
   normalized=regular_boundary(shape);at_most(diff(shape,normalized),pid+'net planar boundary normalization changed wood')
   canonical_c=native_solid(native_record(normalized,single=True));shape=canonical_c
  else:
   at_most(diff(shape,rotate(canonical_c,k)),pid+'classified C family differs from canonical rotation')
   shape=rotate(canonical_c,k)
  q.update(native_record(shape,single=True));q['faces']=q['triangles'];q['fit_geometry']={**q.get('fit_geometry',{}),**volume_centroid(native_solid(q))};P[pid]=q
  # Prove actual protected R/T/foot regions unchanged; changed mortises above
  # them are not mistaken for globally fixed C stock.
  rdiff=diff(S[pid]^hip_tool,shape^hip_tool);ediff=diff(S[pid]^entry,shape^entry)
  foot_old=S[pid].trim_by_plane([0,-1,0],-110*I);foot_new=shape.trim_by_plane([0,-1,0],-110*I)
  at_most(rdiff,pid+'R protected region');at_most(ediff,pid+'entry protected region');at_most(diff(foot_old,foot_new),pid+'lower 110in region')
  records.append({'id':pid,'class':'Preserve lower C; verified full-section splice; extend 6x6 shaft; retain R cuts; move LS/LH mortises','verified_splice_elevation_in':splice/I,'verified_splice_band_in':[bandlo/I,bandhi/I],'source_classified_reconstruction_difference_in3':diff(old_rebuilt,S[pid])/I**3,'R_region_difference_in3':rdiff/I**3,'R_entry_region_difference_in3':ediff/I**3,'below110in_difference_in3':diff(foot_old,foot_new)/I**3,'added_shaft_length_in':DELTA_IN,'old_ring_tools_minY_in':min(np.asarray(j['connector']['vertices'])[:,1].min()/I for j in ring_joints if j['receiver']==pid)})
 out['parts']=[P[p['id']] for p in model['parts']];out['tenon_schedule']=new_joint_list
 # C hip entries are fixed. LS's former main-roof entries become obsolete once
 # the entire LS ring is above the main roof, and are removed by ID only.
 out['joinery_entry_regions']={pid:copy.deepcopy(v) for pid,v in model.get('joinery_entry_regions',{}).items() if not re.fullmatch(r'L[0-7]-S',pid)}
 for row in out.get('proposed_member_volume_centroids',[]):
  if row['id'] in P and P[row['id']]!=old[row['id']]:row.update(volume_centroid(native_solid(P[row['id']])))
 out['upper_cupola_raise10']={'raise_in':DELTA_IN,'source_frozen_sha256':source_sha,'scope':'Explicit member/joint classes; lower main-roof/foot interface geometry retained; capacity unverified'}
 unchanged=[pid for pid in old if not re.fullmatch(r'C[0-7]|(CC|CR)[0-7]|L[0-7]-[SH]|PLY',pid)]
 assert all(P[pid]==old[pid] for pid in unchanged)
 return out,{'idempotent_no_op':False,'unchanged_record_ids':unchanged,'classifications':records,'rigid_member_ids':[pid for pid in P if re.fullmatch(r'(CC|CR)[0-7]|L[0-7]-H|PLY',pid)],'moved_ring_joint_ids':[j['id'] for j in new_joint_list if re.fullmatch(r'L[0-7]-[SH]',j['donor'])]}

# TIMESTAMP END 2026-11-05T06:23:51+00:00 | REVISION R000028
