# TIMESTAMP START 2026-11-06T01:13:10+00:00 | REVISION R000079
"""Actual weather layers retain stock and compose four current fascia cuts."""
from pathlib import Path
import copy,json,gzip,os,sys,unittest
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from weather_seal_parts import inputs,build,compose_fascia
from closure_core_parts import inputs as core_inputs,compose_wood,native_solid,amount,diff,I,TOL
class WeatherSeals(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.data=inputs();cls.built=build(cls.data);fixture=json.loads(gzip.decompress((ROOT/'scripts/fixtures/architectural-inputs.json.gz').read_bytes()));raw=json.loads(fixture['files']['wall_wood']['content'])['add_parts'];del fixture;cls.original=compose_wood({'parts':raw},core_inputs())['parts'];cls.before=copy.deepcopy(cls.original);cls.current=compose_fascia(cls.original,cls.data);cls.parts=cls.current['parts'];cls.solids={p['id']:native_solid(p)for p in cls.built['parts']}
 def test_actual_film_counts_source_trims_and_current_negative_cuts(self):
  self.assertEqual(len(self.built['parts']),108);self.assertEqual(self.original,self.before);self.assertEqual(len(self.current['receipts']),4);self.assertFalse(self.current['oldFasciaSnapshotsSubstituted'])
  for receipt in self.current['receipts']:
   pid=receipt['id'];self.assertLessEqual(amount(native_solid(self.parts[pid])-native_solid(self.original[pid])),TOL);self.assertGreater(receipt['removedIn3'],0)
  second=compose_fascia(self.parts,self.data)
  for receipt in self.current['receipts']:
   pid=receipt['id'];self.assertLessEqual(diff(native_solid(self.parts[pid]),native_solid(second['parts'][pid])),TOL)
 def test_each_weather_layer_and_current_fascia_are_disjoint(self):
  rows=[]
  for p in self.built['parts']:
   v=np.asarray(p['vertices']);rows.append((p['id'],v.min(0),v.max(0)))
  fascia=[row['id']for row in self.current['receipts']];pairs=0
  for index,(a,low,high)in enumerate(rows):
   for b,other_low,other_high in rows[:index]:
    if np.min(np.minimum(high,other_high)-np.maximum(low,other_low))<=0:continue
    pairs+=1;self.assertLessEqual(amount(self.solids[a]^self.solids[b]),TOL,(a,b))
   for b in fascia:self.assertLessEqual(amount(self.solids[a]^native_solid(self.parts[b])),TOL,(a,b))
  self.assertGreater(pairs,50)
if __name__=='__main__':unittest.main()
# TIMESTAMP END 2026-11-06T01:13:10+00:00 | REVISION R000079
