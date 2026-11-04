---
name: track-code-changes
description: Record every Codex-authored code, CSS, public-facing English, and authored-content change in centralized linked ledgers with revision IDs, timestamps, exact translation deltas, snapshots, hashes, patches, optional private GitHub backup, monthly localization reports, and safe restoration. Use for changes to source code, scripts, tests, configuration-as-code, CSS, UI copy, inline public strings, website copy, posts, blogs, articles, documentation intended for publication, or other translatable English; for backup configuration or synchronization; and when finding, inspecting, comparing, reporting, or reverting earlier changes.
---

# Track Code Changes

Use `scripts/change_history.py` for the complete workflow. The default history root is `/Users/stewartlundy/Documents/Codex/.codex-change-history`; override it only with the task-specific `CODEX_CHANGE_HISTORY_DIR` environment variable.

## Record a change

1. Before editing, identify the project root and every source, CSS, or authored-content file in the logical change. Include posts, articles, public documentation, content files, templates, and source files containing changed public English.
2. Run:

   ```bash
   python3 /Users/stewartlundy/.codex/skills/track-code-changes/scripts/change_history.py begin \
     --project /absolute/project/root \
     --summary "Concise purpose of the change" \
     --kind fix \
     --localization auto \
     --file path/from/project/root \
     --file another/file.css
   ```

3. Use the returned revision and timestamp in language-appropriate comments around every contiguous changed code or CSS block:

   ```text
   TIMESTAMP START <timestamp> | REVISION <revision>
   ...changed block...
   TIMESTAMP END <timestamp> | REVISION <revision>
   ```

   For deletions, leave a timestamped deletion marker at the former location when the language supports comments. Never break a commentless format merely to add a marker; the ledger remains mandatory.
4. Make the requested edits and run proportionate verification. Do not hide public English changes inside an untracked source file.
5. Finish the same revision:

   ```bash
   python3 /Users/stewartlundy/.codex/skills/track-code-changes/scripts/change_history.py finish R000001 \
     --reason "Why this implementation was chosen" \
     --verification "pytest -q: passed"
   ```

Do not finish a revision until the logical change and its verification are complete. The finish command saves after-snapshots, hashes, a unified patch for text files, `ledger.jsonl`, and the human-readable `CHANGELOG.md`. The local record is authoritative even if an optional GitHub sync fails.

## Public English and translation ledger

Keep `--localization auto` for ordinary work. It records exact added, removed, and altered English in `localization/ledger.jsonl` and `localization/CHANGELOG.md`, plus a revision-linked `localization.json`. It scans prose and publication files directly and detects string literals, markup text, accessible labels, placeholders, titles, and likely public strings inside source code. Exclude URLs: remove absolute, protocol-relative, bare-domain, mail, telephone, and relative-path URLs before comparison; do not record URL-only changes or URLs in localization excerpts and reports. Exclude standalone `true` and `false` boolean literals case-insensitively, while preserving complete translatable sentences that contain those words. Candidate source strings remain marked for human confirmation so internal messages are not sent blindly for translation.

Use `--localization include` when a revision is known to contain public or translatable English. Use `--localization exclude` only when every tracked file is known to be internal and contains no public English. Never exclude UI copy, public templates, posts, blogs, articles, release notes, help content, or documentation intended for publication. Override a mistaken selection at `finish` with the same flag.

Generate the monthly translation queue in Markdown or machine-readable JSON:

```bash
python3 /Users/stewartlundy/.codex/skills/track-code-changes/scripts/change_history.py localization-report \
  --month 2026-08 \
  --format markdown
```

Each item includes its originating revision, file, line and column, old and new text, and the exact word- or punctuation-level fragments to remove and add. Treat the JSONL ledger as append-only; translation workflow state belongs in the translation system, keyed by `change_id`.

## GitHub backup mirror

Use a dedicated private GitHub repository with access no broader than the source projects. Configure it once per computer:

```bash
python3 /Users/stewartlundy/.codex/skills/track-code-changes/scripts/change_history.py backup-configure \
  --remote git@github.com:OWNER/PRIVATE-REPOSITORY.git \
  --confirm-private
python3 /Users/stewartlundy/.codex/skills/track-code-changes/scripts/change_history.py backup-sync
```

Automatic sync is enabled by default. A network, authentication, or push failure leaves the completed local revision untouched and marks the backup pending for `backup-sync` to retry. Each computer receives a collision-resistant machine ID and writes under its own immutable namespace.

The mirror includes both Markdown and JSONL ledgers, localization artifacts, metadata, hashes, and text patches by default. It excludes before/after source snapshots to reduce confidential-code duplication; opt in only when authorized with `backup-configure --include-snapshots`.

Inspect or search the shared mirror with:

```bash
python3 /Users/stewartlundy/.codex/skills/track-code-changes/scripts/change_history.py backup-status
python3 /Users/stewartlundy/.codex/skills/track-code-changes/scripts/change_history.py backup-find "search terms"
```

Never place credentials in the remote URL. Use the machine's existing Git credential manager or SSH authentication.

## Reversions

Treat a reversion as a new logged change so it is itself reversible:

1. Inspect the old revision with `show`.
2. Start a new revision for the same files with `--kind reversion --reverts R000001`.
3. Dry-run the restoration with `revert R000001`.
4. Apply it only after checking the exact targets: `revert R000001 --apply`.
5. Verify behavior, then finish the new revision.

The restore command refuses to overwrite files that no longer match the recorded after-state. Use `--force` only with explicit user authorization.

## Find earlier changes

```bash
python3 /Users/stewartlundy/.codex/skills/track-code-changes/scripts/change_history.py find "search terms"
python3 /Users/stewartlundy/.codex/skills/track-code-changes/scripts/change_history.py show R000001
```

Report the revision, timestamp, project, files, summary, reason, verification, and any mismatch risk before performing a requested reversion.

<!-- TIMESTAMP START 2026-11-04T07:06:41-05:00 | REVISION R005075 -->
Cloud migration copy: use the repo AGENTS.md for a durable transportable cloud ledger and reconciliation with the authoritative Mac history. This copy contains no credentials or backup configuration.
<!-- TIMESTAMP END 2026-11-04T07:06:41-05:00 | REVISION R005075 -->
