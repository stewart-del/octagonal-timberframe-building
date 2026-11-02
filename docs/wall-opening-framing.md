<!-- TIMESTAMP START 2026-11-02T13:42:10-05:00 | REVISION R004782 -->
# Wall opening framing

The six lower-wall openings now have twelve vertical jambs, six headers and five window sills. All use the existing 6 × 6-inch display section. Each jamb bears on the bottom rail with a complete 6 × 6-inch contact face and reaches the ring-beam underside. The west doorway has no sill or bottom rail across its clear aperture.

Headers and window sills meet the jamb faces. Horizontal rails stop at the jambs, and the wall infill occupies the remaining space. The east window's header and upper rail are partitioned at their shared boundary, removing the former 2.4 mm intersection. The two east jambs have exact clearance notches around the existing knee braces; each jamb remains one connected solid. Wall infill is also fitted around primary timber rather than passing through it.

The clear openings retain their previous dimensions: the west door is 0.95 m wide and 2.10 m high from floor level; the east window uses 65% of the bay width between elevations 0.75–1.95 m; the other four windows use 30% of the bay width between elevations 1.00–1.85 m. The eight cupola window frames are preserved.

The same framing is generated for all three model variants. Each variant's clearance data includes 79 framing members, 71 infill pieces and eight legacy floor sectors, bound to that model and the wall-generator SHA-256 hashes. The primary 104 timber meshes and their source model files are unchanged. Framing retains the `wallStructure` display role, explicit `framingRole`, and individual nonzero exploded offsets.

`tests/schematic-walls.cjs` verifies preserved clear dimensions, a complete disjoint partition of every wall outside the aperture, twelve jambs, and display metadata. `tests/test_enclosure_fit.py` verifies all three fitted variants: continuous valid framing meshes, no positive-volume intersections among framing/infill or with primary timber, preserved apertures and door clearance, and 276 actual face-contact checks across jamb feet, headers, sills, rails and ring beams. The smallest tested contact is 0.0157301586 m²; every jamb foot has the full 0.02322576 m² (36 in²) bearing face. Checks use 1e-9 m plane-distance tolerance and a 1e-10 m³ intersection-volume limit.

These are proposed enclosure framing shapes with matching butt contacts and clearance notches. Member sizing, brace-notch capacity, fastening, lateral restraint and the complete wall-to-foundation load path remain unresolved; the members receive no capacity approval or load credit from the existing primary-timber audit.
<!-- TIMESTAMP END 2026-11-02T13:42:10-05:00 | REVISION R004782 -->
