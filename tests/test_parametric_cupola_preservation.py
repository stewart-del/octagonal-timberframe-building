# TIMESTAMP START 2026-11-05T19:36:48+00:00 | REVISION R000062
"""Independent preservation of lower cupola posts, fixed sections and peg axes."""
from pathlib import Path
import hashlib,json,os,sys,unittest
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from audit_revised_joinery import native_solid
import bounded_local_sweep as bounded
I=.0254;TOL=1e-6*I**3
class CupolaPreservation(unittest.TestCase):
 def test_actual_cupola_only_regeneration_preserves_lower_posts_and_stock(self):
  path=os.environ.get('PARAMETRIC_CORE')
  if not path:self.skipTest('Set PARAMETRIC_CORE to a fresh4:12/defaultwall cupola-height generation')
  data=json.loads(Path(path).read_text());self.assertTrue(data['mainCoreRetained']);self.assertEqual(data['config']['pitch'],4)
  for p,expected in data['generationSources'].items():self.assertEqual(hashlib.sha256((ROOT/p).read_bytes()).hexdigest(),expected,p)
  before=json.loads((ROOT/'src/top-entry-proposed-model.json').read_text());source={p['id']:p for p in before['parts']};parts={p['id']:p for p in data['model']['parts']};origin=np.array([0.,3.,0.]);rows=[]
  def local(part):return bounded.local_shape(native_solid(part),origin)
  def cover(reports):return sum(bounded.tube(r['displacement_bound_m'],r['area_upper_m2'],r['perimeter_upper_m'],r['triangle_count']) for r in reports)
  for row in data['cupolaResearch']['preserved_lower_C']:
   pid=row['id'];a,aa=local(source[pid]);b,ba=local(parts[pid]);limit=row['elevation_in']*I-origin[1];a=a.trim_by_plane([0,-1,0],-limit);b=b.trim_by_plane([0,-1,0],-limit);difference=max(0.,float((a-b).volume()))+max(0.,float((b-a).volume()));bound=cover([aa,ba]);self.assertLessEqual(difference+bound,TOL,pid);rows.append({'id':pid,'native_lower_difference_m3':difference,'transform_cover_bound_m3':bound})
  self.assertEqual(len(rows),8)
  maximum_axis_roundoff=0.
  for pid in data['cupolaResearch']['new_access_peg_ids']:
   for key in ['axis_direction','withdrawal_direction']:
    # Python canonical export and JS regeneration may differ by a few IEEE754
    # units. This bound concerns direction serialization, never solid overlap.
    error=float(np.max(abs(np.asarray(parts[pid][key])-np.asarray(source[pid][key]))));maximum_axis_roundoff=max(maximum_axis_roundoff,error);self.assertLessEqual(error,8*np.finfo(float).eps,(pid,key))
  self.assertEqual(len(data['cupolaResearch']['new_access_peg_ids']),24)
  for pid,stock in data['cupolaStocks'].items():
   section=[6,6] if pid.startswith('C') and pid[1:].isdigit() else [4,6] if pid.startswith('CC') else [2,6] if pid.startswith('CR') else [12,12];self.assertEqual(stock['section_in'],section,pid);part,pa=local(parts[pid]);blank,ba=local(stock['blank']);self.assertLessEqual(max(0.,float((part-blank).volume()))+cover([pa,ba]),TOL,pid)
  self.assertEqual(len(data['cupolaStocks']),25)
  report=os.environ.get('CUPOLA_PRESERVATION_REPORT')
  if report:Path(report).write_text(json.dumps({'status':'PASS','source_geometry_sha256':hashlib.sha256(Path(path).read_bytes()).hexdigest(),'generation_sources':data['generationSources'],'lower_C':rows,'stock_count':25,'upper_axes_checked':24,'maximum_axis_component_roundoff':maximum_axis_roundoff,'axis_roundoff_limit':8*np.finfo(float).eps,'overlap_tolerance_m3':TOL},indent=2)+'\n')
if __name__=='__main__':unittest.main()
# TIMESTAMP END 2026-11-05T19:36:48+00:00 | REVISION R000062
