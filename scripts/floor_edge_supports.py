# TIMESTAMP START 2026-11-05T07:15:21+00:00 | REVISION R000031
"""Normalized edge backing and exact additional fastener placement inputs.

No old receiver mesh replaces current stock. The builder checks its unbored
input geometry, adds only new wood, then bores every current receiver once.
"""
from pathlib import Path
import gzip,hashlib,json
import numpy as np
import manifold3d as m
ROOT=Path(__file__).resolve().parents[1];I=.0254;TOL=1e-6*I**3

def solid(record):return m.Manifold(m.Mesh64(np.asarray(record['vertices'],float),np.asarray(record['triangles'],np.uint64)))
def load():
    path=ROOT/'scripts/fixtures/floor-supports.json.gz';data=json.loads(gzip.decompress(path.read_bytes()))
    for name in ['support','spacing']:
        assert hashlib.sha256(data[name+'_raw'].encode()).hexdigest()==data[name+'_sha256']
        data[name]=json.loads(data.pop(name+'_raw'))
    support=data['support'];spacing=data['spacing']
    assert support['raw_boundary_normalization']['status']=='PASS'
    assert not support['attachment_failures'] and not support['positive_intersections']
    assert len(support['unbored_installed_wood'])==24 and len(support['hardware_instances'])==88
    assert len(spacing['parts'])==34 and not spacing['failures']
    assert spacing['support_candidate_sha256']==data['support_sha256']
    data['fixture_sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
    return data

def verify_unbored_inputs(data,solids):
    errors={}
    for pid,record in data['unbored_source_reference'].items():
        assert pid in solids,('Missing backing compatibility reference',pid)
        a=solids[pid];b=solid(record);error=abs((a-b).volume())+abs((b-a).volume())
        assert error<=TOL,('Backing recipe stale for actual stock',pid,error/I**3)
        errors[pid]=error
    return {'status':'PASS','records':len(errors),'maximum_occupied_difference_m3':max(errors.values()),'tolerance_m3':TOL}

def metadata(part,east,north):
    axis=np.asarray(part['grain_axis_floor'],float);grain=east*axis[0]+north*axis[1]+np.array([0.,1.,0.])*axis[2]
    grain/=np.linalg.norm(grain);up=np.array([0.,1.,0.]);width=np.cross(up,grain);vertices=np.asarray(part['vertices'])
    length=float(np.ptp(vertices@grain)/I);ledger='LEDGER' in part['id'];section=[1.5,5.5] if ledger else [3.5,5.5]
    return {'floorRole':'panel_edge_ledger' if ledger else 'notch_backing','displayRole':'floorStructure',
        'stock_frame':{'axis':grain.tolist(),'width':width.tolist(),'depth':up.tolist()},'actualSectionIn':section,
        'nominalSectionIn':[2,6] if ledger else [4,6],'new_stock_requirements':{'minimum_blank_length_in':length,'status':'Individual connected blank; conservative research search envelope is not a purchase length.'},
        'dimensions':{'length_m':length*I,'width_m':section[0]*I,'depth_m':section[1]*I,'width_in':section[0],'depth_in':section[1]},
        'sourceSearchBlank':part.get('stock'),'ledgerRipWidthIn':part.get('final_rip_width_in'),
        'sequence':part.get('attachment','Place before sheathing; four8dcommon toenails, two each end, using the separately modeled actual receiver paths.'),
        'capacityStatus':'Actual geometry, receiving penetration and nominal fastening pattern checked; project connection capacity unqualified.'}
# TIMESTAMP END 2026-11-05T07:15:21+00:00 | REVISION R000031
