# TIMESTAMP START 2026-11-03T13:09:36-05:00 | REVISION R005024
"""Retain exact independent receiver material before rebuilding roof joints.

Only the original roof-occupied pocket material is restored. All brace, tie,
cupola-band and peg cuts remain intact. Runtime recipes then recut these blanks.
"""
import hashlib,json
from pathlib import Path
from step_lap import mesh,original_stock
# TIMESTAMP START 2026-11-03T16:40:59-05:00 | REVISION R005059
from audit_revised_joinery import native_solid as solid,packed
from export_top_entry_cavities import stock
# TIMESTAMP END 2026-11-03T16:40:59-05:00 | REVISION R005059
from revise_main_braces import clean
# TIMESTAMP START 2026-11-03T15:42:57-05:00 | REVISION R005038
from apply_joinery_revision import normalized
# TIMESTAMP END 2026-11-03T15:42:57-05:00 | REVISION R005038

ROOT=Path(__file__).resolve().parents[1]
VARIANTS={'baseline':'model-data.json','proposed':'step-lap-proposed-model.json','top-entry':'top-entry-proposed-model.json'}
result={'revision':'R005024','timestamp':'2026-11-03T13:09:36-05:00','variants':{}}
baseline={p['id']:p for p in json.loads((ROOT/'src/model-data.json').read_text())['parts']}
for variant,name in VARIANTS.items():
    path=ROOT/'src'/name
    model=json.loads(path.read_text());parts={p['id']:p for p in model['parts']}
    roofs={pid:solid(p) for pid,p in parts.items() if p['group'] in ['radial_rafters','secondary_approx']}
    # TIMESTAMP START 2026-11-03T16:50:27-05:00 | REVISION R005061
    restored={};receiver_voids={}
    baseline_voids=json.loads((ROOT/'src/cavity-data.json').read_text())['parts']
    # TIMESTAMP END 2026-11-03T16:50:27-05:00 | REVISION R005061
    for pid in ['P0','B0','C0']:
        p=parts[pid]
        before=solid(p);blank=original_stock(p)
        if pid in ['P0','B0']:after=solid(baseline[pid])
        else:
            after=blank
            for key,q in parts.items():
                if key.startswith(('T','L','CP')) and (q.get('is_timber') or q.get('is_fastener')):
                    mate=solid(q)
                    if (after^mate).volume()>1e-12:after=after-mate
            # TIMESTAMP START 2026-11-03T15:42:57-05:00 | REVISION R005038
            after=normalized(after)
            # TIMESTAMP END 2026-11-03T15:42:57-05:00 | REVISION R005038
        print(variant,pid,flush=True)
        assert abs((before-after).volume())<1e-10,(pid,'restoration removed material')
        # TIMESTAMP START 2026-11-03T16:50:27-05:00 | REVISION R005061
        void=solid(baseline_voids[pid]['removed']) if pid in ['P0','B0'] else solid(packed(blank-after))
        for k in range(8):
            restored[pid[0]+str(k)]=mesh(after.rotate((0,45*k,0)))
            receiver_voids[pid[0]+str(k)]=mesh(void.rotate((0,45*k,0)))
        # TIMESTAMP END 2026-11-03T16:50:27-05:00 | REVISION R005061
    blanks={}
    for pid,p in parts.items():
        if not p.get('is_timber'):continue
        # TIMESTAMP START 2026-11-03T16:40:59-05:00 | REVISION R005059
        blank=stock(p)
        # TIMESTAMP END 2026-11-03T16:40:59-05:00 | REVISION R005059
        if p.get('declared_exterior_cut',{}).get('triangles'):blank=blank-solid(p['declared_exterior_cut'])
        blanks[pid]=mesh(blank)
    result['variants'][variant]={'source_model_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'roof_receivers':restored,'cavity_blanks':blanks,'roof_receiver_voids':receiver_voids}
(ROOT/'src/parametric-source.json').write_text(json.dumps(result,separators=(',',':'))+'\n')
print('Prepared roof receiver blanks for',', '.join(result['variants']))
# TIMESTAMP END 2026-11-03T13:09:36-05:00 | REVISION R005024
