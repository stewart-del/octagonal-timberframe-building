# Octagon R01 — contacts and joint development

The revised model follows the R01 framing pattern: eight radial triangular frames, sixteen short rafters, and no center-running wall-midpoint rafters. The two short rafters in each bay meet the side faces of the neighboring main hips. They do not run to the cupola bands.

This revision establishes the member arrangement and visible geometric contact surfaces. It does not establish load capacity, final joinery, fasteners, machining allowances or a verified raising sequence. A flush intersection is not, by itself, a completed joint.

## What changes from the previous model

- Preserve the main-frame piece IDs. Retire `J0-1` through `J7-1`, the eight center-running midpoint rafters; do not reuse those IDs for new objects.
- Retain `Ji-0` and `Ji-2` as the two short rafters in bay `i`. Their alignment, lengths and upper contact surfaces change to suit the adjacent hips.
- The revised inventory retains 96 timber IDs. Of these, the 24 `Li-L/S/H` cupola bands remain contextual and hidden by default because their arrangement is not established by this pattern. The 72 other timbers form the visible timber inventory. New metal objects and roof reference surfaces are counted separately.
- Use 6 × 10 in lower radial ties, as directed by Stewart. The earlier 6 × 8 in reconstruction is superseded.
- Interpret 30 ft as the diameter across outside radial post faces. For the working 8 in post section, the center diameter is 29 ft 4 in. Main roof tips are 33 ft 4 in across.
- Use the R01 20 in radial overhang beyond the outside post face. The earlier 2 ft 6 in normal-overhang reconstruction is superseded for this pattern.
- Use a radial 4:12 main roof slope and its compatible normal slope, approximately 4.329569:12. Use the confirmed radial 4:12 cupola roof slope with 12 in radial overhang outside its posts.
- Represent the green cupola spacers and black temporary assembly fitting as separate metal objects. Neither is a substitute timber member. Green spacers use `M-SP0`–`M-SP7`; temporary fixture arms use `M-TMP0`–`M-TMP7`. The eight `ENV-CUP*` objects are roof reference surfaces, not timber rafters.
- Remove the earlier generated overlap keys from the current joint interpretation. Their cut labels, fitted-solid results and withdrawal tests belong to the superseded geometry and cannot validate this revision.

## Reference surfaces and dimensions

All values below refer to the R01 geometric study. They are not blank lengths or cutting instructions.

| Reference | R01 value and status |
| --- | --- |
| Main-post outside radial diameter | 30 ft; user-confirmed datum |
| Main-post center radius | 176 in, conditional on actual 8 in radial post width |
| Main eave-tip radius | 200 in |
| Main hip section | 8 × 10 in source reading; actual section and roof backing still require confirmation |
| Lower radial tie section | 6 × 10 in, user direction |
| Short-rafter section | 4 × 8 in, provisional source reading |
| Cupola outside / inside radial faces | 88 / 76 in diameter |
| Cupola post centers | 41 in radius, with radial 6 × 6 in posts |
| Short-rafter clear gap | 42⅜ in, apparent source reading |
| Short-rafter center spacing | 46⅜ in when actual width is 4 in |
| Green spacer gap | 28⅛ in between adjacent outward post corners; not a metal blank length |

The roof reference surface and a timber centerline are different. Displayed solids may be positioned below the roof surface using explicitly stated section assumptions. Backing a hip to neighboring roof planes, or terminating a short rafter on a hip side plane, does not define a housing, tenon, bearing seat or fastener.

## Contact families in the revised pattern

Indices are modulo eight. `Bi` spans from main corner `i` to `i+1`. The retained short-rafter IDs refer to the two opposite sides of that same roof bay.

| Review family | Members or objects | Current geometric relationship | Joint design still needed |
| --- | --- | --- | --- |
| `JT-EAVE-i` | `Pi`, `B(i−1)`, `Bi` | Perimeter ring ends meet over the main-post location. Equal octagon plan miters are geometric references. | Supported bearing and positive continuity through the corner; post-head connection, available wood and assembly access. A plain miter does not establish the connection. |
| `JT-TIE-OUT-i` | `Ti`, `Pi`, coordinated with both ring ends | The lower radial tie ends at its selected outer support/contact datum. Its section is 6 × 10 in. | Tie shoulder, bearing zone and restraint; any mortise/tenon, housing or connector must be sized and coordinated with the post-head joint. |
| `JT-HIP-HEEL-i` | `Ri` and the main-post/ring/tie corner | Main hip crosses the perimeter support while its tail continues to the corrected eave. | A confirmed heel and bearing datum, bearing area, thrust/uplift restraint and any required seat. The unresolved support detail must not be disguised by overlapping solids or arbitrary subtraction. |
| `JT-BRACE-i-A/B` | `Ki-A/B`, `Pi`, neighboring ring members | Existing brace identities remain available for review of the perimeter subframe. | Confirmed brace shoulder locations, end connections and an insertion path coordinated with the other corner joints. |
| `JT-INNER-BASE-i` | `Ti`, `Ci`, any retained lower-band members | The radial frame reaches the cupola support location. | Actual cupola-post bearing, the tie/post connection and the role of retained band members. The metal assembly fitting does not supply a permanent timber connection. |
| `JT-HIP-HEAD-i` | `Ri`, `Ci`, any neighboring roof-level band members | Main hip reaches the cupola outside radial-face reference. | Actual bearing and connection to the cupola, its elevation, remaining section and assembly access. Do not carry over the former generated keys. |
| `JT-SHORT-i-0` | `Ji-0`, `Ri`, `Bi` | Short rafter runs perpendicular to the eave and ends at the near side face of `Ri`. | Support/bearing and retention at the hip; eave bearing and restraint; a defined end detail suited to the available sections. |
| `JT-SHORT-i-2` | `Ji-2`, `R(i+1)`, `Bi` | Mirrored short rafter ends at the near side face of `R(i+1)`. | The corresponding mirrored connection. Do not assume its compound end is interchangeable with the other handed piece. |
| `JT-CUPOLA-i-*` | `Ci`, neighboring retained cupola bands | Existing band identities are retained where present; their role and connections remain provisional. | Connection arrangement, compatibility with hip bearing and a closure that can actually be assembled. No fully captured cycle of fixed tenons is established. |
| `JT-SPACER-i` | Adjacent cupola posts and a separate green metal spacer | The spacer follows the outer-corner-to-outer-corner gap. | Stock, returns, holes, attachment and developed length. The 28⅛ in clear gap supplies none of those values. |
| `JT-TEMP-CENTRAL` | Black eight-arm assembly fixture and temporary support | Separate temporary assembly equipment beneath the cupola. | Steel details, attachment, erection loading, stability and release/removal criteria. Visibility in the viewer is not an instruction to install or remove it. |

These labels identify review locations and relationships, not approved connection details. References to retained bands or braces do not authenticate their source dimensions or concealed joinery.

## Short-rafter end geometry

For a bay with half-angle `α = 22.5°`, main eave radius `Re = 200 in`, clear gap `g = 42.375 in`, and working short-rafter width `b = 4 in`:

```text
d = g + b
ρ = d / (2 sin α) = 60.591857496 in
t = 0.348520356260
normal roof slope pn = (1/3) / cos α = 0.360797400097
```

Place the two eave starts at fractions `t` and `1−t` along their bay's eave side. Run both inward perpendicular to that side. Their reference axes intersect the adjacent hips at radius `ρ`, outside the cupola.

| Reference measurement | Inches |
| --- | ---: |
| Plan run to hip axis | 128.796329525 |
| Rise to hip axis | 46.469380835 |
| Sloping reference length to hip axis | 136.922963210 |
| Sloping center-reference length to hip side face | 125.810940162 |

The last value assumes an 8 in wide hip with its side plane 4 in from its radial axis. The physical end is a polygon obtained by intersecting every relevant timber edge with that plane. Applying the same shortened length to all corners would not reproduce this skewed end.

For a line `X(u) = X₀ + uv` and contact plane `N · X = K`:

```text
u = (K − N · X₀) / (N · v), provided N · v is not zero
```

A roof-surface reference, timber axis, long point, short point, bearing shoulder and tenon tip are different endpoints. The values above exclude joint projections, housings, seats, clearance, stock allowance and machining setup. Display them as geometry measurements, not saw settings or lumber-order lengths.

## Cupola metal details

Radial 6 × 6 in cupola posts at 41 in center radius reconcile the two diameters and the green-spacer gap. For the first pair, outer-corner endpoints are `(44, 3)` and `Rot45°(44, −3)` in plan inches. Their separation is 28.132864853 in, which rounds to 28⅛ in. The center-to-center post chord is a different measurement: 31.380041 in.

The black fitting is an eight-arm arrangement at 45° spacing. R01 transcribes an 88 in overall span, 14 in end height and 4 in strip depth, with three holes drawn per terminal. Steel thickness/grade, hole sizes and spacing, bends, welds, central junction and fasteners are unspecified. Rendered hardware may therefore be schematic only; no metal cutting or drilling schedule follows from this model.

## Unresolved inputs and validation boundaries

- Ground-to-tie reference height `H`; the apparent 32 in glazing height's exact endpoints; roof-bearing levels; and any retained demonstration elevations.
- Actual timber sections, species/grade/moisture, backing and member-specific joint allowances.
- The physical bearing and connection at each family above, including remaining wood and compatible assembly access.
- Wall and window assemblies. “Boston Layout” is confirmed, but the blurred size string does not establish window width, quantity, rough openings or sill/head heights.
- Foundation/post anchorage, roof build-up, loads, permanent bracing, fasteners, temporary works and the raising sequence.

Geometry checks should establish the revised counts and ID mapping, the correct reference diameters, each short rafter's roof plane and adjacent-hip contact, finite closed solids, and any explicitly tested interference. A check of one interface must not be presented as an all-member contact or collision audit. Rendering an exploded frame proves neither insertion access nor erection safety.

Final joinery can be developed from these relationships once its bearing datums and required design inputs are fixed. Dimensions that remain unresolved must stay visibly unresolved in the viewer, schedules and downloads.

## Source and revision record

- **Octagon-architectural-geometry-study-R01.pdf**, twelve-sheet geometric reconciliation prepared for Stewart Lundy, incorporating his November 1, 2026 corrections. This is the immediate pattern reference; it explicitly distinguishes user directions, source readings, calculations and unresolved fabrication details.
- Robert Swinburne / Bluetime Collaborative, [“Octagon Timber Frame Outbuilding”](https://www.bluetimecollaborative.com/robert-swinburne-vermont-architect/octagon-timber-frame-outbuilding), May 3, 2010; source drawing dated May 8, 2010, as recorded in R01.

The earlier 104-timber fitted reconstruction and its 40% overlap keys are a superseded study. Historical files may be retained for comparison, but their geometry, cut-face labels, tests and reports must not be described as validation of R01.
