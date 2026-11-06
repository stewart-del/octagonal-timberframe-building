# TIMESTAMP START 2026-11-05T19:01:25+00:00 | REVISION R000060
"""Common-local-frame single-piece sweep with a charged transform cover bound.

No collision threshold is changed. Starting world Mesh64 vertices are translated
to a common local frame before constructing the sweep. The frame preserves the
building X/Z axes and shifts only Y by the nearest integer meter, avoiding extra
X/Z rounding in the canonical radial families. Knuth TwoDiff records the
exact subtraction residual; the actual round-trip displacement is also included.
Per-triangle L1 edge bounds conservatively bound area/perimeter. A surface tube
2*r*A + pi*r^2*P +8*pi*r^3/3 is charged for every transformed triangle. For the
moving sweep, source/end meshes and all8-face triangle prisms are included in
the bound, even for locally omitted/parallel prisms. Every pair and aggregate
stage budget includes both this cover bound and the unchanged prism budget.
"""
import math
import numpy as np
import manifold3d as m
import plan_architectural_disassembly as planner
from physical_contacts import permitted_withdrawal
TOL=planner.VOLUME_TOLERANCE_M3
EPS=np.finfo(float).eps
def up(value,operations=32):
 value=float(value);gamma=operations*EPS/(1-operations*EPS)
 return float(np.nextafter(value*(1+gamma),math.inf)) if value else 0.
def two_diff(a,b):
 x=a-b;bvirt=a-x;avirt=x+bvirt;bround=bvirt-b;around=a-avirt
 return x,around+bround
def stats(v,t):
 p=v[t];e1,r1=two_diff(p[:,1],p[:,0]);e2,r2=two_diff(p[:,2],p[:,0]);e3,r3=two_diff(p[:,2],p[:,1])
 gamma=8*EPS/(1-8*EPS)
 lengths=[(np.sum(np.abs(e),axis=1)+np.sum(np.abs(r),axis=1))*(1+gamma) for e,r in [(e1,r1),(e2,r2),(e3,r3)]]
 area=up(math.fsum((.5*lengths[0]*lengths[1]).tolist()),64+len(t))
 perimeter=up(math.fsum((lengths[0]+lengths[1]+lengths[2]).tolist()),64+len(t))
 return area,perimeter,len(t)
def tube(r,area,perimeter,n):
 if r==0:return 0.
 pi=float(np.nextafter(math.pi,math.inf))
 return up(2*r*area+pi*r*r*perimeter+(8*pi/3)*r*r*r*n,128)
def face_keys(v,t):
 out=[]
 for tri in t:
  points=tuple(tuple(float(x) for x in v[i]) for i in tri)
  out.append(min(points,points[1:]+points[:1],points[2:]+points[:2]))
 return sorted(out)
def local_shape(world,origin):
 mesh=world.to_mesh64();v=np.asarray(mesh.vert_properties)[:,:3];t=np.asarray(mesh.tri_verts,np.uint64);local,residual=two_diff(v,origin)
 roundtrip=(local+origin)-v;r=up(max(float(np.max(np.sum(np.abs(residual),axis=1),initial=0)),float(np.max(np.sum(np.abs(roundtrip),axis=1),initial=0))),16)
 local=np.array(local,dtype=np.float64,order='C',copy=True);t=np.array(t,dtype=np.uint64,order='C',copy=True);s=m.Manifold(m.Mesh64(local,t));assert str(s.status())=='Error.NoError','Local Mesh64 import failed'
 actual=s.to_mesh64();av=np.asarray(actual.vert_properties)[:,:3];at=np.asarray(actual.tri_verts,np.uint64)
 assert face_keys(av,at)==face_keys(local,t),'Local import changed an oriented triangle'
 area,perimeter,n=stats(v,t)
 return s,{'roundtrip_max_l1_m':float(np.max(np.sum(np.abs(roundtrip),axis=1),initial=0)),'exact_forward_residual_max_l1_m':float(np.max(np.sum(np.abs(residual),axis=1),initial=0)),'displacement_bound_m':r,'area_upper_m2':area,'perimeter_upper_m':perimeter,'triangle_count':n}
def _check_stage(scene,member_ids,delta,stop_first=False,frame="integer-Y"):
 assert frame in ["integer-Y","bbox-center-XYZ"]
 ids=list(member_ids);assert len(ids)==1,'This external bounded recipe proves one moving actor per stage'
 pid=ids[0];delta=np.asarray(delta,float);shape=scene.current(pid);bb=np.asarray(shape.bounding_box());origin=np.array([0.,float(round((bb[1]+bb[4])/2)),0.]) if frame=='integer-Y' else (bb[:3]+bb[3:])/2
 mover,ma=local_shape(shape,origin);sweep,account=planner.sweep_cover(mover,delta);length=float(np.linalg.norm(delta));mover_cover=tube(ma['displacement_bound_m'],4*ma['area_upper_m2']+length*ma['perimeter_upper_m'],8*ma['perimeter_upper_m']+12*length*ma['triangle_count'],10*ma['triangle_count'])
 broad=np.r_[np.minimum(bb[:3],bb[:3]+delta),np.maximum(bb[3:],bb[3:]+delta)];collisions=[];checks=0;maximum=0.;transform_total=0.;pairs=[];intentional=[]
 for other in scene.parts:
  if other in ids:continue
  obstacle=scene.current(other);ob=np.asarray(obstacle.bounding_box())
  if not np.all((broad[3:]>=ob[:3])&(ob[3:]>=broad[:3])):continue
  if permitted_withdrawal(scene.parts[pid],scene.parts[other],delta):intentional.append({'moving_id':pid,'receiver_id':other});checks+=1;continue
  target,oa=local_shape(obstacle,origin);obstacle_cover=tube(oa['displacement_bound_m'],oa['area_upper_m2'],oa['perimeter_upper_m'],oa['triangle_count']);frame_bound=up(mover_cover+obstacle_cover);transform_total=up(transform_total+frame_bound);volume=max(0.,float((sweep^target).volume()));checks+=1;maximum=max(maximum,volume);error=account['discarded_prism_volume_m3']+frame_bound
  pairs.append({'obstacle_id':other,'overlap_m3':volume,'transform_cover_bound_m3':frame_bound,'mover_sweep_cover_bound_m3':mover_cover,'obstacle_cover_bound_m3':obstacle_cover,'obstacle_transform':oa})
  if volume+error>TOL:
   collisions.append({'moving_id':pid,'obstacle_id':other,'overlap_m3':volume,'omitted_sweep_volume_bound_m3':account['discarded_prism_volume_m3'],'transform_cover_bound_m3':frame_bound,'obstacle_parked':bool(np.linalg.norm(scene.offsets[other])>1e-12)})
   if stop_first:break
 aggregate=up(account['discarded_prism_volume_m3']+transform_total);assert aggregate<TOL,('Accumulated omitted sweep plus transform cover exceeds tolerance',aggregate,TOL)
 return {'status':'BLOCKED' if collisions else 'PASS','common_frame_kind':frame,'scene_version':scene.version,'member_ids':ids,'delta_m':delta.tolist(),'collisions':collisions,'continuous_pair_checks':checks,'maximum_intersection_m3':maximum,'overlap_tolerance_m3':TOL,'discarded_sweep_prism_volume_m3':account['discarded_prism_volume_m3'],'coordinate_transform_cover_bound_m3':transform_total,'aggregate_numerical_error_bound_m3':aggregate,'triangle_prism_count':account['triangle_prism_count'],'methods':[account['method']],'coordinate_transform_method':'Common local Mesh64 frame; exact TwoDiff residual and conservative per-triangle homotopy tube cover','intentional_fastener_withdrawals':intentional,'parked_pieces_checked':True,'local_origin_m':origin.tolist(),'moving_transform':ma,'pair_transform_bounds':pairs}

def check_stage(scene,member_ids,delta,stop_first=False):
 """Try two separately bounded common frames; retain failed diagnostics.

 A real overlap cannot be licensed by a transform error budget: each accepted
 frame independently satisfies every strict pair and aggregate bound. The
 fallback changes numerical conditioning, never geometry or contact policy.
 """
 first=_check_stage(scene,member_ids,delta,stop_first,"integer-Y")
 if first['status']=='PASS':return first
 second=_check_stage(scene,member_ids,delta,stop_first,"bbox-center-XYZ")
 second['prior_common_frame_attempts']=[{'frame':first['common_frame_kind'],'status':first['status'],'collisions':first['collisions'],'aggregate_numerical_error_bound_m3':first['aggregate_numerical_error_bound_m3']}]
 return second

# TIMESTAMP END 2026-11-05T19:01:25+00:00 | REVISION R000060
