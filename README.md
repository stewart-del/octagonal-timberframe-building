<!-- TIMESTAMP START 2026-11-02T10:05:34-05:00 | REVISION R004758 -->
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

<!-- TIMESTAMP START 2026-11-02T08:05:33-05:00 | REVISION R004748 -->
The [joint strength and load-path audit](https://octagonal-timberframe-building.brujodinamico.chatgpt.site/structural-audit.html) records a design hold on the lower cupola connections. **No new dovetails are published.** The existing straight tongues remain an unresolved proposal. Documented traditional working joinery takes priority over invented interlocks.

The documented horizontal through wedged half-dovetail family is a candidate for review, with a separate wedge, matching bearing and a suitable housing. It is not interchangeable with a vertical suspended kingpost tenon through a continuous tie. Here the 10-inch tie underside and cupola post bottom are flush: a full-depth head would leave no timber below it. A smaller head or mirrored flare has not been validated. Vermont Timber Works F-6 detail 7 labels a double tenon, not a double dovetail. Source examples establish joint families, not the original building’s hidden joints or approved dimensions for this model.

The model includes eight horizontal ceiling spokes and one continuous half-inch horizontal plywood panel assembly. The ceiling spoke size is provisional; finish-board thickness remains unconfirmed. Run `scripts/audit_structure.py` after fitting to refresh the measured audit and its model hash. Connection sizing, force paths and the complete raising sequence remain unresolved.
<!-- TIMESTAMP END 2026-11-02T08:05:33-05:00 | REVISION R004748 -->

<!-- TIMESTAMP END 2026-11-01T23:19:38-05:00 | REVISION R004668 -->

## Standing structural-design reference

Use [TFEC 1-2019 and the project design-basis/release checklist](docs/TFEC-project-design-basis.md) for every joint-family revision. **TFEC-informed design review — not structurally qualified.** Applicable jurisdiction/code/NDS edition and professional review remain unresolved; NDS prevails in conflicts under TFEC §1.1. Geometric fit and the self-weight illustration do not establish structural compliance.

## Temporary construction support display

The hidden construction-aid layer contains one reusable symbolic green aid and one black welded-display assembly (`M-TMP`): eight radial L straps, 24 illustrative holes, and the owner's 90 in (7 ft 6 in) opposite-end span. This does not change the 88 in cupola. See [reference dimensions and display-only assumptions](docs/central-support-display.md). It is not a fabrication or erection design. Use the scoped `scripts/central_support.py` migration rather than regenerating existing timbers.

## Proposed step lap comparison

The [proposed step-lap model](docs/step-lap-proposal-review.md) implements actual complementary CSG at all 24 matching perimeter interfaces (16 J/B and 8 R/P), with both pockets on each ring beam. The main model selector switches between proposed and unchanged baseline geometry, including source-matched applied self-weight, enclosure fit, plans and qualified exports. Chosen dimensions and geometric tradeoffs remain a design proposal, not fabrication or structural approval; proposed contact pressures and baseline warning markers are withheld. Both model variants use their own independently audited recess geometry; no baseline overlay is substituted for proposed cuts.
<!-- TIMESTAMP START 2026-11-02T09:09:36-05:00 | REVISION R004753 -->

The nominal cavity-fit audit uses independent occupancy and section checks against the actual timber meshes. It is bound to both source hashes, and the build rejects stale or failed results. The pointed lower-cupola overlays are corrected without changing any timber solid. Invalid 3D residual meshes are no longer exported or displayed. Run `scripts/audit_cavity_fit.py` after fitting, then `scripts/audit_structure.py` and `scripts/build.py`. This checks geometric fit, not structural capacity or the complete raising sequence.

<!-- TIMESTAMP END 2026-11-02T09:09:36-05:00 | REVISION R004753 -->

<!-- TIMESTAMP END 2026-11-02T10:05:34-05:00 | REVISION R004758 -->
