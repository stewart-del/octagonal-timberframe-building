"""Horizontal contact geometry, not allowable bearing or connection capacity."""
from pathlib import Path
import json,numpy as np,manifold3d as m
R=Path(__file__).resolve().parents[1];d=json.loads((R/'src/floor-foundation-solids.json').read_text());P={p['id']:p for p in d['parts']}
def surface(p,y,up):
 v=np.array(p['vertices']);result=m.CrossSection()
 for t in p['triangles']:
  q=v[t];n=np.cross(q[1]-q[0],q[2]-q[0])
  if max(abs(q[:,1]-y))>1e-8 or n[1]*up<=1e-14:continue
  poly=q[:,[0,2]].tolist();area=sum(poly[i][0]*poly[(i+1)%3][1]-poly[(i+1)%3][0]*poly[i][1] for i in range(3))
  if area<0:poly.reverse()
  result=result+m.CrossSection([poly])
 return result
pier=d['layout']['piers'][0]['topY_M'];ledge=pier+.143;top=pier+.286;hub=surface(P['FLOOR-CENTRAL-HUB'],ledge,1);areas=[]
for k in range(8):
 b=surface(P['FLOOR-BEAM-'+str(k)],ledge,-1);area=(hub^b).area();assert area>.015,(k,area);areas.append(area/.0254**2)
joist=[]
beamfaces=[surface(P['FLOOR-BEAM-'+str(k)],top,1) for k in range(8)]
# TIMESTAMP START 2026-11-02T20:27:45-05:00 | REVISION R004866
for member in d['layout']['members']:
 if member['kind']!='joist':continue
 f=surface(P[member['id']],top,-1)
 contacts=[(f^face).area() for face in beamfaces]
 bearing=[a for a in contacts if a>1e-5]
 assert len(bearing)>=2,(member['id'],contacts)
 joist.extend(a/.0254**2 for a in bearing)

# TIMESTAMP END 2026-11-02T20:27:45-05:00 | REVISION R004866
print('PASS center horizontal bearing in²',min(areas),max(areas),'joist horizontal bearing/end in²',min(joist),max(joist),'NOT capacity approval')
