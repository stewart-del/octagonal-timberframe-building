# Octagonal Timberframe Building

An interactive 3D study of an octagonal timber-frame outbuilding: 104 individually selectable fitted solids, cut-surface inspection, exploded views and free camera navigation.

**This is a geometric prototype, not a construction design.** The construction-readiness review found severe reduced sections, local 1–2 mm walls, zero nominal machining clearance and collisions in every tested single-piece straight withdrawal. No structural load rating or safe erection sequence is issued.

[Open the live viewer](https://octagonal-timberframe-building.brujodinamico.chatgpt.site) · [Download models](https://octagonal-timberframe-building.brujodinamico.chatgpt.site/downloads/index.html)

## Explore

- Select a member, then **Isolate & center** to set its fitted bounding-box center as the local orbit pivot.
- Choose **Inspect End A** or **Inspect End B** for a close axis-end view. These enable **Free / WASD** at 0.02 m/s.
- **WASD** travels; **Q/E** moves down/up; drag looks; **Shift** moves faster; shift-drag pans.
- Speed is adjustable from 0.01 to 5 m/s. Movement keys are paused in fields, editable text and the parts schedule.
- Orbit, zoom, labels, individual visibility and exploded cut references remain available.

The exploded animation is a presentation view, not a verified insertion sequence. A/B views refer to original member-axis ends, not approved machining planes.

## Build and check

Requires Python 3 and Node.js. No npm dependencies or network calls are needed for the app.

```sh
python3 scripts/build.py
node tests/check_viewer.cjs
node tests/viewer-regression.cjs dist/index.html
python3 tests/validate_model.py dist/index.html
```

Open `dist/index.html` directly, or serve `dist` with any static server. Root `index.html` is the standalone viewer snapshot; build `dist` for the complete linked site. The automated test uses a mocked DOM/WebGL environment; browser visual testing is not claimed.

## Files

- `src/viewer.template.html` — editable interface, camera controls and renderer.
- `src/model-data.json` — 104-piece model and cut metadata in meters, Y up.
- `public/review/` — construction-readiness report and reproducible audit evidence.
- `public/downloads/` — assembled/exploded GLBs and the complete editable model package.
- `.openai/hosting.json` — registered Sites identity; `dist` is the static deployment directory.
- `ATTRIBUTION.md` — original architectural reference and evidence sources.

The complete downloadable model package includes individual GLBs and the Python geometry/audit source. In GitHub, the large original ZIP is stored in two verified parts under `source-assets/` because of the connector request limit. `python3 scripts/build.py` reconstructs it automatically and verifies its original SHA-256; no network access is needed. The live download is the intact original ZIP. Existing cut-sheet IDs are retained, but older A/B sheets are not a cutting schedule for the fitted internal joints.

## Engineering inputs still needed

Build location and adopted code; occupancy/enclosure; timber species, grade, actual section and moisture; roof build-up/weights; permanent lateral system; foundations and anchors; connection design; machining process; and temporary erection works. See the review and input register before redesigning joints or planning fabrication.

## Publishing status

Public repository: [stewart-del/octagonal-timberframe-building](https://github.com/stewart-del/octagonal-timberframe-building). The live site is published from the existing Sites project. This repository includes the NAV-04 viewer, complete recovered source, original model downloads and review evidence. Deployment details are recorded in `DEPLOYMENT-STATUS.md`.

## Joinery development

The source building's documented layout and timber sizes remain the baseline. The next design work is conventional timber-frame joinery, beginning with the complete P0/B7/B0/T0/R0 corner, a secondary rafter seat and the cupola closure. See `docs/JOINT-DESIGN-BRIEF.md`. Correct the assumed roof-bearing datum before carving any replacement joints. The proposed families have not yet replaced the current solids.

NAV-04 also adds keyboard-accessible schedule controls, focus restoration, persistent cut inspection pivots, and a practical connection-family panel. The current geometry and all timber IDs are preserved.
