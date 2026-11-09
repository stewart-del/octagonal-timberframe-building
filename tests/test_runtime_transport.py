# TIMESTAMP START 2026-11-08T21:52:44-05:00 | REVISION R000001
"""Cross-language exactness and transport invariants, independent of the build."""
from pathlib import Path
import json
import math
import struct
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from runtime_transport import encode_transport, SCHEMA, REFERENCE


def unpack_header(payload):
    length = struct.unpack_from('<I', payload)[0]
    return json.loads(payload[4:4 + length]), 4 + length


class RuntimeTransportTests(unittest.TestCase):
    def roundtrip(self, value):
        payload = encode_transport(value)
        with tempfile.TemporaryDirectory(prefix='octagon-transport-test-') as directory:
            original = Path(directory) / 'original.json'
            original.write_text(json.dumps(value, separators=(',', ':'), allow_nan=False))
            process = subprocess.run(['node', str(ROOT / 'tests/runtime-transport.cjs'), '--check', str(original)],
                                     input=payload, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        self.assertEqual(process.returncode, 0, process.stderr.decode())
        self.assertTrue(json.loads(process.stdout)['pass'])
        return payload

    def test_preserves_float64_signed_zero_and_uint32_extremes(self):
        self.roundtrip({'vertices': [[-0.0, math.nextafter(1.0, 2.0), sys.float_info.min],
                                    [sys.float_info.max, 5e-324, -1.2345678901234567]],
                        'triangles': [[0, 2147483648, 4294967295]],
                        'note': 'Exact Unicode: octagon — π; </script>'})

    def test_identical_numeric_arrays_share_only_the_transport_range(self):
        vertices = [[0.0, 1.1, -0.0], [2.3, 4.5, 6.7]]
        triangles = [[0, 1, 0]]
        payload = self.roundtrip({'one': {'vertices': vertices, 'triangles': triangles, 'faces': triangles},
                                 'two': {'vertices': vertices, 'triangles': triangles}})
        header, start = unpack_header(payload)
        first, second = header['value']['one'], header['value']['two']
        self.assertEqual(first['vertices'], second['vertices'])
        self.assertEqual(first['faces'], first['triangles'])
        self.assertEqual(header['byteLength'], 60)
        self.assertEqual(start % 8, 0)
        self.assertEqual(len(payload), start + 60)

    def test_unsupported_and_ragged_arrays_remain_json(self):
        value = {'vertices': [[1, 2], [3, 4, 5]], 'triangles': [[0, 1.5, 2]],
                 'faces': [[-1, 2, 3]], 'nested': [{'vertices': []}, {'vertices': [[True, 1, 2]]}],
                 'ordinary': {'__proto__': {'keep': True}, 'constructor': 'plain metadata'}}
        payload = self.roundtrip(value)
        header, _ = unpack_header(payload)
        self.assertEqual(header['value'], value)
        self.assertEqual(header['byteLength'], 0)

    def test_roundtrip_scalar_roots_and_mixed_nested_containers(self):
        for value in [None, False, 17, 'mesh', [None, {'vertices': [[1, 2, 3]]}, [1, 2, 3]]]:
            self.roundtrip(value)

    def test_input_is_unchanged_and_encoding_is_deterministic(self):
        value = {'vertices': [[1.25, 2.5, 3.75]], 'triangles': [[0, 0, 0]], 'metadata': {'b': 1, 'a': 2}}
        before = json.dumps(value)
        first = encode_transport(value)
        self.assertEqual(first, encode_transport(value))
        self.assertEqual(json.dumps(value), before)
        header, _ = unpack_header(first)
        self.assertEqual(header['schema'], SCHEMA)
        self.assertEqual(list(header['value']['metadata']), ['b', 'a'])

    def test_reserved_markers_and_non_json_numbers_are_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Reserved'):
            encode_transport({'nested': [{REFERENCE: ['forged']}]})
        with self.assertRaises(ValueError):
            encode_transport({'vertices': [[0, float('nan'), 0]]})
        with self.assertRaisesRegex(ValueError, 'string keys'):
            encode_transport({1: 'not a JSON object key'})


if __name__ == '__main__':
    unittest.main()
# TIMESTAMP END 2026-11-08T21:52:44-05:00 | REVISION R000001
