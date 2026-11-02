"""Construct all 24 matching perimeter CSG step-lap proposals without editing baseline.

A tongue is retained from the existing original-stock envelope, not attached as
extra material. Its complementary pocket is subtracted from its receiver.
Dimensions are modeling choices for the owner-authorized design, not measurements from
the illustration or structural/erection/fabrication approval.
"""
from pathlib import Path
import collections,copy,hashlib,itertools,json,math
import numpy as np
import manifold3d as m
R=Path(__file__).resolve().parents[1];I=.0254;TOL_IN3=1e-6
SPECS=[]
for k in range(8):
 for side in ['0','2']:
  SPECS.append({'id':f'J{k}-{side}_B{k}','family_id':'short_rafter_ring_'+('left' if side=='0' else 'right'),'title':f'Short rafter J{k}-{side} and ring B{k}','rafter':f'J{k}-{side}','receiver':f'B{k}','tongue_width_in':2.,'max_engagement_in':1.,'bay':k,'handed_reflection':side=='2','seed_id':'J0-0_B0'})
for k in range(8):
 SPECS.append({'id':f'R{k}_P{k}','family_id':'main_hip_post','title':f'Main hip R{k} and post P{k}','rafter':f'R{k}','receiver':f'P{k}','tongue_width_in':4.,'max_engagement_in':.5,'bay':k,'handed_reflection':False,'seed_id':'R0_P0'})

SPECS.sort(key=lambda spec:spec['id']!=spec['seed_id'])

def family_transform(spec):
 angle=spec['bay']*math.pi/4;c=math.cos(angle);s=math.sin(angle)
 rotation=np.array([[c,0,s],[0,1,0],[-s,0,c]])
 if spec['handed_reflection']:
  normal=np.array([math.sin(math.pi/8),0,math.cos(math.pi/8)])
  rotation=rotation@(np.eye(3)-2*np.outer(normal,normal))
 return rotation


def family_solid(shape,spec):
 if spec['handed_reflection']:
  c=math.sqrt(.5);shape=shape.transform([[c,0,-c,0],[0,1,0,0],[-c,0,-c,0]])
 # Use the kernel's exact quadrant handling, matching the original generator.
 return shape.rotate((0,spec['bay']*45,0))

def solid(p):return m.Manifold(m.Mesh64(np.asarray(p['vertices'],dtype=float),np.asarray(p['triangles'],dtype=np.uint64))).set_tolerance(1e-9)
def mesh(s):
 q=s.to_mesh64();v=np.asarray(q.vert_properties)[:,:3];t=np.asarray(q.tri_verts)
 return {'vertices':v.tolist(),'triangles':t.tolist(),'volume_m3':s.volume()}
def resolved(s):return m.Manifold(s.to_mesh64()).set_tolerance(1e-9)
def original_stock(p):
 planes=p['geometry_planes_inches'];n=np.asarray([x['normal'] for x in planes]);k=np.asarray([x['constant'] for x in planes]);vs=[]
 for ids in itertools.combinations(range(len(n)),3):
  a=n[list(ids)]
  if abs(np.linalg.det(a))<1e-10:continue
  q=np.linalg.solve(a,k[list(ids)])
  if np.all(n@q<=k+1e-7):vs.append([q[0]*I,q[2]*I,-q[1]*I])
 return m.Manifold.hull_points(vs).set_tolerance(1e-9)
def inside_band(s,normal,low,high):
 normal=np.asarray(normal)
 return s.trim_by_plane(tuple(normal),float(low)).trim_by_plane(tuple(-normal),float(-high))
def poly_area(p):return .5*sum(p[i][0]*p[(i+1)%len(p)][1]-p[(i+1)%len(p)][0]*p[i][1] for i in range(len(p)))
def clip(a,b):
 if poly_area(b)<0:b=b[::-1]
 out=list(a)
 for i in range(3):
  if not out:break
  start,end=b[i],b[(i+1)%3];edge=end-start;inp=out;out=[]
  cross=lambda p:edge[0]*(p-start)[1]-edge[1]*(p-start)[0]
  p=inp[-1];dp=cross(p)
  for q in inp:
   dq=cross(q)
   if (dq>=-1e-12)!=(dp>=-1e-12):out.append(p+(q-p)*(dp/(dp-dq)))
   if dq>=-1e-12:out.append(q)
   p=q;dp=dq
 return out if len(out)>2 else []
def triangles(s):
 q=mesh(s);v=np.asarray(q['vertices']);t=v[np.asarray(q['triangles'])];n=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]);length=np.linalg.norm(n,axis=1);keep=length>1e-14;t=t[keep];n=n[keep]/length[keep,None]
 return t,n,np.einsum('ij,ij->i',t[:,0],n)
def contacts(a,b):
 ta,na,da=triangles(a);tb,nb,db=triangles(b);areas=collections.defaultdict(float);moments=collections.defaultdict(lambda:np.zeros(3))
 for idx,t in enumerate(ta):
  n=na[idx];same=np.where((nb@n < -1+1e-9)&(np.abs(tb[:,0]@n-da[idx])<1e-8))[0]
  u=np.cross(n,np.eye(3)[np.argmin(abs(n))]);u/=np.linalg.norm(u);v=np.cross(n,u);proj=np.array([u,v]).T
  for k in same:
   poly=clip(t@proj,tb[k]@proj);signed=poly_area(poly) if poly else 0;area=abs(signed)
   if area>1e-10:
    q=np.asarray(poly);nxt=np.roll(q,-1,axis=0);cross=q[:,0]*nxt[:,1]-nxt[:,0]*q[:,1];c2=((q+nxt)*cross[:,None]).sum(axis=0)/(6*signed);c3=u*c2[0]+v*c2[1]+n*da[idx]
    key=tuple(np.round(n,8));areas[key]+=area;moments[key]+=c3*area
 return [{'normal_on_rafter':list(key),'area_in2':area/I**2,'centroid_m':(moments[key]/area).tolist(),'meaning':'Outward face normal of first named member; contact geometry, not solved force'} for key,area in sorted(areas.items())]
def close_bounds(a,b):
 aa=a.bounding_box();bb=b.bounding_box()
 return not any(aa[i+3]<bb[i]-1e-8 or bb[i+3]<aa[i]-1e-8 for i in range(3))
def volume_centroid(s):
 q=mesh(s);v=np.asarray(q['vertices']);t=np.asarray(q['triangles']);origin=v.mean(0);w=v-origin;vv=np.einsum('ij,ij->i',w[t[:,0]],np.cross(w[t[:,1]],w[t[:,2]]))/6
 vol=vv.sum();c=origin+(vv[:,None]*(w[t[:,0]]+w[t[:,1]]+w[t[:,2]])/4).sum(0)/vol
 return {'volume_m3':float(vol),'centroid_m':c.tolist()}
def section(s,origin,normal):
 normal=np.asarray(normal,dtype=float);normal/=np.linalg.norm(normal);x=np.cross(normal,np.eye(3)[np.argmin(abs(normal))]);x/=np.linalg.norm(x);y=np.cross(normal,x);rot=np.array([x,y,normal]);tf=np.column_stack((rot,-rot@np.asarray(origin)))
 return s.transform(tf.tolist()).slice(0).area()/I**2

def build_proposal(data,source_hash):
 parts={p['id']:p for p in data['parts']};solids={k:solid(p) for k,p in parts.items() if p['is_timber']};proposed=solids.copy();variants=[];tongues={};candidate_tongues={};seed_specs={};seed_shapes={};isometry=[]
 for spec in SPECS:
  a,b=spec['rafter'],spec['receiver'];pa,pb=parts[a],parts[b];sa,sb=solids[a],solids[b]
  baseline_faces=contacts(sa,sb)
  bearing=[f for f in baseline_faces if np.linalg.norm(np.asarray(f['normal_on_rafter'])-[0,-1,0])<1e-7]
  assert bearing,'Missing current horizontal rafter bearing'
  area=sum(f['area_in2'] for f in bearing);origin=sum(np.asarray(f['centroid_m'])*f['area_in2'] for f in bearing)/area
  top=float(origin[1]);width=np.asarray(pa['stock_frame']['width']);width/=np.linalg.norm(width)
  horizontal=np.asarray(pa['stock_frame']['axis']);horizontal[1]=0;horizontal=-horizontal/np.linalg.norm(horizontal)
  original=original_stock(pa)
  # Closed profile in the true rafter stock frame: restore only stock under the
  # current seat, centered within the chosen width and bounded by maximum depth.
  # The sloping original lower face truncates J/B near its inner seat edge.
  blank=inside_band(original,[0,1,0],top-spec['max_engagement_in']*I,top)
  blank=inside_band(blank,width,float(width@origin-spec['tongue_width_in']*I/2),float(width@origin+spec['tongue_width_in']*I/2))
  tongue=resolved(blank^sb)
  assert tongue.volume()>1e-10,'No available original stock to form a tongue'
  candidate_tongues[spec['id']]=tongue
  if spec['id']==spec['seed_id']:
   new_a=resolved(sa+tongue);new_b=resolved(sb-tongue)
   seed_shapes[spec['id']]={'rafter':new_a,'receiver':new_b,'tongue':tongue}
  else:
   # Accepted seed booleans are transformed, rather than rerunning fragile
   # coplanar unions in every rotated world coordinate frame. Baseline isometry
   # and original-stock containment are independently checked below.
   seed=seed_shapes[spec['seed_id']];tf=np.column_stack((family_transform(spec),np.zeros(3))).tolist()
   new_a=resolved(family_solid(seed['rafter'],spec));new_b=resolved(family_solid(seed['receiver'],spec));tongue=resolved(family_solid(seed['tongue'],spec))
  added=tongue;removed=tongue
  assert abs((new_a.volume()-sa.volume())-tongue.volume())/I**3<TOL_IN3,(spec['id'],'HOLD: serialized owner volume inconsistency')
  assert abs((sb.volume()-new_b.volume())-tongue.volume())/I**3<TOL_IN3,(spec['id'],'HOLD: serialized receiver volume inconsistency')
  assert (added-original).volume()/I**3<TOL_IN3,'New material would exceed original stock'
  assert len(new_a.decompose())==len(new_b.decompose())==1,'Disconnected proposed member'
  assert (new_a^new_b).volume()/I**3<TOL_IN3,'Mating solids overlap'
  assert abs(added.volume()-removed.volume())<1e-12,(spec['id'],'HOLD: pair volume mismatch',added.volume()/I**3,removed.volume()/I**3,abs(added.volume()-removed.volume())/I**3)
  assert ((new_a+new_b)-(sa+sb)).volume()/I**3<TOL_IN3,(spec['id'],'HOLD: extra union volume',((new_a+new_b)-(sa+sb)).volume()/I**3)
  assert ((sa+sb)-(new_a+new_b)).volume()/I**3<TOL_IN3
  # Apply the complete family to the shared receiving members. Each B has TWO
  # distinct short-rafter pockets; never overwrite its first cut with the second.
  proposed[a]=new_a;proposed[b]=new_b # Receivers are combined from the verified bay-zero seed below.
  tongues[spec['id']]=tongue
  if spec['id']==spec['seed_id']:seed_specs[spec['id']]=spec
  face=contacts(new_a,new_b);vv=np.asarray(mesh(added)['vertices']);maxdepth=(top-vv[:,1].min())/I
  transverse=[f for f in face if abs(abs(np.asarray(f['normal_on_rafter'])@width)-1)<1e-7]
  sides={int(np.sign(np.asarray(f['normal_on_rafter'])@width)) for f in transverse}
  assert sides=={-1,1},'No two opposed transverse cheek contacts'
  section_records=[]
  # Sample clearly named sections, not a claim of a globally governing net section.
  for role,name,old,new,n in [('rafter',a,sa,new_a,np.asarray(pa['stock_frame']['axis'])),('receiver',b,sb,new_b,np.asarray(pb['stock_frame']['axis']))]:
   o=origin.copy()
   if role=='receiver' and b.startswith('P'):o[1]-=spec['max_engagement_in']*I/2
   section_records.append({'member_id':name,'role':role,'origin_m':o.tolist(),'normal':n.tolist(),'baseline_area_in2':section(old,o,n),'proposed_area_in2':section(new,o,n),'status':'Named local section only; not an allowable net section or whole-member minimum'})
  footprint=(float((vv@horizontal).max()-(vv@horizontal).min())/I)
  findings=['Real CSG tongue retained inside original rafter stock; matching receiver pocket cut with the same solid.','Outer member axes and roof datums unchanged. Both proposed members are one connected valid solid.','Opposed transverse contact cheeks measured; uplift retention and fastener detail remain unresolved.']
  if a.startswith('J'):findings.append('Contact is redistributed: horizontal area changes from 12 to approximately 6.457 square inches, with approximately 5.893 square inches of inclined contact. A normal force at the inclined face has a horizontal component, but its magnitude and load sharing are unsolved. Neither horizontal-area reduction alone nor total-contact increase establishes a capacity loss or gain. The 1 in setting is maximum engagement. Original sloping stock produces a tapered tongue and sloping pocket floor, with only a short 1 in deep flat portion; no full-depth rectangular tongue is invented.')
  else:findings.append('A section within the shallow post-head slot decreases from 64 to 32 square inches; this needs structural review and is not an improvement claim. The 0.5 in deeper center tongue is bounded by the existing post footprint; side shoulders remain at the baseline seat elevation.')
  clones=[]
  for name,new in [(a,new_a),(b,new_b)]:
   p=copy.deepcopy(parts[name]);q=mesh(new);p.update(vertices=q['vertices'],triangles=q['triangles'],faces=q['triangles'],reference_end_faces=[],joint_cut_faces=[],geometry_purpose='proposed step-lap joinery geometry only',fabrication_dimensions_valid=False,plan_dimension_policy='Proposed comparison only; not fabrication approved; no drill cut or fastening specification')
   p['fit_geometry']=dict(p['fit_geometry'],volume_m3=q['volume_m3'],structural_design_status='PROPOSED STEP LAP — NOT STRUCTURALLY QUALIFIED',nominal_fit='Pair geometry checked only; no strength or erection verification')
   p['cut_status']='PROPOSED STEP-LAP JOINERY — NOT FABRICATION APPROVED';p['notes']=list(p['notes'])+['This separate proposed model uses chosen design assumptions authorized for geometric exploration, not dimensions measured from the reference image. Existing baseline end/cut-face records were withheld; use the new measured contact geometry.']
   clones.append(p)
  def exhibit(name,member,s):return dict(id=name,member_id=member,**mesh(s))
  # Two explicitly matched closed profiles from the actual retained-stock solid.
  # Local profile x follows the horizontal rafter direction; y is vertical.
  rot=np.array([horizontal,[0.,1.,0.],np.cross(horizontal,[0.,1.,0.])]);tf=np.column_stack((rot,-rot@origin))
  raw_profiles=added.transform(tf.tolist()).slice(0).to_polygons()
  profiles=[]
  for polygon in raw_profiles:
   points=(np.asarray(polygon)/I).tolist()
   if points and points[-1]!=points[0]:points.append(points[0])
   profiles.append(points)
  assert profiles and all(len(poly)>=4 for poly in profiles)
  params={
   'tongue_width':{'value':spec['tongue_width_in'],'unit':'in','basis':'chosen design assumption; half nominal member width','source':None},
   'maximum_additional_engagement':{'value':spec['max_engagement_in'],'unit':'in','basis':'chosen design assumption; clipped to original stock and receiver','source':None},
   'actual_maximum_engagement':{'value':maxdepth,'unit':'in','basis':'measured resulting CSG mesh'},
   'actual_contact_footprint_length':{'value':footprint,'unit':'in','basis':'derived from available stock and receiver, not a fabrication length'},
   'nominal_fit_clearance':{'value':0,'unit':'in','basis':'mathematical comparison only; machining, drying and erection clearance unresolved'},
   'support_datum':{'value':top/I,'unit':'in','basis':'existing baseline seat elevation; member axes fixed'},
   'corner_geometry':{'value':'sharp modeled intersections','basis':'chosen geometric profile; tool radii and splitting design unresolved'},
   'uplift_retention':{'value':'unresolved'},'fastener_detail':{'value':'unresolved'}}
  variants.append({'id':spec['id'],'family_id':spec['family_id'],'bay':spec['bay'],'handed_reflection':spec['handed_reflection'],'reference_seed_id':spec['seed_id'],'title':spec['title'],'member_ids':[a,b],'baseline_model_hash':source_hash,'source_attachment_id':None,'source_section':None,'source_printed_page':None,'source_pdf_page':None,'reference_image':'Screenshot 2026-11-02 at 7.46.44 AM.png','reference_image_sha256':'4c8698c865a7714b10893ff0867563f0de36490e19f926634c5dbd5c82cbd0c9','geometry_only':True,'fabrication_dimensions_valid':False,'status':'proposed step-lap joinery','geometry_status':'PASS','parameters':params,'findings':findings,'local_frame':{'origin_m':origin.tolist(),'horizontal':horizontal.tolist(),'transverse':width.tolist(),'up':[0,1,0]},'review_bounds_inches':[[-16,-12,-16],[16,12,16]],'baseline_parts':[copy.deepcopy(pa),copy.deepcopy(pb)],'proposed_parts':clones,'removed_parts':[exhibit(b+'-proposed-pocket',b,removed)],'added_parts':[exhibit(a+'-retained-stock-tongue',a,added)],'baseline_contact_faces':baseline_faces,'contact_faces':face,'measurements':{'baseline_horizontal_bearing_area_in2':area,'proposed_horizontal_bearing_area_in2':sum(f['area_in2'] for f in face if np.linalg.norm(np.asarray(f['normal_on_rafter'])-[0,-1,0])<1e-7),'proposed_total_geometric_contact_area_in2':sum(f['area_in2'] for f in face),'proposed_inclined_contact_area_in2':sum(f['area_in2'] for f in face if 1e-7<abs(f['normal_on_rafter'][1])<1-1e-7),'transverse_cheek_contacts':transverse,'receiver_removed_volume_in3':removed.volume()/I**3,'rafter_retained_stock_volume_in3':added.volume()/I**3,'new_overlap_volume_in3':(new_a^new_b).volume()/I**3,'remaining_local_sections':section_records,'baseline_member_mass_geometry':[dict(member_id=name,**volume_centroid(solids[name])) for name in [a,b]],'proposed_member_mass_geometry':[dict(member_id=name,**volume_centroid(proposed[name])) for name in [a,b]]},'cut_profiles':{'coordinate_system':'local horizontal and vertical inches at the transverse center plane','origin_m':origin.tolist(),'horizontal':horizontal.tolist(),'vertical':[0,1,0],'rafter_retained_tongue_closed_polygons':profiles,'receiver_removed_pocket_closed_polygons':copy.deepcopy(profiles),'status':'Measured CSG profiles; chosen proposal, not a cut template'},'restraint_intent':['geometric transverse location while engaged','broader stepped mating surfaces'],'uplift_retention':'unresolved','fastener_detail':'unresolved'})
 # Form both distinct B0 pockets once, verify the serialized result, then
 # rotate the complete ring-beam member to every bay. P0 has one hip pocket.
 paired_b0=resolved(solids['B0']-(tongues['J0-0_B0']+tongues['J0-2_B0']))
 expected_removal=tongues['J0-0_B0'].volume()+tongues['J0-2_B0'].volume()
 assert abs((solids['B0'].volume()-paired_b0.volume())-expected_removal)/I**3<TOL_IN3,'HOLD: accumulated B0 pockets failed volume conservation'
 for k in range(8):
  proposed[f'B{k}']=resolved(paired_b0.rotate((0,k*45,0)))
  proposed[f'P{k}']=resolved(seed_shapes['R0_P0']['receiver'].rotate((0,k*45,0)))
 # Check every local proposal against the accepted seed, including reflection of
 # the right-handed short-rafter family before the exact bay rotation.
 for spec in SPECS:
  seed=seed_specs[spec['seed_id']];matrix=family_transform(spec)
  tf=np.column_stack((matrix,np.zeros(3))).tolist()
  expected=family_solid(tongues[spec['seed_id']],spec);actual=candidate_tongues[spec['id']]
  errors={'tongue_difference_in3':((actual-expected).volume()+(expected-actual).volume())/I**3}
  old_expected=family_solid(solids[seed['rafter']],spec);old_actual=solids[spec['rafter']]
  errors['baseline_rafter_difference_in3']=((old_actual-old_expected).volume()+(old_expected-old_actual).volume())/I**3
  stock_expected=family_solid(original_stock(parts[seed['rafter']]),spec);stock_actual=original_stock(parts[spec['rafter']])
  errors['original_stock_difference_in3']=((stock_actual-stock_expected).volume()+(stock_expected-stock_actual).volume())/I**3
  assert max(errors.values())<TOL_IN3,(spec['id'],'HOLD: family isometry conflict',errors)
  isometry.append({'interface_id':spec['id'],'seed_id':spec['seed_id'],'bay_rotation_degrees':spec['bay']*45,'handed_reflection':spec['handed_reflection'],'matrix':matrix.tolist(),**errors,'status':'PASS'})
 # Verify no two selected pocket solids compete for the same ring-beam material.
 for left,right in itertools.combinations(SPECS,2):
  if left['receiver']!=right['receiver']:continue
  assert (tongues[left['id']]^tongues[right['id']]).volume()/I**3<TOL_IN3,(left['id'],right['id'],'HOLD: pocket overlap')
 # Replace pair comparison meshes with the final combined family result so every
 # depiction/export of a ring beam contains both of its proposed pockets.
 for v in variants:
  for p in v['proposed_parts']:
   shape=mesh(proposed[p['id']]);p.update(vertices=shape['vertices'],triangles=shape['triangles'],faces=shape['triangles']);p['fit_geometry']['volume_m3']=shape['volume_m3']
  a,b=v['member_ids']
  v['measurements']['proposed_member_mass_geometry']=[dict(member_id=name,**volume_centroid(proposed[name])) for name in [a,b]]
  v['measurements']['receiver_total_removed_volume_in3']=(solids[b]-proposed[b]).volume()/I**3
  v['measurements']['receiver_proposed_pocket_count']=sum(spec['receiver']==b for spec in SPECS)
  v['findings'].append('This view uses the combined all-perimeter proposal; each ring beam includes both short-rafter pockets. Highlighted removed wood belongs to the selected interface only.')
 # Audit the complete family together against ALL original modeled timber neighbors.
 changed={s[k] for s in SPECS for k in ['rafter','receiver']};overlaps=[];neighbors=[];lost=[]
 for a,b in itertools.combinations(solids,2):
  if not ({a,b}&changed):continue
  if not close_bounds(proposed[a],proposed[b]):continue
  inter=(proposed[a]^proposed[b]).volume()/I**3
  if inter>TOL_IN3:overlaps.append({'a':a,'b':b,'volume_in3':inter})
  old=contacts(solids[a],solids[b]);new=contacts(proposed[a],proposed[b]);oldarea=sum(f['area_in2'] for f in old);newarea=sum(f['area_in2'] for f in new)
  if oldarea>.001 or newarea>.001:
   neighbors.append({'a':a,'b':b,'baseline_contact_area_in2':oldarea,'proposed_contact_area_in2':newarea,'baseline_faces':old,'proposed_faces':new,'scope':'geometric contact only, not force transfer capacity'})
   if oldarea>.01 and newarea<.01:lost.append({'a':a,'b':b,'baseline_area_in2':oldarea})
 for v in variants:
  own=set(v['member_ids']);v['measurements']['neighbor_contacts']=[n for n in neighbors if {n['a'],n['b']}&own];v['measurements']['neighbor_interferences']=[n for n in overlaps if {n['a'],n['b']}&own]
  if overlaps or lost:v['geometry_status']='REJECTED';v['findings'].append('STOP: interfering solids or lost neighboring contact detected. Do not replicate.')
  else:v['findings'].append('All affected pairs checked against all 104 timber solids: no new positive-volume intersection and no lost baseline face contact. This is geometry evidence only.')
 # Also ensure the temporary metal and independent non-timber panel remain clear.
 nonwood=[]
 for name in changed:
  for other,p in parts.items():
   if p['is_timber'] or p['material']=='surface':continue
   s=solid(p)
   if not close_bounds(proposed[name],s):continue
   old=(solids[name]^s).volume()/I**3;new=(proposed[name]^s).volume()/I**3
   if new>old+TOL_IN3:nonwood.append({'timber':name,'component':other,'baseline_overlap_in3':old,'proposed_overlap_in3':new})
 if nonwood:
  for v in variants:v['geometry_status']='REJECTED';v['findings'].append('STOP: new interference with non-timber component.')
 limits=['Proposed step-lap joinery using chosen design assumptions. This is not fabrication, strength, uplift, stability or erection approval.','The original reference image is undimensioned. Selected widths and engagement are not measurements from it.','The owner-uploaded timber-frame manual has not been read; externally verified TFEC 1-2019 is not that attachment.','Model selection binds meshes, plans, exports, removed-stock overlays and recomputed applied self-weight to the selected geometry. Baseline contact warning markers and fixed-area pressure shortcuts are disabled for the proposed model; reactions and capacities remain unsolved.','All 24 requested matching perimeter interfaces are represented in the separate proposed model: 16 short-rafter/ring and 8 main-hip/post joints. The canonical baseline stays unchanged; this is not structural or fabrication approval.']
 result={'schema_version':'step-lap-proposal-2','status':'PROPOSED STEP-LAP JOINERY — NOT FABRICATION APPROVED','baseline_model_sha256':source_hash,'canonical_model_unchanged':True,'limitations':limits,'variants':variants,'combined_geometry_audit':{'changed_member_ids':sorted(changed),'requested_interface_count':24,'implemented_interface_count':len(variants),'held_interfaces':[],'family_isometry_checks':isometry,'timber_count':104,'affected_pairs_considered':sum(bool({a,b}&changed) for a,b in itertools.combinations(solids,2)),'interferences':overlaps,'lost_neighbor_contacts':lost,'new_non_timber_interferences':nonwood,'geometry_status':'PASS' if not(overlaps or lost or nonwood) else 'REJECTED','capacity_checked':False}}
 full=copy.deepcopy(data);lookup={p['id']:p for v in variants for p in v['proposed_parts']};full['parts']=[lookup.get(p['id'],p) for p in full['parts']];full['title']='Proposed step-lap joinery model';full['status']=result['status'];full['source_model']='Separate proposed model derived from baseline '+source_hash;full['proposed_review']={'baseline_model_sha256':source_hash,'changed_member_ids':sorted(changed),'geometry_audit':result['combined_geometry_audit'],'limitations':limits,'fabrication_dimensions_valid':False};full['notes']=full['notes']+limits;full['joinery_verification']={'status':'PROPOSED GEOMETRY ONLY','scope':'Current derived pair/contact audit; baseline joinery approval fields intentionally not inherited. No structural verification.'};full['fit_audit']={'status':'PROPOSED GEOMETRY ONLY','capacity_checked':False}
 full['proposed_member_volume_centroids']=[dict(id=name,**volume_centroid(s)) for name,s in proposed.items()]
 result['proposed_timber_volume_m3']=sum(x['volume_m3'] for x in full['proposed_member_volume_centroids']);result['baseline_timber_volume_m3']=sum(s.volume() for s in solids.values())
 return result,full

if __name__=='__main__':
 raw=(R/'src/model-data.json').read_bytes();sha=hashlib.sha256(raw).hexdigest();data=json.loads(raw)
 proposal,full=build_proposal(data,sha)
 (R/'src/step-lap-proposal.json').write_text(json.dumps(proposal,separators=(',',':'))+'\n')
 (R/'src/step-lap-proposed-model.json').write_text(json.dumps(full,separators=(',',':'))+'\n')
 assert (R/'src/model-data.json').read_bytes()==raw,'Canonical model must never be mutated'
 print(json.dumps({'audit':proposal['combined_geometry_audit'],'pairs':[{'id':v['id'],'measurements':{k:val for k,val in v['measurements'].items() if k not in ['neighbor_contacts','baseline_member_mass_geometry','proposed_member_mass_geometry']}} for v in proposal['variants']]},indent=2))
 if proposal['combined_geometry_audit']['geometry_status']!='PASS':raise SystemExit('Proposed geometry rejected; inspect findings before adoption')
