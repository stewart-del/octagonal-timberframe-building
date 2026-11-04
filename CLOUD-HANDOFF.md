<!-- TIMESTAMP START 2026-11-04T07:06:41-05:00 | REVISION R005075 -->
# Octagonal timberframe: cloud continuation, November 4, 2026

The owner requested moving the ongoing implementation into Codex Cloud. Finish the outstanding geometry/motion verification, fix regressions, build, then deploy to the existing Sites website and update GitHub. Publication and all necessary deployment steps are already explicitly authorized. Preserve the finished design. This checkpoint contains unfinished work, not a release.

## Source and publication boundaries

Repository: https://github.com/stewart-del/octagonal-timberframe-building . GitHub main was reread on November 4 and is `b1eec82544e64fa255f82ae8c0244e40b4e1e96a`. The migration branch must be parented to this real main, not to the synthetic local implementation history.

Live website: https://octagonal-timberframe-building.brujodinamico.chatgpt.site/ . Last confirmed publication is version 24, Sites project `appgprj_6ae7b53036e08191809ba201e56e49d3`, version `appgprj_6ae7b53036e08191809ba201e56e49d3~appgver_02798dc9cff4819184a3ddce5349ca8b`, deployment `appgdep_6aea1738f17081918a4da2d3fcc042a4`, source `f7f10f83910e3a572d74e42398eb52c828dbeb05`. Preserve public audience. Recheck before publishing; these Sites values are historical, not a fresh November 4 deployment check.

The source below is newer than that release. `index.html`, any `dist/`, and the saved disassembly certificates are stale for the new joints. Build checks should reject them until corrected. Do not deploy them. Local `DEPLOYMENT-HANDOFF.md` described v24 and is superseded by this file for unfinished work.

Local implementation origin: `/Users/stewartlundy/Documents/ChatGPT/Timberfame Octagon/work/next-version`. Do not depend on that path in cloud. All November 3 `/tmp/octagon-*` motion checkpoints and test logs disappeared before November 4; regenerate them. No planning process remains running.

## Accepted design requirements

- Main eight posts remain 8×8. Cupola posts remain 6×6. Porch posts and door/window jambs are 4×4. The owner's later clarification overrides the earlier suggestion to resize cupola posts.
- North–south 2×6 joists over eight radial beams meeting the fixed central floor hub. Main foundation has 17 piers: center, eight midpoint piers at half radius, eight outer piers. Four porch piers give 21 total. Each column is continuous, with six feet underground shown translucent; either zone selects its full height.
- Skeleton view includes porch, stairs and porch floor. Floor components are individually selectable. Porch and door face site west; the compass is determined. Default camera centers inside the octagon and includes the full building; preserve the mobile canvas improvements.
- Keep the original simple welded eight-L steel fixture shape at its accepted location. It is visible in full view, present before the first truss in assembly, and removed only after all trusses clear in disassembly. Bamboo finish installs after the roof and removes near the beginning.
- Ordered disassembly first disengages joints without positive-volume interference, then reaches compact spherical destinations. Porch moves outward and never jumps back near the end. Floor hub and central pier remain fixed. Preserve whole-building spherical mode, plus assembly mode in which pieces appear and slide into place in reverse disassembly order.
- Wall height means finished floor to underside of main octagon beam. Variable pitch changes the main roof only; cupola and porch remain 4:12. Geometry, joints, voids, roof interfaces and plans must follow parameters.
- Knee braces are centered in their receiving members, with square mortises and squared shoulders. Inward braces are longer/lower to avoid overlapping the other post joints. All tenons are three inches deep, including railing infill; the owner authorized enlarging receiving rails. Bearing laps are not tenons.
- Pegs must cross real tenons and matching receiving bores with wood engagement. Selected pieces show tenon depth, width and height. Main post-to-octagon-beam mortises may be open at the top, covered by rafters when assembled; owner explicitly approved this to permit assembly/removal.
- Plans need clear numeric dimensions, rise, span, rafter length, angles and truss dimensions, derived from current geometry. Separate porch projection where it confuses the main frame. Remove obsolete construction aids. Roof shingles match the main roof color.

## Saved implementation and verification

Geometry already saved: centered 2×6 braces; inward brace feet at 50 inches versus perimeter 62; three-inch structural tenons; open-top three-inch main ring post slots; three-inch cupola foot dovetails with real pegs; three-inch wall/porch joints and enlarged receiving rails. Original eight-L fixture is preserved. New `src/joinery-dimensions.js` exposes real dimensions.

Primary model SHA-256 values at migration:

- `src/model-data.json`: `f9c894dfa6cb8915393b4a3d7a42dea702cd162b1db33a426decbb83a05a864a`
- `src/step-lap-proposed-model.json`: `940b1185925edae29a5c2929a7eb8017fc42ef4508b5194292f7d9860e0670e3`
- `src/top-entry-proposed-model.json`: `de9c5696d73043ad594f3578c4a6069427cc425207508c63a6349436bcf63fa4`

Parameter controls and `src/parametric-model.js` exist; main pitch 3–8:12 and wall height 89.03615129287599–144 inches. Default dimensions bypass regeneration exactly. Cupola and porch stay 4:12. See `docs/parametric-model.md`. Known incomplete behavior: changed dimensions currently disable ordered disassembly and assembly because only the saved default route is certified; spherical mode works. Do not describe dynamic ordered motion as completed.

Durable reports were regenerated November 3: all three cavity fits; peg engagement (101 main and porch pegs); 24 brace sections and visibility; wall and porch joinery fits. November 3 verification passed all three revised-joinery scenes, 134 wall joints per variant, 729 porch solids/89 cavities/3691 pair checks/172 insertion checks, 32 cavity tests including adversarial tests, and twelve parameter scenes (three variants at 3:12/minimum wall, 4:12/96, 5:12/96, and 8:12/144). These are recorded prior results; raw temporary logs are gone, so rerun relevant checks. Geometric fit is not a structural engineering certification.

## First unfinished work: new disassembly route

`scripts/plan_revised_disassembly.py` persists, but its `/tmp/octagon-revised-route-checkpoint.json` and failure JSON do not. Rerun from the beginning. It uses `scripts/compact-disassembly-route.json` as the previous route, then replaces affected joint-release movements.

The prior run reached 1178 checked stages, including all eight main post movements, then failed at `assert not loose_walls(scene), 'Wall members remain held after frame release'`. Investigate remaining wall members and whether they merely missed preferred targets or still retain mating contact. Do not remove the assertion or weaken collision checks without resolving the physical condition.

Saved planner fixes: withdraw T plus inward brace 0.12 m, lower brace 0.1 m, tangent detours around standing posts; move the steel fixture only after T members clear; lift all octagon beams 0.12 m out of open-top slots and move them fully before perimeter braces; withdraw free perimeter braces horizontally; four shelf-trapped braces require carrying post/opposite brace/cleared pegs 1.2 m before sliding the brace axially below the shelf; parked-wall and peg detours are checked. Resume guards exist for some lower-frame steps; audit idempotence before relying on a failure checkpoint.

After a complete candidate, run independent certification through `scripts/plan_architectural_disassembly.py --complete-certificate --candidate-directory DIR` with variant candidates named `top-entry.json`, `baseline.json`, `proposed.json`. Require continuous swept collision checks, final separation and coverage of every physical piece. Exactly three intended fixed anchors are `FLOOR-CENTRAL-HUB`, `PIER-C`, `PIER-C-BELOW`. Prior historical baseline/proposed models remained honestly PARTIAL; their closed head joints must not pass through wood. Their temporary partial candidates are also gone.

The saved `src/disassembly-plan.json`, `src/architectural-disassembly-plans.json`, and `src/main-disassembly-plan.json` have not received the revised successful route. Their source hashes are stale for the new geometry. Generate fresh source-bound proofs rather than editing hashes alone.

## Regression/build work still pending

Viewer code now wraps initialization in `function startViewer(MODEL_CONTEXT)` between `PARAMETRIC_VIEWER_BODY_START/END`; asynchronous initialization is outside at `PARAMETRIC_BOOT_START/END`. Older Node test harnesses append assertions at outer scope and fail because `MODEL_CONTEXT`/`DATA` moved into this function. Adapt test injection to the real scope, preserve actual default boot, and rebuild before running built-viewer comparisons. `tests/model-variants.cjs` was affected. A stale-built-model `step-lap-review.cjs` comparison was stopped after a long run; rerun after fresh build.

Some test context fixes already persist in geometry-overlays, wall-framing-viewer, and enlarged porch guard height checks. The old illustrative step-lap comparison is explicitly marked archived; it predates centered braces/three-inch joints. Use main-view inspector dimensions for current geometry.

CI is `.github/workflows/check.yml`, with new revised joinery, peg, tenon dimensions, motion modes and parameter checks. Legacy cavity comparators use `tests/fixtures/legacy-cavity-report.json.gz`; current geometry uses current tests. Run full required CI after new route/build, then desktop/mobile browser checks for controls, all three modes, selection, plans, compass, complete-building framing and no overflow/errors. Only then deploy and read back exact published assets/source.

## Runtime

Use Python 3.12 and Node 22 or later. Install `numpy scipy manifold3d==3.5.4 Pillow` (Python) and use bundled `public/vendor/manifold.js`/`.wasm` for browser parameter geometry. There is no npm app framework to replace. Most scripts use repo-relative paths; `NODE` can override Node discovery. Use `PYTHONPATH=scripts` if needed. Example first route command: `PYTHONPATH=scripts python3 scripts/plan_revised_disassembly.py`. Geometry can be expensive; save durable checkpoints and logs outside `/tmp` after every phase.

Native manifold import precision matters: use `audit_revised_joinery.native_solid` for new near-coplanar joints, not old forced 1e-9 mesh tolerances. Physical overlap tolerance remains 1e-6 cubic inches. Keep adversarial tests.

## Change history and final delivery

Follow `AGENTS.md` and bundled tracking skill. Pending Mac revisions from the earlier implementation include R005024, R005026, R005027, R005029, R005041, R005043, R005049, R005051, R005060, R005061, R005063, R005066, R005068, R005069, R005072, R005073, R005074. Do not finish or rewrite them from a cloud copy; return accurate final verification and cloud history for local reconciliation. Revision R005075 records this handoff only, not completion of their geometry/motion work.

If Sites tools or credentials are unavailable in cloud, finish all independent implementation, tests, clean source commits and deployment artifact preparation. Report the exact remaining deployment capability; do not claim publication. Never copy local credentials or unrelated workspace files into the repository. Use the official Sites skill/tools when available; preserve existing site identity and design.
<!-- TIMESTAMP END 2026-11-04T07:06:41-05:00 | REVISION R005075 -->
