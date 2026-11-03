<!-- TIMESTAMP START 2026-11-02T13:42:10-05:00 | REVISION R004782 -->
# Wall opening framing

The six lower-wall openings now have twelve vertical jambs, six headers and five window sills. All use the existing 6 × 6-inch display section. Each jamb bears on the bottom rail with a complete 6 × 6-inch contact face and reaches the ring-beam underside. The west doorway has no sill or bottom rail across its clear aperture.

Headers and window sills meet the jamb faces. Horizontal rails stop at the jambs, and the wall infill occupies the remaining space. The east window's header and upper rail are partitioned at their shared boundary, removing the former 2.4 mm intersection. The two east jambs have exact clearance notches around the existing knee braces; each jamb remains one connected solid. Wall infill is also fitted around primary timber rather than passing through it.

The clear openings retain their previous dimensions: the west door is 0.95 m wide and 2.10 m high from floor level; the east window uses 65% of the bay width between elevations 0.75–1.95 m; the other four windows use 30% of the bay width between elevations 1.00–1.85 m. The eight cupola window frames are preserved.

<!-- TIMESTAMP START 2026-11-02T15:07:59-05:00 | REVISION R004800 -->
The upper horizontal rails now align with the window heads: 1.85 m on the six standard faces and 1.95 m at the east window. This leaves a visible wall band below the upper ring beam. The west doorway retains its 2.10 m clear head height, so that face has only a narrow band above its header. These heights follow the chosen opening dimensions rather than closing the space above the rails.

The same framing is generated for all three model variants. Framing, infill, shelves and legacy floor-sector clearance data are bound to the selected model and wall-generator SHA-256 hashes. They are regenerated around the current full 2 × 6-inch main braces, including the third inward brace at each post. The two highest bookshelf boards have matching end clearances around the new inward braces; the other ten shelf boards remain unchanged. Framing retains the `wallStructure` display role, explicit `framingRole`, and individual nonzero exploded offsets.
<!-- TIMESTAMP END 2026-11-02T15:07:59-05:00 | REVISION R004800 -->

<!-- TIMESTAMP START 2026-11-02T15:07:59-05:00 | REVISION R004800 -->
`tests/schematic-walls.cjs` verifies preserved clear dimensions, a complete disjoint partition of every wall outside the aperture, twelve jambs, the wall band above the lowered rails, and display metadata. `tests/test_enclosure_fit.py` verifies all three fitted variants: continuous valid framing meshes, no positive-volume intersections among framing/infill or with primary timber, exact brace-shaped shelf removals, preserved apertures and door clearance, and actual face contacts across jamb feet, headers, sills, rails and ring beams. Every jamb foot retains its full 0.02322576 m² (36 in²) bearing face. Checks use 1e-9 m plane-distance tolerance and a 1e-10 m³ intersection-volume limit.
<!-- TIMESTAMP END 2026-11-02T15:07:59-05:00 | REVISION R004800 -->

These are proposed enclosure framing shapes with matching butt contacts and clearance notches. Member sizing, brace-notch capacity, fastening, lateral restraint and the complete wall-to-foundation load path remain unresolved; the members receive no capacity approval or load credit from the existing primary-timber audit.
<!-- TIMESTAMP END 2026-11-02T13:42:10-05:00 | REVISION R004782 -->
