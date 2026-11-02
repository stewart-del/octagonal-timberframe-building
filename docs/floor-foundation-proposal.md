# Floor/foundation proposal data — not construction approval

The pure module `src/floor-foundation.js` returns a selected-model-dependent layout and printable setting-out SVG. It does not edit the canonical frame, add to the104-timber weight result, or install renderer/UI changes.

Nine pier centers derive from the eight actual P0–P7 centerlines plus their building-center origin. All36 pair distances are supplied, with radius/chord/opposite/diagonal classification. Coordinates and distances print in feet/inches. Local X/Z axes are not surveyed site bearing. Rebuilding from changed post coordinates produces new setting-out values without a stale cache.

The proposed floor stack retains finished floor and existing post feet atY0:¾in bamboo,1½in displayed subfloor/underlayment,235mm joists,286mm radial beams. Eight radial beams and80 chord joists are layout proposals, not approved member spans, species/grades or connections. The central beam hub, joist bearing, rim support and diaphragm fastening remain unresolved.

Equal-height pier tops are at the beam-bottom datum. Reference grade is2ft below those tops; below-grade embedment is deliberately unknown.16in pier diameter is a display choice only. Footing, soil capacity, frost conditions, reinforcement, uplift/lateral anchorage and settlement are not determined.

Eight proposed steel post-bearing stands bridge pier tops to unchanged post feet atY0. Side plates straddle each radial floor beam and a head plate supports the post-foot datum. Plate geometry is chosen for a coherent proposed bearing path, not design approval; buckling, welds, anchors, corrosion, timber bearing and all load combinations require engineering. There is no invented steel-stand capacity or claim that this detail is suitable for construction.

The center metal grate is explicitly deferred (`grate.active=false`); integration must remove it from active visualization and close the bamboo/subfloor center, while retaining old history only. Preserve the requested eight-sector concentric bamboo pattern. All floor materials and supports belong under one floor toggle. Existing frame/head/roof work must remain untouched.

UI integrator: selecting a displayed pier should open `settingOutSVG(build(activeModel))`, not a screenshot of an old plan. Renderer/material/cut-list integration remains a distinct step. These proposal records are not a full fabricated assembly or complete structural design.

## Generated proposed solids and integration

`python scripts/build_floor_solids.py` generates139 positive display solids in `src/floor-foundation-solids.json`, including central hub, beams, joists, rim, bearing stands, piers, continuous subfloor and eight bamboo center-fill wedges replacing the deferred grate. The eight existing outer concentric bamboo sectors remain supplied by the enclosure module. Joist ends are miter-clipped to their radial bay boundaries, preserving broader horizontal bearing without reciprocal overlaps; bearing/connection is NOT sized or approved. Subfloor has conservative bounding-box clearance notches around stands. No actual stock fabrication/export approval follows from these shapes.

`OctagonFloorFoundation.assembly(activeModel,solidsData)` returns runtime components with `schematicKind:'floorAssembly'` and refuses changed post-center geometry. Integration must verify the saved source-model hash too, add these components to the existing single floor toggle in3D/plans, suppress legacy grate and eight old short footer cubes, retain outer bamboo sectors, and let selecting a pier open the nine-center setting-out SVG. Do not claim the application is updated until that renderer/UI integration is tested. CSG pair checks establish non-overlap and some contact per piece, not bearing-area sufficiency, structural continuity or capacity.

## Local application integration

The current local integration uses the complete-floor checkbox for the outer bamboo plus139 proposed foundation/floor solids in3D and plans. Legacy grate and short footer cubes are excluded from the active runtime layout. Foundation components also enter the active-model global cut-face report; missing stock axes remain unknown. Nine concrete piers are ray-selectable, opening the current setting-out SVG with print/download controls; a toolbar button provides the same accessible route. The scene grid moves to the proposal's reference-grade datum when the floor is shown. This remains an unapproved design proposal, not a structural/fabrication release.

The build verifies the baseline source hash and matching post centerlines in the proposed frame. The runtime refuses stale foundation data if selected post-center coordinates change. Further post-foot/floor datum changes require regeneration and validation, not reuse of this assembly. Per-piece contacts and no-overlap tests do not establish bearing-area sufficiency or full load-path capacity. This local integration has automated tests, not a verified production deployment or browser screenshot.


## Bearing correction

The central hub now has a lower143mm-high octagonal shoulder with350mm apothem around the203.2mm-apothem full-height core. Matching beam end recesses are generated from the same hub solid, providing actual horizontal gravity-bearing surfaces rather than vertical-face contact alone. Measured contact is approximately31.855665in² per radial beam. Radial-bay miter clipping raises each joist-end horizontal bearing to approximately5.284790in². These are geometric contact areas only—not allowable bearing, splitting, shear, withdrawal restraint or load-capacity checks. All chosen dimensions are proposed and require engineering.
