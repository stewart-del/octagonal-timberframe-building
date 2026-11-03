# TIMESTAMP START 2026-11-02T17:07:05-05:00 | REVISION R004816
"""Unreleased geometric prototype of a bottom-entry housed dovetail foot.

The housed dovetail family is traditional; this foot orientation, dimensions,
and load path are a new proposal, not a verified historical detail or capacity.
No canonical model file is modified by this prototype.
"""
from pathlib import Path
import copy, hashlib, json
import numpy as np
import manifold3d as m
from step_lap import solid, mesh
from revise_main_braces import clean
from plan_architectural_disassembly import Scene, check_stage, apply_stage, check_multi_stage, apply_multi_stage

ROOT=Path(__file__).resolve().parents[1]
I=.0254


def box(low,high):
    low=np.asarray(low,float)*I;high=np.asarray(high,float)*I
    return m.Manifold.cube((high-low).tolist()).translate(low.tolist())


def prototype(parts):
    original={pid:solid(parts[pid]) for pid in ['P0','T0','R0','C0']}
    # Recover only the old T-owned tongue below the C/T contact plane. The
    # upper cupola joinery and all other C surfaces remain byte-for-byte stock.
    old_tongue=clean(original['T0']^box([37,84,-4],[44,96,4]))
    receiver=clean(original['C0']+old_tongue)
    tie_body=clean(original['T0']-old_tongue)
    # 1:8 flare on both sides: 3-inch neck, 4-inch head, four-inch engagement.
    # The eight-inch height retains a 24-square-inch neck before its peg bore.
    points=np.array([[x,y,z] for y in [85,93]
                     for x,z in [(44,-1.5),(44,1.5),(40,2),(40,-2)]])*I
    tail=m.Manifold.hull_points(points)
    root=box([44,85,-1.5],[44.01,93,1.5])
    tie=clean(tie_body+tail+root)
    cupola=clean(receiver-tail)
    # A separate transverse 3/4-inch hardwood peg locks the vertical entry.
    # Its size is a geometric assumption; no drawbore or strength is implied.
    peg=m.Manifold.cylinder(6*I,.375*I,.375*I,32).translate([42*I,89*I,-3*I])
    tie=clean(tie-peg);cupola=clean(cupola-peg)
    updated={**original,'T0':tie,'C0':cupola,'CP0':peg}
    union_before=original['C0']+original['T0']
    union_after=cupola+tie+peg
    # The new tongue uses C-owned stock; no extra assembly envelope is added.
    mismatch=(union_before-union_after).volume()+(union_after-union_before).volume()
    assert mismatch/I**3<1e-6,mismatch/I**3
    for pid in ['T0','C0']:
        assert len(updated[pid].decompose())==1,(pid,'disconnected')
    return updated,{'old_tongue_in3':old_tongue.volume()/I**3,
        'tail_in3':tail.volume()/I**3,'assembly_envelope_symmetric_difference_in3':mismatch/I**3,
        'neck_in':[3,8],'head_width_in':4,'engagement_in':4,'side_taper':'1:8',
        'peg_diameter_in':.75,'minimum_receiver_cheek_in':1,
        'inner_cupola_radial_face_in':38,'clear_inner_diameter_in':76}


def run():
    path=ROOT/'src/top-entry-proposed-model.json';raw=path.read_bytes()
    model=json.loads(raw);parts={p['id']:p for p in model['parts']}
    solids,dimensions=prototype(parts)
    records={pid:copy.deepcopy(parts.get(pid,{'id':pid,'is_timber':True})) for pid in solids}
    for pid,s in solids.items():records[pid].update(mesh(s))
    scene=Scene('prototype',records,solids,{pid:np.zeros(3) for pid in solids})
    proofs=[]
    for ids,delta,label in [(['CP0'],[0,0,.3],'Remove transverse peg'),
                            (['C0','R0'],[0,.3,0],'Lift cupola post and rafter together'),
                            (['R0'],[.3,-.1,0],'Withdraw rafter from the raised post'),
                            (['T0'],[-.2,0,0],'Withdraw tie from outer post')]:
        proof=check_stage(scene,ids,delta)
        proofs.append({'label':label,**proof})
        if proof['status']!='PASS':break
        apply_stage(scene,ids,delta,proof=proof,label=label)
    report={'status':'GEOMETRIC PROTOTYPE ONLY','source_model_sha256':hashlib.sha256(raw).hexdigest(),
        'dimensions':dimensions,'stages':proofs,
        'traditional_family_source':'https://www.vermonttimberworks.com/learn/timber-frame-joinery/purlins-and-joists/',
        'source_scope':'Housed dovetail family only. The source does not prescribe this open-bottom cupola-foot orientation, dimensions, peg or load capacity.',
        'limitations':['Local four-member loop only; full architecture and parked-piece trajectories still require checking.',
                       'One-inch minimum receiver cheeks require structural evaluation; no hurricane or fabrication qualification.']}
    # This conditional whole-primary-frame test isolates the proposed foot.
    # The braces/short rafters/roof/ceiling have not been teleported in the
    # production scene: their complete prior removal remains a prerequisite.
    primary={pid:solid(p) for pid,p in parts.items() if p.get('is_timber')
             and p['group']!='braces' and not pid.startswith(('J','CR','CC'))}
    for k in range(8):
        for family in ['T','C','CP']:
            primary[f'{family}{k}']=solids[family+'0'].rotate((0,45*k,0))
    records={pid:dict(parts.get(pid,{'id':pid,'is_timber':True}),**mesh(s)) for pid,s in primary.items()}
    ring=Scene('conditional-primary-prototype',records,primary,{pid:np.zeros(3) for pid in primary})
    def move(ids,delta,label):
        proof=check_stage(ring,ids,delta)
        assert proof['status']=='PASS',(label,proof['collisions'])
        apply_stage(ring,ids,delta,proof=proof,label=label)
    for k in range(8):
        a=-k*np.pi/4;tangent=np.array([-np.sin(a),0,np.cos(a)])
        move([f'CP{k}'],(.3*tangent).tolist(),'Remove cupola foot peg '+str(k))
        move([f'CP{k}'],[0,-1,0],'Lower removed cupola foot peg '+str(k))
        move([f'CP{k}'],(5*tangent).tolist(),'Park cupola foot peg '+str(k))
    roof=[pid for pid in primary if pid.startswith(('C','R','L')) and not pid.startswith('CP')]
    move(roof,[0,2,0],'Lift upper cupola and principal rafters clear of bottom-entry feet')
    for k in range(8):
        a=-k*np.pi/4;out=np.array([np.cos(a),0,np.sin(a)])
        move([f'R{k}'],(.3*out+np.array([0,-.1,0])).tolist(),'Withdraw principal-rafter tongue '+str(k))
        move([f'R{k}'],[0,3,0],'Lift detached principal rafter '+str(k))
        move([f'R{k}'],(18*out).tolist(),'Park principal rafter '+str(k))
    motions=[]
    for k in range(8):
        a=-k*np.pi/4;b=-(k+1)*np.pi/4
        first=np.array([np.cos(a),0,np.sin(a)]);second=np.array([np.cos(b),0,np.sin(b)])
        motions.append({'member_ids':[f'C{k}'],'delta_m':(.3*first).tolist()})
        motions.append({'member_ids':[f'L{k}-S',f'L{k}-H'],'delta_m':(.15*(first+second)).tolist()})
    proof=check_multi_stage(ring,motions)
    assert proof['status']=='PASS',proof['collisions']
    apply_multi_stage(ring,motions,proof=proof,label='Open cupola ring tenons simultaneously')
    for k in range(8):
        a=-k*np.pi/4;out=np.array([np.cos(a),0,np.sin(a)])
        move([f'C{k}'],(12*out).tolist(),'Park separate cupola post '+str(k))
    for k in range(8):
        a=-(k+.5)*np.pi/4;out=np.array([np.cos(a),0,np.sin(a)])
        for side in ['H','S']:
            move([f'L{k}-{side}'],[0,4 if side=='S' else 5,0],'Lift separate cupola ring member')
            move([f'L{k}-{side}'],(14*out).tolist(),'Park separate cupola ring member')
    report['conditional_primary_test']={'status':'PASS','excluded_prerequisite_families':['K','J','CR','CC','PLY','architecture'],
        'scope':'Finite paths for all eight modified C/T feet, principal rafters and cupola-ring timbers after excluded prerequisite families are removed. Does not certify the full scene.',
        'stages':ring.stages}
    (ROOT/'docs/cupola-foot-prototype.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'dimensions':dimensions,'stages':[{k:p[k] for k in ['label','status','maximum_intersection_m3','collisions']} for p in proofs]},indent=2))


if __name__=='__main__':run()
# TIMESTAMP END 2026-11-02T17:07:05-05:00 | REVISION R004816
