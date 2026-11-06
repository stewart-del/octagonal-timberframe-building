# TIMESTAMP START 2026-11-04T23:48:03+00:00 | REVISION R000012
# TIMESTAMP START 2026-11-04T23:23:25+00:00 | REVISION R000011
# TIMESTAMP START 2026-11-04T20:45:07+00:00 | REVISION R000009
# TIMESTAMP START 2026-11-04T20:00:49+00:00 | REVISION R000006
"""Continuously checked reverse of the owner's requested construction order.

Checkpoints are planning evidence only. Publication requires the independent
complete-certificate replay with all parked pieces retained as obstacles.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import numpy as np
from plan_architectural_disassembly import (ROOT,load_scene,check_stage,apply_stage,
    check_multi_stage,apply_multi_stage,clone_scene,attempt_path,audit_initial_scene,audit_final_joinery)
from plan_compact_disassembly import move,route,radial
from plan_porch_disassembly import apply_porch_phases

UP=np.array([0.,1.,0.])
DIRECTORY=Path(os.environ.get('OCTAGON_CONSTRUCTION_DIR',ROOT/'.codex-runtime/construction'))
DIRECTORY.mkdir(parents=True,exist_ok=True)
CHECKPOINT=DIRECTORY/'checkpoint.json'
FAILURE=DIRECTORY/'failure.json'
phase='finish';introductions={};phase_ranges={}
# TIMESTAMP START 2026-11-04T20:45:07+00:00 | REVISION R000009
COMPACT=json.loads((ROOT/'scripts/compact-construction-endpoints.json').read_text())['offsets']
def compact_target(scene,pid):
    p=scene.parts[pid]
    if p.get('floorRole')=='underlayment_sheet':return np.asarray(COMPACT[pid])
    if p.get('erectionParentId'):
        parent=p['erectionParentId'];siblings=[r for r in scene.parts.values() if r.get('erectionParentId')==parent]
        center=np.mean([r['center'] for r in siblings],axis=0)
        return np.asarray(COMPACT[parent])+(np.asarray(p['center'])-center)*.001
    return np.asarray(COMPACT[pid]) if pid in COMPACT else None
# TIMESTAMP END 2026-11-04T20:45:07+00:00 | REVISION R000009

def moving(stage):return [pid for motion in stage.get('motions',[stage]) for pid in motion['member_ids']]
def require(value):
    if value is not True:raise RuntimeError(json.dumps(value))
def checked(scene,ids,delta,label,introduce=False):
    if not ids:return
    index=len(scene.stages)
    require(move(scene,ids,delta,label))
    if introduce:
        for pid in ids:introductions.setdefault(pid,index)
# TIMESTAMP START 2026-11-04T20:45:07+00:00 | REVISION R000009
def park(scene,ids,target,label,directions=()):
    preferred=[compact_target(scene,pid) for pid in ids]
    if all(p is not None and np.linalg.norm(p-preferred[0])<1e-9 for p in preferred):
        try:park_at(scene,ids,preferred[0],label+' at compact destination',directions);return
        except RuntimeError:pass
    return park_at(scene,ids,target,label,directions)

def park_at(scene,ids,target,label,directions=()):
# TIMESTAMP END 2026-11-04T20:45:07+00:00 | REVISION R000009
    target=np.asarray(target);result=route(scene,ids,target,label,directions)
    if result is True:return
    if result.get('reason')=='Target endpoint is occupied':require(result)
    delta=target-scene.offsets[ids[0]];vertical=UP*delta[1]
    for height in [1.2,1.8,2.5,3.5,4.,4.5,6.,-.8,-1.5]:
        shift=UP*height
        for segments in [[shift,delta,-shift],[shift,delta-vertical,vertical-shift]]:
            ok,result=attempt_path(scene,label,ids,segments)
            if ok:return
    for axis in directions:
        axis=np.asarray(axis);axis[1]=0
        if np.linalg.norm(axis)<1e-10:continue
        axis=axis/np.linalg.norm(axis);parallel=axis*float(delta@axis);remaining=delta-vertical-parallel
        for segments in [[parallel,remaining,vertical],[parallel,vertical,remaining],[vertical,parallel,remaining]]:
            ok,result=attempt_path(scene,label,ids,[q for q in segments if np.linalg.norm(q)>1e-10])
            if ok:return
        for distance in [.15,.3,.5,.8,1.2,2.,3.,-.15,-.3,-.5,-.8,-1.2,-2.]:
            shift=axis*distance
            for segments in [[shift,vertical,delta-shift-vertical],[shift,delta,-shift]]:
                ok,result=attempt_path(scene,label,ids,[q for q in segments if np.linalg.norm(q)>1e-10])
                if ok:return
    require(result)
def save(scene):
    if phase in phase_ranges:phase_ranges[phase][1]=len(scene.stages)
    CHECKPOINT.write_text(json.dumps({'sources':scene.sources,'phase':phase,'stages':scene.stages,
        'introductions':introductions,'phase_ranges':phase_ranges},separators=(',',':'))+'\n')
def face_basis(part):
    names=['N','NW','W','SW','S','SE','E','NE'];k=names.index(part['face']);a=-(k+.5)*np.pi/4
    normal=np.array([np.cos(a),0,np.sin(a)])
    return normal,np.array([-normal[2],0,normal[0]])

def finish(scene):
    ids=[pid for pid in scene.parts if pid.startswith(('SCHEM-FLOOR-SECTOR-','FLOOR-BAMBOO-CENTER-'))]
    checked(scene,ids,UP*.05,'Remove the last-installed bamboo finish',introduce=True)

def windows(scene):
    for k in range(8):
        ids=[pid for pid in scene.parts if pid.startswith(f'SCHEM-CUP-WINDOW-{k}-')]
        a=-(k+.5)*np.pi/4;n=np.array([np.cos(a),0,np.sin(a)])
        checked(scene,ids,n*.12,'Remove window assembly '+str(k+1),introduce=True)
        park(scene,ids,n*8+UP*5,'Park window assembly '+str(k+1),[n])

def infill(scene):
    # TIMESTAMP START 2026-11-04T20:06:20+00:00 | REVISION R000007
    ids=sorted([pid for pid,p in scene.parts.items() if p.get('schematicKind')=='wall'],
        key=lambda pid:(scene.parts[pid].get('erectionOrder',3),{'post-edge':0,'door-edge':1,'porch-band':2,'inner':1}.get(scene.parts[pid].get('erectionStripRole'),0),pid))
    # TIMESTAMP END 2026-11-04T20:06:20+00:00 | REVISION R000007
    for index,pid in enumerate(ids):
        p=scene.parts[pid];n,t=face_basis(p)
        if np.linalg.norm(scene.offsets[pid])>1e-8:continue
        original=len(scene.stages);result=None
        # Wall panels are separate from their structural rails and jambs.
        # TIMESTAMP START 2026-11-04T20:06:20+00:00 | REVISION R000007
        prescribed=p.get('erectionReleaseSteps')
        candidates=[[np.asarray(d) for d in prescribed]] if prescribed else [[n*.12],[-n*.12],[UP*.08,n*.12],[-UP*.08,n*.12]]
        # TIMESTAMP END 2026-11-04T20:06:20+00:00 | REVISION R000007
        toward=-np.sign(np.asarray(p['center'])@t)*t
        for distance in [.08,.15,.3,.6,1.]:
            candidates.extend([[toward*distance,n*.15],[toward*distance,-n*.15]])
        for segments in candidates:
            ok,result=attempt_path(scene,'Release main wall panel '+pid,[pid],segments)
            if ok:break
        require(True if ok else result)
        introductions.setdefault(pid,original)
        # Separate lanes outside each face prevent later panels sharing an end.
        target=n*(8+index*.035)+t*(np.asarray(p['center'])@t)*.25+UP*(p['center'][1]*.4+1)
        # TIMESTAMP START 2026-11-04T20:06:20+00:00 | REVISION R000007
        if p.get('erectionStripRole')=='door-edge':
            target=n*(8+index*.035)-t*(np.asarray(p['center'])@t)+UP*(p['center'][1]*.4+1)
        if p.get('erectionStripRole')=='inner':
            inner_ids=sorted(q for q,r in scene.parts.items() if r.get('erectionStripRole')=='inner')
            target=-n*(2+inner_ids.index(pid)*.3)-t*(np.asarray(p['center'])@t)
        # TIMESTAMP END 2026-11-04T20:06:20+00:00 | REVISION R000007
        park(scene,[pid],target,'Park main wall panel '+pid,[n,t])
        save(scene)
    # TIMESTAMP START 2026-11-04T20:45:07+00:00 | REVISION R000009
    for pid,p in sorted(scene.parts.items()):
        if p.get('schematicKind')=='shelf' and pid.endswith(('shelf2','shelf3')) and np.linalg.norm(scene.offsets[pid])<1e-8:
            checked(scene,[pid],-UP*(.3 if pid.endswith('shelf2') else .5),'Unseat shelf for late wall installation '+pid,introduce=True)
    # TIMESTAMP END 2026-11-04T20:45:07+00:00 | REVISION R000009

def porch(scene):
    porch_normal=radial((np.asarray(scene.parts['P2']['center'])+scene.parts['P3']['center'])/2)
    for index,pid in enumerate(sorted(q for q,p in scene.parts.items() if p.get('erectionStripRole') in ['post-edge','porch-band'])):
        tangent=np.array([-porch_normal[2],0,porch_normal[0]])
        park_at(scene,[pid],porch_normal*(20+index*.5)+UP*5,'Stage removed west infill clear of porch brace release '+pid,[porch_normal,tangent])
    cover=[pid for pid,p in scene.parts.items() if p.get('roofLayer')]
    n=radial((np.asarray(scene.parts['P2']['center'])+scene.parts['P3']['center'])/2)
    start=len(scene.stages)
    checked(scene,cover,n*.15,'Slide porch covering out from the main roof',introduce=True)
    checked(scene,cover,UP*.15,'Lift porch covering clear')
    park(scene,cover,n*10+UP*5,'Park porch roof covering',[n])
    result=apply_porch_phases(scene,skip_cover=True,parking_scale=.5,construction_order=True)
    require(True if result['status']=='PASS' else result)
    for i,stage in enumerate(scene.stages[start:],start):
        for pid in moving(stage):introductions.setdefault(pid,i)

def roof(scene):
    copper=[pid for pid in scene.parts if pid.startswith('ROOF-COPPER-')]
    if np.linalg.norm(scene.offsets[copper[0]])<1e-8:
        checked(scene,copper,UP*.15,'Lift cupola roof covering',introduce=True)
        park(scene,copper,UP*9,'Park cupola roof covering');save(scene)
    for k in range(8):
        ids=[pid for pid,p in scene.parts.items() if pid.startswith('ROOF-CEDAR-') and p['roof_face']==k]
        if np.linalg.norm(scene.offsets[ids[0]])>1e-8:continue
        a=-(k+.5)*np.pi/4;n=np.array([np.cos(a),0,np.sin(a)])
        checked(scene,ids,UP*.3,'Lift main roof covering '+str(k+1),introduce=True)
        park(scene,ids,n*9+UP*7,'Park main roof covering '+str(k+1),[n])
        save(scene)
    for k in range(8):
        for side in ['0','2']:
            pid=f'J{k}-{side}'
            if np.linalg.norm(scene.offsets[pid])>1e-8:continue
            checked(scene,[pid],UP*.3,'Release short rafter '+pid,introduce=True)
            park(scene,[pid],radial(scene.parts[pid]['center'])*10+UP*6,'Park short rafter '+pid)
            save(scene)
    for k in range(8):
        pid=f'CR{k}'
        if np.linalg.norm(scene.offsets[pid])>1e-8:continue
        checked(scene,[pid],UP*.15,'Release cupola rafter '+pid,introduce=True)
        park(scene,[pid],radial(scene.parts[pid]['center'])*8+UP*9,'Park cupola rafter '+pid)
        save(scene)
    if np.linalg.norm(scene.offsets['PLY'])<1e-8:
        checked(scene,['PLY'],UP*.1,'Lift cupola plywood',introduce=True)
        park(scene,['PLY'],UP*6.2,'Park cupola plywood');save(scene)
    for k in range(8):
        pid=f'CC{k}'
        if np.linalg.norm(scene.offsets[pid])>1e-8:continue
        r=radial(scene.parts[pid]['center']);t=np.array([-r[2],0,r[0]])
        checked(scene,[pid],-UP*.3,'Release cupola ceiling spoke '+pid,introduce=True)
        for delta in [t*.2,r*1.8,UP*5.3]:checked(scene,[pid],delta,'Clear cupola ceiling spoke '+pid)
        park(scene,[pid],r*11+UP*7,'Park cupola ceiling spoke '+pid)
        save(scene)

def trusses(scene):
    for k in [7,3,6,2,5,1,4,0]:
        pid=f'R{k}';r=radial(scene.parts[pid]['center'])
        if np.linalg.norm(scene.offsets[pid])>1e-8:continue
        checked(scene,[pid],UP*.0254,'Disengage hip '+pid+' one inch',introduce=True)
        checked(scene,[pid],r*.1016,'Slide hip '+pid+' four inches clear of cupola')
        introductions[pid]=len(scene.stages)-1
        park(scene,[pid],r*11+UP*6,'Park individual truss hip '+pid,[r])
        save(scene)

def cupola(scene):
    for k in range(8):
        pid=f'CP{k}'
        if np.linalg.norm(scene.offsets[pid])>1e-8:continue
        direction=np.asarray(scene.parts[pid].get('axis_direction',[0,0,1]))
        checked(scene,[pid],direction*.3,'Withdraw cupola foot peg '+pid,introduce=True)
        park(scene,[pid],radial(scene.parts[pid]['center'])*9+UP*4,'Park cupola foot peg '+pid)
        save(scene)
    ids=[f'{prefix}{k}{suffix}' for k in range(8) for prefix,suffix in [('C',''),('L','-S'),('L','-H')]]
    checked(scene,ids,UP*.3,'Lift central cupola frame off the ties',introduce=True)
    prototype=json.loads((ROOT/'docs/cupola-foot-prototype.json').read_text())['conditional_primary_test']['stages']
    step=next(s for s in prototype if s['label']=='Open cupola ring tenons simultaneously')
    proof=check_multi_stage(scene,step['motions'],stop_first=True);require(True if proof['status']=='PASS' else proof)
    apply_multi_stage(scene,step['motions'],proof,step['label'])
    ordered=[f'C{k}' for k in range(8)]+[f'L{k}-{suffix}' for k in range(8) for suffix in ['H','S']]
    for index,pid in enumerate(ordered):
        r=radial(scene.parts[pid]['center'])
        park(scene,[pid],scene.parts[pid]['exploded_offset'],'Clear cupola member above the original eight-L '+pid,[r])
        park(scene,[pid],r*(13+index*.1)+UP*(3+index*.01),'Park cupola member '+pid,[r])

def ties(scene):
    for pid,p in scene.parts.items():
        if not pid.startswith('MAIN-PEG-') or np.linalg.norm(scene.offsets[pid])>1e-8:continue
        direction=np.asarray(p['withdrawal_direction'])*(p['withdrawal_distance_m']+.01)
        # TIMESTAMP START 2026-11-04T20:45:07+00:00 | REVISION R000009
        for sign in [1,-1]:
            proof=check_stage(scene,[pid],direction*sign,stop_first=True)
            if proof['status']=='PASS':break
        require(True if proof['status']=='PASS' else proof)
        checked(scene,[pid],direction*sign,'Withdraw main-frame peg '+pid,introduce=True)
        park(scene,[pid],radial(p['center'])*15+UP*4,'Park main-frame peg '+pid,[direction*sign,radial(p['center'])]);save(scene)
        # TIMESTAMP END 2026-11-04T20:45:07+00:00 | REVISION R000009
    for k in [7,3,6,2,5,1,4,0]:
        pid=f'T{k}';brace=f'K{k}-C';r=radial(scene.parts[pid]['center']);t=np.array([-r[2],0,r[0]])
        if np.linalg.norm(scene.offsets[pid])>1e-8:continue
        checked(scene,[pid,brace],-r*.12,'Withdraw tie and inward brace '+str(k),introduce=True)
        checked(scene,[brace],-UP*.1,'Lower inward brace '+brace)
        # TIMESTAMP START 2026-11-04T20:45:07+00:00 | REVISION R000009
        if k in [5,1,4,0]:
            park(scene,[pid],r*12+UP*2,'Park opposite cross-beam '+pid,[r,t])
            ok=False
            for width in [.3,-.3,.5,-.5,.8,-.8]:
                inside=-r*3+t*width-UP*.1
                ok,result=attempt_path(scene,'Carry shelf brace inside and above post work '+brace,[brace],
                    [inside-scene.offsets[brace],UP*3])
                if ok:break
            require(True if ok else result)
            save(scene);continue
        target=compact_target(scene,brace);current=scene.offsets[brace]
        ok=False
        for inside_distance in [3.,3.5,2.5]:
            if ok:break
            for width in [.3,-.3,.5,-.5]:
                if ok:break
                inside=-r*inside_distance+t*width-UP*.1
                for height in [3.,4.,2.5]:
                    ok,result=attempt_path(scene,'Carry inward brace inside then over standing posts '+brace,[brace],
                        [inside-current,UP*height,target-inside-UP*height+UP*1.5,-UP*1.5])
                    if ok:break
        require(True if ok else result)
        park(scene,[pid],r*12+UP*2,'Park opposite cross-beam '+pid,[r,t])
        save(scene)
        # TIMESTAMP END 2026-11-04T20:45:07+00:00 | REVISION R000009
    checked(scene,['M-TMP'],-UP*.15,'Release original eight-L connector after every tie',introduce=True)
    park(scene,['M-TMP'],[0,6,0],'Park original eight-L connector')
    beams=[f'B{k}' for k in range(8)]
    checked(scene,beams,UP*.12,'Lift perimeter beams from open top post mortises',introduce=True)
    for k in range(8):
        pid=f'B{k}';r=radial(scene.parts[pid]['center']);park(scene,[pid],r*10+UP*3,'Park perimeter beam '+pid,[r])

# TIMESTAMP START 2026-11-04T20:45:07+00:00 | REVISION R000009
def secondary_walls(scene,force_ids=()):
    pending=[pid for pid,p in scene.parts.items() if p.get('schematicKind') in ['rail','shelf'] and np.linalg.norm(scene.offsets[pid]-compact_target(scene,pid))>1e-8 and (np.linalg.norm(scene.offsets[pid])<5 or pid in force_ids)]
    for turn in range(4):
        before=len(scene.stages)
        for pid in pending[:]:
            p=scene.parts[pid];target=compact_target(scene,pid);n,t=face_basis(p)
            candidates=[[-UP*.25],[-UP*.5],[-UP*.75],[-UP*1.],[n*.12],[-n*.12],[UP*.12]] if p.get('schematicKind')=='shelf' or pid in ['SCHEM-W-rail0-0','SCHEM-W-rail0-1'] else [[n*.12],[-UP*.25],[UP*.12]]
            result=None
            for segments in candidates:
                trial=clone_scene(scene)
                ok,result=attempt_path(trial,'Release secondary framing '+pid,[pid],segments)
                if not ok:continue
                result=route(trial,[pid],target,'Park secondary framing '+pid,[n,t])
                if result is not True:
                    result=route(trial,[pid],n*(20+sorted(q for q,r in scene.parts.items() if r.get('schematicKind') in ['rail','shelf']).index(pid)*.3)+UP*4,'Stage secondary framing clear of parked porch '+pid,[n,t])
                if result is True:
                    scene.offsets=trial.offsets;scene.stages=trial.stages;scene.version=trial.version
                    pending.remove(pid);print('Secondary framing clear',pid,flush=True);break
        if len(scene.stages)==before:break
    return pending

def posts(scene):
    def clear_parked(result):
        if not result.get('collisions'):require(result)
        hit=result['collisions'][0];other=hit['obstacle_id'];p=scene.parts[other]
        if not hit['obstacle_parked']:require(result)
        if p.get('schematicKind') in ['rail','shelf']:
            n,t=face_basis(p)
            peers=sorted(q for q,r in scene.parts.items() if r.get('schematicKind') in ['rail','shelf'])
            target=n*(24+peers.index(other)*.3)+UP*4
            if np.linalg.norm(scene.offsets[other]-target)<1e-8:require(result)
            park_at(scene,[other],target,'Clear released framing from bare post carry '+other,[n,t])
        elif other.startswith('MAIN-PEG-'):
            r=radial(p['center']);target=r*20+UP*6
            if np.linalg.norm(scene.offsets[other]-target)<1e-8:require(result)
            park_at(scene,[other],target,'Clear released peg from bare post carry '+other,[r])
        else:require(result)
    def carry(ids,delta,label):
        for attempt in range(24):
            result=move(scene,ids,delta,label)
            if result is True:return
            clear_parked(result)
        raise RuntimeError('Bare post carry exhausted checked obstacle clearances')
    def park_post(pid,r,t):
        for attempt in range(24):
            goal=compact_target(scene,pid);delta=goal-scene.offsets[pid]
            if np.linalg.norm(delta)<1e-8:return
            direct=move(scene,[pid],delta,'Park vertical post after clearing released framing '+pid)
            if direct is True:return
            hit=direct['collisions'][0];obstacle=scene.parts[hit['obstacle_id']]
            if hit['obstacle_parked'] and (obstacle.get('schematicKind') in ['rail','shelf'] or hit['obstacle_id'].startswith('MAIN-PEG-')):
                clear_parked(direct);continue
            try:park(scene,[pid],r*14+UP,'Park vertical post '+pid,[r,t]);return
            except RuntimeError as error:clear_parked(json.loads(str(error)))
        raise RuntimeError('Post parking exhausted checked obstacle clearances')
    ids=[pid for pid,p in scene.parts.items() if pid.startswith('P') and len(pid)==2 or p.get('schematicKind') in ['rail','shelf'] or pid.startswith('K') and not pid.endswith('-C')]
    if not any(stage.get('label')=='Lift bare post framing above the structural floor' for stage in scene.stages):
        checked(scene,ids,UP*.6,'Lift bare post framing above the structural floor',introduce=True)
        secondary_walls(scene)
        held=[];perimeter=[q for q in ids if q.startswith('K')]
        for pid in perimeter:
            p=scene.parts[pid];direction=np.asarray(p['axis_end'])-p['axis_start'];direction[1]=0;direction/=np.linalg.norm(direction)
            result=move(scene,[pid],direction*.12,'Withdraw perimeter brace '+pid)
            if result is not True:held.append(pid)
        for pid in held:
            k=int(pid[1]);post=f'P{k}';other=f"K{k}-{'A' if pid.endswith('B') else 'B'}"
            p=scene.parts[pid];axis=np.asarray(p['axis_end'])-p['axis_start'];axis/=np.linalg.norm(axis)
            horizontal=axis.copy();horizontal[1]=0;horizontal/=np.linalg.norm(horizontal)
            carry([post,other],-horizontal*1.2,'Carry post clear of retained shelf brace '+pid)
            carry([pid],-axis*1.2,'Slide brace axially below the retained shelf '+pid)
        for pid in perimeter:
            r=radial(scene.parts[pid]['center']);t=np.array([-r[2],0,r[0]])
            try:park(scene,[pid],r*12+UP*2,'Park perimeter brace '+pid,[r,t])
            except RuntimeError:
                target=compact_target(scene,pid);delta=target-scene.offsets[pid]
                for height in [1.2,1.8,2.4,3.]:
                    ok,result=attempt_path(scene,'Carry brace above released walls '+pid,[pid],[UP*height,delta,-UP*height])
                    if ok:break
                require(True if ok else result)
    forced=[rail for post,rail in [('P2','SCHEM-W-rail0-0'),('P3','SCHEM-W-rail0-1')]
        if np.linalg.norm(scene.offsets[post])>10 and np.linalg.norm(scene.offsets[rail]-scene.offsets[post])<1e-8]
    if forced:
        pending=secondary_walls(scene,forced)
        require(True if not set(pending)&set(forced) else {'status':'BLOCKED','carried_west_members':pending})
    for k in range(8):
        pid=f'P{k}';r=radial(scene.parts[pid]['center']);t=np.array([-r[2],0,r[0]])
        if np.linalg.norm(scene.offsets[pid]-compact_target(scene,pid))<1e-8 or np.linalg.norm(scene.offsets[pid])>10:continue
        if pid=='P2' and np.linalg.norm(scene.offsets['P2']-scene.offsets['P3'])<1e-8:
            west=[q for q,p in scene.parts.items() if p.get('face')=='W' and p.get('schematicKind')=='rail' and np.linalg.norm(scene.offsets[q]-scene.offsets[pid])<1e-8]
            carried=['P2','P3',*west];n=radial((np.asarray(scene.parts['P2']['center'])+scene.parts['P3']['center'])/2)
            target=n*14+UP;delta=target-scene.offsets[pid];horizontal=delta-UP*delta[1]
            ok=False
            for height in [4.,6.,8.,10.,12.,3.,2.5]:
                ok,result=attempt_path(scene,'Carry west frame above the parked walls',carried,
                    [n*.8,UP*height,horizontal-n*.8,UP*(delta[1]-height)])
                if ok:break
            if not ok:park_at(scene,carried,target,'Carry west posts with still-housed doorway framing',[n,t])
            pending=secondary_walls(scene,west);require(True if not set(pending)&set(west) else {'status':'BLOCKED','carried_west_members':pending})
            save(scene);continue
        carried=[pid]
        rail={'P2':'SCHEM-W-rail0-0','P3':'SCHEM-W-rail0-1'}.get(pid)
        if rail and np.linalg.norm(scene.offsets[rail]-scene.offsets[pid])<1e-8:carried.append(rail)
        if len(carried)>1:
            park_at(scene,carried,r*14+UP,'Carry vertical post with downward-entry sill '+pid,[r,t])
            checked(scene,[rail],-UP*.25,'Separate downward-entry sill from cleared post '+rail)
            n,along=face_basis(scene.parts[rail]);park_at(scene,[rail],n*18+UP*4,'Stage released west sill '+rail,[n,along])
        park_post(pid,r,t)
        save(scene)
    pending=secondary_walls(scene)
    require(True if not pending else {'status':'BLOCKED','remaining_structural_wall_members':pending})
# TIMESTAMP END 2026-11-04T20:45:07+00:00 | REVISION R000009

def post_caps(scene):
    # These caps seat over the plywood and carry the unchanged post feet.
    # They install with post hardware, after the deck and before the posts.
    for pid in [q for q in scene.parts if q.startswith('POST-BEARING-STAND-') and q.endswith('-HEAD')]:
        if np.linalg.norm(scene.offsets[pid])>1e-8:continue
        checked(scene,[pid],UP*.3,'Remove post-bearing cap after lifting posts '+pid,introduce=True)
        r=radial(scene.parts[pid]['center']);park(scene,[pid],r*20+UP,'Park post-bearing cap '+pid,[r]);save(scene)

def underlayment(scene):
    # The original steel fixture stays above the work while floor layers clear.
    # Its accepted compact destination is restored after support removal.
    n=np.array([np.cos(np.pi/8),0,-np.sin(np.pi/8)])
    park_at(scene,['M-TMP'],n*3.5+UP*3,'Stage released eight-L clear of floor lifting',[n])
    for k in [0,1,4,5]:
        pid=f'K{k}-C';r=radial(scene.parts[pid]['center']);t=np.array([-r[2],0,r[0]])
        park_at(scene,[pid],compact_target(scene,pid),'Clear the upper room of staged brace '+pid,[r,t]);save(scene)
    for k in range(8):
        pid=f'T{k}';r=radial(scene.parts[pid]['center']);t=np.array([-r[2],0,r[0]])
        park_at(scene,[pid],r*12+UP*4,'Stage released cross-beam clear of floor lifting '+pid,[r,t]);save(scene)
    porch_normal=radial((np.asarray(scene.parts['P2']['center'])+scene.parts['P3']['center'])/2)
    wall_lift=sum((np.asarray(stage['delta_m']) for stage in scene.stages if stage.get('label')=='Raise released wall members above floor delivery W'),np.zeros(3))
    for index,pid in enumerate(q for q,p in scene.parts.items() if p.get('erectionStripRole')=='inner'):
        park_at(scene,[pid],porch_normal*(20+index*.5)+UP*5+wall_lift,'Clear the floor lane of staged wall strip '+pid,[porch_normal,np.array([-porch_normal[2],0,porch_normal[0]])]);save(scene)
    for pid in [q for q in scene.parts if q.startswith('MUD-POST-')]:
        label='Raise released porch post above bamboo delivery '+pid
        if any(stage.get('label')==label for stage in scene.stages):continue
        checked(scene,[pid],UP*.2,label)
        save(scene)
    for pid in [f'P{k}' for k in range(8)]:
        bottom=scene.current(pid).bounding_box()[1]
        if bottom>=.3-1e-9:continue
        checked(scene,[pid],UP*(.3-bottom),'Raise removed main post above floor delivery '+pid)
        save(scene)
    for face in ['N','NW','W','SW','S','SE','E','NE']:
        ids=[pid for pid,p in scene.parts.items() if p.get('face')==face and p.get('schematicKind') in ['wall','rail']]
        bottom=min(scene.current(pid).bounding_box()[1] for pid in ids)
        if bottom>=.3-1e-9:continue
        checked(scene,ids,UP*(.3-bottom),'Raise released wall members above floor delivery '+face)
        save(scene)
    guard_groups=[('porch-side-guards',('MUD-GUARD-',)),
        ('porch-front-guards',('MUD-FRONT-','MUD-ENTRY-GUARD-')),
        ('stair-guards',('MUD-LANDING-RAIL-','MUD-LANDING-PICKET-','MUD-STAIR-RAIL-','MUD-STAIR-PICKET-'))]
    for name,prefixes in guard_groups:
        ids=[pid for pid in scene.parts if pid.startswith(prefixes)]
        bottom=min(scene.current(pid).bounding_box()[1] for pid in ids)
        if bottom>=.3-1e-9:continue
        checked(scene,ids,UP*(.3-bottom),'Raise released porch assemblies above floor delivery '+name)
        save(scene)
    finish_ids=[pid for pid in scene.parts if pid.startswith(('SCHEM-FLOOR-SECTOR-','FLOOR-BAMBOO-CENTER-'))]
    for index,pid in enumerate(finish_ids):
        c=np.asarray(scene.parts[pid]['center'])
        target=np.array([20+(index%4)*5-c[0],.2,12+(index//4)*5-c[2]])
        if np.linalg.norm(scene.offsets[pid]-target)<1e-8:continue
        if np.allclose(scene.offsets[pid],UP*.05,atol=1e-8):checked(scene,[pid],UP*.05,'Lift bamboo clear of adjacent finish panels '+pid)
        current=scene.offsets[pid]
        ok=False
        for height in [.22,.25,.275,.28]:
            high=current+UP*(height-current[1]);above=target+UP*(height-target[1])
            points=[current,high,above,target]
            ok,result=attempt_path(scene,'Deliver released bamboo through the low clear corridor '+pid,[pid],
                [b-a for a,b in zip(points,points[1:]) if np.linalg.norm(b-a)>1e-10])
            if ok:break
        require(True if ok else result);save(scene)
    for index,pid in enumerate(pid for pid,p in scene.parts.items() if p.get('floorRole')=='underlayment_sheet'):
        if np.linalg.norm(scene.offsets[pid])>3:continue
        if np.linalg.norm(scene.offsets[pid])<1e-8:checked(scene,[pid],UP*.15,'Lift individual 4 by 8 underlayment sheet '+pid,introduce=True)
        c=np.asarray(scene.parts[pid]['center']);r=radial(c)
        target=np.array([40+(index%6)*3.2-c[0],.5,-15+(index//6)*3.2-c[2]])
        park_at(scene,[pid],target,'Park separate 4 by 8 sheet '+pid,[r,np.array([-r[2],0,r[0]])]);save(scene)

def floor_supports(scene):
    ids=[pid for pid,p in scene.parts.items() if p.get('schematicKind')=='floorAssembly']
    east=np.array([np.sin(np.pi/8),0,np.cos(np.pi/8)])
    joists=sorted([pid for pid in ids if pid.startswith('FLOOR-JOIST-')],key=lambda pid:-abs(np.asarray(scene.parts[pid]['center'])@east))
    north=np.array([east[2],0,-east[0]])
    for index,pid in enumerate(joists):
        if np.linalg.norm(scene.offsets[pid])>1:continue
        if np.linalg.norm(scene.offsets[pid])<1e-8:checked(scene,[pid],UP*.21,'Lift north-south floor joist '+pid,introduce=True)
        c=np.asarray(scene.parts[pid]['center']);sign=1 if c@east>=0 else -1
        current=scene.offsets[pid];target=compact_target(scene,pid);ok=False
        for lane in [10.,-10.]:
            high=current+UP*4.5;outside=high+east*(sign*14-(c+high)@east)
            aside=outside+north*lane;low=aside+UP*(target[1]-aside[1]);near=target+north*lane
            points=[current,high,outside,aside,low,near,target]
            segments=[b-a for a,b in zip(points,points[1:]) if np.linalg.norm(b-a)>1e-10]
            ok,result=attempt_path(scene,'Carry joist around the parked porch '+pid,[pid],segments)
            if ok:break
        if not ok:park(scene,[pid],sign*east*(22+index*.1)+UP*.3,'Park floor joist '+pid,[east,north])
        save(scene)
    for k in range(8):
        a=-(k+.5)*np.pi/4;n=np.array([np.cos(a),0,np.sin(a)]);t=np.array([-n[2],0,n[0]])
        rim=f'FLOOR-RIM-{k}';left=f'POST-BEARING-STAND-{k}-SIDE-1';right=f'POST-BEARING-STAND-{(k+1)%8}-SIDE1'
        if np.linalg.norm(scene.offsets[rim])>1e-8:continue
        checked(scene,[rim,left,right],UP*.15,'Lift floor rim and side plates from their bearings '+str(k),introduce=True)
        checked(scene,[rim,left,right],UP*4.35,'Clear floor rim above parked wall framing '+str(k))
        checked(scene,[rim,left,right],n*3,'Release floor rim and side plates '+str(k))
        checked(scene,[left],t*.3,'Separate floor side plate '+left)
        checked(scene,[right],-t*.3,'Separate floor side plate '+right);save(scene)
    for k in range(8):
        pid=f'FLOOR-BEAM-{k}';r=radial(scene.parts[pid]['center'])
        if np.linalg.norm(scene.offsets[pid]-compact_target(scene,pid))<1e-8 or np.linalg.norm(scene.offsets[pid])>10:continue
        if np.linalg.norm(scene.offsets[pid])<1e-8:checked(scene,[pid],r*3,'Withdraw floor support beam '+pid,introduce=True)
        park(scene,[pid],r*25,'Park floor support beam '+pid,[r]);save(scene)

def foundations(scene):
    fixed={'PIER-C','PIER-C-BELOW','FLOOR-CENTRAL-HUB'}
    for index,pid in enumerate(p for p in scene.parts if p.startswith('PIER-') and not p.endswith('-BELOW') and p not in fixed):
        pair=[pid,pid+'-BELOW'];r=radial(scene.parts[pid]['center'])
        if np.linalg.norm(scene.offsets[pid])>.5:continue
        if np.linalg.norm(scene.offsets[pid])<1e-8:checked(scene,pair,-UP*.3,'Release continuous concrete column '+pid,introduce=True)
        park(scene,pair,r*(28+index*.15)-UP*.3,'Park continuous concrete column '+pid,[r]);save(scene)

# TIMESTAMP START 2026-11-04T20:45:07+00:00 | REVISION R000009
def compact_precise(scene,ids,target):
    if len(ids)!=1:return None
    pid=ids[0];p=scene.parts[pid];current=scene.offsets[pid];c=np.asarray(p['center']);last=None
    if pid in [f'P{k}' for k in range(8)] and np.linalg.norm((target-current)[[0,2]])<1e-8:
        ok,last=attempt_path(scene,'Lower main post after floor delivery '+pid,ids,[target-current])
        if ok:return True,None
    if pid in ['P2','P3']:
        n=radial((np.asarray(scene.parts['P2']['center'])+scene.parts['P3']['center'])/2)
        t=np.array([-n[2],0,n[0]]);sign=1 if (c+target)@t>=0 else -1
        for aisle in [2.5,3.,3.5,4.]:
            outside=current+t*(sign*aisle-(c+current)@t)
            low=outside+UP*(target[1]-outside[1])
            near=target+t*(sign*aisle-(c+target)@t)
            points=[current,outside,low,near,target]
            segments=[v-u for u,v in zip(points,points[1:]) if np.linalg.norm(v-u)>1e-10]
            trial=clone_scene(scene);cleared=[];accepted=False
            for attempt in range(16):
                accepted,last=attempt_path(trial,'Return main west post outside the parked porch '+pid,ids,segments)
                if accepted:break
                hits=last.get('collisions',[]);peg=hits[0]['obstacle_id'] if hits else ''
                if not peg.startswith('MAIN-PEG-') or any(item[0]==peg for item in cleared):break
                record=trial.parts[peg];axis=np.asarray(record.get('withdrawal_direction',record.get('axis_direction')))
                axis=axis/np.linalg.norm(axis)
                away=np.asarray(record['center'])+trial.offsets[peg]-c-target;away[1]=0
                if np.linalg.norm(away)>1e-9:away/=np.linalg.norm(away)
                sign_axis=1 if axis@away>=0 else -1
                staged=False
                for shift in [axis*sign_axis*.4,away*.5,UP*.3,-UP*.3,t*.5,-t*.5]:
                    if np.linalg.norm(shift)<1e-9:continue
                    future=clone_scene(trial);future.offsets[pid]=target.copy()
                    proof=check_stage(future,[peg],shift,stop_first=True)
                    if proof['status']!='PASS':continue
                    staged,last=attempt_path(trial,'Temporarily clear withdrawn main peg '+peg,[peg],[shift])
                    if staged:cleared.append((peg,shift));break
                if not staged:break
            if not accepted:continue
            for peg,shift in reversed(cleared):
                restored,last=attempt_path(trial,'Return withdrawn main peg after main post parking '+peg,[peg],[-shift])
                if not restored:accepted=False;break
            if accepted:
                scene.offsets=trial.offsets;scene.stages=trial.stages;scene.version=trial.version
                return True,None
        return False,last
    if pid.startswith(('SCHEM-FLOOR-SECTOR-','FLOOR-BAMBOO-CENTER-')):
        n=radial((np.asarray(scene.parts['P2']['center'])+scene.parts['P3']['center'])/2)
        t=np.array([-n[2],0,n[0]])
        for height in [.05,.1,.15,.25,.4,.6]:
            for lane in [-10.,10.,-15.,15.]:
                above=target+UP*height;low=current+UP*(above[1]-current[1])
                points=[current,low,low+t*lane,above+t*lane,above,target]
                segments=[b-a for a,b in zip(points,points[1:]) if np.linalg.norm(b-a)>1e-10]
                ok,last=attempt_path(scene,'Route finish floor around parked foundations '+pid,ids,segments)
                if ok:return True,None
        return False,last
    if pid.startswith('FLOOR-RIM-') or (pid.startswith('POST-BEARING-STAND-') and '-SIDE' in pid):
        r=radial(c+target);t=np.array([-r[2],0,r[0]])
        aligned=current.copy();aligned[0]=target[0];aligned[2]=target[2]
        for lane in [10.,-10.]:
            outside=aligned+r*(14-(c+aligned)@r);aside=outside+t*lane
            low=aside+UP*(target[1]-aside[1]);near=target+t*lane+r*.4;ready=target+r*.4
            points=[current,aligned,outside,aside,low,near,ready,target]
            segments=[b-a for a,b in zip(points,points[1:]) if np.linalg.norm(b-a)>1e-10]
            ok,last=attempt_path(scene,'Return floor perimeter below the parked joists '+pid,ids,segments)
            if ok:return True,None
        return False,last
    if p.get('floorRole')=='underlayment_sheet':
        north=np.array([np.cos(np.pi/8),0,-np.sin(np.pi/8)])
        for sign in [1,-1]:
            high=current+UP*(2.8-current[1]);a=north*10*sign-c;b=north*3*sign-c
            a[1]=b[1]=2.8;above=target+UP*.3;inside=b.copy();inside[1]=above[1]
            points=[current,high,a,b,inside,above,target]
            segments=[v-u for u,v in zip(points,points[1:]) if np.linalg.norm(v-u)>1e-10]
            ok,last=attempt_path(scene,'Place compact sheet through the clear bay '+pid,ids,segments)
            if ok:return True,None
        return False,last
    if pid.startswith('MUD-POST-'):
        delta=target-current
        if np.linalg.norm(delta[[0,2]])<1e-8:
            ok,last=attempt_path(scene,'Lower porch post after bamboo delivery '+pid,ids,[delta])
            if ok:return True,None
        n=radial((np.asarray(scene.parts['P2']['center'])+scene.parts['P3']['center'])/2)
        t=np.array([-n[2],0,n[0]]);sign=1 if (c+target)@t>=0 else -1
        for aisle in [None,1.3,1.4,1.2,1.1,1.65,1.6,1.7,1.75]:
            trial=clone_scene(scene);cleared=[];accepted=False
            if aisle is None:
                delta=target-current;horizontal=delta-UP*delta[1]
                segments=[UP*3,horizontal,UP*(delta[1]-3)]
            else:
                outward=current+n*.3;side=outward+t*(sign*aisle-(c+outward)@t)
                near=target+t*(sign*aisle-(c+target)@t);points=[current,outward,side,near,target]
                segments=[v-u for u,v in zip(points,points[1:]) if np.linalg.norm(v-u)>1e-10]
            for attempt in range(16):
                accepted,last=attempt_path(trial,'Route released porch post to compact destination '+pid,ids,segments)
                if accepted:break
                hits=last.get('collisions',[]);peg=hits[0]['obstacle_id'] if hits else ''
                if not peg.startswith('MUD-PEG-') or any(item[0]==peg for item in cleared):break
                peg_sign=1 if (np.asarray(trial.parts[peg]['center'])+trial.offsets[peg])@t>=0 else -1
                shift=t*peg_sign*.5
                ok,last=attempt_path(trial,'Clear withdrawn peg above its parked rail '+peg,[peg],[UP*.15,shift])
                if not ok:break
                cleared.append((peg,shift))
            if not accepted:continue
            for peg,shift in reversed(cleared):
                ok,last=attempt_path(trial,'Return withdrawn peg beside the compact post '+peg,[peg],[-shift,-UP*.15])
                if not ok:accepted=False;break
            if accepted:
                scene.offsets=trial.offsets;scene.stages=trial.stages;scene.version=trial.version
                return True,None
        return False,last
    if p.get('face')=='W' and p.get('schematicKind') in ['rail','wall']:
        n=radial((np.asarray(scene.parts['P2']['center'])+scene.parts['P3']['center'])/2)
        t=np.array([-n[2],0,n[0]])
        wall=p.get('schematicKind')=='wall';post=pid.startswith('MUD-POST-')
        clearances=[.3,-.3,.5,-.5,1.,-1.,1.5,-1.5,2.,-2.] if wall else [-.25,-.3,-.2,.25,.3,.5,-.5,.8,-.8,1.2,-1.2,2.,-2.]
        heights=[0.,.15,.3,.5,-.15,-.3] if wall else [0.]
        start=n*.3 if post else np.zeros(3)
        for clearance in clearances:
            for height in heights:
                for lane in [4.,-4.,6.,-6.,10.,-10.]:
                    segments=[start,t*lane,target-current+n*clearance+UP*height-start,
                        -t*lane,-n*clearance,-UP*height]
                    segments=[d for d in segments if np.linalg.norm(d)>1e-10]
                    ok,last=attempt_path(scene,'Route west component around the porch '+pid,ids,segments)
                    if ok:return True,None
        return False,last
    return None

def compact(scene):
    wall_lift=sum((np.asarray(stage['delta_m']) for stage in scene.stages if stage.get('label')=='Raise released wall members above floor delivery W'),np.zeros(3))
    if np.linalg.norm(wall_lift)>1e-9 and not any(stage.get('label')=='Return released enclosure members after floor delivery W' for stage in scene.stages):
        n=radial((np.asarray(scene.parts['P2']['center'])+scene.parts['P3']['center'])/2);t=np.array([-n[2],0,n[0]])
        for index,pid in enumerate(q for q,p in scene.parts.items() if p.get('erectionStripRole')=='inner'):
            park_at(scene,[pid],n*(20+index*.5)+UP*5+wall_lift,'Preserve raised wall-strip delivery pose '+pid,[n,t])
            save(scene)
    for stage in reversed(list(scene.stages)):
        if not stage.get('label','').startswith(('Raise released wall members above floor delivery ','Raise released porch guards above floor delivery ','Raise released porch assemblies above floor delivery ')):continue
        label='Return released enclosure members after floor delivery '+stage['label'].rsplit(' ',1)[-1]
        if any(s.get('label')==label for s in scene.stages):continue
        checked(scene,stage['member_ids'],-np.asarray(stage['delta_m']),label)
        save(scene)
    pending=[];groups={}
    for pid in scene.parts:
        target=compact_target(scene,pid)
        if target is None or np.linalg.norm(target-scene.offsets[pid])<1e-8:continue
        key=tuple(np.round(np.concatenate([scene.offsets[pid],target]),8))
        groups.setdefault(key,[]).append(pid)
    pending=list(groups.values());pending.sort(key=lambda ids:0 if ids[0].startswith('MUD-POST-') else 1)
    for turn in range(len(pending)+1):
        next_pending=[];before=len(scene.stages)
        for ids in pending:
            target=compact_target(scene,ids[0]);r=radial(scene.parts[ids[0]]['center']);t=np.array([-r[2],0,r[0]])
            precise=compact_precise(scene,ids,target)
            if precise is not None:
                if precise[0]:print('Compact clearance path',ids[0],len(scene.stages),flush=True)
                else:
                    next_pending.append(ids)
                    print('Compact path held',ids[0],precise[1],flush=True)
                continue
            try:park_at(scene,ids,target,'Arrange compact exploded parts '+ids[0],[r,t])
            except RuntimeError:next_pending.append(ids)
        pending=next_pending
        print('Compact pass',turn+1,'remaining',len(pending),flush=True)
        save(scene)
        if not pending:return
        if len(scene.stages)==before:break
    raise RuntimeError(json.dumps({'status':'BLOCKED','compact_pending':pending}))
# TIMESTAMP END 2026-11-04T20:45:07+00:00 | REVISION R000009

PHASES=[('finish',finish),('windows',windows),('walls',infill),('porch',porch),('roof',roof),('trusses',trusses),
        ('cupola',cupola),('ties',ties),('posts',posts),('post-caps',post_caps),('underlayment',underlayment),('floor-supports',floor_supports),('foundations',foundations),('compact',compact)]

def main():
    global phase,introductions,phase_ranges
    parser=argparse.ArgumentParser();parser.add_argument('--resume',action='store_true');parser.add_argument('--stop-after');args=parser.parse_args()
    scene=load_scene('top-entry')
    if args.resume and CHECKPOINT.exists():
        previous=json.loads(CHECKPOINT.read_text());assert previous['sources']==scene.sources,'Physical source changed since checkpoint'
        scene.stages=previous['stages'];scene.version=len(scene.stages);introductions=previous['introductions'];phase_ranges=previous['phase_ranges'];phase=previous['phase']
        for stage in scene.stages:
            for motion in stage.get('motions',[stage]):
                for pid in motion['member_ids']:scene.offsets[pid]+=motion['delta_m']
    else:
        initial=audit_initial_scene(scene);assert initial['status']=='PASS',initial
    try:
        start=len(PHASES) if phase=='complete' else next(i for i,p in enumerate(PHASES) if p[0]==phase)
        for index in range(start,len(PHASES)):
            name,action=PHASES[index];phase=name
            first=phase_ranges.get(name,[phase_ranges.get(PHASES[index-1][0],[0,len(scene.stages)])[1] if index else 0])[0]
            phase_ranges[name]=[first,len(scene.stages)]
            action(scene);phase_ranges[name]=[first,len(scene.stages)]
            phase=PHASES[index+1][0] if index+1<len(PHASES) else 'complete';save(scene)
            if args.stop_after==name:return
        separation=audit_final_joinery(scene);assert separation['status']=='PASS',separation
        moved={pid for stage in scene.stages for pid in moving(stage)}
        assert set(scene.parts)-moved=={'FLOOR-CENTRAL-HUB','PIER-C','PIER-C-BELOW'}
        for i,stage in enumerate(scene.stages):stage['id']=f'construction-{i+1:04d}'
        candidate={'stages':scene.stages,'sources':scene.sources,'blocked':[],'prefix_stage_count':0,
            'construction':{'reverse_phases':phase_ranges,'release_stage_by_piece':introductions,
                'anchor_appearance_release_stage':{'FLOOR-CENTRAL-HUB':phase_ranges['floor-supports'][1]-1},
                'sequence':'Main concrete; floor supports; 4x8 underlayment; posts and bare framing; ties/eight-L; cupola; individual hips; roof; complete porch; infill; windows; bamboo finish.'}}
        (ROOT/'scripts/construction-disassembly-route.json').write_text(json.dumps(candidate,separators=(',',':'))+'\n')
        print('PASS:',len(scene.stages),'stages; ordered construction and reversed disassembly')
    except BaseException:
        FAILURE.write_text(json.dumps({'sources':scene.sources,'phase':phase,'stages':scene.stages,'introductions':introductions,'phase_ranges':phase_ranges},separators=(',',':'))+'\n')
        raise

if __name__=='__main__':main()
# TIMESTAMP END 2026-11-04T20:00:49+00:00 | REVISION R000006

# TIMESTAMP END 2026-11-04T20:45:07+00:00 | REVISION R000009

# TIMESTAMP END 2026-11-04T23:23:25+00:00 | REVISION R000011

# TIMESTAMP END 2026-11-04T23:48:03+00:00 | REVISION R000012
