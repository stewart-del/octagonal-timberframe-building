# TIMESTAMP START 2026-11-05T09:01:08+00:00 | REVISION R000039
"""Both source readers preserve exact arrays, reject corruption and decode once."""
import gzip,json,random,subprocess,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from physical_data import read_physical_json,write_physical_json
ROOT=Path(__file__).resolve().parents[1]
class PhysicalData(unittest.TestCase):
 def fixture(self):
  randomizer=random.Random(1977)
  return {'parts':[{'id':'P'+str(k),'note':'Exact physical numeric source','vertices':[[randomizer.random(),randomizer.random(),randomizer.random()] for _ in range(120)],'triangles':[[0,1,2],[3,4,5]],'display_mesh':{'vertices':[[0,0,0]],'triangles':[]}} for k in range(5)],'prototypes':{'unchanged':{'vertices':[[.12345678912345678,0,0]],'triangles':[]}}}
 def test_multiple_archives_python_node_and_cache(self):
  with tempfile.TemporaryDirectory() as folder:
   path=Path(folder)/'test-solids.json';data=self.fixture();metadata=write_physical_json(path,data,geometry_archive_max_bytes=4200)
   self.assertGreater(len(metadata['geometryArchives']),1)
   self.assertTrue(all((path.parent/q['path']).stat().st_size<=4200 for q in metadata['geometryArchives']))
   restored=read_physical_json(path);self.assertEqual(restored['parts'],data['parts']);self.assertEqual(restored['prototypes'],data['prototypes'])
   script="""const fs=require('node:fs'),assert=require('node:assert/strict'),path=require('node:path'),p=process.argv[1],d=JSON.parse(fs.readFileSync(p)),api=require(process.argv[2]),reader=fs.readFileSync;let reads=0;fs.readFileSync=function(...args){if(String(args[0]).endsWith('.gz'))reads++;return reader.apply(this,args);};const a=api.resolveSourceData(d,path.dirname(p)),b=api.resolveSourceData(d,path.dirname(p));assert.equal(a,b);assert.equal(reads,d.geometryArchives.length);process.stdout.write(JSON.stringify(a.parts));"""
   actual=json.loads(subprocess.check_output(['node','-e',script,str(path),str(ROOT/'src/physical-parts.js')]))
   self.assertEqual(actual,data['parts'])
 def test_shared_product_specs_and_small_archived_meshes(self):
  from physical_data import occupied_part
  spec={'manufacturer':'Verified fixture maker','partNumber':'SPEC-1','lengthIn':2.5};prototype={'vertices':[[0,0,0],[1,0,0],[0,1,0],[0,0,1]],'triangles':[[0,2,1],[0,1,3],[0,3,2],[1,2,3]],'fastener_spec':spec};part={'id':'NAIL-1','mesh_instance':{'prototype':'shared','transform':[[1,0,0,4],[0,1,0,5],[0,0,1,6]]}}
  expanded=occupied_part(part,{'shared':prototype});self.assertIs(expanded['fastener_spec'],spec);self.assertNotIn('vertices',part)
  with tempfile.TemporaryDirectory() as folder:
   path=Path(folder)/'small-solids.json';data={'parts':[{'id':'mesh',**{k:prototype[k] for k in ['vertices','triangles']}}]};metadata=write_physical_json(path,data,inline_vertex_limit=0)
   self.assertEqual(metadata['parts'][0]['geometry_ref'],'mesh');self.assertEqual(read_physical_json(path)['parts'],data['parts'])
  script="const assert=require('node:assert/strict'),api=require(process.argv[1]),data=JSON.parse(process.argv[2]),a=api.hydrate(data.part,{shared:data.prototype}),b=api.hydrate({...data.part,id:'NAIL-2'},{shared:data.prototype});assert.equal(a.fastener_spec,b.fastener_spec);assert.equal(a.fastener_spec,data.prototype.fastener_spec);assert.equal(typeof Object.getOwnPropertyDescriptor(a,'vertices').get,'function');assert.deepEqual(a.vertices[0],[4,5,6]);"
  subprocess.run(['node','-e',script,str(ROOT/'src/physical-parts.js'),json.dumps({'part':part,'prototype':prototype})],check=True)
 def test_single_archive_backward_compatibility_and_corruption(self):
  with tempfile.TemporaryDirectory() as folder:
   path=Path(folder)/'test-solids.json';data=self.fixture();metadata=write_physical_json(path,data)
   self.assertIn('geometryArchive',metadata);self.assertNotIn('geometryArchives',metadata)
   self.assertEqual(read_physical_json(path)['parts'],data['parts'])
   archive=path.parent/metadata['geometryArchive'];archive.write_bytes(archive.read_bytes()+b'corrupt')
   with self.assertRaisesRegex(AssertionError,'archive changed'):read_physical_json(path)
 # TIMESTAMP START 2026-11-05T14:38:03+00:00 | REVISION R000047
 def test_part_archives_exact_records_order_cache_and_negative_controls(self):
  with tempfile.TemporaryDirectory() as folder:
   path=Path(folder)/'large-solids.json';data=self.fixture();randomizer=random.Random(246)
   for p in data['parts']:p['longEvidence']=''.join(randomizer.choice('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for _ in range(800))
   metadata=write_physical_json(path,data,geometry_archive_max_bytes=4200,part_archive_limit=1,part_archive_max_bytes=1200)
   self.assertNotIn('parts',metadata);self.assertGreater(len(metadata['partArchives']),1)
   self.assertTrue(all((path.parent/q['path']).stat().st_size<=1200 for q in metadata['partArchives']))
   self.assertEqual(read_physical_json(path)['parts'],data['parts'])
   script="""const fs=require('node:fs'),assert=require('node:assert/strict'),path=require('node:path'),p=process.argv[1],d=JSON.parse(fs.readFileSync(p)),api=require(process.argv[2]),reader=fs.readFileSync;let reads=0;fs.readFileSync=function(...args){if(String(args[0]).endsWith('.gz'))reads++;return reader.apply(this,args);};const a=api.resolveSourceData(d,path.dirname(p)),b=api.resolveSourceData(d,path.dirname(p));assert.strictEqual(a,b);assert.equal(reads,d.geometryArchives.length+d.partArchives.length);process.stdout.write(JSON.stringify(a.parts));"""
   actual=json.loads(subprocess.check_output(['node','-e',script,str(path),str(ROOT/'src/physical-parts.js')]))
   self.assertEqual(actual,data['parts'])
   bad={**metadata,'partArchives':metadata['partArchives']+[metadata['partArchives'][0]]};path.write_text(json.dumps(bad))
   with self.assertRaisesRegex(AssertionError,'Repeated physical part'):read_physical_json(path)
   path.write_text(json.dumps({**metadata,'parts':[]}))
   with self.assertRaisesRegex(AssertionError,'Ambiguous inline'):read_physical_json(path)
   path.write_text(json.dumps(metadata));archive=path.parent/metadata['partArchives'][0]['path'];archive.write_bytes(archive.read_bytes()+b'changed')
   with self.assertRaisesRegex(AssertionError,'part archive changed'):read_physical_json(path)
 # TIMESTAMP END 2026-11-05T14:38:03+00:00 | REVISION R000047
if __name__=='__main__':unittest.main()
# TIMESTAMP END 2026-11-05T09:01:08+00:00 | REVISION R000039
