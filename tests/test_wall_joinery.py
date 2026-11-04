# TIMESTAMP START 2026-11-02T21:09:01-05:00 | REVISION R004877
"""Independently verify occupied dovetails, connected stock and matching cavities."""
from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from fit_wall_joinery import unpack,union,TOL
from plan_architectural_disassembly import load_scene,audit_initial_scene

fits=json.loads((ROOT/'src/wall-joinery-fit.json').read_text())
for variant,fit in fits['variants'].items():
    for path,digest in fit['sources'].items():
        assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest,path
    scene=load_scene(variant)
    for pid,p in {**fit['primary_parts'],**fit['wall_parts']}.items():
        solid=unpack(p)
        assert solid.volume()>0 and len(solid.decompose())==1,pid
        removed=unpack(p['wallJoineryRemoved'])
        assert (solid^removed).volume()<TOL,pid
        donors=union([scene.solids[j['donor']] for j in fit['joints'] if j['receiver']==pid])
        actual_entry=(removed-donors).volume()
        assert abs(actual_entry-p['joineryCavity']['additional_entry_clearance']['volume_m3'])<TOL,pid
    assert len(fit['joints'])==134
    # TIMESTAMP START 2026-11-02T22:01:35-05:00 | REVISION R004882
    doorway=[j for j in fit['joints'] if j['donor'] in ['SCHEM-W-rail0-0','SCHEM-W-rail0-1'] and j['receiver'] in ['P2','P3']]
    assert len(doorway)==2
    for j in doorway:
        assert j['withdrawal_direction']==[0,-1,0],j['id']
        assert 'downward' in j['family'],j['id']
    # TIMESTAMP END 2026-11-02T22:01:35-05:00 | REVISION R004882
    for j in fit['joints']:
        donor=scene.solids[j['donor']];receiver=scene.solids[j['receiver']]
        tongue=unpack(j['tongue']);removed=unpack(j['removed_from_receiver'])
        assert (donor^receiver).volume()<TOL,j['id']
        assert (donor^tongue^removed).volume()>TOL,j['id']
        # TIMESTAMP START 2026-11-03T16:40:59-05:00 | REVISION R005059
        assert j['head_width_m']>j['neck_width_m'] and abs(j['engagement_m']-3*.0254)<1e-12,j['id']
        # TIMESTAMP END 2026-11-03T16:40:59-05:00 | REVISION R005059
    audit=audit_initial_scene(scene)
    assert audit['status']=='PASS',audit['collisions']
    print('PASS',variant,'134 complementary wall joints; connected stock, entry volumes, source binding and',audit['pair_checks'],'complete-scene intersection checks',flush=True)
# TIMESTAMP END 2026-11-02T21:09:01-05:00 | REVISION R004877
