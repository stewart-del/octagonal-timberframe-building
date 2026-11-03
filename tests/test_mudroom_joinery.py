# TIMESTAMP START 2026-11-02T15:00:19-05:00 | REVISION R004797
"""Read back actual porch solids, matched cavities and continuous insertion paths.

This proves nominal geometric fit and the listed local/group motions, not timber
capacity, construction tolerance, a lifting plan or a complete erection design.
"""
from pathlib import Path
import hashlib, itertools, json, os, shutil, subprocess, sys
import numpy as np
import manifold3d as m

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from audit_cavity_fit import inspect_mesh
NODE=os.environ.get('NODE') or shutil.which('node')
assert NODE,'Set NODE to a Node.js executable'
TOL=1e-10
fit=json.loads((ROOT/'src/mudroom-joinery-fit.json').read_text())
for key,path in [('source_module_sha256','src/mudroom.js'),('source_roof_module_sha256','src/mudroom-roof.js'),('source_fitter_sha256','scripts/fit_mudroom_joinery.py'),('source_model_sha256','src/model-data.json')]:
    assert fit[key]==hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),key+' is stale'
layout=json.loads(subprocess.check_output([NODE,'-e',"process.stdout.write(JSON.stringify(require('./src/mudroom.js').build(require('./src/model-data.json'))))"],cwd=ROOT))
records={p['id']:p for p in layout['components']}
origin=np.asarray(layout['origin']);basis=np.asarray([layout['tangent'],[0,1,0],layout['outward']])

def solid(p):
    if not p['vertices']:
        assert not p['triangles'] and p.get('volume_m3',0)==0
        return m.Manifold()
    s=m.Manifold(m.Mesh64(np.asarray(p['vertices'],dtype=float),np.asarray(p['triangles'],dtype=np.uint64))).set_tolerance(1e-10)
    assert str(s.status())=='Error.NoError' and s.volume()>0,p.get('id','mesh')
    return s

def overlaps(a,b):
    aa=a.bounding_box();bb=b.bounding_box()
    return all(aa[k+3]>bb[k]+1e-10 and bb[k+3]>aa[k]+1e-10 for k in range(3))

solids={pid:solid(p) for pid,p in records.items()}
for pid,s in solids.items():
    assert len(s.decompose())==1,pid+' is disconnected'
for pid,p in fit['parts'].items():
    assert inspect_mesh(np.asarray(p['vertices']),np.asarray(p['triangles']),require_single=True)['status']=='PASS',pid+' raw mesh'
    stock=solid(p['joineryStock']);cavity=solid(p['joineryCavity']['removed']);removed=stock-solids[pid]
    assert (removed-cavity).volume()<TOL and (cavity-removed).volume()<TOL,pid+' cavity differs from removed stock'
    assert (solids[pid]-stock).volume()<TOL,pid+' exceeds its joint stock'
    mates=set()
    for joint in fit['joints']:
        if joint['id'] not in p['joineryJointIds']:continue
        mates.add(joint['receiver'] if joint['donor']==pid else joint['donor'])
        if joint.get('peg_id'):mates.add(joint['peg_id'])
    # Adjacent joints can share the same receiver stock: the last birdsmouth
    # also bears on the flush header shoulder/pegs within the side-beam corner.
    # Include every actual contacting occupant, rather than treating a logical
    # pair label as a restriction on which member may fill the physical cavity.
    if not cavity.is_empty():mates.update(other for other,s in solids.items() if other!=pid and overlaps(cavity,s))
    filled=sum((cavity^solids[other]).volume() for other in mates)
    assert abs(cavity.volume()-filled)<TOL,(pid,'unfilled cavity',cavity.volume()-filled)

pair_checks=0
for (aid,a),(bid,b) in itertools.combinations(solids.items(),2):
    if overlaps(a,b):
        assert (a^b).volume()<TOL,(aid,bid,'occupied overlap')
        pair_checks+=1

# Each face prism is the exact continuous translation of that boundary face.
# Union with the initial solid proves the whole path, without discrete samples
# or the empty-space overestimate produced by a convex hull of an entire part.
def swept(s,delta):
    mesh=s.to_mesh64();vertices=np.asarray(mesh.vert_properties)[:,:3]
    triangles=vertices[np.asarray(mesh.tri_verts)];delta=np.asarray(delta)
    normals=np.cross(triangles[:,1]-triangles[:,0],triangles[:,2]-triangles[:,0])
    forward=triangles[normals@delta>1e-14]
    cells=[s]
    cells.extend(m.Manifold.hull_points(np.vstack([face,face+delta])) for face in forward)
    return m.Manifold.batch_boolean(cells,m.OpType.Add)

motion_cache={};motion_checks=0
for joint in fit['joints']:
    moving=joint.get('assembly_member',joint['donor'])
    fixed=joint['donor'] if moving==joint['receiver'] else joint['receiver']
    delta=-np.asarray(joint['insertion_direction_world'])*.15
    key=(moving,tuple(delta))
    if key not in motion_cache:motion_cache[key]=swept(solids[moving],delta)
    assert (motion_cache[key]^solids[fixed]).volume()<TOL,(joint['id'],'continuous withdrawal/insertion blocked')
    motion_checks+=1

# Verify the six braces against both receivers simultaneously in their single
# normal-to-frame insertion direction. All pegs are fitted after insertion.
braces=[p for p in records.values() if p['id'].startswith('MUD-BRACE-')]
assert len(braces)==6
for p in braces:
    pid=p['id'];vertices=(np.asarray(p['joineryStock']['vertices'])-origin)@basis.T
    axis=0 if '-SIDE-' in pid else 2
    assert abs(np.ptp(vertices[:,axis])-.0508)<1e-9,pid+' must be full 2-inch stock'
    run_axis=2 if axis==0 else 0
    sign=(1 if pid.endswith('BACK') else -1) if axis==0 else (1 if pid.endswith('L') else -1)
    perp=np.zeros(3);perp[1]=sign/np.sqrt(2);perp[run_axis]=-1/np.sqrt(2)
    assert abs(np.ptp(vertices@perp)-.1524)<1e-9,pid+' must be full 6-inch stock'
    joints=[j for j in fit['joints'] if j['donor']==pid]
    assert len(joints)==2 and joints[0]['insertion_direction_world']==joints[1]['insertion_direction_world']
    # TIMESTAMP START 2026-11-03T07:32:15-05:00 | REVISION R004924
    # Filled cavities alone miss an open wedge outside both original stocks.
    # Require complete plumb/level end faces, wholly inside receiver profiles.
    post=next(records[j['receiver']] for j in joints if records[j['receiver']]['id'].startswith('MUD-POST-'))
    beam=next(records[j['receiver']] for j in joints if not records[j['receiver']]['id'].startswith('MUD-POST-'))
    post_v=(np.asarray(post['joineryStock']['vertices'])-origin)@basis.T
    beam_v=(np.asarray(beam['joineryStock']['vertices'])-origin)@basis.T
    foot=(post_v[:,run_axis].max() if sign>0 else post_v[:,run_axis].min())-sign*.0254
    head=beam_v[:,1].min()+.0254
    for dimension,value,receiver_v in [(run_axis,foot,post_v),(1,head,beam_v)]:
        cap=[tri for tri in p['joineryStock']['triangles'] if np.all(np.abs(vertices[tri,dimension]-value)<1e-8)]
        area=sum(np.linalg.norm(np.cross(vertices[t[1]]-vertices[t[0]],vertices[t[2]]-vertices[t[0]]))/2 for t in cap)
        assert abs(area-2*6*np.sqrt(2)*.0254**2)<1e-9,(pid,'incomplete nested end face',dimension,area)
        cap_v=vertices[sorted({i for tri in cap for i in tri})]
        assert np.all(cap_v>=receiver_v.min(0)-1e-8) and np.all(cap_v<=receiver_v.max(0)+1e-8),(pid,'end extends outside its receiver')
    # TIMESTAMP END 2026-11-03T07:32:15-05:00 | REVISION R004924
    receivers=solids[joints[0]['receiver']]+solids[joints[1]['receiver']]
    travel=swept(solids[pid],-np.asarray(joints[0]['insertion_direction_world'])*.15)
    assert (travel^receivers).volume()<TOL,pid+' cannot enter both face housings'
    for other,record in records.items():
        if other==pid or other.startswith('MUD-PEG-') or record.get('mudroomRoof'):continue
        if overlaps(travel,solids[other]):assert (travel^solids[other]).volume()<TOL,(pid,other,'brace entry hits assembled porch')
    motion_checks+=1

# Paired rafters lower vertically together after apex assembly. The ties also
# enter open-top seats vertically; held-out pegs cannot obstruct those motions.
roof_fixed=[solids[p] for p in solids if p.startswith('MUD-PLATE-') or p.startswith('MUD-ROOF-TIE-') or p=='MUD-HEADER-FRONT']
fixed=m.Manifold.batch_boolean(roof_fixed,m.OpType.Add)
for k in range(5):
    pair=solids['MUD-RAFTER-L-'+str(k)]+solids['MUD-RAFTER-R-'+str(k)]
    assert (swept(pair,[0,.2,0])^fixed).volume()<TOL,('rafter pair',k,'cannot lower to seats')
    motion_checks+=1

# Cutaway removes apex/tie pegs with the roof. Post, guard and knee-brace pegs
# remain with the visible frame; no detached roof fastening is left floating.
roof_peg_count=0
for joint in fit['joints']:
    if not joint.get('peg_id'):continue
    peg=records[joint['peg_id']]
    expected=joint['family'] in ['pegged apex half lap','open top cross half lap']
    assert bool(peg.get('mudroomRoof'))==expected and bool(peg.get('mudroomScreen'))==expected,joint['id']+' cutaway peg visibility'
    roof_peg_count+=expected
assert roof_peg_count==13
assert fit['verification']['capacity_verified'] is False
assert len(fit['assembly'])==5
print(f'PASS: {len(solids)} porch solids; {len(fit["parts"])} exact filled cavities; {pair_checks} final-solid intersections; {motion_checks} continuous insertion checks; six actual 2×6 braces; 13 roof pegs follow cutaway. Capacity and erection engineering remain unverified.')
# TIMESTAMP END 2026-11-02T15:00:19-05:00 | REVISION R004797
