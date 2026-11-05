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
# TIMESTAMP END 2026-11-04T19:29:44+00:00 | REVISION R000002

ROOT = Path(__file__).resolve().parents[1]

def encode(value):
    return json.dumps(value, separators=(',', ':'), ensure_ascii=True).replace('</', '<\\/')

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
    manifest['common'] = asset('shared-data', encode({'foundation': foundation, 'mudroom': mudroom,
        'baselineAudit': {'sha256': variants['baseline']['sha256'], 'verification': model['joinery_verification']}}), 'json', compress=True)
    manifest['study'] = asset('earlier-joint-study', encode(study), 'json', compress=True)
    for identifier, value in variants.items():
        selected = {**value, 'model': model if identifier == 'baseline' else value['model']}
        payload = {'variants': {identifier: selected}, 'wallJoinery': {'variants': {identifier: wall_joinery['variants'][identifier]}},
                   'disassembly': {'variants': {identifier: disassembly['variants'][identifier]}}}
        # TIMESTAMP START 2026-11-04T19:29:44+00:00 | REVISION R000002
        with tempfile.TemporaryDirectory(prefix='octagon-mesh-build-') as directory:
            base = Path(directory) / identifier
            base.with_suffix('.input').write_text(encode(payload))
            subprocess.run([os.environ.get('NODE', 'node'), str(ROOT / 'scripts/build_mesh_cache.cjs'),
                            str(base.with_suffix('.input')), str(base)], check=True)
            payload['meshRanges'] = json.loads(base.with_suffix('.json').read_text())
            manifest['meshBuffers'][identifier] = asset('edges-' + identifier, base.with_suffix('.bin').read_bytes(), 'bin', compress=True)
        # TIMESTAMP END 2026-11-04T19:29:44+00:00 | REVISION R000002
        manifest['variants'][identifier] = asset('model-' + identifier, encode(payload), 'json', compress=True)

    # Exact replacements fail closed when the executable template changes.
    runtime_match = re.search(r"<script>\n'use strict';\n(.*?)</script>", html, re.S)
    assert runtime_match, 'Missing viewer script'
    runtime = "'use strict';\n" + runtime_match.group(1)
    replacements = [
        ('const MODEL_VARIANTS=' + encode(variants) + ';', 'const MODEL_VARIANTS=SITE_DATA.variants;'),
        ("MODEL_VARIANTS.baseline.model=JSON.parse(document.getElementById('model-data').textContent);", ''),
        ('const WALL_JOINERY_DATA=' + encode(wall_joinery) + ';', 'const WALL_JOINERY_DATA=SITE_DATA.wallJoinery;'),
        ('const FLOOR_FOUNDATION_DATA=' + encode(foundation) + ';', 'const FLOOR_FOUNDATION_DATA=SITE_DATA.foundation;'),
        ('const MUDROOM_JOINERY_FIT=' + encode(mudroom) + ';', 'const MUDROOM_JOINERY_FIT=SITE_DATA.mudroom;'),
        ('const DISASSEMBLY_PLANS=' + encode(disassembly) + ';', 'const DISASSEMBLY_PLANS=SITE_DATA.disassembly;'),
        ('const STEP_LAP_PROPOSAL=' + encode(study) + ';', 'const STEP_LAP_PROPOSAL=()=>OctagonSiteLoader.loadJSON(OctagonSiteLoader.manifest.study);'),
        # TIMESTAMP START 2026-11-04T19:29:44+00:00 | REVISION R000002
        ("const initialModelContext=OctagonModelVariants.context(MODEL_VARIANTS,window.location.search||'');",
         "const initialModelContext={...OctagonModelVariants.context(MODEL_VARIANTS,window.location.search||''),meshCache:SITE_DATA.meshCache};"),
        # TIMESTAMP END 2026-11-04T19:29:44+00:00 | REVISION R000002
    ]
    for before, after in replacements:
        assert runtime.count(before) == 1, 'Missing or repeated runtime data declaration: ' + before[:60]
        runtime = runtime.replace(before, after)
    # The historical audit needs its small summary, not the baseline mesh.
    assert runtime.count('MODEL_VARIANTS.baseline.model.joinery_verification') == 2
    runtime = runtime.replace('MODEL_VARIANTS.baseline.model.joinery_verification', 'SITE_DATA.baselineAudit.verification')
    assert runtime.count('MODEL_VARIANTS.baseline.sha256') == 1
    runtime = runtime.replace('MODEL_VARIANTS.baseline.sha256', 'SITE_DATA.baselineAudit.sha256')

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
    loader = (ROOT / 'src/runtime-loader.js').read_text()
    bootstrap = '<script type="application/json" id="site-assets">' + encode(manifest) + '</script>\n<script>\n' + loader
    bootstrap += "\nOctagonSiteLoader.configure(JSON.parse(document.getElementById('site-assets').textContent));\n</script>\n"
    bootstrap += '<script defer src="' + manifest['runtime'] + '"></script>'
    html = html[:runtime_match.start()] + bootstrap + html[runtime_match.end():]
    html, count = re.subn(r'<script type="application/json" id="model-data">.*?</script>', '', html, flags=re.S)
    assert count == 1
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
            'initial_bytes': {key: len(html.encode()) + sum((dist / manifest[item]).stat().st_size for item in ['runtime', 'styles', 'common']) + (dist / path).stat().st_size
                              # TIMESTAMP START 2026-11-04T19:29:44+00:00 | REVISION R000002
                              + (dist / manifest['meshBuffers'][key]).stat().st_size
                              for key, path in manifest['variants'].items()}, 'manifest': manifest}
                              # TIMESTAMP END 2026-11-04T19:29:44+00:00 | REVISION R000002
# TIMESTAMP END 2026-11-04T19:27:13+00:00 | REVISION R000001
# TIMESTAMP END 2026-11-04T20:33:26+00:00 | REVISION R000023

# TIMESTAMP END 2026-11-04T23:23:25+00:00 | REVISION R000011
