#!/usr/bin/env python3
"""Fresh numerical intersection audit of saved assembled convex cells."""
import argparse, json, math, hashlib
from zipfile import ZipFile
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
import generate_voids as g

def test_pair(task):
    aid,ac,ab,bid,bc,bb=task;total=0;cell_tests=0;positive_cells=0
    for c,cb in zip(ac,ab):
        for d,db in zip(bc,bb):
            if not g.boundsmeet(cb,db):continue
            cell_tests+=1;x=g.intersect(c,d)
            v=g.volume(x) if x else 0
            total+=v
            if v>g.VEPS:positive_cells+=1
    return {'a':aid,'b':bid,'intersection_volume_m3':total,'candidate_cell_pairs':cell_tests,'positive_cell_intersections':positive_cells}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--archive',required=True);ap.add_argument('--output',required=True);ap.add_argument('--jobs',type=int,default=4);args=ap.parse_args()
    with ZipFile(args.archive) as z:raw=z.read('octagon-fit/fitted-cells.json');data=json.loads(raw)
    ps=data['parts'];bs=[[g.bbox(c) for c in p['cells']] for p in ps];overall=[g.bbox(data['original_cells'][p['id']]) for p in ps]
    tasks=[]
    for i,p in enumerate(ps):
        for j in range(i):
            if g.boundsmeet(overall[i],overall[j]):tasks.append((p['id'],p['cells'],bs[i],ps[j]['id'],ps[j]['cells'],bs[j]))
    with ProcessPoolExecutor(max_workers=args.jobs) as pool:rows=list(pool.map(test_pair,tasks))
    threshold=1e-10;bad=[r for r in rows if r['intersection_volume_m3']>threshold]
    r={'source_cells_sha256':hashlib.sha256(raw).hexdigest(),'scope':'Saved assembled fitted timbers only; no source-prism or exploded-pose collision claims.',
       'method':'Fresh convex-cell pair intersections, using prototype numerical half-space kernel. AABB tests only prune candidates.',
       'distance_epsilon_m':g.EPS,'cell_volume_epsilon_m3':g.VEPS,'report_overlap_threshold_m3':threshold,
       'piece_count':len(ps),'total_member_pairs':len(ps)*(len(ps)-1)//2,'candidate_member_pairs':len(rows),
       'candidate_cell_pairs':sum(x['candidate_cell_pairs'] for x in rows),'max_member_intersection_volume_m3':max((x['intersection_volume_m3'] for x in rows),default=0),
       'above_threshold_pair_count':len(bad),'above_threshold_pairs':bad,'results':rows,
       'status':'PASS at stated numerical thresholds' if not bad else 'FAIL: positive double-occupied volume found',
       'limitations':['A lack of material intersections does not authenticate the fitted joint design.','The generated partition deliberately assigns overlapping source-stock regions to different timber owners.','This does not approve bearing, retained wood, tenon size, shrinkage allowance, tool access, or insertion paths.']}
    Path(args.output).write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items() if k!='results'}))

if __name__=='__main__':main()
