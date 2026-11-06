# TIMESTAMP START 2026-11-04T19:57:30+00:00 | REVISION R000005
"""Owner-approved local cupola clearances for one-at-a-time hip erection.

These cuts establish nominal geometric access; they do not establish capacity
or uplift restraint. The complete building route is certified separately.
"""
import copy
import hashlib
import json
from pathlib import Path
import numpy as np
import manifold3d as m
from audit_revised_joinery import native_solid as solid, packed
from step_lap import mesh, volume_centroid, I
from export_top_entry_cavities import stock
from plan_architectural_disassembly import Scene, check_stage, apply_stage

ROOT=Path(__file__).resolve().parents[1]
REVISION='R000005'
STAMP='2026-11-04T19:57:30+00:00'

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def write(path,value):path.write_text(json.dumps(value,separators=(',',':'))+'\n')
def radial(k):return np.array([np.cos(k*np.pi/4),0,-np.sin(k*np.pi/4)])

def generate():
    path=ROOT/'src/top-entry-proposed-model.json'
    model=json.loads(path.read_text())
    if model.get('independent_hip_entry_revision',{}).get('revision')==REVISION:
        assert model['independent_hip_entry_revision']['generator_sha256']==sha(Path(__file__))
        print('Independent hip entries already installed');return
    before_sha=sha(path)
    records={p['id']:p for p in model['parts']}
    shapes={pid:solid(p) for pid,p in records.items() if p.get('is_timber') or p.get('is_fastener') or pid=='M-TMP'}
    original=dict(shapes);tools={}
    for k in range(8):
        joint=next(j for j in model['tenon_schedule'] if j['donor']==f'R{k}' and j['receiver']==f'C{k}')
        points=np.asarray(joint['connector']['vertices']);up=np.array([0,I,0]);out=radial(k)*4*I
        tool=m.Manifold.hull_points(np.vstack([points,points+up]))+m.Manifold.hull_points(np.vstack([points+up,points+up+out]))
        for pid in [f'C{k}',f'L{k}-S',f'L{(k-1)%8}-S']:
            tools[pid]=tools.get(pid,m.Manifold())+tool
    changed={};entries=model['joinery_entry_regions']
    for pid,tool in tools.items():
        final=solid(mesh(shapes[pid]-tool))
        assert str(final.status())=='Error.NoError' and len(final.decompose())==1,pid
        removed=shapes[pid]-final
        assert removed.volume()>0
        shapes[pid]=final
        records[pid].update(packed(final))
        records[pid]['faces']=records[pid]['triangles']
        records[pid]['fit_geometry']={**records[pid].get('fit_geometry',{}),**volume_centroid(final)}
        prior=solid(entries[pid]) if pid in entries and entries[pid]['triangles'] else m.Manifold()
        # The full in-stock access region also covers an old neighboring tongue
        # pocket exposed when that tongue is trimmed by the new entry opening.
        entries[pid]=packed(prior+(tool^stock(records[pid])))
        changed[pid]={'removed_volume_in3':removed.volume()/I**3,'connected_components':len(final.decompose()),
                      'before_volume_m3':original[pid].volume(),'after_volume_m3':final.volume()}
    for joint in model['tenon_schedule']:
        if joint['donor'] not in changed:continue
        donor=shapes[joint['donor']]
        connector=solid(joint['connector'])^donor
        joint['connector']=packed(connector)
        if 'cutting_tool' in joint:joint['cutting_tool']=packed(solid(joint['cutting_tool'])^donor)
        vertices=np.asarray(joint['connector']['vertices'])
        assert abs(np.ptp(vertices@joint['insertion_direction'])/I-3)<1e-7,joint['id']
        joint['width_m']=float(np.ptp(vertices@joint['width_direction']))
        joint['height_m']=float(np.ptp(vertices@joint['height_direction']))
    included={pid:p for pid,p in records.items() if pid in shapes and not pid.startswith(('J','CR','CC'))}
    scene=Scene('independent-hip-entry',included,{pid:shapes[pid] for pid in included},{pid:np.zeros(3) for pid in included})
    for k in range(8):
        for delta in [[0,I,0],(radial(k)*4*I).tolist()]:
            proof=check_stage(scene,[f'R{k}'],delta)
            assert proof['status']=='PASS',(k,proof['collisions'])
            apply_stage(scene,[f'R{k}'],delta,proof,label='Independent hip entry '+str(k))
    for item in model['proposed_member_volume_centroids']:
        if item['id'] in changed:item.update(volume_centroid(shapes[item['id']]))
    model['independent_hip_entry_revision']={'revision':REVISION,'timestamp':STAMP,'generator_sha256':sha(Path(__file__)),
        'source_model_sha256':before_sha,'release_lift_in':1,'release_outward_in':4,'changed_member_ids':sorted(changed),
        'entry':'Lift each hip one inch, then slide four inches radially outward; reverse to install.',
        'capacity_verified':False,'uplift_restraint_verified':False}
    write(path,model)
    report={'status':'PASS','revision':REVISION,'timestamp':STAMP,'model_sha256':sha(path),'source_model_sha256':before_sha,
            'generator_sha256':sha(Path(__file__)),'changes':changed,'stages':scene.stages,
            'scope':'Continuous local access against all stationary primary members except prerequisite short rafters and cupola roof/ceiling; full building route certified separately.',
            'unchanged_families':['R','P','B','T','K','L-H','CP'],'capacity_verified':False,'uplift_restraint_verified':False}
    write(ROOT/'docs/cupola-entry-audit.json',report)
    print('PASS:',len(changed),'local receiver changes; 16 independent hip release stages; sizes and three-inch tenons retained')

if __name__=='__main__':generate()
# TIMESTAMP END 2026-11-04T19:57:30+00:00 | REVISION R000005
