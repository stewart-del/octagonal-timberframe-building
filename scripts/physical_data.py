# TIMESTAMP START 2026-11-05T05:14:11+00:00 | REVISION R000024
"""Lossless source mesh storage; no coordinates or physical tolerances change."""
from pathlib import Path
import gzip,hashlib,json
# TIMESTAMP START 2026-11-05T06:36:54+00:00 | REVISION R000029
def occupied_part(part,prototypes):
    """Expand an instance only for an auditor that needs its world triangles."""
    if not part.get('mesh_instance'):return part
    import numpy as np
    instance=part['mesh_instance'];prototype=prototypes[instance['prototype']]
    matrix=np.asarray(instance['transform'],float);vertices=np.asarray(prototype['vertices'],float)
    assert matrix.shape==(3,4) and np.isfinite(matrix).all()
    # TIMESTAMP START 2026-11-05T09:01:08+00:00 | REVISION R000039
    return {**({'fastener_spec':prototype['fastener_spec']} if prototype.get('fastener_spec') and not part.get('fastener_spec') else {}),**part,'vertices':(vertices@matrix[:,:3].T+matrix[:,3]).tolist(),'triangles':prototype['triangles']}
# TIMESTAMP END 2026-11-05T09:01:08+00:00 | REVISION R000039
# TIMESTAMP END 2026-11-05T06:36:54+00:00 | REVISION R000029

def readable(value,level=0):
    pad='  '*level;child='  '*(level+1)
    if isinstance(value,dict):return '{\n'+',\n'.join(child+json.dumps(k)+': '+readable(v,level+1) for k,v in value.items())+'\n'+pad+'}' if value else '{}'
    if isinstance(value,list):
        if not value or all(not isinstance(v,(dict,list)) for v in value):return json.dumps(value,separators=(',',':'))
        return '[\n'+',\n'.join(child+readable(v,level+1) for v in value)+'\n'+pad+']'
    return json.dumps(value)

# TIMESTAMP START 2026-11-05T09:01:08+00:00 | REVISION R000039
def _archives(data):
    if data.get('geometryArchives'):
        assert not data.get('geometryArchive'),'Ambiguous physical archive declaration'
        return data['geometryArchives']
    return [{'path':data['geometryArchive'],'sha256':data['geometryArchiveSha256']}] if data.get('geometryArchive') else []

# TIMESTAMP START 2026-11-05T14:38:03+00:00 | REVISION R000047
def read_physical_json(path):
    path=Path(path);data=json.loads(path.read_text());archives=_archives(data);part_archives=data.get('partArchives',[])
    if not archives and not part_archives:return data
    parts=data.get('parts',[])
    if part_archives:
        assert 'parts' not in data,'Ambiguous inline and archived part records'
        parts=[];ids=set()
        for archive in part_archives:
            raw=(path.parent/archive['path']).read_bytes();assert hashlib.sha256(raw).hexdigest()==archive['sha256'],'Physical part archive changed'
            decoded=json.loads(gzip.decompress(raw));assert decoded['schema']=='octagon-physical-part-records-1' and len(decoded['parts'])==archive['count'],'Invalid physical part archive'
            for part in decoded['parts']:
                assert part['id'] not in ids,'Repeated physical part across archives'
                ids.add(part['id']);parts.append(part)
    geometry={}
    for archive in archives:
        raw=(path.parent/archive['path']).read_bytes()
        assert hashlib.sha256(raw).hexdigest()==archive['sha256'],'Physical mesh archive changed'
        decoded=json.loads(gzip.decompress(raw))['parts']
        assert not set(decoded)&set(geometry),'Repeated physical geometry across archives'
        geometry.update(decoded)
    restored=[]
    for part in parts:
        if part.get('geometry_ref'):
            assert part['geometry_ref']==part['id'] and part['id'] in geometry
            part={**part,**geometry[part['id']]};part.pop('geometry_ref')
        restored.append(part)
    return {**data,'parts':restored,'geometryResolved':True,**({'partsResolved':True} if part_archives else {})}
# TIMESTAMP END 2026-11-05T14:38:03+00:00 | REVISION R000047

# TIMESTAMP START 2026-11-05T14:38:03+00:00 | REVISION R000047
def write_physical_json(path,data,*,geometry_archive_max_bytes=16*1024*1024,inline_vertex_limit=100,part_archive_limit=None,part_archive_max_bytes=16*1024*1024):
# TIMESTAMP END 2026-11-05T14:38:03+00:00 | REVISION R000047
    path=Path(path);geometry={};parts=[]
    for part in data['parts']:
        part=dict(part)
        if part.get('vertices') and len(part['vertices'])>inline_vertex_limit:
            geometry[part['id']]={key:part.pop(key) for key in ['vertices','triangles']}
            part['geometry_ref']=part['id']
        parts.append(part)
    assert geometry_archive_max_bytes>0
    def chunks(items):
        raw=json.dumps({'parts':dict(items)},separators=(',',':')).encode();compressed=gzip.compress(raw,mtime=0)
        assert gzip.decompress(compressed)==raw,'Mesh compression must be lossless'
        if len(compressed)>geometry_archive_max_bytes:
            assert len(items)>1,'One physical mesh exceeds the archive object limit'
            middle=len(items)//2
            return chunks(items[:middle])+chunks(items[middle:])
        return [compressed]
    payloads=chunks(list(geometry.items()));base=path.stem.replace('-solids','');archives=[]
    for index,compressed in enumerate(payloads):
        name=base+'-geometries'+('' if len(payloads)==1 else '-'+str(index+1).zfill(3))+'.json.gz'
        archive=path.with_name(name);archive.write_bytes(compressed)
        archives.append({'path':archive.name,'sha256':hashlib.sha256(compressed).hexdigest()})
    # TIMESTAMP START 2026-11-05T14:38:03+00:00 | REVISION R000047
    ignored=['geometryArchive','geometryArchiveSha256','geometryArchives','geometryResolved','partArchives','partsResolved']
    # TIMESTAMP END 2026-11-05T14:38:03+00:00 | REVISION R000047
    metadata={**{k:v for k,v in data.items() if k not in ignored},'parts':parts}
    if len(archives)==1:metadata.update(geometryArchive=archives[0]['path'],geometryArchiveSha256=archives[0]['sha256'])
    else:metadata['geometryArchives']=archives
    # TIMESTAMP START 2026-11-05T14:38:03+00:00 | REVISION R000047
    assert len({p['id'] for p in parts})==len(parts),'Repeated physical part identity'
    if part_archive_limit is not None:
        assert part_archive_limit>0 and part_archive_max_bytes>0
        encoded=json.dumps(parts,separators=(',',':')).encode()
        if len(encoded)>part_archive_limit:
            def part_chunks(records):
                payload=gzip.compress(json.dumps({'schema':'octagon-physical-part-records-1','parts':records},separators=(',',':')).encode(),mtime=0)
                if len(payload)>part_archive_max_bytes:
                    assert len(records)>1,'One physical part record exceeds the archive object limit'
                    middle=len(records)//2;return part_chunks(records[:middle])+part_chunks(records[middle:])
                return [(payload,len(records))]
            packed=part_chunks(parts);metadata.pop('parts');metadata['partArchives']=[]
            for index,(payload,count) in enumerate(packed):
                name=base+'-parts'+('' if len(packed)==1 else '-'+str(index+1).zfill(3))+'.json.gz'
                path.with_name(name).write_bytes(payload);metadata['partArchives'].append({'path':name,'sha256':hashlib.sha256(payload).hexdigest(),'count':count})
    # TIMESTAMP END 2026-11-05T14:38:03+00:00 | REVISION R000047
    path.write_text(readable(metadata)+'\n')
    restored=read_physical_json(path)
    assert all(restored[key]==value for key,value in data.items() if key not in ignored)
    return metadata
# TIMESTAMP END 2026-11-05T09:01:08+00:00 | REVISION R000039

# TIMESTAMP END 2026-11-05T05:14:11+00:00 | REVISION R000024
