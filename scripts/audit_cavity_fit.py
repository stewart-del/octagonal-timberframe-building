# TIMESTAMP START 2026-11-02T09:09:22-05:00 | REVISION R004752
"""Independently check exported timber meshes and complementary cavity fit.

The convex-component containment check is the principal coverage test. Winding
samples and scaled Clipper2 sections provide independent numerical cross-checks.
Nothing here changes the model, proves a raising sequence, or rates strength.
"""
from pathlib import Path
import argparse
import hashlib
import itertools
import json
import math
import re

import manifold3d as m
import numpy as np
# TIMESTAMP START 2026-11-02T10:34:57-05:00 | REVISION R004764
from scipy.spatial import ConvexHull as ScipyConvexHull
from types import SimpleNamespace
# TIMESTAMP END 2026-11-02T10:34:57-05:00 | REVISION R004764
from scipy.stats import qmc

ROOT = Path(__file__).resolve().parents[1]
INCH = .0254
SECTION_SCALE = 1e6
DISTANCE_TOLERANCE_M = 1e-8
AREA_TOLERANCE_M2 = 1e-12
VOLUME_TOLERANCE_M3 = 1e-6 * INCH ** 3
FACE_AREA_MIN_M2 = 1e-12
SECTION_EVENT_OFFSET_M = 1e-7


# TIMESTAMP START 2026-11-02T10:34:57-05:00 | REVISION R004764
def ConvexHull(vertices):
    """Evaluate hulls in local coordinates without perturbing physical geometry.

    Near-coplanar facets are coordinate-sensitive in Qhull. Try deterministic
    invertible frames; return halfspaces and volume in physical coordinates.
    Internal convex cells use these directly, not artificial facet winding.
    """
    vertices = np.asarray(vertices, dtype=float)
    origin = vertices.mean(axis=0)
    _, scales, directions = np.linalg.svd(vertices - origin, full_matrices=False)
    if len(scales) != 3 or scales.min() <= 0:
        raise ValueError('non-volume convex hull')
    transforms = [np.eye(3), np.diag(1 / np.ptp(vertices, axis=0)),
                  directions.T @ np.diag(1 / scales)]
    errors = []
    for transform, options in itertools.product(transforms, (None, 'Qx')):
        try:
            result = ScipyConvexHull((vertices - origin) @ transform, qhull_options=options)
        except Exception as error:
            errors.append(type(error).__name__)
            continue
        normals = result.equations[:, :3] @ transform.T
        constants = result.equations[:, 3] - normals @ origin
        equations = np.column_stack([normals, constants]) / np.linalg.norm(normals, axis=1)[:, None]
        volume = float(result.volume) / abs(float(np.linalg.det(transform)))
        return SimpleNamespace(simplices=result.simplices, equations=equations, volume=volume)
    raise ValueError('no unperturbed convex hull: ' + ', '.join(errors))
# TIMESTAMP END 2026-11-02T10:34:57-05:00 | REVISION R004764


def arrays(mesh):
    return np.asarray(mesh['vertices'], dtype=float), np.asarray(mesh['triangles'], dtype=np.uint64)


def solid(vertices, faces):
    return m.Manifold(m.Mesh64(np.array(vertices, dtype=float, order='C', copy=True),
                              np.array(faces, dtype=np.uint64, order='C', copy=True))).set_tolerance(1e-9)


def signed_volume(vertices, faces):
    triangles = vertices[faces]
    # Translate to a nearby origin to reduce cancellation for small cavities.
    triangles = triangles - vertices.mean(axis=0)
    return float(np.einsum('ij,ij->i', triangles[:, 0],
                          np.cross(triangles[:, 1], triangles[:, 2])).sum() / 6)


def mesh_components(vertices, faces):
    """Connected triangle components using shared vertex indices, without CSG."""
    pending = set(range(len(faces)))
    incident = [[] for _ in vertices]
    for index, face in enumerate(faces):
        for vertex in face:
            incident[int(vertex)].append(index)
    result = []
    while pending:
        first = min(pending)
        pending.remove(first)
        component, stack = [first], [first]
        while stack:
            for vertex in faces[stack.pop()]:
                for adjacent in incident[int(vertex)]:
                    if adjacent in pending:
                        pending.remove(adjacent)
                        component.append(adjacent)
                        stack.append(adjacent)
        selected = faces[sorted(component)]
        ids = np.unique(selected)
        remap = np.full(len(vertices), -1, dtype=np.int64)
        remap[ids] = np.arange(len(ids))
        result.append((vertices[ids], remap[selected].astype(np.uint64)))
    return result


# TIMESTAMP START 2026-11-02T10:34:57-05:00 | REVISION R004764
def coplanar_surface_overlaps(vertices, faces):
    """Intersect raw coplanar triangles, including hidden opposed surface patches.

    Signed volumes and solid booleans can cancel coincident opposite faces. This
    check therefore uses the original triangles, projected and clipped in 2D.
    Adjacent triangles sharing only an edge or point have zero intersection area.
    """
    triangles = vertices[faces]
    cross = np.cross(triangles[:, 1] - triangles[:, 0], triangles[:, 2] - triangles[:, 0])
    lengths = np.linalg.norm(cross, axis=1)
    valid = lengths > 2 * FACE_AREA_MIN_M2
    normals = np.zeros_like(cross)
    normals[valid] = cross[valid] / lengths[valid, None]
    bounds_low, bounds_high = triangles.min(axis=1), triangles.max(axis=1)
    plane_tolerance = 1e-9
    overlaps = []
    candidate_count = 0
    for first in range(len(triangles)):
        if not valid[first]:
            continue
        alignment = normals @ normals[first]
        candidates = np.flatnonzero(valid & (np.arange(len(triangles)) > first)
                                   & (np.abs(alignment) > 1 - 1e-10)
                                   & np.all(bounds_high >= bounds_low[first] - plane_tolerance, axis=1)
                                   & np.all(bounds_low <= bounds_high[first] + plane_tolerance, axis=1))
        origin = triangles[first, 0]
        for second in candidates:
            if (np.max(np.abs((triangles[second] - origin) @ normals[first])) > plane_tolerance
                    or np.max(np.abs((triangles[first] - triangles[second, 0]) @ normals[second])) > plane_tolerance):
                continue
            candidate_count += 1
            u = triangles[first, 1] - origin
            u /= np.linalg.norm(u)
            projection = np.column_stack([u, np.cross(normals[first], u)])
            sections = []
            for index in (first, second):
                polygon = (triangles[index] - origin) @ projection * SECTION_SCALE
                signed_area = np.sum(polygon[:, 0] * np.roll(polygon[:, 1], -1)
                                     - polygon[:, 1] * np.roll(polygon[:, 0], -1)) / 2
                if signed_area < 0:
                    polygon = polygon[::-1]
                sections.append(m.CrossSection([polygon.tolist()]))
            area = (sections[0] ^ sections[1]).area() / SECTION_SCALE ** 2
            if area > AREA_TOLERANCE_M2:
                overlaps.append({'triangles': [first, int(second)],
                                 'orientation': 'opposed' if alignment[second] < 0 else 'same-facing',
                                 'area_m2': area, 'area_in2': area / INCH ** 2})
    return {'status': 'PASS' if not overlaps else 'FAIL',
            'coplanar_pairs_tested': candidate_count, 'overlap_pairs': overlaps,
            'opposed_overlap_pair_count': sum(row['orientation'] == 'opposed' for row in overlaps),
            'max_overlap_area_m2': max((row['area_m2'] for row in overlaps), default=0.0),
            'sum_pair_overlap_area_m2': sum(row['area_m2'] for row in overlaps),
            'plane_tolerance_m': plane_tolerance, 'positive_area_tolerance_m2': AREA_TOLERANCE_M2}
# TIMESTAMP END 2026-11-02T10:34:57-05:00 | REVISION R004764


def inspect_mesh(vertices, faces, require_single=False):
    failures = []
    if not len(vertices) or not len(faces):
        return {'status': 'FAIL', 'failures': ['empty mesh']}
    if not np.isfinite(vertices).all() or faces.max() >= len(vertices):
        return {'status': 'FAIL', 'failures': ['invalid coordinate or face index']}
    triangles = vertices[faces]
    areas = np.linalg.norm(np.cross(triangles[:, 1] - triangles[:, 0],
                                    triangles[:, 2] - triangles[:, 0]), axis=1) / 2
    directed = np.vstack([faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]]])
    undirected, counts = np.unique(np.sort(directed, axis=1), axis=0, return_counts=True)
    if not (counts == 2).all():
        failures.append('nonmanifold or open edge')
    directed_set = {(int(a), int(b)) for a, b in directed}
    if any((int(b), int(a)) not in directed_set or (int(a), int(b)) not in directed_set
           for a, b in undirected):
        failures.append('inconsistent face winding')
    if len(np.unique(np.sort(faces, axis=1), axis=0)) != len(faces):
        failures.append('duplicate face')
    if (areas <= FACE_AREA_MIN_M2).any():
        failures.append('degenerate or numerically tiny triangle')
    # TIMESTAMP START 2026-11-02T10:34:57-05:00 | REVISION R004764
    surface_check = coplanar_surface_overlaps(vertices, faces)
    if surface_check['status'] != 'PASS':
        failures.append('positive-area coplanar raw triangle overlap')
    # TIMESTAMP END 2026-11-02T10:34:57-05:00 | REVISION R004764
    components = mesh_components(vertices, faces)
    component_volumes = [signed_volume(v, f) for v, f in components]
    if any(volume <= 1e-14 for volume in component_volumes):
        failures.append('zero-volume or inverted connected surface')
    manifold = solid(vertices, faces)
    if str(manifold.status()) != 'Error.NoError':
        failures.append('Manifold rejected mesh')
    if require_single and (len(components) != 1 or len(manifold.decompose()) != 1):
        failures.append('timber is not one connected solid')
    # TIMESTAMP START 2026-11-02T10:34:57-05:00 | REVISION R004764
    return {'status': 'PASS' if not failures else 'FAIL', 'failures': failures,
            'vertices': len(vertices), 'triangles': len(faces),
            'connected_surfaces': len(components), 'minimum_triangle_area_m2': float(areas.min()),
            'signed_volume_m3': signed_volume(vertices, faces), 'raw_surface_check': surface_check}
    # TIMESTAMP END 2026-11-02T10:34:57-05:00 | REVISION R004764


def winding(points, triangles):
    """Generalized winding number using solid angles; no Boolean engine."""
    values = []
    for start in range(0, len(points), 128):
        offsets = triangles[None, :, :, :] - points[start:start + 128, None, None, :]
        a, b, c = offsets[:, :, 0], offsets[:, :, 1], offsets[:, :, 2]
        la, lb, lc = [np.linalg.norm(x, axis=2) for x in (a, b, c)]
        numerator = np.einsum('ijk,ijk->ij', a, np.cross(b, c))
        denominator = (la * lb * lc + np.einsum('ijk,ijk->ij', a, b) * lc
                       + np.einsum('ijk,ijk->ij', b, c) * la
                       + np.einsum('ijk,ijk->ij', c, a) * lb)
        values.extend(np.sum(2 * np.arctan2(numerator, denominator), axis=1) / (4 * np.pi))
    return np.asarray(values)


def clip_polygon(polygon, equations, inset=DISTANCE_TOLERANCE_M):
    """Clip a 3D polygon against an inward-offset convex cavity."""
    for equation in equations:
        if len(polygon) < 3:
            return []
        output = []
        previous = polygon[-1]
        before = float(previous @ equation[:3] + equation[3] + inset)
        for current in polygon:
            after = float(current @ equation[:3] + equation[3] + inset)
            if (before <= 0) != (after <= 0):
                output.append(previous + (current - previous) * before / (before - after))
            if after <= 0:
                output.append(current)
            previous, before = current, after
        polygon = output
    return polygon


def polygon_area(polygon):
    if len(polygon) < 3:
        return 0.0
    vertices = np.asarray(polygon) - polygon[0]
    return float(np.linalg.norm(np.cross(vertices[:-1], vertices[1:]).sum(axis=0)) / 2)


def hull_mesh(vertices):
    hull = ConvexHull(vertices)
    faces = hull.simplices.copy()
    triangles = vertices[faces]
    normals = np.cross(triangles[:, 1] - triangles[:, 0], triangles[:, 2] - triangles[:, 0])
    reverse = np.einsum('ij,ij->i', normals, hull.equations[:, :3]) < 0
    faces[reverse] = faces[reverse][:, [0, 2, 1]]
    return vertices, faces.astype(np.uint64)


def declared_brace_trim(part):
    match = re.fullmatch(r'K([0-7])-(A|B)', part.get('id', ''))
    if part.get('group') != 'braces' or not match:
        return None
    angle = int(match[1]) * math.pi / 4
    sign = -1 if match[2] == 'A' else 1
    normal = sign * np.array([-math.sin(angle), 0, -math.cos(angle)])
    return {'normal_world': normal.tolist(), 'minimum_projection_in': 2,
            'reason': 'Declared exterior brace-end stop two inches inside its post side, retaining the central post web; not an unfilled socket.'}


def reference_stock(part, apply_declared_trim=False):
    """Reconstruct the saved prejoinery halfspaces, inches/Z-up to meters/Y-up."""
    planes = part['geometry_planes_inches']
    normals = np.asarray([[plane['normal'][0], plane['normal'][2], -plane['normal'][1]] for plane in planes])
    constants = np.asarray([plane['constant'] * INCH for plane in planes])
    trim = declared_brace_trim(part) if apply_declared_trim else None
    if trim:
        normals = np.vstack([normals, -np.asarray(trim['normal_world'])])
        constants = np.r_[constants, -trim['minimum_projection_in'] * INCH]
    vertices = []
    for indices in itertools.combinations(range(len(normals)), 3):
        selected = list(indices)
        if abs(np.linalg.det(normals[selected])) <= 1e-10:
            continue
        point = np.linalg.solve(normals[selected], constants[selected])
        if np.all(normals @ point <= constants + 1e-9):
            vertices.append(point)
    return hull_mesh(np.unique(np.round(vertices, 14), axis=0))


def stock_completeness(part, removed):
    """Prove the exported cavity accounts for all cuts inside the receiver stock."""
    stock_v, stock_f = reference_stock(part, apply_declared_trim=True)
    own_v, own_f = arrays(part)
    covered_by = {'final_receiver_wood': own_v[own_f]}
    outside = 0.0
    if removed['triangles']:
        cavity_v, cavity_f = arrays(removed)
        equations = ConvexHull(stock_v).equations
        outside = max(0.0, float(np.max(cavity_v @ equations[:, :3].T + equations[:, 3])))
        covered_by['exported_cavity'] = cavity_v[cavity_f]
    coverage = component_coverage(stock_v, stock_f, covered_by)
    cells = coverage.get('cells', [coverage])
    passed = coverage['status'] == 'PASS' and outside <= DISTANCE_TOLERANCE_M
    return {'status': 'PASS' if passed else 'FAIL',
            'reference_envelope_volume_in3': signed_volume(stock_v, stock_f) / INCH ** 3,
            'max_cavity_vertex_outside_reference_stock_m': outside,
            'partition_planes': coverage.get('partition_planes', 0),
            'convex_cells': len(cells), 'verified_cells': sum(cell['status'] == 'PASS' for cell in cells),
            'cells_in_final_receiver_wood': sum(cell.get('mate') == 'final_receiver_wood' for cell in cells),
            'cells_in_exported_cavity': sum(cell.get('mate') == 'exported_cavity' for cell in cells),
            'partition_volume_balance_error_m3': coverage.get('partition_volume_balance_error_m3', 0.0),
            'max_interior_boundary_area_m2': max((cell.get('interior_boundary_area_m2', 0) for cell in cells), default=0),
            'failures': [cell for cell in cells if cell['status'] != 'PASS'],
            'declared_external_trim': declared_brace_trim(part),
            'scope': 'Saved prejoinery envelope, after any explicitly listed exterior trim, is covered by final timber wood plus exported removed cavity within the stated tolerances. Added tenons outside this envelope are not counted as removed stock.'}


def split_convex(vertices, equation):
    values = vertices @ equation[:3] + equation[3]
    if values.min() >= -DISTANCE_TOLERANCE_M or values.max() <= DISTANCE_TOLERANCE_M:
        return [vertices]
    faces = ConvexHull(vertices).simplices
    edges = np.unique(np.sort(np.vstack([faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]]]), axis=1), axis=0)
    crossing = []
    for a, b in edges:
        if (values[a] < 0) != (values[b] < 0):
            crossing.append(vertices[a] + (vertices[b] - vertices[a]) * values[a] / (values[a] - values[b]))
    crossing = np.asarray(crossing)
    return [np.unique(np.round(np.vstack([vertices[mask], crossing]), 14), axis=0)
            for mask in (values <= 0, values >= 0)]


# TIMESTAMP START 2026-11-02T10:08:45-05:00 | REVISION R004761
def boundary_partition(vertices, hull, boundary_triangles):
    """Produce disjoint convex cells from actual crossing boundary-face planes."""
    planes = {}
    bounds = np.array([vertices.min(axis=0), vertices.max(axis=0)])
    for triangles in boundary_triangles.values():
        near = (np.all(triangles.max(axis=1) >= bounds[0], axis=1)
                & np.all(triangles.min(axis=1) <= bounds[1], axis=1))
        for triangle in triangles[near]:
            if polygon_area(clip_polygon(list(triangle), hull.equations)) <= AREA_TOLERANCE_M2:
                continue
            normal = np.cross(triangle[1] - triangle[0], triangle[2] - triangle[0])
            normal /= np.linalg.norm(normal)
            if normal[np.flatnonzero(np.abs(normal) > 1e-9)[0]] < 0:
                normal = -normal
            equation = np.r_[normal, -normal @ triangle[0]]
            planes.setdefault(tuple(np.round(equation, 10)), equation)
    cells = [vertices]
    for key in sorted(planes):
        cells = [piece for cell in cells for piece in split_convex(cell, planes[key])]
        if len(cells) > 4096:
            raise ValueError('convex partition exceeds audit complexity bound')
    return cells, len(planes)


def partition_coverage(vertices, hull, mate_triangles):
    """Partition a shared cavity by actual crossing mate-face planes, then prove each cell."""
    try:
        cells, plane_count = boundary_partition(vertices, hull, mate_triangles)
    except ValueError as error:
        return {'status': 'FAIL', 'reason': str(error)}
    # TIMESTAMP START 2026-11-02T10:34:57-05:00 | REVISION R004764
    results = [convex_cell_coverage(cell, ConvexHull(cell), mate_triangles, allow_partition=False) for cell in cells]
    # TIMESTAMP END 2026-11-02T10:34:57-05:00 | REVISION R004764
    volume_error = abs(sum(float(ConvexHull(cell).volume) for cell in cells) - float(hull.volume))
    passed = all(row['status'] == 'PASS' for row in results) and volume_error <= VOLUME_TOLERANCE_M3
    return {'status': 'PASS' if passed else 'FAIL', 'coverage_mode': 'explicit convex partition',
            'partition_planes': plane_count, 'partition_cells': len(cells),
            'partition_volume_balance_error_m3': volume_error, 'cells': results,
            'note': 'Each cell is independently contained in one mate; only the stated distance shell around cell boundaries is excluded.'}


def nonconvex_coverage(vertices, faces, hull, mate_triangles):
    """Partition a concave recess without replacing its rendered surface by its hull."""
    try:
        all_cells, plane_count = boundary_partition(vertices, hull, {'actual_cavity': vertices[faces]})
    except ValueError as error:
        return {'status': 'FAIL', 'reason': str(error)}
    cells = []
    for cell in all_cells:
        # TIMESTAMP START 2026-11-02T10:34:57-05:00 | REVISION R004764
        cell_hull = ConvexHull(cell)
        # Keep only cells proven wholly inside the actual cavity. The volume
        # balance below rejects any missing cavity region, including hidden voids.
        inside = convex_cell_coverage(cell, cell_hull, {'actual_cavity': vertices[faces]}, allow_partition=False)
        if inside['status'] == 'PASS':
            cells.append((cell, cell_hull))
    volume_error = abs(sum(cell_hull.volume for _, cell_hull in cells) - signed_volume(vertices, faces))
    results = [convex_cell_coverage(cell, cell_hull, mate_triangles) for cell, cell_hull in cells]
    # TIMESTAMP END 2026-11-02T10:34:57-05:00 | REVISION R004764
    passed = bool(cells) and volume_error <= VOLUME_TOLERANCE_M3 and all(row['status'] == 'PASS' for row in results)
    return {'status': 'PASS' if passed else 'FAIL', 'coverage_mode': 'nonconvex surface partition',
            'partition_planes': plane_count, 'partition_cells': len(cells),
            'excluded_hull_cells': len(all_cells) - len(cells),
            'partition_volume_balance_error_m3': volume_error, 'cells': results,
            'note': 'Disjoint convex cells are each proved inside the actual concave cavity; their summed volume must recover its signed surface volume. Every retained cell is then proved covered by mating timber.'}


def coverage_leaf_count(row):
    if row['status'] != 'PASS':
        return 0
    return sum(coverage_leaf_count(child) for child in row['cells']) if 'cells' in row else 1


def component_coverage(vertices, faces, mate_triangles, allow_partition=True):
    """Prove the connected inset cavity remains inside one closed mate.

    A convex cavity interior containing an interior point of a closed mate cannot
    leave that mate without crossing its boundary. Every mate triangle is clipped
    against the cavity's inset halfspaces to test for that crossing, including
    boundaries of concealed holes. The excluded tolerance shell is explicit.
    """
    try:
        hull = ConvexHull(vertices)
    except Exception as error:
        return {'status': 'FAIL', 'reason': 'non-volume cavity component', 'detail': type(error).__name__}
    volume = signed_volume(vertices, faces)
    error = abs(float(hull.volume) - volume)
    if volume <= 1e-14:
        return {'status': 'FAIL', 'reason': 'cavity component is not a positive volume',
                'convex_volume_error_m3': error}
    if error > VOLUME_TOLERANCE_M3:
        if not allow_partition:
            return {'status': 'FAIL', 'reason': 'target cell is not convex', 'convex_volume_error_m3': error}
        return nonconvex_coverage(vertices, faces, hull, mate_triangles)
    # TIMESTAMP START 2026-11-02T10:34:57-05:00 | REVISION R004764
    result = convex_cell_coverage(vertices, hull, mate_triangles, allow_partition)
    result['convex_volume_error_m3'] = error
    return result


def convex_cell_coverage(vertices, hull, mate_triangles, allow_partition=True):
    """Prove a convex point hull using its halfspaces, without triangulating it.

    Subdivision cells are convex by construction. Exported source surfaces must
    first pass component_coverage's signed-volume and concavity checks. Avoiding
    artificial facet orientation here leaves the physical mesh checks intact.
    """
    volume = float(hull.volume)
    # TIMESTAMP END 2026-11-02T10:34:57-05:00 | REVISION R004764
    point = vertices.mean(axis=0)
    inset_margin = float(-np.max(hull.equations[:, :3] @ point + hull.equations[:, 3]))
    if inset_margin <= DISTANCE_TOLERANCE_M:
        return {'status': 'FAIL', 'reason': 'cavity thinner than containment tolerance'}
    bounds = np.array([vertices.min(axis=0), vertices.max(axis=0)])
    attempted = []
    for name, triangles in mate_triangles.items():
        if winding(point[None], triangles)[0] < .999999:
            continue
        intersects = (np.all(triangles.max(axis=1) >= bounds[0], axis=1)
                      & np.all(triangles.min(axis=1) <= bounds[1], axis=1))
        maximum = max((polygon_area(clip_polygon(list(triangle), hull.equations))
                       for triangle in triangles[intersects]), default=0.0)
        attempted.append({'mate': name, 'interior_boundary_area_m2': maximum})
        if maximum <= AREA_TOLERANCE_M2:
            return {'status': 'PASS', 'coverage_mode': 'one convex cell', 'mate': name, 'volume_in3': volume / INCH ** 3,
                    # TIMESTAMP START 2026-11-02T10:34:57-05:00 | REVISION R004764
                    'interior_boundary_area_m2': maximum,
                    # TIMESTAMP END 2026-11-02T10:34:57-05:00 | REVISION R004764
                    'centroid_margin_m': inset_margin}
    if allow_partition:
        result = partition_coverage(vertices, hull, mate_triangles)
        # TIMESTAMP START 2026-11-02T10:34:57-05:00 | REVISION R004764
        result.update(volume_in3=volume / INCH ** 3)
        # TIMESTAMP END 2026-11-02T10:34:57-05:00 | REVISION R004764
        return result
    return {'status': 'FAIL', 'reason': 'no single mate covers the connected inset cavity',
            'candidates_containing_centroid': attempted,
            'note': 'Multi-mate coverage needs an explicit partition; samples alone do not certify it.'}
# TIMESTAMP END 2026-11-02T10:08:45-05:00 | REVISION R004761


def bounds_meet(a, b, tolerance=1e-9):
    return bool(np.all(a[0] <= b[1] + tolerance) and np.all(b[0] <= a[1] + tolerance))


def section_heights(coordinates, low, high):
    events = sorted(set(np.round(np.concatenate(coordinates), 10)))
    events = [x for x in events if low - 1e-9 <= x <= high + 1e-9]
    heights = set()
    for event in events:
        for offset in (-SECTION_EVENT_OFFSET_M, SECTION_EVENT_OFFSET_M):
            if low + 1e-9 < event + offset < high - 1e-9:
                heights.add(event + offset)
    for before, after in zip(events, events[1:]):
        if after - before > 1e-9:
            heights.update(before + (after - before) * fraction for fraction in (.25, .5, .75))
    return sorted(heights)


def cavity_sections(name, vertices, faces, woods):
    match = re.fullmatch(r'([A-Z]+)([0-7])(.*)', name)
    angle = int(match[2]) * math.pi / 4 if match else 0
    c, s = math.cos(angle), math.sin(angle)
    rotation = np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])
    vertices = vertices @ rotation
    transformed = {key: (v @ rotation, f) for key, (v, f) in woods.items()}
    box = np.array([vertices.min(axis=0), vertices.max(axis=0)])
    bounds = {key: np.array([v.min(axis=0), v.max(axis=0)]) for key, (v, _) in transformed.items()}
    mates = [key for key in woods if key != name and bounds_meet(box, bounds[key])]
    count, missing_max, receiver_max = 0, 0.0, 0.0
    for axis in range(3):
        order = [(axis + 1) % 3, (axis + 2) % 3, axis]
        cavity = solid(vertices[:, order] * SECTION_SCALE, faces)
        sections = {key: solid(transformed[key][0][:, order] * SECTION_SCALE, transformed[key][1])
                    for key in mates + [name]}
        heights = section_heights([vertices[:, axis]] + [transformed[key][0][:, axis] for key in mates],
                                  box[0, axis], box[1, axis])
        for height in heights:
            cut = cavity.slice(height * SECTION_SCALE)
            if cut.area() / SECTION_SCALE ** 2 < 1e-14:
                continue
            all_sections = [cut] + [sections[key].slice(height * SECTION_SCALE) for key in mates
                                   if bounds[key][0, axis] - 1e-9 <= height <= bounds[key][1, axis] + 1e-9]
            residual = m.CrossSection.batch_boolean(all_sections, m.OpType.Subtract)
            missing_max = max(missing_max, residual.area() / SECTION_SCALE ** 2)
            receiver_max = max(receiver_max, (cut ^ sections[name].slice(height * SECTION_SCALE)).area()
                               / SECTION_SCALE ** 2)
            count += 1
    return {'sections': count, 'max_missing_area_m2': missing_max,
            'max_receiver_overlap_area_m2': receiver_max,
            'status': 'PASS' if max(missing_max, receiver_max) <= AREA_TOLERANCE_M2 else 'FAIL'}


def wood_pair_sections(woods):
    bounds = {key: np.array([v.min(axis=0), v.max(axis=0)]) for key, (v, _) in woods.items()}
    count, candidates, maximum = 0, 0, 0.0
    bad = []
    for a, b in itertools.combinations(woods, 2):
        low, high = np.maximum(bounds[a][0], bounds[b][0]), np.minimum(bounds[a][1], bounds[b][1])
        if np.any(high - low <= DISTANCE_TOLERANCE_M):
            continue
        candidates += 1
        pair_max = 0.0
        for axis in range(3):
            order = [(axis + 1) % 3, (axis + 2) % 3, axis]
            sections = [solid(woods[key][0][:, order] * SECTION_SCALE, woods[key][1]) for key in (a, b)]
            heights = section_heights([woods[a][0][:, axis], woods[b][0][:, axis],
                                       np.array([low[axis], high[axis]])], low[axis], high[axis])
            for height in heights:
                area = (sections[0].slice(height * SECTION_SCALE) ^ sections[1].slice(height * SECTION_SCALE)).area()
                pair_max = max(pair_max, area / SECTION_SCALE ** 2)
                count += 1
        maximum = max(maximum, pair_max)
        if pair_max > AREA_TOLERANCE_M2:
            bad.append({'a': a, 'b': b, 'max_overlap_area_m2': pair_max})
    return {'status': 'PASS' if not bad else 'FAIL', 'pairs_considered': len(woods) * (len(woods) - 1) // 2,
            'positive_extent_bounds_candidates': candidates, 'sections': count,
            'max_overlap_area_m2': maximum, 'failures': bad,
            'scope': 'Independent 2D sectional cross-check; full 3D pair audit remains in joinery-verification.json.'}


def audit(model, cavities):
    parts = {part['id']: part for part in model['parts'] if part['is_timber']}
    woods = {key: arrays(part) for key, part in parts.items()}
    triangles = {key: v[f] for key, (v, f) in woods.items()}
    bounds = {key: np.array([v.min(axis=0), v.max(axis=0)]) for key, (v, _) in woods.items()}
    topology = {key: inspect_mesh(v, f, require_single=True) for key, (v, f) in woods.items()}
    rows, failures, legacy, no_cavity_stock = [], [], [], {}
    if set(woods) != set(cavities['parts']):
        failures.append('cavity record IDs do not exactly match timber IDs')
    if any(row['status'] != 'PASS' for row in topology.values()):
        failures.append('timber topology failure')
    sobol = qmc.Sobol(3, scramble=True, seed=845271).random_base2(12)
    for name, data in cavities['parts'].items():
        residual = data.get('unfilled')
        if residual and residual.get('triangles'):
            rv, rf = arrays(residual)
            legacy.append({'id': name, 'signed_volume_m3': signed_volume(rv, rf),
                           'mesh_check': inspect_mesh(rv, rf),
                           'physical_gap_evidence': False})
        if not data['removed']['triangles']:
            if name in parts:
                no_cavity_stock[name] = stock_completeness(parts[name], data['removed'])
                if no_cavity_stock[name]['status'] != 'PASS':
                    failures.append(name + ': unexplained cut in timber with no exported cavity')
            continue
        v, f = arrays(data['removed'])
        mesh_check = inspect_mesh(v, f)
        if mesh_check['status'] != 'PASS' or name not in woods:
            rows.append({'id': name, 'status': 'FAIL', 'mesh_check': mesh_check})
            failures.append(name + ': invalid removed-cavity mesh')
            continue
        box = np.array([v.min(axis=0), v.max(axis=0)])
        mates = {key: triangles[key] for key in woods if key != name and bounds_meet(box, bounds[key])}
        components = [component_coverage(cv, cf, mates) for cv, cf in mesh_components(v, f)]
        cut_triangles = v[f]
        normals = np.cross(cut_triangles[:, 1] - cut_triangles[:, 0], cut_triangles[:, 2] - cut_triangles[:, 0])
        normals /= np.linalg.norm(normals, axis=1)[:, None]
        points = np.vstack([box[0] + sobol * (box[1] - box[0]), cut_triangles.mean(axis=1) - normals * 1e-6])
        points = points[winding(points, cut_triangles) > .5]
        in_receiver = winding(points, triangles[name]) > .5
        occupied = np.zeros(len(points), dtype=bool)
        for key, mate_triangles in mates.items():
            mask = (~occupied & np.all(points >= bounds[key][0] - 1e-9, axis=1)
                    & np.all(points <= bounds[key][1] + 1e-9, axis=1))
            if mask.any():
                occupied[mask] = winding(points[mask], mate_triangles) > .5
        sampling = {'interior_points': len(points), 'occupied_by_mates': int(occupied.sum()),
                    'inside_receiver': int(in_receiver.sum()), 'unoccupied': int((~occupied).sum())}
        sections = cavity_sections(name, v, f, woods)
        completeness = stock_completeness(parts[name], data['removed'])
        passed = (all(component['status'] == 'PASS' for component in components)
                  and not sampling['inside_receiver'] and not sampling['unoccupied']
                  and sections['status'] == 'PASS' and completeness['status'] == 'PASS')
        rows.append({'id': name, 'status': 'PASS' if passed else 'FAIL', 'mesh_check': mesh_check,
                     'components': components, 'winding_samples': sampling, 'cross_sections': sections,
                     'receiver_stock_completeness': completeness})
        if not passed:
            failures.append(name + ': cavity coverage or receiver exclusion failed')
    pairs = wood_pair_sections(woods)
    if pairs['status'] != 'PASS':
        failures.append('independent wood-pair sectional overlap detected')
    # TIMESTAMP START 2026-11-02T10:08:45-05:00 | REVISION R004761
    component_rows = [component for row in rows for component in row.get('components', [])]
    is_proposed = 'proposed_review' in model
    expected_components = 168 if is_proposed else 144
    if is_proposed and (model['proposed_review'].get('geometry_audit', {}).get('implemented_interface_count') != 24
                        or len(model['proposed_review'].get('changed_member_ids', [])) != 40):
        failures.append('unsupported proposed inventory; expected 24 step-lap transfers and 40 changed members')
    summary = {'timbers': len(woods), 'nonempty_cavity_sets': len(rows),
               'connected_cavity_components': len(component_rows),
               'convex_cavity_components': sum(row.get('coverage_mode') != 'nonconvex surface partition' for row in component_rows),
               'nonconvex_cavity_components': sum(row.get('coverage_mode') == 'nonconvex surface partition' for row in component_rows),
               'components_covered': sum(row['status'] == 'PASS' for row in component_rows),
               'components_contained_in_one_mate': sum(row['status'] == 'PASS' and 'mate' in row for row in component_rows),
               'components_partitioned': sum('partition_cells' in row for row in component_rows),
               'verified_convex_cells': sum(coverage_leaf_count(row) for row in component_rows),
               'receiver_stock_envelopes_verified': sum(row.get('receiver_stock_completeness', {}).get('status') == 'PASS' for row in rows),
               'receiver_stock_convex_cells_verified': sum(row.get('receiver_stock_completeness', {}).get('verified_cells', 0) for row in rows),
               'no_cavity_stock_envelopes_verified': sum(row['status'] == 'PASS' for row in no_cavity_stock.values()),
               'all_timber_stock_envelopes_verified': sum(row.get('receiver_stock_completeness', {}).get('status') == 'PASS' for row in rows)
                                                     + sum(row['status'] == 'PASS' for row in no_cavity_stock.values()),
               'declared_exterior_brace_trims': sum(row['declared_external_trim'] is not None for row in no_cavity_stock.values()),
               'max_cavity_outside_reference_stock_m': max((row.get('receiver_stock_completeness', {}).get('max_cavity_vertex_outside_reference_stock_m', 0) for row in rows), default=0),
               'winding_interior_points': sum(row.get('winding_samples', {}).get('interior_points', 0) for row in rows),
               'winding_unoccupied_points': sum(row.get('winding_samples', {}).get('unoccupied', 0) for row in rows),
               'winding_points_in_receiver': sum(row.get('winding_samples', {}).get('inside_receiver', 0) for row in rows),
               'cavity_cross_sections': sum(row.get('cross_sections', {}).get('sections', 0) for row in rows),
               'max_missing_section_area_m2': max((row.get('cross_sections', {}).get('max_missing_area_m2', 0) for row in rows), default=0),
               'max_receiver_overlap_section_area_m2': max((row.get('cross_sections', {}).get('max_receiver_overlap_area_m2', 0) for row in rows), default=0),
               # TIMESTAMP START 2026-11-02T10:34:57-05:00 | REVISION R004764
               'wood_pair_cross_sections': pairs['sections'], 'max_wood_overlap_section_area_m2': pairs['max_overlap_area_m2'],
               'raw_timber_coplanar_triangle_pairs_tested': sum(row.get('raw_surface_check', {}).get('coplanar_pairs_tested', 0) for row in topology.values()),
               'timbers_with_raw_surface_overlaps': sum(row.get('raw_surface_check', {}).get('status') == 'FAIL' for row in topology.values()),
               'max_raw_timber_triangle_overlap_area_m2': max((row.get('raw_surface_check', {}).get('max_overlap_area_m2', 0) for row in topology.values()), default=0)}
               # TIMESTAMP END 2026-11-02T10:34:57-05:00 | REVISION R004764
    if (len(woods), len(rows), len(component_rows)) != (104, 48, expected_components):
        failures.append(f'expected 104 timbers, 48 nonempty cavity sets, and {expected_components} connected cavity components')
    # TIMESTAMP START 2026-11-02T10:34:57-05:00 | REVISION R004764
    return {'schema_version': 'cavity-fit-audit-3', 'status': 'PASS' if not failures else 'FAIL',
    # TIMESTAMP END 2026-11-02T10:34:57-05:00 | REVISION R004764
            'model_variant': 'proposed-step-lap' if is_proposed else 'baseline',
            'scope': 'Nominal exported geometry within stated numerical tolerances. Full assembly sequence, fabrication clearances and structural capacity are not verified.',
            'tolerances': {'containment_inset_m': DISTANCE_TOLERANCE_M, 'section_area_m2': AREA_TOLERANCE_M2,
                           'convex_volume_difference_m3': VOLUME_TOLERANCE_M3, 'minimum_triangle_area_m2': FACE_AREA_MIN_M2,
                           'section_event_offset_m': SECTION_EVENT_OFFSET_M, 'section_coordinate_scale': SECTION_SCALE},
            'methods': {'containment': 'Positive-volume cavity components are partitioned into disjoint convex cells when concave or shared by multiple mates. Every cell is proved inside its actual source cavity; volume conservation rejects missing cells. Winding-confirmed mate interior points and clipped boundary triangles prove mating coverage, excluding the explicit 1e-8 m tolerance shell.',
                        'completeness': 'Independently reconstruct all 104 timber envelopes from saved prejoinery halfspaces. Prove every envelope cell lies in final timber wood or exported cavity, conserve partition volume, and check every cavity vertex lies inside its original envelope. The 16 declared exterior two-inch brace stop trims are applied explicitly. This detects unexported overcuts, omitted cavities and undersized cavity diagnostics.',
                        'sampling': 'Independent solid-angle winding numbers for deterministic scrambled Sobol points and inward-offset triangle centroids.',
                        'sections': 'Canonical bay coordinates; scaled Clipper2 2D differences/intersections on three axes, just above/below vertex events and at interval quartiles. Exact coplanar boundary planes are excluded.',
                        # TIMESTAMP START 2026-11-02T10:34:57-05:00 | REVISION R004764
                        'raw_surfaces': 'Project original mesh triangles to common planes and use scaled 2D polygon intersections. Positive-area coincident patches fail whether normals are opposed or same-facing; edge/point contact is permitted. This detects surface folds and duplicate patches that signed-volume/solid-occupancy checks can cancel.',
                        'hull_conditioning': 'Convex verification cells use physical halfspaces and volume directly, avoiding numerical winding artifacts from artificial hull triangulations. Qhull uses deterministic centered, axis-scaled and principal-axis affine fallback frames with default/exact-merge options. Exported source surfaces still require raw topology, winding and signed-volume validation; nonconvex source partitions must recover their original signed volume. No random jitter, vertex perturbation, discarded cells or enlarged fit tolerances are used.',
                        # TIMESTAMP END 2026-11-02T10:34:57-05:00 | REVISION R004764
                        'legacy_residuals': 'Legacy 3D unfilled Boolean meshes may have negative volumes and rotation-dependent artifacts. They are diagnostics, not evidence of physical gaps.'},
            'summary': summary, 'failures': failures, 'timber_meshes': topology, 'cavities': rows,
            'wood_pair_sections': pairs, 'no_cavity_stock_completeness': no_cavity_stock,
            'legacy_residual_diagnostics': legacy}
    # TIMESTAMP END 2026-11-02T10:08:45-05:00 | REVISION R004761


# TIMESTAMP START 2026-11-02T11:39:39-05:00 | REVISION R004772
def report_invariants(report, label):
    """Validate proof evidence and retain portable physical/provenance invariants.

    Qhull may subdivide the same convex region differently across platforms.
    Centroids, partition order and diagnostic cell counts need not match, but
    every saved and recomputed proof must independently satisfy its unchanged
    physical bounds. Source hashes, audit policy and physical inventory are exact.
    """
    assert report.get('status') == 'PASS', f'{label}.status={report.get("status")!r}; failures={report.get("failures")!r}'

    def require_fields(value, fields, path):
        assert isinstance(value, dict), f'{path}: missing proof record'
        missing = set(fields.split()) - value.keys()
        assert not missing, f'{path}: missing required proof fields {sorted(missing)!r}'

    def require_mesh(mesh, path):
        require_fields(mesh, 'status failures vertices triangles connected_surfaces minimum_triangle_area_m2 signed_volume_m3 raw_surface_check', path)
        require_fields(mesh['raw_surface_check'], 'status coplanar_pairs_tested overlap_pairs opposed_overlap_pair_count max_overlap_area_m2 sum_pair_overlap_area_m2 plane_tolerance_m positive_area_tolerance_m2', path + '.raw_surface_check')

    def require_stock(stock, path):
        require_fields(stock, 'status reference_envelope_volume_in3 max_cavity_vertex_outside_reference_stock_m partition_planes convex_cells verified_cells cells_in_final_receiver_wood cells_in_exported_cavity partition_volume_balance_error_m3 max_interior_boundary_area_m2 failures declared_external_trim scope', path)

    def require_coverage(proof, path, source_component=False):
        require_fields(proof, 'status coverage_mode', path)
        mode = proof['coverage_mode']
        if mode == 'one convex cell':
            require_fields(proof, 'mate volume_in3 interior_boundary_area_m2 centroid_margin_m', path)
        elif mode in {'explicit convex partition', 'nonconvex surface partition'}:
            require_fields(proof, 'partition_planes partition_cells partition_volume_balance_error_m3 cells note', path)
            require_fields(proof, 'volume_in3' if mode == 'explicit convex partition' else 'excluded_hull_cells', path)
            for index, cell in enumerate(proof['cells']):
                require_coverage(cell, f'{path}.cells[{index}]')
        else:
            raise AssertionError(f'{path}: unknown coverage mode {mode!r}')
        if source_component and mode != 'nonconvex surface partition':
            require_fields(proof, 'convex_volume_error_m3', path)

    require_fields(report, 'schema_version model_sha256 cavity_sha256 model_variant scope methods tolerances status summary failures timber_meshes cavities wood_pair_sections no_cavity_stock_completeness', label)
    for name, mesh in report['timber_meshes'].items():
        require_mesh(mesh, f'{label}.timber_meshes.{name}')
    for index, row in enumerate(report['cavities']):
        path = f'{label}.cavities[{index}]'
        require_fields(row, 'id status mesh_check components winding_samples cross_sections receiver_stock_completeness', path)
        require_mesh(row['mesh_check'], path + '.mesh_check')
        require_stock(row['receiver_stock_completeness'], path + '.receiver_stock_completeness')
        require_fields(row['cross_sections'], 'status sections max_missing_area_m2 max_receiver_overlap_area_m2', path + '.cross_sections')
        require_fields(row['winding_samples'], 'interior_points occupied_by_mates unoccupied inside_receiver', path + '.winding_samples')
        assert row['cross_sections']['sections'] > 0, path + ': no cavity section checks'
        samples = row['winding_samples']
        assert samples['interior_points'] == samples['occupied_by_mates'] > 0, path + ': incomplete winding evidence'
        for component_index, proof in enumerate(row['components']):
            require_coverage(proof, f'{path}.components[{component_index}]', source_component=True)
    for name, stock in report['no_cavity_stock_completeness'].items():
        require_stock(stock, f'{label}.no_cavity_stock_completeness.{name}')
    require_fields(report['wood_pair_sections'], 'status pairs_considered positive_extent_bounds_candidates sections max_overlap_area_m2 failures scope', label + '.wood_pair_sections')
    upper_bounds = {
        'convex_volume_error_m3': VOLUME_TOLERANCE_M3,
        'partition_volume_balance_error_m3': VOLUME_TOLERANCE_M3,
        'interior_boundary_area_m2': AREA_TOLERANCE_M2,
        'max_interior_boundary_area_m2': AREA_TOLERANCE_M2,
        'max_missing_area_m2': AREA_TOLERANCE_M2,
        'max_missing_section_area_m2': AREA_TOLERANCE_M2,
        'max_receiver_overlap_area_m2': AREA_TOLERANCE_M2,
        'max_receiver_overlap_section_area_m2': AREA_TOLERANCE_M2,
        'max_overlap_area_m2': AREA_TOLERANCE_M2,
        'max_wood_overlap_section_area_m2': AREA_TOLERANCE_M2,
        'max_raw_timber_triangle_overlap_area_m2': AREA_TOLERANCE_M2,
        'max_cavity_vertex_outside_reference_stock_m': DISTANCE_TOLERANCE_M,
        'max_cavity_outside_reference_stock_m': DISTANCE_TOLERANCE_M,
    }
    zero_counts = {'unoccupied', 'inside_receiver', 'winding_unoccupied_points',
                   'winding_points_in_receiver', 'timbers_with_raw_surface_overlaps',
                   'opposed_overlap_pair_count'}

    def validate(value, path):
        if isinstance(value, dict):
            if 'status' in value:
                assert value['status'] == 'PASS', f'{path}.status={value["status"]!r}'
            for key, item in value.items():
                location = path + '.' + key
                if key in upper_bounds:
                    assert isinstance(item, (int, float)) and 0 <= item <= upper_bounds[key], (
                        f'{location}={item!r}; required 0 <= value <= {upper_bounds[key]!r}')
                if key in zero_counts:
                    assert item == 0, f'{location}={item!r}; required zero'
                if key in {'failures', 'overlap_pairs'}:
                    assert item == [], f'{location}={item!r}; required no failures'
                if key == 'centroid_margin_m':
                    assert item > DISTANCE_TOLERANCE_M, f'{location}={item!r}; required > {DISTANCE_TOLERANCE_M!r}'
                if key == 'minimum_triangle_area_m2':
                    assert item > FACE_AREA_MIN_M2, f'{location}={item!r}; degenerate triangle'
                if key in {'signed_volume_m3', 'volume_in3'}:
                    assert item > 0, f'{location}={item!r}; required positive volume'
                validate(item, location)
            if 'verified_cells' in value:
                assert value['verified_cells'] == value['convex_cells'], f'{path}: unverified stock cells'
                assert value['cells_in_final_receiver_wood'] + value['cells_in_exported_cavity'] == value['convex_cells'], (
                    f'{path}: stock cells lack complete occupancy evidence')
            if 'partition_cells' in value:
                assert value['partition_cells'] == len(value.get('cells', [])) > 0, f'{path}: missing partition proof cells'
                if 'volume_in3' in value and all('volume_in3' in cell for cell in value['cells']):
                    residual = abs(sum(cell['volume_in3'] for cell in value['cells']) - value['volume_in3']) * INCH ** 3
                    assert residual <= VOLUME_TOLERANCE_M3, f'{path}: partition volume residual={residual!r}'
        elif isinstance(value, list):
            for index, item in enumerate(value):
                validate(item, f'{path}[{index}]')
        elif isinstance(value, float):
            assert math.isfinite(value), f'{path}={value!r}; required finite value'

    # Legacy residual artifacts are explicitly diagnostics, never fit evidence.
    for key in ('failures', 'summary', 'timber_meshes', 'cavities', 'wood_pair_sections', 'no_cavity_stock_completeness'):
        validate(report[key], label + '.' + key)
    assert report['failures'] == [], f'{label}.failures={report["failures"]!r}'
    summary = report['summary']
    assert summary['components_covered'] == summary['connected_cavity_components'], f'{label}: uncovered cavity components'
    assert summary['all_timber_stock_envelopes_verified'] == summary['timbers'], f'{label}: unverified stock envelopes'
    assert summary['receiver_stock_envelopes_verified'] == summary['nonempty_cavity_sets'], f'{label}: unverified receiver stocks'
    assert summary['no_cavity_stock_envelopes_verified'] + summary['receiver_stock_envelopes_verified'] == summary['timbers'], (
        f'{label}: stock inventory does not cover all timbers')
    for key in ('cavity_cross_sections', 'wood_pair_cross_sections', 'raw_timber_coplanar_triangle_pairs_tested'):
        assert summary[key] > 0, f'{label}.summary.{key}={summary[key]!r}; required actual checks'

    def mesh_inventory(mesh):
        result = {key: mesh[key] for key in ('vertices', 'triangles', 'connected_surfaces')}
        result['raw_surface_policy'] = {key: mesh['raw_surface_check'][key]
                                        for key in ('plane_tolerance_m', 'positive_area_tolerance_m2')}
        return result

    cavity_inventory = {row['id']: {'mesh': mesh_inventory(row['mesh_check']), 'components': len(row['components'])}
                        for row in report['cavities']}
    assert len(cavity_inventory) == len(report['cavities']) == summary['nonempty_cavity_sets'], f'{label}: duplicate/missing cavity IDs'
    assert sum(row['components'] for row in cavity_inventory.values()) == summary['connected_cavity_components'], (
        f'{label}: missing cavity component proofs')
    assert len(report['timber_meshes']) == summary['timbers'], f'{label}: missing timber mesh proofs'
    assert len(report['no_cavity_stock_completeness']) == summary['no_cavity_stock_envelopes_verified'], (
        f'{label}: missing no-cavity stock proofs')
    assert sum(coverage_leaf_count(component) for row in report['cavities'] for component in row['components']) == summary['verified_convex_cells'], (
        f'{label}: convex proof count disagrees with its summary')
    assert sum(row['receiver_stock_completeness']['verified_cells'] for row in report['cavities']) == summary['receiver_stock_convex_cells_verified'], (
        f'{label}: stock proof count disagrees with its summary')
    invariants = {key: report[key] for key in ('schema_version', 'model_sha256', 'cavity_sha256',
                                              'model_variant', 'scope', 'methods', 'tolerances')}
    invariants['inventory'] = {key: summary[key] for key in (
        'timbers', 'nonempty_cavity_sets', 'connected_cavity_components', 'components_covered',
        'receiver_stock_envelopes_verified', 'no_cavity_stock_envelopes_verified',
        'all_timber_stock_envelopes_verified', 'declared_exterior_brace_trims')}
    invariants['timbers'] = {name: mesh_inventory(row) for name, row in report['timber_meshes'].items()}
    invariants['cavities'] = cavity_inventory
    invariants['no_cavity_stock_ids'] = sorted(report['no_cavity_stock_completeness'])
    invariants['wood_pairs_considered'] = report['wood_pair_sections']['pairs_considered']
    return invariants


def assert_equivalent_audit_report(saved, actual, path='report'):
    """Compare exact provenance and complete passing proof, not artificial cells."""
    expected = report_invariants(saved, path + '.saved')
    observed = report_invariants(actual, path + '.actual')

    def compare(old, new, location):
        if isinstance(new, dict):
            assert isinstance(old, dict) and old.keys() == new.keys(), f'{location}: saved/actual fields differ'
            for key in new:
                compare(old[key], new[key], location + '.' + key)
        else:
            assert old == new, f'{location}: saved={old!r}; actual={new!r}'

    compare(expected, observed, path)


def assert_equivalent_report(saved, actual, path='report'):
    """Generic numeric JSON comparison retained for auxiliary regeneration tests."""
    if isinstance(actual, dict):
        assert isinstance(saved, dict) and saved.keys() == actual.keys(), path + ': report fields differ'
        for key in actual:
            assert_equivalent_report(saved[key], actual[key], path + '.' + key)
    elif isinstance(actual, list):
        assert isinstance(saved, list) and len(saved) == len(actual), path + ': report list differs'
        for index, (old, new) in enumerate(zip(saved, actual)):
            assert_equivalent_report(old, new, path + '[' + str(index) + ']')
    elif isinstance(actual, float):
        assert isinstance(saved, (int, float)) and math.isfinite(saved), path + ': invalid number'
        assert math.isclose(saved, actual, rel_tol=1e-10, abs_tol=1e-12), f'{path}: saved={saved!r}; actual={actual!r}'
    else:
        assert saved == actual, f'{path}: saved={saved!r}; actual={actual!r}'
# TIMESTAMP END 2026-11-02T11:39:39-05:00 | REVISION R004772


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model', type=Path, default=ROOT / 'src/model-data.json')
    parser.add_argument('--cavities', type=Path, default=ROOT / 'src/cavity-data.json')
    parser.add_argument('--output', type=Path, default=ROOT / 'docs/cavity-fit-audit.json')
    parser.add_argument('--check', action='store_true', help='Compare the committed report without writing it.')
    args = parser.parse_args()
    model_raw, cavity_raw = args.model.read_bytes(), args.cavities.read_bytes()
    model, cavities = json.loads(model_raw), json.loads(cavity_raw)
    model_sha, cavity_sha = hashlib.sha256(model_raw).hexdigest(), hashlib.sha256(cavity_raw).hexdigest()
    report = audit(model, cavities)
    report.update(model_sha256=model_sha, cavity_sha256=cavity_sha)
    if cavities.get('source_model_sha256') != model_sha:
        report['status'] = 'FAIL'
        report['failures'].append('cavity source-model hash mismatch')
    output = json.dumps(report, indent=2, sort_keys=True) + '\n'
    # TIMESTAMP START 2026-11-02T11:39:39-05:00 | REVISION R004772
    # Emit the actual audit outcome before any saved-report mismatch diagnostic.
    print(json.dumps({'status': report['status'], 'summary': report['summary'], 'failures': report['failures']}, sort_keys=True), flush=True)
    # TIMESTAMP END 2026-11-02T11:39:39-05:00 | REVISION R004772
    if args.check:
        # TIMESTAMP START 2026-11-02T11:39:39-05:00 | REVISION R004772
        assert report['status'] == 'PASS', f'actual audit failed: {report["failures"]!r}'
        # TIMESTAMP END 2026-11-02T11:39:39-05:00 | REVISION R004772
        # TIMESTAMP START 2026-11-02T11:39:39-05:00 | REVISION R004772
        assert_equivalent_audit_report(json.loads(args.output.read_text()), report)
        # TIMESTAMP END 2026-11-02T11:39:39-05:00 | REVISION R004772
    else:
        args.output.write_text(output)
    # TIMESTAMP START 2026-11-02T11:39:39-05:00 | REVISION R004772
    assert report['status'] == 'PASS', f'actual audit failed: {report["failures"]!r}'
    # TIMESTAMP END 2026-11-02T11:39:39-05:00 | REVISION R004772


if __name__ == '__main__':
    main()
# TIMESTAMP END 2026-11-02T09:09:22-05:00 | REVISION R004752
