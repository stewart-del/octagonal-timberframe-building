# TIMESTAMP START 2026-11-03T13:49:43-05:00 | REVISION R005031
"""Measure wood immediately outside every bore along each actual peg shaft."""
from pathlib import Path
import json,sys
import numpy as np
import manifold3d as m
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from step_lap import solid,close_bounds
from center_brace_tenons import I,cylinder

def inspect_peg(peg,members,known_axis=None,known_center=None,diameter=None):
    vertices=np.asarray(peg.to_mesh64().vert_properties)[:,:3]
    center=vertices.mean(0);_,_,directions=np.linalg.svd(vertices-center,full_matrices=False)
    axis=np.array(known_axis) if known_axis is not None else directions[0]
    if known_center is not None:center=np.array(known_center)
    low=min(vertices@axis);high=max(vertices@axis)
    radial=vertices-center-np.outer((vertices-center)@axis,axis)
    radius=diameter/2 if diameter is not None else float(np.max(np.linalg.norm(radial,axis=1)))
    # Inspect a thin annulus OUTSIDE the peg. Its intersection with actual
    # retained timber proves the bore is surrounded by that named member.
    outer=cylinder(center,axis,low,high,radius+.02*I)
    inner=cylinder(center,axis,low-.001,high+.001,radius+.001*I)
    ring=outer-inner;area=ring.volume()/(high-low)
    engagement={pid:float((ring^s).volume()/area/I) for pid,s in members.items()}
    overlap={pid:float((peg^s).volume()/I**3) for pid,s in members.items()}
    coverage=[]
    for t in np.linspace(.025,.975,39):
        c=low+(high-low)*t;half=.005*I
        sample=ring.trim_by_plane(axis.tolist(),c-half).trim_by_plane((-axis).tolist(),-c-half)
        denominator=sample.volume()
        peg_section=peg.trim_by_plane(axis.tolist(),c-half).trim_by_plane((-axis).tolist(),-c-half)
        # A flush peg end cut obliquely to its shaft naturally has a partial
        # cross-section. Assess surrounding wood where the full shaft exists.
        if peg_section.volume()/(2*half*np.pi*radius**2)<.95:continue
        coverage.append({pid:max(0.,float((sample^s).volume()/denominator)) for pid,s in members.items()})
    return {'shaft_length_in':float((high-low)/I),'diameter_in':2*radius/I,'engagement_in':engagement,'wood_overlap_in3':overlap,'minimum_combined_bore_surround_fraction':min(sum(row.values()) for row in coverage),'samples':coverage}

def run(model,porch):
    records={p['id']:p for p in model['parts']};shapes={pid:solid(p) for pid,p in records.items() if p.get('is_timber') or p.get('is_fastener')}
    rows=[];failures=[]
    specs=[(p['id'],p['joint_members'],p.get('withdrawal_direction',p.get('axis_direction')),p.get('peg_geometry',{}).get('bore_center_world',p['center']),p['dimensions']['width_m']) for p in model['parts'] if p.get('is_fastener')]
    for pid,p in porch['parts'].items():shapes[pid]=solid(p)
    for p in porch['added_parts']:shapes[p['id']]=solid(p)
    specs.extend((j['peg_id'],[j['donor'],j['receiver']],j.get('peg_axis_world'),j.get('peg_center_world'),j['peg_diameter_m']) for j in porch['joints'] if j.get('peg_id'))
    assert len({spec[0] for spec in specs})==len(specs)
    for pid,ids,axis,center,diameter in specs:
        result=inspect_peg(shapes[pid],{i:shapes[i] for i in ids},axis,center,diameter)
        issues=[]
        if min(result['engagement_in'].values())<.25:issues.append('Less than a quarter inch of full-circumference-equivalent engagement in an intended member')
        if max(result['wood_overlap_in3'].values())>1e-6:issues.append('Peg crosses retained wood without a matching bore')
        if result['minimum_combined_bore_surround_fraction']<.80:issues.append('Part of the shaft has incomplete surrounding wood')
        row={'id':pid,'members':ids,**result,'issues':issues};rows.append(row)
        if issues:failures.append({'id':pid,'issues':issues,'engagement_in':result['engagement_in'],'minimum_surround':result['minimum_combined_bore_surround_fraction']})
    return {'peg_count':len(rows),'status':'FAIL' if failures else 'PASS','failures':failures,'pegs':rows,'scope':'Actual bore engagement and void alignment; no peg shear, splitting, species, drawboring or load-capacity calculation.'}

if __name__=='__main__':
    model=json.loads((ROOT/'src/top-entry-proposed-model.json').read_text());porch=json.loads((ROOT/'src/mudroom-joinery-fit.json').read_text())
    report=run(model,porch)
    if '--output' in sys.argv:Path(sys.argv[sys.argv.index('--output')+1]).write_text(json.dumps(report,separators=(',',':'))+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='pegs'}),flush=True)
    assert report['status']=='PASS',report['failures']
# TIMESTAMP END 2026-11-03T13:49:43-05:00 | REVISION R005031
