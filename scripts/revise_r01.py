#!/usr/bin/env python3
"""Reproduce R01 geometric envelopes. No fabrication joints are inferred.

All construction is in inches, X/Y horizontal, Z up. Output is metres, Y up.
Solids are intersections of explicit halfspaces, not overlapping keyed cutters.
"""
import hashlib, itertools, json, math
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
INCH=.0254
ALPHA=math.pi/8
PH=1/3
PN=PH/math.cos(ALPHA)
RE,RP,RC=200.,176.,41.
H=90. # display-only ground-to-tie centre reference, not a measured height
GAP,B=42.375,4.
RHO=(GAP+B)/(2*math.sin(ALPHA))
STATION=(1-RHO/RE)/2
HIP_HALF_VERTICAL=5/math.cos(math.atan(PH))
ROOF_K=H+PH*RP+HIP_HALF_VERTICAL

def add(a,b):return [a[i]+b[i] for i in range(3)]
def sub(a,b):return [a[i]-b[i] for i in range(3)]
def mul(a,s):return [v*s for v in a]
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def cross(a,b):return [a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]
def norm(a):return math.sqrt(dot(a,a))
def unit(a):return mul(a,1/norm(a))
def radial(k):return [math.cos(k*math.pi/4),math.sin(k*math.pi/4),0.]
def tangent(k):r=radial(k);return [-r[1],r[0],0.]
def at(r,k,z):p=mul(radial(k),r);p[2]=z;return p
def out(p):return [p[0]*INCH,p[2]*INCH,-p[1]*INCH]
def direction(p):return [p[0],p[2],-p[1]]
def plane(n,k,tag=None,mate=None):return {'n':n,'k':k,'tag':tag,'mate':mate}
def solve(a,b,c):
 n1,n2,n3=a['n'],b['n'],c['n'];det=dot(n1,cross(n2,n3))
 if abs(det)<1e-10:return None
 return mul(add(add(mul(cross(n2,n3),a['k']),mul(cross(n3,n1),b['k'])),mul(cross(n1,n2),c['k'])),1/det)

def convex(planes):
 vertices=[]
 for ps in itertools.combinations(planes,3):
  v=solve(*ps)
  if v is None or any(dot(p['n'],v)>p['k']+1e-7 for p in planes):continue
  if not any(norm(sub(v,w))<1e-6 for w in vertices):vertices.append(v)
 if len(vertices)<4:raise ValueError('Degenerate solid: '+repr(planes))
 faces=[]
 for p in planes:
  ids=[i for i,v in enumerate(vertices) if abs(dot(p['n'],v)-p['k'])<1e-6]
  if len(ids)<3:continue
  centre=[sum(vertices[i][j] for i in ids)/len(ids) for j in range(3)]
  normal=unit(p['n']);u=unit(sub(vertices[ids[0]],centre));v=cross(normal,u)
  ids.sort(key=lambda i:math.atan2(dot(sub(vertices[i],centre),v),dot(sub(vertices[i],centre),u)))
  faces.append((ids,p))
 return vertices,faces

def prism_planes(a,b,width,depth,width_axis=None):
 axis=unit(sub(b,a))
 w=unit(width_axis) if width_axis else unit(cross(axis,[0,0,1]))
 dep=unit(cross(w,axis))
 if dep[2]<0:dep=mul(dep,-1)
 return [plane(mul(axis,-1),-dot(axis,a),'A'),plane(axis,dot(axis,b),'B'),plane(w,dot(w,a)+width/2),plane(mul(w,-1),-dot(w,a)+width/2),plane(dep,dot(dep,a)+depth/2),plane(mul(dep,-1),-dot(dep,a)+depth/2)],w,dep

def ftdisplay(inches):return f'{int(inches//12)}\' {inches%12:.3f}"'

PARTS=[]
def member(pid,group,name,a,b,width,depth,planes,notes=(),material='wood',temporary=False,reference=None):
 vv,ff=convex(planes);axis=unit(sub(b,a));centre=mul(add(a,b),.5);length=norm(sub(b,a));vertices=[out(v) for v in vv]
 faces=[ids for ids,_ in ff];tris=[[ids[0],ids[j],ids[j+1]] for ids in faces for j in range(1,len(ids)-1)]
 volume=abs(sum(dot(vertices[t[0]],cross(vertices[t[1]],vertices[t[2]]))/6 for t in tris))
 inclination=math.degrees(math.asin(abs(axis[2])))
 dims={'length_m':length*INCH,'width_m':width*INCH,'depth_m':depth*INCH,'length_ft':length/12,'width_in':width,'depth_in':depth,'length_display':ftdisplay(length),'section_display':f'{width:g} × {depth:g} in','status':'R01 geometric reference; no stock, kerf, tenon or machining allowance.'}
 radial_c=unit([centre[0],centre[1],0]) if norm(centre[:2])>1e-9 else [1,0,0]
 p={'id':pid,'name':name,'group':group,'temporary':temporary,'material':material,'is_timber':material=='wood','vertices':vertices,'triangles':tris,'faces':faces,'center':out(centre),'axis_start':out(a),'axis_end':out(b),'axis_direction':direction(axis),'exploded_offset':direction(add(mul(radial_c,1.4),[0,0,1 if group!='perimeter_posts' else 0])),'label_position':out(centre),'dimensions':dims,'nominal_dimensions':dims.copy(),'angles':{'axis_inclination_deg':inclination,'azimuth_deg':None if abs(axis[2])>.9999 else math.degrees(math.atan2(axis[1],axis[0]))%360,'display_end_cut_off_square_deg':None,'display_end_A_off_square_deg':None,'display_end_B_off_square_deg':None,'display_end_face_to_axis_deg':None,'modeled_vertical_bevel_deg':None,'conditional_plan_miter_off_square_deg':None,'fabrication_end_A_cut_deg':None,'fabrication_end_B_cut_deg':None,'fabrication_bevel_deg':None},'cut_status':'R01 CONTACT GEOMETRY · CONNECTION DESIGN UNRESOLVED','provenance':'Octagon-architectural-geometry-study-R01.pdf; source readings and explicit display assumptions registered separately.','notes':list(notes)+['Contact surfaces are geometric envelopes. Mortises, tenons, housings, seats, peg/bolt sizes, fit clearance and assembly design are not specified.'],'label_lines':[pid,'R01 GEOMETRY',f'AXIS {inclination:.3f}°'],'label_short':[pid,'R01','JOINT VERIFY'],'color':[.51,.35,.20,1] if material=='wood' else ([.13,.44,.28,1] if group=='metal_spacers' else [.12,.15,.17,1]),'source_geometry_metadata':{'revision':'R01','units':'inches','axis_start':a,'axis_end':b,'section_width_in':width,'section_depth_in':depth,'roof_reference':reference,'display_height_H_in':H,'ground_height_status':'unresolved; H=90 in for display continuity only'},'fit_geometry':{'volume_m3':volume,'structural_design_status':'NOT DESIGNED','machining_clearance_m':None},'fitted_axial_extent_inches':max(dot(v,axis) for v in vv)-min(dot(v,axis) for v in vv),'joint_cut_faces':[],'reference_end_faces':[]}
 for ids,pl in ff:
  if pl['tag'] not in ['A','B']:continue
  end=pl['tag'];verts=[out(vv[i]) for i in ids];tri=[[0,j,j+1] for j in range(1,len(ids)-1)]
  normal=direction(unit(pl['n']));off=math.degrees(math.acos(min(1,abs(dot(axis,unit(pl['n']))))))
  p['angles'][f'display_end_{end}_off_square_deg']=off
  p['reference_end_faces'].append({'id':pid+'-'+end,'part_id':pid,'vertices':verts,'triangles':tri,'normal':normal,'description':'R01 geometric end plane. A/B naming retained; not a fabrication blank.'})
  if pl['mate']:
   p['joint_cut_faces'].append({'id':pid+'-'+end+'-CONTACT','part_id':pid,'mate_part_id':pl['mate'],'vertices':verts,'triangles':tri,'normal':normal,'status':'contact_plane_only','description':'R01 physical contact plane. No housing, tenon, fastener or capacity inferred.'})
 p['reference_end_faces'].sort(key=lambda f:f['id'])
 width_direction=unit([centre[0],centre[1],0]) if abs(axis[2])>.999999 else unit(cross(axis,[0,0,1]))
 depth_direction=unit(cross(width_direction,axis))
 if depth_direction[2]<0:depth_direction=mul(depth_direction,-1)
 p['stock_frame']={'axis':direction(axis),'width':direction(width_direction),'depth':direction(depth_direction)}
 # Explicit planes are retained for independent numerical checks and exact end inspection.
 p['geometry_planes_inches']=[{'normal':pl['n'],'constant':pl['k'],'end':pl['tag'],'mate':pl['mate']} for pl in planes]
 PARTS.append(p);return p

CONTEXT='Retained contextual member from the earlier reconstruction; section and detailed placement are unverified.'
for k in range(8):
 r,t=radial(k),tangent(k);rn,tn=radial(k+1),tangent(k+1)
 # Posts retain original A=foot, B=head semantics; H is explicitly provisional.
 a,b=at(RP,k,0),at(RP,k,H-4)
 ps,_,_=prism_planes(a,b,8,8,r)
 member(f'P{k}','perimeter_posts','Perimeter post',a,b,8,8,ps,[CONTEXT,'30 ft across radial outside faces; 8 in actual section assumed.'])
 a,b=at(RP,k,H),at(RP,k+1,H)
 ps,_,_=prism_planes(a,b,6,8)
 ps=ps[2:]+[plane(mul(t,-1),-4,'A',f'P{k}'),plane(tn,-4,'B',f'P{(k+1)%8}')]
 member(f'B{k}','eave_ring','Perimeter ring beam',a,b,6,8,ps,[CONTEXT,'Ends terminate at adjacent post side faces. Post-head bearing and heel connections remain unresolved.'])
 a,b=at(RP,k,H),at(RC,k,H)
 ps,_,_=prism_planes(a,b,6,10,t)
 ps=ps[2:]+[plane(r,RP-4,'A',f'P{k}'),plane(mul(r,-1),-44,'B',f'C{k}')]
 member(f'T{k}','radial_ties','Lower radial tie · 6 × 10',a,b,6,10,ps,['6 × 10 in requested by Stewart. Reference length is 135 in between post centres. Physical body is shown to post faces; joinery allowance unresolved.'])
 # Backed hip: two adjacent top roof planes meet on its radial ridge.
 a,b=at(RE,k,H+PH*(RP-RE)),at(RC,k,H+PH*(RP-RC))
 roof_normal_l=add(mul(r,PH),add(mul(t,PH*math.tan(ALPHA)),[0,0,1]))
 roof_normal_r=add(mul(r,PH),add(mul(t,-PH*math.tan(ALPHA)),[0,0,1]))
 ps=[plane(r,RE,'A'),plane(mul(r,-1),-44,'B',f'C{k}'),plane(t,4),plane(mul(t,-1),4),plane(roof_normal_l,ROOF_K),plane(roof_normal_r,ROOF_K),plane(add(mul(r,-PH),[0,0,-1]),-H-PH*RP+HIP_HALF_VERTICAL)]
 member(f'R{k}','radial_rafters','Main radial hip · 8 × 10',a,b,8,10,ps,['Radial inclination 4:12. Two backed roof faces are an explicit geometric envelope, not a verified carpentry cut.','Hip, tie and post heel geometry still overlaps until seat/joint offsets are designed; no collision-free assembly is claimed.'],reference={'radial_pitch':PH,'eave_radius_in':RE,'cupola_reference_radius_in':RC,'roof_top_offset_from_reference_in':HIP_HALF_VERTICAL})
 a,b=at(RC,k,H+5),at(RC,k,H+45+32)
 ps,_,_=prism_planes(a,b,6,6,r)
 member(f'C{k}','cupola_posts','Cupola post · radial 6 × 6',a,b,6,6,ps,['88 in outside / 76 in inside radial faces. Base, glazing and top bearing heights remain unresolved; 32 in upper interval is a display assumption.'])
 for suffix,z in [('L',H+1),('S',H+45+3),('H',H+45+32-3)]:
  a,b=at(RC,k,z),at(RC,k+1,z);ps,_,_=prism_planes(a,b,4,6)
  ps=ps[2:]+[plane(mul(t,-1),-3,'A',f'C{k}'),plane(tn,-3,'B',f'C{(k+1)%8}')]
  member(f'L{k}-{suffix}','cupola_bands','Contextual cupola band · unconfirmed',a,b,4,6,ps,[CONTEXT,'Hidden by default. R01 does not establish this timber band or its connection; it is not a substitute for the green metal spacer.'])
 for suffix,adj in [('A',k-1),('B',k+1)]:
  a=at(RP,k,H-28);line=unit(sub(at(RP,adj,0),at(RP,k,0)));b=add(at(RP,k,H),mul(line,28))
  ps,_,_=prism_planes(a,b,3,4.8)
  member(f'K{k}-{suffix}','braces','Contextual knee brace',a,b,3,4.8,ps,[CONTEXT,'28 in horizontal/vertical projection retained; ends need redesigned joinery.'])
 # Parallel short rafters, two in each bay. Clip every edge to the hip face.
 n=[math.cos((k+.5)*math.pi/4),math.sin((k+.5)*math.pi/4),0.];w=[-n[1],n[0],0.]
 e0,e1=at(RE,k,0),at(RE,k+1,0)
 for suffix,st,hip,side_sign in [('0',STATION,k,1),('2',1-STATION,k+1,-1)]:
  q=add(mul(e0,1-st),mul(e1,st));plan_run=(RE-RHO)*math.cos(ALPHA)
  contact_run=plan_run-4/math.sin(ALPHA)
  # Centreline through the roof-parallel 4×8 stock. Reference axis remains separately documented.
  top_start=ROOF_K-PN*dot(n,q);mid_offset=4/math.cos(math.atan(PN))
  a=[q[0],q[1],top_start-mid_offset];b=add(a,[-n[0]*contact_run,-n[1]*contact_run,PN*contact_run])
  hip_t=tangent(hip);ps=[plane(n,dot(n,q),'A'),plane(mul(hip_t,-side_sign),-4,'B',f'R{hip%8}'),plane(w,dot(w,q)+2),plane(mul(w,-1),-dot(w,q)+2),plane([PN*n[0],PN*n[1],1],ROOF_K),plane([-PN*n[0],-PN*n[1],-1],-ROOF_K+8/math.cos(math.atan(PN)))]
  p=member(f'J{k}-{suffix}','secondary_approx','Short rafter · hip side-face contact',a,b,4,8,ps,['4 × 8 in source reading is provisional; actual 4 in width used for 42⅜ in clear gap.','Runs perpendicular to its eave, not toward the centre. Every upper end vertex terminates on the receiving hip side plane.','Top surfaces share the adjacent backed hip roof plane. Housings, bearing depth and fasteners remain unresolved.'],reference={'bay':k,'receiving_hip':f'R{hip%8}','station':st,'axis_intersection_radius_in':RHO,'axis_plan_run_in':plan_run,'axis_sloping_length_in':plan_run*math.sqrt(1+PN*PN),'side_face_plan_run_in':contact_run,'side_face_sloping_length_in':contact_run*math.sqrt(1+PN*PN),'roof_reference_pitch':PN,'clear_gap_in':GAP})

# Independent metal is symbolic: dimensions of its section are display choices.
for k in range(8):
 r,t=radial(k),tangent(k);rn,tn=radial(k+1),tangent(k+1)
 a=add(mul(r,44),mul(t,3));b=add(mul(rn,44),mul(tn,-3));a[2]=b[2]=H+45+3
 ps,_,_=prism_planes(a,b,.125,2)
 member(f'M-SP{k}','metal_spacers','Cupola metal spacer · 28⅛ in setting-out gap',a,b,.125,2,ps,['28.132865 in outer-corner gap (rounds to 28⅛ in).','Position along post, thickness, strip depth, returns, holes, fasteners and developed blank length unresolved; section shown only for visibility.'],material='steel')
 a=[0,0,H-7];b=at(44,k,H-7);ps,_,_=prism_planes(a,b,.125,4,t)
 member(f'M-TMP{k}','temporary_fixture','Temporary central assembly fixture · arm',a,b,.125,4,ps,['One of eight symbolic arms; 88 in overall source span. Source terminal height 14 in and strip depth 4 in.','Not permanent timber. Steel thickness shown only for visibility. Terminals, holes, attachment, erection capacity and removal criteria are unresolved.'],material='steel',temporary=True)

# Optional cupola roof envelope: surface shell only, not a rafter or roof assembly.
for k in range(8):
 base=H+45+32
 apex=[0,0,base+44/3]
 a,b=at(56,k,base-4),at(56,k+1,base-4)
 n=[math.cos((k+.5)*math.pi/4),math.sin((k+.5)*math.pi/4),0]
 # A 0.05 in visualization shell prevents degenerate mesh; it is not material thickness.
 ps=[plane(mul(tangent(k),-1),0,'A'),plane(tangent(k+1),0,'B'),plane(n,56*math.cos(ALPHA)),plane([PN*n[0],PN*n[1],1],apex[2]),plane([-PN*n[0],-PN*n[1],-1],-apex[2]+.05)]
 p=member(f'ENV-CUP{k}','roof_envelope','Cupola roof reference surface',a,apex,0,.05,ps,['4:12 radial pitch, 12 in radial overhang beyond the 44 in outside face.','Surface envelope only; 0.05 in shell is a rendering choice, not a roof material or structural section.'],material='surface')

GROUPS=[('perimeter_posts','Perimeter posts','#876247',True),('eave_ring','Perimeter ring beams · provisional','#ae7c4a',True),('radial_ties','Lower radial ties · 6 × 10','#c39a56',True),('radial_rafters','Eight main hips · 8 × 10','#6f8b7b',True),('cupola_posts','Cupola posts · 6 × 6','#8d6e99',True),('cupola_bands','Previous cupola bands · unconfirmed','#a88bb4',False),('braces','Knee braces · provisional','#a68764',True),('secondary_approx','Sixteen short rafters · 4 × 8','#879da2',True),('metal_spacers','Green metal cupola spacers','#28784c',True),('temporary_fixture','Temporary assembly fixture','#273036',False),('roof_envelope','Cupola roof reference envelope','#698a9b',False)]
RETIRED=[f'J{k}-1' for k in range(8)]
r01={'revision':'R01','basis':'Octagon-architectural-geometry-study-R01.pdf','previous_github_commit':'a431e6257848aafcb7b237eedbaece2ca44f3436','retired_ids':RETIRED,'timber_count':96,'metal_count':16,'surface_count':8,'main_frames':8,'short_rafters':16,'midpoint_rafters':0,'display_height_H_in':H,'height_status':'Unresolved; 90 in display reference only. Timber centre/roof backing offsets are explicit model choices.','outside_post_diameter_in':360,'post_center_diameter_in':352,'eave_tip_diameter_in':400,'cupola_outside_diameter_in':88,'cupola_inside_diameter_in':76,'cupola_center_radius_in':41,'cupola_roof_tip_diameter_in':112,'cupola_spacer_gap_in':28.132864853,'main_radial_pitch':PH,'short_normal_pitch':PN,'lower_tie_section_in':[6,10],'short_rafter_section_in':[4,8],'joint_status':'Exact short-rafter side-contact planes; construction connections unresolved.','heel_status':'Hip/tie/post heel intersections are not resolved into a fabrication joint.','global_overlap_status':'Not validated as collision-free; no old fitted-overlap evidence applies.','retained_contextual_ids':[p['id'] for p in PARTS if p['group'] in ['eave_ring','braces','cupola_bands']],'steel_section_status':'Visibility dimensions only; not specified source stock.','roof_backing_status':'Two top bay planes on hips are explicit display geometry; fabrication backing cuts require confirmation.'}
data={'schema_version':'r01-geometry-1.0','title':'Octagonal timberframe · corrected R01 pattern','units':'meters','up_axis':'Y','date':'2026-11-01','source_model':'reproducible R01 halfspace model','source_dimensions':r01,'main_roof_overhang_normal_ft':16.946857/12,'main_roof_overhang_datum':'20 in corner projection beyond outside radial post faces; normal overhang is conditional on assumed 8 in posts.','status':'R01 GEOMETRY REVIEW · JOINTS NOT CONSTRUCTION APPROVED','axis_convention':'Y up; original A/B direction maintained for surviving timbers.','angle_convention':'Angles describe geometry, not saw settings.','notes':['96 wood timbers after retiring eight Jk-1 midpoint rafters.','Existing 40% keyed cuts and old fit/clearance/assembly claims are superseded.','Ground and member-bearing heights remain unresolved.','Short rafter end faces are exact plane intersections; they are not finished housed or tenoned joints.'],'r01':r01,'groups':[{'id':i,'label':l,'color':c,'count':sum(p['group']==i for p in PARTS),'default_visible':v} for i,l,c,v in GROUPS],'parts':PARTS,'fit_audit':{'status':'superseded; old R03 audit does not apply to R01','verified_contact_count':None,'max_overlap_m3':None}}
raw=json.dumps(data,separators=(',',':'),ensure_ascii=True)+'\n'
(ROOT/'src/model-data.json').write_text(raw)
groups=[]
for idx,(name,pids) in enumerate([(g[0],[p['id'] for p in PARTS if p['group']==g[0]]) for g in GROUPS if g[0] not in ['secondary_approx','cupola_bands']]+[('short_left',[f'J{k}-0' for k in range(8)]),('short_right',[f'J{k}-2' for k in range(8)])]+[('cupola_'+s,[f'L{k}-{s}' for k in range(8)]) for s in ['L','S','H']],1):
 groups.append({'id':f'M{idx:02}','number':idx,'quantity':len(pids),'member_ids':pids,'representative_id':pids[0],'family':name,'label':name.replace('_',' '),'status':'R01 generation family; no fabrication interchangeability claim','method':'explicit parameterized pattern'})
materials={'schema_version':'r01-material-groups-1.0','source_sha256':hashlib.sha256(raw.encode()).hexdigest(),'timber_count':96,'item_count':120,'group_count':len(groups),'comparison_tolerance_m':None,'scope':'Parameterized generation families; not a fabrication schedule.','groups':groups,'handed_pair_checks':[],'reference_end_semantics':'A/B maintained for surviving wood members; new references describe R01 geometric end planes.'}
(ROOT/'src/material-groups.json').write_text(json.dumps(materials,indent=2)+'\n')
(ROOT/'docs').mkdir(exist_ok=True)
(ROOT/'docs/r01-change-register.json').write_text(json.dumps({'r01':r01,'source_model_sha256':hashlib.sha256(raw.encode()).hexdigest(),'changes':['Retired J0-1 through J7-1; retained other wood IDs.','Replaced 24 approximate radial secondary rafters with 16 eave-normal 4×8 short rafters meeting adjacent hip side faces.','Corrected 30 ft outside-post datum, 33 ft 4 in eave tips, 6×10 ties, radial cupola posts and cupola roof envelope.','Removed inherited arbitrary 40% keys and stale fit reports from active model data.','Added separate green spacer and temporary black fixture groups.'],'unresolved':['Ground-to-tie H; physical bearing datums; main heel joints; mortises/tenons/housings/fasteners; actual sections; steel geometry; glazing and window dimensions.']},indent=2)+'\n')
print(json.dumps({'revision':'R01','timbers':96,'metals':16,'surfaces':8,'items':len(PARTS),'retired':RETIRED,'model_bytes':len(raw)}))
