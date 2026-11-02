# TIMESTAMP START 2026-11-02T12:38:21-05:00 | REVISION R004776
"""Strict metadata equality and equivalent oriented mesh boundaries.

CPU-dependent native triangulation may choose a different diagonal on an
unchanged planar surface. Accept that only after proving the same oriented
surface regions, closed valid meshes, bounds and signed volume. Numerical
metadata retains the original unit-aware absolute roundoff limits.
"""
import collections
import copy
import math

import manifold3d as m
import numpy as np


def tolerance(path):
    fields = [part for part in path if isinstance(part, str)]
    if any(field.endswith('_m3') for field in fields):
        return 1e-13
    if any(field.endswith('_in3') for field in fields):
        return 1e-9
    if any(field.endswith('_in2') for field in fields):
        return 1e-9
    return 1e-11


POSITION_TOLERANCE_M = 1e-11
# TIMESTAMP START 2026-11-02T13:01:18-05:00 | REVISION R004778
# Coplanarity is bounded in metres; skinny-triangle unit normals are used
# only to preserve orientation, not as a separate angular error allowance.
# TIMESTAMP END 2026-11-02T13:01:18-05:00 | REVISION R004778
SURFACE_AREA_TOLERANCE_M2 = 1e-9 * .0254 ** 2
VOLUME_TOLERANCE_M3 = 1e-13
SECTION_SCALE = 1e6
_MESH_CHECK_CACHE = {}


def mesh_arrays(record, location):
    vertices, triangles = record['vertices'], record['triangles']
    assert isinstance(vertices, list) and isinstance(triangles, list), (location, 'mesh arrays')
    assert vertices and all(isinstance(p, list) and len(p) == 3 for p in vertices), (location, 'vertex shape')
    assert all(type(x) in (float, int) and math.isfinite(x) for p in vertices for x in p), (location, 'finite coordinates')
    assert triangles and all(isinstance(t, list) and len(t) == 3 for t in triangles), (location, 'triangle shape')
    assert all(type(i) is int and 0 <= i < len(vertices) for t in triangles for i in t), (location, 'integer vertex indices')
    assert {i for t in triangles for i in t} == set(range(len(vertices))), (location, 'unreferenced vertex')
    if 'faces' in record:
        assert record['faces'] == triangles, (location, 'faces must describe the same triangle mesh')
    return np.asarray(vertices, dtype=float), np.asarray(triangles, dtype=np.int64)


def checked_mesh(vertices, triangles, location):
    # Raw validation rejects folded coincident patches that a signed-volume or
    # Boolean-only comparison could cancel and wrongly call equivalent.
    key = (vertices.tobytes(), triangles.tobytes())
    if key not in _MESH_CHECK_CACHE:
        from audit_cavity_fit import inspect_mesh
        _MESH_CHECK_CACHE[key] = inspect_mesh(vertices, triangles)
    result = _MESH_CHECK_CACHE[key]
    assert result['status'] == 'PASS', (location, 'invalid raw boundary', result['failures'])
    return result


def cyclic_triangles(triangles):
    return collections.Counter(min(tuple(t[k:] + t[:k]) for k in range(3))
                               for t in triangles)


# TIMESTAMP START 2026-11-02T13:01:18-05:00 | REVISION R004778
def oriented_regions(vertices, triangles):
    """Group coplanar triangles without identifying opposite orientations."""
    groups = []
    candidates = vertices[triangles]
    areas = np.linalg.norm(np.cross(candidates[:, 1] - candidates[:, 0],
                                    candidates[:, 2] - candidates[:, 0]), axis=1)
    # Seed each plane from a broad face: all triangles must satisfy the same
    # absolute vertex-plane bound, including skinny triangles whose normalized
    # cross products amplify harmless coordinate roundoff.
    for tri in candidates[np.argsort(-areas)]:
        normal = np.cross(tri[1] - tri[0], tri[2] - tri[0])
        normal /= np.linalg.norm(normal)
        match = next((g for g in groups
                      if normal @ g['normal'] > 0
                      and np.max(np.abs((tri - g['origin']) @ g['normal'])) <= POSITION_TOLERANCE_M), None)
        if match is None:
            axis = np.eye(3)[np.argmin(np.abs(normal))]
            u = np.cross(normal, axis)
            u /= np.linalg.norm(u)
            match = {'normal': normal, 'origin': tri[0],
                     'projection': np.column_stack((u, np.cross(normal, u))), 'triangles': []}
            groups.append(match)
        match['triangles'].append(tri)
    return groups

# TIMESTAMP END 2026-11-02T13:01:18-05:00 | REVISION R004778

def region_section(group, triangles):
    contours = [(tri - group['origin']) @ group['projection'] * SECTION_SCALE
                for tri in triangles]
    return m.CrossSection(contours, m.FillRule.Positive)


def assert_mesh_equivalent(actual, expected, location, stats):
    av, at = mesh_arrays(actual, location + '/actual')
    ev, et = mesh_arrays(expected, location + '/expected')
    aa = checked_mesh(av, at, location + '/actual')
    ea = checked_mesh(ev, et, location + '/expected')
    assert aa['connected_surfaces'] == ea['connected_surfaces'], (location, 'changed connected boundary count')
    assert abs(aa['signed_volume_m3'] - ea['signed_volume_m3']) <= VOLUME_TOLERANCE_M3, (location, 'changed signed volume')
    for operation in (np.min, np.max):
        assert np.max(np.abs(operation(av, axis=0) - operation(ev, axis=0))) <= POSITION_TOLERANCE_M, (location, 'changed source bounds')

    # Fast path: exact oriented triangles after a bijective, tightly bounded
    # vertex match. Triangle order and cyclic starts do not change a boundary.
    if len(av) == len(ev):
        distances = np.linalg.norm(av[:, None, :] - ev[None, :, :], axis=2)
        mapping = np.argmin(distances, axis=1)
        if len(set(mapping.tolist())) == len(ev) and np.max(distances[np.arange(len(av)), mapping]) <= POSITION_TOLERANCE_M:
            if cyclic_triangles(mapping[at].tolist()) == cyclic_triangles(et.tolist()):
                stats['mesh_index_reorderings'] = stats.get('mesh_index_reorderings', 0) + 1
                return

    # Alternative diagonals/subdivision are allowed only when every triangle
    # belongs to the same oriented support plane and each entire planar union
    # agrees in both directions. Holes, missing slivers and reversed regions
    # cannot be hidden by aggregate area or volume agreement.
    groups = oriented_regions(ev, et)
    actual_groups = [[] for _ in groups]
    # TIMESTAMP START 2026-11-02T13:01:18-05:00 | REVISION R004778
    for tri in av[at]:
        normal = np.cross(tri[1] - tri[0], tri[2] - tri[0])
        normal /= np.linalg.norm(normal)
        matches = [i for i, g in enumerate(groups)
                   if normal @ g['normal'] > 0
                   and np.max(np.abs((tri - g['origin']) @ g['normal'])) <= POSITION_TOLERANCE_M]
        assert len(matches) == 1, (location, 'changed or ambiguous oriented support plane', matches)
        actual_groups[matches[0]].append(tri)
    # TIMESTAMP END 2026-11-02T13:01:18-05:00 | REVISION R004778
    for group, triangles in zip(groups, actual_groups):
        assert triangles, (location, 'missing oriented support plane')
        saved = region_section(group, group['triangles'])
        rebuilt = region_section(group, triangles)
        missing = (saved - rebuilt).area() / SECTION_SCALE ** 2
        extra = (rebuilt - saved).area() / SECTION_SCALE ** 2
        assert missing + extra <= SURFACE_AREA_TOLERANCE_M2, (location, 'changed planar surface region', missing, extra)
    stats['mesh_retriangulations'] = stats.get('mesh_retriangulations', 0) + 1


def assert_equivalent(actual, expected, path=(), stats=None):
    if stats is None:
        stats = {'float_differences': 0, 'max_fraction_of_tolerance': 0.0, 'worst_path': None}
    location = '/'.join(map(str, path)) or '<root>'
    assert type(actual) is type(expected), (location, 'type', type(actual), type(expected))
    if isinstance(actual, dict):
        assert actual.keys() == expected.keys(), (location, 'keys', actual.keys(), expected.keys())
        mesh_keys = set()
        if {'vertices', 'triangles'} <= actual.keys() and actual != expected:
            # Only skip raw mesh-array comparison when their representation
            # changes. All IDs, dimensions, provenance, capacities and other
            # fields still go through strict recursive comparison below.
            if actual['vertices'] != expected['vertices'] or actual['triangles'] != expected['triangles']:
                assert_mesh_equivalent(actual, expected, location, stats)
                mesh_keys = {'vertices', 'triangles'}
                if 'faces' in actual:
                    mesh_keys.add('faces')
        for key in actual:
            if key not in mesh_keys:
                assert_equivalent(actual[key], expected[key], path + (key,), stats)
    elif isinstance(actual, list):
        assert len(actual) == len(expected), (location, 'length', len(actual), len(expected))
        for i, (a, b) in enumerate(zip(actual, expected)):
            assert_equivalent(a, b, path + (i,), stats)
    elif isinstance(actual, float):
        assert math.isfinite(actual) and math.isfinite(expected), (location, 'non-finite')
        error, limit = abs(actual - expected), tolerance(path)
        assert error <= limit, (location, 'float drift', actual, expected, error, 'absolute limit', limit)
        if error:
            stats['float_differences'] += 1
            if error / limit > stats['max_fraction_of_tolerance']:
                stats.update(max_fraction_of_tolerance=error / limit, worst_path=location)
    else:
        assert actual == expected, (location, 'exact value', actual, expected)
    return stats


def test_guard():
    base = {'id': 'J0-0', 'coordinates_m': [[1.0, 2.0, 3.0]], 'indices': [[0, 1, 2]],
            'volume_m3': .1, 'residual_in3': 0.0, 'capacity_checked': False}
    okay = copy.deepcopy(base)
    okay['coordinates_m'][0][0] += 1e-12
    okay['residual_in3'] = 7e-11
    assert_equivalent(okay, base)
    mutations = [lambda d: d.update(id='J0-2'), lambda d: d['indices'][0].__setitem__(1, 2),
                 lambda d: d['coordinates_m'].append([0., 0., 0.]),
                 lambda d: d['coordinates_m'][0].__setitem__(0, 1. + 1e-8),
                 lambda d: d.update(volume_m3=.1 + 1e-11), lambda d: d.update(residual_in3=1e-7),
                 lambda d: d.update(capacity_checked=True),
                 lambda d: d['coordinates_m'][0].__setitem__(0, float('nan')),
                 lambda d: d.update(extra='changed')]
    for mutate in mutations:
        bad = copy.deepcopy(base)
        mutate(bad)
        try:
            assert_equivalent(bad, base)
        except AssertionError:
            continue
        raise AssertionError('Equivalence guard accepted a deliberate metadata change')

    cube = {'id': 'cube', 'vertices': [[0., 0., 0.], [.1, 0., 0.], [.1, .1, 0.], [0., .1, 0.],
                                     [0., 0., .1], [.1, 0., .1], [.1, .1, .1], [0., .1, .1]],
            'triangles': [[0, 2, 1], [0, 3, 2], [4, 5, 6], [4, 6, 7], [0, 1, 5], [0, 5, 4],
                          [3, 7, 6], [3, 6, 2], [0, 4, 7], [0, 7, 3], [1, 2, 6], [1, 6, 5]]}
    cyclic = copy.deepcopy(cube)
    cyclic['triangles'] = [t[1:] + t[:1] for t in reversed(cyclic['triangles'])]
    assert assert_equivalent(cyclic, cube)['mesh_index_reorderings'] == 1
    permuted = copy.deepcopy(cube)
    permuted['vertices'].reverse()
    permuted['triangles'] = [[7 - i for i in t] for t in permuted['triangles']]
    assert assert_equivalent(permuted, cube)['mesh_index_reorderings'] == 1
    diagonal = copy.deepcopy(cube)
    diagonal['triangles'][:2] = [[0, 3, 1], [1, 3, 2]]
    assert assert_equivalent(diagonal, cube)['mesh_retriangulations'] == 1
    subdivided = copy.deepcopy(cube)
    subdivided['vertices'].append([.05, .05, 0.])
    subdivided['triangles'][:2] = [[0, 3, 8], [3, 2, 8], [2, 1, 8], [1, 0, 8]]
    assert assert_equivalent(subdivided, cube)['mesh_retriangulations'] == 1
    bad_meshes = []
    reversed_mesh = copy.deepcopy(cube)
    reversed_mesh['triangles'] = [t[::-1] for t in reversed_mesh['triangles']]
    bad_meshes.append(reversed_mesh)
    hole = copy.deepcopy(cube)
    hole['triangles'].pop()
    bad_meshes.append(hole)
    folded = copy.deepcopy(cube)
    folded['triangles'] += [cube['triangles'][0], cube['triangles'][0][::-1]]
    bad_meshes.append(folded)
    displaced = copy.deepcopy(cube)
    displaced['vertices'][6][0] -= 1e-8
    bad_meshes.append(displaced)
    invalid_index = copy.deepcopy(cube)
    invalid_index['triangles'][0][0] = 999
    bad_meshes.append(invalid_index)
    alias_mismatch = copy.deepcopy(diagonal)
    alias_mismatch['faces'] = cube['triangles']
    expected_alias = copy.deepcopy(cube)
    expected_alias['faces'] = cube['triangles']
    for bad, expected_mesh in [(p, cube) for p in bad_meshes] + [(alias_mismatch, expected_alias)]:
        try:
            assert_equivalent(bad, expected_mesh)
        except AssertionError:
            continue
        raise AssertionError('Equivalence guard accepted an invalid or changed boundary')
# TIMESTAMP END 2026-11-02T12:38:21-05:00 | REVISION R004776
