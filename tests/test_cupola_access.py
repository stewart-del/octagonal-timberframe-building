# TIMESTAMP START 2026-11-05T14:48:08+00:00 | REVISION R000048
"""Source lineage, protected actors and real installed cupola access proofs."""
from pathlib import Path
import hashlib,json,sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from apply_cupola_access import load_inputs,merge,fingerprint
ROOT=Path(__file__).resolve().parents[1]
class CupolaAccess(unittest.TestCase):
 def test_exact_source_merge_protects_every_unmodified_actor(self):
  inputs,digest=load_inputs()
  for variant,record in inputs['variants'].items():
   raw=record['sourceModelText'].encode();before=json.loads(raw);generated=merge(raw,record,digest);actual=json.loads((ROOT/'src'/record['sourceName']).read_text())
   self.assertEqual(generated,actual);old={p['id']:p for p in before['parts']};new={p['id']:p for p in actual['parts']}
   changed={pid for pid in old if old[pid]!=new[pid]};self.assertEqual(len(changed),49)
   self.assertTrue(all(new['P'+str(k)]==old['P'+str(k)] and new['R'+str(k)]==old['R'+str(k)] for k in range(8)))
   changed_pegs=[pid for pid in changed if new[pid].get('group')=='joinery_pegs'];self.assertEqual(len(changed_pegs),24)
   self.assertTrue(all(new[pid]['axis_direction']!=old[pid]['axis_direction'] for pid in changed_pegs))
   altered=json.loads(raw);altered['parts'][0]['center'][0]+=.001
   with self.assertRaisesRegex(AssertionError,'Refusing to overwrite newer source'):merge(json.dumps(altered).encode(),record,digest)
 def test_fresh_independent_proof_matches_actual_current_models(self):
  inputs,digest=load_inputs();report=json.loads((ROOT/'docs/cupola-access-audit.json').read_text());self.assertEqual(report['status'],'PASS')
  for variant,r in report['variants'].items():
   record=inputs['variants'][variant];self.assertEqual(r['output_model_sha256'],hashlib.sha256((ROOT/'src'/record['sourceName']).read_bytes()).hexdigest());self.assertEqual(r['fixture_sha256'],digest)
   self.assertEqual(r['overlap_tolerance_m3'],1e-6*.0254**3);self.assertEqual(len(r['strict_raw_actor_ids']),49);self.assertEqual(len(r['stock']),25);self.assertEqual(len(r['protected_lower_C']),8)
   stages=r['cupola_release_stages'];self.assertEqual(len(stages),75);self.assertTrue(all(len(s['member_ids'])==1 and s['proof']['status']=='PASS' and s['proof']['parked_pieces_checked'] for s in stages))
   self.assertGreater(sum(s['proof']['triangle_prism_count'] for s in stages),0,'Actual concave swept-volume accounting must remain present')
if __name__=='__main__':unittest.main()
# TIMESTAMP END 2026-11-05T14:48:08+00:00 | REVISION R000048
