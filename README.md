<!-- TIMESTAMP START 2026-11-01T23:06:10-05:00 | REVISION R004659 -->
<!-- TIMESTAMP START 2026-11-01T22:44:38-05:00 | REVISION R004653 -->
# Octagonal Timberframe Building

R02 restores the cupola, joins its uprights to the lower ties, adds the roof framing, and retains flat rectangular main-hip tops with no backing bevel. The eight-sided opening below stays clear.

[Open the Site](https://octagonal-timberframe-building.brujodinamico.chatgpt.site) · [Dimensions and evidence](https://octagonal-timberframe-building.brujodinamico.chatgpt.site/r01.html)

The unsupported lower cupola ring has been removed. The two upper rings follow the source section. The explode slider sits directly above the model navigation controls. The P0 close-up, cupola view, rafter inspection, free navigation, multi-selection, end inspection and edge tables are retained. Selecting a timber automatically reveals actual recess volumes in bright transparent color.

Cupola dimensions are 88 in outside, 76 in inside, 41 in post-center radius, and a calculated 28.132865 in outer-corner gap. Roof pitch is radial 4:12 with a 12 in overhang. 4 × 6 ring bands follow the readable source callouts. The source 2x roof note governs cupola rafter width; 6 in depth is provisional. The 6 × 10 lower ties retain Stewart’s prior override of the 6 × 8 source callout.

The model contains explicit proposed shoulder tenons, matching sockets, brace sockets and shallow bearing seats. `docs/joinery-verification.json` records all-pairs wood intersection, intended-contact and connected-solid checks. Nominal fit does not establish strength, shrinkage allowance, fastener capacity, tool access or raising sequence. Those remain unverified.

The inferred physical bearing datums account for actual member depth while retaining the plan dimensions and roof slopes. They are documented design assumptions, not additional dimensions claimed from the blurred source.

Reproduce geometry with `python3 scripts/revise_r01.py` then `python3 scripts/fit_joinery.py` (numpy and manifold3d required). Build with `python3 scripts/build.py`. Run `tests/test_r01_geometry.py`, `tests/test_joinery.py`, the model/export checks and viewer tests. The generated mesh is authoritative; historical reference planes preserve A/B semantics and are not final fabrication cuts.

Original building and drawing: Robert Swinburne / Bluetime Collaborative. See ATTRIBUTION.md. Existing GitHub and Sites identities are preserved.

<!-- TIMESTAMP END 2026-11-01T22:44:38-05:00 | REVISION R004653 -->

<!-- TIMESTAMP END 2026-11-01T23:06:10-05:00 | REVISION R004659 -->

<!-- TIMESTAMP START 2026-11-01T23:19:38-05:00 | REVISION R004668 -->

The [joint strength and load-path audit](https://octagonal-timberframe-building.brujodinamico.chatgpt.site/structural-audit.html) identifies unresolved central restraint, tenon proportions and foundation load paths. Simple integral dovetails are a candidate, not an engineered replacement. The model now includes eight horizontal ceiling spokes and eight half-inch horizontal plywood sectors. The ceiling spoke size is provisional; finish-board thickness remains unconfirmed. Run `scripts/audit_structure.py` after fitting to refresh the measured audit.

<!-- TIMESTAMP END 2026-11-01T23:19:38-05:00 | REVISION R004668 -->
