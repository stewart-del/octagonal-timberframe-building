# TIMESTAMP START 2026-11-02T15:51:57-05:00 | REVISION R004809
"""A concave slot must remain open, and parked parts remain collision obstacles."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
import manifold3d as m
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from plan_architectural_disassembly import Scene,sweep_cover,triangle_prism,check_stage,apply_stage,check_multi_stage,apply_multi_stage,replay_stages,VOLUME_TOLERANCE_M3

skinny=np.array([[3,4,5],[4,4,5],[3.2,4+1e-9,5]],float)
prism=triangle_prism(skinny,[0,0,20])
expected=abs(np.dot(np.cross(skinny[1]-skinny[0],skinny[2]-skinny[0]),[0,0,20]))/2
assert abs(prism.volume()-expected)<1e-16 and prism.volume()>VOLUME_TOLERANCE_M3
# This actual oblique short-rafter mesh previously caused a hull to erase a
# significant skinny boundary prism; the explicit prism must cover its path.
root=Path(__file__).resolve().parents[1]
piece=next(p for p in json.loads((root/'src/top-entry-proposed-model.json').read_text())['parts'] if p['id']=='J0-2')
shape=m.Manifold(m.Mesh64(np.asarray(piece['vertices']),np.asarray(piece['triangles'],np.uint64)))
covered,_=sweep_cover(shape,[0,4.5,0])
for fraction in [.1,.5,.9]:assert (shape.translate([0,4.5*fraction,0])-covered).volume()<VOLUME_TOLERANCE_M3

stock=m.Manifold.cube([3,3,1]);slot=m.Manifold.cube([1,2,1]).translate([1,1,0]);u=stock-slot
swept,account=sweep_cover(u,[0,0,2])
clear=m.Manifold.cube([.5,.5,.5]).translate([1.25,1.75,1.25])
assert (swept^clear).volume()<VOLUME_TOLERANCE_M3,'Sweep may not invent material inside an open slot'
assert abs(swept.volume()-u.volume()*3)<1e-10
assert account['method']=='solid plus exact boundary-triangle prisms'
solids={'moving':m.Manifold.cube([1,1,1]),'blocker':m.Manifold.cube([1,1,1]).translate([3,0,0])}
scene=Scene('test',{pid:{'id':pid} for pid in solids},solids,{pid:np.zeros(3) for pid in solids})
first=check_stage(scene,['moving'],[1,0,0]);assert first['status']=='PASS'
apply_stage(scene,['moving'],[1,0,0],first)
parked=check_stage(scene,['blocker'],[-2,0,0]);assert parked['status']=='BLOCKED'
assert parked['collisions'][0]['obstacle_parked'] is True
group=check_stage(scene,['moving','blocker'],[0,2,0]);assert group['status']=='PASS'
crossing=[{'member_ids':['moving'],'delta_m':[2,0,0]},{'member_ids':['blocker'],'delta_m':[-2,0,0]}]
relative=check_multi_stage(scene,crossing);assert relative['status']=='BLOCKED' and any(q['other_moving'] for q in relative['collisions'])
parallel=[{'member_ids':['moving'],'delta_m':[0,2,0]},{'member_ids':['blocker'],'delta_m':[0,2,0]}]
relative=check_multi_stage(scene,parallel);assert relative['status']=='PASS';apply_multi_stage(scene,parallel,relative)
print('PASS: continuous concave-slot sweep, parked obstacles, rigid groups and relative moving-to-moving collisions')
if '--replay-plan' in sys.argv:
    root=Path(__file__).resolve().parents[1];plan=json.loads((root/'src/disassembly-plan.json').read_text())
    for variant,entry in plan['variants'].items():
        for filename,digest in entry['sources'].items():assert hashlib.sha256((root/filename).read_bytes()).hexdigest()==digest,filename+' is stale'
        scene,proof=replay_stages(variant,entry['stages'])
        assert proof['status']=='PASS' and set(entry['physical_ids'])==set(scene.parts)
        moved={pid for stage in scene.stages for q in stage.get('motions',[stage]) for pid in q['member_ids']}
        assert moved==set(entry['moved_ids'])
        # TIMESTAMP START 2026-11-03T06:54:15-05:00 | REVISION R004896
        fixed=set(entry['anchored_ids'])
        assert fixed==({'FLOOR-CENTRAL-HUB','PIER-C','PIER-C-BELOW'} if variant=='top-entry' else set())
        assert not moved & fixed and all(np.array_equal(scene.offsets[pid],np.zeros(3)) for pid in fixed)
        assert set(entry['unmoved_ids'])==set(scene.parts)-moved-fixed
        # TIMESTAMP END 2026-11-03T06:54:15-05:00 | REVISION R004896
        blocked={pid for group in entry['blocked'] for pid in group['member_ids']}
        assert set(entry['unmoved_ids'])<=blocked,'Every physical piece without a path must be reported'
        assert all(q.get('physical') is False for q in entry['excluded'])
        if entry['status']=='PASS':
            assert not entry['blocked'] and not entry['unmoved_ids']
            assert entry['verification']['final_mating_separation']['status']=='PASS'
            assert not entry['verification']['final_mating_separation']['remaining_mating_pairs']
        print('PASS:',variant,len(entry['stages']),'stored stages replayed against',len(scene.parts),'physical solids')
# TIMESTAMP END 2026-11-02T15:51:57-05:00 | REVISION R004809
