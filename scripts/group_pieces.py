#!/usr/bin/env python3
"""Conservative fitted-timber congruence certificates, using only the stdlib.

The source model is never modified.  Mesh tessellation is NOT an identity key.
A member joins a group only after its complete triangular boundary is covered
bidirectionally under a proper rigid transform, preserving labelled A/B ends.

For each source triangle we subtract the union of projected destination
triangles.  A second pass uses a convex polygon contained in the Euclidean
epsilon-neighbourhood of each destination triangle.  Every accepted convex
covered fragment has a maximum-distance upper bound: distance to one convex
destination triangle is convex, so checking ALL fragment vertices bounds the
whole fragment.  Thus this is not a vertex-only or sampled-surface comparison.
Uncovered area, incompatible normals, or an exceeded residual rejects a match.

Frames use the labelled A->B axis and projected edges of the A reference face.
Their third vector is a cross product: determinant +1, never a reflection.
Candidate search is conservative, not a complete general rigid-registration
solver.  Different reference conventions, noisy meshes, or pathological
triangles can cause false splits.  Nothing here establishes manufacturability,
structural capacity, stock grading, tolerances, or an erection sequence.
"""

import argparse
import hashlib
import json
import math
from pathlib import Path


NUMERICAL_SLACK_M = 1e-10
MIN_TRIANGLE_AREA_M2 = 1e-24
MAX_FRAGMENTS = 20000


def add(a, b): return tuple(x + y for x, y in zip(a, b))
def sub(a, b): return tuple(x - y for x, y in zip(a, b))
def mul(a, s): return tuple(x * s for x in a)
def dot(a, b): return sum(x * y for x, y in zip(a, b))
def cross(a, b): return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])
def norm(a): return math.sqrt(dot(a, a))
def unit(a):
    length = norm(a)
    if length <= 1e-15:
        raise ValueError('Degenerate direction')
    return mul(a, 1/length)


def triangle_distance(p, tri):
    """Exact point-to-closed-triangle distance (Voronoi-region algorithm)."""
    a, b, c = tri
    ab, ac, ap = sub(b, a), sub(c, a), sub(p, a)
    d1, d2 = dot(ab, ap), dot(ac, ap)
    if d1 <= 0 and d2 <= 0: return norm(ap)
    bp = sub(p, b)
    d3, d4 = dot(ab, bp), dot(ac, bp)
    if d3 >= 0 and d4 <= d3: return norm(bp)
    vc = d1*d4-d3*d2
    if vc <= 0 and d1 >= 0 and d3 <= 0:
        return norm(sub(p, add(a, mul(ab, d1/(d1-d3)))))
    cp = sub(p, c)
    d5, d6 = dot(ab, cp), dot(ac, cp)
    if d6 >= 0 and d5 <= d6: return norm(cp)
    vb = d5*d2-d1*d6
    if vb <= 0 and d2 >= 0 and d6 <= 0:
        return norm(sub(p, add(a, mul(ac, d2/(d2-d6)))))
    va = d3*d6-d5*d4
    if va <= 0 and d4-d3 >= 0 and d5-d6 >= 0:
        return norm(sub(p, add(b, mul(sub(c, b), (d4-d3)/((d4-d3)+(d5-d6))))))
    denominator = va+vb+vc
    if denominator == 0:
        raise ValueError('Numerically degenerate triangle')
    q = add(a, add(mul(ab, vb/denominator), mul(ac, vc/denominator)))
    return norm(sub(p, q))


def signed_area(poly):
    return sum(a[0]*b[1]-a[1]*b[0] for a, b in zip(poly, poly[1:]+poly[:1]))/2


def clean(poly):
    result = []
    for point in poly:
        if not result or norm(sub(point, result[-1])) > 1e-13:
            result.append(point)
    if len(result) > 1 and norm(sub(result[0], result[-1])) <= 1e-13:
        result.pop()
    return result


def clip(poly, a, b, sign=1):
    """Clip a convex polygon to a closed half-plane, no epsilon expansion."""
    if not poly: return []
    edge = sub(b, a)
    def side(p): return sign*(edge[0]*(p[1]-a[1])-edge[1]*(p[0]-a[0]))
    out = []
    previous, old_d = poly[-1], side(poly[-1])
    for current in poly:
        new_d = side(current)
        if (old_d >= 0) != (new_d >= 0):
            t = old_d/(old_d-new_d)
            out.append(add(previous, mul(sub(current, previous), t)))
        if new_d >= 0: out.append(current)
        previous, old_d = current, new_d
    return clean(out)


def subtract_convex(poly, cutter):
    """Outside fragments, intersection, and tiny fragments needing proof.

    Small area alone is never accepted as evidence of proximity: a needle
    can have tiny area but long extent.  The caller must distance-bound all
    vertices of each tiny fragment, or retain it for subsequent coverage.
    """
    remainder = []
    tiny = []
    inside = poly
    for a, b in zip(cutter, cutter[1:]+cutter[:1]):
        if not inside: break
        outside = clip(inside, a, b, -1)
        if len(outside) >= 3 and abs(signed_area(outside)) > MIN_TRIANGLE_AREA_M2:
            remainder.append(outside)
        elif outside:
            tiny.append(outside)
        inside = clip(inside, a, b, 1)
    return remainder, inside, tiny


def convex_hull(points):
    points = sorted(set(points))
    def turn(a, b, c): return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
    lower, upper = [], []
    for p in points:
        while len(lower) >= 2 and turn(lower[-2], lower[-1], p) <= 0: lower.pop()
        lower.append(p)
    for p in reversed(points):
        while len(upper) >= 2 and turn(upper[-2], upper[-1], p) <= 0: upper.pop()
        upper.append(p)
    return lower[:-1]+upper[:-1]


def expanded_triangle(poly, radius):
    # Minkowski sum with an INSCRIBED regular 16-gon.  Every point is at
    # most radius from the original triangle; acute corners cannot overshoot.
    return convex_hull([add(p, (radius*math.cos(k*math.pi/8), radius*math.sin(k*math.pi/8)))
                        for p in poly for k in range(16)])


def bbox(points):
    return tuple(min(p[i] for p in points) for i in range(len(points[0]))), tuple(max(p[i] for p in points) for i in range(len(points[0])))


def boxes_overlap(a, b, epsilon=0):
    return all(a[0][i] <= b[1][i]+epsilon and b[0][i] <= a[1][i]+epsilon for i in range(len(a[0])))


def mesh(vertices, indices):
    triangles, area, volume = [], 0.0, 0.0
    origin = vertices[0]
    for index in indices:
        tri = tuple(tuple(vertices[k]) for k in index)
        normal = cross(sub(tri[1], tri[0]), sub(tri[2], tri[0]))
        twice_area = norm(normal)
        if twice_area/2 <= MIN_TRIANGLE_AREA_M2:
            raise ValueError('Degenerate input triangle; no grouping certificate issued')
        triangles.append({'points': tri, 'normal': mul(normal, 1/twice_area), 'bbox': bbox(tri)})
        area += twice_area/2
        volume += dot(sub(tri[0], origin), cross(sub(tri[1], origin), sub(tri[2], origin)))/6
    return {'triangles': triangles, 'bbox': bbox(vertices), 'area': area, 'volume': abs(volume)}


def coverage(source, destination, tolerance):
    """Bound ALL source triangles' distance to the destination boundary."""
    bound = 0.0
    plane_limit = (tolerance-NUMERICAL_SLACK_M)/math.sqrt(2)
    radius = plane_limit
    covered_fragments = 0
    for triangle_number, item in enumerate(source['triangles']):
        tri, normal = item['points'], item['normal']
        # Use the longest edge for a stable planar coordinate basis.
        edges = [sub(tri[(k+1)%3], tri[k]) for k in range(3)]
        u = unit(max(edges, key=norm))
        v = cross(normal, u)
        origin = tri[0]
        def project(p):
            q = sub(p, origin)
            return (dot(q, u), dot(q, v))
        def unproject(p): return add(origin, add(mul(u, p[0]), mul(v, p[1])))
        poly = [project(p) for p in tri]
        if signed_area(poly) < 0: poly.reverse()
        candidates = []
        for other in destination['triangles']:
            if not boxes_overlap(item['bbox'], other['bbox'], tolerance): continue
            if dot(normal, other['normal']) < 0.9: continue
            if max(abs(dot(sub(p, origin), normal)) for p in other['points']) > plane_limit: continue
            projected = [project(p) for p in other['points']]
            if signed_area(projected) < 0: projected.reverse()
            candidates.append((other['points'], projected))
        if not candidates:
            return None, {'reason': 'no compatible destination surface', 'triangle': triangle_number}
        remaining = [poly]
        for expanded in (False, True):
            for other_points, projected in candidates:
                cutter = expanded_triangle(projected, radius) if expanded else projected
                cutter_bounds = bbox(cutter)
                next_remaining = []
                for fragment in remaining:
                    if not boxes_overlap(bbox(fragment), cutter_bounds):
                        next_remaining.append(fragment)
                        continue
                    outside, inside, tiny = subtract_convex(fragment, cutter)
                    if inside:
                        residual = max(triangle_distance(unproject(p), other_points) for p in inside)
                        # Convexity gives an upper bound on the ENTIRE fragment.
                        if residual+NUMERICAL_SLACK_M > tolerance:
                            next_remaining.append(fragment)
                            continue
                        bound = max(bound, residual+NUMERICAL_SLACK_M)
                        covered_fragments += 1
                    for small in tiny:
                        residual = max(triangle_distance(unproject(p), other_points) for p in small)
                        if residual+NUMERICAL_SLACK_M <= tolerance:
                            bound = max(bound, residual+NUMERICAL_SLACK_M)
                            covered_fragments += 1
                        else:
                            # Retain even zero-area fragments unless their
                            # full extent has a valid convex-distance bound.
                            next_remaining.append(small)
                    next_remaining.extend(outside)
                remaining = next_remaining
                if not remaining: break
                if len(remaining) > MAX_FRAGMENTS:
                    return None, {'reason': 'conservative fragmentation limit', 'triangle': triangle_number}
            if not remaining: break
        if remaining:
            return None, {'reason': 'uncovered source surface', 'triangle': triangle_number,
                          'uncovered_area_m2': sum(abs(signed_area(p)) for p in remaining)}
    return bound, {'source_triangle_count': len(source['triangles']), 'covered_convex_fragments': covered_fragments}


def references(part):
    result = {}
    for end in ('A', 'B'):
        identifier = part['id']+'-'+end
        face = next((f for f in part['reference_end_faces'] if f['id'] == identifier), None)
        if face is None: raise ValueError('Missing exact reference end '+identifier)
        result[end] = face
    return result


def frames(part):
    origin = tuple(part['axis_start'])
    axis = unit(sub(part['axis_end'], origin))
    vertices = references(part)['A']['vertices']
    result = []
    for a, b in zip(vertices, vertices[1:]+vertices[:1]):
        edge = sub(b, a)
        transverse = sub(edge, mul(axis, dot(edge, axis)))
        if norm(transverse) <= 1e-10: continue
        transverse = unit(transverse)
        third = unit(cross(axis, transverse))
        transverse = cross(third, axis)
        frame = (axis, transverse, third)
        if not any(dot(transverse, old[1]) > 1-1e-14 for old in result): result.append(frame)
    if not result: raise ValueError('No usable A-reference frame: '+part['id'])
    return result


def transform(source_part, source_frame, target_part, target_frame):
    # Matrix maps source coordinates to target coordinates: T * S^transpose.
    rotation = tuple(tuple(sum(target_frame[k][i]*source_frame[k][j] for k in range(3))
                           for j in range(3)) for i in range(3))
    apply_rotation = lambda p: tuple(dot(row, p) for row in rotation)
    translation = sub(target_part['axis_start'], apply_rotation(source_part['axis_start']))
    def apply(p): return add(apply_rotation(p), translation)
    determinant = dot(rotation[0], cross(rotation[1], rotation[2]))
    if abs(determinant-1) > 1e-10: raise ValueError('Non-proper transform')
    return apply, rotation, translation, determinant


def reference_residual(source_part, destination_part, apply):
    sa, da = references(source_part), references(destination_part)
    worst = 0.0
    for end in ('A', 'B'):
        source = [apply(p) for p in sa[end]['vertices']]
        target = da[end]['vertices']
        if len(source) != len(target): return math.inf
        # Reference quads are metadata, separately from complete fitted surfaces.
        worst = max(worst, max(min(norm(sub(a, b)) for b in target) for a in source),
                    max(min(norm(sub(a, b)) for a in source) for b in target))
    return worst


def compare(source_part, destination_part, source_mesh, destination_mesh, tolerance):
    if abs(norm(sub(source_part['axis_end'], source_part['axis_start']))-
           norm(sub(destination_part['axis_end'], destination_part['axis_start']))) > tolerance:
        return None, 'different labelled-axis lengths'
    if abs(source_mesh['volume']-destination_mesh['volume']) > tolerance*(source_mesh['area']+destination_mesh['area']):
        return None, 'different fitted volumes'
    target_frame = frames(destination_part)[0]
    reason = 'no reference-compatible proper rotation'
    for source_frame in frames(source_part):
        apply, rotation, translation, determinant = transform(source_part, source_frame, destination_part, target_frame)
        end_residual = reference_residual(source_part, destination_part, apply)
        if end_residual > tolerance: continue
        vertices = [apply(p) for p in source_part['vertices']]
        bounds = bbox(vertices)
        if any(abs(bounds[k][i]-destination_mesh['bbox'][k][i]) > tolerance for k in range(2) for i in range(3)):
            reason = 'different fitted boundary extents'
            continue
        transformed = mesh(vertices, source_part['triangles'])
        forward, forward_info = coverage(transformed, destination_mesh, tolerance)
        if forward is None:
            reason = forward_info['reason']
            continue
        reverse, reverse_info = coverage(destination_mesh, transformed, tolerance)
        if reverse is None:
            reason = reverse_info['reason']
            continue
        return {'rotation_to_representative': rotation, 'translation_to_representative_m': translation,
                'rotation_determinant': determinant, 'reference_end_max_residual_m': end_residual,
                'surface_max_residual_bound_m': max(forward, reverse),
                'member_to_representative': forward_info, 'representative_to_member': reverse_info}, None
    return None, reason


def group_model(model, tolerance):
    parts = model['parts']
    ids = [p['id'] for p in parts]
    if len(ids) != len(set(ids)): raise ValueError('Duplicate timber IDs')
    meshes = {p['id']: mesh(p['vertices'], p['triangles']) for p in parts}
    groups = []
    member_tolerance = tolerance/2
    for part in parts:
        match, group = None, None
        for possible in groups:
            representative = possible['_representative']
            match, _ = compare(part, representative, meshes[part['id']], meshes[representative['id']], member_tolerance)
            if match is not None:
                group = possible
                break
        if group is None:
            group = {'group_number': len(groups)+1, 'representative_id': part['id'], '_representative': part,
                     'members': [], 'source_categories': [], 'quantity': 0, 'max_residual_bound_m': 0.0}
            groups.append(group)
            match = {'rotation_to_representative': ((1,0,0),(0,1,0),(0,0,1)),
                     'translation_to_representative_m': (0,0,0), 'rotation_determinant': 1,
                     'reference_end_max_residual_m': 0.0, 'surface_max_residual_bound_m': 0.0,
                     'member_to_representative': {'identity': True}, 'representative_to_member': {'identity': True}}
        if part['group'] not in group['source_categories']: group['source_categories'].append(part['group'])
        group['members'].append({'timber_id': part['id'], 'end_A_reference_id': part['id']+'-A',
                                 'end_B_reference_id': part['id']+'-B', **match})
        group['quantity'] += 1
        group['max_residual_bound_m'] = max(group['max_residual_bound_m'], match['surface_max_residual_bound_m'])
        print(f"{part['id']:6} -> G{group['group_number']:02}  residual bound {match['surface_max_residual_bound_m']*1e6:.6f} um", flush=True)
    for group in groups:
        group.pop('_representative')
        group['timber_ids'] = [m['timber_id'] for m in group['members']]
        group['pairwise_residual_bound_m'] = 2*group['max_residual_bound_m']
        group['id'] = f"M{group['group_number']:02}"
        group['number'] = group['group_number']
        group['member_ids'] = group['timber_ids']
        group['family'] = group['source_categories'][0]
        group['label'] = next(g['label'] for g in model['groups'] if g['id'] == group['family'])
        representative = group['representative_id']
        if group['family'] == 'cupola_bands':
            group['label'] = {'L':'Cupola lower band','S':'Cupola window sill band','H':'Cupola window head band'}[representative.rsplit('-',1)[1]]
        elif group['family'] in ('braces','secondary_approx'):
            group['label'] += ' — '+representative.rsplit('-',1)[1]+' hand/layout'
        group['max_residual_m'] = group['max_residual_bound_m']
        group['status'] = 'prototype_geometry_repeat'
        group['method'] = 'proper_rigid_full_surface_coverage_AB_preserved'
    return groups, meshes


def synthetic_tests():
    """Real invariance/handedness checks, independent of the model's repeats."""
    base = {'id':'S', 'axis_start':[0,0,0], 'axis_end':[2,0,0],
            'vertices':[[0,0,0],[2,0,0],[0,.6,0],[.2,.15,1]],
            'triangles':[[0,2,1],[0,1,3],[1,2,3],[2,0,3]],
            'reference_end_faces':[
                {'id':'S-A','vertices':[[0,-.2,-.3],[0,.2,-.3],[0,.2,.3],[0,-.2,.3]]},
                {'id':'S-B','vertices':[[2,-.2,-.3],[2,.2,-.3],[2,.2,.3],[2,-.2,.3]]}]}
    def transformed(fn):
        p = json.loads(json.dumps(base))
        for key in ('axis_start','axis_end'): p[key] = fn(p[key])
        p['vertices'] = [fn(v) for v in p['vertices']]
        for end in p['reference_end_faces']: end['vertices'] = [fn(v) for v in end['vertices']]
        return p
    theta = .713
    moved = transformed(lambda p: (math.cos(theta)*p[0]-math.sin(theta)*p[1]+3.1,
                                   math.sin(theta)*p[0]+math.cos(theta)*p[1]-.7, p[2]+2.3))
    mirrored = transformed(lambda p: (p[0],-p[1],p[2]))
    mirrored['triangles'] = [list(reversed(t)) for t in mirrored['triangles']]
    retessellated = json.loads(json.dumps(base))
    a,b,c = [base['vertices'][k] for k in base['triangles'][0]]
    retessellated['vertices'].append(mul(add(add(a,b),c),1/3))
    retessellated['triangles'] = [[0,2,4],[2,1,4],[1,0,4]]+base['triangles'][1:]
    altered = json.loads(json.dumps(base))
    altered['vertices'][3][2] += .001
    reversed_ends = json.loads(json.dumps(base))
    reversed_ends['axis_start'], reversed_ends['axis_end'] = reversed_ends['axis_end'], reversed_ends['axis_start']
    ra, rb = reversed_ends['reference_end_faces']
    ra['vertices'], rb['vertices'] = rb['vertices'], ra['vertices']
    original_mesh = mesh(base['vertices'], base['triangles'])
    results = []
    for name, candidate, should_match in [('rigid rotation and translation',moved,True),
                                         ('different tessellation',retessellated,True),
                                         ('asymmetric mirror excluded',mirrored,False),
                                         ('changed fitted geometry excluded',altered,False),
                                         ('labelled A/B end reversal excluded',reversed_ends,False)]:
        result, reason = compare(candidate,base,mesh(candidate['vertices'],candidate['triangles']),original_mesh,5e-6)
        assert (result is not None) == should_match, (name,reason)
        results.append({'test':name,'passed':True})
    return results


def main():
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model',type=Path,default=root/'src/model-data.json')
    parser.add_argument('--output',type=Path,default=root/'public/review/piece-groups.json')
    parser.add_argument('--summary',type=Path,default=root/'public/review/piece-groups-summary.md')
    parser.add_argument('--ui-output',type=Path,default=root/'src/material-groups.json')
    parser.add_argument('--tolerance-m',type=float,default=1e-5,
                        help='Maximum GROUP pairwise surface-distance bound, default 0.00001 m (10 micrometres).')
    parser.add_argument('--self-test-only',action='store_true')
    args = parser.parse_args()
    tests = synthetic_tests()
    if args.self_test_only:
        print(json.dumps(tests,indent=2)); return
    if not 1e-8 <= args.tolerance_m <= 1e-4:
        parser.error('Choose a numerical comparison tolerance between 1e-8 and 1e-4 m; not a machining allowance.')
    source = args.model.read_bytes()
    model = json.loads(source)
    if model.get('units') != 'meters': raise ValueError('Expected metre coordinates')
    groups, meshes = group_model(model,args.tolerance_m)
    by_id = {p['id']:p for p in model['parts']}
    handed_checks = []
    for a,b in [('K0-A','K0-B'),('J0-0','J0-2')]:
        if a in by_id and b in by_id:
            result, reason = compare(by_id[a],by_id[b],meshes[a],meshes[b],args.tolerance_m/2)
            handed_checks.append({'member_a':a,'member_b':b,'proper_rotation_match':result is not None,'rejection':reason})
            if result is not None: raise AssertionError('Unexpected handed-pair match; review before using report')
    report = {'schema_version':'fitted-piece-groups-1.0', 'source_sha256':hashlib.sha256(source).hexdigest(),
              'source_units':'meters','timber_count':len(model['parts']),'group_count':len(groups),
              'comparison_tolerance_m':args.tolerance_m,'member_to_representative_tolerance_m':args.tolerance_m/2,
              'numerical_slack_m':NUMERICAL_SLACK_M,
              'max_member_residual_bound_m':max(g['max_residual_bound_m'] for g in groups),
              'max_group_pairwise_residual_bound_m':max(g['pairwise_residual_bound_m'] for g in groups),
              'algorithm':'Proper rigid frames from labelled A->B axis and projected A-reference edges; separately match A/B reference vertices; bidirectional complete triangle coverage by convex polygon subtraction; per-fragment point-to-triangle convexity bounds; no reflection or end reversal.',
              'scope':'Geometric repeat groups of the existing fitted prototype only. No geometry edits and no fabrication or construction approval.',
              'limitations':[
                  'Conservative candidate search can split congruent shapes with different reference conventions; singleton status does not prove uniqueness.',
                  'A and B are preserved, never swapped; braces such as K0-A have end IDs K0-A-A and K0-A-B.',
                  'Tolerance is a numerical geometry comparison threshold, not machining clearance or stock tolerance.',
                  'Boundary comparison assumes the provided consistently oriented, closed fitted-solid meshes; it does not independently validate material properties or topology.',
                  'Floating-point polygon operations use a 0.1 nanometre numerical slack, not formal exact-arithmetic proof.',
                  'Groups use the first source-order member as representative; every member is directly certified to it, with twice the largest residual bounding all member pairs.',
                  'Mate IDs and installation locations remain individual; geometry-equivalent pieces are not assigned interchangeable construction roles.'
              ],'self_tests':tests,'handed_pair_checks':handed_checks,'groups':groups}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    ui_keys = ('id','number','quantity','member_ids','representative_id','family','label',
               'max_residual_m','pairwise_residual_bound_m','status','method')
    ui_report = {key: report[key] for key in ('schema_version','source_sha256','timber_count','group_count',
                                             'comparison_tolerance_m','max_member_residual_bound_m',
                                             'max_group_pairwise_residual_bound_m','scope')}
    ui_report['groups'] = [{key:g[key] for key in ui_keys} for g in groups]
    ui_report['handed_pair_checks'] = handed_checks
    ui_report['reference_end_semantics'] = 'Keep every original timber ID; end A is ID+A suffix and end B is ID+B suffix, with a hyphen before the end letter. No end swapping.'
    args.ui_output.parent.mkdir(parents=True,exist_ok=True)
    args.ui_output.write_text(json.dumps(ui_report,indent=2)+'\n')
    lines = ['# Fitted-piece repeat groups','',
             '**Prototype geometry only — not a cutting list or construction approval.**','',
             f"Source SHA-256: `{report['source_sha256']}`",'',
             f"{report['timber_count']} original timbers; {report['group_count']} conservative groups. "
             f"Requested pairwise tolerance: {args.tolerance_m*1e6:g} micrometres. "
             f"Largest certified member-to-representative surface-distance bound: {report['max_member_residual_bound_m']*1e6:.6f} micrometres. "
             f"Largest group pairwise bound: {report['max_group_pairwise_residual_bound_m']*1e6:.6f} micrometres.",'',
             '| Group | Quantity | Original timber IDs | Maximum residual bound (µm) |',
             '|---|---:|---|---:|']
    for g in groups:
        lines.append(f"| {g['id']} | {g['quantity']} | {', '.join(g['timber_ids'])} | {g['max_residual_bound_m']*1e6:.6f} |")
    lines += ['', 'A→A and B→B are preserved under determinant +1 rigid transforms. No reflection, scaling, or end reversal is permitted. Full fitted triangular surfaces are covered in both directions; differing tessellation is allowed. The JSON records every original ID, both reference-end IDs, transforms and coverage counts.', '',
              'The brace A/B families and the secondary-rafter 0/2 families remain separate because their fitted geometry is handed. Nominal dimensions alone never establish membership.', '',
              'Algorithm: '+report['algorithm'], '', 'Limitations:', '']+[f'- {s}' for s in report['limitations']]
    args.summary.write_text('\n'.join(lines)+'\n')
    print(f"Wrote {args.output} and {args.summary}: {len(groups)} groups",flush=True)


if __name__ == '__main__': main()
