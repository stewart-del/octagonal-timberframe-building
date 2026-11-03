# TIMESTAMP START 2026-11-03T11:58:59-05:00 | REVISION R004997
"""Replan finish release and retain the welded support until every truss is clear."""
import argparse
import json
import numpy as np
from plan_architectural_disassembly import (ROOT, load_scene, check_stage, check_multi_stage,
    apply_stage, apply_multi_stage, attempt_path, replay_stages, audit_final_joinery)
from plan_compact_disassembly import route

def moving(stage):
    return [pid for motion in stage.get('motions', [stage]) for pid in motion['member_ids']]

def is_finish(pid):
    return pid.startswith(('SCHEM-FLOOR-SECTOR-', 'FLOOR-BAMBOO-CENTER-'))

def checked(scene, ids, delta, label):
    proof = check_stage(scene, ids, delta, stop_first=True)
    assert proof['status'] == 'PASS', (label, proof['collisions'])
    apply_stage(scene, ids, delta, proof, label)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    recipe = json.loads((ROOT/'scripts/compact-disassembly-route.json').read_text())
    assert not recipe.get('finish_support_resequence'), 'Already resequenced'
    scene = load_scene('top-entry')
    finishes = [pid for pid in scene.parts if is_finish(pid)]
    checked(scene, finishes, [0, .05, 0],
            'Lift finished bamboo last-installed layer; keep structural floor in place')
    old_floor_start = next(i for i, s in enumerate(recipe['stages']) if any(is_finish(p) for p in moving(s)))
    last_truss = max(i for i, s in enumerate(recipe['stages'])
                    if any(p in {f'{prefix}{k}' for prefix in ['T', 'R', 'C'] for k in range(8)} for p in moving(s)))
    fixture = [s for s in recipe['stages'] if 'M-TMP' in moving(s)]
    for index, stage in enumerate(recipe['stages']):
        if 'M-TMP' in moving(stage):
            continue
        if index == old_floor_start:
            checked(scene, finishes, [0, -.05, 0], 'Route lifted bamboo into the cleared floor exit plane')
        if index == 969:
            target = np.array([2.8, 1.6, 0.])
            for side in [.15, -.15, .3, -.3, .5, -.5]:
                sideways = np.array([0., 0., side])
                segments = [sideways, np.array([0., 1., 0.]), target-scene.offsets['T0']-sideways-np.array([0., 1., 0.])]
                ok, proof = attempt_path(scene, 'Withdraw T0 around the retained eight-L support', ['T0'], segments)
                if ok:
                    break
            assert ok, ('T0 needs a clear path around retained support', proof)
            continue
        if index == 970:
            continue
        if 'motions' in stage:
            proof = check_multi_stage(scene, stage['motions'], stop_first=True)
            assert proof['status'] == 'PASS', (index, stage['label'], proof['collisions'])
            apply_multi_stage(scene, stage['motions'], proof, stage['label'])
        else:
            checked(scene, stage['member_ids'], stage['delta_m'], stage['label'])
        if index == last_truss:
            for step in fixture:
                checked(scene, step['member_ids'], step['delta_m'],
                        'Release eight-L support after all trusses are clear' if step is fixture[0] else step['label'])
        if index % 50 == 0:
            print('Checked original stage', index, flush=True)
    for index, stage in enumerate(scene.stages):
        stage['id'] = f'stage-{index+1:04d}'
    recipe.update(stages=[{k: v for k, v in s.items() if k in ['id','label','member_ids','delta_m','motions']}
                          for s in scene.stages], sources=scene.sources,
                  finish_support_resequence={'revision': 'R004997', 'bamboo_lift_m': .05,
                    'support_rule': 'Keep M-TMP in place until all R, T and C members are clear'},
                  _change_history={'revision': 'R004997', 'timestamp': '2026-11-03T11:58:59-05:00'})
    separation = audit_final_joinery(scene)
    assert separation['status'] == 'PASS', separation
    with open(args.output, 'w') as stream:
        json.dump(recipe, stream, separators=(',', ':'))
        stream.write('\n')
    print('PASS', len(scene.stages), 'stages; bamboo lifts first, support remains until the last truss', flush=True)

if __name__ == '__main__':
    main()
# TIMESTAMP END 2026-11-03T11:58:59-05:00 | REVISION R004997
