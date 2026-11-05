# TIMESTAMP START 2026-11-05T23:39:11+00:00 | REVISION R000073
"""Waste-only construction candidates; every current stock row needs readback."""
from pathlib import Path,PurePosixPath
from functools import lru_cache
import copy,gzip,hashlib,io,json,tarfile
ROOT=Path(__file__).resolve().parents[1];FIXTURE=ROOT/'scripts/fixtures/stock-waste-inputs.json'
ARCHIVE_SHA='826c556492b308eb55c3eeec299d4e5d5bf4911db78c2d7717bcac38e8183d8c'
MANIFEST_SHA='718ccd89a0cd7c29e8d7057cc91a7bf4493704edb40d14c9825a48b30779577f'
ALLOWED={'declared_exterior_offcut','declared_exterior_offcut_pieces','wasteRepresentation','serializedWasteReadbackRepair','outside_in3','reconstruction_in3'}
def sha(raw):return hashlib.sha256(raw).hexdigest()
def fingerprint(record):return sha(json.dumps({key:record[key] for key in ['vertices','triangles']},sort_keys=True,separators=(',',':')).encode())
@lru_cache(maxsize=1)
def inputs():
 descriptor=json.loads(FIXTURE.read_text());assert descriptor['schema']=='octagon-frozen-stock-waste-1';name=PurePosixPath(descriptor['archive']);assert len(name.parts)==1 and not name.is_absolute();raw=(FIXTURE.parent/str(name)).read_bytes();assert len(raw)==descriptor['archiveBytes'] and sha(raw)==descriptor['archiveSha256']==ARCHIVE_SHA;files={}
 with tarfile.open(fileobj=io.BytesIO(raw),mode='r|gz') as archive:
  for member in archive:
   path=PurePosixPath(member.name);assert not path.is_absolute() and '..' not in path.parts and path.parts[0]=='stock-waste-readback-terminal-v1'
   if member.isdir():continue
   assert member.isfile(),'No waste source links or special entries';name=str(PurePosixPath(*path.parts[1:]));assert name not in files;files[name]=archive.extractfile(member).read()
 assert sha(files['manifest.json'])==descriptor['manifestSha256']==MANIFEST_SHA;manifest=json.loads(files['manifest.json'])
 for name,row in manifest['files'].items():assert len(files[name])==row['bytes'] and sha(files[name])==row['sha256'],('Frozen waste source changed',name)
 from closure_core_parts import inputs as core_inputs,MANIFEST_SHA as CORE_SHA
 core_inputs();assert manifest['requiredCoreManifestSHA256']==CORE_SHA and manifest['originalToleranceIn3']==1e-6 and not any(manifest[key] for key in ['installedGeometryChanged','blankGeometryChanged','stockDimensionsChanged','originalV1Mutated'])
 asset=json.loads(gzip.decompress(files[manifest['assets']['core']]));assert len(asset['corrections'])==188 and len(asset['checkedUnchangedRows'])==102 and asset['unchangedToleranceIn3']==1e-6
 return {'manifest':manifest,'asset':asset}
def candidate(stock_id,record,current_parts,*,require_exact=True):
 """A nonmatching candidate carries no inherited proof or override authority.

 The caller may only use that geometry after a new independent proof against
 its actual current blank and installed children. No part is modified here.
 """
 patch=inputs()['asset']['corrections'].get(stock_id)
 if patch is None:return None
 matched=fingerprint(record['blank'])==patch['sourceBlankGeometrySHA256'] and set(record['children'])==set(patch['sourceInstalledChildGeometrySHA256'])
 matched=matched and all(pid in current_parts and fingerprint(current_parts[pid])==expected for pid,expected in patch['sourceInstalledChildGeometrySHA256'].items())
 if require_exact:assert matched,('Current blank or child differs; original waste proof does not apply',stock_id)
 assert set(patch['setWasteFields'])<=ALLOWED and set(patch['removeWasteFields'])<=ALLOWED,'Forbidden nonwaste correction'
 fields=copy.deepcopy(patch['setWasteFields']);assert ('declared_exterior_offcut' in fields)^('declared_exterior_offcut_pieces' in fields),'Ambiguous waste representation'
 return {'fields':fields,'originalGeometryBindingsMatched':bool(matched),'originalProofInherited':False,'requiresFreshCurrentStockReadback':True,'manifestSha256':MANIFEST_SHA}
# TIMESTAMP END 2026-11-05T23:39:11+00:00 | REVISION R000073
