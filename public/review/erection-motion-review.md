# Digital erection / disassembly review

**Result: erection sequence is not verified. The current fitted model fails every tested one-piece straight withdrawal.** Nominal assembled contact and zero solid overlap do not establish that the parts can be brought into that configuration.

This review uses the actual 104-piece fitted model, represented by 1,789 convex cells. It does not modify the model or substitute proxy boxes. Piece IDs correspond to the current model and cut-reference documents.

## Verified findings

- **832 direction-specific paths across all 104 members were tested. Every path has a positive-volume collision witness.** Depending on duplicate directions, members have 6, 7 or 9 unique tested directions. Families are vertical up/down, member-axis forward/back, horizontal radial inward/outward, horizontal tangential either way, and the member's existing exploded-view offset direction.
- A second run capped each attempted withdrawal at **50 mm (1.97 in)**. All 832 paths still encountered positive-volume interference before that distance. There is no first independent straight withdrawal within this tested direction set, so the reverse process does not provide an erection sequence.
- The presentation's simultaneous exploded animation also intersects. At **0.100001%** of the assembled-to-exploded transition, **J0-0 intersects B0 by 1,650 mm³**. This one witness is sufficient to disprove collision-free motion for that animation; the test does not claim to enumerate every animation collision.
- All 832 full-path witnesses were re-evaluated. Their overlap volumes exceed **1e-10 m³**, the positive-overlap threshold used by the fit audit. The largest overlap for those same cell pairs before motion was only **1.875e-15 m³**, consistent with numerical roundoff. These are new motion collisions, not evidence of a pre-existing material overlap at the nominal assembled position.

Representative collisions when one member moves vertically upward and every other member stays fixed:

| Moving member | Fixed obstruction | Upward displacement | Overlap volume |
|---|---|---:|---:|
| L0-H | C0 | approximately 1.00001 mm | 3,308 mm³ |
| J0-0 | B0 | approximately 1.00001 mm | 1,265 mm³ |
| R0 | B0 | approximately 1.00001 mm | 453 mm³ |
| T0 | C0 | approximately 1.00001 mm | 1,067 mm³ |
| P0 | K0-A | approximately 1.00001 mm | 1,701 mm³ |
| K0-A | B7 | approximately 1.00001 mm | 3,942 mm³ |

The listed positions are interior collision witnesses, not exact first-contact distances or machining allowances. They refer to particular convex-cell pairs; the whole-member overlap can be larger.

## Method and limits

For each moving convex cell and fixed convex cell, the audit computes the **continuous interval** over which their projections overlap on all separating axes: both solids' face normals and cross products of their edge directions. Since the motions are translations without rotation, the axis set is fixed throughout the motion. Swept axis-aligned bounds reject irrelevant pairs. Every reported blocking collision is additionally confirmed by convex halfspace clipping and positive intersection volume at an interior parameter value. A sampled pose is used only as a collision witness, never as evidence that an entire path is clear.

The full-path test extends 40 m, beyond the model's 16.35 m bounding-box diagonal; the supplemental test checks the first 50 mm. SAT projection resolution is 1e-8 m, a numerical analysis setting **not a fabrication tolerance**. The independent evidence script also passes six analytic cube tests covering intersecting, separating, touching, and diagonal translations and a known intersection volume.

This is a finite direction search. **It does not prove that assembly is impossible by every method.** It does not test rotations, curved paths, coordinated groups, partial insertion followed by rotation, deformation, or changing joint topology. Group preassembly could change the problem, but is not established by this result. The source still contains conceptual keyed geometry rather than an approved timber-frame joint system.

## Consequence for construction planning

The exploded display must remain a cut-reference illustration, not an erection instruction. Before deriving a physical raising sequence, each connection needs a designated insertion/removal direction and compatible machining allowance; interfering undercuts or trapped keys need redesign, or an explicitly tested group-assembly strategy. Repeat swept-solid collision checking on the revised joints and their intended staged motions.

Physical erection remains separately unverified: member weights and lifting points, crane/rigging geometry, temporary shoring and bracing, construction-stage stability, temporary-center-support forces, wind during raising, and the release condition for removing that temporary support were not analyzed. This review authorizes no removal of the black temporary center support and supplies no unsupported raising order.

## Reproduction and evidence

Run from the project directory:

```sh
python3 output/octagon-engineering-review/erection_motion_audit.py
python3 output/octagon-engineering-review/erection_audit_evidence.py
```

Outputs in this directory:

- `erection-motion-results.json`: full direction-specific attempts, blockers, cell indices, intersection volumes and continuous collision intervals.
- `erection-blocked-paths.csv`: 832 rows mapped to existing member IDs.
- `erection-initial-release-results.json`: every 50 mm attempted withdrawal and its positive collision witness.
- `erection-exploded-motion-witness.json`: simultaneous presentation-animation collision, including both offset vectors.
- `erection-motion-evidence-checks.json`: reproduction results, analytic checks and exact source hashes.

Audited `fitted-cells.json` SHA-256: `3fc343bb990fc2c592024f33013131b9ba1e4e60936cdba59039b7a58c7a6645`.

Audited `fittedparts.json` SHA-256: `21a9501a235681e3cfd0cbc3d39c53db12ba11d45fe2bf2c392a36e4ff09d3cf`.
