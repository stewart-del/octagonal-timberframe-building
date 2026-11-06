# TIMESTAMP START 2026-11-05T08:15:49+00:00 | REVISION R000034
"""Check preserved real collars, roof extents and actual added bearing pieces."""
import gzip,json,math,sys,unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from audit_revised_joinery import native_solid
from hip_backing_recipe import contacts
I=.0254;TOL=1e-6*I**3;ROOT=Path(__file__).resolve().parents[1]
class RoofStructure(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.frozen=json.loads(gzip.decompress((ROOT/'scripts/fixtures/roof-structure-inputs.json.gz').read_bytes()))['files']
 def test_actual_preserved_collars_eaves_and_bearings(self):
  for name in ['model-data.json','step-lap-proposed-model.json','top-entry-proposed-model.json']:
   with self.subTest(variant=name):
    old={p['id']:p for p in json.loads(self.frozen[name]['content'])['parts']};current=json.loads((ROOT/'src'/name).read_text());parts={p['id']:p for p in current['parts']};self.assertEqual(sum(bool(p.get('is_timber')) for p in parts.values()),129)
    new=[p for p in parts.values() if '-OUT' in p['id']];self.assertEqual(len(new),16)
    for k in range(8):
     pid='R'+str(k);r=np.array([math.cos(k*math.pi/4),0,-math.sin(k*math.pi/4)]);before=native_solid(old[pid]).trim_by_plane((-r).tolist(),-45*I);after=native_solid(parts[pid]).trim_by_plane((-r).tolist(),-45*I)
     self.assertLessEqual(abs((before-after).volume())+abs((after-before).volume()),TOL)
     for half in [-.5,.5]:
      angle=(k+half)*math.pi/4;n=np.array([math.cos(angle),0,-math.sin(angle)]);self.assertLessEqual(float(np.max(np.asarray(parts[pid]['vertices'])@n)),200*I*math.cos(math.pi/8)+1e-8)
     for side in ['0','2']:self.assertEqual(parts['J'+str(k)+'-'+side]['vertices'],old['J'+str(k)+'-'+side]['vertices'])
    for p in new:
     joint=next(j for j in current['tenon_schedule'] if j['donor']==p['id'] and j['receiver'].startswith('R'))
     area=sum(q['area_in2'] for q in contacts(native_solid(p),native_solid(parts[joint['receiver']])))
     self.assertGreater(area,1.)
if __name__=='__main__':unittest.main()
# TIMESTAMP END 2026-11-05T08:15:49+00:00 | REVISION R000034
