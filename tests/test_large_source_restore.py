# TIMESTAMP START 2026-11-05T21:31:46+00:00 | REVISION R000067
"""Fresh source restoration, corruption refusal and owner-edit preservation."""
from pathlib import Path
import hashlib,json,shutil,sys,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from restore_large_sources import restore,SourceRestoreError,sha
from current_cache_bindings import verify
class LargeSources(unittest.TestCase):
 def fixture(self,root,data=b'\x00exact source geometry\xff'*100):
  folder=Path(root)/'source-assets';folder.mkdir();parts=[]
  for i,piece in enumerate([data[:177],data[177:]]):
   path=folder/('part'+str(i));path.write_bytes(piece);parts.append({'path':str(path.relative_to(root)),'bytes':len(piece),'sha256':sha(path)})
  manifest={'schema':'octagon-lossless-large-source-1','files':[{'path':'src/geometry.json','bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'parts':parts}]};(folder/'large-source-manifest.json').write_text(json.dumps(manifest));return manifest,data
 def test_exact_fresh_restore_and_reuse(self):
  with tempfile.TemporaryDirectory() as root:
   _,data=self.fixture(root);self.assertEqual(restore(root)['restored'],['src/geometry.json']);target=Path(root)/'src/geometry.json';self.assertEqual(target.read_bytes(),data);before=target.stat().st_ino;self.assertEqual(restore(root)['existingExact'],['src/geometry.json']);self.assertEqual(target.stat().st_ino,before)
 def test_corrupt_chunk_and_existing_owner_edit_are_preserved(self):
  with tempfile.TemporaryDirectory() as root:
   self.fixture(root);part=Path(root)/'source-assets/part0';original=part.read_bytes();part.write_bytes(b'x'+original[1:])
   with self.assertRaisesRegex(SourceRestoreError,'chunk changed'):restore(root)
   self.assertFalse((Path(root)/'src/geometry.json').exists());part.write_bytes(original);restore(root);target=Path(root)/'src/geometry.json';target.write_bytes(b'owner edit')
   with self.assertRaisesRegex(SourceRestoreError,'Existing source differs'):restore(root)
   self.assertEqual(target.read_bytes(),b'owner edit');self.assertFalse(list(target.parent.glob('*.restore-*')))
 def test_actual_large_cache_reconstructs_all_original_bytes_and_binding(self):
  manifest=json.loads((ROOT/'source-assets/large-source-manifest.json').read_text());self.assertEqual(len(manifest['files']),1);record=manifest['files'][0];self.assertEqual(record['path'],'src/wall-joinery-fit.json');self.assertEqual(record['bytes'],31392052)
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory);(root/'source-assets').mkdir();(root/'source-assets/large-source-manifest.json').write_text(json.dumps(manifest))
   for part in record['parts']:
    path=root/part['path'];path.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/part['path'],path);self.assertLessEqual(path.stat().st_size,8*1024*1024)
   restore(root);target=root/record['path'];self.assertEqual(target.read_bytes(),(ROOT/record['path']).read_bytes());descriptor=verify(read_source=lambda name:target.read_bytes() if name==record['path'] else (ROOT/name).read_bytes());self.assertEqual(descriptor['repositoryInputs'][record['path']],sha(target));self.assertFalse(descriptor['wholeBuildingReady'])
if __name__=='__main__':unittest.main()
# TIMESTAMP END 2026-11-05T21:31:46+00:00 | REVISION R000067
