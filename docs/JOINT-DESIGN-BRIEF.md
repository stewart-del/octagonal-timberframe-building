# Octagon joint redesign brief

**Aim:** keep the documented building layout and timber sections, and replace the generated overlap keys with recognizable, buildable timber-frame joints. This is a connection-design proposal, not a change to all model pieces or a new load-capacity assessment.

The existing building is the reference. The original 864 × 631 image has now been inspected: it is a building overview, not a dimensioned corner-joint detail. It does not authenticate the generated wing-like projections or concealed joinery. Accordingly, everything called **proposed** below is a new detail to develop, not a claim to have recovered Swinburne's original joinery.

The fresh assembled fitted-solid check reports zero member-pair overlaps above 1e-10 m³. This does not approve the saved 40% key envelopes, bearing, cuts, retained wood or assembly paths. The hip/ring bearing-datum conflict described below remains unresolved; the overview does not establish a replacement datum.

## Baseline and one necessary geometric correction

Retain the source's 8 × 10 major radial members, 6 × 8 horizontal radial members, 4 × 6 cupola bands, and documented setting-out dimensions. Preserve the user's minimum 2 ft 6 in roof overhang. Other model sections and vertical datums remain tagged with their existing source status; a section that was a rendering assumption does not become a documented building specification through repetition.

Discard the requirement to preserve the union of the original colliding prisms. A real tenon can extend beyond a shoulder line; a beam can end at a post face; a seat can sit above its support. Those are legitimate joint changes, not accidental gaps.

The first detail to resolve is **vertical bearing at the roof supports**. In R03, the roof upper surface is placed approximately level with the eave-ring top at the post. Consequently, the 10 in hip penetrates almost the full ring depth and below its underside. The automated fit process cut the ring and hip around that collision. A conventional seat cannot simply be inserted into that same occupied volume. Establish the source's plate, tie, hip seat and roof-surface datums, then position the hip on a deliberate seat or heel. This can correct an assumed model datum without changing the documented lumber sizes or plan.

## Connection families to develop

Indices are modulo 8. At corner i, the adjoining eave members are B(i−1) and Bi. Cupola bands use the existing L/S/H suffixes for lower, roof-level and upper bands.

| New joint family | Existing pieces | Proposed detail | Insertion / blank implication |
|---|---|---|---|
| `JT-EAVE-i` | Pi, B(i−1), Bi | Direct beam bearing over the post. Develop a **supported oblique lap** between the ring ends, with a post-head stub tenon or a designed locating/locking detail. Keep the visible 22.5° corner geometry, but do not treat a plain miter as a tie. | Extend ring blanks past their shoulder/miter references as required by the lap. A post-head tenon adds length above the post body's bearing shoulder. The lap must remain over its support. |
| `JT-TIE-OUT-i` | Ti, Pi; coordinated with both B members | **Housed, shouldered mortise-and-tenon** for the radial tie, with a through/wedged or other positively tied variant if the connection's role requires it. Reserve its mortise zone before locating ring and brace joinery. | Insert as part of a radial subassembly before closing the perimeter. A fixed tenon adds blank length beyond the tie's shoulder. A through/wedged version also needs exposed wedge access and relish. |
| `JT-HIP-HEEL-i` | Ri, Ti and/or the supported B corner | **Bearing heel/seat** with an explicit abutment for the hip's horizontal component; develop a small locator/tenon only where useful. Choose one defined load-transfer detail, not multiple deep interpenetrating keys. | Lower the hip into the completed support or place it with the radial subassembly. Keep the overhang tail continuous across its support. Verify the path before adding any captured tenon. |
| `JT-BRACE-i-A/B` | Ki-A/B, Pi, B members | **Shouldered brace tenons in shallow housings**, with one end deliberately arranged for assembly in the chosen subframe. | Fixed tenons at both ends require preassembly before the receiving frame closes. If a brace must be installed later, develop a chase-mortise or accessible removable connection specifically for that brace. Include tenon length in the blank. |
| `JT-INNER-BASE-i` | Ti, Ci, L(i−1)-L, Li-L | Direct support of the cupola post and lower ring on the inner tie/support arrangement. Develop **supported ring laps and a post-foot stub tenon**, or a housed alternative, once the actual support bearing is laid out. | Form the lower ring on temporary support, then lower posts into foot joints. Do not allow three blind mortises to occupy the same little corner of a 4 × 6 band. Added tenons require blank extensions. |
| `JT-HIP-HEAD-i` | Ri, Ci and adjacent L-S bands | **Housed hip head / shouldered tenon** or a deliberate open bearing seat at the cupola. Give the hip its own bearing zone. Adjacent band tenons must stop, offset or change level before reaching that zone. | Prefer top/down or inward-access assembly while the upper cupola remains open. If a conventional fixed tenon captures the hip, assemble the receiving cupola portion together with it. |
| `JT-CUPOLA-i-L/S/H` | Ci, L(i−1)-*, Li-* | Normally **housed, shouldered band-to-post tenons** where post geometry permits; supported laps are an alternative at the lower and top levels. Stagger adjacent oblique tenons, or shorten one into a blind mortise with adequate wood between pockets. | A closed octagon needs an explicit last connection. Assign it before cutting. Use an accessible loose-spline/locking-key closure on designed bearing seats, or a concealed connector at that closure, rather than two uninsertable fixed end tenons. |
| `JT-SECONDARY-i-j` | Ji-j, Bi, Li-S | **Shallow rafter birdsmouth/bearing seat at the eave** and an end bearing/housed seat at the cupola band, according to the corrected roof-support datum. Use a defined uplift/side-restraint detail. | Lower from above after primary supports are connected. Preserve a substantial continuous rafter section through the eave and overhang; remove the present central 0.8 × 2.4 in key. Do not heavily mortise a thin secondary rafter merely to imitate heavy-timber joinery. |

These are joint families, not approved depths, peg sizes, tenon widths or machine settings. Such dimensions must follow the chosen bearing surfaces, available stock and actual tool setup. Merely naming a joint does not resolve its fit.

## First prototype: corner P0 / B7 / B0 / T0 / R0

Build and dry-fit this complete corner before replicating it eight times.

1. **Define reference shoulders:** P0 head bearing, B7/B0 support underside, T0 outer shoulder and R0 heel. Resolve the roof datum before subtracting any cuts.
2. **Place the supported ring joint:** start with an oblique lap over P0. Its horizontal meeting angle is 135°; the visible equal miter is 22.5° off square. A half-depth lap is one conventional starting form, but its remaining section and bearing must be resolved for this corner; it is not an automatic instruction to remove 4 in everywhere.
3. **Reserve the tie zone:** T0 receives a real shoulder and tenon at a dedicated level/position. If the current assumed coplanar T/B arrangement leaves no viable mortise zone, correct that offset from the source or develop a specific tying-joint arrangement. Do not excavate whichever timber happens to have lower software priority.
4. **Seat the hip:** preserve the R0 body and extended tail, and cut only the chosen seat/heel. Determine how thrust and uplift are restrained. R0's notch must not consume the ring corner or collide with the tie tenon.
5. **Add the brace joints last:** K0-A/B mortises lie outside the post-head/tie congestion. Use the documented brace setting-out as the baseline; any small joint staggering needs an explicit changed shoulder coordinate.
6. **Prove the movement:** the chosen joint should have a visible insertion route, open tool access, and an accessible peg/wedge/fastener position. Simulate the complete subassembly movement, not just each piece separated radially in an exploded picture.

A useful lap-ring insertion candidate is four alternate lower-lap members followed by the four upper-lap members. This avoids giving every beam one under-lap and one over-lap in a locked cycle. It is only a candidate until the post tenons, braces, tie positions and corner geometry are included in the motion test. A prefitted ring lifted as a unit is another option; it requires its own lift/support plan.

If an all-wood corner leaves too little sound timber or no practical insertion route, retain the timber bearing and use a concealed engineered tie/connector locally. That is a deliberate alternative, not a reason to return to arbitrary 40% keys.

## Cupola closure: choose it before detailing the mortises

The current three closed bands and eight posts should not be given fixed tenons on every end and assumed to assemble afterward.

Proposed sequence concept:

1. Dry-fit the lower support ring and its tie interfaces on a setting-out platform with the documented central opening.
2. Assemble compatible post/band subframes while their joints remain accessible. Label which parts move together.
3. Reserve a named closure bay—initially **L7-L / L7-S / L7-H between C7 and C0**, subject to access review. The lower band may be closed before posts are installed; the roof-level closure must remain installable after the adjacent subframes stand.
4. At the closure, use designed bearing shoulders with an accessible loose spline/key or concealed connector if a fixed-tenon insertion path is unavailable. Model the spline/key/connector as its own part. Do not create an unnamed wedge or omit it from the cut schedule.
5. Place the upper cap band after the hips and lower roof joints that need access. Confirm that temporary support can be released only after the specified permanent connections and bracing are complete.

This is an assembly strategy for selecting joints, not a field lifting or shoring instruction. The black temporary central assembly remains explicitly temporary; its removal must follow the completed connection scheme, not the disappearance of an object in the viewer.

## Machining and model rules for the replacement joints

- Separate **overall blank**, **shoulder-to-shoulder**, **tenon projection**, **housing depth**, **remaining section**, and **final outside envelope**. Current axis lengths are not sufficient blank lengths.
- Use one stable bearing reference per interface. Keep intended shoulders bearing; allow specified clearance only on the correct nonbearing cheeks, tenon tips or relief surfaces. Do not globally scale male or female geometry.
- Set tenon-tip relief, moisture movement allowance, kerf and tool-radius treatment with the fabricator. The model's present zero clearance and 1 mm third-member guard are not workshop prescriptions.
- Keep peg holes, wedges and hardware separate from visualization features. Drawboring is a deliberate hole offset, not an accidental mismatch; it must be dimensioned and compatible with assembly access.
- Stagger adjacent mortises by an explicitly dimensioned depth, offset or level. Keep remaining wood visible and measurable in isolated-piece mode.
- Give every new joint a `JT-*` identifier and its individual cut faces new `FC-*` identifiers. Retain P/B/T/R/C/L/K/J piece IDs; preserve old FC labels only as a superseded revision, because they describe different surfaces.
- Validate three things separately: final solid contact/collision, physical insertion/removal paths including closure pieces, and workshop access/clearances. A successful boolean subtraction proves only the first.

## Source grounding

The proposals above are project-specific design inferences. They are not details copied from the existing building.

- **TFEC, Rules of Timber Joinery Design (2011-03):** supports deliberate bearing surfaces, preserving useful timber section and allowing shrinkage without opening bearing shoulders. It illustrates why joint shape and material removal need to be chosen together; it supplies no octagonal corner recipe. [Primary bulletin](https://www.tfguild.org/timber-frame-engineering-council/technical-bulletins/view/112/download).
- **Timber Framers Guild, Glossary (2015):** supplies the terminology for birdsmouth, bearing, bridle, chase mortise, housing and assembly marks. A chase mortise can enable an otherwise blocked insertion; its use here still requires specific geometry. [Primary glossary](https://www.tfguild.org/documents/Glossary2015.pdf).
- **Timber Framers Guild, Timber Framing: The Basics:** describes mortise-and-tenon/pegged framing, ground test-fitting and raising subassemblies, and the use of concealed connectors when appropriate. [Primary guide](https://www.tfguild.org/timber-framing-the-basics).

Next model work should complete and demonstrate `JT-EAVE-0`, its associated tie/hip/brace joints, one secondary rafter seat and one cupola closure. Once those are coherent, replicate the proven geometry around the octagon instead of redesigning all 104 parts simultaneously.
