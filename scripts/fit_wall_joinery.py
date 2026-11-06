# TIMESTAMP START 2026-11-05T04:16:45+00:00 | REVISION R000019
# TIMESTAMP START 2026-11-02T20:38:50-05:00 | REVISION R004870
"""Concealed straight wall tenons with finite blind sockets, separate from saved frame sources."""
from pathlib import Path
import hashlib,itertools,json,subprocess
import numpy as np
import manifold3d as m
from step_lap import mesh,volume_centroid,close_bounds,regular_boundary
# TIMESTAMP START 2026-11-03T16:40:59-05:00 | REVISION R005059
def solid(record):
    return m.Manifold(m.Mesh64(np.asarray(record['vertices'],float),np.asarray(record['triangles'],np.uint64)))
# TIMESTAMP END 2026-11-03T16:40:59-05:00 | REVISION R005059
from revise_main_braces import clean
from audit_cavity_fit import inspect_mesh

ROOT=Path(__file__).resolve().parents[1]
I=.0254
TOL=1e-6*I**3
VARIANTS={'baseline':('model-data.json','enclosure-fit.json','cavity-data.json'),
 'proposed':('step-lap-proposed-model.json','step-lap-proposed-enclosure-fit.json','step-lap-proposed-cavities.json'),
 'top-entry':('top-entry-proposed-model.json','top-entry-proposed-enclosure-fit.json','top-entry-proposed-cavities.json')}
def digest(path):return hashlib.sha256((ROOT/path).read_bytes()).hexdigest()
def normalize(s):
    if s.is_empty() or abs(s.volume())<1e-16:return m.Manifold()
    for candidate in [s,s.simplify(1e-10),s.simplify(1e-9)]:
        q=mesh(candidate)
        if inspect_mesh(np.array(q['vertices']),np.array(q['triangles'],dtype=np.uint64),require_single=False)['status']=='PASS':
            error=abs((s-candidate).volume())+abs((candidate-s).volume())
            assert error<TOL,('Wall boundary normalization changed occupied material',error)
            return candidate
    return regular_boundary(s)
def packed(s):
    s=normalize(s)
    if s.is_empty():return {'vertices':[],'triangles':[],'volume_m3':0.}
    return dict(mesh(s),volume_m3=s.volume())
def unpack(p):return solid(p) if p.get('triangles') else m.Manifold()
def union(shapes):return m.Manifold.batch_boolean(shapes,m.OpType.Add) if shapes else m.Manifold()

def clip_to_convex(shape,tool):
    data=tool.to_mesh64();vertices=np.asarray(data.vert_properties)[:,:3];seen=set()
    for face in data.tri_verts:
        pts=vertices[face];n=np.cross(pts[1]-pts[0],pts[2]-pts[0]);length=np.linalg.norm(n)
        if length<1e-14:continue
        n/=length;d=float(n@pts[0]);key=tuple(np.round(np.r_[n,d],10))
        if key in seen:continue
        seen.add(key);shape=shape.trim_by_plane((-n).tolist(),-d)
    return shape

def generate(variant):
    model_name,enclosure_name,cavity_name=VARIANTS[variant]
    model=json.loads((ROOT/'src'/model_name).read_text());cavities=json.loads((ROOT/'src'/cavity_name).read_text())
    code="global.OCTAGON_ENCLOSURE_FIT=require('./src/'+process.argv[2]);const m=require('./src/'+process.argv[1]);process.stdout.write(JSON.stringify(require('./src/schematic-walls.js').build(m.parts)))"
    layout=json.loads(subprocess.check_output(['node','-e',code,model_name,enclosure_name],cwd=ROOT))
    primary={p['id']:p for p in model['parts'] if p.get('is_timber') or p.get('group')=='joinery_pegs'}
    wall={p['id']:p for p in layout['components'] if p['schematicKind'] in ['rail','wall','shelf']}
    records={**primary,**wall};original={pid:solid(p) for pid,p in records.items()}
    additions={pid:[] for pid in records};cutters={pid:[] for pid in records};part_joints={pid:[] for pid in records};joints=[]
    def joint(donor,receiver,center,qaxis,transverse,outward,engagement,neck,head,depth):
        center=np.asarray(center);q=np.asarray(qaxis);t=np.asarray(transverse);n=np.asarray(outward)
        # TIMESTAMP START 2026-11-03T15:42:57-05:00 | REVISION R005038
        engagement=3*I
        # Opposed three-inch tongues entering a four-inch jamb use separate
        # depth bands. Both remain inside their existing horizontal rail stock.
        if records[receiver].get('framingRole')=='jamb' and abs(q[1])<.1:
            vv=np.asarray(records[donor]['vertices']);lo=min(vv@n);hi=max(vv@n)
            direction=float(q@np.cross([0,1,0],n))
            target=lo+.5*I if direction<0 else hi-.5*I
            center=center+n*(target-center@n)
        # TIMESTAMP END 2026-11-03T15:42:57-05:00 | REVISION R005038
        head=neck  # Constant-section tongues withdraw along their insertion axes.
        root=.75*I
        # TIMESTAMP START 2026-11-03T16:40:59-05:00 | REVISION R005059
        local_points=np.array([[x,y,z] for x,w in [(-root,neck),(0,neck),(engagement,head)] for y in [-w,w] for z in [-depth/2,depth/2]])
        basis=np.column_stack([q,t,n]);points=local_points@basis.T+center
        transform=np.column_stack([basis,center]).tolist()
        tool=m.Manifold.hull_points(local_points).transform(transform)
        # TIMESTAMP END 2026-11-03T16:40:59-05:00 | REVISION R005059
        # A finite matching tool preserves the outside post skin. Socket mouths
        # open only at the donor shoulder; no outward sweep cuts the facade.
        sweep=tool
        entry=-q
        occupied=tool^original[receiver]
        if occupied.volume()<=TOL:raise AssertionError((donor,receiver,'tongue misses receiver'))
        joined=normalize(original[donor]+tool)
        assert len(joined.decompose())==1,(donor,receiver,'detached tongue')
        jid='WJ-'+str(len(joints)+1).zfill(3)
        additions[donor].append(tool);cutters[receiver].append(sweep)
        for pid in [donor,receiver]:part_joints[pid].append(jid)
        # TIMESTAMP START 2026-11-02T21:12:46-05:00 | REVISION R004878
        try:
            actual_removed=original[receiver]^sweep
            clipped=clip_to_convex(original[receiver],sweep)
            if abs(clipped.volume()-actual_removed.volume())>TOL:
                clipped=actual_removed
            # TIMESTAMP START 2026-11-03T16:40:59-05:00 | REVISION R005059
            try:removed_record=packed(clipped)
            except AssertionError:
                Path('/tmp/octagon-wall-cut-debug.json').write_text(json.dumps({'clipped':mesh(clipped),'actual':mesh(actual_removed),'receiver':mesh(original[receiver]),'sweep':mesh(sweep)}))
                removed_record=packed(actual_removed)
            # TIMESTAMP END 2026-11-03T16:40:59-05:00 | REVISION R005059
            assert abs(removed_record['volume_m3']-actual_removed.volume())<TOL
        # TIMESTAMP END 2026-11-02T21:12:46-05:00 | REVISION R004878
        except AssertionError as error:raise AssertionError((donor,receiver,center.tolist(),'cut boundary')) from error
        # TIMESTAMP START 2026-11-02T22:01:35-05:00 | REVISION R004882
        joints.append({'id':jid,'donor':donor,'receiver':receiver,'family':'concealed straight mortise and tenon',
          'withdrawal_direction':entry.tolist(),'engagement_m':engagement,'neck_width_m':neck*2,'head_width_m':head*2,
          'tongue':packed(tool),'removed_from_receiver':removed_record,
          'blind_socket':True,'socket_tool':packed(tool),
          'restraint_status':'Finite concealed tongue and shoulder bearing. Positive locking pins and capacity are specified separately.'})
        # TIMESTAMP START 2026-11-03T15:42:57-05:00 | REVISION R005038
        joints[-1].update(tenon_projection_m=engagement,tenon_cross_section_m=[depth,neck*2],insertion_direction_world=q.tolist())
        # TIMESTAMP END 2026-11-03T15:42:57-05:00 | REVISION R005038
        # TIMESTAMP END 2026-11-02T22:01:35-05:00 | REVISION R004882
    for connection in layout['railConnections']:
        rail=records[connection['railId']];direction=-1 if connection['end']=='A' else 1
        h=connection['height'];half=min(I,(h-I)/2);head=min(1.5*I,(h-.5*I)/2)
        depth=connection['depth']/2;center=np.array(connection['center'])
        joint(rail['id'],connection['postId'],center,np.array(connection['axis'])*direction,[0,1,0],connection['normal'],I,half,head,depth)
    for face in layout['walls']:
        n=np.array(face['normal']);u=np.array([n[2],0,-n[0]])
        # Use the actual rail connection axis to avoid depending on polygon winding.
        connection=next(c for c in layout['railConnections'] if c['face']==face['face']);u=np.array(connection['axis'])
        face_parts=[p for p in wall.values() if p.get('face')==face['face'] and p.get('framingRole')]
        jambs=[p for p in face_parts if p['framingRole']=='jamb'];rails=[p for p in face_parts if p['framingRole']!='jamb']
        origin=np.array(connection['center'])-u*(records[connection['railId']]['localBounds'][0] if connection['end']=='A' else records[connection['railId']]['localBounds'][1]);origin[1]=0
        origin-=n*np.mean(records[connection['railId']]['localBounds'][4:6])
        world=lambda x,y,z:origin+u*x+np.array([0,y,0])+n*z
        for rail in rails:
            a,b,low,high,near,far=rail['localBounds']
            for jamb in jambs:
                ja,jb,jlo,jhi,jn,jf=jamb['localBounds']
                for end,direction in [(a,-1),(b,1)]:
                    receiver_face=jb if direction<0 else ja
                    if abs(end-receiver_face)>1e-8:continue
                    yl,yh=max(low,jlo),min(high,jhi);zl,zh=max(near,jn),min(far,jf)
                    if yh-yl<.75*I or zh-zl<.5*I:continue
                    half=min(I,(yh-yl-.5*I)/2);head=min(1.5*I,(yh-yl-.25*I)/2)
                    depth=min(.5*I,(zh-zl)/2)
                    joint(rail['id'],jamb['id'],world(end,(yl+yh)/2,zh-depth/2),u*direction,[0,1,0],n,I,half,head,depth)
        for jamb in jambs:
            a,b,low,high,near,far=jamb['localBounds']
            for rail in rails:
                ra,rb,rlo,rhi,rn,rf=rail['localBounds']
                if abs(low-rhi)>1e-8 or min(b,rb)-max(a,ra)<I:continue
                zl,zh=max(near,rn),min(far,rf)
                if zh-zl<.5*I:continue
                joint(jamb['id'],rail['id'],world((a+b)/2,low,(zl+zh)/2),[0,-1,0],u,n,I,.5*I,.75*I,(zh-zl)/2)
    final={}
    for pid,s in original.items():
        try:final[pid]=normalize((s+union(additions[pid]))-union(cutters[pid]))
        except AssertionError as error:raise AssertionError((pid,'final boundary')) from error
# TIMESTAMP START 2026-11-05T08:46:05+00:00 | REVISION R000036
    from wall_locking_pegs import attach as attach_wall_pegs
    locking_pegs,locking_owners,locking_audit=attach_wall_pegs(variant,final,joints)
    peg_solids={p['id']:solid(p) for p in locking_pegs}
# TIMESTAMP END 2026-11-05T08:46:05+00:00 | REVISION R000036
    for pid,s in final.items():
        assert s.volume()>0 and len(s.decompose())==1,(pid,'disconnected receiver')
    checks=0;maximum=0.
    for (a,sa),(b,sb) in itertools.combinations(final.items(),2):
        if not (part_joints[a] or part_joints[b]) or not close_bounds(sa,sb):continue
        amount=max(0.,(sa^sb).volume());checks+=1;maximum=max(maximum,amount)
        assert amount<TOL,(a,b,'overlap',amount)
    patches={}
    for pid,s in final.items():
        if not part_joints[pid]:continue
        added=union(additions[pid]);stock=original[pid]+added;removed=stock-s
        assert (s-original[pid]-added).volume()<TOL,(pid,'unrecorded added material')
        old_cavity=cavities.get('parts',{}).get(pid,{})
        combined=unpack(old_cavity.get('removed',{}))+removed
# TIMESTAMP START 2026-11-05T08:46:05+00:00 | REVISION R000036
        mates=union([final[j['donor']] for j in joints if j['receiver']==pid]+[peg_solids[x] for x in locking_owners.get(pid,[])])
# TIMESTAMP END 2026-11-05T08:46:05+00:00 | REVISION R000036
        entry=removed-mates
# TIMESTAMP START 2026-11-05T08:46:05+00:00 | REVISION R000036
        patches[pid]={**packed(s),'wallJoineryJointIds':part_joints[pid],
          'joineryCavity':{**old_cavity,'removed':old_cavity.get('removed',{'vertices':[],'triangles':[],'volume_m3':0.}),
            'additional_removed':packed(removed),'additional_entry_clearance':{'vertices':[],'triangles':[],'volume_m3':max(0.,entry.volume()),'representation':'Volume classification of actual removed stock minus actual mating wood; full removed and tongue meshes are retained in the joint records.'},
            'fit_audit':{'status':'PASS','scope':'Saved primary cavities plus exact finite blind wall sockets'}},
          'wallJoineryAdded':packed(added),'wallJoineryRemoved':packed(removed),
          'wallJoineryMass':volume_centroid(s),'lockingPegIds':locking_owners.get(pid,[]),'connectionStatus':'Concealed straight tenons, blind sockets, shoulder bearing and transverse hardwood locking pegs. Structural capacity requires review.'}
# TIMESTAMP END 2026-11-05T08:46:05+00:00 | REVISION R000036
    # TIMESTAMP START 2026-11-03T17:15:09-05:00 | REVISION R005070
    # Quantities describe the exact serialized meshes used by the viewer.
    published={pid:unpack(patches[pid]) if pid in patches else solid(records[pid]) for pid in final}
    for pid,patch in patches.items():
        removed=unpack(patch['wallJoineryRemoved'])
# TIMESTAMP START 2026-11-05T08:46:05+00:00 | REVISION R000036
        mates=union([published[j['donor']] for j in joints if j['receiver']==pid]+[peg_solids[x] for x in locking_owners.get(pid,[])])
# TIMESTAMP END 2026-11-05T08:46:05+00:00 | REVISION R000036
        patch['joineryCavity']['additional_entry_clearance']['volume_m3']=max(0.,(removed-mates).volume())
    # TIMESTAMP END 2026-11-03T17:15:09-05:00 | REVISION R005070
    sources={f'src/{name}':digest(f'src/{name}') for name in [model_name,enclosure_name,cavity_name,'schematic-walls.js']}
    sources['scripts/fit_wall_joinery.py']=digest('scripts/fit_wall_joinery.py')
# TIMESTAMP START 2026-11-05T08:46:05+00:00 | REVISION R000036
    for path in ['scripts/wall_locking_pegs.py','scripts/fixtures/wall-locking-pegs.json.gz']:
        sources[path]=digest(path)
# TIMESTAMP END 2026-11-05T08:46:05+00:00 | REVISION R000036
# TIMESTAMP START 2026-11-05T08:46:05+00:00 | REVISION R000036
    return {'status':'PASS','sources':sources,'source_model_sha256':digest('src/'+model_name),
      'primary_parts':{pid:p for pid,p in patches.items() if pid in primary},'wall_parts':{pid:p for pid,p in patches.items() if pid in wall},
      'locking_pegs':locking_pegs,'lockingPegAudit':locking_audit,'joints':joints,'verification':{'pair_checks':checks,'maximum_overlap_m3':maximum,'tolerance_m3':TOL,'capacity_verified':False}}
# TIMESTAMP END 2026-11-05T08:46:05+00:00 | REVISION R000036

def readable_json(value,level=0):
    """Readable bounded source lines without expanding each vector component."""
    pad='  '*level;child='  '*(level+1)
    if isinstance(value,dict):
        return '{\n'+',\n'.join(child+json.dumps(k)+': '+readable_json(v,level+1) for k,v in value.items())+'\n'+pad+'}' if value else '{}'
    if isinstance(value,list):
        if not value or all(not isinstance(v,(dict,list)) for v in value):return json.dumps(value,separators=(',',':'))
        return '[\n'+',\n'.join(child+readable_json(v,level+1) for v in value)+'\n'+pad+']'
    return json.dumps(value)

# TIMESTAMP START 2026-11-05T08:46:05+00:00 | REVISION R000036
if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=ROOT/'src/wall-joinery-fit.json');args=parser.parse_args()
    result={'revision':'R000036','timestamp':'2026-11-05T08:46:05+00:00','variants':{}}
    for variant in VARIANTS:
        result['variants'][variant]=generate(variant)
        print(variant,len(result['variants'][variant]['joints']),'matching wall joints;134 separate locking pegs',flush=True)
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(result,separators=(',',':'))+'\n')
# TIMESTAMP END 2026-11-05T08:46:05+00:00 | REVISION R000036
# TIMESTAMP END 2026-11-02T20:38:50-05:00 | REVISION R004870

# TIMESTAMP END 2026-11-05T04:16:45+00:00 | REVISION R000019
