# TIMESTAMP START 2026-11-04T23:23:25+00:00 | REVISION R000011
# TIMESTAMP START 2026-11-04T20:33:26+00:00 | REVISION R000023
# TIMESTAMP START 2026-11-04T19:27:13+00:00 | REVISION R000001
"""Publish one shared viewer and content-addressed data for each selected model.

The root index.html remains the complete offline export used by geometry tests.
No geometry, tolerances, certificate or provenance data is rewritten here.
"""
from pathlib import Path
import hashlib
import json
import re
import shutil
# TIMESTAMP START 2026-11-04T19:29:44+00:00 | REVISION R000002
import os
import subprocess
import tempfile
import gzip
# TIMESTAMP START 2026-11-05T06:13:38+00:00 | REVISION R000027
import struct
# TIMESTAMP END 2026-11-05T06:13:38+00:00 | REVISION R000027
# TIMESTAMP END 2026-11-04T19:29:44+00:00 | REVISION R000002
# TIMESTAMP START 2026-11-08T21:51:47-05:00 | REVISION R000001
from runtime_transport import encode_transport
# TIMESTAMP END 2026-11-08T21:51:47-05:00 | REVISION R000001

ROOT = Path(__file__).resolve().parents[1]

def encode(value):
    return json.dumps(value, separators=(',', ':'), ensure_ascii=True).replace('</', '<\\/')

# TIMESTAMP START 2026-11-06T03:31:53+00:00 | REVISION R000085
def rewrite_baseline_audit(runtime):
    """Optional archived audit references must never require baseline meshes."""
    runtime=runtime.replace('MODEL_VARIANTS.baseline.model.joinery_verification','SITE_DATA.baselineAudit.verification').replace('MODEL_VARIANTS.baseline.sha256','SITE_DATA.baselineAudit.sha256')
    assert 'MODEL_VARIANTS.baseline' not in runtime,'Unsupported eager baseline dependency in selected-model runtime'
    return runtime

def build_edges(payload,base,*,root=ROOT,run=subprocess.run):
    """Reuse drawing buffers only for identical source bytes and exact inputs."""
    raw=encode(payload).encode();hasher=hashlib.sha256(raw)
    sources=[root/'scripts/build_mesh_cache.cjs',*sorted(p for p in (root/'src').iterdir()if p.is_file()and p.suffix in ['.js','.json','.gz'])]
    for path in sources:
        hasher.update(str(path.relative_to(root)).encode()+b'\0')
        with path.open('rb')as stream:
            while chunk:=stream.read(1024*1024):hasher.update(chunk)
    key=hasher.hexdigest();cache=root/'.codex-runtime/runtime-mesh-cache'/key;outputs=['.bin','.json']
    if (cache/'manifest.json').exists():
        try:
            manifest=json.loads((cache/'manifest.json').read_text())
            valid=manifest['key']==key and all(hashlib.sha256((cache/('output'+suffix)).read_bytes()).hexdigest()==manifest['outputs'][suffix]for suffix in outputs)
        except (ValueError,KeyError,OSError):valid=False
        if valid:
            for suffix in outputs:shutil.copyfile(cache/('output'+suffix),base.with_suffix(suffix))
            return
    base.with_suffix('.input').write_bytes(raw)
    run([os.environ.get('NODE','node'),str(root/'scripts/build_mesh_cache.cjs'),str(base.with_suffix('.input')),str(base)],check=True)
    cache.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='pending-',dir=cache.parent)as directory:
        temporary=Path(directory);manifest={'key':key,'outputs':{}}
        for suffix in outputs:
            content=base.with_suffix(suffix).read_bytes();(temporary/('output'+suffix)).write_bytes(content);manifest['outputs'][suffix]=hashlib.sha256(content).hexdigest()
        (temporary/'manifest.json').write_text(json.dumps(manifest))
        if cache.exists():shutil.rmtree(cache)
        temporary.rename(cache)
# TIMESTAMP END 2026-11-06T03:31:53+00:00 | REVISION R000085

# TIMESTAMP START 2026-11-06T01:19:41+00:00 | REVISION R000080
def split_foundation_detail(foundation):
    """Canonical lazy detail never owns an architectural replacement's ID."""
    architecture=foundation.get('architecture',{})
    if architecture.get('partArchives') and 'parts' not in architecture:
        raise ValueError('Resolve architectural owners before building runtime detail')
    owned={part['id'] for part in architecture.get('parts',[]) if part.get('replaceExisting')}
    initial_parts=[];detail_parts={}
    for part in foundation['parts']:
        initial={key:value for key,value in part.items() if key not in ['display_mesh','detail_ref','renderGeometry']}
        if part.get('display_mesh'):
            initial.update({key:part['display_mesh'][key] for key in ['vertices','triangles']})
            if part['id'] not in owned:
                detail_parts[part['id']]={key:part[key] for key in ['vertices','triangles']}
                initial.update(detail_ref=part['id'],renderGeometry='Assembled outer rendering envelope; concealed physical bores load once for inspection or motion.')
        initial_parts.append(initial)
    return {**foundation,'parts':initial_parts},detail_parts
# TIMESTAMP END 2026-11-06T01:19:41+00:00 | REVISION R000080

def write_runtime(html, *, model, variants, wall_joinery, foundation, mudroom, disassembly, study):
    dist = ROOT / 'dist'
    assets = dist / 'assets'
    if assets.exists():
        shutil.rmtree(assets)
    assets.mkdir()

    def asset(name, content, suffix, compress=False):
        payload = content if isinstance(content, bytes) else content.encode()
        # TIMESTAMP START 2026-11-04T19:29:44+00:00 | REVISION R000002
        if compress:
            payload = gzip.compress(payload, mtime=0)
            suffix += '.gz'
        # TIMESTAMP END 2026-11-04T19:29:44+00:00 | REVISION R000002
        path = 'assets/' + name + '.' + hashlib.sha256(payload).hexdigest()[:16] + '.' + suffix
        (dist / path).write_bytes(payload)
        return path

    # TIMESTAMP START 2026-11-04T19:29:44+00:00 | REVISION R000002
    manifest = {'variants': {}, 'meshBuffers': {}}
    # TIMESTAMP END 2026-11-04T19:29:44+00:00 | REVISION R000002
    # TIMESTAMP START 2026-11-05T06:13:38+00:00 | REVISION R000027
    # Startup renders exact outer envelopes with concealed bores omitted. The
    # physical source, offline export and every geometry audit retain all bores.
    # TIMESTAMP START 2026-11-06T01:19:41+00:00 | REVISION R000080
    initial_foundation,detail_parts=split_foundation_detail(foundation)
    # TIMESTAMP END 2026-11-06T01:19:41+00:00 | REVISION R000080
    if detail_parts:
        with tempfile.TemporaryDirectory(prefix='octagon-detail-build-') as directory:
            base=Path(directory)/'occupied-detail'
            selected={**variants['top-entry'],'model':variants['top-entry']['model']}
            payload={'variants':{'top-entry':selected},'wallJoinery':{'variants':{'top-entry':wall_joinery['variants']['top-entry']}},
                'foundation':foundation,'onlyIds':list(detail_parts)}
            # TIMESTAMP START 2026-11-06T03:31:53+00:00 | REVISION R000085
            build_edges(payload,base)
            # TIMESTAMP END 2026-11-06T03:31:53+00:00 | REVISION R000085
            header=encode({'schema':'octagon-occupied-detail-1','parts':detail_parts,'meshRanges':json.loads(base.with_suffix('.json').read_text())}).encode()
            header+=b' '*((-len(header))%4)
            content=struct.pack('<I',len(header))+header+base.with_suffix('.bin').read_bytes()
            manifest['detail']=asset('occupied-detail',content,'bin',compress=True)
# TIMESTAMP START 2026-11-05T13:07:26+00:00 | REVISION R000043
    shared_ids=[p['id'] for p in [*initial_foundation['parts'],*initial_foundation.get('architecture',{}).get('parts',[])] if not p.get('mesh_instance')]
    with tempfile.TemporaryDirectory(prefix='octagon-shared-edges-') as directory:
        base=Path(directory)/'common'
        payload={'variants':{'top-entry':variants['top-entry']},'wallJoinery':{'variants':{'top-entry':wall_joinery['variants']['top-entry']}},'foundation':initial_foundation,'onlyIds':shared_ids}
        # TIMESTAMP START 2026-11-06T03:31:53+00:00 | REVISION R000085
        build_edges(payload,base)
        # TIMESTAMP END 2026-11-06T03:31:53+00:00 | REVISION R000085
        common_mesh_ranges=json.loads(base.with_suffix('.json').read_text())
        manifest['commonMesh']=asset('shared-edges',base.with_suffix('.bin').read_bytes(),'bin',compress=True)
# TIMESTAMP END 2026-11-05T13:07:26+00:00 | REVISION R000043
# TIMESTAMP START 2026-11-05T13:07:26+00:00 | REVISION R000043
    # TIMESTAMP START 2026-11-08T21:51:47-05:00 | REVISION R000001
    manifest['common'] = asset('shared-data', encode_transport({'foundation': initial_foundation, 'mudroom': mudroom,
        'commonMeshRanges':common_mesh_ranges,
        'baselineAudit': {'sha256': variants['baseline']['sha256'], 'verification': model['joinery_verification']}}), 'pack', compress=True)
    # TIMESTAMP END 2026-11-08T21:51:47-05:00 | REVISION R000001
# TIMESTAMP END 2026-11-05T13:07:26+00:00 | REVISION R000043
    # TIMESTAMP END 2026-11-05T06:13:38+00:00 | REVISION R000027
    manifest['study'] = asset('earlier-joint-study', encode(study), 'json', compress=True)
    for identifier, value in variants.items():
        selected = {**value, 'model': model if identifier == 'baseline' else value['model']}
        payload = {'variants': {identifier: selected}, 'wallJoinery': {'variants': {identifier: wall_joinery['variants'][identifier]}},
                   'disassembly': {'variants': {identifier: disassembly['variants'][identifier]}}}
        # TIMESTAMP START 2026-11-04T19:29:44+00:00 | REVISION R000002
        with tempfile.TemporaryDirectory(prefix='octagon-mesh-build-') as directory:
            base = Path(directory) / identifier
            # TIMESTAMP START 2026-11-05T06:13:38+00:00 | REVISION R000027
# TIMESTAMP START 2026-11-05T13:07:26+00:00 | REVISION R000043
            # TIMESTAMP START 2026-11-06T03:31:53+00:00 | REVISION R000085
            build_edges({**payload,'foundation':initial_foundation,'excludeIds':shared_ids},base)
            # TIMESTAMP END 2026-11-06T03:31:53+00:00 | REVISION R000085
# TIMESTAMP END 2026-11-05T13:07:26+00:00 | REVISION R000043
            # TIMESTAMP END 2026-11-05T06:13:38+00:00 | REVISION R000027
            # TIMESTAMP START 2026-11-06T03:31:53+00:00 | REVISION R000085
            # The exact-source drawing cache above owns this generation.
            # TIMESTAMP END 2026-11-06T03:31:53+00:00 | REVISION R000085
            payload['meshRanges'] = json.loads(base.with_suffix('.json').read_text())
            manifest['meshBuffers'][identifier] = asset('edges-' + identifier, base.with_suffix('.bin').read_bytes(), 'bin', compress=True)
        # TIMESTAMP END 2026-11-04T19:29:44+00:00 | REVISION R000002
        # TIMESTAMP START 2026-11-08T21:51:47-05:00 | REVISION R000001
        manifest['variants'][identifier] = asset('model-' + identifier, encode_transport(payload), 'pack', compress=True)
        # TIMESTAMP END 2026-11-08T21:51:47-05:00 | REVISION R000001

    # TIMESTAMP START 2026-11-08T21:51:47-05:00 | REVISION R000001
    # Remove the validated one-line JSON declarations in one pass before
    # copying the executable script. The full offline export stays unchanged.
    declarations = {
        'MODEL_VARIANTS': 'SITE_DATA.variants',
        'WALL_JOINERY_DATA': 'SITE_DATA.wallJoinery',
        'FLOOR_FOUNDATION_DATA': 'SITE_DATA.foundation',
        'MUDROOM_JOINERY_FIT': 'SITE_DATA.mudroom',
        'DISASSEMBLY_PLANS': 'SITE_DATA.disassembly',
        'STEP_LAP_PROPOSAL': '()=>OctagonSiteLoader.loadJSON(OctagonSiteLoader.manifest.study)',
    }
    counts = {name: 0 for name in declarations}
    def external_data(match):
        name = match.group(1)
        counts[name] += 1
        return 'const ' + name + '=' + declarations[name] + ';\n'
    html = re.sub(r'^const (' + '|'.join(declarations) + r')=[^\n]*;\n', external_data, html, flags=re.M)
    assert all(count == 1 for count in counts.values()), 'Missing or repeated runtime data declaration: ' + str(counts)
    html, count = re.subn(r'<script type="application/json" id="model-data">.*?</script>', '', html, flags=re.S)
    assert count == 1
    runtime_match = re.search(r"<script>\n'use strict';\n(.*?)</script>", html, re.S)
    assert runtime_match, 'Missing viewer script'
    runtime = "'use strict';\n" + runtime_match.group(1)
    for before, after in [
        ("MODEL_VARIANTS.baseline.model=JSON.parse(document.getElementById('model-data').textContent);", ''),
        ("const initialModelContext=OctagonModelVariants.context(MODEL_VARIANTS,window.location.search||'');",
         "const initialModelContext={...OctagonModelVariants.context(MODEL_VARIANTS,window.location.search||''),meshCache:SITE_DATA.meshCache};"),
    ]:
        assert runtime.count(before) == 1, 'Missing or repeated runtime declaration: ' + before
        runtime = runtime.replace(before, after)
    # TIMESTAMP END 2026-11-08T21:51:47-05:00 | REVISION R000001
    # The historical audit needs its small summary, not the baseline mesh.
    # TIMESTAMP START 2026-11-06T03:31:53+00:00 | REVISION R000085
    runtime=rewrite_baseline_audit(runtime)
    # TIMESTAMP END 2026-11-06T03:31:53+00:00 | REVISION R000085

    # Dynamic imports resolve relative to an external script; use versioned paths
    # at the Site root for the optional geometry engine and its source data.
    for original, name, suffix in [('public/vendor/manifold.js', 'manifold', 'js'),
                                    ('public/vendor/manifold.wasm', 'manifold', 'wasm'),
                                    ('src/parametric-source.json', 'parametric-source', 'json')]:
        target = asset(name, (ROOT / original).read_bytes(), suffix, compress=suffix == 'json')
        old = './parametric-source.json' if suffix == 'json' else './vendor/manifold.' + suffix
        # TIMESTAMP START 2026-11-04T19:29:44+00:00 | REVISION R000002
        if suffix == 'json':
            fetch_source = "fetch('./parametric-source.json').then(r=>{if(!r.ok)throw Error('Could not load parametric source');return r.json();})"
            assert runtime.count(fetch_source) == 1
            runtime = runtime.replace(fetch_source, "OctagonSiteLoader.loadJSON('/" + target + "')")
            continue
        # TIMESTAMP END 2026-11-04T19:29:44+00:00 | REVISION R000002
        assert runtime.count("'" + old + "'") == 1
        runtime = runtime.replace("'" + old + "'", "'/" + target + "'")

    runtime = '(async()=>{\nconst SITE_DATA=await OctagonSiteLoader.data;\n' + runtime + '\n})().catch(OctagonSiteLoader.showError);\n'
    manifest['runtime'] = asset('viewer', runtime, 'js')
    # TIMESTAMP START 2026-11-08T21:51:47-05:00 | REVISION R000001
    loader = (ROOT / 'src/runtime-transport.js').read_text() + '\n' + (ROOT / 'src/runtime-loader.js').read_text()
    # TIMESTAMP END 2026-11-08T21:51:47-05:00 | REVISION R000001
    bootstrap = '<script type="application/json" id="site-assets">' + encode(manifest) + '</script>\n<script>\n' + loader
    bootstrap += "\nOctagonSiteLoader.configure(JSON.parse(document.getElementById('site-assets').textContent));\n</script>\n"
    bootstrap += '<script defer src="' + manifest['runtime'] + '"></script>'
    # TIMESTAMP START 2026-11-08T21:51:47-05:00 | REVISION R000001
    html = html[:runtime_match.start()] + html[runtime_match.end():]
    # Begin the selected model's four downloads before the stylesheet blocks
    # parsing; the deferred viewer still waits for the completed document.
    assert 0 <= html.index('<style>') < html.index('</head>')
    html = html.replace('<style>', bootstrap + '\n<style>', 1)
    # TIMESTAMP END 2026-11-08T21:51:47-05:00 | REVISION R000001
    styles = re.findall(r'<style>(.*?)</style>', html, re.S)
    manifest['styles'] = asset('viewer', '\n'.join(styles), 'css')
    first = True
    def stylesheet(match):
        nonlocal first
        if not first:
            return ''
        first = False
        return '<link rel="stylesheet" href="' + manifest['styles'] + '">'
    html = re.sub(r'<style>.*?</style>', stylesheet, html, flags=re.S)
    # Avoid a redundant browser request for a favicon that the viewer does not use.
    html = html.replace('</head>', '<link rel="icon" href="data:,">\n</head>', 1)
    (dist / 'index.html').write_text(html)
    (dist / '_headers').write_text('/assets/*\n  Cache-Control: public, max-age=31536000, immutable\n/\n  Cache-Control: no-cache\n/index.html\n  Cache-Control: no-cache\n')
    return {'offline_html_bytes': (ROOT / 'index.html').stat().st_size, 'page_bytes': len(html.encode()),
            # TIMESTAMP START 2026-11-08T21:51:47-05:00 | REVISION R000001
            'initial_bytes': {key: len(html.encode()) + sum((dist / manifest[item]).stat().st_size for item in ['runtime', 'styles', 'common', 'commonMesh']) + (dist / path).stat().st_size
            # TIMESTAMP END 2026-11-08T21:51:47-05:00 | REVISION R000001
                              # TIMESTAMP START 2026-11-04T19:29:44+00:00 | REVISION R000002
                              + (dist / manifest['meshBuffers'][key]).stat().st_size
                              for key, path in manifest['variants'].items()}, 'manifest': manifest}
                              # TIMESTAMP END 2026-11-04T19:29:44+00:00 | REVISION R000002
# TIMESTAMP END 2026-11-04T19:27:13+00:00 | REVISION R000001
# TIMESTAMP END 2026-11-04T20:33:26+00:00 | REVISION R000023

# TIMESTAMP END 2026-11-04T23:23:25+00:00 | REVISION R000011
