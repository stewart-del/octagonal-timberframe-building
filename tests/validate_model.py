from pathlib import Path
import hashlib, json, re, sys

path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1] / "index.html"
html = path.read_text(encoding="utf-8")
match = re.search(r'<script[^>]*id="model-data"[^>]*>(.*?)</script>', html, re.S)
assert match, "Missing embedded model"
raw = match.group(1)
expected = "f9e3052986b2df9ef5024c1d4dc665839d22944a2c9e7acebcfd8817220bf8a4"
assert hashlib.sha256(raw.encode("utf-8")).hexdigest() == expected, "Model changed from recovered baseline"
data = json.loads(raw)
parts = data["parts"]
expected_ids = [name for i in range(8) for name in [f"P{i}", f"B{i}", f"T{i}", f"R{i}", f"C{i}", f"L{i}-L", f"L{i}-S", f"L{i}-H", f"K{i}-A", f"K{i}-B", f"J{i}-0", f"J{i}-1", f"J{i}-2"]]
assert [p["id"] for p in parts] == expected_ids, "Timber IDs or order changed"
assert len(parts) == len(set(p["id"] for p in parts)) == 104
for part in parts:
    assert not part["temporary"]
    assert [f["id"] for f in part["reference_end_faces"]] == [part["id"] + "-A", part["id"] + "-B"]
    assert all(f["part_id"] == part["id"] for f in part["reference_end_faces"])
assert data["main_roof_overhang_normal_ft"] == 2.5
ids = re.findall(r'\bid="([^"]+)"', html)
assert len(ids) == len(set(ids)), "Duplicate HTML IDs"
print(json.dumps({"model_unchanged": True, "timber_count": 104, "end_references": 208, "model_data_sha256": expected, "limits": "This checks source integrity; no structural, fabrication, browser rendering or assembly approval."}, indent=2))
