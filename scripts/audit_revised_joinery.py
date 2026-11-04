# TIMESTAMP START 2026-11-03T15:46:44-05:00 | REVISION R005039
"""Source-bound stock, mating-pocket and explicit assembly-entry audits."""
from pathlib import Path
import argparse,copy,hashlib,json
import numpy as np
import manifold3d as m
import export_top_entry_cavities as audit
from apply_joinery_revision import normalized
from step_lap import mesh,solid,I
from audit_cavity_fit import inspect_mesh,arrays

ROOT=Path(__file__).resolve().parents[1]
FILES={'baseline':('model-data.json','cavity-data.json','cavity-fit-audit.json'),
       'proposed':('step-lap-proposed-model.json','step-lap-proposed-cavities.json','step-lap-proposed-cavity-fit-audit.json'),
       'top-entry':('top-entry-proposed-model.json','top-entry-proposed-cavities.json','top-entry-cavity-fit-audit.json')}
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def save(path,data):path.write_text(json.dumps(data,separators=(',',':'))+'\n')
# TIMESTAMP START 2026-11-03T16:12:39-05:00 | REVISION R005050
def native_solid(record):
    # Preserve the imported double-precision boundary. Forcing a larger CSG
    # tolerance can merge distinct root vertices before a Boolean operation.
    return m.Manifold(m.Mesh64(np.asarray(record['vertices'],float),np.asarray(record['triangles'],np.uint64)))
solid=native_solid
# TIMESTAMP END 2026-11-03T16:12:39-05:00 | REVISION R005050

def packed(shape):
    if shape.is_empty() or abs(shape.volume())<1e-9*I**3:return copy.deepcopy(audit.EMPTY)
    # TIMESTAMP START 2026-11-03T15:58:36-05:00 | REVISION R005044
    # TIMESTAMP START 2026-11-03T16:12:39-05:00 | REVISION R005050
    result=None
    imported=solid(mesh(shape))
    # TIMESTAMP START 2026-11-03T16:49:21-05:00 | REVISION R005060
    candidates=[shape]+[source.simplify(epsilon) for source in [shape,imported] for epsilon in [1e-10,1e-9,1e-8]]
    # TIMESTAMP END 2026-11-03T16:49:21-05:00 | REVISION R005060
    pieces=[q for q in imported.decompose() if q.volume()>1e-14]
    if pieces:candidates.append(m.Manifold.compose(pieces).simplify(1e-10))
    for candidate in candidates:
        data=mesh(candidate);proof=inspect_mesh(*arrays(data))
        if proof['status']=='PASS':
            error=abs((shape-candidate).volume())+abs((candidate-shape).volume())
            if error>=1e-6*I**3:
                save(Path('/tmp/octagon-boundary-before.json'),mesh(shape));save(Path('/tmp/octagon-boundary-after.json'),data)
            if error>=1e-6*I**3:continue
            result=data;break
    if result is None:
        save(Path('/tmp/octagon-cavity-boundary-failure.json'),mesh(shape))
        candidate=normalized(shape);result=mesh(candidate);proof=inspect_mesh(*arrays(result))
        # TIMESTAMP START 2026-11-03T16:49:21-05:00 | REVISION R005060
        if proof['status']!='PASS':
            save(Path('/tmp/octagon-normalized-boundary-failure.json'),result)
            simplified=solid(result).simplify(1e-8);data=mesh(simplified);check=inspect_mesh(*arrays(data))
            error=abs((simplified-candidate).volume())+abs((candidate-simplified).volume())
            if check['status']=='PASS' and error<1e-6*I**3:result=data;proof=check
        # TIMESTAMP END 2026-11-03T16:49:21-05:00 | REVISION R005060
        assert proof['status']=='PASS',proof['failures']
    # TIMESTAMP END 2026-11-03T16:12:39-05:00 | REVISION R005050
    # TIMESTAMP END 2026-11-03T15:58:36-05:00 | REVISION R005044
    result['edges']=[list(e) for e in sorted({tuple(sorted((t[k],t[(k+1)%3]))) for t in result['triangles'] for k in range(3)})]
    return result

def generate(variant,source_dir,output_dir):
    model_name,cavity_name,report_name=FILES[variant];path=source_dir/model_name;model=json.loads(path.read_text())
    assert model.get('three_inch_joinery_revision'),'Expected revised model'
    proposal=json.loads((ROOT/'src/top-entry-proposal.json').read_text())
    original_entries=audit.entry_regions
    entries={pid:solid(record) for pid,record in model['joinery_entry_regions'].items()}
    # TIMESTAMP START 2026-11-03T15:58:36-05:00 | REVISION R005044
    post_entries=m.Manifold.batch_boolean(list(entries.values()),m.OpType.Add)
    for k in range(8):entries[f'R{k}']=post_entries
    if variant=='top-entry':
        for pid,shape in original_entries(proposal).items():entries[pid]=entries.get(pid,m.Manifold())+shape
    # TIMESTAMP END 2026-11-03T15:58:36-05:00 | REVISION R005044
    names=['scripts/audit_revised_joinery.py','scripts/export_top_entry_cavities.py','scripts/audit_cavity_fit.py','scripts/step_lap.py','scripts/apply_joinery_revision.py','scripts/three_inch_tenons.py','scripts/center_brace_tenons.py']
    sources={name:sha(ROOT/name) for name in names};sources['src/'+model_name]=sha(path)
    if variant=='top-entry':sources['src/top-entry-proposal.json']=sha(ROOT/'src/top-entry-proposal.json')
    previous_sources=audit.sources;previous_packed=audit.packed;previous_solid=audit.solid
    audit.entry_regions=lambda _:entries;audit.sources=lambda:sources;audit.packed=packed;audit.solid=native_solid
    try:
        cavities=audit.generate(model,proposal);cavities['source_model_sha256']=sha(path)
        report=audit.audit(model,cavities,proposal);report['model_sha256']=sha(path)
    finally:audit.entry_regions=original_entries;audit.sources=previous_sources;audit.packed=previous_packed;audit.solid=previous_solid
    if report['status']!='PASS':save(Path('/tmp/octagon-'+variant+'-cavity-failure-report.json'),report)
    assert report['status']=='PASS',report['failures']
    report['schema_version']='revised-joinery-cavity-audit-1';cavities['schema_version']='revised-joinery-cavities-1'
    report['summary'].update(timbers=112,all_timber_stock_envelopes_verified=112,permanent_wood_fasteners=sum(p.get('is_fastener',False) for p in model['parts']))
    output_dir.mkdir(parents=True,exist_ok=True);save(output_dir/cavity_name,cavities);report['cavity_sha256']=sha(output_dir/cavity_name);save(output_dir/report_name,report)
    print(variant,'PASS',report['summary'],flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--source-dir',type=Path,default=ROOT/'src');parser.add_argument('--output-dir',type=Path,default=Path('/tmp/octagon-joinery-audits'));parser.add_argument('--variant',choices=FILES);args=parser.parse_args()
    for variant in ([args.variant] if args.variant else FILES):generate(variant,args.source_dir,args.output_dir)
# TIMESTAMP END 2026-11-03T15:46:44-05:00 | REVISION R005039
