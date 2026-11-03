# TIMESTAMP START 2026-11-02T19:03:42-05:00 | REVISION R004847
"""Measure actual brace cross sections using mesh feature edges, not stock labels."""
from pathlib import Path
import argparse,hashlib,json
import numpy as np
from step_lap import solid

ROOT=Path(__file__).resolve().parents[1]
INCH=.0254

def measure(part):
    vertices=np.array(part['vertices']);faces=np.array(part['triangles']);tri=vertices[faces]
    normals=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);normals/=np.linalg.norm(normals,axis=1)[:,None]
    edges={}
    for index,face in enumerate(faces):
        for a,b in zip(face,np.roll(face,-1)):edges.setdefault(tuple(sorted([int(a),int(b)])),[]).append(index)
    features=[(np.linalg.norm(vertices[b]-vertices[a]),a,b) for (a,b),adjacent in edges.items()
              if len(adjacent)==2 and abs(normals[adjacent[0]]@normals[adjacent[1]])<.99999]
# TIMESTAMP START 2026-11-02T20:47:22-05:00 | REVISION R004872
    longest=max(row[0] for row in features)
    # Equal parallel edges need a geometric tie-break independent of BLAS last bits.
    candidates=[row for row in features if abs(row[0]-longest)<1e-9]
    length,a,b=min(candidates,key=lambda row:tuple(np.round(np.sort(vertices[[row[1],row[2]]],axis=0).ravel(),9)))
    axis=(vertices[b]-vertices[a])/length
# TIMESTAMP END 2026-11-02T20:47:22-05:00 | REVISION R004872
    if axis[1]<0:axis=-axis
    origin=(vertices[a]+vertices[b])/2;u=np.cross(axis,[0,1,0]);u/=np.linalg.norm(u);v=np.cross(axis,u)
    rotation=np.array([u,v,axis]);transform=np.column_stack([rotation,-rotation@origin])
    section=solid(part).transform(transform.tolist()).scale((1e6,1e6,1e6)).slice(0)
    polygons=section.to_polygons();assert len(polygons)==1,part['id']
    polygon=np.asarray(polygons[0])/1e6;boxes=[]
    for edge in np.diff(np.vstack([polygon,polygon[0]]),axis=0):
        if np.linalg.norm(edge)<1e-9:continue
        x=edge/np.linalg.norm(edge);y=np.array([-x[1],x[0]])
        q=polygon@np.array([x,y]).T/INCH;dimensions=np.ptp(q,axis=0)
        boxes.append((float(np.prod(dimensions)),q,dimensions))
    _,outline,dimensions=min(boxes,key=lambda item:item[0])
    if dimensions[0]>dimensions[1]:outline=outline[:,[1,0]];dimensions=dimensions[::-1]
# TIMESTAMP START 2026-11-02T20:47:22-05:00 | REVISION R004872
    outline-=outline.min(0);area=section.area()/1e12/INCH**2
    outline=np.round(outline,8)
    outline=outline[np.argsort(np.arctan2(outline[:,1]-3,outline[:,0]-1))]
    start=min(range(len(outline)),key=lambda index:tuple(outline[index]));outline=np.roll(outline,-start,axis=0)
# TIMESTAMP END 2026-11-02T20:47:22-05:00 | REVISION R004872
    assert np.allclose(dimensions,[2,6],rtol=0,atol=1e-7),(part['id'],dimensions)
    assert abs(area-12)<1e-7,(part['id'],area)
    return {'id':part['id'],'measured_width_in':float(dimensions[0]),'measured_depth_in':float(dimensions[1]),
            'measured_area_in2':float(area),'section_origin_m':origin.tolist(),'axis_from_mesh_edge':axis.tolist(),
            'axis_edge_length_m':float(length),'profile_inches':outline.tolist()}

def diagram(rows):
    by_id={row['id']:row for row in rows};draw=[]
    for index,name in enumerate(['K2-A','K2-B','K2-C']):
        row=by_id[name];x=150+index*300;y=145;scale=55
        points=' '.join(f'{x+px*scale:.6f},{y+(6-py)*scale:.6f}' for px,py in row['profile_inches'])
        draw.append(f'<text x="{x+55}" y="112" text-anchor="middle" font-size="24">{name}</text>')
        draw.append(f'<polygon points="{points}" fill="#b88b57" stroke="#493b2b" stroke-width="2"/>')
        draw.append(f'<path d="M{x} 490V515 M{x+110} 490V515 M{x} 507H{x+110}" fill="none" stroke="#29494d" stroke-width="1.5"/>')
        draw.append(f'<text x="{x+55}" y="542" text-anchor="middle" font-size="22">{row["measured_width_in"]:.3f} in</text>')
        draw.append(f'<path d="M{x-8} {y}H{x-40} M{x-8} {y+330}H{x-40} M{x-31} {y}V{y+330}" fill="none" stroke="#29494d" stroke-width="1.5"/>')
        draw.append(f'<text x="{x-50}" y="{y+165}" text-anchor="middle" transform="rotate(-90 {x-50} {y+165})" font-size="22">{row["measured_depth_in"]:.3f} in</text>')
        draw.append(f'<text x="{x+55}" y="576" text-anchor="middle" font-size="18">Area: {row["measured_area_in2"]:.3f} in²</text>')
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="1020" height="690" viewBox="0 0 1020 690">'
        '<!-- TIMESTAMP START 2026-11-02T19:03:42-05:00 | REVISION R004847 -->'
        '<rect width="1020" height="690" fill="#f8f7f2"/><g font-family="Arial, sans-serif" fill="#213e42">'
        '<text x="35" y="42" font-size="28">Actual brace body sections: 2 × 6 inches</text>'
        '<text x="35" y="74" font-size="17">Perpendicular slices through the occupied meshes, shown at the same scale.</text>'
        +''.join(draw)+
        '<text x="35" y="628" font-size="18">All 24 main braces measured: 2.000 × 6.000 in; 12.000 in².</text>'
        '<text x="35" y="660" font-size="16">Axis derived from real mesh edges. Body dimensions do not qualify joint strength.</text>'
        '</g><!-- TIMESTAMP END 2026-11-02T19:03:42-05:00 | REVISION R004847 --></svg>\n')

def build():
    sources={};models=[]
    for filename in ['model-data.json','step-lap-proposed-model.json','top-entry-proposed-model.json']:
        path='src/'+filename;raw=(ROOT/path).read_bytes();sources[path]=hashlib.sha256(raw).hexdigest();models.append(json.loads(raw))
    braces=[p for p in models[-1]['parts'] if p.get('group')=='braces'];assert len(braces)==24
    rows=[measure(p) for p in braces]
    for model in models:
        by_id={p['id']:p for p in model['parts']}
        for p in braces:
            candidate=by_id[p['id']]
            assert candidate['vertices']==p['vertices'] and candidate['triangles']==p['triangles']
            for key in ['dimensions','nominal_dimensions']:
                assert candidate[key]['width_in']==2 and candidate[key]['depth_in']==6,(p['id'],key)
                assert candidate[key]['section_display']=='2 × 6 in'
    svg=diagram(rows);sources['scripts/audit_brace_sections.py']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    report={'status':'PASS','revision':'R004847','timestamp':'2026-11-02T19:03:42-05:00',
            'sources':sources,'primary_brace_count':24,'all_three_variants_identical_brace_meshes':True,
            'method':'Find the longest actual non-coplanar mesh feature edge, cut a perpendicular plane at its midpoint, then measure the minimum-area bounding rectangle and occupied area of that actual section. No stock frame, nominal size or declared axis enters the measurement.',
            'scope':'Full body stock section, outside end joinery; capacity and fabrication dimensions remain unqualified.',
            'inspector_labels_match_geometry':True,'measurements':rows,
            'image':{'path':'public/review/brace-sections.svg','sha256':hashlib.sha256(svg.encode()).hexdigest()}}
# TIMESTAMP START 2026-11-02T20:47:22-05:00 | REVISION R004872
    def stable(value):
        if isinstance(value,float):return round(value,8)
        if isinstance(value,list):return [stable(item) for item in value]
        if isinstance(value,dict):return {key:stable(item) for key,item in value.items()}
        return value
    return stable(report),svg
# TIMESTAMP END 2026-11-02T20:47:22-05:00 | REVISION R004872

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args();report,svg=build()
    path=ROOT/'docs/brace-sections.json';image=ROOT/report['image']['path']
    if args.check:
        assert json.loads(path.read_text())==report,'Stale measured-section report'
        assert image.read_text()==svg,'Stale orthographic section diagram'
    else:path.write_text(json.dumps(report,indent=2)+'\n');image.write_text(svg)
    print('PASS: all24 actual mesh-derived body sections are2.000×6.000in and12.000in²; allthree variants and inspector labels match')
# TIMESTAMP END 2026-11-02T19:03:42-05:00 | REVISION R004847
