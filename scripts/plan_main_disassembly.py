# TIMESTAMP START 2026-11-02T15:56:09-05:00 | REVISION R004810
"""Main-frame contact constraints and continuously checked removal proposals.

Contact-cone tests are necessary initial-motion conditions, not a substitute
for swept-volume tests, structural dismantling approval, or rotational analysis.
"""
from pathlib import Path
import argparse,hashlib,itertools,json
import numpy as np
from scipy.optimize import linprog
from scipy.sparse import lil_matrix
from step_lap import solid,contacts,close_bounds
from plan_architectural_disassembly import VARIANTS

ROOT=Path(__file__).resolve().parents[1]
CONTACT_AREA_MIN_IN2=.0001
LP_TOLERANCE=1e-9


def contact_graph(parts):
    solids={pid:solid(part) for pid,part in parts.items()}
    pairs=[]
    for a,b in itertools.combinations(parts,2):
        if not close_bounds(solids[a],solids[b]):continue
        planes={}
        for face in contacts(solids[a],solids[b]):
            if face['area_in2']<=CONTACT_AREA_MIN_IN2:continue
            n=face['normal_on_rafter'];key=tuple(np.round(n,10))
            if key not in planes:planes[key]={'normal_on_a':n,'area_in2':0.}
            planes[key]['area_in2']+=face['area_in2']
        if planes:pairs.append({'a':a,'b':b,'planes':list(planes.values())})
    return pairs


def solve(c,A,bounds):
    result=linprog(c,A_ub=A if A.shape[0] else None,
        b_ub=np.zeros(A.shape[0]) if A.shape[0] else None,bounds=bounds,method='highs',
        options={'dual_feasibility_tolerance':LP_TOLERANCE,'primal_feasibility_tolerance':LP_TOLERANCE})
    assert result.success,(result.status,result.message)
    return result


def local_directions(name,remaining,graph):
    normals=[]
    for pair in graph:
        if pair['a'] not in remaining or pair['b'] not in remaining:continue
        if pair['a']==name:normals.extend(x['normal_on_a'] for x in pair['planes'])
        elif pair['b']==name:normals.extend((-np.asarray(x['normal_on_a'])).tolist() for x in pair['planes'])
    A=np.array(normals).reshape(-1,3);directions=[]
    for axis in np.vstack([np.eye(3),-np.eye(3)]):
        result=solve(-axis,A,[(-1,1)]*3)
        if -result.fun>1e-7:
            v=result.x/np.linalg.norm(result.x)
            if not any(np.linalg.norm(v-q)<1e-7 for q in directions):directions.append(v)
    return directions


def local_elimination(parts,graph):
    remaining=set(parts);rounds=[]
    while True:
        movable={name:local_directions(name,remaining,graph) for name in sorted(remaining)}
        movable={name:[v.tolist() for v in velocities] for name,velocities in movable.items() if velocities}
        if not movable:break
        rounds.append(movable);remaining-=movable.keys()
    return rounds,sorted(remaining)


def coupled_cone(parts,graph,remaining,anchor='P0',prove_locked=True):
    """Bound every relative translational degree of freedom of the contact cone.

    Each contact uses n_a dot(v_a-v_b)<=0. Fixing one member removes only global
    translation. Bounds [-1,1] make homogeneous feasible rays measurable. If
    every coordinate's positive and negative maximum is zero, this cone has no
    non-rigid translational release. Rotation is deliberately not modeled.
    """
    names=sorted(remaining);index={name:i for i,name in enumerate(names)}
    anchor=anchor if anchor in index else names[0]
    selected=[p for p in graph if p['a'] in index and p['b'] in index]
    rows=sum(len(p['planes']) for p in selected);A=lil_matrix((rows,3*len(names)))
    row=0
    for pair in selected:
        for face in pair['planes']:
            n=np.asarray(face['normal_on_a']);ia=3*index[pair['a']];ib=3*index[pair['b']]
            A[row,ia:ia+3]=n;A[row,ib:ib+3]=-n;row+=1
    A=A.tocsr();bounds=[(-1,1)]*(3*len(names))
    for j in range(3):bounds[3*index[anchor]+j]=(0,0)
    centers=np.array([parts[name]['center'] for name in names]);centers-=centers.mean(0)
    spread=solve(-centers.reshape(-1),A,bounds)
    result={'member_ids':names,'anchor':anchor,'contact_pairs':len(selected),'contact_plane_constraints':rows,
        'solver':'scipy.optimize.linprog / HiGHS','solver_tolerance':LP_TOLERANCE,
        'scope':'Necessary first-motion translational contact constraints; rotations and finite trajectories require separate checks.',
        'global_translation_removed':True,'velocity_coordinate_bound':1.,'spreading_objective':float(-spread.fun)}
    if np.max(np.abs(spread.x))>1e-7:
        result.update(status='CANDIDATE',velocities={name:spread.x[3*i:3*i+3].tolist() for i,name in enumerate(names)},
            maximum_constraint_residual=float(max(0.,np.max(A@spread.x))))
        return result
    maxima=[];maximum=0.;best=None
    if prove_locked:
        for coordinate in range(3*len(names)):
            if bounds[coordinate]==(0,0):continue
            for sign in [-1,1]:
                objective=np.zeros(3*len(names));objective[coordinate]=-sign
                candidate=solve(objective,A,bounds);bound=max(0.,float(-candidate.fun));maximum=max(maximum,bound)
                maxima.append({'member':names[coordinate//3],'axis':'XYZ'[coordinate%3],'sign':sign,'maximum':bound})
                if bound>1e-7 and best is None:best=candidate.x
    if best is not None:
        result.update(status='CANDIDATE',velocities={name:best[3*i:3*i+3].tolist() for i,name in enumerate(names)})
    else:result['status']='TRANSLATION_LOCKED' if prove_locked else 'NO_SPREADING_CANDIDATE'
    result.update(coordinate_optimizations=len(maxima),maximum_relative_coordinate=maximum,coordinate_bounds=maxima)
    return result


def diagnose(variant):
    path=ROOT/'src'/VARIANTS[variant][0];raw=path.read_bytes();model=json.loads(raw)
    parts={p['id']:p for p in model['parts'] if p['is_timber'] or p['id']=='PLY'}
    graph=contact_graph(parts);rounds,remaining=local_elimination(parts,graph)
    coupled=coupled_cone(parts,graph,remaining) if remaining else None
    return {'status':'PARTIAL','source_model_sha256':hashlib.sha256(raw).hexdigest(),
        'physical_canonical_ids':list(parts),'contact_pairs':graph,'local_elimination_rounds':rounds,
        'locally_locked_ids':remaining,'coupled_release':coupled,
        'scope':'Diagnostic only. Hypothetical local elimination ignores intermediate and parked obstacles; it does not authorize motion.'}


def apply_free_primary_phases(scene):
    """Peel free canonical members against the actual current global scene.

    Roof coverings/windows and the architectural/porch prefix must run first.
    No parked object is removed from collision checks. Failed complete paths
    leave the scene unchanged. Remaining closed joinery is explicitly held.
    """
    from plan_architectural_disassembly import attempt_path
    blocked=[]
    def unmoved(pid):return pid in scene.parts and np.linalg.norm(scene.offsets[pid])<1e-12
    def path(pid,label,candidates):
        if not unmoved(pid):return True
        failures=[]
        for segments in candidates:
            try:success,proof=attempt_path(scene,label,[pid],segments)
            except AssertionError as error:raise AssertionError((pid,segments,error)) from error
            if success:return True
            failures.append({'segments':np.asarray(segments,float).tolist(),'collisions':proof['collisions']})
        blocked.append({'member_ids':[pid],'reason':'No checked continuous withdrawal path succeeded with the current remaining and parked pieces.','attempts':failures})
        return False
    # The selected top-entry short-rafter heads admit vertical withdrawal; the
    # historical closed-head variants remain held rather than crossing wood.
    if scene.variant=='top-entry':
        for k in range(8):
            a=-(k+.5)*np.pi/4;out=np.array([np.cos(a),0,np.sin(a)])
            for side in ['0','2']:
                pid=f'J{k}-{side}'
                path(pid,'Lift and park short rafter '+pid,[[[0,4.5,0],(15*out).tolist()],
                    [[0,1,0],(5*out).tolist(),[0,5,0],(10*out).tolist()]])
    for k in range(8):
        a=-k*np.pi/4;out=np.array([np.cos(a),0,np.sin(a)])
        path(f'CR{k}','Withdraw cupola roof member CR'+str(k),
             [[(2*out+np.array([0,2,0])).tolist(),(18*out).tolist()],[(3*out+np.array([0,3,0])).tolist(),(17*out).tolist()]])
    path('PLY','Lift and park the horizontal cupola plywood',
         [[[0,3,0],[15,0,0]],[[0,3,0],[0,0,15]],[[0,3,0],[-15,0,0]]])
    for k in range(8):
        a=-k*np.pi/4;out=np.array([np.cos(a),0,np.sin(a)])
        path(f'CC{k}','Lower ceiling spoke CC'+str(k)+' through the open cupola well',
             [[[0,-.25,0],(-.55*out).tolist(),[0,-5.5,0],(20*out).tolist()],
              [[0,-.4,0],(-.6*out).tolist(),[0,-6,0],(22*out).tolist()]])
    primary=[pid for pid,p in scene.parts.items() if (p.get('is_timber') or pid=='PLY') and not p.get('schematic')]
    held=[pid for pid in primary if unmoved(pid) and not any(pid in row['member_ids'] for row in blocked)]
    if held:blocked.append({'member_ids':held,'reason':'Closed joinery has no checked release yet. The coupled contact-cone audit and brace-entry investigation must be resolved before these timbers move.'})
    return blocked

def radial(k):
    angle=-float(k)*np.pi/4
    return np.array([np.cos(angle),0,np.sin(angle)])

def release_brace_with_fitted_companions(scene,pid):
    """Withdraw a captive brace/panel set, then separate every actual piece."""
    from plan_architectural_disassembly import clone_scene,check_stage,apply_stage,attempt_path
    k=int(pid[1]);side=pid[-1];faces=['N','NW','W','SW','S','SE','E','NE']
    if side in ['A','B']:
        face_index=(k-1)%8 if side=='A' else k;face=faces[face_index]
        if face in ['N','S']:return False
        suffix=['infill-6-upper','rail3-1','infill-7'] if side=='A' else ['infill-2-upper','rail3-0','infill-3']
        companions=['SCHEM-'+face+'-'+suffix for suffix in suffix]
        if face=='E':companions.append('SCHEM-E-rail-jamb-'+('right' if side=='A' else 'left'))
    elif k in [1,5]:
        face_index=0 if k==1 else 4;face=faces[face_index];companions=['SCHEM-'+face+'-shelf'+str(level) for level in [4,5]]
    else:return False
    companions=[q for q in companions if q in scene.parts and np.linalg.norm(scene.offsets[q])<1e-12]
    if not companions:return False
    joint=scene.parts[pid]['main_face_brace_joinery'];direction=np.asarray(joint['withdrawal_world'])*.25
    axis=np.asarray(joint['axis_end'])-np.asarray(joint['axis_start']);axis/=np.linalg.norm(axis)
    for sign in [1,-1]:
        trial=clone_scene(scene);valid=True
        steps=[([pid,*companions],direction),([pid,*companions],[0,-1,0]),([pid],sign*axis*1.2)]
        steps.extend(([q],[0,-3,0]) for q in companions);steps.append(([pid],[0,-3,0]))
        for ids,delta in steps:
            proof=check_stage(trial,ids,delta,stop_first=True)
            if proof['status']!='PASS':valid=False;break
            apply_stage(trial,ids,delta,proof,'Separate the brace and fitted enclosure pieces at '+pid)
        if not valid:continue
        parked=False
        for segments in [[radial(k)*10],[[0,-1,0],radial(k)*10],[[0,1,0],radial(k)*10]]:
            if attempt_path(trial,'Park the separated brace '+pid,[pid],segments)[0]:parked=True;break
        if not parked:continue
        for index,q in reversed(list(enumerate(companions))):
            distance=28 if scene.parts[q].get('schematicKind')=='shelf' else 22+index
            parked=False
            for segments in [[radial(face_index+.5)*distance],[-radial(face_index+.5)*3],*[[[0,shift,0],radial(face_index+.5)*distance] for shift in [2,-2,4,-4,6,8,-6]]]:
                if attempt_path(trial,'Park the separated enclosure piece '+q,[q],segments)[0]:parked=True;break
            if not parked:valid=False;break
        if valid:
            scene.offsets=trial.offsets;scene.stages=trial.stages;scene.version=trial.version
            return True
    return False

def apply_retained_bent_lower_phases(scene):
    """Open the perimeter while preserving the two intact infilled bents."""
    from plan_architectural_disassembly import check_multi_stage,apply_multi_stage,attempt_path
    blocked=[]
    def together(label,motions):
        proof=check_multi_stage(scene,motions,stop_first=True)
        if proof['status']!='PASS':
            blocked.append({'member_ids':[pid for q in motions for pid in q['member_ids']],'reason':label,'collisions':proof['collisions']});return False
        apply_multi_stage(scene,motions,proof,label);return True
    def path(pid,label,candidates):
        proof=None
        for segments in candidates:
            ok,proof=attempt_path(scene,label,[pid],segments)
            if ok:return True
        blocked.append({'member_ids':[pid],'reason':label,'collisions':proof['collisions']});return False
    retained={pid for pid in scene.parts if np.linalg.norm(scene.offsets[pid])<1e-12}
    root2=np.sqrt(2);south=np.array([-1.,0,5-3*root2]);west=np.array([root2-2,0,4-3*root2]);east=np.array([1-root2,0,1.])
    north_ids=['P0','P1','T0','T1','B0','B1','K0-B','K1-A','SCHEM-N-infill-2-upper','SCHEM-N-infill-3','SCHEM-N-rail3-0']
    south_ids=['P4','P5','T4','T5','B4','B5','K4-B','K5-A','K5-C','SCHEM-S-shelf5','SCHEM-S-infill-2-upper','SCHEM-S-infill-3','SCHEM-S-rail3-0']
    west_ids=['P2','P3','T2','T3','B2','B3'];east_ids=['P6','P7','T6','T7','B6','B7']
    motions=[{'member_ids':[pid for pid in ids if pid in retained],'delta_m':delta.tolist()} for ids,delta in [(south_ids,south),(west_ids,west),(east_ids,east)]]
    if not together('Open the lower frame while retaining the north and south bents',motions):return blocked
    for k in range(8):
        if k in [1,5] and f'K{k}-C' in retained:continue
        if not path(f'T{k}','Withdraw and park radial tie '+str(k),[[-.2*radial(k),[0,1,0],20*radial(k)]]):return blocked
    def beam_axis(k):
        p=scene.parts[f'B{k}'];axis=np.asarray(p['axis_end'])-np.asarray(p['axis_start']);return axis/np.linalg.norm(axis)
    def park_beam(k,withdraw=None):
        before=[] if withdraw is None else [withdraw]
        return path(f'B{k}','Withdraw and park perimeter beam '+str(k),[[*before,[0,lift,0],16*radial(k+.5)] for lift in [1,4,.5,1.5,2,2.5,3]])
    def park_post(k):
        return path(f'P{k}','Park separated perimeter post '+str(k),[[10*radial(k)],*[[[0,shift,0],10*radial(k)] for shift in [-3,-4,3,6]]])
    for k in [1,3,5,7]:
        if not park_beam(k,.2*beam_axis(k)):return blocked
    for k in [2,6]:
        axis=beam_axis(k)
        if not together('Open the unbraced perimeter bent '+str(k),[{'member_ids':[f'P{k}'],'delta_m':(-.2*axis).tolist()},{'member_ids':[f'P{k+1}'],'delta_m':(.2*axis).tolist()}]):return blocked
        if not park_beam(k) or not park_post(k) or not park_post(k+1):return blocked
    for k,face in [(0,'N'),(4,'S')]:
        if f'SCHEM-{face}-shelf5' in retained:
            directions={f'P{k+1}':[-0.4142135609390545, -0.0, -1.0],
                f'T{k+1}':[-1.0, -0.0, -0.4142135609390545],
                f'B{k}':[-0.021382132759578808, -0.0, -0.05162103507935338],
                f'K{k}-B':[-0.2726852969612805, 7.137529843921416e-10, -0.2195364405928119],
                f'K{k+1}-A':[-0.08034618210819641, -0.0, 0.244811261768167],
                f'K{k+1}-C':[-1.0, -0.0, -0.2988475341523616],
                f'SCHEM-{face}-shelf5':[-0.14600633219288864, -0.25346362369986813, -0.0]}
            rotation=np.array([1,1,1]) if k==0 else np.array([-1,1,-1])
            motions=[{'member_ids':[pid],'delta_m':(np.asarray(delta)*rotation).tolist()} for pid,delta in directions.items()]
            if not together('Release the '+face+' bent and its retained top shelf with relative motion',motions):return blocked
            continue
        b=np.array([-(root2-1)/2,0,-.5])*(1 if k==0 else -1)
        k0=f'K{k}-B';k1=f'K{k+1}-A';j0=scene.parts[k0]['main_face_brace_joinery'];j1=scene.parts[k1]['main_face_brace_joinery']
        n0=np.asarray(j0['withdrawal_world']);n1=np.asarray(j1['withdrawal_world'])
        a0=np.asarray(j0['axis_end'])-j0['axis_start'];a0/=np.linalg.norm(a0)
        a1=np.asarray(j1['axis_end'])-j1['axis_start'];a1/=np.linalg.norm(a1)
        lam=.2;c=lam*np.dot(n0-n1,a0-a1)/np.dot(a0-a1,a0-a1)
        wall=b+lam*n0-c*a0;wall_ids=[f'SCHEM-{face}-infill-2-upper',f'SCHEM-{face}-infill-3',f'SCHEM-{face}-rail3-0']
        motions=[{'member_ids':[f'P{k+1}'],'delta_m':(2*b).tolist()},{'member_ids':[f'B{k}'],'delta_m':b.tolist()},
            {'member_ids':[k0],'delta_m':(b+lam*n0).tolist()},{'member_ids':[k1],'delta_m':(b+lam*n1).tolist()},
            {'member_ids':wall_ids,'delta_m':wall.tolist()}]
        motions=[{**motion,'member_ids':[pid for pid in motion['member_ids'] if pid in retained]} for motion in motions]
        motions=[motion for motion in motions if motion['member_ids']]
        if not together('Release the intact '+face+' infilled bent with relative motion',motions):return blocked
    for k,face in [(0,'N'),(4,'S')]:
        normal=radial(k+.5)
        if f'SCHEM-{face}-shelf5' in retained:
            if not park_post(k) or not park_post(k+1):return blocked
            if not path(f'B{k}','Lift the separated shelf-bent girt '+face,[[[0,4,0]]]):return blocked
            if not path(f'T{k+1}','Withdraw the shelf-bent radial tie '+face,[[[0,1,0],20*radial(k+1)]]):return blocked
            for suffix,post,distance in [('B',k,10),('A',k+1,12),('C',k+1,14)]:
                pid=f'K{post}-{suffix}';joint=scene.parts[pid]['main_face_brace_joinery']
                axis=np.asarray(joint['axis_end'])-joint['axis_start'];axis/=np.linalg.norm(axis)
                if not path(pid,'Slide the '+face+' brace out of the retained shelf',[[-1.6*axis,distance*normal],*[[-1.6*axis,[0,shift,0],distance*normal] for shift in [-.5,-1,.5,1]]]):return blocked
            if not path(f'SCHEM-{face}-shelf5','Separate the retained top bookshelf '+face,[[5*normal]]):return blocked
            continue
        if not park_post(k) or not park_post(k+1):return blocked
        if not path(f'B{k}','Lift the separated intact girt '+face,[[[0,4,0]]]):return blocked
        for suffix,post,distance in [('B',k,10),('A',k+1,12)]:
            pid=f'K{post}-{suffix}'
            if pid not in retained:continue
            joint=scene.parts[pid]['main_face_brace_joinery']
            axis=np.asarray(joint['axis_end'])-joint['axis_start'];axis/=np.linalg.norm(axis)
            if not path(pid,'Slide the separated '+face+' brace axially out of the infill',[[-1.6*axis,distance*normal],*[[-1.6*axis,[0,shift,0],distance*normal] for shift in [-.5,-1,.5,1]]]):return blocked
        for suffix,distance in [('infill-2-upper',5),('infill-3',6),('rail3-0',7)]:
            pid=f'SCHEM-{face}-{suffix}'
            if pid not in retained:continue
            if not path(pid,'Separate the intact '+face+' enclosure member '+suffix,[[distance*normal]]):return blocked
    return blocked


def apply_primary_phases(scene):
    """Release actual pegs and entry joints, retaining every parked obstacle."""
    from plan_architectural_disassembly import attempt_path,apply_stage,check_stage,check_multi_stage,apply_multi_stage,apply_wall_phases,apply_shelf_phases,clone_scene
    apply_free_primary_phases(scene)
    blocked=[]
    def path(pid,label,segments,alternatives=None,record=True):
        ok=False;proof=None
        for candidate in [segments,*(alternatives or [])]:
            ok,proof=attempt_path(scene,label,[pid],candidate)
            if ok:break
        if not ok and record:blocked.append({'member_ids':[pid],'reason':label+' is obstructed','collisions':proof['collisions']})
        return ok
    # Removable infill boards, pegs and braces can depend on each other. Peel
    # only currently free items, then retry the remaining actual geometry.
    primary_release=[pid for pid,p in scene.parts.items() if pid.startswith('MAIN-PEG-') or p.get('main_face_brace_joinery')]
    for _ in range(len(primary_release)+1):
        before=scene.version
        for pid in primary_release:
            if np.linalg.norm(scene.offsets[pid])>1e-12:continue
            p=scene.parts[pid];joint=p.get('main_face_brace_joinery')
            if joint:
                if any(np.linalg.norm(scene.offsets[peg])<1e-12 for peg in joint['peg_ids']):continue
                out=radial(int(pid[1]));withdraw=np.asarray(joint['withdrawal_world'])*.25
                if not path(pid,'Withdraw and park face-housed brace '+pid,[withdraw,[0,-2,0],out*10],[[withdraw,[0,drop,0],out*10] for drop in [-3,-4,-1,1,2]],record=False):
                    release_brace_with_fitted_companions(scene,pid)
            else:
                direction=np.asarray(p['withdrawal_direction'],float);distance=p['withdrawal_distance_m']
                center=np.asarray(p['center'],float);center[1]=0;out=center/np.linalg.norm(center)
                path(pid,'Withdraw and park the retaining peg '+pid,[direction*distance,[0,-3,0],out*12],[[-direction*distance,[0,-3,0],out*12]],record=False)
        apply_shelf_phases(scene)
        apply_wall_phases(scene)
        if scene.version==before:break
    held=[pid for pid in primary_release if np.linalg.norm(scene.offsets[pid])<1e-12]
    deferred={'K0-B','K1-A','K1-C','K4-B','K5-A','K5-C'}
    if set(held)-deferred:return [{'member_ids':held,'reason':'Retaining pegs or face-housed braces are still captured by physical enclosure or adjacent wood.'}]
    if scene.variant=='top-entry':
        expected=[f'J{k}-{side}' for k in range(8) for side in ['0','2']]+[f'CR{k}' for k in range(8)]+[f'CC{k}' for k in range(8)]+['PLY']
        held=[pid for pid in expected if np.linalg.norm(scene.offsets[pid])<1e-12]
        if held:return [{'member_ids':held,'reason':'Roof and ceiling prerequisites did not clear the upper frame'}]
        accepted_scene=scene;scene=clone_scene(scene)
        prototype=json.loads((ROOT/'docs/cupola-foot-prototype.json').read_text())['conditional_primary_test']['stages']
        for source in prototype:
            stage=dict(source)
            if stage['label'].startswith('Lift detached principal rafter'):continue
            if stage['label']=='Park cupola foot peg 6':stage['delta_m']=(3*np.asarray(stage['delta_m'])).tolist()
            if stage['label']=='Lift separate cupola ring member':stage['delta_m']=[0,1,0]
            if 'motions' in stage:
                proof=check_multi_stage(scene,stage['motions'],stop_first=True)
                if proof['status']!='PASS':return [{'member_ids':[pid for q in stage['motions'] for pid in q['member_ids']],'reason':stage['label'],'collisions':proof['collisions']}]
                apply_multi_stage(scene,stage['motions'],proof,stage['label'])
            else:
                proof=check_stage(scene,stage['member_ids'],stage['delta_m'],stop_first=True)
                if proof['status']!='PASS':return [{'member_ids':stage['member_ids'],'reason':stage['label'],'collisions':proof['collisions']}]
                apply_stage(scene,stage['member_ids'],stage['delta_m'],proof,stage['label'])
        lower_blocked=apply_retained_bent_lower_phases(scene)
        if lower_blocked:return lower_blocked
        apply_wall_phases(scene)
        accepted_scene.offsets=scene.offsets;accepted_scene.stages=scene.stages;accepted_scene.version=scene.version
        scene=accepted_scene
    rail='SCHEM-W-rail3-1';panel='SCHEM-W-infill-6-upper'
    if all(np.linalg.norm(scene.offsets[pid])>1 for pid in [rail,panel]) and scene.current(rail).min_gap(scene.current(panel),2e-5)<=1e-5:
        path(rail,'Leave a clear gap between the parked west rail and infill',[[0,.2,0]],[[.25*radial(2.5)],[[0,-.2,0]]])
    moved={pid for stage in scene.stages for q in stage.get('motions',[stage]) for pid in q['member_ids']}
    held=[pid for pid,p in scene.parts.items() if (p.get('is_timber') or p.get('group')=='joinery_pegs' or pid=='PLY') and pid not in moved]
    if held:blocked.append({'member_ids':held,'reason':'Historical closed joinery has no verified release in this model; no motion is invented.'})
    return blocked


def restore_verified_prefix(variant,manifest):
    from plan_architectural_disassembly import load_scene
    scene=load_scene(variant)
    assert all(manifest['sources'].get(path)==digest for path,digest in scene.sources.items()),'Prerequisite geometry source hashes changed'
    # This cached state is for planning only; the combined plan is replayed
    # independently from the assembly before publication with the current helper.
    assert manifest['verification']['status']=='PASS'
    for stage in manifest['stages']:
        for motion in stage.get('motions',[stage]):
            for pid in motion['member_ids']:scene.offsets[pid]+=np.asarray(motion['delta_m'])
    scene.stages=list(manifest['stages']);scene.version=len(scene.stages)
    return scene


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--variant',choices=VARIANTS,default='top-entry');parser.add_argument('--diagnose',action='store_true');args=parser.parse_args()
    report=diagnose(args.variant)
    print(json.dumps({'variant':args.variant,'initial_movable_count':len(report['local_elimination_rounds'][0]),
        'locally_locked_count':len(report['locally_locked_ids']),
        'coupled_release':{k:v for k,v in report['coupled_release'].items() if k not in ['coordinate_bounds','member_ids','velocities']}},indent=2))
# TIMESTAMP END 2026-11-02T15:56:09-05:00 | REVISION R004810
