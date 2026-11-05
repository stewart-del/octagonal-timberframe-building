# TIMESTAMP START 2026-11-05T21:07:06+00:00 | REVISION R000065
"""Load the exact current product scene beside the frozen motion checker.

This loader neither certifies a route nor hides parked, temporary or unborn
actors. Its assembled projection is an input to a separate lifecycle registry.
"""
from pathlib import Path
import hashlib,json,os,shutil,subprocess
from plan_architectural_disassembly import ROOT,scene_from_payload
KERNEL_SOURCES={'scripts/plan_architectural_disassembly.py':'32cf8a371afc150ef8dcfdd5753522e3e8076abdc164c040d767c5a5f0fd3f35','scripts/bounded_local_sweep.py':'a4eb7baeb45df29f0a086e925ab2e3bf9e1ead3a01822f03bc8c18235663d721','scripts/physical_contacts.py':'683e6bf0d228a01851aa81ce121b8aa23a0c15daefad10e096d9ed69b1abbaea'}
def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def assert_current_sources(sources,root=ROOT):
 for name,expected in sources.items():assert digest(Path(root)/name)==expected,('Physical scene source changed',name)
def payload(variant='top-entry',architecture_path=None,*,allow_staging=False):
 command=[os.environ.get('NODE') or shutil.which('node') or 'node',str(ROOT/'scripts/current_physical_scene.cjs'),variant,str(architecture_path or ROOT/'src/architectural-solids.json')]
 if allow_staging:command.append('--staging')
 result=json.loads(subprocess.check_output(command,cwd=ROOT));assert result['projection']['variant']==variant
 assert_current_sources(result['sources']);return result
def load_scene(variant='top-entry',architecture_path=None,*,allow_staging=False):
 assert_current_sources(KERNEL_SOURCES)
 raw=payload(variant,architecture_path,allow_staging=allow_staging)
 scene=scene_from_payload(variant,raw,{**raw['sources'],**KERNEL_SOURCES,'scripts/current_physical_scene.py':digest(__file__)})
 scene.projection=raw['projection'];assert_current_sources(scene.sources)
 assert len(scene.parts)==scene.projection['physicalActorCount'];return scene
# TIMESTAMP END 2026-11-05T21:07:06+00:00 | REVISION R000065
