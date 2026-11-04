# TIMESTAMP START 2026-11-02T17:13:08-05:00 | REVISION R004818
"""Verify the selected flared feet, exact stock transfers and physical pegs."""
from pathlib import Path
import itertools,json,sys
import numpy as np
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from step_lap import solid,close_bounds
from cupola_foot import seed,I
from audit_cavity_fit import inspect_mesh
from plan_architectural_disassembly import Scene,check_stage,apply_stage

source=json.loads((R/'src/step-lap-proposed-model.json').read_text())
model=json.loads((R/'src/top-entry-proposed-model.json').read_text())
before={p['id']:p for p in source['parts']};parts={p['id']:p for p in model['parts']}

assert model['cupola_foot_revision']['clear_inner_diameter_in']==76
assert model['cupola_foot_revision']['neck_in']==[3,8]
# TIMESTAMP START 2026-11-03T17:00:04-05:00 | REVISION R005063
assert model['cupola_foot_revision']['head_width_in']==3.75
assert model['cupola_foot_revision']['engagement_in']==3
# TIMESTAMP END 2026-11-03T17:00:04-05:00 | REVISION R005063

assert model['cupola_foot_revision']['capacity_checked'] is False
physical={pid:solid(p) for pid,p in parts.items() if p.get('is_timber') or p.get('group')=='joinery_pegs'}
changed={f'{f}{k}' for k in range(8) for f in ['C','T','CP']}
for k in range(8):
    for family in ['C','T','CP']:
        # TIMESTAMP START 2026-11-03T17:00:04-05:00 | REVISION R005063
        pid=f'{family}{k}';p=parts[pid];s=physical[pid]
        assert inspect_mesh(np.asarray(p['vertices']),np.asarray(p['triangles'],dtype=np.uint64))['status']=='PASS',pid
        assert len(s.decompose())==1,pid
        # TIMESTAMP END 2026-11-03T17:00:04-05:00 | REVISION R005063
    # TIMESTAMP START 2026-11-03T17:00:04-05:00 | REVISION R005063
    joint=next(j for j in model['tenon_schedule'] if j['donor']==f'T{k}' and j['receiver']==f'C{k}')
    v=np.asarray(joint['connector']['vertices']);normal=np.asarray(joint['insertion_direction']);width=np.asarray(joint['width_direction'])
    assert abs(np.ptp(v@normal)/I-3)<1e-8
    assert abs(np.ptp(v@width)/I-3.75)<1e-8
    assert abs(np.ptp(v[:,1])/I-8)<1e-8
    assert (solid(joint['connector'])^physical[f'C{k}']).volume()/I**3<1e-6
    # TIMESTAMP END 2026-11-03T17:00:04-05:00 | REVISION R005063
    peg=parts[f'CP{k}']
    assert peg['is_timber'] is False and peg['temporary'] is False and peg['displayRole']=='jointFastener'
    assert peg['group']=='joinery_pegs' and peg['dimensions']['width_in']==.75
    # A peg must physically engage both members, not merely sit near the joint.
    for family in ['C','T']:
        assert physical[f'CP{k}'].min_gap(physical[f'{family}{k}'],.01)<1e-8
count=0;maximum=0.
for a,b in itertools.combinations(physical,2):
    if not ({a,b}&changed) or not close_bounds(physical[a],physical[b]):continue
    v=max(0.,(physical[a]^physical[b]).volume()/I**3);maximum=max(maximum,v);count+=1
    assert v<1e-6,(a,b,v)
# Local finite trajectory independently replays actual saved solids, retaining
# the removed peg as an obstacle. Full scene planning is checked separately.
ids=['P0','T0','R0','C0','CP0'];scene=Scene('foot-test',{p:parts[p] for p in ids},{p:physical[p] for p in ids},{p:np.zeros(3) for p in ids})
for moving,delta in [(['CP0'],[0,0,.3]),(['C0','R0'],[0,.3,0]),(['R0'],[.3,-.1,0]),(['T0'],[-.2,0,0])]:
    proof=check_stage(scene,moving,delta);assert proof['status']=='PASS',proof['collisions']
    apply_stage(scene,moving,delta,proof=proof)
print('PASS: eight flared foot/peg sets, three-inch dovetail depths and flat bearing ends, connected clean meshes,',count,'physical pair checks; local four-stage removal; max overlap in3',maximum)
# TIMESTAMP END 2026-11-02T17:13:08-05:00 | REVISION R004818
