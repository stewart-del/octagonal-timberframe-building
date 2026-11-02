#!/usr/bin/env python3
"""Export current component triangles to GLB, preserving IDs."""
from pathlib import Path
import json, struct
ROOT = Path(__file__).resolve().parents[1]

def export(model, exploded=False):
    binary = bytearray()
    views, accessors, meshes, nodes, materials = [], [], [], [], []
    def buffer(values, code, kind, count, low=None, high=None):
        while len(binary) % 4: binary.append(0)
        offset = len(binary)
        binary.extend(struct.pack('<' + code*len(values), *values))
        views.append({'buffer':0, 'byteOffset':offset, 'byteLength':len(binary)-offset})
        accessor = {'bufferView':len(views)-1, 'componentType':5126 if code=='f' else 5125,
                    'count':count, 'type':kind}
        if low is not None: accessor.update(min=low, max=high)
        accessors.append(accessor)
        return len(accessors)-1
    for part in model['parts']:
        if part.get('temporary') or part.get('group') == 'roof_envelope': continue
        vertices = part['vertices']
        pos = buffer([x for v in vertices for x in v], 'f', 'VEC3', len(vertices),
                     [min(v[i] for v in vertices) for i in range(3)],
                     [max(v[i] for v in vertices) for i in range(3)])
        indices = [i for tri in part['triangles'] for i in tri]
        idx = buffer(indices, 'I', 'SCALAR', len(indices))
        color = part.get('color', [.55,.37,.2,1])
        if isinstance(color, str): color=[.55,.37,.2,1]
        materials.append({'name':part['id'], 'doubleSided':True,
                          'pbrMetallicRoughness':{'baseColorFactor':color,
                          'metallicFactor':0,'roughnessFactor':.8}})
        meshes.append({'name':part['id'], 'primitives':[{'attributes':{'POSITION':pos},
                       'indices':idx, 'material':len(materials)-1}]})
        nodes.append({'name':part['id'], 'mesh':len(meshes)-1,
                      'translation':part.get('exploded_offset',[0,0,0]) if exploded else [0,0,0],
                      'extras':{'component_id':part['id'], 'group':part['group'],
                                'joint_status':part.get('cut_status'),
                                'axis_start':part.get('axis_start'), 'axis_end':part.get('axis_end')}})
    doc={'asset':{'version':'2.0','generator':'Octagon R01 geometry export'},
         'scene':0,'scenes':[{'nodes':list(range(len(nodes)))}], 'nodes':nodes,'meshes':meshes,
         'materials':materials,'buffers':[{'byteLength':len(binary)}],
         'bufferViews':views,'accessors':accessors,
         'extras':{'revision':'R01','status':'Geometry study; physical joint sizing unresolved',
                   'coordinate_system':'meters, Y up', 'display_tie_height_in':90}}
    encoded=json.dumps(doc,separators=(',',':')).encode()
    encoded += b' '*((-len(encoded))%4)
    binary += b'\0'*((-len(binary))%4)
    length=12+8+len(encoded)+8+len(binary)
    return struct.pack('<III',0x46546c67,2,length)+struct.pack('<I4s',len(encoded),b'JSON')+encoded+struct.pack('<I4s',len(binary),b'BIN\0')+binary

if __name__=='__main__':
    model=json.loads((ROOT/'src/model-data.json').read_text())
    target=ROOT/'dist/downloads'
    target.mkdir(parents=True,exist_ok=True)
    for exploded in [False, True]:
        (target/('Octagon-R01-'+('exploded' if exploded else 'assembled')+'.glb')).write_bytes(export(model,exploded))
