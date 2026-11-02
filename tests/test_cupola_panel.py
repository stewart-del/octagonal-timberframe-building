"""Panel representation only: preserve current baseline geometry and self-weight."""
from pathlib import Path
import hashlib,json,sys
import numpy as np
import manifold3d as m
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from cupola_panel import solid,consolidate
model=json.loads((R/'src/model-data.json').read_text());parts=model['parts'];panel=next(p for p in parts if p['id']=='PLY');proof=json.loads((R/'docs/continuous-panel-baseline.json').read_text())
assert len(parts)==115 and sum(p['is_timber'] for p in parts)==104
assert not any(p['id'] in panel['legacy_ids'] for p in parts)
for p in parts:
 if p['id']=='PLY':continue
 if p['group']=='temporary_fixture':continue # Separately audited by test_central_support.py.
 if p['id']=='M-SP0':
  h=hashlib.sha256(json.dumps({k:p[k] for k in ['vertices','triangles','faces','exploded_offset']},sort_keys=True,separators=(',',':')).encode()).hexdigest()
  assert h==proof['fixture_geometry_hashes'][p['id']],p['id']
  continue
 sha=hashlib.sha256(json.dumps(p,sort_keys=True,separators=(',',':')).encode()).hexdigest()
 assert sha==proof['unchanged_part_hashes'][p['id']],p['id']
s=solid(panel);assert len(s.decompose())==1 and str(s.status())=='Error.NoError'
assert abs(s.volume()-proof['volume_m3'])<1e-10
assert np.allclose(s.bounding_box(),proof['bounds_m'],atol=1e-12,rtol=0)
assert abs(s.bounding_box()[4]-s.bounding_box()[1]-.0127)<1e-12
old=m.Manifold()
for p in proof['former_sectors']:old=old+solid(p)
assert (old-s).volume()<1e-10 and (s-old).volume()<1e-10
assert panel['exploded_offset']==[0,6.2,0]
assert consolidate(parts)==parts
assert all(model['component_id_history'][f'PLY{k}']=='PLY' for k in range(8))
assert all(model['component_id_history'][f'M-SP{k}']=='M-SP0' for k in range(1,8))
assert next(p for p in parts if p['id']=='M-SP0')['temporary']
assert len([p for p in parts if p['group']=='metal_spacers'])==1
assert len([p for p in parts if p.get('assembly_id')=='CENTRAL-SUPPORT'])==1
assert 'commercial sheet' in ' '.join(panel['notes']) and 'diaphragm' in ' '.join(panel['notes'])
print('PASS: one panel, original union/envelope/thickness/volume preserved; all permanent non-panel parts exact; surviving green-aid geometry exact;104 timber weights unchanged; ID history and unified explode retained')
