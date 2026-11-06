# TIMESTAMP START 2026-11-02T17:13:18-05:00 | REVISION R004819
"""Readback, regeneration and deliberate bad-fit checks for active cavities."""
from pathlib import Path
import copy,hashlib,json,sys,unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
# TIMESTAMP START 2026-11-03T17:08:46-05:00 | REVISION R005066
from test_revised_cavities import ROOT,read,verify_saved,audit_current
# TIMESTAMP END 2026-11-03T17:08:46-05:00 | REVISION R005066

class TopEntryCavities(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model=read(ROOT/'src/top-entry-proposed-model.json')
        cls.proposal=read(ROOT/'src/top-entry-proposal.json')
        cls.cavities=read(ROOT/'src/top-entry-proposed-cavities.json')

    # TIMESTAMP START 2026-11-03T17:08:46-05:00 | REVISION R005066
    def test_exported_fit_and_source_binding(self):
        report=verify_saved('top-entry')
        self.assertEqual(report['summary']['structural_timbers'],112)
        self.assertEqual(report['summary']['physical_wooden_pegs'],56)
        # TIMESTAMP START 2026-11-05T01:29:35+00:00 | REVISION R000016
        self.assertEqual(report['summary']['open_entry_records'],32)
        # TIMESTAMP END 2026-11-05T01:29:35+00:00 | REVISION R000016
        self.assertEqual(report['summary']['explicit_exterior_offcut_records'],80)
        self.assertEqual(report['summary']['uncovered_winding_samples'],0)
    # TIMESTAMP END 2026-11-03T17:08:46-05:00 | REVISION R005066

    def test_undersized_void_is_rejected(self):
        changed=copy.deepcopy(self.cavities)
        for key in ['removed','mating_pocket']:
            record=changed['parts']['C0'][key]
            vertices=np.asarray(record['vertices']);center=vertices.mean(0)
            record['vertices']=(center+.95*(vertices-center)).tolist()
        # TIMESTAMP START 2026-11-03T17:08:46-05:00 | REVISION R005066
        report=audit_current('top-entry',changed,only={'C0'})
        # TIMESTAMP END 2026-11-03T17:08:46-05:00 | REVISION R005066
        self.assertEqual(report['status'],'FAIL')
        self.assertTrue(any(name.startswith('C0:') for name in report['failures']))

    def test_entry_space_cannot_be_claimed_as_a_filled_pocket(self):
        changed=copy.deepcopy(self.cavities)
        changed['parts']['R0']['mating_pocket']=copy.deepcopy(changed['parts']['R0']['removed'])
        # TIMESTAMP START 2026-11-03T17:08:46-05:00 | REVISION R005066
        report=audit_current('top-entry',changed,only={'R0'})
        # TIMESTAMP END 2026-11-03T17:08:46-05:00 | REVISION R005066
        self.assertEqual(report['status'],'FAIL')
        self.assertTrue(any(name.startswith('R0:') for name in report['failures']))

    def test_exterior_shoulder_offcut_cannot_be_claimed_as_a_pocket(self):
        changed=copy.deepcopy(self.cavities)
        for key in ['removed','mating_pocket']:
            changed['parts']['K0-A'][key]=copy.deepcopy(changed['parts']['K0-A']['blank_offcuts'])
        # TIMESTAMP START 2026-11-03T17:08:46-05:00 | REVISION R005066
        report=audit_current('top-entry',changed,only={'K0-A'})
        # TIMESTAMP END 2026-11-03T17:08:46-05:00 | REVISION R005066
        self.assertEqual(report['status'],'FAIL')
        self.assertTrue(any(name.startswith('K0-A:') for name in report['failures']))

if __name__=='__main__':unittest.main()
# TIMESTAMP END 2026-11-02T17:13:18-05:00 | REVISION R004819
