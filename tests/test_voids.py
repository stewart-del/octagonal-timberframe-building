#!/usr/bin/env python3
"""Analytic fixtures for the cavity generator, without external packages."""
import unittest
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import generate_voids as g

def box(lo,hi):
    v=[(x,y,z) for z in [lo[2],hi[2]] for x,y in [(lo[0],lo[1]),(hi[0],lo[1]),(hi[0],hi[1]),(lo[0],hi[1])]]
    return [g.face([v[k] for k in f]) for f in [[0,3,2,1],[4,5,6,7],[0,1,5,4],[1,2,6,5],[2,3,7,6],[3,0,4,7]]]

def surface_volume(mesh):
    v=mesh['vertices']
    return sum(g.dot(v[a],g.cross(v[b],v[c]))/6 for a,b,c in mesh['triangles'])

class GeometryFixtures(unittest.TestCase):
    def test_two_halves_have_cube_boundary_without_partition_wire(self):
        cells=[box((0,0,0),(.5,1,1)),box((.5,0,0),(1,1,1))]
        m=g.mesh(cells)
        self.assertAlmostEqual(surface_volume(m),1)
        self.assertEqual(len(m['edges']),12)
        for tri in m['triangles']:
            xs=[m['vertices'][i][0] for i in tri]
            self.assertFalse(all(abs(x-.5)<1e-9 for x in xs),'Internal partition face survived')

    def test_hollow_cube_retains_inner_boundary_and_volume(self):
        stock=box((0,0,0),(1,1,1));inside=box((.25,.25,.25),(.75,.75,.75))
        remaining=g.difference(stock,inside);m=g.mesh(remaining)
        self.assertAlmostEqual(m['volume_m3'],.875)
        self.assertAlmostEqual(surface_volume(m),.875)
        self.assertEqual(len(m['edges']),24)

    def test_touching_does_not_become_positive_overlap(self):
        a=box((0,0,0),(1,1,1))
        for lo in [(1,0,0),(1,1,0),(1,1,1)]:
            b=box(lo,tuple(x+1 for x in lo));self.assertFalse(g.intersect(a,b))

    def test_thin_positive_overlap_is_detected(self):
        a=box((0,0,0),(1,1,1));b=box((1-1e-6,0,0),(2,1,1));overlap=g.intersect(a,b)
        self.assertTrue(overlap);self.assertAlmostEqual(g.volume(overlap),1e-6,places=11)

    def test_occupied_pocket_vs_unfilled(self):
        stock=box((0,0,0),(1,1,1));own=[box((0,0,0),(.5,1,1))];mate=box((.5,0,0),(.75,1,1));offcut=box((.75,0,0),(1,1,1))
        result=g.one_member(('TEST',stock,own,[('MATE',[mate])],[offcut]))
        self.assertAlmostEqual(result['removed']['volume_m3'],.5)
        self.assertAlmostEqual(result['occupied_volume_m3'],.25)
        self.assertAlmostEqual(result['unfilled']['volume_m3'],.25)
        self.assertAlmostEqual(result['unexplained_unfilled_volume_m3'],0)

if __name__=='__main__':unittest.main()
