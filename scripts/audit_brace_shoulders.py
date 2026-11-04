# TIMESTAMP START 2026-11-04T19:33:21+00:00 | REVISION R000014
"""Read actual brace meshes: lower inward feet, square bearing and 3 in tips."""
from pathlib import Path
import argparse,copy,hashlib,json,os
import numpy as np
import manifold3d as m
from plan_architectural_disassembly import load_scene,VARIANTS
from audit_revised_joinery import native_solid

ROOT=Path(__file__).resolve().parents[1]
I=.0254
REV='R000014'
STAMP='2026-11-04T19:33:21+00:00'

def area_at_y(shape,y):
    # Scaled section extraction avoids the slice kernel's small-unit tolerance.
    return shape.rotate([90,0,0]).scale([1e5]*3).slice(y*1e5).area()/1e10/I**2

def upper_joint(scene,joint):
    assert joint['receiver'].startswith('B')
    donor=scene.parts[joint['donor']];receiver=scene.parts[joint['receiver']]
    vertices=np.asarray(joint['connector']['vertices']);up=np.array([0.,1.,0.]);mouth=joint['face_center'][1]
    assert np.allclose(joint['insertion_direction'],up,rtol=0,atol=1e-9)
    assert abs(np.ptp(vertices@up)/I-3)<1e-6,'Upper tenon must penetrate three inches'
    assert abs(vertices[:,1].min()-mouth)<1e-9 and abs(vertices[:,1].max()-mouth-3*I)<1e-9
    # TIMESTAMP START 2026-11-04T19:33:21+00:00 | REVISION R000014
    bearing=np.asarray(joint['bearing_direction']);nose=max(vertices@bearing)
    flat_end=vertices[abs(vertices@bearing-nose)<1e-8]
    assert len(flat_end)>=4 and abs(np.ptp(flat_end[:,1])/I-3)<1e-6,'Squared internal bearing end is missing'
    brace=scene.solids[donor['id']];beam=scene.solids[receiver['id']];epsilon=1e-5*I
    body_area=area_at_y(brace,mouth-epsilon);tongue_area=area_at_y(brace,mouth+epsilon)
    assert body_area-tongue_area>5,'Outer shoulder lip is missing'
    assert tongue_area>7,'Broad housed brace profile was replaced by a pencil tongue'
    assert area_at_y(brace,mouth+3*I-epsilon)>4,'Sloping heel has been cut away'
    assert area_at_y(brace,mouth+3*I+epsilon)<1e-8,'Tenon nose is not flat at three inches'
    # TIMESTAMP END 2026-11-04T19:33:21+00:00 | REVISION R000014
    # Read mating contact surfaces independently from the stored joint metadata.
    from step_lap import contacts
    contact=contacts(brace,beam)
    bearing_area=sum(c['area_in2'] for c in contact if np.dot(c['normal_on_rafter'],bearing)>1-1e-8)
    assert bearing_area>2.99,'Squared end does not bear against the interior mortise wall'
    connector=native_solid(joint['connector']);peg=scene.solids[joint['peg_id']]
    assert (connector^beam).volume()/I**3<1e-6,'Mortise does not fit tenon'
    assert (brace^beam).volume()/I**3<1e-6,'Brace intersects its receiver'
    assert (connector^peg).volume()/I**3>.15,'Peg misses the actual tenon'
    frame=np.asarray(donor['stock_frame']['axis']);points=np.asarray(donor['vertices'])
    return {'brace':donor['id'],'receiver':receiver['id'],'tenon_depth_in':float(np.ptp(vertices@up)/I),
        'internal_bearing_area_in2':bearing_area,'minimum_blank_length_in':float(np.ptp(points@frame)/I),
        'body_reference_length_in':donor['dimensions']['length_m']/I,'flat_tip_and_square_sides':True,'peg_crosses_tenon':True}

def inspect(variant):
    scene=load_scene(variant);model=json.loads((ROOT/'src'/VARIANTS[variant][0]).read_text());joints=model['tenon_schedule'];rows=[];post_bearing=[]
    for k in range(8):
        feet={suffix:scene.parts[f'K{k}-{suffix}']['axis_start'][1]/I for suffix in ['A','B','C']}
        assert abs(feet['C']-44)<1e-6 and abs(feet['A']-62)<1e-6 and abs(feet['B']-62)<1e-6,'Inward brace must remain eighteen inches lower'
        # TIMESTAMP START 2026-11-04T19:33:21+00:00 | REVISION R000014
        inward=scene.parts[f'K{k}-C'];width=np.asarray(inward['stock_frame']['width']);vv=np.asarray(inward['vertices']);mid=(min(vv@width)+max(vv@width))/2
        assert abs(mid-np.asarray(scene.parts[f'P{k}']['center'])@width)<1e-8,'Inward brace is off the post center plane'
        assert abs(mid-np.asarray(scene.parts[f'T{k}']['center'])@width)<1e-8,'Inward brace is off the cross-beam center plane'
        from audit_brace_sections import measure
        section=measure(inward);assert abs(section['measured_width_in']-2)<1e-7 and abs(section['measured_depth_in']-6)<1e-7
        lower=next(j for j in joints if j['donor']==f'K{k}-C' and j['receiver']==f'P{k}')
        # TIMESTAMP END 2026-11-04T19:33:21+00:00 | REVISION R000014
        outer=[j for j in joints if j['donor'] in [f'K{k}-A',f'K{k}-B'] and j['receiver']==f'P{k}']
        assert max(v[1] for v in lower['connector']['vertices'])+8*I<min(v[1] for j in outer for v in j['connector']['vertices'])
        # TIMESTAMP START 2026-11-04T19:33:21+00:00 | REVISION R000014
        head=next(j for j in joints if j['donor']==f'K{k}-C' and j['receiver']==f'T{k}')
        assert head['shape']=='simple square-seated vertical tenon' and head['gravity_seated']
        head_vertices=np.asarray(head['connector']['vertices']);assert abs(np.ptp(head_vertices[:,1])/I-3)<1e-6
        base_y=head['face_center'][1];tip_y=base_y+3*I
        assert abs(area_at_y(scene.solids[f'K{k}-C'],base_y+I)-2)<1e-5,'Cross-beam tenon is not plain and square'
        assert abs(area_at_y(scene.solids[f'K{k}-C'],tip_y-I*.001)-2)<1e-5
        # TIMESTAMP END 2026-11-04T19:33:21+00:00 | REVISION R000014
        for suffix in ['A','B']:
            joint=next(j for j in joints if j['donor']==f'K{k}-{suffix}' and j['receiver'].startswith('B'))
            rows.append(upper_joint(scene,joint))
        for suffix in ['A','B','C']:
            for joint in (j for j in joints if j['donor']==f'K{k}-{suffix}'):
                if joint['receiver']==f'P{k}':
                    from step_lap import contacts
                    bearing=np.asarray(joint['bearing_direction'])
                    contact=contacts(scene.solids[joint['donor']],scene.solids[joint['receiver']])
                    area=sum(c['area_in2'] for c in contact if np.dot(c['normal_on_rafter'],bearing)>1-1e-8)
                    assert area>2.99,(joint['id'],'internal post bearing wall has lost contact',area)
                    post_bearing.append(area)
                v=np.asarray(joint['connector']['vertices']);n=np.asarray(joint['insertion_direction'])
                assert abs(np.ptp(v@n)/I-3)<1e-6,(joint['id'],'three-inch engagement')
    return scene,model,{'variant':variant,'status':'PASS','sources':scene.sources,'outer_joints':rows,'inward_foot_in':44,'outer_foot_in':62,'foot_separation_in':18,'minimum_internal_post_bearing_area_in2':min(post_bearing)}

def profile(shape,origin,e,normal):
    frame=np.array([e,[0,1,0],normal]);trans=np.column_stack([frame,-frame@origin])
    return [np.asarray(poly)/1e5/I for poly in shape.transform(trans.tolist()).scale([1e5]*3).slice(0).to_polygons()]

def draw(scene,model,destination):
    os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'.codex-runtime/matplotlib'))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.path import Path as PlotPath
    from matplotlib.patches import PathPatch
    joint=next(j for j in model['tenon_schedule'] if j['donor']=='K0-B' and j['receiver']=='B0')
    origin=np.asarray(joint['face_center']);e=np.asarray(joint['height_direction']);normal=np.asarray(joint['width_direction'])
    brace=scene.solids['K0-B'];beam=scene.solids['B0']
    peg_center=np.asarray(scene.parts[joint['peg_id']]['peg_geometry']['bore_center_world']);peg_xy=[float((peg_center-origin)@e/I),float((peg_center[1]-origin[1])/I)-8]
    fig,axes=plt.subplots(1,2,figsize=(14,8));fig.patch.set_facecolor('#f6f2e9')
    def patch(ax,polygons,color):
        vertices=[];codes=[]
        for poly in polygons:
            vertices.extend([*poly,poly[0]]);codes.extend([PlotPath.MOVETO]+[PlotPath.LINETO]*(len(poly)-1)+[PlotPath.CLOSEPOLY])
        ax.add_patch(PathPatch(PlotPath(vertices,codes),facecolor=color,edgecolor='#514032',lw=1.4))
    for ax,drop,title in zip(axes,[0,8],['Assembled: squared end bears inside the mortise','Withdrawn: housed brace profile from your reference']):
        ax.set_facecolor('#f6f2e9');patch(ax,profile(beam,origin,e,normal),'#dfbd88')
        patch(ax,profile(brace.translate([0,-drop*I,0]),origin,e,normal),'#bc8b51')
        ax.set_aspect('equal');ax.set_xlim(-13,9);ax.set_ylim(-19,9);ax.axis('off');ax.set_title(title,loc='left',fontsize=14,pad=15)
        if drop:
            ax.annotate('',xy=(5,-5),xytext=(5,-8),arrowprops={'arrowstyle':'<->','color':'#206067','lw':1.5})
            ax.text(5.5,-6.5,'3 in',va='center',color='#206067',fontsize=13)
            ax.annotate('Squared bearing end',xy=(3.49,-6.5),xytext=(-12,-2),arrowprops={'arrowstyle':'->','color':'#206067'},color='#206067',fontsize=11)
            ax.annotate('Interior bearing wall',xy=(3.49,1.5),xytext=(-12,6),arrowprops={'arrowstyle':'->','color':'#206067'},color='#206067',fontsize=11)
            ax.annotate('Actual peg bore',xy=peg_xy,xytext=(3,-11),arrowprops={'arrowstyle':'->','color':'#206067'},color='#206067',fontsize=11)
        else:
            ax.annotate('Squared end bears here',xy=(3.49,1.5),xytext=(-12,-3.5),arrowprops={'arrowstyle':'->','color':'#206067'},color='#206067',fontsize=11)
    fig.suptitle('Outer wall brace joint — section through the actual model',x=.055,ha='left',fontsize=19,color='#203f43')
    fig.text(.055,.115,'Inward brace foot: 44 in     Outer brace feet: 62 in     Difference: 18 in lower',fontsize=13,color='#203f43')
    lengths=[np.ptp(np.asarray(scene.parts[pid]['vertices'])@np.asarray(scene.parts[pid]['stock_frame']['axis']))/I for pid in ['K0-B','K0-C']]
    fig.text(.055,.077,f'2 × 6 minimum stock lengths including housed tenons: outer {lengths[0]:.3f} in; inward {lengths[1]:.3f} in.',fontsize=12,color='#203f43')
    fig.text(.055,.04,'Sections use occupied meshes and real bores. Add cutting and dressing allowances to stock lengths.',fontsize=10,color='#59645d')
    fig.subplots_adjust(left=.04,right=.98,top=.86,bottom=.17,wspace=.15)
    destination.parent.mkdir(parents=True,exist_ok=True);fig.savefig(destination,dpi=150,facecolor=fig.get_facecolor());plt.close(fig)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--write',action='store_true');parser.add_argument('--self-test',action='store_true');args=parser.parse_args()
    reports=[]
    for variant in ['baseline','proposed','top-entry']:
        scene,model,result=inspect(variant);reports.append(result);print(variant,'PASS: 16 square-shouldered outer joints; 48 three-inch brace tenons; inward feet eighteen inches lower',flush=True)
    if args.self_test:
        source=next(j for j in model['tenon_schedule'] if j['donor']=='K0-B' and j['receiver']=='B0');bad=copy.deepcopy(source)
        tip=max(v[1] for v in bad['connector']['vertices'])
        for v in bad['connector']['vertices']:
            if abs(v[1]-tip)<1e-9:v[1]+=I
        try:upper_joint(scene,bad)
        except AssertionError:pass
        else:raise AssertionError('Overlong tenon adversary was accepted')
        good=scene.solids[source['donor']];scene.solids[source['donor']]=good.translate([0,-.01,0])
        try:upper_joint(scene,source)
        except AssertionError:pass
        else:raise AssertionError('Detached bearing shoulder adversary was accepted')
        scene.solids[source['donor']]=good
        print('PASS: overlong tenon and detached shoulder adversaries rejected',flush=True)
    if args.write:
        image=ROOT/'public/review/brace-shoulders.png';draw(scene,model,image)
        report={'status':'PASS','revision':REV,'timestamp':STAMP,'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'variants':reports,
            'image':{'path':str(image.relative_to(ROOT)),'sha256':hashlib.sha256(image.read_bytes()).hexdigest()},'scope':'Nominal joint geometry and minimum blank envelope; no machining allowances or structural capacity calculation.'}
        (ROOT/'docs/brace-shoulder-audit.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
# TIMESTAMP END 2026-11-04T19:33:21+00:00 | REVISION R000014
