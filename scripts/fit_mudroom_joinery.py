# TIMESTAMP START 2026-11-02T15:00:19-05:00 | REVISION R004797
"""Generate nominal complementary porch joinery; never edits the original frame.
The same occupied connector solid is added to its donor and removed from its
receiver. Chosen member/joint/peg sizes are proposals, not capacity approval.
"""
from pathlib import Path
import argparse, hashlib, itertools, json, os, shutil, subprocess
import numpy as np
import manifold3d as m

ROOT=Path(__file__).resolve().parents[1]
INCH=.0254
NODE=os.environ.get('NODE') or shutil.which('node')
if not NODE: raise RuntimeError('Set NODE to a Node.js executable')

def generate():
    source=ROOT/'src/mudroom.js'
    model_path=ROOT/'src/model-data.json'
    model=json.loads(model_path.read_text())
    layout=json.loads(subprocess.check_output([NODE,'-e',"process.stdout.write(JSON.stringify(require('./src/mudroom.js').build(require('./src/model-data.json'),{applyJoinery:false})))"],cwd=ROOT))
    origin=np.array(layout['origin']); basis=np.array([layout['tangent'],[0,1,0],layout['outward']])
    world=lambda v: np.asarray(v)@basis+origin
    local=lambda v: (np.asarray(v)-origin)@basis.T
    records={p['id']:p for p in layout['components']}
    def solid(p):
        vertices=np.asarray(p.get('localVertices',local(p['vertices'])))
        q=m.Manifold(m.Mesh64(vertices,np.asarray(p['triangles'],dtype=np.uint64))).set_tolerance(1e-10)
        assert str(q.status())=='Error.NoError' and q.volume()>0,p['id']
        return q
    original={pid:solid(p) for pid,p in records.items()}
    additions={pid:m.Manifold() for pid in records};cuts={pid:m.Manifold() for pid in records}
    joints=[]; pegs={}; extra_members=set();part_joint_ids={pid:[] for pid in records}
    def cube(lo,hi):
        lo=np.asarray(lo);hi=np.asarray(hi)
        assert np.all(hi>lo),(lo,hi)
        return m.Manifold.cube((hi-lo).tolist()).translate(lo.tolist())
    def bounds(pid):
        b=original[pid].bounding_box();return np.array(b[:3]),np.array(b[3:])
    def export(s):
        if s.is_empty():return {'vertices':[],'triangles':[],'volume_m3':0.0}
        mesh=s.to_mesh64();v=world(np.asarray(mesh.vert_properties)[:,:3]);ts=np.asarray(mesh.tri_verts)
        return {'vertices':v.tolist(),'triangles':ts.tolist(),'volume_m3':s.volume()}
    def pair(donor,receiver,axis,direction,widths,housing,tenon_length,peg_diameter=0,peg_offset=None):
        lo,hi=bounds(donor);rlo,rhi=bounds(receiver);cross=[k for k in range(3) if k!=axis]
        face=hi[axis] if direction>0 else lo[axis];center=(lo+hi)/2
        for k in cross:center[k]=(max(lo[k],rlo[k])+min(hi[k],rhi[k]))/2
        center[axis]=face
        cross_lo=lo.copy()-1;cross_hi=hi.copy()+1
        for k,w in zip(cross,widths):cross_lo[k]=center[k]-w/2;cross_hi[k]=center[k]+w/2
        cross_lo[axis]=face-tenon_length-housing-.1;cross_hi[axis]=face+tenon_length+housing+.1
        shift=np.eye(3)[axis]*direction*(housing+tenon_length)
        tenon_tool=original[donor].translate(shift.tolist())^cube(cross_lo,cross_hi)
        tenon=tenon_tool^original[receiver]
        shoulder=m.Manifold();shoulder_tool=m.Manifold()
        if housing:
            shoulder_tool=original[donor].translate((np.eye(3)[axis]*direction*housing).tolist())
            shoulder=shoulder_tool^original[receiver]
        connector=tenon+shoulder
        assert connector.volume()>1e-10,(donor,receiver,'no connector')
        assert len(connector.decompose())==1,(donor,receiver,'disconnected connector')
        assert (connector^cuts[receiver]).volume()<1e-12,(donor,receiver,'intersecting joint sockets')
        # The shared tool continues into donor stock and out through the mortise
        # mouth. Those harmless outside portions avoid coincident CSG end caps;
        # the occupied receiver region remains exactly the connector above.
        additions[donor]=additions[donor]+tenon_tool+shoulder_tool;cuts[receiver]=cuts[receiver]+tenon_tool+shoulder_tool
        jid='PJ-'+str(len(joints)+1).zfill(3)
        for pid in [donor,receiver]:part_joint_ids[pid].append(jid)
        entry={'id':jid,'family':'housed straight mortise and tenon' if housing else 'straight mortise and tenon','donor':donor,'receiver':receiver,'axis_local':axis,'insertion_direction_local':(np.eye(3)[axis]*direction).tolist(),'insertion_direction_world':(np.eye(3)[axis]*direction@basis).tolist(),'housing_depth_m':housing,'tenon_projection_m':tenon_length,'tenon_cross_section_m':widths,'connector':export(connector),'connector_volume_m3':connector.volume(),'peg_id':None,'capacity_status':'Proposed dimensions; capacity, species, shrinkage and fastening design unverified.'}
        if peg_diameter:
            # Bore across the receiver's short cross direction, never along a
            # long beam merely because a railing receiver was a square post.
            peg_axis=min(cross,key=lambda k:rhi[k]-rlo[k])
            c=center.copy();c[axis]=face+direction*(housing+tenon_length/2)
            if peg_offset:c+=np.asarray(peg_offset)
            start=rlo[peg_axis];length=rhi[peg_axis]-start;c[peg_axis]=start
            cyl=m.Manifold.cylinder(length,peg_diameter/2,peg_diameter/2,24)
            if peg_axis==0:cyl=cyl.rotate([0,90,0])
            elif peg_axis==1:cyl=cyl.rotate([-90,0,0])
            cyl=cyl.translate(c.tolist())
            assert (cyl^connector).volume()>1e-10,(jid,'peg misses tenon')
            cuts[donor]=cuts[donor]+cyl;cuts[receiver]=cuts[receiver]+cyl
            peg_id='MUD-PEG-'+jid;pegs[peg_id]=cyl;entry['peg_id']=peg_id;entry['peg_diameter_m']=peg_diameter
        joints.append(entry)
    # Rails use deep shoulders and centered tenons; perpendicular corner joints
    # are vertically staggered in the architectural module before fitting.
    for side in ['L','R']:
        for end,direction in [('BACK',-1),('FRONT',1)]:pair('MUD-GUARD-TOP-'+side,'MUD-POST-'+side+'-'+end,2,direction,[1.5*INCH,1.5*INCH],.25*INCH,INCH,.375*INCH)
        outer='MUD-POST-'+side+'-FRONT';inner='MUD-ENTRY-GUARD-POST-'+side
        for receiver,direction in [(outer,-1 if side=='L' else 1),(inner,1 if side=='L' else -1)]:pair('MUD-FRONT-GUARD-'+side,receiver,0,direction,[1.5*INCH,1.5*INCH],.25*INCH,INCH,.375*INCH)
    for pid in records:
        if pid.startswith('MUD-GUARD-PICKET-'):
            side=pid.split('-')[3];lo,hi=bounds(pid);z=(lo[2]+hi[2])/2
            base='MUD-SILL-'+side+('-BACK' if z<layout['dimensions']['frontZ_M'] else '-FRONT')
            if base not in records:base='MUD-SILL-'+side
            pair(pid,base,1,-1,[.5*INCH,.5*INCH],0,.5*INCH)
            pair(pid,'MUD-GUARD-TOP-'+side,1,1,[.5*INCH,.5*INCH],0,.5*INCH)
        elif pid.startswith('MUD-FRONT-PICKET-'):
            side=pid.split('-')[3]
            pair(pid,'MUD-FRONT-SILL-'+side,1,-1,[.5*INCH,.5*INCH],0,.5*INCH)
            pair(pid,'MUD-FRONT-GUARD-'+side,1,1,[.5*INCH,.5*INCH],0,.5*INCH)
    for side in ['L','R']:
        for end in ['BACK','FRONT']:
            pid='MUD-POST-'+side+'-'+end
            pair(pid,'MUD-PLATE-'+side,1,1,[1.5*INCH,3.5*INCH],0,1.5*INCH,.5*INCH)
            base='MUD-SILL-'+side+'-'+end
            pair(pid,base,1,-1,[1.5*INCH,3.5*INCH],0,INCH,.5*INCH)
        pair('MUD-ENTRY-GUARD-POST-'+side,'MUD-FRONT-SILL-'+side,1,-1,[1.5*INCH,3.5*INCH],0,INCH,.375*INCH)
        pair('MUD-HEADER-FRONT','MUD-PLATE-'+side,0,-1 if side=='L' else 1,[1.5*INCH,3.5*INCH],.25*INCH,INCH,.5*INCH,[0,0,INCH])
    def register_joint(family,donor,receiver,connector,direction,metadata=None):
        jid='PJ-'+str(len(joints)+1).zfill(3)
        for pid in [donor,receiver]:part_joint_ids[pid].append(jid)
        item={'id':jid,'family':family,'donor':donor,'receiver':receiver,'connector':export(connector),'connector_volume_m3':connector.volume(),'insertion_direction_local':list(direction),'insertion_direction_world':(np.asarray(direction)@basis).tolist(),'capacity_status':'Proposed geometry; joint and peg capacity unverified.'}
        if metadata:item.update(metadata)
        joints.append(item);return item
    def peg_joint(joint,donor,receiver,axis,center,diameter,lo,hi):
        c=np.asarray(center).copy();c[axis]=lo
        peg=m.Manifold.cylinder(hi-lo,diameter/2,diameter/2,24)
        bore=m.Manifold.cylinder(hi-lo+.002,diameter/2,diameter/2,24)
        if axis==0:peg=peg.rotate([0,90,0]);bore=bore.rotate([0,90,0])
        elif axis==1:peg=peg.rotate([-90,0,0]);bore=bore.rotate([-90,0,0])
        peg=peg.translate(c.tolist());c[axis]-=.001;bore=bore.translate(c.tolist())
        cuts[donor]=cuts[donor]+bore;cuts[receiver]=cuts[receiver]+bore
        pid='MUD-PEG-'+joint['id'];pegs[pid]=peg;joint.update(peg_id=pid,peg_diameter_m=diameter)
    def roof_clip(s):
        # The drawing blank is profiled to the two deck-underface planes before
        # joint cuts; above-roof waste is not shown as a mating cavity.
        offset=-2.701/np.sqrt(1+1/9)
        return s.trim_by_plane([1/3,-1,0],offset).trim_by_plane([-1/3,-1,0],offset)
    for k in range(5):
        left='MUD-RAFTER-L-'+str(k);right='MUD-RAFTER-R-'+str(k)
        original[left]=roof_clip(original[left]);original[right]=roof_clip(original[right])
        overlap=original[left]^original[right];lo,hi=bounds(left);z=(lo[2]+hi[2])/2
        back=cube([-10,-10,lo[2]-.01],[10,10,z]);front=cube([-10,-10,z],[10,10,hi[2]+.01])
        # Extend the cutter beyond the shared roof face. Its extension lies
        # wholly outside the profiled receiver, removing a coincident mouth cap
        # without changing the occupied half-lap or its matching bearing faces.
        right_tool=original[right]+original[right].translate([0,.001,0])
        left_tool=original[left]+original[left].translate([0,.001,0])
        assert abs((right_tool^original[left]).volume()-overlap.volume())<1e-12
        assert abs((left_tool^original[right]).volume()-overlap.volume())<1e-12
        cuts[left]=cuts[left]+(right_tool^front);cuts[right]=cuts[right]+(left_tool^back)
        joint=register_joint('pegged apex half lap',left,right,overlap,[0,0,1],{'lap_depth_m':(hi[2]-lo[2])/2})
        vv=np.asarray(overlap.to_mesh64().vert_properties)[:,:3];c=vv.mean(0);peg_joint(joint,left,right,2,c,.5*INCH,lo[2],hi[2])
        for pid,side in [(left,'L'),(right,'R')]:
            receiver='MUD-PLATE-'+side;seat=original[pid]^original[receiver]
            assert seat.volume()>0,(pid,'missing birdsmouth')
            cuts[pid]=cuts[pid]+original[receiver]
            register_joint('open horizontal birdsmouth seat',receiver,pid,seat,[0,-1,0],{'assembly_member':pid,'seat_width_m':5.5*INCH})
    for k in range(4):
        pid='MUD-ROOF-TIE-'+str(k)
        for side in ['L','R']:
            receiver='MUD-PLATE-'+side;overlap=original[pid]^original[receiver]
            assert overlap.volume()>0,(pid,receiver)
            cuts[receiver]=cuts[receiver]+original[pid]
            joint=register_joint('open top cross half lap',pid,receiver,overlap,[0,-1,0],{'lap_depth_m':2.75*INCH})
            lo,hi=bounds(receiver);a,b=bounds(pid);c=np.array([(lo[0]+hi[0])/2,(lo[1]+b[1])/2,(a[2]+b[2])/2]);peg_joint(joint,pid,receiver,1,c,.5*INCH,lo[1],b[1])
    # Full actual 2x6 stock with face-housed ends. An open outside face permits
    # a single insertion direction into both receivers after the bent is square.
    def brace(pid,post,beam,normal_axis,outside_sign,run_axis,run_sign):
        plo,phi=bounds(post);blo,bhi=bounds(beam);normal_face=phi[normal_axis] if outside_sign>0 else plo[normal_axis]
        post_face=phi[run_axis] if run_sign>0 else plo[run_axis]
        a=(plo+phi)/2;a[normal_axis]=normal_face-outside_sign*INCH;a[run_axis]=post_face;a[1]=blo[1]-.50
        b=a.copy();b[run_axis]+=run_sign*.50;b[1]=blo[1]
        direction=(b-a)/np.linalg.norm(b-a);perp=np.zeros(3);perp[1]=direction[run_axis];perp[run_axis]=-direction[1];normal=np.zeros(3);normal[normal_axis]=1
        start=a-direction*INCH;end=b+direction*INCH
        vertices=[c+normal*x*INCH+perp*y*3*INCH for c in [start,end] for x in [-1,1] for y in [-1,1]]
        stock=m.Manifold.hull_points(np.asarray(vertices));assert stock.volume()>0
        original[pid]=stock;additions[pid]=m.Manifold();cuts[pid]=m.Manifold();part_joint_ids[pid]=[];extra_members.add(pid)
        mesh=export(stock);center=world((start+end)/2).tolist()
        records[pid]={'id':pid,'name':'Actual 2 × 6 porch knee brace','schematic':True,'schematicKind':'mudroom','displayRole':'mudroom','mudroomRole':'framing','group':'mudroom','face':'W','material':'timber brace proposal','is_timber':False,'vertices':mesh['vertices'],'triangles':mesh['triangles'],'center':center,'color':[.58,.38,.22],'exploded_offset':(np.eye(3)[normal_axis]*outside_sign*.8@basis+np.array([0,.2,0])).tolist(),'stockWidthM':2*INCH,'stockDepthM':6*INCH,'connectionStatus':'Documented face-housed pegged brace family; chosen dimensions and capacity require review.'}
        for receiver in [post,beam]:
            overlap=stock^original[receiver];assert overlap.volume()>0,(pid,receiver)
            lo=np.array([-10.,-10.,-10.]);hi=-lo
            if outside_sign>0:lo[normal_axis]=normal_face-INCH
            else:hi[normal_axis]=normal_face+INCH
            toe=overlap^cube(lo,hi);assert toe.volume()>0
            inner_lo=np.array([-10.,-10.,-10.]);inner_hi=-inner_lo
            if outside_sign>0:inner_hi[normal_axis]=normal_face-INCH
            else:inner_lo[normal_axis]=normal_face+INCH
            shoulder_tool=original[receiver]^cube(inner_lo,inner_hi)
            # Both cutters extend through their open mouths, avoiding shared
            # stock-boundary membranes while preserving exact occupied cuts.
            outward=np.eye(3)[normal_axis]*outside_sign*.001
            housing_tool=(stock+stock.translate(outward.tolist()))^cube(lo,hi)
            assert abs((shoulder_tool^stock).volume()-(overlap-toe).volume())<1e-12
            assert abs((housing_tool^original[receiver]).volume()-toe.volume())<1e-12
            cuts[pid]=cuts[pid]+shoulder_tool;cuts[receiver]=cuts[receiver]+housing_tool
            vector=np.eye(3)[normal_axis]*-outside_sign
            joint=register_joint('face-housed pegged knee brace',pid,receiver,toe,vector,{'housing_depth_m':INCH,'brace_stock_m':[2*INCH,6*INCH],'source':'https://www.vermonttimberworks.com/ask-the-timber-framing-experts/can-a-mortise-tenon-brace-be-installed-after-the-post-beam-have-been-assembled/'})
            v=np.asarray(toe.to_mesh64().vert_properties)[:,:3];c=v.mean(0);rlo,rhi=bounds(receiver);peg_joint(joint,pid,receiver,normal_axis,c,.5*INCH,rlo[normal_axis],rhi[normal_axis])
    for side,sign in [('L',-1),('R',1)]:
        for end,run in [('BACK',1),('FRONT',-1)]:brace('MUD-BRACE-SIDE-'+side+'-'+end,'MUD-POST-'+side+'-'+end,'MUD-PLATE-'+side,0,sign,2,run)
        brace('MUD-BRACE-FRONT-'+side,'MUD-POST-'+side+'-FRONT','MUD-HEADER-FRONT',2,1,0,1 if side=='L' else -1)
    final={pid:(original[pid]+additions[pid])-cuts[pid] for pid in records}
    numerical_residual=0.0
    for pid,s in final.items():
        pieces=s.decompose();kept=[p for p in pieces if abs(p.volume())>1e-12]
        numerical_residual+=sum(abs(p.volume()) for p in pieces if abs(p.volume())<=1e-12)
        assert len(kept)==1 and kept[0].volume()>0,(pid,'disconnected occupied stock',[p.volume() for p in pieces])
        final[pid]=kept[0]
    for pid,s in final.items():assert str(s.status())=='Error.NoError' and s.volume()>0 and len(s.decompose())==1,(pid,str(s.status()),s.volume(),[q.volume() for q in s.decompose()])
    all_solids={**final,**pegs};maximum_overlap=0.0;checks=0
    for (aid,a),(bid,b) in itertools.combinations(all_solids.items(),2):
        aa=a.bounding_box();bb=b.bounding_box()
        if not all(aa[k+3]>bb[k]+1e-10 and bb[k+3]>aa[k]+1e-10 for k in range(3)):continue
        overlap=(a^b).volume();checks+=1;maximum_overlap=max(maximum_overlap,overlap)
        assert overlap<1e-10,(aid,bid,overlap)
    fitted={}
    for pid,s in final.items():
        if not part_joint_ids[pid]:continue
        mesh=export(s);v=np.array(mesh['vertices']);removed=export((original[pid]+additions[pid])-s)
        fitted[pid]={'vertices':mesh['vertices'],'triangles':mesh['triangles'],'center':((v.min(0)+v.max(0))/2).tolist(),'joineryJointIds':part_joint_ids[pid],'joineryStock':export(original[pid]+additions[pid]),'joineryCavity':{'removed':removed,'fit_audit':{'status':'PASS'}},'connectionStatus':'Modeled traditional joint family with matched mating cavities; assembly sequence recorded, structural capacity unverified.'}
    added=[{**records[pid],**fitted[pid]} for pid in sorted(extra_members)]
    for k,(pid,s) in enumerate(pegs.items()):
        mesh=export(s);v=np.asarray(mesh['vertices']);c=((v.min(0)+v.max(0))/2).tolist();off=world([.8+k*.01,.25,.75])-origin
        joint=next(j for j in joints if j.get('peg_id')==pid)
        roof_only=all(records[joint[key]].get('mudroomRoof',False) for key in ['donor','receiver']) or joint['family']=='open top cross half lap'
        added.append({'id':pid,'name':'Proposed hardwood timber-joint peg','schematic':True,'schematicKind':'mudroom','displayRole':'mudroom','mudroomRole':'framing','group':'mudroom','face':'W','material':'hardwood peg proposal','is_timber':False,'vertices':mesh['vertices'],'triangles':mesh['triangles'],'center':c,'label_position':c,'color':[.72,.51,.28],'exploded_offset':off.tolist(),'mudroomRoof':roof_only,'mudroomScreen':roof_only,'connectionStatus':'Matched bore and peg geometry; diameter, edge distance and capacity require design.'})
    assembly=[{'stage':1,'action':'Join top guard rails between movable side posts. Seat pickets in side base rails, then lower each post/top-rail subassembly onto the picket and post-foot tenons.','scope':'Nominal subassembly sequence; lifting rig, temporary bracing, tolerances and structural erection plan remain unverified.'},{'stage':2,'action':'Preassemble front guard panels and entry posts, then bring the two side bents together along X around the front panels. Do not fix both bents before engaging the transverse tenons.'},{'stage':3,'action':'Preassemble the two roof beams with the front header, then lower this U-shaped assembly onto all four post-head tenons.'},{'stage':4,'action':'Lower the transverse roof ties into their open top half-laps. Insert each face-housed knee brace normal to its frame plane, then fit its pegs.'},{'stage':5,'action':'Preassemble and peg each rafter pair at its apex half-lap. Lower the paired rafters onto their open birdsmouth seats before installing the deck, cedar and flashing. Rafter uplift restraint remains a design requirement.'}]
    return {'schema_version':1,'status':'PASS','source_module_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'source_roof_module_sha256':hashlib.sha256((ROOT/'src/mudroom-roof.js').read_bytes()).hexdigest(),'source_fitter_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'source_model_sha256':hashlib.sha256(model_path.read_bytes()).hexdigest(),'anchors':{pid:next(p for p in model['parts'] if p['id']==pid)['center'] for pid in ['P2','P3']},'parts':fitted,'added_parts':added,'joints':joints,'assembly':assembly,'verification':{'scope':'Nominal housed guard/post/header joints, face-housed 2x6 braces, roof half-laps and birdsmouth seats; capacity and erection engineering unverified.','pair_intersection_checks':checks,'maximum_pair_overlap_m3':maximum_overlap,'discarded_numerical_residual_m3':numerical_residual,'joint_count':len(joints),'peg_count':len(pegs),'capacity_verified':False}}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',default='src/mudroom-joinery-fit.json');args=parser.parse_args()
    data=generate();(ROOT/args.output).write_text(json.dumps(data,separators=(',',':'))+'\n')
    print('PASS:',len(data['joints']),'porch joints,',len(data['parts']),'fitted members,',data['verification']['peg_count'],'pegs; source SHA',data['source_module_sha256'])
# TIMESTAMP END 2026-11-02T15:00:19-05:00 | REVISION R004797
