# TIMESTAMP START 2026-11-04T23:23:25+00:00 | REVISION R000011
# TIMESTAMP START 2026-11-04T20:33:26+00:00 | REVISION R000023
# TIMESTAMP START 2026-11-01T23:06:10-05:00 | REVISION R004659
"""Validate the built R01 viewer against canonical model and local assets.

These are geometry/data and packaging checks, not construction approval.
"""
from pathlib import Path
from urllib.parse import unquote, urlsplit
import hashlib
import json
import math
import re
import sys
# TIMESTAMP START 2026-11-04T19:27:13+00:00 | REVISION R000001
import gzip
# TIMESTAMP END 2026-11-04T19:27:13+00:00 | REVISION R000001

ROOT = Path(__file__).resolve().parents[1]
path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "dist/index.html"
html = path.read_text(encoding="utf-8")
match = re.search(r'<script[^>]*id="model-data"[^>]*>(.*?)</script>', html, re.S)
# TIMESTAMP START 2026-11-04T19:27:13+00:00 | REVISION R000001
if match:
    data = json.loads(match.group(1))
else:
    assets = re.search(r'<script[^>]*id="site-assets"[^>]*>(.*?)</script>', html, re.S)
    assert assets, 'Missing model asset manifest'
    manifest = json.loads(assets.group(1))
    bundle = json.loads(gzip.decompress((path.parent / manifest['variants']['baseline']).read_bytes()))
    data = bundle['variants']['baseline']['model']
# TIMESTAMP END 2026-11-04T19:27:13+00:00 | REVISION R000001
source = json.loads((ROOT / "src/model-data.json").read_text())
assert data == source, "Built viewer is stale relative to src/model-data.json"
assert data["units"] == "meters" and data["up_axis"] == "Y"
parts = data["parts"]
by_id = {p["id"]: p for p in parts}
assert len(by_id) == len(parts), "Duplicate component IDs"
retained = {name for k in range(8) for name in (
    f"P{k}", f"B{k}", f"T{k}", f"R{k}", f"C{k}",
    f"L{k}-S", f"L{k}-H", f"K{k}-A", f"K{k}-B",
    f"J{k}-0", f"J{k}-2")}
retired = {f"J{k}-1" for k in range(8)}
assert retained <= by_id.keys(), "A surviving legacy timber ID was lost"
assert not (retired & by_id.keys()), "Retired midpoint rafters still in model"
assert len(retained) == 88
groups = {g["id"]: g for g in data["groups"]}
assert len(groups) == len(data["groups"])
for group in groups.values():
    members = [p for p in parts if p["group"] == group["id"]]
    assert group["count"] == len(members), f"Stale count for {group['id']}"
for part in parts:
    pid = part["id"]
    assert part["group"] in groups, f"Unknown group: {pid}"
    assert len(part["vertices"]) >= 3 and part["triangles"], f"No mesh: {pid}"
    assert all(len(v) == 3 and all(math.isfinite(n) for n in v) for v in part["vertices"])
    assert all(len(t) == 3 and len(set(t)) == 3 and
               all(isinstance(i, int) and 0 <= i < len(part["vertices"]) for i in t)
               for t in part["triangles"]), f"Invalid mesh indices: {pid}"
    for cut in part.get("joint_cut_faces", []):
        assert cut.get("part_id", pid) == pid
        assert not cut.get("mate_part_id") or cut["mate_part_id"] in by_id, f"Stale mate: {pid}"
    if pid in retained:
        # TIMESTAMP START 2026-11-04T13:00:51+00:00 | REVISION R000007
        # Current shoulders and mortises supersede the legacy stock-end overlays.
        assert data["three_inch_joinery_revision"]["status"] == "PASS"
        assert part["reference_end_faces"] == [], f"Retired stock-end overlay returned: {pid}"
        if re.fullmatch(r"K[0-7]-[AB]", pid):
            joint=part["main_face_brace_joinery"]
            assert joint["id"] == pid and len(joint["tenons"]) == 2
            for dimensions in (part["dimensions"], part["nominal_dimensions"]):
                assert dimensions["width_in"] == 2 and dimensions["depth_in"] == 6, pid
                assert math.isclose(dimensions["width_m"], 0.0508, abs_tol=1e-12), pid
                assert math.isclose(dimensions["depth_m"], 0.1524, abs_tol=1e-12), pid
        # TIMESTAMP END 2026-11-04T13:00:51+00:00 | REVISION R000007
        assert part["angles"].get("fabrication_end_A_cut_deg") is None
        assert part["angles"].get("fabrication_end_B_cut_deg") is None

short_contacts = []
for k in range(8):
    for suffix, hip in ((0, k), (2, (k + 1) % 8)):
        short = by_id[f"J{k}-{suffix}"]
        # TIMESTAMP START 2026-11-04T13:00:51+00:00 | REVISION R000007
        joints = [j for j in data["tenon_schedule"] if j["donor"] == short["id"] and j["receiver"] == f"R{hip}"]
        assert len(joints) == 1, f"Short rafter {short['id']} lacks its current hip joint"
        assert math.isclose(joints[0]["projection_m"], 3 * 0.0254, abs_tol=1e-10)
        assert joints[0]["connector"]["triangles"]
        short_contacts.extend(joints)
        # TIMESTAMP END 2026-11-04T13:00:51+00:00 | REVISION R000007

ids = re.findall(r'\bid="([^"]+)"', html)
assert len(ids) == len(set(ids)), "Duplicate HTML IDs"
assert "__PARTS_JSON__" not in html and "__MATERIALS_JSON__" not in html
assert "__CAVITY_JSON__" not in html and "/*__INSPECTION_TOOLS__*/" not in html
missing = []
for href in re.findall(r'<a\b[^>]*\bhref=[\"\']([^\"\']+)', html):
    url = urlsplit(href)
    if url.scheme or url.netloc or not url.path:
        continue
    target = path.parent / unquote(url.path).lstrip("/")
    if target.is_dir():
        target = target / "index.html"
    if not target.exists():
        missing.append(href)
assert not missing, f"Missing packaged links: {missing}"
print(json.dumps({
    "revision": "R01", "retained_legacy_timbers": len(retained),
    "retired_midpoint_rafters": sorted(retired), "model_items": len(parts),
    "short_rafter_contact_faces": len(short_contacts),
    "source_model_sha256": hashlib.sha256((ROOT / "src/model-data.json").read_bytes()).hexdigest(),
    "embedded_model_matches_source": True, "local_links_exist": True,
    "scope": "Geometry/data and packaging validation; no structural or fabrication approval."
}, indent=2))

# TIMESTAMP END 2026-11-01T23:06:10-05:00 | REVISION R004659
# TIMESTAMP END 2026-11-04T20:33:26+00:00 | REVISION R000023

# TIMESTAMP END 2026-11-04T23:23:25+00:00 | REVISION R000011
