# TIMESTAMP START 2026-11-05T04:51:00+00:00 | REVISION R000023
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
    # TIMESTAMP START 2026-11-05T08:15:49+00:00 | REVISION R000034
    record=part.get('declared_exterior_cut')
    pieces=[unpack(record)] if record else []
    pieces.extend(unpack(p) for p in part.get('additional_declared_exterior_cuts',{}).get('pieces',[]))
    return union(pieces)
    # TIMESTAMP END 2026-11-05T08:15:49+00:00 | REVISION R000034

def sources():
    names=['src/top-entry-proposed-model.json','src/top-entry-proposal.json',
           'scripts/export_top_entry_cavities.py','scripts/revise_main_braces.py',
           'scripts/revise_face_braces.py','scripts/prototype_main_brace_faces.py',
           'scripts/cupola_foot.py','scripts/top_entry_heads.py',
           'scripts/audit_cavity_fit.py','scripts/step_lap.py']
    return {name:digest(ROOT/name) for name in names}

# TIMESTAMP START 2026-11-05T15:30:01+00:00 | REVISION R000049
def entry_regions(proposal,model=None):
    cutters=[solid(x['top_open_cutter'])-solid(x['proposed_nose']) for x in proposal['representative']['interfaces']]
    seed=union(cutters);regions={f'R{k}':seed.rotate((0,45*k,0)) for k in range(8)}
    # Later source joints explicitly declare post, cupola and outer-rafter
    # entry cuts. Retain the original inner-rafter proposal too; neither set
    # may disappear merely because its receiver also has another entry cut.
    for pid,record in (model or {}).get('joinery_entry_regions',{}).items():
        declared=unpack(record)
        assert str(declared.status())=='Error.NoError',('Invalid declared source entry',pid)
        regions[pid]=union([regions[pid],declared]) if pid in regions else declared
    if (model or {}).get('three_inch_joinery_revision'):
        # The hip foot shares its named post's open assembly slot. The source
        # post entry also classifies the small clearance cut in that hip; it
        # is not mating wood or an unexplained exterior stock subtraction.
        for k in range(8):
            pid='R'+str(k);related=[regions[key] for key in ['P'+str(k),'C'+str(k)] if key in regions]
            if related:regions[pid]=union([regions.get(pid,m.Manifold()),*related])
    return regions
# TIMESTAMP END 2026-11-05T15:30:01+00:00 | REVISION R000049

# TIMESTAMP START 2026-11-05T06:03:29+00:00 | REVISION R000025
def hub_record(model, physical):
    """Partition the actual hub using complete tools before clipping once.

    Unioning separately clipped, coplanar mating fragments creates invalid
    cancellation surfaces. The connector tools are unbored; actual donor wood
    and its peg jointly fill each tool. audit() checks that equality from the
    saved physical triangles, independently of this construction.
    """
    parts={p['id']:p for p in model['parts']};hub=parts['CUP-KINGPOST']
    origin=np.asarray(hub['center'],float)
    local=lambda s:s.translate((-origin).tolist())
    world=lambda s:s.translate(origin.tolist())
    bottom=hub['axis_start'][1]-origin[1];top=hub['axis_end'][1]-origin[1]
    def box(lo,hi):
        lo=np.asarray(lo,float)
        return m.Manifold.cube((np.asarray(hi)-lo).tolist()).translate(lo.tolist())
    envelope=box([-6*I,bottom,-6*I],[6*I,top,6*I])
    for k in range(8):
        angle=k*np.pi/4;radial=np.array([np.cos(angle),0,-np.sin(angle)])
        envelope=envelope.trim_by_plane((-radial).tolist(),-6*I)
    joints=[j for j in model['tenon_schedule'] if j['receiver']=='CUP-KINGPOST']
    assert len(joints)==16 and {j['donor'] for j in joints}=={f'{prefix}{k}' for prefix in ['CC','CR'] for k in range(8)}
    pegs=[local(physical[p['id']]) for p in model['parts'] if p.get('peg_geometry',{}).get('receiver')=='CUP-KINGPOST']
    assert len(pegs)==16,'Every hub socket must retain its real transverse peg'
    tools=[local(solid(j['cutting_tool'])) for j in joints]
    entry=local(solid(model['joinery_entry_regions']['CUP-KINGPOST']))
    cy=parts['CC0']['center'][1]-origin[1]
    roofcy=next(j for j in joints if j['donor']=='CR0')['face_center'][1]-origin[1]
    access=[]
    for k in range(8):
        access.append(box([3*I,bottom,-.5*I],[6*I,cy-2*I,.5*I]).rotate((0,45*k,0)))
        access.append(box([3*I,roofcy+1.5*I,-.5*I],[6*I,top,.5*I]).rotate((0,45*k,0)))
    expected=envelope-union([entry,*pegs]);own=local(physical['CUP-KINGPOST'])
    assert volume(expected-own)+volume(own-expected)<=TOL,'Hub no longer matches the recorded socket/peg recipe'
    return {'removed':packed(world(union([entry,*pegs])^envelope)),
        'mating_pocket':packed(world(union([*tools,*pegs])^envelope)),
        'entry_clearance':packed(world(union(access))),
        'blank_offcuts':packed(declared_offcuts(hub)),
        'stock_basis':'Actual 12-inch-across-flats octagon in recorded 12x12 stock; complete connector and peg tools clipped once. Explicit shoulder-plane entry prisms; saved physical mates independently audited.',
        'roundoff_omission_limit_m3':ROUND_OFF,'mating_clip_roundoff_omitted_m3':0.}
# TIMESTAMP END 2026-11-05T06:03:29+00:00 | REVISION R000025

# TIMESTAMP START 2026-11-04T20:04:39+00:00 | REVISION R000018
def generate(model=None,proposal=None,unchanged_seeds=None):
# TIMESTAMP END 2026-11-04T20:04:39+00:00 | REVISION R000018
    model=model or read(ROOT/'src/top-entry-proposed-model.json')
    proposal=proposal or read(ROOT/'src/top-entry-proposal.json')
    timbers={p['id']:p for p in model['parts'] if p['is_timber']}
    physical={p['id']:solid(p) for p in model['parts'] if p['is_timber'] or p.get('is_fastener') or p.get('group')=='joinery_pegs'}
    # TIMESTAMP START 2026-11-05T15:30:01+00:00 | REVISION R000049
    entries=entry_regions(proposal,model);records={};seeds={}
# TIMESTAMP END 2026-11-05T15:30:01+00:00 | REVISION R000049
    def transform_record(record,matrix):
        result=copy.deepcopy(record)
        for key in ['removed','mating_pocket','entry_clearance','blank_offcuts']:
            item=result[key]
            item['vertices']=[(matrix@np.asarray(v)).tolist() for v in item['vertices']]
            if np.linalg.det(matrix)<0:item['triangles']=[list(reversed(t)) for t in item['triangles']]
        return result
    def seed(pid):
        if pid in seeds:return seeds[pid]
        # TIMESTAMP START 2026-11-05T06:03:29+00:00 | REVISION R000025
        if pid=='CUP-KINGPOST':
            seeds[pid]=hub_record(model,physical)
            return seeds[pid]
        # TIMESTAMP END 2026-11-05T06:03:29+00:00 | REVISION R000025
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
        # TIMESTAMP START 2026-11-05T06:03:29+00:00 | REVISION R000025
        # Opposite socket peg elevations alternate around the cupola. Reuse a
        # rotation only after testing actual wood, stock, offcuts and entries;
        # every resulting saved pocket is still audited against current mates.
        if pid=='CUP-KINGPOST' or re.fullmatch(r'(?:C[0-7]|CC[0-7]|CR[0-7]|L[0-7]-[HS])',pid):
            match=re.fullmatch(r'([A-Z]+)([0-7])(.*)',pid)
            if match:
                for previous in list(seeds):
                    before=re.fullmatch(r'([A-Z]+)([0-7])(.*)',previous)
                    if not before or (before[1],before[3])!=(match[1],match[3]):continue
                    degrees=45*(int(match[2])-int(before[2]));angle=degrees*np.pi/180;c,s=np.cos(angle),np.sin(angle)
                    matrix=np.array([[c,0,s],[0,1,0],[-s,0,c]])
                    pairs=[(physical[previous],physical[pid]),(stock(timbers[previous]),stock(p)),
                        (declared_offcuts(timbers[previous]),declared_offcuts(p)),
                        (entries.get(previous,m.Manifold()),entries.get(pid,m.Manifold()))]
                    errors=[volume(a.rotate((0,degrees,0))-b)+volume(b-a.rotate((0,degrees,0))) for a,b in pairs]
                    if max(errors)<=TOL:
                        records[pid]=transform_record(seeds[previous],matrix)
                        records[pid]['verified_geometry_isometry']={'seed_id':previous,'rotation_degrees':degrees,'wood_stock_offcut_entry_difference_m3':errors}
                        break
                if pid in records:continue
            records[pid]=copy.deepcopy(seed(pid))
            continue
        # TIMESTAMP END 2026-11-05T06:03:29+00:00 | REVISION R000025
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
    physical={p['id']:solid(p) for p in model['parts'] if p['is_timber'] or p.get('is_fastener') or p.get('group')=='joinery_pegs'}
    # TIMESTAMP START 2026-11-05T15:30:01+00:00 | REVISION R000049
    entries=entry_regions(proposal,model);rows=[];failures=[]
# TIMESTAMP END 2026-11-05T15:30:01+00:00 | REVISION R000049
    if set(cavities['parts'])!=set(timbers):failures.append('Cavity IDs do not match structural timber IDs')
    for pid,p in timbers.items():
        data=cavities['parts'].get(pid)
        if data is None:continue
        # TIMESTAMP START 2026-11-05T06:03:29+00:00 | REVISION R000025
        # Perform occupied-volume Booleans near the receiving stock origin.
        # This is an isometry, not a mesh cleanup, offset or tolerance change.
        # Raw JSON boundary/winding checks below continue in world coordinates.
        blank=stock(p);origin=np.asarray(blank.bounding_box()).reshape(2,3).mean(0)
        match=re.fullmatch(r'([A-Z]+)([0-7])(.*)',pid);degrees=-45*int(match[2]) if match else 0
        local=lambda s:s.translate((-origin).tolist()).rotate((0,degrees,0))
        mate_shapes={key:s for key,s in physical.items() if key!=pid and close_bounds(blank,s)}
        shapes={key:local(unpack(data[key])) for key in ['removed','mating_pocket','entry_clearance','blank_offcuts']}
        blank=local(blank);legacy=local(stock(p,False));own=local(physical[pid]);declared=local(declared_offcuts(p))
        mates=union([local(s) for s in mate_shapes.values()]);all_removed=shapes['removed']+shapes['blank_offcuts']
        # TIMESTAMP END 2026-11-05T06:03:29+00:00 | REVISION R000025
        checks={
            'overlay_partition_difference':volume(shapes['removed']-(shapes['mating_pocket']+shapes['entry_clearance']))+volume((shapes['mating_pocket']+shapes['entry_clearance'])-shapes['removed']),
            'pocket_entry_overlap':volume(shapes['mating_pocket']^shapes['entry_clearance']),
            'overlay_offcut_overlap':volume(shapes['removed']^shapes['blank_offcuts']),
            'pocket_without_mate':volume(shapes['mating_pocket']-mates),
            'mate_pocket_omitted':volume(((blank-own)^mates)-declared-shapes['mating_pocket']),
            'receiver_overlap':volume(all_removed^own),
            'outside_stock':volume(all_removed-blank),
            'unrecorded_removed_stock':volume(blank-(own+all_removed)),
            # TIMESTAMP START 2026-11-05T06:03:29+00:00 | REVISION R000025
            'entry_outside_declared_region':volume(shapes['entry_clearance']-local(entries.get(pid,m.Manifold()))),
            # TIMESTAMP END 2026-11-05T06:03:29+00:00 | REVISION R000025
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
        # TIMESTAMP START 2026-11-05T06:03:29+00:00 | REVISION R000025
        for component in unpack(data['mating_pocket']).decompose():
        # TIMESTAMP END 2026-11-05T06:03:29+00:00 | REVISION R000025
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

# TIMESTAMP END 2026-11-05T04:51:00+00:00 | REVISION R000023
