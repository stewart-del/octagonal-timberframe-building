# TIMESTAMP START 2026-11-02T21:01:13-05:00 | REVISION R004875
"""Compact checked translations toward the original radial exploded layout."""
import json
import numpy as np
# TIMESTAMP START 2026-11-04T23:17:24+00:00 | REVISION R000029
from plan_architectural_disassembly import check_stage,apply_stage,attempt_path,clone_scene,underlayment_ids,spread_underlayment
# TIMESTAMP END 2026-11-04T23:17:24+00:00 | REVISION R000029

UP=np.array([0.,1.,0.])
def radial(point):
    q=np.asarray(point,float).copy();q[1]=0
    return q/np.linalg.norm(q) if np.linalg.norm(q)>1e-9 else np.array([1.,0.,0.])

def move(scene,ids,delta,label):
    if not ids:return True
    proof=check_stage(scene,ids,np.asarray(delta,float),stop_first=True)
    if proof['status']!='PASS':return proof
    apply_stage(scene,ids,np.asarray(delta,float),proof,label)
    print(scene.variant,scene.version,label,flush=True)
    return True

def route(scene,ids,target,label,directions=()):
    """Try a bounded set of continuous paths; no teleports or hidden obstacles."""
    delta=np.asarray(target,float)-scene.offsets[ids[0]]
    if np.linalg.norm(delta)<1e-10:return True
    # A blocked destination cannot be repaired by choosing a different route.
    from plan_architectural_disassembly import boxes_overlap,VOLUME_TOLERANCE_M3
    stationary={pid:scene.current(pid) for pid in scene.parts if pid not in ids}
    boxes={pid:s.bounding_box() for pid,s in stationary.items()}
    for pid in ids:
        final=scene.current(pid).translate(delta.tolist());box=final.bounding_box()
        for other,shape in stationary.items():
            if not boxes_overlap(box,boxes[other]):continue
            volume=(final^shape).volume()
            if volume>VOLUME_TOLERANCE_M3:
                return {'status':'BLOCKED','scene_version':scene.version,'member_ids':ids,'delta_m':delta.tolist(),
                    'reason':'Target endpoint is occupied','collisions':[{'moving_id':pid,'obstacle_id':other,'overlap_m3':volume,'obstacle_parked':bool(np.linalg.norm(scene.offsets[other])>1e-12)}]}
    vertical=UP*delta[1];horizontal=delta-vertical
    candidates=[[delta],[vertical,horizontal],[horizontal,vertical]]
    for direction in [UP,*directions]:
        direction=np.asarray(direction,float)
        for amount in [.15,-.15,.3,-.3,.6,-.6]:
            shift=direction*amount
            candidates.append([shift,delta-shift])
    failure=None;attempts=[]
    for candidate in candidates[:32]:
        candidate=[d for d in candidate if np.linalg.norm(d)>1e-10]
        ok,failure=attempt_path(scene,label,ids,candidate)
        if ok:
            print(scene.variant,scene.version,label,flush=True)
            return True
        attempts.append({'segments':[np.asarray(q).tolist() for q in candidate],'collisions':failure['collisions']})
    failure['attempts']=attempts
    return failure

def upper_frame(scene):
    """Short local releases before each member's original radial destination."""
    from plan_architectural_disassembly import ROOT,check_multi_stage,apply_multi_stage
    def step(pid,delta,label):
        result=move(scene,[pid],delta,label)
        if result is not True:raise RuntimeError(json.dumps(result))
    def settle(pid):
        target=np.asarray(scene.parts[pid]['exploded_offset'],float)
        result=route(scene,[pid],target,'Spread released '+pid,[radial(scene.parts[pid]['center'])])
        if result is not True:raise RuntimeError(json.dumps(result))
    try:
        if 'M-TMP' in scene.parts:
            step('M-TMP',-UP*.15,'Disengage welded support');settle('M-TMP')
        for k in range(8):
            for side in ['0','2']:
                pid=f'J{k}-{side}';step(pid,UP*.3,'Withdraw short rafter '+pid);settle(pid)
        for k in range(8):
            pid=f'CR{k}';step(pid,UP*.15,'Withdraw cupola rafter '+pid);settle(pid)
        step('PLY',UP*.1,'Disengage cupola plywood');settle('PLY')
        for k in range(8):
            pid=f'CC{k}';r=radial(scene.parts[pid]['center']);t=np.array([-r[2],0,r[0]])
            for delta in [-UP*.3,t*.2,r*1.8,UP*5.3]:step(pid,delta,'Release ceiling spoke '+pid)
            settle(pid)
        for k in range(8):
            pid=f'CP{k}';step(pid,np.asarray(scene.parts[pid]['exploded_offset'])*.75,'Withdraw cupola foot peg '+pid);settle(pid)
        ids=[f'{prefix}{k}{suffix}' for k in range(8) for prefix,suffix in [('R',''),('C',''),('L','-S'),('L','-H')]]
        result=move(scene,ids,UP*.3,'Disengage cupola feet and main rafter seats')
        if result is not True:return [result]
        for k in range(8):
            pid=f'R{k}';step(pid,radial(scene.parts[pid]['center'])*.3-UP*.1,'Withdraw principal rafter tongue '+pid);settle(pid)
        prototype=json.loads((ROOT/'docs/cupola-foot-prototype.json').read_text())['conditional_primary_test']['stages']
        stage=next(q for q in prototype if q['label']=='Open cupola ring tenons simultaneously')
        proof=check_multi_stage(scene,stage['motions'],stop_first=True)
        if proof['status']!='PASS':return [proof]
        apply_multi_stage(scene,stage['motions'],proof,stage['label'])
        for k in range(8):settle(f'C{k}')
        for k in range(8):
            for suffix in ['H','S']:settle(f'L{k}-{suffix}')
    except RuntimeError as error:return [json.loads(str(error))]
    return []

def roof_and_windows(scene):
    failures=[]
    def require(result):
        if result is not True:failures.append(result);return False
        return True
    cover=[pid for pid,p in scene.parts.items() if p.get('roofLayer')]
    n=radial(scene.parts['MUD-POST-L-BACK']['center'])
    if cover:
        if not require(move(scene,cover,UP*.15,'Disengage porch roof covering')):return failures
        if not require(route(scene,cover,n*2.5+UP*.7,'Spread released porch roof covering')):return failures
    copper=[pid for pid in scene.parts if pid.startswith('ROOF-COPPER-')]
    if not require(move(scene,copper,UP*.15,'Disengage cupola covering')):return failures
    if not require(route(scene,copper,UP*6.5,'Spread released cupola covering')):return failures
    for k in range(8):
        ids=[pid for pid,p in scene.parts.items() if pid.startswith('ROOF-CEDAR-') and p['roof_face']==k]
        a=-(k+.5)*np.pi/4;n=np.array([np.cos(a),0,np.sin(a)])
        if not require(move(scene,ids,UP*.3,'Disengage cedar roof face '+str(k+1))):return failures
        if not require(route(scene,ids,n*4.2+UP*3.6,'Spread released cedar roof face '+str(k+1),[n])):return failures
    for k in range(8):
        ids=[pid for pid in scene.parts if pid.startswith('SCHEM-CUP-WINDOW-'+str(k)+'-')]
        a=-(k+.5)*np.pi/4;n=np.array([np.cos(a),0,np.sin(a)])
        if not require(move(scene,ids,n*.12,'Disengage cupola window '+str(k+1))):return failures
        if not require(route(scene,ids,n*3+UP*4,'Spread released cupola window '+str(k+1),[n])):return failures
    return failures

def floor_frame(scene):
    """Separate the north-south joists above the eight radial support beams."""
    failures=[]
    def check(result):
        if result is not True:failures.append(result);return False
        return True
    def slide(pid,target):
        return check(route(scene,[pid],target,'Spread released '+pid,[radial(scene.parts[pid]['center'])]))
    ids=[pid for pid,p in scene.parts.items() if p.get('schematicKind') in ['floor','floorAssembly']]
    if not check(move(scene,ids,-UP,'Disengage floor and supports below the main posts')):return failures
    for pid in ids:
        if pid.startswith(('SCHEM-FLOOR-SECTOR-','FLOOR-BAMBOO-CENTER-')):
            if not check(move(scene,[pid],UP*.1,'Lift floor finish '+pid)):return failures
            radius=2.8 if pid.startswith('FLOOR-BAMBOO-CENTER-') else 3.5
            if not slide(pid,radial(scene.parts[pid]['center'])*radius-UP*.4):return failures
    for pid in ids:
        if pid.startswith('POST-BEARING-STAND-') and pid.endswith('-HEAD'):
            if not check(move(scene,[pid],UP*.3,'Lift bearing head '+pid)):return failures
            if not slide(pid,radial(scene.parts[pid]['center'])*3-UP*.7):return failures
# TIMESTAMP START 2026-11-04T23:17:24+00:00 | REVISION R000029
    for pid in underlayment_ids(scene):
        if not check(move(scene,[pid],UP*.25,'Lift cut sheet off the joists '+pid)):return failures
# TIMESTAMP END 2026-11-04T23:17:24+00:00 | REVISION R000029
    east=np.array([np.sin(np.pi/8),0,np.cos(np.pi/8)])
    joists=sorted([pid for pid in ids if pid.startswith('FLOOR-JOIST-')],key=lambda pid:-abs(np.asarray(scene.parts[pid]['center'])@east))
    for pid in joists:
        if not check(move(scene,[pid],UP*.21,'Disengage north-south joist '+pid)):return failures
        lateral=float(np.asarray(scene.parts[pid]['center'])@east);sign=1 if lateral>=0 else -1
        distance=4.3 if sign>0 else 4.3-.2*max(0,abs(lateral)-.4064)
        if not slide(pid,sign*east*distance-UP*.79):return failures
    for k in range(8):
        a=-(k+.5)*np.pi/4;n=np.array([np.cos(a),0,np.sin(a)]);t=np.array([np.sin(a),0,-np.cos(a)])
        rim='FLOOR-RIM-'+str(k);left='POST-BEARING-STAND-'+str(k)+'-SIDE-1';right='POST-BEARING-STAND-'+str((k+1)%8)+'-SIDE1'
        if not check(move(scene,[rim,left,right],n*3,'Withdraw rim and its notched side plates '+str(k))):return failures
        if not check(move(scene,[left],-t*.3,'Disengage first rim side plate '+str(k))):return failures
        if not check(move(scene,[right],t*.3,'Disengage second rim side plate '+str(k))):return failures
    for pid in ids:
        if pid.startswith('FLOOR-BEAM-') and not check(move(scene,[pid],radial(scene.parts[pid]['center'])*3,'Withdraw radial floor beam '+pid)):return failures
    for pid in ids:
        if pid.startswith('PIER-') and not pid.endswith('-BELOW'):
            pair=[pid,pid+'-BELOW']
            if not check(move(scene,pair,-UP*1.15,'Disengage support '+pid)):return failures
            if not check(move(scene,pair,radial(scene.parts[pid]['center'])*1.5,'Spread support '+pid)):return failures
            if not check(move(scene,[pid+'-BELOW'],-UP*.12,'Separate buried column '+pid)):return failures
    beams=[pid for pid in ids if pid.startswith('FLOOR-BEAM-')]
    if not check(move(scene,beams,-UP*.5,'Separate radial beams beneath the floor layers')):return failures
    if not slide('FLOOR-CENTRAL-HUB',-UP*1.8):return failures
# TIMESTAMP START 2026-11-04T23:17:24+00:00 | REVISION R000029
    if not check(route(scene,underlayment_ids(scene),-UP*1.2,'Lower cut underlayment sheets')):return failures
    spread_underlayment(scene)
# TIMESTAMP END 2026-11-04T23:17:24+00:00 | REVISION R000029
    return failures

def wall_prefix(scene):
    """Open exterior-entry housings before extracting the main brace pegs."""
    failures=[]
    faces=['N','NW','W','SW','S','SE','E','NE']
    for face in ['NW','SW','SE','E','NE','N','S']:
        k=faces.index(face);a=-(k+.5)*np.pi/4;n=np.array([np.cos(a),0,np.sin(a)])
        ids=[pid for pid,p in scene.parts.items() if p.get('face')==face and p.get('schematicKind') in ['wall','rail']]
        result=move(scene,ids,n*.4,'Disengage '+face+' wall sockets from main posts')
        if result is not True:return [result]
    for pid,p in scene.parts.items():
        if not pid.startswith('MAIN-PEG-'):continue
        direction=np.asarray(p['withdrawal_direction'],float);distance=p['withdrawal_distance_m']+.25
        for sign in [1,-1]:
            result=move(scene,[pid],direction*distance*sign,'Withdraw and clear main peg '+pid)
            if result is True:break
        if result is not True:failures.append(result)
    return failures

def wall_target(p):
    faces=['N','NW','W','SW','S','SE','E','NE'];k=faces.index(p['face']);a=-(k+.5)*np.pi/4
    n=np.array([np.cos(a),0,np.sin(a)]);t=np.array([-n[2],0,n[0]]);c=np.asarray(p['center'])
    distance=3.0 if p.get('schematicKind')=='rail' else 2.1
    if p.get('framingRole')=='jamb':distance=2.75
    if '-rail0-' in p['id']:distance=2.5
    return n*distance+t*(c@t)*.15+UP*(c[1]-1.2)*.2,n

def loose_walls(scene):
    """Release donor rails before jambs and sills, retrying real constraints."""
    ids=[pid for pid,p in scene.parts.items() if p.get('schematicKind') in ['rail','wall','shelf']]
    pending=[]
    for pid in ids:
        target,n=wall_target(scene.parts[pid])
        if np.linalg.norm(scene.offsets[pid]-target)>1e-8:pending.append(pid)
    for _ in range(3):
        before=scene.version
        for pid in pending[:]:
            p=scene.parts[pid];target,n=wall_target(p);trial=clone_scene(scene)
            if p.get('schematicKind')=='shelf':
                delta=-UP*min(.25,max(0.,p['center'][1]+scene.offsets[pid][1]+.25))
            elif pid in ['SCHEM-W-rail0-0','SCHEM-W-rail0-1'] and np.linalg.norm(scene.offsets[pid])<.15:
                delta=-UP*.25
            else:delta=n*.12
            if np.linalg.norm(delta)>1e-10:
                proof=check_stage(trial,[pid],delta,stop_first=True)
                if proof['status']!='PASS':continue
                apply_stage(trial,[pid],delta,proof,'Disengage wall member '+pid)
            reached=route(trial,[pid],target,'Spread released wall member '+pid,[n]) is True
            scene.offsets=trial.offsets;scene.stages=trial.stages;scene.version=trial.version
            if reached:pending.remove(pid)
        if scene.version==before:break
    return pending

def carried_ids(scene,ids):
    result=list(ids)
    for post,rail in [('P2','SCHEM-W-rail0-0'),('P3','SCHEM-W-rail0-1')]:
        if post in ids and rail not in result and np.linalg.norm(scene.offsets[post]-scene.offsets[rail])<1e-8:result.append(rail)
    for post in ids:
        if not (len(post)==2 and post[0]=='P' and post[1].isdigit()):continue
        k=post[1]
        for pid in scene.parts:
            if pid in result or not pid.startswith(('K'+k+'-','MAIN-PEG-K'+k+'-')):continue
            if np.linalg.norm(scene.offsets[pid])>1e-8 and np.linalg.norm(scene.offsets[pid]-scene.offsets[post])<.8:result.append(pid)
    if any(len(pid)==2 and pid.startswith('P') for pid in ids):
        for brace,stem in [('K2-B','2'),('K3-A','6')]:
            if brace not in result:continue
            for side in ['lower','upper']:
                panel=f'SCHEM-W-infill-{stem}-{side}'
                if panel not in result and np.linalg.norm(scene.offsets[panel]-scene.offsets[brace])<.8:result.append(panel)
    return result

def settle_primary(scene,pid,prefix=()):
    p=scene.parts[pid]
    target=wall_target(p)[0] if p.get('schematicKind') in ['wall','rail','shelf'] else np.asarray(p['exploded_offset'],float)
    r=radial(p['center']);t=np.array([-r[2],0,r[0]])
    ids=carried_ids(scene,[pid])
    for correction in [np.zeros(3),t*.15,-t*.15,t*.3,-t*.3,UP*.3,-UP*.3]:
        trial=clone_scene(scene)
        if prefix:
            ok,result=attempt_path(trial,'Disengage '+pid,ids,prefix)
            if not ok:continue
        result=route(trial,ids,target+correction,'Spread released '+pid,[r,t])
        if result is True:
            scene.offsets=trial.offsets;scene.stages=trial.stages;scene.version=trial.version
            return True
    return result

def lower_frame(scene):
    """Release accessible walls and braces before opening retained shelf bents."""
    from plan_main_disassembly import apply_retained_bent_lower_phases
    loose_walls(scene)
    for _ in range(3):
        before=scene.version
        for pid,p in scene.parts.items():
            joint=p.get('main_face_brace_joinery')
            if not joint or np.linalg.norm(scene.offsets[pid])>1e-8:continue
            n=np.asarray(joint['withdrawal_world'])
            if pid in ['K2-B','K3-A']:
                stem='2' if pid=='K2-B' else '6';companions=[f'SCHEM-W-infill-{stem}-{side}' for side in ['lower','upper']]
                companions=[q for q in companions if np.linalg.norm(scene.offsets[q])<.75]
                if companions:
                    trial=clone_scene(scene);axis=np.asarray(joint['axis_end'])-joint['axis_start'];axis/=np.linalg.norm(axis)
                    if move(trial,[pid,*companions],n*.12,'Disengage west brace with fitted infill '+pid) is not True:continue
                    if move(trial,[pid],axis*.15,'Slide brace free from west infill '+pid) is not True:continue
                    scene.offsets=trial.offsets;scene.stages=trial.stages;scene.version=trial.version
                    continue
            # Clear the housings now; final radial placement follows perimeter release.
            if move(scene,[pid],n*.25,'Disengage face-housed brace '+pid) is not True:
                move(scene,[pid],n*.12,'Disengage face-housed brace '+pid)
        loose_walls(scene)
        if scene.version==before:break
    with open('/tmp/octagon-compact-ready-bents.json','w') as stream:
        json.dump({'phase':'ready-bents','sources':scene.sources,'stages':scene.stages},stream)
    return finish_lower(scene)

def finish_lower(scene):
    from plan_main_disassembly import apply_retained_bent_lower_phases
    result=move(scene,['MAIN-PEG-K4-B-B4'],-UP*.15,'Clear the released south peg from the tie route')
    if result is not True:return [result]
    blocked=apply_retained_bent_lower_phases(scene,compact=True)
    if blocked:return blocked
    for pid,p in scene.parts.items():
        if p.get('main_face_brace_joinery'):
            result=settle_primary(scene,pid)
            if result is not True:return [result]
    pending=loose_walls(scene)
    return [{'member_ids':pending,'reason':'Wall members still need a checked compact destination'}] if pending else []

# TIMESTAMP START 2026-11-03T06:36:08-05:00 | REVISION R004891
def complete_plan(scene):
    """Replay the retained compact route against current occupied solids."""
    from plan_architectural_disassembly import ROOT,check_multi_stage,apply_multi_stage
    recipe=json.loads((ROOT/'scripts/compact-disassembly-route.json').read_text())
    assert scene.variant==recipe['variant'] and scene.version==0
    assert all(scene.sources.get(name)==digest for name,digest in recipe['sources'].items()),'Compact route geometry changed; replan before publication'
    for stage in recipe['stages']:
        if 'motions' in stage:
            proof=check_multi_stage(scene,stage['motions'],stop_first=True)
            if proof['status']!='PASS':return [{'member_ids':stage['member_ids'],'reason':stage['label'],'collisions':proof['collisions']}]
            apply_multi_stage(scene,stage['motions'],proof,stage['label'],stage['id'])
        else:
            proof=check_stage(scene,stage['member_ids'],stage['delta_m'],stop_first=True)
            if proof['status']!='PASS':return [{'member_ids':stage['member_ids'],'reason':stage['label'],'collisions':proof['collisions']}]
            apply_stage(scene,stage['member_ids'],stage['delta_m'],proof,stage['label'],stage['id'])
    return []

if __name__=='__main__':
    from plan_architectural_disassembly import load_scene,audit_initial_scene,audit_final_joinery
    scene=load_scene('top-entry');assert audit_initial_scene(scene)['status']=='PASS'
    blocked=complete_plan(scene)
    separation=audit_final_joinery(scene)
    assert not blocked and separation['status']=='PASS',(blocked,separation)
    print(json.dumps({'status':'PASS','stage_count':len(scene.stages),'physical_piece_count':len(scene.parts),'final_mating_separation':separation}))
# TIMESTAMP END 2026-11-03T06:36:08-05:00 | REVISION R004891
# TIMESTAMP END 2026-11-02T21:01:13-05:00 | REVISION R004875
