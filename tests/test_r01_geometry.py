#!/usr/bin/env python3
"""Independent invariants for the R01 pattern, not structural qualification."""
import collections, hashlib, json, math, unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATA=json.loads((ROOT/'src/model-data.json').read_text())
PART={p['id']:p for p in DATA['parts']}
I=.0254

def source(v):return [v[0]/I,-v[2]/I,v[1]/I]
def sub(a,b):return [x-y for x,y in zip(a,b)]
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def length(v):return math.sqrt(dot(v,v))
def radial(k):return [math.cos(k*math.pi/4),math.sin(k*math.pi/4),0]

class R01Geometry(unittest.TestCase):
 def test_inventory_and_retirement(self):
  self.assertEqual(len(PART),120)
  wood=[p['id'] for p in PART.values() if p['is_timber']]
  expected={name for k in range(8) for name in [f'P{k}',f'B{k}',f'T{k}',f'R{k}',f'C{k}',f'L{k}-L',f'L{k}-S',f'L{k}-H',f'K{k}-A',f'K{k}-B',f'J{k}-0',f'J{k}-2']}
  self.assertEqual(set(wood),expected)
  self.assertEqual(set(DATA['r01']['retired_ids']),{f'J{k}-1' for k in range(8)})
  self.assertTrue(all(pid not in PART for pid in DATA['r01']['retired_ids']))
  self.assertTrue(all(PART[f'M-TMP{k}']['temporary'] for k in range(8)))

 def test_finite_closed_meshes(self):
  for p in PART.values():
   with self.subTest(part=p['id']):
    self.assertTrue(all(math.isfinite(x) for v in p['vertices'] for x in v))
    edges=collections.Counter(tuple(sorted((tri[j],tri[(j+1)%3]))) for tri in p['triangles'] for j in range(3))
    self.assertTrue(all(count==2 for count in edges.values()),'Mesh must be closed, including the optional envelope shell')
    self.assertGreater(p['fit_geometry']['volume_m3'],0)
    for v in map(source,p['vertices']):
     self.assertTrue(all(dot(pl['normal'],v)<=pl['constant']+1e-6 for pl in p['geometry_planes_inches']))

 def test_diameter_datums(self):
  for k in range(8):
   r=radial(k)
   self.assertAlmostEqual(dot(source(PART[f'P{k}']['axis_start']),r),176,places=8)
   self.assertAlmostEqual(max(dot(source(v),r) for v in PART[f'P{k}']['vertices']),180,places=8)
   self.assertAlmostEqual(max(dot(source(v),r) for v in PART[f'R{k}']['vertices']),200,places=8)
   self.assertAlmostEqual(max(dot(source(v),r) for v in PART[f'C{k}']['vertices']),44,places=8)
   self.assertAlmostEqual(min(dot(source(v),r) for v in PART[f'C{k}']['vertices']),38,places=8)

 def test_slope_and_sections(self):
  pn=(1/3)/math.cos(math.pi/8)
  for k in range(8):
   hip=PART[f'R{k}'];a,b=map(source,[hip['axis_start'],hip['axis_end']]);delta=sub(b,a)
   self.assertAlmostEqual(delta[2]/math.hypot(*delta[:2]),1/3,places=9)
   self.assertEqual(PART[f'T{k}']['dimensions']['width_in'],6)
   self.assertEqual(PART[f'T{k}']['dimensions']['depth_in'],10)
   for suffix in ['0','2']:
    p=PART[f'J{k}-{suffix}'];a,b=map(source,[p['axis_start'],p['axis_end']]);delta=sub(b,a)
    self.assertAlmostEqual(delta[2]/math.hypot(*delta[:2]),pn,places=9)
    self.assertEqual([p['dimensions']['width_in'],p['dimensions']['depth_in']],[4,8])

 def test_parallel_shorts_and_clear_gap(self):
  for k in range(8):
   a=source(PART[f'J{k}-0']['axis_start']);b=source(PART[f'J{k}-2']['axis_start'])
   self.assertAlmostEqual(math.hypot(a[0]-b[0],a[1]-b[1])-4,42.375,places=8)
   normal=[math.cos((k+.5)*math.pi/4),math.sin((k+.5)*math.pi/4),0]
   side=[-normal[1],normal[0],0]
   for suffix in ['0','2']:
    p=PART[f'J{k}-{suffix}'];a,b=map(source,[p['axis_start'],p['axis_end']])
    self.assertAlmostEqual(dot(sub(b,a),side),0,places=8)
    self.assertAlmostEqual(dot(a,normal),200*math.cos(math.pi/8),places=8)

 def test_every_short_contact_vertex_on_receiving_hip(self):
  for k in range(8):
   for suffix,receiving in [('0',k),('2',(k+1)%8)]:
    p=PART[f'J{k}-{suffix}'];cut=p['joint_cut_faces'][0]
    self.assertEqual(cut['mate_part_id'],f'R{receiving}')
    r=radial(receiving);t=[-r[1],r[0],0];hip=PART[cut['mate_part_id']]
    for v in map(source,cut['vertices']):
     self.assertAlmostEqual(abs(dot(t,v)),4,places=8)
     self.assertTrue(all(dot(pl['normal'],v)<=pl['constant']+1e-6 for pl in hip['geometry_planes_inches']),f'{p["id"]} contact outside receiving hip')
    metadata=p['source_geometry_metadata']['roof_reference']
    self.assertAlmostEqual(metadata['side_face_sloping_length_in'],125.810940162,places=7)
    self.assertAlmostEqual(metadata['axis_sloping_length_in'],136.922963210,places=7)
    self.assertGreater(metadata['axis_intersection_radius_in'],44)

 def test_spacer_corner_gap_and_roof(self):
  for k in range(8):
   spacer=PART[f'M-SP{k}'];a,b=map(source,[spacer['axis_start'],spacer['axis_end']])
   self.assertAlmostEqual(length(sub(b,a)),28.132864853,places=8)
   self.assertFalse(spacer['is_timber'])
   roof=PART[f'ENV-CUP{k}'];a,b=map(source,[roof['axis_start'],roof['axis_end']])
   self.assertAlmostEqual(math.hypot(a[0],a[1]),56,places=8)
   self.assertAlmostEqual((b[2]-a[2])/56,1/3,places=8)
   self.assertFalse(roof['is_timber'])

 def test_no_stale_fabrication_claims(self):
  self.assertIn('not resolved',DATA['r01']['heel_status'])
  self.assertIn('Not validated',DATA['r01']['global_overlap_status'])
  for p in PART.values():
   self.assertIsNone(p['fit_geometry']['machining_clearance_m'])
   self.assertNotIn('conceptual_key_width_fraction',p['fit_geometry'])
   self.assertEqual({f['id'] for f in p['reference_end_faces']},{p['id']+'-A',p['id']+'-B'})
  materials=json.loads((ROOT/'src/material-groups.json').read_text())
  self.assertEqual(materials['source_sha256'],hashlib.sha256((ROOT/'src/model-data.json').read_bytes()).hexdigest())
  ids=[pid for g in materials['groups'] for pid in g['member_ids']]
  self.assertEqual(set(ids),set(PART))
  self.assertEqual(len(ids),len(PART))

if __name__=='__main__':unittest.main()
