# TIMESTAMP START 2026-11-04T23:23:25+00:00 | REVISION R000011
# TIMESTAMP START 2026-11-02T20:42:47-05:00 | REVISION R004871
# Restore the original six-inch cupola and remove the R004869 four-inch trial.
# TIMESTAMP START 2026-11-02T17:13:18-05:00 | REVISION R004819
"""Export actual pockets, explicit head-entry space and separate blank offcuts.

The displayed void is derived from recorded stock minus the finished timber.
Pegs count as physical mating wood, not as additional structural timbers.
"""
from pathlib import Path
import argparse, copy, hashlib, json, re
import numpy as np
import manifold3d as m
from step_lap import solid, close_bounds, regular_boundary, mesh
from audit_cavity_fit import reference_stock, inspect_mesh, arrays, winding
from revise_main_braces import exported, clean

ROOT=Path(__file__).resolve().parents[1]
I=.0254
TOL=1e-6*I**3
ROUND_OFF=1e-9*I**3
EMPTY={'vertices':[],'triangles':[],'edges':[],'volume_m3':0.}

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path):return json.loads(path.read_text())
def volume(shape):return max(0.,float(shape.volume()))
def stock(part,proposed=True):
    record=copy.deepcopy(part)
    # R's extra two-inch blank allowance contains its unchanged projecting
    # tenon and exterior end dressing. Its recess envelope remains the same
    # legacy body used by the independently audited perimeter model.
    # TIMESTAMP START 2026-11-03T15:46:44-05:00 | REVISION R005039
    if proposed and (not part['id'].startswith('R') or part.get('new_stock_requirements',{}).get('tenon_projection_in')==3) and record.get('proposed_stock_planes_inches'):
    # TIMESTAMP END 2026-11-03T15:46:44-05:00 | REVISION R005039
        record['geometry_planes_inches']=record['proposed_stock_planes_inches']
    v,f=reference_stock(record,apply_declared_trim=True)
    return m.Manifold(m.Mesh64(v,f))
def union(shapes):return m.Manifold.batch_boolean(shapes,m.OpType.Add) if shapes else m.Manifold()
def packed(shape):
    if shape.is_empty() or abs(shape.volume())<=ROUND_OFF:return copy.deepcopy(EMPTY)
    candidate=shape
    result=mesh(candidate)
    if inspect_mesh(*arrays(result))['status']!='PASS':
        candidate=regular_boundary(candidate)
        assert volume(shape-candidate)+volume(candidate-shape)<=TOL,'Boundary cleanup changed occupied volume'
        result=mesh(candidate)
    assert inspect_mesh(*arrays(result))['status']=='PASS','Invalid exported cavity boundary'
    result['edges']=[list(edge) for edge in sorted({tuple(sorted((t[k],t[(k+1)%3]))) for t in result['triangles'] for k in range(3)})]
    return result
def unpack(record):return solid(record) if record['triangles'] else m.Manifold()
def declared_offcuts(part):
    record=part.get('declared_exterior_cut')
    return unpack(record) if record else m.Manifold()

def sources():
    names=['src/top-entry-proposed-model.json','src/top-entry-proposal.json',
           'scripts/export_top_entry_cavities.py','scripts/revise_main_braces.py',
           'scripts/revise_face_braces.py','scripts/prototype_main_brace_faces.py',
           'scripts/cupola_foot.py','scripts/top_entry_heads.py',
           'scripts/audit_cavity_fit.py','scripts/step_lap.py']
    return {name:digest(ROOT/name) for name in names}

def entry_regions(proposal):
    cutters=[solid(x['top_open_cutter'])-solid(x['proposed_nose']) for x in proposal['representative']['interfaces']]
    seed=union(cutters)
    return {f'R{k}':seed.rotate((0,45*k,0)) for k in range(8)}

# TIMESTAMP START 2026-11-04T20:04:39+00:00 | REVISION R000018
def generate(model=None,proposal=None,unchanged_seeds=None):
# TIMESTAMP END 2026-11-04T20:04:39+00:00 | REVISION R000018
    model=model or read(ROOT/'src/top-entry-proposed-model.json')
    proposal=proposal or read(ROOT/'src/top-entry-proposal.json')
    timbers={p['id']:p for p in model['parts'] if p['is_timber']}
    physical={p['id']:solid(p) for p in model['parts'] if p['is_timber'] or p.get('group')=='joinery_pegs'}
    entries=entry_regions(proposal);records={};seeds={}
    def transform_record(record,matrix):
        result=copy.deepcopy(record)
        for key in ['removed','mating_pocket','entry_clearance','blank_offcuts']:
            item=result[key]
            item['vertices']=[(matrix@np.asarray(v)).tolist() for v in item['vertices']]
            if np.linalg.det(matrix)<0:item['triangles']=[list(reversed(t)) for t in item['triangles']]
        return result
    def seed(pid):
        if pid in seeds:return seeds[pid]
        # TIMESTAMP START 2026-11-04T20:04:39+00:00 | REVISION R000018
        retained=(unchanged_seeds or {}).get(pid)
        if retained:
            fingerprint=hashlib.sha256(json.dumps(timbers[pid],sort_keys=True,separators=(',',':')).encode()).hexdigest()
            if fingerprint==retained['part_sha256']:
                # This is input mesh geometry, never a reused verification.
                # audit() below still checks every pocket against current mates.
                seeds[pid]=copy.deepcopy(retained['record'])
                print('Retain exact unchanged cavity geometry',pid,flush=True)
                return seeds[pid]
        # TIMESTAMP END 2026-11-04T20:04:39+00:00 | REVISION R000018
        if pid=='J0-2':
            diagonal=np.sqrt(.5);reflection=np.array([[diagonal,0,-diagonal],[0,1,0],[-diagonal,0,-diagonal]])
            seeds[pid]=transform_record(seed('J0-0'),reflection)
            return seeds[pid]
        # TIMESTAMP START 2026-11-03T15:58:36-05:00 | REVISION R005044
        if model.get('three_inch_joinery_revision'):print('audit cavity',pid,flush=True)
        # TIMESTAMP END 2026-11-03T15:58:36-05:00 | REVISION R005044
        # TIMESTAMP START 2026-11-03T16:12:39-05:00 | REVISION R005050
        p=timbers[pid];blank=stock(p);legacy=stock(p,False);own=physical[pid]
        mate_shapes=[shape for key,shape in physical.items() if key!=pid and close_bounds(blank,shape)]
        origin=np.array(blank.bounding_box()).reshape(2,3).mean(0) if model.get('three_inch_joinery_revision') and pid.startswith('P') else np.zeros(3)
        local=lambda shape:shape.translate((-origin).tolist())
        world=lambda shape:shape.translate(origin.tolist())
        blank=local(blank);legacy=local(legacy);own=local(own);mate_shapes=[local(shape) for shape in mate_shapes]
        declared=local(declared_offcuts(p));removed=blank-own;envelope=blank-declared
        if model.get('three_inch_joinery_revision') and not pid.startswith(('B','J')):
            from fit_wall_joinery import clip_to_convex
            joints=[j for j in model['tenon_schedule'] if j['receiver']==pid];donors={j['donor'] for j in joints}
            shapes=[local(shape) for key,shape in physical.items() if key!=pid and key not in donors and close_bounds(stock(p),shape)]
            shapes.extend(local(solid(j.get('cutting_tool',j['connector']))) for j in joints)
            clips=[]
            for shape in shapes:
                clip=clip_to_convex(shape,legacy if pid.startswith('R') else blank)
                if volume(clip)>ROUND_OFF and volume(clip^declared)>ROUND_OFF:clip=clip-declared
                if volume(clip)>ROUND_OFF:clips.append(unpack(packed(clip)))
        # TIMESTAMP START 2026-11-03T16:49:21-05:00 | REVISION R005060
        else:clips=[envelope^shape for shape in mate_shapes]
        clip_budget=TOL/max(100,len(clips)*100)
        omitted=sum(volume(clip) for clip in clips if volume(clip)<=clip_budget)
        assert omitted<=TOL/100
        filled=union([clip for clip in clips if volume(clip)>clip_budget])
        # TIMESTAMP END 2026-11-03T16:49:21-05:00 | REVISION R005060
        access=(local(entries.get(pid,m.Manifold()))^removed)-filled-declared
        # TIMESTAMP START 2026-11-03T16:49:21-05:00 | REVISION R005060
        exterior=declared if model.get('three_inch_joinery_revision') else declared+((removed-filled-access)^(blank-legacy))
        # TIMESTAMP END 2026-11-03T16:49:21-05:00 | REVISION R005060
        unexplained=removed-filled-access-exterior
        assert volume(unexplained)<=TOL,(pid,'unclassified removed stock',volume(unexplained)/I**3)
        # TIMESTAMP START 2026-11-04T20:18:13+00:00 | REVISION R000008
        if model.get('independent_hip_entry_revision') and re.fullmatch(r'C[0-7]',pid):
            joint=next(j for j in model['tenon_schedule'] if j['donor']=='R'+pid[1:] and j['receiver']==pid)
            depth=np.asarray(timbers[joint['donor']]['stock_frame']['depth'])
            top=float(np.max(np.asarray(joint['connector']['vertices'])@depth)-origin@depth)
            clean_access=local(entries[pid]).trim_by_plane(depth.tolist(),top)
            error=volume(access-clean_access)+volume(clean_access-access)
            assert error<=TOL,(pid,'support-plane entry differs from occupied-stock partition',error)
            access=clean_access
        # Direct stock complement avoids zero-thickness coplanar flaps from
        # re-unioning independently computed pocket and access boundaries.
        overlay=(removed-exterior) if model.get('independent_hip_entry_revision') and re.fullmatch(r'C[0-7]',pid) else filled+access
        seeds[pid]={'removed':packed(world(overlay)),'mating_pocket':packed(world(filled)),
        # TIMESTAMP END 2026-11-04T20:18:13+00:00 | REVISION R000008
            'entry_clearance':packed(world(access)),'blank_offcuts':packed(world(exterior)),
            'stock_basis':'Recorded stock halfspaces with separate declared exterior shoulder offcuts and open assembly-entry regions.',
            'roundoff_omission_limit_m3':ROUND_OFF,'mating_clip_roundoff_omitted_m3':omitted}
        # TIMESTAMP END 2026-11-03T16:12:39-05:00 | REVISION R005050
        return seeds[pid]
    for pid,p in timbers.items():
        match=re.fullmatch(r'([A-Z]+)([0-7])(.*)',pid)
        assert match,pid
        base=match[1]+'0'+match[3];angle=int(match[2])*np.pi/4;c,s=np.cos(angle),np.sin(angle)
        matrix=np.array([[c,0,s],[0,1,0],[-s,0,c]])
        # The audit below checks each exported member independently against its
        # actual final mesh. Exact pattern rotations avoid re-solving identical
        # coplanar cuts eight times with different floating-point roundoff.
        records[pid]=transform_record(seed(base),matrix)
    return {'schema_version':'top-entry-cavities-2','source_model_sha256':digest(ROOT/'src/top-entry-proposed-model.json'),
        'sources':sources(),'available':True,'parts':records,
        'summary':{'complete':True,'part_count':len(records)},
        'status':'Actual mating pockets and separately identified open head-entry clearance. Declared brace shoulders and replacement-blank end offcuts are audited separately.',
        'limitations':'Nominal geometry within explicit numerical tolerances; no fabrication clearance or structural capacity approval.'}

def audit(model,cavities,proposal):
    timbers={p['id']:p for p in model['parts'] if p['is_timber']}
    physical={p['id']:solid(p) for p in model['parts'] if p['is_timber'] or p.get('group')=='joinery_pegs'}
    entries=entry_regions(proposal);rows=[];failures=[]
    if set(cavities['parts'])!=set(timbers):failures.append('Cavity IDs do not match structural timber IDs')
    for pid,p in timbers.items():
        data=cavities['parts'].get(pid)
        if data is None:continue
        shapes={key:unpack(data[key]) for key in ['removed','mating_pocket','entry_clearance','blank_offcuts']}
        blank=stock(p);legacy=stock(p,False);own=physical[pid];declared=declared_offcuts(p)
        mate_shapes={key:s for key,s in physical.items() if key!=pid and close_bounds(blank,s)}
        mates=union(list(mate_shapes.values()));all_removed=shapes['removed']+shapes['blank_offcuts']
        checks={
            'overlay_partition_difference':volume(shapes['removed']-(shapes['mating_pocket']+shapes['entry_clearance']))+volume((shapes['mating_pocket']+shapes['entry_clearance'])-shapes['removed']),
            'pocket_entry_overlap':volume(shapes['mating_pocket']^shapes['entry_clearance']),
            'overlay_offcut_overlap':volume(shapes['removed']^shapes['blank_offcuts']),
            'pocket_without_mate':volume(shapes['mating_pocket']-mates),
            'mate_pocket_omitted':volume(((blank-own)^mates)-declared-shapes['mating_pocket']),
            'receiver_overlap':volume(all_removed^own),
            'outside_stock':volume(all_removed-blank),
            'unrecorded_removed_stock':volume(blank-(own+all_removed)),
            'entry_outside_declared_region':volume(shapes['entry_clearance']-entries.get(pid,m.Manifold())),
            'entry_occupied_by_mate':volume(shapes['entry_clearance']^mates),
            'offcut_inside_legacy_stock_without_declaration':volume((shapes['blank_offcuts']^legacy)-declared),
            'offcut_outside_declared_region':volume(shapes['blank_offcuts']-((blank-legacy)+declared)),
            'declared_exterior_cut_omitted':volume(declared-shapes['blank_offcuts']),
            'offcut_occupied_by_mate_without_declaration':volume((shapes['blank_offcuts']^mates)-declared),
        }
        surfaces={}
        for key,record in [(key,data[key]) for key in shapes]:
            if not record['triangles']:continue
            check=inspect_mesh(*arrays(record));surfaces[key]=check
            if check['status']!='PASS':failures.append(pid+': invalid raw '+key+' surface')
        # An independent winding test reads the exported triangles, rather than
        # the Boolean result used to produce the overlay.
        samples=0;uncovered=0
        for component in shapes['mating_pocket'].decompose():
            if component.volume()<=ROUND_OFF:continue
            q=component.to_mesh64();v=np.asarray(q.vert_properties)[:,:3];f=np.asarray(q.tri_verts)
            tri=v[f];normals=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);length=np.linalg.norm(normals,axis=1)
            points=tri.mean(axis=1)-normals/np.maximum(length[:,None],1e-30)*1e-7
            points=points[winding(points,tri)>.999]
            covered=np.zeros(len(points),dtype=bool)
            for key in mate_shapes:
                mate=next(x for x in model['parts'] if x['id']==key);mv,mf=arrays(mate)
                covered|=winding(points,mv[mf])>.999
            samples+=len(points);uncovered+=int((~covered).sum())
        bad={key:value for key,value in checks.items() if value>TOL}
        if bad or uncovered:failures.append(pid+': pocket/stock coverage failed')
        rows.append({'id':pid,'status':'FAIL' if bad or uncovered or any(x['status']!='PASS' for x in surfaces.values()) else 'PASS',
            'errors_m3':checks,'raw_surfaces':surfaces,'independent_winding_samples':samples,'uncovered_winding_samples':uncovered,
            'mating_pocket_in3':volume(shapes['mating_pocket'])/I**3,'entry_clearance_in3':volume(shapes['entry_clearance'])/I**3,
            'blank_offcuts_in3':volume(shapes['blank_offcuts'])/I**3,'declared_exterior_offcut_in3':volume(declared)/I**3})
    return {'schema_version':'top-entry-cavity-fit-audit-1','status':'FAIL' if failures else 'PASS','failures':failures,
        'model_sha256':digest(ROOT/'src/top-entry-proposed-model.json'),'sources':sources(),
        'tolerances':{'positive_volume_error_m3':TOL,'roundoff_omission_m3':ROUND_OFF,'winding_inset_m':1e-7},
        'summary':{'structural_timbers':len(timbers),'physical_wooden_pegs':sum(bool(p.get('group')=='joinery_pegs') for p in model['parts']),
            'verified_records':sum(r['status']=='PASS' for r in rows),'open_entry_records':sum(r['entry_clearance_in3']>1e-6 for r in rows),
            'explicit_exterior_offcut_records':sum(r['declared_exterior_offcut_in3']>1e-6 for r in rows),
            'uncovered_winding_samples':sum(r['uncovered_winding_samples'] for r in rows)},
        'scope':'Raw exported pockets checked for exact mating occupancy, receiver exclusion and recorded-stock reconstruction. Explicit top-entry access space, declared brace shoulders and added-blank end offcuts remain separately classified. Strength and machining tolerances are not certified.',
        'members':rows}

def export():
    model=read(ROOT/'src/top-entry-proposed-model.json');proposal=read(ROOT/'src/top-entry-proposal.json')
    cavities=generate(model,proposal);report=audit(model,cavities,proposal)
    assert report['status']=='PASS',report['failures']
    path=ROOT/'src/top-entry-proposed-cavities.json'
    path.write_text(json.dumps(cavities,separators=(',',':'))+'\n')
    report['cavity_sha256']=digest(path)
    (ROOT/'docs/top-entry-cavity-fit-audit.json').write_text(json.dumps(report,separators=(',',':'))+'\n')
    print('PASS:',report['summary'],flush=True)
    return cavities,report

if __name__=='__main__':export()
# TIMESTAMP END 2026-11-02T17:13:18-05:00 | REVISION R004819

# TIMESTAMP END 2026-11-02T20:42:47-05:00 | REVISION R004871

# TIMESTAMP END 2026-11-04T23:23:25+00:00 | REVISION R000011
