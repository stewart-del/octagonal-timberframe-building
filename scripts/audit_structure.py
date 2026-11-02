# TIMESTAMP START 2026-11-01T23:19:38-05:00 | REVISION R004668
"""Measured geometry and load-path screening; never a structural capacity check."""
from pathlib import Path
import hashlib, itertools, json, math
import numpy as np
import manifold3d as m
ROOT=Path(__file__).resolve().parents[1]
I=.0254
raw=(ROOT/'src/model-data.json').read_bytes();D=json.loads(raw)
P={p['id']:p for p in D['parts']}
# TIMESTAMP START 2026-11-02T09:09:36-05:00 | REVISION R004753
cavity_fit=json.loads((ROOT/'docs/cavity-fit-audit.json').read_text())
assert cavity_fit['status']=='PASS'
assert cavity_fit['model_sha256']==hashlib.sha256(raw).hexdigest()
assert cavity_fit['cavity_sha256']==hashlib.sha256((ROOT/'src/cavity-data.json').read_bytes()).hexdigest()
# TIMESTAMP START 2026-11-02T10:05:34-05:00 | REVISION R004758
proposed_cavity_fit=json.loads((ROOT/'docs/step-lap-proposed-cavity-fit-audit.json').read_text())
assert proposed_cavity_fit['status']=='PASS'
assert proposed_cavity_fit['model_sha256']==hashlib.sha256((ROOT/'src/step-lap-proposed-model.json').read_bytes()).hexdigest()
assert proposed_cavity_fit['cavity_sha256']==hashlib.sha256((ROOT/'src/step-lap-proposed-cavities.json').read_bytes()).hexdigest()
# TIMESTAMP END 2026-11-02T10:05:34-05:00 | REVISION R004758
# TIMESTAMP END 2026-11-02T09:09:36-05:00 | REVISION R004753
def solid(p):return m.Manifold(m.Mesh64(np.asarray(p['vertices']),np.asarray(p['triangles'],dtype=np.uint64)))
def stock(p):
    planes=p['geometry_planes_inches'];N=np.array([v['normal'] for v in planes]);K=np.array([v['constant'] for v in planes]);points=[]
    for ix in itertools.combinations(range(len(planes)),3):
        if abs(np.linalg.det(N[list(ix)]))<1e-10:continue
        v=np.linalg.solve(N[list(ix)],K[list(ix)])
        if np.all(N@v<=K+1e-7):points.append([v[0]*I,v[2]*I,-v[1]*I])
    return m.Manifold.hull_points(points)
def section_screen(name):
    p=P[name];frame=np.array([p['stock_frame'][a] for a in ['width','depth','axis']]);xf=np.column_stack([frame,np.zeros(3)])
    s=solid(p).transform(xf);original=stock(p).transform(xf)
    vv=np.concatenate([np.asarray(s.to_mesh64().vert_properties)[:,:3],np.asarray(original.to_mesh64().vert_properties)[:,:3]])
    levels=sorted(set(float(z) for z in vv[:,2]));stations=set((a+b)/2 for a,b in zip(levels,levels[1:]))
    stations.update(z+d for z in levels for d in [-1e-6,1e-6])
    nominal=p['dimensions']['width_in']*p['dimensions']['depth_in'];rows=[]
    for z in sorted(stations):
        gross=original.slice(z).area()/I**2
        if gross<nominal*.99999:continue # exclude stock end miters and sloping head cuts
        net=(s.slice(z)^original.slice(z)).area()/I**2
        rows.append((net,z))
    net,z=min(rows)
    return {'part':name,'gross_area_in2':nominal,'minimum_sampled_body_area_in2':net,'remaining_area_percent':100*net/nominal,
            'station_world_axis_in':z/I,'method':'Cross sections at vertex planes +/- 1 micrometre and interval midpoints; only full original rectangular sections. End miters and added tongues excluded. Area ratio is not a strength ratio.'}
sections=[section_screen(name) for name in ['P0','C0','R0','J0-0','T0','B0']]
area=lambda r:2*math.sqrt(2)*r*r/144
main=area(200)-area(44);cap=area(56)
wood_volume=sum(p['fit_geometry']['volume_m3'] for p in P.values() if p['is_timber'])/.3048**3
# TIMESTAMP START 2026-11-02T08:05:33-05:00 | REVISION R004748
c_bottom=stock(P['C0']).bounding_box()[1]/I
t_bottom=stock(P['T0']).bounding_box()[1]/I
lower_joint_review={
 'status':'DESIGN HOLD — no replacement dovetail released',
 'existing_joint':'Horizontal radial tie end into the side of a cupola upright; the lower well stays open.',
 'cupola_post_bottom_in':c_bottom,'tie_underside_in':t_bottom,
 'full_depth_head_bottom_relish_in':max(0.0,t_bottom-c_bottom),
 'traditional_candidate':'Through wedged half-dovetail tie-to-post joint, with a separate hardwood wedge and bearing housing where required.',
 'geometric_limit':'A head retaining the full 10-inch tie depth reaches the current post bottom, leaving no timber below that head. A smaller head or reversed flare is an unverified adaptation, not a resolved repair.',
 'kingpost_distinction':'A traditional suspended kingpost can hang a continuous tie from a vertical through tenon. That arrangement is different from these radial tie ends entering cupola posts; the cupola and ring forces must be resolved before selecting the joint.',
 'release_requirements':['Resolve cupola/ring/tie forces and bearing support','Size cheeks, tenon, housing, remaining timber and any peg or wedge from the actual loads and material','Verify insertion, access and retention through the complete assembly sequence'],
 'provenance_limit':'The references document joint families in other structures. They do not establish the concealed joinery of the Bluetime building or approve dimensions for this model.'}
# TIMESTAMP END 2026-11-02T08:05:33-05:00 | REVISION R004748
findings=[
 # TIMESTAMP START 2026-11-02T08:05:33-05:00 | REVISION R004748
 {'id':'S1','priority':'critical','title':'Center connection design is on hold','parts':'T0–T7 / R0–R7 / C0–C7 / cupola rings',
  'finding':'The straight two-inch tongues have no pegs, bolts, retained dovetail or other positive withdrawal restraint. Nominal contact does not close the central force path.',
  'action':'Use documented traditional joint families, then resolve their suitability and dimensions for this open-center system. A through wedged half-dovetail is a documented horizontal tie-to-post family, but its housing, bottom relish and assembly are unresolved here. No new dovetail is released. Do not assume the polygon or plywood alone supplies ring action.'},
 # TIMESTAMP END 2026-11-02T08:05:33-05:00 | REVISION R004748
 {'id':'S2','priority':'high','title':'Main-rafter tongue exceeds the receiver-based proportion','parts':'R0–R7 to C0–C7',
  'finding':'The generic width rule uses the 8-inch rafter: 8/3 = 2.667 inches. In a 6-inch receiving post, nominal cheeks are only (6 - 2.667)/2 = 1.667 inches before neighboring cuts. TFEC 1-2019 §§3.4.10–11 use the receiving member and require each cheek at least the mortise width for the prescribed tension-joint provisions.',
  'action':'Redesign this joint from the receiving post and load demand. A broader head is not a remedy for thin cheeks. A dovetail is a different connection requiring its own neck, bearing and splitting/block-shear checks.'},
 {'id':'S3','priority':'high','title':'Two-inch insertion is not a ready-made pegged tension joint','parts':'All generic two-inch shoulder tenons',
  'finding':'No peg location or end distance is modeled. For illustration, the TFEC full geometry factor calls for 4D loaded-end distance in a softwood tension member: a 3/4-inch peg alone needs 3 inches from peg center to the loaded end. The current two-inch tongue cannot provide that distance.',
  'action':'Resolve species, peg diameter, receiving-face edge distances and joint arrangement together; do not simply drill the existing tongues. This comparison does not assign a capacity or prohibit every alternative tested detail.'},
 {'id':'S4','priority':'high','title':'Outer seats carry gravity but do not lock against uplift','parts':'R/P heels and J/B seats',
  'finding':'R0 bears across the 8 × 8 post head (64 in² nominal horizontal footprint). Each short rafter has approximately 12 in² of horizontal bearing on its ring beam. These are real support surfaces, not merely the colored cavity edge seen in the screenshot. No rated uplift or sliding restraint is modeled.',
  'action':'Keep broad gravity bearing; check heel/block shear, remaining rafter section and the signed force direction. Retain or adjust the seat only after those checks. Add a designed restraint for force reversal; a deeper notch alone is not a solution.'},
 {'id':'S5','priority':'high','title':'Braces, eave-ring joints and post bases need a complete lateral system','parts':'K/B/P families and foundations',
  'finding':'Braces use full-section diagonal sockets without a complete peg/housing design. Eave-ring joints share post heads with other cuts. No foundation anchorage is modeled. Enclosed walls are confirmed, but their sheathing and attachments are not.',
  'action':'Trace wall/roof shear through collectors, braces or shear panels, post joints and foundations. Check both wind directions, load reversal, combined notches and erection stability.'},
 {'id':'S6','priority':'high','title':'Cupola ceiling and roof require attachments','parts':'CC/CR/PLY families and upper rings',
  'finding':'The horizontal half-inch plywood and eight exposed horizontal ceiling spokes now follow the user-confirmed arrangement. Ceiling spoke 4 × 6 sizes and roof-rafter 2 × 6 depths are assumptions. Center miters touch but do not themselves resist separation. Finish boards are not assigned an invented thickness.',
  'action':'Design center and perimeter connections plus plywood grade, panel joints, edge blocking and fastening. Do not credit the plywood as a diaphragm until its complete boundary load path is specified.'},
 {'id':'S7','priority':'review','title':'Earlier prototype is not verified stronger','parts':'Historical keyed version',
  'finding':'The earlier model used algorithmic keys and larger-looking interlocks. Its own engineering review recorded severely reduced webs and unresolved raising/tool access. Those shapes were not a verified traditional joinery schedule.',
  'action':'Retain useful viewing features and compare real housings/shoulders, but do not restore arbitrary keys as a structural fix.'},
# TIMESTAMP START 2026-11-02T09:09:36-05:00 | REVISION R004753
 {'id':'S8','priority':'review','title':'Nominal cavity fit passes independent checks','parts':'All modeled recesses and mating timber solids',
  'finding':'The actual removed-stock cavities pass independent occupancy and section checks at the recorded numerical tolerances. All timber pair overlaps, registered contacts and connected-solid checks also pass. The former residual meshes were numerical artifacts and are no longer exported or displayed.',
  'action':'Read the hash-bound cavity-fit audit for methods and tolerances. Geometry agreement does not establish connection strength, shrinkage allowance, tool access or a complete raising sequence.'}
# TIMESTAMP END 2026-11-02T09:09:36-05:00 | REVISION R004753
]
# TIMESTAMP START 2026-11-02T08:05:33-05:00 | REVISION R004748
report={'revision':'R02-S2','audit_revision':'R004748','audit_timestamp':'2026-11-02T08:05:33-05:00','model_sha256':hashlib.sha256(raw).hexdigest(),'status':'NOT STRUCTURALLY QUALIFIED — CENTER CONNECTION DESIGN HOLD',
 'confirmed':{'enclosure':'Enclosed, following the Bluetime photos; site-specific wind enclosure classification still to be checked.','plywood':'1/2 inch, horizontal upper ceiling/deck, explicitly confirmed by user.','joinery_preference':'Use documented traditional working joinery wherever possible; keep it simple, with dovetails where appropriate and matching cavities plus a verified assembly path.'},
 'traditional_joinery_review':lower_joint_review,
# TIMESTAMP END 2026-11-02T08:05:33-05:00 | REVISION R004748
 'missing_inputs':['Actual building site and adopted design criteria','Timber species, grade, moisture and actual dimensions','Roof/wall assembly weights and openings','Joint fasteners and foundation/soil design'],
# TIMESTAMP START 2026-11-02T09:09:36-05:00 | REVISION R004753
 'cavity_fit_audit':{'status':cavity_fit['status'],'summary':cavity_fit['summary'],'report':'downloads/cavity-fit-audit.json'},
# TIMESTAMP START 2026-11-02T10:05:34-05:00 | REVISION R004758
 'proposed_cavity_fit_audit':{'status':proposed_cavity_fit['status'],'model_sha256':proposed_cavity_fit['model_sha256'],'summary':proposed_cavity_fit['summary'],'report':'downloads/step-lap-proposed-cavity-fit-audit.json'},
# TIMESTAMP END 2026-11-02T10:05:34-05:00 | REVISION R004758
# TIMESTAMP END 2026-11-02T09:09:36-05:00 | REVISION R004753
 'section_screen':sections,'findings':findings,
 'load_coefficients':{'main_roof_plan_area_ft2':main,'cupola_roof_plan_area_ft2':cap,'symmetric_main_bay_plan_area_ft2':main/8,'symmetric_cupola_bay_plan_area_ft2':cap/8,'wood_volume_ft3':wood_volume,
 'usage':'For a uniform pressure q in lb/ft² of horizontal projection, total vertical force equals q times plan area. Per-bay values apply only to a symmetric load accounting case, not individual joint reactions. Actual wind/snow are not assumed uniform or divided equally. Timber weight equals volume times confirmed density. No load magnitudes or capacities have been assigned.'},
 'sources':[{'title':'TFEC 1-2019 Standard and Commentary','url':'https://www.tfguild.org/timber-frame-engineering-council/standards/view/104/download','use':'Sections 2.3, 3.1, 3.3, 3.4, 3.6 and 4; proportion screen only.'},
 {'title':'FEMA wind retrofit guide','url':'https://www.fema.gov/sites/default/files/documents/fema_rsl_fema-p-804-wind-retrofit-guide_042025.pdf','use':'Continuous roof-to-foundation load path and force reversal.'},
 # TIMESTAMP START 2026-11-02T08:05:33-05:00 | REVISION R004748
 {'title':'Vermont Timber Works F-6 joint sheet, detail 7','url':'https://www.vermonttimberworks.com/wp-content/uploads/2013/08/sample-shop-drawings-hostetter-habib-residence-joints.pdf','use':'The kingpost/bottom-chord detail labels a double tenon, with pegs; it does not show a double dovetail. The post continues below the chord. This is a different structure, not an approved replacement schedule.'},
 {'title':'TFEC Bulletin 2018-13: Wedged Dovetail Tenon Joints','url':'https://www.tfguild.org/timber-frame-engineering-council/technical-bulletins/view/123/download','use':'Pages 2–5 and 9: through wedged half-dovetail family, full matching bearing, cheek proportions and full-depth head recommendation. Required shear housings are outside its scope. Its 8×10 beam/10×10 post example does not qualify this 6×6 cupola post.'},
 {'title':'Timber Frame HQ: horizontal tie-to-post wedged half-dovetail','url':'https://timberframehq.com/wedged-half-dovetail-tie-beam-tenon-to-post-detail/','use':'Exploded horizontal tie-to-post example with diminished housing and separate hardwood wedge; a documented family, not evidence for this building’s hidden joints.'},
 {'title':'Timber Frame HQ: kingpost-to-tie wedged tenon','url':'https://timberframehq.com/king-post-to-tie-wedged-tenon/','use':'Documented Windham Congregational Church example: vertical through half-dovetail, two pegs and top-inserted hardwood wedge. Different orientation and member arrangement from a radial tie ending at a cupola post.'},
 {'title':'Timber Frame HQ: upper kingpost joinery','url':'https://timberframehq.com/upper-king-post-joinery-detail/','use':'Rafter-to-kingpost precedent uses a diminished housing and tenon. It supports evaluating housed bearing and retention instead of requiring a flare at every connection; its oak dimensions are not adopted.'},
 # TIMESTAMP END 2026-11-02T08:05:33-05:00 | REVISION R004748
 {'title':'Bluetime architectural reference','url':'https://www.bluetimecollaborative.com/robert-swinburne-vermont-architect/octagon-timber-frame-outbuilding','use':'Building form and user-confirmed enclosed arrangement.'}]}
(ROOT/'docs/structural-audit.json').write_text(json.dumps(report,indent=2)+'\n')
from html import escape as E
rows=''.join(f'<tr><th>{r["part"]}</th><td>{r["gross_area_in2"]:.2f}</td><td>{r["minimum_sampled_body_area_in2"]:.2f}</td><td>{r["remaining_area_percent"]:.1f}%</td></tr>' for r in sections)
cards=''.join(f'<article><p class="tag">{E(f["priority"].upper())} · {E(f["parts"])}</p><h2>{E(f["title"])}</h2><p>{E(f["finding"])}</p><p><strong>Design response:</strong> {E(f["action"])}</p></article>' for f in findings)
links=''.join(f'<li><a href="{s["url"]}">{E(s["title"])}</a> — {E(s["use"])}</li>' for s in report['sources'])
# TIMESTAMP START 2026-11-02T09:09:36-05:00 | REVISION R004753
# TIMESTAMP START 2026-11-02T08:05:33-05:00 | REVISION R004748
page='''<!doctype html><!-- TIMESTAMP START 2026-11-02T08:05:33-05:00 | REVISION R004748 --><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Joint strength and load-path audit</title>
<!-- TIMESTAMP START 2026-11-01T23:19:38-05:00 | REVISION R004668 -->
<style>/* TIMESTAMP START 2026-11-01T23:19:38-05:00 | REVISION R004668 */
*{box-sizing:border-box}body{margin:0;background:#f8f8f3;color:#263d40;font:17px/1.65 system-ui,sans-serif}main{max-width:1060px;margin:auto;padding:36px 24px}a{color:#176a7d}h1{font-size:clamp(2rem,5vw,3.4rem);line-height:1.12}h2{line-height:1.3}.lead{font-size:1.2rem}article{padding:24px;background:white;border:1px solid #d2dcd6;margin:20px 0;border-radius:12px}.tag{font-size:.8rem;letter-spacing:.05em;color:#80591d}.note{padding:20px;background:#f0e7ce;border-left:5px solid #a37d37}table{border-collapse:collapse;width:100%}th,td{text-align:left;padding:12px;border-bottom:1px solid #ccd6d0}.table{overflow:auto}svg{width:100%;height:auto;max-width:820px}svg text{font-family:system-ui,sans-serif;fill:#263d40}footer{margin:40px 0;font-size:.9rem}
/* TIMESTAMP END 2026-11-01T23:19:38-05:00 | REVISION R004668 */</style></head><body><main><nav><a href="index.html">← 3D frame</a> · <a href="downloads/structural-audit.json">Measured audit data</a></nav>
<p class="tag">R02-S2 · TRADITIONAL JOINERY REVIEW</p><h1>Traditional joint families.<br>Center connections still need design.</h1><p class="lead">The lower cupola connections are on design hold. No new dovetail is published in this model. The existing straight tongues remain an unresolved geometric proposal, with no fabrication or hurricane-resistance approval.</p>
<h2>What the references establish</h2><p>The design preference is simple, documented traditional working joinery wherever possible. A <a href="https://timberframehq.com/wedged-half-dovetail-tie-beam-tenon-to-post-detail/">through wedged half-dovetail</a> is a documented horizontal tie-to-post family, with a separate hardwood wedge and a diminished bearing housing. It is a candidate for review here; it has not been sized or adopted.</p>
<p>The <a href="https://www.tfguild.org/timber-frame-engineering-council/technical-bulletins/view/123/download">TFEC design guide</a> requires matching bearing interfaces and adequate mortise cheeks. Its full-depth head recommendation exposes a problem in the present layout: the 10-inch tie underside and cupola post bottom are flush, so such a head would leave no timber below it. Shrinking the head or reversing the flare to fit would require a new design check. The guide also leaves shear-bearing shoulder and housing design outside its scope.</p>
<p>A <a href="https://timberframehq.com/king-post-to-tie-wedged-tenon/">suspended kingpost through a continuous tie</a> is a different arrangement: the vertical post tenon is retained with pegs and a wedge. These cupola uprights receive horizontal radial tie ends and carry the cupola assembly. Their appearance of floating does not establish the direction or magnitude of the joint forces.</p>
<p>The <a href="https://www.vermonttimberworks.com/wp-content/uploads/2013/08/sample-shop-drawings-hostetter-habib-residence-joints.pdf">Vermont Timber Works F-6 sheet, detail 7</a> labels a <strong>double tenon</strong>, not a double dovetail. Its post extends below the bottom chord. For the upper connection, a <a href="https://timberframehq.com/upper-king-post-joinery-detail/">housed rafter-to-post tenon</a> provides a traditional family to evaluate. None of these references establishes the concealed joints in the original Bluetime building.</p>
<p class="note">Release condition: resolve the cupola, ring and tie forces; provide adequate bearing, remaining timber and withdrawal restraint; then verify matching cavities and an accessible assembly sequence. Existing viewing and cavity tools remain available while that connection design is unresolved.</p>
<!-- TIMESTAMP START 2026-11-02T09:09:36-05:00 | REVISION R004753 -->
<!-- TIMESTAMP START 2026-11-02T10:05:34-05:00 | REVISION R004758 -->
<p>The <a href="downloads/step-lap-proposed-cavity-fit-audit.json">proposed step-lap model</a> and <a href="downloads/cavity-fit-audit.json">saved baseline model</a> each have a separate passing cavity-fit audit bound to their own geometry. Both checks account for every original timber stock envelope and require the actual mating wood to occupy each recess. The section proportions and traditional-joint discussion below refer to the saved baseline; see the proposed joint comparison for its changed perimeter cuts.</p>
<!-- TIMESTAMP END 2026-11-02T10:05:34-05:00 | REVISION R004758 -->
<h2>Nominal cavity fit</h2><p>The <a href="downloads/cavity-fit-audit.json">independent cavity-fit audit</a> checks the actual removed wood against the mating solids. The false pointed lower-cupola overlays are corrected. Invalid residual meshes have been retired; the reported gap checks use separate occupancy and section methods. All results refer to the exact model and cavity hashes in the report and their stated numerical tolerances.</p>
<!-- TIMESTAMP END 2026-11-02T09:09:36-05:00 | REVISION R004753 -->
<h2>Gravity and wind must be followed through every joint</h2><p>Roof covering/deck → short rafters and hips → perimeter bearing and central cupola assembly → ring/tie system and posts → anchors → foundations. The cupola ceiling has a separate path through its spokes and upper frame. Lateral loads need the enclosed walls or a designed bracing/diaphragm system. The central opening must remain clear while the surrounding system transfers both compression and tension.</p>
'''
# TIMESTAMP END 2026-11-02T08:05:33-05:00 | REVISION R004748
# TIMESTAMP END 2026-11-02T09:09:36-05:00 | REVISION R004753
page+=f'<p>Main-roof horizontal projected area: <strong>{main:.2f} ft²</strong>; cupola-roof area: <strong>{cap:.2f} ft²</strong>. Each uniform 1 psf of vertical load therefore contributes {main+cap:.2f} lb in total. A symmetric bookkeeping share is {main/8:.2f} + {cap/8:.2f} ft² per radial bay. These are load coefficients, not joint reactions; asymmetric snow and local wind suction require separate cases.</p>'
page+='<h2>Measured remaining sections</h2><p>Representative bay-zero members, sampled where the original stock has its full rectangular section. These are geometric cross-sectional areas; their percentages are <strong>not strength percentages</strong>. Bending, shear, grain, notch stress concentration and bearing must be calculated separately.</p><div class="table"><table><tr><th>Member</th><th>Gross in²</th><th>Minimum sampled net in²</th><th>Area retained</th></tr>'+rows+'</table></div>'+cards
page+='<h2>Inputs still needed</h2><p>The building is confirmed enclosed. Actual location, species/grade/moisture, assembly weights, openings and foundation details remain unresolved. A timber-frame structural engineer needs those inputs to size the final joints and verify gravity, uplift, lateral and erection cases.</p><h2>Standards and construction examples</h2><ul>'+links+'</ul><footer>Model SHA-256: '+report['model_sha256']+'<br>Generated from the same current solids as the viewer. No structural approval or safe load is issued.</footer></main></body></html><!-- TIMESTAMP END 2026-11-01T23:19:38-05:00 | REVISION R004668 -->'
# TIMESTAMP START 2026-11-02T08:05:33-05:00 | REVISION R004748
page+='<!-- TIMESTAMP END 2026-11-02T08:05:33-05:00 | REVISION R004748 -->'
# TIMESTAMP END 2026-11-02T08:05:33-05:00 | REVISION R004748
(ROOT/'public/structural-audit.html').write_text(page)
print(json.dumps({'status':report['status'],'sections':sections,'main_plan_ft2':main,'cupola_plan_ft2':cap}))
# TIMESTAMP END 2026-11-01T23:19:38-05:00 | REVISION R004668
