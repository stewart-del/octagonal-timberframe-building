#!/usr/bin/env python3
"""Build the offline-capable static viewer and prepare its scripted regression fixture."""
from pathlib import Path
import hashlib, json, re, shutil
ROOT=Path(__file__).resolve().parents[1]
# GitHub's connector has a request-size limit. Restore the saved ZIP from
# verified parts without changing its bytes or downloading anything.
manifest_path=ROOT/'source-assets/model-archive.json'
if manifest_path.exists():
 manifest=json.loads(manifest_path.read_text())
 chunks=[]
 for part in manifest['parts']:
  chunk=(manifest_path.parent/part['file']).read_bytes()
  if len(chunk)!=part['bytes'] or hashlib.sha256(chunk).hexdigest()!=part['sha256']:
   raise ValueError('Model archive part failed integrity check: '+part['file'])
  chunks.append(chunk)
 archive=b''.join(chunks)
 if len(archive)!=manifest['bytes'] or hashlib.sha256(archive).hexdigest()!=manifest['sha256']:
  raise ValueError('Restored model archive differs from the original saved ZIP')
 destination=ROOT/'public/downloads/Octagon-model-and-review.zip'
 destination.parent.mkdir(parents=True,exist_ok=True)
 if not destination.exists() or destination.read_bytes()!=archive:
  temporary=destination.with_suffix('.zip.tmp')
  temporary.write_bytes(archive)
  temporary.replace(destination)
data=json.loads((ROOT/'src/model-data.json').read_text())
assert len(data['parts'])==104
template=(ROOT/'src/viewer.template.html').read_text()
materials=json.loads((ROOT/'src/material-groups.json').read_text())
assert materials['source_sha256']==hashlib.sha256((ROOT/'src/model-data.json').read_bytes()).hexdigest(), 'Materials grouping must be regenerated for changed geometry'
grouped_ids=[pid for group in materials['groups'] for pid in group['member_ids']]
assert sorted(grouped_ids)==sorted(p['id'] for p in data['parts']) and len(set(grouped_ids))==104
assert all(group['quantity']==len(group['member_ids']) and group['representative_id'] in group['member_ids'] for group in materials['groups'])
inspection=(ROOT/'src/inspection-tools.js').read_text()
assert inspection.count('__MATERIALS_JSON__')==1
inspection=inspection.replace('__MATERIALS_JSON__',json.dumps(materials,separators=(',',':'),ensure_ascii=True).replace('</','<\\/'))
assert template.count('/*__INSPECTION_TOOLS__*/')==1
template=template.replace('/*__INSPECTION_TOOLS__*/',inspection)
cavities=json.loads((ROOT/'src/cavity-data.json').read_text())
assert cavities['source_model_sha256']==hashlib.sha256((ROOT/'src/model-data.json').read_bytes()).hexdigest(), 'Cavity data must match current geometry'
assert set(cavities['parts'])==set(p['id'] for p in data['parts']) and cavities['summary']['complete']
overlap=json.loads((ROOT/'public/review/fitted-overlap-check.json').read_text())
assert overlap['source_cells_sha256']==cavities['source_cells_sha256'], 'Overlap evidence must match the cavity source cells'
edge_audit=json.loads((ROOT/'public/review/edge-model-audit.json').read_text())
assert edge_audit['source_sha256']==cavities['source_model_sha256'], 'Edge evidence must match current geometry'
overlays=(ROOT/'src/geometry-overlays.js').read_text().replace('__CAVITY_JSON__',json.dumps(cavities,separators=(',',':'),ensure_ascii=True).replace('</','<\\/'))
assert template.count('/*__EDGE_MEASUREMENT_TOOLS__*/')==1
template=template.replace('/*__EDGE_MEASUREMENT_TOOLS__*/',(ROOT/'src/edge-measurements.js').read_text())
assert template.count('/*__GEOMETRY_OVERLAYS__*/')==1
template=template.replace('/*__GEOMETRY_OVERLAYS__*/',overlays)
assert template.count('__PARTS_JSON__')==1
encoded=json.dumps(data,separators=(',',':'),ensure_ascii=True).replace('</','<\\/')
page=template.replace('__PARTS_JSON__',encoded)
dist=ROOT/'dist'
dist.mkdir(exist_ok=True)
shutil.copytree(ROOT/'public',dist,dirs_exist_ok=True)
(dist/'index.html').write_text(page)
tests=ROOT/'tests'
tests.mkdir(exist_ok=True)
(tests/'embedded-model.json').write_text(json.dumps(data,separators=(',',':')))
(tests/'viewer-script-check.js').write_text('\n'.join(re.findall(r'<script>(.*?)</script>',page,flags=re.S)))
print(json.dumps({'site':'Octagonal Timberframe Building','pieces':len(data['parts']),'html_bytes':len(page.encode()),'output':'dist/index.html','network_dependencies':False}))
