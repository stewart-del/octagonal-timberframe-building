# TIMESTAMP START 2026-11-04T23:48:03+00:00 | REVISION R000012
# TIMESTAMP START 2026-11-04T20:45:07+00:00 | REVISION R000009
"""Check the requested erection order against the published swept-motion proof."""
import json
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
plan=json.loads((ROOT/'src/disassembly-plan.json').read_text())['variants']['top-entry']
assert plan['status']=='PASS' and plan['verification']['status']=='PASS'
stages=plan['stages'];meta=plan['construction'];phases=meta['reverse_phases'];release=meta['release_stage_by_piece']
expected=['finish','windows','walls','porch','roof','trusses','cupola','ties','posts','post-caps','underlayment','floor-supports','foundations','compact']
assert list(phases)==expected
for i,name in enumerate(expected):
    lo,hi=phases[name];assert hi>lo
    if i:assert lo==phases[expected[i-1]][1]
assert phases[expected[-1]][1]==len(stages)
def motions(stage):return stage.get('motions',[stage])
def moving(stage):return {pid for m in motions(stage) for pid in m['member_ids']}
def phase_ids(name):
    lo,hi=phases[name];return set().union(*(moving(s) for s in stages[lo:hi]))
assert all(pid.startswith(('SCHEM-FLOOR-SECTOR-','FLOOR-BAMBOO-CENTER-')) for pid in phase_ids('finish'))
assert len([pid for pid in release if pid.startswith('FLOOR-SUBFLOOR-')])==28
for pid,index in release.items():
    assert pid in moving(stages[index]),(pid,index)
    assert index<phases['compact'][0], 'Off-site arrangements cannot introduce installed material'
for k in range(8):
    pid=f'R{k}';index=release[pid]
    assert phases['trusses'][0]<=index<phases['trusses'][1]
    assert moving(stages[index])=={pid} and moving(stages[index-1])=={pid}
    assert np.isclose(np.linalg.norm(motions(stages[index])[0]['delta_m']),.1016)
    assert np.allclose(motions(stages[index-1])[0]['delta_m'],[0,.0254,0])
    assert release[pid]<release[f'T{k}']<release['M-TMP'], 'Reverse construction: ties and original eight-L seat before hips'
    assert release[f'P{k}']>release[f'T{k}']
    cap=f'POST-BEARING-STAND-{k}-HEAD'
    assert phases['post-caps'][0]<=release[cap]<phases['post-caps'][1]
    assert release[f'P{k}']<release[cap]<min(release[p] for p in release if p.startswith('FLOOR-SUBFLOOR-'))
    assert release[f'PIER-{k}']>release[f'P{k}']
assert not any(pid.startswith('R') and len(pid)==2 for pid in phase_ids('cupola')), 'Hips must seat independently'
porch_start,porch_end=phases['porch'];porch_ids=phase_ids('porch')
assert {'MUD-POST-L-BACK','MUD-POST-R-BACK'}.issubset(porch_ids)
for pid in porch_ids:
    if pid.startswith(('MUD-SUPPORT-','MUD-POST-','MUD-RAFTER-')):assert porch_start<=release[pid]<porch_end
# Every above/below zone remains one continuous concrete column at every stage.
ids=set(plan['physical_ids'])
for stage in stages:
    delta={pid:m['delta_m'] for m in motions(stage) for pid in m['member_ids']}
    for pid in ids:
        if pid.endswith('-BELOW') and pid[:-6] in ids and pid.startswith(('PIER-','MUD-SUPPORT-')):
            assert delta.get(pid,[0,0,0])==delta.get(pid[:-6],[0,0,0])
assert set(plan['anchored_ids'])=={'FLOOR-CENTRAL-HUB','PIER-C','PIER-C-BELOW'}
# Preserve the accepted compact endpoint of existing pieces, not a remote yard.
compact=json.loads((ROOT/'scripts/compact-construction-endpoints.json').read_text())['offsets']
end={pid:np.zeros(3) for pid in ids}
for stage in stages:
    for motion in motions(stage):
        for pid in motion['member_ids']:end[pid]+=motion['delta_m']
for pid,target in compact.items():
    if pid in end:assert np.allclose(end[pid],target,atol=1e-8,rtol=0),(pid,end[pid],target)
assert plan['verification']['final_mating_separation']['status']=='PASS'
print('PASS: requested build order, independent hips, 28 underlayment sheets, full porch, continuous columns, flooring last and compact endpoints')
# TIMESTAMP END 2026-11-04T20:45:07+00:00 | REVISION R000009

# TIMESTAMP END 2026-11-04T23:48:03+00:00 | REVISION R000012
