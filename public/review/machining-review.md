# Machining feasibility review — fitted octagon prototype

1 November 2026. Geometry was inspected without modification. This review applies to the fitted model identified by SHA-256 in `machining-measurements.json`.

**The current geometric fit is not ready for a shop release.** Its complementary surfaces fit mathematically, but the model specifies zero clearance, contains very thin local walls and sharp re-entrant corners, and has no verified cutter, machine, stock, moisture, or workholding definition. Passing an intersection test does not establish that these shapes can be cut accurately, assembled without damage, or remain fitted as the timber moves.

## Specific geometry findings

| Member IDs | Measured or modeled feature | Practical implication |
|---|---|---|
| P0–P7, perimeter posts | A **1.000 mm local solid wall** was found in each post. For example, P2 has a witness from `(0.010035, 2.183400, -4.648684)` to `(0.010035, 2.184400, -4.648684)` m in GLB X/Y/Z coordinates, with about 435.8 mm² projected face overlap. | This is an actual thin region of the fitted solid, not merely a parameter name. It requires explicit structural and manufacturing review; it is not an approved timber web thickness. |
| T0–T7, radial ties | Approximately **2.000 mm local solid walls**; T0 has a witness spanning Z = −0.001 to +0.001 m, with about 1,315.5 mm² projected overlap. | Competing recesses leave a thin local region that cannot be accepted solely because the digital body is connected. |
| R0–R7, main hip rafters | Approximately **2.000 mm local walls**; R1 measured about 1.9998 mm. | The geometric partition has created closely spaced cut surfaces. Their strength and ability to survive machining/handling are unverified. |
| C0–C7, cupola posts | Approximately **2.000 mm local walls**; the smallest mesh-based witness was about 1.9981 mm at C1. | Several cuts converge in small post sections. Differences of a few micrometers reflect the numerical mesh; they are not shop precision claims. |
| J0-0 through J7-2, secondary rafters | The search found local parallel-wall witnesses around **20.32 mm**. | This is a measured feature, not proof that no smaller feature exists elsewhere or that the member is adequately sized. |
| B0–B7, L0-L through L7-H, K0-A through K7-B | No positive-thickness witness below 30 mm was found by this particular parallel-face search. | This does **not** clear these members: oblique wedges, corner arrises, narrow bridges and other untested features can govern. |
| All 104 members | Sharp re-entrant edges occur in every member mesh, with **zero modeled corner radius**. | Exact sharp inside corners need an appropriate cutting method or redesigned relief/radii. A round milling/router tool alone does not produce the ideal sharp pocket corners shown. |
| All mating geometries | Specified nominal clearance is **0 mm**. | There is no allowance model for machining variation, measured timber size, moisture movement, surface irregularity or assembly handling. |

The parallel-wall search uses actual exterior faces. It requires opposing parallel planes, positive projected overlap greater than 0.01 mm², and complete solid coverage along a normal witness segment, checked against the member's convex-cell intervals. The reported thickness is therefore a witnessed local solid thickness. **It is not a proof of the global minimum remaining section or web.** Arbitrarily sharp arrises approach zero thickness; a useful engineering minimum must define the relevant load-bearing section and feature.

## The 1 mm guard is not a minimum-web specification

The generator excludes keyed transfers within 1 mm of a third member's stock. That **guard parameter** prevents some geometric recess conflicts. It does not constrain every remaining region of the resulting nonconvex timber to be at least 1 mm thick, and it is not a structural design rule. The measured 1 mm post walls happen to be real consequences of the present geometry; other features need their own measurements and checks.

The 40% width/depth key envelope is similarly a conceptual generator choice. Actual keys are clipped by intersection geometry and can have compound, nonstandard shapes. The JSON distinguishes members that actually donate keyed projections from a hypothetical 40% envelope calculation; a receiver's nominal section does not define its mortise size automatically.

## Cutter geometry and access

The 104 meshes contain approximately 4,000 segmented re-entrant mesh edges. This is **not** a count of machining operations or distinct mortises. Many edges are split by the boundary triangulation or intersecting cut planes.

No fillet radii, relief pockets, drilled start holes, tool diameters, cutting lengths, holder envelopes, machine-axis limits, entry moves or clamping bodies have been supplied. Consequently, the following are **not verified**:

- Whether any proposed pocket is accessible from a permitted tool direction.
- Whether the compound keyed shapes contain undercuts for a chosen setup.
- Whether a cutter can reach the required depth without holder/stock collision.
- Whether fixtures can hold the timber without concealing required surfaces.
- Whether subsequent setups preserve a consistent face/edge datum.
- Whether narrow tongues and thin walls survive machining or handling.

A machining process could involve appropriate mortising, boring, chiseling, sawing or multi-axis operations, but no such process has been selected or simulated. Rounded internal corners, rounded mating projections, or approved relief cuts would change the fit geometry and would need to be modeled together and rechecked. Relief cuts must not be added merely to satisfy a router if they compromise the timber joint.

## Allowances and timber datums

No universal clearance number is assigned here. A shop needs a joint-specific plan separating intended bearing faces and shoulders from entry/side clearances, reliefs and peg details. It also needs the species, grade, grain orientation, target and measured moisture content, actual dressed stock sizes, checking/warp limits and tooling capability.

The source's 8 × 10, 6 × 8 and 4 × 6 callouts do not establish actual measured stock sizes. Other sections and several dimensions remain modeling assumptions. The current model's micrometer-scale computational tolerance does not establish a comparable manufacturing accuracy in timber.

Wood changes dimensions with moisture, and shrinkage depends on species, direction and drying conditions. A nominal zero-clearance digital union should not be interpreted as a promise of permanently gap-free wood joints. The shop allowance and moisture plan must preserve the intended bearing conditions as the timber changes.

## What would permit a machining verification

1. Obtain an approved joint layout and remaining-section design for every connection, resolving the measured 1–2 mm local walls.
2. Select actual stock, machining datums and a moisture-control plan.
3. Specify the intended fit/allowance separately for each functional face and revise both mating members together.
4. Model real cutter geometry, holder, machine axes, clamps and tool approach; identify required hand finishing explicitly.
5. Simulate stock removal and collision/remaining-stock checks, then test representative joints in the actual timber before releasing all members.

This review supplies measurable problems and missing inputs. It does not prescribe final clearances, certify CNC access, approve the current keyed shapes or establish a safe erection sequence.

## Sources

Bergman, Richard. “Drying and Control of Moisture Content and Dimensional Changes.” In *Wood Handbook—Wood as an Engineering Material*. General Technical Report FPL-GTR-282. Madison, WI: U.S. Department of Agriculture, Forest Service, Forest Products Laboratory, 2021. https://research.fs.usda.gov/treesearch/62261. The official chapter description addresses moisture control, dimensional changes and construction/storage handling.

Autodesk. “How to Machine Internal Corners Correctly.” *Fusion Blog*. https://www.autodesk.com/products/fusion-360/blog/fusion-360-machine-internal-corners/. Explains why actual concave radii and tool dimensions affect tool engagement and remaining stock. Its example dimensions and rules of thumb are not adopted as timber-joint specifications here.

Autodesk. “Designing for Manufacture: Keeping the Production Team Happy.” *Autodesk University*, 2020. https://www.autodesk.com/autodesk-university/es/article/Designing-Manufacture-Keeping-Production-Team-Happy-2020. Explains corner relief for square mating parts; this supports identifying the present sharp-corner issue, not approving relief cuts in a structural joint.
