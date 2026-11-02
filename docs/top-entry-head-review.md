# Proposed top-entry upper rafter heads

## What changes

All **16 upper J-to-R interfaces at eight nodes** use real top-open seats. At R0 the pair is J0-0 and J7-2; generally Rk receives Jk-0 and J(k−1)-2. These are not the perimeter feet. The 24 released perimeter step laps, member axes, roof datums, cupola geometry, enclosure and construction aids remain unchanged. The original baseline and V13 perimeter model remain separate files.

The supplied undimensioned stepped-notch image guided the top-entry idea, not its dimensions. The trial retains the full 4 in nominal J width, penetrates 2 in inward from each hip side, and places the inclined floor 4 in below the hip top measured normal to that top. The two ends **do not need to meet**: their inner planes leave 4 in across the center. These are chosen design dimensions, not measured source details or approved proportions.

**This is a new/raw-stock design.** Each J needs about 5.556 in additional axial stock envelope beyond the old side-plane termination. The old hip-head mortise region is reconstituted from its original 8 × 10 stock envelope before the new cut, requiring an uncut/replacement hip blank—not a repair instruction for an already-cut timber. Other cuts outside the local head region are preserved. The replacement hip-stock envelope also retains the existing 2 in cupola-end tongue projection beyond its legacy reference end plane; that is an unchanged feature, not a new cupola cut or evidence of an original physical blank.

## Measured result

- Each new inclined bearing face is approximately **22.0358 in²**. Its normal has both upward and horizontal components on the receiving side; gravity bearing is not positive uplift retention. Reactions, capacities and fasteners remain unsolved.
- At the illustrated section normal to R0, V13 has about **70.638 in²** and the trial about **64.000 in²**, versus 80 in² gross stock. The latter is also the minimum among 121 sampled sections through the changed 55–85 in radial head region. The nominal 6 in bottom and 4 in central web are geometry, not allowable sections or proof of strength.
- All 104 timber volumes and centroids are recalculated. Total modeled timber becomes **6.29366006607 m³**, down approximately 0.00227036547 m³ from V13. Density/species/moisture remain separate unknowns; unchanged total weight must not be assumed.

## Fit and insertion evidence

The full-model audit considers 2,196 timber pairs involving the 24 changed members. It records the measured worst positive overlap, all known face-contact changes, nominal head contact gaps and explicit numeric limits. Each finished member is connected and closed; direct halfspace checks bound it within the stated raw-stock envelope. All 24 changed members' outer regions beyond a conservative 100 in radial plane are equivalent to V13, protecting the released feet.

Each entire J, including its foot, is tested over a continuous 24 in vertical translation against all 104 modeled timbers. The covering construction uses its initial solid plus each boundary triangle's full translation prism—not just selected poses or a whole-member convex hull. Summed prism intersections conservatively bound overlap; the bound also includes the per-prism numerical discard allowance. The declared positive-volume limit is 0.000001 in³, the kernel distance setting is 10⁻⁹ m, and the nominal contact-gap limit is 10⁻⁸ m. These are numerical CAD checks, **not literal physical zero clearance or machining tolerances**.

This does not model roof covering, walls/rails in the moving-member path, lifting gear, worker access, tolerances, moisture movement, or a safe raising sequence. Open top-entry clearance is intentional; bearing faces are nominally mated. No strength, stability, uplift or erection approval follows from geometric fit.

An independent reviewer checked the representative contact, section, volume, all affected intersections and continuous sweep; full-family review is recorded in the release handoff. The [comparison diagram](../public/review/top-entry-head-comparison.svg) uses actual meshes and named sections.

## Data and reproduction

`src/top-entry-proposed-model.json` is separate from both prior models. `top-entry-proposal.json` contains the actual sixteen comparisons and full audit. Matching load, material and enclosure datasets are source-hash-bound to the selected model. Old contact warning markers and fixed-area pressure shortcuts are not reused.

Run `scripts/top_entry_heads.py`, `scripts/top_entry_auxiliary.py`, and `scripts/fit_enclosure.py --model src/top-entry-proposed-model.json --output src/top-entry-proposed-enclosure-fit.json`; then run `tests/test_top_entry_heads.py` and `tests/test_top_entry_auxiliary.py` plus the repository checks.

Removed-stock and unfilled-gap overlays are **required follow-on repair work**, not completed. They must be derived from evidence-backed original stock minus the selected final solid, verified disjoint from its owner and reconstructing stock, with assembly-unfilled space classified separately. No legacy cutter mask is substituted while that validation is pending.
