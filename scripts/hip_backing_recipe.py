# TIMESTAMP START 2026-11-05T08:15:49+00:00 | REVISION R000034
# Derived from independently checked hip_backing_candidate.py SHA256 4df09f069c51a86a91b6ae72684753e6f1c9de6a311c4cbd2165973db334152e.
"""Stage stopped hip backing while preserving actual mating contacts."""
import sys
sys.dont_write_bytecode=True
import argparse,copy,hashlib,json,math,time
from pathlib import Path
import numpy as np
import manifold3d as m
D=Path(__file__).resolve().parent
sys.path.insert(0,str(D))
from shapely.geometry import Polygon
from collections import defaultdict
from cupola_joinery_recipe import I,TOL,UP,native_solid,native_record as raw_record,amount,diff,save,union
from export_top_entry_cavities import stock
from step_lap import regular_boundary,triangles
# TIMESTAMP START 2026-11-05T08:52:17+00:00 | REVISION R000038
from closed_backing_offcuts import closed_stopped_backing_offcuts
from audit_cavity_fit import inspect_mesh
# TIMESTAMP END 2026-11-05T08:52:17+00:00 | REVISION R000038
from plan_architectural_disassembly import Scene,check_stage,apply_stage,audit_initial_scene,boxes_overlap

CLEANUPS=[]
def native_record(shape,single=False):
 try:return raw_record(shape,single)
 except AssertionError:
  positive=[q for q in shape.decompose() if q.volume()>1e-16]
  if positive:
   candidate=m.Manifold.compose(positive);error=diff(shape,candidate)
   if error<=TOL:
    try:
     record=raw_record(candidate,single);CLEANUPS.append({'method':'Drop only occupied-null CSG surface components','occupied_difference_in3':error/I**3,'before_components':len(shape.decompose()),'positive_components':len(positive)});return record
    except AssertionError:pass
  clean=regular_boundary(shape);error=diff(shape,clean);assert error<=TOL
  record=raw_record(clean,single);CLEANUPS.append({'occupied_difference_in3':error/I**3,'before_triangles':len(shape.to_mesh64().tri_verts),'after_triangles':len(record['triangles'])});return record

def contacts(a,b):
 # Independent GEOS polygon intersections of actual triangle patches.
 # This changes no geometry or test threshold; every coplanar surface pair
 # is checked using the source contact routine's normal/plane tolerances.
 ta,na,da=triangles(a);tb,nb,db=triangles(b);areas=defaultdict(float)
 for idx,t in enumerate(ta):
  n=na[idx];same=np.where((nb@n < -1+1e-9)&(np.abs(tb[:,0]@n-da[idx])<1e-8))[0]
  u=np.cross(n,np.eye(3)[np.argmin(abs(n))]);u/=np.linalg.norm(u);v=np.cross(n,u);basis=np.array([u,v]).T;origin=t[0];poly=Polygon((t-origin)@basis)
  for k in same:
   area=poly.intersection(Polygon((tb[k]-origin)@basis)).area
   if area>1e-12:areas[tuple(np.round(n,8))]+=area
 return [{'normal_on_rafter':list(key),'area_in2':area/I**2,'method':'GEOS intersection of actual coplanar raw triangle polygons'} for key,area in sorted(areas.items())]

def keep_at_most(s,n,c):
 n=np.asarray(n,float);length=np.linalg.norm(n)
 return s.trim_by_plane((-n/length).tolist(),-c/length)

def topfaces(shape,n,c):
 v=np.asarray(shape.to_mesh64().vert_properties)[:,:3];t=np.asarray(shape.to_mesh64().tri_verts);normal=np.asarray(n)/np.linalg.norm(n);tris=[];area=0.
 for tri in t:
  points=v[tri];cross=np.cross(points[1]-points[0],points[2]-points[0]);a=np.linalg.norm(cross)/2
  if a>1e-15 and np.dot(cross/np.linalg.norm(cross),normal)>1-1e-9 and np.max(np.abs(points@np.asarray(n)-c))<1e-8:
   tris.append(points.tolist());area+=a
 return {'unit_normal':normal.tolist(),'plane_normal_unnormalized':np.asarray(n).tolist(),'plane_constant_m':c,'area_in2':area/I**2,'world_triangles_m':tris}

def build(source,out):
 CLEANUPS.clear()
 started=time.time();out.mkdir(exist_ok=True,parents=True);raw=source.read_bytes();sha=hashlib.sha256(raw).hexdigest();(out/'frozen-roof-support-model.json').write_bytes(raw)
 model=json.loads(raw);P={p['id']:copy.deepcopy(p) for p in model['parts']};S={k:native_solid(p) for k,p in P.items() if p.get('triangles') and(p.get('is_timber') or p.get('is_fastener') or k in ['PLY','M-TMP'])};original=dict(S)
 rows=[];replacement={};backcuts={};faces={};stop=45*I;coef=math.tan(math.pi/8)/3
 for k in range(8):
  pid=f'R{k}';p=P[pid];r=np.array([math.cos(k*math.pi/4),0.,-math.sin(k*math.pi/4)]);w=np.asarray(p['stock_frame']['width']);c=next(q['constant'] for q in p['proposed_stock_planes_inches'] if q['normal'][2]>.9)*I
  normals=[UP+r/3+w*coef,UP+r/3-w*coef]
  blanket=stock(p);fully_backed=S[pid]
  for n in normals:fully_backed=keep_at_most(fully_backed,n,c)
  unbounded=S[pid]-fully_backed;cut=unbounded.trim_by_plane(r.tolist(),stop);backed=S[pid]-cut
  # Keep the two independent exterior wedge tools separate. Joining two
  # stock wedges along their zero-area ridge can create a non-regular raw
  # surface even though each wedge is a valid closed machining offcut.
  rawcuts=[blanket.trim_by_plane((n/np.linalg.norm(n)).tolist(),c/np.linalg.norm(n)).trim_by_plane(r.tolist(),stop) for n in normals]
# TIMESTAMP START 2026-11-05T08:15:49+00:00 | REVISION R000034
  try:geometry=native_record(backed,single=True)
  except AssertionError:
   # A rotated boundary is admissible only after checking THIS actual input
   # and THIS target occupied shape against the already accepted seed.
   assert k>0 and 'R0' in replacement
   input_error=diff(original[pid],original['R0'].rotate([0,45*k,0]));assert input_error<=TOL,('Non-isometric backing source',pid,input_error)
   candidate=native_solid(replacement['R0']).rotate([0,45*k,0]);target_error=diff(backed,candidate)
   assert target_error<=TOL,('Rotated backing differs from actual target',pid,target_error)
   geometry=raw_record(candidate,single=True);CLEANUPS.append({'id':pid,'method':'Verified rigid isometry of accepted actual R0 boundary','source_input_difference_in3':input_error/I**3,'target_occupied_difference_in3':target_error/I**3})
  readback=native_solid(geometry);assert diff(backed,readback)<=TOL
# TIMESTAMP END 2026-11-05T08:15:49+00:00 | REVISION R000034
  protected=keep_at_most(S[pid],r,stop);assert amount(cut^protected)<=TOL
  own_connections=[j for j in model['tenon_schedule'] if j.get('donor')==pid]
  jointloss={j['id']:amount(cut^native_solid(j['connector']))/I**3 for j in own_connections};assert all(v<=1e-6 for v in jointloss.values())
  old_entry=model.get('joinery_entry_regions',{}).get(pid);entry=native_solid(old_entry) if old_entry else union([]);assert amount(cut^entry)<=TOL
  original_declared=p.get('declared_exterior_cut');ext=native_solid(original_declared) if original_declared else union([]);assert amount(ext^cut)<=TOL
# TIMESTAMP START 2026-11-05T08:52:17+00:00 | REVISION R000038
  closed_offcuts=closed_stopped_backing_offcuts(original[pid],normals,c,r,stop,inspect_mesh,native_solid,removed_reference=cut)
  p.update(geometry);p['faces']=p['triangles'];p['additional_declared_exterior_cuts']={'scope':'Separate closed top-backing offcuts; preserve original source declaration without a cofacial union.','pieces':closed_offcuts['pieces']};p['research_only']=True;p['hip_backing_research']={'radial_start_in':45.,'scope':'Two-plane top backing only outboard of stopped inner collar; no joint redesign or capacity approval.','unchanged_inner_collar':'All actual source material at radial coordinate <=45in retained.','planes_world_m':[{'normal':n.tolist(),'constant':c} for n in normals]}
# TIMESTAMP END 2026-11-05T08:52:17+00:00 | REVISION R000038
  p['notes']=[note for note in p.get('notes',[]) if 'Flat rectangular top face' not in note]+['EXTERNAL OPTION: two-plane hip top backing starts radially45in from center; protected cupola shoulder collar remains unchanged. No structural/fabrication approval.']
# TIMESTAMP START 2026-11-05T08:52:17+00:00 | REVISION R000038
  replacement[pid]=p;S[pid]=readback;P[pid]=p;backcuts[pid]={'actual_top_offcut':closed_offcuts['combined_closed_record'],'closed_offcut_receipt':closed_offcuts['receipt'],'cutting_regions_within_independent_blank':[native_record(q,single=True) for q in rawcuts],'source_declared_exterior_cut':original_declared,'new_declared_exterior_cut':p['declared_exterior_cut']};faces[pid]=[topfaces(readback,n,c) for n in normals]
# TIMESTAMP END 2026-11-05T08:52:17+00:00 | REVISION R000038
  checks={'added_material_in3':amount(readback-original[pid])/I**3,'outside_source_in3':amount(readback-original[pid])/I**3,'reconstruction_difference_in3':diff(original[pid],readback+cut)/I**3,'protected_inner_collar_difference_in3':diff(protected,keep_at_most(readback,r,stop))/I**3,'joint_connector_loss_in3':jointloss,'entry_region_new_material_removal_in3':amount(cut^entry)/I**3,'readback_difference_in3':diff(backed,readback)/I**3}
  rows.append({'id':pid,'source_in3':original[pid].volume()/I**3,'actual_new_top_offcut_in3':cut.volume()/I**3,'fully_backed_unbounded_cut_in3':unbounded.volume()/I**3,'stopped_before_radial_in':45.,'support_face_areas_in2':[f['area_in2'] for f in faces[pid]],'checks':checks});print('BACKED',pid,cut.volume()/I**3,checks,flush=True)
 save(out/'backed-R-patch.json',{'scope':'External geometric candidate only. Eight R replacements composed against exact OUT candidate. No other part changed; stop collar requires matching deck inner cutout.','source_model':str(source),'source_model_sha256':sha,'replace_parts':replacement,'add_parts':{},'deck_inner_apothem_in':42.,'deck_common_plane_intercept_in':c/I})
 save(out/'backing-top-offcuts.json',{'scope':'Actual newly removed source-R material and independent blank-bounded cutting regions; prior source offcuts preserved separately.','source_model_sha256':sha,'parts':backcuts})
 save(out/'backed-R-support-faces.json',{'scope':'Actual readback triangle patches lying in each common-J roof support plane; top collar excluded.','source_model_sha256':sha,'parts':faces})
 # Compare actual contacts for the representative full family. Also verify
 # every radial family isometry, so altered top geometry is independently
 # checked against each actual source R rather than presumed to rotate.
 contactchecks=[]
 for k in range(8):
  pid=f'R{k}';error=diff(S[pid],S['R0'].rotate([0,45*k,0]));assert error<=TOL
  # All possible contact mates are retained; areas and centroids compared.
  for mid,other in original.items():
   if mid==pid or not boxes_overlap(original[pid].bounding_box(),other.bounding_box()):continue
   before=contacts(original[pid],other)
   if not before:continue
   after=contacts(S[pid],S.get(mid,other));groups=[]
   # Skinny, coplanar readback triangles can have slightly different raw
   # normals. Match patches using the SAME angular criterion as contact
   # recognition, rather than comparing rounded normal dictionary keys.
   for side,records in enumerate([before,after]):
    for f in records:
     n=np.asarray(f['normal_on_rafter']);n=n/np.linalg.norm(n);group=next((g for g in groups if np.dot(n,g['normal'])>1-1e-9),None)
     if group is None:group={'normal':n,'areas':[0.,0.]};groups.append(group)
     group['areas'][side]+=f['area_in2']
   maxerror=max([abs(g['areas'][0]-g['areas'][1]) for g in groups] or [0.]);assert maxerror<=1e-6,(pid,mid,maxerror)
   contactchecks.append({'r':pid,'mate':mid,'maximum_contact_area_difference_in2':maxerror,'before':before,'after':after})
  print('CONTACTS_PRESERVED',pid,flush=True)
 scene=Scene('external-stopped-hip-backing',P,S,{pid:np.zeros(3) for pid in S});scene.parts={pid:P[pid] for pid in S};static=audit_initial_scene(scene);assert static['status']=='PASS',static
 probes=[]
 for pid in [k for k in S if k.startswith('J')]:
  proof=check_stage(scene,[pid],UP*.3,stop_first=True)
  if model.get('independent_hip_entry_revision'):assert proof['status']=='PASS',(pid,proof)
  probes.append({'test':pid+' UP0.3m','scope':'All other current primary wood/physical fasteners stationary; covering prerequisites removed. Legacy closed-head variants retain their genuine blocked paths.','proof':proof});print('J_WITHDRAWAL',pid,proof['status'],flush=True)
 hipids=[k for k in S if not k.startswith('J')]
 for k in range(8):
  pid=f'R{k}';trial=Scene('external-independent-backed-hip',{q:P[q] for q in hipids},{q:S[q] for q in hipids},{q:np.zeros(3) for q in hipids})
  r=np.array([math.cos(k*math.pi/4),0.,-math.sin(k*math.pi/4)])
  for label,delta in [('UP1in',UP*I),('OUT4in',r*4*I)]:
   proof=check_stage(trial,[pid],delta,stop_first=True)
   if model.get('independent_hip_entry_revision'):assert proof['status']=='PASS',(pid,label,proof)
   probes.append({'test':pid+' '+label,'scope':'J rafters and covering removal prerequisites; all other primary actors stationary. Legacy closed-head paths are not claimed erectable.','proof':proof});print('R_WITHDRAWAL',pid,label,proof['status'],flush=True)
   if proof['status']!='PASS':break
   apply_stage(trial,[pid],delta,proof,label)
 report={'scope':'External stopped backing geometry/contact/initial withdrawal checks; not structural qualification, stock/cavity regeneration, full erection certificate or deployed geometry.','status':'LOCAL_PASS','source_model_path':str(source),'source_model_sha256':sha,'generator_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'tolerance_in3':1e-6,'radial_backing_start_in':45.,'deck_inner_apothem_in':42.,'deck_inner_hip_radius_in':42/math.cos(math.pi/8),'vertical_corner_cut_in':4*coef,'normal_packer_height_in':4*coef/math.sqrt(1+1/9+coef**2),'backing_cross_angle_deg':math.degrees(math.atan(coef/math.sqrt(1+1/9))),'rows':rows,'contact_checks':contactchecks,'static_primary_audit':static,'continuous_initial_withdrawals':probes,'geometry_preserving_boundary_cleanups':CLEANUPS,'elapsed_seconds':time.time()-started}
 report['initial_motion_complete']=all(p['proof']['status']=='PASS' for p in probes)
 if not report['initial_motion_complete']:report['status']='LOCAL_STATIC_CONTACT_PASS_LEGACY_MOTION_BLOCKED'
 save(out/'hip-backing-report.json',report);return report

# TIMESTAMP END 2026-11-05T08:15:49+00:00 | REVISION R000034
