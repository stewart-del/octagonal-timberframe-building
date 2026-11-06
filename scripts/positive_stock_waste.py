# TIMESTAMP START 2026-11-06T01:05:01+00:00 | REVISION R000078
"""Construct positive offcut chunks from the actual current stock difference.

This supplies candidates only. The consuming stock owner must independently
prove world/local partition, volume, containment and pairwise nonoverlap.
"""
import numpy as np
from cupola_joinery_recipe import native_solid,amount,I,TOL
from audit_cavity_fit import inspect_mesh
from floor_surface_normalization import regular_local
def raw(solid):
 mesh=solid.to_mesh64();return {'vertices':np.asarray(mesh.vert_properties)[:,:3].tolist(),'triangles':np.asarray(mesh.tri_verts).astype(int).tolist()}
def cutting_plane(solid):
 """Expose an actual enclosed negative boundary to a new offcut face."""
 record=raw(solid);v=np.asarray(record['vertices']);faces=np.asarray(record['triangles'],np.uint64);parents=list(range(len(faces)));edges={}
 def root(k):
  while parents[k]!=k:parents[k]=parents[parents[k]];k=parents[k]
  return k
 for index,face in enumerate(faces):
  for a,b in zip(face,np.roll(face,-1)):
   key=tuple(sorted((int(a),int(b))))
   if key in edges:parents[root(index)]=root(edges[key])
   else:edges[key]=index
 groups={}
 for index in range(len(faces)):groups.setdefault(root(index),[]).append(index)
 candidates=[]
 for indices in groups.values():
  selected=faces[indices];points=v[np.unique(selected)];origin=points.mean(0);triangles=v[selected]-origin;volume=float(np.einsum('ij,ij->i',triangles[:,0],np.cross(triangles[:,1],triangles[:,2])).sum()/6)
  if volume<-1e-6:candidates.append((volume,points))
 points=min(candidates,key=lambda row:row[0])[1]if candidates else v;low,high=points.min(0),points.max(0);axis=int(np.argmax(high-low));normal=np.eye(3)[axis];return normal,float((low[axis]+high[axis])/2)
def candidate(blank,children,basis,origin,*,max_splits=64):
 basis=np.asarray(basis,float);origin=np.asarray(origin,float);assert basis.shape==(3,3)and np.max(abs(basis.T@basis-np.eye(3)))<1e-9 and abs(np.linalg.det(basis)-1)<1e-9,'Positive stock construction requires proper physical axes';to_local=np.column_stack([basis.T/I,-basis.T@origin/I]);to_world=np.column_stack([basis*I,origin]);stock=native_solid(blank).transform(to_local.tolist());installed=[native_solid(p).transform(to_local.tolist())for p in children];waste=stock
 for part in installed:waste=waste-part
 stack=[waste];pieces=[];splits=0;discarded=0.
 while stack:
  solid=stack.pop();components=solid.decompose()
  if any(part.volume()<-1e-6 for part in components):physical=[solid];residue=0.
  else:physical=[part for part in components if part.volume()>1e-6];residue=sum(abs(part.volume())for part in components if part.volume()<=1e-6)
  discarded+=residue;assert discarded<=1e-6,'Stock construction numerical residue exceeds the original occupied-volume limit'
  if len(physical)!=1:stack.extend(physical);continue
  solid=physical[0];found=None
  for conditioned in [False,True]:
   try:
    shaped=regular_local(solid,1e-10/I)if conditioned else solid;record=raw(shaped.transform(to_world.tolist()));audit=inspect_mesh(np.asarray(record['vertices']),np.asarray(record['triangles'],np.uint64),True)
    if audit['status']=='PASS':found=record;break
   except (AssertionError,RuntimeError,ValueError):continue
  if found is not None:pieces.append(found);continue
  assert splits<max_splits,'Positive stock subdivision exhausted; retain blocked source diagnostics';normal,offset=cutting_plane(solid);children=solid.split_by_plane(normal.tolist(),offset);assert all(part.volume()>1e-6 for part in children),'A subdivision must create two actual positive offcuts';stack.extend(children);splits+=1
 assert pieces,'No positive stock waste was constructed'
 return {'declared_exterior_offcut_pieces':pieces}
# TIMESTAMP END 2026-11-06T01:05:01+00:00 | REVISION R000078
