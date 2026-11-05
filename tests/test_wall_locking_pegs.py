# TIMESTAMP START 2026-11-05T08:46:05+00:00 | REVISION R000036
"""Actual transverse pin fit and moved-live-recipient adversary."""
# TIMESTAMP START 2026-11-05T12:57:30+00:00 | REVISION R000042
import copy,gzip,json,sys,unittest
# TIMESTAMP END 2026-11-05T12:57:30+00:00 | REVISION R000042
from pathlib import Path
from unittest.mock import patch
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import wall_locking_pegs as W
from audit_revised_joinery import native_solid
ROOT=Path(__file__).resolve().parents[1]
class WallLockingPegs(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  all_design=W.load('top-entry');row=all_design['joint_mapping'][0];cls.row=row;pid=row['id']
  cls.design={**all_design,'joint_mapping':[row],'pegs':[x for x in all_design['pegs'] if x['id']==pid],'bore_tools':[x for x in all_design['bore_tools'] if x['id']==pid]}
# TIMESTAMP START 2026-11-05T12:57:30+00:00 | REVISION R000042
  fixture=json.loads(gzip.decompress((ROOT/'tests/fixtures/wall-locking-prebore.json.gz').read_bytes()));assert fixture['joint']['id']==row['joint'];cls.original={x:native_solid(fixture['parts'][x]) for x in [row['donor'],row['receiver']]};cls.joint=fixture['joint']
# TIMESTAMP END 2026-11-05T12:57:30+00:00 | REVISION R000042
 def test_pin_requires_real_matching_bores(self):
  live=dict(self.original);pin=native_solid(self.design['pegs'][0]);self.assertGreater((pin^live[self.row['donor']]).volume(),W.TOL)
  with patch.object(W,'load',return_value=self.design):pegs,owners,proof=W.attach('top-entry',live,[self.joint])
  self.assertEqual(proof['status'],'PASS');self.assertEqual(len(pegs),1)
  for pid in live:
   self.assertIn(pegs[0]['id'],owners[pid]);self.assertLessEqual((pin^live[pid]).volume(),W.TOL);self.assertGreater((self.original[pid]-live[pid]).volume(),W.TOL)
 def test_moved_actual_recipients_rejected(self):
  live={pid:s.translate([.5,.5,.5]) for pid,s in self.original.items()}
  with patch.object(W,'load',return_value=self.design):
   with self.assertRaisesRegex(AssertionError,'current mating wood'):W.attach('top-entry',live,[self.joint])
if __name__=='__main__':unittest.main()
# TIMESTAMP END 2026-11-05T08:46:05+00:00 | REVISION R000036
