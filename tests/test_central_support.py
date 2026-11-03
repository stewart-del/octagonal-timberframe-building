"""Display-only central fixture invariants; no capacity or erection verification."""
from pathlib import Path
import collections,hashlib,json,math,shutil,subprocess,sys,tempfile
import numpy as np
import manifold3d as m
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from central_support import FIXTURE_ID,LEGACY_IDS,make_fixture,consolidate_fixture,migrate
from construction_aids import consolidate_aids
raw=(R/'src/model-data.json').read_bytes();model=json.loads(raw);parts={p['id']:p for p in model['parts']};p=parts[FIXTURE_ID]
proof=json.loads((R/'docs/central-support-baseline.json').read_text())
def sha(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest()
# TIMESTAMP START 2026-11-02T15:15:55-05:00 | REVISION R004802
# TIMESTAMP START 2026-11-02T17:44:11-05:00 | REVISION R004823
assert len(parts)==171 and sum(x['is_timber'] for x in parts.values())==112
# TIMESTAMP END 2026-11-02T17:44:11-05:00 | REVISION R004823
# TIMESTAMP END 2026-11-02T15:15:55-05:00 | REVISION R004802
# TIMESTAMP START 2026-11-02T15:15:55-05:00 | REVISION R004802
brace_scope={f'{f}{k}' for k in range(8) for f in ['P','B','T']}|{f'K{k}-{s}' for k in range(8) for s in ['A','B','C']}
for key,h in proof['unchanged_part_hashes'].items():
 if key not in brace_scope:assert sha(parts[key])==h,key
# TIMESTAMP END 2026-11-02T15:15:55-05:00 | REVISION R004802
assert sha({k:v for k,v in parts['M-SP0'].items() if k!='notes'})==proof['green_aid_hash_without_notes']
assert model['r01']['cupola_outside_diameter_in']==model['source_dimensions']['cupola_outside_diameter_in']==88
# TIMESTAMP START 2026-11-02T15:15:55-05:00 | REVISION R004802
# TIMESTAMP START 2026-11-02T17:44:11-05:00 | REVISION R004823
assert abs(sum(x['fit_geometry']['volume_m3'] for x in parts.values() if x['is_timber'])-6.3404246737588075)<1e-10
# TIMESTAMP END 2026-11-02T17:44:11-05:00 | REVISION R004823
# TIMESTAMP END 2026-11-02T15:15:55-05:00 | REVISION R004802
assert {x['id'] for x in parts.values() if x['group']=='temporary_fixture'}=={FIXTURE_ID}
assert all(model['component_id_history'][old]==FIXTURE_ID and old not in parts for old in LEGACY_IDS)
assert p['assembly_id']=='CENTRAL-SUPPORT' and p['assembly_quantity']==1 and p['temporary'] and not p['is_timber'] and p['material']=='steel'
assert p['exploded_offset']==[0,-1.5,0]
assert next(g for g in model['groups'] if g['id']=='temporary_fixture')['default_visible'] is False
assert model['r01']['metal_count']==model['source_dimensions']['metal_count']==2
assert p['reference_dimensions']=={'overall_span_in':90.0,'strap_depth_in':4.0,'outer_leg_height_in':14.0,'radial_strap_count':8,'holes_per_strap':3,'total_holes':24}
v=np.asarray(p['vertices']);t=np.asarray(p['triangles'],dtype=np.uint64);solid=m.Manifold(m.Mesh64(v,t))
assert str(solid.status())=='Error.NoError' and len(solid.decompose())==1
# TIMESTAMP START 2026-11-03T06:59:29-05:00 | REVISION R004900
a=math.radians(-p['display_assumptions']['rigid_rotation_y_degrees']);c,s=math.cos(a),math.sin(a)
local=v@np.array([[c,0,-s],[0,1,0],[s,0,c]])
assert np.allclose((local.max(0)-local.min(0))/.0254,[90,14,90],atol=1e-9,rtol=0)
# Closed original radial form:24 screw bores, no added central open cells.
# TIMESTAMP END 2026-11-03T06:59:29-05:00 | REVISION R004900
edges=collections.Counter(tuple(sorted((int(tri[j]),int(tri[(j+1)%3])))) for tri in t for j in range(3))
assert all(n==2 for n in edges.values())
# TIMESTAMP START 2026-11-03T06:59:29-05:00 | REVISION R004900
assert len(v)-len(edges)+len(t)==2-2*24
# TIMESTAMP END 2026-11-03T06:59:29-05:00 | REVISION R004900
assert len(p['display_holes'])==24 and len({h['id'] for h in p['display_holes']})==24
assert collections.Counter(h['arm_index'] for h in p['display_holes'])=={k:3 for k in range(8)}
for h in p['display_holes']:
 assert 'NOT DRILLING' in h['status']
 # Every recorded bore center is actually empty, not a painted-on circular mark.
 center=np.asarray(h['center_m']);probe=m.Manifold.cube((.001,.001,.001),center=True).translate(center)
 assert (solid^probe).volume()<1e-14
assert p['fabrication_dimensions_valid'] is False and 'illustrative' in p['geometry_purpose']
assert 'Suppress' in p['plan_dimension_policy']
for name in ['steel_thickness_in','hole_diameter_in','hole_centers_m','top_elevation_m']:assert p['dimension_status'][name]
# TIMESTAMP START 2026-11-03T06:59:29-05:00 | REVISION R004900
assert p['display_assumptions']['steel_thickness_in']==.125
# TIMESTAMP END 2026-11-03T06:59:29-05:00 | REVISION R004900
assert p['display_assumptions']['top_elevation_in']==109
assert not p['reference_end_faces'] and all(x is None for x in p['angles'].values())
assert consolidate_fixture(model['parts'])==model['parts'] and consolidate_aids(model['parts'])==model['parts']
from support_fit import fit_fixture
# TIMESTAMP START 2026-11-03T08:41:52-05:00 | REVISION R004949
def assert_same_fixture(actual,expected,path='fixture'):
 """Keep topology and metadata exact; allow 1 pm numerical regeneration noise."""
 if isinstance(expected,dict):
  assert actual.keys()==expected.keys(),path
  for key in expected:assert_same_fixture(actual[key],expected[key],path+'.'+key)
 elif isinstance(expected,list):
  assert isinstance(actual,list) and len(actual)==len(expected),path
  for i,(a,b) in enumerate(zip(actual,expected)):assert_same_fixture(a,b,f'{path}[{i}]')
 elif isinstance(expected,float):
  assert isinstance(actual,(int,float)) and math.isclose(actual,expected,rel_tol=0,abs_tol=1e-12),(path,actual,expected)
 else:assert actual==expected,(path,actual,expected)
assert_same_fixture(fit_fixture(model)[0],p)
# TIMESTAMP END 2026-11-03T08:41:52-05:00 | REVISION R004949
# Verify scoped migration is byte-idempotent in a sandbox copy, never regenerated timber.
with tempfile.TemporaryDirectory(prefix='octagon-support-test-') as tmp:
 root=Path(tmp);(root/'src').mkdir();(root/'docs').mkdir()
 paths=['src/model-data.json','src/material-groups.json','src/cavity-data.json','src/load-review-data.json','docs/joinery-verification.json']
 for name in paths:shutil.copy2(R/name,root/name)
 migrate(root);first={name:(root/name).read_bytes() for name in paths};migrate(root)
 assert all(first[name]==(root/name).read_bytes() for name in paths)
 for name in paths:assert first[name]==(R/name).read_bytes(),name
# Updated generator is smoke-tested only in a disposable copy: known legacy drift
# means its timber results must never replace the protected production meshes.
with tempfile.TemporaryDirectory(prefix='octagon-support-generator-') as tmp:
 root=Path(tmp);(root/'src').mkdir();(root/'scripts').mkdir()
 for name in ['revise_r01.py','cupola_panel.py','construction_aids.py','central_support.py']:shutil.copy2(R/'scripts'/name,root/'scripts'/name)
 subprocess.run([sys.executable,str(root/'scripts/revise_r01.py')],check=True,stdout=subprocess.PIPE)
 generated=json.loads((root/'src/model-data.json').read_text());gparts={x['id']:x for x in generated['parts']}
 # TIMESTAMP START 2026-11-02T15:15:55-05:00 | REVISION R004802
 assert len(gparts)==115 and gparts[FIXTURE_ID]==make_fixture()
 # TIMESTAMP END 2026-11-02T15:15:55-05:00 | REVISION R004802
 assert generated['r01']['metal_count']==2 and generated['r01']['cupola_outside_diameter_in']==88
 assert all(generated['component_id_history'][x]==FIXTURE_ID for x in LEGACY_IDS)
 materials=json.loads((root/'src/material-groups.json').read_text());g=next(x for x in materials['groups'] if x['family']=='temporary_fixture')
 assert g['quantity']==1 and g['member_ids']==[FIXTURE_ID]
# TIMESTAMP START 2026-11-02T15:15:55-05:00 | REVISION R004802
print('PASS: one connected 8-L support with24 real bores;90in outer span;14in legheight;112 timber records/panel/green geometry unchanged; aliases, display limitations, scoped idempotence and disposable generator checks')
# TIMESTAMP END 2026-11-02T15:15:55-05:00 | REVISION R004802
