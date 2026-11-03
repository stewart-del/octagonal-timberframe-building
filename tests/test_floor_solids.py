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
# TIMESTAMP START 2026-11-02T21:30:42-05:00 | REVISION R004880
import sys
sys.path.insert(0,str(R/'scripts'))
from plan_architectural_disassembly import sweep_cover,VOLUME_TOLERANCE_M3
for pid,s in ss.items():
 if not pid.startswith('FLOOR-JOIST-'):continue
 sweep,account=sweep_cover(s,[0,.17,0])
 for plate,q in ss.items():
  if plate.startswith('POST-BEARING-STAND-') and '-SIDE' in plate:
   assert (sweep^q).volume()+account['discarded_prism_volume_m3']<VOLUME_TOLERANCE_M3,(pid,plate)
print('PASS: every north-south joist clears the open sideplate slots after headplate removal')
# TIMESTAMP END 2026-11-02T21:30:42-05:00 | REVISION R004880
