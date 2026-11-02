"""Verify both downloadable GLBs contain the revised model's actual geometry."""
from pathlib import Path
import json
import math
import struct

ROOT = Path(__file__).resolve().parents[1]
model = json.loads((ROOT / 'src/model-data.json').read_text())
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
        assert node['translation'] == (part.get('exploded_offset', [0, 0, 0]) if mode == 'exploded' else [0, 0, 0])
        primitive = doc['meshes'][node['mesh']]['primitives'][0]
        actual = unpack_accessor(primitive['attributes']['POSITION'], 'f', 3)
        reference = [v for point in part['vertices'] for v in point]
        assert len(actual) == len(reference)
        assert all(math.isclose(a, b, rel_tol=1e-6, abs_tol=1e-6) for a, b in zip(actual, reference))
        assert unpack_accessor(primitive['indices'], 'I', 1) == tuple(i for face in part['triangles'] for i in face)
    print(f'{mode}: {len(expected)} component IDs, positions, triangles and translations match current R01 source')
