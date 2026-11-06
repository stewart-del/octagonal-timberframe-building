# TIMESTAMP START 2026-11-06T03:31:53+00:00 | REVISION R000085
"""Current templates and changed geometry cannot reuse stale build assumptions."""
from pathlib import Path
import json,sys,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from build_runtime import rewrite_baseline_audit,build_edges

class RuntimePackaging(unittest.TestCase):
 def test_audit_summary_is_optional_and_never_reintroduces_the_baseline_mesh(self):
  self.assertEqual(rewrite_baseline_audit('current viewer'),'current viewer')
  for count in [1,2,3]:
   value=';'.join(['MODEL_VARIANTS.baseline.model.joinery_verification']*count)+ ';MODEL_VARIANTS.baseline.sha256'
   converted=rewrite_baseline_audit(value);self.assertNotIn('MODEL_VARIANTS.baseline',converted);self.assertEqual(converted.count('SITE_DATA.baselineAudit.verification'),count)
  with self.assertRaisesRegex(AssertionError,'Unsupported eager baseline'):rewrite_baseline_audit('MODEL_VARIANTS.baseline.model.vertices')
 def test_drawing_cache_reuses_exact_inputs_and_rejects_changed_or_corrupt_outputs(self):
  with tempfile.TemporaryDirectory()as directory:
   root=Path(directory);(root/'scripts').mkdir();(root/'src').mkdir();script=root/'scripts/build_mesh_cache.cjs';script.write_text('geometry producer');source=root/'src/shape.js';source.write_text('actual shape');base=root/'output';calls=[]
   def worker(args,check):
    calls.append(args);base.with_suffix('.bin').write_bytes(b'exact source edge data');base.with_suffix('.json').write_text(json.dumps({'ACTOR':[0,6]}))
   build_edges({'vertices':[1,2,3]},base,root=root,run=worker);build_edges({'vertices':[1,2,3]},base,root=root,run=worker);self.assertEqual(len(calls),1)
   build_edges({'vertices':[1,2,4]},base,root=root,run=worker);self.assertEqual(len(calls),2)
   source.write_text('changed actual shape');build_edges({'vertices':[1,2,4]},base,root=root,run=worker);self.assertEqual(len(calls),3)
   for path in (root/'.codex-runtime/runtime-mesh-cache').glob('*/output.bin'):path.write_bytes(b'corrupt')
   build_edges({'vertices':[1,2,4]},base,root=root,run=worker);self.assertEqual(len(calls),4);self.assertEqual(base.with_suffix('.bin').read_bytes(),b'exact source edge data')

if __name__=='__main__':unittest.main()
# TIMESTAMP END 2026-11-06T03:31:53+00:00 | REVISION R000085
