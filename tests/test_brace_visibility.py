# TIMESTAMP START 2026-11-02T18:37:05-05:00 | REVISION R004835
"""Keep the actual interior diagonal faces in front of secondary wall surfaces."""
from pathlib import Path
import hashlib,json,sys
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from audit_brace_visibility import audit,hits
from plan_architectural_disassembly import load_scene

saved=json.loads((ROOT/'docs/brace-visibility-audit.json').read_text())
assert saved['status']=='PASS'
for path,expected in saved['sources'].items():
    assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==expected,(path,'stale visibility evidence')
actual=audit(load_scene('top-entry'))
assert actual=={k:v for k,v in saved.items() if k!='image'},'Actual mesh-ray evidence differs from the saved report'
assert saved['image']['path']=='public/review/interior-braces.png'
assert hashlib.sha256((ROOT/saved['image']['path']).read_bytes()).hexdigest()==saved['image']['sha256'],'Review image differs from its source-bound report'
assert actual['physical_braces_in_complete']==24 and actual['inward_braces']==8
assert actual['maximum_side_brace_wall_occlusion']<.005
for part in actual['parts']:
    assert all(view['visible_samples']>0 for view in part['views']),part['id']
# A physical skin between the eye and a brace target must register as an
# occluder; moving that same skin behind the target must cease to occlude.
skin=np.array([[[1.,-1,-1],[1.,1,-1],[1.,0,1]]])
assert len(hits(np.array([0.,0,0]),np.array([2.,0,0]),skin)[0])==1
assert not len(hits(np.array([0.,0,0]),np.array([.5,0,0]),skin)[0])
print('PASS:24 Complete braces,8 inward supports, actual source-bound interior mesh rays and deliberate skin occlusion detection')
# TIMESTAMP END 2026-11-02T18:37:05-05:00 | REVISION R004835
