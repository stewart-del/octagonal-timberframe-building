# TIMESTAMP START 2026-11-05T23:02:22+00:00 | REVISION R000071
"""Guarded Cu head retention correction; preserve every unaffected roof actor."""
from pathlib import Path
from functools import lru_cache
import base64,copy,gzip,hashlib,json
from audit_revised_joinery import native_solid
from cupola_joinery_recipe import diff,TOL
ROOT=Path(__file__).resolve().parents[1];FIXTURE=ROOT/'scripts/fixtures/cupola-roof-bearing-inputs.json.gz'
FIXTURE_SHA='496d5d0f928074d457cc3cfed7fe4ddd9ae6d6dcd93a1b7b3fb091134b2718ed'
MANIFEST_SHA='356e1e12916746c12769539771f539398bb1136e2ea432bac824204a4428c41f'
def sha(raw):return hashlib.sha256(raw).hexdigest()
@lru_cache(maxsize=1)
def inputs():
 raw=FIXTURE.read_bytes();assert sha(raw)==FIXTURE_SHA,'Cupola bearing fixture changed';source=json.loads(gzip.decompress(raw));assert source['schema']=='octagon-frozen-cupola-roof-bearing-1';files={}
 for name,row in source['files'].items():
  data=base64.b64decode(row['base64'],validate=True);assert len(data)==row['bytes'] and sha(data)==row['sha256'],('Cupola bearing source changed',name);files[name]=data
 assert sha(files['manifest.json'])==source['manifestSha256']==MANIFEST_SHA;manifest=json.loads(files['manifest.json'])
 for row in [*manifest['assets'].values(),*manifest['frozen_recipe_import_closure'].values()]:assert sha(files[row['path']])==row['sha256']
 assert sha(files[manifest['reproducer']])==manifest['reproducer_sha256']
 from cupola_roof_parts import inputs as original_roof
 from main_roof_membrane_parts import inputs as main_roof,V1_SHA,V2_SHA
 original=original_roof();main=main_roof();represented={sha(data) for data in [*files.values(),*original.values()]}|{V1_SHA,V2_SHA}|{row['sha256'] for key in ['v1','v2'] for row in main[key]['assets'].values()}
 guards=json.loads(files['assets/source-guards.json'])
 for row in guards['inputs']:assert row['sha256'] in represented,('Missing current cupola correction source',row['path'])
 expected={row['manifest_sha256'] for row in manifest['immutable_dependencies']};assert expected<={sha(original['manifest.json']),V1_SHA,V2_SHA}
 def decode(name):return json.loads(gzip.decompress(files[name]) if name.endswith('.gz') else files[name])
 return {**source,'manifest':manifest,'copper':decode('assets/replacement-cupola-copper.json.gz')['parts'],'nails':decode('assets/cupola48-instances.json.gz')['instances'],'prototypes':decode('assets/prototypes.json')['prototypes'],'guard':guards,'proof':decode('assets/report.json'),'covers':decode('assets/actual-causal-cover-receipts.json')}
def compose(current,data=None):
 data=data or inputs();parts={p['id']:p for p in current['parts']};assert len(parts)==len(current['parts'])==385,'Cupola roof actor inventory changed';copper={p['id']:p for p in data['copper']};nails={p['id']:p for p in data['nails']};assert len(copper)==17 and len(nails)==48 and set(copper)==set(data['originalCu']) and set(nails)==set(data['originalNailPoses']);assert (set(copper)|set(nails))<=set(parts),'Missing cupola correction recipient';changed={};prototypes=dict(current['prototypes'])
 for name,record in data['prototypes'].items():prototypes['CUP-BEARING-'+name]=copy.deepcopy(record['metal'])
 for pid,replacement in copper.items():
  p=parts[pid];actual=native_solid(p);old=native_solid(data['originalCu'][pid]);new=native_solid(replacement);assert min(diff(actual,old),diff(actual,new))<=TOL,('Current Cu changed; never overwrite a later cavity',pid)
  changed[pid]={**p,**copy.deepcopy(replacement),'headBearingCorrectionManifestSha256':MANIFEST_SHA}
  if pid.startswith('CU-DRIP-'):changed[pid]['freshNailHoleCount']=len(replacement['actualNailIds'])
 for pid,replacement in nails.items():
  p=parts[pid];old=data['originalNailPoses'][pid];oldmeta=data['originalNailMetadata'][pid];new=copy.deepcopy(replacement);name='CUP-BEARING-'+new['mesh_instance']['prototype'];placed={**new['mesh_instance'],'prototype':name};assert p['mesh_instance'] in [old['mesh_instance'],placed],('Current nail pose changed before bearing correction',pid);spec=p.get('fastenerSpec',p.get('fastener_spec',{}));assert spec['partNumber']==new['sku'] and spec.get('lengthIn',spec.get('nominalLengthIn'))==new['length_in'],('Nail product changed before bearing correction',pid)
  later=set(new['extractionBlockedBy'])|set(new['withdrawalPrerequisiteIds'])|(set(p.get('removalPrerequisites',[]))-set(oldmeta.get('removalPrerequisites',[])));assert later<=set(parts),'Missing actual later Cu cover';extras=set(p['receiverIds'])-set(oldmeta['receiverIds']);receivers=sorted(set(new['receiverIds'])|extras);earlier=new['withdrawalReceiverIds'];assert set(earlier)<=set(receivers) and not set(earlier)&later
  spec=copy.deepcopy(new['fastenerSpec']);spec['lengthIn']=new['length_in'];new.update(name='Cupola roof nail '+pid,mesh_instance=placed,receiverIds=receivers,withdrawalReceiverIds=earlier,removalPrerequisites=sorted(later),assemblyPrerequisiteIds=new['installAfterIds'],fastenerSpec=spec,actualHeadBearing=True,headBearingCorrectionManifestSha256=MANIFEST_SHA);changed[pid]={**p,**new}
 result={**current,'parts':[changed.get(p['id'],p) for p in current['parts']],'prototypes':prototypes};report=dict(current['report']);report['supersededDripHoleRecipe']=report.pop('drip_hole_composition',[]);report['drip_hole_composition']=[{'id':pid,'actual_hole_tools':len(p['actualNailIds']),'holeProfile':'Actual nail shank only; head retained above Cu'} for pid,p in copper.items() if pid.startswith('CU-DRIP-')];report['bearingCorrection']={'status':'DEFAULT_BOUND_CU_AND_NAIL_CORRECTION_APPLIED','manifestSha256':MANIFEST_SHA,'fixtureSha256':FIXTURE_SHA,'generatorSha256':sha(Path(__file__).read_bytes()),'replacementCu':17,'correctedNailPoses':48,'packageParts':385,'historicalBoundedProofStatus':data['proof']['status'],'laterCuCoverPrerequisites':48,'limits':data['manifest']['limitations']};result['report']=report
 assert len(result['parts'])==385 and len(changed)==65
 return result
# TIMESTAMP END 2026-11-05T23:02:22+00:00 | REVISION R000071
