"""Verify runtime clearance geometry; not structural support or connection design."""
from pathlib import Path
import hashlib,json,subprocess
import numpy as np
import manifold3d as m
R=Path(__file__).resolve().parents[1];raw=(R/'src/model-data.json').read_bytes();model=json.loads(raw);fit=json.loads((R/'src/enclosure-fit.json').read_text())
assert fit['source_model_sha256']==hashlib.sha256(raw).hexdigest()
assert fit['source_module_sha256']==hashlib.sha256((R/'src/schematic-walls.js').read_bytes()).hexdigest()
items=json.loads(subprocess.check_output(['node','-e',"process.stdout.write(JSON.stringify(require('./src/schematic-walls.js').build(require('./src/model-data.json').parts).components))"],cwd=R))
def solid(p):return m.Manifold(m.Mesh64(np.array(p['vertices'],dtype=float),np.array(p['triangles'],dtype=np.uint64)))
def overlap(a,b):
 x,y=a.bounding_box(),b.bounding_box();return all(x[i+3]>y[i]+1e-10 and y[i+3]>x[i]+1e-10 for i in range(3))
timbers=[solid(p) for p in model['parts'] if p['is_timber']];footers=[solid(p) for p in items if p['schematicKind']=='footer'];rails=[p for p in items if p['schematicKind']=='rail'];floor=[p for p in items if p['schematicKind']=='floor']
for p in rails+floor:
 s=solid(p);assert str(s.status())=='Error.NoError' and s.volume()>0
 for t in (timbers if p['schematicKind']=='rail' else footers):
  if overlap(s,t):assert (s^t).volume()<1e-10,p['id']
# At the middle of each wall the floor perimeter lies exactly on its inside face.
for k,p in enumerate(floor):
 n=np.array([np.cos((k+.5)*np.pi/4),0,-np.sin((k+.5)*np.pi/4)])
 post=next(x for x in model['parts'] if x['id']=='P'+str(k));r=np.hypot(post['center'][0],post['center'][2]);target=r*np.cos(np.pi/8)-.05
 assert abs(max(np.array(p['vertices'])@n)-target)<1e-8
assert all('unresolved' in q['status'] for q in json.loads(subprocess.check_output(['node','-e',"process.stdout.write(JSON.stringify(require('./src/schematic-walls.js').build(require('./src/model-data.json').parts).railConnections))"],cwd=R)))
print('PASS: all rail/timber overlaps removed, floor/footer clearance and inner-wall boundary exact; no structural-joint assertion')
