<!-- TIMESTAMP START 2026-11-04T07:13:51-05:00 | REVISION R005077 -->
# Start the timberframe continuation in Codex Cloud

This branch transports the unfinished local implementation as a verified Git bundle. Its ordinary source files still match published main. **Restore the bundle before doing any implementation work.** The bundle contains all 265 saved source files, including uncommitted work, tests, the personal change-history skill and `CLOUD-HANDOFF.md`.

Repository: `stewart-del/octagonal-timberframe-building`.
Transport branch: `codex/cloud-handoff-20261104`.
Required parent: `b1eec82544e64fa255f82ae8c0244e40b4e1e96a`.
Source checkpoint commit: `3ac78a8b4a72ed45b7afb3e8ab9988b1215001b2`.
Bundle: 5,007,975 bytes in 26 numbered chunks.
Bundle SHA-256: `ae836381cdfe1dad081e05bd017dd3754ba8b84dc344ea382477d527a56ab9a6`.

From a clean checkout of the transport branch, run:

```sh
cat .codex-handoff/checkpoint.bundle.part* > /tmp/octagon-cloud-checkpoint.bundle
printf '%s  %s\n' ae836381cdfe1dad081e05bd017dd3754ba8b84dc344ea382477d527a56ab9a6 /tmp/octagon-cloud-checkpoint.bundle | sha256sum --check
git bundle verify /tmp/octagon-cloud-checkpoint.bundle
git fetch /tmp/octagon-cloud-checkpoint.bundle HEAD
git switch -c codex/timberframe-cloud-continuation FETCH_HEAD
git rev-parse HEAD
```

The last command must return the source checkpoint commit above. Then read `AGENTS.md` and `CLOUD-HANDOFF.md` in that restored source. Keep the finished design; complete the unfinished route verification and regression fixes before building or deploying. The owner already authorized publication to the existing Sites project and updating GitHub. Do not deploy the stale saved `index.html`.

This checkpoint is intentionally marked `[skip ci]`: it is unfinished work being moved between machines, not a passing release. Run the full required checks after resolving the issues documented in the handoff. Keep cloud history artifacts for later reconciliation with the authoritative Mac ledger.
<!-- TIMESTAMP END 2026-11-04T07:13:51-05:00 | REVISION R005077 -->
