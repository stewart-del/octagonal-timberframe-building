# TIMESTAMP START 2026-11-01T23:19:38-05:00 | REVISION R004668
# TIMESTAMP START 2026-11-01T22:44:38-05:00 | REVISION R004653
#!/usr/bin/env python3
"""Build the R01 viewer and exports from the same current geometry source."""
from pathlib import Path
import hashlib, json, re, runpy, shutil

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
def encode(value):
    return json.dumps(value, separators=(',', ':'), ensure_ascii=True).replace('</', '<\\/')
inspection = (ROOT/'src/inspection-tools.js').read_text().replace('__MATERIALS_JSON__', encode(materials))
# TIMESTAMP START 2026-11-01T22:44:38-05:00 | REVISION R004653
cavities = json.loads((ROOT/'src/cavity-data.json').read_text())
assert cavities['source_model_sha256'] == model_sha
# TIMESTAMP END 2026-11-01T22:44:38-05:00 | REVISION R004653

load_data=json.loads((ROOT/'src/load-review-data.json').read_text())
assert load_data['source_model_sha256']==model_sha, 'Load review must match current geometry'
load_review=(ROOT/'src/load-review.js').read_text().replace('__LOAD_REVIEW_JSON__',encode(load_data))
overlays = (ROOT/'src/geometry-overlays.js').read_text().replace('__CAVITY_JSON__', encode(cavities))
for marker, value in [('/*__INSPECTION_TOOLS__*/', inspection),
                      ('/*__EDGE_MEASUREMENT_TOOLS__*/', (ROOT/'src/edge-measurements.js').read_text()),
                      ('/*__LOAD_REVIEW__*/', load_review), ('/*__GEOMETRY_OVERLAYS__*/', overlays), ('__PARTS_JSON__', encode(data))]:
    assert template.count(marker) == 1, marker
    template = template.replace(marker, value)
assert not re.search(r'__(?:PARTS|MATERIALS|CAVITY)_JSON__', template)

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
for source_name in ['r01-change-register.json', 'r01-verification.json', 'joinery-verification.json', 'structural-audit.json']:
    source = ROOT/'docs'/source_name
    if source.exists():
        shutil.copyfile(source, downloads/source_name)
runpy.run_path(str(ROOT/'scripts/export_r01_glb.py'), run_name='__main__')
tests = ROOT/'tests'
tests.mkdir(exist_ok=True)
(tests/'embedded-model.json').write_text(encode(data))
(tests/'viewer-script-check.js').write_text('\n'.join(re.findall(r'<script>(.*?)</script>', template, flags=re.S)))
print(json.dumps({'revision':'R01', 'components':len(ids), 'html_bytes':len(template.encode()),
                  'model_sha256':model_sha, 'output':'dist/index.html', 'network_dependencies':False}))


# TIMESTAMP END 2026-11-01T22:44:38-05:00 | REVISION R004653

# TIMESTAMP END 2026-11-01T23:19:38-05:00 | REVISION R004668
