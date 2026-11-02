"""Allow planar retriangulation only after checking the same oriented surface.
Does not relax the repository's mesh validity/intersection/stock/path tests.
"""
import collections,copy
import numpy as np
# TIMESTAMP START 2026-11-02T13:01:18-05:00 | REVISION R004778
from regeneration_equivalence import assert_equivalent, assert_mesh_equivalent
import manifold3d as m
# TIMESTAMP END 2026-11-02T13:01:18-05:00 | REVISION R004778
from step_lap import solid,volume_centroid

def surface_record(mesh):
    v=np.asarray(mesh['vertices']);tri=np.asarray(mesh['triangles']);groups=[];edges=collections.defaultdict(list)
    for ids in tri:
        p=v[ids];vector=np.cross(p[1]-p[0],p[2]-p[0]);length=np.linalg.norm(vector)
        assert length>1e-16,'Degenerate triangle cannot certify retriangulation'
        normal=vector/length;offset=float(normal@p[0]);area=length/2;center=p.mean(0)
        group=next((g for g in groups if np.linalg.norm(g['normal']-normal)<1e-9 and abs(g['offset']-offset)<1e-10),None)
        if group is None:group={'normal':normal,'offset':offset,'area':0.,'moment':np.zeros(3)};groups.append(group)
        group['area']+=area;group['moment']+=area*center
        for i in range(3):edges[tuple(sorted((int(ids[i]),int(ids[(i+1)%3]))))].append(normal)
    assert all(len(normals)==2 for normals in edges.values()),'Open or nonmanifold mesh'
    features={edge for edge,normals in edges.items() if np.linalg.norm(normals[0]-normals[1])>1e-8}
    return groups,features

# TIMESTAMP START 2026-11-02T13:01:18-05:00 | REVISION R004778
def assert_same_surface(actual,expected,path=()):
    # One shared proof covers cyclic starts, vertex reindexing and alternative
    # planar diagonals. Raw overlaps and inverted/open faces are rejected;
    # matched signed plane regions are checked in both directions, not merely
    # by aggregate area or centroid. Metadata is checked by the caller.
    return assert_mesh_equivalent(actual,expected,'/'.join(map(str,path)) or '<root>',{})
# TIMESTAMP END 2026-11-02T13:01:18-05:00 | REVISION R004778

def normalize_planar_retriangulation(actual,expected,path=(),stats=None):
    if stats is None:stats={'equivalent_retriangulated_meshes':0}
    if isinstance(actual,dict) and isinstance(expected,dict):
        if all(k in actual and k in expected for k in ['vertices','triangles']) and actual['triangles']!=expected['triangles']:
            assert_same_surface(actual,expected,path)
            if 'faces' in actual:
                assert actual['faces']==actual['triangles'] and expected.get('faces')==expected['triangles'],(path,'faces/index mismatch')
                actual['faces']=copy.deepcopy(expected['faces'])
            # TIMESTAMP START 2026-11-02T13:01:18-05:00 | REVISION R004778
            # The proof also permits a bijective vertex reindex. Normalize the
            # coordinate/index arrays together so this in-memory comparison
            # cannot pair saved indices with a different vertex ordering.
            actual['vertices']=copy.deepcopy(expected['vertices'])
            actual['triangles']=copy.deepcopy(expected['triangles']);stats['equivalent_retriangulated_meshes']+=1
            # TIMESTAMP END 2026-11-02T13:01:18-05:00 | REVISION R004778
        for key in actual.keys()&expected.keys():normalize_planar_retriangulation(actual[key],expected[key],path+(key,),stats)
        # TIMESTAMP START 2026-11-02T13:01:18-05:00 | REVISION R004778
        if 'continuous_vertical_sweeps' in actual and 'continuous_vertical_sweeps' in expected:
            normalize_sweep_work_counts(actual['continuous_vertical_sweeps'],expected['continuous_vertical_sweeps'],path,stats)
        if all(k in actual and k in expected for k in ['baseline_parts','proposed_parts','node','geometry_audit']):
            normalize_named_sections(actual,expected,path,stats)
        # TIMESTAMP END 2026-11-02T13:01:18-05:00 | REVISION R004778
    elif isinstance(actual,list) and isinstance(expected,list):
        for i,(a,b) in enumerate(zip(actual,expected)):normalize_planar_retriangulation(a,b,path+(i,),stats)
    return stats

# TIMESTAMP START 2026-11-02T13:01:18-05:00 | REVISION R004778
def normalize_sweep_work_counts(actual,expected,path=(),stats=None):
    """Check both clearance certificates; normalize only partition work counts.

    Boundary retriangulation changes the number of vertical triangle prisms,
    not the covered motion. The top-entry test independently checks the actual
    entire-member motion. Keep all measured upper bounds, identities, motion,
    scope and methods for the caller's strict comparison.
    """
    assert len(actual)==len(expected),(path,'sweep record count')
    cutoff_in3=1e-15/.0254**3
    for a,b in zip(actual,expected):
        assert a.keys()==b.keys() and a['member']==b['member'],(path,'sweep identity/schema')
        for row in [a,b]:
            if 'lift_in' in row:assert row['lift_in']==24,(path,'sweep motion')
            else:assert np.max(np.abs(np.asarray(row['translation_world_m'])-[0,24*.0254,0]))<1e-13,(path,'sweep motion')
            assert row['interferences']==[],(path,'sweep interference')
            bound=row['discarded_prism_volume_bound_in3'];total=row['maximum_total_overlap_bound_in3']
            key='maximum_overlap_upper_bound_in3' if 'maximum_overlap_upper_bound_in3' in row else 'maximum_summed_overlap_upper_bound_in3'
            measured=row[key]
            assert all(isinstance(v,(int,float)) and not isinstance(v,bool) and np.isfinite(v) and v>=0 for v in [bound,total,measured]),(path,'invalid sweep bound')
            assert total<1e-6 and abs(total-(measured+bound))<1e-15,(path,'sweep bound exceeded/inconsistent')
            triangles=round(bound/cutoff_in3)
            assert triangles>0 and abs(bound/cutoff_in3-triangles)<1e-6,(path,'unaccounted prism omission')
            cover=row['covering_solids'];checks=row.get('prism_intersection_checks',row.get('narrow_phase_checks'))
            assert type(cover) is int and 1<=cover<=triangles+1,(path,'invalid sweep cover count')
            assert type(checks) is int and 0<=checks<=cover*103,(path,'invalid sweep work count')
        changed=False
        for key in ['covering_solids','prism_intersection_checks','narrow_phase_checks']:
            if key in a:
                changed|=a[key]!=b[key]
                a[key]=b[key]
        if changed and stats is not None:stats['equivalent_sweep_work_counts']=stats.get('equivalent_sweep_work_counts',0)+1


def test_sweep_work_guard():
    bound=60*1e-15/.0254**3
    base=[{'member':'J0-0','lift_in':24,'covering_solids':27,'narrow_phase_checks':61,
           'maximum_overlap_upper_bound_in3':0.,'discarded_prism_volume_bound_in3':bound,
           'maximum_total_overlap_bound_in3':bound,'interferences':[]}]
    valid=copy.deepcopy(base);valid[0].update(covering_solids=21,narrow_phase_checks=53)
    normalize_sweep_work_counts(valid,base);assert valid==base
    mutations=[lambda r:r.update(member='J0-2'),lambda r:r.update(lift_in=12),
               lambda r:r.update(covering_solids=0),lambda r:r.update(narrow_phase_checks=999999),
               lambda r:r.update(interferences=[{'member':'R0'}]),
               lambda r:r.update(maximum_total_overlap_bound_in3=1e-5),
               lambda r:r.update(discarded_prism_volume_bound_in3=bound*1.001)]
    for mutate in mutations:
        invalid=copy.deepcopy(base);mutate(invalid[0])
        try:normalize_sweep_work_counts(invalid,base)
        except AssertionError:continue
        raise AssertionError('Sweep work normalization accepted changed motion, an obstruction or an invalid bound')
# TIMESTAMP END 2026-11-02T13:01:18-05:00 | REVISION R004778

# TIMESTAMP START 2026-11-02T13:01:18-05:00 | REVISION R004778
def normalize_named_sections(actual,expected,path=(),stats=None):
    """Validate native section-area diagnostics against scaled canonical slices.

    Manifold 3.5.4 uses Clipper precision_=8 for CrossSection: native metre
    coordinates are rounded to a 10 nm grid. A vertex moves at most half the
    grid diagonal; add the solid kernel 1 nm tolerance and the scaled oracle
    grid error. Total contour perimeter times this displacement, plus a circular
    allowance for each contour, bounds the area diagnostic including holes.
    This does not loosen the independent 3D boundary position/area/volume limits.
    Source: https://github.com/elalish/manifold/blob/v3.5.4/src/cross_section/cross_section.cpp
    """
    key='R_named_region_section_samples'
    if key not in actual['geometry_audit'] or key not in expected['geometry_audit']:return
    aa=actual['geometry_audit'][key];bb=expected['geometry_audit'][key]
    assert len(aa)==len(bb),(path,'section sample count')
    hip=expected['node']['hip'];assert actual['node']['hip']==hip
    baseline=next(p for p in expected['baseline_parts'] if p['id']==hip)
    proposed=next(p for p in expected['proposed_parts'] if p['id']==hip)
    origin=np.asarray(baseline['axis_end']);axis=np.asarray(baseline['stock_frame']['axis']);axis=axis/np.linalg.norm(axis)
    u=np.cross(axis,np.eye(3)[np.argmin(np.abs(axis))]);u/=np.linalg.norm(u)
    rotation=np.array([u,np.cross(axis,u),axis]);scale=1e6;inch=.0254
    clip_grid_m=1e-8;diagnostic_displacement_m=clip_grid_m/np.sqrt(2)*(1+1/scale)+1e-9
    for record in [actual,expected]:
        audit=record['geometry_audit']
        assert abs(audit['minimum_sampled_R_section_in2']-min(r['proposed_area_in2'] for r in audit[key]))<1e-9,(path,'section minimum inconsistent')
    for a,b in zip(aa,bb):
        assert a.keys()==b.keys() and a['radial_station_in']==b['radial_station_in'],(path,'section identity')
        station=origin+((b['radial_station_in']*inch-origin[0])/axis[0])*axis
        for field,member in [('V13_area_in2',baseline),('proposed_area_in2',proposed)]:
            vertices=(np.asarray(member['vertices'])-station)@rotation.T*scale
            shape=m.Manifold(m.Mesh64(vertices,np.asarray(member['triangles'],dtype=np.uint64)))
            assert shape.status()==m.Error.NoError,(path,'canonical section mesh invalid')
            cut=shape.slice(0);area=cut.area()/scale**2/inch**2
            contours=cut.to_polygons()
            assert contours,(path,'canonical section is empty')
            perimeter=sum(np.linalg.norm(np.roll(p,-1,axis=0)-p,axis=1).sum() for p in map(np.asarray,contours))/scale
            limit=(perimeter*diagnostic_displacement_m+len(contours)*np.pi*diagnostic_displacement_m**2)/inch**2
            for row in [a,b]:
                assert np.isfinite(row[field]) and abs(row[field]-area)<=limit,(path,field,'section diagnostic exceeds documented clipping envelope',row[field],area,limit)
            if a[field]!=b[field] and stats is not None:stats['equivalent_section_diagnostics']=stats.get('equivalent_section_diagnostics',0)+1
            a[field]=b[field]
    actual['geometry_audit']['minimum_sampled_R_section_in2']=expected['geometry_audit']['minimum_sampled_R_section_in2']


def test_named_section_guard(base):
    member=dict(copy.deepcopy(base),id='R0',axis_end=[0.,0.,0.],stock_frame={'axis':[1.,0.,0.]})
    area=1/.0254**2
    record={'node':{'hip':'R0'},'baseline_parts':[member],'proposed_parts':[copy.deepcopy(member)],
            'geometry_audit':{'R_named_region_section_samples':[{'radial_station_in':.5/.0254,'V13_area_in2':area,'proposed_area_in2':area}],
                              'minimum_sampled_R_section_in2':area}}
    valid=copy.deepcopy(record);valid['geometry_audit']['R_named_region_section_samples'][0]['proposed_area_in2']+=1e-8;valid['geometry_audit']['minimum_sampled_R_section_in2']+=1e-8
    normalize_named_sections(valid,record);assert valid==record
    for field in ['area','station']:
        bad=copy.deepcopy(record);row=bad['geometry_audit']['R_named_region_section_samples'][0]
        if field=='area':row['proposed_area_in2']+=.001;bad['geometry_audit']['minimum_sampled_R_section_in2']+=.001
        else:row['radial_station_in']+=.001
        try:normalize_named_sections(bad,record)
        except AssertionError:continue
        raise AssertionError('Named section normalization accepted changed station or excessive area error')
# TIMESTAMP END 2026-11-02T13:01:18-05:00 | REVISION R004778

def test_mesh_guard():
    # TIMESTAMP START 2026-11-02T13:01:18-05:00 | REVISION R004778
    test_sweep_work_guard()
    # TIMESTAMP END 2026-11-02T13:01:18-05:00 | REVISION R004778
    base={'vertices':[[0.,0.,0.],[1.,0.,0.],[1.,1.,0.],[0.,1.,0.],[0.,0.,1.],[1.,0.,1.],[1.,1.,1.],[0.,1.,1.]],'triangles':[[0,2,1],[0,3,2],[4,5,6],[4,6,7],[0,1,5],[0,5,4],[1,2,6],[1,6,5],[2,3,7],[2,7,6],[3,0,4],[3,4,7]]}
    # TIMESTAMP START 2026-11-02T13:01:18-05:00 | REVISION R004778
    test_named_section_guard(base)
    # TIMESTAMP END 2026-11-02T13:01:18-05:00 | REVISION R004778
    other=copy.deepcopy(base);other['triangles'][:2]=[[0,3,1],[1,3,2]];assert_same_surface(other,base)
    # TIMESTAMP START 2026-11-02T13:01:18-05:00 | REVISION R004778
    permuted=copy.deepcopy(base);permuted['vertices'].reverse();permuted['triangles']=[[7-i for i in t] for t in permuted['triangles']]
    normalize_planar_retriangulation(permuted,base)
    assert permuted==base,'Verified vertex/index normalization must preserve a consistent mesh'
    # TIMESTAMP END 2026-11-02T13:01:18-05:00 | REVISION R004778
    bads=[]
    bad=copy.deepcopy(other);bad['triangles'][0]=[0,1,3];bads.append(bad)
    bad=copy.deepcopy(other);bad['triangles'].pop();bads.append(bad)
    bad=copy.deepcopy(other);bad['vertices'][0][0]=1e-6;bads.append(bad)
    for bad in bads:
        try:assert_same_surface(bad,base)
        except (AssertionError,ValueError):continue
        raise AssertionError('Mesh guard accepted actual geometric/topological change')

def normalize_section_diagrams(actual,expected,path=()):
    """Diagnostic 2D loops may gain collinear vertices after retriangulation.
    Check oriented boundary equivalence to1e-6in (not a3D geometry allowance).
    """
    def area(p):return .5*np.sum(p[:,0]*np.roll(p[:,1],-1)-p[:,1]*np.roll(p[:,0],-1))
    def distance(points,loop):
        a=loop;b=np.roll(loop,-1,axis=0);edge=b-a;length=np.sum(edge*edge,axis=1);worst=0.
        for p in points:
            t=np.divide(np.sum((p-a)*edge,axis=1),length,out=np.zeros_like(length),where=length>1e-24);near=a+np.clip(t,0,1)[:,None]*edge
            worst=max(worst,float(np.min(np.linalg.norm(near-p,axis=1))))
        return worst
    def same(a,b):
        a=np.asarray(a);b=np.asarray(b)
        return np.sign(area(a))==np.sign(area(b)) and abs(area(a)-area(b))<1e-5 and max(distance(a,b),distance(b,a))<1e-6
    if isinstance(actual,dict) and isinstance(expected,dict):
        if 'diagram_sections' in actual and 'diagram_sections' in expected:
            for key in ['stock','V13','candidate']:
                aa=actual['diagram_sections'][key];bb=expected['diagram_sections'][key]
                assert len(aa)==len(bb),(path,key,'section loop count')
                remaining=list(bb)
                for loop in aa:
                    hits=[i for i,p in enumerate(remaining) if same(loop,p)]
                    assert len(hits)==1,(path,key,'changed oriented section boundary')
                    remaining.pop(hits[0])
                actual['diagram_sections'][key]=copy.deepcopy(bb)
        for key in actual.keys()&expected.keys():normalize_section_diagrams(actual[key],expected[key],path+(key,))
    elif isinstance(actual,list) and isinstance(expected,list):
        for i,(a,b) in enumerate(zip(actual,expected)):normalize_section_diagrams(a,b,path+(i,))

def test_section_guard():
    square=[[0.,0.],[1.,0.],[1.,1.],[0.,1.]]
    base={'diagram_sections':{key:[copy.deepcopy(square)] for key in ['stock','V13','candidate']}}
    good=copy.deepcopy(base);good['diagram_sections']['candidate'][0].insert(1,[.5,0.]);normalize_section_diagrams(good,base)
    for kind in ['shift','reverse','missing']:
        bad=copy.deepcopy(base)
        if kind=='shift':bad['diagram_sections']['candidate'][0][0][0]=.001
        elif kind=='reverse':bad['diagram_sections']['candidate'][0].reverse()
        else:bad['diagram_sections']['candidate']=[]
        try:normalize_section_diagrams(bad,base)
        except AssertionError:continue
        raise AssertionError('Section guard accepted changed boundary/orientation/loop count')
