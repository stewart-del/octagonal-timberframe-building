# Octagonal Timberframe Building

An interactive geometry study of the corrected octagonal frame: eight main triangular frames, sixteen short rafters and separate cupola metalwork. R01 replaces the previous approximate secondary-rafter layout.

[Open the Site](https://octagonal-timberframe-building.brujodinamico.chatgpt.site) · [R01 geometry and joint register](https://octagonal-timberframe-building.brujodinamico.chatgpt.site/r01.html)

## R01 changes

- Retire the eight inward-running midpoint rafters, `J0-1` through `J7-1`. Preserve the surviving timber IDs and their A/B directions.
- Set the lower radial ties to 6 × 10 in. Main hips use the source-read 8 × 10 in section; short rafters use a provisional actual 4 × 8 in section.
- Place each short rafter perpendicular to its eave side and clip its physical end to the side plane of the adjacent main hip. Each bay contains two mirrored short rafters.
- Interpret the 30 ft diameter across outside radial post faces. Under the provisional 8 in post assumption, post centers span 29 ft 4 in and eave tips span 33 ft 4 in.
- Use the radial 4:12 main slope with its compatible 4.329569:12 short-rafter slope.
- Place the rotated 6 × 6 in cupola posts at a 41 in center radius. Green metal spacers span adjacent outer corners, reproducing the 28⅛ in clear setting-out gap.
- Keep the black assembly fixture separate and temporary. Show the cupola roof as an optional geometric envelope with a radial 4:12 slope and 12 in overhang.

The retained timber inventory contains 96 IDs. Cupola bands, perimeter ring sections and knee-brace sections remain contextual assumptions. Cupola bands, the temporary fixture and roof envelope start hidden. They can be enabled in the group controls.

## Inspect the frame

**Inspect rafter-to-hip joints** focuses `R0`, `J0-0` and `J7-2`. Select a contact surface to inspect its plane angles, boundary edges and vertices. **Top framing plan** reveals the repeating roof arrangement. **Restore full frame** returns to the default visible groups.

Select any piece to view dimensions, reference angles and complete edge tables. Shift-click to select several pieces. **Isolate & center** focuses one member; **Inspect End A/B** preserves the member's recorded direction. Orbit, zoom, keyboard travel, mouse-look and the simplified 2D fallback remain available. Edge labels and piece labels start off to keep the view clear.

The parts schedule, grouped materials, individual edge/angle tables and complete model data can be exported in the viewer. Metal and envelope components are not counted as timber or included in board-foot totals.

## Geometry and unresolved joints

R01 records contact-plane geometry; it does not supply finished mortises, tenons, housings, pegs, fasteners, bearing seats or machining allowances. The short-rafter-to-hip surfaces are generated from physical clipping planes, not the earlier shared-cutter keys.

The ground-to-tie height `H` is unresolved. The viewer uses 90 in only as a display datum. Actual roof bearing offsets, cupola height endpoints, timber sections where provisional, roof backing, wall/window openings, foundations and steel connection details require confirmation. "Boston Layout" is retained as the window source note without inventing openings from the blurred size annotation.

**This is a geometry study, not a construction or fabrication set.** The previous fitted-solid overlap, cavity and erection-path audits describe the superseded prototype; they do not certify R01. Historical artifacts remain identified as such.

## Source and build

- `src/model-data.json`: current generated member geometry and dimension metadata.
- `src/material-groups.json`: current repeated-member groups, including distinct non-timber groups.
- `src/viewer.template.html`: interactive viewer.
- `src/inspection-tools.js`: material schedules and contact-plane angle measurements.
- `src/edge-measurements.js`: geometric edge and dihedral measurements.
- `public/r01.html`: current dimension and joint-status register.
- `scripts/build.py`: produces the static viewer under `dist/`.
- `tests/`: current geometry and viewer checks; historical result files identify their older build.

Build with `python3 scripts/build.py`. Run the current geometry and viewer checks documented in the repository's test scripts and CI workflow. Source constants and recorded status, rather than old numerical fit reports, govern the current geometry.

The existing Sites identity in `.openai/hosting.json` is preserved. Publication should use the verified source and corresponding static build; do not treat a GitHub push alone as a confirmed Sites deployment.

## Attribution

The underlying drawing is credited to Robert Swinburne / Bluetime Collaborative, *Octagon Timber Frame Outbuilding* (drawing dated May 8, 2010). The revised geometry follows Stewart Lundy's corrections and the 12-sheet *Octagon architectural geometry study R01*. See `ATTRIBUTION.md` for the historical source record.
