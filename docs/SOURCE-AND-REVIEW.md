# Source and practical joinery review

This repository contains the recovered saved viewer, its complete embedded mesh data, NAV-05 inspection and navigation controls, tests, and the JR-01 connection-family review. The original Sites source package has also been recovered intact: editable source, assembled/exploded GLBs, the individual-model and review ZIP, audit evidence, original hosting manifest, and attribution are included. The original downloadable assets and model data remain byte-identical. The original 864 × 631 reference image has also been recovered and inspected as working evidence; it is not redistributed by this Site. Other saved drawings or rendering materials outside the recovered package are not claimed as recovered here.

## Preserved geometry and provenance

- All 104 permanent timber IDs, their geometry, nominal dimensions, cut patches, and 208 A/B references remain unchanged.
- The embedded model-data SHA-256 is `f9e3052986b2df9ef5024c1d4dc665839d22944a2c9e7acebcfd8817220bf8a4`.
- The model's 30 ft dimension is interpreted across opposite perimeter post-center vertices. Do not conflate it with the earlier 30 ft finished-interior across-flat adaptation.
- Main overhang remains 2 ft 6 in total beyond the modeled outer post envelope, perpendicular to each wall. It is a recorded design change.
- The 104-piece viewer contains permanent members only. Temporary shoring is not permanent structure and no removal sequence is established.
- Model axes are not surveyed site north.

## Practical corner finding

At the P0 post-center plane, nominal R0 geometry passes through the full depth of B0/B7. The measured hip underside lies approximately 2.39173 in below the nominal ring underside at that plane. This is a diagnostic of the current reconstruction, not a notch depth or a specified roof-raising amount. Use the viewer's **Inspect P0 corner** button to see the exact existing members.

Resolve the source roof bearing datum and intended load path before cutting away more wood or propagating a replacement detail. The source-building article establishes project context. The inspected 864 × 631 image is a building overview, not a dimensioned corner-joint detail, and does not authenticate the generated wings, concealed joints or modeled bearing datum. Its inspection does not independently verify every inherited model dimension.

## Proposed connection families

### Supported ring-beam laps

Consider supported laps or another designed ring connection over the posts. Each intersecting ring member needs a defined bearing area; continuity and uplift restraint require a separate connection design.

**Unresolved:** Current 22.5° plan miters define only a geometric seam. Resolve the post-head bearing, roof interference, remaining section, grain direction, ring forces and assembly access before selecting lap depth or fasteners.

### Housed radial tie tenons

Review a housed shoulder and tenon arrangement that transfers the intended force without treating the saved keyed partition as a structural connection.

**Unresolved:** Confirm whether each tie end carries tension, compression, shear, or combined forces. Resolve net section, tension restraint, end distances, peg specification, mortise access and insertion direction. No tenon or peg dimensions are assigned.

### Housed brace tenons

Review shoulders or housings for compressive bearing and a compatible tenon for location and required restraint. Coordinate adjacent mortises at the post head.

**Unresolved:** Check brace force direction, bearing area, post/ring retained wood, grain and splitting, then tool and raising access. Allow for shrinkage so the tenon does not bottom out before its shoulder bears. Do not substitute peg action for designed shear bearing.

### Hip bearing seats

Develop a bearing-seat detail only after the roof datum and corner load path are agreed. Inspect the P0 corner as the first representative study.

**Unresolved:** Current hip geometry crosses the full depth of the ring at the representative corner. Do not deepen a notch, trim away the ring, or move the roof by an unapproved amount to clear the collision. Resolve retained hip section, seat bearing and uplift/rotation restraint.

### Shallow secondary-rafter seats

Review shallow seats aligned with a verified roof support plane, with defined bearing and any required uplift restraint.

**Unresolved:** The secondary layout is approximate. Confirm spacing, loads, section, grain, retained depth and clearance from neighboring joints. Verify each eventual cut member remains one connected solid; do not delete detached fragments to manufacture a pass.

### Accessible cupola closure

Select a closing connection that can be inserted with the surrounding members in place. Develop a connection-specific raising and temporary-support sequence.

**Unresolved:** Reject trapped keys and closed loops that cannot be assembled. Verify actual swept insertion paths, handling clearance, tool access, temporary stability and release criteria. The explode slider is not an erection simulation.

The complete machine-readable review and member associations are in [joinery-review.json](joinery-review.json).

## Verification limits

The fresh assembled fitted-solid check in `public/review/fitted-overlap-check.json` reports zero member-pair overlaps above 1e-10 m³ for all 104 timbers. It uses convex-cell intersections with 1e-9 m distance and 1e-12 m³ cell-volume numerical thresholds; bounding boxes only prune candidates. This does not approve the assumed 40% key envelopes, bearing, cuts or retained sections. The earlier findings of thin webs, trapped keys and excessive hip/ring cutting remain unresolved. Zero nominal clearance and 0.003 mm display tolerance are not manufacturing allowances. The explosion slider is a display aid, not an erection simulation. Structural capacity, real machining tolerances, tool access and assembly paths remain unresolved.

NAV-05 retains keyboard schedule controls, focus restoration and cut inspection pivots, and adds complete angle/edge tables, 13 fitted-shape material groups of eight timbers, Shift-click multi-selection, and explicit-click mouse capture for Free / WASD. Escape and the parts/materials dialogs release capture. Labels start off; dark edges and high contrast surfaces start on. Browserless regression checks cover the controls; native pointer-lock behavior and browser/WebGL rendering have not been visually verified in this continuation.

Optional edge text and the full edge table distinguish the angle through the timber material from the acute angle between adjacent face planes. These are geometric measurements, not saw settings. Amber recess overlays show removed original stock, which may be occupied by mating timber; magenta shows the unfilled subset within that stock in the saved assembly. Exterior trimming is not an internal defect, and these overlays are not a complete void or contact assessment.

## References

- Robert Swinburne, Octagon Timber Frame Outbuilding (May 3, 2010). https://www.bluetimecollaborative.com/robert-swinburne-vermont-architect/octagon-timber-frame-outbuilding — Project identification. The recovered 864 × 631 overview was inspected; it supplies no authenticated dimensioned corner or wing detail, and not every inherited model dimension has been independently reverified.
- Jim DeStefano, Rules of Timber Joinery Design, TFEC Technical Bulletin 2011-03 (December 7, 2011). https://dcstructural.com/pdfs/technical/Bulletin_Joinery.pdf — General joinery principles, not a detail for this octagon.
- TFEC, Standard for Design of Timber Frame Structures and Commentary, TFEC 1-2019 (January 2019). https://www.tfguild.org/timber-frame-engineering-council/standards/view/104/download — Sections 1.3, 1.5, 2.3, 3.1, 3.3, 3.4 and 3.5: design inputs, notches, connections and seasoning.
- TFEC, Code of Standard Practice for Timber Frame Structures, TFEC 2-2018 (February 2018). https://dcstructural.com/wp-content/uploads/2013/06/TFEC-COSP-2018.pdf — Sections 3.01, 4.02, 5.02 and 6.01: shop drawings, shrinkage, temporary stability and explicit tolerances.
