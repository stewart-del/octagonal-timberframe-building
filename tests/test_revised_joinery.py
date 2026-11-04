# TIMESTAMP START 2026-11-03T16:18:36-05:00 | REVISION R005052
"""Read back current solid geometry and measure every recorded primary tenon."""
from pathlib import Path
import hashlib,itertools,json,sys
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from step_lap import solid,close_bounds,I
from audit_cavity_fit import inspect_mesh,arrays
from export_top_entry_cavities import stock

for name in ['model-data.json','step-lap-proposed-model.json','top-entry-proposed-model.json']:
    raw=(ROOT/'src'/name).read_bytes();model=json.loads(raw)
    assert model['three_inch_joinery_revision']['status']=='PASS'
    records={p['id']:p for p in model['parts'] if p['is_timber'] or p.get('is_fastener')}
    shapes={pid:solid(p) for pid,p in records.items()}
    for pid,p in records.items():
        proof=inspect_mesh(*arrays(p),require_single=True)
        assert proof['status']=='PASS',(name,pid,proof['failures'])
        if p['is_timber']:
            blank=stock(p);assert (shapes[pid]-blank).volume()/I**3<1e-6,(pid,'exceeds raw stock')
    checks=0
    for a,b in itertools.combinations(shapes,2):
        if not close_bounds(shapes[a],shapes[b]):continue
        checks+=1;assert (shapes[a]^shapes[b]).volume()/I**3<1e-6,(name,a,b,'physical overlap')
    # TIMESTAMP START 2026-11-03T16:36:22-05:00 | REVISION R005058
    assert len(model['tenon_schedule'])==(120 if name.startswith('top-entry') else 136)
    # TIMESTAMP END 2026-11-03T16:36:22-05:00 | REVISION R005058
    for joint in model['tenon_schedule']:
        v=np.asarray(joint['connector']['vertices']);n=np.asarray(joint['insertion_direction'])
        assert abs(np.linalg.norm(n)-1)<1e-9
        assert abs(np.ptp(v@n)/I-3)<1e-6,(joint['id'],'depth is not three inches')
        assert abs(joint['projection_m']/I-3)<1e-9
        a,b=joint['donor'],joint['receiver']
        assert shapes[a].min_gap(shapes[b],.01)<1e-7,(joint['id'],'bearing gap')
    for k in range(8):
        assert records[f'P{k}']['dimensions']['width_in']==8
        assert records[f'C{k}']['dimensions']['width_in']==6
        for suffix in ['A','B','C']:
            p=records[f'K{k}-{suffix}'];assert p['dimensions']['width_in']==2 and p['dimensions']['depth_in']==6
        lower=[j for j in model['tenon_schedule'] if j['donor']==f'K{k}-C' and j['receiver']==f'P{k}'][0]
        upper=[j for j in model['tenon_schedule'] if j['donor'] in [f'K{k}-A',f'K{k}-B'] and j['receiver']==f'P{k}']
        assert max(v[1] for v in lower['connector']['vertices'])+8*I<min(v[1] for j in upper for v in j['connector']['vertices'])
    print(name,'PASS:',len(shapes),'physical solids;',checks,'overlap checks;',len(model['tenon_schedule']),'measured three-inch tenons',flush=True)

porch=json.loads((ROOT/'src/mudroom-joinery-fit.json').read_text())
assert porch['status']=='PASS'
for j in porch['joints']:
    if 'tenon_projection_m' in j:assert abs(j['tenon_projection_m']/I-3)<1e-9,j['id']
print('PASS: porch tenon projections and fitted-member audit')
# TIMESTAMP END 2026-11-03T16:18:36-05:00 | REVISION R005052
