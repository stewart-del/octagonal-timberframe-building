# Fitted-piece repeat groups

**Prototype geometry only — not a cutting list or construction approval.**

Source SHA-256: `f9e3052986b2df9ef5024c1d4dc665839d22944a2c9e7acebcfd8817220bf8a4`

104 original timbers; 13 conservative groups. Requested pairwise tolerance: 10 micrometres. Largest certified member-to-representative surface-distance bound: 4.998392 micrometres. Largest group pairwise bound: 9.996783 micrometres.

| Group | Quantity | Original timber IDs | Maximum residual bound (µm) |
|---|---:|---|---:|
| M01 | 8 | P0, P1, P2, P3, P4, P5, P6, P7 | 4.996368 |
| M02 | 8 | B0, B1, B2, B3, B4, B5, B6, B7 | 4.992658 |
| M03 | 8 | T0, T1, T2, T3, T4, T5, T6, T7 | 4.550278 |
| M04 | 8 | R0, R1, R2, R3, R4, R5, R6, R7 | 4.960687 |
| M05 | 8 | C0, C1, C2, C3, C4, C5, C6, C7 | 4.986884 |
| M06 | 8 | L0-L, L1-L, L2-L, L3-L, L4-L, L5-L, L6-L, L7-L | 4.890078 |
| M07 | 8 | L0-S, L1-S, L2-S, L3-S, L4-S, L5-S, L6-S, L7-S | 4.993952 |
| M08 | 8 | L0-H, L1-H, L2-H, L3-H, L4-H, L5-H, L6-H, L7-H | 4.993952 |
| M09 | 8 | K0-A, K1-A, K2-A, K3-A, K4-A, K5-A, K6-A, K7-A | 4.984880 |
| M10 | 8 | K0-B, K1-B, K2-B, K3-B, K4-B, K5-B, K6-B, K7-B | 4.996105 |
| M11 | 8 | J0-0, J1-0, J2-0, J3-0, J4-0, J5-0, J6-0, J7-0 | 4.998392 |
| M12 | 8 | J0-1, J1-1, J2-1, J3-1, J4-1, J5-1, J6-1, J7-1 | 4.937893 |
| M13 | 8 | J0-2, J1-2, J2-2, J3-2, J4-2, J5-2, J6-2, J7-2 | 4.917964 |

A→A and B→B are preserved under determinant +1 rigid transforms. No reflection, scaling, or end reversal is permitted. Full fitted triangular surfaces are covered in both directions; differing tessellation is allowed. The JSON records every original ID, both reference-end IDs, transforms and coverage counts.

The brace A/B families and the secondary-rafter 0/2 families remain separate because their fitted geometry is handed. Nominal dimensions alone never establish membership.

Algorithm: Proper rigid frames from labelled A->B axis and projected A-reference edges; separately match A/B reference vertices; bidirectional complete triangle coverage by convex polygon subtraction; per-fragment point-to-triangle convexity bounds; no reflection or end reversal.

Limitations:

- Conservative candidate search can split congruent shapes with different reference conventions; singleton status does not prove uniqueness.
- A and B are preserved, never swapped; braces such as K0-A have end IDs K0-A-A and K0-A-B.
- Tolerance is a numerical geometry comparison threshold, not machining clearance or stock tolerance.
- Boundary comparison assumes the provided consistently oriented, closed fitted-solid meshes; it does not independently validate material properties or topology.
- Floating-point polygon operations use a 0.1 nanometre numerical slack, not formal exact-arithmetic proof.
- Groups use the first source-order member as representative; every member is directly certified to it, with twice the largest residual bounding all member pairs.
- Mate IDs and installation locations remain individual; geometry-equivalent pieces are not assigned interchangeable construction roles.
