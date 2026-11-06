# TIMESTAMP START 2026-11-04T23:23:25+00:00 | REVISION R000011
# TIMESTAMP START 2026-11-03T13:49:43-05:00 | REVISION R005031
"""Centered full 2x6 braces with regular rectangular three-inch tenons.

Prototype output is isolated until the assembled and moving geometry pass.
Peg checks establish engagement with real wood, not structural capacity.
"""
from pathlib import Path
import copy, hashlib, itertools, json, math
import numpy as np
import manifold3d as m
from step_lap import solid, mesh, original_stock, close_bounds, volume_centroid
from revise_main_braces import clean

ROOT=Path(__file__).resolve().parents[1]
I=.0254
STAMP='2026-11-03T13:49:43-05:00'
REVISION='R005031'

def box(lo,hi):
    lo=np.asarray(lo,float);hi=np.asarray(hi,float)
    return m.Manifold.cube((hi-lo).tolist()).translate(lo.tolist())

def oriented_box(center,axes,size):
    center=np.asarray(center);axes=np.asarray(axes);size=np.asarray(size)
    return m.Manifold.hull_points(np.array([center+np.asarray(s)*size/2@axes for s in itertools.product([-1,1],repeat=3)]))

def rotate(v,k):
    a=k*math.pi/4;c=math.cos(a);s=math.sin(a)
    return np.array([[c,0,s],[0,1,0],[-s,0,c]])@np.asarray(v)

def cylinder(center,axis,lo,hi,radius):
    axis=np.asarray(axis);u=np.cross(axis,np.eye(3)[np.argmin(abs(axis))]);u/=np.linalg.norm(u);v=np.cross(axis,u)
    origin=np.asarray(center)+axis*(lo-np.dot(center,axis))
    return m.Manifold.cylinder(hi-lo,radius,radius,32).transform(np.column_stack([u,v,axis,origin]).tolist())

def build(model):
    records={p['id']:p for p in model['parts']}
    original={pid:solid(p) for pid,p in records.items() if p.get('is_timber') or p.get('is_fastener')}
    old=[s for pid,s in original.items() if pid.startswith(('K','MAIN-PEG-'))]
    restored={};raw={}
    for pid in ['P0','B0','T0']:
        stock=original_stock(records[pid]);after=original[pid];inserts=[]
        for s in old:
            if not close_bounds(s,stock):continue
            insert=s^stock
            if insert.volume()<1e-12:continue
            inserts.append(insert)
            vv=np.array(insert.to_mesh64().vert_properties)[:,:3]
            # Refill a tiny surrounding stock region as well as the void.
            # Overlapping intact material avoids coincident bore membranes.
            after=after+(stock^box(vv.min(0)-.001,vv.max(0)+.001))
        expected=m.Manifold.batch_boolean([original[pid],*inserts],m.OpType.Add)
        after=clean(after)
        assert abs(after.volume()-expected.volume())/I**3<1e-6,(pid,'restoration changed unrelated pockets')
        for k in range(8):
            target=pid[0]+str(k);raw[target]=stock.rotate([0,45*k,0]);restored[target]=after.rotate([0,45*k,0])
    bodies={};blanks={};specs={};joints=[]
    up=np.array([0.,1.,0.])
    for suffix in ['A','B','C']:
        receiver='T0' if suffix=='C' else 'B7' if suffix=='A' else 'B0'
        e=np.array([-1.,0.,0.]) if suffix=='C' else np.array([-math.sin(math.pi/8),0.,math.cos(math.pi/8)*(1 if suffix=='A' else -1)])
        normal=np.cross(e,up);normal/=np.linalg.norm(normal)
        post_axis=0 if suffix=='C' else 2
        post_sign=-1 if suffix in ['B','C'] else 1
        face=(172 if suffix=='C' else 4*post_sign)*I
        # TIMESTAMP START 2026-11-04T19:42:40+00:00 | REVISION R000016
        base=np.array([176*I,(44 if suffix=='C' else 62)*I,0.])
        # TIMESTAMP END 2026-11-04T19:42:40+00:00 | REVISION R000016
        a=base+e*((face-base[post_axis])/e[post_axis])
        beam_y=min(v[1] for v in records[receiver]['vertices'])
        run=24*I if suffix=='C' else beam_y-a[1]
        b=a+e*run;b[1]=beam_y
        axis=(b-a)/np.linalg.norm(b-a);depth=np.cross(normal,axis)
        if depth[1]<0:depth=-depth
        blank=oriented_box((a+b)/2,[axis,normal,depth],[np.linalg.norm(b-a)+16*I,2*I,6*I])
        exterior=blank.trim_by_plane((np.eye(3)[post_axis]*post_sign).tolist(),face*post_sign).trim_by_plane([0,-1,0],-beam_y)
        body=exterior
        # Rectangular post mortise is normal to the actual post face; the
        # upper mortise is vertical through the beam underside. Both are 3 in.
        post_in=-np.eye(3)[post_axis]*post_sign
        post_cross=normal
        endpoints=[('P0',a-up*.5*I,post_in,post_cross,up),(receiver,b,up,normal,e)]
        local_joints=[]
        for rid,face_center,inward,cross,along in endpoints:
            # TIMESTAMP START 2026-11-04T19:42:40+00:00 | REVISION R000016
            # Keep the brace's sloping heel, but square its nose against an
            # INTERNAL bearing wall. This is the supplied housed-brace profile,
            # not a small rectangular pencil tongue on an exterior shoulder.
            bearing=-up if rid=='P0' else e
            data=np.asarray(exterior.to_mesh64().vert_properties)[:,:3]
            mouth=float(face_center@inward)
            cap=data[abs(data@inward-mouth)<1e-8]
            assert len(cap)>=3,(suffix,rid,'missing shoulder cap')
            nose=float(max(cap@bearing)-.75*I)
            strip=blank.trim_by_plane(cross.tolist(),float(face_center@cross-.5*I)).trim_by_plane((-cross).tolist(),float(-face_center@cross-.5*I))
            tongue=strip.trim_by_plane(inward.tolist(),mouth).trim_by_plane((-inward).tolist(),-mouth-3*I).trim_by_plane((-bearing).tolist(),-nose)
            root=strip.trim_by_plane(inward.tolist(),mouth-.05*I).trim_by_plane((-inward).tolist(),-mouth-.05*I).trim_by_plane((-bearing).tolist(),-nose)
            # TIMESTAMP END 2026-11-04T19:42:40+00:00 | REVISION R000016
            # TIMESTAMP START 2026-11-04T19:42:40+00:00 | REVISION R000016
            if suffix=='C' and rid!='P0':
                # Owner: gravity-seated square tenon at the cross-beam end.
                tongue=oriented_box(face_center+up*1.5*I,[up,cross,e],[3*I,I,2*I])
                root=oriented_box(face_center-up*.05*I,[up,cross,e],[.1*I,I,2*I])
            # TIMESTAMP END 2026-11-04T19:42:40+00:00 | REVISION R000016
            assert (tongue-restored[rid]).volume()/I**3<1e-6,(suffix,rid,'tenon leaves receiver stock')
            assert (root^body).volume()/I**3>.05,(suffix,rid,'tenon root misses brace')
            # TIMESTAMP START 2026-11-04T19:42:40+00:00 | REVISION R000016
            body=body+tongue
            # TIMESTAMP END 2026-11-04T19:42:40+00:00 | REVISION R000016
            local_joints.append((rid,tongue,face_center,inward,cross,along))
        body=clean(body)
        assert (body-blank).volume()/I**3<1e-6,(suffix,'tenon cannot be cut from full 2x6 stock')
        for k in range(8):
            pid=f'K{k}-{suffix}';bodies[pid]=body.rotate([0,k*45,0]);blanks[pid]=blank.rotate([0,k*45,0])
            specs[pid]={'id':pid,'axis_start':rotate(a,k).tolist(),'axis_end':rotate(b,k).tolist(),'stock_frame':{'axis':rotate(axis,k).tolist(),'width':rotate(normal,k).tolist(),'depth':rotate(depth,k).tolist()},'tenons':[]}
            for rid,tongue,center,inward,cross,along in local_joints:
                target=rid[0]+str((int(rid[1])+k)%8)
                # TIMESTAMP START 2026-11-04T19:42:40+00:00 | REVISION R000016
                vertices=np.asarray(tongue.to_mesh64().vert_properties)[:,:3]
                bearing=-up if rid=='P0' else e
                joint={'id':f'BJ-{pid}-{target}','donor':pid,'receiver':target,'projection_m':3*I,'width_m':I,'height_m':float(np.ptp(vertices@along)),'shape':'housed brace tenon with squared internal bearing end','face_center':rotate(center,k).tolist(),'insertion_direction':rotate(inward,k).tolist(),'width_direction':rotate(cross,k).tolist(),'height_direction':rotate(along,k).tolist(),'bearing_direction':rotate(bearing,k).tolist(),'bearing_coordinate_m':float(max(vertices@bearing)),'outer_shoulder_lip_m':.75*I,'connector':mesh(tongue.rotate([0,45*k,0]))}
                # TIMESTAMP END 2026-11-04T19:42:40+00:00 | REVISION R000016
                # TIMESTAMP START 2026-11-04T19:42:40+00:00 | REVISION R000016
                if suffix=='C' and rid!='P0':
                    joint.update(shape='simple square-seated vertical tenon',gravity_seated=True,bearing_direction=[0,1,0],bearing_coordinate_m=float(max(vertices@up)))
                # TIMESTAMP END 2026-11-04T19:42:40+00:00 | REVISION R000016
                joints.append(joint);specs[pid]['tenons'].append(joint)
    receivers=dict(restored)
    for joint in joints:
        # TIMESTAMP START 2026-11-03T16:00:30-05:00 | REVISION R005047
        cutter=bodies[joint['donor']]
        # TIMESTAMP END 2026-11-03T16:00:30-05:00 | REVISION R005047
        receivers[joint['receiver']]=receivers[joint['receiver']]-cutter
    before={**receivers,**bodies};pegs={};peg_specs=[]
    for joint in joints:
        donor=joint['donor'];rid=joint['receiver'];axis=np.array(joint['width_direction']);center=np.array(volume_centroid(solid(joint['connector']))['centroid_m'])
        vs=np.array(raw[rid].to_mesh64().vert_properties)[:,:3];lo=min(vs@axis);hi=max(vs@axis)
        peg=cylinder(center,axis,lo,hi,.25*I)^raw[rid]
        # A real centered tenon has receiver wood on both sides of its bore.
        tongue=solid(joint['connector']);engagement=(peg^tongue).volume();cheeks=peg^before[rid]
        assert engagement>.15*I**3,(donor,rid,'peg misses tenon')
        segments=[q for q in cheeks.decompose() if q.volume()>1e-12]
        assert len(segments)==2,(donor,rid,'peg lacks two receiver cheeks',len(segments))
        lengths=[float(np.ptp(np.array(q.to_mesh64().vert_properties)[:,:3]@axis)/I) for q in segments]
        assert min(lengths)>.75,(donor,rid,'insufficient modeled cheek',lengths)
        pid=f'MAIN-PEG-{donor}-{rid}';pegs[pid]=peg;joint['peg_id']=pid
        bore=cylinder(center,axis,lo-.001,hi+.001,.25*I)
        bodies[donor]=bodies[donor]-bore;receivers[rid]=receivers[rid]-bore
        peg_specs.append({'id':pid,'brace':donor,'crossed_braces':[donor],'receiver':rid,'diameter_m':.5*I,'withdrawal_world':axis.tolist(),'withdrawal_distance_m':float(hi-lo+.05),'tenon_engagement_in':1.,'receiver_cheek_lengths_in':lengths,'tenon_edge_clearance_in':.75})
        peg_specs[-1]['bore_center_world']=center.tolist()
    final={pid:s for pid,s in original.items() if not pid.startswith(('K','MAIN-PEG-'))}
    seeds={}
    for pid,s in {**receivers,**bodies}.items():
        seed=pid[0]+'0'+pid[2:]
        if seed not in seeds:
            try:seeds[seed]=clean(({**receivers,**bodies})[seed].simplify(1e-10))
            except Exception as error:raise AssertionError((seed,'boundary normalization',str(error))) from error
        normalized=seeds[seed].rotate([0,45*int(pid[1]),0])
        assert abs((s-normalized).volume())+abs((normalized-s).volume())<1e-6*I**3,(pid,'family geometry differs')
        final[pid]=normalized
    final.update(pegs)
    failures=[];checks=0
    for (aid,a),(bid,b) in itertools.combinations(final.items(),2):
        if not close_bounds(a,b):continue
        checks+=1;amount=(a^b).volume()/I**3
        if amount>1e-6:failures.append({'pair':[aid,bid],'overlap_in3':amount})
    return {'solids':final,'braces':bodies,'receivers':receivers,'stocks':blanks,'restored_receivers':restored,'pre_bore_braces':{k:before[k] for k in bodies},'pegs':pegs,'specs':list(specs.values()),'joints':joints,'peg_specs':peg_specs,'audit':{'status':'FAIL' if failures else 'PASS','checks':checks,'failures':failures,'peg_count':len(pegs),'minimum_cheek_in':min(min(q['receiver_cheek_lengths_in']) for q in peg_specs),'tenon_depth_in':3,'capacity_verified':False}}

if __name__=='__main__':
    path=ROOT/'src/top-entry-proposed-model.json';result=build(json.loads(path.read_text()))
    report={'revision':REVISION,'timestamp':STAMP,'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),**result['audit'],'joints':result['joints'],'peg_specs':result['peg_specs'],'brace_specs':result['specs']}
    (ROOT/'docs/centered-brace-prototype.json').write_text(json.dumps(report,separators=(',',':'))+'\n')
    print(json.dumps(result['audit']),flush=True)
    assert report['status']=='PASS',report['failures']
# TIMESTAMP END 2026-11-03T13:49:43-05:00 | REVISION R005031

# TIMESTAMP END 2026-11-04T23:23:25+00:00 | REVISION R000011
