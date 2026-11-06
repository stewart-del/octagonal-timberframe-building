# TIMESTAMP START 2026-11-05T17:01:40+00:00 | REVISION R000056
"""Source-bound current primary proofs and valid-boundary rejection controls."""
from pathlib import Path
import copy,hashlib,json,sys,unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import export_top_entry_cavities as exporter
from prepare_primary_cavities import OUTPUTS,VARIANTS,method_hash
from audit_revised_joinery import native_solid
from audit_cavity_fit import inspect_mesh,arrays
ROOT=Path(__file__).resolve().parents[1]
class CurrentPrimaryCavities(unittest.TestCase):
 def test_every_proof_is_bound_to_current_source_and_original_auditor(self):
  combined=json.loads((ROOT/'docs/current-primary-cavity-generation.json').read_text());self.assertEqual(combined['status'],'PASS');self.assertEqual(len(combined['variants']),3)
  for variant,(cavity_name,report_name) in OUTPUTS.items():
   model=json.loads((ROOT/'src'/VARIANTS[variant][0]).read_text());raw=(ROOT/'src'/cavity_name).read_bytes();cav=json.loads(raw);report=json.loads((ROOT/'docs'/report_name).read_text());summary=combined['variants'][variant]
   self.assertEqual(report['status'],'PASS');self.assertEqual(len(report['members']),129);self.assertEqual(set(cav['parts']),{p['id'] for p in model['parts'] if p.get('is_timber')});self.assertEqual(report['cavity_sha256'],hashlib.sha256(raw).hexdigest());self.assertEqual(summary['cavity_sha256'],report['cavity_sha256']);self.assertEqual(summary['timbers'],129);self.assertEqual(summary['uncovered_winding_samples'],0);self.assertGreater(summary['independent_winding_samples'],50000);self.assertLessEqual(summary['maximum_member_error_m3'],1e-6*.0254**3);self.assertEqual(summary['original_audit_method_ast_sha256'],'609ef893274552613ff3542c5cd09eaa293db46587874b858066e8f5476136df')
   for relative,digest in report['sources'].items():self.assertEqual(hashlib.sha256((ROOT/relative).read_bytes()).hexdigest(),digest,relative)
 def test_actual_missing_and_shifted_pockets_are_rejected_without_invalid_meshes(self):
  original_solid=exporter.solid;original_entries=exporter.entry_regions;exporter.solid=native_solid
  try:
   proposal=json.loads((ROOT/'src/top-entry-proposal.json').read_text())
   for variant,(cavity_name,_) in OUTPUTS.items():
    model=json.loads((ROOT/'src'/VARIANTS[variant][0]).read_text());cav=json.loads((ROOT/'src'/cavity_name).read_text());entries=original_entries(proposal if variant=='top-entry' else {'representative':{'interfaces':[]}},model);exporter.entry_regions=lambda _proposal,model=None:entries
    for pid,mutation,measure in [('P0','missing','mate_pocket_omitted'),('R0','shifted','pocket_without_mate')]:
     changed=copy.deepcopy(cav['parts'][pid])
     if mutation=='missing':changed['mating_pocket']=copy.deepcopy(exporter.EMPTY)
     else:changed['mating_pocket']['vertices']=(np.asarray(changed['mating_pocket']['vertices'])+[0,.0254,0]).tolist()
     for key in ['removed','mating_pocket','entry_clearance','blank_offcuts']:
      if changed[key]['triangles']:self.assertEqual(inspect_mesh(*arrays(changed[key]))['status'],'PASS',(variant,pid,key))
     report=exporter.audit(model,{'parts':{pid:changed}},proposal);row=next(r for r in report['members'] if r['id']==pid);self.assertEqual(row['status'],'FAIL');self.assertGreater(row['errors_m3'][measure],exporter.TOL)
  finally:exporter.solid=original_solid;exporter.entry_regions=original_entries
if __name__=='__main__':unittest.main()
# TIMESTAMP END 2026-11-05T17:01:40+00:00 | REVISION R000056
