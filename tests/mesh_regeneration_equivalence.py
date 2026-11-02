"""Allow planar retriangulation only after checking the same oriented surface.
Does not relax the repository's mesh validity/intersection/stock/path tests.
"""
import collections,copy
import numpy as np
from regeneration_equivalence import assert_equivalent
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

def assert_same_surface(actual,expected,path=()):
    # Vertex identity/order and tiny coordinate drift stay strictly checked;
    # we do not accept arbitrary nearest-surface or whole-solid AABB matches.
    assert_equivalent(actual['vertices'],expected['vertices'],path+('vertices',))
    a=solid(actual);b=solid(expected)
    assert str(a.status())==str(b.status())=='Error.NoError',(path,'invalid manifold')
    assert len(a.decompose())==len(b.decompose()),(path,'component count')
    ag,ae=surface_record(actual);bg,be=surface_record(expected)
    assert ae==be,(path,'changed noncoplanar boundary edges')
    assert len(ag)==len(bg),(path,'changed oriented face planes')
    unmatched=list(bg)
    for g in ag:
        matches=[h for h in unmatched if np.linalg.norm(g['normal']-h['normal'])<1e-9 and abs(g['offset']-h['offset'])<1e-10]
        assert len(matches)==1,(path,'missing/ambiguous oriented face')
        h=matches[0];unmatched=[x for x in unmatched if x is not h]
        assert abs(g['area']-h['area'])<1e-12,(path,'face area')
        assert np.linalg.norm(g['moment']/g['area']-h['moment']/h['area'])<1e-10,(path,'face centroid')
    av=volume_centroid(a);bv=volume_centroid(b)
    assert abs(av['volume_m3']-bv['volume_m3'])<1e-13,(path,'net volume')
    assert np.linalg.norm(np.asarray(av['centroid_m'])-bv['centroid_m'])<1e-11,(path,'net centroid')

def normalize_planar_retriangulation(actual,expected,path=(),stats=None):
    if stats is None:stats={'equivalent_retriangulated_meshes':0}
    if isinstance(actual,dict) and isinstance(expected,dict):
        if all(k in actual and k in expected for k in ['vertices','triangles']) and actual['triangles']!=expected['triangles']:
            assert_same_surface(actual,expected,path)
            if 'faces' in actual:
                assert actual['faces']==actual['triangles'] and expected.get('faces')==expected['triangles'],(path,'faces/index mismatch')
                actual['faces']=copy.deepcopy(expected['faces'])
            actual['triangles']=copy.deepcopy(expected['triangles']);stats['equivalent_retriangulated_meshes']+=1
        for key in actual.keys()&expected.keys():normalize_planar_retriangulation(actual[key],expected[key],path+(key,),stats)
    elif isinstance(actual,list) and isinstance(expected,list):
        for i,(a,b) in enumerate(zip(actual,expected)):normalize_planar_retriangulation(a,b,path+(i,),stats)
    return stats

def test_mesh_guard():
    base={'vertices':[[0.,0.,0.],[1.,0.,0.],[1.,1.,0.],[0.,1.,0.],[0.,0.,1.],[1.,0.,1.],[1.,1.,1.],[0.,1.,1.]],'triangles':[[0,2,1],[0,3,2],[4,5,6],[4,6,7],[0,1,5],[0,5,4],[1,2,6],[1,6,5],[2,3,7],[2,7,6],[3,0,4],[3,4,7]]}
    other=copy.deepcopy(base);other['triangles'][:2]=[[0,3,1],[1,3,2]];assert_same_surface(other,base)
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
