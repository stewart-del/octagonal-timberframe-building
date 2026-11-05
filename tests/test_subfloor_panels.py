# TIMESTAMP START 2026-11-04T23:48:03+00:00 | REVISION R000012
# TIMESTAMP START 2026-11-04T19:48:56+00:00 | REVISION R000004
"""Every modeled underlayment piece fits one 4 x 8 sheet; the floor is covered."""
import itertools
import json
from pathlib import Path
import numpy as np
import manifold3d as m

root=Path(__file__).resolve().parents[1]
data=json.loads((root/'src/floor-foundation-solids.json').read_text())
panels=[p for p in data['parts'] if p.get('floorRole')=='underlayment_sheet']
assert len(panels)>20 and not any(p['id']=='FLOOR-SUBFLOOR' for p in data['parts'])
solids=[]
for part in panels:
    stock=part['sheet_stock'];vertices=np.asarray(part['vertices'])
    assert stock['widthM']==48*.0254 and stock['lengthM']==96*.0254
    assert np.ptp(vertices@stock['shortAxisM'])<=48*.0254+1e-10
    assert np.ptp(vertices@stock['longAxisM'])<=96*.0254+1e-10
    assert abs(np.ptp(vertices[:,1])-1.5*.0254)<1e-10
    assert stock['staggerM']==48*.0254
    shape=m.Manifold(m.Mesh64(vertices,np.asarray(part['triangles'],np.uint64)))
    assert str(shape.status())=='Error.NoError' and len(shape.decompose())==1
    solids.append(shape)
for a,b in itertools.combinations(solids,2):
    assert abs((a^b).volume())<1e-13,'Sheets may share an edge, but may not overlap'
assembled=m.Manifold.batch_boolean(solids,m.OpType.Add)
assert abs(sum(s.volume() for s in solids)-assembled.volume())<1e-12
fixture=json.loads((root/'scripts/fixtures/underlayment-footprint.json').read_text())['footprint']
reference=m.Manifold(m.Mesh64(np.asarray(fixture['vertices']),np.asarray(fixture['triangles'],np.uint64)))
assert abs((reference-assembled).volume())+abs((assembled-reference).volume())<1e-12
assert len(panels)==28
print('PASS:',len(panels),'separate staggered 4 x 8 sheets; stock bounds, thickness, connectedness, no overlap, exact footprint coverage')
# TIMESTAMP END 2026-11-04T19:48:56+00:00 | REVISION R000004

# TIMESTAMP END 2026-11-04T23:48:03+00:00 | REVISION R000012
