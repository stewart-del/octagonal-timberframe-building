# TIMESTAMP START 2026-11-03T17:08:46-05:00 | REVISION R005066
"""Reject stale or incomplete revised perimeter cavities."""
import copy,unittest
from test_revised_cavities import ROOT,read,verify_saved,audit_current
class ProposedCavityFixtures(unittest.TestCase):
    def test_current_source_binding(self):
        report=verify_saved('proposed')
        self.assertEqual(report['summary']['structural_timbers'],112)
        self.assertEqual(report['summary']['physical_wooden_pegs'],48)
    def test_omitted_perimeter_pocket_is_rejected(self):
        cavities=read(ROOT/'src/step-lap-proposed-cavities.json')
        for key in ['removed','mating_pocket']:
            cavities['parts']['B0'][key]={'vertices':[],'triangles':[],'edges':[],'volume_m3':0}
        result=audit_current('proposed',cavities,only={'B0'})
        self.assertEqual(result['status'],'FAIL')
        self.assertTrue(any(s.startswith('B0:') for s in result['failures']))
if __name__=='__main__':unittest.main()
# TIMESTAMP END 2026-11-03T17:08:46-05:00 | REVISION R005066
