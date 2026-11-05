# TIMESTAMP START 2026-11-05T17:01:40+00:00 | REVISION R000056
"""Current R/OUT cavity partitions using actual physical mates.

Complete current physical mates are unioned before one stock clip. Entry is
bounded by explicit source R/P/C regions and historical top-entry tools, never
an inferred blank-complement mask. Every saved part faces the original audit.
"""
import sys,json,copy,hashlib,math,time,argparse,traceback,re,os
from pathlib import Path
import numpy as np,manifold3d as m
S=Path(__file__).resolve().parent
import export_top_entry_cavities as a
from audit_revised_joinery import native_solid
from audit_cavity_fit import inspect_mesh,arrays
from floor_surface_normalization import regular_local
from step_lap import close_bounds
I=.0254;TOL=1e-6;OUT=Path.cwd()/'.primary-cavity-diagnostics';KEYS=['removed','mating_pocket','entry_clearance','blank_offcuts']
def read(p):return json.load(open(p))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):Path(p).write_text(json.dumps(x,separators=(',',':'))+'\n')
def vol(s):return max(0.,float(s.volume()))
def diff(x,y):return abs(float((x-y).volume()))+abs(float((y-x).volume()))
def union(ss):return m.Manifold.batch_boolean(list(ss),m.OpType.Add) if ss else m.Manifold()
def raw(s):
 q=s.to_mesh64();return {'vertices':np.asarray(q.vert_properties)[:,:3].tolist(),'triangles':np.asarray(q.tri_verts).tolist()}

def pack_local(s,origin,pid,key,receipts):
 if s.is_empty() or abs(s.volume())<=1e-9:return copy.deepcopy(a.EMPTY)
 def worldrecord(x):
  q=raw(x);q['vertices']=(np.array(q['vertices'])*I+origin).tolist();q['volume_m3']=float(x.volume())*I**3;return q
 def checked(candidate,method):
  rec=worldrecord(candidate);proof=inspect_mesh(*arrays(rec));
  if proof['status']!='PASS':return None
  # Fresh actual serialized world boundary -> stock-local readback.
  serialized=json.loads(json.dumps(rec));back=native_solid({'vertices':((np.array(serialized['vertices'])-origin)/I).tolist(),'triangles':serialized['triangles']});err=diff(s,back)
  if err>TOL:return None
  receipts.append({'id':pid,'record':key,'method':method,'source_to_saved_readback_difference_in3':err,'raw':proof});return rec
 print('PACK',pid,key,'vol',s.volume(),flush=True);save(OUT/'current-operation.json',{'pid':pid,'record':key,'stage':'packing','stock_local_input':raw(s),'origin_m':origin.tolist()})
 r=checked(s,'native local-inch boundary')
 if r:return r
 source_raw=worldrecord(s);save(OUT/(pid+'-'+key+'-failed-native.json'),source_raw)
 for eps in [1e-10,1e-9,1e-8]:
  candidate=s.simplify(eps)
  if diff(s,candidate)<=TOL:
   r=checked(candidate,'native simplify '+str(eps)+'in')
   if r:return r
 for plane in [1e-10/I,1e-9/I]:
  print('REGULAR',pid,key,plane,flush=True)
  try:candidate=regular_local(s,plane)
  except AssertionError:continue
  if diff(s,candidate)>TOL:continue
  r=checked(candidate,'signed support-plane contour rebuild at physical '+str(plane*I)+'m')
  if r:return r
 raise AssertionError((pid,key,'No unchanged-tolerance stable raw readback'))

def build_record(model,proposal,pid,receipts):
 P={p['id']:p for p in model['parts']};part=P[pid];blankworld=a.stock(part);origin=np.asarray(blankworld.bounding_box()).reshape(2,3).mean(0)
 def localraw(rec):return native_solid({'vertices':((np.array(rec['vertices'])-origin)/I).tolist(),'triangles':rec['triangles']}) if rec.get('triangles') else m.Manifold()
 local=lambda s:s.translate((-origin).tolist()).scale([1/I]*3)
 blank=local(blankworld);own=localraw(part);declared=local(a.declared_offcuts(part));physical={p['id']:localraw(p) for p in model['parts'] if p['id']!=pid and(p.get('is_timber') or p.get('is_fastener')) and close_bounds(blankworld,native_solid(p))}
 print('BUILD',pid,'mates',list(physical),flush=True);mates=union(physical.values());print('UNIONMATES',pid,flush=True)
 entrypieces=[];entrysource=[]
 if pid.startswith('R'):
  k=int(pid[1]);indices=[pid,'P'+str(k),'C'+str(k)]
  for qid in indices:
   if qid in model.get('joinery_entry_regions',{}):entrypieces.append(localraw(model['joinery_entry_regions'][qid]));entrysource.append('model.joinery_entry_regions.'+qid)
  for j in proposal['representative']['interfaces']:
   # The recorded historical R0 proposal is rotated to this hip before the
   # rigid local translation. No missing-volume-derived access is introduced.
   tool=native_solid(j['top_open_cutter']).rotate([0,45*k,0]);nose=native_solid(j['proposed_nose']).rotate([0,45*k,0]);entrypieces.append(local(tool-nose));entrysource.append('historical '+str(j.get('owner','representative')))
 entries=union(entrypieces);removed=blank-own;overlay=blank-(own+declared);filled=(mates^blank)-declared;access=((entries^blank)-own)-(declared+mates)
 unknown=removed-filled-access-declared;checks={'unclassified_removed_in3':vol(unknown),'filled_own_overlap_in3':vol(filled^own),'entry_outside_source_tools_in3':vol(access-entries),'entry_mate_overlap_in3':vol(access^mates),'pocket_without_actual_mate_in3':vol(filled-mates),'overlay_partition_difference_in3':diff(overlay,filled+access),'stock_reconstruction_difference_in3':diff(blank,own+filled+access+declared)};print('CLASS',pid,checks,flush=True);assert all(v<=TOL for v in checks.values()),checks
 shapes={'removed':overlay,'mating_pocket':filled,'entry_clearance':access,'blank_offcuts':declared};record={k:pack_local(s,origin,pid,k,receipts) for k,s in shapes.items()};record.update(stock_basis='Actual recorded stock halfspaces; complete actual physical mating solids unioned before one stock clip. Entry bounded ONLY by explicit matching R/P/C source regions plus historical top-open proposal. Source declared shoulder/backing/eave offcuts separate.',roundoff_omission_limit_m3=1e-9*I**3,mating_clip_roundoff_omitted_m3=0.);return record,{'id':pid,'actual_mate_ids':list(physical),'entry_sources':entrysource,'local_checks_in3':checks}

# TIMESTAMP END 2026-11-05T17:01:40+00:00 | REVISION R000056
