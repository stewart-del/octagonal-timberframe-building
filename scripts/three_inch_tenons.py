# TIMESTAMP START 2026-11-03T13:59:01-05:00 | REVISION R005033
"""Three-inch shoulder tenons and dimension records, measured from solids."""
from pathlib import Path
import itertools,json
import numpy as np
import manifold3d as m
from step_lap import solid,mesh,original_stock,inside_band,close_bounds
from center_brace_tenons import build as centered_braces,box,rotate,cylinder,I
from revise_main_braces import clean

ROOT=Path(__file__).resolve().parents[1]

def build(model):
    result=centered_braces(model);parts={p['id']:p for p in model['parts']};shapes=dict(result['solids']);joints=list(result['joints']);entries={}
    raw={pid:original_stock(p) for pid,p in parts.items() if p.get('is_timber') and not pid.startswith('K')}
    # Retain the bottom-entry dovetail family, shortening its penetration to
    # three inches. Its transverse peg moves to the new tenon's midpoint.
    if model.get('cupola_foot_revision'):
        c=shapes['C0']+box(np.array([38,85,-3])*I,np.array([44,94,3])*I)
        t=shapes['T0'].trim_by_plane([1,0,0],44*I)
        tail=m.Manifold.hull_points(np.array([[x,y,z] for y in [85,93] for x,z in [(44,-1.5),(44,1.5),(41,1.875),(41,-1.875)]])*I)
        t=t+tail+box(np.array([44,85,-1.5])*I,np.array([44.01,93,1.5])*I)
        peg=cylinder(np.array([42.5,89,0])*I,[0,0,1],-3*I,3*I,.375*I)
        bore=cylinder(np.array([42.5,89,0])*I,[0,0,1],-3*I-.001,3*I+.001,.375*I)
        c=clean(c-tail-bore);t=clean(t-bore)
        for k in range(8):
            shapes[f'C{k}']=c.rotate([0,45*k,0]);shapes[f'T{k}']=t.rotate([0,45*k,0]);shapes[f'CP{k}']=peg.rotate([0,45*k,0])
            joints.append({'id':f'TJ-T{k}-C{k}','donor':f'T{k}','receiver':f'C{k}','shape':'housed dovetail','projection_m':3*I,'width_m':3*I,'head_width_m':3.75*I,'height_m':8*I,'face_center':rotate(np.array([44,89,0])*I,k).tolist(),'insertion_direction':rotate([-1,0,0],k).tolist(),'width_direction':rotate([0,0,1],k).tolist(),'height_direction':[0,1,0],'connector':mesh(tail.rotate([0,45*k,0])),'peg_id':f'CP{k}'})
    # The lower cupola ring shares each post with a principal-rafter tenon.
    # Move its narrower tenons into the upper half of the unchanged ring stock.
    # Rebuild its old sockets from receiver stock after all tongues are defined.
    for k in range(8):
        shapes[f'L{k}-S']=raw[f'L{k}-S']
        shapes[f'L{k}-H']=raw[f'L{k}-H']
        r=rotate([1,0,0],k);shapes[f'R{k}']=shapes[f'R{k}'].trim_by_plane(r.tolist(),44*I)
        for pid,ends in [(f'B{k}',{'A','B'}),(f'T{k}',{'A'} if model.get('cupola_foot_revision') else {'A','B'})]:
            for plane in parts[pid]['geometry_planes_inches']:
                if plane.get('end') not in ends:continue
                n=np.array([plane['normal'][0],plane['normal'][2],-plane['normal'][1]])
                shapes[pid]=shapes[pid].trim_by_plane((-n).tolist(),-plane['constant']*I)
    for k in range(8):
        specs=[(f'T{k}',f'P{k}','A'),(f'B{k}',f'P{k}','A'),(f'B{k}',f'P{(k+1)%8}','B'),(f'R{k}',f'C{k}','B')]
        if not model.get('cupola_foot_revision'):specs.append((f'T{k}',f'C{k}','B'))
        for suffix in ['S','H']:specs.extend([(f'L{k}-{suffix}',f'C{k}','A'),(f'L{k}-{suffix}',f'C{(k+1)%8}','B')])
        for donor,receiver,end in specs:
            p=parts[donor];plane=next(q for q in p['geometry_planes_inches'] if q.get('end')==end)
            n=np.array([plane['normal'][0],plane['normal'][2],-plane['normal'][1]]);face=plane['constant']*I
            vertices=np.array(raw[donor].to_mesh64().vert_properties)[:,:3];points=vertices[abs(vertices@n-face)<1e-7];center=points.mean(0)
            tongue=raw[donor].translate((n*3*I).tolist())^raw[receiver]
            bands=[]
            for key,half in [('width',p['dimensions']['width_in']/6),('depth',max(.5,p['dimensions']['depth_in']/2-1))]:
                axis=np.array(p['stock_frame'][key]);offset=0
                if donor.startswith('L') and donor.endswith('-S') and key=='depth':half=.75;offset=1.25*I
                if donor.startswith('R') and key=='depth':half=3
                low=axis@center+offset-half*I;high=axis@center+offset+half*I
                tongue=inside_band(tongue,axis,low,high);bands.append((axis,low,high))
            points=np.array(tongue.to_mesh64().vert_properties)[:,:3]
            depth=np.ptp(points@n)/I
            assert abs(depth-3)<1e-6,(donor,receiver,'truncated tenon',depth)
            tool=m.Manifold.hull_points(np.vstack([points,points-n*.0001]))
            for axis,low,high in bands:tool=inside_band(tool,axis,low,high)
            cutter=tool
            if donor.startswith('B'):
                # Owner-approved open-top post mortises let the ring lift
                # vertically off the centered brace heads after roof removal.
                vv=np.array(tool.to_mesh64().vert_properties)[:,:3]
                cutter=m.Manifold.hull_points(np.vstack([vv,vv+[0,.4,0]]))
                entries[receiver]=entries.get(receiver,m.Manifold())+(cutter-tool)
            shapes[donor]=shapes[donor]+tool;shapes[receiver]=shapes[receiver]-cutter
            w=np.array(p['stock_frame']['width']);d=np.array(p['stock_frame']['depth'])
            joints.append({'id':f'TJ-{donor}-{receiver}','donor':donor,'receiver':receiver,'end':end,'shape':'shouldered tenon','projection_m':3*I,'width_m':float(np.ptp(points@w)),'height_m':float(np.ptp(points@d)),'face_center':center.tolist(),'insertion_direction':n.tolist(),'width_direction':w.tolist(),'height_direction':d.tolist(),'connector':mesh(tongue)})
            joints[-1]['cutting_tool']=mesh(tool)
    for k in range(8):
        pid=f'C{k}';receiver=raw[pid]
        for joint in joints:
            if joint['receiver']!=pid:continue
            tongue=solid(joint.get('cutting_tool',joint['connector']))
            receiver=receiver-tongue
        if f'CP{k}' in shapes:
            peg=shapes[f'CP{k}'];axis=rotate([0,0,1],k)
            receiver=receiver-(peg+peg.translate((axis*.001).tolist())+peg.translate((-axis*.001).tolist()))
        shapes[pid]=receiver
    # TIMESTAMP START 2026-11-03T16:00:30-05:00 | REVISION R005047
    # Recut the main post from its raw blank using the current physical members.
    # This removes obsolete slivers around the shorter, earlier ring tenons.
    for k in range(8):
        pid=f'P{k}';receiver=raw[pid]
        for joint in joints:
            if joint['receiver']==pid:receiver=receiver-solid(joint.get('cutting_tool',joint['connector']))
        for other,shape in shapes.items():
            if not close_bounds(receiver,shape):continue
            if other.startswith('MAIN-PEG-'):
                spec=next(q for q in result['peg_specs'] if q['id']==other)
                axis=np.array(spec['withdrawal_world']);vv=np.array(shape.to_mesh64().vert_properties)[:,:3]
                shape=cylinder(spec['bore_center_world'],axis,min(vv@axis)-.001,max(vv@axis)+.001,.25*I)
                receiver=receiver-shape
            elif other.startswith('R') and (receiver^shape).volume()>1e-12:receiver=receiver-shape
        receiver=receiver-entries.get(pid,m.Manifold())
        shapes[pid]=receiver
    # TIMESTAMP END 2026-11-03T16:00:30-05:00 | REVISION R005047
    failures=[];checks=0
    for (a,sa),(b,sb) in itertools.combinations(shapes.items(),2):
        if not close_bounds(sa,sb):continue
        amount=(sa^sb).volume()/I**3;checks+=1
        if amount>1e-6:failures.append({'pair':[a,b],'overlap_in3':amount})
    result.update(solids=shapes,joints=joints,entry_regions=entries)
    result['audit']={'status':'FAIL' if failures else 'PASS','checks':checks,'failures':failures,'tenon_count':len(joints),'projection_in':3,'capacity_verified':False}
    return result

if __name__=='__main__':
    result=build(json.loads((ROOT/'src/top-entry-proposed-model.json').read_text()));print(json.dumps(result['audit']),flush=True)
    assert result['audit']['status']=='PASS'
# TIMESTAMP END 2026-11-03T13:59:01-05:00 | REVISION R005033
