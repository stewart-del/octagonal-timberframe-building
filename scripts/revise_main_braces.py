# TIMESTAMP START 2026-11-02T15:15:55-05:00 | REVISION R004802
"""Scoped replacement of the existing knee braces; never rebuild legacy roof joints.

Actual full-sawn 2 x 6 inch stock is user specified. Socket depth and placement
remain a geometric proposal, without structural or fabrication approval.
"""
from pathlib import Path
import copy, hashlib, itertools, json, math
import numpy as np
import manifold3d as m
from step_lap import solid, mesh, resolved, regular_boundary, volume_centroid, close_bounds, contacts
from audit_cavity_fit import inspect_mesh, reference_stock

ROOT = Path(__file__).resolve().parents[1]
I = .0254
REVISION = 'R004802'
STAMP = '2026-11-02T15:15:55-05:00'


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path): return json.loads(path.read_text())
def save(path, data): path.write_text(json.dumps(data, separators=(',', ':')) + '\n')
def shape(record): return solid(record) if record['triangles'] else m.Manifold()

def clean(s):
    s = resolved(s)
    q = mesh(s)
    result = inspect_mesh(np.asarray(q['vertices']), np.asarray(q['triangles'], dtype=np.uint64))
    if result['status'] != 'PASS':
        assert set(result['failures']) <= {'positive-area coplanar raw triangle overlap', 'zero-volume or inverted connected surface'}, result
        s = regular_boundary(s)
    q = mesh(s)
    assert inspect_mesh(np.asarray(q['vertices']), np.asarray(q['triangles'], dtype=np.uint64))['status'] == 'PASS'
    return s


def exported(s):
    if s.is_empty(): return {'vertices': [], 'triangles': [], 'edges': [], 'volume_m3': 0.0}
    result = mesh(clean(s))
    result['edges'] = [list(e) for e in sorted({tuple(sorted((t[i], t[(i+1)%3]))) for t in result['triangles'] for i in range(3)})]
    return result


def stock_brace(template, suffix):
    p = copy.deepcopy(template)
    p['id'] = 'K0-' + suffix
    a = np.array([176, 62, 0.]) * I
    if suffix == 'C':
        b = np.array([148, 90, 0.]) * I
    else:
        b = np.array(template['axis_end'])
    axis = (b-a)/np.linalg.norm(b-a)
    width = np.cross(axis, [0, 1, 0]); width /= np.linalg.norm(width)
    depth = np.cross(width, axis)
    if depth[1] < 0: depth = -depth
    center = (a+b)/2
    # Halfspaces are saved in the original inch/Z-up convention for the
    # independent stock-completeness audit, not inferred from final cavities.
    planes = []
    for n, c, end in [(-axis, -axis@a, 'A'), (axis, axis@b, 'B'),
                       (width, width@center+I, None), (-width, -width@center+I, None),
                       (depth, depth@center+3*I, None), (-depth, -depth@center+3*I, None)]:
        planes.append({'normal': [float(n[0]), float(-n[2]), float(n[1])],
                       'constant': float(c/I), 'end': end, 'mate': None})
    if suffix == 'C':
        # A horizontal bearing end extends two inches above the 85-inch tie
        # underside, instead of consuming seven inches of its ten-inch depth.
        planes.append({'normal': [0, 0, 1], 'constant': 87., 'end': None, 'mate': 'T0'})
    p.update(name='Inward post-to-tie knee brace' if suffix == 'C' else 'Perimeter knee brace',
             axis_start=a.tolist(), axis_end=b.tolist(), axis_direction=axis.tolist(),
             center=center.tolist(), label_position=center.tolist(),
             stock_frame={'axis': axis.tolist(), 'width': width.tolist(), 'depth': depth.tolist()},
             geometry_planes_inches=planes, joint_cut_faces=[])
    p['reference_end_faces'] = []
    for end, point, normal in [('A', a, -axis), ('B', b, axis)]:
        points = [point+sw*I*width+sd*3*I*depth for sw, sd in [(-1,-1),(1,-1),(1,1),(-1,1)]]
        p['reference_end_faces'].append({'id': p['id']+'-'+end, 'part_id': p['id'],
            'vertices': [x.tolist() for x in points], 'triangles': [[0,1,2],[0,2,3]],
            'normal': normal.tolist(), 'description': 'Axis reference only; actual horizontal seat and post stop are recorded separately.'})
    for name in ['dimensions', 'nominal_dimensions']:
        p[name].update(width_m=2*I, depth_m=6*I, width_in=2, depth_in=6, section_display='2 × 6 in',
                       status='Actual full-sawn section specified by owner; joint and capacity design unresolved.')
    p['source_geometry_metadata'].update(revision=REVISION, axis_start=[176.,0.,62.],
        axis_end=[float(b[0]/I),float(-b[2]/I),float(b[1]/I)], section_width_in=2, section_depth_in=6)
    p['notes'] = ['Actual full-sawn 2 × 6 inch section confirmed by owner.',
        '28 inch horizontal and vertical axis projections retained. Two inch post engagement preserves the central post web.',
        'Inward brace has a horizontal upper bearing end two inches above the radial tie underside.' if suffix == 'C' else 'Upper end fits the existing ring-beam location.',
        'Complementary nominal sockets; strength, pegs, movement, assembly and machining clearances remain unverified.']
    p['label_lines'] = [p['id'], '2 × 6 ACTUAL', 'AXIS 45.000°']
    p['label_short'] = [p['id'], '2 × 6', 'JOINT VERIFY']
    p['cut_status'] = 'COMPLEMENTARY BRACE FIT · STRENGTH UNVERIFIED'
    p['exploded_offset'] = [1.5, -.35, 0] if suffix == 'C' else template['exploded_offset']
    vertices, faces = reference_stock(p, apply_declared_trim=True)
    return p, clean(m.Manifold(m.Mesh64(vertices, faces)).set_tolerance(1e-9))


def rotate_record(seed, angle, target):
    p = copy.deepcopy(seed)
    theta = math.radians(angle); c,s = math.cos(theta),math.sin(theta)
    rot = np.array([[c,0,s],[0,1,0],[-s,0,c]])
    def point(v): return (rot@v).tolist()
    p['id'] = target
    for name in ['axis_start','axis_end','axis_direction','center','label_position','exploded_offset']:
        p[name] = point(np.asarray(p[name]))
    p['stock_frame'] = {k:point(np.asarray(v)) for k,v in p['stock_frame'].items()}
    for face in p['reference_end_faces']:
        face['id'] = target+'-'+face['id'][-1]; face['part_id'] = target
        face['vertices'] = [point(np.asarray(v)) for v in face['vertices']]; face['normal'] = point(np.asarray(face['normal']))
    for plane in p['geometry_planes_inches']:
        n=plane['normal']; q=rot@np.array([n[0],n[2],-n[1]])
        plane['normal']=[float(q[0]),float(-q[2]),float(q[1])]
        if plane['mate']: plane['mate']='T'+target[1]
    for name in ['axis_start','axis_end']:
        q = p[name]; p['source_geometry_metadata'][name]=[q[0]/I,-q[2]/I,q[1]/I]
    p['angles']['azimuth_deg'] = math.degrees(math.atan2(-p['axis_direction'][2], p['axis_direction'][0])) % 360
    p['label_lines'][0]=target; p['label_short'][0]=target
    return p


def migrate(model, cavities):
    assert not model.get('main_brace_revision'), 'Migration already applied; do not recut saved joints.'
    original=copy.deepcopy(model); parts={p['id']:p for p in model['parts']}
    solids={k:solid(p) for k,p in parts.items() if p['is_timber']}
    old_braces={k:s for k,s in solids.items() if k.startswith('K')}
    assert len(old_braces)==16
    removed={k:shape(v['removed']) for k,v in cavities['parts'].items()}
    records={}; braces={}; restored={}; sockets={}; transfers=[]
    for suffix in ['A','B','C']:
        records['K0-'+suffix],braces['K0-'+suffix]=stock_brace(parts['K0-'+('A' if suffix=='C' else suffix)],suffix)
    # Only refill material occupied by old braces. All other cuts remain intact.
    for name in ['P0','B0','T0']:
        old_occupied=m.Manifold(); retained=m.Manifold()
        for component in removed[name].decompose():
            brace_owned=any(close_bounds(brace,component) and
                abs((brace^component).volume()-component.volume())/I**3<1e-6
                for brace in old_braces.values())
            if brace_owned: old_occupied=old_occupied+component
            else: retained=retained+component
        restored[name]=clean(solids[name]+old_occupied)
        sockets[name]=retained
        assert abs((old_occupied-solids[name]).volume()-old_occupied.volume())/I**3<1e-6
        transfers.append({'receiver':name,'old_brace_stock_restored_in3':old_occupied.volume()/I**3})
    contacts=[]
    targets={'P0':[braces['K0-A'],braces['K0-B'],braces['K0-C']],
             'B0':[braces['K0-B'],braces['K0-A'].rotate((0,45,0))],
             'T0':[braces['K0-C']]}
    target_ids={'P0':['K0-A','K0-B','K0-C'],'B0':['K0-B','K1-A'],'T0':['K0-C']}
    for name, owners in targets.items():
        total=m.Manifold()
        for owner,brace in zip(target_ids[name],owners):
            insert=clean(restored[name]^brace)
            assert insert.volume()>I**3, (name,owner,'no meaningful joint engagement')
            total=total+insert
            contacts.append({'owner':owner,'receiver':name,'insert_volume_in3':insert.volume()/I**3})
        solids[name]=clean(restored[name]-total)
        removed[name]=clean(sockets[name]+total)
    # Exact quadrant rotations keep the three families and their cavities alike.
    for k in range(8):
        for family in ['P','B','T']:
            name=f'{family}{k}'; seed=family+'0'
            if k:
                solids[name]=clean(solids[seed].rotate((0,45*k,0)))
                removed[name]=clean(removed[seed].rotate((0,45*k,0)))
            p=parts[name];g=mesh(solids[name]);p.update(vertices=g['vertices'],triangles=g['triangles'],faces=g['triangles'])
            p['fit_geometry']['volume_m3']=g['volume_m3']
        for suffix in ['A','B','C']:
            name=f'K{k}-{suffix}';p=rotate_record(records['K0-'+suffix],45*k,name)
            solids[name]=clean(braces['K0-'+suffix].rotate((0,45*k,0)))
            g=mesh(solids[name]);p.update(vertices=g['vertices'],triangles=g['triangles'],faces=g['triangles'])
            p['fitted_axial_extent_inches'] = float(np.ptp(np.asarray(g['vertices'])@p['stock_frame']['axis'])/I)
            p['fit_geometry'].update(volume_m3=g['volume_m3'],nominal_fit='Complementary full 2 × 6 brace sockets; geometry only')
            parts[name]=p;removed[name]=m.Manifold()
    output=[]
    for p in model['parts']:
        output.append(parts[p['id']])
        if p['id'].endswith('-B') and p['id'].startswith('K'): output.append(parts[p['id'][:-1]+'C'])
    model['parts']=output
    model['r01']['timber_count']=112
    model['r01']['main_brace_section_in']=[2,6]
    model['r01']['main_brace_count']=24
    for g in model['groups']:
        if g['id']=='braces':g.update(count=24,label='24 knee braces · actual 2 × 6')
    unchanged=[p['id'] for p in original['parts'] if p['id'][0] not in 'PBTK']
    for name in unchanged: assert parts[name]==next(p for p in original['parts'] if p['id']==name)
    overlaps=[];maximum=0.
    for a,b in itertools.combinations(solids,2):
        if not close_bounds(solids[a],solids[b]):continue
        amount=max(0.,(solids[a]^solids[b]).volume()/I**3);maximum=max(maximum,amount)
        if amount>1e-6:overlaps.append({'a':a,'b':b,'overlap_in3':amount})
    assert not overlaps, overlaps
    model['main_brace_revision']={'revision':REVISION,'timestamp':STAMP,'actual_section_in':[2,6],
        'brace_count':24,'third_brace_ids':[f'K{k}-C' for k in range(8)],
        'scope':'Only main brace solids and their P/B/T receiving sockets changed; new stock, not repair instructions for already-cut members.',
        'strength_verified':False,'assembly_sequence_verified':False}
    model['joinery_verification'].update(wood_count=112,pairs_tested=6216)
    cavities['parts']={p['id']:{'removed':exported(removed[p['id']])} for p in output if p['is_timber']}
    cavities['summary']['part_count']=112
    report={'status':'PASS','revision':REVISION,'actual_section_in':[2,6],'timber_count':112,'item_count':123,
        'brace_count':24,'unchanged_member_ids':unchanged,'receiver_restoration':transfers,'seed_joint_insertions':contacts,
        'pairs_tested':6216,'maximum_positive_overlap_in3':maximum,'interferences':overlaps,
        'tolerance_in3':1e-6,'strength_verified':False,'assembly_sequence_verified':False,
        'limitations':'Nominal CAD fit only; full raising sequence, physical fit allowance, connection capacity and stock quality remain unresolved.'}
    return model,cavities,report


def update_auxiliary(model, model_sha):
    members={p['id']:p for p in model['parts'] if p['is_timber']}
    data=read(ROOT/'src/load-review-data.json');data['source_model_sha256']=model_sha
    data['members']=[dict(id=k,**volume_centroid(solid(p))) for k,p in members.items()]
    # TIMESTAMP START 2026-11-02T17:32:31-05:00 | REVISION R004820
    fasteners=[p for p in model['parts'] if p.get('group')=='joinery_pegs']
    data['fasteners']=[dict(id=p['id'],**volume_centroid(solid(p))) for p in fasteners]
    data['fastener_scope']='Permanent wood fasteners; separate from the primary-timber self-weight subtotal.'
    data['fastener_volume_m3']=sum(p['volume_m3'] for p in data['fasteners'])
    # TIMESTAMP END 2026-11-02T17:32:31-05:00 | REVISION R004820
    (ROOT/'src/load-review-data.json').write_text(json.dumps(data,indent=2)+'\n')
    # TIMESTAMP START 2026-11-02T17:32:31-05:00 | REVISION R004820
    groups=read(ROOT/'src/material-groups.json');groups.update(source_sha256=model_sha,timber_count=len(members),item_count=len(model['parts']))
    groups['groups']=[g for g in groups['groups'] if g['family']!='joinery_pegs']
    if fasteners:
        number=len(groups['groups'])+1
        groups['groups'].append({'id':f'M{number:02d}','number':number,'quantity':len(fasteners),
            'member_ids':[p['id'] for p in fasteners],'representative_id':fasteners[0]['id'],
            'family':'joinery_pegs','label':'Permanent wooden joint pegs','status':'Chosen geometric fasteners; no capacity or interchangeability approval',
            'method':'Explicit fitted peg geometry; lengths vary with their brace/receiver envelopes'})
    groups['group_count']=len(groups['groups'])
    # TIMESTAMP END 2026-11-02T17:32:31-05:00 | REVISION R004820
    for g in groups['groups']:
        if g['family']=='braces':g.update(quantity=24,member_ids=list(k for k in members if k.startswith('K')),label='Knee braces · actual 2 × 6')
    (ROOT/'src/material-groups.json').write_text(json.dumps(groups,indent=2)+'\n')
    foundation=read(ROOT/'src/floor-foundation-solids.json');foundation['source_model_sha256']=model_sha
    foundation['source_module_sha256']=sha(ROOT/'src/floor-foundation.js')
    save(ROOT/'src/floor-foundation-solids.json',foundation)


def write_joinery_report(model, model_sha):
    parts={p['id']:p for p in model['parts'] if p['is_timber']}
    solids={k:solid(p) for k,p in parts.items()}
    report=read(ROOT/'docs/joinery-verification.json')
    report.update(source_model_sha256=model_sha,wood_count=112,pairs_tested=6216,
        overlaps=[],invalid_contacts=[],revision=REVISION)
    report['joints']=[j for j in report['joints'] if not j['owner'].startswith('K')]
    for k in range(8):
        for suffix in ['A','B','C']:
            owner=f'K{k}-{suffix}'
            targets=[f'P{k}', f'T{k}' if suffix=='C' else f'B{(k-1)%8 if suffix=="A" else k}']
            for receiver in targets:
                v,f=reference_stock(parts[receiver]);stock=m.Manifold(m.Mesh64(v,f))
                faces=contacts(solids[owner],solids[receiver])
                projected=max(sum(face['area_in2']*max(0.,face['normal_on_rafter'][axis]) for face in faces) for axis in range(3))
                gap=solids[owner].min_gap(solids[receiver],.01)*1000
                assert gap<1e-4 and projected>.01,(owner,receiver,gap,projected)
                report['joints'].append({'owner':owner,'receiver':receiver,
                    'kind':'Full 2 × 6 diagonal brace socket; proposed two inch engagement',
                    'insert_volume_in3':(solids[owner]^stock).volume()/I**3,
                    'gap_mm':gap,'projected_contact_area_in2':projected})
    old={row['id']:row for row in report['pieces']}
    report['pieces']=[]
    for name,p in parts.items():
        record=old.get(name,{'id':name})
        record.update(connected_solids=len(solids[name].decompose()),valid=str(solids[name].status())=='Error.NoError',
                      final_volume_in3=solids[name].volume()/I**3)
        if name.startswith('K'):
            v,f=reference_stock(p);record['original_volume_in3']=m.Manifold(m.Mesh64(v,f)).volume()/I**3
        report['pieces'].append(record)
    report['main_brace_revision']=model['main_brace_revision']
    (ROOT/'docs/joinery-verification.json').write_text(json.dumps(report,indent=2)+'\n')


def main():
    path=ROOT/'src/model-data.json';model=read(path)
    if model.get('main_brace_revision',{}).get('revision')==REVISION:
        print('Brace migration already present; left source untouched.');return
    model,cavities,report=migrate(model,read(ROOT/'src/cavity-data.json'))
    save(path,model);model_sha=sha(path);cavities['source_model_sha256']=model_sha
    save(ROOT/'src/cavity-data.json',cavities);report['source_model_sha256']=model_sha
    save(ROOT/'docs/main-brace-fit-audit.json',report);update_auxiliary(model,model_sha);write_joinery_report(model,model_sha)
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
# TIMESTAMP END 2026-11-02T15:15:55-05:00 | REVISION R004802
