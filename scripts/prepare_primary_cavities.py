# TIMESTAMP START 2026-11-05T17:01:40+00:00 | REVISION R000056
"""Rebuild current primary cavities and audit every actual member from disk.

The original production audit function remains unchanged. Stock-local input
geometry and serialization fix numerical conditioning, with the same volume
limits, actual mating solids and explicitly authored entry regions.
"""
from pathlib import Path
import argparse,ast,copy,hashlib,json,time
import numpy as np
import export_top_entry_cavities as exporter
import current_roof_cavity_partitions as roof
from primary_actual_mate_seed import build as actual_mate_seed
from audit_revised_joinery import native_solid
from audit_cavity_fit import inspect_mesh,arrays
from prepare_primary_auxiliary import VARIANTS
ROOT=Path(__file__).resolve().parents[1];I=.0254;TOL=1e-6*I**3
OUTPUTS={'baseline':('cavity-data.json','cavity-fit-audit.json'),'proposed':('step-lap-proposed-cavities.json','step-lap-proposed-cavity-fit-audit.json'),'top-entry':('top-entry-proposed-cavities.json','top-entry-cavity-fit-audit.json')}
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):return json.loads(Path(path).read_text())
def save(path,value):Path(path).write_text(json.dumps(value,separators=(',',':'))+'\n')
def method_hash(path,name):return hashlib.sha256(ast.dump(next(x for x in ast.parse(Path(path).read_text()).body if isinstance(x,ast.FunctionDef) and x.name==name),include_attributes=False).encode()).hexdigest()
def generate(variant,directory,install=False):
 start=time.monotonic();directory=Path(directory);directory.mkdir(parents=True,exist_ok=True);roof.OUT=directory/'diagnostics';roof.OUT.mkdir(exist_ok=True)
 model_path=ROOT/'src'/VARIANTS[variant][0];proposal_path=ROOT/'src/top-entry-proposal.json';seeds_path=ROOT/'src/unchanged-roof-cavity-seeds.json'
 paths=[model_path,proposal_path,seeds_path]+[ROOT/'scripts'/name for name in ['prepare_primary_cavities.py','current_roof_cavity_partitions.py','primary_actual_mate_seed.py','export_top_entry_cavities.py','audit_revised_joinery.py','audit_cavity_fit.py','step_lap.py','apply_joinery_revision.py','three_inch_tenons.py','center_brace_tenons.py','floor_surface_normalization.py','fit_wall_joinery.py','revise_main_braces.py']]
 sources={str(path.relative_to(ROOT)):sha(path) for path in paths};model=read(model_path);proposal=read(proposal_path);entry_proposal=proposal if variant=='top-entry' else {'representative':{'interfaces':[]}};parts={p['id']:p for p in model['parts']};receipts=[];seed_rows=[];seeds=copy.deepcopy(read(seeds_path)['variants'][variant]);original_solid=exporter.solid;original_entries=exporter.entry_regions;original_packed=exporter.packed;counter=[0]
 exporter.solid=native_solid
 try:
  for pid in ['R0','J0-OUT0','J0-OUT2']:
   record,row=roof.build_record(model,entry_proposal,pid,receipts);seeds[pid]={'part_sha256':hashlib.sha256(json.dumps(parts[pid],sort_keys=True,separators=(',',':')).encode()).hexdigest(),'record':record};seed_rows.append(row)
  if variant!='top-entry':
   record,row=actual_mate_seed(model,entry_proposal,'P0',receipts);seeds['P0']={'part_sha256':hashlib.sha256(json.dumps(parts['P0'],sort_keys=True,separators=(',',':')).encode()).hexdigest(),'record':record};seed_rows.append(row)
  entries=original_entries(entry_proposal,model);exporter.entry_regions=lambda _proposal,model=None:entries
  def packed(shape):
   counter[0]+=1
   if shape.is_empty() or abs(shape.volume())<=exporter.ROUND_OFF:return copy.deepcopy(exporter.EMPTY)
   origin=np.asarray(shape.bounding_box()).reshape(2,3).mean(0);local=shape.translate((-origin).tolist()).scale([1/I]*3);record=roof.pack_local(local,origin,variant+'-generated-'+str(counter[0]).zfill(4),'boundary',receipts);record['edges']=[list(e) for e in sorted({tuple(sorted((int(t[k]),int(t[(k+1)%3])))) for t in record['triangles'] for k in range(3)})];return record
  exporter.packed=packed
  cavities=exporter.generate(model,proposal,unchanged_seeds=seeds);cavities.update(schema_version='current-primary-cavities-1',source_model_sha256=sources[str(model_path.relative_to(ROOT))],sources=sources,retained_geometry_policy='Fresh source-bound R/OUT and legacyP0 seeds; historical geometry only on exact source fingerprints. Every129member is independently audited anew.')
  cavity_name,report_name=OUTPUTS[variant];cavity_path=directory/cavity_name;save(cavity_path,cavities);disk=read(cavity_path);report=exporter.audit(model,disk,proposal);assert report['status']=='PASS' and len(report['members'])==129,report['failures']
  raw=[]
  for part in model['parts']:
   if not part.get('is_timber'):continue
   proof=inspect_mesh(*arrays(part),require_single=True);assert proof['status']=='PASS',(part['id'],'source timber boundary',proof);raw.append({'id':part['id'],'kind':'source_timber','proof':proof});blank=exporter.stock(part);mesh=blank.to_mesh64();proof=inspect_mesh(np.asarray(mesh.vert_properties)[:,:3],np.asarray(mesh.tri_verts,np.uint64),require_single=True);assert proof['status']=='PASS',(part['id'],'raw stock boundary',proof);raw.append({'id':part['id'],'kind':'stock','proof':proof})
 finally:
  exporter.solid=original_solid;exporter.entry_regions=original_entries;exporter.packed=original_packed
 for relative,digest in sources.items():assert sha(ROOT/relative)==digest,('Source changed during cavity generation/audit',relative)
 report.update(schema_version='current-primary-cavity-audit-1',sources=sources,model_sha256=sources[str(model_path.relative_to(ROOT))],cavity_sha256=sha(cavity_path),scope='Fresh complete129primary stock, actualmate, explicitentry, strictboundary and winding audit. Architecture, motion and capacity remain separately verified.')
 save(directory/report_name,report);summary={'status':'PASS','variant':variant,'sources':sources,'model_sha256':report['model_sha256'],'cavity_sha256':report['cavity_sha256'],'original_audit_method_ast_sha256':method_hash(ROOT/'scripts/export_top_entry_cavities.py','audit'),'timbers':129,'strict_source_and_stock_raw':raw,'seed_rows':seed_rows,'serialization_receipts':receipts,'serializer_call_count':counter[0],'independent_winding_samples':sum(r['independent_winding_samples'] for r in report['members']),'uncovered_winding_samples':sum(r['uncovered_winding_samples'] for r in report['members']),'maximum_member_error_m3':max(v for r in report['members'] for v in r['errors_m3'].values()),'unchanged_tolerance_m3':TOL,'elapsed_seconds':time.monotonic()-start};save(directory/'generation-summary.json',summary)
 if install:
  for relative,digest in sources.items():assert sha(ROOT/relative)==digest,('Changed cavity input before install',relative)
  (ROOT/'src'/cavity_name).write_bytes(cavity_path.read_bytes());(ROOT/'docs'/report_name).write_bytes((directory/report_name).read_bytes())
 print('PASS',variant,summary['independent_winding_samples'],'fresh winding samples',round(summary['elapsed_seconds'],2),'seconds',flush=True);return summary
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--variant',choices=OUTPUTS,required=True);parser.add_argument('--output-directory',type=Path,required=True);parser.add_argument('--install',action='store_true');args=parser.parse_args();generate(args.variant,args.output_directory,args.install)
# TIMESTAMP END 2026-11-05T17:01:40+00:00 | REVISION R000056
