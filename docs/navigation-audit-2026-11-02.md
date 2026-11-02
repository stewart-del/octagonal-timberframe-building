# Navigation and geometry-derived detail audit — November 2, 2026

Live V13 was inspected in its own cloud-browser tab. Architectural plans opened and rendered top and side SVG sheets from the selected proposed model. Source/runtime tests verify the actual selected mesh/hash is also the plan input. These are projected mesh dimensions, not construction-approved fabrication drawings.

## Defects corrected
- Active Piece followed preliminary load review; now primary.
- Joint comparison followed disabled diagnostics; now before diagnostics.
- Advanced recess/assembly controls consumed first-screen space; collapsed without removing access.
- Narrow layout put the entire sidebar before the model; model now first, with direct workspace navigation links and visible keyboard focus.
- Proposed timber J0-0/R0 incorrectly showed temporary steel support measurements because a generic fabrication flag was treated as a component identity. Only M-TMP now shows its 90-inch span/24-hole fixture details.
- Reset retained nonzero assembly separation, preventing newly restored room layers from appearing. It now resets both assembly and cut separation to zero.

## Dedicated cut-angle screen
Select a piece → Cut angles. The main inspector remains concise. All faces and edge angles derive from the shared content-keyed analysis module and the selected model. A face button highlights that patch on an actual-mesh projection. The Cut list header button gives a complete model component index and CSV/full JSON export. All-model analysis yields between pieces and can be cancelled by closing. Facets, unverified stock references and unmodeled manufacturing work are not disguised as verified saw operations. Geometry is unchanged.

## Verification boundary
Live pre-patch checks verified plans, isolate-on/off restoring 115 pieces, explode to 40%, Free/WASD mode and explicit pointer-lock fallback. Scripted DOM/runtime tests cover selected-model binding, focus return, modal input guards, mesh face reports, reset, and existing navigation. No GPU/WebGL success is claimed. Local preview navigation timed out; publisher must independently verify the revised public layout, small-screen appearance, actual modal rendering and downloads after integration.
