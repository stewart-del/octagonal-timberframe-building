# TIMESTAMP START 2026-11-05T21:31:46+00:00 | REVISION R000067
"""Restore byte-exact generated caches from small hash-verified Git objects.

Chunking changes source transport only. Original geometry, source hashes,
historical certificates and physical thresholds remain unchanged.
"""
from pathlib import Path
import hashlib,json,os,tempfile
ROOT=Path(__file__).resolve().parents[1]
class SourceRestoreError(RuntimeError):pass
def safe_path(root,name):
 root=Path(root).resolve();value=Path(name)
 if value.is_absolute() or '..' in value.parts:raise SourceRestoreError('Invalid large-source relative path')
 target=(root/value).resolve()
 if not target.is_relative_to(root):raise SourceRestoreError('Large-source path escapes the project')
 return target
def sha(path):
 digest=hashlib.sha256()
 with Path(path).open('rb') as stream:
  for data in iter(lambda:stream.read(512*1024),b''):digest.update(data)
 return digest.hexdigest()
def restore(root=ROOT,manifest_name='source-assets/large-source-manifest.json'):
 root=Path(root).resolve();manifest=json.loads(safe_path(root,manifest_name).read_text())
 if manifest.get('schema')!='octagon-lossless-large-source-1':raise SourceRestoreError('Unknown large-source manifest')
 restored=[];existing=[];targets=set()
 for record in manifest['files']:
  target=safe_path(root,record['path'])
  if target in targets:raise SourceRestoreError('Duplicate large-source target')
  targets.add(target);parts=[];size=0
  for part in record['parts']:
   source=safe_path(root,part['path'])
   if source.stat().st_size!=part['bytes'] or sha(source)!=part['sha256']:raise SourceRestoreError('Large-source chunk changed: '+part['path'])
   parts.append(source);size+=part['bytes']
  if size!=record['bytes']:raise SourceRestoreError('Large-source byte count disagrees')
  if target.exists():
   if target.stat().st_size!=size or sha(target)!=record['sha256']:raise SourceRestoreError('Existing source differs; preserve and review it before restoring: '+record['path'])
   existing.append(record['path']);continue
  target.parent.mkdir(parents=True,exist_ok=True);temporary=None
  try:
   digest=hashlib.sha256()
   with tempfile.NamedTemporaryFile(dir=target.parent,prefix='.'+target.name+'.restore-',delete=False) as output:
    temporary=Path(output.name)
    for source in parts:
     with source.open('rb') as stream:
      for data in iter(lambda:stream.read(512*1024),b''):digest.update(data);output.write(data)
    output.flush();os.fsync(output.fileno())
   if digest.hexdigest()!=record['sha256']:raise SourceRestoreError('Reconstructed source digest disagrees: '+record['path'])
   os.chmod(temporary,0o644)
   # A hard link publishes the complete file atomically without replacing a
   # source another process or the owner created during reconstruction.
   try:os.link(temporary,target)
   except FileExistsError:
    if target.stat().st_size!=size or sha(target)!=record['sha256']:raise SourceRestoreError('Source appeared during restoration; it was preserved')
   restored.append(record['path'])
  finally:
   if temporary is not None:temporary.unlink(missing_ok=True)
 return {'restored':restored,'existingExact':existing,'sourceBytesUnchanged':True}
if __name__=='__main__':print(json.dumps(restore()))
# TIMESTAMP END 2026-11-05T21:31:46+00:00 | REVISION R000067
