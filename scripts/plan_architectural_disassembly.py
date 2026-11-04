# TIMESTAMP START 2026-11-02T15:51:57-05:00 | REVISION R004809
"""Exact translational collision checks for the complete physical assembly.

Translations retain every parked solid. Boundary-triangle prisms cover the
continuous sweep without filling a concave member's mortises with a full hull.
This is a geometric disassembly proposal, not a structural demolition plan.
"""
from dataclasses import dataclass, field
from pathlib import Path
import argparse, hashlib, json, os, shutil, subprocess
import itertools
import numpy as np
import manifold3d as m

ROOT=Path(__file__).resolve().parents[1]
NODE=os.environ.get('NODE') or shutil.which('node') or '/Users/stewartlundy/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node'
VARIANTS={'baseline':('model-data.json','enclosure-fit.json'),'proposed':('step-lap-proposed-model.json','step-lap-proposed-enclosure-fit.json'),'top-entry':('top-entry-proposed-model.json','top-entry-proposed-enclosure-fit.json')}
VOLUME_TOLERANCE_M3=1e-6*.0254**3
PRISM_DISCARD_M3=1e-14
BOX_TOLERANCE_M=0.
# TIMESTAMP START 2026-11-02T20:38:50-05:00 | REVISION R004870
NODE_SCENE="""const base=require('./src/'+process.argv[1]);
const variant=process.argv[1].startsWith('top-entry')?'top-entry':process.argv[1].startsWith('step-lap')?'proposed':'baseline';
const W=require('./src/wall-joinery.js'),fit=require('./src/wall-joinery-fit.json').variants[variant],model=W.applyModel(base,fit);
global.OCTAGON_ENCLOSURE_FIT=require('./src/'+process.argv[2]);
const parts=[...model.parts,...require('./src/roof-coverings.js').build(model).components,
 ...require('./src/floor-foundation.js').roomLayout(model,W.applyLayout(require('./src/schematic-walls.js').build(model.parts),fit),require('./src/floor-foundation-solids.json')).components,
 ...require('./src/mudroom.js').build(model).components];
const roles=require('./src/display-presets.js');
process.stdout.write(JSON.stringify({parts:parts.filter(p=>roles.included(p,'complete')),
 excluded:parts.filter(p=>!roles.included(p,'complete')).map(p=>({id:p.id,reason:roles.role(p),physical:false}))}));"""
# TIMESTAMP END 2026-11-02T20:38:50-05:00 | REVISION R004870

@dataclass
class Scene:
    variant: str
    parts: dict
    solids: dict
    offsets: dict
    sources: dict=field(default_factory=dict)
    excluded: list=field(default_factory=list)
    version: int=0
    stages: list=field(default_factory=list)

    def current(self,pid):
        return self.solids[pid].translate(self.offsets[pid].tolist())

def load_scene(variant='baseline'):
    model,enclosure=VARIANTS[variant]
    fitted=json.loads((ROOT/'src'/enclosure).read_text())
    for key,source in [('source_model_sha256',model),('source_module_sha256','schematic-walls.js'),('source_foundation_sha256','floor-foundation-solids.json')]:
        assert fitted[key]==hashlib.sha256((ROOT/'src'/source).read_bytes()).hexdigest(),enclosure+' is stale for '+source
    raw=json.loads(subprocess.check_output([NODE,'-e',NODE_SCENE,model,enclosure],cwd=ROOT))
    parts={p['id']:p for p in raw['parts']}
    assert len(parts)==len(raw['parts']),'Physical scene has duplicate identifiers'
    solids={}
    for pid,p in parts.items():
        s=m.Manifold(m.Mesh64(np.asarray(p['vertices'],dtype=float),np.asarray(p['triangles'],dtype=np.uint64)))
        assert str(s.status())=='Error.NoError' and s.volume()>0,(pid,str(s.status()),s.volume())
        solids[pid]=s
    files=[model,enclosure,'wall-joinery-fit.json','wall-joinery.js','floor-foundation-solids.json','mudroom-joinery-fit.json','mudroom.js','mudroom-roof.js','roof-coverings.js','floor-foundation.js','schematic-walls.js','display-presets.js']
    sources={'src/'+name:hashlib.sha256((ROOT/'src'/name).read_bytes()).hexdigest() for name in files}
    return Scene(variant,parts,solids,{pid:np.zeros(3) for pid in parts},sources,raw['excluded'])

def boxes_overlap(a,b):
    return all(a[i+3]>b[i]+BOX_TOLERANCE_M and b[i+3]>a[i]+BOX_TOLERANCE_M for i in range(3))

def audit_initial_scene(scene):
    boxes={pid:s.bounding_box() for pid,s in scene.solids.items()};collisions=[];checks=0;maximum=0.
    for a,b in itertools.combinations(scene.parts,2):
        if not boxes_overlap(boxes[a],boxes[b]):continue
        volume=(scene.solids[a]^scene.solids[b]).volume();checks+=1;maximum=max(maximum,volume)
        if volume>VOLUME_TOLERANCE_M3:collisions.append({'a':a,'b':b,'overlap_m3':volume})
    return {'status':'BLOCKED' if collisions else 'PASS','physical_piece_count':len(scene.parts),'pair_checks':checks,'maximum_intersection_m3':maximum,'collisions':collisions,'overlap_tolerance_m3':VOLUME_TOLERANCE_M3}

def triangle_prism(triangle,delta):
    """Affine image of a unit prism, without an ill-conditioned world hull.

    The six corners and eight outward faces are known analytically. A skinny
    boundary triangle may have a substantial swept volume even when a hull
    implementation merges its nearby corners; the unit construction avoids
    that hull tolerance entirely.
    """
    triangle=np.asarray(triangle,float);delta=np.asarray(delta,float)
    matrix=np.column_stack([triangle[1]-triangle[0],triangle[2]-triangle[0],delta,triangle[0]])
    vertices=np.array([[0,0,0],[1,0,0],[0,1,0],[0,0,1],[1,0,1],[0,1,1]],float)
    faces=np.array([[0,2,1],[3,4,5],[0,1,4],[0,4,3],[1,2,5],[1,5,4],[2,0,3],[2,3,5]],np.uint64)
    prism=m.Manifold(m.Mesh64(vertices,faces)).transform(matrix.tolist())
    expected=abs(float(np.linalg.det(matrix[:,:3])))/2
    assert str(prism.status())=='Error.NoError' and prism.volume()>0,('Explicit swept prism failed',expected,prism.volume())
    # World-coordinate summation can lose relative accuracy for a prism only
    # a few femtolitres large. Its absolute residual is accounted against the
    # unchanged physical overlap tolerance by sweep_cover, never ignored.
    assert abs(prism.volume()-expected)<=VOLUME_TOLERANCE_M3/100,('Swept prism volume mismatch',expected,prism.volume())
    return prism

def sweep_cover(shape,delta):
    """Return an occupied sweep and numerical accounting for one translation."""
    delta=np.asarray(delta,dtype=float)
    assert delta.shape==(3,) and np.isfinite(delta).all()
    if np.linalg.norm(delta)<1e-14:
        return shape,{'method':'stationary','discarded_prism_volume_m3':0.,'triangle_prism_count':0}
    # Convex connected components admit the exact hull shortcut independently.
    # A concave member is never replaced with the convex hull of its full stock.
    pieces=shape.decompose();convex=[];all_convex=True
    for piece in pieces:
        v=np.asarray(piece.to_mesh64().vert_properties)[:,:3]
        hull=m.Manifold.hull_points(v)
        if abs(hull.volume()-piece.volume())>1e-13:
            all_convex=False;break
        convex.append(m.Manifold.hull_points(np.vstack([v,v+delta])))
    if all_convex:
        cover=m.Manifold.batch_boolean(convex,m.OpType.Add)
        return cover,{'method':'exact convex-component extrusion','discarded_prism_volume_m3':0.,'triangle_prism_count':0}
    mesh=shape.to_mesh64();vertices=np.asarray(mesh.vert_properties)[:,:3]
    prisms=[shape,shape.translate(delta.tolist())];discarded=0.;numeric=0.;count=0
    for indices in np.asarray(mesh.tri_verts):
        triangle=vertices[indices]
        volume=abs(float(np.dot(np.cross(triangle[1]-triangle[0],triangle[2]-triangle[0]),delta)))/2
        if volume<=PRISM_DISCARD_M3:
            discarded+=volume;continue
        prism=triangle_prism(triangle,delta)
        numeric+=abs(prism.volume()-volume)
        prisms.append(prism);count+=1
    cover=m.Manifold.batch_boolean(prisms,m.OpType.Add)
    assert str(cover.status())=='Error.NoError' and cover.volume()>0,'Continuous sweep union failed'
    return cover,{'method':'solid plus exact boundary-triangle prisms','discarded_prism_volume_m3':discarded+numeric,'omitted_prism_volume_m3':discarded,'numerical_prism_volume_residual_m3':numeric,'triangle_prism_count':count}

def check_stage(scene,member_ids,delta,stop_first=False):
    ids=list(member_ids);delta=np.asarray(delta,dtype=float)
    assert ids and len(ids)==len(set(ids)) and all(pid in scene.parts for pid in ids)
    assert delta.shape==(3,) and np.isfinite(delta).all() and np.linalg.norm(delta)>0
    moving=set(ids);obstacles={pid:scene.current(pid) for pid in scene.parts if pid not in moving}
    bounds={pid:s.bounding_box() for pid,s in obstacles.items()}
    collisions=[];checks=0;discarded=0.;prisms=0;methods=set();maximum=0.
    for pid in ids:
        shape=scene.current(pid);a=np.array(shape.bounding_box());b=a+np.r_[delta,delta]
        broad=np.r_[np.minimum(a[:3],b[:3]),np.maximum(a[3:],b[3:])]
        candidates=[other for other,box in bounds.items() if boxes_overlap(broad,box)]
        if not candidates:continue
        sweep,account=sweep_cover(shape,delta);discarded+=account['discarded_prism_volume_m3'];prisms+=account['triangle_prism_count'];methods.add(account['method'])
        for other in candidates:
            volume=(sweep^obstacles[other]).volume();checks+=1;maximum=max(maximum,volume)
            error_bound=account['discarded_prism_volume_m3']
            if volume+error_bound>VOLUME_TOLERANCE_M3:
                collisions.append({'moving_id':pid,'obstacle_id':other,'overlap_m3':volume,'omitted_sweep_volume_bound_m3':error_bound,'obstacle_parked':bool(np.linalg.norm(scene.offsets[other])>1e-12)})
                if stop_first:break
        if collisions and stop_first:break
    assert discarded<VOLUME_TOLERANCE_M3,'Accumulated omitted sweep volume exceeds the collision tolerance'
    return {'status':'BLOCKED' if collisions else 'PASS','scene_version':scene.version,'member_ids':ids,'delta_m':delta.tolist(),'collisions':collisions,'continuous_pair_checks':checks,'maximum_intersection_m3':maximum,'overlap_tolerance_m3':VOLUME_TOLERANCE_M3,'discarded_sweep_prism_volume_m3':discarded,'triangle_prism_count':prisms,'methods':sorted(methods),'parked_pieces_checked':True}

def apply_stage(scene,member_ids,delta,proof=None,label=None,stage_id=None):
    ids=list(member_ids);delta=np.asarray(delta,dtype=float)
    proof=proof or check_stage(scene,ids,delta)
    assert proof['scene_version']==scene.version and proof['member_ids']==ids and proof['delta_m']==delta.tolist(),'Proof does not match this scene state/motion'
    assert proof['status']=='PASS',proof.get('collisions')
    stage={'id':stage_id or 'stage-'+str(scene.version+1).zfill(4),'label':label or 'Withdraw '+', '.join(ids),'member_ids':ids,'delta_m':delta.tolist(),'proof':proof}
    for pid in ids:scene.offsets[pid]=scene.offsets[pid]+delta
    scene.stages.append(stage);scene.version+=1
    return stage

def check_multi_stage(scene,motions,stop_first=False):
    """Check simultaneous groups using relative continuous motion for each pair."""
    normalized=[{'member_ids':list(q['member_ids']),'delta_m':np.asarray(q['delta_m'],float).tolist()} for q in motions]
    all_ids=[pid for q in normalized for pid in q['member_ids']]
    assert all_ids and len(all_ids)==len(set(all_ids)) and all(pid in scene.parts for pid in all_ids)
    assert all(len(q['delta_m'])==3 and np.isfinite(q['delta_m']).all() for q in normalized)
    moving=set(all_ids);obstacles={pid:scene.current(pid) for pid in scene.parts if pid not in moving}
    current={pid:scene.current(pid) for pid in all_ids};collisions=[];cache={};checks=0;maximum=0.
    def against(pid,delta,other,target,relative=False):
        nonlocal checks,maximum
        shape=current[pid];delta=np.asarray(delta);a=np.array(shape.bounding_box());b=a+np.r_[delta,delta]
        broad=np.r_[np.minimum(a[:3],b[:3]),np.maximum(a[3:],b[3:])]
        if not boxes_overlap(broad,target.bounding_box()):return
        key=(pid,*delta.tolist())
        if key not in cache:cache[key]=sweep_cover(shape,delta)
        volume=(cache[key][0]^target).volume();checks+=1;maximum=max(maximum,volume)
        error_bound=cache[key][1]['discarded_prism_volume_m3']
        if volume+error_bound>VOLUME_TOLERANCE_M3:collisions.append({'moving_id':pid,'obstacle_id':other,'overlap_m3':volume,'omitted_sweep_volume_bound_m3':error_bound,'obstacle_parked':bool(np.linalg.norm(scene.offsets[other])>1e-12),'other_moving':relative})
    for q in normalized:
        for pid in q['member_ids']:
            for other,target in obstacles.items():
                against(pid,q['delta_m'],other,target)
                if collisions and stop_first:break
            if collisions and stop_first:break
        if collisions and stop_first:break
    if not(collisions and stop_first):
        for a in range(len(normalized)):
            for b in range(a+1,len(normalized)):
                qa,qb=normalized[a],normalized[b];relative=np.asarray(qa['delta_m'])-np.asarray(qb['delta_m'])
                for pid in qa['member_ids']:
                    for other in qb['member_ids']:
                        against(pid,relative,other,current[other],True)
                        if collisions and stop_first:break
                    if collisions and stop_first:break
                if collisions and stop_first:break
            if collisions and stop_first:break
    discarded=sum(q[1]['discarded_prism_volume_m3'] for q in cache.values())
    assert discarded<VOLUME_TOLERANCE_M3,'Accumulated omitted relative-sweep volume exceeds tolerance'
    return {'status':'BLOCKED' if collisions else 'PASS','scene_version':scene.version,'motions':normalized,'collisions':collisions,'continuous_pair_checks':checks,'maximum_intersection_m3':maximum,'overlap_tolerance_m3':VOLUME_TOLERANCE_M3,'discarded_sweep_prism_volume_m3':discarded,'triangle_prism_count':sum(q[1]['triangle_prism_count'] for q in cache.values()),'methods':sorted({q[1]['method'] for q in cache.values()}),'parked_pieces_checked':True,'relative_moving_pairs_checked':True}

def apply_multi_stage(scene,motions,proof=None,label=None,stage_id=None):
    normalized=[{'member_ids':list(q['member_ids']),'delta_m':np.asarray(q['delta_m'],float).tolist()} for q in motions]
    proof=proof or check_multi_stage(scene,normalized)
    assert proof['scene_version']==scene.version and proof['motions']==normalized,'Relative-motion proof is stale'
    assert proof['status']=='PASS',proof.get('collisions')
    stage={'id':stage_id or 'stage-'+str(scene.version+1).zfill(4),'label':label or 'Coordinated withdrawal','motions':normalized,'proof':proof}
    for q in normalized:
        for pid in q['member_ids']:scene.offsets[pid]=scene.offsets[pid]+np.asarray(q['delta_m'])
    scene.stages.append(stage);scene.version+=1
    return stage

def architectural_ids(scene):
    return [pid for pid,p in scene.parts.items() if pid=='PLY' or p.get('schematicKind') in ['roofCover','wall','rail','shelf','cupolaWindow','floor','floorAssembly']]

def attempt_move(scene,label,ids,delta,blocked=None):
    if not ids:return True
    proof=check_stage(scene,ids,delta,stop_first=True)
    if proof['status']=='PASS':
        apply_stage(scene,ids,delta,proof,label)
        return True
    if blocked is not None:blocked.append({'member_ids':list(ids),'label':label,'attempted_delta_m':np.asarray(delta,float).tolist(),'reason':'Occupied geometry blocks this continuous withdrawal','collisions':proof['collisions']})
    return False

def clone_scene(scene):
    return Scene(scene.variant,scene.parts,scene.solids,{pid:v.copy() for pid,v in scene.offsets.items()},dict(scene.sources),list(scene.excluded),scene.version,list(scene.stages))

def attempt_path(scene,label,ids,segments):
    trial=clone_scene(scene);pending=[]
    for index,delta in enumerate(segments):
        proof=check_stage(trial,ids,delta,stop_first=True)
        if proof['status']!='PASS':return False,proof
        stage=apply_stage(trial,ids,delta,proof,label+' · '+str(index+1));pending.append(stage)
    for stage in pending:apply_stage(scene,stage['member_ids'],stage['delta_m'],stage['proof'],stage['label'],stage['id'])
    return True,None

def roof_cover_prefix(scene):
    """Verified covering removal prerequisites; keep every cover parked in-scene."""
    blocked=[];porch=[pid for pid,p in scene.parts.items() if p.get('roofLayer')]
    if all(np.linalg.norm(scene.offsets[pid])<1e-12 for pid in porch):
        if attempt_move(scene,'Lift the porch covering clear of its rafters',porch,[0,6,0],blocked):
            attempt_move(scene,'Park the lifted porch covering beyond the entrance',porch,[-3.0614674589207183,0,-7.391036260090294],blocked)
    copper=[pid for pid in scene.parts if pid.startswith('ROOF-COPPER-')]
    attempt_move(scene,'Lift the cupola copper covering',copper,[0,6,0],blocked)
    for k in range(8):
        ids=[pid for pid,p in scene.parts.items() if pid.startswith('ROOF-CEDAR-') and p['roof_face']==k]
        if attempt_move(scene,'Lift cedar roof face '+str(k+1)+' clear of the frame',ids,[0,.3,0],blocked):
            a=-(k+.5)*np.pi/4
            attempt_move(scene,'Withdraw cedar roof face '+str(k+1)+' outward',ids,[6*np.cos(a),2,6*np.sin(a)],blocked)
    return blocked

def apply_architectural_phases(scene,include_roof=True):
    """Remove only proved loose architectural groups; preserve blocked evidence."""
    blocked=roof_cover_prefix(scene) if include_roof else []
    for k in range(8):
        ids=[pid for pid in scene.parts if pid.startswith('SCHEM-CUP-WINDOW-'+str(k)+'-')]
        angle=-(k+.5)*np.pi/4;normal=np.array([np.cos(angle),0,np.sin(angle)])
        attempt_move(scene,'Withdraw cupola window '+str(k+1)+' outward',ids,(normal*12).tolist(),blocked)
    return blocked

def apply_floor_phases(scene):
    """Clear the supported floor assembly, then release its individual members."""
    blocked=[];ids=[pid for pid,p in scene.parts.items() if p.get('schematicKind') in ['floor','floorAssembly']]
    if not attempt_move(scene,'Lower the complete floor and support assembly clear of the posts',ids,[0,-6,0],blocked):return blocked
    def radial(pid,distance):
        if pid.startswith('FLOOR-JOIST-'):
            # TIMESTAMP START 2026-11-02T21:01:13-05:00 | REVISION R004875
            east=np.array([np.sin(np.pi/8),0,np.cos(np.pi/8)])
            return east*(1 if np.asarray(scene.parts[pid]['center'])@east>=0 else -1)*distance
            # TIMESTAMP END 2026-11-02T21:01:13-05:00 | REVISION R004875
        c=np.asarray(scene.parts[pid]['center'],float).copy();c[1]=0
        if np.linalg.norm(c)<1e-8:c=np.array([np.cos(np.pi/8),0,-np.sin(np.pi/8)])
        return c/np.linalg.norm(c)*distance
    def release(pid,lift,distance):
        if not attempt_move(scene,'Lift '+pid+' out of its bearing', [pid],[0,lift,0],blocked):return False
        return attempt_move(scene,'Park '+pid+' clear of the floor assembly',[pid],radial(pid,distance),blocked)
    for pid in ids:
        if pid.startswith('SCHEM-FLOOR-SECTOR-') and not release(pid,.1,12):return blocked
    for pid in ids:
        if pid.startswith('FLOOR-BAMBOO-CENTER-') and not release(pid,.2,16):return blocked
    for pid in ids:
        if pid.startswith('POST-BEARING-STAND-') and pid.endswith('-HEAD') and not release(pid,3,22):return blocked
# TIMESTAMP START 2026-11-04T23:17:24+00:00 | REVISION R000029
    for pid in underlayment_ids(scene):
        if not attempt_move(scene,'Lift cut sheet '+pid,[pid],[0,.6,0],blocked):return blocked
    if not attempt_move(scene,'Park the cut underlayment beside the assembly',underlayment_ids(scene),[22,0,0],blocked):return blocked
# TIMESTAMP END 2026-11-04T23:17:24+00:00 | REVISION R000029
    # TIMESTAMP START 2026-11-02T21:01:13-05:00 | REVISION R004875
    east=np.array([np.sin(np.pi/8),0,np.cos(np.pi/8)])
    joists=sorted([pid for pid in ids if pid.startswith('FLOOR-JOIST-')],key=lambda pid:-abs(np.asarray(scene.parts[pid]['center'])@east))
    # TIMESTAMP END 2026-11-02T21:01:13-05:00 | REVISION R004875
    for pid in joists:
        if not release(pid,.7,12):return blocked
    for k in range(8):
        angle=-(k+.5)*np.pi/4;normal=np.array([np.cos(angle),0,np.sin(angle)]);tangent=np.array([np.sin(angle),0,-np.cos(angle)])
        rim='FLOOR-RIM-'+str(k);left='POST-BEARING-STAND-'+str(k)+'-SIDE-1';right='POST-BEARING-STAND-'+str((k+1)%8)+'-SIDE1'
        if not attempt_move(scene,'Withdraw rim '+str(k+1)+' with its two notched side plates',[rim,left,right],normal*14,blocked):return blocked
        if not attempt_move(scene,'Slide '+left+' off the open rim end',[left],-tangent*.6,blocked):return blocked
        if not attempt_move(scene,'Slide '+right+' off the opposite rim end',[right],tangent*.6,blocked):return blocked
    for pid in ids:
        if pid.startswith('FLOOR-BEAM-') and not attempt_move(scene,'Slide '+pid+' outward from the hub',[pid],radial(pid,12),blocked):return blocked
    if not release('FLOOR-CENTRAL-HUB',3,24):return blocked
    for pid in ids:
        if pid.startswith('PIER-'):
            ok,proof=attempt_path(scene,'Separate '+pid+' from the support layout',[pid],[[0,-1,0],radial(pid,8)])
            if not ok:
                blocked.append({'member_ids':[pid],'reason':'Pier withdrawal is obstructed','collisions':proof['collisions']});return blocked
    return blocked

def apply_shelf_phases(scene):
    blocked=[]
    for face,k in [('N',0),('S',4)]:
        ids=[pid for pid,p in scene.parts.items() if p.get('face')==face and p.get('schematicKind')=='shelf' and np.linalg.norm(scene.offsets[pid])<1e-12]
        if not ids:continue
        angle=-(k+.5)*np.pi/4;normal=np.array([np.cos(angle),0,np.sin(angle)])
        for pid in sorted(ids):
            ok=False;proof=None
            for segments in [[[0,-4,0],normal*3,[0,5,0],normal*30],[[0,-10,0],normal*30],[-normal*.8,[0,-3,0],normal*30],[[0,-.7,0],-normal*.8,[0,-2,0],normal*30],[-normal*.8,[0,-5,0],normal*30]]:
                ok,proof=attempt_path(scene,'Withdraw the bookshelf '+pid,[pid],segments)
                if ok:break
            if not ok:blocked.append({'member_ids':[pid],'reason':'Bookshelf withdrawal is obstructed','collisions':proof['collisions']})
    return blocked

def apply_wall_phases(scene):
    """Peel infill and rails downward after the floor/support assembly is clear."""
    ids=[pid for pid,p in scene.parts.items() if p.get('schematicKind') in ['wall','rail'] and np.linalg.norm(scene.offsets[pid])<1e-12]
    ids.sort(key=lambda pid:(min(v[1] for v in scene.parts[pid]['vertices']),pid))
    order={pid:k for k,pid in enumerate(ids)};blocked={};remaining=list(ids)
    for _ in range(8):
        progress=False
        for pid in remaining[:]:
            p=scene.parts[pid];face=p['face'];k=['N','NW','W','SW','S','SE','E','NE'].index(face);angle=-(k+.5)*np.pi/4;normal=np.array([np.cos(angle),0,np.sin(angle)])
            peers=[q for q in ids if scene.parts[q]['face']==face];rank=peers.index(pid);distance=15+(len(peers)-rank)*.4
            ok=False;proof=None
            for segments in [[[0,-4,0],normal*distance],[normal*distance],[-normal*.6,[0,-4,0],normal*(distance+.6)]]:
                ok,proof=attempt_path(scene,'Withdraw fitted wall member '+pid,[pid],segments)
                if ok:break
            if ok:remaining.remove(pid);blocked.pop(pid,None);progress=True
            else:blocked[pid]={'member_ids':[pid],'reason':'The fitted enclosure member remains constrained by adjacent frame stock','collisions':proof['collisions']}
        if not progress:break
    return list(blocked.values())

# TIMESTAMP START 2026-11-04T23:17:24+00:00 | REVISION R000029
def underlayment_ids(scene):
    return sorted(pid for pid,p in scene.parts.items() if p.get('floorRole')=='underlayment_sheet')

def expand_underlayment_stage(scene,stage):
    """Translate legacy motion proposals into the actual individual sheet inventory."""
    import copy
    result=copy.deepcopy(stage);panels=underlayment_ids(scene)
    for motion in result.get('motions',[result]):
        motion['member_ids']=[q for pid in motion['member_ids'] for q in (panels if pid=='FLOOR-SUBFLOOR' else [pid])]
    if 'motions' not in stage and stage['member_ids']==['FLOOR-SUBFLOOR'] and abs(stage['delta_m'][0])+abs(stage['delta_m'][2])<1e-12:
        return [{**result,'id':stage['id']+'-sheet-'+str(k+1).zfill(2),'member_ids':[pid],
                 'label':stage['label']+' · '+pid} for k,pid in enumerate(panels)]
    return [result]

def spread_underlayment(scene):
    """Open sheet seams by a checked half-inch expansion of their stock-cell grid."""
    label='Separate cut underlayment sheets on their stock grid'
    if any(stage['label']==label for stage in scene.stages):return
    east=np.array([np.sin(np.pi/8),0,np.cos(np.pi/8)])
    north=np.array([np.cos(np.pi/8),0,-np.sin(np.pi/8)])
    motions=[]
    for pid in underlayment_ids(scene):
        stock=scene.parts[pid]['sheet_stock'];u=np.mean(stock['eastBoundsM']);v=np.mean(stock['northBoundsM'])
        delta=east*(u/stock['lengthM'])*.0127+north*(v/stock['widthM'])*.0127
        motions.append({'member_ids':[pid],'delta_m':delta.tolist()})
    proof=check_multi_stage(scene,motions)
    assert proof['status']=='PASS',proof['collisions']
    apply_multi_stage(scene,motions,proof,label)
# TIMESTAMP END 2026-11-04T23:17:24+00:00 | REVISION R000029

def prepare_scene(variant='baseline'):
    """Build the common prerequisite sequence with all prior parking retained."""
    from plan_porch_disassembly import apply_porch_phases
    scene=load_scene(variant);initial=audit_initial_scene(scene)
    assert initial['status']=='PASS',initial['collisions']
    early=apply_architectural_phases(scene)
    # Wall rails, infill and shelves separate individually after the enclosing
    # support assemblies clear; a detached whole wall is not the endpoint.
    blocked=list(early)
    porch=apply_porch_phases(scene,skip_cover=True)
    blocked.extend(porch['blocked'])
    blocked.extend(apply_floor_phases(scene))
    blocked.extend(apply_shelf_phases(scene))
    blocked.extend(apply_wall_phases(scene))
    # TIMESTAMP START 2026-11-04T23:17:24+00:00 | REVISION R000029
    spread_underlayment(scene)
    # TIMESTAMP END 2026-11-04T23:17:24+00:00 | REVISION R000029
    return scene,blocked

# TIMESTAMP START 2026-11-03T06:54:15-05:00 | REVISION R004896
CENTER_ANCHORS={'FLOOR-CENTRAL-HUB','PIER-C','PIER-C-BELOW'}

def anchored_ids(scene):
    return CENTER_ANCHORS & set(scene.parts) if scene.variant=='top-entry' else set()

def output_snapshot(scene,blocked=None):
    moved={pid for stage in scene.stages for q in stage.get('motions',[stage]) for pid in q['member_ids']}
    fixed=anchored_ids(scene)
    assert not moved & fixed and all(np.array_equal(scene.offsets[pid],np.zeros(3)) for pid in fixed)
    return {'status':'PARTIAL' if blocked or moved|fixed!=set(scene.parts) else 'PASS','sources':scene.sources,'physical_piece_count':len(scene.parts),'stages':scene.stages,'blocked':blocked or [],'excluded':scene.excluded,'moved_ids':sorted(moved),'anchored_ids':sorted(fixed),'scope':'Nominal geometry and continuous straight translations around the stationary central pier and floor hub; structural dismantling procedure, access and lifting remain unspecified.'}

# TIMESTAMP END 2026-11-03T06:54:15-05:00 | REVISION R004896

# TIMESTAMP START 2026-11-03T07:02:34-05:00 | REVISION R004905
def column_pairs(scene):
    return [(pid[:-6],pid) for pid in scene.parts if pid.endswith('-BELOW') and pid[:-6] in scene.parts and (pid.startswith('PIER-') or pid.startswith('MUD-SUPPORT-'))]

def assert_rigid_columns(scene,stage):
    deltas={pid:np.asarray(q['delta_m']) for q in stage.get('motions',[stage]) for pid in q['member_ids']}
    for above,below in column_pairs(scene):
        assert np.array_equal(deltas.get(above,np.zeros(3)),deltas.get(below,np.zeros(3))),('A continuous column cannot split at grade',stage['id'],above)

# TIMESTAMP END 2026-11-03T07:02:34-05:00 | REVISION R004905
def replay_stages(variant,stages):
    """Recompute all proofs in a fresh full scene; never trust saved pair proofs."""
    scene=load_scene(variant);initial=audit_initial_scene(scene)
    assert initial['status']=='PASS',initial['collisions']
    checks=0;maximum=initial['maximum_intersection_m3'];discarded=0.
    for stage in stages:
# TIMESTAMP START 2026-11-03T07:02:34-05:00 | REVISION R004905
        assert_rigid_columns(scene,stage)
# TIMESTAMP END 2026-11-03T07:02:34-05:00 | REVISION R004905
        if 'motions' in stage:
            proof=check_multi_stage(scene,stage['motions'])
            assert proof['status']=='PASS',(stage['id'],proof['collisions'])
            apply_multi_stage(scene,stage['motions'],proof,stage['label'],stage['id'])
        else:
            proof=check_stage(scene,stage['member_ids'],stage['delta_m'])
            assert proof['status']=='PASS',(stage['id'],proof['collisions'])
            apply_stage(scene,stage['member_ids'],stage['delta_m'],proof,stage['label'],stage['id'])
        checks+=proof['continuous_pair_checks'];maximum=max(maximum,proof['maximum_intersection_m3']);discarded+=proof['discarded_sweep_prism_volume_m3']
    return scene,{'status':'PASS','independent_full_scene_replay':True,'initial_assembly':initial,'stage_count':len(stages),'continuous_pair_checks':checks,'maximum_intersection_m3':maximum,'discarded_sweep_prism_volume_m3':discarded,'parked_pieces_retained':True,'moving_group_pairs_checked':True,'overlap_tolerance_m3':VOLUME_TOLERANCE_M3}

def audit_final_joinery(scene):
    """Require the initially mating timber/peg surfaces to be separated."""
    porch=json.loads((ROOT/'src/mudroom-joinery-fit.json').read_text())
    ids={pid for pid,p in scene.parts.items() if p.get('is_timber') or p.get('group')=='joinery_pegs' or pid=='PLY' or p.get('schematicKind') in ['floorAssembly','wall','rail','shelf']}
    ids.update(porch['parts']);ids.update(p['id'] for p in porch['added_parts']);ids&=set(scene.parts)
    boxes={pid:scene.solids[pid].bounding_box() for pid in ids};pairs=[];remaining=[]
    # TIMESTAMP START 2026-11-03T06:54:15-05:00 | REVISION R004896
# TIMESTAMP START 2026-11-03T07:02:34-05:00 | REVISION R004905
    fixed=anchored_ids(scene);anchored_pairs=[];continuous_columns={frozenset(pair) for pair in column_pairs(scene)};column_seams=[]
# TIMESTAMP END 2026-11-03T07:02:34-05:00 | REVISION R004905
    contact_tolerance=1e-6;separation_tolerance=1e-5
    # TIMESTAMP END 2026-11-03T06:54:15-05:00 | REVISION R004896
    for a,b in itertools.combinations(sorted(ids),2):
        aa,bb=boxes[a],boxes[b]
        if any(aa[i+3]+contact_tolerance<bb[i] or bb[i+3]+contact_tolerance<aa[i] for i in range(3)):continue
        initial_gap=scene.solids[a].min_gap(scene.solids[b],contact_tolerance*2)
        if initial_gap>contact_tolerance:continue
        # TIMESTAMP START 2026-11-03T06:54:15-05:00 | REVISION R004896
# TIMESTAMP START 2026-11-03T07:02:34-05:00 | REVISION R004905
        if frozenset((a,b)) in continuous_columns:
            column_seams.append([a,b]);continue
        if a in fixed and b in fixed:
            anchored_pairs.append([a,b]);continue
# TIMESTAMP END 2026-11-03T07:02:34-05:00 | REVISION R004905
        # TIMESTAMP END 2026-11-03T06:54:15-05:00 | REVISION R004896
        gap=scene.current(a).min_gap(scene.current(b),separation_tolerance*2)
        pairs.append([a,b])
        if gap<=separation_tolerance:remaining.append({'a':a,'b':b,'final_gap_m':gap})
    return {'status':'PASS' if not remaining else 'PARTIAL','initial_mating_pair_count':len(pairs),
        # TIMESTAMP START 2026-11-03T06:54:15-05:00 | REVISION R004896
        'remaining_mating_pairs':remaining,'intentionally_anchored_mating_pairs':anchored_pairs,'continuous_column_display_seams':column_seams,'minimum_required_final_gap_m':separation_tolerance,
        # TIMESTAMP END 2026-11-03T06:54:15-05:00 | REVISION R004896
        'scope':'All initially contacting canonical timber/pegs, fitted porch stock/pegs, floor/support members and individual wall rails/infill/shelves; non-interlocking roof covering and window assemblies may remain grouped.'}

# TIMESTAMP START 2026-11-02T21:01:13-05:00 | REVISION R004875
def generate_complete_certificate(candidate_directory=None):
# TIMESTAMP END 2026-11-02T21:01:13-05:00 | REVISION R004875
    """Plan and independently replay the complete current physical scene."""
    from plan_main_disassembly import apply_primary_phases
    # TIMESTAMP START 2026-11-02T21:01:13-05:00 | REVISION R004875
    files=['scripts/plan_architectural_disassembly.py','scripts/plan_porch_disassembly.py',
        # TIMESTAMP START 2026-11-03T06:36:08-05:00 | REVISION R004891
        # TIMESTAMP START 2026-11-04T12:48:28+00:00 | REVISION R000004
        'scripts/plan_main_disassembly.py','scripts/plan_compact_disassembly.py','scripts/plan_revised_disassembly.py','scripts/revised-disassembly-seed.json','scripts/compact-disassembly-route.json','docs/cupola-foot-prototype.json']
        # TIMESTAMP END 2026-11-04T12:48:28+00:00 | REVISION R000004
        # TIMESTAMP END 2026-11-03T06:36:08-05:00 | REVISION R004891
    # TIMESTAMP END 2026-11-02T21:01:13-05:00 | REVISION R004875
    script_hashes={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in files}
    variants={};primary_variants={}
    for variant in ['top-entry','baseline','proposed']:
        # TIMESTAMP START 2026-11-02T21:01:13-05:00 | REVISION R004875
        if candidate_directory:
            # Candidates contain proposed translations only. Their cached proofs
            # never authorize publication: every stage is independently replayed
            # below against the current full scene and all parked obstacles.
            candidate=json.loads((Path(candidate_directory)/(variant+'.json')).read_text())
            planned=load_scene(variant);planned.stages=candidate['stages'];planned.version=len(planned.stages)
            for stage in planned.stages:
                for motion in stage.get('motions',[stage]):
                    for pid in motion['member_ids']:planned.offsets[pid]+=np.asarray(motion['delta_m'])
            prefix_count=candidate.get('prefix_stage_count',0);prefix_blocked=[];primary_blocked=candidate.get('blocked',[])
        elif variant=='top-entry':
            from plan_compact_disassembly import complete_plan
            planned=load_scene(variant);prefix_count=0;prefix_blocked=[];primary_blocked=complete_plan(planned)
        else:
            planned,prefix_blocked=prepare_scene(variant);prefix_count=len(planned.stages)
            primary_blocked=apply_primary_phases(planned)
        print(variant,'prerequisite stages',prefix_count,'pending groups',len(prefix_blocked),flush=True)
        # TIMESTAMP END 2026-11-02T21:01:13-05:00 | REVISION R004875
        moved={pid for stage in planned.stages for q in stage.get('motions',[stage]) for pid in q['member_ids']}
        # TIMESTAMP START 2026-11-03T06:54:15-05:00 | REVISION R004896
        fixed=anchored_ids(planned)
        assert not moved & fixed and all(np.array_equal(planned.offsets[pid],np.zeros(3)) for pid in fixed)
        unmoved=set(planned.parts)-moved-fixed
        # TIMESTAMP END 2026-11-03T06:54:15-05:00 | REVISION R004896
        blocked=list(primary_blocked)
        for group in prefix_blocked:
            held=[pid for pid in group['member_ids'] if pid in unmoved]
            if held:blocked.append({**group,'member_ids':held})
            elif any(planned.parts[pid].get('schematicKind') not in ['wall','rail','shelf'] for pid in group['member_ids']):
                blocked.append(group)
        reported={pid for group in blocked for pid in group['member_ids']}
        if unmoved-reported:blocked.append({'member_ids':sorted(unmoved-reported),'reason':'No complete checked withdrawal path is available for this physical piece.'})
        print(variant,'planned',len(planned.stages),'stages;',len(moved),'of',len(planned.parts),'pieces moved;',len(blocked),'blocked groups',flush=True)
        assert len({stage['id'] for stage in planned.stages})==len(planned.stages),'Duplicate stage identifiers'
        if variant=='top-entry':assert not blocked and not unmoved,blocked
        # Rebuild the scene and all swept solids from the unchanged physical
        # sources. Cached planning proofs never authorize the published motion.
        replayed,verification=replay_stages(variant,planned.stages)
        assert set(replayed.parts)==set(planned.parts),'Physical piece inventory changed during planning or replay'
        assert all(np.array_equal(replayed.parts[pid][key],planned.parts[pid][key]) for pid in replayed.parts for key in ['vertices','triangles','center']),'Physical mesh changed during planning or replay'
        verification['exact_physical_mesh_equality_after_rebuild']=True
        verification['source_metadata_rebindings']={name:{'planned':planned.sources[name],'replayed':digest} for name,digest in replayed.sources.items() if planned.sources[name]!=digest}
        assert all(np.allclose(replayed.offsets[pid],planned.offsets[pid],atol=1e-12,rtol=0) for pid in replayed.parts)
        separation=audit_final_joinery(replayed)
        verification['final_mating_separation']=separation
        if variant=='top-entry':assert separation['status']=='PASS',separation
        if separation['remaining_mating_pairs']:
            blocked.append({'member_ids':sorted({pid for pair in separation['remaining_mating_pairs'] for pid in [pair['a'],pair['b']]}),'reason':'These initially mating physical surfaces remain in contact after the available sequence.'})
        result=output_snapshot(replayed,blocked);result['sources'].update(script_hashes)
        result.update(verification=verification,physical_ids=sorted(replayed.parts),unmoved_ids=sorted(unmoved),
            # TIMESTAMP START 2026-11-03T06:54:15-05:00 | REVISION R004896
            coverage={'physical_piece_count':len(replayed.parts),'moved_piece_count':len(moved),'unmoved_piece_count':len(unmoved),'anchored_piece_count':len(fixed)},
            # TIMESTAMP END 2026-11-03T06:54:15-05:00 | REVISION R004896
            stage_count=len(replayed.stages),prefix_stage_count=prefix_count,
            completion_status='Complete geometric withdrawal sequence' if not blocked and not unmoved else 'Partial verified sequence; listed physical pieces remain held')
        if unmoved:result['status']='PARTIAL'
        variants[variant]=result
        tail=result['stages'][prefix_count:]
        primary_variants[variant]={'status':result['status'],'sources':result['sources'],
            'prefix_stage_count':prefix_count,'stages':tail,'blocked':blocked,
            'moved_ids':sorted({pid for stage in tail for q in stage.get('motions',[stage]) for pid in q['member_ids']}),
            # TIMESTAMP START 2026-11-03T06:54:15-05:00 | REVISION R004896
            'verification':verification,'physical_ids':result['physical_ids'],'unmoved_ids':result['unmoved_ids'],'anchored_ids':result['anchored_ids']}
            # TIMESTAMP END 2026-11-03T06:54:15-05:00 | REVISION R004896
        print(variant,'independent replay',verification['status'],'pair checks',verification['continuous_pair_checks'],flush=True)
    assert variants['top-entry']['status']=='PASS',variants['top-entry']['blocked']
    for result in variants.values():
        assert all(hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==sha for name,sha in result['sources'].items()),'Source changed before certificate publication'
    common={'schema_version':1,'status':'PASS' if all(q['status']=='PASS' for q in variants.values()) else 'PARTIAL',
        'variants':variants,'coordinate_system':'World model X/Y/Z in metres; stage deltas accumulate; all parked pieces remain obstacles',
        'scope':'Nominal geometric disassembly visualization; structural dismantling, access and lifting require separate planning'}
    # TIMESTAMP START 2026-11-02T21:01:13-05:00 | REVISION R004875
    # TIMESTAMP START 2026-11-04T12:48:28+00:00 | REVISION R000004
    from datetime import datetime,timezone
    # TIMESTAMP START 2026-11-04T20:18:09+00:00 | REVISION R000021
    # TIMESTAMP START 2026-11-04T23:17:24+00:00 | REVISION R000029
    history={'revision':'R000029','timestamp_start':'2026-11-04T23:17:24+00:00','timestamp_end':datetime.now(timezone.utc).isoformat(),'ledger_origin':'cloud; authoritative Mac ledger requires reconciliation'}
    # TIMESTAMP END 2026-11-04T23:17:24+00:00 | REVISION R000029
    # TIMESTAMP END 2026-11-04T20:18:09+00:00 | REVISION R000021
    # TIMESTAMP END 2026-11-04T12:48:28+00:00 | REVISION R000004
    architectural={**common,'_change_history':history}
    primary={**common,'variants':primary_variants,'_change_history':history}
    combined={**common,'_change_history':history}
    # TIMESTAMP END 2026-11-02T21:01:13-05:00 | REVISION R004875
    for name,document in [('architectural-disassembly-plans.json',architectural),('main-disassembly-plan.json',primary),('disassembly-plan.json',combined)]:
        (ROOT/'src'/name).write_text(json.dumps(document,separators=(',',':'))+'\n')
    return combined

if __name__=='__main__':
    # TIMESTAMP START 2026-11-02T21:01:13-05:00 | REVISION R004875
    parser=argparse.ArgumentParser();parser.add_argument('--variant',choices=VARIANTS,default='baseline');parser.add_argument('--inventory',action='store_true');parser.add_argument('--complete-certificate',action='store_true');parser.add_argument('--candidate-directory');args=parser.parse_args()
    if args.complete_certificate:generate_complete_certificate(args.candidate_directory)
    # TIMESTAMP END 2026-11-02T21:01:13-05:00 | REVISION R004875
    else:
        scene=load_scene(args.variant)
        print(json.dumps({'variant':args.variant,'physical_piece_count':len(scene.parts),'architectural_piece_count':len(architectural_ids(scene)),'sources':scene.sources,'excluded':scene.excluded},indent=2))
# TIMESTAMP END 2026-11-02T15:51:57-05:00 | REVISION R004809
