# TIMESTAMP START 2026-11-05T08:15:49+00:00 | REVISION R000034
# Derived from independently checked roof_support_candidate.py SHA256 261b49686aa4a790e00480f1db88658181e94bf607215dcdfabdb2b858d3f306.
"""Generate source-bound outer common rafters and bounded geometry checks.

No production files, certificate outputs, or Site writes. The extra rafters
retain existing variant end-joint designs; their measured projection is stated
explicitly rather than calling existing two/one-inch profiles three-inch ones.
"""
import argparse,copy,hashlib,itertools,json,math,sys,time
from pathlib import Path
import numpy as np
import manifold3d as m
D=Path(__file__).resolve().parent
sys.path.insert(0,str(D))
from cupola_joinery_recipe import REPO,I,TOL,UP,native_solid,native_record as raw_native_record,union,amount,diff,save
from export_top_entry_cavities import stock
from step_lap import inside_band,volume_centroid,contacts,regular_boundary
from plan_architectural_disassembly import Scene,check_stage,audit_initial_scene,sweep_cover

def worldnormal(plane):return np.array([plane['normal'][0],plane['normal'][2],-plane['normal'][1]],float)
def atmost(x,what):assert x<=TOL,(what,x/I**3)
CLEANUPS=[]
def native_record(shape,single=False):
 try:return raw_native_record(shape,single)
 except AssertionError:
  clean=regular_boundary(shape);error=diff(shape,clean);atmost(error,'support-plane boundary cleanup changed material');record=raw_native_record(clean,single);CLEANUPS.append({'occupied_difference_in3':error/I**3,'before_triangles':len(shape.to_mesh64().tri_verts),'after_triangles':len(record['triangles'])});return record

def build(source,out,penetration=None):
 CLEANUPS.clear()
 started=time.time();out.mkdir(parents=True,exist_ok=True);sourcebytes=source.read_bytes();sourcesha=hashlib.sha256(sourcebytes).hexdigest();model=json.loads(sourcebytes);assert not any('-OUT' in p['id'] for p in model['parts']),'Use a frozen pre-extra-rafter model, not a previously generated candidate';(out/'frozen-source-model.json').write_bytes(sourcebytes);P={p['id']:copy.deepcopy(p) for p in model['parts']};top=bool(model.get('independent_hip_entry_revision'));sourceP=copy.deepcopy(P)
 S={pid:native_solid(p) for pid,p in P.items() if p.get('triangles') and (p.get('is_timber') or p.get('is_fastener') or pid in ['M-TMP','PLY'])};original=dict(S);changed=set();added=[];stocks={};cuts={};newjoints=[];rows=[]
 proposalbytes=(REPO/'src/top-entry-proposal.json').read_bytes() if top else None
 support_source=json.loads(proposalbytes) if proposalbytes else None
 if proposalbytes:(out/'frozen-top-entry-proposal.json').write_bytes(proposalbytes)
 interfaces={j['owner']:j for j in support_source.get('interfaces',[])} if support_source else {}
 for k in range(8):
  for side in ['0','2']:
   oldid=f'J{k}-{side}';pid=f'J{k}-OUT{side}';p=copy.deepcopy(P[oldid]);u=np.asarray(p['stock_frame']['width']);N=-np.asarray(p['stock_frame']['axis']);N[1]=0;N/=np.linalg.norm(N)
   oldt=float(np.dot(np.asarray(p['axis_start']),u))/I;eave=float(next(q for q in p['geometry_planes_inches'] if q.get('end')=='A')['constant']);hipt=eave*math.tan(math.pi/8);newt=math.copysign((abs(oldt)+hipt)/2,oldt);dt=u*(newt-oldt)*I
   baseplanes=copy.deepcopy(p['geometry_planes_inches']);newplanes=copy.deepcopy(baseplanes)
   for q in newplanes:
    n=worldnormal(q)
    if q.get('end') is None and abs(n@u)>.99:q['constant']+=float(n@dt)/I
   basepart={**p,'geometry_planes_inches':newplanes};basepart.pop('proposed_stock_planes_inches',None);base=stock(basepart,False)
   rpid=next(q['mate'] for q in newplanes if q.get('end')=='B');rblank=stock(P[rpid]);bp=next(q for q in newplanes if q.get('end')=='B');bn=worldnormal(bp)
   dq=-float(bn@dt)/float(bn@N);roofplane=next(q for q in newplanes if worldnormal(q)[1]>.9);rn=worldnormal(roofplane);dy=-float(rn@(dt+N*dq))/float(rn@UP);headshift=dt+N*dq+UP*dy
   assert abs(float(bn@headshift))<1e-12 and abs(float(rn@headshift))<1e-12
   # Preserve the actual source solid and shorten only its upper end. This
   # retains every real lower-foot contour without reconstructing its notch.
   bpid=f'B{k}';bblank=stock(P[bpid]);sourcefoot=original[oldid]^bblank
   sourcefoot=sourcefoot if sourcefoot.volume()>1e-14 else m.Manifold()
   if not sourcefoot.is_empty():
    clean=regular_boundary(sourcefoot);atmost(diff(sourcefoot,clean),oldid+'foot boundary cleanup');sourcefoot=native_solid(native_record(clean))
   foot=sourcefoot.translate(dt.tolist())
   body=original[oldid].translate(dt.tolist()).trim_by_plane((-bn).tolist(),-bp['constant']*I)
   atmost(amount(body-base),pid+' source body outside independently shifted stock')
   extplanes=copy.deepcopy(newplanes)
   if top:
    j=interfaces[oldid];source_nose=native_solid(j['proposed_nose']);source_tool=native_solid(j['top_open_cutter']);atmost(diff(source_nose,original[oldid]^rblank),oldid+' historical nose differs from actual current wood');atmost(amount(source_tool^original[rpid]),rpid+' historical open tool not clear in actual source');nose=source_nose.translate(headshift.tolist());tool=source_tool.translate(headshift.tolist());projection=2.
    if penetration is not None and abs(penetration-2)>1e-12:
     # Same approved inclined landing/support-plane design, optionally with
     # a new chosen3in side penetration. Existing J actors remain untouched.
     projection=float(penetration);next(q for q in extplanes if q.get('end')=='B')['constant']+=projection
     extended=stock({**basepart,'geometry_planes_inches':extplanes},False);rp=P[rpid];rw=np.asarray(rp['stock_frame']['width']);rd=np.asarray(rp['stock_frame']['depth']);sign=1 if np.dot(p['axis_end'],rw)>0 else -1;normal=rw*sign
     # Translate floor along the actual R roof plane; its normal coordinate
     # is invariant under headshift by construction.
     floor=float(rd@np.asarray(rp['axis_end'])+I)
     nose=(extended^rblank.translate((normal*.01*I).tolist())).trim_by_plane(rd.tolist(),floor)
     nose=inside_band(nose,normal,(4-projection)*I,4.01*I)
     conn=nose^rblank;v=np.asarray(conn.to_mesh64().vert_properties)[:,:3];tool=m.Manifold.hull_points(np.vstack([v,v+UP*24*I]))^rblank
    else:next(q for q in extplanes if q.get('end')=='B')['constant']+=projection
    conn=nose^rblank
    face=np.asarray(p['axis_end'])+headshift
   else:
    j=next(j for j in model['tenon_schedule'] if j['donor']==oldid and j['receiver']==rpid);conn=native_solid(j['connector']).translate(headshift.tolist());tool=native_solid(j.get('cutting_tool',j['connector'])).translate(headshift.tolist());nose=tool;projection=j['projection_m']/I;next(q for q in extplanes if q.get('end')=='B')['constant']+=projection;face=np.asarray(j['face_center'])+headshift
   extended=stock({**basepart,'geometry_planes_inches':extplanes},False)
   if top:
    nv=np.asarray(nose.to_mesh64().vert_properties)[:,:3];nose_root=m.Manifold.hull_points(np.vstack([nv,nv-bn*.01*I]))^extended;atmost(amount(nose_root-(base+nose)),pid+'head root changed occupied volume')
   else:nose_root=nose
   candidate=body+nose_root;atmost(amount(candidate-extended),pid+' outside raw blank')
   if top:
    v=np.asarray(nose_root.to_mesh64().vert_properties)[:,:3];open_tool=m.Manifold.hull_points(np.vstack([v,v+UP*24*I]));atmost(diff(original[rpid]^tool,original[rpid]^open_tool),pid+'open-tool extension changed receiver cut');tool=open_tool
   # Same seated foot tongue as actual source, translated only across face.
   S[bpid]=S[bpid]-foot;S[rpid]=S[rpid]-tool;changed|={bpid,rpid}
   exterior=(extended.trim_by_plane(bn.tolist(),bp['constant']*I)-nose)
   if p.get('declared_exterior_cut',{}).get('triangles') and (penetration is None or abs(penetration-2)<1e-12 or not top):
    existing_exterior=native_solid(p['declared_exterior_cut']).translate(headshift.tolist());atmost(diff(exterior,existing_exterior),pid+' translated exterior shape differs');exterior=existing_exterior
   p['id']=pid;p['name']='Additional outer short common rafter '+str(k)+'/'+side;p['label_short']=pid;p['label_lines']=[pid,'4 × 8 in'];p['proposed_stock_planes_inches']=extplanes;p['geometry_planes_inches']=newplanes
   start=np.asarray(p['axis_start'])+dt;end=np.asarray(p['axis_end'])+headshift;p['axis_start']=start.tolist();p['axis_end']=end.tolist();p['center']=((start+end)/2).tolist();p['label_position']=p['center'];p['exploded_offset']=(N*10+UP*(6+len(added)*.01)).tolist();p['reference_end_faces']=[];p['joint_cut_faces']=[]
   axis=np.asarray(p['stock_frame']['axis']);minimum=float(np.ptp(np.asarray(extended.to_mesh64().vert_properties)[:,:3]@axis)/I);reference=float(np.linalg.norm(end-start));p['dimensions'].update(length_m=minimum*I,length_ft=minimum*I/.3048,length_display=f'{minimum:.6f} in minimum raw axial envelope',status='External research measured minimum blank; cutting/dressing allowance and capacity unverified.');p['nominal_dimensions']=copy.deepcopy(p['dimensions']);p['fitted_axial_extent_inches']=float(np.ptp(np.asarray(candidate.to_mesh64().vert_properties)[:,:3]@axis)/I);p['new_stock_requirements']={'minimum_blank_length_in':minimum,'section_in':[4,8],'head_side_projection_in':projection,'reference_axis_length_in':reference/I,'status':'External new-stock research prototype; existing variant joint profile retained unless explicit3in option.'};p['declared_exterior_cut']=native_record(exterior);p['research_only']=True
   geometry=native_record(candidate,single=True);p.update(geometry);p['faces']=p['triangles'];p['fit_geometry']={**p.get('fit_geometry',{}),**volume_centroid(candidate),'nominal_fit':'External additional support rafter; capacity unverified'};P[pid]=p;S[pid]=native_solid(p);added.append(pid)
   cv=np.asarray(conn.to_mesh64().vert_properties)[:,:3]
   joints=[{'id':'ROOF-SUPPORT-'+pid+'-'+rpid,'donor':pid,'receiver':rpid,'end':'B','shape':'top-entry inclined nose' if top else j['shape'],'projection_m':projection*I,'projection_direction':bn.tolist(),'connector':native_record(conn),'cutting_tool':native_record(tool),'face_center':face.tolist(),'insertion_direction':(UP if top else np.asarray(j['insertion_direction'])).tolist(),'width_direction':p['stock_frame']['width'],'height_direction':p['stock_frame']['depth'],'width_m':float(np.ptp(cv@np.asarray(p['stock_frame']['width']))),'height_m':float(np.ptp(cv@np.asarray(p['stock_frame']['depth'])))}]
   if not foot.is_empty():joints.append({'id':'ROOF-SUPPORT-'+pid+'-'+bpid,'donor':pid,'receiver':bpid,'end':'A','shape':'retained tapered perimeter birdsmouth step','projection_m':I,'connector':native_record(foot),'cutting_tool':native_record(foot),'face_center':volume_centroid(foot)['centroid_m'],'insertion_direction':(-UP).tolist(),'width_direction':p['stock_frame']['width'],'height_direction':[0,1,0],'width_m':2*I,'height_m':I})
   newjoints.extend(joints);stocks[pid]={'blank':native_record(extended),'planes_inches':extplanes,'legacy_body_envelope':native_record(base),'declared_exterior_cut':p['declared_exterior_cut'],'minimum_blank_length_in':minimum};cuts[rpid]=cuts.get(rpid,[])+[tool];cuts[bpid]=cuts.get(bpid,[])+([] if foot.is_empty() else [foot]);rows.append({'id':pid,'source':oldid,'face':k,'side':side,'old_face_t_in':oldt,'eave_hip_face_t_in':math.copysign(hipt,oldt),'new_face_t_in':newt,'side_translation_m':dt.tolist(),'head_translation_m':headshift.tolist(),'inner_q_delta_in':dq/I,'minimum_blank_length_in':minimum,'reference_axis_length_in':reference/I,'head_projection_in':projection,'outer_foot_max_projection_in':0 if foot.is_empty() else (max(v[1] for v in P[bpid]['vertices'])-min(v[1] for v in foot.to_mesh64().vert_properties))/I,'source_head_tool_in3':tool.volume()/I**3})
 for pid in sorted(changed):
  print('receiver boundary',pid,flush=True)
  try:g=native_record(S[pid],single=True)
  except AssertionError:
   clean=regular_boundary(S[pid]);atmost(diff(S[pid],clean),pid+'receiver boundary cleanup');g=native_record(clean,single=True)
  P[pid].update(g);P[pid]['faces']=g['triangles'];P[pid]['fit_geometry']={**P[pid].get('fit_geometry',{}),**volume_centroid(S[pid])};S[pid]=native_solid(P[pid])
 # Primary wood + actual fasteners only. Explicit covering prerequisites are
 # absent in this scoped initial withdrawal; this is not a full scene replay.
 scene=Scene('external-roof-support',P,S,{pid:np.zeros(3) for pid in S});scene.parts={pid:P[pid] for pid in S}
 initial=audit_initial_scene(scene);print('STATIC',initial,flush=True)
 probes=[]
 for pid in added:
  moves=[UP*.3] if top else [-np.asarray(next(j for j in newjoints if j['donor']==pid and j['end']=='B')['insertion_direction'])*3.01*I]
  proof=check_stage(scene,[pid],moves[0],stop_first=True);probes.append({'id':pid,'scope':'Current primary wood/physical fasteners; roof envelope coverings are explicit removal prerequisite. All other primary actors fixed.','proof':proof});print('PROBE',pid,proof['status'],proof.get('collisions'),flush=True)
 preservation=[]
 for pid in original:
  if pid not in changed:atmost(diff(original[pid],S[pid]),pid+' unexpected change')
 for pid in sorted(changed):
  removed=original[pid]-S[pid];newcuts=union(cuts.get(pid,[]));preservation.append({'id':pid,'added_material_in3':amount(S[pid]-original[pid])/I**3,'removed_outside_declared_new_joint_tools_in3':amount(removed-newcuts)/I**3,'removed_in3':amount(removed)/I**3})
 report={'scope':'External actual-source16 additional4x8 roof-support rafters, static primary geometry and initial withdrawal only; no strength/span/connection capacity or complete erection certification.','source_model':str(source),'frozen_source_model':str(out/'frozen-source-model.json'),'source_model_sha256':sourcesha,'generator':str(Path(__file__).resolve()),'generator_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'is_top_entry':top,'new_ids':added,'changed_receivers':sorted(changed),'new_rafter_count':len(added),'spacing_eave_in':[abs(rows[0]['eave_hip_face_t_in'])-abs(rows[0]['new_face_t_in']),abs(rows[0]['new_face_t_in'])-abs(rows[0]['old_face_t_in']),2*abs(rows[0]['old_face_t_in']),abs(rows[0]['new_face_t_in'])-abs(rows[0]['old_face_t_in']),abs(rows[0]['eave_hip_face_t_in'])-abs(rows[0]['new_face_t_in'])],'stock_and_offsets':rows,'static_primary_audit':initial,'continuous_initial_withdrawals':probes,'receiver_material_removal':preservation,'elapsed_seconds':time.time()-started,'status':'LOCAL_PASS' if initial['status']=='PASS' and all(x['proof']['status']=='PASS' for x in probes) else 'LOCAL_BLOCKED'}
 candidate=copy.deepcopy(model);candidate['parts']=[P[p['id']] for p in model['parts']]+[P[x] for x in added];candidate['tenon_schedule']=copy.deepcopy(model['tenon_schedule'])+newjoints;candidate['research_only']=True;candidate['status']='EXTERNAL UNVERIFIED ROOF SUPPORT CANDIDATE';candidate['roof_support_research_source']=report['source_model_sha256']
 report['geometry_preserving_boundary_cleanup']=CLEANUPS
 if proposalbytes:report['source_top_entry_proposal_sha256']=hashlib.sha256(proposalbytes).hexdigest()
 if top:
  for pid,cs in cuts.items():
   if pid.startswith('R'):
    existing=candidate.setdefault('joinery_entry_regions',{}).get(pid);entry=native_solid(existing) if existing and existing.get('triangles') else m.Manifold();candidate['joinery_entry_regions'][pid]=native_record(entry+union(cs))
 save(out/'roof-support-model.json',candidate);save(out/'roof-support-patch.json',{'scope':report['scope'],'replace_parts':{x:P[x] for x in changed},'add_parts':{x:P[x] for x in added},'append_tenon_schedule':newjoints,'source_model_sha256':report['source_model_sha256']});save(out/'roof-support-stock.json',stocks);save(out/'roof-support-report.json',report);return report

# TIMESTAMP END 2026-11-05T08:15:49+00:00 | REVISION R000034
