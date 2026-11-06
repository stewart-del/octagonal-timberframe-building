# TIMESTAMP START 2026-11-02T18:13:09-05:00 | REVISION R004829
"""Verify real panel seams preserve material and admit the local release step.

The motion check retains primary timbers, pegs and every new board. Removal of
the other enclosure layers is a prerequisite verified by the global planner.
"""
from pathlib import Path
import json,subprocess,sys
import numpy as np
import manifold3d as m

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from step_lap import solid,close_bounds,contacts
from plan_architectural_disassembly import Scene,check_stage,apply_stage,NODE
from audit_cavity_fit import inspect_mesh

TOL=1e-6*.0254**3
VARIANTS=[('model-data.json','enclosure-fit.json'),('step-lap-proposed-model.json','step-lap-proposed-enclosure-fit.json'),('top-entry-proposed-model.json','top-entry-proposed-enclosure-fit.json')]
SCRIPT="""const model=require(process.argv[1]);global.OCTAGON_ENCLOSURE_FIT=require(process.argv[2]);
const walls=require('./src/schematic-walls.js');process.stdout.write(JSON.stringify({
 fitted:walls.build(model.parts).components,
 unsplit:walls.build(model.parts,{applyFit:false,splitInfill:false}).components}));"""

def difference(a,b):return abs((a-b).volume())+abs((b-a).volume())

checks=0;seams=0;minimum_contact=float('inf');maximum_error=0.
for model_name,fit_name in VARIANTS:
    model=json.loads((ROOT/'src'/model_name).read_text())
    fit=json.loads((ROOT/'src'/fit_name).read_text())
    layout=json.loads(subprocess.check_output([NODE,'-e',SCRIPT,str(ROOT/'src'/model_name),str(ROOT/'src'/fit_name)],cwd=ROOT))
    current={p['id']:p for p in layout['fitted']};original={p['id']:p for p in layout['unsplit']}
    parents={p['panelAssemblyId'] for p in current.values() if p.get('panelAssemblyId')}
    assert len(parents)==14 and set(fit['panel_seams'])==parents
    primary={p['id']:p for p in model['parts'] if p.get('is_timber') or p.get('group')=='joinery_pegs'}
    primary_solids={pid:solid(p) for pid,p in primary.items()}
    for parent in sorted(parents):
        rows=[p for p in current.values() if p.get('panelAssemblyId')==parent]
        # TIMESTAMP START 2026-11-04T20:06:20+00:00 | REVISION R000007
        rows.sort(key=lambda p:p['panelSeamPart']);assert len(rows)>=2
        # TIMESTAMP END 2026-11-04T20:06:20+00:00 | REVISION R000007
        children=[solid(p) for p in rows]
        for p,shape in zip(rows,children):
            assert len(shape.decompose())==1,p['id']
            assert inspect_mesh(np.asarray(p['vertices']),np.asarray(p['triangles']))['status']=='PASS',p['id']
        expected=solid(original[parent])
        for obstacle in primary_solids.values():
            if close_bounds(expected,obstacle):expected=expected-obstacle
        # TIMESTAMP START 2026-11-04T20:06:20+00:00 | REVISION R000007
        low=m.Manifold.batch_boolean([shape for row,shape in zip(rows,children) if row['panelSeamPart']=='lower'],m.OpType.Add)
        high=m.Manifold.batch_boolean([shape for row,shape in zip(rows,children) if row['panelSeamPart']=='upper'],m.OpType.Add)
        reunited=low+high;error=difference(expected,reunited);maximum_error=max(maximum_error,error)
        # TIMESTAMP END 2026-11-04T20:06:20+00:00 | REVISION R000007
        assert error<TOL,(parent,'panel material changed',error)
        # TIMESTAMP START 2026-11-04T20:06:20+00:00 | REVISION R000007
        assert abs((low^high).volume())<TOL,(parent,'board overlap')
        area=sum(face['area_in2']*.0254**2 for face in contacts(low,high))
        # TIMESTAMP END 2026-11-04T20:06:20+00:00 | REVISION R000007
        assert area>1e-5,(parent,'missing actual shared seam face')
        minimum_contact=min(minimum_contact,area);seams+=1
        assert fit['panel_seams'][parent]['status']=='PASS'
        # An actual0.1mm gap must be detected by the same material-union audit.
        # TIMESTAMP START 2026-11-04T20:06:20+00:00 | REVISION R000007
        trimmed=low.trim_by_plane([0,-1,0],-(64*.0254-.0001))
        assert difference(expected,trimmed+high)>TOL,(parent,'gap rejection is ineffective')
        # TIMESTAMP END 2026-11-04T20:06:20+00:00 | REVISION R000007
    boards={p['id']:p for p in current.values() if p.get('panelAssemblyId')}
    parts={**primary,**boards};solids={**primary_solids,**{pid:solid(p) for pid,p in boards.items()}}
    scene=Scene('conditional-board-release',parts,solids,{pid:np.zeros(3) for pid in parts})
    for pid,p in sorted(boards.items()):
        if p['panelSeamPart']!='lower':continue
        delta=[0,-.4,0];proof=check_stage(scene,[pid],delta)
        assert proof['status']=='PASS',(pid,proof['collisions'])
        apply_stage(scene,[pid],delta,proof=proof);checks+=1
print('PASS:',seams,'exact shared panel seams;',checks,'continuous lower-board release steps; minimum contact',minimum_contact,'m2; maximum union difference',maximum_error,'m3. Full architectural sequencing is checked separately.')
# TIMESTAMP END 2026-11-02T18:13:09-05:00 | REVISION R004829
