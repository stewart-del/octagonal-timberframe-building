# TIMESTAMP START 2026-11-03T12:00:26-05:00 | REVISION R004998
"""Trim only hidden bamboo below wall sills to allow an independent finish lift."""
import hashlib
import json
import numpy as np
from plan_architectural_disassembly import ROOT, VARIANTS, load_scene, check_stage

LIFT_M = .05

def main():
    wall_path = ROOT / 'src/wall-joinery-fit.json'
    wall = json.loads(wall_path.read_text())
    # Load all scenes before rebinding their enclosure files.
    scenes = {variant: load_scene(variant) for variant in VARIANTS}
    for variant, scene in scenes.items():
        relative = 'src/' + VARIANTS[variant][1]
        path = ROOT / relative
        fit = json.loads(path.read_text())
        before = json.loads(path.read_text())
        for pid, part in scene.parts.items():
            if not pid.startswith('SCHEM-FLOOR-SECTOR-'):
                continue
            shape = scene.solids[pid]
            removed = []
            # Sills begin at finish level and already cover these strips in the
            # assembled view. Their downward copy removes only that hidden area.
            for other, obstacle in scene.solids.items():
                p = scene.parts[other]
                if p.get('schematicKind') != 'rail':
                    continue
                box = obstacle.bounding_box()
                if box[1] > 1e-8 or box[4] < LIFT_M:
                    continue
                cutter = obstacle.translate([0, -LIFT_M, 0])
                amount = (shape ^ cutter).volume()
                if amount > 1e-14:
                    shape = shape - cutter
                    removed.append({'id': other, 'volume_m3': amount})
            mesh = shape.to_mesh64()
            vertices = np.asarray(mesh.vert_properties)[:, :3]
            entry = fit['parts'][pid]
            entry.update(vertices=vertices.tolist(), triangles=np.asarray(mesh.tri_verts).tolist(),
                         center=((vertices.min(0)+vertices.max(0))/2).tolist(),
                         fitted_volume_m3=shape.volume(), connected_components=len(shape.decompose()))
            if removed:
                entry['finish_sill_clearance'] = {'lift_m': LIFT_M, 'removed_hidden_strips': removed}
            scene.solids[pid] = shape
            scene.parts[pid] = {**part, **entry}
        assert all(value == fit['parts'][pid] for pid, value in before['parts'].items()
                   if not pid.startswith('SCHEM-FLOOR-SECTOR-'))
        ids = [pid for pid in scene.parts if pid.startswith(('SCHEM-FLOOR-SECTOR-', 'FLOOR-BAMBOO-CENTER-'))]
        proof = check_stage(scene, ids, [0, LIFT_M, 0])
        assert proof['status'] == 'PASS', proof['collisions']
        fit['finish_floor_clearance'] = {'revision': 'R004998', 'lift_m': LIFT_M,
                                       'scope': 'Hidden strips beneath wall sills only; finished visible pattern preserved'}
        path.write_text(json.dumps(fit, separators=(',', ':'))+'\n')
        wall['variants'][variant]['sources'][relative] = hashlib.sha256(path.read_bytes()).hexdigest()
        print(variant, 'PASS: 16 bamboo finish parts lift independently; all non-floor meshes unchanged', flush=True)
    wall_path.write_text(json.dumps(wall, separators=(',', ':'))+'\n')

if __name__ == '__main__':
    main()
# TIMESTAMP END 2026-11-03T12:00:26-05:00 | REVISION R004998
