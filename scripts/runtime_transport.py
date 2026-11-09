# TIMESTAMP START 2026-11-08T21:52:44-05:00 | REVISION R000001
"""Lossless little-endian mesh transport; canonical JSON sources stay unchanged.

The first uint32 stores the padded UTF-8 header length. The binary body starts
on an eight-byte boundary. Vertex coordinates retain all IEEE-754 Float64 bits;
triangle indices use Uint32 only when every source index is representable.
Identical numeric arrays share transport bytes. The browser reconstructs a fresh
array for each reference, so independently mutable parts never become aliases.
"""
from array import array
import json
import math
import struct
import sys

SCHEMA = 'octagon-mesh-transport-1'
REFERENCE = '$octagonMesh'
MAX_SAFE_INTEGER = (1 << 53) - 1


def encode_transport(value):
    """Return a binary envelope whose decoded value equals JSON.parse(source)."""
    binary = bytearray()
    ranges = {}

    def matrix_kind(node, key):
        if key not in ('vertices', 'triangles', 'faces') or not isinstance(node, list) or not node:
            return None
        if not all(isinstance(row, list) and len(row) == 3 for row in node):
            return None
        if key == 'vertices':
            for row in node:
                for number in row:
                    if type(number) not in (int, float) or not math.isfinite(number):
                        return None
                    if type(number) is int and abs(number) > MAX_SAFE_INTEGER:
                        return None
            return 'f64'
        if all(type(number) is int and 0 <= number <= 0xffffffff for row in node for number in row):
            return 'u32'
        return None

    def encode(node, key=None):
        kind = matrix_kind(node, key)
        if kind:
            width, code = (8, 'd') if kind == 'f64' else (4, 'I')
            numbers = array(code, (number for row in node for number in row))
            if numbers.itemsize != width:
                raise ValueError('Unsupported native numeric array width')
            if sys.byteorder != 'little':
                numbers.byteswap()
            raw = numbers.tobytes()
            # The actual bytes participate in equality; no digest collision can
            # make two different meshes share a transport range.
            identity = (kind, raw)
            if identity not in ranges:
                binary.extend(b'\0' * (-len(binary) % width))
                ranges[identity] = len(binary)
                binary.extend(raw)
            return {REFERENCE: [kind, ranges[identity], len(node), 3]}
        if isinstance(node, dict):
            if REFERENCE in node:
                raise ValueError('Reserved mesh transport marker occurs in source')
            if not all(isinstance(name, str) for name in node):
                raise ValueError('Mesh transport requires JSON object string keys')
            return {name: encode(child, name) for name, child in node.items()}
        if isinstance(node, list):
            return [encode(child) if isinstance(child, (dict, list)) else child for child in node]
        return node

    encoded = encode(value)
    header = json.dumps({'schema': SCHEMA, 'byteLength': len(binary), 'value': encoded},
                        separators=(',', ':'), ensure_ascii=True, allow_nan=False).encode('utf-8')
    header += b' ' * (-(4 + len(header)) % 8)
    if len(header) > 0xffffffff:
        raise ValueError('Mesh transport header exceeds its uint32 length')
    return struct.pack('<I', len(header)) + header + binary
# TIMESTAMP END 2026-11-08T21:52:44-05:00 | REVISION R000001
