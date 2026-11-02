# Octagonal Timberframe Building

An interactive 3D study of an octagonal timber-frame outbuilding: 104 individually selectable fitted solids, cut-surface inspection, exploded views and free camera navigation.

**This is a geometric prototype, not a construction design.** The construction-readiness review found severe reduced sections, local 1–2 mm walls, zero nominal machining clearance and collisions in every tested single-piece straight withdrawal. No structural load rating or safe erection sequence is issued.

## Explore

- Start with **P0 corner** at the top left. **Investigate P0 corner** brings the five related timbers into a close joint view with R0 active. **Restore full frame** returns to all 104 timbers. The visible finding distinguishes the source-height conflict from the fresh fitted-solid overlap check.
- Select a member, then **Isolate & center** to set its fitted bounding-box center as the local orbit pivot.
- Choose **Inspect End A** or **Inspect End B** for a close axis-end view. These enable **Free / WASD** at 0.02 m/s.
- Click **Free / WASD** for mouse-look without dragging; **WASD** travels, **Q/E** moves down/up, **Shift** moves faster. **Esc** releases the mouse. Dragging remains available if capture is unsupported.
- **Shift-click** in the model or piece list to add/remove timbers. Selected timbers stay solid; the other visible pieces become transparent. Plain click starts a new selection.
- Labels start **off**. The active-timber panel contains complete angle tables in named expandable sections.
- Dark member edges and **High contrast surfaces** start on. Optional **Edge measurements** show small length/angle labels for the active timber; the full edge table and CSV remain available with labels off.
- **Hollows and recesses** highlights removed stock in amber. Some of that space is occupied by mating timber in the saved assembly. Switch to magenta **Unfilled in assembly** to inspect the unoccupied subset within the original stock; exterior trimming is not an internal defect.
- **Materials list** groups 104 timbers into 13 fitted-shape types, eight per type, with stable M01–M13 group numbers and the unchanged timber IDs. Export a grouped CSV or inspect any numbered piece.
- Speed is adjustable from 0.01 to 5 m/s. Movement keys are paused in fields, editable text and the parts/materials dialogs. Opening either dialog releases mouse capture.
- Primary inspection actions come before dimensions; longer tables and secondary settings expand on demand. Open inspection sections stay open when selecting a cut.
- Orbit, zoom, labels, individual visibility and exploded cut references remain available. Secondary camera views and exports are grouped in compact menus; narrow screens use a single-column layout.

The exploded animation is a presentation view, not a verified insertion sequence. A/B views refer to original member-axis ends, not approved machining planes.

## Build and check

Requires Python 3 and Node.js. No npm dependencies or network calls are needed for the app.

```sh
python3 scripts/build.py
node tests/check_viewer.cjs
node tests/viewer-regression.cjs dist/index.html
node tests/multi-selection.cjs src/viewer.template.html
node tests/mouse-look-regression.cjs src/viewer.template.html
node tests/surface-contrast.cjs src/viewer.template.html
node tests/edge-measurements.cjs
node tests/geometry-overlays.cjs
python3 scripts/group_pieces.py --self-test-only
python3 tests/test_voids.py
python3 tests/validate_model.py dist/index.html
```

Open `dist/index.html` directly, or serve `dist` with any static server. Root `index.html` is a standalone viewer snapshot; build `dist` for the complete linked site. The automated test uses a mocked DOM/WebGL environment; browser visual testing is not claimed.

## Files

- `src/viewer.template.html` — editable interface, camera controls and renderer.
- `src/model-data.json` — 104-piece model and cut metadata in meters, Y up.
- `public/review/` — construction-readiness report and reproducible audit evidence.
- `public/downloads/` — assembled/exploded GLBs and the complete editable model package.
- `.openai/hosting.json` — registered Sites identity; `dist` is the static deployment directory.
- `ATTRIBUTION.md` — original architectural reference and evidence sources.

The complete downloadable model package includes individual GLBs and the Python geometry/audit source. Existing cut-sheet IDs are retained, but older A/B sheets are not a cutting schedule for the fitted internal joints.

## Engineering inputs still needed

Build location and adopted code; occupancy/enclosure; timber species, grade, actual section and moisture; roof build-up/weights; permanent lateral system; foundations and anchors; connection design; machining process; and temporary erection works. See the review and input register before redesigning joints or planning fabrication.

## Publishing status

Public repository: [stewart-del/octagonal-timberframe-building](https://github.com/stewart-del/octagonal-timberframe-building). The original model downloads, review evidence and Sites configuration are retained. NAV-05 adds complete model-angle and edge tables, numbered materials groups, multi-selection with transparent context, mouse-look, high contrast surfaces and recess-volume inspection. Piece and edge labels start off. Live deployment status is recorded in `DEPLOYMENT-STATUS.md`.

## Joinery development

The source building's documented layout and timber sizes remain the baseline. The next design work is conventional timber-frame joinery, beginning with the complete P0/B7/B0/T0/R0 corner, a secondary rafter seat and the cupola closure. See `docs/JOINT-DESIGN-BRIEF.md`. Correct the assumed roof-bearing datum before carving any replacement joints. The proposed families have not yet replaced the current solids.

The viewer also provides keyboard-accessible schedule controls, focus restoration, persistent cut inspection pivots, and a practical connection-family panel. The current geometry and all timber IDs are preserved.

## Angle and material conventions

All selected-piece reference angles are labeled separately from measured fitted-plane angles. Each cut retains its exact FC identifier and reports off-square angle, local-normal yaw and tilt. Missing fabrication angles stay unresolved. These values are not saw settings. Each piece can export its angle CSV.

Edge tables distinguish the **inside material angle** from the **acute angle between face planes**. An inside angle above 180° describes a concave edge. Neither value is an end-cut or machine setting; undefined or unverified values remain labeled as such.

Materials groups compare complete fitted surfaces under proper rotations/translations while preserving A/B ends and handedness. The 0.01 mm grouping tolerance is numerical only. Nominal lengths exclude joinery and purchasing allowances. Evidence: `public/review/piece-groups.json`; regenerate after geometry changes with `python3 scripts/group_pieces.py`. The build refuses stale grouping data.

See `docs/PROJECTION-PROVENANCE.md` for why the generated keys and wing-like projections are not authenticated original-plan details.

## Evidence and unresolved geometry

The original 864 × 631 reference image has now been inspected. It is a building overview, not a dimensioned corner-joint detail, and it does not authenticate the generated wing-like projections or concealed joints. The assumed 40% key envelopes and hip/ring bearing-datum conflict remain unresolved.

A fresh assembled fitted-solid check reports **zero member-pair overlaps above 1e-10 m³** across 104 timbers: `public/review/fitted-overlap-check.json`. It uses convex-cell intersections with numerical thresholds, not just bounding boxes. It does not approve bearing, retained wood, cut geometry, machining clearances or insertion paths. Recess overlays likewise inspect only the original-stock envelope; they are not a complete contact, void or structural assessment.

GitHub stores the original large model ZIP in two verified parts under `source-assets/`. The build restores the exact original archive locally without a network request.

Live site: https://octagonal-timberframe-building.brujodinamico.chatgpt.site
