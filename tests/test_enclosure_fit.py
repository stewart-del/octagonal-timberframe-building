# TIMESTAMP START 2026-11-02T13:42:10-05:00 | REVISION R004782
"""Verify modeled opening contacts and clearance in every variant, not capacity."""
from pathlib import Path
import hashlib,json,subprocess,sys,itertools
import numpy as np
import manifold3d as m
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'scripts'))
from audit_cavity_fit import inspect_mesh
# TIMESTAMP START 2026-11-02T18:40:43-05:00 | REVISION R004837
from step_lap import contacts
# TIMESTAMP END 2026-11-02T18:40:43-05:00 | REVISION R004837
VARIANTS=[('model-data.json','enclosure-fit.json'),('step-lap-proposed-model.json','step-lap-proposed-enclosure-fit.json'),('top-entry-proposed-model.json','top-entry-proposed-enclosure-fit.json')]
NODE="global.OCTAGON_ENCLOSURE_FIT=require(process.argv[2]);process.stdout.write(JSON.stringify(require('./src/schematic-walls.js').build(require(process.argv[1]).parts)))"
def solid(p):
 s=m.Manifold(m.Mesh64(np.array(p['vertices'],dtype=float),np.array(p['triangles'],dtype=np.uint64)))
 assert str(s.status())=='Error.NoError' and s.volume()>0,p['id']
 return s
def overlap(a,b):
 x,y=a.bounding_box(),b.bounding_box()
 return all(x[i+3]>y[i]+1e-10 and y[i+3]>x[i]+1e-10 for i in range(3))
def section_face(p,axis,coordinate,origin,basis):
 v=(np.asarray(p['vertices'])-origin)@basis.T;polygons=[];other=[i for i in range(3) if i!=axis]
 for triangle in p['triangles']:
  q=v[triangle]
  if max(abs(q[:,axis]-coordinate))>1e-9:continue
  poly=q[:,other]*1e6
  area=sum(poly[i,0]*poly[(i+1)%3,1]-poly[(i+1)%3,0]*poly[i,1] for i in range(3))/2
  if abs(area)<1e-8:continue
  polygons.append(poly if area>0 else poly[::-1])
 return m.CrossSection(polygons)
def contact_area(a,b,axis,coordinate,origin,basis):
 return (section_face(a,axis,coordinate,origin,basis)^section_face(b,axis,coordinate,origin,basis)).area()/1e12
# TIMESTAMP START 2026-11-02T16:10:36-05:00 | REVISION R004814
foundation_path=R/'src/floor-foundation-solids.json'
foundation_raw=foundation_path.read_bytes()
foundation_solids=[solid(p) for p in json.loads(foundation_raw)['parts']]

# TIMESTAMP END 2026-11-02T16:10:36-05:00 | REVISION R004814
checks=0;minimum_contact=float('inf')
for model_name,fit_name in VARIANTS:
 raw=(R/'src'/model_name).read_bytes();model=json.loads(raw);fit=json.loads((R/'src'/fit_name).read_text())
 assert fit['source_model_sha256']==hashlib.sha256(raw).hexdigest()
 assert fit['source_module_sha256']==hashlib.sha256((R/'src/schematic-walls.js').read_bytes()).hexdigest()
# TIMESTAMP START 2026-11-02T16:10:36-05:00 | REVISION R004814
 assert fit['source_foundation_sha256']==hashlib.sha256(foundation_raw).hexdigest()
# TIMESTAMP END 2026-11-02T16:10:36-05:00 | REVISION R004814
 layout=json.loads(subprocess.check_output(['node','-e',NODE,str(R/'src'/model_name),str(R/'src'/fit_name)],cwd=R));items=layout['components']
 # TIMESTAMP START 2026-11-02T15:33:07-05:00 | REVISION R004807
 expected={p['id'] for p in items if p['schematicKind'] in ['rail','wall','floor','shelf']}
 # TIMESTAMP END 2026-11-02T15:33:07-05:00 | REVISION R004807
 # TIMESTAMP START 2026-11-02T15:33:07-05:00 | REVISION R004807
 assert set(fit['parts'])==expected,'Every generated framing, infill, floor and shelf ID needs a current fitted mesh'
 # TIMESTAMP END 2026-11-02T15:33:07-05:00 | REVISION R004807
 frames=[p for p in items if p['schematicKind']=='rail'];infill=[p for p in items if p['schematicKind']=='wall'];floor=[p for p in items if p['schematicKind']=='floor']
 # TIMESTAMP START 2026-11-02T14:35:15-05:00 | REVISION R004794
 # TIMESTAMP START 2026-11-02T18:13:09-05:00 | REVISION R004829
 assert len(frames)==74 and len(infill)==81 and len(floor)==8
 # TIMESTAMP END 2026-11-02T18:13:09-05:00 | REVISION R004829
 # TIMESTAMP END 2026-11-02T14:35:15-05:00 | REVISION R004794
 assert {role:sum(p['framingRole']==role for p in frames) for role in ['jamb','header','sill']}=={'jamb':12,'header':6,'sill':5}
 # TIMESTAMP START 2026-11-02T15:33:07-05:00 | REVISION R004807
 # TIMESTAMP START 2026-11-02T17:45:34-05:00 | REVISION R004824
 timbers={p['id']:solid(p) for p in model['parts'] if p['is_timber'] or p.get('group')=='joinery_pegs'};footers=[solid(p) for p in items if p['schematicKind']=='footer'];shelves=[p for p in items if p['schematicKind']=='shelf'];solids={p['id']:solid(p) for p in frames+infill+floor+shelves}
 # TIMESTAMP END 2026-11-02T17:45:34-05:00 | REVISION R004824
 # TIMESTAMP END 2026-11-02T15:33:07-05:00 | REVISION R004807
 # TIMESTAMP START 2026-11-02T15:33:07-05:00 | REVISION R004807
 for p in frames+infill+floor+shelves:
 # TIMESTAMP END 2026-11-02T15:33:07-05:00 | REVISION R004807
  s=solids[p['id']]
  # TIMESTAMP START 2026-11-02T15:33:07-05:00 | REVISION R004807
  # TIMESTAMP START 2026-11-02T18:13:09-05:00 | REVISION R004829
  if p['schematicKind'] in ['rail','shelf','wall']:
  # TIMESTAMP END 2026-11-02T18:13:09-05:00 | REVISION R004829
  # TIMESTAMP END 2026-11-02T15:33:07-05:00 | REVISION R004807
   assert len(s.decompose())==1,p['id']+' must remain one continuous piece after brace clearance'
   assert inspect_mesh(np.asarray(p['vertices']),np.asarray(p['triangles']))['status']=='PASS',p['id']
# TIMESTAMP START 2026-11-02T16:10:36-05:00 | REVISION R004814
  for t in (footers+foundation_solids if p['schematicKind']=='floor' else timbers.values()):
# TIMESTAMP END 2026-11-02T16:10:36-05:00 | REVISION R004814
   if overlap(s,t):assert (s^t).volume()<1e-10,p['id']
 # TIMESTAMP START 2026-11-02T15:33:07-05:00 | REVISION R004807
 # Shelf relief must remove exactly occupied timber, preserving board middles.
 raw_items=json.loads(subprocess.check_output(['node','-e',"process.stdout.write(JSON.stringify(require('./src/schematic-walls.js').build(require(process.argv[1]).parts,{applyFit:false}).components))",str(R/'src'/model_name)],cwd=R))
 # TIMESTAMP START 2026-11-02T18:40:43-05:00 | REVISION R004837
 # Every relief must be actual permanent timber/peg occupancy. The optional
 # porch cannot leave porch-shaped holes when the standalone room is shown.
 raw_by_id={p['id']:p for p in raw_items}
 assert 'source_porch_sha256' not in fit
 porch=json.loads(subprocess.check_output(['node','-e',"process.stdout.write(JSON.stringify(require('./src/mudroom.js').build(require(process.argv[1])).components))",str(R/'src'/model_name)],cwd=R))
 porch_solids={p['id']:solid(p) for p in porch}
 for p in frames+infill:
  expected=solid(raw_by_id[p['id']])
  for obstacle in timbers.values():
   if overlap(expected,obstacle):expected=expected-obstacle
  actual=solids[p['id']]
  assert abs((expected-actual).volume())+abs((actual-expected).volume())<1e-10,(p['id'],'unexpected enclosure material removed')
  for pid,obstacle in porch_solids.items():
   if overlap(actual,obstacle):assert abs((actual^obstacle).volume())<1e-10,(p['id'],pid,'optional porch overlap')
 for connection in layout['railConnections']:
  area=sum(q['area_in2']*.0254**2 for q in contacts(solids[connection['railId']],timbers[connection['postId']]))
  assert area>1e-6,(connection['railId'],connection['postId'],'recessed rail/post contact missing')
 # TIMESTAMP END 2026-11-02T18:40:43-05:00 | REVISION R004837
# TIMESTAMP START 2026-11-02T16:10:36-05:00 | REVISION R004814
 raw_floors={p['id']:p for p in raw_items if p['schematicKind']=='floor'}
 for p in floor:
  before=solid(raw_floors[p['id']]);after=solids[p['id']];occupied=m.Manifold()
  for obstacle in footers+foundation_solids:
   if overlap(before,obstacle):occupied=occupied+(before^obstacle)
  # TIMESTAMP START 2026-11-03T12:04:27-05:00 | REVISION R005002
  # The finish ends at the wall sill footprint instead of being trapped under
  # it. Match only actual sill shadows, retaining the original support cuts.
  for frame in frames:
   obstacle=solids[frame['id']];box=obstacle.bounding_box()
   if box[1]<=1e-8 and box[4]>=.05:
    cutter=obstacle.translate([0,-.05,0])
    if overlap(before,cutter):occupied=occupied+(before^cutter)
  removed=before-after
  assert (removed-occupied).volume()<1e-10 and (occupied-removed).volume()<1e-10,p['id']+' floor relief must match support geometry and covered sill footprints'
  # TIMESTAMP END 2026-11-03T12:04:27-05:00 | REVISION R005002
  assert len(after.decompose())==len(before.decompose()),p['id']+' retain every existing bamboo plank without detached offcuts'
  assert inspect_mesh(np.asarray(p['vertices']),np.asarray(p['triangles']),require_single=False)['status']=='PASS',p['id']+' raw floor mesh'

# TIMESTAMP END 2026-11-02T16:10:36-05:00 | REVISION R004814
 raw_shelves={p['id']:p for p in raw_items if p['schematicKind']=='shelf'}
 # TIMESTAMP START 2026-11-02T18:13:09-05:00 | REVISION R004829
 assert len(shelves)==12 and len(fit['parts'])==175
 # TIMESTAMP END 2026-11-02T18:13:09-05:00 | REVISION R004829
 changed_shelves=[]
 for p in shelves:
  before=solid(raw_shelves[p['id']]);after=solids[p['id']];expected_cut=m.Manifold()
  for timber in timbers.values():
   if overlap(before,timber):expected_cut=expected_cut+(before^timber)
  removed=before-after
  assert abs((after-before).volume())<1e-10,p['id']+' added shelf stock'
  exact_remainder=before-expected_cut
  offcuts=fit['parts'][p['id']]['discarded_end_offcuts'];offcut_union=m.Manifold()
  for index,record in enumerate(offcuts):
   offcut=solid(dict(record,id=p['id']+'-offcut-'+str(index)))
   assert abs((offcut-after).volume()-offcut.volume())<1e-10
   assert offcut.min_gap(after,.1)>1e-5 and after.volume()>offcut.volume(),p['id']+' offcut not separate from shelf middle'
   assert abs((offcut-exact_remainder).volume())<1e-10
   offcut_union=offcut_union+offcut
  accounted_cut=expected_cut+offcut_union
  assert abs((removed-accounted_cut).volume())<1e-10 and abs((accounted_cut-removed).volume())<1e-10,p['id']+' shelf stock unaccounted'
  reconstructed=after+offcut_union
  assert abs((reconstructed-exact_remainder).volume())<1e-10 and abs((exact_remainder-reconstructed).volume())<1e-10,p['id']+' connected shelf middle or offcuts changed'
  # TIMESTAMP START 2026-11-02T17:45:34-05:00 | REVISION R004824
  # TIMESTAMP START 2026-11-02T18:40:43-05:00 | REVISION R004837
  # TIMESTAMP START 2026-11-04T13:00:51+00:00 | REVISION R000007
  # TIMESTAMP START 2026-11-04T20:54:04+00:00 | REVISION R000025
  # The longer inward supports now cross the ends of the fourth shelves.
  # Keep exact stock reconstruction above: each recorded end must be separate
  # waste, and all retained wood must remain the single connected middle.
  expected_offcuts=2 if p['id'] in ['SCHEM-N-shelf4','SCHEM-S-shelf4'] else 0
  assert len(offcuts)==expected_offcuts,p['id']+' unexpected detached shelf stock'
  # TIMESTAMP END 2026-11-04T20:54:04+00:00 | REVISION R000025
  # TIMESTAMP END 2026-11-04T13:00:51+00:00 | REVISION R000007
  # TIMESTAMP END 2026-11-02T18:40:43-05:00 | REVISION R004837
  # TIMESTAMP END 2026-11-02T17:45:34-05:00 | REVISION R004824

  assert len(after.decompose())==1,p['id']+' split shelf board'
  if removed.volume()>1e-10:changed_shelves.append(p['id'])
 # TIMESTAMP START 2026-11-02T18:40:43-05:00 | REVISION R004837
 assert sorted(changed_shelves)==sorted(p['id'] for p in shelves),'Extended shelf backs meet the post envelope and must receive its exact relief'
 # TIMESTAMP END 2026-11-02T18:40:43-05:00 | REVISION R004837
 # TIMESTAMP END 2026-11-02T15:33:07-05:00 | REVISION R004807
 # All new framing and infill must be disjoint, including at neighboring walls.
 # TIMESTAMP START 2026-11-02T18:40:43-05:00 | REVISION R004837
 for a,b in itertools.combinations(frames+infill+shelves,2):
 # TIMESTAMP END 2026-11-02T18:40:43-05:00 | REVISION R004837
  sa,sb=solids[a['id']],solids[b['id']]
  if overlap(sa,sb):assert (sa^sb).volume()<1e-10,(a['id'],b['id'])
 by_id={p['id']:p for p in items};canonical={p['id']:p for p in model['parts']}
 # TIMESTAMP START 2026-11-02T18:40:43-05:00 | REVISION R004837
 for p in frames:
  if '-rail0-' not in p['id']:continue
  # TIMESTAMP START 2026-11-03T12:04:27-05:00 | REVISION R005002
  gap=min(solids[p['id']].min_gap(solids[q['id']],.01) for q in floor)
  assert gap<1e-7,(p['id'],'finish edge must meet the sill without extending underneath it')
  # TIMESTAMP END 2026-11-03T12:04:27-05:00 | REVISION R005002
 for face in ['N','S']:
  wall=next(w for w in layout['walls'] if w['face']==face)
  a=np.asarray(canonical[wall['postIds'][0]]['center']);b=np.asarray(canonical[wall['postIds'][1]]['center']);origin=(a+b)/2;origin[1]=0
  u=b-a;u[1]=0;u/=np.linalg.norm(u);normal=origin/np.linalg.norm(origin);basis=np.array([u,[0,1,0],normal])
  shelf=by_id['SCHEM-'+face+'-shelf2'];rail=by_id['SCHEM-'+face+'-rail1-0']
  assert shelf['localBounds'][4:]==[-.40,.0508]
  assert contact_area(shelf,rail,2,.0508,origin,basis)>1e-4,(face,'shelf back must touch the recessed rail')
 # TIMESTAMP END 2026-11-02T18:40:43-05:00 | REVISION R004837
 for wall in layout['walls']:
  if not wall['opening']:continue
  o=wall['opening'];w=o['width']/2;face=wall['face'];a=np.asarray(canonical[wall['postIds'][0]]['center']);b=np.asarray(canonical[wall['postIds'][1]]['center']);origin=(a+b)/2;origin[1]=0;u=b-a;u[1]=0;u/=np.linalg.norm(u);normal=origin/np.linalg.norm(origin);basis=np.array([u,[0,1,0],normal])
  # TIMESTAMP START 2026-11-02T18:32:34-05:00 | REVISION R004834
  assert o['top']==(2.10 if face=='W' else 1.85),(face,'common window head elevation')
  if face=='E':
   assert o['bottom']==.75 and o['width']==wall['width']*.65,'Preserve wide east window sill and width'
  header=by_id['SCHEM-'+face+'-rail-header']
  if face!='W':
   assert header['localBounds'][2:4]==[1.85,1.85+.1524]
   assert abs(max(v[1] for v in header['vertices'])-(1.85+.1524))<1e-9,(face,'actual header top must match neighboring windows')
  # TIMESTAMP END 2026-11-02T18:32:34-05:00 | REVISION R004834
  local_members=[p for p in frames+infill if p['face']==face]
  for p in local_members:
   q=(np.asarray(p['vertices'])-origin)@basis.T
   # Each fitted piece remains wholly on one side of the exact clear aperture.
   assert q[:,0].max()<=-w+1e-9 or q[:,0].min()>=w-1e-9 or q[:,1].max()<=o['bottom']+1e-9 or q[:,1].min()>=o['top']-1e-9,p['id']
  jambs=[by_id['SCHEM-'+face+'-rail-jamb-'+side] for side in ['left','right']]
  horizontal=[by_id['SCHEM-'+face+'-rail-header']]
  if face!='W':horizontal.append(by_id['SCHEM-'+face+'-rail-sill'])
  else:assert 'SCHEM-W-rail-sill' not in by_id and o['bottom']==wall['base']==0
  for jamb,x in zip(jambs,[-w,w]):
   for member in horizontal:
    area=contact_area(jamb,member,0,x,origin,basis);assert area>1e-6,(jamb['id'],member['id'],'missing face contact');minimum_contact=min(minimum_contact,area);checks+=1
   # TIMESTAMP START 2026-11-02T18:40:43-05:00 | REVISION R004837
   # TIMESTAMP START 2026-11-03T06:58:53-05:00 | REVISION R004899
   # A full4x4 jamb has4x2 inches of contact on the two-inch-deep bottom rail.
   # TIMESTAMP END 2026-11-03T06:58:53-05:00 | REVISION R004899
   foot_y=jamb['localBounds'][2]
   bearing=sum(contact_area(jamb,p,1,foot_y,origin,basis) for p in local_members if p.get('framingRole')=='rail')
   # TIMESTAMP START 2026-11-03T06:58:53-05:00 | REVISION R004899
   assert abs(bearing-.1016*.0508)<1e-10,(jamb['id'],'4x2-inch jamb-to-rail contact',bearing)
   # TIMESTAMP END 2026-11-03T06:58:53-05:00 | REVISION R004899
   # TIMESTAMP END 2026-11-02T18:40:43-05:00 | REVISION R004837
   checks+=1
   # The jamb reaches the unchanged ring-beam underside with actual face contact.
   area=contact_area(jamb,canonical['B'+wall['postIds'][0][1:]],1,wall['height'],origin,basis)
   assert area>1e-6,(jamb['id'],'ring beam contact');minimum_contact=min(minimum_contact,area);checks+=1
   for member in local_members:
    if member.get('framingRole')!='rail':continue
    lo,hi,y0,y1=member['localBounds'][:4];j0,j1=jamb['localBounds'][:2]
    interface=j0 if abs(hi-j0)<1e-9 else j1 if abs(lo-j1)<1e-9 else None
    if interface is None:continue
    area=contact_area(jamb,member,0,interface,origin,basis)
    assert area>1e-6,(jamb['id'],member['id'],'rail must meet jamb');minimum_contact=min(minimum_contact,area);checks+=1
 # Preserve the original floor boundary regression as wall framing changes.
 for k,p in enumerate(floor):
  normal=np.array([np.cos((k+.5)*np.pi/4),0,-np.sin((k+.5)*np.pi/4)])
  post=canonical['P'+str(k)];radius=np.hypot(post['center'][0],post['center'][2]);target=radius*np.cos(np.pi/8)-.05
  # TIMESTAMP START 2026-11-03T12:04:27-05:00 | REVISION R005002
  edge=max(np.array(p['vertices'])@normal)
  assert target-.00080001<=edge<=target+1e-8,(p['id'],'only the covered 0.8 mm sill-edge strip may recede')
  # TIMESTAMP END 2026-11-03T12:04:27-05:00 | REVISION R005002
 assert all('unresolved' in q['status'] for q in layout['railConnections'])
 assert (R/'src'/model_name).read_bytes()==raw
# TIMESTAMP START 2026-11-02T15:33:07-05:00 | REVISION R004807
print(f'PASS: all three variants; 12 continuous jambs, 6 headers, 5 sills each; {checks} fitted face contacts (minimum {minimum_contact:.9g} m²); no framing/infill/shelf/primary-timber overlaps; clear apertures and threshold preserved')
# TIMESTAMP END 2026-11-02T15:33:07-05:00 | REVISION R004807
# TIMESTAMP END 2026-11-02T13:42:10-05:00 | REVISION R004782
