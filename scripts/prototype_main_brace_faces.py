# TIMESTAMP START 2026-11-02T17:12:42-05:00 | REVISION R004817
"""Isolated geometric prototype of pegged face-housed main knee braces.

No canonical file is written. This uses the documented face-cut brace family,
not a strength rating. Endpoint offsets and peg sizes remain proposed geometry.
"""
import itertools, json, math
from pathlib import Path
import numpy as np
import manifold3d as m
from step_lap import solid, close_bounds, volume_centroid, regular_boundary, mesh
from audit_cavity_fit import reference_stock, inspect_mesh
from plan_architectural_disassembly import sweep_cover

ROOT=Path(__file__).resolve().parents[1]
I=.0254
SOURCE='https://www.vermonttimberworks.com/ask-the-timber-framing-experts/can-a-mortise-tenon-brace-be-installed-after-the-post-beam-have-been-assembled/'

def clean(s):
    pieces=[p for p in s.decompose() if abs(p.volume())>1e-12]
    assert len(pieces)==1 and pieces[0].volume()>0,'Disconnected occupied timber'
    s=pieces[0];q=mesh(s)
    if inspect_mesh(np.asarray(q['vertices']),np.asarray(q['triangles']))['status']!='PASS':s=regular_boundary(s)
    q=mesh(s)
    assert inspect_mesh(np.asarray(q['vertices']),np.asarray(q['triangles']),require_single=True)['status']=='PASS'
    return s

def rotated(v,angle):
    c=math.cos(angle);s=math.sin(angle)
    return np.array([[c,0,s],[0,1,0],[-s,0,c]])@v

def build(model):
    parts={p['id']:p for p in model['parts'] if p.get('is_timber')}
    original={pid:solid(p) for pid,p in parts.items()}
    raw={};restored={}
    old_braces={pid:s for pid,s in original.items() if pid.startswith('K')}
    for pid,p in parts.items():
        if pid[0] not in 'PBT':continue
        vertices,faces=reference_stock(p);stock=m.Manifold(m.Mesh64(vertices,faces));raw[pid]=stock
        inserts=[stock^brace for brace in old_braces.values() if close_bounds(stock,brace)]
        restored[pid]=clean(m.Manifold.batch_boolean([original[pid],*inserts],m.OpType.Add))
    specs=[];braces={};stocks={};joints=[]
    for k in range(8):
        theta=k*math.pi/4
        for suffix in ['A','B','C']:
            seed=parts['K0-'+suffix];old_a=np.asarray(seed['axis_start']);old_b=np.asarray(seed['axis_end'])
            width=np.asarray(seed['stock_frame']['width'])
            if suffix=='A':post_face=np.array([0.,0,1]);beam_face=width
            elif suffix=='B':post_face=np.array([0.,0,-1]);beam_face=-width
            else:post_face=np.array([-1.,0,0]);beam_face=np.array([0.,0,1])
            a=old_a+post_face*3*I;b=old_b+beam_face*2.5*I
            edge=old_b-old_a;edge[1]=0;edge/=np.linalg.norm(edge)
            delta=b-a;delta[1]=0;target=(b[1]-a[1])
            along=-delta@edge+math.sqrt((delta@edge)**2+target**2-delta@delta)
            b=b+edge*along
            axis=(b-a)/np.linalg.norm(b-a);width=np.cross(axis,[0,1,0]);width/=np.linalg.norm(width);depth=np.cross(width,axis)
            if depth[1]<0:depth=-depth
            points=np.array([point+width*x*I+depth*y*3*I for point in [a-axis*2*I,b+axis*2*I] for x in [-1,1] for y in [-1,1]])
            stock=m.Manifold.hull_points(points)
            if suffix=='C':stock=stock.trim_by_plane([0,-1,0],-87*I)
            stock=stock.rotate([0,45*k,0]);pid='K'+str(k)+'-'+suffix
            n=post_face+beam_face;n/=np.linalg.norm(n);n=rotated(n,theta)
            receiver='T'+str(k) if suffix=='C' else 'B'+str((k-1)%8 if suffix=='A' else k)
            faces=[('P'+str(k),rotated(post_face,theta)),(receiver,rotated(beam_face,theta))]
            fitted=stock;tools=[]
            for rid,nface in faces:
                r=restored[rid];rv=np.asarray(raw[rid].to_mesh64().vert_properties)[:,:3]
                outside=stock.trim_by_plane(nface.tolist(),float(max(rv@nface)))
                assert not outside.is_empty(),(pid,rid,'No exposed face for insertion')
                vertices=np.asarray(outside.to_mesh64().vert_properties)[:,:3]
                # The face patch is swept inward exactly one inch normal to
                # the receiving face. This retains only material visible from
                # the common insertion direction, avoiding trapped corners.
                tool=m.Manifold.hull_points(np.vstack([vertices,vertices-n*I/(n@nface)]))
                fitted=fitted-(r-tool);tools.append((rid,nface))
            fitted=clean(fitted);braces[pid]=fitted;stocks[pid]=stock
            specs.append({'id':pid,'axis_start':rotated(a,theta).tolist(),'axis_end':rotated(b,theta).tolist(),
                'withdrawal_world':n.tolist(),'actual_section_m':[2*I,6*I],
                'stock_axis_allowance_each_end_m':2*I,'source':SOURCE})
            for rid,nface in tools:
                toe=fitted^restored[rid]
                assert toe.volume()>3*I**3,(pid,rid,'Insufficient prototype engagement')
                joints.append({'brace':pid,'receiver':rid,'face_normal':nface.tolist(),
                    'toe':toe,'toe_volume_in3':toe.volume()/I**3})
    receivers={pid:r for pid,r in restored.items()}
    for joint in joints:receivers[joint['receiver']]=receivers[joint['receiver']]-braces[joint['brace']]
    receivers={pid:clean(s) for pid,s in receivers.items()}
    pre_bore_braces=dict(braces);pre_bore_receivers=dict(receivers)
    pegs={};peg_specs=[]
    for joint in joints:
        bid=joint['brace'];rid=joint['receiver'];axis=np.asarray(joint['face_normal']);toe=joint['toe']
        center=np.asarray(volume_centroid(toe)['centroid_m'])
        if rid.startswith('P'):
            center[1]+=(-.75 if bid.endswith('-A') else .75 if bid.endswith('-B') else 0)*I
        vertices=np.asarray(raw[rid].to_mesh64().vert_properties)[:,:3];low=min(vertices@axis);high=max(vertices@axis)
        u=np.cross(axis,np.eye(3)[np.argmin(abs(axis))]);u/=np.linalg.norm(u);v=np.cross(axis,u)
        origin=center+axis*(low-6*I-center@axis);matrix=np.column_stack([u,v,axis,origin])
        bore=m.Manifold.cylinder(high-low+12*I,.25*I,.25*I,24).transform(matrix.tolist())
        assert (bore^braces[bid]).volume()>.1*I**3,(bid,rid,'Peg misses brace toe')
        crossed=[other for other,shape in braces.items() if close_bounds(bore,shape) and (bore^shape).volume()>1e-10]
        occupied=m.Manifold.batch_boolean([receivers[rid],*[braces[other] for other in crossed]],m.OpType.Add)
        # The cylindrical bore crosses the projecting brace as well as the
        # receiver. Trim the wooden peg flush to those real external faces.
        candidate=bore^occupied
        peg=clean(m.Manifold.hull_points(np.asarray(candidate.to_mesh64().vert_properties)[:,:3]))
        assert abs((peg-candidate).volume())+abs((candidate-peg).volume())<I**3*1e-6,(bid,rid,'Peg hull changes occupied volume')
        assert (peg^braces[bid]).volume()>.1*I**3,(bid,rid,'Peg misses brace toe')
        peg_id='MAIN-PEG-'+bid+'-'+rid;pegs[peg_id]=peg
        for other in crossed:braces[other]=braces[other]-peg
        receivers[rid]=receivers[rid]-peg
        peg_vertices=np.asarray(peg.to_mesh64().vert_properties)[:,:3];peg_low=min(peg_vertices@axis);peg_high=max(peg_vertices@axis)
        peg_specs.append({'id':peg_id,'brace':bid,'crossed_braces':crossed,'receiver':rid,'diameter_m':.5*I,'withdrawal_world':axis.tolist(),'withdrawal_distance_m':float(peg_high-peg_low+.05)})
    fitted={**original,**receivers,**braces,**pegs}
    for pid in braces:braces[pid]=clean(braces[pid]);fitted[pid]=braces[pid]
    for pid in receivers:receivers[pid]=clean(receivers[pid]);fitted[pid]=receivers[pid]
    return {'solids':fitted,'braces':braces,'receivers':receivers,'pegs':pegs,'specs':specs,'peg_specs':peg_specs,'joints':joints,'stocks':stocks,'restored_receivers':restored,'pre_bore_braces':pre_bore_braces,'pre_bore_receivers':pre_bore_receivers,'structural_capacity_verified':False}

def audit(result):
    """Check nominal fit and local release; parking/global order is separate."""
    tolerance=I**3*1e-6;failures=[];maximum=0.;checks=0
    for a,b in itertools.combinations(result['solids'],2):
        sa=result['solids'][a];sb=result['solids'][b]
        if not close_bounds(sa,sb):continue
        volume=max(0.,(sa^sb).volume());checks+=1;maximum=max(maximum,volume)
        if volume>tolerance:failures.append({'kind':'assembled_overlap','parts':[a,b],'volume_m3':volume})
    paths=0;path_checks=0;maximum_path=0.
    for kind,specs in [('peg',result['peg_specs']),('brace',result['specs'])]:
        for spec in specs:
            pid=spec['id'];distance=spec['withdrawal_distance_m'] if kind=='peg' else .25
            travel,account=sweep_cover(result['solids'][pid],np.asarray(spec['withdrawal_world'])*distance)
            paths+=1
            for other,shape in result['solids'].items():
                if other==pid or (kind=='brace' and other in result['pegs']) or not close_bounds(travel,shape):continue
                volume=max(0.,(travel^shape).volume());path_checks+=1;maximum_path=max(maximum_path,volume)
                if volume>tolerance:failures.append({'kind':kind+'_withdrawal','parts':[pid,other],'volume_m3':volume})
    report={'status':'PASS' if not failures else 'FAIL','brace_count':len(result['braces']),
        'peg_count':len(result['pegs']),'static_pair_checks':checks,'maximum_static_overlap_in3':maximum/I**3,
        'continuous_local_paths':paths,'path_pair_checks':path_checks,'maximum_path_overlap_in3':maximum_path/I**3,
        'toe_volume_range_in3':[min(j['toe_volume_in3'] for j in result['joints']),max(j['toe_volume_in3'] for j in result['joints'])],
        'overlap_tolerance_in3':tolerance/I**3,'failures':failures,
        'scope':'Local continuous translations against primary timbers and pegs; brace paths assume every retaining peg has already been removed. Parked pieces, architecture, lifting and global assembly order require the separate complete-scene audit.',
        'structural_capacity_verified':False}
    return report

if __name__=='__main__':
    for filename in ['model-data.json','step-lap-proposed-model.json','top-entry-proposed-model.json']:
        path=ROOT/'src'/filename
        if not path.exists():continue
        result=build(json.loads(path.read_text()));report=audit(result)
        print(filename,json.dumps(report),flush=True)
        assert report['status']=='PASS',report
# TIMESTAMP END 2026-11-02T17:12:42-05:00 | REVISION R004817
