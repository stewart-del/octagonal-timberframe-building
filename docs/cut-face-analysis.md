# Current-model cut-face analysis — phase 1

`src/cut-face-analysis.js` measures the supplied live part meshes; it does not read the saved `angles` or recorded contact-plane arrays as the answer. It must receive the active baseline/proposed `DATA` and its current revision/parameters. It does not modify geometry.

## Meaning and coverage

- Each nondegenerate triangle is assigned to a connected planar patch. Coplanar shared triangle seams are deduplicated, including partial-edge/T-junction adjacency. Disconnected coplanar regions retain separate face IDs.
- IDs `piece-F001…` are revision-specific. A content fingerprint accompanies every report; IDs may change when geometry changes. This is not a permanent joinery-operation identifier.
- Validated orthogonal stock axes come from `stock_frame`; local locations use the recorded A/axis-start origin. This is not a certified machining datum. Missing or nonorthogonal frames yield unknown local angles rather than invented axes.
- Off-square is the acute angle between face normal and longitudinal axis. Miter is geometric normal yaw toward stock width. Bevel is geometric normal tilt toward stock depth. The canonical plane-normal sign is chosen in local-axis/width/depth order. These are NOT saw settings; stock orientation, machine convention, kerf and tool access are not inferred.
- Adjacent edge records associate face IDs and expose acute plane angle and, only where the existing analyser verifies closed consistent topology, material-side interior/reflex angle. Embeddedness/self-intersections are not certified.
- Stock-aligned fitted-envelope surfaces are distinguished from end planes, shoulders, recess planes and oblique cut candidates. “Envelope surface” does not prove it was left uncut. A planar patch is not necessarily a distinct manufacturing operation.
- Area, centroid and local bounds are derived from the actual triangles. Insets are distances from the CURRENT fitted envelope, not removal depth from the original blank. Actual machining depth, mating contact, allowance and structural capacity remain unknown.
- Curves are only their supplied mesh facets, not analytic curved-cut instructions. No complete manufacturing-cut coverage is claimed even when all supplied triangles are accounted for.

## API and freshness

`analysePart(part,{revision,parameters})` returns faces, stock reference, warnings, and adjacent dihedrals. `analyseModel(model,options)` returns the same per-part records for the whole supplied model. `analyseModelAsync` yields between pieces and supports an `isCancelled` callback; use it for a global detail screen. A complex individual mesh may still take time, so paint a busy state first. `toCSV` accepts either report and exports the same measured records.

The bounded128-entry cache uses the full serialized geometry, stock frame, origin, revision and parameters, not array/object identity. In-place CSG edits invalidate it. The short display fingerprint is not a cryptographic integrity check; cache lookup uses the complete input string. Do not substitute cached baseline data when the proposed model is selected.

## UI contract

Selection should expose a **Cut angles** button leading to a separate detail screen. Do not dump every face into the main inspector. A global cut-face list/export must use the same active-model source and reports. Unsupported measurements stay unknown, with one clear geometric/not-machine-settings explanation.

## Phase 2 — specification only

Dynamic wall height and roof rise are NOT implemented by this phase. Future parameters require explicit dimensional datums and valid ranges; regenerate the affected member endpoints, faces, mating joints, enclosure fit, roof/cupola offsets and load data from one revisioned source. Never blindly scale all vertices or stretch an existing notch. Preserve unrelated stock sections, check all collisions/gaps and minimum remaining sections, recalculate contacts and every derived angle, invalidate per-piece/global reports by geometry/revision/parameter change, and verify both baseline and proposed choices. Parameter changes do not establish structural adequacy; joints, load paths and construction review remain separate release gates.
