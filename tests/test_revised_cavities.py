# TIMESTAMP START 2026-11-03T17:08:46-05:00 | REVISION R005066
"""Independent current-mesh cavity verification and source provenance gates."""
from pathlib import Path
import copy,hashlib,json,sys,unittest
import manifold3d as m
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import export_top_entry_cavities as exporter
from audit_revised_joinery import FILES,native_solid

def read(path):return json.loads(path.read_text())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def verify_saved(variant):
    model,cavities,report=FILES[variant]
    saved=read(ROOT/'docs'/report);data=read(ROOT/'src'/cavities)
    assert saved['status']=='PASS' and not saved['failures']
    assert saved['model_sha256']==sha(ROOT/'src'/model)==data['source_model_sha256']
    assert saved['cavity_sha256']==sha(ROOT/'src'/cavities)
    assert data['sources']==saved['sources']
    for name,digest in saved['sources'].items():assert sha(ROOT/name)==digest,name
    return saved

def audit_current(variant,cavities=None,only=None):
    model_name,cavity_name,_=FILES[variant]
    model=read(ROOT/'src'/model_name)
    data=copy.deepcopy(cavities) if cavities is not None else read(ROOT/'src'/cavity_name)
    proposal=read(ROOT/'src/top-entry-proposal.json')
    previous_entries=exporter.entry_regions;previous_solid=exporter.solid
    entries={pid:native_solid(shape) for pid,shape in model['joinery_entry_regions'].items()}
    post_entries=exporter.union(list(entries.values()))
    for k in range(8):entries[f'R{k}']=post_entries
    if variant=='top-entry':
        for pid,shape in previous_entries(proposal).items():entries[pid]=entries.get(pid,m.Manifold())+shape
    # Keep every physical mate while optionally checking only one receiver's
    # exported records in a deliberate bad-fit fixture.
    if only is not None:
        model=copy.deepcopy(model)
        for p in model['parts']:
            if p.get('is_timber') and p['id'] not in only:p['is_timber']=False;p['group']='joinery_pegs'
        data['parts']={pid:data['parts'][pid] for pid in only}
    exporter.solid=native_solid;exporter.entry_regions=lambda _:entries
    try:return exporter.audit(model,data,proposal)
    finally:exporter.solid=previous_solid;exporter.entry_regions=previous_entries

class RevisedCavities(unittest.TestCase):
    def test_all_three_variants_reconstruct_stock_and_fill_actual_pockets(self):
        for variant in FILES:
            with self.subTest(variant=variant):
                saved=verify_saved(variant);actual=audit_current(variant)
                self.assertEqual(actual['status'],'PASS',actual['failures'])
                self.assertEqual(actual['summary']['verified_records'],112)
                self.assertEqual(actual['summary']['uncovered_winding_samples'],0)
                for key,value in actual['summary'].items():self.assertEqual(value,saved['summary'][key],key)
                self.assertTrue(all(row['status']=='PASS' for row in actual['members']))

if __name__=='__main__':unittest.main()
# TIMESTAMP END 2026-11-03T17:08:46-05:00 | REVISION R005066
