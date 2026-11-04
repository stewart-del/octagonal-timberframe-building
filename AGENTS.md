<!-- TIMESTAMP START 2026-11-04T07:06:41-05:00 | REVISION R005075 -->
# Timberframe continuation

Read `CLOUD-HANDOFF.md` before changing this project. Preserve the accepted design and the user's explicit deployment authorization.

For every code, CSS, script, test, configuration or authored-content change, use the bundled personal skill `.codex/skills/track-code-changes/SKILL.md`. Run its `scripts/change_history.py begin` before editing, naming every affected file. Surround every contiguous changed block with language-appropriate `TIMESTAMP START` and `TIMESTAMP END` comments containing the exact revision and ISO 8601 timestamp returned by begin. Do not break commentless formats. Run `finish` after verification with the reason and accurate results. Reversions are new revisions cross-referencing the original.

The authoritative history is on the owner's Mac at `/Users/stewartlundy/Documents/Codex/.codex-change-history`. A cloud worker must keep its own transportable history with `CODEX_CHANGE_HISTORY_DIR` pointing to a durable task directory, retain all metadata, snapshots, patches and ledgers, and return that directory as an artifact for reconciliation into the authoritative Mac history. Never claim the Mac ledger was updated from cloud. Do not overwrite local revision IDs or finish the prior Mac revisions from another machine. Keep this limitation explicit in the final handoff.

Use a new `codex/` branch based on the checkpoint. Keep checkpoint/ledger artifacts out of the deployed website. Do not publish a stale built page or relabel stale geometry certificates. Rerun the physical geometry checks; never lower collision thresholds to make a route pass.
<!-- TIMESTAMP END 2026-11-04T07:06:41-05:00 | REVISION R005075 -->
