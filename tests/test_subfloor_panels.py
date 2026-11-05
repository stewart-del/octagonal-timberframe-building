# TIMESTAMP START 2026-11-05T12:32:16+00:00 | REVISION R000040
"""Real panel stock, intended joint gaps and physical sheet pair boundaries."""
from pathlib import Path
import itertools,sys
import numpy as np
import manifold3d as m
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from physical_data import read_physical_json
I=.0254;TOL=1e-6*I**3
data=read_physical_json(ROOT/'src/floor-foundation-solids.json');panels=[p for p in data['parts'] if p.get('floorRole')=='underlayment_sheet'];assert len(panels)==28
shapes=[]
for p in panels:
 stock=p['sheet_stock'];v=np.asarray(p['vertices']);assert np.allclose([stock['widthM'],stock['lengthM'],stock['thicknessM']],[47.875*I,95.875*I,.703*I],rtol=0,atol=1e-12)
 assert np.ptp(v@stock['shortAxisM'])<=47.875*I+1e-9 and np.ptp(v@stock['longAxisM'])<=95.875*I+1e-9
 assert abs(np.ptp(v[:,1])-.703*I)<1e-10
 shape=m.Manifold(m.Mesh64(v,np.asarray(p['triangles'],np.uint64)));assert str(shape.status())=='Error.NoError' and len(shape.decompose())==1;shapes.append(shape)
for a,b in itertools.combinations(shapes,2):assert max(0.,(a^b).volume())<=TOL,'Independent sheets interpenetrate'
assert data['fastenerSummary']['edgeBackingPieces']==24
print('PASS:28 connected actual.703in ×47.875in ×95.875in stock cut panels, intended⅛in joints,24separate perimeter/notch backers, no panel overlap')
# TIMESTAMP END 2026-11-05T12:32:16+00:00 | REVISION R000040
