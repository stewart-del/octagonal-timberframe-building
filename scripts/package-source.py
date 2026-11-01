#!/usr/bin/env python3
"""Package editable source and public assets; regenerate dist with scripts/build.py."""
from pathlib import Path
import hashlib,json,sys,zipfile
root=Path(__file__).resolve().parents[1]
if len(sys.argv)!=2:raise SystemExit('Usage: python3 scripts/package-source.py /absolute/output.zip')
archive=Path(sys.argv[1]).resolve()
files=[]
for p in root.rglob('*'):
 if not p.is_file() or p.resolve()==archive:continue
 rel=p.relative_to(root)
 if any(x in rel.parts for x in ['.git','dist','__pycache__','node_modules','.sites-runtime']):continue
 if p.name in ['embedded-model.json','viewer-script-check.js'] or p.name.startswith('.env'):continue
 files.append(p)
archive.parent.mkdir(parents=True,exist_ok=True)
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in sorted(files):z.write(p,'octagonal-timberframe-building/'+str(p.relative_to(root)))
 z.writestr('SOURCE-MANIFEST.json',json.dumps([{'path':str(p.relative_to(root)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(files)],indent=2))
with zipfile.ZipFile(archive) as z:assert z.testzip() is None
print(json.dumps({'archive':str(archive),'files':len(files),'bytes':archive.stat().st_size,'crc':'PASS'}))
