"""Verify both downloadable GLBs contain the revised model's actual geometry."""
from pathlib import Path
import json
import math
import struct

ROOT = Path(__file__).resolve().parents[1]
model = json.loads((ROOT / 'src/model-data.json').read_text())
# TIMESTAMP START 2026-11-02T18:14:42-05:00 | REVISION R004830
import hashlib
plan_bytes=(ROOT/'src/disassembly-plan.json').read_bytes()
plan=json.loads(plan_bytes)['variants']['baseline']
offsets={p['id']:[0.,0.,0.] for p in model['parts']}
for stage in plan['stages']:
    for motion in stage.get('motions',[stage]):
        for member_id in motion['member_ids']:
            if member_id in offsets:
                offsets[member_id]=[a+b for a,b in zip(offsets[member_id],motion['delta_m'])]
# TIMESTAMP END 2026-11-02T18:14:42-05:00 | REVISION R004830
expected = [p for p in model['parts'] if not p.get('temporary') and p['group'] != 'roof_envelope']
for mode in ['assembled', 'exploded']:
    data = (ROOT / 'dist/downloads' / f'Octagon-R01-{mode}.glb').read_bytes()
    magic, version, total = struct.unpack_from('<III', data)
    assert magic == 0x46546C67 and version == 2 and total == len(data)
    json_size, json_type = struct.unpack_from('<I4s', data, 12)
    assert json_type == b'JSON'
    doc = json.loads(data[20:20 + json_size])
    binary_offset = 20 + json_size
    binary_size, binary_type = struct.unpack_from('<I4s', data, binary_offset)
    assert binary_type == b'BIN\0' and binary_offset + 8 + binary_size == len(data)
    binary = data[binary_offset + 8:]
    assert doc['asset']['version'] == '2.0'
    assert doc['extras']['revision'] == 'R01'
    # TIMESTAMP START 2026-11-02T18:14:42-05:00 | REVISION R004830
    assert doc['extras']['source_model_sha256']==hashlib.sha256((ROOT/'src/model-data.json').read_bytes()).hexdigest()
    assert doc['extras']['disassembly_pose']==('checked-endpoint' if mode=='exploded' else 'assembled-start')
    assert doc['extras']['disassembly_plan_sha256']==hashlib.sha256(plan_bytes).hexdigest()
    assert doc['extras']['disassembly_variant']=='baseline'
    assert doc['extras']['disassembly_status']==plan['status']
    assert doc['extras']['disassembly_stage_count']==len(plan['stages'])
    assert doc['extras']['disassembly_held_ids']==sorted(set(plan['unmoved_ids']).intersection(p['id'] for p in expected))
    # TIMESTAMP END 2026-11-02T18:14:42-05:00 | REVISION R004830
    assert [n['name'] for n in doc['nodes']] == [p['id'] for p in expected]
    assert doc['scenes'][doc['scene']]['nodes'] == list(range(len(expected)))
    def unpack_accessor(index, code, stride):
        accessor = doc['accessors'][index]
        view = doc['bufferViews'][accessor['bufferView']]
        offset = view.get('byteOffset', 0) + accessor.get('byteOffset', 0)
        count = accessor['count'] * stride
        assert offset + count * 4 <= len(binary)
        return struct.unpack_from('<' + code * count, binary, offset)
    for node, part in zip(doc['nodes'], expected):
        assert node['extras']['component_id'] == part['id']
        # TIMESTAMP START 2026-11-02T18:14:42-05:00 | REVISION R004830
        assert node['translation'] == (offsets[part['id']] if mode == 'exploded' else [0, 0, 0])
        # TIMESTAMP END 2026-11-02T18:14:42-05:00 | REVISION R004830
        primitive = doc['meshes'][node['mesh']]['primitives'][0]
        actual = unpack_accessor(primitive['attributes']['POSITION'], 'f', 3)
        reference = [v for point in part['vertices'] for v in point]
        assert len(actual) == len(reference)
        assert all(math.isclose(a, b, rel_tol=1e-6, abs_tol=1e-6) for a, b in zip(actual, reference))
        assert unpack_accessor(primitive['indices'], 'I', 1) == tuple(i for face in part['triangles'] for i in face)
    print(f'{mode}: {len(expected)} component IDs, positions, triangles and translations match current R01 source')
