# Permanent-building display presets

Complete is the initial state: permanent frame, wall framing/enclosure/windows, built-in shelves, floor structure/foundation/bamboo and roof coverings. Temporary aids, the reference envelope and deferred grate are excluded. They are not silently restored by Reset.

Skeleton retains posts, timber frame, braces, horizontal wall rails, floor structure/subfloor and foundation. It hides enclosure, shelving, glazing, bamboo finish, ceiling plywood and roof coverings. Foundation & Posts shows foundations/bearing stands and all actual support-post groups. Floor Assembly shows foundation, floor beams/joists/subfloor and bamboo finish.

Presets clear isolation and manual hides and reassemble explosion so the selected layers appear, but leave camera coordinates and navigation mode unchanged. Reset additionally clears selection and fits the whole Complete geometry, including below-floor components. Manual group/part/layer choices remain editable and show Custom when not matching a preset. Hide all includes schematic layers; Show all remains an explicit manual way to expose temporary/reference groups.

`display-presets.js` classifies explicit `displayRole` first (after authoritative temporary/deferred status), then established group/kind/material/ID mappings. New floor bearing cleats may declare `displayRole: floorStructure`. Roof coverings use `schematicKind: roofCover`. No geometry or capacity is changed.

Simple inline SVG house icons use a thin complete outline and heavier relevant roof/wall/floor/structure strokes. Short text labels, tooltips, keyboard focus and pressed-state semantics remain available; these are not icon-only controls.

Global cut-face inventory includes all current model and schematic components, including roofing batches. Preliminary cold Node benchmark before the final roof winding/inner-edge corrections: 450 components, 61,308 triangles, 26,116 planar patches, 27.15 seconds; yielded once per component. UI now reports per-component progress and retains cancellation. Missing roof stock frames remain unavailable, not invented. This is not a GPU/browser performance claim.

Post-correction roof benchmark (`0772236 + 1f6cedd + eddb107`, top-entry with then-current floor solids): 450 components, 59,196 triangles, 25,644 planar patches, 32.285s cold Node. 450 component yields; longest individual component calculation 3.054s. Roofing records have no stock frame, so local machining angles remain unavailable. Cancellation/progress runs between components, not inside a costly component; no claim of uninterrupted main-thread responsiveness. Later floor/roof geometry changes require fresh measurement.
