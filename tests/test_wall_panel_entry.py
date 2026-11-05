# TIMESTAMP START 2026-11-04T20:06:20+00:00 | REVISION R000007
"""West panel strips reconstruct their walls and fit after the complete porch."""
import json
import subprocess
import sys
from pathlib import Path
import numpy as np
import manifold3d as m
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'scripts'))
from plan_architectural_disassembly import load_scene,check_stage,apply_stage
from audit_revised_joinery import native_solid as solid
from step_lap import close_bounds

for variant,model_file in [('baseline','model-data.json'),('proposed','step-lap-proposed-model.json'),('top-entry','top-entry-proposed-model.json')]:
    scene=load_scene(variant)
    model=json.loads((root/'src'/model_file).read_text())
    raw=json.loads(subprocess.check_output(['node','-e',"process.stdout.write(JSON.stringify(require('./src/schematic-walls.js').build(require('./src/'+process.argv[1]).parts,{applyFit:false,splitErection:false}).components))",model_file],cwd=root))
    original={p['id']:p for p in raw}
    parents={p['erectionParentId'] for p in scene.parts.values() if p.get('erectionParentId')}
    assert len(parents)==10
    wood={p['id']:solid(p) for p in model['parts'] if p.get('is_timber') or p.get('is_fastener')}
    for parent in parents:
        expected=solid(original[parent])
        for shape in wood.values():
            if close_bounds(expected,shape):expected=expected-shape
        pieces=[scene.solids[pid] for pid,p in scene.parts.items() if p.get('erectionParentId')==parent]
        united=m.Manifold.batch_boolean(pieces,m.OpType.Add)
        error=abs((expected-united).volume())+abs((united-expected).volume())
        assert error<1e-6*.0254**3,(parent,error)
    strips=sorted([p for p in scene.parts.values() if p.get('erectionParentId')],
        key=lambda p:(p['erectionOrder'],{'post-edge':0,'door-edge':1,'porch-band':2,'inner':1}[p['erectionStripRole']],p['id']))
    assert len(strips)==26
    checks=0
    for p in strips:
        for delta in p['erectionReleaseSteps']:
            proof=check_stage(scene,[p['id']],delta)
            assert proof['status']=='PASS',(p['id'],proof['collisions'])
            apply_stage(scene,[p['id']],delta,proof);checks+=1
    print('PASS:',variant,'26 strips reconstruct10 west panels and release in',checks,'continuous stages with porch, floor, frame and earlier released strips retained')
# TIMESTAMP END 2026-11-04T20:06:20+00:00 | REVISION R000007
