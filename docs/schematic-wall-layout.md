# Provisional wall/opening layout

Separate, default-off runtime visualization. Canonical model data, timber/joinery geometry, cut schedules, exports and timber self-weight inputs are unchanged. The reference interior photo informed only the idea of pale infill between exposed timber, not dimensions or structural details. That private photo is not included in this repository.

## Design compass (not surveyed geographic orientation)

Shared `TimberSchematicWalls.orientation` in `src/schematic-walls.js` defines North at the P0–P1 WALL FACE, not a post/vertex. Face sequence P0–P1 through P7–P0: N, NW, W, SW, S, SE, E, NE. In X/Y-up/Z coordinates, north = [cos(π/8),0,−sin(π/8)] and east = [sin(π/8),0,cos(π/8)]. No canonical model rotation occurs. Site north remains unverified; plan views must use this same object if they display this design compass.

- North/South: solid infill with illustrative built-in bookshelves.
- East: large window opening.
- West: door opening.
- NE/SE/SW/NW: smaller window openings.

Window and door apertures are genuine gaps in the rendering geometry, not opaque rectangles. Glazing/door leaves and structural headers are not invented. Wall infill ends meet the existing post footprint faces; modeled end clearance is zero.

## Explicit visualization assumptions, not measurements

- Wall envelope: 100 mm thick; base at the post-foot datum and top at the existing ring-beam underside. See frame-continuity correction below.
- Large window:65%of clear wall width, sill0.75m/top1.95m.
- Small windows:30%of clear wall width, sill1.00m/top1.85m.
- Door:0.95m wide, from wall base to2.10m.
- N/S shelves:80%of wall width,300mm projection,25mm display boards; six shelves at350mm spacing.

These are reasonable schematic proportions only. Actual wall heights/build-up, window and door dimensions, shelf details, ground/floor datums, weatherproofing, bracing, load paths, headers, fasteners and code compliance require design inputs. No floor is modeled. Walls, shelves, books, glazing and other added loads remain excluded from the existing timber-only self-weight visualization.

The layer pauses during exploded or isolated-member views to avoid suggesting that proposed walls move with structural pieces. It is not included in timber selection/cut schedules or structural exports. Both WebGL and canvas fallback use the same schematic triangle data and normal depth/painter ordering.

## Independent controls and architectural plans

Walls/windows/door, N/S bookshelves, and eight cupola window-frame assemblies each have independent controls in both the 3D viewer and the architectural-plan dialog. All three are off initially. Reset View / Show all restores all three 3D controls to on, consistent with the owner's show-all request; exploded or isolated inspection still pauses the schematic layers. Plan controls are independent choices and do not modify the 3D controls or canonical model.

The same runtime meshes generate the top/side SVG line plans. The shared design-compass object supplies the plan north annotation; model +Z remains an axis, not geographic north. Hidden-line removal is sampled and may be shown dashed; drawings remain provisional, not construction documents.

Cupola windows are eight illustrative four-sided frames between the existing lower/upper ring bands. Bottom/top come from current ring mesh bounds with 12.7 mm illustrative clearance; plan width uses post-center span minus 200 mm, with 25.4 mm frame profiles and 38.1 mm depth. These are display assumptions, not approved openings, glazing, ventilation, flashing or fastening specifications. No glass solid, new timber cut, structural-bracing credit or added self-weight is asserted.

Validation: independent per-layer visibility tests (including shelves with walls off and cupola frames with shelves off), unchanged canonical model hash, all existing test suites, and SVG raster renders visually inspected. Live browser QA remains for the publisher.

## Frame-continuity correction
Infill now meets the actual adjacent post base-footprint faces across its full 100 mm thickness, with beveled ends, and the existing ring-beam underside (current model Y=2.26151824283905 m). Its base is the current post-foot datum Y=0. The earlier arbitrary 150 mm end inset, 0.10 m base and 2.20 m top are retired. Independent solid-intersection checks found no positive overlap with adjacent posts/beam; intended door/window apertures remain. This establishes modeled surface continuity, not weatherproofing or attachment capacity. Ground and foundation design remain unresolved.
