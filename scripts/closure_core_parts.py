# TIMESTAMP START 2026-11-05T21:51:55+00:00 | REVISION R000068
"""Compose real closure stock with negative tools against current recipients.

The frozen source supplies stock, physical split identities and product data.
It never substitutes its old primary/floor/rail snapshots for current bodies.
Construction lifetimes, weather films and causal fastener metadata are separate.
"""
from pathlib import Path,PurePosixPath
from functools import lru_cache
from types import SimpleNamespace
import base64,copy,gzip,hashlib,io,json,tarfile
import numpy as np
from cupola_joinery_recipe import native_solid,native_record,amount,diff,union,I,TOL
from audit_cavity_fit import inspect_mesh
from floor_surface_normalization import normalize_one,regular_local
ROOT=Path(__file__).resolve().parents[1];FIXTURE=ROOT/'scripts/fixtures/closure-core-inputs.json'
MANIFEST_SHA='841d073466a0d998f0f54d3998771c54a7889606d385710c8ab5c311096aeded'
ARCHIVE_SHA='1c803ea03f556e1bee08ccebffba231024bc29c555892e88aa00c9bc048cf7ab'
# TIMESTAMP START 2026-11-05T22:31:25+00:00 | REVISION R000069
CAUSAL_FIXTURE=ROOT/'scripts/fixtures/closure-core-causal-inputs.json.gz'
CAUSAL_DELTA_SHA='bfca97e399a7c2bb6fe9d0cb0e5b5b019734a19909f57c1f704a9ebf2dcdea5b'
CAUSAL_CHECK_SHA='a7463dedc874843e30b98fa7c7028c6331cbe95b15e5b7566366460d7d2a6425'
# TIMESTAMP END 2026-11-05T22:31:25+00:00 | REVISION R000069
REQUIRED=['assets/closure-final-raw-wood-patch.json.gz','assets/closure-final-hardware-instances.json.gz','assets/main-wall-hardware-final-receivers.json.gz','assets/construction-local-frames.json','assets/core-supplemental-negative-tools.json.gz','assets/composition-current-receivers.json.gz','assets/core-logical-release-group-inventory.json']
def sha(raw):return hashlib.sha256(raw).hexdigest()
@lru_cache(maxsize=1)
def inputs():
 fixture=json.loads(FIXTURE.read_text());assert fixture['schema']=='octagon-frozen-closure-core-inputs-1';manifest_raw=base64.b64decode(fixture['manifest_base64'],validate=True);assert sha(manifest_raw)==fixture['manifest_sha256']==MANIFEST_SHA;manifest=json.loads(manifest_raw);chunks=[]
 for row in fixture['parts']:
  path=PurePosixPath(row['path']);assert not path.is_absolute() and '..' not in path.parts;raw=(ROOT/str(path)).read_bytes();assert len(raw)==row['bytes'] and sha(raw)==row['sha256'],('Closure source transport chunk changed',str(path));chunks.append(raw)
 archive=b''.join(chunks);assert len(archive)==fixture['archive_bytes'] and sha(archive)==fixture['archive_sha256']==ARCHIVE_SHA
 expected={row['path']:row for row in manifest['completeBundleFiles']};seen=set();files={};verified={}
 with tarfile.open(fileobj=io.BytesIO(archive),mode='r|gz') as stream:
  for member in stream:
   name=PurePosixPath(member.name);assert not name.is_absolute() and '..' not in name.parts and name.parts[0]=='closure-core-terminal-v1','Unsafe closure source entry'
   if member.isdir():continue
   relative=str(PurePosixPath(*name.parts[1:]));assert relative not in seen,('Repeated closure source',relative);seen.add(relative)
   if member.islnk():
    target=PurePosixPath(member.linkname);assert not target.is_absolute() and '..' not in target.parts and target.parts[0]=='closure-core-terminal-v1';target=str(PurePosixPath(*target.parts[1:]));assert target in verified,'Internal source hard link must reference an already verified archive member';assert relative in expected and verified[target]==(expected[relative]['sha256'],expected[relative]['bytes']);verified[relative]=verified[target]
    if relative in REQUIRED:
     assert target in files,'Required hard-link data was not retained';files[relative]=files[target]
    continue
   assert member.isfile(),'Symbolic links and special source entries are not accepted'
   data=stream.extractfile(member).read()
   if relative=='manifest.json':assert sha(data)==MANIFEST_SHA
   else:
    assert relative in expected and len(data)==expected[relative]['bytes'] and sha(data)==expected[relative]['sha256'],('Frozen closure source changed',relative)
   verified[relative]=(sha(data),len(data))
   if relative in REQUIRED:files[relative]=data
 assert set(expected)<=seen and set(REQUIRED)==set(files),'Incomplete closure source bundle'
 def decode(name):
  raw=files['assets/'+name];return json.loads(gzip.decompress(raw) if name.endswith('.gz') else raw)
 return {'manifest':manifest,'wood':decode('closure-final-raw-wood-patch.json.gz'),'hardware':decode('closure-final-hardware-instances.json.gz'),'retained':decode('main-wall-hardware-final-receivers.json.gz'),'frames':decode('construction-local-frames.json'),'supplemental':decode('core-supplemental-negative-tools.json.gz'),'receivers':decode('composition-current-receivers.json.gz'),'groups':decode('core-logical-release-group-inventory.json')}
def verify_default(data=None,*,read_source=None):
 data=data or inputs();read_source=read_source or (lambda name:(ROOT/name).read_bytes())
 for name,expected in data['manifest']['sourceGuards'].items():
  marker='/reference-repository/'
  if marker in name:
   relative=name.split(marker,1)[1];assert sha(read_source(relative))==expected,('Closure default source changed',relative)
 assert data['manifest']['strictOccupiedDifferenceLimitIn3']==1e-6
 return True
def shape(p):
 assert p.get('triangles'),'Current closure recipient must have actual materialized geometry';return native_solid(p)
def mesh(s):
 q=s.to_mesh64();return {'vertices':np.asarray(q.vert_properties)[:,:3].tolist(),'triangles':np.asarray(q.tri_verts).astype(int).tolist(),'volume_m3':float(s.volume())}
def affine(s,matrix):return s.transform(matrix.tolist())
class RawStockBoundary:
 """Keep signed raw contours until their net boundary has been rebuilt."""
 def __init__(self,vertices,triangles):self.vertices=np.asarray(vertices,float);self.triangles=np.asarray(triangles,np.uint64)
 def to_mesh64(self):return SimpleNamespace(vert_properties=self.vertices,tri_verts=self.triangles)
 def volume(self):
  v=self.vertices-self.vertices.mean(0);t=v[self.triangles];return float(np.einsum('ij,ij->i',t[:,0],np.cross(t[:,1],t[:,2])).sum()/6)
def stock_frame(sid,blank,data):
 for face in data['frames']['mainFaces']:
  if '-'+face['face']+'-' in sid:return np.asarray(face['basis'])[:,:3]
 vertices=np.asarray(blank['vertices']);vectors=vertices-vertices[0];axes=[]
 for v in sorted(vectors,key=np.linalg.norm):
  length=np.linalg.norm(v)
  if length<1e-10:continue
  axis=v/length
  if all(abs(float(axis@other))<1e-8 for other in axes):axes.append(axis)
  if len(axes)==3:break
 assert len(axes)==3,('Purchased blank has no orthogonal stock frame',sid)
 matrix=np.column_stack(axes)
 if np.linalg.det(matrix)<0:matrix[:,-1]*=-1
 return matrix
def repaired_stock_waste(raw,sid,blank,data,plane_epsilon_m=1e-10):
 basis=stock_frame(sid,blank,data);origin=np.asarray(blank['vertices']).mean(0);local=(np.asarray(raw['vertices'])-origin)@basis/I;boundary=RawStockBoundary(local,raw['triangles']);regular=regular_local(boundary,plane_epsilon_m/I);world=affine(regular,np.column_stack([basis*I,origin]));return mesh(world)
def signed_stock_difference(blank,children):
 # An owned blank with disjoint contained children has this exact signed
 # boundary: outward blank faces and reversed installed-piece faces. Net
 # coplanar contours are reconstructed before any native waste import.
 vertices=[];triangles=[]
 for record,sign in [(blank,1),*[(child,-1) for child in children]]:
  offset=len(vertices);vertices.extend(record['vertices'])
  for face in record['triangles']:
   values=[index+offset for index in face];triangles.append(values if sign>0 else values[::-1])
 return {'vertices':vertices,'triangles':triangles}
def compose_wood(current,data=None):
 data=data or inputs();verify_default(data);source=dict(current);parts=source['parts'];aslist=isinstance(parts,list);P={p['id']:p for p in parts} if aslist else dict(parts);core=data['wood'];templates={**core['replace_new_envelope_parts'],**core['add_parts']};receipts=[]
 for pid,tool in core['requiredAdditionalNewEnvelopeCutTools'].items():
  assert pid.startswith(('ENV-','LAP-')),('Protected primary recipient',pid);assert pid in P,('Missing current closure recipient',pid)
  refs=core['splitConstructionGroups'][pid];face=pid.split('-')[1];frame=np.asarray(next(f['basis'] for f in data['frames']['mainFaces'] if f['face']==face));toLocal=np.column_stack([frame[:,:3].T/I,-frame[:,:3].T@frame[:,3]/I]);toWorld=np.column_stack([frame[:,:3]*I,frame[:,3]])
  currentSolids=[shape(P[r]) for r in refs if r in P];before=currentSolids[0] if len(currentSolids)==1 else union(currentSolids);beforeLocal=affine(before,toLocal);cut=shape(tool);supplement=data['supplemental']['requiredAdditionalNegativeTools'].get(pid);active=[q for q in [cut]+([shape(supplement)] if supplement else []) if amount(before^q)>TOL]
  if not active and set(refs)<=set(P) and all(len(shape(P[r]).decompose())==1 for r in refs):
   for rid in refs:assert amount(shape(P[rid])-shape(templates[rid]))<=TOL,('Current recipient outside audited reference',rid)
   receipts.append({'receiverId':pid,'removedIn3':0.,'secondApplicationChangeIn3':0.,'survivingPhysicalIds':refs,'skippedBecauseNoPositiveVolumeToolContact':True});continue
  afterLocal=beforeLocal
  for q in active:afterLocal=afterLocal-affine(q,toLocal)
  after=affine(afterLocal,toWorld);expected=union([shape(templates[r]) for r in refs]);outside=amount(after-expected);assert outside<=TOL,('Changed default stock requires regeneration',pid,outside/I**3)
  components=after.decompose();physical=[c for c in components if c.volume()>TOL];residue=sum(abs(c.volume()) for c in components if c.volume()<=TOL);assert residue<=TOL,('Native decomposition residue exceeds unchanged tolerance',pid)
  matched={}
  for component in physical:
   assert component.volume()>=.01*I**3,('Unclassified current wood component',pid,component.volume()/I**3)
   scores=sorted([(amount(component^shape(templates[r])),r) for r in refs],reverse=True);value,rid=scores[0];assert value>0 and rid not in matched,('Ambiguous physical closure split',pid,rid);matched[rid]=component
  assert set(matched)==set(refs) and len(matched)==len(physical),('Later current void deleted or split a component; never restore reference wood',pid,sorted(matched),refs)
  for rid,s in matched.items():
   q=mesh(s);audit=inspect_mesh(np.asarray(q['vertices']),np.asarray(q['triangles'],np.uint64))
   if audit['status']!='PASS':q,_=normalize_one({'id':rid,'stock_frame':{'axis':frame[:,0].tolist(),'width':frame[:,1].tolist(),'depth':frame[:,2].tolist()},**q},audit['failures'])
   assert amount(native_solid(q)-shape(templates[rid]))<=TOL,('Serialized current component exceeds audited stock',rid)
   metadata=copy.deepcopy(P[pid]);metadata.update({k:copy.deepcopy(templates[rid][k]) for k in ['fastenerIds','receiverIds','incomingReceivingWoodFastenerIds','constructionGroupId'] if k in templates[rid]});P[rid]={**metadata,'id':rid,'name':templates[rid].get('name',rid),**q,'coreNegativeToolAppliedToCurrentGeometry':True,'geometryFingerprintRegenerationRequired':True}
  second=(after-cut)-shape(supplement) if supplement else after-cut
  receipts.append({'receiverId':pid,'removedIn3':amount(before-after)/I**3,'secondApplicationChangeIn3':diff(after,second)/I**3,'survivingPhysicalIds':sorted(matched),'nativeComponentResidueM3':residue,'referenceTargetIsUpperBoundOnly':True})
 for pid,p in core['add_parts'].items():
  if pid in P:assert amount(shape(P[pid])-shape(p))<=TOL,('Existing new actor exceeds frozen reference',pid)
  else:P[pid]=copy.deepcopy(p)
 for pid in templates:P[pid]={**P[pid],'closureCorePiece':True}
 source['parts']=list(P.values()) if aslist else P;source['closureCoreComposition']={'status':'NEGATIVE_TOOLS_COMPOSED_DEFAULT_ONLY','receiverCount':len(receipts),'receipts':receipts,'primarySnapshotsOverwritten':False,'joineryFingerprintRefreshRequired':True,'manifestSha256':MANIFEST_SHA,'sourceArchiveSha256':ARCHIVE_SHA,'localWoodReleaseQualification':data['manifest']['releaseQualification'],'causalHardwareMetadataStatus':'PENDING_SEPARATE_RECEIVER_AND_COVER_DELTA','limits':data['manifest']['limits']};return source
def hardware(data=None):
 data=data or inputs();prototypes={**data['retained']['prototypes'],**data['hardware']['prototypes']};parts=[]
 for original in [*data['retained']['instances'],*data['hardware']['instances']]:
  p=copy.deepcopy(original);spec=p['fastenerSpec'];code=spec['partNumber'];p['fastenerKind']='nail' if code.startswith('T') else 'screw';p['intentionalFastenerPenetration']=True
  # TIMESTAMP START 2026-11-05T22:31:25+00:00 | REVISION R000069
  p=apply_causal_metadata(p);parts.append(p)
  # TIMESTAMP END 2026-11-05T22:31:25+00:00 | REVISION R000069
 assert len(parts)==9415 and len({p['id'] for p in parts})==9415
 return {'parts':parts,'prototypes':prototypes,'retainedIds':{p['id'] for p in data['retained']['instances']},'newIds':{p['id'] for p in data['hardware']['instances']}}
# TIMESTAMP START 2026-11-05T23:39:11+00:00 | REVISION R000073
def compose_stock(parts,data=None):
 """Prove each actual current blank/children against serialized positive waste."""
 from itertools import combinations
 from closure_stock_waste import candidate as repaired_candidate,ALLOWED
 data=data or inputs();records={**data['wood']['stock'],**data['wood']['sourceStockRecordOverrides']};solids={};results={};receipts=[]
 for sid,row in records.items():
  blank=shape(row['blank']);audit=inspect_mesh(np.asarray(row['blank']['vertices']),np.asarray(row['blank']['triangles'],np.uint64),True);assert audit['status']=='PASS',('Invalid purchased stock blank',sid,audit)
  for pid in row['children']:
   if pid not in solids:solids[pid]=shape(parts[pid])
  installed=union([solids[pid] for pid in row['children']]);assert amount(installed-blank)<=TOL,('Installed closure exceeds purchased stock',sid);assert abs(sum(solids[pid].volume() for pid in row['children'])-installed.volume())<=TOL,('Installed stock children overlap',sid)
  intended=blank-installed;attempts=[];chosen=None;patch=repaired_candidate(sid,row,parts,require_exact=False);basis=stock_frame(sid,row['blank'],data);origin=np.asarray(row['blank']['vertices']).mean(0);toLocal=np.column_stack([basis.T/I,-basis.T@origin/I]);blankLocal=affine(blank,toLocal);installedLocal=union([affine(solids[pid],toLocal) for pid in row['children']])
  candidates=[]
  if patch:candidates.append(('Repaired serialized waste candidate; fresh actual-current proof required',lambda:copy.deepcopy(patch['fields'])))
  candidates.extend([('Original serialized waste; fresh actual-current proof required',lambda:{'declared_exterior_offcut':copy.deepcopy(row['declared_exterior_offcut'])}),('Current blank minus installed, native serialization',lambda:{'declared_exterior_offcut':native_record(intended,single=False)}),('Net signed blank-minus-current-children contours in stock frame',lambda:{'declared_exterior_offcut':repaired_stock_waste(signed_stock_difference(row['blank'],[parts[pid] for pid in row['children']]),sid,row['blank'],data)}),('Signed current CSG contours in stock frame',lambda:{'declared_exterior_offcut':repaired_stock_waste(mesh(intended),sid,row['blank'],data)}),('Signed archived waste contours, independently compared with current stock',lambda:{'declared_exterior_offcut':repaired_stock_waste(row['declared_exterior_offcut'],sid,row['blank'],data)}),('Net signed current stock contours with1e-11m plane grouping',lambda:{'declared_exterior_offcut':repaired_stock_waste(signed_stock_difference(row['blank'],[parts[pid] for pid in row['children']]),sid,row['blank'],data,1e-11)})])
  for method,build in candidates:
   try:
    fields=build();assert set(fields)<=ALLOWED;separate='declared_exterior_offcut_pieces' in fields;assert separate!=('declared_exterior_offcut' in fields);meshes=fields['declared_exterior_offcut_pieces'] if separate else [fields['declared_exterior_offcut']];assert meshes;pieces=[]
    for record in meshes:
     if record['triangles']:
      proof=inspect_mesh(np.asarray(record['vertices']),np.asarray(record['triangles'],np.uint64),separate);assert proof['status']=='PASS',('Invalid serialized stock waste',sid,proof['failures']);piece=native_solid(record);assert piece.volume()>0;pieces.append(piece)
     else:assert not separate,'Every separate waste piece must contain real positive material'
    waste=union(pieces);wasteLocalPieces=[affine(piece,toLocal) for piece in pieces];wasteLocal=union(wasteLocalPieces)
    errors={'partitionDifferenceM3':diff(blank,installed+waste),'volumeBalanceM3':abs(float(blank.volume()-installed.volume()-waste.volume())),'wasteInstalledOverlapM3':amount(installed^waste),'wasteOutsideBlankM3':amount(waste-blank),'betweenWastePiecesOverlapM3':sum(amount(a^b) for a,b in combinations(pieces,2)),'localPartitionDifferenceM3':diff(blankLocal,installedLocal+wasteLocal)*I**3,'localVolumeBalanceM3':abs(float(blankLocal.volume()-installedLocal.volume()-wasteLocal.volume()))*I**3,'localWasteInstalledOverlapM3':amount(installedLocal^wasteLocal)*I**3,'localWasteOutsideBlankM3':amount(wasteLocal-blankLocal)*I**3,'localBetweenWastePiecesOverlapM3':sum(amount(a^b) for a,b in combinations(wasteLocalPieces,2))*I**3};assert np.isfinite(list(errors.values())).all() and max(errors.values())<=TOL,('Serialized current stock partition fails',sid,{key:value/I**3 for key,value in errors.items()});chosen=fields;attempts.append({'method':method,'status':'PASS'});break
   except (AssertionError,RuntimeError,ValueError) as error:attempts.append({'method':method,'status':'BLOCKED','reason':str(error)[:1600]})
  assert chosen is not None,('No strict current-stock waste serialization passed',sid,attempts)
  clean={key:copy.deepcopy(value) for key,value in row.items() if key not in ALLOWED};clean.update(chosen);clean.update(wasteReadbackStatus='PASS',wasteSource=method,currentStockPartitionDifferenceM3=errors['partitionDifferenceM3'],currentStockVolumeBalanceM3=errors['volumeBalanceM3']);results[sid]=clean;receipts.append({'stockId':sid,**errors,'serializedPositiveWastePieceCount':len(pieces),'separateWastePieces':separate,'repairedSourceGeometryBindingsMatched':patch['originalGeometryBindingsMatched'] if patch else None,'historicalProofInherited':False,'freshCurrentBlankAndChildrenReadback':True,'serializationAttempts':attempts,'installedGeometryChanged':False,'purchasedDimensionsChanged':False})
 return {'newStock':{sid:results[sid] for sid in data['wood']['stock']},'sourceStockRecordOverrides':{sid:results[sid] for sid in data['wood']['sourceStockRecordOverrides']},'serializedWasteComposition':{'status':'PASS','stockCount':len(results),'receipts':receipts,'overlapToleranceM3':TOL,'sourceArchiveUnchanged':True}}
# TIMESTAMP END 2026-11-05T23:39:11+00:00 | REVISION R000073
# TIMESTAMP START 2026-11-05T22:31:25+00:00 | REVISION R000069
@lru_cache(maxsize=1)
def causal_inputs():
 fixture=json.loads(gzip.decompress(CAUSAL_FIXTURE.read_bytes()));assert fixture['schema']=='octagon-frozen-closure-core-causal-1' and fixture['core_manifest_sha256']==MANIFEST_SHA;files={}
 for name,row in fixture['files'].items():
  raw=base64.b64decode(row['base64'],validate=True);assert len(raw)==row['bytes'] and sha(raw)==row['sha256'],('Causal source file changed',name);files[name]=raw
 assert sha(files['delta.json.gz'])==fixture['delta_sha256']==CAUSAL_DELTA_SHA and sha(files['check.json'])==fixture['check_sha256']==CAUSAL_CHECK_SHA
 core=inputs()['manifest'];core_files={row['path']:row['sha256'] for row in core['completeBundleFiles']}
 for row in fixture['existingCoreSourceReferences'].values():assert core_files[row['coreMember']]==row['sha256'],'Causal source reference differs from frozen core'
 delta=json.loads(gzip.decompress(files['delta.json.gz']));check=json.loads(files['check.json']);assert check['status']=='PASS' and check['deltaSHA256']==CAUSAL_DELTA_SHA and not check['positionsChanged'] and not check['meshesChanged'] and not check['errors'];assert delta['sourcesUnchangedDuringRun'] and delta['sourceGuardsAtStart']==delta['sourceGuardsAtEnd'] and delta['sourceStaticReceiverListsPreserved']
 represented={row['sha256'] for row in fixture['files'].values()}|{row['sha256'] for row in fixture['existingCoreSourceReferences'].values()}
 for path,expected in delta['sourceGuardsAtStart'].items():
  assert expected in represented,('Incomplete causal producer source closure',path)
  if path.startswith(str(ROOT)+'/'):assert sha(Path(path).read_bytes())==expected,('Current causal source changed',path)
 assert len(delta['fasteners'])==9415
 return delta
def source_pose(p):
 spec=p.get('fastenerSpec') or p.get('fastener_spec');result={key:p[key] for key in ['mesh_instance','head_m','axis_inward','withdrawal_direction','withdrawal_distance_m'] if key in p};result.update(partNumber=spec['partNumber'],lengthIn=spec['lengthIn']);return result
def apply_causal_metadata(part,delta=None):
 delta=delta or causal_inputs();row=delta['fasteners'][part['id']];pose=source_pose(part);fingerprint=sha(json.dumps(pose,sort_keys=True,separators=(',',':')).encode());assert fingerprint==row['sourcePoseSHA256'] and pose==row['sourcePoseDescriptor'],('Causal metadata source pose changed',part['id']);assert part['parentId']==row['sourceParentId'],('Causal source parent changed',part['id'])
 current=set(part['receiverIds']);assert set(row['sourceReceiverIds'])<=current,('Causal source recipients were removed',part['id']);earlier=list(row['withdrawalReceiverIds']);later=set(row['laterStaticContactIds'])|set(row['laterHeadCoverIds']);uncertain=set(row['uncertainSamePhaseStaticContacts']);assert set(earlier)<=current and not set(earlier)&(later|uncertain),('Later or uncertain contact cannot be an extraction exemption',part['id'])
 result={**part,'parentId':row['parentId'],'withdrawalReceiverIds':earlier,'removalPrerequisites':sorted(set(part.get('removalPrerequisites',[]))|later),'assemblyPrerequisiteWoodIds':row['assemblyPrerequisiteWoodIds'],'withdrawalObstacleCandidateIds':row['withdrawalObstacleCandidateIds'],'causalSourcePoseSha256':fingerprint,'causalMetadataStatus':'SOURCE_BOUND_EARLIER_WOOD_AND_LATER_COVERS_APPLIED'}
 assert result['receiverIds']==part['receiverIds'] and source_pose(result)==pose,'Causal metadata must not alter physical geometry or static recipients'
 return result
# TIMESTAMP END 2026-11-05T22:31:25+00:00 | REVISION R000069
# TIMESTAMP END 2026-11-05T21:51:55+00:00 | REVISION R000068
# TIMESTAMP START 2026-11-05T23:58:27+00:00 | REVISION R000074
def wall_hardware_inventory(original,data=None):
 """Keep exact identities; only two source-declared obsolete anchors retire."""
 data=data or inputs();retained=data['retained'];before=[p['id'] for p in original['instances']];after=[p['id'] for p in retained['instances']];removed={'FAST-ENV-W-STUD-03-0-06','FAST-ENV-W-STUD-14-0-06'};revision=retained['freshWestHardwareCheck'];assert len(before)==len(set(before)) and len(after)==len(set(after)),'Duplicate wall hardware identity';assert original['sourceSHA256']==retained['sourceSHA256'],'Original wall hardware source changed';assert revision['status']=='PASS' and not revision['failed'] and revision['counts']['removedObsoleteStudTopAnchors']==2,'West profile anchor retirement lacks its source receipt';assert set(after)==set(before)-removed and removed<=set(before),('Wall hardware changed beyond the two source-declared obsolete anchors',sorted(set(before)-set(after)),sorted(set(after)-set(before)))
 return {'status':'SOURCE_BOUND_RETAINED_AND_RETIRED_IDS_MATCH','originalCount':len(before),'retainedCount':len(after),'retiredIds':sorted(removed),'retirementReason':'The revised west porch profile removes these two stud-top anchor stations; actual retained poses and receivers come from the separately verified revised source.','retainedGeometryOrPosesChangedByThisCheck':False,'historicalSourceChecksPreserved':True}
# TIMESTAMP END 2026-11-05T23:58:27+00:00 | REVISION R000074
