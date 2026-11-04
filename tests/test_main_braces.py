# TIMESTAMP START 2026-11-02T15:15:55-05:00 | REVISION R004802
"""Verify actual stock, three-way brace nodes and exact complementary sockets."""
from pathlib import Path
import hashlib,itertools,json,sys
import numpy as np
import manifold3d as m
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from step_lap import solid,contacts,close_bounds
from audit_cavity_fit import reference_stock,inspect_mesh
# TIMESTAMP START 2026-11-02T17:32:31-05:00 | REVISION R004820
import manifold3d as m
from revise_main_braces import I
# TIMESTAMP END 2026-11-02T17:32:31-05:00 | REVISION R004820

models=[json.loads((R/'src'/name).read_text()) for name in
        ['model-data.json','step-lap-proposed-model.json','top-entry-proposed-model.json']]
expected={f'K{k}-{side}' for k in range(8) for side in ['A','B','C']}
base_parts={p['id']:p for p in models[0]['parts']}
for model in models:
    parts={p['id']:p for p in model['parts']};timbers={k:solid(p) for k,p in parts.items() if p['is_timber']}
    # TIMESTAMP START 2026-11-02T17:32:31-05:00 | REVISION R004820
    assert len(parts)==(179 if model.get('cupola_foot_revision') else 171) and len(timbers)==112
    pegs={k:solid(p) for k,p in parts.items() if p.get('group')=='joinery_pegs'}
    assert len(pegs)==(56 if model.get('cupola_foot_revision') else 48)
    # TIMESTAMP END 2026-11-02T17:32:31-05:00 | REVISION R004820
    assert {k for k,p in parts.items() if p['group']=='braces'}==expected
    assert model['main_brace_revision']['actual_section_in']==[2,6]
    for k in range(8):
        for side in ['A','B','C']:
            name=f'K{k}-{side}';p=parts[name];s=timbers[name]
            assert p==base_parts[name],(name,'model variants must share the same braces')
            assert p['dimensions']['width_in']==2 and p['dimensions']['depth_in']==6
            # TIMESTAMP START 2026-11-02T17:32:31-05:00 | REVISION R004820
            assert p['main_face_brace_joinery']['peg_ids']
            assert p['declared_exterior_cut']['volume_m3']>0
            raw_v,raw_f=reference_stock(p);raw=m.Manifold(m.Mesh64(raw_v,raw_f))
            exterior=solid(p['declared_exterior_cut']);pre_bore=raw-exterior
            bore_union=m.Manifold.batch_boolean([peg for peg in pegs.values() if close_bounds(peg,s)],m.OpType.Add)^pre_bore
            # Compare the disjoint material partition directly. Re-unioning
            # exactly touching bore walls creates zero-thickness membranes in
            # some rotated bays, which are not additional physical material.
            assert abs(pre_bore.volume()-s.volume()-bore_union.volume())/I**3<1e-6,(name,'matching bore/peg volume mismatch')
            assert abs((s^bore_union).volume())/I**3<1e-6,(name,'bore overlaps retained wood')
            assert abs((s-raw).volume())/I**3<1e-6,(name,'brace outside declared stock')
            assert abs((exterior^s).volume())/I**3<1e-6,(name,'exterior cut crosses wood')
            # TIMESTAMP END 2026-11-02T17:32:31-05:00 | REVISION R004820
            # TIMESTAMP START 2026-11-03T17:00:04-05:00 | REVISION R005063
            expected_length=np.hypot(24,35) if side=='C' else np.sqrt(2)*(89.03615129287599-62)
            assert abs(np.linalg.norm(np.asarray(p['axis_end'])-p['axis_start'])/I-expected_length)<1e-8
            # TIMESTAMP END 2026-11-03T17:00:04-05:00 | REVISION R005063
            assert np.linalg.norm(p['exploded_offset'])>1 and len(s.decompose())==1
            # Independently measure a true section through the body, rather than
            # merely trusting the section labels or an axis-aligned bounding box.
            frame=p['stock_frame'];rotation=np.array([frame['width'],-np.array(frame['depth']),frame['axis']])
            center=np.array(p['center']);tf=np.column_stack([rotation,-rotation@center])
            section=s.transform(tf.tolist()).scale((1e6,1e6,1e6)).slice(0)
            assert abs(section.area()/1e12/I**2-12)<1e-7,(name,'not a full 2 × 6 section')
            points=np.vstack(section.to_polygons())/1e6;assert np.allclose(np.ptp(points,axis=0)/I,[2,6],atol=1e-8)
            receivers=[f'P{k}', f'T{k}' if side=='C' else f'B{(k-1)%8 if side=="A" else k}']
            for receiver in receivers:
                assert s.min_gap(timbers[receiver],.01)<1e-8,(name,receiver,'gap')
                assert abs((s^timbers[receiver]).volume())/I**3<1e-6,(name,receiver,'overlap')
                assert sum(f['area_in2'] for f in contacts(s,timbers[receiver]))>2,(name,receiver,'missing bearing')
            if side=='C':
                assert abs(max(v[1] for v in p['vertices'])/I-88)<1e-8
                assert abs(min(v[1] for v in parts[f'T{k}']['vertices'])/I-85)<1e-8
                assert len({tuple(parts[f'K{k}-{side}']['exploded_offset']) for side in ['A','B','C']})==3
    for a,b in itertools.combinations(timbers,2):
        if a not in expected and b not in expected:continue
        if close_bounds(timbers[a],timbers[b]):
            assert abs((timbers[a]^timbers[b]).volume())/I**3<1e-6,(a,b,'brace collides with another timber')
for filename,auditname in [('cavity-data.json','cavity-fit-audit.json'),('step-lap-proposed-cavities.json','step-lap-proposed-cavity-fit-audit.json')]:
    cavity=json.loads((R/'src'/filename).read_text());audit=json.loads((R/'docs'/auditname).read_text())
    assert audit['status']=='PASS' and audit['summary']['all_timber_stock_envelopes_verified']==112
    assert all(cavity['parts'][f'T{k}']['removed']['triangles'] for k in range(8))
    # TIMESTAMP START 2026-11-02T17:32:31-05:00 | REVISION R004820
    assert all(cavity['parts'][name]['removed']['triangles'] for name in expected)
    assert audit['summary']['permanent_wood_fasteners']==48
# Legacy brace stock reconstruction is superseded by explicit face-entry stock,
# exterior shoulders and separate peg bores, independently checked above.
# TIMESTAMP END 2026-11-02T17:32:31-05:00 | REVISION R004820
print('PASS: all three model variants have 24 actual 2 × 6 braces; each post has two ring braces and an inward tie brace; complementary sockets, full body sections, unique explode offsets and existing independent cavity proofs verified. Capacity and raising sequence are not approved.')
# TIMESTAMP END 2026-11-02T15:15:55-05:00 | REVISION R004802
