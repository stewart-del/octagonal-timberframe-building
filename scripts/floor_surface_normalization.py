# TIMESTAMP START 2026-11-05T08:36:47+00:00 | REVISION R000035
"""Strict occupied-floor boundary normalization after actual fastener bores.

All edits are bounded by occupied symmetric difference in metres and inches.
Stock-local transforms are rigid isometries; the hardware and bores are not
replaced with simplified stock. Shared prototypes remain byte-identical.
"""
import argparse,copy,gzip,hashlib,json,math,os,sys,time,itertools
from concurrent.futures import ProcessPoolExecutor,as_completed
from pathlib import Path
import numpy as np
import manifold3d as m
REPO=Path(__file__).resolve().parents[1]
from physical_data import read_physical_json,occupied_part
from audit_cavity_fit import inspect_mesh,FACE_AREA_MIN_M2
from audit_revised_joinery import native_solid
from plan_architectural_disassembly import boxes_overlap
I=.0254;TOL=1e-6*I**3

def save(path,data):path.write_text(json.dumps(data,separators=(',',':'))+'\n')
def amount(s):return max(0.,float(s.volume()))
def difference(a,b):return abs(float((a-b).volume()))+abs(float((b-a).volume()))
def frame(part):
 if part.get('stock_frame'):
  f=part['stock_frame'];B=np.column_stack([f['axis'],f['width'],f['depth']]);kind='recorded stock_frame'
 elif part['id'].startswith('FLOOR-RIM-'):
  k=int(part['id'].rsplit('-',1)[1]);a=-(k+.5)*math.pi/4;width=np.array([math.cos(a),0,math.sin(a)]);axis=np.cross(width,[0,1,0]);B=np.column_stack([axis,width,[0,1,0]]);kind='regular-octagon rim axes from exact rim index'
 elif part['id'].startswith('POST-BEARING-STAND-'):
  k=int(part['id'].split('-')[3]);a=k*math.pi/4;axis=np.array([math.cos(a),0,-math.sin(a)]);B=np.column_stack([axis,[0,1,0],np.cross(axis,[0,1,0])]);kind='recorded stand index radial/vertical plate axes'
 else:B=np.eye(3);kind='world-axis local frame'
 # Exact quarter-turn axes should not acquire a spurious6e-17 component from
 # sin/cos evaluation. This changes the reference frame, never stock vertices.
 B[abs(B)<1e-15]=0.;B[abs(B-1)<1e-15]=1.;B[abs(B+1)<1e-15]=-1.
 assert np.max(abs(B.T@B-np.eye(3)))<1e-12
 if np.linalg.det(B)<0:B[:,2]*=-1
 assert abs(np.linalg.det(B)-1)<1e-12
 origin=np.asarray(part.get('center',np.asarray(part['vertices']).mean(0)),float)
 return origin,B,kind
def arrays(s):
 q=s.to_mesh64();return np.array(np.asarray(q.vert_properties)[:,:3],dtype=float,order='C'),np.array(q.tri_verts,dtype=np.uint64,order='C')
def quick(s,B,origin):
 if str(s.status())!='Error.NoError' or s.volume()<=0 or len(s.decompose())!=1:return False,None
 v,f=arrays(s);world=v*I@B.T+origin;area=np.linalg.norm(np.cross(world[f[:,1]]-world[f[:,0]],world[f[:,2]]-world[f[:,0]]),axis=1)/2
 return bool(len(area) and np.min(area)>FACE_AREA_MIN_M2),(world,f)

def regular_local(shape,plane_tolerance_in=1e-9/I):
 """Signed support-plane contour rebuild, in local inches.

 Same regular_boundary algorithm as production, with physical plane/weld
 distance1nm expressed in inches and volume units explicitly in³. No source
 auditor edits or triangle-pruning shortcut. Every resulting solid is checked.
 """
 vertices,faces=arrays(shape);groups=[];tol=plane_tolerance_in;scale=1e6
 for ids in faces:
  p=vertices[ids];n=np.cross(p[1]-p[0],p[2]-p[0]);ln=np.linalg.norm(n)
  if ln<1e-20:continue
  n/=ln
  if n[np.argmax(abs(n))]<0:n=-n
  group=next((g for g in groups if np.linalg.norm(n-g['n'])<1e-9 and np.max(abs((p-g['origin'])@g['n']))<tol),None)
  if group is None:
   axis=np.eye(3)[np.argmin(abs(n))];u=np.cross(n,axis);u/=np.linalg.norm(u);group={'n':n,'origin':p[0],'basis':np.column_stack([u,np.cross(n,u)]),'contours':[]};groups.append(group)
  group['contours'].append((p-group['origin'])@group['basis']*scale)
 pool=[];regions=[]
 for point in vertices:
  if not any(np.linalg.norm(point-v)<=tol for v in pool):pool.append(point.copy())
 def weld(point):
  dist=np.linalg.norm(np.asarray(pool)-point,axis=1);nearest=int(np.argmin(dist))
  if dist[nearest]<=tol:return nearest
  pool.append(point);return len(pool)-1
 for group in groups:
  for sign,fill in [(1,m.FillRule.Positive),(-1,m.FillRule.Negative)]:
   section=m.CrossSection(group['contours'],fill)
   if section.is_empty():continue
   loops=[]
   for poly in section.to_polygons():
    points=group['origin']+np.asarray(poly)/scale@group['basis'].T;loops.append([weld(p) for p in points])
   regions.append((group,sign,loops))
 points=np.asarray(pool);out=[]
 for group,sign,loops in regions:
  contours=[];ids=[]
  for loop in loops:
   split=[]
   for start,end in zip(loop,loop[1:]+loop[:1]):
    a,b=points[start],points[end];edge=b-a;length2=float(edge@edge)
    if length2<=tol*tol:continue
    t=(points-a)@edge/length2;dist=np.linalg.norm(points-(a+t[:,None]*edge),axis=1);middle=np.flatnonzero((t>1e-10)&(t<1-1e-10)&(dist<=tol));split.extend([start]+sorted(middle.tolist(),key=lambda k:t[k]))
   if len(split)<3:continue
   contours.append((points[split]-group['origin'])@group['basis']);ids.extend(split)
  if not contours:continue
  for tri in m.triangulate(contours,epsilon=1e-12,allow_convex=False):
   mapped=[ids[int(i)] for i in tri];out.append(mapped if sign>0 else mapped[::-1])
 used=sorted(set(i for tri in out for i in tri));mp={x:j for j,x in enumerate(used)};result=m.Manifold(m.Mesh64(points[used],np.asarray([[mp[i] for i in tri] for tri in out],np.uint64)))
 assert str(result.status())=='Error.NoError',('local signed boundary',str(result.status()))
 assert abs(result.volume()-shape.volume())<=1e-6,'Local boundary changed signed volume'
 return result

def collapse_short_edges(shape,epsilon_in):
 """Bounded local mesh contraction; this edits geometry, never the auditor.

 Only endpoints of existing native edges shorter than epsilon may coincide.
 A removed indexed face has become topologically zero-area after that weld;
 native reconstruction must accept its complete closed boundary. Every
 resulting mesh still faces strict raw inspection and TWO occupied diffs.
 """
 vertices,faces=arrays(shape);parents=list(range(len(vertices)))
 def root(index):
  while parents[index]!=index:index=parents[index]
  return index
 edges={tuple(sorted((int(a),int(b)))) for tri in faces for a,b in zip(tri,np.roll(tri,1))}
 for a,b in sorted(edges,key=lambda pair:(np.linalg.norm(vertices[pair[0]]-vertices[pair[1]]),pair)):
  a,b=root(a),root(b)
  if a!=b and np.linalg.norm(vertices[a]-vertices[b])<=epsilon_in:parents[max(a,b)]=min(a,b)
 contracted=np.array([[root(int(i)) for i in tri] for tri in faces])
 contracted=contracted[(contracted[:,0]!=contracted[:,1])&(contracted[:,1]!=contracted[:,2])&(contracted[:,2]!=contracted[:,0])]
 used=sorted(set(contracted.ravel()));remap={old:new for new,old in enumerate(used)}
 candidate=m.Manifold(m.Mesh64(np.array(vertices[used],order='C'),np.array([[remap[i] for i in tri] for tri in contracted],np.uint64)))
 return candidate,{'contracted_native_vertices':sum(root(i)!=i for i in range(len(vertices))),'removed_index_degenerate_faces':len(faces)-len(contracted)}

def normalize_one(part,original_failure=None,allow_regular=True):
 pid=part['id'];started=time.monotonic();origin,B,kind=frame(part);v=np.asarray(part['vertices'],float);f=np.asarray(part['triangles'],np.uint64);local_v=(v-origin)@B/I;local=m.Manifold(m.Mesh64(local_v,f));original=native_solid(part);attempts=[]
 def evaluate(candidate,method,epsilon=None):
  ok,pair=quick(candidate,B,origin)
  if not ok:attempts.append({'method':method,'epsilon_in':epsilon,'status':'QUICK_REJECT'});return None
  w,t=pair;record=json.loads(json.dumps({'vertices':w.tolist(),'triangles':t.tolist()}));w=np.asarray(record['vertices'],float);t=np.asarray(record['triangles'],np.uint64);proof=inspect_mesh(w,t,require_single=True)
  if proof['status']!='PASS':attempts.append({'method':method,'epsilon_in':epsilon,'status':'RAW_REJECT','failures':proof['failures']});return None
  readback=native_solid(record);world_error=difference(original,readback);backlocal=m.Manifold(m.Mesh64(np.array((w-origin)@B/I,order='C'),np.array(t,dtype=np.uint64,order='C')));local_error=difference(local,backlocal)*I**3;volume_delta=abs(original.volume()-readback.volume())
  row={'method':method,'epsilon_in':epsilon,'status':'PASS' if max(world_error,local_error,volume_delta)<=TOL else 'OCCUPIED_REJECT','world_symmetric_difference_m3':world_error,'local_symmetric_difference_m3':local_error,'absolute_volume_delta_m3':volume_delta};attempts.append(row)
  if row['status']!='PASS':return None
  return record,{'id':pid,'status':'PASS','method':method,'epsilon_in':epsilon,'frame_kind':kind,'origin_m':origin.tolist(),'basis_columns':B.tolist(),'input_triangles':len(f),'output_triangles':len(t),'input_failure':original_failure,'raw_readback':proof,**{k:v for k,v in row.items() if k not in ['status']},'attempts':attempts,'elapsed_seconds':time.monotonic()-started}
 # Invertible local-frame round trip before considering any simplification.
 for eps_m in [0,1e-10,1e-9,1e-8,1e-7]:
  epsilon=eps_m/I;candidate=local if eps_m==0 else local.simplify(epsilon);result=evaluate(candidate,'stock-local inch native roundtrip' if eps_m==0 else 'stock-local inch simplify',epsilon)
  if result:return result
 if pid.startswith('POST-BEARING-STAND-'):
  # Rotated slot intersections retain microscopic native edges even after
  # simplify. Contract those actual short edges, then retriangulate locally.
  seed=local.simplify(1e-8/I)
  for edge_m in [1e-8,2e-8,5e-8,1e-7]:
   candidate,contraction=collapse_short_edges(seed,edge_m/I)
   if str(candidate.status())!='Error.NoError':continue
   candidate=candidate.simplify(1e-8/I);result=evaluate(candidate,'stock-local short-edge contraction then native retriangulation',1e-8/I)
   if result:result[1].update({'edge_contraction_limit_m':edge_m,**contraction});return result
 if allow_regular:
  for plane_m in [1e-10,1e-9]:
   candidate=regular_local(local,plane_m/I)
   for eps_m in [0,1e-10,1e-9,1e-8,1e-7]:
    c=candidate if eps_m==0 else candidate.simplify(eps_m/I);result=evaluate(c,'stock-local signed planar boundary then simplify',eps_m/I)
    if result:result[1]['plane_weld_tolerance_m']=plane_m;return result
 raise AssertionError({'id':pid,'attempts':attempts,'failure':'No strict occupied-shape-preserving raw boundary found'})

FIXTURE=Path(__file__).with_name('fixtures')/'floor-boundary-failures.json.gz'
def load_fixture():
 return json.loads(gzip.decompress(FIXTURE.read_bytes()))

def normalize_parts(parts):
 """Repair current occupied records; retain every other descriptor verbatim."""
 fixture=load_fixture();targets=fixture['failures'];seen=set();result=[];proofs=[]
 for part in parts:
  if part['id'] not in targets:
   result.append(part);continue
  seen.add(part['id']);record,proof=normalize_one(part)
  proof['input_mesh_sha256']=hashlib.sha256(json.dumps({'vertices':part['vertices'],'triangles':part['triangles']},separators=(',',':')).encode()).hexdigest()
  fixed={**part,**record,'volumeM3':native_solid(record).volume()}
  result.append(fixed);proofs.append(proof)
  print('Normalized occupied floor boundary',part['id'],proof['method'],flush=True)
 assert seen==set(targets),('Missing expected floor boundaries',set(targets)-seen)
 return result,{'scope':'Current generated occupied-mesh normalization only; strict raw inspection and world/local occupied comparisons. Complete static/motion/stock audits are separate.','status':'PASS','per_record_difference_limit_m3':TOL,'source_normalizer_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'source_regression_fixture_sha256':hashlib.sha256(FIXTURE.read_bytes()).hexdigest(),'records':proofs}

def main():
 from physical_data import write_physical_json
 parser=argparse.ArgumentParser();parser.add_argument('--source',required=True,type=Path);parser.add_argument('--output',required=True,type=Path);parser.add_argument('--report',required=True,type=Path);a=parser.parse_args()
 data=read_physical_json(a.source);parts,proof=normalize_parts(data['parts']);data={**data,'parts':parts,'boundaryNormalization':proof};a.output.parent.mkdir(parents=True,exist_ok=True);write_physical_json(a.output,data)
 proof={**proof,'source_sha256':hashlib.sha256(a.source.read_bytes()).hexdigest(),'output_sha256':hashlib.sha256(a.output.read_bytes()).hexdigest()};a.report.write_text(json.dumps(proof,indent=2)+'\n')

if __name__=='__main__':main()

# TIMESTAMP END 2026-11-05T08:36:47+00:00 | REVISION R000035
