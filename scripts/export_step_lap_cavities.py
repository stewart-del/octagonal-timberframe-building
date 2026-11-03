# TIMESTAMP START 2026-11-02T10:08:45-05:00 | REVISION R004761
"""Derive proposed recesses from corrected baseline recesses and exact transfers.

Only cavity diagnostics are written. Neither timber model is modified. The
separate audit_cavity_fit.py proves mating coverage and stock completeness.
"""
from pathlib import Path
import copy
import hashlib
import json
import re

import manifold3d as m
import numpy as np
from scipy.spatial import ConvexHull

from audit_cavity_fit import INCH, arrays, inspect_mesh, signed_volume, solid
# TIMESTAMP START 2026-11-02T10:50:48-05:00 | REVISION R004767
from step_lap import regular_boundary
# TIMESTAMP END 2026-11-02T10:50:48-05:00 | REVISION R004767

ROOT = Path(__file__).resolve().parents[1]
VOLUME_TOLERANCE_IN3 = 1e-6


def read_json(path):
    raw = path.read_bytes()
    return json.loads(raw), hashlib.sha256(raw).hexdigest()


def shape(record):
    if not record['triangles']:
        return m.Manifold()
    return solid(*arrays(record))


def exported_mesh(manifold):
    mesh = manifold.to_mesh64()
    vertices = np.asarray(mesh.vert_properties)[:, :3]
    faces = np.asarray(mesh.tri_verts, dtype=np.uint64)
    edges = sorted({tuple(sorted((int(face[i]), int(face[(i + 1) % 3]))))
                    for face in faces for i in range(3)})
    result = {'vertices': vertices.tolist(), 'triangles': faces.tolist(),
              'edges': [list(edge) for edge in edges], 'volume_m3': signed_volume(vertices, faces)}
    assert inspect_mesh(vertices, faces)['status'] == 'PASS', 'Invalid proposed cavity surface'
    return result


def expected_interfaces():
    return {(f'J{k}-{side}', f'B{k}') for k in range(8) for side in ('0', '2')} | {
        (f'R{k}', f'P{k}') for k in range(8)}


def verify_reflected_convex(left, right, matrix):
    expected = np.asarray(left['vertices']) @ matrix.T
    actual = np.asarray(right['vertices'])
    for vertices, comparison in ((expected, actual), (actual, expected)):
        equations = ConvexHull(vertices).equations
        assert np.max(comparison @ equations[:, :3].T + equations[:, 3]) <= 1e-9, 'Handed cavity/transfer mismatch'


def build_cavities(baseline, base_cavities, proposed, proposal, hashes):
    baseline_sha, baseline_cavity_sha, proposed_sha, proposal_sha = hashes
    assert base_cavities['source_model_sha256'] == baseline_sha
    assert proposal['baseline_model_sha256'] == baseline_sha
    assert proposed['proposed_review']['baseline_model_sha256'] == baseline_sha
    base_parts = {part['id']: part for part in baseline['parts'] if part['is_timber']}
    new_parts = {part['id']: part for part in proposed['parts'] if part['is_timber']}
    # TIMESTAMP START 2026-11-02T15:15:55-05:00 | REVISION R004802
    assert set(base_parts) == set(new_parts) == set(base_cavities['parts']) and len(base_parts) == 112
    # TIMESTAMP END 2026-11-02T15:15:55-05:00 | REVISION R004802
    variants = proposal['variants']
    assert len(variants) == 24 and len({item['id'] for item in variants}) == 24
    assert {tuple(item['member_ids']) for item in variants} == expected_interfaces()
    changed = {name for pair in expected_interfaces() for name in pair}
    assert len(changed) == 40 and set(proposed['proposed_review']['changed_member_ids']) == changed
    increases, decreases, transfers = {}, {}, []
    for item in variants:
        owner, receiver = item['member_ids']
        assert len(item['added_parts']) == len(item['removed_parts']) == 1
        added, removed = item['added_parts'][0], item['removed_parts'][0]
        assert added['member_id'] == owner and removed['member_id'] == receiver
        assert added['vertices'] == removed['vertices'] and added['triangles'] == removed['triangles']
        vertices, faces = arrays(added)
        check = inspect_mesh(vertices, faces)
        assert check['status'] == 'PASS', (item['id'], 'invalid transfer solid', check)
        volume = signed_volume(vertices, faces)
        assert volume > 0
        increases.setdefault(receiver, []).append(removed)
        decreases.setdefault(owner, []).append(added)
        transfers.append({'id': item['id'], 'retained_by': owner, 'removed_from': receiver,
                          'volume_in3': volume / INCH ** 3})
    # Solve each complete bay-zero cavity once, matching the model generator's
    # quadrant rotations. Each B0 receives both distinct authoritative pockets.
    seeds = {}
    for name in ('B0', 'P0', 'R0', 'J0-0'):
        result = shape(base_cavities['parts'][name]['removed'])
        for addition in increases.get(name, []):
            result = result + shape(addition)
        for restoration in decreases.get(name, []):
            result = result - shape(restoration)
        # TIMESTAMP START 2026-11-02T10:50:48-05:00 | REVISION R004767
        # TIMESTAMP START 2026-11-02T17:32:31-05:00 | REVISION R004820
        candidate = result
        original_volume=result.volume()
        # TIMESTAMP END 2026-11-02T17:32:31-05:00 | REVISION R004820
        raw = candidate.to_mesh64()
        check = inspect_mesh(np.asarray(raw.vert_properties)[:, :3], np.asarray(raw.tri_verts, dtype=np.uint64))
        if check['status'] != 'PASS':
            assert set(check['failures']) == {'positive-area coplanar raw triangle overlap'}, (name, check)
            # The producer cancels signed coplanar folds without changing the
            # solid. The audit remains independent and checks these raw faces.
            candidate = regular_boundary(candidate)
            cleaned = candidate.to_mesh64()
            assert inspect_mesh(np.asarray(cleaned.vert_properties)[:, :3],
                                np.asarray(cleaned.tri_verts, dtype=np.uint64))['status'] == 'PASS', name
        # TIMESTAMP START 2026-11-02T17:32:31-05:00 | REVISION R004820
        assert abs(candidate.volume()-original_volume)/INCH**3<=VOLUME_TOLERANCE_IN3,(name,'raw boundary normalization changed cavity volume')
        # TIMESTAMP END 2026-11-02T17:32:31-05:00 | REVISION R004820
        seeds[name] = candidate
        # TIMESTAMP END 2026-11-02T10:50:48-05:00 | REVISION R004767
    diagonal = np.sqrt(.5)
    reflection = np.array([[diagonal, 0, -diagonal], [0, 1, 0], [-diagonal, 0, -diagonal]])
    verify_reflected_convex(base_cavities['parts']['J0-0']['removed'],
                            base_cavities['parts']['J0-2']['removed'], reflection)
    verify_reflected_convex(decreases['J0-0'][0], decreases['J0-2'][0], reflection)
    seeds['J0-2'] = seeds['J0-0'].transform(np.column_stack([reflection, np.zeros(3)]).tolist())
    output_parts, deltas = {}, []
    for name in base_parts:
        if name not in changed:
            assert base_parts[name]['vertices'] == new_parts[name]['vertices']
            assert base_parts[name]['triangles'] == new_parts[name]['triangles']
            output_parts[name] = {'removed': copy.deepcopy(base_cavities['parts'][name]['removed'])}
            continue
        match = re.fullmatch(r'([A-Z]+)([0-7])(.*)', name)
        seed_name = match[1] + '0' + match[3]
        removed = exported_mesh(seeds[seed_name].rotate((0, int(match[2]) * 45, 0)))
        before = base_cavities['parts'][name]['removed']['volume_m3']
        added_volume = sum(signed_volume(*arrays(item)) for item in increases.get(name, []))
        restored_volume = sum(signed_volume(*arrays(item)) for item in decreases.get(name, []))
        expected = before + added_volume - restored_volume
        error_in3 = abs(removed['volume_m3'] - expected) / INCH ** 3
        assert error_in3 <= VOLUME_TOLERANCE_IN3, (name, 'cavity material-transfer balance', error_in3)
        old_v, old_f = arrays(base_parts[name])
        new_v, new_f = arrays(new_parts[name])
        wood_delta = signed_volume(new_v, new_f) - signed_volume(old_v, old_f)
        assert abs(wood_delta + added_volume - restored_volume) / INCH ** 3 <= VOLUME_TOLERANCE_IN3, name
        output_parts[name] = {'removed': removed}
        deltas.append({'id': name, 'baseline_removed_volume_in3': before / INCH ** 3,
                       'new_pocket_volume_in3': added_volume / INCH ** 3,
                       'restored_tongue_volume_in3': restored_volume / INCH ** 3,
                       'proposed_removed_volume_in3': removed['volume_m3'] / INCH ** 3,
                       'balance_error_in3': error_in3})
    return {'schema_version': 'proposed-step-lap-cavities-2', 'source_model_sha256': proposed_sha,
            'baseline_model_sha256': baseline_sha, 'baseline_cavity_sha256': baseline_cavity_sha,
            'proposal_sha256': proposal_sha, 'available': True, 'parts': output_parts,
            # TIMESTAMP START 2026-11-02T15:15:55-05:00 | REVISION R004802
            'summary': {'complete': True, 'part_count': 112, 'changed_cavity_count': 40, 'transfer_count': 24},
            # TIMESTAMP END 2026-11-02T15:15:55-05:00 | REVISION R004802
            'status': 'Actual proposed recesses derived from corrected baseline cavities and identical retained-tongue/receiver-pocket transfer solids. Verify with the separately hash-bound proposed cavity-fit audit.',
            # TIMESTAMP START 2026-11-02T10:50:48-05:00 | REVISION R004767
            'method': 'Baseline removed stock plus receiver transfers minus stock retained by rafters; opposed coplanar folds cancelled on canonical boundary planes before completed bay-zero cavities are rotated to each bay. Raw surfaces and material-transfer volumes must pass independently. No inherited unfilled Boolean residuals and no timber edits.',
            # TIMESTAMP END 2026-11-02T10:50:48-05:00 | REVISION R004767
            'transfer_count': 24, 'transfers': transfers, 'member_volume_balances': deltas,
            'limitations': 'Nominal geometry only. Structural capacity, fabrication tolerances and full assembly sequence remain unresolved.'}


def generate():
    baseline, baseline_sha = read_json(ROOT / 'src/model-data.json')
    base_cavities, cavity_sha = read_json(ROOT / 'src/cavity-data.json')
    proposed, proposed_sha = read_json(ROOT / 'src/step-lap-proposed-model.json')
    proposal, proposal_sha = read_json(ROOT / 'src/step-lap-proposal.json')
    baseline_audit = json.loads((ROOT / 'docs/cavity-fit-audit.json').read_text())
    assert baseline_audit['status'] == 'PASS'
    assert (baseline_audit['model_sha256'], baseline_audit['cavity_sha256']) == (baseline_sha, cavity_sha)
    result = build_cavities(baseline, base_cavities, proposed, proposal,
                            (baseline_sha, cavity_sha, proposed_sha, proposal_sha))
    (ROOT / 'src/step-lap-proposed-cavities.json').write_text(json.dumps(result, separators=(',', ':')) + '\n')
    # TIMESTAMP START 2026-11-02T15:15:55-05:00 | REVISION R004802
    print('Exported 112 proposed cavity records from 24 exact material transfers; proposed model', proposed_sha)
    # TIMESTAMP END 2026-11-02T15:15:55-05:00 | REVISION R004802
    return result


if __name__ == '__main__':
    generate()
# TIMESTAMP END 2026-11-02T10:08:45-05:00 | REVISION R004761
