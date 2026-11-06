# TIMESTAMP START 2026-11-05T04:51:00+00:00 | REVISION R000023
"""Rebuild cupola geometry from frozen inputs, preserving unrelated live parts.

Primary static and bounded joint motions are checked here. Full architecture,
stock/cavity classification, parameter regeneration and the complete erection
route are separately required before publication.
"""
from pathlib import Path
import argparse,copy,gzip,hashlib,json
from cupola_joinery_recipe import prototype
from cupola_bridge_recipe import generate as bridge
# TIMESTAMP START 2026-11-05T06:23:51+00:00 | REVISION R000028
from cupola_raise_recipe import transform as raise_upper
# TIMESTAMP END 2026-11-05T06:23:51+00:00 | REVISION R000028

ROOT=Path(__file__).resolve().parents[1]
FILES={'baseline':'model-data.json','proposed':'step-lap-proposed-model.json','top-entry':'top-entry-proposed-model.json'}
STAMP={'revision':'R000023','timestamp':'2026-11-05T04:51:00+00:00'}
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path):return json.loads(path.read_text())
def readable(value,level=0):
    pad='  '*level;child='  '*(level+1)
    if isinstance(value,dict):return '{\n'+',\n'.join(child+json.dumps(k)+': '+readable(v,level+1) for k,v in value.items())+'\n'+pad+'}' if value else '{}'
    if isinstance(value,list):
        if not value or all(not isinstance(v,(dict,list)) for v in value):return json.dumps(value,separators=(',',':'))
        return '[\n'+',\n'.join(child+readable(v,level+1) for v in value)+'\n'+pad+']'
    return json.dumps(value)
def save(path,value):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(readable(value)+'\n')
def production_part(part):
    result=copy.deepcopy(part);result.pop('research_only',None)
    if result.get('new_stock_requirements'):result['new_stock_requirements']['status']='Measured minimum blank envelope; add cutting and dressing allowance. Connection capacity is unverified.'
    if result['id']=='CUP-KINGPOST':result['dimensions']['status']='Proposed12-inch-across-flats octagon dressed from12x12stock; measured vertical blank length.'
    if result['id'].startswith('M-TMP-SCREW-'):
        result.update(parentId='M-TMP',showWithTemporaryConnector=True)
        spec=result['screw_geometry']
        result['fastenerSpec']={'manufacturer':'GRK','partNumber':'14221 / RSS5/16x3-1/8','lengthIn':3.12,'majorDiameterIn':.276,'headDiameterIn':.620,'drive':'T30','material':'Climatek-coated case-hardened steel','installation':'One per3/8-inch steel clearance hole. Custom steel-to-wood connection capacity requires design; ESR2442wood-to-wood listing is not a steel-connection rating.','sourceURL':spec['manufacturer_drawing']}
        result['receiverIds']=[spec['receiver'],'M-TMP']
    if result['id']=='M-TMP':
        result.update(name='Welded eight-L cupola-post / cross-beam bridge',geometry_purpose='Custom bridge with eight bearing returns and forty actual screw holes; structural and welding capacity unverified.')
        # TIMESTAMP START 2026-11-05T06:23:51+00:00 | REVISION R000028
        for key in ['dimensions','nominal_dimensions']:result[key]['length_ft']=result[key]['length_m']/.3048
        result.update(axis_start=[-47*.0254,109*.0254,0],axis_end=[47*.0254,109*.0254,0],axis_direction=[1,0,0],fitted_axial_extent_inches=94)
        result['stock_frame']={'axis':[1,0,0],'width':[0,0,1],'depth':[0,1,0]}
        result['provenance']='Original owner 90-inch star reference; revised 94-inch overall bridge spans both cupola posts and cross-beams as requested. Forty modeled temporary screw holes.'
        result['display_assumptions']['rigid_rotation_y_degrees']=0
        result['dimension_status']={'overall_span_in':'Actual proposed 94-inch bridge envelope; original 90-inch reference superseded to overlap both members.',
            'bridge_plate_vertical_span_in':'85 to109in in the saved assembly; 24in total.',
            'hole_centers_m':'Actual modeled centers; custom steel connection edge distances, welds and load rating require design.',
            'steel_thickness_in':'Proposed1/8-inch steel; stock/weld design unqualified.'}
        # TIMESTAMP END 2026-11-05T06:23:51+00:00 | REVISION R000028
    return result
def rebuild(output,apply=False):
    frozen_path=ROOT/'scripts/fixtures/cupola-inputs.json.gz'
    frozen=json.loads(gzip.decompress(frozen_path.read_bytes()))
    pending={};stock={};reports={}
    for variant,name in FILES.items():
        folder=output/variant;folder.mkdir(parents=True,exist_ok=True)
        record=frozen['files'][name];source=folder/'frozen-input.json';source.write_text(record['content'])
        assert sha(source)==record['sha256'],'Frozen cupola input changed'
        # TIMESTAMP START 2026-11-05T06:23:51+00:00 | REVISION R000028
        original=read(source)
        baseline=json.loads(frozen['files']['model-data.json']['content'])
        raised,raise_report=raise_upper(original,baseline,record['sha256'])
        raised_source=folder/'raised-frozen-input.json';save(raised_source,raised)
        prototype(raised_source,folder)
        # TIMESTAMP END 2026-11-05T06:23:51+00:00 | REVISION R000028
        patch=read(folder/'cupola-candidate-patch.json');report=read(folder/'cupola-candidate-report.json')
        assert report['static_primary_pair_audit']['status']=='PASS',report['static_primary_pair_audit']['collisions']
        assert all(p['proof']['status']=='PASS' for p in report['local_probes'])
        replacements=patch['replace_parts'];new_parts=patch['add_parts']
        timber_model={**original,'parts':[replacements.get(p['id'],p) for p in original['parts']]+list(new_parts.values()),'tenon_schedule':patch['tenon_schedule'],'joinery_entry_regions':patch['joinery_entry_regions']}
        bridge_input=folder/'timber-before-bridge.json';save(bridge_input,timber_model)
        bridge_folder=folder/'bridge';bridge_folder.mkdir(exist_ok=True);bridge(bridge_input,bridge_folder)
        bridge_patch=read(bridge_folder/'bridge-candidate-patch.json');bridge_report=read(bridge_folder/'bridge-candidate-report.json')
        assert bridge_report['static_primary']['status']=='PASS'
        assert bridge_report['screw_count']==40 and all(p['proof']['status']=='PASS' for p in bridge_report['screw_initial_withdrawals'])
        assert bridge_report['fixture_up_after_screw_prerequisite']['status']=='PASS'
        assert bridge_report['fixture_down_with_screws_removed']['status']=='BLOCKED'
        combined={**replacements,**new_parts,**bridge_patch['replace_parts'],**bridge_patch['add_parts']}
        current=read(ROOT/'src'/name);current_ids={p['id'] for p in current['parts']}
        model=copy.deepcopy(current);model['parts']=[production_part(combined[p['id']]) if p['id'] in combined else copy.deepcopy(p) for p in current['parts']]+[production_part(p) for pid,p in combined.items() if pid not in current_ids]
        old_joints={j['id']:j for j in original['tenon_schedule']}
        changed_joints={j['id']:j for j in patch['tenon_schedule'] if j['id'] not in old_joints or j!=old_joints[j['id']]}
        model['tenon_schedule']=[changed_joints.pop(j['id'],j) for j in current['tenon_schedule']]+list(changed_joints.values())
        # TIMESTAMP START 2026-11-05T06:23:51+00:00 | REVISION R000028
        model['joinery_entry_regions']={**{pid:value for pid,value in model.get('joinery_entry_regions',{}).items() if pid not in {f'L{k}-S' for k in range(8)}},**patch['joinery_entry_regions']}
        model['upper_cupola_raise']={'revision':'R000028','timestamp':'2026-11-05T06:23:51+00:00','rise_in':10,
            'reason':'Provide roof flashing upturn and real AAN1814 window clearance; retain all lower truss seats and the forty-screw bridge.',
            'backed_common_plane_pan_clearance_in':13.398792377510,'required_membrane_upturn_in':12,'capacity_verified':False}
        # TIMESTAMP END 2026-11-05T06:23:51+00:00 | REVISION R000028
        model['cupola_joinery_revision']={**STAMP,'status':'PRIMARY STATIC AND LOCAL MOTION CHECKED','input_sha256':record['sha256'],'stock_and_cavity_audit':'Separate fresh audit required','capacity_verified':False}
        model['bridge_holes']=bridge_patch.get('holes',bridge_report.get('holes',[]))
        ids=[p['id'] for p in model['parts']];assert len(ids)==len(set(ids))
        assert sum(p.get('is_timber',False) for p in model['parts'])==113
        pending[name]=model;stock[variant]=read(folder/'cupola-stock-envelopes.json')
        # TIMESTAMP START 2026-11-05T06:23:51+00:00 | REVISION R000028
        reports[variant]={'upper_raise':raise_report,'timber':report,'bridge':bridge_report}
        # TIMESTAMP END 2026-11-05T06:23:51+00:00 | REVISION R000028
        save(folder/name,model)
    if apply:
        for name,model in pending.items():save(ROOT/'src'/name,model)
        save(ROOT/'src/cupola-stock-envelopes.json',{**STAMP,'variants':stock})
        # TIMESTAMP START 2026-11-05T06:23:51+00:00 | REVISION R000028
        sources={str(path.relative_to(ROOT)):sha(path) for path in [frozen_path,Path(__file__),ROOT/'scripts/cupola_joinery_recipe.py',ROOT/'scripts/cupola_bridge_recipe.py',ROOT/'scripts/cupola_raise_recipe.py']}
        # TIMESTAMP END 2026-11-05T06:23:51+00:00 | REVISION R000028
        save(ROOT/'docs/cupola-joinery-audit.json',{**STAMP,'status':'PASS','scope':'Primary occupied geometry and bounded local joint motions only; full-building motion, final cavity audit and structural capacity are separate.','sources':sources,'models':{name:sha(ROOT/'src'/name) for name in pending},'variants':reports,'capacity_verified':False})
    return pending
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=ROOT/'.codex-runtime/cupola-rebuild');parser.add_argument('--apply',action='store_true');args=parser.parse_args();rebuild(args.output,args.apply)
# TIMESTAMP END 2026-11-05T04:51:00+00:00 | REVISION R000023
