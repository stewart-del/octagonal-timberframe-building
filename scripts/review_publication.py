# TIMESTAMP START 2026-11-06T03:14:49+00:00 | REVISION R000083
"""Publish a current progress model while preserving its unfinished status."""
from pathlib import Path
import hashlib
from physical_data import read_physical_json

NOTICE='Work in progress. Individual wall assembly, exterior siding, weather seals and dimension-dependent animation are still being completed.'

def load_architecture(root,review=False):
 root=Path(root);path=root/'src'/('review-architectural-solids.json'if review else'architectural-solids.json');data=read_physical_json(path)
 assert data['schema']=='octagon-articulated-architecture-1','Unsupported architectural export'
 assert data['source_generator_sha256']==hashlib.sha256((root/'scripts/prepare_architecture.py').read_bytes()).hexdigest(),'Architectural export generator changed'
 assert data['source_fixture_sha256']==hashlib.sha256((root/'scripts/fixtures/architectural-inputs.json.gz').read_bytes()).hexdigest(),'Architectural export fixture changed'
 assert data['sourceFloorSha256']==hashlib.sha256((root/'src/floor-foundation-solids.json').read_bytes()).hexdigest(),'Architectural floor source changed'
 ids=[part['id']for part in data['parts']];assert ids and len(ids)==len(set(ids)),'Empty or duplicate architectural actors'
 for part in data['parts']:
  if part.get('mesh_instance'):assert part['mesh_instance']['prototype']in data['prototypes'],'Missing physical prototype'
 if review:
  assert data['status']=='STAGING_INCOMPLETE_DO_NOT_PUBLISH','Progress publication requires the explicit incomplete source export'
  data={**data,'publication':{'mode':'work-in-progress','notice':NOTICE,'constructionComplete':False,'orderedMotionQualified':False,'sourceStatus':data['status']}}
 else:assert data['status']=='PASS','The detailed architectural assembly is not ready for final publication'
 return data

def unavailable_plans():
 return {'publicationMode':'work-in-progress','variants':{name:{'status':'PARTIAL','verification':{'status':'UNAVAILABLE','reason':'The current component set does not have a complete verified construction route.'},'stages':[],'physical_ids':[],'moved_ids':[],'unmoved_ids':[],'anchored_ids':[],'excluded':[],'blocked':[],'sources':{}}for name in ['baseline','proposed','top-entry']}}

def notice_html(review):
 return '<p id="publicationStatus" class="navigation-status" role="status"><strong>Work in progress</strong><br>'+NOTICE.removeprefix('Work in progress. ')+'</p>'if review else''
# TIMESTAMP END 2026-11-06T03:14:49+00:00 | REVISION R000083
