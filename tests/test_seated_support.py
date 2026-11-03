"""Temporary support positioning, not a connection capacity check."""
import sys,json,math
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from support_fit import fit_fixture,mesh,INCH
for name in ['model-data.json','step-lap-proposed-model.json','top-entry-proposed-model.json']:
    path=R/'src'/name
    if not path.exists():continue
    model=json.loads(path.read_text());before=json.dumps(model['parts'],sort_keys=True)
    p,r=fit_fixture(model)
    assert json.dumps(model['parts'],sort_keys=True)==before
    assert r['assembly_components']==1 and not r['positive_intersections']
    assert len(r['holes'])==24
    assert all(h['wood_entry_gap_m']==0 and h['wood_path_m']>5.9*INCH for h in r['holes'])
    v=np.asarray(p['vertices']);assert np.allclose((v.max(0)-v.min(0))/INCH,[90,14,90],atol=1e-9)
    assert len(mesh(p).decompose())==1
    # TIMESTAMP START 2026-11-02T17:44:11-05:00 | REVISION R004823
    print(name,'24 hole paths hit adjacent timber; no primary-timber interference; original model unchanged')
    # TIMESTAMP END 2026-11-02T17:44:11-05:00 | REVISION R004823
