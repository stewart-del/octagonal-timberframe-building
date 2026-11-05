# TIMESTAMP START 2026-11-05T23:26:47+00:00 | REVISION R000072
"""Fixed-stock floor closure: compose actual tools, never substitute old hosts."""
from pathlib import Path,PurePosixPath
from functools import lru_cache
import copy,gzip,hashlib,io,json,tarfile
import numpy as np
from audit_revised_joinery import native_solid
from audit_cavity_fit import inspect_mesh
from cupola_joinery_recipe import I,TOL,amount,diff
from floor_surface_normalization import collapse_short_edges,regular_local
ROOT=Path(__file__).resolve().parents[1];FIXTURE=ROOT/'scripts/fixtures/floor-closure-inputs.json'
ARCHIVE_SHA='7e65f8f7a5eb3b11a041899d78b0e9e10eb1e656a5171a4ebbf57f916fa49bcb'
MANIFEST_SHA='3b25e360c7f87528e52c4ec9547fd8a8e62b6ef9ff7de453cb9a0e5607aaff7c'
def sha(raw):return hashlib.sha256(raw).hexdigest()
@lru_cache(maxsize=1)
def inputs():
 descriptor=json.loads(FIXTURE.read_text());assert descriptor['schema']=='octagon-frozen-floor-closure-1';path=PurePosixPath(descriptor['archive']);assert len(path.parts)==1 and not path.is_absolute();raw=(FIXTURE.parent/str(path)).read_bytes();assert len(raw)==descriptor['archiveBytes'] and sha(raw)==descriptor['archiveSha256']==ARCHIVE_SHA;files={}
 with tarfile.open(fileobj=io.BytesIO(raw),mode='r|gz') as archive:
  for member in archive:
   path=PurePosixPath(member.name);assert not path.is_absolute() and '..' not in path.parts and path.parts[0]=='closure-floor-terminal-v1'
   if member.isdir():continue
   assert member.isfile(),'No floor source links or special entries';name=str(PurePosixPath(*path.parts[1:]));assert name not in files;files[name]=archive.extractfile(member).read()
 assert sha(files['manifest.json'])==descriptor['manifestSha256']==MANIFEST_SHA;manifest=json.loads(files['manifest.json'])
 for name,row in manifest['files'].items():assert len(files[name])==row['bytes'] and sha(files[name])==row['sha256'],('Floor closure source changed',name)
 from closure_core_parts import inputs as core_inputs,MANIFEST_SHA as CORE_SHA
 core=core_inputs();assert manifest['requiredCoreManifestSHA256']==descriptor['requiredCoreManifestSha256']==CORE_SHA and not manifest['readyForCompleteImport'],'Frozen partial source must retain its actual status'
 for name,expected in [('src/floor-foundation-solids.json',manifest['canonicalFloorSHA256']),('src/floor-foundation-geometries.json.gz',manifest['canonicalFloorArchiveSHA256'])]:assert sha((ROOT/name).read_bytes())==expected,('Canonical floor source changed',name)
 def decode(name):return json.loads(gzip.decompress(files[name]) if name.endswith('.gz') else files[name])
 values={name:decode(path) for name,path in manifest['primaryAssets'].items()}
 return {**values,'manifest':manifest,'frames':core['frames'],'sourceFiles':files}
def stock_basis(part):
 frame=part['stock_frame'];basis=np.column_stack([frame[key] for key in ['axis','width','depth']]);assert np.max(abs(basis.T@basis-np.eye(3)))<1e-9,'Non-orthogonal physical stock axes'
 if np.linalg.det(basis)<0:basis[:,-1]*=-1
 return basis,np.asarray(part['vertices']).mean(0)
def cut_current_lower(part,tools):
 """Construct source-minus-tools in stock inches and verify world readback.

 Only endpoints of existing microscopic edges may be contracted. Every
 accepted boundary still obeys the original physical occupied-volume limit.
 """
 basis,origin=stock_basis(part)
 def local(record):return {'vertices':((np.asarray(record['vertices'])-origin)@basis/I).tolist(),'triangles':record['triangles']}
 before=native_solid(part);reference=before;local_reference=native_solid(local(part));active=[]
 for tool in tools:
  cutter=native_solid(tool)
  if amount(before^cutter)<=TOL:continue
  reference=reference-cutter;local_reference=local_reference-native_solid(local(tool));active.append(tool)
 if not active:return part,{'id':part['id'],'status':'UNCHANGED_NO_MATERIAL_CONTACT','removedIn3':0.}
 components=local_reference.decompose();physical=[s for s in components if s.volume()>1e-6];residue=sum(abs(s.volume()) for s in components if s.volume()<=1e-6);assert len(physical)==1 and residue<=1e-6,('Negative seats split a current actor; new physical identities are required',part['id'],len(physical),residue);seed=physical[0];attempts=[]
 def evaluate(candidate,epsilon_m,contraction,method):
  if str(candidate.status())!='Error.NoError':attempts.append({'edgeLimitM':epsilon_m,'method':method,'status':'NATIVE_REJECT'});return None
  mesh=candidate.to_mesh64();record={'vertices':(np.asarray(mesh.vert_properties)[:,:3]@basis.T*I+origin).tolist(),'triangles':np.asarray(mesh.tri_verts).astype(int).tolist()};audit=inspect_mesh(np.asarray(record['vertices']),np.asarray(record['triangles'],np.uint64),True)
  if audit['status']!='PASS':attempts.append({'edgeLimitM':epsilon_m,'method':method,'status':'RAW_REJECT','failures':audit['failures']});return None
  readback=native_solid(record);errors={'worldDifferenceIn3':diff(reference,readback)/I**3,'localDifferenceIn3':diff(local_reference,native_solid(local(record))),'absoluteVolumeDeltaIn3':abs(reference.volume()-readback.volume())/I**3,'addedOutsideOriginalIn3':amount(readback-before)/I**3};status='PASS' if np.isfinite(list(errors.values())).all() and max(errors.values())<=1e-6 else 'OCCUPIED_REJECT';attempts.append({'edgeLimitM':epsilon_m,'method':method,'status':status,**errors,**contraction})
  if status!='PASS':return None
  result={**part,**record,'volumeM3':float(readback.volume()),'floorFilmSeatComposedOnCurrent':True};return result,{'id':part['id'],'status':'PASS','attempts':attempts,'rawAudit':audit,'removedIn3':amount(before-readback)/I**3,'zeroMaterialNativeResidueIn3':residue,'geometryWasDerivedFromCurrentPart':True,'unchangedToleranceIn3':1e-6}
 for epsilon_m in [0,1e-8,2e-8,5e-8,1e-7]:
  candidate,contraction=(seed,{}) if epsilon_m==0 else collapse_short_edges(seed,epsilon_m/I)
  result=evaluate(candidate,epsilon_m,contraction,'conditioned current CSG and existing short-edge contraction')
  if result:return result
  for plane_m in [1e-10,1e-9]:
   try:rebuilt=regular_local(candidate,plane_m/I)
   except (AssertionError,RuntimeError,ValueError) as error:attempts.append({'edgeLimitM':epsilon_m,'planeToleranceM':plane_m,'status':'SIGNED_PLANAR_CONSTRUCTION_REJECT','reason':str(error)[:400]});continue
   result=evaluate(rebuilt,epsilon_m,{**contraction,'planeToleranceM':plane_m},'signed planar reconstruction after conditioned current CSG')
   if result:return result
 raise AssertionError(('No strict current lower-seat serialization passed',part['id'],attempts))
# TIMESTAMP END 2026-11-05T23:26:47+00:00 | REVISION R000072
