"""Geometric seating correction for the temporary aid, not fastening design."""
import copy,json,math,sys
from pathlib import Path
import numpy as np
import manifold3d as m
from central_support import make_fixture,INCH

def mesh(p):return m.Manifold(m.Mesh64(np.asarray(p['vertices']),np.asarray(p['triangles'],dtype=np.uint64)))
def fit_fixture(model):
    parts={p['id']:p for p in model['parts']}
    # Actual post side is 3in from radial plane. Actual tie top establishes lower leg datum.
    post=np.asarray(parts['C0']['vertices'])/INCH
    side=float(post[:,2].max());top=max(v[1] for v in parts['T0']['vertices'])/INCH+14
    thickness=.25;offset=side+thickness/2
    arm=m.Manifold.cube((50,4,thickness)).translate((-5,-4,-thickness/2))
    arm+=m.Manifold.cube((4,14,thickness)).translate((41,-14,-thickness/2))
    for d in (2,7,12):arm-=m.Manifold.cylinder(thickness+1,.375/2,circular_segments=32,center=True).translate((43,-d,0))
    arm=arm.translate((0,top,offset));solid=m.Manifold()
    for k in range(8):solid+=arm.rotate((0,k*45,0))
    solid=solid.scale((INCH,)*3);v=np.asarray(solid.to_mesh64().vert_properties)[:,:3];t=solid.to_mesh64().tri_verts.tolist()
    p=make_fixture(top*INCH)
    p.update(vertices=v.tolist(),triangles=t,faces=t,center=((v.min(0)+v.max(0))/2).tolist())
    p['label_position']=p['center'];p['fit_geometry']['volume_m3']=solid.volume()
    p['display_assumptions'].update(steel_thickness_in=thickness,tangential_offset_in=offset,central_overlap_extension_in=5)
    p['source_geometry_metadata']['revision']='central-support-face-seated-2'
    p['source_geometry_metadata']['illustrative_display_assumptions']=copy.deepcopy(p['display_assumptions'])
    p['dimension_status']['top_elevation_m']='chosen erection display level: outer leg bottom at actual lower-tie top; not verified erection sequence'
    p['notes']=[n for n in p['notes'] if 'Placement retains' not in n and '1/8' not in n]
    p['notes']+=['Outer legs seat against actual cupola-post side faces. Each radial L is tangentially offset; 5in central extensions overlap as one welded display union. Pure rotation would leave wedge-shaped gaps.','Chosen display thickness 1/4in, hole diameter3/8in and screw positions remain unspecified construction details, not approved fabrication.','The lower leg aligns with lower-tie top; all24 hole axes meet adjacent post wood. This geometric fit does not verify screw engagement, weld design, installation access or support capacity.']
    p['dimension_status']['steel_thickness_in']='chosen 1/4in display thickness; steel grade and required gauge not established'
    p['source_geometry_metadata']['dimension_status']=copy.deepcopy(p['dimension_status'])
    p['display_holes']=[];report={'chosen_top_in':top,'post_side_in':side,'thickness_in':thickness,'holes':[],'positive_intersections':[],'contact_faces':[]}
    for k in range(8):
        a=k*math.pi/4;c,s=math.cos(a),math.sin(a)
        # Rotation convention matches Manifold Y rotation; into timber is negative local Z.
        inward=np.array([-s,0,-c]);receiver=parts[f'C{k}']
        for j,d in enumerate((2,7,12)):
            center=np.array([43*c+offset*s,top-d,-43*s+offset*c])*INCH
            origin=center+inward*thickness/2*INCH
            ray=ray_hit(origin+inward*1e-8,inward,receiver)
            assert ray is not None and ray>0
            h={'id':f'M-TMP-ARM{k}-DISPLAY-HOLE{j+1}','arm_index':k,'center_m':center.tolist(),'axis':(-inward).tolist(),'diameter_in':.375,'status':'DISPLAY ONLY — NOT DRILLING OR FASTENER SPECIFICATION'}
            p['display_holes'].append(h)
            report['holes'].append({'id':h['id'],'receiver':receiver['id'],'wood_entry_gap_m':0,'wood_path_m':ray,'axis_into_wood':inward.tolist()})
        report['contact_faces'].append({'receiver':receiver['id'],'plane_normal':inward.tolist(),'gross_face_area_in2':6*4+3*10,'net_face_area_in2':6*4+3*10-3*16*(.375/2)**2*math.sin(2*math.pi/32),'bores_deducted':True})
    for q in parts.values():
        if q.get('is_timber'):
            vol=(solid^mesh(q)).volume()
            if vol>1e-10:report['positive_intersections'].append({'id':q['id'],'volume_m3':vol})
    assert not report['positive_intersections']
    assert len(solid.decompose())==1
    report.update(assembly_components=1,temporary=True,structural_capacity='not calculated',screw_and_weld_specification='not established',timbers_unchanged=True)
    return p,report

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
