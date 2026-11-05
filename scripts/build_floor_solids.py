# TIMESTAMP START 2026-11-05T05:14:11+00:00 | REVISION R000024
# TIMESTAMP START 2026-11-05T04:26:16+00:00 | REVISION R000021
# TIMESTAMP START 2026-11-04T23:48:03+00:00 | REVISION R000012
"""Display-only proposed assembly solids; no engineered capacities."""
from pathlib import Path
import subprocess,json,math,hashlib
# TIMESTAMP START 2026-11-05T06:36:54+00:00 | REVISION R000029
import argparse
# TIMESTAMP END 2026-11-05T06:36:54+00:00 | REVISION R000029
import numpy as np
import manifold3d as m
R=Path(__file__).resolve().parents[1];raw=(R/'src/model-data.json').read_bytes();d=json.loads(raw)
# TIMESTAMP START 2026-11-05T06:36:54+00:00 | REVISION R000029
parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=R/'src/floor-foundation-solids.json');arguments=parser.parse_args()
arguments.output.parent.mkdir(parents=True,exist_ok=True)
# TIMESTAMP END 2026-11-05T06:36:54+00:00 | REVISION R000029
layout=json.loads(subprocess.check_output(['node','-e',"process.stdout.write(JSON.stringify(require('./src/floor-foundation.js').build(require('./src/model-data.json'))))"],cwd=R))
# TIMESTAMP START 2026-11-05T06:36:54+00:00 | REVISION R000029
furniture_path=R/'src/bookshelf-solids.json';furniture=json.loads(furniture_path.read_text())
furniture_parts=furniture['parts']
# TIMESTAMP END 2026-11-05T06:36:54+00:00 | REVISION R000029
# TIMESTAMP START 2026-11-05T07:15:21+00:00 | REVISION R000031
import floor_edge_supports
edge_supports=floor_edge_supports.load()
# TIMESTAMP END 2026-11-05T07:15:21+00:00 | REVISION R000031
solids={};materials={};extra_metadata={};prototypes={};instances=[]
I=.0254
NORTH=np.array(layout['joistDirectionM']);EAST=np.array([-NORTH[2],0,NORTH[0]]);UP=np.array([0.,1.,0.])
FLOOR_BASIS=np.column_stack([EAST,NORTH,UP]);FLOOR_TRANSFORM=np.column_stack([FLOOR_BASIS,np.zeros(3)]).tolist()
def floor_box(e0,e1,n0,n1,y0,y1):
 return m.Manifold.cube([e1-e0,n1-n0,y1-y0]).translate([e0,n0,y0]).transform(FLOOR_TRANSFORM)
def floor_prism(section,bottom,height):
 return section.extrude(height).translate([0,0,bottom]).transform(FLOOR_TRANSFORM)
footprint2=m.CrossSection([[[float(np.dot(p,EAST)),float(np.dot(p,NORTH))] for p in layout['sourcePostCenters']]])
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
# Nominal2x6 panel-edge blocking is actual1.5x5.5, flush with joist tops.
# It supports sheet seams; it is not a six-inch full-depth end-restraint claim.
support_ids=[pid for pid in solids if pid.startswith(('FLOOR-JOIST-','FLOOR-RIM-'))]
support_union=m.Manifold.batch_boolean([solids[pid] for pid in support_ids],m.OpType.Add)
joist_stations=sorted(float(np.dot(p['startM'],EAST)) for p in layout['members'] if p['kind']=='joist')
block_info={}
n_limit=max(abs(float(np.dot(p,NORTH))) for p in layout['sourcePostCenters'])
for row in range(math.floor(-n_limit/(48*I)-.5),math.ceil(n_limit/(48*I)-.5)):
 n=(row+.5)*48*I
 for bay,(e0,e1) in enumerate(zip(joist_stations,joist_stations[1:])):
  raw_block=floor_box(e0+I,e1-I,n-.75*I,n+.75*I,joistTop-5.5*I,joistTop)
  shape=raw_block
  # The same independent inner-rim halfspaces used for the joist ends avoid
  # ambiguous re-unions of coincident rim/joist boundary fragments.
  for k in range(8):
   q=np.array(layout['sourcePostCenters'][k]);r=np.array(layout['sourcePostCenters'][(k+1)%8]);normal=(q+r)/2;normal[1]=0;normal/=np.linalg.norm(normal)
   shape=shape.trim_by_plane((-normal).tolist(),-float(normal@q)+I)
  for support_id in support_ids:
   if support_id.startswith('FLOOR-JOIST-'):shape=subtract(shape,solids[support_id])
  if shape.volume()<1e-9:continue
  pieces=shape.decompose();kept=[p for p in pieces if p.volume()>1e-16]
  assert len(kept)==1,('Disconnectedblocking',row,bay,[p.volume()/I**3 for p in pieces])
  clean=kept[0];error=abs((shape-clean).volume())+abs((clean-shape).volume())
  assert error<1e-6*I**3,('Blockingnormalizationchangedmaterial',error)
  shape=clean
  pid=f'FLOOR-BLOCKING-{row+10:02d}-{bay:02d}';add(pid,shape,'dimensional wood panel-edge blocking')
  extra_metadata[pid]={'floorRole':'panel_edge_blocking','stock_frame':{'axis':EAST.tolist(),'width':NORTH.tolist(),'depth':UP.tolist()},'nominalSectionIn':[2,6],'actualSectionIn':[1.5,5.5],'sequence':'Place between the existing full2x6joists before decking; four8dcommon toenails, two each end. Cut the octagonal perimeter end to the actual rim face.','nominalSeamNorthM':n,'capacityStatus':'Panel-edge support proposal; member and connection load design remains unverified.'}
  block_info[pid]={'row':row,'bay':bay,'north':n}
for stand in layout['bearingStands']:
 c=np.array(stand['centerM']);axis=np.array(stand['axis']);side=np.array(stand['sideAxis']);bottom=stand['bottomY_M'];top=-stand['headPlateThicknessM'];height=top-bottom
 for sign in [-1,1]:
  mid=c+side*sign*(stand['clearBeamWidthM']/2+stand['sidePlateThicknessM']/2);mid[1]=(bottom+top)/2
  a=mid-axis*stand['plateLengthM']/2;b=mid+axis*stand['plateLengthM']/2;s=box_between(a,b,stand['sidePlateThicknessM'],height)
  for key,other in list(solids.items()):
   # TIMESTAMP START 2026-11-02T21:30:42-05:00 | REVISION R004880
   if key.startswith(('FLOOR-JOIST-','FLOOR-RIM-','FLOOR-BEAM-','FLOOR-BLOCKING-')):
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
# TIMESTAMP START 2026-11-05T07:15:21+00:00 | REVISION R000031
# Only new wood enters here; original joists/rims remain their current stock.
for part in edge_supports['support']['unbored_installed_wood']:
 add(part['id'],floor_edge_supports.solid(part),'dimensional wood panel-edge backing')
 extra_metadata[part['id']]=floor_edge_supports.metadata(part,EAST,NORTH)
# TIMESTAMP END 2026-11-05T07:15:21+00:00 | REVISION R000031
# Continuous subfloor, including formerly deferred grate center.
poly=[[p[0],-p[2]] for p in pts]
deck=next(p for p in layout['layers'] if p['id']=='SUBFLOOR')
sub=floor_prism(footprint2,deck['topY_M']-deck['thicknessM'],deck['thicknessM'])
for key,other in solids.items():
 if key.startswith('POST-BEARING-STAND'):
  # TIMESTAMP START 2026-11-05T06:36:54+00:00 | REVISION R000029
  b=other.bounding_box();lo=np.array(b[:3]);hi=np.array(b[3:])
  if key.endswith('-HEAD'):
   lo[1]=deck['topY_M']-deck['thicknessM']-.001
   hi[1]=deck['topY_M']+.001
  cut=m.Manifold.cube((hi-lo+2e-5).tolist(),True).translate(((hi+lo)/2).tolist());sub=subtract(sub,cut)
  # TIMESTAMP END 2026-11-05T06:36:54+00:00 | REVISION R000029
# TIMESTAMP START 2026-11-04T23:17:24+00:00 | REVISION R000029
from floor_sheet_panels import cut_sheets,sheet_metadata
sheet_info={}
for identifier,shape,stock in cut_sheets(sub):
 add(identifier,shape,'cut 4 × 8-foot sheet underlayment')
 sheet_info[identifier]=sheet_metadata(identifier,stock)
# TIMESTAMP END 2026-11-04T23:17:24+00:00 | REVISION R000029
# TIMESTAMP START 2026-11-05T07:15:21+00:00 | REVISION R000031
edge_input_check=floor_edge_supports.verify_unbored_inputs(edge_supports,solids)
# TIMESTAMP END 2026-11-05T07:15:21+00:00 | REVISION R000031
# Real floating finish: finite parallel boards, not merged concentric sectors.
from scipy.spatial import ConvexHull
raw_fixed=json.loads(subprocess.check_output(['node','-e',"const m=require('./src/model-data.json');const w=require('./src/schematic-walls.js').build(m.parts,{applyFit:false});const p=require('./src/mudroom.js').build(m,{applyJoinery:false});process.stdout.write(JSON.stringify([...m.parts,...w.components.filter(x=>x.schematicKind==='rail'),...p.components.filter(x=>x.mudroomRole==='floor')]))"],cwd=R))
fixed_sections=[]
def fixed_section(vertices):
 points=np.unique(np.round([[float(np.dot(v,EAST)),float(np.dot(v,NORTH))] for v in vertices],12),axis=0)
 if len(points)<3:return
 hull=ConvexHull(points);fixed_sections.append(m.CrossSection([points[hull.vertices].tolist()]).offset(.5*I))
for part in raw_fixed:
 ys=np.asarray(part['vertices'])[:,1]
 if min(ys)<=1e-8 and max(ys)>=-.375*I-1e-8:fixed_section(part['vertices'])
for pid,shape in solids.items():
 if pid.startswith('POST-BEARING-STAND-') and pid.endswith('-HEAD'):fixed_section(np.asarray(shape.to_mesh64().vert_properties)[:,:3])
# TIMESTAMP START 2026-11-05T06:36:54+00:00 | REVISION R000029
for part in furniture_parts:
 if part['id'].startswith('BOOK-') and '-FOOT-' in part['id'] and part.get('joineryStock'):
  fixed_section(part['joineryStock']['vertices'])
# TIMESTAMP END 2026-11-05T06:36:54+00:00 | REVISION R000029
finish_section=footprint2.offset(-.5*I)
for section in fixed_sections:finish_section=finish_section-section
floorpad=next(p for p in layout['layers'] if p['id']=='FLOORPAD')
finish=next(p for p in layout['layers'] if p['id']=='BAMBOO')
# TIMESTAMP START 2026-11-05T06:36:54+00:00 | REVISION R000029
# Published actual 3mm x100ft x4ft rolls, cut before the floating planks.
lo,hi=finish_section.bounds()[:2],finish_section.bounds()[2:]
cork_product=floorpad['product'];roll_width=cork_product['rollWidthM']
for k,n0 in enumerate(np.arange(math.floor(lo[1]/roll_width)*roll_width,hi[1],roll_width)):
 band=m.CrossSection.square([hi[0]-lo[0]+2,roll_width]).translate([lo[0]-1,n0])
 shape=finish_section^band
 if shape.area()<1e-8:continue
 cut_length=shape.bounds()[2]-shape.bounds()[0]
 for j,piece in enumerate(shape.decompose()):
  if piece.area()<1e-8:continue
  pid=f'FLOOR-CORK-{k:02d}-{j:02d}';add(pid,floor_prism(piece,floorpad['topY_M']-floorpad['thicknessM'],floorpad['thicknessM']),'3 mm cork underlayment')
  extra_metadata[pid]={'floorRole':'finish_underlayment','displayRole':'floorFinish','nominalThicknessM':.003,'product':cork_product,'stock_parent_id':f'CORK-ROLL-CUT-{k:02d}',
   'rollStock':{'rollWidthM':roll_width,'rollLengthM':cork_product['rollLengthM'],'cutLengthM':cut_length,'thicknessM':.003},
   'stock_frame':{'axis':EAST.tolist(),'width':NORTH.tolist(),'depth':UP.tolist()},'installation':cork_product['installation']}
# TIMESTAMP END 2026-11-05T06:36:54+00:00 | REVISION R000029
width=5.125*I;previous_seams=[];before_previous=[];board_index=0
n0=lo[1];row=0
while n0<hi[1]-1e-9:
 n1=min(n0+width,hi[1]);band=finish_section^m.CrossSection.square([hi[0]-lo[0]+2,n1-n0]).translate([lo[0]-1,n0])
 if band.area()<1e-8:n0=n1;row+=1;continue
 # TIMESTAMP START 2026-11-05T06:36:54+00:00 | REVISION R000029
 row_seams=[]
 for segment in band.decompose():
  e0,_,e1,_=segment.bounds();span=e1-e0
  candidates=[]
  for starter in [16,40,24,48,32,12,20,44,28,36,18,42,14,38,22,46,26,34,30]:
   cuts=[e0];x=e0+starter*I
   while x<e1-1e-8:cuts.append(x);x+=48*I
   cuts.append(e1)
   if len(cuts)>2 and cuts[-1]-cuts[-2]<10*I-1e-9:continue
   seams=cuts[1:-1]
   closest=min((abs(a-b) for a in seams for b in previous_seams),default=100)
   h_joint=min((abs(a-b) for a in seams for b in before_previous),default=100)
   if closest<6*I-1e-9:continue
   # A new end joint must not split a notched board into disconnected or
   # sub-ten-inch fragments beside a fixed foot. Replan this connected band.
   valid=True
   for a,b in zip(cuts,cuts[1:]):
    cut=segment^m.CrossSection.square([b-a,n1-n0]).translate([a,n0])
    pieces=[q for q in cut.decompose() if q.area()>1e-8]
    if len(pieces)!=1 or pieces[0].bounds()[2]-pieces[0].bounds()[0]<10*I-1e-8:valid=False;break
   if not valid:continue
   candidates.append((closest+(min(h_joint,3*I)/10),cuts,seams))
  if not candidates:
   raise AssertionError(('No6inch-staggered finite board layout',row,span/I))
  _,cuts,seams=max(candidates,key=lambda p:p[0])
  for a,b in zip(cuts,cuts[1:]):
   rectangle=m.CrossSection.square([b-a,n1-n0]).translate([a,n0]);piece_section=segment^rectangle
   for cut_index,piece in enumerate(piece_section.decompose()):
    if piece.area()<1e-8:continue
    pid=f'FLOOR-BAMBOO-BOARD-{board_index:04d}';board_index+=1
    add(pid,floor_prism(piece,-finish['thicknessM'],finish['thicknessM']),'engineered bamboo')
    extra_metadata[pid]={'floorRole':'finish_plank','displayRole':'floorFinish','stock_frame':{'axis':EAST.tolist(),'width':NORTH.tolist(),'depth':UP.tolist()},'flooringProduct':finish['product'],'proposedCutLengthIn':(b-a)/I,'row':row,'endJointEastM':[a,b],'minimumAdjacentEndStaggerIn':6,'factoryJointGeometry':'Published external plank envelope; exact proprietary click profile and carton length mix unavailable. Placement is illustrative; follow the product guide for angle-lock installation.','installation':'Floating click, no flooring nails or substrate screws; half-inch clearance around fixed objects.'}
  row_seams.extend(seams)
 before_previous,previous_seams=previous_seams,row_seams;n0=n1;row+=1
 # TIMESTAMP END 2026-11-05T06:36:54+00:00 | REVISION R000029
# Every floor fastener is a distinct physical instance of one shared envelope.
# Bores represent displaced wood, not a recommendation to predrill full shank OD.
TOL=1e-6*I**3
# TIMESTAMP START 2026-11-05T06:36:54+00:00 | REVISION R000029
# Anchor geometry reserves its real position before deck screw placement, and
# composes its displacement into the newly generated sheets without old bores.
fastener_solids={p['id']:m.Manifold(m.Mesh64(np.asarray(p['vertices'],float),np.asarray(p['triangles'],np.uint64))) for p in furniture_parts if p['id'].startswith('BOOK-SCREW-')}
fastener_receivers={}
# TIMESTAMP END 2026-11-05T06:36:54+00:00 | REVISION R000029
def packed(shape):
 raw=shape.to_mesh64();return {'vertices':np.asarray(raw.vert_properties)[:,:3].tolist(),'triangles':np.asarray(raw.tri_verts).tolist()}
def fastener_transform(point,axis):
 axis=np.asarray(axis,float);axis/=np.linalg.norm(axis);a=np.eye(3)[np.argmin(abs(axis))];u=np.cross(axis,a);u/=np.linalg.norm(u);v=np.cross(axis,u)
 return np.column_stack([u,v,axis,np.asarray(point)]).tolist()
def ray_intervals(shape,point,axis,length):
 hits=shape.ray_cast(np.asarray(point).tolist(),(np.asarray(point)+np.asarray(axis)*length).tolist());intervals=[];start=None
 for hit in hits:
  direction=np.dot(hit.normal,axis)
  if direction<-1e-8:start=max(0.,hit.distance)
  elif direction>1e-8 and start is not None:intervals.append([start*length,hit.distance*length]);start=None
 if start is not None:intervals.append([start*length,length])
 return intervals
nail_length=2.5*I;nail_radius=.131*I/2;head_height=.06*I;tip=.25*I
nail=m.Manifold.cylinder(nail_length-tip,nail_radius,nail_radius,24)+m.Manifold.cylinder(head_height+.005*I,.285*I/2,.285*I/2,24).translate([0,0,-head_height])+m.Manifold.cylinder(tip+.005*I,nail_radius,0,24).translate([0,0,nail_length-tip-.005*I])
ws_length=2.5*I;ws_head=(.333-.132)/2*I;ws_tip=.268*I;ws_unthreaded=(2.5-1.95)*I
wsv=m.Manifold.cylinder(ws_head,.333*I/2,.132*I/2,24)+m.Manifold.cylinder(ws_unthreaded,.132*I/2,.132*I/2,24)+m.Manifold.cylinder(ws_length-ws_unthreaded-ws_tip+.005*I,.182*I/2,.182*I/2,24).translate([0,0,ws_unthreaded-.005*I])+m.Manifold.cylinder(ws_tip+.005*I,.182*I/2,0,24).translate([0,0,ws_length-ws_tip-.005*I])
prototypes['FLOOR-8DHDGPT']=packed(nail);prototypes['FLOOR-WSV212S']=packed(wsv)
nail_spec={'manufacturer':'Simpson Strong-Tie','partNumber':'8DHDGPT500 /8DHDGPT2500','lengthIn':2.5,'majorDiameterIn':.131,'headDiameterIn':.285,'drive':'Hammer or compatible 33° paper strip nailer','material':'Hot-dip galvanized carbon steel, smooth shank','installation':'Two 8d common toenails at each end, approximately 30° to the blocking grain; start approximately one-third of nail length from the end. NDS minimum receiving-wood penetration including tip: 6D = 0.786 in. Verify project loads and local code adoption.','geometryProfile':'Verified nominal length/shank/head diameters; .06in head thickness and.25in point profile are explicit illustrative envelopes, not factory CAD.','sourceURL':'https://dublin.ca.gov/DocumentCenter/View/6881/Residential-Nailing-Schedule'}
ws_spec={'manufacturer':'Simpson Strong-Tie','partNumber':'WSV212S','lengthIn':2.5,'majorDiameterIn':.182,'shankDiameterIn':.132,'headDiameterIn':.333,'threadLengthIn':1.95,'drive':'T25','material':'Yellow-zinc-coated steel','installation':'Chosen panel schedule: at most 6 in at edges and 12 in at intermediate supports; minimum 3/8-in panel-edge setback and 1-3/8-in receiving-wood penetration. Set countersunk heads flush.','geometryProfile':'Conservative major-thread occupancy; nibs, exact thread helix and T25 recess not represented. Head cone is an explicit90degree depiction.','sourceURL':'https://www.strongtie.com/strongdrive_subfloorandsheathingfasteners/wsv_screw/p/strong-drive-wsv-subfloor-screw'}
# TIMESTAMP START 2026-11-05T07:15:21+00:00 | REVISION R000031
def emit(pid,key,prototype,point,axis,receivers,spec,role,parent,checks,matrix=None):
 matrix=fastener_transform(point,axis) if matrix is None else matrix;shape=prototype.transform(matrix)
# TIMESTAMP END 2026-11-05T07:15:21+00:00 | REVISION R000031
 for other,obstacle in fastener_solids.items():
  aa,bb=shape.bounding_box(),obstacle.bounding_box()
  if all(aa[k+3]>bb[k]+1e-10 and bb[k+3]>aa[k]+1e-10 for k in range(3)):assert (shape^obstacle).volume()<TOL,(pid,other,'fastenercollision')
 fastener_solids[pid]=shape;fastener_receivers[pid]=receivers
 center=np.asarray(point)+np.asarray(axis)*spec['lengthIn']*I/2
 instances.append({'id':pid,'name':spec['partNumber']+' '+role.replace('_',' '),'schematic':True,'schematicKind':'floorAssembly','displayRole':'floorStructure','group':'floor_fasteners','material':spec['material'],'is_timber':False,'is_fastener':True,'mesh_instance':{'prototype':key,'transform':matrix},'center':center.tolist(),'label_position':center.tolist(),'color':[.42,.44,.40],'exploded_offset':[0,0,0],'fastenerSpec':spec,'floorRole':role,'parentId':parent,'receiverIds':receivers,'withdrawal_direction':(-np.asarray(axis)).tolist(),'withdrawal_distance_m':spec['lengthIn']*I+.01,'penetrationCheck':checks,'volumeM3':shape.volume(),'boreBasis':'Occupied steel envelope represents displaced wood. Pilot holes and installation follow the manufacturer; no full-major-diameter predrilling instruction.'})
# Exact end-plane intersections select the real cut end, including angled rims.
for block_id,info in block_info.items():
 block=solids[block_id];seam=info['north'];serial=0
 for end_sign in [1,-1]:
  for side_index,side_sign in enumerate([-1,1]):
   n=seam+side_sign*(.175 if info['bay']%2==0 else .35)*I
   y=joistTop-2*I
   origin=EAST*(-20*.3048)+NORTH*n+UP*y;endpoint=EAST*(20*.3048)+NORTH*n+UP*y
   hits=block.ray_cast(origin.tolist(),endpoint.tolist());assert len(hits)>=2,(block_id,'Missingrealend')
   values=[np.dot(hit.position,EAST) for hit in hits];end=min(values) if end_sign==1 else max(values)
   axis=-end_sign*math.cos(math.pi/6)*EAST-.5*UP
   entry=EAST*(end+end_sign*nail_length/3)+NORTH*n+UP*joistTop
   # A nail set drives the angled round head below the deck bearing plane.
   point=entry+axis*.32*I
   receivers=[];lengths={}
   for support_id in support_ids:
    intervals=ray_intervals(solids[support_id],point,axis,nail_length);length=sum(b-a for a,b in intervals)
    if length>1e-8:receivers.append(support_id);lengths[support_id]=length/I
   assert lengths and max(lengths.values())>=6*.131-1e-6,(block_id,end_sign,side_sign,'Insufficientreceivingwood',lengths)
   serial+=1;emit(block_id+'-NAIL-'+str(serial),'FLOOR-8DHDGPT',nail,point,axis,[block_id]+receivers,nail_spec,'blocking_nail',block_id,{'receivingWoodLengthIn':lengths,'minimumIn':6*.131,'entryStartFromEndIn':2.5/3,'drivenHeadRecessAlongAxisIn':.32,'basis':'Exact native ray intersections including tapered tip. Top-entry toe angle30degrees; set head below deck bearing plane before sheathing.'})
# TIMESTAMP START 2026-11-05T07:15:21+00:00 | REVISION R000031
for key,record in edge_supports['support']['hardware_prototypes'].items():
 actual=floor_edge_supports.solid(prototypes[key]);reference=floor_edge_supports.solid(record)
 assert abs((actual-reference).volume())+abs((reference-actual).volume())<=TOL,('Support hardware prototype changed',key)
receipts={p['fastener']:p for p in edge_supports['support']['fastener_receiver_mapping']}
for p in edge_supports['support']['hardware_instances']:
 key=p['mesh_instance']['prototype'];prototype=wsv if key=='FLOOR-WSV212S' else nail
 ledger=key=='FLOOR-WSV212S';spec={**(ws_spec if ledger else nail_spec)};receipt=receipts[p['id']]
 if ledger:spec['installation']='Two horizontal screws through the broad face of each eight-inch rim ledger into existing rim wood. Actual receiving penetration1.8972in; connection capacity unqualified.'
 emit(p['id'],key,prototype,p['prototype_origin_m'],p['axis_m'],[p['donor'],*p['receiver_ids']],spec,'ledger_screw' if ledger else 'trimmer_nail',p['donor'],receipt,matrix=p['mesh_instance']['transform'])
# TIMESTAMP END 2026-11-05T07:15:21+00:00 | REVISION R000031
# Perimeter points follow actual cut edges, rather than treating a cut octagon
# sheet as an uncut rectangle. Field lines follow actual joist centers.
wood_ids=[pid for pid in solids if pid.startswith(('FLOOR-JOIST-','FLOOR-RIM-','FLOOR-BLOCKING-','FLOOR-BEAM-'))]
# TIMESTAMP START 2026-11-05T07:15:21+00:00 | REVISION R000031
base_wood_ids=wood_ids.copy()
wood_ids.extend(p['id'] for p in edge_supports['support']['unbored_installed_wood'] if p['id'] not in wood_ids)
# TIMESTAMP END 2026-11-05T07:15:21+00:00 | REVISION R000031
steel_obstacles={pid:shape for pid,shape in solids.items() if 'steel' in materials[pid]}
# TIMESTAMP START 2026-11-05T07:15:21+00:00 | REVISION R000031
# Retain the verified base screw placement, then fill its measured gaps with
# the explicit34 placements below. New backers must not create guessed extras.
wood_union=m.Manifold.batch_boolean([solids[p] for p in base_wood_ids],m.OpType.Add)
# TIMESTAMP END 2026-11-05T07:15:21+00:00 | REVISION R000031
world_to_floor=np.column_stack([FLOOR_BASIS.T,np.zeros(3)]).tolist();skipped_edges=[];sheet_fastener_counts={}
for sheet_id in sheet_info:
 sheet=solids[sheet_id];section=sheet.transform(world_to_floor).slice(deck['topY_M']-deck['thicknessM']/2);inset=section.offset(-.4375*I);points=[]
 for poly in inset.to_polygons():
  for a,b in zip(poly,np.roll(poly,-1,axis=0)):
   distance=np.linalg.norm(b-a);count=max(1,math.ceil(distance/(5.5*I)))
   points.extend(a+(b-a)*(k/count) for k in range(count))
 stock=sheet_info[sheet_id]['sheet_stock'];emin,emax=stock['eastBoundsM'];nmin,nmax=stock['northBoundsM']
 for e in joist_stations:
  if not emin+.4375*I<e<emax-.4375*I:continue
  for n in np.arange(nmin+.5*I,nmax-.4375*I,11.5*I):points.append(np.array([e,n]))
 used=[];serial=0
 for index,q in enumerate(points):
  if any(np.linalg.norm(q-p)<.75*I for p in used):continue
  success=False
  for de,dn in [(0,0),(.125*I,0),(-.125*I,0),(0,.125*I),(0,-.125*I),(.25*I,0),(-.25*I,0)]:
   e,n=q+np.array([de,dn]);point=EAST*e+NORTH*n+UP*deck['topY_M'];probe=m.Manifold.cylinder(.0001,.375*I,.375*I,32).rotate([90,0,0]).translate((point-UP*deck['thicknessM']/2).tolist())
   if (probe-sheet).volume()>TOL:continue
   below=point-UP*(deck['thicknessM']-1e-7);length=ws_length-deck['thicknessM']+1e-7;intervals=ray_intervals(wood_union,below,-UP,length)
   if not intervals or intervals[0][0]>1e-6 or intervals[0][1]<1.375*I:continue
   shape=wsv.transform(fastener_transform(point,-UP));collision=False
   # A wood screw must clear the actual steel bearing stand, including its
   # head plate. A ray through adjacent wood alone does not establish clearance.
   for other in [*steel_obstacles.values(),*fastener_solids.values()]:
    aa,bb=shape.bounding_box(),other.bounding_box()
    if all(aa[k+3]>bb[k]+1e-10 and bb[k+3]>aa[k]+1e-10 for k in range(3)) and (shape^other).volume()>TOL:collision=True;break
   if collision:continue
   receivers=[];embed={}
   for pid in wood_ids:
    vals=ray_intervals(solids[pid],below,-UP,length);amount=sum(b-a for a,b in vals)
    if amount>1e-8:receivers.append(pid);embed[pid]=amount/I
   serial+=1;emit(sheet_id+'-SCREW-'+f'{serial:03d}','FLOOR-WSV212S',wsv,point,-UP,[sheet_id]+receivers,ws_spec,'deck_screw',sheet_id,{'receivingWoodLengthIn':embed,'minimumIn':1.375,'panelEdgeSetbackIn':.375,'basis':'Exact native ray intersections; edge disc contained in occupied sheet'})
   used.append(np.array([e,n]));success=True;break
  if not success:skipped_edges.append({'sheet':sheet_id,'candidate':index,'eastNorthM':q.tolist()})
 assert serial>0,(sheet_id,'Nofasteners',len(points));sheet_fastener_counts[sheet_id]=serial
 print(sheet_id,serial,'sheet screws',flush=True)
# TIMESTAMP START 2026-11-05T07:15:21+00:00 | REVISION R000031
for p in edge_supports['spacing']['parts']:
 point=np.asarray(p['prototype_origin_m']);axis=np.asarray(p['axis_m']);sheet_id=p['sheet'];receivers=[];lengths={}
 for pid in wood_ids:
  intervals=ray_intervals(solids[pid],point+UP*1e-7,axis,ws_length+1e-7)
  length=sum(b-a for a,b in intervals)
  if length>1e-8:receivers.append(pid);lengths[pid]=length/I
 assert lengths and max(lengths.values())>=1.375-1e-6,('Gap fill lost receiving wood',p['id'],lengths)
 probe=m.Manifold.cylinder(.0001,.375*I,.375*I,32).rotate([90,0,0]).translate((point-UP*deck['thicknessM']/2).tolist())
 assert (probe-solids[sheet_id]).volume()<=TOL,('Gap fill lost panel-edge setback',p['id'])
 shape=wsv.transform(p['mesh_instance']['transform'])
 for sid,obstacle in steel_obstacles.items():
  aa,bb=shape.bounding_box(),obstacle.bounding_box()
  if all(aa[k+3]>bb[k] and bb[k+3]>aa[k] for k in range(3)):assert (shape^obstacle).volume()<=TOL,(p['id'],sid,'Gap fill hits steel')
 emit(p['id'],'FLOOR-WSV212S',wsv,point,axis,[sheet_id,*receivers],ws_spec,'deck_screw',sheet_id,
      {'receivingWoodLengthIn':lengths,'minimumIn':1.375,'panelEdgeSetbackIn':p['panel_edge_setback_in'],'basis':p['reason']},matrix=p['mesh_instance']['transform'])
 sheet_fastener_counts[sheet_id]+=1
# TIMESTAMP END 2026-11-05T07:15:21+00:00 | REVISION R000031
# Cut only actual fastener occupancy from every receiving wood piece, and record
# every matching bore/wood-displacement envelope for independent readback.
for pid in list(solids):
 if not (pid in wood_ids or pid in sheet_info):continue
 shape=solids[pid];cutters=[];ids=[]
 extra_metadata.setdefault(pid,{})['display_mesh']={**packed(shape),'geometry_purpose':'Rendering envelope before concealed fastener bores. Physical occupied mesh and verification use the detailed vertices and triangles.'}
 for fid,tool in fastener_solids.items():
  aa,bb=shape.bounding_box(),tool.bounding_box()
  if not all(aa[k+3]>bb[k]+1e-10 and bb[k+3]>aa[k]+1e-10 for k in range(3)):continue
  if (shape^tool).volume()>TOL:cutters.append(tool);ids.append(fid)
 if cutters:
  combined=m.Manifold.batch_boolean(cutters,m.OpType.Add);after=shape-combined
  assert len([p for p in after.decompose() if p.volume()>1e-16])==1,(pid,'Boresdisconnectwood')
  solids[pid]=after;extra_metadata.setdefault(pid,{}).update(fastenerBoreIds=ids,fastenerDisplacedWoodM3=shape.volume()-after.volume())
fastener_summary={'blockingBoards':len(block_info),'blockingNails':sum(p['floorRole']=='blocking_nail' for p in instances),'deckScrews':sum(p['floorRole']=='deck_screw' for p in instances),'sheetFastenerCounts':sheet_fastener_counts,'skippedUnsupportedCandidates':skipped_edges,'scope':'Actual installed counts and individual occupied fasteners. Remaining unsupported candidate locations require edge-support review; no structural capacity or complete edge-spacing claim.'}
# TIMESTAMP START 2026-11-05T07:15:21+00:00 | REVISION R000031
fastener_summary.update(edgeBackingPieces=24,trimmerNails=sum(p['floorRole']=='trimmer_nail' for p in instances),ledgerScrews=sum(p['floorRole']=='ledger_screw' for p in instances),explicitGapFillDeckScrews=34,
 sourceEdgeSupportFixtureSha256=edge_supports['fixture_sha256'],unboredInputCompatibility=edge_input_check,
 scope='Individually modeled installed fasteners; rejected candidates are not required missing fasteners. Fresh final bearing, edge/field interval and whole-scene audits remain separate. No project load capacity is assigned.')
# TIMESTAMP END 2026-11-05T07:15:21+00:00 | REVISION R000031
parts=[]
for id,s in solids.items():
# TIMESTAMP START 2026-11-02T20:27:45-05:00 | REVISION R004866
 mesh=s.to_mesh64();v=np.array(mesh.vert_properties)[:,:3];parts.append({'id':id,'name':id,'schematic':True,'schematicKind':'floorAssembly','group':'floor_foundation_proposal','color':([.73,.72,.68] if materials[id]=='concrete' else [.29,.32,.34] if 'steel' in materials[id] else [.63,.45,.26]),'material':materials[id],'is_timber':False,'vertices':v.tolist(),'triangles':mesh.tri_verts.tolist(),'center':((v.min(0)+v.max(0))/2).tolist(),'exploded_offset':[0,0,0],'volumeM3':s.volume(),'underground':id.endswith('-BELOW'),'displayOpacity':.28 if id.endswith('-BELOW') else 1,'status':'Proposed layout/clearance only, capacity and connections undesigned'})
# TIMESTAMP END 2026-11-02T20:27:45-05:00 | REVISION R004866
# TIMESTAMP START 2026-11-04T23:17:24+00:00 | REVISION R000029
for part in parts:part.update(sheet_info.get(part['id'],{}));part.update(extra_metadata.get(part['id'],{}))
parts.extend(instances)
# TIMESTAMP START 2026-11-05T06:36:54+00:00 | REVISION R000029
parts.extend(furniture_parts)
# TIMESTAMP END 2026-11-05T06:36:54+00:00 | REVISION R000029
from physical_data import write_physical_json
# TIMESTAMP START 2026-11-05T08:36:47+00:00 | REVISION R000035
from floor_surface_normalization import normalize_parts
parts,boundary_normalization=normalize_parts(parts)
# TIMESTAMP END 2026-11-05T08:36:47+00:00 | REVISION R000035
# TIMESTAMP START 2026-11-05T06:36:54+00:00 | REVISION R000029
# TIMESTAMP START 2026-11-05T08:36:47+00:00 | REVISION R000035
write_physical_json(arguments.output,{'source_model_sha256':hashlib.sha256(raw).hexdigest(),'source_module_sha256':hashlib.sha256((R/'src/floor-foundation.js').read_bytes()).hexdigest(),'source_furniture_sha256':hashlib.sha256(furniture_path.read_bytes()).hexdigest(),'replacedSchematicIds':furniture['replacedSchematicIds'],'furnitureJoints':furniture['joints'],'layout':layout,'prototypes':prototypes,'revision':'R000029','timestamp':'2026-11-05T06:36:54+00:00','boundaryNormalization':boundary_normalization,'fastenerSummary':fastener_summary,'parts':parts,'source_builder_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'source_sheet_module_sha256':hashlib.sha256((R/'scripts/floor_sheet_panels.py').read_bytes()).hexdigest()})
# TIMESTAMP END 2026-11-05T08:36:47+00:00 | REVISION R000035
# TIMESTAMP END 2026-11-05T06:36:54+00:00 | REVISION R000029
# TIMESTAMP END 2026-11-04T23:17:24+00:00 | REVISION R000029
print(len(parts),'proposed solids')

# TIMESTAMP END 2026-11-04T23:48:03+00:00 | REVISION R000012

# TIMESTAMP END 2026-11-05T04:26:16+00:00 | REVISION R000021

# TIMESTAMP END 2026-11-05T05:14:11+00:00 | REVISION R000024
