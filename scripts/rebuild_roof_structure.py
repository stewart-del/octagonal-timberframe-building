# TIMESTAMP START 2026-11-05T08:15:49+00:00 | REVISION R000034
"""Reproduce OUT rafters, supported hip planes and true octagonal eave tails.

Stage fresh static/contact/local-motion evidence from exact frozen inputs;
merge only the intended B/R/J records into the current source on --apply.
Legacy closed-head variants retain their blocked independent erection paths.
"""
from pathlib import Path
import argparse,copy,gzip,hashlib,json
from roof_support_recipe import build as add_supports
from hip_backing_recipe import build as back_hips
from hip_eave_recipe import build as trim_eaves
from rebuild_cupola import readable
ROOT=Path(__file__).resolve().parents[1]
FILES={'baseline':'model-data.json','proposed':'step-lap-proposed-model.json','top-entry':'top-entry-proposed-model.json'}
STAMP={'revision':'R000034','timestamp':'2026-11-05T08:15:49+00:00'}
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,data):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(readable(data)+'\n')
def production(p):
 p=copy.deepcopy(p);p.pop('research_only',None)
 if '-OUT' in p['id']:
  p['notes']=['Additional actual4×8 common rafter with matching perimeter seat and upper hip bearing. Top-entry variants use a2in full-width bearing nose; historical closed-head variants retain their3in joint profile and blocked independent lift. Geometric fit does not assign connection or span capacity.']
 if p.get('new_stock_requirements'):p['new_stock_requirements']['status']='Measured minimum blank, add cutting and dressing allowance. Connection capacity unqualified.'
 return p
def rebuild(output,apply=False):
 fixture=ROOT/'scripts/fixtures/roof-structure-inputs.json.gz';frozen=json.loads(gzip.decompress(fixture.read_bytes()));models={};reports={};stocks={}
 for variant,name in FILES.items():
  folder=output/variant;folder.mkdir(parents=True,exist_ok=True);record=frozen['files'][name];source=folder/'frozen-input.json';source.write_text(record['content']);assert sha(source)==record['sha256']
  out=folder/'outer';outer=add_supports(source,out);assert outer['static_primary_audit']['status']=='PASS'
  if variant=='top-entry':assert all(p['proof']['status']=='PASS' for p in outer['continuous_initial_withdrawals'])
  patch=read(out/'roof-support-patch.json');intermediate=read(out/'roof-support-model.json')
  backing_folder=folder/'backing';backing=back_hips(out/'roof-support-model.json',backing_folder)
  back_patch=read(backing_folder/'backed-R-patch.json');intermediate['parts']=[back_patch['replace_parts'].get(p['id'],p) for p in intermediate['parts']]
  eave_parts,eave_report=trim_eaves(intermediate)
  combined={**patch['replace_parts'],**patch['add_parts'],**back_patch['replace_parts'],**eave_parts}
  current=read(ROOT/'src'/name);ids={p['id'] for p in current['parts']};model=copy.deepcopy(current)
  model['parts']=[production(combined[p['id']]) if p['id'] in combined else copy.deepcopy(p) for p in current['parts']]+[production(p) for pid,p in combined.items() if pid not in ids]
  joints={j['id']:j for j in patch['append_tenon_schedule']};model['tenon_schedule']=[joints.pop(j['id'],j) for j in model['tenon_schedule']]+list(joints.values())
  model['joinery_entry_regions']={**model.get('joinery_entry_regions',{}),**intermediate['joinery_entry_regions']}
  model['roof_structure_revision']={**STAMP,'input_sha256':record['sha256'],'new_outer_rafters':16,'hip_backing_stop_radial_in':45,'eave_face_apothem_in':eave_report['face_apothem_in'],'scope':'Primary static/contact and scoped release evidence only. Full current architecture/cavity/stock/parameter/erection proofs and project capacity remain separate.'}
  assert sum(bool(p.get('is_timber')) for p in model['parts'])==129
  assert len({p['id'] for p in model['parts']})==len(model['parts'])
  models[name]=model;stocks[variant]=read(out/'roof-support-stock.json');reports[variant]={'outer':outer,'backing':backing,'eave':eave_report}
  save(folder/name,model);save(folder/'roof-structure-audit.json',reports[variant]);print(variant,'STAGED129timbers',flush=True)
 if apply:
  for name,model in models.items():save(ROOT/'src'/name,model)
  save(ROOT/'src/roof-structure-stock.json',{**STAMP,'variants':stocks})
  names=['scripts/rebuild_roof_structure.py','scripts/roof_support_recipe.py','scripts/hip_backing_recipe.py','scripts/hip_eave_recipe.py','scripts/fixtures/roof-structure-inputs.json.gz','requirements-geometry.txt']
  save(ROOT/'docs/roof-structure-audit.json',{**STAMP,'status':'PASS','scope':'Fresh primary static/contact and bounded local paths. Legacy closed heads remain blocked; full architectural/cavity/stock/parameter proofs are separate.','sources':{n:sha(ROOT/n) for n in names},'models':{n:sha(ROOT/'src'/n) for n in models},'variants':reports,'capacity_verified':False})
 return models,reports,stocks
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=ROOT/'.codex-runtime/roof-structure');parser.add_argument('--apply',action='store_true');args=parser.parse_args();rebuild(args.output,args.apply)
# TIMESTAMP END 2026-11-05T08:15:49+00:00 | REVISION R000034
