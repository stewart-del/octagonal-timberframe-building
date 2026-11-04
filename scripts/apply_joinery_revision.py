# TIMESTAMP START 2026-11-03T15:35:25-05:00 | REVISION R005035
"""Prepare all revised primary variants before replacing any saved source."""
from pathlib import Path
import argparse,copy,hashlib,json,math,re
import numpy as np
import manifold3d as m
from step_lap import solid,mesh,original_stock,volume_centroid,close_bounds
from three_inch_tenons import build
from revise_face_braces import planes
from fit_wall_joinery import normalize,packed
from center_brace_tenons import I,rotate
from audit_cavity_fit import inspect_mesh,coplanar_surface_overlaps

ROOT=Path(__file__).resolve().parents[1]
REV='R005035';STAMP='2026-11-03T15:35:25-05:00'
FILES=[('baseline','model-data.json','cavity-data.json'),('proposed','step-lap-proposed-model.json','step-lap-proposed-cavities.json'),('top-entry','top-entry-proposed-model.json','top-entry-proposed-cavities.json')]

def save(path,data):path.write_text(json.dumps(data,separators=(',',':'))+'\n')
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def normalized(shape):
    try:return normalize(shape)
    except AssertionError:
        # Opposed mortises that meet exactly at the middle of a six-inch
        # post can leave internal zero-thickness caps in the CSG boundary.
        # Remove only triangles proved wholly covered by opposed triangles.
        data=mesh(shape);v=np.array(data['vertices']);f=np.array(data['triangles'],dtype=np.uint64)
        check=coplanar_surface_overlaps(v,f);coverage={}
        for pair in check['overlap_pairs']:
            if pair['orientation']!='opposed':continue
            for index in pair['triangles']:coverage[index]=coverage.get(index,0)+pair['area_m2']
        area=np.linalg.norm(np.cross(v[f[:,1]]-v[f[:,0]],v[f[:,2]]-v[f[:,0]]),axis=1)/2
        remove={i for i,covered in coverage.items() if abs(covered-area[i])<1e-11}
        assert remove,'No complete internal caps to remove'
        faces=[t for i,t in enumerate(f) if i not in remove];pool=[];mapping={}
        for index in sorted({int(i) for t in faces for i in t}):
            point=v[index];hit=next((j for j,q in enumerate(pool) if np.linalg.norm(point-q)<1e-9),None)
            if hit is None:hit=len(pool);pool.append(point)
            mapping[index]=hit
        triangles=np.array([[mapping[int(i)] for i in t] for t in faces],dtype=np.uint64);vertices=np.array(pool)
        proof=inspect_mesh(vertices,triangles);assert proof['status']=='PASS',proof['failures']
        result=m.Manifold(m.Mesh64(vertices,triangles));assert str(result.status())=='Error.NoError'
        assert abs(result.volume()-shape.volume())/I**3<1e-6,'Boundary cleanup changed volume'
        return result

def candidate(model,source_sha):
    assert not model.get('three_inch_joinery_revision'),'Revision already applied'
    result=build(model);assert result['audit']['status']=='PASS',result['audit']
    revised=copy.deepcopy(model);records={p['id']:p for p in revised['parts']}
    brace_specs={p['id']:p for p in result['specs']};peg_specs={p['id']:p for p in result['peg_specs']}
    shapes={};cache={}
    for pid,shape in result['solids'].items():
        match=re.fullmatch(r'([A-Z]+)([0-7])(.*)',pid);seed=match[1]+'0'+match[3] if match else pid
        if match and seed in result['solids']:
            if seed not in cache:
                print('normalize',seed,flush=True);cache[seed]=normalized(result['solids'][seed])
            shape=cache[seed].rotate([0,45*int(match[2]),0])
        else:shape=normalized(shape)
        shapes[pid]=shape;p=records[pid];q=mesh(shape);p.update(vertices=q['vertices'],triangles=q['triangles'],faces=q['triangles'])
        p['fit_geometry']={**p.get('fit_geometry',{}),'volume_m3':shape.volume(),'nominal_fit':'Current three-inch joinery geometry; capacity unverified'}
        if pid in brace_specs:
            spec=brace_specs[pid];a=np.array(spec['axis_start']);b=np.array(spec['axis_end']);axis=(b-a)/np.linalg.norm(b-a)
            p.update(axis_start=a.tolist(),axis_end=b.tolist(),axis_direction=axis.tolist(),center=((a+b)/2).tolist(),label_position=((a+b)/2).tolist(),stock_frame=spec['stock_frame'],geometry_planes_inches=planes(result['stocks'][pid]),reference_end_faces=[],joint_cut_faces=[])
            p['main_face_brace_joinery']={**spec,'revision':REV,'family':'Centered straight tenons; flat bearing ends','peg_ids':[q['id'] for q in result['peg_specs'] if q['brace']==pid]}
            p['declared_exterior_cut']=packed(result['stocks'][pid]-result['pre_bore_braces'][pid])
            length=float(np.linalg.norm(b-a));p['dimensions']={**p['dimensions'],'length_m':length,'length_ft':length/.3048,'length_display':f'{length/I:.3f} in','status':'Full 2x6 stock with measured three-inch tenons'};p['nominal_dimensions']=copy.deepcopy(p['dimensions'])
            p['angles']={**p['angles'],'axis_inclination_deg':math.degrees(math.asin(axis[1])),'azimuth_deg':math.degrees(math.atan2(-axis[2],axis[0]))%360}
            p['notes']=['Centered full 2x6 stock. Each straight tenon projects three inches into its receiver.','Inward braces meet the posts below the two perimeter-brace mortises.','Nominal geometry only; joint capacity and fabrication tolerances remain unverified.']
            p['cut_status']='CENTERED THREE-INCH TENONS'
        if pid in peg_specs:
            spec=peg_specs[pid];axis=np.array(spec['withdrawal_world']);vv=np.array(p['vertices']);center=np.array(volume_centroid(shape)['centroid_m']);low=min(vv@axis);high=max(vv@axis)
            p.update(joint_members=[spec['receiver'],spec['brace']],axis_direction=axis.tolist(),axis_start=(center+axis*(low-center@axis)).tolist(),axis_end=(center+axis*(high-center@axis)).tolist(),center=center.tolist(),label_position=center.tolist(),withdrawal_direction=axis.tolist(),withdrawal_distance_m=spec['withdrawal_distance_m'],exploded_offset=(axis*.4).tolist(),peg_geometry=spec)
            p['dimensions']={**p['dimensions'],'length_m':float(high-low),'length_ft':float((high-low)/.3048),'length_display':f'{(high-low)/I:.3f} in'};p['nominal_dimensions']=copy.deepcopy(p['dimensions'])
            p['notes']=['Transverse hardwood peg through the real tenon and both receiver cheeks.','Matching bores are subtracted from both members. Diameter and structural capacity need engineering.']
        if pid.startswith('CP'):
            delta=rotate([.5*I,0,0],int(pid[2]))
            for key in ['axis_start','axis_end','center','label_position']:p[key]=(np.array(p[key])+delta).tolist()
        if p.get('is_timber'):
            p['reference_end_faces']=[];p['joint_cut_faces']=[]
            if p.get('cupola_foot_joinery'):p['cupola_foot_joinery'].update(engagement_in=3,head_width_in=3.75,revision=REV)
            joints=[j for j in result['joints'] if j['donor']==pid]
            if joints:p['new_stock_requirements']={**p.get('new_stock_requirements',{}),'tenon_projection_in':3,'status':'Cut from longer raw stock; no glued-on tenons'}
            if joints and not pid.startswith('K'):
                ends={j['end'] for j in joints if j.get('end') in ['A','B']}
                if p.get('cupola_foot_joinery') and pid.startswith('T'):ends.add('B')
                full=copy.deepcopy(p.get('proposed_stock_planes_inches',p['geometry_planes_inches']))
                for plane in full:
                    if plane.get('end') in ends:
                        original=next(q for q in p['geometry_planes_inches'] if q.get('end')==plane['end'])
                        plane['constant']=original['constant']+3
                p['proposed_stock_planes_inches']=full
    # The extra blank length is cut down to a tenon. Its exterior shoulders
    # are offcuts, not hollow pockets in the finished member.
    offcut_seeds={}
    for pid,p in records.items():
        if not p.get('is_timber') or pid.startswith('K') or not p.get('proposed_stock_planes_inches'):continue
        match=re.fullmatch(r'([A-Z]+)([0-7])(.*)',pid);seed=match[1]+'0'+match[3]
        if seed in offcut_seeds:
            p['declared_exterior_cut']=mesh(offcut_seeds[seed].rotate([0,45*int(match[2]),0]));continue
        # TIMESTAMP START 2026-11-03T16:00:30-05:00 | REVISION R005047
        if seed=='J0-2' and 'J0-0' in offcut_seeds:
            diagonal=math.sqrt(.5)
            reflected=offcut_seeds['J0-0'].transform([[diagonal,0,-diagonal,0],[0,1,0,0],[-diagonal,0,-diagonal,0]])
            offcut_seeds[seed]=reflected
            p['declared_exterior_cut']=mesh(reflected.rotate([0,45*int(match[2]),0]));continue
        # TIMESTAMP END 2026-11-03T16:00:30-05:00 | REVISION R005047
        print('offcut',pid,flush=True)
        stock_record={**p,'geometry_planes_inches':p['proposed_stock_planes_inches']}
        full=original_stock(stock_record);legacy=original_stock(p)
        assert (shapes[pid]-full).volume()/I**3<1e-6,(pid,'finished timber exceeds declared raw stock')
        offcuts=full-legacy
        tongues=[j for j in result['joints'] if j['donor']==pid]
        if tongues:
            for joint in tongues:offcuts=offcuts-solid(joint.get('cutting_tool',joint['connector']))
        else:offcuts=offcuts-shapes[pid]
        offcut_seeds[seed]=normalized(offcuts);p['declared_exterior_cut']=mesh(offcut_seeds[seed])
    # TIMESTAMP START 2026-11-03T15:58:36-05:00 | REVISION R005044
    # The independent cavity exporter partitions full stock into mating pockets,
    # explicit entry space and shoulder offcuts. Do not emit a second, legacy
    # subtraction that incorrectly treats every removed region as a mortise.
    cavities={}
    # TIMESTAMP END 2026-11-03T15:58:36-05:00 | REVISION R005044
    revised['tenon_schedule']=result['joints'];revised['joinery_entry_regions']={pid:packed(s) for pid,s in result['entry_regions'].items()}
    revised['three_inch_joinery_revision']={'revision':REV,'timestamp':STAMP,**result['audit'],'open_top_ring_mortises':True,'source_model_sha256':source_sha}
    revised['main_brace_revision'].update(revision=REV,actual_section_in=[2,6],brace_count=24)
    revised['main_face_brace_revision']={'revision':REV,'timestamp':STAMP,'family':'Centered three-inch tenons','brace_count':24,'peg_count':48,'brace_specs':result['specs'],'peg_specs':result['peg_specs'],'capacity_checked':False,'full_scene_disassembly_verified':False}
    if revised.get('cupola_foot_revision'):revised['cupola_foot_revision'].update(revision=REV,engagement_in=3,head_width_in=3.75,full_scene_disassembly_verified=False)
    revised['proposed_member_volume_centroids']=[dict(id=pid,**volume_centroid(s)) for pid,s in shapes.items() if records[pid].get('is_timber')]
    return revised,cavities,result['audit']

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',default='/tmp/octagon-joinery-candidate');args=parser.parse_args();out=Path(args.output);out.mkdir(parents=True,exist_ok=True)
    reports={}
    for variant,name,cavity_name in FILES:
        print('variant',variant,flush=True);model,cavities,audit=candidate(json.loads((ROOT/'src'/name).read_text()),digest(ROOT/'src'/name));save(out/name,model)
        old=json.loads((ROOT/'src'/cavity_name).read_text());old.update(parts=cavities,source_model_sha256=digest(out/name),revision=REV)
        old.pop('fit_audit',None);save(out/cavity_name,old);reports[variant]=audit
    save(out/'three-inch-tenon-audit.json',{'revision':REV,'timestamp':STAMP,'variants':reports});print('Prepared all three candidate variants',flush=True)

if __name__=='__main__':main()
# TIMESTAMP END 2026-11-03T15:35:25-05:00 | REVISION R005035
