# TIMESTAMP START 2026-11-04T23:23:25+00:00 | REVISION R000011
# TIMESTAMP START 2026-11-02T18:37:05-05:00 | REVISION R004835
"""Source-bound ray checks of actual interior brace faces, plus a mesh review image."""
from pathlib import Path
import argparse,hashlib,json,subprocess
import numpy as np
import manifold3d as m
from plan_architectural_disassembly import load_scene,NODE
from step_lap import solid,close_bounds,regular_boundary

ROOT=Path(__file__).resolve().parents[1]

def hits(eye,target,triangles):
    a=triangles[:,0];b=triangles[:,1]-a;c=triangles[:,2]-a;d=target-eye
    h=np.cross(np.broadcast_to(d,c.shape),c);det=np.einsum('ij,ij->i',b,h)
    valid=np.abs(det)>1e-12;inv=np.zeros_like(det);inv[valid]=1/det[valid]
    q=eye-a;u=np.einsum('ij,ij->i',q,h)*inv;cross=np.cross(q,b)
    v=np.einsum('j,ij->i',d,cross)*inv;distance=np.einsum('ij,ij->i',c,cross)*inv
    good=valid&(u>=-1e-9)&(v>=-1e-9)&(u+v<=1+1e-9)&(distance>1e-7)&(distance<1-1e-6)
    return np.where(good)[0],distance

def candidate_scene():
    """Read-only dimensional prototype; never changes the production model."""
    scene=load_scene('top-entry')
    program=r"""
const fs=require('fs'),code=fs.readFileSync('./src/schematic-walls.js','utf8')
.replace('z0=-.05,z1=.05','z0=.08255,z1=.1016')
.replace('...rect,-railDepth/2,railDepth/2','...rect,label.startsWith("rail0")?-.0508:.0508,.1016')
.replace(',-.40,-.0762,',',-.40,.0508,');
const mod={exports:{}};new Function('module','exports','require',code)(mod,mod.exports,require);
const model=require('./src/top-entry-proposed-model.json');
process.stdout.write(JSON.stringify(mod.exports.build(model.parts,{applyFit:false}).components));
"""
    pieces=json.loads(subprocess.check_output([NODE,'-e',program],cwd=ROOT))
    timber=[shape for pid,shape in scene.solids.items() if scene.parts[pid].get('is_timber') or scene.parts[pid].get('group')=='joinery_pegs']
    for part in pieces:
        if part.get('schematicKind') not in ['wall','rail','shelf']:continue
        shape=solid(part)
        for obstacle in timber:
            if close_bounds(shape,obstacle):shape=shape-obstacle
        components=[q for q in shape.decompose() if q.volume()>1e-16]
        if part['schematicKind']=='shelf':components=[max(components,key=lambda q:q.volume())]
        shape=m.Manifold.batch_boolean(components,m.OpType.Add) if len(components)>1 else components[0]
        shape=regular_boundary(shape);mesh=shape.to_mesh64()
        part={**part,'vertices':np.asarray(mesh.vert_properties)[:,:3].tolist(),'triangles':np.asarray(mesh.tri_verts).tolist()}
        scene.parts[part['id']]=part;scene.solids[part['id']]=shape
    return scene

def audit(scene):
    walls=[p for p in scene.parts.values() if p.get('schematicKind') in ['wall','rail','shelf']]
    triangles=[];owners=[]
    for p in walls:
        t=np.array(p['vertices'])[np.array(p['triangles'])];triangles.extend(t);owners.extend([p['id']]*len(t))
    triangles=np.array(triangles);records=[]
    for name in sorted(p for p in scene.parts if p.startswith('K')):
        p=scene.parts[name];t=np.array(p['vertices'])[np.array(p['triangles'])]
        normals=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]);areas=np.linalg.norm(normals,axis=1)/2;centers=t.mean(1)
        radial=np.array(scene.parts['P'+name[1]]['center'])*[1,0,1];radial/=np.linalg.norm(radial)
        row={'id':name,'included_in_complete':True,'views':[]}
        for label,eye in [('room_center',np.array([0.,1.6,0.])),('near_post',radial*2.7+np.array([0.,1.6,0.]))]:
            front=[j for j in range(len(t)) if areas[j]>1e-5 and normals[j]@(eye-centers[j])>0]
            front=sorted(front,key=lambda j:-areas[j])[:12];visible=[];occluded=[]
            for j in front:
                own,_=hits(eye,centers[j],t)
                if len(own):continue
                hit,dist=hits(eye,centers[j],triangles)
                if len(hit):occluded.append((j,owners[min(hit,key=lambda q:dist[q])]))
                else:visible.append(j)
            total=sum(areas[j] for j in visible)+sum(areas[j] for j,_ in occluded)
            wall_area=sum(areas[j] for j,pid in occluded if scene.parts[pid].get('schematicKind')!='shelf')
            shelf_area=sum(areas[j] for j,pid in occluded if scene.parts[pid].get('schematicKind')=='shelf')
            row['views'].append({'view':label,'eye_m':eye.tolist(),'visible_samples':len(visible),
                'occluded_samples':len(occluded),'sampled_front_area_m2':float(total),
                'wall_occluded_sample_area_fraction':float(wall_area/total) if total else 1.,
                'furniture_occluded_sample_area_fraction':float(shelf_area/total) if total else 1.,
                'occluders':sorted({q for _,q in occluded})})
        records.append(row)
    assert len(records)==24 and all(any(q['visible_samples'] for q in r['views']) for r in records)
    side=[q for r in records if r['id'].endswith(('-A','-B')) for q in r['views']]
    maximum=max(q['wall_occluded_sample_area_fraction'] for q in side)
    sources={**scene.sources,'scripts/audit_brace_visibility.py':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    # TIMESTAMP START 2026-11-04T19:54:43+00:00 | REVISION R000017
    return {'revision':'R000017','timestamp':'2026-11-04T19:54:43+00:00',
    # TIMESTAMP END 2026-11-04T19:54:43+00:00 | REVISION R000017
        'status':'PASS' if maximum<.005 else 'OCCLUDED','sources':sources,
        'method':'Nearest actual mesh-ray intersections from two interior eye positions; twelve largest front-facing triangle centroids per brace, excluding self-occluded faces. Area-weighted samples are not a whole-surface visibility percentage.',
        'sample_limitations':'A finite mesh-surface sample; end housings and pegs may remain concealed. No drawing-order override, transparency, or omitted wall occluders.',
        'physical_braces_in_complete':24,'inward_braces':8,'maximum_side_brace_wall_occlusion':maximum,
        'maximum_side_brace_furniture_occlusion':max(q['furniture_occluded_sample_area_fraction'] for q in side),'parts':records}

def render(scene,destination):
    from PIL import Image,ImageDraw,ImageFont
    width,height=1200,1000;image=np.full((height,width,3),[240,241,233],dtype=np.uint8);depth=np.full((height,width),-np.inf)
    target=np.array([0.,1.85,-4.05]);eye=np.array([1.8,1.4,-1.7]);direction=eye-target;direction/=np.linalg.norm(direction)
    right=np.cross([0.,1.,0.],direction);right/=np.linalg.norm(right);up=np.cross(direction,right);matrix=np.array([right,up,direction]).T
    parts=[p for p in scene.parts.values() if (p.get('face') in ['NW','W'] and p.get('schematicKind') in ['wall','rail']) or p['id'] in ['P2','T2','R2','B1','B2','K2-A','K2-B','K2-C']]
    edges=[];scale=330.
    for part in parts:
        vertices=np.array(part['vertices']);projected=(vertices-target)@matrix
        projected[:,0]=width/2+projected[:,0]*scale;projected[:,1]=height*.52-projected[:,1]*scale
        color=np.array(part.get('color',[.58,.40,.25])[:3]);adjacent={}
        for triangle in part['triangles']:
            q=projected[triangle];v=vertices[triangle];normal=np.cross(v[1]-v[0],v[2]-v[0]);size=np.linalg.norm(normal)
            if size<1e-12:continue
            normal/=size
            for a,b in zip(triangle,triangle[1:]+triangle[:1]):adjacent.setdefault(tuple(sorted((a,b))),[]).append(normal)
            x0=max(0,int(np.floor(q[:,0].min())));x1=min(width-1,int(np.ceil(q[:,0].max())))
            y0=max(0,int(np.floor(q[:,1].min())));y1=min(height-1,int(np.ceil(q[:,1].max())))
            if x1<x0 or y1<y0:continue
            den=(q[1,1]-q[2,1])*(q[0,0]-q[2,0])+(q[2,0]-q[1,0])*(q[0,1]-q[2,1])
            if abs(den)<1e-10:continue
            yy,xx=np.mgrid[y0:y1+1,x0:x1+1]
            a=((q[1,1]-q[2,1])*(xx-q[2,0])+(q[2,0]-q[1,0])*(yy-q[2,1]))/den
            b=((q[2,1]-q[0,1])*(xx-q[2,0])+(q[0,0]-q[2,0])*(yy-q[2,1]))/den;c=1-a-b;z=a*q[0,2]+b*q[1,2]+c*q[2,2]
            shown=(a>=-1e-8)&(b>=-1e-8)&(c>=-1e-8)&(z>depth[y0:y1+1,x0:x1+1])
            light=.72+.28*abs(normal@np.array([-.35,.85,.40]));image[y0:y1+1,x0:x1+1][shown]=np.clip(color*light*255,0,255).astype(np.uint8);depth[y0:y1+1,x0:x1+1][shown]=z[shown]
        for (a,b),normals in adjacent.items():
            if len(normals)!=2 or abs(normals[0]@normals[1])<.99999:edges.append((projected[a],projected[b]))
    for a,b in edges:
        count=max(2,int(np.linalg.norm((b-a)[:2])*1.5));q=a+np.linspace(0,1,count)[:,None]*(b-a);xy=np.rint(q[:,:2]).astype(int)
        valid=(xy[:,0]>=0)&(xy[:,0]<width)&(xy[:,1]>=0)&(xy[:,1]<height);xy=xy[valid];z=q[valid,2];shown=z>=depth[xy[:,1],xy[:,0]]-.002
        image[xy[shown,1],xy[shown,0]]=[64,62,51]
    # TIMESTAMP START 2026-11-04T19:54:43+00:00 | REVISION R000017
    out=Image.fromarray(image);draw=ImageDraw.Draw(out)
    fontpath=next(str(p) for p in [Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'),Path('/System/Library/Fonts/Supplemental/Arial.ttf')] if p.exists())
    # TIMESTAMP END 2026-11-04T19:54:43+00:00 | REVISION R000017
    draw.rectangle([0,0,width,80],fill='#f8f7f2');draw.text((24,14),'Interior P2: two wall braces and the inward tie brace',fill='#173a40',font=ImageFont.truetype(fontpath,28))
    draw.text((24,49),'Actual occupied meshes; selected corner context; geometric proposal, capacity unverified.',fill='#56676b',font=ImageFont.truetype(fontpath,18))
    destination.parent.mkdir(parents=True,exist_ok=True);out.save(destination)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--candidate',action='store_true');parser.add_argument('--write',action='store_true');parser.add_argument('--render',action='store_true');args=parser.parse_args()
    scene=candidate_scene() if args.candidate else load_scene('top-entry');report=audit(scene)
    if args.candidate:report['status']='CANDIDATE_'+report['status']
    if args.render:
        assert not args.candidate,'Retained review image must use the production meshes'
        destination=ROOT/'public/review/interior-braces.png';render(scene,destination)
        report['image']={'path':str(destination.relative_to(ROOT)),'sha256':hashlib.sha256(destination.read_bytes()).hexdigest()}
    if args.write:
        assert not args.candidate,'Prototype data must not replace the source-bound production audit'
        (ROOT/'docs/brace-visibility-audit.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='parts'}))
# TIMESTAMP END 2026-11-02T18:37:05-05:00 | REVISION R004835

# TIMESTAMP END 2026-11-04T23:23:25+00:00 | REVISION R000011
