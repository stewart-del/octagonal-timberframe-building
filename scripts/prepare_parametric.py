# TIMESTAMP START 2026-11-05T17:19:58+00:00 | REVISION R000058
"""Deterministic current-source receiver preparation with bounded local proofs.

No saved cavity/source payload is read. Source hashes bind every current tool.
Boolean construction preserves the P/B reference design and all nonroof cuts.
Ownership checks use only AABB-relevant tools, a common local Mesh64 frame and
charged exact-subtraction/round-trip triangle-tube bounds. No threshold changes.
"""
from pathlib import Path
import argparse,hashlib,json,math,sys
import numpy as np
import manifold3d as m
I=.0254;TOL=1e-6*I**3;EPS=np.finfo(float).eps
FILES={'baseline':'model-data.json','proposed':'step-lap-proposed-model.json','top-entry':'top-entry-proposed-model.json'}
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def save(path,value):Path(path).write_text(json.dumps(value,separators=(',',':'))+'\n')
def up(value,operations=32):
 value=float(value);gamma=operations*EPS/(1-operations*EPS)
 return float(np.nextafter(value*(1+gamma),math.inf)) if value else 0.
def two_diff(a,b):
 x=a-b;bvirt=a-x;avirt=x+bvirt;bround=bvirt-b;around=a-avirt
 return x,around+bround
def stats(v,t):
 p=v[t];e1,r1=two_diff(p[:,1],p[:,0]);e2,r2=two_diff(p[:,2],p[:,0]);e3,r3=two_diff(p[:,2],p[:,1]);gamma=8*EPS/(1-8*EPS)
 lengths=[(np.sum(np.abs(e),axis=1)+np.sum(np.abs(r),axis=1))*(1+gamma) for e,r in [(e1,r1),(e2,r2),(e3,r3)]]
 return up(math.fsum((.5*lengths[0]*lengths[1]).tolist()),64+len(t)),up(math.fsum((lengths[0]+lengths[1]+lengths[2]).tolist()),64+len(t)),len(t)
def tube(r,area,perimeter,n):
 if r==0:return 0.
 pi=float(np.nextafter(math.pi,math.inf))
 return up(2*r*area+pi*r*r*perimeter+(8*pi/3)*r*r*r*n,128)
def face_keys(v,t):
 out=[]
 for tri in t:
  points=tuple(tuple(float(x) for x in v[i]) for i in tri);out.append(min(points,points[1:]+points[:1],points[2:]+points[:2]))
 return sorted(out)
def local_shape(world,origin):
 # Native rigid translation and resetting inherited numeric precision to the
 # local machine minimum preserve intermediate indexed triangles, including
 # any zero-area kernel caps. Reimporting such stock boundaries may silently
 # retriangulate them; these are input tools, not physical mesh certificates.
 raw=world.to_mesh64();v=np.asarray(raw.vert_properties)[:,:3];t=np.asarray(raw.tri_verts,np.uint64);expected,residual=two_diff(v,origin);value=world.translate((-origin).tolist()).set_tolerance(0);actual=value.to_mesh64();av=np.asarray(actual.vert_properties)[:,:3];at=np.asarray(actual.tri_verts,np.uint64)
 assert av.shape==v.shape and np.array_equal(t,at),'Native local translation changed indexed triangles'
 delta,dr=two_diff(av,expected);forward=up(float(np.max(np.sum(np.abs(residual)+np.abs(delta)+np.abs(dr),axis=1),initial=0)),32);roundtrip=(av+origin)-v;r=up(max(forward,float(np.max(np.sum(np.abs(roundtrip),axis=1),initial=0))),16);area,perimeter,n=stats(v,t);cover=tube(r,area,perimeter,n)
 return value,{'exact_forward_residual_max_l1_m':forward,'roundtrip_max_l1_m':float(np.max(np.sum(np.abs(roundtrip),axis=1),initial=0)),'displacement_bound_m':r,'triangle_count':n,'transform_cover_bound_m3':cover,'indexed_triangles_preserved':True}

def amount(shape):return max(0.,float(shape.volume()))
def union(shapes):return m.Manifold.batch_boolean(list(shapes),m.OpType.Add) if shapes else m.Manifold()
def diff(a,b):return amount(a-b)+amount(b-a)
def relevant(a,b):
 a=np.asarray(a.bounding_box());b=np.asarray(b.bounding_box());return bool(np.all(a[3:]>=b[:3]) and np.all(b[3:]>=a[:3]))
def prove_ownership(envelope,before,after,roof_records,protected_records):
 bb=envelope.bounding_box();origin=np.array([0.,float(round((bb[1]+bb[4])/2)),0.]);en,eb=local_shape(envelope,origin);old,ob=local_shape(before,origin);new,nb=local_shape(after,origin)
 roofs=[(key,value) for key,value in roof_records if relevant(value,envelope)];protected=[(key,value) for key,value in protected_records if relevant(value,envelope)];roof_local=[];protected_local=[];facts={}
 for key,value in roofs:
  local,bound=local_shape(value,origin);roof_local.append(local);facts[key]=bound
 for key,value in protected:
  local,bound=local_shape(value,origin);protected_local.append(local);facts[key]=bound
 roof_union=union(roof_local);protected_union=union(protected_local);added=new-old;lost=old-new
 common=up(ob['transform_cover_bound_m3']+nb['transform_cover_bound_m3']);roof_bound=up(common+math.fsum(facts[key]['transform_cover_bound_m3'] for key,_ in roofs));protected_bound=up(common+math.fsum(facts[key]['transform_cover_bound_m3'] for key,_ in protected));stock_bound=up(nb['transform_cover_bound_m3']+eb['transform_cover_bound_m3'])
 measures={'unexplained_restoration':(amount(added-roof_union),roof_bound),'lost_source_wood':(amount(lost),common),'protected_refill':(amount(added^protected_union),protected_bound),'outside_independent_stock':(amount(new-en),stock_bound)}
 proofs={key:{'local_volume_m3':volume,'transform_cover_bound_m3':bound,'upper_bound_m3':up(volume+bound),'status':'PASS' if up(volume+bound)<=TOL else 'FAIL'} for key,(volume,bound) in measures.items()}
 aggregate=up(math.fsum(bound for _,bound in measures.values()));assert aggregate<TOL,('Aggregate receiver transform cover exceeds original tolerance',aggregate,TOL)
 for key,p in proofs.items():assert p['status']=='PASS',(key,p,p['upper_bound_m3']/I**3)
 restore=(en^roof_union)-protected_union
 return {'status':'PASS','common_local_origin_m':origin.tolist(),'aabb_selection':'Inclusive exact native bounds; omitted tools have no positive-volume envelope intersection. No distance tolerance used.','ordered_relevant_roof_tool_ids':[key for key,_ in roofs],'ordered_relevant_protected_tool_ids':[key for key,_ in protected],'selected_roof_tool_count':len(roofs),'selected_protected_tool_count':len(protected),'source_roof_tool_count':len(roof_records),'source_protected_tool_count':len(protected_records),'proofs':proofs,'aggregate_transform_cover_bound_m3':aggregate,'added_roof_owned_volume_m3':amount(added),'before_after_difference_upper_m3':up(amount(added)+amount(lost)+common),'coincident_fragment_readback_m3_diagnostic_only':diff(new-restore,old-restore),'input_transform_facts':{'envelope':eb,'before':ob,'after':nb,**facts}}
def build(source_dir=None,output_path=None,report_path=None,repo_root=None):
 import re
 root=Path(repo_root) if repo_root else Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'scripts'))
 from audit_revised_joinery import native_solid as solid
 from export_top_entry_cavities import stock,declared_offcuts
 from step_lap import mesh
 source_dir=Path(source_dir) if source_dir else root/'src';output_path=Path(output_path) if output_path else root/'src/parametric-source.json'
 report_path=Path(report_path) if report_path else None
 input_bytes={name:(source_dir/name).read_bytes() for name in FILES.values()};input_hashes={name:hashlib.sha256(raw).hexdigest() for name,raw in input_bytes.items()};baseline=json.loads(input_bytes[FILES['baseline']]);baseline_parts={p['id']:p for p in baseline['parts']};baseline_sha=input_hashes[FILES['baseline']]
 helper_paths=[Path(__file__),root/'scripts/audit_revised_joinery.py',root/'scripts/export_top_entry_cavities.py',root/'scripts/audit_cavity_fit.py',root/'scripts/step_lap.py'];helper_hashes={str(path):sha(path) for path in helper_paths};result={'scope':'Fresh external source-tool restoration research, no reused certificates','variants':{}};reports=[]
 for variant,name in FILES.items():
  model=json.loads(input_bytes[name]);P={p['id']:p for p in model['parts']};S={pid:solid(p) for pid,p in P.items() if p.get('triangles')};roofs=sorted(pid for pid in P if re.fullmatch(r'R[0-7]|J[0-7]-(?:OUT)?[02]',pid));roof_set=set(roofs);blanks={pid:stock(p)-declared_offcuts(p) for pid,p in P.items() if p.get('is_timber')};receivers={};voids={}
  for pid in ['P0','B0','C0']:
   envelope=blanks[pid];before=S[pid]
   roof_records=[('roof-part:'+rid,S[rid]) for rid in roofs]
   roof_records.extend(('roof-joint:'+j['id'],solid(j.get('cutting_tool',j['connector']))) for j in sorted(model['tenon_schedule'],key=lambda j:j['id']) if j['receiver']==pid and j['donor'] in roof_set)
   # Part and nonroof-joint records retain their source JSON order. Their
   # complete source bytes are guarded; no set drives any Boolean operation.
   protected=[('protected-part:'+qid,S[qid]) for qid in S if qid!=pid and qid not in roof_set and (P[qid].get('is_timber') or P[qid].get('is_fastener') or qid=='M-TMP')]
   protected.extend(('protected-joint:'+j['id'],solid(j.get('cutting_tool',j['connector']))) for j in model['tenon_schedule'] if j['receiver']==pid and j['donor'] not in roof_set)
   entry=model.get('joinery_entry_regions',{}).get(pid)
   if entry and entry.get('triangles'):
    access=solid(entry)
    if pid.startswith('C') and model.get('independent_hip_entry_revision'):
     joint=next(j for j in model['tenon_schedule'] if j['donor']=='R'+pid[1:] and j['receiver']==pid);depth=np.asarray(P[joint['donor']]['stock_frame']['depth']);top=float(np.max(np.asarray(joint['connector']['vertices'])@depth));access=access.trim_by_plane(depth.tolist(),top)
    protected.append(('protected-entry:'+pid,access))
   after=envelope-union([shape for _,shape in protected])
   if pid[0] in ['P','B']:after=solid(baseline_parts[pid])
   ownership=prove_ownership(envelope,before,after,roof_records,protected)
   if ownership['before_after_difference_upper_m3']<=TOL:after=before
   print(variant,pid,'restored',ownership['added_roof_owned_volume_m3']/I**3,'PASS bounded local ownership',flush=True)
   for k in range(8):
    rid=pid[0]+str(k);residual=diff(S[rid],before.rotate([0,45*k,0]));assert residual<=TOL,(rid+' current source family isometry',residual/I**3);receivers[rid]=mesh(after.rotate([0,45*k,0]));voids[rid]=mesh((envelope-after).rotate([0,45*k,0]))
   reports.append({'variant':variant,'id':pid,'added_current_roof_owned_in3':ownership['added_roof_owned_volume_m3']/I**3,'lost_source_wood_in3':ownership['proofs']['lost_source_wood']['upper_bound_m3']/I**3,'protected_refill_in3':ownership['proofs']['protected_refill']['upper_bound_m3']/I**3,'ownership':ownership})
  result['variants'][variant]={'source_model_sha256':input_hashes[name],'current_baseline_receiver_sha256':baseline_sha,'roof_receivers':receivers,'roof_receiver_voids':voids,'cavity_blanks':{pid:mesh(value) for pid,value in blanks.items()},'intermediate_boundary_status':'RAW_KERNEL_INPUT; final generated meshes independently inspected'}
  print(variant,'prepared',len(blanks),'current timber envelopes',flush=True)
 for name,digest in input_hashes.items():assert sha(source_dir/name)==digest,'Source changed during preparation: '+name
 for path,digest in helper_hashes.items():assert sha(path)==digest,'Helper changed during preparation: '+path
 report={'status':'PASS','scope':result['scope'],'source_dir':str(source_dir),'models':input_hashes,'generator_sha256':sha(Path(__file__)),'helper_sha256':helper_hashes,'current_roof_ids_count':40,'ordering_policy':'Roof IDs and roof joints sorted explicitly; nonroof tools retain guarded source JSON order. No set iteration in geometry or proofs.','ownership_policy':'Actual output, input and relevant exact tools transformed into common local Mesh64 before Boolean ownership checks; every imported oriented triangle retained. Exact subtraction/round-trip triangle-tube covers charged to original per-check and aggregate tolerance.','receiver_restorations':reports,'overlap_tolerance_m3':TOL,'capacity_verified':False}
 save(output_path,result);report['payload_sha256']=sha(output_path)
 if report_path:save(report_path,report)
 return result,report
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--repo',type=Path);parser.add_argument('--source-dir',type=Path);parser.add_argument('--output',type=Path);parser.add_argument('--report',type=Path);args=parser.parse_args();build(args.source_dir,args.output,args.report,args.repo)

# TIMESTAMP END 2026-11-05T17:19:58+00:00 | REVISION R000058
