# TIMESTAMP START 2026-11-03T13:09:36-05:00 | REVISION R005024
"""Independent solid-kernel readback of browser-generated parametric geometry."""
import itertools,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from step_lap import close_bounds,contacts
# TIMESTAMP START 2026-11-03T16:50:27-05:00 | REVISION R005061
from audit_revised_joinery import native_solid as solid
import numpy as np
# TIMESTAMP END 2026-11-03T16:50:27-05:00 | REVISION R005061

path=Path(sys.argv[1] if len(sys.argv)>1 else '/tmp/octagon-parameter-core.json')
data=json.loads(path.read_text());model=data['model'];parts={p['id']:p for p in model['parts'] if p.get('is_timber') or p.get('is_fastener') or p['id']=='M-TMP'}
parts.update({p['id']:p for p in data.get('components',[])})
shapes={pid:solid(p) for pid,p in parts.items()};invalid=[];overlaps=[];checks=0;I=.0254
for pid,s in shapes.items():
    if str(s.status())!='Error.NoError' or s.volume()<=0:invalid.append((pid,str(s.status()),s.volume()))
for a,b in itertools.combinations(shapes,2):
    if not close_bounds(shapes[a],shapes[b]):continue
    checks+=1;amount=(shapes[a]^shapes[b]).volume()/I**3
    if amount>1e-6:overlaps.append((a,b,amount))
# TIMESTAMP START 2026-11-03T16:50:27-05:00 | REVISION R005061
for joint in model['tenon_schedule']:
    points=np.asarray(joint['connector']['vertices']);normal=np.asarray(joint['insertion_direction'])
    depth=np.ptp(points@normal)/I
    assert abs(depth-3)<1e-5,(joint['id'],'tenon depth',depth)
    donor,receiver=shapes[joint['donor']],shapes[joint['receiver']]
    assert donor.min_gap(receiver,.01)<1e-6,(joint['id'],'joint gap')
# TIMESTAMP END 2026-11-03T16:50:27-05:00 | REVISION R005061
print(json.dumps({'parameters':data['config'],'invalid':invalid,'overlaps':overlaps,'checks':checks},indent=2))
assert not invalid and not overlaps,'Parametric physical solids fail independent readback'
# TIMESTAMP END 2026-11-03T13:09:36-05:00 | REVISION R005024
