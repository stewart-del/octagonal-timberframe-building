# TIMESTAMP START 2026-11-02T15:56:09-05:00 | REVISION R004810
"""Guard contact-cone claims and replay actual primary withdrawal paths."""
from pathlib import Path
import copy,hashlib,json,sys
import numpy as np
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from plan_main_disassembly import coupled_cone,local_directions,restore_verified_prefix
from plan_architectural_disassembly import check_stage,apply_stage,check_multi_stage,apply_multi_stage

# A two-ended bar cannot move while both receivers stay fixed, but a receiver
# can first withdraw. The coupled solver must not call the whole system locked.
# TIMESTAMP START 2026-11-02T19:53:45-05:00 | REVISION R004859
parts={'A':{'center':[-2.,0.,0.]},'B':{'center':[0.,0.,0.]},'C':{'center':[2.,0.,0.]}}
# TIMESTAMP END 2026-11-02T19:53:45-05:00 | REVISION R004859
graph=[]
for a,b in [('A','B'),('B','C')]:
    graph.append({'a':a,'b':b,'planes':[{'normal_on_a':n,'area_in2':1} for n in [[1,0,0],[0,1,0],[0,-1,0],[0,0,1],[0,0,-1]]]})
assert not local_directions('B',set(parts),graph)
assert coupled_cone(parts,graph,list(parts),anchor='A')['status']=='CANDIDATE'
# A solid captive on all six faces has no relative translation; every signed
# coordinate is bounded independently instead of relying on one objective.
closed=[{'a':'A','b':'B','planes':[{'normal_on_a':n.tolist(),'area_in2':1} for n in np.vstack([np.eye(3),-np.eye(3)])]}]
locked=coupled_cone({k:parts[k] for k in ['A','B']},closed,['A','B'],anchor='A')
assert locked['status']=='TRANSLATION_LOCKED' and locked['coordinate_optimizations']==6
assert locked['maximum_relative_coordinate']==0

plans=json.loads((R/'src/main-disassembly-plan.json').read_text())
global_manifest=json.loads((R/'src/disassembly-plan.json').read_text())
for variant,plan in plans['variants'].items():
    prefix=copy.deepcopy(global_manifest['variants'][variant]);prefix['stages']=prefix['stages'][:plan['prefix_stage_count']]
    scene=restore_verified_prefix(variant,prefix)
    assert plan['status']==('PASS' if variant=='top-entry' else 'PARTIAL')
    assert all(plan['sources'].get(name)==digest for name,digest in scene.sources.items())
    moved=set();checks=0
    for stage in plan['stages']:
        if 'motions' in stage:
            proof=check_multi_stage(scene,stage['motions'])
            assert proof['status']=='PASS',(variant,stage['id'],proof['collisions'])
            apply_multi_stage(scene,stage['motions'],proof,stage['label'],stage['id'])
        else:
            proof=check_stage(scene,stage['member_ids'],stage['delta_m'])
            assert proof['status']=='PASS',(variant,stage['id'],proof['collisions'])
            apply_stage(scene,stage['member_ids'],stage['delta_m'],proof,stage['label'],stage['id'])
        assert proof['parked_pieces_checked']
        moved.update(pid for q in stage.get('motions',[stage]) for pid in q['member_ids']);checks+=proof['continuous_pair_checks']
    assert moved==set(plan['moved_ids'])
    # TIMESTAMP START 2026-11-03T06:36:08-05:00 | REVISION R004891
    assert {f'CR{k}' for k in range(8)}|{'PLY'}<=moved
    # A partially withdrawn member can have moved and still be held at a later
    # stage; its blocked status must remain explicit instead of claiming release.
    assert all(set(row['member_ids'])<=set(scene.parts) for row in plan['blocked'])
    # TIMESTAMP END 2026-11-03T06:36:08-05:00 | REVISION R004891
    canonical={pid for pid,p in scene.parts.items() if p.get('is_timber') or p.get('group')=='joinery_pegs' or pid=='PLY'}
    if variant=='top-entry':
        # TIMESTAMP START 2026-11-03T06:54:15-05:00 | REVISION R004896
        fixed=set(plan['anchored_ids'])
        assert fixed=={'FLOOR-CENTRAL-HUB','PIER-C','PIER-C-BELOW'}
        assert not fixed & moved and all(np.array_equal(scene.offsets[pid],np.zeros(3)) for pid in fixed)
        assert canonical<=moved|fixed and not plan['blocked'] and not plan['unmoved_ids']
        # TIMESTAMP END 2026-11-03T06:54:15-05:00 | REVISION R004896
    else:
        assert {f'J{k}-{side}' for k in range(8) for side in ['0','2']}<=set(plan['unmoved_ids'])
        assert plan['blocked']
    print('PASS',variant,len(moved),'primary members',len(plan['stages']),'continuous stages',checks,'full-scene pair checks; parked obstacles retained')
print('PASS: independent fixed-neighbor/coupled-motion distinction and signed-coordinate lock bounds; no rotational, structural or demolition approval claimed')
# TIMESTAMP END 2026-11-02T15:56:09-05:00 | REVISION R004810
