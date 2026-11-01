# Independent review QA — 2026-11-01

**Result: PASS for the geometric evidence and scope statements reviewed.** This is a check of the review findings, not engineering approval or a construction release. No geometry or viewer files were changed.

- The current fitted-cell and mesh SHA-256 hashes match the motion evidence, machining measurements, and review summary. Exact hashes are recorded in `review-QA.json`.
- All **832 saved collision witnesses within the first 50 mm** were independently reproduced using separate convex clipping. Every witness has positive intersection volume above the stated 1e-10 m³ audit threshold. The most distant witness is at **42.640 mm**. These are interior collision poses, not first-contact distances.
- Six selected net-section areas were independently checked by slicing thin volumetric slabs, a different calculation from the review's planar polygon-area method. The largest difference was **0.000093 mm²**. Section fractions describe remaining geometric area, not strength.
- The current summary correctly uses the **T0 body** section: **9,599.98064 mm², 31.0%**, at **296.23969 mm**. The removed original end is not described as a zero-area break in the remaining member.
- Five reported local wall witnesses were independently checked: the normal segments for P0 and P2 span **1 mm** of continuous solid, and those for T0, R0, and C0 span **2 mm**. These are local examples, not certified global minimum thicknesses.
- The motion search is explicitly limited to the tested straight directions with other members held fixed. It does not rule out rotations, grouped movement, or a redesigned erection sequence. Its failed first-removal tests do not establish that every possible assembly method is impossible.

The continuous SAT motion code, sampled section code, and local wall-witness code were reviewed for units, sign conventions, and scope. No additional material defect was found. The expensive full motion and section searches were not repeated; this QA reproduces their saved geometric witnesses and selected measurements. Reproduction code and machine-readable results are in `review-QA.py` and `review-QA.json`.
