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
