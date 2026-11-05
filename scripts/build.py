# TIMESTAMP START 2026-11-04T23:48:03+00:00 | REVISION R000012
# TIMESTAMP START 2026-11-04T23:23:25+00:00 | REVISION R000011
# TIMESTAMP START 2026-11-04T20:33:26+00:00 | REVISION R000023
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
# TIMESTAMP START 2026-11-05T21:31:46+00:00 | REVISION R000067
from restore_large_sources import restore as restore_large_sources
restore_large_sources(ROOT)
# TIMESTAMP END 2026-11-05T21:31:46+00:00 | REVISION R000067
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
# TIMESTAMP START 2026-11-05T16:50:20+00:00 | REVISION R000055
# Retain the old explanatory comparison with its original source hashes.
# Current geometry is bound by a separate fresh actual-member audit.
from validate_primary_auxiliary import validate as validate_primary_auxiliary
current_primary=validate_primary_auxiliary(ROOT)
assert step_lap['canonical_model_unchanged'] is True
proposed_model=current_primary['proposed']['model']
assert 'NOT FABRICATION' in proposed_model['status'], 'Proposed export must retain its explicit status'
baseline_by_id={p['id']:p for p in data['parts']}
assert [p['id'] for p in proposed_model['parts']]==ids, 'Current proposed export must preserve inventory and ordering'
# TIMESTAMP END 2026-11-05T16:50:20+00:00 | REVISION R000055
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
# TIMESTAMP START 2026-11-02T15:07:59-05:00 | REVISION R004800
# TIMESTAMP START 2026-11-05T16:50:20+00:00 | REVISION R000055
assert len(proposed_load['members'])==len(load_data['members'])==129 and all(math.isfinite(m['volume_m3']) and m['volume_m3']>0 and len(m['centroid_m'])==3 and all(math.isfinite(x) for x in m['centroid_m']) for m in proposed_load['members'])
# TIMESTAMP END 2026-11-05T16:50:20+00:00 | REVISION R000055
# TIMESTAMP END 2026-11-02T15:07:59-05:00 | REVISION R004800
assert sorted(pid for g in proposed_materials['groups'] for pid in g['member_ids'])==sorted(ids)
# TIMESTAMP START 2026-11-05T20:08:59+00:00 | REVISION R000063
from current_cache_bindings import verify as verify_cache_ownership,load_cache,assert_applies,runtime_descriptor
cache_ownership=verify_cache_ownership()
assert json.loads((ROOT/'src/current-cache-bindings.json').read_text())==cache_ownership,'Current cache descriptor differs from its immutable native proof'
enclosure_fit=load_cache('enclosure-baseline','baseline',cache_ownership)
proposed_enclosure_fit=load_cache('enclosure-proposed','proposed',cache_ownership)
assert_applies(enclosure_fit,'enclosure-baseline','baseline',cache_ownership)
assert_applies(proposed_enclosure_fit,'enclosure-proposed','proposed',cache_ownership)
# TIMESTAMP END 2026-11-05T20:08:59+00:00 | REVISION R000063
# TIMESTAMP START 2026-11-05T05:14:11+00:00 | REVISION R000024
from physical_data import read_physical_json
# TIMESTAMP START 2026-11-05T20:08:59+00:00 | REVISION R000063
foundation_data=load_cache('floor','baseline',cache_ownership,physical=True)
# TIMESTAMP END 2026-11-05T20:08:59+00:00 | REVISION R000063
# TIMESTAMP START 2026-11-05T12:40:59+00:00 | REVISION R000041
architecture_data=read_physical_json(ROOT/'src/architectural-solids.json')
assert architecture_data['status']=='PASS','The detailed architectural assembly is not ready for publication'
foundation_data={**foundation_data,'architecture':architecture_data}
# TIMESTAMP END 2026-11-05T12:40:59+00:00 | REVISION R000041
# TIMESTAMP END 2026-11-05T05:14:11+00:00 | REVISION R000024
# TIMESTAMP START 2026-11-05T20:08:59+00:00 | REVISION R000063
assert_applies(foundation_data,'floor','baseline',cache_ownership)
# TIMESTAMP END 2026-11-05T20:08:59+00:00 | REVISION R000063
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
# TIMESTAMP START 2026-11-05T20:08:59+00:00 | REVISION R000063
top_aux['enclosureFit']=load_cache('enclosure-top-entry','top-entry',cache_ownership)
for key,value in top_aux.items():
    if key=='enclosureFit':assert_applies(value,'enclosure-top-entry','top-entry',cache_ownership)
    else:assert value.get('source_model_sha256',value.get('source_sha256'))==top_sha,'Top-entry auxiliary hash mismatch: '+key
# TIMESTAMP END 2026-11-05T20:08:59+00:00 | REVISION R000063
# TIMESTAMP START 2026-11-02T15:07:59-05:00 | REVISION R004800
# TIMESTAMP START 2026-11-05T16:50:20+00:00 | REVISION R000055
assert len(top_aux['loadReview']['members'])==len(load_data['members'])==129
# TIMESTAMP END 2026-11-05T16:50:20+00:00 | REVISION R000055
# TIMESTAMP END 2026-11-02T15:07:59-05:00 | REVISION R004800
# TIMESTAMP START 2026-11-02T17:13:18-05:00 | REVISION R004819
assert {p['id'] for p in top_model['parts'] if p['is_timber']}=={p['id'] for p in data['parts'] if p['is_timber']}
assert set(ids)<={p['id'] for p in top_model['parts']}
assert all(p.get('group')=='joinery_pegs' for p in top_model['parts'] if p['id'] not in ids), 'Only declared physical locking pegs may extend the selected inventory'
top_cavity_audit=json.loads((ROOT/'docs/top-entry-cavity-fit-audit.json').read_text())
assert top_cavity_audit['status']=='PASS' and top_cavity_audit['model_sha256']==top_sha
assert top_cavity_audit['cavity_sha256']==hashlib.sha256((ROOT/'src/top-entry-proposed-cavities.json').read_bytes()).hexdigest()
for relative,sha in top_cavity_audit['sources'].items():
    assert hashlib.sha256((ROOT/relative).read_bytes()).hexdigest()==sha, 'Top-entry cavity proof is stale: '+relative
top_aux['cavities']['fit_audit']={key:top_cavity_audit[key] for key in ['status','summary']}
# TIMESTAMP END 2026-11-02T17:13:18-05:00 | REVISION R004819
model_variants['top-entry']={'model':top_model,'sha256':top_sha,**top_aux}
# TIMESTAMP START 2026-11-05T20:08:59+00:00 | REVISION R000063
for selected_variant in model_variants.values():selected_variant['cacheOwnership']=runtime_descriptor(cache_ownership)
# TIMESTAMP END 2026-11-05T20:08:59+00:00 | REVISION R000063
# TIMESTAMP START 2026-11-02T20:38:50-05:00 | REVISION R004870
# TIMESTAMP START 2026-11-05T20:08:59+00:00 | REVISION R000063
wall_joinery=load_cache('wall','baseline',cache_ownership)
# TIMESTAMP END 2026-11-05T20:08:59+00:00 | REVISION R000063
wall_joinery_sha=hashlib.sha256((ROOT/'src/wall-joinery-fit.json').read_bytes()).hexdigest()
for variant,fit in wall_joinery['variants'].items():
    assert fit['status']=='PASS'
    # TIMESTAMP START 2026-11-05T20:08:59+00:00 | REVISION R000063
    assert_applies(fit,'wall',variant,cache_ownership)
    # TIMESTAMP END 2026-11-05T20:08:59+00:00 | REVISION R000063
wall_joinery_code='const WALL_JOINERY_DATA='+encode(wall_joinery)+';\n'+(ROOT/'src/wall-joinery.js').read_text()
def assembled_model(model,variant):
    fit=wall_joinery['variants'][variant]
    return {**model,'parts':[{**p,**fit['primary_parts'][p['id']], 'faces':fit['primary_parts'][p['id']]['triangles'],
        'fit_geometry':{**p.get('fit_geometry',{}),'volume_m3':fit['primary_parts'][p['id']]['volume_m3']}}
        if p['id'] in fit['primary_parts'] else p for p in model['parts']],
        'wall_joinery_revision':'R004870','wall_joinery_fit_sha256':wall_joinery_sha}

# TIMESTAMP END 2026-11-02T20:38:50-05:00 | REVISION R004870
# TIMESTAMP START 2026-11-02T18:39:35-05:00 | REVISION R004836
# TIMESTAMP START 2026-11-04T23:17:24+00:00 | REVISION R000029
sheet_audit=json.loads((ROOT/'docs/underlayment-sheet-audit.json').read_text())
assert sheet_audit['status']=='PASS' and sheet_audit['sheetCount']==28
for relative,sha in sheet_audit['sources'].items():
    assert hashlib.sha256((ROOT/relative).read_bytes()).hexdigest()==sha,'Underlayment proof is stale: '+relative
assert hashlib.sha256((ROOT/sheet_audit['image']['path']).read_bytes()).hexdigest()==sheet_audit['image']['sha256'],'Underlayment drawing is stale'
# TIMESTAMP END 2026-11-04T23:17:24+00:00 | REVISION R000029
brace_visibility=json.loads((ROOT/'docs/brace-visibility-audit.json').read_text())
assert brace_visibility['status']=='PASS' and brace_visibility['physical_braces_in_complete']==24
for relative,sha in brace_visibility['sources'].items():
    assert hashlib.sha256((ROOT/relative).read_bytes()).hexdigest()==sha, 'Brace visibility audit is stale: '+relative
visibility_image=brace_visibility['image']
assert visibility_image['path']=='public/review/interior-braces.png'
assert hashlib.sha256((ROOT/visibility_image['path']).read_bytes()).hexdigest()==visibility_image['sha256'], 'Interior brace image is stale'
# TIMESTAMP END 2026-11-02T18:39:35-05:00 | REVISION R004836
# TIMESTAMP START 2026-11-04T19:33:21+00:00 | REVISION R000014
shoulder_audit=json.loads((ROOT/'docs/brace-shoulder-audit.json').read_text())
assert shoulder_audit['status']=='PASS'
assert shoulder_audit['script_sha256']==hashlib.sha256((ROOT/'scripts/audit_brace_shoulders.py').read_bytes()).hexdigest(),'Brace shoulder audit script is stale'
for result in shoulder_audit['variants']:
    for relative,sha in result['sources'].items():
        assert hashlib.sha256((ROOT/relative).read_bytes()).hexdigest()==sha,'Brace shoulder geometry proof is stale: '+relative
assert hashlib.sha256((ROOT/shoulder_audit['image']['path']).read_bytes()).hexdigest()==shoulder_audit['image']['sha256'],'Brace detail image is stale'
# TIMESTAMP END 2026-11-04T19:33:21+00:00 | REVISION R000014
# TIMESTAMP START 2026-11-02T19:03:48-05:00 | REVISION R004848
brace_sections=json.loads((ROOT/'docs/brace-sections.json').read_text())
assert brace_sections['status']=='PASS' and brace_sections['primary_brace_count']==24
for relative,sha in brace_sections['sources'].items():
    assert hashlib.sha256((ROOT/relative).read_bytes()).hexdigest()==sha, 'Brace section audit is stale: '+relative
assert brace_sections['image']['path']=='public/review/brace-sections.svg'
assert hashlib.sha256((ROOT/brace_sections['image']['path']).read_bytes()).hexdigest()==brace_sections['image']['sha256'], 'Brace section drawing is stale'
# TIMESTAMP END 2026-11-02T19:03:48-05:00 | REVISION R004848


# TIMESTAMP START 2026-11-02T15:07:59-05:00 | REVISION R004800
mudroom_source=(ROOT/'src/mudroom.js').read_text()
mudroom_roof_source=(ROOT/'src/mudroom-roof.js').read_text()
# TIMESTAMP START 2026-11-05T20:08:59+00:00 | REVISION R000063
mudroom_fit=load_cache('porch','baseline',cache_ownership)
assert mudroom_fit['status']=='PASS','Porch joinery must pass before publishing'
assert_applies(mudroom_fit,'porch','baseline',cache_ownership)
# TIMESTAMP END 2026-11-05T20:08:59+00:00 | REVISION R000063
for selected_model in [data,proposed_model,top_model]:
    for pid,anchor in mudroom_fit['anchors'].items():
        assert next(p for p in selected_model['parts'] if p['id']==pid)['center']==anchor, 'Porch anchor differs between models'
mudroom_code=mudroom_roof_source+'\nconst MUDROOM_JOINERY_FIT='+encode(mudroom_fit)+';\n'+mudroom_source
# TIMESTAMP START 2026-11-02T15:57:59-05:00 | REVISION R004811
disassembly_plans=json.loads((ROOT/'src/disassembly-plan.json').read_text())
for variant in ['baseline','proposed','top-entry']:
    plan=disassembly_plans['variants'][variant]
    assert plan['status'] in ['PASS','PARTIAL'] and plan['verification']['status']=='PASS', 'Disassembly path audit must pass: '+variant
    # TIMESTAMP START 2026-11-02T18:14:42-05:00 | REVISION R004830
    if variant=='top-entry':
        assert plan['status']=='PASS', 'Default model requires a complete disassembly sequence'
    # TIMESTAMP END 2026-11-02T18:14:42-05:00 | REVISION R004830
    for relative,sha in plan['sources'].items():
        assert hashlib.sha256((ROOT/relative).read_bytes()).hexdigest()==sha, 'Disassembly source is stale: '+relative
    model_file={'baseline':'model-data.json','proposed':'step-lap-proposed-model.json','top-entry':'top-entry-proposed-model.json'}[variant]
    enclosure_file={'baseline':'enclosure-fit.json','proposed':'step-lap-proposed-enclosure-fit.json','top-entry':'top-entry-proposed-enclosure-fit.json'}[variant]
    # TIMESTAMP START 2026-11-02T20:38:50-05:00 | REVISION R004870
    required_sources={'src/'+name for name in [model_file,enclosure_file,'wall-joinery-fit.json','wall-joinery.js','floor-foundation-solids.json','mudroom-joinery-fit.json','mudroom.js','mudroom-roof.js','roof-coverings.js','floor-foundation.js','schematic-walls.js','display-presets.js']}
    # TIMESTAMP END 2026-11-02T20:38:50-05:00 | REVISION R004870
    assert required_sources<=set(plan['sources']), 'Disassembly proof omits a physical geometry source'
    physical=set(plan['physical_ids']);moved={pid for stage in plan['stages'] for motion in stage.get('motions',[stage]) for pid in motion['member_ids']}
    blocked={pid for group in plan['blocked'] for pid in group['member_ids']}
    assert len(physical)==len(plan['physical_ids']) and moved<=physical and blocked<=physical
    # TIMESTAMP START 2026-11-03T06:58:53-05:00 | REVISION R004899
    fixed=set(plan['anchored_ids'])
    assert fixed==({'FLOOR-CENTRAL-HUB','PIER-C','PIER-C-BELOW'} if variant=='top-entry' else set())
    assert not fixed & moved and fixed<=physical
    assert moved==set(plan['moved_ids']) and physical-moved-fixed==set(plan['unmoved_ids'])
    assert physical-moved-fixed<=blocked, 'Disassembly proof must account for every physical piece'
    # TIMESTAMP END 2026-11-03T06:58:53-05:00 | REVISION R004899
    assert len({stage['id'] for stage in plan['stages']})==len(plan['stages']), 'Disassembly stage identifiers must be unique'
    assert all(entry.get('physical') is False and entry['id'] not in physical for entry in plan['excluded'])
    if plan['status']=='PASS':
        assert not plan.get('blocked') and not plan['unmoved_ids'], 'Complete disassembly cannot contain locked pieces'
disassembly_code='const DISASSEMBLY_PLANS='+encode(disassembly_plans)+';\n'+(ROOT/'src/disassembly.js').read_text()
assert template.count('/*__DISASSEMBLY__*/')==1
template=template.replace('/*__DISASSEMBLY__*/',disassembly_code)
# TIMESTAMP END 2026-11-02T15:57:59-05:00 | REVISION R004811
# TIMESTAMP END 2026-11-02T15:07:59-05:00 | REVISION R004800

# TIMESTAMP START 2026-11-02T15:07:59-05:00 | REVISION R004800
# TIMESTAMP START 2026-11-02T14:22:13-05:00 | REVISION R004792
# TIMESTAMP START 2026-11-02T20:38:50-05:00 | REVISION R004870
template=template.replace('/*__WALL_JOINERY__*/',wall_joinery_code)
# TIMESTAMP START 2026-11-05T04:09:58+00:00 | REVISION R000018
# TIMESTAMP START 2026-11-05T04:29:18+00:00 | REVISION R000022
assert template.count('/*__PHYSICAL_PARTS__*/')==1
template=template.replace('/*__PHYSICAL_PARTS__*/',(ROOT/'src/physical-parts.js').read_text())
# TIMESTAMP END 2026-11-05T04:29:18+00:00 | REVISION R000022
assert template.count('/*__FOUNDATION_TAKEOFF__*/')==1
template=template.replace('/*__FOUNDATION_TAKEOFF__*/',(ROOT/'src/foundation-takeoff.js').read_text())
# TIMESTAMP START 2026-11-05T06:53:24+00:00 | REVISION R000030
assert template.count('/*__COMPONENT_INVENTORY__*/')==1
template=template.replace('/*__COMPONENT_INVENTORY__*/',(ROOT/'src/component-inventory.js').read_text())
# TIMESTAMP END 2026-11-05T06:53:24+00:00 | REVISION R000030
# TIMESTAMP END 2026-11-05T04:09:58+00:00 | REVISION R000018
# TIMESTAMP START 2026-11-03T13:30:29-05:00 | REVISION R005026
# TIMESTAMP START 2026-11-03T13:59:01-05:00 | REVISION R005033
# TIMESTAMP START 2026-11-05T12:40:59+00:00 | REVISION R000041
# TIMESTAMP START 2026-11-05T17:09:28+00:00 | REVISION R000057
# TIMESTAMP START 2026-11-05T17:19:58+00:00 | REVISION R000058
# TIMESTAMP START 2026-11-05T20:08:59+00:00 | REVISION R000063
for marker,name in [('/*__CURRENT_CACHE_BINDINGS__*/','current-cache-bindings.js'),('/*__CUPOLA_PARAMETRIC__*/','cupola-parametric.js'),('/*__WINDOW_ASSEMBLIES__*/','window-assemblies.js'),('/*__ARCHITECTURE__*/','architecture.js'),('/*__JOINERY_DIMENSIONS__*/','joinery-dimensions.js'),('/*__PARAMETRIC_MODEL__*/','parametric-model.js'),('/*__PARAMETRIC_CONTROLS__*/','parametric-controls.js'),('/*__MOTION_MODES__*/','motion-modes.js')]:
# TIMESTAMP END 2026-11-05T20:08:59+00:00 | REVISION R000063
# TIMESTAMP END 2026-11-05T17:19:58+00:00 | REVISION R000058
# TIMESTAMP END 2026-11-05T17:09:28+00:00 | REVISION R000057
# TIMESTAMP END 2026-11-05T12:40:59+00:00 | REVISION R000041
# TIMESTAMP END 2026-11-03T13:59:01-05:00 | REVISION R005033
    assert template.count(marker)==1
    template=template.replace(marker,(ROOT/'src'/name).read_text())
# TIMESTAMP END 2026-11-03T13:30:29-05:00 | REVISION R005026
# TIMESTAMP END 2026-11-02T20:38:50-05:00 | REVISION R004870
for marker, value in [('/*__MUDROOM__*/',mudroom_code), ('/*__ROOF_COVERINGS__*/',(ROOT/'src/roof-coverings.js').read_text()), ('/*__DISPLAY_PRESETS__*/',(ROOT/'src/display-presets.js').read_text()), ('/*__FLOOR_FOUNDATION__*/','const FLOOR_FOUNDATION_DATA='+encode(foundation_data)+';\n'+(ROOT/'src/floor-foundation.js').read_text()),('/*__CUT_FACE_ANALYSIS__*/', (ROOT/'src/cut-face-analysis.js').read_text()), ('/*__CUT_ANGLE_VIEW__*/', (ROOT/'src/cut-angle-view.js').read_text()), ('/*__MODEL_VARIANTS__*/', (ROOT/'src/model-variants.js').read_text()), ('__MODEL_VARIANTS_JSON__',encode(model_variants)), ('/*__STEP_LAP_REVIEW__*/', (ROOT/'src/step-lap-review.js').read_text()), ('__STEP_LAP_PROPOSAL_JSON__',encode(step_lap)), ('/*__SCHEMATIC_WALLS__*/', 'const OCTAGON_ENCLOSURE_FIT=SAVED_MODEL_CONTEXT.enclosureFit;\n'+(ROOT/'src/schematic-walls.js').read_text()), ('/*__INSPECTION_TOOLS__*/', inspection),
                      ('/*__ARCHITECTURAL_PLANS__*/', (ROOT/'src/architectural-plans.js').read_text()),
                      ('/*__EDGE_MEASUREMENT_TOOLS__*/', (ROOT/'src/edge-measurements.js').read_text()),
                      ('/*__LOAD_REVIEW__*/', load_review), ('/*__GEOMETRY_OVERLAYS__*/', overlays), ('__PARTS_JSON__', encode(data))]:
    assert template.count(marker) == 1, marker
    template = template.replace(marker, value)
# TIMESTAMP END 2026-11-02T14:22:13-05:00 | REVISION R004792
# TIMESTAMP END 2026-11-02T15:07:59-05:00 | REVISION R004800
assert not re.search(r'__(?:PARTS|MATERIALS|CAVITY|STEP_LAP_PROPOSAL)_JSON__', template)
for block in ScriptBlocks(template).blocks:
    if block['attrs'].get('type','').lower()=='application/json':
        json.loads(block['body'])  # Every embedded data script must remain valid JSON.
scripts=executable_blocks(template)
# TIMESTAMP START 2026-11-03T13:30:29-05:00 | REVISION R005026
# Browser bootstrap owns async generation. The offline harness executes the
# exact viewer body at the saved context, while parameter tests exercise the
# generator and real-browser QA exercises the asynchronous bootstrap.
scripts=[s.replace('function startViewer(MODEL_CONTEXT){','const MODEL_CONTEXT=SAVED_MODEL_CONTEXT;') for s in scripts]
scripts=[re.sub(r'\n}\n/\* PARAMETRIC_VIEWER_BODY_END \*/','\n/* PARAMETRIC_VIEWER_BODY_END */',s) for s in scripts]
scripts=[re.sub(r'/\* PARAMETRIC_BOOT_START \*/.*?/\* PARAMETRIC_BOOT_END \*/','',s,flags=re.S) for s in scripts]
# TIMESTAMP END 2026-11-03T13:30:29-05:00 | REVISION R005026
assert sum('const stepLapReview=OctagonStepLap.createController' in b for b in scripts)==1

dist = ROOT/'dist'
dist.mkdir(exist_ok=True)
# TIMESTAMP START 2026-11-03T13:30:29-05:00 | REVISION R005026
shutil.copytree(ROOT/'public/vendor',dist/'vendor',dirs_exist_ok=True)
shutil.copyfile(ROOT/'src/parametric-source.json',dist/'parametric-source.json')
# TIMESTAMP END 2026-11-03T13:30:29-05:00 | REVISION R005026
# TIMESTAMP START 2026-11-02T19:03:48-05:00 | REVISION R004848
(dist/'review').mkdir(exist_ok=True)
shutil.copyfile(ROOT/'public/review/brace-sections.svg',dist/'review/brace-sections.svg')
# TIMESTAMP START 2026-11-04T23:17:24+00:00 | REVISION R000029
shutil.copyfile(ROOT/'public/review/underlayment-sheets.svg',dist/'review/underlayment-sheets.svg')
# TIMESTAMP END 2026-11-04T23:17:24+00:00 | REVISION R000029
# TIMESTAMP START 2026-11-04T19:33:21+00:00 | REVISION R000014
shutil.copyfile(ROOT/'public/review/brace-shoulders.png',dist/'review/brace-shoulders.png')
# TIMESTAMP END 2026-11-04T19:33:21+00:00 | REVISION R000014
# TIMESTAMP END 2026-11-02T19:03:48-05:00 | REVISION R004848
# Current pages only; historical NAV-05 reports remain available through Git history.
for name in ['about.html', 'r01.html', 'joinery.html', 'structural-audit.html', 'JOINT-DESIGN-BRIEF.md',
             # TIMESTAMP START 2026-11-02T18:39:35-05:00 | REVISION R004836
             'downloads/index.html', 'review/index.html', 'review/interior-braces.png', 'robots.txt']:
             # TIMESTAMP END 2026-11-02T18:39:35-05:00 | REVISION R004836
    source = ROOT/'public'/name
    if source.exists():
        target = dist/name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
(dist/'index.html').write_text(template)
(ROOT/'index.html').write_text(template)
downloads = dist/'downloads'
downloads.mkdir(exist_ok=True)
# TIMESTAMP START 2026-11-02T19:03:48-05:00 | REVISION R004848
shutil.copyfile(ROOT/'docs/brace-sections.json',downloads/'brace-section-audit.json')
# TIMESTAMP END 2026-11-02T19:03:48-05:00 | REVISION R004848
# TIMESTAMP START 2026-11-02T20:38:50-05:00 | REVISION R004870
(downloads/'Octagon-R01-model.json').write_text(encode(assembled_model(data,'baseline'))+'\n')
(downloads/'Octagon-PROPOSED-step-lap-model.json').write_text(encode(assembled_model(proposed_model,'proposed'))+'\n')
# TIMESTAMP END 2026-11-02T20:38:50-05:00 | REVISION R004870
# TIMESTAMP START 2026-11-02T10:05:34-05:00 | REVISION R004758
# TIMESTAMP START 2026-11-02T17:13:18-05:00 | REVISION R004819
# TIMESTAMP START 2026-11-04T23:17:24+00:00 | REVISION R000029
audit_downloads=['underlayment-sheet-audit.json']
audit_downloads+=['r01-change-register.json','r01-verification.json','joinery-verification.json','structural-audit.json','cavity-fit-audit.json','step-lap-proposed-cavity-fit-audit.json','top-entry-cavity-fit-audit.json']
# TIMESTAMP END 2026-11-04T23:17:24+00:00 | REVISION R000029
# TIMESTAMP START 2026-11-02T18:39:35-05:00 | REVISION R004836
audit_downloads.append('brace-visibility-audit.json')
# TIMESTAMP END 2026-11-02T18:39:35-05:00 | REVISION R004836
# TIMESTAMP END 2026-11-02T17:13:18-05:00 | REVISION R004819
# TIMESTAMP END 2026-11-02T10:05:34-05:00 | REVISION R004758
for source_name in audit_downloads:
    source = ROOT/'docs'/source_name
    if source.exists():
        shutil.copyfile(source, downloads/source_name)
# TIMESTAMP START 2026-11-02T18:14:42-05:00 | REVISION R004830
glb_exports=runpy.run_path(str(ROOT/'scripts/export_r01_glb.py'), run_name='octagon_glb_exports')
plan_sha=hashlib.sha256((ROOT/'src/disassembly-plan.json').read_bytes()).hexdigest()
for variant,model,prefix,revision,source_sha in [
    ('baseline',data,'Octagon-R01-','R01',model_sha),
    ('proposed',proposed_model,'Octagon-PROPOSED-step-lap-','Proposed step-lap joinery',proposed_sha),
    ('top-entry',top_model,'Octagon-TOP-ENTRY-','Removable joinery proposal',top_sha),
]:
# TIMESTAMP START 2026-11-02T20:38:50-05:00 | REVISION R004870
    model=assembled_model(model,variant)
# TIMESTAMP END 2026-11-02T20:38:50-05:00 | REVISION R004870
    plan=disassembly_plans['variants'][variant]
    offsets={p['id']:[0.,0.,0.] for p in model['parts']}
    for stage in plan['stages']:
        for motion in stage.get('motions',[stage]):
            for member_id in motion['member_ids']:
                if member_id in offsets:
                    offsets[member_id]=[a+b for a,b in zip(offsets[member_id],motion['delta_m'])]
    endpoint_model={**model,'parts':[{**p,'exploded_offset':offsets[p['id']]} for p in model['parts']]}
    exported_ids={p['id'] for p in model['parts'] if not p.get('temporary') and p['group']!='roof_envelope'}
    metadata={'revision':revision,'source_model_sha256':source_sha,
              'disassembly_plan_sha256':plan_sha,'disassembly_variant':variant,
              'disassembly_status':plan['status'],'disassembly_stage_count':len(plan['stages']),
              'disassembly_held_ids':sorted(exported_ids.intersection(plan['unmoved_ids']))}
    if variant!='baseline':
        metadata['status']=model['status']
    for exploded in [False,True]:
        target=downloads/(prefix+('exploded' if exploded else 'assembled')+'.glb')
        pose_metadata={**metadata,'disassembly_pose':'checked-endpoint' if exploded else 'assembled-start',
                       'disassembly_scope':'Canonical frame/cupola subset; '+('static endpoint' if exploded else 'assembled start')+' of the checked full-scene sequence.'}
        target.write_bytes(glb_exports['export'](endpoint_model if exploded else model,exploded,pose_metadata))
# TIMESTAMP END 2026-11-02T18:14:42-05:00 | REVISION R004830
# TIMESTAMP START 2026-11-02T20:38:50-05:00 | REVISION R004870
(downloads/'Octagon-TOP-ENTRY-model.json').write_text(encode(assembled_model(top_model,'top-entry'))+'\n')
# TIMESTAMP END 2026-11-02T20:38:50-05:00 | REVISION R004870
tests = ROOT/'tests'
tests.mkdir(exist_ok=True)
(tests/'embedded-model.json').write_text(encode(data))
(tests/'viewer-script-check.js').write_text('\n'.join(scripts))
# TIMESTAMP START 2026-11-04T19:27:13+00:00 | REVISION R000001
from build_runtime import write_runtime
print(json.dumps(write_runtime(template, model=data, variants=model_variants,
    wall_joinery=wall_joinery, foundation=foundation_data, mudroom=mudroom_fit,
    disassembly=disassembly_plans, study=step_lap)))
# TIMESTAMP END 2026-11-04T19:27:13+00:00 | REVISION R000001
print(json.dumps({'revision':'R01', 'components':len(ids), 'html_bytes':len(template.encode()),
                  'model_sha256':model_sha, 'output':'dist/index.html', 'network_dependencies':False}))


# TIMESTAMP END 2026-11-01T22:44:38-05:00 | REVISION R004653

# TIMESTAMP END 2026-11-01T23:19:38-05:00 | REVISION R004668
# TIMESTAMP END 2026-11-04T20:33:26+00:00 | REVISION R000023

# TIMESTAMP END 2026-11-04T23:23:25+00:00 | REVISION R000011

# TIMESTAMP END 2026-11-04T23:48:03+00:00 | REVISION R000012
