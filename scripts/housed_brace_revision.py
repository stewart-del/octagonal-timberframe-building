# TIMESTAMP START 2026-11-04T19:42:40+00:00 | REVISION R000016
"""Stage the supplied housed-brace profile without changing unrelated joinery."""
from pathlib import Path
import argparse,copy,hashlib,json,math
import numpy as np
from center_brace_tenons import build,I
from step_lap import mesh,volume_centroid
from revise_face_braces import planes
from audit_revised_joinery import packed,native_solid
from audit_cavity_fit import inspect_mesh,arrays
ROOT=Path(__file__).resolve().parents[1]
FILES=['model-data.json','step-lap-proposed-model.json','top-entry-proposed-model.json']
REV='R000016';STAMP='2026-11-04T19:42:40+00:00'

def candidate(model):
    result=build(model);assert result['audit']['status']=='PASS',result['audit']
    revised=copy.deepcopy(model);parts={p['id']:p for p in revised['parts']};specs={p['id']:p for p in result['specs']};peg_specs={p['id']:p for p in result['peg_specs']};offcuts={}
    for pid,shape in result['solids'].items():
        # Preserve byte-exact geometry for members unrelated to the brace edit.
        if pid not in specs and pid not in peg_specs and pid not in result['receivers']:continue
        p=parts[pid];q=mesh(shape);p.update(vertices=q['vertices'],triangles=q['triangles'],faces=q['triangles']);p['fit_geometry']={**p.get('fit_geometry',{}),'volume_m3':shape.volume()}
        if pid in specs:
            spec=specs[pid];a=np.asarray(spec['axis_start']);b=np.asarray(spec['axis_end']);axis=(b-a)/np.linalg.norm(b-a)
            p.update(axis_start=a.tolist(),axis_end=b.tolist(),axis_direction=axis.tolist(),stock_frame=spec['stock_frame'],center=((a+b)/2).tolist(),label_position=((a+b)/2).tolist())
            p['dimensions']={**p['dimensions'],'length_m':float(np.linalg.norm(b-a)),'length_ft':float(np.linalg.norm(b-a)/.3048),'length_display':f'{np.linalg.norm(b-a)/I:.3f} in'};p['nominal_dimensions']=copy.deepcopy(p['dimensions'])
            p['main_face_brace_joinery']={**spec,'revision':REV,'family':'Housed brace with squared internal bearing end','peg_ids':[j['peg_id'] for j in spec['tenons']]}
            print('stock/offcut',pid,flush=True)
            p['geometry_planes_inches']=planes(result['stocks'][pid]);seed='K0-'+pid[-1]
            if seed not in offcuts:offcuts[seed]=native_solid(packed(result['stocks'][seed]-result['pre_bore_braces'][seed]))
            exterior=mesh(offcuts[seed].rotate([0,45*int(pid[1]),0]));assert inspect_mesh(*arrays(exterior))['status']=='PASS'
            p['declared_exterior_cut']=exterior
            length=float(np.ptp(np.asarray(q['vertices'])@np.asarray(p['stock_frame']['axis']))/I)
            p['fitted_axial_extent_inches']=length
            p['angles']={**p['angles'],'axis_inclination_deg':math.degrees(math.asin(axis[1])),'azimuth_deg':math.degrees(math.atan2(-axis[2],axis[0]))%360}
            p['new_stock_requirements']={**p.get('new_stock_requirements',{}),'tenon_projection_in':3,'minimum_blank_length_in':length,'quarter_inch_blank_length_in':float(np.ceil((length-1e-7)*4)/4),'status':'Full 2x6 blank enclosing both three-inch tenons; add cutting and dressing allowances'}
            p['cut_status']='LOWER HOUSED / UPPER SQUARE-SEATED THREE-INCH TENON' if pid.endswith('-C') else 'HOUSED THREE-INCH TENON; SQUARED INTERNAL BEARING END'
            p['notes']=['Centered full 2x6 brace stock. Keep the sloping heel and square the bearing end against the internal mortise wall.','Both tongues penetrate three inches; matching housings and bores are cut from the actual receiving members.','Inward brace feet remain eighteen inches lower than the two outer brace feet.']
        if pid in peg_specs:
            spec=peg_specs[pid];axis=np.asarray(spec['withdrawal_world']);points=np.asarray(q['vertices']);center=np.asarray(volume_centroid(shape)['centroid_m']);lo=min(points@axis);hi=max(points@axis)
            p.update(axis_direction=axis.tolist(),axis_start=(center+axis*(lo-center@axis)).tolist(),axis_end=(center+axis*(hi-center@axis)).tolist(),center=center.tolist(),label_position=center.tolist(),withdrawal_direction=axis.tolist(),withdrawal_distance_m=spec['withdrawal_distance_m'],peg_geometry=spec)
            p['dimensions']={**p['dimensions'],'length_m':float(hi-lo),'length_ft':float((hi-lo)/.3048),'length_display':f'{(hi-lo)/I:.3f} in'};p['nominal_dimensions']=copy.deepcopy(p['dimensions'])
    revised['proposed_member_volume_centroids']=[dict(id=p['id'],**volume_centroid(native_solid(p))) for p in revised['parts'] if p.get('is_timber')]
    revised['tenon_schedule']=[j for j in revised['tenon_schedule'] if not j['donor'].startswith('K')]+result['joints']
    revised['main_face_brace_revision']={**revised['main_face_brace_revision'],'revision':REV,'timestamp':STAMP,'family':'Reference-profile housed tenon; squared internal bearing end','brace_specs':result['specs'],'peg_specs':result['peg_specs'],'full_scene_disassembly_verified':False}
    revised['housed_brace_revision']={'revision':REV,'timestamp':STAMP,**result['audit'],'shape':'Broad housed profile with sloping heel and squared internal bearing end','inward_foot_in':44,'outer_foot_in':62,'cross_beam_end':'plain square vertical three-inch gravity-seated tenon'}
    revised['three_inch_joinery_revision'].update(revision=REV,timestamp=STAMP,status='PASS',housed_brace_profile=True,checks=result['audit']['checks'],failures=result['audit']['failures'])
    return revised,result['audit']

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);parser.add_argument('--source-dir',type=Path,default=ROOT/'src');args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True);reports={}
    for filename in FILES:
        revised,audit=candidate(json.loads((args.source_dir/filename).read_text()));(args.output/filename).write_text(json.dumps(revised,separators=(',',':'))+'\n');reports[filename]=audit;print(filename,'PASS',flush=True)
    (args.output/'three-inch-tenon-audit.json').write_text(json.dumps({'revision':REV,'timestamp':STAMP,'variants':reports},separators=(',',':'))+'\n')
# TIMESTAMP END 2026-11-04T19:42:40+00:00 | REVISION R000016
