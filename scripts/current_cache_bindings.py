# TIMESTAMP START 2026-11-05T20:08:59+00:00 | REVISION R000063
"""Strict current applicability of original floor/wall/porch geometry caches.

Original cache source headers and certificates are preserved. The independent
fresh native ownership checks bind every actual influential input and proof;
this separate metadata is never a whole-building construction certificate.
"""
from pathlib import Path,PurePosixPath
import copy,hashlib,io,json,tarfile
ROOT=Path(__file__).resolve().parents[1]
FIXTURE=ROOT/'scripts/fixtures/current-cache-binding.tar.gz'
FIXTURE_SHA='807b6eaf5e525ebf90bbd89f4ebfe444092982d250fd9ce6313075b4cffdb8fb'
BINDING_SHA='b1658b1208dd12cffa8860b10ef136e3f294b6bba40937b37cbf428b933d36f5'
PREFIX='cache-ownership-audit/'
CACHE_FILES={'floor':'src/floor-foundation-solids.json','wall':'src/wall-joinery-fit.json','porch':'src/mudroom-joinery-fit.json','enclosure-baseline':'src/enclosure-fit.json','enclosure-proposed':'src/step-lap-proposed-enclosure-fit.json','enclosure-top-entry':'src/top-entry-proposed-enclosure-fit.json'}
STATUS='PASS_BOUNDED_CURRENT_INPUT_BINDING_ONLY'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def package():
 raw=FIXTURE.read_bytes();assert sha(raw)==FIXTURE_SHA,'Current cache proof package changed'
 with tarfile.open(fileobj=io.BytesIO(raw),mode='r:gz') as archive:
  files={}
  for member in archive.getmembers():
   name=PurePosixPath(member.name);assert not name.is_absolute() and '..' not in name.parts,'Unsafe cache proof path'
   if member.isdir():continue
   assert member.isfile() and member.name not in files,'Unsupported cache proof entry';files[member.name]=archive.extractfile(member).read()
 manifest=json.loads(files[PREFIX+'manifest.json'])
 for name,row in manifest['files'].items():assert name in files and sha(files[name])==row['sha256'] and len(files[name])==row['bytes'],('Changed native compatibility artifact',name)
 binding_raw=files[PREFIX+'current-source-scoped-cache-binding.json'];assert sha(binding_raw)==BINDING_SHA
 return json.loads(binding_raw),files

def verify(repo=ROOT,*,read_source=None,alter_evidence=None):
 binding,files=package();repo=Path(repo);read_source=read_source or (lambda name:(repo/name).read_bytes());files=alter_evidence(files.copy()) if alter_evidence else files
 assert binding['status']=='PASS_BOUNDED_CURRENT_INPUT_COMPATIBILITY' and binding['preserveHistoricalCacheMetadata'] and binding['separateCurrentSourceAndWholeAssemblyGatesRequired'];assert binding['collisionToleranceIn3']==1e-6
 for name,expected in binding['repositoryInputs'].items():assert sha(read_source(name))==expected,('Current cache source input changed',name)
 for name,expected in binding['artifactInputs'].items():assert sha(files[PREFIX+name])==expected,('Current cache native evidence changed',name)
 for name,expected in binding['producerInputs'].items():
  key=PREFIX+name if name=='verify-scoped-binding.py' else name;assert sha(files[key])==expected,('Current cache producer changed',name)
 return {'schema':'octagon-current-cache-ownership-1','status':STATUS,'bindingSha256':BINDING_SHA,'fixtureSha256':FIXTURE_SHA,'models':binding['acceptedCurrentModelSha256'],'caches':{key:binding['repositoryInputs'][path] for key,path in CACHE_FILES.items()},'repositoryInputs':binding['repositoryInputs'],'scopes':binding['acceptedScopes'],'wholeBuildingReady':False,'preserveHistoricalHeaders':True}

def runtime_descriptor(descriptor):
 return {key:copy.deepcopy(value) for key,value in descriptor.items() if key!='repositoryInputs'}

def attach(cache,key,variant,descriptor):
 assert descriptor['status']==STATUS and descriptor['bindingSha256']==BINDING_SHA;assert key in CACHE_FILES and variant in descriptor['models'];assert not key.startswith('enclosure-') or key=='enclosure-'+variant
 # No original source_model/module/fitter header or old certificate changes.
 return {**cache,'currentSourceBinding':{'status':STATUS,'bindingSha256':BINDING_SHA,'fixtureSha256':FIXTURE_SHA,'cacheKey':key,'cacheSha256':descriptor['caches'][key],'variant':variant,'currentModelSha256':descriptor['models'][variant],'preservedHistoricalHeaders':True}}

def load_cache(key,variant,descriptor,*,physical=False):
 assert key in CACHE_FILES and descriptor['status']==STATUS
 path=ROOT/CACHE_FILES[key];raw=path.read_bytes();assert sha(raw)==descriptor['caches'][key],('Current cache bytes changed during load',key)
 if physical:
  from physical_data import read_physical_json
  value=read_physical_json(path)
 else:value=json.loads(raw)
 if key=='wall':return {**value,'variants':{name:attach(row,key,name,descriptor) for name,row in value['variants'].items()}}
 return attach(value,key,variant,descriptor)

def assert_applies(cache,key,variant,descriptor):
 proof=cache.get('currentSourceBinding');assert proof and proof['status']==STATUS and proof['bindingSha256']==BINDING_SHA and proof['fixtureSha256']==FIXTURE_SHA and proof['cacheKey']==key and proof['variant']==variant and proof['currentModelSha256']==descriptor['models'][variant] and proof['cacheSha256']==descriptor['caches'][key] and proof['preservedHistoricalHeaders'],('Cache has no verified current applicability',key,variant)
 return True

def write_descriptor(path=ROOT/'src/current-cache-bindings.json'):
 descriptor=verify();Path(path).write_text(json.dumps(descriptor,indent=2)+'\n');return descriptor
if __name__=='__main__':
 import argparse
 parser=argparse.ArgumentParser();parser.add_argument('--write',action='store_true');args=parser.parse_args();result=write_descriptor() if args.write else verify();print(json.dumps({'status':result['status'],'inputs':len(result['repositoryInputs']),'scopes':result['scopes'],'wholeBuildingReady':False}))
# TIMESTAMP END 2026-11-05T20:08:59+00:00 | REVISION R000063
