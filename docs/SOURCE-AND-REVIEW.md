# Source and practical joinery review

This repository contains the recovered saved viewer, its complete embedded mesh data, NAV-04 interaction fixes, tests, and the JR-01 connection-family review. The original broader CAD/model packages, drawings, individual measurement sheets, rendering materials, and original Sites hosting manifest have not been recovered into this repository. Their saved originals have not been overwritten. This repository is not a replacement for those broader packages.

## Preserved geometry and provenance

- All 104 permanent timber IDs, their geometry, nominal dimensions, cut patches, and 208 A/B references remain unchanged.
- The embedded model-data SHA-256 is `f9e3052986b2df9ef5024c1d4dc665839d22944a2c9e7acebcfd8817220bf8a4`.
- The model's 30 ft dimension is interpreted across opposite perimeter post-center vertices. Do not conflate it with the earlier 30 ft finished-interior across-flat adaptation.
- Main overhang remains 2 ft 6 in total beyond the modeled outer post envelope, perpendicular to each wall. It is a recorded design change.
- The 104-piece viewer contains permanent members only. Temporary shoring is not permanent structure and no removal sequence is established.
- Model axes are not surveyed site north.

## Practical corner finding

At the P0 post-center plane, nominal R0 geometry passes through the full depth of B0/B7. The measured hip underside lies approximately 2.39173 in below the nominal ring underside at that plane. This is a diagnostic of the current reconstruction, not a notch depth or a specified roof-raising amount. Use the viewer's **Inspect P0 corner** button to see the exact existing members.

Resolve the source roof bearing datum and intended load path before cutting away more wood or propagating a replacement detail. The source-building article establishes project context; its image dimensions were not independently reverified during this continuation.

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

The prior model records a numerical fit pass. Later review identified thin webs, trapped keys and excessive hip/ring cutting. That earlier pass was not rerun here. Zero nominal clearance and 0.003 mm display tolerance are not manufacturing allowances. The explosion slider is a display aid, not an erection simulation. Structural capacity, retained-section adequacy, real machining tolerances, tool access and assembly paths remain unresolved.

NAV-04 fixes list-focus retention, keyboard schedule controls, modal focus restoration, and cut inspection pivots. It explicitly returns focus to the canvas when Free / WASD is chosen. Twenty-four assertions passed in a JavaScript runtime using a minimal DOM stub; they are not real-browser or WebGL tests.

## References

- Robert Swinburne, Octagon Timber Frame Outbuilding (May 3, 2010). https://www.bluetimecollaborative.com/robert-swinburne-vermont-architect/octagon-timber-frame-outbuilding — Project identification; dimensions in source images were not reverified in this continuation.
- Jim DeStefano, Rules of Timber Joinery Design, TFEC Technical Bulletin 2011-03 (December 7, 2011). https://dcstructural.com/pdfs/technical/Bulletin_Joinery.pdf — General joinery principles, not a detail for this octagon.
- TFEC, Standard for Design of Timber Frame Structures and Commentary, TFEC 1-2019 (January 2019). https://www.tfguild.org/timber-frame-engineering-council/standards/view/104/download — Sections 1.3, 1.5, 2.3, 3.1, 3.3, 3.4 and 3.5: design inputs, notches, connections and seasoning.
- TFEC, Code of Standard Practice for Timber Frame Structures, TFEC 2-2018 (February 2018). https://dcstructural.com/wp-content/uploads/2013/06/TFEC-COSP-2018.pdf — Sections 3.01, 4.02, 5.02 and 6.01: shop drawings, shrinkage, temporary stability and explicit tolerances.
