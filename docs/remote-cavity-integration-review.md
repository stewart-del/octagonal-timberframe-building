# Remote515312b cavity integration review
Exact remote commit:515312bffb66d69c95edf4dd9487747bd67611a3.
Read via connected GitHub fetch_file, no remote writes.

## Scope distinction
Remote audit validates recorded prejoinery envelope with explicit16K exterior trims, filled by final receiver plus mating-occupied recesses. It excludes added-tenon stock outside recorded envelope. Our2fc1a32 validates removed design stock including explicit replacement blanks and unoccupied waste. These are not interchangeable meanings or proofs.

## Frozen release adaptation
- Preserve remote scripts/audit_cavity_fit.py, export_step_lap_cavities.py, regular_boundary producer logic and independently hash-bound reports.
- Rebind/regenerate after seated M-TMP baseline metadata change; do not rewrite report SHA only. Audit provenance exact.
- Retain current three-model build/selection/exports. Remote build only knows baseline/perimeter.
- Add baseline/perimeter audit PASS+modelSHA+cavitySHA build gates and fit_audit attachments; top-entry keeps its own SHA-bound available:false. Never fallback to baseline masks.
- Perimeter auxiliary must invoke remote exporter after actual model/proposal generation and baseline audit. Do not retain all-stock regeneration hook.
- Preserve current source-bound contact warning repair; remote auxiliary clears issues and remote build asserts empty issues, which would erase later reviewed work.
- Remote overlay is removed-only. Remove/disable old hollowMode selector and handler together; availability disables controls on top-entry. Red feature borders and Labels independence can be adapted without changing recess semantics.
- Preserve floor, roof, support, cut-angle, plans, complete/skeleton runtime paths from current release; do not replace whole remote viewer/build.
- Audit adds scipy dependency. Current /tmp/octagon-ci-env lacks scipy; parent owns dependency environment.

## Additional finding
AST-extracted exact remote inspect_mesh/raw overlap functions run on12 representative current all-stock masks. Baseline P0/C0/R0/J0-0 PASS; perimeter/top-entry P0/C0/R0 PASS; perimeter/top-entry J0-0 FAIL positive-area coplanar raw triangle overlap. Thus previous volume/winding validation was insufficient for raw surface quality. Parent notified NOT to publish2fc1a32 masks until regularized and independently raw-surface checked. No timber geometry defect inferred from this mask-only check.
Full remote audit NOT run here. Exact check script check_raw.py; source files retained under scripts/.
