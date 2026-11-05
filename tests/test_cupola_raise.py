# TIMESTAMP START 2026-11-05T06:23:51+00:00 | REVISION R000028
"""Window clearance revisions must preserve actual lower timber connections."""
from pathlib import Path
import gzip,json,re,sys,unittest
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from audit_revised_joinery import native_solid
from export_top_entry_cavities import union
I=.0254;TOL=1e-6*I**3

class CupolaRaise(unittest.TestCase):
    def test_raised_stock_and_unchanged_lower_connections_in_every_variant(self):
        frozen=json.loads(gzip.decompress((ROOT/'scripts/fixtures/cupola-inputs.json.gz').read_bytes()))
        for name,record in frozen['files'].items():
            with self.subTest(model=name):
                before=json.loads(record['content']);model=json.loads((ROOT/'src'/name).read_text())
                self.assertEqual(model['upper_cupola_raise']['rise_in'],10)
                old={p['id']:p for p in before['parts']};parts={p['id']:p for p in model['parts']}
                screws=[p for p in model['parts'] if p['id'].startswith('M-TMP-SCREW-')]
                self.assertEqual(len(screws),40)
                self.assertEqual(len(parts['M-TMP']['display_holes']),40)
                self.assertEqual(parts['M-TMP']['reference_dimensions']['overall_span_in'],94)
                for k in range(8):
                    c=parts[f'C{k}'];self.assertEqual([c['dimensions']['width_in'],c['dimensions']['depth_in']],[6,6])
                    self.assertAlmostEqual(c['axis_end'][1]-old[f'C{k}']['axis_end'][1],10*I,12)
                    for pid in [f'C{k}',f'T{k}']:
                        tools=[native_solid(p) for p in screws if p.get('screw_geometry',{}).get('receiver')==pid]
                        reference=(native_solid(old[pid])-union(tools)).trim_by_plane([0,-1,0],-110*I)
                        actual=native_solid(parts[pid]).trim_by_plane([0,-1,0],-110*I)
                        self.assertLessEqual(abs((actual-reference).volume())+abs((reference-actual).volume()),TOL,pid)
                    self.assertNotIn(f'L{k}-S',model['joinery_entry_regions'])
                    for prefix in ['CC','CR']:
                        pid=prefix+str(k)
                        self.assertAlmostEqual(parts[pid]['axis_end'][1]-old[pid]['axis_end'][1],10*I,12)
                    hip=next(j for j in model['tenon_schedule'] if j['donor']==f'R{k}' and j['receiver']==f'C{k}')
                    prior=next(j for j in before['tenon_schedule'] if j['id']==hip['id'])
                    self.assertEqual(hip,prior,'R-to-C connection must remain at its actual original elevation')
                self.assertEqual(sum(p['id'].startswith('CUP-PEG-') for p in model['parts']),64)

if __name__=='__main__':unittest.main()
# TIMESTAMP END 2026-11-05T06:23:51+00:00 | REVISION R000028
