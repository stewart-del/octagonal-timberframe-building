# Temporary central support display

Owner reference supplied and visually inspected 2 November 2026: central-support diagram at 8.18.54 AM and building image at 8.18.30 AM. This is one temporary welded assembly represented as eight radial vertical-plane L straps, with three holes on each downturned outer leg, 24 total. It is construction equipment, hidden by default, not permanent structure.

## Reference dimensions and separate display assumptions

| Field | Value | Status |
|---|---:|---|
| Opposite outer-end span | 90 in / 7 ft 6 in | Explicit owner instruction; distinct from unchanged 88 in cupola |
| Horizontal strap depth | 4 in | Drawing callout |
| Outer leg total height | 14 in | Drawing callout interpreted top to bottom |
| Outer leg radial width | 4 in | Illustrative constant-width L interpretation |
| Steel thickness | 1/8 in | Illustrative visibility assumption only |
| Hole diameter | 3/8 in | Illustrative display only, not a screw size |
| Hole center radius | 43 in | Illustrative display only |
| Hole centers below top | 2, 7 and 12 in | Illustrative display only; no edge-distance check |
| Top elevation | 85 in above provisional model base | Retained old fixture-top datum, not verified erection placement |

No stock, cut, drill, weld, screw, fastening or erection specification is established. Welding is represented only by a connected mesh at the center, without weld beads or joint detail. Steel grade, hole layout, fasteners, capacity, attachment and removal sequence require separate design. The building image does not establish these details or validate this reconstructed assembly. The green aid retains its old symbolic shape; this black-support drawing does not validate it.

## Model and downstream plans

Stable ID `M-TMP`, assembly ID `CENTRAL-SUPPORT`, quantity one. Legacy IDs `M-TMP0` through `M-TMP7` resolve to the assembly; the viewer, selection, isolation and explode operate on the whole assembly. It is steel, temporary, excluded from timber gravity calculations and permanent assembled/exploded GLB exports. The eight legs have three actual mesh bores each, not decorative circles. A closed connected mesh is a visualization property, not strength verification.

Each record carries `geometry_purpose`, `dimension_status`, `fabrication_dimensions_valid: false` and `plan_dimension_policy`. Plans and schedules must suppress drilling/cut/weld/fastener dimensions and show only clearly labeled owner-reference dimensions; no dimensions from the assumed hole geometry may be treated as validated fabrication values. The inspector and CSV explicitly qualify assumptions and suppress member-style cut/edge measurement tools for this assembly.

## Scoped reproduction

Run `python3 scripts/central_support.py`, then `python3 scripts/build.py`. This changes only the temporary support plus its source-bound metadata and descriptive green-aid note. It does not invoke full timber regeneration. `scripts/revise_r01.py` is updated for future generator consistency but was not run against production timber meshes: known legacy-timber regeneration drift is outside this change.

`docs/central-support-baseline.json` records the previous source hash and protected part hashes from commit `80b4619`. Tests require exact preservation of all 104 timber records, the continuous panel and roof envelopes, and the green aid apart from its clarified note. The cupola remains 88 in outside. No force, bearing, connection capacity or structural-approval result changes.
