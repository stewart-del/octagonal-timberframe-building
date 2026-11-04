# TIMESTAMP START 2026-11-03T16:36:22-05:00 | REVISION R005058
"""Three-inch side-entry short-rafter tenons for the two alternative frames."""
from pathlib import Path
import argparse,copy,itertools,json
import numpy as np
import manifold3d as m
from step_lap import original_stock,mesh,inside_band,close_bounds,volume_centroid,I
from audit_revised_joinery import native_solid as solid,packed

ROOT=Path(__file__).resolve().parents[1]
def save(path,data):path.write_text(json.dumps(data,separators=(',',':'))+'\n')
def build(model):
    result=copy.deepcopy(model);P={p['id']:p for p in result['parts']}
    S={pid:solid(p) for pid,p in P.items() if p['is_timber'] or p.get('is_fastener')}
    raw={pid:m.Manifold(original_stock(p).to_mesh64()) for pid,p in P.items() if pid.startswith(('J','R')) and p['is_timber']}
    joints=[]
    pid='J0-0';p=P[pid];receiver='R0'
    plane=next(q for q in p['geometry_planes_inches'] if q.get('end')=='B')
    n=np.array([plane['normal'][0],plane['normal'][2],-plane['normal'][1]]);face=plane['constant']*I
    vv=np.array(raw[pid].to_mesh64().vert_properties)[:,:3];center=vv[abs(vv@n-face)<1e-7].mean(0)
    full=copy.deepcopy(p['geometry_planes_inches']);next(q for q in full if q.get('end')=='B')['constant']+=3
    blank=m.Manifold(original_stock({**p,'geometry_planes_inches':full}).to_mesh64())
    tongue=blank.trim_by_plane(n.tolist(),face)^raw[receiver];bands=[]
    for key,half in [('width',4/6),('depth',3)]:
        axis=np.array(p['stock_frame'][key]);lo=axis@center-half*I;hi=axis@center+half*I
        tongue=inside_band(tongue,axis,lo,hi);bands.append((axis,lo,hi))
    vv=np.array(tongue.to_mesh64().vert_properties)[:,:3]
    assert abs(np.ptp(vv@n)/I-3)<1e-7
    tool=m.Manifold.hull_points(np.vstack([vv,vv-n*.0001]))
    for axis,lo,hi in bands:tool=inside_band(tool,axis,lo,hi)
    donor=solid(packed(S[pid].trim_by_plane((-n).tolist(),-face)+tool))
    offcut=solid(packed(blank.trim_by_plane(n.tolist(),face)-tool))
    c=np.sqrt(.5);reflection=np.array([[c,0,-c],[0,1,0],[-c,0,-c]])
    for k in range(8):
        a=k*np.pi/4;c,s=np.cos(a),np.sin(a);rotation=np.array([[c,0,s],[0,1,0],[-s,0,c]])
        for side in ['0','2']:
            pid=f'J{k}-{side}';receiver=f'R{k if side=="0" else (k+1)%8}';part=P[pid]
            matrix=rotation@(np.eye(3) if side=='0' else reflection)
            def transformed(shape):
                if side=='2':shape=shape.transform(np.column_stack([reflection,np.zeros(3)]).tolist())
                return shape.rotate([0,45*k,0])
            S[pid]=transformed(donor)
            joints.append({'id':f'TJ-{pid}-{receiver}','donor':pid,'receiver':receiver,'end':'B','shape':'shouldered tenon',
                   'projection_m':3*I,'width_m':(4/3)*I,'height_m':6*I,'face_center':(matrix@center).tolist(),
                   'insertion_direction':(matrix@n).tolist(),'width_direction':part['stock_frame']['width'],
                   'height_direction':part['stock_frame']['depth'],'connector':mesh(transformed(tongue)),'cutting_tool':mesh(transformed(tool))})
            full=copy.deepcopy(part['geometry_planes_inches']);next(q for q in full if q.get('end')=='B')['constant']+=3
            part['proposed_stock_planes_inches']=full
            part['declared_exterior_cut']=mesh(transformed(offcut))
            part['new_stock_requirements']={'tenon_projection_in':3,'status':'Longer raw stock includes the three-inch side-entry tenon.'}
    shape=raw['R0']
    for j in result['tenon_schedule']:
        if j['donor']=='R0':shape=shape+solid(j.get('cutting_tool',j['connector']))
    for other,q in S.items():
        if other.startswith(('P','B')) and close_bounds(shape,q) and (shape^q).volume()>1e-12:shape=shape-q
    for j in joints:
        if j['receiver']=='R0':shape=shape-solid(j['cutting_tool'])
    shape=solid(packed(shape))
    for k in range(8):S[f'R{k}']=shape.rotate([0,45*k,0])
    for pid,shape in S.items():
        if not pid.startswith(('J','R')):continue
        geometry=packed(shape);P[pid].update(geometry);P[pid]['faces']=geometry['triangles']
        P[pid]['fit_geometry']['volume_m3']=geometry['volume_m3']
        S[pid]=solid(P[pid])
    checks=0
    for a,b in itertools.combinations(S,2):
        if not close_bounds(S[a],S[b]):continue
        checks+=1;assert (S[a]^S[b]).volume()/I**3<1e-6,(a,b,'overlap',(S[a]^S[b]).volume()/I**3)
    result['tenon_schedule'].extend(joints)
    result['three_inch_joinery_revision']['tenon_count']=len(result['tenon_schedule'])
    result['three_inch_joinery_revision']['short_rafter_revision']='R005058'
    result['proposed_member_volume_centroids']=[dict(id=pid,**volume_centroid(s)) for pid,s in S.items() if P[pid]['is_timber']]
    print('PASS:',len(joints),'extended short-rafter tenons;',checks,'physical overlap checks',flush=True)
    return result

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=Path('/tmp/octagon-short-rafter-three-inch'));args=parser.parse_args();args.output.mkdir(exist_ok=True)
    for name in ['model-data.json','step-lap-proposed-model.json']:
        save(args.output/name,build(json.loads((ROOT/'src'/name).read_text())))
# TIMESTAMP END 2026-11-03T16:36:22-05:00 | REVISION R005058
