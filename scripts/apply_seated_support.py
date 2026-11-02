"""Scoped deterministic support-only migration across all selected revisions."""
import copy,hashlib,json
from pathlib import Path
from support_fit import fit_fixture
ROOT=Path(__file__).resolve().parents[1]
def replace(value,old,new):
 if isinstance(value,str):return value.replace(old,new)
 if isinstance(value,list):return [replace(x,old,new) for x in value]
 if isinstance(value,dict):return {k:replace(v,old,new) for k,v in value.items()}
 return value
def migrate(root=ROOT):
 artifacts=list((root/'src').glob('*.json'))+[root/'docs/joinery-verification.json']
 originals={p:json.loads(p.read_text()) for p in artifacts}
 models=['model-data.json','step-lap-proposed-model.json','top-entry-proposed-model.json']
 mapping={};revised={};changes=[]
 for name in models:
  path=root/'src'/name
  if path not in originals:continue
  old=hashlib.sha256(path.read_bytes()).hexdigest();model=copy.deepcopy(originals[path]);prior=copy.deepcopy(model)
  for a,b in mapping.items():model=replace(model,a,b)
  if name=='step-lap-proposed-model.json':
   model['source_model']='Separate proposed model derived from baseline '+hashlib.sha256(revised.get(root/'src/model-data.json',(root/'src/model-data.json').read_bytes())).hexdigest()
  if name=='top-entry-proposed-model.json':
   source_path=root/'src/step-lap-proposed-model.json'
   source_sha=hashlib.sha256(revised.get(source_path,source_path.read_bytes())).hexdigest()
   model['source_model']='Separate top-entry model derived from V13 perimeter model '+source_sha
  fixture,report=fit_fixture(model)
  model['parts']=[fixture if p['id']=='M-TMP' else p for p in model['parts']]
  assert [p for p in prior['parts'] if p['id']!='M-TMP']==[p for p in model['parts'] if p['id']!='M-TMP']
  if model==prior:continue
  raw=(json.dumps(model,separators=(',',':'))+'\n').encode();new=hashlib.sha256(raw).hexdigest()
  mapping[old]=new;revised[path]=raw
  changes.append({'model':name,'previous_sha256':old,'new_sha256':new,'timber_records_unchanged':True,'fit':report})
 for path,data in originals.items():
  if path in revised:path.write_bytes(revised[path]);continue
  updated=data
  for a,b in mapping.items():updated=replace(updated,a,b)
  if updated!=data:
   pretty=path.read_text().startswith('{\n')
   path.write_text((json.dumps(updated,indent=2) if pretty else json.dumps(updated,separators=(',',':')))+'\n')
 return changes
if __name__=='__main__':
 changes=migrate()
 if changes:
  checkpoint=ROOT/'docs/seated-support-migration.json'
  previous=json.loads(checkpoint.read_text()) if checkpoint.exists() else []
  checkpoint.write_text(json.dumps(previous+changes,indent=2)+'\n')
 print(json.dumps([{k:v for k,v in c.items() if k!='fit'} for c in changes],indent=2))
