"""Fit display rails/floor around unchanged actual timber and footing solids.
Not a proposed structural joint or connection-capacity analysis.
"""
from pathlib import Path
import json,subprocess,hashlib
import numpy as np
import manifold3d as m
R=Path(__file__).resolve().parents[1]
raw=(R/'src/model-data.json').read_bytes();model=json.loads(raw)
components=json.loads(subprocess.check_output(['node','-e',"const m=require('./src/model-data.json'),s=require('./src/schematic-walls.js');process.stdout.write(JSON.stringify(s.build(m.parts,{applyFit:false}).components))"],cwd=R))
def solid(p):
 s=m.Manifold(m.Mesh64(np.asarray(p['vertices'],dtype=float),np.asarray(p['triangles'],dtype=np.uint64))).set_tolerance(1e-9)
 assert str(s.status())=='Error.NoError',p['id']
 return s
def overlap(a,b):
 x,y=a.bounding_box(),b.bounding_box();return all(x[i+3]>y[i]+1e-10 and y[i+3]>x[i]+1e-10 for i in range(3))
timbers={p['id']:solid(p) for p in model['parts'] if p['is_timber']};footers={p['id']:solid(p) for p in components if p['schematicKind']=='footer'}
data={'source_model_sha256':hashlib.sha256(raw).hexdigest(),'source_module_sha256':hashlib.sha256((R/'src/schematic-walls.js').read_bytes()).hexdigest(),'status':'Visualization clearance fit only; rail joints, foundations and floor support undesigned.','parts':{}}
for p in components:
 if p['schematicKind'] not in ['rail','floor']:continue
 s=solid(p);before=s.volume();hits=[]
 for name,t in (timbers if p['schematicKind']=='rail' else footers).items():
  if not overlap(s,t):continue
  amount=(s^t).volume()
  if amount>1e-12:s=s-t;hits.append({'part':name,'removed_m3':amount})
 assert str(s.status())=='Error.NoError' and s.volume()>0,p['id']
 mesh=s.to_mesh64();v=np.asarray(mesh.vert_properties)[:,:3];tris=mesh.tri_verts
 for name,t in (timbers if p['schematicKind']=='rail' else footers).items():
  if overlap(s,t):assert (s^t).volume()<1e-10,(p['id'],name)
 data['parts'][p['id']]={'vertices':v.tolist(),'triangles':tris.tolist(),'center':((v.min(0)+v.max(0))/2).tolist(),'source_volume_m3':before,'fitted_volume_m3':s.volume(),'clearance_cuts':hits,'connected_components':len(s.decompose())}
(R/'src/enclosure-fit.json').write_text(json.dumps(data,separators=(',',':'))+'\n')
print('Fitted',len(data['parts']),'rail/floor components; canonical timber untouched')
