# TIMESTAMP START 2026-11-05T04:51:00+00:00 | REVISION R000023
# Derived from independently probed research recipe 20b703cd488c651a47533d35af61a2682ec087324470e62f6b90af687a6a3497.
"""EXTERNAL nominal cupola joinery prototype; never writes the repository.

Uses the actual current primary model. Outputs replacement meshes, independent
stock blanks, offcuts, joints, pegs and explicitly scoped solid/path probes.
This is not a production generator, structural approval or public certificate.
"""
import argparse,copy,hashlib,itertools,json,math,sys,time
from pathlib import Path
import numpy as np
import manifold3d as m
REPO=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(REPO/'scripts'))
from audit_revised_joinery import native_solid
from audit_cavity_fit import inspect_mesh
from export_top_entry_cavities import stock as existing_stock
from step_lap import volume_centroid,contacts
from plan_architectural_disassembly import Scene,check_stage,apply_stage,clone_scene,audit_initial_scene
I=.0254;TOL=1e-6*I**3;UP=np.array([0.,1.,0.]);REV='EXTERNAL-CUPOLA-RESEARCH'
def radial(k):return np.array([math.cos(k*math.pi/4),0.,-math.sin(k*math.pi/4)])
def tangent(k):return np.array([math.sin(k*math.pi/4),0.,math.cos(k*math.pi/4)])
def box(lo,hi):
 lo=np.asarray(lo,float);return m.Manifold.cube((np.asarray(hi,float)-lo).tolist()).translate(lo.tolist())
def rotate(s,k):return s.rotate([0,45*k,0])
def union(ss):return m.Manifold.batch_boolean(list(ss),m.OpType.Add) if ss else m.Manifold()
def empty():return m.Manifold()
def amount(s):return max(0.,float(s.volume()))
def diff(a,b):return amount(a-b)+amount(b-a)
def at_most(x,msg):assert x<=TOL,(msg,x/I**3)
def save(path,value):path.write_text(json.dumps(value,indent=2,default=lambda x:x.item() if hasattr(x,'item') else x)+'\n')
def native_record(shape,single=False):
 if shape.is_empty() or abs(shape.volume())<1e-16:return {'vertices':[],'triangles':[],'edges':[],'volume_m3':0.}
 candidates=[shape]+[shape.simplify(e) for e in [1e-10,1e-9,1e-8]]
 for s in candidates:
  mesh=s.to_mesh64();v=np.asarray(mesh.vert_properties)[:,:3];t=np.asarray(mesh.tri_verts,dtype=np.uint64)
  q={'vertices':v.tolist(),'triangles':t.tolist(),'volume_m3':float(s.volume())}
  imported=native_solid(q);audit=inspect_mesh(v,t,require_single=single)
  if str(imported.status())=='Error.NoError' and audit['status']=='PASS' and diff(shape,imported)<=TOL:
   q['edges']=[list(e) for e in sorted({tuple(sorted((int(f[i]),int(f[(i+1)%3])))) for f in t for i in range(3)})];return q
 raise AssertionError(('unusable boundary',str(shape.status()),audit))
def planes_from_world(planes):
 return [{'normal':[float(n[0]),float(-n[2]),float(n[1])],'constant':float(k/I),'end':None,'mate':None} for n,k in planes]
def box_planes(r,t,lo,hi,width,height,y):
 # Sloping CR blanks use their independently recorded roof planes separately.
 return planes_from_world([(r,hi),(-r,-lo),(t,width/2),(-t,width/2),(UP,y+height/2),(-UP,-y+height/2)])
def prism_from_footprint(record,lo,hi):
 v=np.asarray(record['vertices']);return m.Manifold.hull_points(np.array([[p[0],y,p[2]] for p in v for y in [lo,hi]]))
def cylinder(center,axis,radius=.1875*I,length=80*I):
 axis=np.asarray(axis,float);u=np.cross(axis,np.eye(3)[np.argmin(abs(axis))]);u/=np.linalg.norm(u);v=np.cross(axis,u)
 return m.Manifold.cylinder(length,radius,radius,32,center=True).transform(np.column_stack([u,v,axis,np.asarray(center)]).tolist())
def prototype(source,out):
 started=time.time();source_raw=source.read_bytes();source_sha=hashlib.sha256(source_raw).hexdigest();model=json.loads(source_raw);assert not model.get('research_only') and not any(p['id']=='CUP-KINGPOST' for p in model['parts']),'Use a frozen pre-cupola input; do not feed a generated candidate back into the recipe';independent_main_hips=bool(model.get('independent_hip_entry_revision'));P={p['id']:copy.deepcopy(p) for p in model['parts']}
 S={pid:native_solid(p) for pid,p in P.items() if p.get('triangles')};original=dict(S);blanks={};blank_planes={};envelopes={};offcuts={};changed=set();new_ids=[];new_joints=[];joint_updates={};entry_regions=copy.deepcopy(model.get('joinery_entry_regions',{}));peg_info=[];part_bores={}
 cy=float(P['CC0']['center'][1]);bottom=cy-3*I;hubA=6*I;apex=float(P['CR0']['axis_end'][1]);roof_center_at_face=apex-hubA/3;hubtop=roof_center_at_face+math.sqrt(10)*I
 # Source dimensions are measured from the actual file, not assumed from IDs.
 assert abs(P['CC0']['dimensions']['width_in']-4)<1e-8 and abs(P['CR0']['dimensions']['width_in']-2)<1e-8
 for k in range(8):
  assert P[f'C{k}']['dimensions']['width_in']==6 and P[f'C{k}']['dimensions']['depth_in']==6
  assert P[f'P{k}']['dimensions']['width_in']==8 and P[f'P{k}']['dimensions']['depth_in']==8
 # Reuse actual upper-band body geometry and restore only its exact old pockets.
 old_h=[j for j in model['tenon_schedule'] if j['donor'].startswith('L') and j['donor'].endswith('-H')]
 for k in range(8):
  pid=f'C{k}';raw=existing_stock(P[pid]);old_tools=[native_solid(j.get('cutting_tool',j['connector'])) for j in old_h if j['receiver']==pid]
  
  # Replace only the verified upper unjointed interval, with a positive-overlap
  # splice in unchanged wood; direct cavity refill can retain zero-thickness flaps.
  lower=S[pid].trim_by_plane([0,-1,0],-170.01*I);upper=raw.trim_by_plane([0,1,0],170*I)
  restored=lower+upper;at_most(diff(restored-union(old_tools),original[pid]),pid+'upper reconstruction changed other material')
  S[pid]=restored;changed.add(pid)
 for k in range(8):
  pid=f'L{k}-H';body=S[pid];offcut_cutters=[]
  for j in [j for j in old_h if j['donor']==pid]:body=body-native_solid(j['connector'])
  actual_body=body;lhblank=existing_stock(P[pid]);body=lhblank
  for plane in P[pid]['geometry_planes_inches']:
   if plane.get('end') not in ['A','B']:continue
   normal=np.array([plane['normal'][0],plane['normal'][2],-plane['normal'][1]]);length=np.linalg.norm(normal);body=body.trim_by_plane((-normal/length).tolist(),-plane['constant']*I/length)
  at_most(diff(actual_body,body),pid+'actual LH body differs from exact stock-frame body')
  for j in [j for j in old_h if j['donor']==pid]:
   lo,hi=(cy-2.75*I,cy-I) if j['end']=='A' else (cy+I,cy+2.75*I)
   conn=prism_from_footprint(j['connector'],lo,hi);tool=prism_from_footprint(j.get('cutting_tool',j['connector']),lo,hi);body=body+tool;S[j['receiver']]=S[j['receiver']]-tool
   along=np.asarray(P[pid]['stock_frame']['axis'])*(-1 if j['end']=='A' else 1);offcut_cutters.append(tool+tool.translate((along*.05*I).tolist()))
   q=copy.deepcopy(j);q.update(shape='blind three-inch shouldered ring tenon; staggered upper-band level',connector=native_record(conn),cutting_tool=native_record(tool),height_m=hi-lo,face_center=[j['face_center'][0],(lo+hi)/2,j['face_center'][2]]);joint_updates[q['id']]=q
  S[pid]=body;blanks[pid]=lhblank;blank_planes[pid]=copy.deepcopy(P[pid].get('proposed_stock_planes_inches',P[pid]['geometry_planes_inches']));envelopes[pid]=body;old_offcut=blanks[pid]-body;offcuts[pid]=blanks[pid]-(body+union(offcut_cutters));at_most(diff(old_offcut,offcuts[pid]),pid+'offcut cap extension changed occupied stock');changed.add(pid)
 # Actual CC outside the new hub face, with integral central/outer tenons.
 for k in range(8):
  pid=f'CC{k}';r=radial(k);t=tangent(k);actual_body=original[pid].trim_by_plane(r.tolist(),hubA);body=rotate(box([6*I,cy-3*I,-2*I],[38*I,cy+3*I,2*I]),k);at_most(diff(actual_body,body),pid+'actual CC body differs from exact stock-frame body')
  inner=rotate(box([3*I,cy-2*I,-.5*I],[6*I,cy+2*I,.5*I]),k)
  outer=rotate(box([38*I,cy-.75*I,-.5*I],[41*I,cy+.75*I,.5*I]),k)
  inner_root=rotate(box([3*I,cy-2*I,-.5*I],[6.01*I,cy+2*I,.5*I]),k);outer_root=rotate(box([37.99*I,cy-.75*I,-.5*I],[41*I,cy+.75*I,.5*I]),k)
  S[pid]=body+inner_root+outer_root;S[f'C{k}']=S[f'C{k}']-outer
  blanks[pid]=rotate(box([3*I,cy-3*I,-2*I],[41*I,cy+3*I,2*I]),k);blank_planes[pid]=box_planes(r,t,3*I,41*I,4*I,6*I,cy);envelopes[pid]=S[pid];offcuts[pid]=blanks[pid]-S[pid];changed.add(pid)
  for receiver,conn,direction,face,kind in [(f'C{k}',outer,r,38*I,'blind outer shoulder tenon'),('CUP-KINGPOST',inner,-r,6*I,'bottom-entry housed ceiling tenon')]:
   new_joints.append({'id':f'CJ-{pid}-{receiver}','donor':pid,'receiver':receiver,'shape':kind,'projection_m':3*I,'width_m':I,'height_m':(1.5 if receiver.startswith('C') and receiver!='CUP-KINGPOST' else 4)*I,'insertion_direction':direction.tolist(),'width_direction':t.tolist(),'height_direction':UP.tolist(),'face_center':(r*face+UP*cy).tolist(),'connector':native_record(conn),'cutting_tool':native_record(conn)})
 # Twelve-inch square blank dressed into an octagon; bottom/top entry slots.
 hubblank=box([-hubA,bottom,-hubA],[hubA,hubtop,hubA]);hub=hubblank
 for k in range(8):hub=hub.trim_by_plane((-radial(k)).tolist(),-hubA)
 hub_envelope=hub;hubtools=[]
 # Explicit convex corner prisms avoid zero-area membranes from square-minus-octagon.
 edge=hubA*(math.sqrt(2)-1);corner=m.Manifold.hull_points(np.array([[x,y,z] for x,z in [(hubA,hubA),(hubA,edge),(edge,hubA)] for y in [bottom,hubtop]]));hub_offcuts=union([rotate(corner,2*k) for k in range(4)]);at_most(diff(hubblank-hub_envelope,hub_offcuts),'hub corner offcuts differ')
 for k in range(8):
  hubtools.append(rotate(box([3*I,bottom-.01*I,-.5*I],[6.01*I,cy+2*I,.5*I]),k))
  hubtools.append(rotate(box([3*I,roof_center_at_face-1.5*I,-.5*I],[6.01*I,hubtop+.01*I,.5*I]),k))
 hubcutter=union(hubtools);S['CUP-KINGPOST']=hub-hubcutter;blanks['CUP-KINGPOST']=hubblank;blank_planes['CUP-KINGPOST']=planes_from_world([(np.array([1.,0,0]),hubA),(np.array([-1.,0,0]),hubA),(np.array([0.,0,1]),hubA),(np.array([0.,0,-1]),hubA),(UP,hubtop),(-UP,-bottom)]);envelopes['CUP-KINGPOST']=hub_envelope;offcuts['CUP-KINGPOST']=hub_offcuts;entry_regions['CUP-KINGPOST']=native_record(hubcutter);new_ids.append('CUP-KINGPOST')
 # A flat housed C-head seat makes the vertical projection exactly three inches.
 # The unchanged sloping shoulders outside the new 3x2in flat seat remain.
 slope=1/3;under0=float(P['CR0']['axis_end'][1])-math.sqrt(10)*I;seat=under0-39.5*I*slope;head_connectors={};head_tools={}
 for k in range(8):
  r=radial(k);t=tangent(k);pid=f'CR{k}';body=original[pid].trim_by_plane(r.tolist(),hubA)
  apex_conn=rotate(box([3*I,roof_center_at_face-1.5*I,-.5*I],[6*I,roof_center_at_face+1.5*I,.5*I]),k)
  apex_root=rotate(box([3*I,roof_center_at_face-1.5*I,-.5*I],[6.01*I,roof_center_at_face+1.5*I,.5*I]),k);pre=body+apex_root
  # Wedge under the flat seat, including .05in root overlap with actual C wood.
  wedge_points=np.array([[x*I,y,z*I] for x in [39.5,42.5] for z in [-1,1] for y in [under0-x*I*slope-.05*I,seat]])
  wedge=rotate(m.Manifold.hull_points(wedge_points),k)
  male=rotate(box([39.5*I,seat,-.5*I],[42.5*I,seat+3*I,.5*I]),k);male_root=rotate(box([39.5*I,seat-.01*I,-.5*I],[42.5*I,seat+3*I,.5*I]),k);head_tools[k]=wedge+male_root;head_connectors[k]=male
  S[f'C{k}']=S[f'C{k}']+head_tools[k];S[pid]=pre-head_tools[k]
  # Independent rectangular sloping 2x6 blank; no old center miter in stock.
  raw=box([-100*I,-100*I,-100*I],[100*I,300*I,100*I]);worldplanes=[]
  for normal,const in [(r,56*I),(-r,-3*I),(t,I),(-t,I),(UP+r*slope,under0+2*math.sqrt(10)*I),(-UP-r*slope,-under0)]:
   length=np.linalg.norm(normal);raw=raw.trim_by_plane((-normal/length).tolist(),-const/length);worldplanes.append((normal,const))
  canonical_body=raw.trim_by_plane(r.tolist(),hubA);at_most(diff(body,canonical_body),pid+'actual CR body differs from exact stock-frame body');pre=canonical_body+apex_root;S[pid]=pre-head_tools[k]
  blanks[pid]=raw;blank_planes[pid]=planes_from_world(worldplanes);envelopes[pid]=pre;offcuts[pid]=raw-pre;changed.add(pid)
  new_joints.append({'id':f'CJ-{pid}-CUP-KINGPOST','donor':pid,'receiver':'CUP-KINGPOST','shape':'top-entry housed roof-apex tenon','projection_m':3*I,'width_m':I,'height_m':3*I,'insertion_direction':(-r).tolist(),'width_direction':t.tolist(),'height_direction':UP.tolist(),'face_center':(r*hubA+UP*roof_center_at_face).tolist(),'connector':native_record(apex_conn),'cutting_tool':native_record(apex_conn)})
  new_joints.append({'id':f'CJ-C{k}-{pid}','donor':f'C{k}','receiver':pid,'shape':'three-inch upright head tenon above flat housed bearing seat','projection_m':3*I,'width_m':I,'height_m':3*I,'insertion_direction':UP.tolist(),'width_direction':t.tolist(),'height_direction':r.tolist(),'face_center':(r*41*I+UP*seat).tolist(),'connector':native_record(male),'cutting_tool':native_record(head_tools[k]),'housing':native_record(wedge),'flat_seat_y_m':seat,'bearing_footprint_in':[3,2]})
  # Full6x6 straight blank with exact new horizontal top; offcuts exclude all pockets.
  newtop=seat+3*I;cb=rotate(box([38*I,85*I,-3*I],[44*I,newtop,3*I]),k)
  old_envelope=existing_stock(P[f'C{k}']);ce=old_envelope+head_tools[k]
  blanks[f'C{k}']=cb;blank_planes[f'C{k}']=box_planes(r,t,38*I,44*I,6*I,newtop-85*I,(newtop+85*I)/2);envelopes[f'C{k}']=ce;offcuts[f'C{k}']=cb-ce
 # Canonical source families avoid coplanar slivers from independently
 # rounded rotated void boundaries. Quantify original family isometry first.
 family_isometry=[]
 for stem,suffix in [('C',''),('CR',''),('CC',''),('L','-H')]:
  seed=stem+'0'+suffix
  for k in range(8):
   pid=stem+str(k)+suffix;err=diff(original[pid],rotate(original[seed],k));at_most(err,pid+'source family not isometric');family_isometry.append({'id':pid,'source_family_difference_in3':err/I**3})
  canonical=S[seed];canonical_blank=blanks.get(seed);canonical_envelope=envelopes.get(seed);canonical_offcut=native_solid(native_record(offcuts[seed])) if seed in offcuts and not offcuts[seed].is_empty() else offcuts.get(seed)
  for k in range(8):
   pid=stem+str(k)+suffix;S[pid]=rotate(canonical,k)
   if canonical_envelope is not None:envelopes[pid]=rotate(canonical_envelope,k)
   if canonical_blank is not None:blanks[pid]=rotate(canonical_blank,k)
   if canonical_offcut is not None:offcuts[pid]=rotate(canonical_offcut,k)
 # Preserve existing L-S envelopes and add real bores through both cheeks.
 for k in range(8):
  pid=f'L{k}-S';envelopes[pid]=original[pid];blanks[pid]=existing_stock(P[pid]);blank_planes[pid]=copy.deepcopy(P[pid].get('proposed_stock_planes_inches',P[pid]['geometry_planes_inches']));changed.add(pid)
  offcuts[pid]=native_solid(P[pid]['declared_exterior_cut']) if P[pid].get('declared_exterior_cut',{}).get('triangles') else empty()
 # Source ring schedules are preserved except actual upper height changes.
 schedule=[copy.deepcopy(joint_updates.get(j['id'],j)) for j in model['tenon_schedule']]+new_joints
 def peg_for(j,center,axis):
  donor,receiver=j['donor'],j['receiver'];pid='CUP-PEG-'+j['id'];bore=cylinder(center,axis);peg=bore^envelopes.get(receiver,blanks[receiver])
  assert peg.volume()>0,(pid,'empty peg',receiver,blanks[receiver].bounding_box(),np.asarray(center).tolist(),np.asarray(axis).tolist(),blanks[receiver].volume());engage=(peg^native_solid(j['connector'])).volume();assert engage>.02*I**3,(pid,'misses connector',engage/I**3)
  cheeks=peg^S[receiver];lengths=[float(np.ptp(np.asarray(q.to_mesh64().vert_properties)[:,:3]@np.asarray(axis))/I) for q in cheeks.decompose() if q.volume()>1e-14]
  
  if len(lengths)!=2:
   save(out/'debug-peg-cheeks.json',{'pid':pid,'cheeks':[{'volume_in3':q.volume()/I**3,'length_in':float(np.ptp(np.asarray(q.to_mesh64().vert_properties)[:,:3]@np.asarray(axis))/I)} for q in cheeks.decompose()]})
   raise AssertionError((pid,'receiver cheeks',lengths))
  S[donor]=S[donor]-bore;S[receiver]=S[receiver]-bore;part_bores.setdefault(donor,[]).append(bore);part_bores.setdefault(receiver,[]).append(bore);S[pid]=peg;new_ids.append(pid);j['peg_id']=pid
  dims={'length_m':float(np.ptp(np.asarray(peg.to_mesh64().vert_properties)[:,:3]@np.asarray(axis))),'width_m':.375*I,'depth_m':.375*I,'width_in':.375,'depth_in':.375,'section_display':'3/8 in round hardwood peg','status':'External nominal research geometry; capacity unverified'}
  P[pid]={'id':pid,'name':'Cupola hardwood locking peg','group':'joinery_pegs','material':'hardwood','is_timber':False,'is_fastener':True,'center':np.asarray(center).tolist(),'label_position':np.asarray(center).tolist(),'axis_direction':np.asarray(axis).tolist(),'withdrawal_direction':np.asarray(axis).tolist(),'withdrawal_distance_m':dims['length_m']+.05,'dimensions':dims,'nominal_dimensions':copy.deepcopy(dims),'peg_geometry':{'joint_id':j['id'],'donor':donor,'receiver':receiver,'diameter_m':.375*I},'exploded_offset':(radial(int(donor[2]) if donor.startswith(('CC','CR')) else int(donor[1]))*10+UP*6).tolist(),'research_only':True}
  peg_info.append({'id':pid,'joint':j['id'],'donor':donor,'receiver':receiver,'axis':np.asarray(axis).tolist(),'center_m':np.asarray(center).tolist(),'engagement_in3':engage/I**3,'receiver_cheek_lengths_in':lengths})
 for j in schedule:
  donor=j['donor'];receiver=j['receiver']
  if donor.startswith('L') and donor.endswith(('-S','-H')):
   k=int(receiver[1]);q=np.asarray(j['insertion_direction']);v=np.asarray(j['connector']['vertices']);point=np.asarray(j['face_center'])+q*1.25*I;y=float((v[:,1].min()+v[:,1].max())/2);point[1]=y;peg_for(j,point,radial(k))
  elif j['id'].startswith('CJ-'):
   k=int(donor[2]) if donor.startswith(('CC','CR')) else int(donor[1]);r=radial(k);t=tangent(k)
   if receiver=='CUP-KINGPOST':
    mid=cy if donor.startswith('CC') else roof_center_at_face;step=I if donor.startswith('CC') else .75*I;point=r*5.5*I+UP*(mid+(step if k%2 else -step));peg_for(j,point,t)
   elif donor.startswith('CC'):peg_for(j,r*39.5*I+UP*cy,t)
   else:peg_for(j,r*41*I+UP*(seat+1.5*I),t)
 # Cut the PLY opening rather than overlapping the new central timber.
 if 'PLY' in S:
  hole=box([-(6.0625)*I,-100*I,-6.0625*I],[6.0625*I,300*I,6.0625*I])
  for k in range(8):hole=hole.trim_by_plane((-radial(k)).tolist(),-6.0625*I)
  S['PLY']=S['PLY']-hole;changed.add('PLY')
 # Record connectors after actual bores, so donor voids are not called mating wood.
 changed_joint_ids=[]
 for j in schedule:
  if j['donor'] in changed or j['receiver']=='CUP-KINGPOST':
   old=native_solid(j['connector']);conn=old-union(part_bores.get(j['donor'],[]));at_most(amount(conn-S[j['donor']]),j['id']+'connector outside donor');j['connector']=native_record(conn)
   direction=np.asarray(j['insertion_direction']);projection=float(np.ptp(np.asarray(j['connector']['vertices'])@direction))
   # C-head connector is exact3in above its flat seat; other tenons are radial.
   assert abs(projection-3*I)<1e-8,(j['id'],'not3in',projection/I);changed_joint_ids.append(j['id'])
 # New hub record, with an independent12x12 blank and distinct exterior dressing.
 P['CUP-KINGPOST']={'id':'CUP-KINGPOST','name':'Octagonal cupola kingpost and ceiling hub','group':'cupola_posts','material':'wood','is_timber':True,'axis_start':[0,bottom,0],'axis_end':[0,hubtop,0],'axis_direction':[0,1,0],'stock_frame':{'axis':[0,1,0],'width':[1,0,0],'depth':[0,0,1]},'center':[0,(bottom+hubtop)/2,0],'label_position':[0,(bottom+hubtop)/2,0],'dimensions':{'width_in':12,'depth_in':12,'width_m':12*I,'depth_m':12*I,'length_m':hubtop-bottom,'section_display':'12in AF octagon from12x12 blank','status':'External nominal research geometry'},'nominal_dimensions':{'width_in':12,'depth_in':12,'width_m':12*I,'depth_m':12*I,'length_m':hubtop-bottom},'exploded_offset':[0,8,0],'geometry_planes_inches':blank_planes['CUP-KINGPOST'],'research_only':True}
 # Serialize every changed/new record. Geometry quality checks never reduce TOL.
 replacements={};stock_data={};mesh_checks=[]
 for pid in sorted(changed|set(new_ids)):
  print('Serialize',pid,flush=True);p=P[pid];q=native_record(S[pid],single=True);imported=native_solid(q);assert len(imported.decompose())==1,(pid,'disconnected')
  p.update(q);p['faces']=p['triangles'];p['fit_geometry']={**p.get('fit_geometry',{}),**volume_centroid(imported)};p['research_only']=True
  if pid in blanks:
   at_most(amount(S[pid]-blanks[pid]),pid+'outside independent blank');p['proposed_stock_planes_inches']=blank_planes[pid]
   if pid in offcuts:p['declared_exterior_cut']=native_record(offcuts[pid])
   axis=np.asarray(p['stock_frame']['axis']);v=np.asarray(native_record(blanks[pid])['vertices']);minimum=float(np.ptp(v@axis)/I);p['new_stock_requirements']={**p.get('new_stock_requirements',{}),'minimum_blank_length_in':minimum,'quarter_inch_blank_length_in':math.ceil((minimum-1e-8)*4)/4,'status':'Exact external research blank envelope; add fabrication/dressing allowance','preserved_section_in':[p['dimensions']['width_in'],p['dimensions']['depth_in']]}
   stock_data[pid]={'blank':native_record(blanks[pid]),'planes_inches':blank_planes[pid],'working_envelope_before_pockets':native_record(envelopes.get(pid,blanks[pid]-offcuts.get(pid,empty()))),'declared_exterior_cut':native_record(offcuts.get(pid,empty())),'minimum_blank_length_in':minimum,'section_in':[p['dimensions']['width_in'],p['dimensions']['depth_in']]}
  replacements[pid]=p;mesh_checks.append({'id':pid,'connected_components':len(imported.decompose()),'volume_in3':imported.volume()/I**3,'native_roundtrip_difference_in3':diff(S[pid],imported)/I**3})
 # All untouched original records, including P/B/T/K/R/CP, remain identical.
 original_ids=set(p['id'] for p in model['parts']);assert all(P[p['id']]==p for p in model['parts'] if p['id'] not in changed)
 allparts=[replacements.get(p['id'],copy.deepcopy(p)) for p in model['parts']]+[replacements[pid] for pid in new_ids if pid not in original_ids]
 # Rebuild source mates from actual serialized records for all local checks.
 serialized={p['id']:p for p in allparts};SS={pid:native_solid(p) for pid,p in serialized.items() if p.get('triangles')};physical={pid:p for pid,p in serialized.items() if p.get('is_timber') or p.get('is_fastener') or pid in ['M-TMP','PLY']};primary=Scene(REV,physical,{pid:SS[pid] for pid in physical},{pid:np.zeros(3) for pid in physical});static=audit_initial_scene(primary);print('Static primary',static['status'],static['collisions'][:5],flush=True)
 preservation=[]
 for k in range(8):
  pid=f'C{k}';low=lambda sh:sh.trim_by_plane([0,-1,0],-110*I);footdiff=diff(low(original[pid]),low(SS[pid]));at_most(footdiff,pid+'foot changed')
  reg_record=model.get('joinery_entry_regions',{}).get(pid);reg=native_solid(reg_record) if reg_record and reg_record.get('triangles') else empty();entrydiff=amount((original[pid]-SS[pid])^reg)+amount((SS[pid]-original[pid])^reg);at_most(entrydiff,pid+'hip entry changed');preservation.append({'id':pid,'foot_region_difference_in3':footdiff/I**3,'hip_entry_region_difference_in3':entrydiff/I**3})
 # Upper post sockets are actually disjoint after the L-H stagger.
 upper_pairs=[]
 for k in range(8):
  js=[j for j in schedule if j['receiver']==f'C{k}' and (j['donor'].endswith('-H') or j['donor']==f'CC{k}')]
  for a,b in itertools.combinations(js,2):
   overlap=amount(native_solid(a['connector'])^native_solid(b['connector']));at_most(overlap,'upper mortises cross');upper_pairs.append({'a':a['id'],'b':b['id'],'overlap_in3':overlap/I**3})
 proofs=[]
 def local_scene(ids):return Scene(REV,{p:serialized[p] for p in ids},{p:SS[p] for p in ids},{p:np.zeros(3) for p in ids})
 cupbase=[p for p in physical if p.startswith(('C','L')) or p=='PLY']
 # All upper wood pegs are declared prerequisite removals for these local probes.
 cupbase=[p for p in cupbase if not p.startswith('CUP-PEG-')]
 for k in range(8):
  trial=local_scene(cupbase);pid=f'CR{k}'
  for name,delta in [('UP3.025in',UP*3.025*I),('OUT3.025in',radial(k)*3.025*I)]:
   proof=check_stage(trial,[pid],delta,stop_first=True);proofs.append({'scope':'cupola wood subset; locking pegs/covers prerequisite removals','test':pid+' '+name,'proof':proof});assert proof['status']=='PASS',(pid,name,proof['collisions']);apply_stage(trial,[pid],delta,proof,'Local research '+name)
 hub_ids=[p for p in cupbase if not p.startswith('CR')];trial=local_scene(hub_ids);proof=check_stage(trial,['CUP-KINGPOST'],UP*5.025*I,stop_first=True);proofs.append({'scope':'cupola subset after CR and locking peg prerequisite removals','test':'hub UP5.025in','proof':proof});assert proof['status']=='PASS',proof
 cc_ids=[p for p in hub_ids if p!='CUP-KINGPOST']
 for k in range(8):
  trial=local_scene(cc_ids);pid=f'CC{k}';proof=check_stage(trial,[pid],-radial(k)*3.025*I,stop_first=True);proofs.append({'scope':'cupola subset after hub/own outer peg prerequisite removals','test':pid+' IN3.025in','proof':proof});assert proof['status']=='PASS',(pid,proof)
 # Existing independent hip route, with short J rafters as explicit prerequisites.
 if independent_main_hips:
  hip_ids=[p for p in physical if not p.startswith('J')];trial=local_scene(hip_ids)
  for k in range(8):
   for delta in [UP*I,radial(k)*4*I]:
    proof=check_stage(trial,[f'R{k}'],delta,stop_first=True);proofs.append({'scope':'all candidate primary physical actors except prerequisite J rafters; architecture excluded','test':f'R{k} independent hip','proof':proof});assert proof['status']=='PASS',(k,proof);apply_stage(trial,[f'R{k}'],delta,proof,'Preserved independent hip')
 # Existing positive foot bearing/CP retention remains demonstrable.
 foot_ids=['C0','T0']+(['CP0'] if 'CP0' in serialized else []);foot=local_scene(foot_ids);down=check_stage(foot,['C0'],[0,-.1,0],stop_first=False);up=check_stage(foot,['C0'],[0,.1,0],stop_first=False);source_foot=Scene(REV,{p:P[p] for p in foot_ids},{p:original[p] for p in foot_ids},{p:np.zeros(3) for p in foot_ids});source_up=check_stage(source_foot,['C0'],[0,.1,0],stop_first=False);faces=contacts(SS['C0'],SS['T0']);bearing=sum(float(f['area_in2']) for f in faces if np.linalg.norm(np.asarray(f['normal_on_rafter'])-[0,-1,0])<1e-8);source_bearing=sum(float(f['area_in2']) for f in contacts(original['C0'],original['T0']) if np.linalg.norm(np.asarray(f['normal_on_rafter'])-[0,-1,0])<1e-8);assert down['status']=='BLOCKED' and up['status']==source_up['status'] and abs(bearing-source_bearing)<1e-6
 # Export only research data; no old PASS/source bindings are assigned to new geometry.
 patch={'scope':'External unverified candidate; apply only after production review and fresh complete audits','input_model_path':str(source),'input_model_sha256':source_sha,'replace_parts':{k:v for k,v in replacements.items() if k in original_ids},'add_parts':{k:v for k,v in replacements.items() if k not in original_ids},'tenon_schedule':schedule,'joinery_entry_regions':entry_regions,'stock_envelopes_file':'cupola-stock-envelopes.json'}
 candidate={'schema_version':model.get('schema_version'),'title':'External cupola timber-joinery research candidate','units':model.get('units'),'up_axis':model.get('up_axis'),'source_dimensions':copy.deepcopy(model.get('source_dimensions')),'groups':copy.deepcopy(model.get('groups')),'parts':allparts,'tenon_schedule':schedule,'joinery_entry_regions':entry_regions,'research_only':True,'status':'UNVERIFIED EXTERNAL RESEARCH CANDIDATE','research_source':{'path':str(source),'sha256':source_sha}}
 report={'scope':'External candidate actual-solid geometry research. Static and local probes only; no capacity/public certificate/whole-building construction-path claim.','source_model_path':str(source),'source_model_sha256':source_sha,'independent_main_hips':{'status':'LOCAL_PASS' if independent_main_hips else 'CLOSED_HEAD_VARIANT_NOT_ASSERTED','scope':'Top-entry independent route only; baseline/proposed lower main joints remain unchanged and their complete disassembly stays PARTIAL'},'generator_path':str(Path(__file__).resolve()),'generator_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'changed_original_ids':sorted(changed),'new_ids':new_ids,'primary_piece_count':len(physical),'new_joint_count':len(new_joints),'new_peg_count':len(peg_info),'unchanged_sections':{'P':'8x8','C':'6x6','CC':'4x6','CR':'2x6','L':'4x6'},'hub_across_flats_in':12,'hub_square_blank_in':[12,12],'hub_base_in':bottom/I,'hub_top_in':hubtop/I,'flat_C_CR_seat_in':seat/I,'upper_LH_tenon_levels_relative_CC_in':{'endA':[-2.75,-1],'endB':[1,2.75],'CC_outer':[-.75,.75]},'static_primary_pair_audit':static,'connected_mesh_readback':mesh_checks,'preservation':preservation,'source_family_isometry':family_isometry,'upper_socket_pair_checks':upper_pairs,'pegs':peg_info,'local_probes':proofs,'C0_foot':{'CP_present':'CP0' in serialized,'source_bearing_area_in2':source_bearing,'down_probe':down,'up_with_CP_probe':up,'downward_bearing_area_in2':bearing,'contact_faces':faces},'elapsed_seconds':time.time()-started,'production_integration_required':['Retain every roof/wall/floor/porch solid in complete replay; these probes do not include architecture.','Include new fasteners as cavity mates and physical display/inventory actors.','Add CUP-KINGPOST and new peg maps to cupShift; preserve CC/CR/head pockets when preparing C receiver blanks.','Update actual timber/peg quantities and source-bound stock/cavity/entry audits.','Integrate new joint pipeline after old three-inch rebuild; rerunning old C/L builders would erase these upper cuts.','Bridge40-screw steel candidate is separate and not included here.']}
 save(out/'cupola-candidate-patch.json',patch);save(out/'cupola-candidate-model.json',candidate);save(out/'cupola-stock-envelopes.json',{'scope':'Independent nominal stock envelopes and actual shoulder/end offcuts for research candidate','parts':stock_data});save(out/'cupola-candidate-report.json',report)
 print('DONE',len(changed),'replaced',len(new_ids),'added',len(peg_info),'newpegs','bearing',bearing,'elapsed',time.time()-started,flush=True)
 assert static['status']=='PASS',static['collisions']
 return report

# TIMESTAMP END 2026-11-05T04:51:00+00:00 | REVISION R000023
