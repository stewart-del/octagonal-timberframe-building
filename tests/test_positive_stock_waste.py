# TIMESTAMP START 2026-11-06T01:05:01+00:00 | REVISION R000078
"""Closed internal cutouts must become actual positive, disjoint offcuts."""
from pathlib import Path
import sys,unittest
import numpy as np
import manifold3d as manifold
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from positive_stock_waste import candidate,raw
from cupola_joinery_recipe import native_solid,union,amount,diff,I,TOL
from audit_cavity_fit import inspect_mesh
class PositiveWaste(unittest.TestCase):
 def test_enclosed_multiple_installed_children_have_positive_world_partition(self):
  a=.37;basis=np.array([[np.cos(a),-np.sin(a),0],[np.sin(a),np.cos(a),0],[0,0,1]]);origin=np.array([4,-.03,-2]);transform=np.column_stack([basis*I,origin]);blank=manifold.Manifold.cube([20,3,2]).transform(transform.tolist());children=[manifold.Manifold.cube([7,1,1]).translate([x,1,.5]).transform(transform.tolist())for x in [1,11]];records=candidate(raw(blank),[raw(p)for p in children],basis,origin);pieces=[native_solid(p)for p in records['declared_exterior_offcut_pieces']];self.assertGreater(len(pieces),1);self.assertLessEqual(diff(blank,union(children+pieces)),TOL)
  for i,p in enumerate(pieces):
   self.assertGreater(p.volume(),0);self.assertLessEqual(amount(p-blank),TOL)
   for other in children+pieces[:i]:self.assertLessEqual(amount(p^other),TOL)
  for p in records['declared_exterior_offcut_pieces']:self.assertEqual(inspect_mesh(np.asarray(p['vertices']),np.asarray(p['triangles'],np.uint64),True)['status'],'PASS')
 def test_nonrigid_stock_axes_are_refused(self):
  blank=raw(manifold.Manifold.cube([1,1,1]))
  with self.assertRaisesRegex(AssertionError,'proper physical axes'):candidate(blank,[],np.diag([2,1,1]),[0,0,0])
if __name__=='__main__':unittest.main()
# TIMESTAMP END 2026-11-06T01:05:01+00:00 | REVISION R000078
