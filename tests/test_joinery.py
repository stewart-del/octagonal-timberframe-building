# TIMESTAMP START 2026-11-01T22:44:38-05:00 | REVISION R004653
"""Independently reload the exported solids and verify nominal fit and cavities."""
from pathlib import Path
import hashlib, itertools, json, math
import numpy as np
import manifold3d as m

ROOT=Path(__file__).resolve().parents[1]
raw=(ROOT/'src/model-data.json').read_bytes()
data=json.loads(raw)
audit=json.loads((ROOT/'docs/joinery-verification.json').read_text())
cavities=json.loads((ROOT/'src/cavity-data.json').read_text())
assert audit['status']=='PASS'
assert audit['source_model_sha256']==hashlib.sha256(raw).hexdigest()==cavities['source_model_sha256']
parts={p['id']:p for p in data['parts'] if p['is_timber']}
def solid(p):return m.Manifold(m.Mesh64(np.asarray(p['vertices']),np.asarray(p['triangles'],dtype=np.uint64))).set_tolerance(1e-9)
solids={k:solid(p) for k,p in parts.items()}
bounds={k:s.bounding_box() for k,s in solids.items()}
for name,s in solids.items():
    assert str(s.status())=='Error.NoError',name
    assert len(s.decompose())==1,name
for a,b in itertools.combinations(parts,2):
    x,y=bounds[a],bounds[b]
    if any(x[i+3]<y[i]-1e-9 or y[i+3]<x[i]-1e-9 for i in range(3)):continue
    assert (solids[a]^solids[b]).volume()/.0254**3<=1e-6,(a,b,'overlap')
for joint in audit['joints']:
    a,b=joint['owner'],joint['receiver']
    assert solids[a].min_gap(solids[b],.01)<1e-7,(a,b,'gap')
    assert joint['projected_contact_area_in2']>.01,(a,b,'edge-only contact')
for k in range(8):
    # Uprights and ties share their bottom datum; no member spans the well below.
    assert abs(min(v[1] for v in parts[f'C{k}']['vertices'])-min(v[1] for v in parts[f'T{k}']['vertices']))<1e-8
    p=parts[f'R{k}'];r=np.array([math.cos(k*math.pi/4),0,-math.sin(k*math.pi/4)])
    # Main hip top uses one plane across its width, with no center ridge.
    vv=np.asarray(p['vertices']);heights=vv[:,1]+(vv@r)/3
    top=vv[np.abs(heights-heights.max())<1e-8]
    assert len(top)>=4,(p['id'],'flat top missing')
    for name in [f'C{k}',f'P{k}']:
        cavity=cavities['parts'][name]['removed']
        assert cavity['volume_m3']>0 and cavity['triangles'],name
assert all(g['default_visible'] for g in data['groups'] if g['id'] in ['cupola_bands','cupola_rafters'])
print(f'PASS: {len(solids)} reloaded solids, {len(solids)*(len(solids)-1)//2} wood pairs, {len(audit["joints"])} contacts, cupola datums, flat tops and current cavities')
# TIMESTAMP END 2026-11-01T22:44:38-05:00 | REVISION R004653

# TIMESTAMP START 2026-11-01T23:19:38-05:00 | REVISION R004668
# Horizontal plywood thickness and material-to-timber non-overlap are independent checks.
plywood=[p for p in data['parts'] if p['group']=='cupola_plywood']
assert len(plywood)==1 and plywood[0]['id']=='PLY'
for p in plywood:
    y=[v[1] for v in p['vertices']]
    assert abs((max(y)-min(y))/.0254-.5)<1e-8
    sheet=solid(p)
    assert len(sheet.decompose())==1
    for name,timber in solids.items():
        assert (sheet^timber).volume()/.0254**3<=1e-6,(p['id'],name,'plywood overlap')
for k in range(8):
    p=parts[f'CC{k}']
    assert abs(p['axis_start'][1]-p['axis_end'][1])<1e-9,'Ceiling spoke must be horizontal'
print('PASS: horizontal half-inch plywood, eight horizontal spokes and plywood/timber separation')
# TIMESTAMP END 2026-11-01T23:19:38-05:00 | REVISION R004668
