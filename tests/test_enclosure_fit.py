# TIMESTAMP START 2026-11-02T13:42:10-05:00 | REVISION R004782
"""Verify modeled opening contacts and clearance in every variant, not capacity."""
from pathlib import Path
import hashlib,json,subprocess,sys,itertools
import numpy as np
import manifold3d as m
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'scripts'))
from audit_cavity_fit import inspect_mesh
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
checks=0;minimum_contact=float('inf')
for model_name,fit_name in VARIANTS:
 raw=(R/'src'/model_name).read_bytes();model=json.loads(raw);fit=json.loads((R/'src'/fit_name).read_text())
 assert fit['source_model_sha256']==hashlib.sha256(raw).hexdigest()
 assert fit['source_module_sha256']==hashlib.sha256((R/'src/schematic-walls.js').read_bytes()).hexdigest()
 layout=json.loads(subprocess.check_output(['node','-e',NODE,str(R/'src'/model_name),str(R/'src'/fit_name)],cwd=R));items=layout['components']
 expected={p['id'] for p in items if p['schematicKind'] in ['rail','wall','floor']}
 assert set(fit['parts'])==expected,'Every generated framing, infill and floor ID needs a current fitted mesh'
 frames=[p for p in items if p['schematicKind']=='rail'];infill=[p for p in items if p['schematicKind']=='wall'];floor=[p for p in items if p['schematicKind']=='floor']
 assert len(frames)==79 and len(infill)==71 and len(floor)==8
 assert {role:sum(p['framingRole']==role for p in frames) for role in ['jamb','header','sill']}=={'jamb':12,'header':6,'sill':5}
 timbers={p['id']:solid(p) for p in model['parts'] if p['is_timber']};footers=[solid(p) for p in items if p['schematicKind']=='footer'];solids={p['id']:solid(p) for p in frames+infill+floor}
 for p in frames+infill+floor:
  s=solids[p['id']]
  if p['schematicKind']=='rail':
   assert len(s.decompose())==1,p['id']+' must remain one continuous piece after brace clearance'
   assert inspect_mesh(np.asarray(p['vertices']),np.asarray(p['triangles']))['status']=='PASS',p['id']
  for t in (footers if p['schematicKind']=='floor' else timbers.values()):
   if overlap(s,t):assert (s^t).volume()<1e-10,p['id']
 # All new framing and infill must be disjoint, including at neighboring walls.
 for a,b in itertools.combinations(frames+infill,2):
  sa,sb=solids[a['id']],solids[b['id']]
  if overlap(sa,sb):assert (sa^sb).volume()<1e-10,(a['id'],b['id'])
 by_id={p['id']:p for p in items};canonical={p['id']:p for p in model['parts']}
 for wall in layout['walls']:
  if not wall['opening']:continue
  o=wall['opening'];w=o['width']/2;face=wall['face'];a=np.asarray(canonical[wall['postIds'][0]]['center']);b=np.asarray(canonical[wall['postIds'][1]]['center']);origin=(a+b)/2;origin[1]=0;u=b-a;u[1]=0;u/=np.linalg.norm(u);normal=origin/np.linalg.norm(origin);basis=np.array([u,[0,1,0],normal])
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
   # Full 6×6-inch foot bearing on a continuous bottom rail, not floor finish.
   foot_y=jamb['localBounds'][2]
   bearing=sum(contact_area(jamb,p,1,foot_y,origin,basis) for p in local_members if p.get('framingRole')=='rail')
   assert abs(bearing-.1524**2)<1e-10,(jamb['id'],'full jamb-foot bearing',bearing)
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
  assert abs(max(np.array(p['vertices'])@normal)-target)<1e-8
 assert all('unresolved' in q['status'] for q in layout['railConnections'])
 assert (R/'src'/model_name).read_bytes()==raw
print(f'PASS: all three variants; 12 continuous jambs, 6 headers, 5 sills each; {checks} fitted face contacts (minimum {minimum_contact:.9g} m²); no framing/infill/primary-timber overlaps; clear apertures and threshold preserved')
# TIMESTAMP END 2026-11-02T13:42:10-05:00 | REVISION R004782
