"""Geometric seating correction for the temporary aid, not fastening design."""
import copy,json,math,sys
from pathlib import Path
import numpy as np
import manifold3d as m
from central_support import make_fixture,INCH

def mesh(p):return m.Manifold(m.Mesh64(np.asarray(p['vertices']),np.asarray(p['triangles'],dtype=np.uint64)))
# TIMESTAMP START 2026-11-03T06:59:29-05:00 | REVISION R004900
def fit_fixture(model):
    """Restore the original radial L form; alter only its rigid placement."""
    parts={p['id']:p for p in model['parts']}
    top=max(v[1] for v in parts['T0']['vertices'])+14*INCH
    p=make_fixture(top);angle=-4.7;a=math.radians(angle);c,s=math.cos(a),math.sin(a)
    rotation=np.array([[c,0,s],[0,1,0],[-s,0,c]])
    for key in ['vertices']:
        p[key]=(np.asarray(p[key])@rotation.T).tolist()
    for key in ['center','label_position','axis_start','axis_end','axis_direction']:
        p[key]=(rotation@np.asarray(p[key])).tolist()
    p['stock_frame']={k:(rotation@np.asarray(v)).tolist() for k,v in p['stock_frame'].items()}
    for hole in p['display_holes']:
        for key in ['center_m','axis']:hole[key]=(rotation@np.asarray(hole[key])).tolist()
    p['display_assumptions']['rigid_rotation_y_degrees']=angle
    p['source_geometry_metadata']['revision']='central-support-original-form-raised-3'
    p['source_geometry_metadata']['illustrative_display_assumptions']=copy.deepcopy(p['display_assumptions'])
    p['dimension_status']['top_elevation_m']='retained current display elevation: lower leg at actual lower-tie top'
    p['source_geometry_metadata']['dimension_status']=copy.deepcopy(p['dimension_status'])
    p['notes']=[n for n in p['notes'] if not n.startswith('Placement retains')]
    p['notes'].append('Original simple radial L shape restored at the retained height and center, with a rigid -4.7 degree rotation for post clearance. The legs are not flush against the post faces; the visible gap is not a designed fastening detail.')
    solid=mesh(p);p['fit_geometry']['volume_m3']=solid.volume()
    report={'chosen_top_in':top/INCH,'thickness_in':.125,'rigid_rotation_y_degrees':angle,'holes':[],'positive_intersections':[],'contact_faces':[],'flush_seating':False}
    for h in p['display_holes']:
        inward=-np.asarray(h['axis']);receiver=parts['C'+str(h['arm_index'])]
        origin=np.asarray(h['center_m'])+inward*.125/2*INCH
        entry=ray_hit(origin,inward,receiver)
        assert entry is not None and entry>0
        path=ray_hit(origin+inward*(entry+1e-8),inward,receiver)
        assert path is not None and path>0
        report['holes'].append({'id':h['id'],'receiver':receiver['id'],'wood_entry_gap_m':entry,'wood_path_m':path+1e-8,'axis_into_wood':inward.tolist()})
    for q in parts.values():
        if q.get('is_timber'):
            vol=(solid^mesh(q)).volume()
            if vol>1e-10:report['positive_intersections'].append({'id':q['id'],'volume_m3':vol})
    assert not report['positive_intersections'] and len(solid.decompose())==1
    report.update(assembly_components=1,temporary=True,structural_capacity='not calculated',screw_and_weld_specification='not established',timbers_unchanged=True)
    return p,report
# TIMESTAMP END 2026-11-03T06:59:29-05:00 | REVISION R004900

def ray_hit(o,d,p):
    """Nearest positive ray/triangle crossing (origin just inside the actual timber)."""
    hits=[];v=np.asarray(p['vertices'])
    for tri in p['triangles']:
        a,b,c=v[tri];e1=b-a;e2=c-a;h=np.cross(d,e2);det=np.dot(e1,h)
        if abs(det)<1e-12:continue
        f=1/det;s=o-a;u=f*np.dot(s,h)
        if u< -1e-9 or u>1+1e-9:continue
        q=np.cross(s,e1);w=f*np.dot(d,q)
        if w< -1e-9 or u+w>1+1e-9:continue
        t=f*np.dot(e2,q)
        if t>1e-7:hits.append(t)
    return min(hits) if hits else None

if __name__=='__main__':
    root=Path(__file__).resolve().parents[1];model=json.loads((root/'src/model-data.json').read_text());p,r=fit_fixture(model)
    (root/'src/seated-support.json').write_text(json.dumps(p,separators=(',',':')))
    (root/'docs/seated-support-fit.json').write_text(json.dumps(r,indent=2))
    print(json.dumps({k:r[k] for k in ('chosen_top_in','assembly_components','positive_intersections')}))
