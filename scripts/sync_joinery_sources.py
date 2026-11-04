# TIMESTAMP START 2026-11-03T15:59:31-05:00 | REVISION R005046
"""Install checked joinery candidates and recompute their dependent quantities."""
from pathlib import Path
import argparse,copy,hashlib,itertools,json,shutil
from step_lap import solid,volume_centroid,close_bounds,contacts,I

ROOT=Path(__file__).resolve().parents[1]
FILES={'baseline':('model-data.json','load-review-data.json','material-groups.json'),
       'proposed':('step-lap-proposed-model.json','step-lap-proposed-load-review.json','step-lap-proposed-material-groups.json'),
       'top-entry':('top-entry-proposed-model.json','top-entry-proposed-load-review.json','top-entry-proposed-material-groups.json')}
HISTORY={'revision':'R005046','timestamp':'2026-11-03T15:59:31-05:00'}
def read(path):return json.loads(path.read_text())
def save(path,data):path.write_text(json.dumps(data,separators=(',',':'))+'\n')
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def install(folder):
    backup=Path('/tmp/octagon-before-three-inch-20261103');backup.mkdir(exist_ok=True)
    for name,_,_ in FILES.values():
        target=ROOT/'src'/name
        if not (backup/name).exists():shutil.copyfile(target,backup/name)
        candidate=read(folder/name);assert candidate['three_inch_joinery_revision']['status']=='PASS'
        save(target,candidate)
    baseline=read(ROOT/'src/model-data.json');baseline_sha=sha(ROOT/'src/model-data.json')
    proposed=read(ROOT/'src/step-lap-proposed-model.json')
    before={p['id']:p for p in baseline['parts']}
    changed=[p['id'] for p in proposed['parts'] if p!=before[p['id']]]
    proposed['proposed_review'].update(baseline_model_sha256=baseline_sha,changed_member_ids=changed)
    save(ROOT/'src/step-lap-proposed-model.json',proposed)
    proposal=read(ROOT/'src/step-lap-proposal.json')
    proposal['baseline_model_sha256']=baseline_sha
    proposal['combined_geometry_audit']['changed_member_ids']=changed
    proposal['three_inch_revision']=HISTORY
    save(ROOT/'src/step-lap-proposal.json',proposal)
    top_proposal=read(ROOT/'src/top-entry-proposal.json')
    top_proposal['baseline_model_sha256']=sha(ROOT/'src/step-lap-proposed-model.json')
    top_proposal['three_inch_revision']=HISTORY
    save(ROOT/'src/top-entry-proposal.json',top_proposal)
    foundation=read(ROOT/'src/floor-foundation-solids.json')
    for k,center in enumerate(foundation['layout']['sourcePostCenters']):
        assert before[f'P{k}']['center'][::2]==[center[0],center[2]]
    foundation['source_model_sha256']=baseline_sha
    save(ROOT/'src/floor-foundation-solids.json',foundation)
    shutil.copyfile(folder/'three-inch-tenon-audit.json',ROOT/'docs/three-inch-tenon-audit.json')
    print('Installed revised models; floor solids preserved exactly',flush=True)

def auxiliary():
    for variant,(model_name,load_name,material_name) in FILES.items():
        path=ROOT/'src'/model_name;model=read(path);digest=sha(path)
        load=read(ROOT/'src'/load_name)
        load.update(source_model_sha256=digest,issues=[],baseline_pressure_disabled=True,
                    status='Self-weight from current geometry; joint reactions, contact pressures and capacity are not calculated.',
                    members=[dict(id=p['id'],**volume_centroid(solid(p))) for p in model['parts'] if p['is_timber']],
                    fasteners=[dict(id=p['id'],**volume_centroid(solid(p))) for p in model['parts'] if p.get('is_fastener')])
        load['fastener_volume_m3']=sum(p['volume_m3'] for p in load['fasteners'])
        save(ROOT/'src'/load_name,load)
        materials=read(ROOT/'src'/material_name);materials['source_sha256']=digest
        assert sorted(pid for g in materials['groups'] for pid in g['member_ids'])==sorted(p['id'] for p in model['parts'])
        for group in materials['groups']:
            group['status']='Current geometric family; select individual members for tenon measurements.'
        save(ROOT/'src'/material_name,materials)
    model=read(ROOT/'src/model-data.json');shapes={p['id']:solid(p) for p in model['parts'] if p['is_timber'] or p.get('is_fastener')}
    checks=0
    for a,b in itertools.combinations(shapes,2):
        if not close_bounds(shapes[a],shapes[b]):continue
        checks+=1;assert (shapes[a]^shapes[b]).volume()/I**3<=1e-6,(a,b,'wood overlap')
    joints=[]
    for j in model['tenon_schedule']:
        a,b=j['donor'],j['receiver'];contact=contacts(shapes[a],shapes[b])
        assert shapes[a].min_gap(shapes[b],.01)<1e-7,(a,b,'gap')
        joints.append({'owner':a,'receiver':b,'projection_in':3,'contact':contact,
                       'projected_contact_area_in2':sum(q['area_in2'] for q in contact)})
    save(ROOT/'docs/joinery-verification.json',{'status':'PASS','source_model_sha256':sha(ROOT/'src/model-data.json'),
         'pair_checks':checks,'joints':joints,'revision':HISTORY,'capacity_verified':False})
    print('Current volumes, centroids, inventory and physical contacts verified',flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--install',type=Path);parser.add_argument('--auxiliary',action='store_true');args=parser.parse_args()
    if args.install:install(args.install)
    if args.auxiliary:auxiliary()
# TIMESTAMP END 2026-11-03T15:59:31-05:00 | REVISION R005046
