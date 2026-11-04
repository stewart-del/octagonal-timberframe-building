#!/usr/bin/env python3
# TIMESTAMP START 2026-11-04T07:06:41-05:00 | REVISION R005075
# TIMESTAMP START 2026-08-18T12:27:07-04:00 | REVISION BOOTSTRAP
# TIMESTAMP START 2026-08-19T18:13:49-04:00 | REVISION R000085
"""Create linked, reversible records of Codex-authored source and public-English changes."""
# TIMESTAMP END 2026-08-19T18:13:49-04:00 | REVISION R000085

from __future__ import annotations

import argparse
import difflib
import fcntl
import hashlib
import json
import os
# TIMESTAMP START 2026-08-18T13:51:51-04:00 | REVISION R000008
import platform
import re
# TIMESTAMP END 2026-08-18T13:51:51-04:00 | REVISION R000008
import shutil
# TIMESTAMP START 2026-08-18T13:51:51-04:00 | REVISION R000008
import subprocess
# TIMESTAMP END 2026-08-18T13:51:51-04:00 | REVISION R000008
import sys
# TIMESTAMP START 2026-08-18T13:51:51-04:00 | REVISION R000008
import uuid
# TIMESTAMP END 2026-08-18T13:51:51-04:00 | REVISION R000008
from datetime import datetime
from pathlib import Path
from typing import Any


DEFAULT_HISTORY_ROOT = Path.home() / "Documents" / "Codex" / ".codex-change-history"
# TIMESTAMP START 2026-08-18T13:51:51-04:00 | REVISION R000008
BACKUP_CONFIG_NAME = "github-backup.json"
BACKUP_STATUS_NAME = "github-backup-status.json"
# TIMESTAMP END 2026-08-18T13:51:51-04:00 | REVISION R000008
# TIMESTAMP START 2026-08-19T18:13:49-04:00 | REVISION R000085
LOCALIZATION_DIR_NAME = "localization"
LOCALIZATION_LEDGER_NAME = "ledger.jsonl"
LOCALIZATION_CHANGELOG_NAME = "CHANGELOG.md"
PROSE_SUFFIXES = {".adoc", ".markdown", ".md", ".mdx", ".org", ".rst", ".text", ".txt"}
PUBLIC_CONTENT_KEYS = {
    "description",
    "excerpt",
    "seo-description",
    "seo-title",
    "subtitle",
    "summary",
    "title",
}
PUBLIC_ATTRIBUTE_NAMES = {
    "alt",
    "aria-description",
    "aria-label",
    "caption",
    "label",
    "placeholder",
    "summary",
    "title",
# TIMESTAMP START 2026-08-19T18:13:49-04:00 | REVISION R000085
    "value",
# TIMESTAMP END 2026-08-19T18:13:49-04:00 | REVISION R000085
}
TIMESTAMP_MARKER_RE = re.compile(r"TIMESTAMP (?:START|END) .* \| REVISION ")
STRING_LITERAL_RE = re.compile(
    r"(?P<triple>'''|\"\"\")(?P<triple_value>.*?)(?P=triple)|"
    r"(?P<quote>['\"`])(?P<value>(?:\\.|(?!(?P=quote)).)*)(?P=quote)",
    re.DOTALL,
)
HTML_TEXT_RE = re.compile(r">([^<>{}]+)<", re.DOTALL)
TEXT_TOKEN_RE = re.compile(r"\s+|[\w]+(?:['’\-][\w]+)*|[^\w\s]", re.UNICODE)
# TIMESTAMP START 2026-08-19T18:24:38-04:00 | REVISION R000088
URL_RE = re.compile(
    r"(?:\b(?:https?|ftp)://[^\s<>{}\[\]()\"']+|"
    r"\b(?:mailto|tel):[^\s<>{}\[\]()\"']+|"
    r"(?<!:)//(?:[A-Za-z0-9-]+\.)+[A-Za-z]{2,}[^\s<>{}\[\]()\"']*|"
    r"\bwww\.(?:[A-Za-z0-9-]+\.)+[A-Za-z]{2,}[^\s<>{}\[\]()\"']*|"
    r"\b(?:[A-Za-z0-9-]+\.)+[A-Za-z]{2,}(?:/[^\s<>{}\[\]()\"']*)?|"
    r"(?<![\w/])/(?!/)[^\s<>{}\[\]()\"']+)",
    re.IGNORECASE,
)
# TIMESTAMP START 2026-08-19T18:28:59-04:00 | REVISION R000089
BOOLEAN_LITERAL_RE = re.compile(r"(?:true|false)", re.IGNORECASE)
# TIMESTAMP END 2026-08-19T18:28:59-04:00 | REVISION R000089
# TIMESTAMP END 2026-08-19T18:24:38-04:00 | REVISION R000088
# TIMESTAMP END 2026-08-19T18:13:49-04:00 | REVISION R000085


def timestamp_now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def history_root() -> Path:
    configured = os.environ.get("CODEX_CHANGE_HISTORY_DIR")
    return Path(configured).expanduser().resolve() if configured else DEFAULT_HISTORY_ROOT


def sha256(path: Path) -> str | None:
    if not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def ensure_history() -> Path:
    root = history_root()
    (root / "revisions").mkdir(parents=True, exist_ok=True)
    changelog = root / "CHANGELOG.md"
    if not changelog.exists():
        changelog.write_text(
            "# Codex Code Change History\n\n"
            "Append-only index of Codex-authored changes. Revision artifacts are stored in `revisions/`.\n\n",
            encoding="utf-8",
        )
    return root


def allocate_revision(root: Path) -> str:
    counter_path = root / "counter.txt"
    with counter_path.open("a+", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        handle.seek(0)
        raw = handle.read().strip()
        number = int(raw) + 1 if raw else 1
        handle.seek(0)
        handle.truncate()
        handle.write(f"{number}\n")
        handle.flush()
        os.fsync(handle.fileno())
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
    return f"R{number:06d}"


def normalize_files(project: Path, supplied: list[str]) -> list[str]:
    if not project.is_dir():
        raise ValueError(f"Project root does not exist or is not a directory: {project}")
    normalized: list[str] = []
    seen: set[str] = set()
    for raw in supplied:
        candidate = Path(raw).expanduser()
        absolute = (candidate if candidate.is_absolute() else project / candidate).resolve(strict=False)
        try:
            relative = absolute.relative_to(project)
        except ValueError as exc:
            raise ValueError(f"Tracked file must be inside the project root: {raw}") from exc
        if absolute.exists() and not (absolute.is_file() or absolute.is_symlink()):
            raise ValueError(f"Tracked path must be a file: {raw}")
        value = relative.as_posix()
        if value not in seen:
            normalized.append(value)
            seen.add(value)
    if not normalized:
        raise ValueError("At least one --file is required")
    return normalized


def snapshot_file(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if source.is_symlink():
        destination.write_text(os.readlink(source), encoding="utf-8")
    elif source.is_file():
        shutil.copy2(source, destination)


def file_state(path: Path) -> dict[str, Any]:
    if path.is_symlink():
        return {
            "exists": True,
            "kind": "symlink",
            "sha256": hashlib.sha256(os.readlink(path).encode("utf-8")).hexdigest(),
        }
    if path.is_file():
        return {"exists": True, "kind": "file", "sha256": sha256(path)}
    return {"exists": False, "kind": "missing", "sha256": None}


def metadata_path(revision: str) -> Path:
    return ensure_history() / "revisions" / revision / "metadata.json"


def load_metadata(revision: str) -> tuple[Path, dict[str, Any]]:
    path = metadata_path(revision)
    if not path.is_file():
        raise ValueError(f"Unknown revision: {revision}")
    return path, json.loads(path.read_text(encoding="utf-8"))


def save_metadata(path: Path, metadata: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def command_begin(args: argparse.Namespace) -> int:
    root = ensure_history()
    project = Path(args.project).expanduser().resolve()
    files = normalize_files(project, args.file)
    revision = allocate_revision(root)
    started_at = timestamp_now()
    revision_dir = root / "revisions" / revision
    before_dir = revision_dir / "before"
    records: list[dict[str, Any]] = []
    for relative in files:
        source = project / relative
        state = file_state(source)
        snapshot_file(source, before_dir / relative)
        records.append({"path": relative, "before": state})
    metadata: dict[str, Any] = {
        "revision": revision,
        "status": "pending",
        "started_at": started_at,
        "finished_at": None,
        "project": str(project),
        "summary": args.summary.strip(),
        "kind": args.kind,
        "reverts": args.reverts,
        "reason": None,
        "verification": None,
        "files": records,
# TIMESTAMP START 2026-08-19T18:13:49-04:00 | REVISION R000085
        "localization_scope": args.localization,
# TIMESTAMP END 2026-08-19T18:13:49-04:00 | REVISION R000085
    }
    save_metadata(revision_dir / "metadata.json", metadata)
    print(f"REVISION={revision}")
    print(f"TIMESTAMP={started_at}")
    print(f"PROJECT={project}")
    print("Use this exact revision and timestamp in every changed-block comment.")
    return 0


def read_text(path: Path) -> list[str] | None:
    if not path.is_file():
        return []
    try:
        return path.read_text(encoding="utf-8").splitlines(keepends=True)
    except UnicodeDecodeError:
        return None


def build_patch(metadata: dict[str, Any], revision_dir: Path) -> tuple[str, list[str]]:
    chunks: list[str] = []
    binary_files: list[str] = []
    for record in metadata["files"]:
        relative = record["path"]
        before = read_text(revision_dir / "before" / relative)
        after = read_text(revision_dir / "after" / relative)
        if before is None or after is None:
            binary_files.append(relative)
            continue
        chunks.extend(
            difflib.unified_diff(
                before,
                after,
                fromfile=f"a/{relative}",
                tofile=f"b/{relative}",
            )
        )
    return "".join(chunks), binary_files


# TIMESTAMP START 2026-08-19T18:13:49-04:00 | REVISION R000085
# TIMESTAMP START 2026-08-19T18:24:38-04:00 | REVISION R000088
def remove_urls(text: str) -> str:
    def preserve_sentence_punctuation(match: re.Match[str]) -> str:
        value = match.group(0)
        punctuation = ""
        while value and value[-1] in ".,!?;:":
            punctuation = value[-1] + punctuation
            value = value[:-1]
        return punctuation

    without_urls = URL_RE.sub(preserve_sentence_punctuation, text)
    without_urls = re.sub(r"[ \t]{2,}", " ", without_urls)
    without_urls = re.sub(r"[ \t]+([.,!?;:])", r"\1", without_urls)
    return without_urls.strip()


# TIMESTAMP END 2026-08-19T18:24:38-04:00 | REVISION R000088
def looks_like_english(text: str) -> bool:
# TIMESTAMP START 2026-08-19T18:24:38-04:00 | REVISION R000088
# TIMESTAMP START 2026-08-19T18:28:59-04:00 | REVISION R000089
    without_urls = remove_urls(text)
    if BOOLEAN_LITERAL_RE.fullmatch(without_urls):
        return False
    candidate = re.sub(
        r"\$\{.*?}|\{\{.*?\}\}", " ", without_urls, flags=re.DOTALL
    ).strip()
# TIMESTAMP END 2026-08-19T18:28:59-04:00 | REVISION R000089
# TIMESTAMP END 2026-08-19T18:24:38-04:00 | REVISION R000088
    words = re.findall(r"[A-Za-z]+(?:['’\-][A-Za-z]+)*", candidate)
    if not any(len(word) >= 2 for word in words):
        return False
    if re.fullmatch(r"[a-z0-9_./:@-]+", candidate) and any(mark in candidate for mark in "_./:@"):
        return False
    return True


def clean_prose_text(line: str) -> str | None:
    value = line.strip()
    if (
        not value
        or value in {"---", "+++"}
        or value.startswith(("```", "~~~", "<!--"))
        or TIMESTAMP_MARKER_RE.search(value)
    ):
        return None
    value = re.sub(r"^\s{0,3}(?:#{1,6}\s+|[-*+]\s+|\d+[.)]\s+|>\s*)", "", value)
    metadata_value = re.match(r"([A-Za-z_][-A-Za-z0-9_]*)\s*:\s*(.+)$", value)
    if metadata_value and metadata_value.group(1).casefold().replace("_", "-") in PUBLIC_CONTENT_KEYS:
        value = metadata_value.group(2).strip().strip("'\"")
    value = re.sub(r"!\[([^]]*)\]\([^)]*\)", r"\1", value)
    value = re.sub(r"\[([^]]+)\]\([^)]*\)", r"\1", value)
    value = re.sub(r"<[^>]+>", "", value).strip()
    return value if looks_like_english(value) else None


def line_and_column(text: str, offset: int, base_line: int) -> tuple[int, int]:
    preceding = text[:offset]
    line = base_line + preceding.count("\n")
    last_newline = preceding.rfind("\n")
    column = offset + 1 if last_newline == -1 else offset - last_newline
    return line, column


def source_line_at(text: str, offset: int) -> str:
    start = text.rfind("\n", 0, offset) + 1
    end = text.find("\n", offset)
    return text[start : len(text) if end == -1 else end]


def candidate(
    text: str,
    line: int,
    column: int,
    kind: str,
    source_excerpt: str,
) -> dict[str, Any]:
# TIMESTAMP START 2026-08-19T18:24:38-04:00 | REVISION R000088
    return {
        "text": remove_urls(text),
        "line": line,
        "column": column,
        "kind": kind,
        "source_excerpt": remove_urls(source_excerpt),
    }
# TIMESTAMP END 2026-08-19T18:24:38-04:00 | REVISION R000088


def string_is_nonpublic_source(text: str, match: re.Match[str], path: Path) -> bool:
    line = source_line_at(text, match.start())
    if TIMESTAMP_MARKER_RE.search(line):
        return True
    prefix = line[: match.start() - (text.rfind("\n", 0, match.start()) + 1)]
    if re.match(r"\s*(?:from\s+|import\s+|@import\s+)", line):
        return True
    if re.search(r"(?:require|url)\s*\(\s*$", prefix):
        return True
    following = text[match.end() : match.end() + 24]
    if path.suffix.casefold() in {".json", ".jsonc", ".toml", ".yaml", ".yml"} and re.match(r"\s*:", following):
        return True
    return False


# TIMESTAMP START 2026-10-15T11:03:39-04:00 | REVISION R004366
def is_encoded_asset_chunk(path: Path, line: str) -> bool:
    """Recognize generated base64 modules without ignoring adjacent UI strings."""
    if not re.fullmatch(r"asset-chunk-\d+\.js", path.name):
        return False
    stripped = line.strip()
    if not stripped.startswith("export default "):
        return False
    try:
        entries = json.loads(stripped[len("export default "):].removesuffix(";"))
    except (ValueError, TypeError):
        return False
    return isinstance(entries, list) and bool(entries) and all(
        isinstance(entry, dict) and set(entry) == {"asset", "type", "body"}
        and isinstance(entry["asset"], str) and isinstance(entry["type"], str)
        and isinstance(entry["body"], str)
        and re.fullmatch(r"[A-Za-z0-9+/]*={0,2}", entry["body"]) is not None
        for entry in entries
    )
# TIMESTAMP END 2026-10-15T11:03:39-04:00 | REVISION R004366


def extract_source_candidates(path: Path, lines: list[str], base_line: int) -> list[dict[str, Any]]:
    # TIMESTAMP START 2026-10-15T11:03:39-04:00 | REVISION R004366
    lines = ["\n" if is_encoded_asset_chunk(path, line) else line for line in lines]
    # TIMESTAMP END 2026-10-15T11:03:39-04:00 | REVISION R004366
    # TIMESTAMP START 2026-10-12T09:40:52-04:00 | REVISION R004257
    # Generated asset bundles contain encoded files, not authored English.
    # Retain line positions while avoiding quadratic URL scans of binary data.
    lines = [
        "\n" if len(line) > 1_000_000
        and re.match(r"^\s*const\s+BUNDLE\s*=", line)
        # TIMESTAMP START 2026-10-12T09:43:49-04:00 | REVISION R004258
        and ('"base64":' in line or ('"body":' in line and '"type":' in line)) else line
        # TIMESTAMP END 2026-10-12T09:43:49-04:00 | REVISION R004258
        for line in lines
    ]
    # TIMESTAMP END 2026-10-12T09:40:52-04:00 | REVISION R004257
    text = "".join(lines)
    results: list[dict[str, Any]] = []
    covered_lines: set[int] = set()
    for match in STRING_LITERAL_RE.finditer(text):
        value = match.group("triple_value") if match.group("triple") else match.group("value")
        if not value or not looks_like_english(value) or string_is_nonpublic_source(text, match, path):
            continue
        value_offset = match.start("triple_value") if match.group("triple") else match.start("value")
        line, column = line_and_column(text, value_offset, base_line)
        source_excerpt = source_line_at(text, match.start())
        prefix = source_excerpt[: match.start() - (text.rfind("\n", 0, match.start()) + 1)]
        attribute = re.search(r"([A-Za-z_:][-A-Za-z0-9_:.]*)\s*=\s*$", prefix)
# TIMESTAMP START 2026-08-19T18:24:38-04:00 | REVISION R000088
        if attribute and prefix.rfind("<") > prefix.rfind(">"):
# TIMESTAMP END 2026-08-19T18:24:38-04:00 | REVISION R000088
            attribute_name = attribute.group(1).casefold()
            if attribute_name not in PUBLIC_ATTRIBUTE_NAMES and not attribute_name.startswith("aria-"):
                continue
            kind = "public-attribute"
        else:
            kind = "source-string-candidate"
        end_line, _ = line_and_column(text, match.end(), base_line)
        covered_lines.update(range(line, end_line + 1))
        results.append(candidate(value, line, column, kind, source_excerpt))
    for match in HTML_TEXT_RE.finditer(text):
        value = re.sub(r"\s+", " ", match.group(1)).strip()
        if not looks_like_english(value):
            continue
        value_offset = match.start(1)
        line, column = line_and_column(text, value_offset, base_line)
        covered_lines.add(line)
        results.append(candidate(value, line, column, "public-markup-text", source_line_at(text, value_offset)))
    for offset, raw_line in enumerate(lines):
        line_number = base_line + offset
        stripped = raw_line.strip()
        if line_number in covered_lines or not stripped or TIMESTAMP_MARKER_RE.search(stripped):
            continue
        if stripped.startswith(("#", "//", "/*", "*", "--")):
            continue
# TIMESTAMP START 2026-08-19T18:28:59-04:00 | REVISION R000089
        if path.suffix.casefold() in {".toml", ".yaml", ".yml"}:
            structured_value = re.match(r"[A-Za-z_][-A-Za-z0-9_.]*\s*[:=]\s*(.+?)\s*$", stripped)
            if structured_value:
                value = structured_value.group(1).strip().strip("'\"")
                if looks_like_english(value):
                    results.append(
                        candidate(
                            value,
                            line_number,
                            max(raw_line.find(structured_value.group(1)), 0) + 1,
                            "structured-value-candidate",
                            raw_line.rstrip("\r\n"),
                        )
                    )
                continue
# TIMESTAMP END 2026-08-19T18:28:59-04:00 | REVISION R000089
        if re.fullmatch(r"[A-Za-z][A-Za-z0-9 ,.!?;:'’()\-–—…]{3,}", stripped) and (
            " " in stripped or stripped.endswith((".", "!", "?"))
        ):
            results.append(candidate(stripped, line_number, len(raw_line) - len(raw_line.lstrip()) + 1, "source-line-candidate", raw_line.rstrip("\r\n")))
    return deduplicate_candidates(results)


def extract_prose_candidates(path: Path, lines: list[str], base_line: int) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for offset, raw_line in enumerate(lines):
        stripped = raw_line.strip()
        if path.suffix.casefold() == ".mdx" and stripped.startswith(("<", "{", "export ", "import ")):
            results.extend(extract_source_candidates(path, [raw_line], base_line + offset))
            continue
        value = clean_prose_text(raw_line)
        if value is None:
            continue
        results.append(
            candidate(
                value,
                base_line + offset,
                max(raw_line.find(value), 0) + 1,
                "prose",
                raw_line.rstrip("\r\n"),
            )
        )
    return deduplicate_candidates(results)


def deduplicate_candidates(values: list[dict[str, Any]]) -> list[dict[str, Any]]:
    unique: list[dict[str, Any]] = []
    seen: set[tuple[Any, ...]] = set()
    for value in values:
        key = (value["text"], value["line"], value["column"], value["kind"])
        if key not in seen:
            seen.add(key)
            unique.append(value)
    return unique


def extract_localization_candidates(path: Path, lines: list[str], base_line: int) -> list[dict[str, Any]]:
    if path.suffix.casefold() in PROSE_SUFFIXES:
        return extract_prose_candidates(path, lines, base_line)
    return extract_source_candidates(path, lines, base_line)


def pair_candidates(
    removed: list[dict[str, Any]],
    added: list[dict[str, Any]],
) -> list[tuple[dict[str, Any] | None, dict[str, Any] | None]]:
    if len(removed) == 1 and len(added) == 1:
        return [(removed[0], added[0])]
    pairs: list[tuple[dict[str, Any] | None, dict[str, Any] | None]] = []
    unused_added = set(range(len(added)))
    for old in removed:
        best_index: int | None = None
        best_score = 0.0
        for index in unused_added:
            new = added[index]
            score = difflib.SequenceMatcher(None, old["text"], new["text"]).ratio()
            if old["kind"] == new["kind"]:
                score += 0.15
            if score > best_score:
                best_score = score
                best_index = index
        if best_index is not None and best_score >= 0.35:
            pairs.append((old, added[best_index]))
            unused_added.remove(best_index)
        else:
            pairs.append((old, None))
    pairs.extend((None, added[index]) for index in sorted(unused_added))
    return pairs


def exact_text_delta(old_text: str, new_text: str) -> tuple[list[str], list[str]]:
    old_tokens = TEXT_TOKEN_RE.findall(old_text)
    new_tokens = TEXT_TOKEN_RE.findall(new_text)
    removed: list[str] = []
    added: list[str] = []
    for operation, old_start, old_end, new_start, new_end in difflib.SequenceMatcher(
        None, old_tokens, new_tokens
    ).get_opcodes():
        if operation in {"delete", "replace"}:
            fragment = "".join(old_tokens[old_start:old_end])
            if fragment.strip():
                removed.append(fragment)
        if operation in {"insert", "replace"}:
            fragment = "".join(new_tokens[new_start:new_end])
            if fragment.strip():
                added.append(fragment)
    return removed, added


def localization_change(
    change_id: str,
    relative: str,
    old: dict[str, Any] | None,
    new: dict[str, Any] | None,
) -> dict[str, Any] | None:
    old_text = old["text"] if old else ""
    new_text = new["text"] if new else ""
    if old_text == new_text:
        return None
    removed_fragments, added_fragments = exact_text_delta(old_text, new_text)
    return {
        "change_id": change_id,
        "file": relative,
        "change_type": "altered" if old and new else "removed" if old else "added",
        "source_kind": (new or old)["kind"],
        "before": old,
        "after": new,
        "old_text": old_text or None,
        "new_text": new_text or None,
        "removed_fragments": removed_fragments,
        "added_fragments": added_fragments,
        "translation_status": "pending",
        "review_note": "Confirm source-string candidates are public-facing before translation."
        if (new or old)["kind"].endswith("candidate")
        else None,
    }


def build_localization_record(
    metadata: dict[str, Any], revision_dir: Path, scope: str
) -> dict[str, Any] | None:
    if scope == "exclude":
        return None
    changes: list[dict[str, Any]] = []
    for record in metadata["files"]:
        relative = record["path"]
        before = read_text(revision_dir / "before" / relative)
        after = read_text(revision_dir / "after" / relative)
        if before is None or after is None:
            continue
        path = Path(relative)
        matcher = difflib.SequenceMatcher(None, before, after)
        for operation, old_start, old_end, new_start, new_end in matcher.get_opcodes():
            if operation == "equal":
                continue
            removed = extract_localization_candidates(path, before[old_start:old_end], old_start + 1)
            added = extract_localization_candidates(path, after[new_start:new_end], new_start + 1)
            for old, new in pair_candidates(removed, added):
                item = localization_change(
                    f"{metadata['revision']}-L{len(changes) + 1:04d}", relative, old, new
                )
                if item is not None:
                    changes.append(item)
    if not changes:
        return None
    return {
        "schema_version": 1,
        "revision": metadata["revision"],
        "finished_at": metadata["finished_at"],
        "project": metadata["project"],
        "summary": metadata["summary"],
        "localization_scope": scope,
        "change_count": len(changes),
        "changes": changes,
    }


def ensure_localization_history(root: Path) -> Path:
    directory = root / LOCALIZATION_DIR_NAME
    directory.mkdir(parents=True, exist_ok=True)
    ledger = directory / LOCALIZATION_LEDGER_NAME
    if not ledger.exists():
        ledger.write_text("", encoding="utf-8")
    changelog = directory / LOCALIZATION_CHANGELOG_NAME
    if not changelog.exists():
        changelog.write_text(
            "# Public English Translation Change History\n\n"
            "Append-only queue of exact public-facing English changes linked to code-ledger revisions.\n\n",
            encoding="utf-8",
        )
    return directory


def exact_markdown_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False) if value not in (None, "") else "—"


def append_localization_ledger(root: Path, record: dict[str, Any]) -> None:
    directory = ensure_localization_history(root)
    with (directory / LOCALIZATION_LEDGER_NAME).open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    lines = [
        f"## {record['revision']} — {record['summary']}",
        "",
        f"- Finished: `{record['finished_at']}`",
        f"- Project: `{record['project']}`",
        f"- Exact changes: {record['change_count']}",
        "",
    ]
    for change in record["changes"]:
        location = change["after"] or change["before"]
        lines.extend(
            [
                f"### {change['change_id']} — {change['change_type']}",
                "",
                f"- Source: `{change['file']}:{location['line']}:{location['column']}` ({change['source_kind']})",
                f"- Old text: {exact_markdown_text(change['old_text'])}",
                f"- New text: {exact_markdown_text(change['new_text'])}",
                f"- Removed fragments: {exact_markdown_text(change['removed_fragments'])}",
                f"- Added fragments: {exact_markdown_text(change['added_fragments'])}",
                f"- Translation status: `{change['translation_status']}`",
                "",
            ]
        )
    with (directory / LOCALIZATION_CHANGELOG_NAME).open("a", encoding="utf-8") as handle:
# TIMESTAMP START 2026-08-19T18:13:49-04:00 | REVISION R000085
        handle.write("\n".join(lines) + "\n")
# TIMESTAMP END 2026-08-19T18:13:49-04:00 | REVISION R000085


def read_localization_ledger() -> list[dict[str, Any]]:
    ledger = ensure_localization_history(ensure_history()) / LOCALIZATION_LEDGER_NAME
    if not ledger.is_file():
        return []
    return [json.loads(line) for line in ledger.read_text(encoding="utf-8").splitlines() if line.strip()]


def render_localization_report(records: list[dict[str, Any]], month: str) -> str:
    changes = [change for record in records for change in record["changes"]]
    lines = [
        f"# Translation Update Report — {month}",
        "",
        f"Revisions: {len(records)}  ",
        f"Exact English changes: {len(changes)}",
        "",
    ]
    for record in records:
        lines.extend([f"## {record['revision']} — {record['summary']}", ""])
        for change in record["changes"]:
            location = change["after"] or change["before"]
            lines.extend(
                [
                    f"### {change['change_id']} — `{change['file']}:{location['line']}`",
                    "",
                    f"- Change: `{change['change_type']}` / `{change['source_kind']}`",
                    f"- Old: {exact_markdown_text(change['old_text'])}",
                    f"- New: {exact_markdown_text(change['new_text'])}",
                    f"- Remove from translations: {exact_markdown_text(change['removed_fragments'])}",
                    f"- Add to translations: {exact_markdown_text(change['added_fragments'])}",
                    f"- Review: {exact_markdown_text(change['review_note'])}",
                    "",
                ]
            )
    if not records:
        lines.extend(["No translatable English changes were recorded for this month.", ""])
    return "\n".join(lines)
# TIMESTAMP END 2026-08-19T18:13:49-04:00 | REVISION R000085


def markdown_value(value: Any) -> str:
    if value in (None, ""):
        return "—"
    return str(value).replace("|", "\\|").replace("\n", " ")


# TIMESTAMP START 2026-08-19T18:13:49-04:00 | REVISION R000085
def append_ledger(
    root: Path,
    metadata: dict[str, Any],
    localization_record: dict[str, Any] | None = None,
) -> None:
# TIMESTAMP END 2026-08-19T18:13:49-04:00 | REVISION R000085
    # TIMESTAMP START 2026-08-18T12:32:37-04:00 | REVISION R000001
    lock_path = root / "ledger.lock"
    with lock_path.open("a+", encoding="utf-8") as lock_handle:
        fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX)
        ledger = root / "ledger.jsonl"
        with ledger.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(metadata, sort_keys=True) + "\n")
        files = ", ".join(f"`{record['path']}`" for record in metadata["files"])
        entry = (
            f"## {metadata['revision']} — {metadata['summary']}\n\n"
            f"- Started: `{metadata['started_at']}`\n"
            f"- Finished: `{metadata['finished_at']}`\n"
            f"- Project: `{metadata['project']}`\n"
            f"- Kind: `{metadata['kind']}`\n"
            f"- Reverts: `{markdown_value(metadata['reverts'])}`\n"
            f"- Files: {files}\n"
            f"- Reason: {markdown_value(metadata['reason'])}\n"
            f"- Verification: {markdown_value(metadata['verification'])}\n"
            f"- Patch: `revisions/{metadata['revision']}/change.patch`\n\n"
        )
        with (root / "CHANGELOG.md").open("a", encoding="utf-8") as handle:
            handle.write(entry)
# TIMESTAMP START 2026-08-19T18:13:49-04:00 | REVISION R000085
        if localization_record is not None:
            append_localization_ledger(root, localization_record)
# TIMESTAMP END 2026-08-19T18:13:49-04:00 | REVISION R000085
        fcntl.flock(lock_handle.fileno(), fcntl.LOCK_UN)
    # TIMESTAMP END 2026-08-18T12:32:37-04:00 | REVISION R000001


# TIMESTAMP START 2026-08-18T13:51:51-04:00 | REVISION R000008
def backup_config_path(root: Path) -> Path:
    return root / BACKUP_CONFIG_NAME


def backup_status_path(root: Path) -> Path:
    return root / BACKUP_STATUS_NAME


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def load_backup_config(root: Path, required: bool = False) -> dict[str, Any] | None:
    path = backup_config_path(root)
    if not path.is_file():
        if required:
            raise ValueError("GitHub backup is not configured. Run backup-configure first.")
        return None
    config = read_json(path)
    required_keys = {"remote", "branch", "machine_id", "mirror_dir", "auto_sync", "include_snapshots"}
    missing = sorted(required_keys - config.keys())
    if missing:
        raise ValueError(f"GitHub backup configuration is missing: {', '.join(missing)}")
    return config


def machine_id_default() -> str:
    hostname = re.sub(r"[^a-z0-9-]+", "-", platform.node().casefold()).strip("-") or "machine"
    return f"{hostname}-{uuid.uuid4().hex[:8]}"


def validate_machine_id(value: str) -> str:
    normalized = value.strip().casefold()
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,62}", normalized):
        raise ValueError("Machine ID must contain only lowercase letters, digits, and hyphens (1-63 chars)")
    return normalized


def validate_remote(remote: str) -> str:
    value = remote.strip()
    if not value:
        raise ValueError("A GitHub repository clone URL or path is required")
    if re.match(r"https?://[^/]*@", value, flags=re.IGNORECASE):
        raise ValueError("Do not embed credentials in the remote URL; use Git credential or SSH authentication")
    return value


def run_git(arguments: list[str], cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", *arguments],
        cwd=str(cwd) if cwd else None,
        text=True,
        capture_output=True,
        check=False,
    )
    if check and result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or f"exit status {result.returncode}"
        raise ValueError(f"git {' '.join(arguments)} failed: {detail}")
    return result


def git_ref_exists(repository: Path, ref: str) -> bool:
    return run_git(["show-ref", "--verify", "--quiet", ref], cwd=repository, check=False).returncode == 0


def git_head_exists(repository: Path) -> bool:
    return run_git(["rev-parse", "--verify", "HEAD"], cwd=repository, check=False).returncode == 0


def prepare_mirror(config: dict[str, Any]) -> Path:
    mirror = Path(config["mirror_dir"]).expanduser().resolve()
    remote = config["remote"]
    branch = config["branch"]
    if not (mirror / ".git").is_dir():
        if mirror.exists() and any(mirror.iterdir()):
            raise ValueError(f"Backup mirror directory is not empty: {mirror}")
        mirror.parent.mkdir(parents=True, exist_ok=True)
        run_git(["clone", remote, str(mirror)])
    origin = run_git(["remote", "get-url", "origin"], cwd=mirror).stdout.strip()
    if origin != remote:
        raise ValueError(f"Backup mirror origin is {origin}, not configured remote {remote}")
    run_git(["fetch", "origin"], cwd=mirror)
    remote_ref = f"refs/remotes/origin/{branch}"
    local_ref = f"refs/heads/{branch}"
    if git_ref_exists(mirror, remote_ref):
        if git_ref_exists(mirror, local_ref):
            run_git(["checkout", branch], cwd=mirror)
            run_git(["pull", "--rebase", "origin", branch], cwd=mirror)
        else:
            run_git(["checkout", "-b", branch, f"origin/{branch}"], cwd=mirror)
    elif not git_head_exists(mirror):
        run_git(["symbolic-ref", "HEAD", local_ref], cwd=mirror)
    else:
        current = run_git(["branch", "--show-current"], cwd=mirror).stdout.strip()
        if current != branch:
            raise ValueError(f"Configured branch {branch} does not exist on the remote; current branch is {current}")
    return mirror


def copy_backup_payload(root: Path, mirror: Path, config: dict[str, Any]) -> Path:
    machine_dir = mirror / "machines" / config["machine_id"]
    machine_dir.mkdir(parents=True, exist_ok=True)
    for filename in ("CHANGELOG.md", "ledger.jsonl"):
        source = root / filename
        if source.is_file():
            shutil.copy2(source, machine_dir / filename)
# TIMESTAMP START 2026-08-19T18:13:49-04:00 | REVISION R000085
    localization_source = root / LOCALIZATION_DIR_NAME
    if localization_source.is_dir():
        shutil.copytree(
            localization_source,
            machine_dir / LOCALIZATION_DIR_NAME,
            dirs_exist_ok=True,
        )
# TIMESTAMP END 2026-08-19T18:13:49-04:00 | REVISION R000085
    target_revisions = machine_dir / "revisions"
    target_revisions.mkdir(parents=True, exist_ok=True)
    for revision_dir in sorted((root / "revisions").iterdir()):
        metadata_file = revision_dir / "metadata.json"
        if not metadata_file.is_file():
            continue
        metadata = read_json(metadata_file)
        if metadata.get("status") != "complete":
            continue
        target = target_revisions / revision_dir.name
        target.mkdir(parents=True, exist_ok=True)
        shutil.copy2(metadata_file, target / "metadata.json")
        patch = revision_dir / "change.patch"
        if patch.is_file():
            shutil.copy2(patch, target / "change.patch")
# TIMESTAMP START 2026-08-19T18:13:49-04:00 | REVISION R000085
        localization_artifact = revision_dir / "localization.json"
        if localization_artifact.is_file():
            shutil.copy2(localization_artifact, target / "localization.json")
# TIMESTAMP END 2026-08-19T18:13:49-04:00 | REVISION R000085
        if config["include_snapshots"]:
            for snapshot_name in ("before", "after"):
                snapshot = revision_dir / snapshot_name
                if snapshot.is_dir():
                    shutil.copytree(snapshot, target / snapshot_name, dirs_exist_ok=True)
    write_json(
        machine_dir / "manifest.json",
        {
            "machine_id": config["machine_id"],
            "source_history": str(root),
            "include_snapshots": config["include_snapshots"],
        },
    )
    return machine_dir


def update_backup_status(root: Path, **updates: Any) -> dict[str, Any]:
    path = backup_status_path(root)
    status = read_json(path) if path.is_file() else {}
    status.update(updates)
    write_json(path, status)
    return status


def sync_backup(root: Path, config: dict[str, Any]) -> str | None:
    lock_path = root / "github-backup.lock"
    with lock_path.open("a+", encoding="utf-8") as lock_handle:
        fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX)
        mirror = prepare_mirror(config)
        machine_dir = copy_backup_payload(root, mirror, config)
        relative_machine_dir = machine_dir.relative_to(mirror).as_posix()
        run_git(["add", "--", relative_machine_dir], cwd=mirror)
        staged = run_git(["diff", "--cached", "--quiet"], cwd=mirror, check=False)
        if staged.returncode not in (0, 1):
            raise ValueError(staged.stderr.strip() or "Unable to inspect staged GitHub backup changes")
        if staged.returncode == 1:
            run_git(
                [
                    "-c",
                    "user.name=Codex Change Ledger",
                    "-c",
                    "user.email=codex-ledger@localhost",
                    "commit",
                    "-m",
                    f"Backup {config['machine_id']} {timestamp_now()}",
                ],
                cwd=mirror,
            )
        if not git_head_exists(mirror):
            fcntl.flock(lock_handle.fileno(), fcntl.LOCK_UN)
            return None
        for attempt in range(1, 4):
            push = run_git(["push", "origin", f"HEAD:{config['branch']}"], cwd=mirror, check=False)
            if push.returncode == 0:
                commit = run_git(["rev-parse", "HEAD"], cwd=mirror).stdout.strip()
                fcntl.flock(lock_handle.fileno(), fcntl.LOCK_UN)
                return commit
            if attempt == 3:
                detail = push.stderr.strip() or push.stdout.strip()
                raise ValueError(f"GitHub backup push failed after 3 attempts: {detail}")
            run_git(["pull", "--rebase", "origin", config["branch"]], cwd=mirror)
    return None


def attempt_backup_sync(root: Path, config: dict[str, Any], announce: bool = True) -> bool:
    attempted_at = timestamp_now()
    update_backup_status(root, last_attempt_at=attempted_at, pending=True)
    try:
        commit = sync_backup(root, config)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        update_backup_status(root, last_error=str(exc), pending=True)
        if announce:
            print(f"warning: local revision is safe; GitHub backup remains pending: {exc}", file=sys.stderr)
        return False
    update_backup_status(
        root,
        last_success_at=timestamp_now(),
        last_commit=commit,
        last_error=None,
        pending=False,
    )
    if announce:
        print(f"GitHub backup synchronized at commit {commit or 'none'}")
    return True


def command_backup_configure(args: argparse.Namespace) -> int:
    if not args.confirm_private:
        raise ValueError("Refusing to configure backup without --confirm-private")
    root = ensure_history()
    existing = load_backup_config(root) or {}
    remote = validate_remote(args.remote)
    branch_check = run_git(["check-ref-format", "--branch", args.branch], check=False)
    if branch_check.returncode != 0:
        raise ValueError(f"Invalid backup branch: {args.branch}")
    machine_id = validate_machine_id(args.machine_id or existing.get("machine_id") or machine_id_default())
    mirror_dir = Path(args.mirror_dir).expanduser().resolve() if args.mirror_dir else root / "github-mirror"
    config = {
        "remote": remote,
        "branch": args.branch,
        "machine_id": machine_id,
        "mirror_dir": str(mirror_dir),
        "auto_sync": not args.manual_only,
        "include_snapshots": args.include_snapshots,
        "private_repository_confirmed": True,
    }
    write_json(backup_config_path(root), config)
    update_backup_status(root, configured_at=timestamp_now(), pending=True, last_error=None)
    print(f"Configured GitHub backup for {remote} on branch {args.branch}")
    print(f"MACHINE_ID={machine_id}")
    print("Local history remains authoritative. Run backup-sync to create and verify the mirror.")
    return 0


def command_backup_sync(args: argparse.Namespace) -> int:
    root = ensure_history()
    config = load_backup_config(root, required=True)
    return 0 if attempt_backup_sync(root, config) else 1


def command_backup_status(args: argparse.Namespace) -> int:
    root = ensure_history()
    config = load_backup_config(root)
    status_file = backup_status_path(root)
    status = read_json(status_file) if status_file.is_file() else {}
    print(json.dumps({"configured": config is not None, "config": config, "status": status}, indent=2, sort_keys=True))
    return 0


def command_backup_find(args: argparse.Namespace) -> int:
    root = ensure_history()
    config = load_backup_config(root, required=True)
    if not attempt_backup_sync(root, config, announce=False):
        print("warning: searching the most recently available local mirror", file=sys.stderr)
    mirror = Path(config["mirror_dir"])
    query = args.query.casefold()
    matches: list[tuple[str, dict[str, Any]]] = []
    for ledger in mirror.glob("machines/*/ledger.jsonl"):
        machine_id = ledger.parent.name
        for line in ledger.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            entry = json.loads(line)
            if query in json.dumps(entry, sort_keys=True).casefold():
                matches.append((machine_id, entry))
    for machine_id, entry in reversed(matches):
        files = ", ".join(record["path"] for record in entry["files"])
        print(
            f"{machine_id}:{entry['revision']} | {entry['started_at']} | {entry['project']} | "
            f"{entry['summary']} | {files}"
        )
    if not matches:
        print("No matching revisions in the GitHub backup mirror.")
    return 0
# TIMESTAMP END 2026-08-18T13:51:51-04:00 | REVISION R000008


def command_finish(args: argparse.Namespace) -> int:
    metadata_file, metadata = load_metadata(args.revision)
    if metadata["status"] != "pending":
        raise ValueError(f"Revision {args.revision} is already {metadata['status']}")
    project = Path(metadata["project"])
    revision_dir = metadata_file.parent
    after_dir = revision_dir / "after"
    for record in metadata["files"]:
        path = project / record["path"]
        state = file_state(path)
        snapshot_file(path, after_dir / record["path"])
        record["after"] = state
    patch, binary_files = build_patch(metadata, revision_dir)
    (revision_dir / "change.patch").write_text(patch, encoding="utf-8")
# TIMESTAMP START 2026-08-19T18:13:49-04:00 | REVISION R000085
    metadata["status"] = "complete"
    metadata["finished_at"] = timestamp_now()
    metadata["reason"] = args.reason.strip()
    metadata["verification"] = args.verification.strip()
    metadata["binary_files_without_text_patch"] = binary_files
    localization_scope = args.localization or metadata.get("localization_scope", "auto")
    metadata["localization_scope"] = localization_scope
    localization_record = build_localization_record(metadata, revision_dir, localization_scope)
    if localization_record is not None:
        write_json(revision_dir / "localization.json", localization_record)
    metadata["localization"] = {
        "artifact": "localization.json" if localization_record else None,
        "change_count": localization_record["change_count"] if localization_record else 0,
        "scope": localization_scope,
    }
    save_metadata(metadata_file, metadata)
    append_ledger(ensure_history(), metadata, localization_record)
    print(f"Recorded {metadata['revision']} at {metadata['finished_at']}")
    print(f"Artifacts: {revision_dir}")
    if localization_record is not None:
        print(
            f"Localization ledger: {localization_record['change_count']} exact English change(s) recorded"
        )
# TIMESTAMP END 2026-08-19T18:13:49-04:00 | REVISION R000085
    # TIMESTAMP START 2026-08-18T13:51:51-04:00 | REVISION R000008
    root = ensure_history()
    backup_config = load_backup_config(root)
    if backup_config and backup_config["auto_sync"]:
        attempt_backup_sync(root, backup_config)
    # TIMESTAMP END 2026-08-18T13:51:51-04:00 | REVISION R000008
    return 0


def command_show(args: argparse.Namespace) -> int:
    metadata_file, metadata = load_metadata(args.revision)
    print(json.dumps(metadata, indent=2, sort_keys=True))
    print(f"artifact_directory: {metadata_file.parent}")
    return 0


def read_ledger() -> list[dict[str, Any]]:
    ledger = ensure_history() / "ledger.jsonl"
    if not ledger.is_file():
        return []
    entries: list[dict[str, Any]] = []
    for line in ledger.read_text(encoding="utf-8").splitlines():
        if line.strip():
            entries.append(json.loads(line))
    return entries


def command_find(args: argparse.Namespace) -> int:
    query = args.query.casefold()
    matches = [entry for entry in read_ledger() if query in json.dumps(entry, sort_keys=True).casefold()]
    for entry in reversed(matches):
        files = ", ".join(record["path"] for record in entry["files"])
        print(
            f"{entry['revision']} | {entry['started_at']} | {entry['project']} | "
            f"{entry['summary']} | {files}"
        )
    if not matches:
        print("No matching completed revisions.")
    return 0


# TIMESTAMP START 2026-08-19T18:13:49-04:00 | REVISION R000085
def validate_month(value: str) -> str:
    if not re.fullmatch(r"\d{4}-(?:0[1-9]|1[0-2])", value):
        raise ValueError("Month must use YYYY-MM format")
    return value


def command_localization_report(args: argparse.Namespace) -> int:
    month = validate_month(args.month or timestamp_now()[:7])
    records = [
        record for record in read_localization_ledger() if record["finished_at"].startswith(month)
    ]
    if args.format == "json":
        print(
            json.dumps(
                {"month": month, "revision_count": len(records), "records": records},
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
        )
    else:
        print(render_localization_report(records, month))
    return 0
# TIMESTAMP END 2026-08-19T18:13:49-04:00 | REVISION R000085


def state_matches(path: Path, expected: dict[str, Any]) -> bool:
    return file_state(path) == expected


def command_revert(args: argparse.Namespace) -> int:
    metadata_file, metadata = load_metadata(args.revision)
    if metadata["status"] != "complete":
        raise ValueError(f"Cannot restore incomplete revision {args.revision}")
    project = Path(metadata["project"])
    revision_dir = metadata_file.parent
    conflicts: list[str] = []
    for record in metadata["files"]:
        path = project / record["path"]
        if not state_matches(path, record["after"]):
            conflicts.append(record["path"])
    print(f"Restore plan for {args.revision} in {project}:")
    for record in metadata["files"]:
        action = "restore before-snapshot" if record["before"]["exists"] else "remove file created by revision"
        print(f"- {record['path']}: {action}")
    if conflicts:
        print("Current state differs from the recorded after-state:", file=sys.stderr)
        for relative in conflicts:
            print(f"- {relative}", file=sys.stderr)
        if not args.force:
            print("Refusing to overwrite. Inspect the files or use --force with explicit authorization.", file=sys.stderr)
            return 2
    if not args.apply:
        print("Dry run only. Re-run with --apply after starting a new reversion revision.")
        return 0
    for record in metadata["files"]:
        target = project / record["path"]
        before = record["before"]
        if before["exists"]:
            source = revision_dir / "before" / record["path"]
            target.parent.mkdir(parents=True, exist_ok=True)
            if before["kind"] == "symlink":
                if target.exists() or target.is_symlink():
                    target.unlink()
                target.symlink_to(source.read_text(encoding="utf-8"))
            else:
                shutil.copy2(source, target)
        elif target.exists() or target.is_symlink():
            target.unlink()
    print(f"Applied before-snapshots from {args.revision}.")
    print("Verify the project, then finish the separate reversion revision.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    begin = subparsers.add_parser("begin", help="Allocate a revision and save before-snapshots")
    begin.add_argument("--project", required=True)
    begin.add_argument("--summary", required=True)
    begin.add_argument(
        "--kind",
        default="modification",
        choices=("addition", "modification", "fix", "refactor", "reversion", "test", "config", "other"),
    )
    begin.add_argument("--file", action="append", required=True)
    begin.add_argument("--reverts")
# TIMESTAMP START 2026-08-19T18:13:49-04:00 | REVISION R000085
    begin.add_argument(
        "--localization",
        choices=("auto", "include", "exclude"),
        default="auto",
        help="Scan changed text for exact public-English translation changes",
    )
# TIMESTAMP END 2026-08-19T18:13:49-04:00 | REVISION R000085
    begin.set_defaults(handler=command_begin)

    finish = subparsers.add_parser("finish", help="Save after-snapshots and complete a revision")
    finish.add_argument("revision")
    finish.add_argument("--reason", required=True)
    finish.add_argument("--verification", required=True)
# TIMESTAMP START 2026-08-19T18:13:49-04:00 | REVISION R000085
    finish.add_argument(
        "--localization",
        choices=("auto", "include", "exclude"),
        help="Override the localization scope selected at begin time",
    )
# TIMESTAMP END 2026-08-19T18:13:49-04:00 | REVISION R000085
    finish.set_defaults(handler=command_finish)

    show = subparsers.add_parser("show", help="Display one revision")
    show.add_argument("revision")
    show.set_defaults(handler=command_show)

    find = subparsers.add_parser("find", help="Search completed revisions")
    find.add_argument("query")
    find.set_defaults(handler=command_find)

# TIMESTAMP START 2026-08-19T18:13:49-04:00 | REVISION R000085
    localization_report = subparsers.add_parser(
        "localization-report",
        help="Render the exact English translation queue for one month",
    )
    localization_report.add_argument("--month", help="Calendar month in YYYY-MM format; defaults to current")
    localization_report.add_argument("--format", choices=("markdown", "json"), default="markdown")
    localization_report.set_defaults(handler=command_localization_report)
# TIMESTAMP END 2026-08-19T18:13:49-04:00 | REVISION R000085

    revert = subparsers.add_parser("revert", help="Dry-run or apply the recorded before-state")
    revert.add_argument("revision")
    revert.add_argument("--apply", action="store_true")
    revert.add_argument("--force", action="store_true")
    revert.set_defaults(handler=command_revert)

    # TIMESTAMP START 2026-08-18T13:51:51-04:00 | REVISION R000008
    backup_configure = subparsers.add_parser(
        "backup-configure",
        help="Configure a private GitHub repository as an optional ledger mirror",
    )
    backup_configure.add_argument("--remote", required=True)
    backup_configure.add_argument("--branch", default="main")
    backup_configure.add_argument("--machine-id")
    backup_configure.add_argument("--mirror-dir")
    backup_configure.add_argument("--include-snapshots", action="store_true")
    backup_configure.add_argument("--manual-only", action="store_true")
    backup_configure.add_argument("--confirm-private", action="store_true")
    backup_configure.set_defaults(handler=command_backup_configure)

    backup_sync = subparsers.add_parser("backup-sync", help="Retry and verify the GitHub ledger mirror")
    backup_sync.set_defaults(handler=command_backup_sync)

    backup_status = subparsers.add_parser("backup-status", help="Show GitHub mirror configuration and status")
    backup_status.set_defaults(handler=command_backup_status)

    backup_find = subparsers.add_parser("backup-find", help="Search revisions from every mirrored computer")
    backup_find.add_argument("query")
    backup_find.set_defaults(handler=command_backup_find)
    # TIMESTAMP END 2026-08-18T13:51:51-04:00 | REVISION R000008
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return args.handler(args)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
# TIMESTAMP END 2026-08-18T12:27:07-04:00 | REVISION BOOTSTRAP

# TIMESTAMP END 2026-11-04T07:06:41-05:00 | REVISION R005075
