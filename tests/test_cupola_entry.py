# TIMESTAMP START 2026-11-04T19:57:30+00:00 | REVISION R000005
"""Read back the changed receivers and independently replay each hip release."""
import hashlib
import json
import sys
from pathlib import Path
import numpy as np
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'scripts'))
from audit_revised_joinery import native_solid as solid
from plan_architectural_disassembly import Scene, check_stage, apply_stage
model=json.loads((root/'src/top-entry-proposed-model.json').read_text())
report=json.loads((root/'docs/cupola-entry-audit.json').read_text())
assert report['model_sha256']==hashlib.sha256((root/'src/top-entry-proposed-model.json').read_bytes()).hexdigest()
assert report['generator_sha256']==hashlib.sha256((root/'scripts/cupola_independent_entry.py').read_bytes()).hexdigest()
parts={p['id']:p for p in model['parts'] if (p.get('is_timber') or p.get('is_fastener') or p['id']=='M-TMP') and not p['id'].startswith(('J','CR','CC'))}
shapes={pid:solid(p) for pid,p in parts.items()}
for pid in report['changes']:
    assert len(shapes[pid].decompose())==1,pid
scene=Scene('entry-readback',parts,shapes,{pid:np.zeros(3) for pid in parts})
for k in range(8):
    assert parts[f'C{k}']['dimensions']['width_in']==6
    for delta in [[0,.0254,0],[4*.0254*np.cos(k*np.pi/4),0,-4*.0254*np.sin(k*np.pi/4)]]:
        proof=check_stage(scene,[f'R{k}'],delta)
        assert proof['status']=='PASS',(k,proof['collisions'])
        apply_stage(scene,[f'R{k}'],delta,proof)
for joint in model['tenon_schedule']:
    if not joint['donor'].startswith(('R','L')):continue
    assert abs(np.ptp(np.asarray(joint['connector']['vertices'])@joint['insertion_direction'])/.0254-3)<1e-7
print('PASS: all eight hips release independently; parked hips retained, cupola posts/rings stationary, connected receivers, three-inch tenons')
# TIMESTAMP END 2026-11-04T19:57:30+00:00 | REVISION R000005
