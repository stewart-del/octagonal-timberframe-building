"""Display-only proposed assembly solids; no engineered capacities."""
from pathlib import Path
import subprocess,json,math,hashlib
import numpy as np
import manifold3d as m
R=Path(__file__).resolve().parents[1];raw=(R/'src/model-data.json').read_bytes();d=json.loads(raw)
layout=json.loads(subprocess.check_output(['node','-e',"process.stdout.write(JSON.stringify(require('./src/floor-foundation.js').build(require('./src/model-data.json'))))"],cwd=R))
solids={};materials={}
def add(id,s,material):
 assert str(s.status())=='Error.NoError' and s.volume()>1e-10,id
 solids[id]=m.Manifold(s.to_mesh64());materials[id]=material

def subtract(s,t):
 a,b=s.bounding_box(),t.bounding_box()
 if any(a[i+3]<=b[i]+1e-10 or b[i+3]<=a[i]+1e-10 for i in range(3)):return s
 return m.Manifold((s-t).to_mesh64())

def box_between(a,b,w,h):
 a=np.array(a);b=np.array(b);v=b-a;L=np.linalg.norm(v);angle=math.degrees(math.atan2(-v[2],v[0]));return m.Manifold.cube([L,h,w],True).rotate([0,angle,0]).translate(((a+b)/2).tolist())
pierTop=layout['piers'][0]['topY_M'];beamTop=pierTop+.286;joistTop=beamTop+.235
# A central octagonal hub bears on center pier; beams terminate at its faces.
hubR=.2032/math.cos(math.pi/8)
poly=[[hubR*math.cos((k+.5)*math.pi/4),hubR*math.sin((k+.5)*math.pi/4)] for k in range(8)]
hub=m.CrossSection([poly]).extrude(.286).rotate([90,0,0]).translate([0,beamTop,0])
shoulderR=.35/math.cos(math.pi/8);shoulderPoly=[[shoulderR*math.cos((k+.5)*math.pi/4),shoulderR*math.sin((k+.5)*math.pi/4)] for k in range(8)]
shoulder=m.CrossSection([shoulderPoly]).extrude(.143).rotate([90,0,0]).translate([0,pierTop+.143,0]);hub=m.Manifold((hub+shoulder).to_mesh64());add('FLOOR-CENTRAL-HUB',hub,'wood')
for p in layout['piers']:
 x,_,z=p['centerM'];s=m.Manifold.cylinder(.6096,.2032,.2032,32).rotate([-90,0,0]).translate([x,p['gradeY_M'],z]);add(p['id'],s,'concrete')
for b in layout['members']:
 if b['kind']!='beam':continue
 s=box_between(b['startM'],b['endM'],b['widthM'],b['depthM'])-hub
 # Retain exactly the intended radial segment, no overlapping center hub.
 add(b['id'],s,'wood')
# Joists sit on radial beams; trim reciprocal ends so chosen solids do not overlap.
for b in layout['members']:
 if b['kind']!='joist':continue
 a=np.array(b['startM']);z=np.array(b['endM']);u=(z-a)/np.linalg.norm(z-a);s=box_between(a-u*.1,z+u*.1,b['widthM'],b['depthM'])
 k=int(b['id'].split('-')[2]);alpha=k*math.pi/4;beta=(k+1)*math.pi/4
 s=s.trim_by_plane([-math.sin(alpha),0,-math.cos(alpha)],0).trim_by_plane([math.sin(beta),0,math.cos(beta)],0)
 add(b['id'],s,'wood')
pts=layout['sourcePostCenters']
for k in range(8):
 a=pts[k].copy();b=pts[(k+1)%8].copy();a[1]=b[1]=joistTop-.235/2
 s=box_between(a,b,.045,.235)
 for key,other in list(solids.items()):
  if key.startswith(('FLOOR-JOIST-','FLOOR-RIM-')):s=subtract(s,other)
 add('FLOOR-RIM-'+str(k),s,'wood')
for stand in layout['bearingStands']:
 c=np.array(stand['centerM']);axis=np.array(stand['axis']);side=np.array(stand['sideAxis']);bottom=stand['bottomY_M'];top=-stand['headPlateThicknessM'];height=top-bottom
 for sign in [-1,1]:
  mid=c+side*sign*(stand['clearBeamWidthM']/2+stand['sidePlateThicknessM']/2);mid[1]=(bottom+top)/2
  a=mid-axis*stand['plateLengthM']/2;b=mid+axis*stand['plateLengthM']/2;s=box_between(a,b,stand['sidePlateThicknessM'],height)
  for key,other in list(solids.items()):
   if key.startswith(('FLOOR-JOIST-','FLOOR-RIM-','FLOOR-BEAM-')):s=subtract(s,other)
  add(stand['id']+'-SIDE'+str(sign),s,'steel proposal')
 mid=c.copy();mid[1]=-stand['headPlateThicknessM']/2;s=box_between(mid-axis*.12,mid+axis*.12,.24,stand['headPlateThicknessM'])
 for key,other in list(solids.items()):
  if key.startswith(('FLOOR-JOIST-','FLOOR-RIM-')):s=subtract(s,other)
 add(stand['id']+'-HEAD',s,'steel proposal')
# Continuous subfloor, including formerly deferred grate center.
poly=[[p[0],-p[2]] for p in pts]
sub=m.CrossSection([poly]).extrude(.0381).rotate([90,0,0]).translate([0,-.01905,0])
for key,other in solids.items():
 if key.startswith('POST-BEARING-STAND'):
  b=other.bounding_box();lo=np.array(b[:3]);hi=np.array(b[3:]);cut=m.Manifold.cube((hi-lo+2e-5).tolist(),True).translate(((hi+lo)/2).tolist());sub=subtract(sub,cut)
add('FLOOR-SUBFLOOR',sub,'subfloor proposal')
for k in range(8):
 a=k*math.pi/4;b=(k+1)*math.pi/4;poly=[[0,0],[.45*math.cos(a),.45*math.sin(a)],[.45*math.cos(b),.45*math.sin(b)]]
 s=m.CrossSection([poly]).extrude(.01905).rotate([90,0,0]);add('FLOOR-BAMBOO-CENTER-'+str(k),s,'strand-woven bamboo')
parts=[]
for id,s in solids.items():
 mesh=s.to_mesh64();v=np.array(mesh.vert_properties)[:,:3];parts.append({'id':id,'name':id,'schematic':True,'schematicKind':'floorAssembly','group':'floor_foundation_proposal','color':([.73,.72,.68] if materials[id]=='concrete' else [.29,.32,.34] if 'steel' in materials[id] else [.63,.45,.26]),'material':materials[id],'is_timber':False,'vertices':v.tolist(),'triangles':mesh.tri_verts.tolist(),'center':((v.min(0)+v.max(0))/2).tolist(),'exploded_offset':[0,0,0],'volumeM3':s.volume(),'status':'Proposed layout/clearance only, capacity and connections undesigned'})
(R/'src/floor-foundation-solids.json').write_text(json.dumps({'source_model_sha256':hashlib.sha256(raw).hexdigest(),'source_module_sha256':hashlib.sha256((R/'src/floor-foundation.js').read_bytes()).hexdigest(),'layout':layout,'parts':parts},separators=(',',':'))+'\n')
print(len(parts),'proposed solids')
