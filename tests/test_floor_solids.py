import json,numpy as np,manifold3d as m
from pathlib import Path
R=Path(__file__).resolve().parents[1];d=json.loads((R/'src/floor-foundation-solids.json').read_text());ss={p['id']:m.Manifold(m.Mesh64(np.array(p['vertices']),np.array(p['triangles'],dtype=np.uint64))) for p in d['parts']};over=[];contacts={k:[] for k in ss}
for k,s in ss.items():assert str(s.status())=='Error.NoError' and s.volume()>0,k
keys=list(ss)
for i,a in enumerate(keys):
 for b in keys[i+1:]:
  x,y=ss[a].bounding_box(),ss[b].bounding_box()
  if any(x[k+3]<y[k]-1e-8 or y[k+3]<x[k]-1e-8 for k in range(3)):continue
  v=(ss[a]^ss[b]).volume()
  if v>1e-9:over.append((a,b,v))
  if ss[a].min_gap(ss[b],.00001)<1e-7:contacts[a].append(b);contacts[b].append(a)
print('overlaps',over[:12],'isolated',[k for k,v in contacts.items() if not v]);assert not over;assert all(contacts.values())
print('PASS',len(keys),'positive solids, no pair overlaps above1e-9m3, each touches another; contact is NOT capacity or full loadpath verification')
