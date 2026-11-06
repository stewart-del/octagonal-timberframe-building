# TIMESTAMP START 2026-11-05T14:48:08+00:00 | REVISION R000048
"""Merge source-bound cupola access cuts, then audit actual output before install.

The frozen input retains the independent stock, ownership receipts and exact
original model. Newer source actors never get overwritten by an old snapshot.
"""
from pathlib import Path
import argparse,copy,gzip,hashlib,json,shutil,subprocess
import numpy as np
import manifold3d as m
from audit_revised_joinery import native_solid
from audit_cavity_fit import inspect_mesh
from plan_architectural_disassembly import scene_from_payload,audit_initial_scene,check_stage,apply_stage,VOLUME_TOLERANCE_M3
ROOT=Path(__file__).resolve().parents[1]
FIXTURE=ROOT/'scripts/fixtures/cupola-access-inputs.json.gz'
STAMP='2026-11-05T14:48:08+00:00'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def fingerprint(part):return sha(json.dumps(part,sort_keys=True,separators=(',',':')).encode())
def load_inputs():
 raw=FIXTURE.read_bytes();payload=json.loads(gzip.decompress(raw));assert payload['schema']=='source-bound-cupola-access-inputs-1'
 for record in payload['variants'].values():
  assert sha(record['sourceModelText'].encode())==record['sourceSha256']
  for item in record['files'].values():assert sha(item['content'].encode())==item['sha256']
 route=payload['routeProposal'];assert sha(route['content'].encode())==route['sha256']
 return payload,sha(raw)
def merge(raw,record,fixture_hash):
 assert sha(raw)==record['sourceSha256'],'Refusing to overwrite newer source: cupola input hash changed'
 model=json.loads(raw);patch=json.loads(record['files']['patch.json']['content']);assert patch['source_model_sha256']==sha(raw)
 parts={p['id']:p for p in model['parts']};replacements=patch['replace_parts'];assert len(parts)==len(model['parts']) and len(replacements)==49
 for pid,value in patch['source_part_fingerprints'].items():assert fingerprint(parts[pid])==value,('Cupola source actor changed',pid)
 assert set(parts)==set(patch['unchanged_part_ids'])|set(replacements)
 joints={j['id']:j for j in model['tenon_schedule']};assert set(patch['replace_joints'])<=set(joints)
 result=copy.deepcopy(model);result['parts']=[replacements.get(p['id'],p) for p in model['parts']]
 result['tenon_schedule']=[patch['replace_joints'].get(j['id'],j) for j in model['tenon_schedule']]
 result['cupola_access']={'revision':'R000048','timestamp':STAMP,'source_model_sha256':sha(raw),'fixture_sha256':fixture_hash,'changed_actor_ids':sorted(replacements),'changed_joint_ids':sorted(patch['replace_joints']),'scope':'Source-bound accessible pegged joints and stopped roof backing. Geometric core fit and route only; architecture and capacities require their separate checks.'}
 for pid in patch['unchanged_part_ids']:assert next(p for p in result['parts'] if p['id']==pid)==parts[pid]
 return result

def solid(record):return native_solid(record) if record.get('triangles') else m.Manifold()
def difference(a,b):return max(0.,float((a-b).volume()))+max(0.,float((b-a).volume()))
def verify(model,record,route):
 patch=json.loads(record['files']['patch.json']['content']);stock=json.loads(record['files']['stock-envelopes.json']['content']);old=json.loads(record['sourceModelText']);old_parts={p['id']:p for p in old['parts']};parts={p['id']:p for p in model['parts']}
 strict=[];stock_results=[];lower=[]
 for pid in patch['replace_parts']:
  p=parts[pid];status=inspect_mesh(np.asarray(p['vertices']),np.asarray(p['triangles'],np.uint64),require_single=True)
  assert status['status']=='PASS',(pid,status);strict.append(pid)
 for pid,item in stock['parts'].items():
  occupied=solid(parts[pid]);blank=solid(item['blank']);working=solid(item['working_envelope_before_pockets']);cut=solid(item['declared_exterior_cut_union'])
  outside=max(0.,float((occupied-blank).volume()));declared=difference(blank-cut,working)
  assert outside<=VOLUME_TOLERANCE_M3 and declared<=VOLUME_TOLERANCE_M3,(pid,'Stock/offcut mismatch',outside,declared)
  assert max(0.,float((occupied-working).volume()))<=VOLUME_TOLERANCE_M3,pid
  stock_results.append({'id':pid,'occupied_outside_blank_m3':outside,'declared_offcut_residual_m3':declared})
 for k in range(8):
  pid='C'+str(k);level=153.601601597*.0254
  residual=difference(solid(old_parts[pid]).trim_by_plane([0,-1,0],-level),solid(parts[pid]).trim_by_plane([0,-1,0],-level))
  assert residual<=VOLUME_TOLERANCE_M3,(pid,'Protected lower cupola connection changed',residual)
  lower.append({'id':pid,'fixed_lower_difference_m3':residual})
 code="const fs=require('fs'),r=require('./src/display-presets.js'),d=JSON.parse(fs.readFileSync(0,'utf8'));process.stdout.write(JSON.stringify(d.parts.filter(p=>r.included(p,'complete')).map(p=>p.id)));"
 ids=set(json.loads(subprocess.check_output(['node','-e',code],input=json.dumps(model).encode(),cwd=ROOT)))
 scene=scene_from_payload('cupola-core',{'parts':[p for p in model['parts'] if p['id'] in ids]});initial=audit_initial_scene(scene);assert initial['status']=='PASS',initial['collisions'][:4]
 for proposal in route['stages']:
  assert len(proposal['member_ids'])==1,'Cupola members must retain individual releases'
  proof=check_stage(scene,proposal['member_ids'],proposal['delta_m'],stop_first=True);assert proof['status']=='PASS',(proposal['label'],proof['collisions'])
  apply_stage(scene,proposal['member_ids'],proposal['delta_m'],proof,proposal['label'])
 assert len(scene.stages)==75
 return {'status':'PASS','scope':'49 changed actor boundaries,25 independent timber blanks/offcuts,8 protected lower cupola interfaces,complete primary core static fit and75 individual cupola release stages with all parked core actors retained. This is not a full-building route or capacity certificate.','overlap_tolerance_m3':VOLUME_TOLERANCE_M3,'strict_raw_actor_ids':strict,'stock':stock_results,'protected_lower_C':lower,'initial_core':initial,'cupola_release_stages':scene.stages}

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--output-directory',required=True,type=Path);parser.add_argument('--install',action='store_true');args=parser.parse_args()
 payload,fixture_hash=load_inputs();route=json.loads(payload['routeProposal']['content']);args.output_directory.mkdir(parents=True,exist_ok=True);reports={};candidates={}
 for variant,record in payload['variants'].items():
  path=ROOT/'src'/record['sourceName'];raw=path.read_bytes();model=merge(raw,record,fixture_hash);print('Audit cupola access',variant,flush=True)
  report=verify(model,record,route);output=args.output_directory/record['sourceName'];output.write_text(json.dumps(model,separators=(',',':'))+'\n');candidates[variant]=(path,output,sha(raw))
  report.update(source_model_sha256=sha(raw),output_model_sha256=sha(output.read_bytes()),fixture_sha256=fixture_hash,generator_sha256=sha(Path(__file__).read_bytes()));reports[variant]=report
  print('PASS',variant,len(report['strict_raw_actor_ids']),'raw actors;',len(report['cupola_release_stages']),'continuous core stages',flush=True)
 result={'status':'PASS','variants':reports,'scope':'Cupola core checks only; full-building architectural proofs remain required.'};(args.output_directory/'cupola-access-audit.json').write_text(json.dumps(result,indent=2)+'\n')
 if args.install:
  for path,output,old_hash in candidates.values():assert sha(path.read_bytes())==old_hash,'Source changed during audit; nothing installed'
  for path,output,old_hash in candidates.values():shutil.copyfile(output,path)
  shutil.copyfile(args.output_directory/'cupola-access-audit.json',ROOT/'docs/cupola-access-audit.json')
  print('Installed all three verified cupola sources',flush=True)
if __name__=='__main__':main()
# TIMESTAMP END 2026-11-05T14:48:08+00:00 | REVISION R000048
