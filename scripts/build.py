# TIMESTAMP START 2026-11-01T23:19:38-05:00 | REVISION R004668
# TIMESTAMP START 2026-11-01T22:44:38-05:00 | REVISION R004653
#!/usr/bin/env python3
"""Build the R01 viewer and exports from the same current geometry source."""
from pathlib import Path
from html.parser import HTMLParser
import hashlib, json, math, re, runpy, shutil

class ScriptBlocks(HTMLParser):
    """Keep executable JS separate from JSON data blocks, as a browser does."""
    def __init__(self, html):
        super().__init__(convert_charrefs=False)
        self.blocks=[]
        self.current=None
        self.feed(html)
    def handle_starttag(self, tag, attrs):
        if tag=='script':
            self.current={'attrs':dict(attrs), 'body':''}
    def handle_data(self, value):
        if self.current is not None:
            self.current['body']+=value
    def handle_endtag(self, tag):
        if tag=='script' and self.current is not None:
            self.blocks.append(self.current)
            self.current=None

def executable_blocks(html):
    return [b['body'] for b in ScriptBlocks(html).blocks
            if b['attrs'].get('type','').lower() in ('','text/javascript','application/javascript')]

ROOT = Path(__file__).resolve().parents[1]
model_path = ROOT / 'src/model-data.json'
data = json.loads(model_path.read_text())
ids = [p['id'] for p in data['parts']]
assert len(ids) == len(set(ids)), 'Duplicate component identifiers'
assert not any(f'J{k}-1' in ids for k in range(8)), 'Retired midpoint rafter still present'
model_sha = hashlib.sha256(model_path.read_bytes()).hexdigest()
materials = json.loads((ROOT/'src/material-groups.json').read_text())
assert materials['source_sha256'] == model_sha, 'Inventory must match current geometry'
grouped = [pid for g in materials['groups'] for pid in g['member_ids']]
assert len(grouped) == len(set(grouped)) and set(grouped) == set(ids)

template = (ROOT/'src/viewer.template.html').read_text()
for code_marker in ['/*__STEP_LAP_REVIEW__*/','/*__MODEL_VARIANTS__*/']:
    assert sum(code_marker in b for b in executable_blocks(template))==1, code_marker+' must be in executable JavaScript, not a JSON data block'
def encode(value):
    return json.dumps(value, separators=(',', ':'), ensure_ascii=True).replace('</', '<\\/')
inspection = (ROOT/'src/inspection-tools.js').read_text().replace('__MATERIALS_JSON__', 'MODEL_CONTEXT.materials')
# TIMESTAMP START 2026-11-01T22:44:38-05:00 | REVISION R004653
cavities = json.loads((ROOT/'src/cavity-data.json').read_text())
assert cavities['source_model_sha256'] == model_sha
# TIMESTAMP START 2026-11-02T09:09:36-05:00 | REVISION R004753
cavity_audit=json.loads((ROOT/'docs/cavity-fit-audit.json').read_text())
assert cavity_audit['status']=='PASS', 'Cavity fit audit must pass before publishing'
assert cavity_audit['model_sha256']==model_sha, 'Cavity audit model is stale'
assert cavity_audit['cavity_sha256']==hashlib.sha256((ROOT/'src/cavity-data.json').read_bytes()).hexdigest(), 'Cavity audit geometry is stale'
cavities['fit_audit']={k:cavity_audit[k] for k in ['status','summary']}
# TIMESTAMP START 2026-11-02T10:05:34-05:00 | REVISION R004758
cavities['available']=True
# TIMESTAMP END 2026-11-02T10:05:34-05:00 | REVISION R004758
# TIMESTAMP END 2026-11-02T09:09:36-05:00 | REVISION R004753
# TIMESTAMP END 2026-11-01T22:44:38-05:00 | REVISION R004653

load_data=json.loads((ROOT/'src/load-review-data.json').read_text())
assert load_data['source_model_sha256']==model_sha, 'Load review must match current geometry'
load_review=(ROOT/'src/load-review.js').read_text().replace('__LOAD_REVIEW_JSON__','MODEL_CONTEXT.loadReview')
# Never offer the baseline area shortcuts on altered contact geometry.
load_review=load_review.replace('function updateHypotheticalPressure(){', "function updateHypotheticalPressure(){if(!MODEL_CONTEXT.pressureAvailable){$('hypotheticalPressure').textContent='Unavailable for proposed joints: baseline 64/12 in² pressure shortcuts are disabled. Reactions and capacities remain unsolved.';return;}")
overlays = (ROOT/'src/geometry-overlays.js').read_text().replace('__CAVITY_JSON__', 'MODEL_CONTEXT.cavities').replace('let showHollows=true', 'let showHollows=MODEL_CONTEXT.cavities.available!==false')
step_lap=json.loads((ROOT/'src/step-lap-proposal.json').read_text())
assert step_lap['baseline_model_sha256']==model_sha, 'Proposed step-lap comparison must match its unchanged baseline'
assert step_lap['canonical_model_unchanged'] is True
proposed_model=json.loads((ROOT/'src/step-lap-proposed-model.json').read_text())
assert proposed_model['proposed_review']['baseline_model_sha256']==model_sha, 'Proposed model export is stale'
assert 'NOT FABRICATION' in proposed_model['status'], 'Proposed export must retain its explicit status'
expected_changes=set(step_lap['combined_geometry_audit']['changed_member_ids'])
assert set(proposed_model['proposed_review']['changed_member_ids'])==expected_changes
baseline_by_id={p['id']:p for p in data['parts']}
assert [p['id'] for p in proposed_model['parts']]==ids, 'Proposed export must preserve inventory and ordering'
actual_changes={p['id'] for p in proposed_model['parts'] if p!=baseline_by_id[p['id']]}
assert actual_changes==expected_changes, 'Proposed export changed members do not match its reviewed scope'
proposed_sha=hashlib.sha256((ROOT/'src/step-lap-proposed-model.json').read_bytes()).hexdigest()
proposed_load=json.loads((ROOT/'src/step-lap-proposed-load-review.json').read_text())
proposed_cavities=json.loads((ROOT/'src/step-lap-proposed-cavities.json').read_text())
proposed_materials=json.loads((ROOT/'src/step-lap-proposed-material-groups.json').read_text())
assert proposed_load['source_model_sha256']==proposed_sha, 'Proposed self-weight data is stale'
assert proposed_cavities['source_model_sha256']==proposed_sha, 'Proposed cavity data is stale'
# TIMESTAMP START 2026-11-02T10:05:34-05:00 | REVISION R004758
proposed_cavity_audit=json.loads((ROOT/'docs/step-lap-proposed-cavity-fit-audit.json').read_text())
assert proposed_cavity_audit['status']=='PASS', 'Proposed cavity fit audit must pass before publishing'
assert proposed_cavity_audit['model_sha256']==proposed_sha, 'Proposed cavity audit model is stale'
assert proposed_cavity_audit['cavity_sha256']==hashlib.sha256((ROOT/'src/step-lap-proposed-cavities.json').read_bytes()).hexdigest(), 'Proposed cavity audit geometry is stale'
proposed_cavities['fit_audit']={k:proposed_cavity_audit[k] for k in ['status','summary']}
proposed_cavities['available']=True
# TIMESTAMP END 2026-11-02T10:05:34-05:00 | REVISION R004758
assert proposed_materials['source_sha256']==proposed_sha, 'Proposed inventory is stale'
assert proposed_load['issues']==[] and proposed_load['baseline_pressure_disabled'] is True, 'Baseline markers/area shortcuts must not be reused for proposed joints'
assert sorted(m['id'] for m in proposed_load['members'])==sorted(m['id'] for m in load_data['members'])
assert len(proposed_load['members'])==104 and all(math.isfinite(m['volume_m3']) and m['volume_m3']>0 and len(m['centroid_m'])==3 and all(math.isfinite(x) for x in m['centroid_m']) for m in proposed_load['members'])
assert sorted(pid for g in proposed_materials['groups'] for pid in g['member_ids'])==sorted(ids)
enclosure_fit=json.loads((ROOT/'src/enclosure-fit.json').read_text())
proposed_enclosure_fit=json.loads((ROOT/'src/step-lap-proposed-enclosure-fit.json').read_text())
module_sha=hashlib.sha256((ROOT/'src/schematic-walls.js').read_bytes()).hexdigest()
assert enclosure_fit['source_model_sha256']==model_sha
assert proposed_enclosure_fit['source_model_sha256']==proposed_sha
assert enclosure_fit['source_module_sha256']==proposed_enclosure_fit['source_module_sha256']==module_sha
foundation_data=json.loads((ROOT/'src/floor-foundation-solids.json').read_text())
assert foundation_data['source_model_sha256']==model_sha
assert foundation_data['source_module_sha256']==hashlib.sha256((ROOT/'src/floor-foundation.js').read_bytes()).hexdigest()
# Foundation layout is valid for either selected model only when actual post centers match.
for selected_model in [data,proposed_model]:
 assert [next(p for p in selected_model['parts'] if p['id']=='P'+str(k))['center'][::2] for k in range(8)]==[[p[0],p[2]] for p in foundation_data['layout']['sourcePostCenters']]
model_variants={'baseline':{'sha256':model_sha,'loadReview':load_data,'cavities':cavities,'materials':materials,'enclosureFit':enclosure_fit},
                'proposed':{'model':proposed_model,'sha256':proposed_sha,'loadReview':proposed_load,
                            'cavities':proposed_cavities,'materials':proposed_materials,'enclosureFit':proposed_enclosure_fit}}


# A distinct selected revision: never mix top-entry meshes with perimeter-only metadata.
top_path=ROOT/'src/top-entry-proposed-model.json'
top_model=json.loads(top_path.read_text())
top_sha=hashlib.sha256(top_path.read_bytes()).hexdigest()
top_aux={key:json.loads((ROOT/('src/top-entry-proposed-'+suffix+'.json')).read_text()) for key,suffix in [('loadReview','load-review'),('materials','material-groups'),('enclosureFit','enclosure-fit'),('cavities','cavities')]}
for key,value in top_aux.items():
    assert value.get('source_model_sha256',value.get('source_sha256'))==top_sha, 'Top-entry auxiliary hash mismatch: '+key
assert top_aux['enclosureFit']['source_module_sha256']==module_sha
assert len(top_aux['loadReview']['members'])==104
assert [p['id'] for p in top_model['parts']]==ids
model_variants['top-entry']={'model':top_model,'sha256':top_sha,**top_aux}


for marker, value in [('/*__ROOF_COVERINGS__*/',(ROOT/'src/roof-coverings.js').read_text()), ('/*__DISPLAY_PRESETS__*/',(ROOT/'src/display-presets.js').read_text()), ('/*__FLOOR_FOUNDATION__*/','const FLOOR_FOUNDATION_DATA='+encode(foundation_data)+';\n'+(ROOT/'src/floor-foundation.js').read_text()),('/*__CUT_FACE_ANALYSIS__*/', (ROOT/'src/cut-face-analysis.js').read_text()), ('/*__CUT_ANGLE_VIEW__*/', (ROOT/'src/cut-angle-view.js').read_text()), ('/*__MODEL_VARIANTS__*/', (ROOT/'src/model-variants.js').read_text()), ('__MODEL_VARIANTS_JSON__',encode(model_variants)), ('/*__STEP_LAP_REVIEW__*/', (ROOT/'src/step-lap-review.js').read_text()), ('__STEP_LAP_PROPOSAL_JSON__',encode(step_lap)), ('/*__SCHEMATIC_WALLS__*/', 'const OCTAGON_ENCLOSURE_FIT=MODEL_CONTEXT.enclosureFit;\n'+(ROOT/'src/schematic-walls.js').read_text()), ('/*__INSPECTION_TOOLS__*/', inspection),
                      ('/*__ARCHITECTURAL_PLANS__*/', (ROOT/'src/architectural-plans.js').read_text()),
                      ('/*__EDGE_MEASUREMENT_TOOLS__*/', (ROOT/'src/edge-measurements.js').read_text()),
                      ('/*__LOAD_REVIEW__*/', load_review), ('/*__GEOMETRY_OVERLAYS__*/', overlays), ('__PARTS_JSON__', encode(data))]:
    assert template.count(marker) == 1, marker
    template = template.replace(marker, value)
assert not re.search(r'__(?:PARTS|MATERIALS|CAVITY|STEP_LAP_PROPOSAL)_JSON__', template)
for block in ScriptBlocks(template).blocks:
    if block['attrs'].get('type','').lower()=='application/json':
        json.loads(block['body'])  # Every embedded data script must remain valid JSON.
scripts=executable_blocks(template)
assert sum('const stepLapReview=OctagonStepLap.createController' in b for b in scripts)==1

dist = ROOT/'dist'
dist.mkdir(exist_ok=True)
# Current pages only; historical NAV-05 reports remain available through Git history.
for name in ['about.html', 'r01.html', 'joinery.html', 'structural-audit.html', 'JOINT-DESIGN-BRIEF.md',
             'downloads/index.html', 'review/index.html', 'robots.txt']:
    source = ROOT/'public'/name
    if source.exists():
        target = dist/name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
(dist/'index.html').write_text(template)
(ROOT/'index.html').write_text(template)
downloads = dist/'downloads'
downloads.mkdir(exist_ok=True)
shutil.copyfile(model_path, downloads/'Octagon-R01-model.json')
shutil.copyfile(ROOT/'src/step-lap-proposed-model.json',downloads/'Octagon-PROPOSED-step-lap-model.json')
# TIMESTAMP START 2026-11-02T10:05:34-05:00 | REVISION R004758
audit_downloads=['r01-change-register.json','r01-verification.json','joinery-verification.json','structural-audit.json','cavity-fit-audit.json','step-lap-proposed-cavity-fit-audit.json']
# TIMESTAMP END 2026-11-02T10:05:34-05:00 | REVISION R004758
for source_name in audit_downloads:
    source = ROOT/'docs'/source_name
    if source.exists():
        shutil.copyfile(source, downloads/source_name)
glb_exports=runpy.run_path(str(ROOT/'scripts/export_r01_glb.py'), run_name='__main__')
for exploded in [False,True]:
    (downloads/('Octagon-PROPOSED-step-lap-'+('exploded' if exploded else 'assembled')+'.glb')).write_bytes(
        glb_exports['export'](proposed_model,exploded,{'revision':'Proposed step-lap joinery','status':proposed_model['status'],'source_model_sha256':proposed_sha}))
shutil.copyfile(top_path,downloads/'Octagon-TOP-ENTRY-model.json')
for exploded in [False,True]:
    (downloads/('Octagon-TOP-ENTRY-'+('exploded' if exploded else 'assembled')+'.glb')).write_bytes(glb_exports['export'](top_model,exploded,{'revision':'Top-entry head proposal','status':top_model['status'],'source_model_sha256':top_sha}))
tests = ROOT/'tests'
tests.mkdir(exist_ok=True)
(tests/'embedded-model.json').write_text(encode(data))
(tests/'viewer-script-check.js').write_text('\n'.join(scripts))
print(json.dumps({'revision':'R01', 'components':len(ids), 'html_bytes':len(template.encode()),
                  'model_sha256':model_sha, 'output':'dist/index.html', 'network_dependencies':False}))


# TIMESTAMP END 2026-11-01T22:44:38-05:00 | REVISION R004653

# TIMESTAMP END 2026-11-01T23:19:38-05:00 | REVISION R004668
