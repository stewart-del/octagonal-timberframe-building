"""Validate illustrative applied-weight data against current mesh, not structural adequacy."""
from pathlib import Path
import hashlib,json
import numpy as np
R=Path(__file__).resolve().parents[1]
raw=(R/'src/model-data.json').read_bytes();model=json.loads(raw);data=json.loads((R/'src/load-review-data.json').read_text())
assert data['source_model_sha256']==hashlib.sha256(raw).hexdigest()
parts={p['id']:p for p in model['parts']};timbers={k for k,p in parts.items() if p['is_timber']}
# TIMESTAMP START 2026-11-02T15:15:55-05:00 | REVISION R004802
assert len(data['members'])==112 and {m['id'] for m in data['members']}==timbers
# TIMESTAMP END 2026-11-02T15:15:55-05:00 | REVISION R004802
for m in data['members']:
 p=parts[m['id']];v=np.array(p['vertices']);t=np.array(p['triangles']);o=v.mean(axis=0);q=v-o
 sv=np.einsum('ij,ij->i',q[t[:,0]],np.cross(q[t[:,1]],q[t[:,2]]))/6
 volume=sv.sum();centroid=o+(sv[:,None]*(q[t[:,0]]+q[t[:,1]]+q[t[:,2]])/4).sum(axis=0)/volume
 assert abs(volume-m['volume_m3'])<1e-10,m['id']
 assert np.linalg.norm(centroid-m['centroid_m'])<1e-10,m['id']
assert len(data['issues'])==128 and len({i['id'] for i in data['issues']})==128
for i in data['issues']:
 assert i['owner'] in parts and (i['mate'] is None or i['mate'] in parts)
 assert i['classification'] in ['missing_restraint','capacity_unknown']
 point=np.array(i['point_m']);assert np.all(np.isfinite(point))
 for name in [i['owner'],i['mate']]:
  if name is None:continue
  v=np.array(parts[name]['vertices']);assert np.all(point>=v.min(axis=0)-1e-7) and np.all(point<=v.max(axis=0)+1e-7),(i['id'],name)
# TIMESTAMP START 2026-11-02T15:15:55-05:00 | REVISION R004802
print('PASS: all112 net volumes and gravity centroids independently match model;128 unique known-interface/base markers; no load capacity asserted')
# TIMESTAMP END 2026-11-02T15:15:55-05:00 | REVISION R004802

# Standing engineering-reference instructions must remain visible, not a safety claim.
html=(R/'src/viewer.template.html').read_text()
assert html.index('id="tfecDesignStatus"') < html.index('id="loadReviewControls"')
for phrase in ['TFEC-informed design review — not structurally qualified.', 'NDS prevails in conflicts', 'Reactions, pressure demands, strain and capacities remain unsolved', 'standards/view/104/download']:
 assert phrase in html, phrase
assert (R/'docs/TFEC-project-design-basis.md').exists()
print('PASS: visible TFEC reference, authority limits and geometry-change release gates retained')
