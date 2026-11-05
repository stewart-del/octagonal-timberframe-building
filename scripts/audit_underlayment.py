# TIMESTAMP START 2026-11-04T23:48:03+00:00 | REVISION R000012
# TIMESTAMP START 2026-11-04T23:17:24+00:00 | REVISION R000029
"""Independently verify cut sheet stock, material conservation and unchanged supports."""
from pathlib import Path
import argparse, hashlib, itertools, json, math
import numpy as np
import manifold3d as m

ROOT = Path(__file__).resolve().parents[1]
I = .0254
TOL = 1e-6*I**3
NORTH = np.array([math.cos(math.pi/8), 0, -math.sin(math.pi/8)])
EAST = np.array([-NORTH[2], 0, NORTH[0]])
def digest(path): return hashlib.sha256((ROOT/path).read_bytes()).hexdigest()
def solid(part): return m.Manifold(m.Mesh64(np.asarray(part['vertices']), np.asarray(part['triangles'], dtype=np.uint64)))

def inspect(data, fixture):
    panels = [p for p in data['parts'] if p.get('floorRole') == 'underlayment_sheet']
    other = {p['id']: hashlib.sha256(json.dumps(p, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
             for p in data['parts'] if p not in panels}
    assert other == fixture['unchangedParts'], 'A non-underlayment component changed'
    assert len(panels) == 28 and len({p['id'] for p in panels}) == 28
    shapes = [solid(p) for p in panels]
    reference = solid(fixture['footprint'])
    union = m.Manifold.batch_boolean(shapes, m.OpType.Add)
    missing, added = (reference-union).volume(), (union-reference).volume()
    assert max(missing, added) <= TOL, ('Occupied floor changed', missing, added)
    maximum = max((a^b).volume() for a,b in itertools.combinations(shapes, 2))
    assert maximum <= TOL, ('Overlapping sheets', maximum)
    rows = []
    for p, shape in zip(panels, shapes):
        assert str(shape.status()) == 'Error.NoError' and shape.volume() > 0 and len(shape.decompose()) == 1, p['id']
        v = np.asarray(p['vertices']); stock = p['sheet_stock']
        sizes = [np.ptp(v@axis) for axis in [EAST, NORTH, np.array([0, 1, 0])]]
        assert sizes[0] <= 96*I+1e-8 and sizes[1] <= 48*I+1e-8 and abs(sizes[2]-1.5*I) < 1e-9
        assert np.allclose([stock['lengthM'], stock['widthM'], stock['thicknessM']], [96*I,48*I,1.5*I], atol=1e-10)
        row, column = stock['row'], stock['column']
        u0 = (column*96+((row+1)%2)*48)*I; v0 = (row*48+24)*I
        assert np.allclose(stock['eastBoundsM'], [u0,u0+96*I], atol=1e-10)
        assert np.allclose(stock['northBoundsM'], [v0,v0+48*I], atol=1e-10)
        assert abs(u0/(16*I)-round(u0/(16*I))) < 1e-8, 'Butt joint missed joist centerline'
        assert (v@EAST).min() >= u0-1e-8 and (v@EAST).max() <= u0+96*I+1e-8
        assert (v@NORTH).min() >= v0-1e-8 and (v@NORTH).max() <= v0+48*I+1e-8
        assert abs(v[:,1].min()+.05715) < 1e-9 and abs(v[:,1].max()+.01905) < 1e-9
        rows.append({'id':p['id'], 'row':row, 'column':column, 'cutBoundingSizeIn':[float(x/I) for x in sizes], 'volumeM3':shape.volume()})
    return {'status':'PASS','sheetCount':len(panels),'stockSizeFt':[8,4], 'thicknessIn':1.5,
            'staggerIn':48,'unchangedComponentCount':len(other),'symmetricDifferenceM3':{'missing':missing,'added':added},
            'maximumSheetIntersectionM3':maximum,'overlapToleranceM3':TOL,'panels':rows,
            'scope':'Geometric cut layout; 28 installed cut pieces, not an optimized sheet purchase count. Existing thickness and elevations retained.'}

def drawing(data):
    panels = [p for p in data['parts'] if p.get('floorRole') == 'underlayment_sheet']
    def xy(v): return (400+float(np.dot(v,EAST))*69, 405-float(np.dot(v,NORTH))*69)
    out=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 860">',
         '<!-- TIMESTAMP START 2026-11-04T23:17:24+00:00 | REVISION R000029 -->',
         '<rect width="800" height="860" fill="#f8f7f2"/><g font-family="sans-serif" fill="#173a40">',
         '<text x="32" y="34" font-size="23">Underlayment · cut 4 × 8-foot sheets</text>',
         '<text x="32" y="60" font-size="14">28 separate cut pieces · 4-foot stagger · existing 1½-inch thickness</text>']
    for p in panels:
        vertices=np.asarray(p['vertices']); edges={}
        for triangle in p['triangles']:
            if not all(abs(vertices[k,1]+.01905)<1e-8 for k in triangle): continue
            for a,b in zip(triangle,triangle[1:]+triangle[:1]):
                key=tuple(sorted((a,b)));edges[key]=edges.get(key,0)+1
        path=' '.join(f'M {xy(vertices[a])[0]:.4f} {xy(vertices[a])[1]:.4f} L {xy(vertices[b])[0]:.4f} {xy(vertices[b])[1]:.4f}' for (a,b),count in edges.items() if count==1)
        out.append(f'<path d="{path}" fill="none" stroke="#56676b" stroke-width="1.8"/>')
        x,y=xy(p['center']); out.append(f'<text x="{x:.2f}" y="{y:.2f}" text-anchor="middle" font-size="12">{p["id"].rsplit("-",1)[1]}</text>')
    out += ['<text x="400" y="92" text-anchor="middle" font-size="14">N ↑</text>',
            '<text x="32" y="805" font-size="14">Actual mesh boundaries include the octagonal cuts and bearing-stand notches.</text>',
            '<text x="32" y="830" font-size="14">Geometric layout; sheet grade, edge support and connections require design.</text></g>',
            '<!-- TIMESTAMP END 2026-11-04T23:17:24+00:00 | REVISION R000029 --></svg>']
    return '\n'.join(out)+'\n'

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--write',action='store_true');parser.add_argument('--check',action='store_true');parser.add_argument('--self-test',action='store_true');args=parser.parse_args()
    data=json.loads((ROOT/'src/floor-foundation-solids.json').read_text());fixture=json.loads((ROOT/'scripts/fixtures/underlayment-footprint.json').read_text())
    report=inspect(data,fixture)
    sources=['src/floor-foundation-solids.json','src/floor-foundation.js','scripts/floor_sheet_panels.py','scripts/build_floor_solids.py','scripts/audit_underlayment.py','scripts/fixtures/underlayment-footprint.json']
    report['sources']={path:digest(path) for path in sources}
    image=ROOT/'public/review/underlayment-sheets.svg'; svg=drawing(data)
    report['image']={'path':str(image.relative_to(ROOT)),'sha256':hashlib.sha256(svg.encode()).hexdigest()}
    if args.self_test:
        import copy
        bad=copy.deepcopy(data);panel=next(p for p in bad['parts'] if p.get('floorRole')=='underlayment_sheet')
        panel['vertices']=[[x+.001,y,z] for x,y,z in panel['vertices']]
        try:inspect(bad,fixture)
        except AssertionError:pass
        else:raise AssertionError('Displaced sheet adversary was accepted')
    if args.write:
        image.write_text(svg);(ROOT/'docs/underlayment-sheet-audit.json').write_text(json.dumps(report,indent=2)+'\n')
    if args.check:
        assert json.loads((ROOT/'docs/underlayment-sheet-audit.json').read_text())==report,'Underlayment audit is stale'
        assert image.read_text()==svg,'Sheet drawing is stale'
    print('PASS: 28 connected sheets fit 4×8-foot stock; exact occupied floor retained; 104 other components unchanged; butt joints align with joists')

if __name__=='__main__':main()
# TIMESTAMP END 2026-11-04T23:17:24+00:00 | REVISION R000029

# TIMESTAMP END 2026-11-04T23:48:03+00:00 | REVISION R000012
