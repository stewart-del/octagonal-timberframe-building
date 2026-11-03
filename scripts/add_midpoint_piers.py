# TIMESTAMP START 2026-11-03T12:04:27-05:00 | REVISION R005002
"""Add the half-radius pier ring without changing any existing physical member."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import numpy as np
from plan_architectural_disassembly import ROOT, VARIANTS, load_scene

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--candidates', required=True)
    args=parser.parse_args()
    folder=Path(args.candidates);folder.mkdir(exist_ok=True)
    floor=ROOT/'src/floor-foundation-solids.json'
    previous=json.loads(floor.read_text())
    old={p['id']:p for p in previous['parts']}
    assert not any(pid.startswith('PIER-MID-') for pid in old), 'Already added'
    subprocess.run([sys.executable,str(ROOT/'scripts/build_floor_solids.py')],check=True)
    updated=json.loads(floor.read_text())
    new={p['id']:p for p in updated['parts']}
    assert all(new[pid]==p for pid,p in old.items()), 'An existing physical member changed'
    added=set(new)-set(old)
    assert added=={f'PIER-MID-{k}{tail}' for k in range(8) for tail in ['', '-BELOW']}
    assert all(max(v[1] for v in new[pid]['vertices'])<-.4 for pid in added)
    wall_path=ROOT/'src/wall-joinery-fit.json';wall=json.loads(wall_path.read_text())
    for variant,(_,name) in VARIANTS.items():
        path=ROOT/'src'/name;fit=json.loads(path.read_text())
        # New piers lie entirely beneath the fitted floor. Existing solids were
        # compared exactly above, so all earlier enclosure cuts stay identical.
        fit['source_foundation_sha256']=digest(floor)
        path.write_text(json.dumps(fit,separators=(',',':'))+'\n')
        wall['variants'][variant]['sources']['src/'+name]=digest(path)
    wall_path.write_text(json.dumps(wall,separators=(',',':'))+'\n')
    plans=json.loads((ROOT/'src/disassembly-plan.json').read_text())['variants']
    recipe_path=ROOT/'scripts/compact-disassembly-route.json'
    recipe=json.loads(recipe_path.read_text())
    for variant in VARIANTS:
        candidate=recipe if variant=='top-entry' else plans[variant]
        stages=candidate['stages']
        lowering=next(stage for stage in stages if 'PIER-0' in stage.get('member_ids',[]) and stage.get('delta_m',[0,0,0])[1]<-.5)
        lowering['member_ids'].extend(sorted(added))
        for k in range(8):
            ids=[f'PIER-MID-{k}',f'PIER-MID-{k}-BELOW']
            point=np.asarray(new[ids[0]]['center']);point[1]=0;point/=np.linalg.norm(point)
            stages.extend([
                {'member_ids':ids,'delta_m':[0,-1.15,0],'label':f'Disengage full-height midpoint pier {k+1}'},
                {'member_ids':ids,'delta_m':(point*1.5).tolist(),'label':f'Spread midpoint pier {k+1} radially'}])
        for i,stage in enumerate(stages):stage['id']=f'stage-{i+1:04d}'
        candidate['sources']=load_scene(variant).sources
        (folder/(variant+'.json')).write_text(json.dumps(candidate,separators=(',',':'))+'\n')
        if variant=='top-entry':
            candidate['midpoint_piers']={'revision':'R005002','count':8,'radius_fraction':.5}
            recipe_path.write_text(json.dumps(candidate,separators=(',',':'))+'\n')
    print('PASS: 16 new rendering zones; every pre-existing floor solid exactly preserved; candidates require independent replay')

if __name__=='__main__':
    main()
# TIMESTAMP END 2026-11-03T12:04:27-05:00 | REVISION R005002
