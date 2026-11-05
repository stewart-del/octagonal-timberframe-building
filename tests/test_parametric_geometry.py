# TIMESTAMP START 2026-11-04T23:23:25+00:00 | REVISION R000011
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
# TIMESTAMP START 2026-11-05T16:01:12+00:00 | REVISION R000052
assert data['config'].get('cupolaPitch',data['config']['pitch'])==data['config']['pitch'],'Cupola pitch must follow the main roof'
# TIMESTAMP END 2026-11-05T16:01:12+00:00 | REVISION R000052
parts.update({p['id']:p for p in data.get('components',[])})
# TIMESTAMP START 2026-11-05T17:19:58+00:00 | REVISION R000058
from audit_cavity_fit import inspect_mesh
raw_failures=[]
for pid,p in parts.items():
 if p.get('is_timber'):
  check=inspect_mesh(np.asarray(p['vertices']),np.asarray(p['triangles'],np.uint64),require_single=True)
  if check['status']!='PASS':raw_failures.append({'id':pid,'failures':check['failures']})
assert not raw_failures,('Parametric timber export has invalid raw boundaries',raw_failures)
# TIMESTAMP END 2026-11-05T17:19:58+00:00 | REVISION R000058
shapes={pid:solid(p) for pid,p in parts.items()};invalid=[];overlaps=[];checks=0;I=.0254
for pid,s in shapes.items():
    if str(s.status())!='Error.NoError' or s.volume()<=0:invalid.append((pid,str(s.status()),s.volume()))
for a,b in itertools.combinations(shapes,2):
    if not close_bounds(shapes[a],shapes[b]):continue
    checks+=1;amount=(shapes[a]^shapes[b]).volume()/I**3
    if amount>1e-6:overlaps.append((a,b,amount))
# TIMESTAMP START 2026-11-03T16:50:27-05:00 | REVISION R005061
for joint in model['tenon_schedule']:
    # TIMESTAMP START 2026-11-05T14:18:42+00:00 | REVISION R000046
    points=np.asarray(joint['connector']['vertices']);normal=np.asarray(joint.get('projection_direction',joint['insertion_direction']))
    depth=np.ptp(points@normal)/I
    if joint['id'].startswith('ROOF-SUPPORT-') and joint['receiver'].startswith('B'):
        assert 0<depth<=1+1e-5,(joint['id'],'Tapered perimeter bearing step must fit its1in allowance',depth)
        assert abs(depth-joint['projection_m']/I)<1e-5,(joint['id'],'Reported step differs from actual connector')
    elif joint['id'].startswith('ROOF-SUPPORT-') and joint.get('shape')=='top-entry inclined nose':
        assert 2-1e-5<=depth<=2.01+1e-5,(joint['id'],'Top-entry nose projection',depth)
    else:assert abs(depth-3)<1e-5,(joint['id'],'Three-inch structural tenon depth',depth)
    # TIMESTAMP END 2026-11-05T14:18:42+00:00 | REVISION R000046
    # TIMESTAMP START 2026-11-04T20:12:02+00:00 | REVISION R000019
    if joint.get('bearing_direction'):
        plane=max(points@np.asarray(joint['bearing_direction']))
        assert abs(plane-joint['bearing_coordinate_m'])<1e-6,(joint['id'],'bearing plane detached from current tenon')
    # TIMESTAMP END 2026-11-04T20:12:02+00:00 | REVISION R000019
    donor,receiver=shapes[joint['donor']],shapes[joint['receiver']]
    assert donor.min_gap(receiver,.01)<1e-6,(joint['id'],'joint gap')
# TIMESTAMP END 2026-11-03T16:50:27-05:00 | REVISION R005061
print(json.dumps({'parameters':data['config'],'invalid':invalid,'overlaps':overlaps,'checks':checks},indent=2))
assert not invalid and not overlaps,'Parametric physical solids fail independent readback'
# TIMESTAMP END 2026-11-03T13:09:36-05:00 | REVISION R005024

# TIMESTAMP END 2026-11-04T23:23:25+00:00 | REVISION R000011
