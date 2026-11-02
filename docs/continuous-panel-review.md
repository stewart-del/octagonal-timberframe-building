# Continuous cupola panel representation

PLY replaces the historical display-sector IDs PLY0–PLY7. This is one selection and explosion assembly, not a claim that it can be fabricated from one commercial sheet. Seams, sheet sizes, fastening, blocking and diaphragm design remain unresolved.

The current model is migrated with `python scripts/cupola_panel.py`, without regenerating any timber. The exact source vertices' convex hull is accepted only after both directional solid differences against the former sector union are less than 1e-10 m³. This guards against filling any actual nonconvex cutout. All 128 non-panel component dictionaries remain exactly unchanged; all 104 timber self-weight inputs remain unchanged.

Baseline volume: 0.03484125134639 m³. Thickness: 0.0127 m. Elevation bounds: 4.502669754280461–4.515369754280461 m. Material density is unchanged/unspecified, so mass at any given plywood density is unchanged; no new mass assumption is introduced.

`revise_r01.py` and `fit_joinery.py` now retain this unified identity for new generated models. A disposable full regeneration passed the fitter, but the historical generator does not reproduce all stored timber meshes/metadata byte-for-byte. Its regenerated timber data was NOT substituted into this change. The checked-in baseline remains authoritative. Do not use full regeneration as an incidental way to make display edits.

Independent geometric review confirmed union symmetric difference 9.63e-17 m³ and unchanged bounds/center of mass. Browserless interaction and export regression checks cover selection and a unified exploded offset; no live-browser or structural certification is implied.
