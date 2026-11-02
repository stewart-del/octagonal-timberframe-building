# TIMESTAMP START 2026-11-02T10:08:45-05:00 | REVISION R004761
"""Verify proposed cavity changes against authoritative material-transfer masks."""
from pathlib import Path
import copy
import hashlib
import json
import sys
import unittest

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import audit_cavity_fit as audit
import export_step_lap_cavities as exporter


class ProposedCavityFixtures(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        paths = ['src/model-data.json', 'src/cavity-data.json',
                 'src/step-lap-proposed-model.json', 'src/step-lap-proposal.json']
        loaded = [exporter.read_json(ROOT / path) for path in paths]
        cls.baseline, cls.base_cavities, cls.proposed, cls.proposal = [item[0] for item in loaded]
        cls.hashes = tuple(item[1] for item in loaded)
        cls.cavities = json.loads((ROOT / 'src/step-lap-proposed-cavities.json').read_text())
        cls.baseline_parts = {part['id']: part for part in cls.baseline['parts'] if part['is_timber']}
        cls.proposed_parts = {part['id']: part for part in cls.proposed['parts'] if part['is_timber']}

    def test_generation_is_deterministic_and_preserves_unchanged_cavities(self):
        rebuilt = exporter.build_cavities(self.baseline, self.base_cavities, self.proposed, self.proposal, self.hashes)
        self.assertEqual(rebuilt, self.cavities)
        changed = set(self.proposed['proposed_review']['changed_member_ids'])
        self.assertEqual(len(changed), 40)
        for name in self.baseline_parts:
            if name not in changed:
                self.assertEqual(self.cavities['parts'][name]['removed'], self.base_cavities['parts'][name]['removed'])
        self.assertTrue(self.cavities['available'])
        self.assertEqual(len(self.cavities['parts']), 104)
        self.assertTrue(all(set(row) == {'removed'} for row in self.cavities['parts'].values()))

    def test_each_transfer_switches_actual_wood_and_cavity_ownership(self):
        for transfer in self.proposal['variants']:
            owner, receiver = transfer['member_ids']
            point = np.asarray(transfer['added_parts'][0]['vertices']).mean(axis=0)[None]
            for name, inside_after, cavity_after in ((owner, True, False), (receiver, False, True)):
                vertices, faces = audit.arrays(self.proposed_parts[name])
                inside = audit.winding(point, vertices[faces])[0]
                self.assertEqual(inside > .999, inside_after, (transfer['id'], name, 'proposed wood'))
                vertices, faces = audit.arrays(self.cavities['parts'][name]['removed'])
                in_cavity = audit.winding(point, vertices[faces])[0]
                self.assertEqual(in_cavity > .999, cavity_after, (transfer['id'], name, 'proposed cavity'))
                vertices, faces = audit.arrays(self.base_cavities['parts'][name]['removed'])
                old_cavity = audit.winding(point, vertices[faces])[0]
                self.assertEqual(old_cavity > .999, not cavity_after, (transfer['id'], name, 'baseline cavity'))

    def test_all_transfers_conserve_the_sum_of_removed_stock(self):
        before = sum(row['removed']['volume_m3'] for row in self.base_cavities['parts'].values())
        after = sum(row['removed']['volume_m3'] for row in self.cavities['parts'].values())
        self.assertLess(abs(after - before) / audit.INCH ** 3, 1e-6)
        self.assertEqual(self.cavities['transfer_count'], 24)
        self.assertEqual(len(self.cavities['member_volume_balances']), 40)
        self.assertTrue(all(row['balance_error_in3'] <= 1e-6 for row in self.cavities['member_volume_balances']))

    def test_mismatched_transfer_masks_are_rejected(self):
        corrupt = copy.deepcopy(self.proposal)
        corrupt['variants'][0]['removed_parts'][0]['vertices'][0][0] += .001
        with self.assertRaises(AssertionError):
            exporter.build_cavities(self.baseline, self.base_cavities, self.proposed, corrupt, self.hashes)

    def test_stale_baseline_source_is_rejected(self):
        bad_hashes = ('wrong-baseline',) + self.hashes[1:]
        with self.assertRaises(AssertionError):
            exporter.build_cavities(self.baseline, self.base_cavities, self.proposed, self.proposal, bad_hashes)

    def test_independent_proposed_audit_covers_actual_stock_and_concave_recesses(self):
        # TIMESTAMP START 2026-11-02T10:21:34-05:00 | REVISION R004762
        report = json.loads((ROOT / 'docs/step-lap-proposed-cavity-fit-audit.json').read_text())
        # TIMESTAMP END 2026-11-02T10:21:34-05:00 | REVISION R004762
        self.assertEqual(report['status'], 'PASS')
        self.assertEqual(report['model_variant'], 'proposed-step-lap')
        self.assertEqual(report['model_sha256'], self.hashes[2])
        self.assertEqual(report['cavity_sha256'], hashlib.sha256((ROOT / 'src/step-lap-proposed-cavities.json').read_bytes()).hexdigest())
        self.assertEqual(report['summary']['connected_cavity_components'], 168)
        self.assertEqual(report['summary']['nonconvex_cavity_components'], 24)
        self.assertEqual(report['summary']['components_covered'], 168)
        self.assertEqual(report['summary']['all_timber_stock_envelopes_verified'], 104)
        self.assertEqual(report['summary']['winding_unoccupied_points'], 0)
        self.assertEqual(report['summary']['winding_points_in_receiver'], 0)


if __name__ == '__main__':
    unittest.main()
# TIMESTAMP END 2026-11-02T10:08:45-05:00 | REVISION R004761
