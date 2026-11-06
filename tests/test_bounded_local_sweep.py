# TIMESTAMP START 2026-11-05T19:01:25+00:00 | REVISION R000060
"""Real near-threshold collisions, retained obstacles and charged frame error."""
from pathlib import Path
from fractions import Fraction
from unittest.mock import patch
import hashlib,json,math,os,random,sys,unittest
import numpy as np
import manifold3d as m
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import plan_architectural_disassembly as planner
import bounded_local_sweep as bounded
from audit_revised_joinery import native_solid

def scene(a,b):
 parts={p:{'id':p,'is_timber':True,'material':'wood'} for p in ['moving','obstacle']}
 return planner.Scene('bounded-adversary',parts,{'moving':a,'obstacle':b},{p:np.zeros(3) for p in parts})

class BoundedSweep(unittest.TestCase):
 def test_exact_subtraction_and_budget_rejection(self):
  rng=random.Random(20261105)
  for _ in range(3000):
   a=rng.uniform(-1,1)*2.**rng.randint(-400,400);b=rng.uniform(-1,1)*2.**rng.randint(-400,400);x,error=bounded.two_diff(a,b)
   self.assertEqual(Fraction(x)+Fraction(error),Fraction(a)-Fraction(b))
  fixture=scene(m.Manifold.cube([.1]*3).translate([0,8,0]),m.Manifold.cube([.1]*3).translate([-.1,8,0]))
  clear=planner.check_stage(fixture,['moving'],[1,0,0]);self.assertEqual(clear['status'],'PASS');self.assertIn('coordinate_transform_cover_bound_m3',clear)
  with patch.object(bounded,'tube',return_value=2*bounded.TOL):
   with self.assertRaisesRegex(AssertionError,'Accumulated omitted sweep plus transform cover exceeds tolerance'):planner.check_stage(fixture,['moving'],[1,0,0])
 def test_above_threshold_intrusions_in_every_frame(self):
  for name,angle,position in [('reference',0.,[0.,8.,0.]),('translated',0.,[100.,80.,-50.]),('rotated',math.pi/4,[10.,80.,-20.]),('high-rotated',math.pi/4,[100.,1.e6,-50.])]:
   c=math.cos(angle);s=math.sin(angle);rotation=np.array([[c,0,s],[0,1,0],[-s,0,c]]);matrix=np.column_stack([rotation,np.array(position)])
   for multiple in [1.05,1.5,2.]:
    side=.01;penetration=multiple*bounded.TOL/side**2;a=m.Manifold.cube([side]*3).transform(matrix.tolist());b=m.Manifold.cube([side]*3).translate([.015,0,0]).transform(matrix.tolist());delta=rotation@np.array([.005+penetration,0,0]);trial=scene(a,b)
    result=planner.check_stage(trial,['moving'],delta);self.assertEqual(result['status'],'BLOCKED',(name,multiple));self.assertTrue(all(r['status']=='BLOCKED' for r in result.get('prior_common_frame_attempts',[])))
    origin=np.array([0.,position[1],0.]);aa,ar=bounded.local_shape(a.translate(delta.tolist()),origin);bb,br=bounded.local_shape(b,origin);actual=float((aa^bb).volume());cover=bounded.up(sum(bounded.tube(r['displacement_bound_m'],r['area_upper_m2'],r['perimeter_upper_m'],r['triangle_count']) for r in [ar,br]));self.assertGreater(actual-cover,bounded.TOL,(name,multiple))
 def test_parked_obstacle_never_disappears(self):
  trial=scene(m.Manifold.cube([.1]*3),m.Manifold.cube([.1]*3).translate([2.,0,0]));trial.offsets['obstacle']=np.array([-1.5,0.,0.])
  result=planner.check_stage(trial,['moving'],[1.,0,0]);self.assertEqual(result['status'],'BLOCKED');self.assertTrue(any(r['obstacle_parked'] for r in result['collisions']))
 def test_current_browser_core_prefix(self):
  path=os.environ.get('PARAMETRIC_CORE')
  if not path:self.skipTest('Set PARAMETRIC_CORE to an actual source-bound browser generation')
  path=Path(path);source_hash=hashlib.sha256(path.read_bytes()).hexdigest();data=json.loads(path.read_text())
  for p,expected in data['generationSources'].items():self.assertEqual(hashlib.sha256((ROOT/p).read_bytes()).hexdigest(),expected,p)
  parts={p['id']:p for p in data['model']['parts'] if p.get('triangles') and (p.get('is_timber') or p.get('is_fastener') or p['id'] in ['M-TMP','PLY'])};self.assertEqual(sum(p.get('is_timber',False) for p in parts.values()),129)
  trial=planner.Scene('current-cupola-prefix',parts,{pid:native_solid(p) for pid,p in parts.items()},{pid:np.zeros(3) for pid in parts});initial=planner.audit_initial_scene(trial);self.assertEqual(initial['status'],'PASS');stages=[];up=np.array([0.,1.,0.]);inch=.0254
  tools=['scripts/plan_architectural_disassembly.py','scripts/bounded_local_sweep.py','scripts/physical_contacts.py','tests/test_bounded_local_sweep.py'];tool_hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in tools}
  def stage(pid,delta):
   proof=planner.check_stage(trial,[pid],np.asarray(delta));self.assertEqual(proof['status'],'PASS',(pid,proof['collisions'][:2]));self.assertLess(proof['aggregate_numerical_error_bound_m3'],bounded.TOL);self.assertTrue(proof['parked_pieces_checked']);stages.append(planner.apply_stage(trial,[pid],np.asarray(delta),proof));print('checked',len(stages),pid,flush=True)
  def radial(k):return np.array([math.cos(k*math.pi/4),0.,-math.sin(k*math.pi/4)])
  for k in range(8):
   for pid in [f'CUP-PEG-CJ-C{k}-CR{k}',f'CUP-PEG-CJ-CR{k}-CUP-KINGPOST']:stage(pid,np.asarray(parts[pid]['withdrawal_direction'])*1.5)
  for k in range(8):stage(f'CR{k}',up*3.025*inch);stage(f'CR{k}',radial(k)*5.)
  stage('PLY',up*.8);stage('PLY',[2.5,0,0])
  for k in range(8):
   for pid in [f'CUP-PEG-CJ-CC{k}-CUP-KINGPOST',f'CUP-PEG-CJ-CC{k}-C{k}']:stage(pid,np.asarray(parts[pid]['withdrawal_direction'])*1.5)
  stage('CUP-KINGPOST',up*.6)
  for k in range(8):stage(f'CC{k}',-radial(k)*3.025*inch);stage(f'CC{k}',up*.35);stage(f'CC{k}',radial(k)*3.)
  self.assertEqual(len(stages),75);self.assertEqual(len({p for r in stages for p in r['member_ids']}),50);self.assertEqual(set(trial.parts),set(parts));self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),source_hash)
  for p,expected in tool_hashes.items():self.assertEqual(hashlib.sha256((ROOT/p).read_bytes()).hexdigest(),expected,p)
  output=os.environ.get('BOUNDED_CORE_REPORT')
  if output:Path(output).write_text(json.dumps({'status':'PASS_PREFIX','scope':'129-timber primary core only; replaced historical PLY retained for this bounded recipe. Real ceiling, weather, architectural products and compact parking need their own full route.','source_geometry_sha256':source_hash,'parameters':data['config'],'tools':tool_hashes,'initial':initial,'stages':stages,'parked_pieces_retained':True,'full_building_route_verified':False},indent=2)+'\n')

if __name__=='__main__':unittest.main()
# TIMESTAMP END 2026-11-05T19:01:25+00:00 | REVISION R000060
