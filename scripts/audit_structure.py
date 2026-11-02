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
findings=[
 {'id':'S1','priority':'critical','title':'Center has no designed tension and uplift restraint','parts':'T0–T7 / R0–R7 / C0–C7 / cupola rings',
  'finding':'The straight two-inch tongues have no pegs, bolts, retained dovetail or other positive withdrawal restraint. Nominal contact does not close the central force path.',
  'action':'Design the open-center drum/ring and its joints as one system. Evaluate a plain housed dovetail where radial withdrawal governs, with separate restraint against its insertion/removal direction. Do not assume an open-bottom polygon or plywood alone supplies the required ring action.'},
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
 {'id':'S8','priority':'review','title':'Geometric audit has a defined limit','parts':'All sockets',
  'finding':'Positive-volume pair overlaps, registered contact and connected meshes pass. The separate unfilled-socket volume diagnostics are nonzero and numerically inconsistent under rotation; complete cavity closure is not certified.',
  'action':'Resolve socket-volume closure independently before any fabrication claim. The contact-area proxy in the fit report is a geometry diagnostic, not a structural bearing-capacity calculation.'}
]
report={'revision':'R02-S1','model_sha256':hashlib.sha256(raw).hexdigest(),'status':'NOT STRUCTURALLY QUALIFIED',
 'confirmed':{'enclosure':'Enclosed, following the Bluetime photos; site-specific wind enclosure classification still to be checked.','plywood':'1/2 inch, horizontal upper ceiling/deck, explicitly confirmed by user.','joinery_preference':'Simple integral flared dovetails where relevant; no driven wedges requested.'},
 'missing_inputs':['Actual building site and adopted design criteria','Timber species, grade, moisture and actual dimensions','Roof/wall assembly weights and openings','Joint fasteners and foundation/soil design'],
 'section_screen':sections,'findings':findings,
 'load_coefficients':{'main_roof_plan_area_ft2':main,'cupola_roof_plan_area_ft2':cap,'symmetric_main_bay_plan_area_ft2':main/8,'symmetric_cupola_bay_plan_area_ft2':cap/8,'wood_volume_ft3':wood_volume,
 'usage':'For a uniform pressure q in lb/ft² of horizontal projection, total vertical force equals q times plan area. Per-bay values apply only to a symmetric load accounting case, not individual joint reactions. Actual wind/snow are not assumed uniform or divided equally. Timber weight equals volume times confirmed density. No load magnitudes or capacities have been assigned.'},
 'sources':[{'title':'TFEC 1-2019 Standard and Commentary','url':'https://www.tfguild.org/timber-frame-engineering-council/standards/view/104/download','use':'Sections 2.3, 3.1, 3.3, 3.4, 3.6 and 4; proportion screen only.'},
 {'title':'FEMA wind retrofit guide','url':'https://www.fema.gov/sites/default/files/documents/fema_rsl_fema-p-804-wind-retrofit-guide_042025.pdf','use':'Continuous roof-to-foundation load path and force reversal.'},
 {'title':'Vermont Timber Works F-6 joint sheet','url':'https://www.vermonttimberworks.com/wp-content/uploads/2013/08/sample-shop-drawings-hostetter-habib-residence-joints.pdf','use':'Professional housing, tenon and mechanical restraint examples from a different structure; dimensions not transplanted.'},
 {'title':'Bluetime architectural reference','url':'https://www.bluetimecollaborative.com/robert-swinburne-vermont-architect/octagon-timber-frame-outbuilding','use':'Building form and user-confirmed enclosed arrangement.'}]}
(ROOT/'docs/structural-audit.json').write_text(json.dumps(report,indent=2)+'\n')
from html import escape as E
rows=''.join(f'<tr><th>{r["part"]}</th><td>{r["gross_area_in2"]:.2f}</td><td>{r["minimum_sampled_body_area_in2"]:.2f}</td><td>{r["remaining_area_percent"]:.1f}%</td></tr>' for r in sections)
cards=''.join(f'<article><p class="tag">{E(f["priority"].upper())} · {E(f["parts"])}</p><h2>{E(f["title"])}</h2><p>{E(f["finding"])}</p><p><strong>Design response:</strong> {E(f["action"])}</p></article>' for f in findings)
links=''.join(f'<li><a href="{s["url"]}">{E(s["title"])}</a> — {E(s["use"])}</li>' for s in report['sources'])
page='''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Joint strength and load-path audit</title>
<!-- TIMESTAMP START 2026-11-01T23:19:38-05:00 | REVISION R004668 -->
<style>/* TIMESTAMP START 2026-11-01T23:19:38-05:00 | REVISION R004668 */
*{box-sizing:border-box}body{margin:0;background:#f8f8f3;color:#263d40;font:17px/1.65 system-ui,sans-serif}main{max-width:1060px;margin:auto;padding:36px 24px}a{color:#176a7d}h1{font-size:clamp(2rem,5vw,3.4rem);line-height:1.12}h2{line-height:1.3}.lead{font-size:1.2rem}article{padding:24px;background:white;border:1px solid #d2dcd6;margin:20px 0;border-radius:12px}.tag{font-size:.8rem;letter-spacing:.05em;color:#80591d}.note{padding:20px;background:#f0e7ce;border-left:5px solid #a37d37}table{border-collapse:collapse;width:100%}th,td{text-align:left;padding:12px;border-bottom:1px solid #ccd6d0}.table{overflow:auto}svg{width:100%;height:auto;max-width:820px}svg text{font-family:system-ui,sans-serif;fill:#263d40}footer{margin:40px 0;font-size:.9rem}
/* TIMESTAMP END 2026-11-01T23:19:38-05:00 | REVISION R004668 */</style></head><body><main><nav><a href="index.html">← 3D frame</a> · <a href="downloads/structural-audit.json">Measured audit data</a></nav>
<p class="tag">R02-S1 · MODEL AUDIT</p><h1>Fit is checked.<br>Strength needs a complete connection design.</h1><p class="lead">The current joints are not yet suitable as a fabrication or hurricane-resistance specification. The central withdrawal restraint, receiver proportions and continuous load path need redesign.</p>
<h2>A simple dovetail is a candidate—not a universal upgrade</h2><p>An integral flare can resist withdrawal along the member. The receiving cheeks must resist the spreading force, and the neck must carry tension. An open-entry dovetail can still move back out along its assembly direction. The diagram below describes that distinction; it supplies no cut dimensions.</p>
<svg viewBox="0 0 820 285" role="img" aria-label="Schematic dovetail plan: wider integral head bears against matching cheeks; assembly direction perpendicular to this view still needs restraint"><rect x="315" y="30" width="440" height="200" rx="4" fill="#d7bd8f" stroke="#6f5737" stroke-width="2"/><path d="M45 100H340L475 65V195L340 160H45Z" fill="#6ba8ad" stroke="#284e54" stroke-width="3"/><path d="M280 130H100m0 0l18 -12m-18 12l18 12" fill="none" stroke="#284e54" stroke-width="4"/><text x="50" y="80" font-size="18">Withdrawal</text><text x="515" y="92" font-size="18">Matching bearing faces</text><text x="515" y="125" font-size="18">Adequate cheeks and relish</text><text x="515" y="158" font-size="18">Check splitting and block shear</text><text x="50" y="264" font-size="17">Plan schematic only · insertion/removal is out of this view and needs its own restraint</text></svg>
<p class="note">Design direction: broad housed bearing for gravity; a plain dovetail only where its direction and assembly make sense; engineered pegs or concealed restraint where load reversal requires it. No ornamental carving and no driven wedge are proposed. A locked geometry still requires a capacity calculation.</p>
<h2>Gravity and wind must be followed through every joint</h2><p>Roof covering/deck → short rafters and hips → perimeter bearing and central cupola assembly → ring/tie system and posts → anchors → foundations. The cupola ceiling has a separate path through its spokes and upper frame. Lateral loads need the enclosed walls or a designed bracing/diaphragm system. The central opening must remain clear while the surrounding system transfers both compression and tension.</p>
'''
page+=f'<p>Main-roof horizontal projected area: <strong>{main:.2f} ft²</strong>; cupola-roof area: <strong>{cap:.2f} ft²</strong>. Each uniform 1 psf of vertical load therefore contributes {main+cap:.2f} lb in total. A symmetric bookkeeping share is {main/8:.2f} + {cap/8:.2f} ft² per radial bay. These are load coefficients, not joint reactions; asymmetric snow and local wind suction require separate cases.</p>'
page+='<h2>Measured remaining sections</h2><p>Representative bay-zero members, sampled where the original stock has its full rectangular section. These are geometric cross-sectional areas; their percentages are <strong>not strength percentages</strong>. Bending, shear, grain, notch stress concentration and bearing must be calculated separately.</p><div class="table"><table><tr><th>Member</th><th>Gross in²</th><th>Minimum sampled net in²</th><th>Area retained</th></tr>'+rows+'</table></div>'+cards
page+='<h2>Inputs still needed</h2><p>The building is confirmed enclosed. Actual location, species/grade/moisture, assembly weights, openings and foundation details remain unresolved. A timber-frame structural engineer needs those inputs to size the final joints and verify gravity, uplift, lateral and erection cases.</p><h2>Standards and construction examples</h2><ul>'+links+'</ul><footer>Model SHA-256: '+report['model_sha256']+'<br>Generated from the same current solids as the viewer. No structural approval or safe load is issued.</footer></main></body></html><!-- TIMESTAMP END 2026-11-01T23:19:38-05:00 | REVISION R004668 -->'
(ROOT/'public/structural-audit.html').write_text(page)
print(json.dumps({'status':report['status'],'sections':sections,'main_plan_ft2':main,'cupola_plan_ft2':cap}))
# TIMESTAMP END 2026-11-01T23:19:38-05:00 | REVISION R004668
