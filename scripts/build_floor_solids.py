# TIMESTAMP START 2026-11-04T23:48:03+00:00 | REVISION R000012
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
# TIMESTAMP START 2026-11-02T20:27:45-05:00 | REVISION R004866
 # Extend the cutter 0.01 micrometre through coincident horizontal faces.
 return m.Manifold((s-t.translate([0,1e-8,0])-t.translate([0,-1e-8,0])).to_mesh64())
# TIMESTAMP END 2026-11-02T20:27:45-05:00 | REVISION R004866

def box_between(a,b,w,h):
 a=np.array(a);b=np.array(b);v=b-a;L=np.linalg.norm(v);angle=math.degrees(math.atan2(-v[2],v[0]));return m.Manifold.cube([L,h,w],True).rotate([0,angle,0]).translate(((a+b)/2).tolist())
# TIMESTAMP START 2026-11-02T20:27:45-05:00 | REVISION R004866
pierTop=layout['piers'][0]['topY_M'];beamDepth=next(p['depthM'] for p in layout['members'] if p['kind']=='beam');joistDepth=next(p['depthM'] for p in layout['members'] if p['kind']=='joist');beamTop=pierTop+beamDepth;joistTop=beamTop+joistDepth
# TIMESTAMP END 2026-11-02T20:27:45-05:00 | REVISION R004866
# A central octagonal hub bears on center pier; beams terminate at its faces.
hubR=.2032/math.cos(math.pi/8)
poly=[[hubR*math.cos((k+.5)*math.pi/4),hubR*math.sin((k+.5)*math.pi/4)] for k in range(8)]
hub=m.CrossSection([poly]).extrude(.286).rotate([90,0,0]).translate([0,beamTop,0])
shoulderR=.35/math.cos(math.pi/8);shoulderPoly=[[shoulderR*math.cos((k+.5)*math.pi/4),shoulderR*math.sin((k+.5)*math.pi/4)] for k in range(8)]
shoulder=m.CrossSection([shoulderPoly]).extrude(.143).rotate([90,0,0]).translate([0,pierTop+.143,0]);hub=m.Manifold((hub+shoulder).to_mesh64());add('FLOOR-CENTRAL-HUB',hub,'wood')
for p in layout['piers']:
# TIMESTAMP START 2026-11-02T20:27:45-05:00 | REVISION R004866
 x,_,z=p['centerM'];s=m.Manifold.cylinder(.6096,.2032,.2032,32).rotate([-90,0,0]).translate([x,p['gradeY_M'],z]);add(p['id'],s,'concrete')
 s=m.Manifold.cylinder(p['embedDepthM'],p['diameterM']/2,p['diameterM']/2,32).rotate([-90,0,0]).translate([x,p['gradeY_M']-p['embedDepthM'],z]);add(p['id']+'-BELOW',s,'concrete')
# TIMESTAMP END 2026-11-02T20:27:45-05:00 | REVISION R004866
for b in layout['members']:
 if b['kind']!='beam':continue
 s=box_between(b['startM'],b['endM'],b['widthM'],b['depthM'])-hub
 # Retain exactly the intended radial segment, no overlapping center hub.
 add(b['id'],s,'wood')
# TIMESTAMP START 2026-11-02T20:27:45-05:00 | REVISION R004866
# Parallel joists are clipped to the same octagonal perimeter as the floor.
footprint=m.CrossSection([[[p[0],-p[2]] for p in layout['sourcePostCenters']]]).extrude(joistDepth).rotate([90,0,0]).translate([0,joistTop,0])
for b in layout['members']:
 if b['kind']!='joist':continue
 a=np.array(b['startM']);z=np.array(b['endM']);u=(z-a)/np.linalg.norm(z-a)
 s=box_between(a-u*.1,z+u*.1,b['widthM'],b['depthM'])^footprint
 # End each joist at the inner face of the continuous two-inch rim.
 for k in range(8):
  q=np.array(layout['sourcePostCenters'][k]);r=np.array(layout['sourcePostCenters'][(k+1)%8]);normal=(q+r)/2;normal[1]=0;normal/=np.linalg.norm(normal)
  s=s.trim_by_plane((-normal).tolist(),-float(normal@q)+.0254)
 add(b['id'],s,'wood')
# TIMESTAMP END 2026-11-02T20:27:45-05:00 | REVISION R004866
pts=layout['sourcePostCenters']
for k in range(8):
# TIMESTAMP START 2026-11-02T20:27:45-05:00 | REVISION R004866
 a=pts[k].copy();b=pts[(k+1)%8].copy();a[1]=b[1]=joistTop-joistDepth/2
 s=box_between(a,b,.0508,joistDepth)
# TIMESTAMP END 2026-11-02T20:27:45-05:00 | REVISION R004866
 for key,other in list(solids.items()):
  if key.startswith(('FLOOR-JOIST-','FLOOR-RIM-')):s=subtract(s,other)
 add('FLOOR-RIM-'+str(k),s,'wood')
for stand in layout['bearingStands']:
 c=np.array(stand['centerM']);axis=np.array(stand['axis']);side=np.array(stand['sideAxis']);bottom=stand['bottomY_M'];top=-stand['headPlateThicknessM'];height=top-bottom
 for sign in [-1,1]:
  mid=c+side*sign*(stand['clearBeamWidthM']/2+stand['sidePlateThicknessM']/2);mid[1]=(bottom+top)/2
  a=mid-axis*stand['plateLengthM']/2;b=mid+axis*stand['plateLengthM']/2;s=box_between(a,b,stand['sidePlateThicknessM'],height)
  for key,other in list(solids.items()):
   # TIMESTAMP START 2026-11-02T21:30:42-05:00 | REVISION R004880
   if key.startswith(('FLOOR-JOIST-','FLOOR-RIM-','FLOOR-BEAM-')):
    cutter=other
    if key.startswith('FLOOR-JOIST-'):
     v=np.asarray(other.to_mesh64().vert_properties)[:,:3]
     footprint=np.unique(np.round(v[:,[0,2]],12),axis=0)
     center=footprint.mean(0);footprint=footprint[np.argsort(np.arctan2(*(footprint-center)[:,::-1].T))]
     cutter=m.CrossSection([footprint.tolist()]).offset(1e-8).extrude(top+.01-v[:,1].min()+1e-8).rotate([90,0,0]).translate([0,top+.01,0])
     assert (other-cutter).volume()<1e-11,(key,'open slot must include its seated joist')
    s=subtract(s,cutter)
   # TIMESTAMP END 2026-11-02T21:30:42-05:00 | REVISION R004880
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
# TIMESTAMP START 2026-11-04T23:17:24+00:00 | REVISION R000029
from floor_sheet_panels import cut_sheets,sheet_metadata
sheet_info={}
for identifier,shape,stock in cut_sheets(sub):
 add(identifier,shape,'cut 4 × 8-foot sheet underlayment')
 sheet_info[identifier]=sheet_metadata(identifier,stock)
# TIMESTAMP END 2026-11-04T23:17:24+00:00 | REVISION R000029
for k in range(8):
 a=k*math.pi/4;b=(k+1)*math.pi/4;poly=[[0,0],[.45*math.cos(a),.45*math.sin(a)],[.45*math.cos(b),.45*math.sin(b)]]
 s=m.CrossSection([poly]).extrude(.01905).rotate([90,0,0]);add('FLOOR-BAMBOO-CENTER-'+str(k),s,'strand-woven bamboo')
parts=[]
for id,s in solids.items():
# TIMESTAMP START 2026-11-02T20:27:45-05:00 | REVISION R004866
 mesh=s.to_mesh64();v=np.array(mesh.vert_properties)[:,:3];parts.append({'id':id,'name':id,'schematic':True,'schematicKind':'floorAssembly','group':'floor_foundation_proposal','color':([.73,.72,.68] if materials[id]=='concrete' else [.29,.32,.34] if 'steel' in materials[id] else [.63,.45,.26]),'material':materials[id],'is_timber':False,'vertices':v.tolist(),'triangles':mesh.tri_verts.tolist(),'center':((v.min(0)+v.max(0))/2).tolist(),'exploded_offset':[0,0,0],'volumeM3':s.volume(),'underground':id.endswith('-BELOW'),'displayOpacity':.28 if id.endswith('-BELOW') else 1,'status':'Proposed layout/clearance only, capacity and connections undesigned'})
# TIMESTAMP END 2026-11-02T20:27:45-05:00 | REVISION R004866
# TIMESTAMP START 2026-11-04T23:17:24+00:00 | REVISION R000029
for part in parts:part.update(sheet_info.get(part['id'],{}))
(R/'src/floor-foundation-solids.json').write_text(json.dumps({'source_model_sha256':hashlib.sha256(raw).hexdigest(),'source_module_sha256':hashlib.sha256((R/'src/floor-foundation.js').read_bytes()).hexdigest(),'layout':layout,'parts':parts},separators=(',',':'))+'\n')
# TIMESTAMP END 2026-11-04T23:17:24+00:00 | REVISION R000029
print(len(parts),'proposed solids')

# TIMESTAMP END 2026-11-04T23:48:03+00:00 | REVISION R000012
