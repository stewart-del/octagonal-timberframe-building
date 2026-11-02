# Proposed step lap joinery review

## Scope and result

This model implements **all 24 matching perimeter interfaces: 16 short-rafter/ring joints and 8 main-hip/post joints** with real complementary CSG tongue and pocket meshes. The main viewer defaults to the proposed model, with the unchanged saved baseline available in the model selector. Forty members change in the proposed model; every ring beam contains both corresponding pockets. Canonical baseline files remain unchanged.

Starting dimensions chosen for the owner-authorized proposed design are a 2 in wide tongue with up to 1 in additional engagement for J/B, and a 4 in wide tongue with 0.5 in additional engagement for R/P. They are chosen design assumptions, not measured dimensions from the undimensioned reference image, code-prescribed proportions or approved construction details. The image was visually inspected. The actual owner-uploaded timber-frame manual has not been located/read; externally verified TFEC 1-2019 is not that attachment.

**Geometry checks pass within the stated numerical tolerance. Strength, bearing capacity, uplift retention, rotation restraint, durability and safe erection are not established.** Every transformed interface, including the handed short rafters, is checked individually. This is geometric design development, not approved construction joinery.

## How the actual cuts are made

Original rafter stock is reconstructed from its recorded pre-joinery halfspaces. A centered, partial-width tongue is retained from that stock beneath the current seat, limited by the chosen maximum engagement and existing receiving timber. The identical solid is cut out of the receiver. Side shoulders retain their original seat elevation. No disconnected block or material outside original stock is introduced; all original member axes and roof elevations remain fixed.

Each retained tongue exactly complements its receiver pocket; the complete assembly occupies the same combined space as the baseline assembly. Material remains in the proposed rafter where it is removed from the proposed support. This explains why total modeled timber volume stays 6.29593043154 m³ even though the 40 individual member volumes and centroids change. Those changed quantities are recomputed in the proposed data; the selected model uses its own recomputed applied self-weight arrows. Baseline contact warning markers and fixed 64/12 in² pressure shortcuts are disabled for the proposal; their absence does not establish safe restraint or capacity.

The model uses exact nominal mating surfaces with zero mathematical clearance. This is not a machining tolerance. Corner radii, tool access, shrinkage allowances, assembly motion, pegs/fasteners and uplift retention remain unresolved. The independent profile records are closed polygons measured from the actual tongue and matching pocket at the transverse center plane, not ornamental overlays.

## Measured results and tradeoffs

| Geometric result per interface | Each J/B joint | Each R/P joint |
|---|---:|---:|
| Tongue width | 2 in | 4 in |
| Maximum added engagement | 1 in | 0.5 in |
| Volume retained in rafter and removed from receiver | 3.228 in³ | 16.000 in³ |
| Baseline horizontal contact area | 12.000 in² | 64.000 in² |
| Proposed horizontal contact area | 6.457 in² | 64.000 in² across two levels |
| New inclined contact area | 5.893 in² | None |
| Opposed transverse cheek area each | 1.614 in² | 4.000 in² |
| Named receiver section before and after | 48.000 to 46.386 in² | 64.000 to 32.000 in² within the shallow top slot |

For J/B, original stock slopes through the current seat. The proposed foot therefore tapers into a matching sloping pocket, reaching 1 in only near the outer edge. It is not a full-depth rectangular tongue. The new inclined face's normal has a horizontal component; any normal bearing force there also has a horizontal component, but its magnitude and load sharing are unsolved. Neither reduced horizontal area alone nor greater total contact area establishes a capacity loss or gain.

For R/P, 0.5 in fits inside original stock across the post footprint; a generic 1 in depth would exceed original stock at the inner edge. The shallow centered slot leaves two geometric 2 in side portions at the post top. The 32 in² result is a named horizontal slice within that slot, not the minimum section of the whole post or an allowable value. Transverse cheeks only provide unilateral contact while engaged; the open-top form can still lift free and is not a completed retention detail.

## Verification and limitations

- All 40 altered solids are valid, connected, closed meshes. All 16 J, all 8 B, all 8 R and all 8 P members change; the other 64 timbers and non-timber components do not.
- All 3,340 timber pairs involving an altered member were checked against the 104 timber solids. No overlap exceeds 0.000001 in³ and no previously nonzero face contact is lost. Neighbor contact areas/normals are recomputed and retained, including post-head ring, tie and brace interfaces.
- Added rafter volume satisfies the original stock halfspaces. The representative seed pair unions and all transformed tongue/pocket complements conserve the occupied assembly space within numerical tolerance. The two pockets in each B are accumulated, never overwritten. Non-timber checks show no new interference.
- The 45° rotations and handed reflection about each bay bisector are explicitly verified against the actual baseline stock and meshes. Native-kernel quadrant rotations avoid unstable Boolean operations on reimported nearly coplanar faces; direct authoritative tongue vertices and signed whole-member volumes provide separate checks.
- An independent reviewer reproduced original-stock containment, connectedness, all affected-pair intersections, volume conservation and all-24 independent transformed-tongue and coplanar polygon-union contact measurements. This is independent geometric review, not structural qualification.
- Named local cross sections are measured directly from the altered meshes. They are not exhaustive governing-section, splitting, notch, block-shear, buckling or combined-action checks.
- No solved reaction, pressure demand, stress, strain, allowable load or safety factor is supplied. Geometry-only pass labels must not be interpreted as engineering acceptance.

External technical reading destinations remain [TFEC 1-2019](https://www.tfguild.org/timber-frame-engineering-council/standards/view/104/download), notably §2.3 and traditional-joint checks in §§3.1.4.2 and 3.5–3.6. These do not prescribe this prototype or substitute for the unread project manual and a qualified engineer's review.

## Reproduction and provenance

Baseline commit: `4c78a0b`. Canonical model SHA-256: `b3a0363a2c2e83a541038d0ff39ad86e38d8b79ceb7415cde9174d74273086a2`.

Run `python3 scripts/step_lap.py`, `python3 tests/test_step_lap.py`, then `python3 scripts/build.py` and the complete repository checks. The geometry script only writes `src/step-lap-proposal.json` and `src/step-lap-proposed-model.json`. Run `scripts/step_lap_auxiliary.py` for matching applied-self-weight, inventory and explicit cavity-unavailable data; run `scripts/fit_enclosure.py --model src/step-lap-proposed-model.json --output src/step-lap-proposed-enclosure-fit.json` for selected-model enclosure clearance fits. Every selected dataset is hash-bound to its model. The viewer also retains detailed baseline/proposed comparisons with assembled, inspection-lift and center-section views. Model switching reloads a coherent dataset rather than mixing cached meshes. Plans, JSON, CSV, SVG and GLB exports identify the selected model and proposed status.

Proposed recess and unfilled overlays are **disabled**, rather than substituting inherited baseline masks. Independent non-CSG winding-number checks found inherited removed-mask points inside owner wood:13 of7,533 sampled mask-interior points for P0 and111 of2,896 for C0. These samples establish an overlap issue, not a precise overlap volume. Direct baseline triangle integration agrees with saved volumes; the separate re-import volume discrepancy was a kernel artifact. The actual timber meshes, tongue/pocket geometry and selected-model self-weight are independently checked separately. The unavailable proposed control states this limited hold; the existing baseline display remains available as diagnostic/unverified, not certified empty space. The 48 rail/floor display components are regenerated against the selected model, not borrowed from a stale baseline fit. Wall/floor layers remain schematic, with support and connections undesigned.

Read the owner's actual manual and resolve a reviewed joint design, all affected reduced sections, grain/material data, design reactions, retention, tolerances and erection path before fabrication or construction; the modeled perimeter replication does not establish those missing checks.
