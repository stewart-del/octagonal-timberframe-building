# TIMESTAMP START 2026-11-05T08:15:49+00:00 | REVISION R000034
# Derived from external exact tail clipping SHA256 1feb70524c765a6635fef47b03313ff817433b15ae0e8ae05fab0e8c8dd205ec.
"""External owner-selected compound eave trim after stopped R backing."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
D=Path(__file__).resolve().parent;sys.path.insert(0,str(D))
import copy,hashlib,json,math,numpy as np,manifold3d as m
from hip_backing_recipe import I,TOL,native_record,native_solid,keep_at_most,contacts
from cupola_joinery_recipe import amount,diff,save,UP
from plan_architectural_disassembly import Scene,audit_initial_scene,check_stage,apply_stage,boxes_overlap
from audit_cavity_fit import inspect_mesh

def exact_clipped_record(p,normals,offset):
 """Clip tail triangles while retaining every unaffected source vertex."""
 v=[np.array(q,float) for q in p['vertices']];facets=[list(t) for t in p['triangles']]
 for n in normals:
  cache={};out=[];ring=set()
  def crossing(i,j):
   key=tuple(sorted([i,j]))
   if key not in cache:
    a,b=(v[k] for k in key);da=float(a@n-offset);db=float(b@n-offset);q=a+(b-a)*(da/(da-db));cache[key]=len(v);v.append(q)
   return cache[key]
  for face in facets:
   poly=[]
   for i,j in zip(face,face[1:]+face[:1]):
    di=float(v[i]@n-offset);dj=float(v[j]@n-offset)
    if di<=1e-12:poly.append(i)
    if (di < -1e-12 and dj>1e-12) or (dj < -1e-12 and di>1e-12):poly.append(crossing(i,j))
   poly=list(dict.fromkeys(poly))
   if len(poly)>=3:
    out.append(poly)
    ring|={i for i in poly if abs(float(v[i]@n-offset))<=1e-10}
  if len(ring)>=3:
   origin=np.mean([v[i] for i in ring],axis=0);u=np.cross(n,np.eye(3)[np.argmin(abs(n))]);u/=np.linalg.norm(u);w=np.cross(n,u);cap=sorted(ring,key=lambda i:math.atan2(float((v[i]-origin)@w),float((v[i]-origin)@u)));out.append(cap)
  facets=out
 triangles=[]
 for face in facets:
  if len(face)==3:triangles.append(face);continue
  pts=np.array([v[i] for i in face]);normal=np.cross(pts[1]-pts[0],pts[2]-pts[0]);length=np.linalg.norm(normal)
  if length<1e-14:
   for j in range(2,len(pts)-1):
    normal=np.cross(pts[j]-pts[0],pts[j+1]-pts[0]);length=np.linalg.norm(normal)
    if length>1e-14:break
  if length<1e-14:continue
  normal/=length;u=np.cross(normal,np.eye(3)[np.argmin(abs(normal))]);u/=np.linalg.norm(u);w=np.cross(normal,u);xy=np.column_stack([(pts-pts[0])@u,(pts-pts[0])@w])
  for t in m.triangulate([xy],epsilon=1e-13,allow_convex=False):triangles.append([face[int(i)] for i in t])
 used=sorted(set(i for t in triangles for i in t));mapping={i:j for j,i in enumerate(used)};vv=np.array([v[i] for i in used]);tt=np.array([[mapping[i] for i in t] for t in triangles],dtype=np.uint64);audit=inspect_mesh(vv,tt,require_single=True);assert audit['status']=='PASS',audit
 result={'vertices':vv.tolist(),'triangles':tt.tolist()};s=native_solid(result);assert str(s.status())=='Error.NoError';result['volume_m3']=s.volume();result['edges']=[list(e) for e in sorted({tuple(sorted((int(t[i]),int(t[(i+1)%3])))) for t in tt for i in range(3)})];return result

def build(model):
 """Compound trim the real backed tails; preserve every actual mating area."""
 from cupola_joinery_recipe import volume_centroid,union
 P={p['id']:copy.deepcopy(p) for p in model['parts']}
 original={pid:native_solid(p) for pid,p in P.items() if p.get('triangles') and (p.get('is_timber') or p.get('is_fastener') or pid in ['M-TMP','PLY'])}
 S=dict(original);replacement={};rows=[];contact_rows=[];q=200*math.cos(math.pi/8)*I
 for k in range(8):
  pid=f'R{k}';before=S[pid];after=before;normals=[]
  for a in [(k-.5)*math.pi/4,(k+.5)*math.pi/4]:
   n=np.array([math.cos(a),0.,-math.sin(a)]);normals.append(n);after=keep_at_most(after,n,q)
  cut=before-after;record=exact_clipped_record(P[pid],normals,q);actual=native_solid(record)
  assert diff(after,actual)<=TOL
  pieces=[]
  for n in normals:
   part=before.trim_by_plane(n.tolist(),q)
   if part.volume()<=1e-16:continue
   clean=m.Manifold.hull_points(np.asarray(part.to_mesh64().vert_properties)[:,:3]);assert diff(part,clean)<=TOL
   pieces.append(native_record(clean,True))
  assert diff(cut,union([native_solid(p) for p in pieces]))<=TOL
  p=copy.deepcopy(P[pid]);p.update(record);p['faces']=p['triangles'];p['fit_geometry']={**p.get('fit_geometry',{}),**volume_centroid(actual)}
  p['additional_declared_exterior_cuts']={'scope':'Separate closed backing and compound-eave corner offcuts; preserve the original source declaration.','pieces':p.get('additional_declared_exterior_cuts',{}).get('pieces',[])+pieces}
  p['eave_miter']={'outside_octagon_face_apothem_in':q/I,'world_cutting_planes':[{'normal':n.tolist(),'constant_m':q} for n in normals],'normal_overhang_changed':False}
  for mid,other in original.items():
   if mid==pid or not boxes_overlap(before.bounding_box(),other.bounding_box()):continue
   pairs=[contacts(before,other),contacts(actual,other)];groups=[]
   for side,items in enumerate(pairs):
    for item in items:
     normal=np.asarray(item['normal_on_rafter']);normal/=np.linalg.norm(normal)
     group=next((g for g in groups if normal@g['normal']>1-1e-9),None)
     if group is None:group={'normal':normal,'areas':[0.,0.]};groups.append(group)
     group['areas'][side]+=item['area_in2']
   error=max([abs(g['areas'][0]-g['areas'][1]) for g in groups] or [0.])
   assert error<=1e-6,(pid,mid,'Eave trim altered mating contact',error)
   if groups:contact_rows.append({'id':pid,'mate':mid,'maximum_contact_area_difference_in2':error})
  rows.append({'id':pid,'removed_tail_in3':amount(cut)/I**3,'readback_difference_in3':diff(after,actual)/I**3,'explicit_offcut_count':len(pieces)})
  replacement[pid]=p;P[pid]=p;S[pid]=actual
 scene=Scene('compound-eave-primary',{pid:P[pid] for pid in S},S,{pid:np.zeros(3) for pid in S});static=audit_initial_scene(scene);assert static['status']=='PASS',static
 probes=[]
 for k in range(8):
  pid=f'R{k}';keep=[p for p in S if not p.startswith('J')];trial=Scene('eave-hip-release',{p:P[p] for p in keep},{p:S[p] for p in keep},{p:np.zeros(3) for p in keep})
  radial=np.array([math.cos(k*math.pi/4),0.,-math.sin(k*math.pi/4)])
  for name,delta in [('UP1in',UP*I),('OUT4in',radial*4*I)]:
   proof=check_stage(trial,[pid],delta,stop_first=True)
   if model.get('independent_hip_entry_revision'):assert proof['status']=='PASS',(pid,name,proof)
   probes.append({'id':pid,'segment':name,'proof':proof})
   if proof['status']!='PASS':break
   apply_stage(trial,[pid],delta,proof,name)
 return replacement,{'status':'LOCAL_PASS' if all(p['proof']['status']=='PASS' for p in probes) else 'LOCAL_STATIC_CONTACT_PASS_LEGACY_MOTION_BLOCKED',
  'scope':'Actual eave trim, preserved mate contact, primary static and initial hip paths only; full architecture/stock/cavity/strength remain separate.',
  'static':static,'contact_checks':contact_rows,'members':rows,'initial_hip_paths':probes,'face_apothem_in':q/I,'normal_overhang_changed':False}
# TIMESTAMP END 2026-11-05T08:15:49+00:00 | REVISION R000034
