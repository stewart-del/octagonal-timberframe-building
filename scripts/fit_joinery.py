# TIMESTAMP START 2026-11-02T08:04:03-05:00 | REVISION R004746
# Restore the pre-R004741 joint study; custom sliding dovetails were withdrawn.
# TIMESTAMP START 2026-11-01T23:06:10-05:00 | REVISION R004659
# TIMESTAMP START 2026-11-01T22:44:38-05:00 | REVISION R004653
"""Complementary draft timber joints and an all-pairs solid/contact audit.

The socket is the exact same solid as its tongue. Joint allowances below are
explicit proposed geometry, not dimensions recovered from the source drawing.
Requires numpy, manifold3d and scipy. Run after revise_r01.py, before build.py.
"""
from pathlib import Path
import hashlib, itertools, json, math, re
import numpy as np
import manifold3d as m

ROOT=Path(__file__).resolve().parents[1]
I=.0254
D=json.loads((ROOT/'src/model-data.json').read_text())
P={p['id']:p for p in D['parts'] if p['is_timber']}
def solid(p):
    return m.Manifold(m.Mesh64(np.asarray(p['vertices']),np.asarray(p['triangles'],dtype=np.uint64))).set_tolerance(1e-9)
S={k:solid(p) for k,p in P.items()}
STOCK=S.copy()
SOCKETS={k:m.Manifold() for k in P}
JOINTS=[]
def v3(a):return np.asarray(a,dtype=float)
def radial(k):return np.array([math.cos(k*math.pi/4),0,-math.sin(k*math.pi/4)])
def tangent(k):return np.array([-math.sin(k*math.pi/4),0,-math.cos(k*math.pi/4)])
def resolved(s):return m.Manifold(s.to_mesh64()).set_tolerance(1e-9)

def cut_socket(owner,receiver,tongue,kind):
    assert tongue.volume()>1e-12,(owner,receiver,'empty joint')
    S[owner]=resolved(S[owner]+tongue)
    # TIMESTAMP START 2026-11-02T08:43:02-05:00 | REVISION R004750
    # Only the joint cutter defines removed stock. The complete owner also
    # touches the broad shoulder plane, producing spurious coplanar fragments
    # in some boolean intersections. Keep the timber subtraction unchanged.
    removed=resolved(S[receiver]^tongue)
    # TIMESTAMP END 2026-11-02T08:43:02-05:00 | REVISION R004750
    S[receiver]=resolved(S[receiver]-S[owner])
    SOCKETS[receiver]=resolved(SOCKETS[receiver]+removed)
    JOINTS.append({'owner':owner,'receiver':receiver,'kind':kind,'insert_volume_in3':tongue.volume()/I**3})

# Raise the roof reference by the actual timber depth in the generator; only
# the shallow heel seat, not a deep slice through the hip, is required here.
for k in range(8):
    seat=S[f'R{k}']^S[f'P{k}']
    S[f'R{k}']=S[f'R{k}']-S[f'P{k}']
    SOCKETS[f'R{k}']=SOCKETS[f'R{k}']+seat
    JOINTS.append({'owner':f'P{k}','receiver':f'R{k}','kind':'shallow heel bearing seat','insert_volume_in3':seat.volume()/I**3})

# Shallow birdsmouth bearing against the adjacent ring beams; same datum at all bays.
for k in range(8):
    for owner,receivers in [(f'R{k}',[f'B{k}',f'B{(k-1)%8}']), (f'J{k}-0',[f'B{k}']), (f'J{k}-2',[f'B{k}'])]:
        for receiver in receivers:
            seat=S[owner]^S[receiver]
            if seat.volume()>1e-12:
                S[owner]=S[owner]-S[receiver]
                SOCKETS[owner]=SOCKETS[owner]+seat
            JOINTS.append({'owner':receiver,'receiver':owner,'kind':'ring bearing seat','insert_volume_in3':seat.volume()/I**3})
print('Bearing seats complete',flush=True)

# Stop each brace within its own side of the post, leaving a central web.
# These are explicit two-inch-deep diagonal sockets, not a global collision trim.
for k in range(8):
    for suffix,sign,bay in [('A',-1,(k-1)%8),('B',1,k)]:
        name=f'K{k}-{suffix}'
        S[name]=S[name].trim_by_plane(tuple(sign*tangent(k)),2*I)
        for receiver in [f'P{k}',f'B{bay}']:
            insert=S[name]^S[receiver]
            cut_socket(name,receiver,insert,'diagonal brace socket; proposed depth')

print('Brace sockets complete',flush=True)

def tenon(owner,receiver,end,depth=2):
    """Grow a centered tongue through the existing physical contact plane."""
    p=P[owner]
    face=next(f for f in p['reference_end_faces'] if f['id']==owner+'-'+end)
    n=v3(face['normal']);c=np.mean(np.asarray(face['vertices']),axis=0)
    tongue=STOCK[owner].translate(tuple(n*depth*I))^STOCK[receiver]
    for key,half in [('width',p['dimensions']['width_in']/6),('depth',max(.5,p['dimensions']['depth_in']/2-1))]:
        axis=v3(p['stock_frame'][key])
        tongue=tongue.trim_by_plane(tuple(axis),float(axis@c-half*I))
        tongue=tongue.trim_by_plane(tuple(-axis),float(-axis@c-half*I))
    # Root the tongue 0.1 mm inside its own stock to avoid coplanar-union cracks.
    vertices=np.asarray(tongue.to_mesh64().vert_properties)[:,:3]
    tongue=m.Manifold.hull_points(np.vstack([vertices,vertices-n*.0001]).tolist()).set_tolerance(1e-9)
    cut_socket(owner,receiver,tongue,'centered shoulder tenon; proposed 2 in insertion')

for k in range(8):
    for owner,receiver,end in [(f'T{k}',f'P{k}','A'),(f'T{k}',f'C{k}','B'),
        (f'B{k}',f'P{k}','A'),(f'B{k}',f'P{(k+1)%8}','B'),
        (f'R{k}',f'C{k}','B'),(f'J{k}-0',f'R{k}','B'),(f'J{k}-2',f'R{(k+1)%8}','B')]:
        tenon(owner,receiver,end)
    print('Tenon bay',k,flush=True)
    for suffix in ['S','H']:
        tenon(f'L{k}-{suffix}',f'C{k}','A')
        tenon(f'L{k}-{suffix}',f'C{(k+1)%8}','B')
    JOINTS.append({'owner':f'C{k}','receiver':f'CR{k}','kind':'matching sloped roof bearing','insert_volume_in3':0})
    JOINTS.append({'owner':f'CR{k}','receiver':f'CR{(k+1)%8}','kind':'radial apex miter','insert_volume_in3':0})

# TIMESTAMP START 2026-11-01T23:19:38-05:00 | REVISION R004668
for k in range(8):
    JOINTS.append({'owner':f'C{k}','receiver':f'CC{k}','kind':'ceiling spoke butt contact; retention unresolved','insert_volume_in3':0})
    JOINTS.append({'owner':f'CC{k}','receiver':f'CC{(k+1)%8}','kind':'horizontal ceiling center miter; retention unresolved','insert_volume_in3':0})
# TIMESTAMP END 2026-11-01T23:19:38-05:00 | REVISION R004668

def mesh(s):
    result=s.to_mesh64()
    vv=np.asarray(result.vert_properties)[:,:3].tolist()
    tt=np.asarray(result.tri_verts).tolist()
    edges=sorted({tuple(sorted((t[i],t[(i+1)%3]))) for t in tt for i in range(3)})
    return {'vertices':vv,'triangles':tt,'edges':edges,'volume_m3':s.volume()}

def contact_area(a,b):
    """Area of opposite coplanar triangle intersections, independent of min_gap."""
    # A 1 micron translation closes the interface. Volume / translation gives
    # its projected area; test three orthogonal directions to avoid edge contact.
    step=1e-6
    values=[]
    for axis in np.eye(3):
        values.append(max((a.translate(tuple(axis*step))^b).volume(),(a.translate(tuple(-axis*step))^b).volume())/step)
    return max(values)

# This is an eightfold repeating frame: instantiate the solved bay-zero
# solids by exact 45-degree rotations, including their matching socket volumes.
# This also prevents independent trigonometric roundoff from splitting common faces.
for name in list(S):
    match=re.fullmatch(r'([A-Z]+)([0-7])(.*)',name)
    if match and match[2]!='0':
        base=match[1]+'0'+match[3]
        S[name]=S[base].rotate((0,int(match[2])*45,0))
        SOCKETS[name]=SOCKETS[base].rotate((0,int(match[2])*45,0))
print('Joint solids constructed; evaluating pair intersections',flush=True)
overlaps=[]
BOX={k:s.bounding_box() for k,s in S.items()}
for a,b in itertools.combinations(P,2):
    ba,bb=BOX[a],BOX[b]
    if any(ba[i+3]<bb[i]-1e-9 or bb[i+3]<ba[i]-1e-9 for i in range(3)):continue
    volume=(S[a]^S[b]).volume()/I**3
    if volume>1e-6:overlaps.append({'a':a,'b':b,'volume_in3':volume})
print('Pair intersections complete; checking contacts',flush=True)
for joint in JOINTS:
    a,b=joint['owner'],joint['receiver']
    joint['gap_mm']=S[a].min_gap(S[b],.1)*1000
    joint['projected_contact_area_in2']=contact_area(S[a],S[b])/I**2
invalid=[j for j in JOINTS if j['gap_mm']>1e-4 or j['projected_contact_area_in2']<.01]
print('Contact checks complete; checking connected solids',flush=True)
pieces=[]
for name,s in S.items():
    pieces.append({'id':name,'connected_solids':len(s.decompose()),'valid':str(s.status())=='Error.NoError',
        'original_volume_in3':STOCK[name].volume()/I**3,'final_volume_in3':s.volume()/I**3})
report={'revision':'R02','status':'PASS' if not overlaps and not invalid and all(p['connected_solids']==1 and p['valid'] for p in pieces) else 'FAIL',
    'wood_count':len(P),'pairs_tested':len(P)*(len(P)-1)//2,'overlap_tolerance_in3':1e-6,'gap_tolerance_mm':1e-4,
    'overlaps':overlaps,'invalid_contacts':invalid,'joints':JOINTS,'pieces':pieces,
    'scope':'Nominal mathematical fit only. Strength, movement, pegs, fasteners, tool clearance and raising sequence are not verified.',
    'source_dimensions':{'cupola_inside_in':76,'cupola_outside_in':88,'cupola_post_center_radius_in':41,'outer_corner_gap_in':28.132864853},
    'design_assumptions':['Main roof bearing datum corrected by 5 + 5/cos(atan(1/3)) inches to sit above the lower tie, retaining 4:12 slope and plan dimensions.',
        'Centered tenon thickness one third of member width, 1 inch depth shoulders, 2 inch insertion: proposed geometry only.',
        'Brace sockets terminate two inches inside the post side; source does not supply the joint.',
        'Cupola roof depth and backing remain provisional; source calls for 2x roof framing.']}
(ROOT/'docs/joinery-verification.json').write_text(json.dumps(report,indent=2)+'\n')
if report['status']!='PASS':
    print(json.dumps({'status':'FAIL','overlaps':overlaps,'invalid':invalid,'disconnected':[p for p in pieces if p['connected_solids']!=1]},indent=2))
    raise SystemExit(1)

cavities={}
for name,p in P.items():
    shaped=mesh(S[name]);p.update({k:shaped[k] for k in ['vertices','triangles']})
    p['faces']=shaped['triangles']
    p['fit_geometry']['volume_m3']=S[name].volume()
    p['fit_geometry']['nominal_fit']='Exact complementary solid; numerical audit R02'
    p['fit_geometry']['structural_design_status']='UNVERIFIED PROPOSED JOINERY'
    p['cut_status']='R02 DRAFT JOINERY · NOMINAL FIT VERIFIED · STRENGTH UNVERIFIED'
    p['notes']=[n for n in p['notes'] if 'Hidden by default' not in n and 'Hip, tie and post heel geometry still overlaps' not in n]
    p['notes'].append('R02 complementary joint geometry is an explicit design proposal, not a verified source cut or structural rating.')
    # Actual removed recesses only; exterior shoulder trimming is not an internal gap.
    removed=SOCKETS[name]
    # TIMESTAMP START 2026-11-02T08:43:02-05:00 | REVISION R004750
    # Do not export repeated coplanar 3D differences as alleged empty space.
    # Their inverted residual shells are numerically invalid. Occupancy is
    # independently checked by audit_cavity_fit.py against every mating solid.
    cavities[name]={'removed':mesh(removed)}
    # TIMESTAMP END 2026-11-02T08:43:02-05:00 | REVISION R004750
    p['geometry_planes_inches_status']='Pre-joinery reference envelope; current solid is the vertex/triangle mesh.'
# Each family separates in radius and height; paired braces also separate sideways.
# The same scalar drives every part, including brown posts and purple cupola timber.
# TIMESTAMP START 2026-11-01T23:19:38-05:00 | REVISION R004668
explosion_levels={'perimeter_posts':(1.4,0),'eave_ring':(2.1,.8),'radial_ties':(2.8,1.6),
 'radial_rafters':(3.5,2.5),'cupola_posts':(.8,3.2),'cupola_bands':(1.8,4.0),
 'cupola_rafters':(2.4,5.8),'braces':(2.3,.3),'secondary_approx':(4.3,3.4),
 'cupola_ceiling':(1.8,5.0),'cupola_plywood':(2.7,6.2),'metal_spacers':(2.5,4.8),'temporary_fixture':(1.0,-1.5),'roof_envelope':(3.1,6.8)}
# TIMESTAMP END 2026-11-01T23:19:38-05:00 | REVISION R004668
for p in D['parts']:
    c=np.asarray(p['center']);plan=np.array([c[0],0,c[2]])
    plan=plan/np.linalg.norm(plan) if np.linalg.norm(plan)>1e-9 else np.array([1.,0,0])
    radius,height=explosion_levels[p['group']]
    if p['group']=='cupola_bands' and p['id'].endswith('-H'):height+=.8;radius+=.4
    delta=plan*radius+np.array([0,height,0])
    if p['group']=='braces':delta+=np.array([-plan[2],0,plan[0]])*(.6 if p['id'].endswith('-A') else -.6)
    p['exploded_offset']=[0,6.2,0] if p['id']=='PLY' else [0,-1.5,0] if p['id']=='M-TMP' else delta.tolist()
# TIMESTAMP START 2026-11-01T23:19:38-05:00 | REVISION R004668
# Plywood is a separate half-inch horizontal material, cut around final timbers.
plywood=[]
for p in D['parts']:
    if p['group']!='cupola_plywood':continue
    sheet=solid(p)
    for timber in S.values():
        sheet=resolved(sheet-timber)
    assert str(sheet.status())=='Error.NoError' and len(sheet.decompose())==1,p['id']
    shaped=mesh(sheet)
    p.update({k:shaped[k] for k in ['vertices','triangles']});p['faces']=shaped['triangles']
    p['fit_geometry']['volume_m3']=sheet.volume()
    p['cut_status']='HORIZONTAL HALF-INCH PLYWOOD · ATTACHMENT AND PANEL SEAMS UNDESIGNED'
    plywood.append((p['id'],sheet))
report['sheet_goods_count']=len(plywood)
report['sheet_goods_timber_overlaps']=[]
for name,sheet in plywood:
    for other,timber in S.items():
        volume=(sheet^timber).volume()/I**3
        if volume>1e-6:report['sheet_goods_timber_overlaps'].append({'a':name,'b':other,'volume_in3':volume})
assert not report['sheet_goods_timber_overlaps'],report['sheet_goods_timber_overlaps']
# TIMESTAMP START 2026-11-02T08:43:02-05:00 | REVISION R004750
report['cavity_closure_status']='Run audit_cavity_fit.py for independent cavity occupancy checks; legacy 3D residual meshes are not exported.'
# TIMESTAMP END 2026-11-02T08:43:02-05:00 | REVISION R004750
# TIMESTAMP END 2026-11-01T23:19:38-05:00 | REVISION R004668
D['revision']='R02'
D['title']='Octagonal timberframe · cupola and complementary joint study'
D['status']='NOMINAL FIT VERIFIED · STRUCTURAL JOINT DESIGN UNVERIFIED'
D['joinery_verification']={k:report[k] for k in ['status','wood_count','pairs_tested','overlap_tolerance_in3','gap_tolerance_mm','scope','design_assumptions']}
D['r01']['heel_status']='R02 shallow seat and shoulder joinery modeled; strength not verified.'
D['r01']['global_overlap_status']='R02 all permanent timber pairs tested; no overlap above 0.000001 cubic inch.'
D['r01']['joint_status']='R02 nominal complementary geometry; fabrication and structural review pending.'
raw=json.dumps(D,separators=(',',':'))+'\n'
(ROOT/'src/model-data.json').write_text(raw)
sha=hashlib.sha256(raw.encode()).hexdigest()
materials=json.loads((ROOT/'src/material-groups.json').read_text());materials['source_sha256']=sha
(ROOT/'src/material-groups.json').write_text(json.dumps(materials,indent=2)+'\n')
(ROOT/'src/cavity-data.json').write_text(json.dumps({'schema_version':'r02-cavities','source_model_sha256':sha,'parts':cavities,'available':True,'summary':{'complete':True},'status':'Actual complementary sockets; occupied by mating wood at nominal fit.'},separators=(',',':'))+'\n')
report['source_model_sha256']=sha
(ROOT/'docs/joinery-verification.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'status':report['status'],'wood_pairs':report['pairs_tested'],'contact_pairs':len(JOINTS),'connected_solids':len(pieces)}))
# TIMESTAMP END 2026-11-01T22:44:38-05:00 | REVISION R004653

# TIMESTAMP END 2026-11-01T23:06:10-05:00 | REVISION R004659

# Preserve one panel identity and refresh model-bound metadata after fitting.
from cupola_panel import migrate
migrate(ROOT)
# TIMESTAMP END 2026-11-02T08:04:03-05:00 | REVISION R004746
