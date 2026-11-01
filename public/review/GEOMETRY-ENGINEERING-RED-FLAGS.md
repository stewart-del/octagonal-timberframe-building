# Geometry evidence for engineering review

**Disposition: not ready for fabrication or erection.** The existing geometric fit audit establishes digital non-overlap, complementary contact and connected meshes. It does not establish a load rating, joint strength, machining allowance or safe erection sequence. The fitted joints are an algorithmic prototype, not reconstructed traditional joints or an engineer-designed connection system.

This independent review reads the final `fitted-cells.json` and `fittedparts.json`. It does not alter the solids. All measurements below describe geometry only; retained area percentages are **not strength or capacity percentages**.

## Principal findings

| Piece / location | Measured retained section | Where to inspect | Implication for design review |
|---|---:|---|---|
| B0 eave ring, near R0 | 233.75 mm² of 30,967.68 mm²; **0.755%** | Station 70.930738 mm / 2.792549 in; `FC-B0-001`, `FC-B0-064`–`067`, `FC-B0-075`–`077` | A severe geometric neck remains near the corner. It is inside the fitted piece, not the extreme miter tip. The nominal 6 × 8 in ring section cannot be assumed to continue through this detail. The force crossing this particular neck is not established. |
| J0-0 secondary rafter at B0 eave beam | 1,238.71 mm² of 7,741.92 mm²; **16.000%** | Station 940.450987 mm / 37.025629 in; `FC-J0-0-019`–`021`, `023`, `024`, `026` | The 2 × 6 in rafter is reduced to a central 20.32 × 60.96 mm / 0.8 × 2.4 in key across this section. This is within its length at the eave crossing; it is not just an end tenon. Its cantilever and support connection require redesign or justification. |
| R0 hip rafter, eave/post/tie intersection | 33,052.44 mm² of 51,612.80 mm²; **64.039%** | Station 1,009.116266 mm / 39.728987 in; `FC-R0-004`–`007`, `012`–`014`; cutter provenance B0/B7/P0/T0 | Several simultaneous cuts reduce the 8 × 10 in member. Net section, shear, bearing, grain direction, and load transfer need explicit engineering. |
| T0 radial tie, hip intersection | 9,599.98 mm² of 30,967.68 mm²; **31.000%** | Station 296.239691 mm / 11.662980 in; `FC-T0-001`, `004`, `005`, `017`–`019`, `021`; provenance R0 | The cut crosses a substantial part of the tie. At this section the retained material consists of separated regions in the section plane; they connect elsewhere in the 3D solid. A whole-piece connectivity test does not establish an effective tension tie. |
| C0 cupola post, roof/band zone | 14,729.40 mm² of 23,225.76 mm²; **63.418%** | Station 985.896893 mm / 38.814838 in; `FC-C0-001`, `005`, `007`, `016`–`018`, `044`; cutter provenance includes R0 and cupola bands | The assumed 6 × 6 in column is locally reduced by multiple intersecting joints. |
| K0-A brace near P0 | 479.93 mm² of 9,290.30 mm²; **5.166%** | Station 46.762435 mm / 1.841041 in; `FC-K0-A-009`–`011`, `014`–`017`, `030`, `031` | A small, irregular neck appears near the post end. This is a geometric fact, not a calculated brace or tenon capacity. |

All eight eave beams exhibit an approximately 0.755% sampled near-corner section. All 24 secondary rafters exhibit approximately 16% sampled sections. The pattern follows the repeated joint-generating algorithm, rather than being an isolated rendering defect.

The modeled 2.5 ft total roof overhang beyond the assumed post envelope makes the eave connection and remaining rafter section particularly relevant to the design. This review does not assume a snow, wind, live, dead or maintenance load or calculate a permissible load.

## B0 neck is inside the actual member

B0's fitted solid extends from station **−31.563148 mm to 3,530.820304 mm**. The 70.930738 mm section is 102.493886 mm from its near extreme. The original stock is full 6 × 8 in at all three following sections:

| Station along B0 | Retained area | Fraction of full stock |
|---:|---:|---:|
| 60.930738 mm / 2.398848 in | 620.49 mm² | 2.004% |
| 70.930738 mm / 2.792549 in | 233.75 mm² | 0.755% |
| 80.930738 mm / 3.186250 in | 3,328.57 mm² | 10.749% |

The center slice contains an approximately 40.42 × 11.50 mm bounding triangle plus a very small second rectangular region. It is not a full 40%-width by 40%-depth rectangular key at this station. Tiny polygon fragments can arise near intersections and are not, by themselves, reliable minimum-thickness measures.

See [B0-net-sections.svg](B0-net-sections.svg) for exact polygon slices and [J0-0-net-sections.svg](J0-0-net-sections.svg) for the secondary rafter. These are deterministic geometry drawings, not generated photographs.

## Key sizes and machining assumptions

The generator selects keys using **40% of nominal member width and depth**, then clips those envelopes against other stocks. That choice has no structural sizing basis. Its 1 mm third-member buffer is a Boolean geometry separation parameter, **not a tested 1 mm machining clearance or a verified minimum wood ligament**. Nominal mating clearance is zero for every piece.

Examples of actual boundary envelopes, measured in the tongue member's local axis and transverse directions:

| Key transfer | Tongue / receiver | Axis × transverse × transverse envelope | Interpretation |
|---|---|---:|---|
| `J-P0-R0` | R0 / P0 | 38.42 × 81.28 × 11.76 mm | The rafter-to-post feature has only an 11.76 mm maximum depth in this envelope, despite the nominal rafter being 254 mm deep. Its transferred volume is 19.02 cm³. |
| `J-C0-R0` | R0 / C0 | 95.38 × 81.28 × 101.60 mm | Different from the post-side feature despite the shared hip member. |
| `J-R0-T0` | T0 / R0 | 575.58 × 60.96 × 81.28 mm | A long irregular overlap transfer; not a verified traditional tenon or standard saw cut. |
| `J-T0-L0-L` | L0-L / T0 | 56.39 × 19.94 × 60.96 mm | Competing cuts narrow the envelope below the nominal 40% width. |
| `J-B0-J0-0` | J0-0 / B0 | 188.04 × 20.32 × 60.96 mm | The narrow central key passes through the eave crossing of the rafter. |

Envelopes are bounds on boundary patches, not guarantees of a solid rectangular tenon. Exact surface IDs for each key are retained in `net-section-measurements.json`.

The following fabrication information is absent: timber species and grade; moisture at machining and service; actual dressed stock measurements; tool/kerf and cutter radii; fit class and allowable deviations by mating face; stock/tenon allowances; peg, bolt or connector design; and tool-access or workholding plans. Sharp polygonal inside corners have no cutter-radius treatment. They may require appropriate tooling or revised geometry; this review has not proved each pocket accessible. Neither a positive arbitrary clearance nor the model's zero clearance can be accepted as a fabrication allowance without those decisions.

`mate_part_id` is cutting/transfer provenance. It is not proof that the entire labelled patch still contacts that named member after later cuts. Do not automatically interpret every `FC` face as an engineer-defined bearing surface or pocket.

## Volume retention is an inadequate strength check

| Member family | Fitted volume / original stock volume |
|---|---:|
| Perimeter posts | 99.608% |
| Cupola posts | 97.239% |
| Major hip rafters | 96.798% |
| Secondary rafters | 96.259–96.261% |
| Eave ring beams | 93.278% |
| Radial ties | 86.987% |
| Cupola bands | 80.770–93.177% |
| Braces | 74.330% |

A beam can retain most of its total volume and still have a very small section at one joint. No conclusions about member or connection capacity follow from these volume percentages alone.

## Measurement convention and limits

`station` is distance along the part's unit `axis_direction`, from its original `axis_start` in `fittedparts.json`. Coordinates are meters, Y up. For example:

- B0 axis start = (4.571999788284302, 2.2860000133514404, 0), direction = (−0.3826833561365775, 0, −0.9238795640861667).
- J0-0 axis start = (5.134775638580322, 2.022295117378235, −0.9794254451990128), direction = (−0.9338046681662668, 0.31029516787614314, 0.17811723808661706).

Each original and fitted convex cell is independently intersected with a plane normal to the member axis. Polygon areas are summed across cells. The scan uses midpoints and samples up to 0.01 mm inside the interval boundaries defined by all cell vertex stations. Source-stock sections below 95% nominal area are excluded to avoid treating extreme miter tips as reduced nominal sections. Results are **sampled minima, not proven global minima** and not structural stress analyses.

The JSON additionally provides a statistic excluding one maximum nominal section dimension at both stock ends. It reports fitted extents and a minimum at least 1 mm inside those extents. This matters for T0: the first 83.56 mm of its original stock axis has no retained timber; the zero area there means the original end was removed, not an internal break. The table above uses T0's body statistic to avoid that misleading endpoint result. The R0 and C0 values are also body results. B0, J0-0 and K0-A use actual interior necks identified above.

These measurements do not prove tensile, bending, compression, shear, splitting, buckling, joint bearing, uplift, racking, diaphragm, foundation or temporary-stage capacities. They also do not prove an assembly path. A separate erection/kinematic review is required; a collision-free final pose alone is insufficient.

## Reproduce

Run `review_net_sections.py`, then `make_section_figures.py` from this directory or the workspace root. Inputs are read only. Outputs include all 104 part measurements, 168 key envelopes, surface references and section figures. The fitted geometry remains unchanged.
