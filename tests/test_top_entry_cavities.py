# TIMESTAMP START 2026-11-02T17:13:18-05:00 | REVISION R004819
"""Readback, regeneration and deliberate bad-fit checks for active cavities."""
from pathlib import Path
import copy,hashlib,json,sys,unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from export_top_entry_cavities import ROOT,read,generate,audit,unpack,volume,TOL

class TopEntryCavities(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model=read(ROOT/'src/top-entry-proposed-model.json')
        cls.proposal=read(ROOT/'src/top-entry-proposal.json')
        cls.cavities=read(ROOT/'src/top-entry-proposed-cavities.json')

    def test_exported_fit_and_source_binding(self):
        saved=read(ROOT/'docs/top-entry-cavity-fit-audit.json')
        self.assertEqual(saved['status'],'PASS')
        self.assertTrue(self.cavities['available'])
        self.assertEqual(self.cavities['source_model_sha256'],hashlib.sha256((ROOT/'src/top-entry-proposed-model.json').read_bytes()).hexdigest())
        self.assertEqual(self.cavities['sources'],saved['sources'])
        self.assertEqual(saved['cavity_sha256'],hashlib.sha256((ROOT/'src/top-entry-proposed-cavities.json').read_bytes()).hexdigest())
        for path,digest in saved['sources'].items():
            self.assertEqual(digest,hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),path)
        report=audit(self.model,self.cavities,self.proposal)
        self.assertEqual(report['status'],'PASS',report['failures'])
        self.assertEqual(report['summary']['structural_timbers'],112)
        self.assertEqual(report['summary']['physical_wooden_pegs'],56)
        self.assertEqual(report['summary']['open_entry_records'],8)
        self.assertEqual(report['summary']['explicit_exterior_offcut_records'],24)
        self.assertEqual(report['summary']['uncovered_winding_samples'],0)

    def test_regeneration_preserves_each_occupied_region(self):
        generated=generate(self.model,self.proposal)
        for pid,record in self.cavities['parts'].items():
            for key in ['removed','mating_pocket','entry_clearance','blank_offcuts']:
                a,b=unpack(record[key]),unpack(generated['parts'][pid][key])
                self.assertLessEqual(volume(a-b)+volume(b-a),TOL,(pid,key))

    def test_undersized_void_is_rejected(self):
        changed=copy.deepcopy(self.cavities)
        for key in ['removed','mating_pocket']:
            record=changed['parts']['C0'][key]
            vertices=np.asarray(record['vertices']);center=vertices.mean(0)
            record['vertices']=(center+.95*(vertices-center)).tolist()
        report=audit(self.model,changed,self.proposal)
        self.assertEqual(report['status'],'FAIL')
        self.assertTrue(any(name.startswith('C0:') for name in report['failures']))

    def test_entry_space_cannot_be_claimed_as_a_filled_pocket(self):
        changed=copy.deepcopy(self.cavities)
        changed['parts']['R0']['mating_pocket']=copy.deepcopy(changed['parts']['R0']['removed'])
        report=audit(self.model,changed,self.proposal)
        self.assertEqual(report['status'],'FAIL')
        self.assertTrue(any(name.startswith('R0:') for name in report['failures']))

    def test_exterior_shoulder_offcut_cannot_be_claimed_as_a_pocket(self):
        changed=copy.deepcopy(self.cavities)
        for key in ['removed','mating_pocket']:
            changed['parts']['K0-A'][key]=copy.deepcopy(changed['parts']['K0-A']['blank_offcuts'])
        report=audit(self.model,changed,self.proposal)
        self.assertEqual(report['status'],'FAIL')
        self.assertTrue(any(name.startswith('K0-A:') for name in report['failures']))

if __name__=='__main__':unittest.main()
# TIMESTAMP END 2026-11-02T17:13:18-05:00 | REVISION R004819
