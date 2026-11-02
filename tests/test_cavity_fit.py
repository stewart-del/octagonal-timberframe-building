# TIMESTAMP START 2026-11-02T09:09:22-05:00 | REVISION R004752
"""Adversarial geometric fixtures for the independent cavity-fit audit."""
from pathlib import Path
import hashlib
import json
import sys
import unittest

import manifold3d as m
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import audit_cavity_fit as audit


def mesh(manifold):
    result = manifold.to_mesh64()
    return np.asarray(result.vert_properties)[:, :3], np.asarray(result.tri_verts, dtype=np.uint64)


def box(low, high):
    return m.Manifold.cube(tuple(np.asarray(high) - low)).translate(tuple(low))


def receiver_part(wood):
    vertices, faces = mesh(wood)
    planes = []
    for axis in range(3):
        for sign, constant in ((1, 1), (-1, 0)):
            normal = np.eye(3)[axis] * sign
            planes.append({'normal': [float(normal[0]), float(-normal[2]), float(normal[1])],
                           'constant': constant / audit.INCH})
    return {'vertices': vertices.tolist(), 'triangles': faces.tolist(), 'geometry_planes_inches': planes}


def mesh_record(shape):
    vertices, faces = mesh(shape)
    return {'vertices': vertices.tolist(), 'triangles': faces.tolist()}


# Exact lower C0 cavity surface from c9394c4f181d7e9073473af652256afd9e4c72e5.
# It includes an unphysical zero-volume sheet and a wedge extending into wood.
# Keeping this compact fixture independent of Git history makes shallow CI clones safe.
LEGACY_C0_VERTICES = np.array([
    [1.0668, 2.1844, -.025399999999999867],
    [1.0668, 2.3875999999999995, -.025399999999999867],
    [1.1176, 2.159, -.07619999999999999],
    [1.1176, 2.413, -.07619999999999999],
    [1.1176, 2.1844, -.025399999999999867],
    [1.1176, 2.1844, -.025399999999999867],
    [1.1176, 2.3875999999999995, -.025399999999999867],
    [1.1176, 2.3875999999999995, -.025399999999999867],
    [1.0668, 2.1844, .025399999999999867],
    [1.0668, 2.3875999999999995, .025399999999999867],
    [1.1176, 2.159, 0],
    [1.1176, 2.1743397485964837, .014841005614065858],
    [1.1176, 2.1844, .025399999999999867],
    [1.1176, 2.3875999999999995, .025399999999999867],
])
LEGACY_C0_FACES = np.array([
    [2, 6, 3], [2, 4, 6], [2, 3, 4], [3, 6, 4], [5, 11, 10],
    [5, 7, 13], [5, 12, 11], [5, 13, 12], [0, 8, 1], [0, 1, 7],
    [0, 5, 8], [0, 7, 5], [1, 13, 7], [1, 8, 9], [1, 9, 13],
    [8, 12, 9], [5, 10, 8], [8, 10, 11], [8, 11, 12], [9, 12, 13],
], dtype=np.uint64)


class CavityFitFixtures(unittest.TestCase):
    # TIMESTAMP START 2026-11-02T10:34:57-05:00 | REVISION R004764
    def test_slender_partition_uses_physical_halfspaces_and_volume(self):
        # Real C0 verification cell: independently orienting Qhull facets can
        # produce a closed triangulation with a 0.64% volume error on these points.
        # A constructed convex cell is proved from its halfspaces and volume.
        vertices = np.array([
            [.9652, 2.3876, -.03386666666667], [.9652, 2.3876, -.03262300052545],
            [.9652, 2.3876, -.0254], [.9652, 3.35623487714023, -.0254],
            [.9652, 3.60817395085609, -.03386666666667],
            [.9652, 3.60817395085609, -.02608295934744], [.9652, 3.60817395085609, -.0254],
            [.97798235339756, 3.60391316639024, -.0254],
            [.98758599054192, 2.3876, -.03386666666667],
            [1.00904345942935, 2.3876, -.03386666666667],
            [1.00904345942935, 3.0374121874703, -.03386666666667],
            [1.00904345942935, 3.59355946437964, -.03386666666667],
            [1.00986988927466, 3.59328398776454, -.03187148852577],
            [1.01057473124192, 2.3876, -.03016984948906],
            [1.01143002488457, 3.59276394256124, -.02810498797719],
            [1.01158577846137, 3.59271202470231, -.02772896557969],
            [1.01255046759077, 2.3876, -.0254], [1.01255046759077, 3.0139357982575, -.0254],
            [1.01255046759077, 3.59239046165917, -.0254],
        ])
        hull = audit.ConvexHull(vertices)
        self.assertAlmostEqual(hull.volume, .00046827254775351, delta=1e-14)
        self.assertLessEqual(np.max(vertices @ hull.equations[:, :3].T + hull.equations[:, 3]), 1e-12)
        mate_v, mate_f = mesh(box((.9, 2, -.1), (1.1, 3.7, .1)))
        result = audit.convex_cell_coverage(vertices, hull, {'mate': mate_v[mate_f]})
        self.assertEqual(result['status'], 'PASS')
        self.assertAlmostEqual(result['volume_in3'] * audit.INCH ** 3, .00046827254775351, delta=1e-14)

    def test_historical_b0_opposed_surface_patch_is_rejected(self):
        # Raw triangles 44/97 from proposed model at commit 890b4eb. Solid
        # occupancy/volume checks missed their coincident backtracking patch.
        vertices = np.array([
            [3.6704586658332827, 2.4647182428390497, -2.130349413895276],
            [4.101790729537779, 2.4647182428390497, -1.0890216958135053],
            [3.657498453590519, 2.4393182428390494, -2.1616381340629918],
            [3.6704586658332827, 2.4393182428390494, -2.130349413895276],
            [3.6704586658332827, 2.4647182428390497, -2.130349413895276],
            [3.657498453590519, 2.4393182428390494, -2.1616381340629918],
        ])
        result = audit.coplanar_surface_overlaps(vertices, np.array([[0, 1, 2], [3, 4, 5]]))
        self.assertEqual(result['status'], 'FAIL')
        self.assertEqual(result['opposed_overlap_pair_count'], 1)
        self.assertAlmostEqual(result['sum_pair_overlap_area_m2'] / audit.INCH ** 2, .6472196900636814, places=9)

    def test_coplanar_shared_edges_and_separated_parallel_faces_are_allowed(self):
        vertices = np.array([[0., 0, 0], [1., 0, 0], [0., 1, 0], [1., 1, 0]])
        faces = np.array([[0, 1, 2], [1, 2, 3]])
        self.assertEqual(audit.coplanar_surface_overlaps(vertices, faces)['status'], 'PASS')
        separated = np.vstack([vertices[:3], vertices[:3] + [0, 0, 1e-5]])
        self.assertEqual(audit.coplanar_surface_overlaps(separated, np.array([[0, 1, 2], [5, 4, 3]]))['status'], 'PASS')

    def test_coincident_same_facing_duplicate_patch_is_also_rejected(self):
        vertices = np.array([[0., 0, 0], [1., 0, 0], [0., 1, 0], [.1, .1, 0], [.5, .1, 0], [.1, .5, 0]])
        result = audit.coplanar_surface_overlaps(vertices, np.array([[0, 1, 2], [3, 4, 5]]))
        self.assertEqual(result['status'], 'FAIL')
        self.assertEqual(result['opposed_overlap_pair_count'], 0)
        self.assertEqual(result['overlap_pairs'][0]['orientation'], 'same-facing')

    def test_mesh_gate_rejects_hidden_opposed_partition_with_correct_volume(self):
        av, af = mesh(box((0, 0, 0), (.5, 1, 1)))
        bv, bf = mesh(box((.5, 0, 0), (1, 1, 1)))
        vertices = np.vstack([av, bv])
        faces = np.vstack([af, bf + len(av)])
        self.assertAlmostEqual(audit.signed_volume(vertices, faces), 1)
        result = audit.inspect_mesh(vertices, faces)
        self.assertEqual(result['status'], 'FAIL')
        self.assertIn('positive-area coplanar raw triangle overlap', result['failures'])
        self.assertGreater(result['raw_surface_check']['opposed_overlap_pair_count'], 0)
    # TIMESTAMP END 2026-11-02T10:34:57-05:00 | REVISION R004764

    # TIMESTAMP START 2026-11-02T10:08:45-05:00 | REVISION R004761
    def test_concave_recess_is_partitioned_without_filling_its_notch(self):
        recess = box((0, 0, 0), (1, 1, 1)) - box((.5, .5, 0), (1, 1, 1))
        vertices, faces = mesh(recess)
        result = audit.component_coverage(vertices, faces, {'mate': vertices[faces]})
        self.assertEqual(result['status'], 'PASS')
        self.assertEqual(result['coverage_mode'], 'nonconvex surface partition')
        self.assertGreater(result['excluded_hull_cells'], 0)
        self.assertLessEqual(result['partition_volume_balance_error_m3'], audit.VOLUME_TOLERANCE_M3)
        incomplete_v, incomplete_f = mesh(box((0, 0, 0), (1, .5, 1)))
        missing = audit.component_coverage(vertices, faces, {'mate': incomplete_v[incomplete_f]})
        self.assertEqual(missing['status'], 'FAIL')
    # TIMESTAMP END 2026-11-02T10:08:45-05:00 | REVISION R004761

    def test_exact_complement_is_contained(self):
        vertices, faces = mesh(box((0, 0, 0), (1, 1, 1)))
        result = audit.component_coverage(vertices, faces, {'mate': vertices[faces]})
        self.assertEqual(result['status'], 'PASS')
        self.assertEqual(result['mate'], 'mate')

    def test_shared_cavity_requires_and_passes_explicit_partition(self):
        vertices, faces = mesh(box((0, 0, 0), (1, 1, 1)))
        left_v, left_f = mesh(box((0, 0, 0), (.5, 1, 1)))
        right_v, right_f = mesh(box((.5, 0, 0), (1, 1, 1)))
        result = audit.component_coverage(vertices, faces,
                                         {'left': left_v[left_f], 'right': right_v[right_f]})
        self.assertEqual(result['status'], 'PASS')
        self.assertEqual(result['partition_cells'], 2)
        self.assertEqual({cell['mate'] for cell in result['cells']}, {'left', 'right'})

    def test_thin_real_gap_fails_containment(self):
        vertices, faces = mesh(box((0, 0, 0), (1, 1, 1)))
        left_v, left_f = mesh(box((0, 0, 0), (.499998, 1, 1)))
        right_v, right_f = mesh(box((.500002, 0, 0), (1, 1, 1)))
        result = audit.component_coverage(vertices, faces,
                                         {'left': left_v[left_f], 'right': right_v[right_f]})
        self.assertEqual(result['status'], 'FAIL')

    def test_concealed_hole_fails_even_with_centroid_in_wood(self):
        cavity = box((0, 0, 0), (1, 1, 1))
        vertices, faces = mesh(cavity)
        mate_v, mate_f = mesh(cavity - box((.1, .1, .1), (.2, .2, .2)))
        self.assertGreater(audit.winding(np.array([[.5, .5, .5]]), mate_v[mate_f])[0], .999)
        result = audit.component_coverage(vertices, faces, {'mate': mate_v[mate_f]})
        self.assertEqual(result['status'], 'FAIL')

    def test_receiver_intrusion_fails_independent_sections(self):
        vertices, faces = mesh(box((0, 0, 0), (1, 1, 1)))
        receiver = mesh(box((-.5, 0, 0), (.1, 1, 1)))
        result = audit.cavity_sections('fixture', vertices, faces,
                                      {'fixture': receiver, 'mate': (vertices, faces)})
        self.assertEqual(result['status'], 'FAIL')
        self.assertGreater(result['max_receiver_overlap_area_m2'], .09)

    def test_real_wood_overlap_fails_sectional_check(self):
        result = audit.wood_pair_sections({'a': mesh(box((0, 0, 0), (1, 1, 1))),
                                          'b': mesh(box((.999, 0, 0), (2, 1, 1)))})
        self.assertEqual(result['status'], 'FAIL')
        self.assertGreater(result['max_overlap_area_m2'], .0009)

    def test_stock_completeness_rejects_undersized_exported_cavity(self):
        stock = box((0, 0, 0), (1, 1, 1))
        actual_socket = box((.5, .25, .25), (1, .75, .75))
        receiver = receiver_part(stock - actual_socket)
        complete = audit.stock_completeness(receiver, mesh_record(actual_socket))
        self.assertEqual(complete['status'], 'PASS')
        undersized = box((.75, .25, .25), (1, .75, .75))
        result = audit.stock_completeness(receiver, mesh_record(undersized))
        self.assertEqual(result['status'], 'FAIL')
        self.assertTrue(result['failures'], 'Missing actual receiver recess must fail the coverage proof.')

    def test_stock_completeness_rejects_cavity_outside_original_receiver(self):
        stock = box((0, 0, 0), (1, 1, 1))
        socket = box((.5, .25, .25), (1, .75, .75))
        result = audit.stock_completeness(receiver_part(stock - socket),
                                          mesh_record(box((.5, .25, .25), (1.1, .75, .75))))
        self.assertEqual(result['status'], 'FAIL')
        self.assertGreater(result['max_cavity_vertex_outside_reference_stock_m'], .09)

    def test_stock_completeness_rejects_entirely_omitted_socket(self):
        stock = box((0, 0, 0), (1, 1, 1))
        receiver = receiver_part(stock - box((.5, .25, .25), (1, .75, .75)))
        result = audit.stock_completeness(receiver, {'vertices': [], 'triangles': []})
        self.assertEqual(result['status'], 'FAIL')
        self.assertTrue(result['failures'])

    def test_open_and_inverted_surfaces_are_rejected(self):
        vertices, faces = mesh(box((0, 0, 0), (1, 1, 1)))
        self.assertEqual(audit.inspect_mesh(vertices, faces[:-1])['status'], 'FAIL')
        inverted = faces.copy()
        inverted[0] = inverted[0, ::-1]
        self.assertEqual(audit.inspect_mesh(vertices, inverted)['status'], 'FAIL')

    def test_historical_c0_false_cavity_is_rejected_at_known_wood_point(self):
        result = audit.inspect_mesh(LEGACY_C0_VERTICES, LEGACY_C0_FACES)
        self.assertEqual(result['status'], 'FAIL')
        self.assertIn('zero-volume or inverted connected surface', result['failures'])
        point = np.array([[43.8, 85.5, 0]]) * audit.INCH
        self.assertGreater(audit.winding(point, LEGACY_C0_VERTICES[LEGACY_C0_FACES])[0], .999)
        model = json.loads((ROOT / 'src/model-data.json').read_text())
        timber = next(part for part in model['parts'] if part['id'] == 'C0')
        vertices, faces = audit.arrays(timber)
        self.assertGreater(audit.winding(point, vertices[faces])[0], .999,
                           'The historical overlay point must remain solid C0 wood.')
        cavities = json.loads((ROOT / 'src/cavity-data.json').read_text())
        vertices, faces = audit.arrays(cavities['parts']['C0']['removed'])
        self.assertLess(abs(audit.winding(point, vertices[faces])[0]), .001,
                        'The corrected cavity must exclude this actual-wood point.')

    def test_report_matches_current_geometry_and_all_components_pass(self):
        report = json.loads((ROOT / 'docs/cavity-fit-audit.json').read_text())
        self.assertEqual(report['model_sha256'], hashlib.sha256((ROOT / 'src/model-data.json').read_bytes()).hexdigest())
        self.assertEqual(report['cavity_sha256'], hashlib.sha256((ROOT / 'src/cavity-data.json').read_bytes()).hexdigest())
        self.assertEqual(report['status'], 'PASS')
        self.assertEqual(report['summary']['components_covered'], 144)
        self.assertEqual(report['summary']['timbers'], 104)
        self.assertEqual(report['summary']['nonempty_cavity_sets'], 48)
        self.assertEqual(report['summary']['winding_unoccupied_points'], 0)
        self.assertEqual(report['summary']['receiver_stock_envelopes_verified'], 48)
        self.assertEqual(report['summary']['all_timber_stock_envelopes_verified'], 104)
        self.assertEqual(report['summary']['declared_exterior_brace_trims'], 16)
        # TIMESTAMP START 2026-11-02T10:34:57-05:00 | REVISION R004764
        self.assertEqual(report['summary']['timbers_with_raw_surface_overlaps'], 0)
        self.assertGreater(report['summary']['raw_timber_coplanar_triangle_pairs_tested'], 0)
        self.assertTrue(all(row['raw_surface_check']['status'] == 'PASS' for row in report['timber_meshes'].values()))
        # TIMESTAMP END 2026-11-02T10:34:57-05:00 | REVISION R004764

    def test_report_comparison_allows_float_noise_but_rejects_stale_inputs(self):
        current = {'model_sha256': 'current', 'count': 144, 'area': 2e-14}
        audit.assert_equivalent_report(dict(current, area=2.01e-14), current)
        with self.assertRaises(AssertionError):
            audit.assert_equivalent_report(dict(current, model_sha256='stale'), current)
        with self.assertRaises(AssertionError):
            audit.assert_equivalent_report(dict(current, count=143), current)
        with self.assertRaises(AssertionError):
            audit.assert_equivalent_report(dict(current, area=1e-6), current)


if __name__ == '__main__':
    unittest.main()
# TIMESTAMP END 2026-11-02T09:09:22-05:00 | REVISION R004752
