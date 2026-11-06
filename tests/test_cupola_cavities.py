# TIMESTAMP START 2026-11-05T06:03:29+00:00 | REVISION R000025
"""Actual saved hub stock/occupancy, with missing-peg and moved-pocket adversaries."""
from pathlib import Path
import copy,json,sys,unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import export_top_entry_cavities as exporter
from audit_revised_joinery import native_solid,packed

class CupolaCavities(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model=json.loads((ROOT/'src/top-entry-proposed-model.json').read_text())
        cls.physical={p['id']:native_solid(p) for p in cls.model['parts'] if p.get('is_timber') or p.get('is_fastener')}

    def record(self,model=None):
        oldsolid,oldpacked=exporter.solid,exporter.packed
        exporter.solid=native_solid;exporter.packed=packed
        try:return exporter.hub_record(model or self.model,self.physical)
        finally:exporter.solid=oldsolid;exporter.packed=oldpacked

    def audit_record(self,record):
        oldsolid,oldentries=exporter.solid,exporter.entry_regions
        exporter.solid=native_solid
        # TIMESTAMP START 2026-11-05T15:30:01+00:00 | REVISION R000049
        exporter.entry_regions=lambda _,model=None:{pid:native_solid(value) for pid,value in self.model['joinery_entry_regions'].items()}
        # TIMESTAMP END 2026-11-05T15:30:01+00:00 | REVISION R000049
        try:return exporter.audit(self.model,{'parts':{'CUP-KINGPOST':record}},None)
        finally:exporter.solid=oldsolid;exporter.entry_regions=oldentries

    def test_actual_saved_hub_and_all_physical_mates(self):
        result=self.audit_record(self.record())
        self.assertEqual(result['failures'],['Cavity IDs do not match structural timber IDs'])
        row=result['members'][0]
        self.assertEqual(row['status'],'PASS',row)
        self.assertGreater(row['independent_winding_samples'],0)
        self.assertEqual(row['uncovered_winding_samples'],0)

    def test_missing_hub_peg_is_rejected(self):
        model=copy.deepcopy(self.model)
        peg=next(p for p in model['parts'] if p.get('peg_geometry',{}).get('receiver')=='CUP-KINGPOST')
        model['parts'].remove(peg)
        with self.assertRaisesRegex(AssertionError,'real transverse peg'):self.record(model)

    def test_shifted_pocket_is_rejected(self):
        record=self.record()
        record['mating_pocket']['vertices']=[[x+.5*.0254,y,z] for x,y,z in record['mating_pocket']['vertices']]
        row=self.audit_record(record)['members'][0]
        self.assertEqual(row['status'],'FAIL')
        self.assertGreater(row['errors_m3']['pocket_without_mate'],1e-6*.0254**3)

# TIMESTAMP START 2026-11-05T15:30:01+00:00 | REVISION R000049
class ExplicitAssemblyEntries(unittest.TestCase):
    def test_post_and_outer_rafter_entries_preserve_original_inner_entry(self):
        import manifold3d as m
        import numpy as np
        def record(shape):
            mesh=shape.to_mesh64();return {'vertices':np.asarray(mesh.vert_properties)[:,:3].tolist(),'triangles':np.asarray(mesh.tri_verts).tolist()}
        cutter=m.Manifold.cube([2,2,2]);nose=m.Manifold.cube([1,2,2]);extra=m.Manifold.cube([1,1,1]).translate([3,0,0]);post=m.Manifold.cube([1,2,3]).translate([5,0,0])
        proposal={'representative':{'interfaces':[{'top_open_cutter':record(cutter),'proposed_nose':record(nose)}]}}
        model={'joinery_entry_regions':{'R0':record(extra),'C0':record(post)}};before=copy.deepcopy((proposal,model));regions=exporter.entry_regions(proposal,model)
        expected=(cutter-nose)+extra
        self.assertLess(abs(regions['R0'].volume()-5),1e-12);self.assertLess((regions['R0']-expected).volume()+(expected-regions['R0']).volume(),exporter.TOL)
        self.assertLess((regions['C0']-post).volume()+(post-regions['C0']).volume(),exporter.TOL);self.assertEqual((proposal,model),before)
        self.assertNotIn('C0',exporter.entry_regions(proposal),'Source-declared post entry must never be silently omitted')
        shared={'three_inch_joinery_revision':'fixture','joinery_entry_regions':{'P0':record(post),'R0':record(extra)}}
        region=exporter.entry_regions(proposal,shared)['R0'];shared_expected=expected+post
        self.assertLess((region-shared_expected).volume()+(shared_expected-region).volume(),exporter.TOL)
        other=exporter.entry_regions(proposal,shared)['R1'];original=exporter.entry_regions(proposal)['R1']
        self.assertLess((other-original).volume()+(original-other).volume(),exporter.TOL,'Another post slot must not become arbitrary clearance in every hip')
# TIMESTAMP END 2026-11-05T15:30:01+00:00 | REVISION R000049
if __name__=='__main__':unittest.main()
# TIMESTAMP END 2026-11-05T06:03:29+00:00 | REVISION R000025
