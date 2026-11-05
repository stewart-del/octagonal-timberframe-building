# TIMESTAMP START 2026-11-05T17:09:28+00:00 | REVISION R000057
"""Published bought-unit dimensions and conservative installed core clearance."""
from pathlib import Path
import json,sys,unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from window_assemblies import build
from audit_revised_joinery import native_solid
from audit_cavity_fit import inspect_mesh
ROOT=Path(__file__).resolve().parents[1]
class WindowAssemblies(unittest.TestCase):
 def test_published_boxes_are_real_size_and_clear_installed_primary_wood(self):
  result=build();self.assertEqual(len(result['parts']),70);units={u['unitId']:u for u in result['opening']['units']};primary=json.loads((ROOT/'src/top-entry-proposed-model.json').read_text())['parts'];wood=[(p,native_solid(p),np.asarray(p['vertices']).min(0),np.asarray(p['vertices']).max(0)) for p in primary if p.get('is_timber')];count=0
  for p in result['parts']:
   if not p.get('isPurchasedAssemblyProxy'):continue
   count+=1;u=units[p['unitId']];frame=np.asarray(u['localFrame3x4']);local=(np.asarray(p['vertices'])-frame[:,3])@frame[:,:3];size=np.ptp(local,axis=0)/.0254;self.assertTrue(np.allclose(size[:2],u['publishedFrameOverallIn'],atol=1e-10));self.assertAlmostEqual(size[2],u['publishedFrameApproxTotalDepthIn'],places=10)
   self.assertEqual(inspect_mesh(np.asarray(p['vertices']),np.asarray(p['triangles'],np.uint64),True)['status'],'PASS');solid=native_solid(p);low=np.asarray(p['vertices']).min(0);high=np.asarray(p['vertices']).max(0)
   for other,shape,olow,ohigh in wood:
    if np.min(np.minimum(high,ohigh)-np.maximum(low,olow))>1e-9:self.assertLessEqual(max(0.,float((solid^shape).volume())),1e-6*.0254**3,(p['id'],other['id']))
  self.assertEqual(count,14)
 def test_factory_references_are_never_claimed_to_be_individual_fabrication_solids(self):
  result=build();references=[p for p in result['parts'] if p.get('windowReference')];self.assertEqual(len(references),56);self.assertTrue(all(p['displayRole']=='reference' and p['isPhysicalPart'] is False and p['volumeM3']==0 for p in references));self.assertEqual(sum(p['countAsPurchasedItem'] for p in references),14);self.assertEqual(len(result['componentReferences']['components']),182)
  self.assertTrue(all(p['manufacturerMaximumAngle'] is None for p in references))
if __name__=='__main__':unittest.main()
# TIMESTAMP END 2026-11-05T17:09:28+00:00 | REVISION R000057
