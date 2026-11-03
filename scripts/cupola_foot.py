# TIMESTAMP START 2026-11-02T17:13:08-05:00 | REVISION R004818
"""Selected-model bottom-entry housed dovetail and removable wooden peg.

This adapts a traditional housed-dovetail family to the cupola foot. The chosen
dimensions and orientation are geometric proposals, without capacity approval.
"""
import copy,itertools,math
import numpy as np
import manifold3d as m
from step_lap import solid,mesh,volume_centroid,close_bounds,contacts
from revise_main_braces import clean,exported

I=.0254
REVISION='R004818'
STAMP='2026-11-02T17:13:08-05:00'


def box(low,high):
    low=np.asarray(low,float)*I;high=np.asarray(high,float)*I
    return m.Manifold.cube((high-low).tolist()).translate(low.tolist())


def seed(parts):
    old_c=solid(parts['C0']);old_t=solid(parts['T0'])
    old_tongue=clean(old_t^box([37,84,-4],[44,96,4]))
    receiver=clean(old_c+old_tongue);body=clean(old_t-old_tongue)
    points=np.array([[x,y,z] for y in [85,93]
                     for x,z in [(44,-1.5),(44,1.5),(40,2),(40,-2)]])*I
    tail=m.Manifold.hull_points(points)
    peg=m.Manifold.cylinder(6*I,.375*I,.375*I,32).translate([42*I,89*I,-3*I])
    tie=clean(body+tail+box([44,85,-1.5],[44.01,93,1.5])-peg)
    cupola=clean(receiver-tail-peg)
    before=old_c+old_t;after=cupola+tie+peg
    error=abs((before-after).volume())+abs((after-before).volume())
    assert error/I**3<1e-6,error/I**3
    return {'C':cupola,'T':tie,'CP':peg}, {'old_tongue':old_tongue,'tail':tail,
        'C_old_stock_restored':old_tongue,'C_new_removed':clean(receiver-cupola),
        'T_new_removed':clean((body+tail)-tie),'C_before':old_c,'T_before':old_t},error/I**3


def rotation(k):
    a=k*math.pi/4;c,s=math.cos(a),math.sin(a)
    return np.array([[c,0,s],[0,1,0],[-s,0,c]])


def peg_record(k,shape):
    rot=rotation(k);start=rot@np.array([42,89,-3])*I;end=rot@np.array([42,89,3])*I
    center=(start+end)/2;axis=(end-start)/np.linalg.norm(end-start);pid=f'CP{k}'
    dimensions={'length_m':6*I,'width_m':.75*I,'depth_m':.75*I,'length_ft':.5,
        'width_in':.75,'depth_in':.75,'length_display':'6 in','section_display':'¾ in diameter',
        'status':'Chosen geometric peg size; species, capacity and physical fit unresolved.'}
    geometry=mesh(shape)
    return {'id':pid,'name':'Cupola foot retaining peg','group':'joinery_pegs','temporary':False,
        'material':'wood','is_timber':False,'is_fastener':True,'displayRole':'jointFastener',
        **geometry,'faces':geometry['triangles'],'center':center.tolist(),'label_position':center.tolist(),
        'axis_start':start.tolist(),'axis_end':end.tolist(),'axis_direction':axis.tolist(),
        'exploded_offset':(rot@np.array([0,0,.4])).tolist(),'dimensions':dimensions,
        'nominal_dimensions':copy.deepcopy(dimensions),
        'angles':{'axis_inclination_deg':0,'azimuth_deg':(270+45*k)%360},
        'cut_status':'REMOVABLE PEG PROPOSAL · STRENGTH UNVERIFIED',
        'provenance':'Chosen geometry for the bottom-entry housed dovetail; not read from the source building.',
        'notes':['Withdraw the transverse peg before lifting the cupola post and principal rafter.',
                 'Exact nominal bore/peg geometry; physical fit allowance and uplift capacity unresolved.'],
        'label_lines':[pid,'¾ in PEG','CAPACITY UNVERIFIED'],'label_short':[pid,'PEG'],
        'color':[.61,.43,.24,1],'fit_geometry':{'volume_m3':shape.volume(),'machining_clearance_m':None,
            'nominal_fit':'Exact complementary bore; no strength or fabrication qualification'},
        'stock_frame':{'axis':axis.tolist(),'width':(rot@np.array([1,0,0])).tolist(),'depth':[0,1,0]},
        'reference_end_faces':[],'joint_cut_faces':[],
        'joint_members':[f'C{k}',f'T{k}'],'withdrawal_direction':axis.tolist(),
        'source_geometry_metadata':{'revision':REVISION,'peg_diameter_in':.75,'peg_length_in':6}}


def apply(model):
    assert 'cupola_foot_revision' not in model,'Do not apply the foot migration twice'
    parts={p['id']:p for p in model['parts']};shapes,transfers,error=seed(parts)
    records=[];interfaces=[]
    for k in range(8):
        for family in ['C','T']:
            pid=f'{family}{k}';p=parts[pid];s=clean(shapes[family].rotate((0,45*k,0)))
            geometry=mesh(s);p.update(vertices=geometry['vertices'],triangles=geometry['triangles'],faces=geometry['triangles'])
            p['fit_geometry'].update(volume_m3=s.volume(),nominal_fit='Exact bottom-entry housed dovetail and removable peg; geometric proposal only')
            p['cut_status']='BOTTOM-ENTRY DOVETAIL PROPOSAL · STRENGTH UNVERIFIED'
            p['fabrication_dimensions_valid']=False
            p['notes']=list(p['notes'])+['Cupola foot uses a bottom-entry plan-flared dovetail with an actual transverse retaining peg. Dimensions are chosen proposals, not source readings.']
            if family=='T':
                p['proposed_stock_planes_inches']=copy.deepcopy(p.get('proposed_stock_planes_inches',p['geometry_planes_inches']))
                for plane in p['proposed_stock_planes_inches']:
                    if plane.get('end')=='B':plane['constant']+=4
                p['new_stock_requirements']=dict(p.get('new_stock_requirements',{}),cupola_end_projection_in=4,
                    status='New/raw-stock proposal; no instructions for modifying a previously cut timber')
            else:
                p['proposed_stock_planes_inches']=copy.deepcopy(p.get('proposed_stock_planes_inches',p['geometry_planes_inches']))
            p['cupola_foot_joinery']={'revision':REVISION,'mate':f'{"T" if family=="C" else "C"}{k}',
                'peg':f'CP{k}','entry_direction':[0,-1,0] if family=='C' else [0,1,0],
                'neck_width_in':3,'head_width_in':4,'height_in':8,'engagement_in':4,'side_flare_ratio':'1:8'}
        peg=peg_record(k,shapes['CP'].rotate((0,45*k,0)));records.append(peg);parts[peg['id']]=peg
        interfaces.append({'post':f'C{k}','tie':f'T{k}','peg':f'CP{k}',
            'transfers':{name:exported(s.rotate((0,45*k,0))) for name,s in transfers.items() if not name.endswith('_before')},
            'assembled_envelope_difference_in3':error})
    model['parts'].extend(records)
    group=next((g for g in model['groups'] if g['id']=='joinery_pegs'),None)
    if group is None:
        group={'id':'joinery_pegs','label':'Permanent wooden joint pegs','color':'#9c6e3d','count':0,'default_visible':True};model['groups'].append(group)
    group['count']=sum(p['group']=='joinery_pegs' for p in model['parts'])
    physical={pid:solid(p) for pid,p in parts.items() if p.get('is_timber') or p.get('group')=='joinery_pegs'}
    changed={f'{family}{k}' for k in range(8) for family in ['C','T','CP']};maximum=0.;checks=0
    for a,b in itertools.combinations(physical,2):
        if not ({a,b}&changed) or not close_bounds(physical[a],physical[b]):continue
        amount=max(0.,(physical[a]^physical[b]).volume()/I**3);checks+=1;maximum=max(maximum,amount)
        assert amount<1e-6,(a,b,amount)
    report={'revision':REVISION,'timestamp':STAMP,'status':'NOMINAL GEOMETRY PASS · CAPACITY UNVERIFIED',
        'traditional_family':'Housed dovetail; adapted here to an open-bottom cupola-post foot',
        'source':'https://www.vermonttimberworks.com/learn/timber-frame-joinery/purlins-and-joists/',
        'source_scope':'Documents the joint family only, not this foot orientation, dimensions or load capacity.',
        'neck_in':[3,8],'head_width_in':4,'engagement_in':4,'side_taper':'1:8','peg_diameter_in':.75,
        'minimum_receiver_cheek_in':1,'clear_inner_diameter_in':76,'physical_piece_pair_checks':checks,
        'maximum_overlap_in3':maximum,'interfaces':interfaces,'capacity_checked':False,
        'full_scene_disassembly_verified':False,'changed_member_ids':sorted(changed)}
    model['cupola_foot_revision']={key:value for key,value in report.items() if key!='interfaces'}
    model['proposed_member_volume_centroids']=[dict(id=p['id'],**volume_centroid(physical[p['id']])) for p in model['parts'] if p.get('is_timber')]
    return report
# TIMESTAMP END 2026-11-02T17:13:08-05:00 | REVISION R004818
