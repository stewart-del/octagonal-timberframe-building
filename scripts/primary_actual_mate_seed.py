# TIMESTAMP START 2026-11-05T17:01:40+00:00 | REVISION R000056
"""Explicit-source actual-mate primary cavity seed."""
import sys,json,copy,os
from pathlib import Path
import numpy as np,manifold3d as m
S=Path(__file__).resolve().parent
import current_roof_cavity_partitions as roof
import export_top_entry_cavities as a
from audit_revised_joinery import native_solid
from step_lap import close_bounds
I=.0254;TOL=1e-6

def build(model,proposal,pid,receipts):
 P={p['id']:p for p in model['parts']};p=P[pid];blankworld=a.stock(p);origin=np.asarray(blankworld.bounding_box()).reshape(2,3).mean(0)
 def local(r):return native_solid({'vertices':((np.asarray(r['vertices'])-origin)/I).tolist(),'triangles':r['triangles']}) if r.get('triangles') else m.Manifold()
 conv=lambda s:s.translate((-origin).tolist()).scale([1/I]*3)
 blank=conv(blankworld);own=local(p);pieces=([p['declared_exterior_cut']] if p.get('declared_exterior_cut') else[])+p.get('additional_declared_exterior_cuts',{}).get('pieces',[]);declared=roof.union(local(r) for r in pieces);matedict={q['id']:local(q) for q in model['parts'] if q['id']!=pid and(q.get('is_timber') or q.get('is_fastener')) and close_bounds(blankworld,native_solid(q))};mates=roof.union(matedict.values());entryids=[pid]
 if pid.startswith('R'):entryids+=['P'+pid[1:],'C'+pid[1:]]
 entries=[local(model['joinery_entry_regions'][key]) for key in entryids if key in model.get('joinery_entry_regions',{})]
 if pid.startswith('R'):
  k=int(pid[1])
  for j in proposal['representative']['interfaces']:entries.append(conv(native_solid(j['top_open_cutter']).rotate([0,45*k,0])-native_solid(j['proposed_nose']).rotate([0,45*k,0])))
 E=roof.union(entries);filled=(mates^blank)-declared;access=((E^blank)-own)-(declared+mates);overlay=blank-(own+declared);checks={'unclassified_removed_in3':roof.vol(blank-own-filled-access-declared),'partition_difference_in3':roof.diff(overlay,filled+access),'source_entry_containment_in3':roof.vol(access-E),'pocket_without_actual_mate_in3':roof.vol(filled-mates),'receiver_overlap_in3':roof.vol((filled+access+declared)^own)};print('ACTUAL SEED',pid,checks,flush=True);assert max(checks.values())<=TOL,(pid,checks)
 rec={key:roof.pack_local(s,origin,pid,key,receipts) for key,s in [('removed',overlay),('mating_pocket',filled),('entry_clearance',access),('blank_offcuts',declared)]};rec.update(stock_basis='Actual receiver stock and complete current physical mates united before one clip. Entry restricted to explicit corresponding source regions; declared exterior offcuts separate.',roundoff_omission_limit_m3=1e-9*I**3,mating_clip_roundoff_omitted_m3=0.);return rec,{'id':pid,'construction_checks_in3':checks,'actual_mate_ids':list(matedict),'explicit_source_entry_ids':entryids}

# TIMESTAMP END 2026-11-05T17:01:40+00:00 | REVISION R000056
