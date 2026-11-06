# TIMESTAMP START 2026-11-05T04:51:00+00:00 | REVISION R000023
# Derived from independently probed research recipe 82f89253677968c32d1e40e21a1d89f2cf130582100b18c2ab659a2232bf0a17.
"""Separate external40-screw eight-L bridge candidate; never writes source."""
import argparse,copy,hashlib,json,math,sys
from pathlib import Path
import numpy as np,manifold3d as m
sys.path.insert(0,str(Path(__file__).resolve().parent))
from cupola_joinery_recipe import (I,TOL,UP,REPO,radial,tangent,box,rotate,union,native_record,save,amount,diff,at_most,cylinder,volume_centroid)
from audit_revised_joinery import native_solid
from plan_architectural_disassembly import Scene,check_stage,audit_initial_scene
from step_lap import contacts

def segment_cylinder(r,y,lo,hi,radius):
 return cylinder([r*I,y*I,(lo+hi)/2*I],[0,0,1],radius*I,(hi-lo)*I)
def generate(source,out):
 raw=source.read_bytes();model=json.loads(raw);assert not any(p['id'].startswith('M-TMP-SCREW-') for p in model['parts']),'Use the frozen pre-bridge timber input, not a generated bridge model';P={p['id']:copy.deepcopy(p) for p in model['parts']};S={pid:native_solid(p) for pid,p in P.items() if p.get('triangles')};original=dict(S);meta=P['M-TMP'];top=max(v[1] for v in meta['vertices']);assert abs(top/I-109)<1e-6
 # Recognizable original8-arm radial upper star; replace its outer legs/hole plan.
 beam=m.Manifold.cube([45,4,.125]).translate([0,-4,-.0625]);star=union([beam.rotate([0,45*k,0]) for k in range(8)]).scale([I,I,I]).translate([0,top,0]).rotate([0,meta.get('display_assumptions',{}).get('rigid_rotation_y_degrees',-4.7),0])
 plates=[]
 for k in range(8):
  plates.append(rotate(box([41*I,85*I,3*I],[47*I,109*I,3.125*I]),k))
  # Actual horizontal gravity seat on T-top, supporting steel before screws.
  plates.append(rotate(box([44*I,95*I,2*I],[47*I,95.125*I,3.125*I]),k))
  # Positive-overlap return connects rotated radial web to flush C/T side plate.
  plates.append(rotate(box([42.9375*I,105*I,3.0625*I],[43.0625*I,109*I,3.8*I]),k))
 metal=star+union(plates);holes=[];screw_ids=[];screws={};engagement=[]
 for k in range(8):
  for number,(family,r,y) in enumerate([('C',42,97),('C',42,100),('C',42,103),('T',46,88),('T',46,92)],1):
   receiver=f'{family}{k}';pid=f'M-TMP-SCREW-{k}-{number}';axis=tangent(k)
   clearance=rotate(segment_cylinder(r,y,2.9,3.2,.1875),k);metal=metal-clearance
   # Verified RSS14221 dimensions; conservative occupied shoulder/thread envelope.
   # GRK RSS14221 drawing: L3.12,TL1.61,Dhead.620,Hhead.157,
   # Dshank.195,Dmajor.276,Dminor.167,Dshoulder.301.
   # Shoulder axial extent is unpublished here: conservatively envelope the
   # entire unthreaded zone at Dshoulder; no helical/CEE/Zip-Tip exactness claim.
   tip=3.125-3.12;thread_end=tip+1.61
   thread=segment_cylinder(r,y,tip,thread_end+.01,.276/2);neck=segment_cylinder(r,y,thread_end,3.135,.301/2);head=segment_cylinder(r,y,3.125,3.125+.157,.620/2);screw=rotate(thread+neck+head,k);bore=rotate(thread+neck,k)
   hit=amount(screw^S[receiver]);assert hit>.1*I**3,(pid,'insufficient geometric wood engagement',hit/I**3);S[receiver]=S[receiver]-bore;screws[pid]=screw;screw_ids.append(pid)
   hole={'id':f'M-TMP-ARM{k}-HOLE{number}','arm_index':k,'receiver':receiver,'center_m':(radial(k)*r*I+UP*y*I+axis*3.0625*I).tolist(),'axis':axis.tolist(),'diameter_in':.375,'fastener_id':pid};holes.append(hole)
   P[pid]={'id':pid,'name':'GRK RSS14221 temporary eight-L bridge screw','group':'construction_fasteners','material':'case-hardened steel with Climatek coating','temporary':True,'is_timber':False,'is_fastener':True,'displayRole':'jointFastener','center':hole['center_m'],'label_position':hole['center_m'],'axis_direction':(-axis).tolist(),'withdrawal_direction':axis.tolist(),'withdrawal_distance_m':3.25*I,'dimensions':{'length_m':3.12*I,'width_m':.620*I,'depth_m':.620*I,'width_in':.620,'depth_in':.620,'section_display':'GRK RSS14221 nominal5/16x3-1/8; T30 washer head'},'nominal_dimensions':{'length_m':3.12*I,'width_in':.620,'depth_in':.620},'exploded_offset':(radial(k)*12+UP*2).tolist(),'research_only':True,'screw_geometry':{'receiver':receiver,'hole_id':hole['id'],'product':'GRK RSS14221','nominal_size':'5/16x3-1/8','underhead_length_in':3.12,'head_diameter_in':.620,'head_height_in':.157,'shank_diameter_in':.195,'major_thread_diameter_in':.276,'minor_thread_diameter_in':.167,'shoulder_diameter_in':.301,'thread_length_in':1.61,'drive':'T30','steel_clearance_in':.375,'nominal_wood_embedment_in':2.995,'package_quantity':25,'manufacturer_drawing':'https://www.grkfasteners.com/getmedia/7bc4871d-04c7-4c1c-a304-3ce6f6a49cdb/GRK-RSS-Customer-Drawing-(2).pdf?ext=.pdf','drawing_date':'2023-11-01','thread_geometry':'Conservative major-thread and shoulder occupancy; shoulder axial extent, exact CEE/Zip-Tip/thread and T30 recess profiles not modeled; no pilot-hole or fastening-capacity claim'}}
   engagement.append({'id':pid,'receiver':receiver,'wood_intersection_before_bore_in3':hit/I**3,'nominal_embedment_in':2.995})
 assert len(holes)==len(screw_ids)==40 and len(metal.decompose())==1
 S['M-TMP']=metal;S.update(screws);changed={f'{fam}{k}' for fam in ['C','T'] for k in range(8)}|{'M-TMP'}
 P['M-TMP']['dimensions']={**P['M-TMP']['dimensions'],'length_m':94*I,'width_m':94*I,'depth_m':24*I,'width_in':94,'depth_in':24,'length_display':'94in overall bridge assembly span','section_display':'Eight-L bridge assembly; not stock'};P['M-TMP']['nominal_dimensions']=copy.deepcopy(P['M-TMP']['dimensions']);P['M-TMP']['notes']=['External candidate: eight radial upper webs, flush C/T bridging legs and horizontal seats on T tops.','Forty actual holes, each paired with one modeled GRK RSS14221 envelope. Original24-hole display pattern is retired.','Steel thickness/return/weld geometry and this custom steel-to-wood joint capacity remain unverified.'];P['M-TMP']['source_geometry_metadata']={'revision':'EXTERNAL40-RSS-BRIDGE','reference_star_span_in':90,'new_bridge_span_in':94,'hole_count':40,'capacity_verified':False};P['M-TMP']['display_assumptions']={'steel_thickness_in':.125,'rigid_rotation_y_degrees':-4.7,'weld_beads_modeled':False,'capacity_verified':False}
 P['M-TMP'].update(name='Eight-L C/T bridge connector research candidate',display_holes=holes,temporary=True,research_only=True,reference_dimensions={'overall_span_in':94,'radial_strap_count':8,'bridge_plate_radial_span_in':[41,47],'bridge_plate_vertical_span_in':[85,109],'bridge_plate_thickness_in':.125,'total_holes':40},geometry_purpose='External user-requested bridge concept; capacity/fastener specification not established',fabrication_dimensions_valid=False)
 replacements={}
 for pid in sorted(changed|set(screw_ids)):
  q=native_record(S[pid],single=True);p=P[pid];p.update(q);p['faces']=p['triangles'];p['fit_geometry']={**p.get('fit_geometry',{}),**volume_centroid(S[pid])};p['research_only']=True;replacements[pid]=p
 allparts=[replacements.get(p['id'],copy.deepcopy(p)) for p in model['parts']]+[replacements[p] for p in screw_ids]
 actual={p['id']:p for p in allparts};ss={pid:native_solid(p) for pid,p in actual.items() if p.get('triangles')};physical={pid:p for pid,p in actual.items() if p.get('is_timber') or p.get('is_fastener') or pid in ['M-TMP','PLY']};scene=Scene('external-bridge',physical,{pid:ss[pid] for pid in physical},{pid:np.zeros(3) for pid in physical});static=audit_initial_scene(scene);print('STATIC',static['status'],static['collisions'][:5],flush=True)
 foot_ids=['C0','T0']+(['CP0'] if 'CP0' in actual else []);foot=Scene('external-foot',{p:actual[p] for p in foot_ids},{p:ss[p] for p in foot_ids},{p:np.zeros(3) for p in foot_ids});down=check_stage(foot,['C0'],[0,-.1,0],stop_first=False);up=check_stage(foot,['C0'],[0,.1,0],stop_first=False);bearing=sum(float(f['area_in2']) for f in contacts(ss['C0'],ss['T0']) if np.linalg.norm(np.asarray(f['normal_on_rafter'])-[0,-1,0])<1e-8);source_bearing=sum(float(f['area_in2']) for f in contacts(original['C0'],original['T0']) if np.linalg.norm(np.asarray(f['normal_on_rafter'])-[0,-1,0])<1e-8);assert abs(bearing-source_bearing)<1e-6 and down['status']=='BLOCKED' and up['status']=='BLOCKED'
 bearing_faces={pid:contacts(ss['M-TMP'],ss[pid]) for pid in ['C0','T0']};assert all(sum(float(x['area_in2']) for x in v)>1 for v in bearing_faces.values())
 # All40 initial axial withdrawals, with every other physical actor retained.
 screw_proofs=[]
 for pid in screw_ids:
  axis=np.asarray(P[pid]['withdrawal_direction']);proof=check_stage(scene,[pid],axis*3.25*I,stop_first=True);screw_proofs.append({'id':pid,'proof':proof});print(pid,proof['status'],proof['collisions'],flush=True)
 # Fixture slide after explicit screw prerequisites; existing CP remains.
 ids=[p for p in physical if p not in screw_ids];local=Scene('bridge-with-screws-removed',{p:actual[p] for p in ids},{p:ss[p] for p in ids},{p:np.zeros(3) for p in ids});fixture_probe=check_stage(local,['M-TMP'],[0,.15,0],stop_first=True);down_bearing=check_stage(local,['M-TMP'],[0,-.1,0],stop_first=True);tab_bearing=sum(float(f['area_in2']) for f in bearing_faces['T0'] if np.linalg.norm(np.asarray(f['normal_on_rafter'])-[0,-1,0])<1e-8);assert abs(tab_bearing-3)<1e-6;print('M UP',fixture_probe['status'],fixture_probe['collisions'],'M DOWN',down_bearing['status'],down_bearing['collisions'],'bearing',tab_bearing,flush=True)
 report={'scope':'Separate external actual-solid bridge candidate. Static primary/local screw probes only; no full building sequence, thread mechanics, steel/screw capacity or public certificate.','input_model':str(source),'input_sha256':hashlib.sha256(raw).hexdigest(),'generator_path':str(Path(__file__).resolve()),'generator_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'changes':'Retain recognizable upper radial star; replace rotated original outer legs/display holes with flush bridging plates and40 actual holes/screw envelopes.','holes':holes,'screw_count':40,'engagement':engagement,'static_primary':static,'M_to_C_T_contact_faces':bearing_faces,'CP_present':'CP0' in actual,'C0_source_bearing_in2':source_bearing,'C0_bearing_in2':bearing,'C0_down_probe':down,'C0_up_with_CP_probe':up,'screw_initial_withdrawals':screw_proofs,'fixture_up_after_screw_prerequisite':fixture_probe,'fixture_down_with_screws_removed':down_bearing,'steel_downward_bearing_area_in2_per_T0':tab_bearing,'sequence':'Seat C/L on T and retain the source variant foot restraint (CP where present); then install/fasten bridge. Horizontal T-top tabs support the steel before its first screw. Remove40 screws and lift bridge UP.15m clear before CP/foot release.','integration':'Merge with the timber patch only after review; add screw bores as physical cavity mates and all40 screws to complete display/inventory. New C/T screw bores are below the new upper joints and preserve the existing foot/T-tail/CP geometry.'}
 candidate={**model,'parts':allparts,'status':'UNVERIFIED EXTERNAL BRIDGE CANDIDATE','research_only':True};save(out/'bridge-candidate-patch.json',{'scope':report['scope'],'input_sha256':report['input_sha256'],'replace_parts':{p:replacements[p] for p in changed},'add_parts':{p:replacements[p] for p in screw_ids}});save(out/'bridge-candidate-model.json',candidate);save(out/'bridge-candidate-report.json',report)
 assert static['status']=='PASS',static['collisions'];assert all(p['proof']['status']=='PASS' for p in screw_proofs);assert fixture_probe['status']=='PASS' and down_bearing['status']=='BLOCKED',fixture_probe

# TIMESTAMP END 2026-11-05T04:51:00+00:00 | REVISION R000023
