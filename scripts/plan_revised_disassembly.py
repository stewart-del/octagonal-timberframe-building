# TIMESTAMP START 2026-11-04T23:48:03+00:00 | REVISION R000012
# TIMESTAMP START 2026-11-04T23:23:25+00:00 | REVISION R000011
# TIMESTAMP START 2026-11-03T16:08:22-05:00 | REVISION R005049
"""Replan the saved compact sequence against the revised physical members."""
from pathlib import Path
# TIMESTAMP START 2026-11-04T12:46:13+00:00 | REVISION R000003
import argparse,json,os
# TIMESTAMP END 2026-11-04T12:46:13+00:00 | REVISION R000003
import numpy as np
from plan_architectural_disassembly import (ROOT,load_scene,check_stage,check_multi_stage,
    apply_stage,apply_multi_stage,audit_initial_scene,audit_final_joinery,clone_scene,attempt_path)
from plan_compact_disassembly import route,move,radial,loose_walls,settle_primary,wall_target
from plan_porch_disassembly import apply_porch_phases

# TIMESTAMP START 2026-11-04T12:46:13+00:00 | REVISION R000003
CHECKPOINT_DIRECTORY=Path(os.environ.get('OCTAGON_CHECKPOINT_DIR',ROOT/'.codex-runtime/disassembly'))
CHECKPOINT_DIRECTORY.mkdir(parents=True,exist_ok=True)
CHECKPOINT=CHECKPOINT_DIRECTORY/'route-checkpoint.json'
FAILURE=CHECKPOINT_DIRECTORY/'route-failure.json'
# TIMESTAMP END 2026-11-04T12:46:13+00:00 | REVISION R000003
UP=np.array([0.,1.,0.])
# TIMESTAMP START 2026-11-03T16:49:21-05:00 | REVISION R005060
precleared=set()
# TIMESTAMP END 2026-11-03T16:49:21-05:00 | REVISION R005060
# TIMESTAMP START 2026-11-04T20:23:51+00:00 | REVISION R000022
deferred_shelves=set()
# TIMESTAMP END 2026-11-04T20:23:51+00:00 | REVISION R000022
def save(scene,phase,index=0):
    # TIMESTAMP START 2026-11-04T20:23:51+00:00 | REVISION R000022
    CHECKPOINT.write_text(json.dumps({'variant':scene.variant,'sources':scene.sources,'phase':phase,'index':index,'stages':scene.stages,'precleared':sorted(precleared),'deferred_shelves':sorted(deferred_shelves)},separators=(',',':'))+'\n')
    # TIMESTAMP END 2026-11-04T20:23:51+00:00 | REVISION R000022
def require(result):
    assert result is True,result
# TIMESTAMP START 2026-11-04T23:17:24+00:00 | REVISION R000029
from plan_architectural_disassembly import expand_underlayment_stage,spread_underlayment

def replay_one(scene,stage):
    expanded=expand_underlayment_stage(scene,stage)
    if any(pid=='FLOOR-SUBFLOOR' for q in stage.get('motions',[stage]) for pid in q['member_ids']):
        for replacement in expanded:replay_one(scene,replacement)
        return
# TIMESTAMP END 2026-11-04T23:17:24+00:00 | REVISION R000029
    if all(pid in precleared for motion in stage.get('motions',[stage]) for pid in motion['member_ids']):return
    # TIMESTAMP START 2026-11-04T20:23:51+00:00 | REVISION R000022
    if all(pid in deferred_shelves for motion in stage.get('motions',[stage]) for pid in motion['member_ids']):return
    # TIMESTAMP END 2026-11-04T20:23:51+00:00 | REVISION R000022
    if 'motions' in stage:
        proof=check_multi_stage(scene,stage['motions'],stop_first=True)
        assert proof['status']=='PASS',(stage['label'],proof)
        apply_multi_stage(scene,stage['motions'],proof,stage['label'])
    # TIMESTAMP START 2026-11-03T16:49:21-05:00 | REVISION R005060
    else:
        result=move(scene,stage['member_ids'],stage['delta_m'],stage['label'])
        if result is not True and len(stage['member_ids'])==1:
            other=result['collisions'][0]['obstacle_id']
            if scene.parts[other].get('schematicKind') in ['wall','rail'] and other not in precleared:
                target,n=wall_target(scene.parts[other])
                released=settle_primary(scene,other,prefix=[n*.12])
                if released is True:
                    precleared.add(other)
                    result=move(scene,stage['member_ids'],stage['delta_m'],stage['label'])
        if result is not True:
            hit=result['collisions'][0];other=hit['obstacle_id']
            if hit['obstacle_parked'] and other.startswith('MAIN-PEG-'):
                for amount in [.1,.2,.4,.8]:
                    if result is True:break
                    for direction in [UP,-UP,np.array([1,0,0]),np.array([-1,0,0]),np.array([0,0,1]),np.array([0,0,-1])]:
                        trial=clone_scene(scene)
                        if move(trial,[other],direction*amount,'Clear released peg from wall route '+other) is not True:continue
                        retry=move(trial,stage['member_ids'],stage['delta_m'],stage['label'])
                        if retry is not True:continue
                        scene.offsets=trial.offsets;scene.stages=trial.stages;scene.version=trial.version;result=True;break
        # TIMESTAMP START 2026-11-04T20:23:51+00:00 | REVISION R000022
        if result is not True and len(stage['member_ids'])==1:
            pid=stage['member_ids'][0]
            if scene.parts[pid].get('schematicKind')=='shelf':
                # Clear movable parked pegs first. A shelf still trapped by
                # the longer brace stays physically present until it releases.
                deferred_shelves.add(pid)
                print('Retain shelf until inward support clears',pid,flush=True)
                return
        # TIMESTAMP END 2026-11-04T20:23:51+00:00 | REVISION R000022
        require(result)
    # TIMESTAMP END 2026-11-03T16:49:21-05:00 | REVISION R005060
def lower_frame(scene):
    # Withdraw the tie and its inward knee together, then lower the knee off
    # its vertical head tenon. The posts and outer ring remain in place.
    for k in range(8):
        tie=f'T{k}';brace=f'K{k}-C';r=radial(scene.parts[tie]['center'])
        # TIMESTAMP START 2026-11-03T17:12:03-05:00 | REVISION R005068
        if np.allclose(scene.offsets[tie],scene.parts[tie]['exploded_offset'],atol=1e-10):continue
        # TIMESTAMP END 2026-11-03T17:12:03-05:00 | REVISION R005068
        # TIMESTAMP START 2026-11-04T20:23:51+00:00 | REVISION R000022
        def release(ids,delta,label):
            result=move(scene,ids,delta,label)
            if result is not True:
                other=result['collisions'][0]['obstacle_id']
                if scene.parts[other].get('schematicKind')=='shelf':
                    deferred_shelves.discard(other)
                    replay_one(scene,{'member_ids':[other],'delta_m':(-UP*.25).tolist(),
                        'label':'Lower retained shelf before inward support release '+other})
                    result=move(scene,ids,delta,label)
            require(result)
        release([tie,brace],-r*.12,'Withdraw radial tie and inward brace '+str(k))
        release([brace],-UP*.1,'Lower inward brace from tie mortise '+str(k))
        # TIMESTAMP END 2026-11-04T20:23:51+00:00 | REVISION R000022
        # TIMESTAMP START 2026-11-03T17:12:03-05:00 | REVISION R005068
        target=np.asarray(scene.parts[brace]['exploded_offset'])
        tangent=np.array([-r[2],0,r[0]])
        result=route(scene,[brace],target,'Spread released '+brace,[tangent,r])
        if result is not True:
            delta=target-scene.offsets[brace]
            for width in [.3,-.3,.5,-.5,.8,-.8]:
                ok,result=attempt_path(scene,'Carry released brace around post '+brace,[brace],
                    [tangent*width,delta,-tangent*width])
                if ok:result=True;break
        require(result)
        # TIMESTAMP END 2026-11-03T17:12:03-05:00 | REVISION R005068
        require(route(scene,[tie],np.asarray(scene.parts[tie]['exploded_offset']),'Spread released '+tie,[r,np.array([-r[2],0,r[0]])]))
    # TIMESTAMP START 2026-11-03T17:12:03-05:00 | REVISION R005068
    if np.linalg.norm(scene.offsets['M-TMP'])<1e-10:
        require(move(scene,['M-TMP'],-UP*.15,'Release eight-L support after all trusses are clear'))
        require(route(scene,['M-TMP'],np.asarray(scene.parts['M-TMP']['exploded_offset']),'Spread released eight-L support'))
    beams=[f'B{k}' for k in range(8)]
    if all(np.linalg.norm(scene.offsets[pid])<1e-10 for pid in beams):
        require(move(scene,beams,UP*.12,'Lift octagon beams from open-top post mortises and centered brace heads'))
    loose_walls(scene)
    for pid in beams:
        require(route(scene,[pid],np.asarray(scene.parts[pid]['exploded_offset']),'Spread released '+pid,[radial(scene.parts[pid]['center'])]))
    perimeter=[];held=[]
    for k in range(8):
        for suffix in ['A','B']:
            pid=f'K{k}-{suffix}';p=scene.parts[pid];direction=np.asarray(p['axis_end'])-p['axis_start'];direction[1]=0;direction/=np.linalg.norm(direction)
            if np.linalg.norm(scene.offsets[pid])<1e-10:
                result=move(scene,[pid],direction*.12,'Withdraw centered perimeter brace '+pid)
                if result is not True:held.append((pid,result))
            perimeter.append(pid)
    for pid,blocked in held:
        k=int(pid[1]);companion=f"K{k}-{'A' if pid.endswith('B') else 'B'}";post=f'P{k}'
        p=scene.parts[pid];axis=np.asarray(p['axis_end'])-p['axis_start'];axis/=np.linalg.norm(axis)
        horizontal=axis.copy();horizontal[1]=0;horizontal/=np.linalg.norm(horizontal)
        carried=[post,companion,*[q for q in scene.parts if q.startswith(f'MAIN-PEG-K{k}-')]]
        require(move(scene,carried,-horizontal*1.2,'Move post and cleared pegs away from retained shelf brace '+pid))
        require(move(scene,[pid],-axis*1.2,'Slide brace axially below fitted shelf '+pid))
    for pid in perimeter:
        p=scene.parts[pid];r=radial(p['center']);t=np.array([-r[2],0,r[0]])
        target=np.asarray(p['exploded_offset']);result=route(scene,[pid],target,'Spread released '+pid,[r,t])
        if result is not True:
            delta=target-scene.offsets[pid]
            for height in [.9,1.2,1.5,1.8,2.1]:
                ok,result=attempt_path(scene,'Carry released brace above parked walls '+pid,[pid],[UP*height,delta,-UP*height])
                if ok:result=True;break
        require(result)
    # TIMESTAMP END 2026-11-03T17:12:03-05:00 | REVISION R005068
    for k in range(8):
        pid=f'P{k}';r=radial(scene.parts[pid]['center'])
        # TIMESTAMP START 2026-11-03T17:12:03-05:00 | REVISION R005068
        require(settle_primary(scene,pid))
        # TIMESTAMP END 2026-11-03T17:12:03-05:00 | REVISION R005068
    # TIMESTAMP START 2026-11-04T12:46:13+00:00 | REVISION R000003
    loose_walls(scene)
    save(scene,'walls-final')
    finish_walls(scene)

def finish_walls(scene):
    """Finish released walls without reapplying a blocked joint withdrawal."""
    def finish_one(trial,pid):
        target,n=wall_target(trial.parts[pid]);tangent=np.array([-n[2],0,n[0]])
        result=route(trial,[pid],target,'Finish released wall '+pid,[n,tangent])
        if result is True or result.get('reason')=='Target endpoint is occupied':return result
        delta=target-trial.offsets[pid]
        for direction in [UP,tangent,n]:
            for amount in [.3,-.3,.6,-.6,.9,-.9,1.2,-1.2]:
                shift=direction*amount
                ok,proof=attempt_path(trial,'Detour released wall around parked post '+pid,[pid],[shift,delta,-shift])
                if ok:return True
        return result
    pending=[pid for pid,p in scene.parts.items()
        if p.get('schematicKind') in ['wall','rail','shelf']
        and np.linalg.norm(scene.offsets[pid]-wall_target(p)[0])>1e-8]
    # The two downward-entry west rails must separate from their carried posts.
    pending.sort(key=lambda pid:0 if '-rail0-' in pid else 1)
    occupied={}
    for pid in pending:
        result=finish_one(scene,pid)
        if result is True:
            save(scene,'walls-final')
            continue
        obstacle=result['collisions'][0]['obstacle_id']
        assert result.get('reason')=='Target endpoint is occupied' and obstacle in ['MUD-POST-L-BACK','MUD-POST-R-BACK'],(pid,result)
        occupied.setdefault(obstacle,[]).append(pid)
    for post,ids in occupied.items():
        normal=wall_target(scene.parts[ids[0]])[1]
        for distance in [.15,.3,.45,.6,.9]:
            trial=clone_scene(scene)
            result=move(trial,[post],normal*distance,'Move parked porch post farther outward to clear wall destinations '+post)
            if result is not True:continue
            for pid in ids:
                result=finish_one(trial,pid)
                if result is not True:break
            if result is True:
                scene.offsets=trial.offsets;scene.stages=trial.stages;scene.version=trial.version
                save(scene,'walls-final')
                break
        require(result)
    assert not loose_walls(scene),'Wall members remain held after frame release'
    # TIMESTAMP END 2026-11-04T12:46:13+00:00 | REVISION R000003

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--resume',action='store_true');parser.add_argument('--stop-after',choices=['roof','porch','floor','walls','lower']);args=parser.parse_args()
    # TIMESTAMP START 2026-11-04T12:46:13+00:00 | REVISION R000003
    old=json.loads((ROOT/'scripts/revised-disassembly-seed.json').read_text());scene=load_scene('top-entry');phase='roof';index=0
    # TIMESTAMP END 2026-11-04T12:46:13+00:00 | REVISION R000003
    if args.resume and CHECKPOINT.exists():
        saved=json.loads(CHECKPOINT.read_text());precleared.update(saved.get('precleared',[]));assert saved['sources']==scene.sources,'Checkpoint geometry changed'
        # TIMESTAMP START 2026-11-04T20:23:51+00:00 | REVISION R000022
        deferred_shelves.update(saved.get('deferred_shelves',[]))
        # TIMESTAMP END 2026-11-04T20:23:51+00:00 | REVISION R000022
        scene.stages=saved['stages'];scene.version=len(scene.stages);phase=saved['phase'];index=saved['index']
        for stage in scene.stages:
            for motion in stage.get('motions',[stage]):
                for pid in motion['member_ids']:scene.offsets[pid]+=motion['delta_m']
    else:
        initial=audit_initial_scene(scene);assert initial['status']=='PASS',initial['collisions']
    try:
        if phase=='roof':
            for i in range(index,190):replay_one(scene,old['stages'][i]);save(scene,'roof',i+1)
            phase='porch';save(scene,phase)
            if args.stop_after=='roof':return
        if phase=='porch':
            result=apply_porch_phases(scene,skip_cover=True,parking_scale=.5)
            assert result['status']=='PASS',result
            phase='floor';save(scene,phase,274);index=274
            if args.stop_after=='porch':return
        if phase=='floor':
            for i in range(max(index,274),470):replay_one(scene,old['stages'][i]);save(scene,'floor',i+1)
            phase='walls';save(scene,phase,470);index=470
            if args.stop_after=='floor':return
        if phase=='walls':
            for i in range(max(index,470),875):
                stage=old['stages'][i]
                if len(stage.get('member_ids',[]))==1 and stage['member_ids'][0].startswith('MAIN-PEG-'):
                    pid=stage['member_ids'][0];p=scene.parts[pid]
                    if np.linalg.norm(scene.offsets[pid])<1e-10:
                        direction=np.asarray(p['withdrawal_direction'])*(p['withdrawal_distance_m']+.01)
                        result=move(scene,[pid],direction,'Withdraw actual centered-joint peg '+pid)
                        if result is not True:result=move(scene,[pid],-direction,'Withdraw actual centered-joint peg '+pid)
                        require(result)
                else:replay_one(scene,stage)
                save(scene,'walls',i+1)
            phase='lower';save(scene,phase)
            if args.stop_after=='walls':return
        # TIMESTAMP START 2026-11-04T12:46:13+00:00 | REVISION R000003
        if phase=='lower':
            lower_frame(scene);phase='complete';save(scene,phase)
        if phase=='walls-final':
            finish_walls(scene);phase='complete';save(scene,phase)
        # TIMESTAMP END 2026-11-04T12:46:13+00:00 | REVISION R000003
        # TIMESTAMP START 2026-11-04T23:17:24+00:00 | REVISION R000029
        spread_underlayment(scene);save(scene,'complete')
        # TIMESTAMP END 2026-11-04T23:17:24+00:00 | REVISION R000029
        separation=audit_final_joinery(scene);assert separation['status']=='PASS',separation
        moved={pid for s in scene.stages for q in s.get('motions',[s]) for pid in q['member_ids']}
        fixed={'FLOOR-CENTRAL-HUB','PIER-C','PIER-C-BELOW'}
        assert set(scene.parts)-moved==fixed,sorted(set(scene.parts)-moved-fixed)
        print('PASS',len(scene.stages),'stages; all physical pieces accounted for',flush=True)
    except BaseException:
        # TIMESTAMP START 2026-11-04T12:46:13+00:00 | REVISION R000003
        # TIMESTAMP START 2026-11-04T20:23:51+00:00 | REVISION R000022
        FAILURE.write_text(json.dumps({'phase':phase,'sources':scene.sources,'stages':scene.stages,'precleared':sorted(precleared),'deferred_shelves':sorted(deferred_shelves)},separators=(',',':'))+'\n')
        # TIMESTAMP END 2026-11-04T20:23:51+00:00 | REVISION R000022
        # TIMESTAMP END 2026-11-04T12:46:13+00:00 | REVISION R000003
        raise

if __name__=='__main__':main()
# TIMESTAMP END 2026-11-03T16:08:22-05:00 | REVISION R005049

# TIMESTAMP END 2026-11-04T23:23:25+00:00 | REVISION R000011

# TIMESTAMP END 2026-11-04T23:48:03+00:00 | REVISION R000012
