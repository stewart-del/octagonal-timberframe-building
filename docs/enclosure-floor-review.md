# Enclosure and floor visualization

This is a separate runtime layout. All 104 canonical timbers, joinery, source model, plywood, temporary construction aids and timber self-weight inputs remain unchanged. The reference photographs establish the appearance of substantial horizontal rails and plain light post bases, but do not establish dimensions, joinery or structural capacity. Private source photographs are not redistributed.

## Included layout

- Existing infill follows actual post footprints and beam undersides; cardinal face layout is retained: N/S solid with built-in shelving, E large window, W door, diagonal faces smaller windows.
- Horizontal rails are a chosen 6 × 6 in display section at four levels. Window and door clear apertures remain open. The rails are **clearance-trimmed against the actual existing posts, braces and ties**, not simply overlapping them. These recesses are visualization clearance, **not designed mating structural joints**. Post/rail connections, tension restraint and capacity remain unresolved. `railConnections` supplies proposed endpoint IDs, axes and sections for the separate joint-design task.
- N/S shelves span the framing bays and meet the back of the rails; the former freestanding side-cabinet panels are removed. Shelf supports/fasteners and book loads remain undesigned.
- Eight plain light post footers: displayed post bounding footprint plus1in each side,10in high, top at existing post bottom. These are appearance assumptions, not footing/foundation specifications.
- Eight radial strand-woven/compressed bamboo floor sectors with concentric octagonal strip geometry,¾in display thickness and approximately150mm bands. The outer edge meets the inner wall face; local footing clearance notches prevent floor/footer solid intersections. Board seams are illustrated, not a product/cut schedule.
- A central octagonal metal grate with true openings is shown for the owner's intended cool-air/chimney concept.900mm across corners,25mm depth,25mm rim and24mm bars are display assumptions, not a load-rated grate design. There is no modeled joist system, foundation system or verified air-intake path. No cooling/ventilation performance is asserted.

## Visibility and plans

Wall/rail/footer, shelves, eight cupola frames, and bamboo floor/grate each have their own layer controls. Floor has its own toggle in both3D and architectural plans. Plans use the same runtime geometry and face-centered design compass; geographic/site bearing remains unverified. Exploded/isolated inspection pauses these enclosure layers. One design-assumptions section holds qualifications rather than labeling every object repeatedly.

All added wall, rail, foundation, shelf, book, bamboo and metal-grate loads are excluded from the104-timber self-weight layer. The global structural-review notice remains applicable.

## Reproduction and checks

`python scripts/fit_enclosure.py` uses Mesh64 to create `src/enclosure-fit.json`, bound to both canonical-model and schematic-module hashes. It subtracts unchanged actual timber solids from rails and footing solids from floor pieces. `build.py` refuses stale fitted data. The operation never modifies canonical timber. Geometry tests independently verify no rail/timber volume intersections, no floor/footer intersections and exact inner-wall perimeter extent. Existing joinery tests are geometric checks, not structural certification.
