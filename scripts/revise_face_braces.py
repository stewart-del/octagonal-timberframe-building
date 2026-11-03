# TIMESTAMP START 2026-11-02T17:32:31-05:00 | REVISION R004820
"""Migrate the saved baseline to removable, pegged face-housed knee braces.

Only old brace-occupied receiver material is restored. Exterior shoulder
offcuts remain distinct from matching peg bores and receiving housings.
"""
from pathlib import Path
import copy,hashlib,itertools,json,math
import numpy as np
import manifold3d as m
from scipy.spatial import ConvexHull
from prototype_main_brace_faces import build,SOURCE
from revise_main_braces import clean,save,read,update_auxiliary,write_joinery_report
from step_lap import solid,mesh,volume_centroid,close_bounds,regular_boundary
from audit_cavity_fit import reference_stock,inspect_mesh

ROOT=Path(__file__).resolve().parents[1];I=.0254
REVISION='R004820';STAMP='2026-11-02T17:32:31-05:00'


def exported(shape):
    if shape.is_empty():return {'vertices':[],'triangles':[],'edges':[],'volume_m3':0.}
    initial=shape.volume();q=mesh(shape)
    if inspect_mesh(np.asarray(q['vertices']),np.asarray(q['triangles'],dtype=np.uint64))['status']!='PASS':
        # Cancel raw coincident membranes before reconstructing a Manifold.
        # Rebuilding the invalid boundary first can change occupied volume.
        shape=regular_boundary(shape);q=mesh(shape)
    assert abs(shape.volume()-initial)/I**3<1e-6,'Export normalization changed occupied volume'
    check=inspect_mesh(np.asarray(q['vertices']),np.asarray(q['triangles'],dtype=np.uint64))
    assert check['status']=='PASS',check['failures']
    q['edges']=[list(e) for e in sorted({tuple(sorted((t[i],t[(i+1)%3]))) for t in q['triangles'] for i in range(3)})]
    return q


def planes(shape):
    vertices=np.asarray(shape.to_mesh64().vert_properties)[:,:3]
    equations=ConvexHull(vertices).equations;seen=set();result=[]
    for row in equations:
        n=row[:3];constant=-row[3]/I;key=tuple(np.round(np.r_[n,constant],10))
        if key in seen:continue
        seen.add(key);result.append({'normal':[float(n[0]),float(-n[2]),float(n[1])],
            'constant':float(constant),'end':None,'mate':None})
    return result


def fastener_record(spec,shape):
    axis=np.asarray(spec['withdrawal_world']);vertices=np.asarray(shape.to_mesh64().vert_properties)[:,:3]
    center=np.asarray(volume_centroid(shape)['centroid_m']);low=min(vertices@axis);high=max(vertices@axis)
    start=center+axis*(low-center@axis);end=center+axis*(high-center@axis)
    width=np.cross(axis,np.eye(3)[np.argmin(abs(axis))]);width/=np.linalg.norm(width);depth=np.cross(axis,width)
    geometry=mesh(shape);pid=spec['id'];length=high-low
    dims={'length_m':float(length),'width_m':.5*I,'depth_m':.5*I,'length_ft':float(length/.3048),
        'width_in':.5,'depth_in':.5,'length_display':f'{length/I:.3f} in','section_display':'½ in diameter',
        'status':'Chosen geometric hardwood peg; capacity and physical fit unresolved.'}
    return {'id':pid,'name':'Main knee-brace retaining peg','group':'joinery_pegs','temporary':False,
        'material':'wood','is_timber':False,'is_fastener':True,'displayRole':'jointFastener',**geometry,
        'faces':geometry['triangles'],'center':center.tolist(),'label_position':center.tolist(),
        'axis_start':start.tolist(),'axis_end':end.tolist(),'axis_direction':axis.tolist(),
        'exploded_offset':(axis*.4).tolist(),'dimensions':dims,'nominal_dimensions':copy.deepcopy(dims),
        'angles':{'axis_inclination_deg':math.degrees(math.asin(axis[1])),'azimuth_deg':math.degrees(math.atan2(-axis[2],axis[0]))%360},
        'cut_status':'REMOVABLE BRACE PEG PROPOSAL · STRENGTH UNVERIFIED','provenance':SOURCE,
        'notes':['Face-housed brace family with removable transverse peg; actual dimensions are chosen geometry, not capacity-approved.',
                 'Through peg is flush to the real brace/receiver envelope; withdraw all crossing pegs before removing a brace.'],
        'label_lines':[pid,'½ in PEG','CAPACITY UNVERIFIED'],'label_short':[pid,'PEG'],'color':[.61,.43,.24,1],
        'fit_geometry':{'volume_m3':shape.volume(),'machining_clearance_m':None,'nominal_fit':'Exact complementary bore'},
        'stock_frame':{'axis':axis.tolist(),'width':width.tolist(),'depth':depth.tolist()},
        'reference_end_faces':[],'joint_cut_faces':[],
        'joint_members':[spec['receiver'],*spec['crossed_braces']],
        'withdrawal_direction':axis.tolist(),'withdrawal_distance_m':spec['withdrawal_distance_m'],
        'source_geometry_metadata':{'revision':REVISION,'peg_diameter_in':.5,'peg_length_in':float(length/I)}}


def migrate(model,cavities,result):
    assert not model.get('main_face_brace_revision'),'Face-brace migration already applied'
    parts={p['id']:p for p in model['parts']};original=copy.deepcopy(parts)
    for pid,s in {**result['receivers'],**result['braces']}.items():
        geometry=mesh(s);parts[pid].update(vertices=geometry['vertices'],triangles=geometry['triangles'],faces=geometry['triangles'])
        parts[pid]['fit_geometry'].update(volume_m3=s.volume(),nominal_fit='Face-housed brace and removable peg; exact nominal fit only')
    exterior_seeds={suffix:solid(exported(result['stocks']['K0-'+suffix]-result['pre_bore_braces']['K0-'+suffix])) for suffix in ['A','B','C']}
    for spec in result['specs']:
        pid=spec['id'];p=parts[pid];a=np.asarray(spec['axis_start']);b=np.asarray(spec['axis_end'])
        axis=(b-a)/np.linalg.norm(b-a);width=np.cross(axis,[0,1,0]);width/=np.linalg.norm(width);depth=np.cross(width,axis)
        if depth[1]<0:depth=-depth
        p.update(axis_start=a.tolist(),axis_end=b.tolist(),axis_direction=axis.tolist(),center=((a+b)/2).tolist(),
            label_position=((a+b)/2).tolist(),stock_frame={'axis':axis.tolist(),'width':width.tolist(),'depth':depth.tolist()},
            geometry_planes_inches=planes(result['stocks'][pid]),reference_end_faces=[],joint_cut_faces=[])
        p['angles']['axis_inclination_deg']=45.;p['angles']['azimuth_deg']=math.degrees(math.atan2(-axis[2],axis[0]))%360
        p['source_geometry_metadata'].update(revision=REVISION,
            axis_start=[a[0]/I,-a[2]/I,a[1]/I],axis_end=[b[0]/I,-b[2]/I,b[1]/I])
        p['geometry_planes_inches_status']='Chosen full2×6 raw stock, including2in axial allowance at each end; explicit exterior shoulder cuts are separate from fitted peg bores.'
        exterior=exterior_seeds[pid[-1]].rotate((0,45*int(pid[1]),0))
        direct=result['stocks'][pid]-result['pre_bore_braces'][pid]
        assert (abs((exterior-direct).volume())+abs((direct-exterior).volume()))/I**3<1e-6,(pid,'exterior rotation mismatch')
        p['declared_exterior_cut']=exported(exterior)
        p['main_face_brace_joinery']={**spec,'revision':REVISION,
            'peg_ids':[q['id'] for q in result['peg_specs'] if pid in q['crossed_braces']],
            'exterior_cut_basis':'Raw full2×6 stock minus the visible face-housed brace before any peg bores.'}
        p['notes']=['Actual full-sawn2×6 stock;28in rise and horizontal run retained.',
            'Two receiver faces admit one common withdrawal direction after all crossing pegs are removed.',
            'One-inch face housing and half-inch pegs are chosen geometric proposals, not qualified structural dimensions.']
        p['cut_status']='PEGGED FACE-HOUSED BRACE · STRENGTH UNVERIFIED'
        p['fitted_axial_extent_inches']=float(np.ptp(np.asarray(p['vertices'])@axis)/I)
        bore_parts=[peg^result['pre_bore_braces'][pid] for peg in result['pegs'].values()
                    if close_bounds(peg,result['pre_bore_braces'][pid])]
        bores=m.Manifold.batch_boolean(bore_parts,m.OpType.Add)
        expected_bore_volume=result['pre_bore_braces'][pid].volume()-result['braces'][pid].volume()
        assert abs(bores.volume()-expected_bore_volume)/I**3<1e-6,(pid,'bore conservation')
        try:cavities['parts'][pid]={'removed':exported(bores)}
        except AssertionError as error:raise AssertionError((pid,'peg bore export',str(error))) from error
    receiver_seed_cavities={}
    for pid,s in result['receivers'].items():
        v,f=reference_stock(parts[pid]);stock=m.Manifold(m.Mesh64(v,f))
        family=pid[0]
        if family not in receiver_seed_cavities:
            old_mask=solid(cavities['parts'][pid]['removed'])
            old_braces=[solid(p) for name,p in original.items() if name.startswith('K')]
            retained=[piece for piece in old_mask.decompose() if not any(close_bounds(piece,brace) and abs((piece^brace).volume()-piece.volume())/I**3<1e-6 for brace in old_braces)]
            inserts=[owner^stock for owner in [*result['braces'].values(),*result['pegs'].values()] if close_bounds(owner,stock)]
            direct_mask=m.Manifold.batch_boolean([*retained,*inserts],m.OpType.Add)
            try:receiver_seed_cavities[family]=solid(exported(direct_mask))
            except AssertionError as error:raise AssertionError((pid,'receiver seed export',str(error))) from error
        cavity=receiver_seed_cavities[family].rotate((0,45*int(pid[1]),0))
        direct=stock-s
        assert (abs((cavity-direct).volume())+abs((direct-cavity).volume()))/I**3<1e-6,(pid,'receiver cavity rotation mismatch')
        cavities['parts'][pid]={'removed':exported(cavity)}
    pegs=[fastener_record(spec,result['pegs'][spec['id']]) for spec in result['peg_specs']]
    model['parts'].extend(pegs)
    model['groups'].append({'id':'joinery_pegs','label':'Permanent wooden joint pegs','color':'#9c6e3d','count':len(pegs),'default_visible':True})
    changed=set(result['receivers'])|set(result['braces'])
    assert all(parts[pid]==p for pid,p in original.items() if pid not in changed)
    maximum=0.;checks=0
    for a,b in itertools.combinations(result['solids'],2):
        if not close_bounds(result['solids'][a],result['solids'][b]):continue
        amount=max(0.,(result['solids'][a]^result['solids'][b]).volume()/I**3);maximum=max(maximum,amount);checks+=1
        assert amount<1e-6,(a,b,amount)
    report={'revision':REVISION,'timestamp':STAMP,'status':'NOMINAL GEOMETRY PASS · CAPACITY UNVERIFIED',
        'brace_count':24,'peg_count':48,'actual_section_in':[2,6],'chosen_face_housing_depth_in':1,
        'chosen_peg_diameter_in':.5,'joint_family_source':SOURCE,'changed_member_ids':sorted(changed),
        'minimum_toe_volume_in3':min(j['toe_volume_in3'] for j in result['joints']),
        'maximum_toe_volume_in3':max(j['toe_volume_in3'] for j in result['joints']),
        'physical_pair_checks':checks,'maximum_overlap_in3':maximum,
        'brace_specs':result['specs'],'peg_specs':result['peg_specs'],
        'capacity_checked':False,'full_scene_disassembly_verified':False}
    model['main_face_brace_revision']=report
    cavities['status']='Exact receiving housings and peg bores; declared exterior brace shoulder cuts are not mating cavities.'
    return model,cavities,report


def main():
    path=ROOT/'src/model-data.json';model=read(path)
    assert not model.get('main_face_brace_revision'),'Already migrated; do not recut'
    result=build(model);model,cavities,report=migrate(model,read(ROOT/'src/cavity-data.json'),result)
    save(path,model);sha=hashlib.sha256(path.read_bytes()).hexdigest();cavities['source_model_sha256']=sha
    save(ROOT/'src/cavity-data.json',cavities);report['source_model_sha256']=sha
    save(ROOT/'docs/main-brace-face-fit-audit.json',report)
    update_auxiliary(model,sha);write_joinery_report(model,sha)
    print('Migrated',len(model['parts']),'items; baseline',sha,flush=True)


if __name__=='__main__':main()
# TIMESTAMP END 2026-11-02T17:32:31-05:00 | REVISION R004820
