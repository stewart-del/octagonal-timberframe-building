#!/usr/bin/env python3
"""Derive removed-stock overlays from archived convex timber cells.

No timber is edited. Occupied mating recesses are distinguished from unfilled
original stock. No claim is made about air outside the original stock union.
Clipping uses the saved prototype's numerical half-space convention, not AABBs
as volume proxies. The kernel is copied below from the project's archived
build_fitted_geometry.py; it is not represented as an independent CAD engine.
"""
from pathlib import Path
from zipfile import ZipFile
import argparse, collections, hashlib, json, math, time
from concurrent.futures import ProcessPoolExecutor

EPS = 1e-9
VEPS = 1e-12

def add(a,b): return tuple(x+y for x,y in zip(a,b))
def sub(a,b): return tuple(x-y for x,y in zip(a,b))
def mul(v,k): return tuple(x*k for x in v)
def dot(a,b): return sum(x*y for x,y in zip(a,b))
def cross(a,b): return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def norm(v): return math.sqrt(dot(v,v))
def unit(v): return mul(v,1/norm(v))
def mean(v): return mul(tuple(sum(p[k] for p in v) for k in range(3)),1/len(v))
def clean(v):
    out=[]
    for p in v:
        if not out or norm(sub(p,out[-1]))>EPS: out.append(tuple(p))
    if len(out)>1 and norm(sub(out[0],out[-1]))<EPS: out.pop()
    return out
def plane(ps):
    best=None; size=0
    for i in range(1,len(ps)-1):
        for j in range(i+1,len(ps)):
            n=cross(sub(ps[i],ps[0]),sub(ps[j],ps[0])); nn=norm(n)
            if nn>size: best=n; size=nn
    if size>1e-13:
        n=mul(best,1/size); return n,dot(n,ps[0])
def face(ps,tag=None): return {'points':clean(ps),'tag':tag}
def volume(cell):
    return abs(sum(dot(f['points'][0],cross(f['points'][i],f['points'][i+1]))/6 for f in cell for i in range(1,len(f['points'])-1)))
def points(cell): return [p for f in cell for p in f['points']]
def bbox(cell):
    vs=points(cell)
    return tuple(min(p[k] for p in vs) for k in range(3)),tuple(max(p[k] for p in vs) for k in range(3))
def boundsmeet(a,b,tol=EPS): return all(a[0][k]<=b[1][k]+tol and b[0][k]<=a[1][k]+tol for k in range(3))
def polyclip(poly,n,d):
    out=[]; cuts=[]
    for a,b in zip(poly,poly[1:]+poly[:1]):
        da=dot(n,a)-d; db=dot(n,b)-d; ia=da<=EPS; ib=db<=EPS
        if ia: out.append(a)
        if ia!=ib:
            p=add(a,mul(sub(b,a),da/(da-db))); out.append(p); cuts.append(p)
    return clean(out),cuts
def clip(cell,n,d,tag=None):
    vals=[dot(n,p)-d for p in points(cell)]
    if max(vals)<=EPS:return cell
    if min(vals)>=-EPS:return []
    fs=[]; cap=[]
    for f in cell:
        vs,cs=polyclip(f['points'],n,d); cap+=cs
        if len(vs)>=3 and plane(vs):fs.append(face(vs,f.get('tag')))
    cap=list({tuple(round(x,10) for x in p):p for p in cap}.values())
    if len(cap)>=3:
        center=mean(cap);e=unit(cross(n,(1,0,0) if abs(n[0])<.8 else (0,1,0)));f=cross(n,e)
        cap.sort(key=lambda p:math.atan2(dot(sub(p,center),f),dot(sub(p,center),e)))
        fs.append(face(cap,tag))
    return fs if len(fs)>=4 and volume(fs)>VEPS else []
def intersect(a,b):
    if not boundsmeet(bbox(a),bbox(b)):return []
    out=a
    for f in b:
        pd=plane(f['points'])
        if pd:out=clip(out,*pd)
        if not out:break
    return out
def difference(a,b):
    if not boundsmeet(bbox(a),bbox(b)):return [a]
    q=intersect(a,b)
    if not q or volume(q)<VEPS:return [a]
    out=[];pending=a
    for f in b:
        pd=plane(f['points'])
        if not pd:continue
        n,d=pd; outer=clip(pending,mul(n,-1),-d)
        if outer:out.append(outer)
        pending=clip(pending,n,d)
        if not pending:break
    return out
def subtract_cells(cells,cutter):return [p for c in cells for p in difference(c,cutter)]
def polygon_outside_cell(poly,cell):
    pending=poly;out=[]
    for f in cell:
        pd=plane(f['points'])
        if not pd:continue
        n,d=pd;outer,_=polyclip(pending,mul(n,-1),-d)
        if len(outer)>=3 and plane(outer) and any(dot(n,p)-d>EPS for p in pending):out.append(outer)
        pending,_=polyclip(pending,n,d)
        if len(pending)<3:break
    return out
def exterior_faces(cells):
    answer=[];bbs=[bbox(c) for c in cells];planes=[[plane(f['points']) for f in c] for c in cells]
    for i,cell in enumerate(cells):
        for f in cell:
            pd=plane(f['points'])
            if not pd:continue
            n,d=pd;polys=[f['points']]
            for j,other in enumerate(cells):
                if i==j or not boundsmeet(bbs[i],bbs[j],1e-7):continue
                if not any(pd and dot(n,pd[0])<-1+1e-7 and abs(d+pd[1])<1e-7 for pd in planes[j]):continue
                polys=[piece for poly in polys for piece in polygon_outside_cell(poly,other)]
                if not polys:break
            answer.extend(poly for poly in polys if len(poly)>=3 and plane(poly))
    return answer

def boundary_feature_edges(polygons,vi):
    """Split collinear polygon edges at all endpoints; omit coplanar seams.

    Union surface polygons can have partial edge matches (T junctions). Matching
    only complete endpoint pairs would expose the hidden convex partition.
    This interval sweep keeps only changes of surface normal above 0.1 degree.
    """
    buckets={};tolerance=1e-7
    for poly in polygons:
        n,_=plane(poly)
        for a,b in zip(poly,poly[1:]+poly[:1]):
            d=sub(b,a)
            if norm(d)<tolerance:continue
            d=unit(d)
            if next((x for x in d if abs(x)>1e-7),1)<0:d=mul(d,-1)
            moment=cross(d,a)
            key=tuple(round(x/1e-5) for x in d)+tuple(round(x/1e-6) for x in moment)
            bucket=buckets.setdefault(key,{'u':d,'origin':a,'segments':[]})
            lo,hi=sorted([dot(sub(a,bucket['origin']),bucket['u']),dot(sub(b,bucket['origin']),bucket['u'])])
            bucket['segments'].append((lo,hi,n))
    edges=[];single_normal_intervals=0;cos=math.cos(math.radians(.1))
    for bucket in buckets.values():
        breaks=sorted({round(x/tolerance)*tolerance for lo,hi,n in bucket['segments'] for x in [lo,hi]})
        runs=[]
        for lo,hi in zip(breaks,breaks[1:]):
            if hi-lo<tolerance*.5:continue
            mid=(lo+hi)/2
            normals=[n for start,end,n in bucket['segments'] if start<=mid+tolerance*.25 and end>=mid-tolerance*.25]
            feature=any(abs(dot(a,b))<cos for i,a in enumerate(normals) for b in normals[i+1:])
            if len(normals)==1:single_normal_intervals+=1
            if feature:
                if runs and abs(runs[-1][1]-lo)<tolerance*.5:runs[-1][1]=hi
                else:runs.append([lo,hi])
        for lo,hi in runs:
            a=add(bucket['origin'],mul(bucket['u'],lo));b=add(bucket['origin'],mul(bucket['u'],hi))
            ia,ib=vi(a),vi(b)
            if ia!=ib:edges.append([ia,ib])
    return edges,{'method':'collinear interval sweep; only noncoplanar exterior-face boundaries',
                  'minimum_dihedral_deg':.1,'interval_tolerance_m':tolerance,
                  'single_normal_intervals_omitted':single_normal_intervals,
                  'note':'Display wire only, not a watertightness or machining test.'}

def mesh(cells):
    """Exterior polygon fans; duplicated coplanar internal cell faces removed."""
    if not cells:return {'vertices':[],'triangles':[],'edges':[],'bounds_m':None,'volume_m3':0,'cell_count':0}
    ps=exterior_faces(cells);vs=[];index={};ts=[]
    def vi(p):
        k=tuple(round(v,9) for v in p)
        if k not in index:index[k]=len(vs);vs.append(list(k))
        return index[k]
    for poly in ps:
        n,_=plane(poly);ids=[vi(p) for p in poly];center=vi(mean(poly))
        for a,b in zip(ids,ids[1:]+ids[:1]):
            if len({a,b,center})==3 and norm(cross(sub(vs[a],vs[center]),sub(vs[b],vs[center])))>1e-15:
                ts.append([center,a,b])
    edges,edge_method=boundary_feature_edges(ps,vi)
    total=sum(volume(c) for c in cells)
    return {'vertices':vs,'triangles':ts,'edges':edges,'edge_method':edge_method,'bounds_m':[[min(v[k] for v in vs),max(v[k] for v in vs)] for k in range(3)],'volume_m3':total,'cell_count':len(cells)}

def one_member(task):
    pid,stock,own,others,offcuts=task;t=time.monotonic()
    cavities=[stock]
    for c in own:cavities=subtract_cells(cavities,c)
    cavity_volume=sum(volume(c) for c in cavities)
    expected=volume(stock)-sum(volume(c) for c in own)
    if abs(cavity_volume-expected)>1e-8:raise ValueError(f'{pid}: stock-minus-piece volume mismatch {cavity_volume-expected}')
    remaining=cavities;occupancy=[]
    for other_id,other_cells in others:
        taken=[]
        for cutter in other_cells:
            if not remaining:break
            next_remaining=[]
            for c in remaining:
                shared=intersect(c,cutter)
                if shared and volume(shared)>VEPS:
                    taken.append(shared);next_remaining.extend(difference(c,cutter))
                else:next_remaining.append(c)
            remaining=next_remaining
        if taken:occupancy.append({'part_id':other_id,'volume_m3':sum(volume(c) for c in taken)})
    empty_volume=sum(volume(c) for c in remaining)
    occupied_volume=sum(x['volume_m3'] for x in occupancy)
    if abs(cavity_volume-empty_volume-occupied_volume)>1e-8:raise ValueError(f'{pid}: classification volume mismatch')
    offcut_volume=0;unexplained=remaining
    for c in offcuts:
        offcut_volume+=sum(volume(x) for r in remaining if (x:=intersect(r,c)))
        unexplained=subtract_cells(unexplained,c)
    return {'id':pid,'original_stock_volume_m3':volume(stock),'fitted_piece_volume_m3':sum(volume(c) for c in own),
            'removed':mesh(cavities),'unfilled':mesh(remaining),
            'occupied_mates':occupancy,'occupied_volume_m3':occupied_volume,
            'declared_exterior_offcut_overlap_m3':offcut_volume,
            'unexplained_unfilled_volume_m3':sum(volume(c) for c in unexplained),
            'stock_balance_error_m3':cavity_volume-expected,
            'classification_balance_error_m3':cavity_volume-empty_volume-occupied_volume,
            'elapsed_seconds':round(time.monotonic()-t,3)}

def geometry_hash(model):
    # Canonical identity/geometry payload, excluding mutable UI annotations.
    payload=[{'id':p['id'],'vertices':p['vertices'],'triangles':p['triangles']} for p in model['parts']]
    return hashlib.sha256(json.dumps(payload,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--archive',required=True);ap.add_argument('--model',required=True);ap.add_argument('--output',required=True);ap.add_argument('--jobs',type=int,default=2);ap.add_argument('--part',action='append');args=ap.parse_args()
    archive=Path(args.archive);model_path=Path(args.model);model=json.loads(model_path.read_text())
    with ZipFile(archive) as z:
        raw=z.read('octagon-fit/fitted-cells.json');D=json.loads(raw)
        source_model=json.loads(z.read('octagon-fit/viewer/embedded-model.json'))
    if geometry_hash(model)!=geometry_hash(source_model):raise SystemExit('Model geometry differs from source archive; regenerate cells first.')
    fitted={p['id']:p['cells'] for p in D['parts']};original=D['original_cells']
    ids=[p['id'] for p in model['parts']]
    if set(ids)!=set(original) or set(ids)!=set(fitted):raise SystemExit('ID mismatch between model and convex source')
    all_offcuts=[c for o in D['intentional_offcuts'] for c in o['cells']]
    tasks=[]
    for pid in ids:
        if args.part and pid not in args.part:continue
        stock=original[pid];bb=bbox(stock)
        others=[(oid,[c for c in cells if boundsmeet(bb,bbox(c))]) for oid,cells in fitted.items() if oid!=pid]
        others=[(oid,cs) for oid,cs in others if cs]
        tasks.append((pid,stock,fitted[pid],others,[c for c in all_offcuts if boundsmeet(bb,bbox(c))]))
    results=[]
    with ProcessPoolExecutor(max_workers=max(1,args.jobs)) as pool:
        for r in pool.map(one_member,tasks):
            elapsed=r.pop('elapsed_seconds')
            results.append(r);print(json.dumps({'id':r['id'],'removed_m3':r['removed']['volume_m3'],'empty_m3':r['unfilled']['volume_m3'],'unexplained_m3':r['unexplained_unfilled_volume_m3'],'seconds':elapsed}),flush=True)
    out={'schema_version':'1.0','units':'meters','up_axis':'Y',
         'description':'Per-member original stock minus fitted piece; assembly-unfilled subtracts every other saved fitted timber.',
         'source_archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),
         'source_cells_sha256':hashlib.sha256(raw).hexdigest(),
         'source_model_file_sha256':hashlib.sha256(model_path.read_bytes()).hexdigest(),
         'source_model_sha256':hashlib.sha256(model_path.read_bytes()).hexdigest(),
         'source_sha256':geometry_hash(model),'source_geometry_sha256':geometry_hash(model),'source_part_ids':ids,
         'source_geometry_hash_convention':'SHA256 UTF-8 compact JSON of ordered [{id,vertices,triangles}] with ensure_ascii=False.',
         'method':'Numerical convex half-space subtraction/intersection of saved cells; bounding boxes only cull candidate pairs. Clipping kernel adapted from archived project generator.',
         'distance_epsilon_m':EPS,'cell_volume_epsilon_m3':VEPS,
         'status':'Prototype geometric overlays; no machining clearance, load capacity or assembly approval.',
         'limitations':['Removed stock includes recesses, notches and exterior trimming; it is not exclusively enclosed cavities.',
                        'Occupied pockets are filled by the listed mate when assembled; they are not assembly gaps.',
                        'Unfilled classification is confined to original stock; it does not test intended bearing contacts or arbitrary space between unrelated members.',
                        'Floating-point clipping thresholds apply. Overlay meshes are display surfaces, not fabrication solids.',
                        'Exploded presentation must translate each overlay with its owner; assembly classification always refers to the saved assembled pose.'],
         'parts':{r['id']:r for r in results},
         'summary':{'part_count':len(results),'complete':len(results)==len(ids),
                    'per_member_removed_stock_sum_m3':sum(r['removed']['volume_m3'] for r in results),
                    'per_member_unfilled_sum_m3':sum(r['unfilled']['volume_m3'] for r in results),
                    'unexplained_unfilled_sum_m3':sum(r['unexplained_unfilled_volume_m3'] for r in results),
                    'declared_offcuts_volume_m3':sum(volume(c) for c in all_offcuts),
                    'note':'Per-member sums can count overlapping original-stock regions more than once; they are not a global union-volume calculation.'}}
    Path(args.output).write_text(json.dumps(out,separators=(',',':'))+'\n')
    print(json.dumps({'output':args.output,'bytes':Path(args.output).stat().st_size,'summary':out['summary']}),flush=True)

if __name__=='__main__':main()
