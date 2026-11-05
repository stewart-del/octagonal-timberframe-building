# TIMESTAMP START 2026-11-05T16:27:06+00:00 | REVISION R000053
"""Real porch-stock containment and independently assembled interference checks."""
from pathlib import Path
import copy,json,subprocess,sys,unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from porch_roof_parts import build,load_inputs,TOL
from prepare_architecture import load_inputs as architecture_inputs
from physical_data import occupied_part
from physical_contacts import intended_penetration
from audit_revised_joinery import native_solid
from audit_cavity_fit import inspect_mesh
ROOT=Path(__file__).resolve().parents[1]
class PorchRoofParts(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.original=json.loads(subprocess.run(['node','-e',"process.stdout.write(JSON.stringify(require('./src/mudroom.js').build(require('./src/top-entry-proposed-model.json')).components));"],cwd=ROOT,check=True,capture_output=True,text=True).stdout);cls.inputs,_=load_inputs();cls.result=build(cls.original);cls.added=[occupied_part(p,{name:record.get('metal',record) for name,record in cls.result['prototypes'].items()}) for p in cls.result['parts']]
 def test_all_real_stock_and_boundaries(self):
  self.assertEqual(len(self.added),209);self.assertEqual(sum(p.get('replaceExisting',False) for p in self.added),14);self.assertEqual(len(self.result['report']['stock_checks']),39)
  for p in self.added:
   audit=inspect_mesh(np.asarray(p['vertices']),np.asarray(p['triangles'],np.uint64),True);self.assertEqual(audit['status'],'PASS',p['id'])
   if p['id'] in self.inputs['stocks']:
    self.assertLessEqual(max(0.,float((native_solid(p)-native_solid(self.inputs['stocks'][p['id']]['raw_blank'])).volume())),TOL,p['id'])
  for side in ['L','R']:
   p=next(p for p in self.added if p['id']=='MUD-PLATE-'+side);self.assertEqual(p['stockSectionIn'],[7.5,11.5]);self.assertAlmostEqual(p['stockLengthIn'],101.5)
 def test_current_combined_primary_and_retained_main_roof(self):
  arch,_=architecture_inputs();porch={p['id']:p for p in self.inputs['original_frame']['parts']};porch.update({p['id']:p for p in self.added});roof=arch['main_deck']['parts']+list(arch['main_backing']['add_parts'].values())
  for variant in ['model-data.json','step-lap-proposed-model.json','top-entry-proposed-model.json']:
   model=json.loads((ROOT/'src'/variant).read_text());primary=[p for p in model['parts'] if p.get('is_timber') or p.get('is_fastener') or p['id']=='M-TMP'];parts=primary+list(porch.values())+roof;self.assertEqual(len(parts),len({p['id'] for p in parts}));rows=[]
   for p in parts:
    v=np.asarray(p['vertices']);rows.append((p,v.min(0),v.max(0),native_solid(p)))
   pairs=0
   for k,(a,low,high,sa) in enumerate(rows):
    for b,other_low,other_high,sb in rows[k+1:]:
     if np.min(np.minimum(high,other_high)-np.maximum(low,other_low))<=1e-9:continue
     pairs+=1
     if intended_penetration(a,b) or intended_penetration(b,a):continue
     self.assertLessEqual(max(0.,float((sa^sb).volume())),TOL,(variant,a['id'],b['id']))
   self.assertGreater(pairs,3000)
 def test_later_frame_change_requires_regeneration(self):
  changed=copy.deepcopy(self.original);part=next(p for p in changed if p['id']=='MUD-POST-L-BACK');part['vertices'][0][0]+=.001
  with self.assertRaisesRegex(AssertionError,'Porch source changed'):build(changed)
if __name__=='__main__':unittest.main()
# TIMESTAMP END 2026-11-05T16:27:06+00:00 | REVISION R000053
