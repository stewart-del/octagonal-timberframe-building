# TIMESTAMP START 2026-11-05T08:52:17+00:00 | REVISION R000038
"""Portable stopped-backing offcuts; preserve separate actual source wedges.

No model/auditor mutations. Input and output units are meters. The inspector
and native mesh importer are injected from the unchanged production tools.
"""
from __future__ import annotations
import numpy as np
import manifold3d as m

INCH = .0254
VOLUME_TOLERANCE_M3 = 1e-6 * INCH ** 3

def occupied_difference(a, b):
    return max(0., float((a-b).volume())) + max(0., float((b-a).volume()))

def _raw_record(shape):
    mesh=shape.to_mesh64()
    vertices=np.asarray(mesh.vert_properties)[:,:3]
    faces=np.asarray(mesh.tri_verts,dtype=np.uint64)
    return {'vertices':vertices.tolist(),'triangles':faces.tolist(),
            'volume_m3':float(shape.volume()),
            'edges':[list(e) for e in sorted({tuple(sorted((int(t[i]),int(t[(i+1)%3])))) for t in faces for i in range(3)})]}

def concatenate_closed_records(records):
    """Keep independent closed components; do not cofacially Boolean-union."""
    vertices=[];triangles=[]
    for p in records:
        base=len(vertices);vertices.extend(p['vertices'])
        triangles.extend([[base+i for i in t] for t in p['triangles']])
    return {'vertices':vertices,'triangles':triangles,
            'edges':[list(e) for e in sorted({tuple(sorted((int(t[i]),int(t[(i+1)%3])))) for t in triangles for i in range(3)})],
            'volume_m3':sum(p['volume_m3'] for p in records)}

def closed_stopped_backing_offcuts(source, top_normals, top_constant_m,
                                   radial, stop_m, inspect_mesh, native_solid,
                                   removed_reference=None,
                                   tolerance_m3=VOLUME_TOLERANCE_M3):
    """Return real closed offcuts and receipts, refusing unverified repair.

    Each plane clips the ACTUAL source R, rather than a blank envelope.
    The separately closed wedges meet only at a zero-area ridge. A convex
    hull is accepted only if its occupied symmetric difference from the
    actual clipped source is within the unchanged tolerance. Nonconvex
    pieces retain their actual boundary or fail explicitly.
    """
    radial=np.asarray(radial,float);radial/=np.linalg.norm(radial)
    pieces=[];checks=[];actual_wedges=[]
    for plane_index, normal in enumerate(top_normals):
        normal=np.asarray(normal,float);length=np.linalg.norm(normal)
        actual=source.trim_by_plane((normal/length).tolist(),float(top_constant_m)/length)
        actual=actual.trim_by_plane(radial.tolist(),float(stop_m))
        actual_wedges.append(actual)
        components=actual.decompose()
        for component_index, component in enumerate(components):
            if component.is_empty():continue
            # Retain every measurable positive component. A true null CSG
            # membrane is accepted as omitted only by the final aggregate
            # unchanged occupied-difference check, never by a larger cutoff.
            if component.volume()<=0:continue
            hull=m.Manifold.hull_points(np.asarray(component.to_mesh64().vert_properties)[:,:3])
            candidates=[('occupied-equivalent convex boundary',hull),
                        ('actual clipped source boundary',component)]
            candidates.extend(('actual boundary simplification',component.simplify(e)) for e in [1e-10,1e-9,1e-8])
            accepted=None
            for method,candidate in candidates:
                delta=occupied_difference(component,candidate)
                if delta>tolerance_m3:continue
                record=_raw_record(candidate)
                audit=inspect_mesh(np.array(record['vertices']),np.array(record['triangles'],dtype=np.uint64),require_single=True)
                if audit['status']!='PASS':continue
                readback=native_solid(record)
                if str(readback.status())!='Error.NoError':continue
                error=occupied_difference(component,readback)
                if error>tolerance_m3:continue
                if record['volume_m3']<=0:continue
                accepted=(record,readback,method,audit,error);break
            if accepted is None:
                raise AssertionError(('No verified closed actual backing offcut',plane_index,component_index,float(component.volume())/INCH**3))
            record,readback,method,audit,error=accepted
            record['offcut_provenance']={'plane_index':plane_index,'component_index':component_index,'method':method,
                'scope':'Actual source material above one backing plane and outboard stop; not the independent stock cutting envelope.'}
            pieces.append(record);checks.append({'plane_index':plane_index,'component_index':component_index,
                'method':method,'volume_in3':readback.volume()/INCH**3,
                'actual_source_wedge_difference_in3':error/INCH**3,'raw_mesh_audit':audit})
    assert pieces,'No positive backing material was removed'
    combined=concatenate_closed_records(pieces)
    combined_audit=inspect_mesh(np.array(combined['vertices']),np.array(combined['triangles'],dtype=np.uint64),require_single=False)
    assert combined_audit['status']=='PASS',combined_audit
    combined_solid=native_solid(combined)
    assert str(combined_solid.status())=='Error.NoError'
    actual_union=m.Manifold.batch_boolean(actual_wedges,m.OpType.Add)
    aggregate_error=occupied_difference(actual_union,combined_solid)
    assert aggregate_error<=tolerance_m3,('Actual wedge reconstruction mismatch',aggregate_error/INCH**3)
    reference_error=None
    if removed_reference is not None:
        reference_error=occupied_difference(removed_reference,combined_solid)
        assert reference_error<=tolerance_m3,('Removed material differs',reference_error/INCH**3)
    source_outside=max(0.,float((combined_solid-source).volume()))
    assert source_outside<=tolerance_m3,('Offcut outside actual source',source_outside/INCH**3)
    overlaps=[]
    for i in range(len(pieces)):
        for j in range(i):
            amount=max(0.,float((native_solid(pieces[i])^native_solid(pieces[j])).volume()))
            assert amount<=tolerance_m3,('Offcut pieces overlap',i,j,amount/INCH**3)
            overlaps.append({'pieces':[j,i],'intersection_in3':amount/INCH**3})
    return {'pieces':pieces,'combined_closed_record':combined,
            'receipt':{'status':'PASS','piece_count':len(pieces),'tolerance_in3':tolerance_m3/INCH**3,
                'piece_checks':checks,'combined_raw_mesh_audit':combined_audit,
                'aggregate_actual_wedge_difference_in3':aggregate_error/INCH**3,
                'removed_reference_difference_in3':None if reference_error is None else reference_error/INCH**3,
                'outside_actual_source_in3':source_outside/INCH**3,'piece_intersections':overlaps}}

# TIMESTAMP END 2026-11-05T08:52:17+00:00 | REVISION R000038
