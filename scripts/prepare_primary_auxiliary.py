# TIMESTAMP START 2026-11-05T15:44:02+00:00 | REVISION R000051
"""Current primary-member inventory and assumed-density self-weight inputs.

Family grouping does not assert identical cuts or fabrication interchangeability.
Roof, floor, wall and porch quantities belong to the complete component schedule.
"""
from pathlib import Path
import argparse,hashlib,json,shutil
import numpy as np
from audit_revised_joinery import native_solid
from step_lap import volume_centroid
ROOT=Path(__file__).resolve().parents[1]
VARIANTS={'baseline':('model-data.json','material-groups.json','load-review-data.json'),'proposed':('step-lap-proposed-model.json','step-lap-proposed-material-groups.json','step-lap-proposed-load-review.json'),'top-entry':('top-entry-proposed-model.json','top-entry-proposed-material-groups.json','top-entry-proposed-load-review.json')}
TOL=1e-6*.0254**3
STAMP={'revision':'R000051','timestamp':'2026-11-05T15:44:02+00:00'}
def sha(raw):return hashlib.sha256(raw).hexdigest()
def derive(model,source_hash):
 parts=model['parts'];assert len(parts)==len({p['id'] for p in parts});groups={};members=[];fasteners=[]
 labels={g['id']:g.get('label',g.get('name',g['id'])) for g in model.get('groups',[])}
 for p in parts:
  family=p.get('group','other');key=(family,p.get('material',''),bool(p.get('is_timber')))
  if key not in groups:
   number=len(groups)+1;groups[key]={'id':'M'+str(number).zfill(2),'number':number,'quantity':0,'member_ids':[],'representative_id':p['id'],'family':family,'label':labels.get(family,family.replace('_',' ')),'status':'Generation family only. Inspect each actual member and blank; matching cuts and interchangeability are not certified.','method':'Explicit current source membership; no inferred fabrication equivalence'}
  groups[key]['quantity']+=1;groups[key]['member_ids'].append(p['id'])
  if p.get('is_timber') or p.get('is_fastener'):
   s=native_solid(p);assert str(s.status())=='Error.NoError' and s.volume()>0,p['id'];q={'id':p['id'],**volume_centroid(s)}
   assert q['volume_m3']>0 and np.isfinite(q['centroid_m']).all(),p['id']
   (members if p.get('is_timber') else fasteners).append(q)
 materials={**STAMP,'schema_version':'current-primary-generation-families-1','source_sha256':source_hash,'timber_count':len(members),'item_count':len(parts),'group_count':len(groups),'comparison_tolerance_m':None,'scope':'Current primary generation/material families. Individual stock and cuts remain separate; no fabrication interchangeability claim. Complete architectural products and hardware are in the full component schedule.','groups':list(groups.values()),'handed_pair_checks':[],'reference_end_semantics':'A/B are the actual selected member reference ends; inspect current geometry.'}
 loads={**STAMP,'source_model_sha256':source_hash,'members':members,'issues':[],'sources':{'scripts/prepare_primary_auxiliary.py':sha(Path(__file__).read_bytes())},'density_basis':'User-selected illustrative timber density, not a measured grade/species or verified building dead load.','fasteners':fasteners,'fastener_volume_m3':sum(p['volume_m3'] for p in fasteners),'fastener_scope':'Separate primary fastening-component volumes; not included in the primary timber subtotal. Full component quantities are itemized separately.','baseline_pressure_disabled':True,'status':'Applied self-weight of actual current primary timber geometry only. Joint reactions, pressures and capacities are unsolved; floor, walls, porch, roofing and other added loads are outside this subtotal.'}
 assert {pid for g in materials['groups'] for pid in g['member_ids']}=={p['id'] for p in parts}
 return materials,loads

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--output-directory',required=True,type=Path);parser.add_argument('--install',action='store_true');args=parser.parse_args();args.output_directory.mkdir(parents=True,exist_ok=True);records={};outputs=[];models={};solids={}
 for variant,(name,material_name,load_name) in VARIANTS.items():
  path=ROOT/'src'/name;raw=path.read_bytes();model=json.loads(raw);digest=sha(raw);models[variant]=model;materials,loads=derive(model,digest)
  for filename,value in [(material_name,materials),(load_name,loads)]:
   output=args.output_directory/filename;output.write_text(json.dumps(value,separators=(',',':'))+'\n');outputs.append((output,ROOT/'src'/filename))
  records[variant]={'source_model_sha256':digest,'timber_count':len(loads['members']),'primary_item_count':len(model['parts']),'primary_fastener_count':len(loads['fasteners']),'total_primary_timber_volume_m3':sum(q['volume_m3'] for q in loads['members']),'materials_sha256':sha((args.output_directory/material_name).read_bytes()),'loads_sha256':sha((args.output_directory/load_name).read_bytes())};print(variant,records[variant],flush=True)
  solids[variant]={p['id']:native_solid(p) for p in model['parts'] if p.get('is_timber')}
 base=solids['baseline'];comparisons={}
 for variant in ['proposed','top-entry']:
  selected=solids[variant];changes=[]
  for pid in sorted(set(base)&set(selected)):
   added=max(0.,float((selected[pid]-base[pid]).volume()));removed=max(0.,float((base[pid]-selected[pid]).volume()))
   if added+removed>TOL:changes.append({'id':pid,'added_material_m3':added,'removed_material_m3':removed})
  comparisons[variant]={'native_changed_timber_ids':[q['id'] for q in changes],'changes':changes,'added_timber_ids':sorted(set(selected)-set(base)),'removed_timber_ids':sorted(set(base)-set(selected)),'overlap_tolerance_m3':TOL,'scope':'Actual current occupied-material comparison against the current baseline; no old comparison is relabeled.'}
 report={**STAMP,'status':'PASS','scope':'Actual current primary inventories, native positive volumes/centroids and occupied variant comparisons only. Cavity, architecture, movement and capacity checks remain separate.','generator_sha256':sha(Path(__file__).read_bytes()),'variants':records,'comparisons':comparisons};report_path=args.output_directory/'primary-model-audit.json';report_path.write_text(json.dumps(report,indent=2)+'\n')
 if args.install:
  for variant,(name,_,_) in VARIANTS.items():assert sha((ROOT/'src'/name).read_bytes())==records[variant]['source_model_sha256'],'Source changed during derivation'
  for source,target in outputs:shutil.copyfile(source,target)
  shutil.copyfile(report_path,ROOT/'docs/primary-model-audit.json');print('Installed fresh primary auxiliary data',flush=True)
if __name__=='__main__':main()
# TIMESTAMP END 2026-11-05T15:44:02+00:00 | REVISION R000051
