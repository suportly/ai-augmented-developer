"""Review-log utilities for the bmad-inspired evolutions feature.

Implements three primitives backing Story 3 (per cl-5 in
``specs/0014-bmad-inspired-evolutions/spec.md``):

* ``is_non_trivial_change`` — decides whether a diff warrants a code
  review, applying the LOC threshold and the docs/governance exclusions.
* ``append_review_entry`` — appends a JSON line to
  ``<workspace>/specs/<branch>/.review-log.jsonl``.
* ``last_review_entry`` — returns the most recent valid JSON entry from
  the same file, tolerating malformed lines.

Stdlib only. No I/O happens at import time.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Union

_EXCLUDED_EXTENSIONS = frozenset({".md", ".json", ".lock", ".toml"})

_LOC_THRESHOLD = 10

_INSERTIONS_RE = re.compile(r"(\d+)\s+insertion")

_DELETIONS_RE = re.compile(r"(\d+)\s+deletion")

_GOVERNANCE_RE = re.compile(r"^specs/\d+-[^/]+/(spec|plan)\.md$")

ShortstatInput = Union[str, dict]


def _excluded(path: str) -> bool:
    """Return True when ``path`` falls outside the reviewable surface."""
    if path.startswith("docs/"):
        return True
    suffix = Path(path).suffix
    return suffix in _EXCLUDED_EXTENSIONS


def _is_governance_artifact(path: str) -> bool:
    """Return True when ``path`` is a spec.md or plan.md governance file."""
    return bool(_GOVERNANCE_RE.match(path))


def _parse_loc(diff_shortstat: ShortstatInput) -> int:
    """Return total changed LOC (insertions + deletions) for a shortstat."""
    if isinstance(diff_shortstat, dict):
        insertions = int(diff_shortstat.get("insertions", 0))
        deletions = int(diff_shortstat.get("deletions", 0))
        return insertions + deletions
    insertions_match = _INSERTIONS_RE.search(diff_shortstat)
    deletions_match = _DELETIONS_RE.search(diff_shortstat)
    insertions = int(insertions_match.group(1)) if insertions_match else 0
    deletions = int(deletions_match.group(1)) if deletions_match else 0
    return insertions + deletions


def is_non_trivial_change(
    diff_shortstat: ShortstatInput, paths: list[str]
) -> bool:
    """Return True when the diff is large enough or touches a governance artifact."""
    if not paths:
        return False
    if any(_is_governance_artifact(path) for path in paths):
        return True
    reviewable_paths = [path for path in paths if not _excluded(path)]
    if not reviewable_paths:
        return False
    total_loc = _parse_loc(diff_shortstat)
    return total_loc > _LOC_THRESHOLD


def _branch_dir(workspace_path: Path) -> Path:
    """Return the single ``<workspace>/specs/<branch>/`` directory."""
    specs_dir = workspace_path / "specs"
    if not specs_dir.is_dir():
        raise FileNotFoundError(
            f"specs directory not found under workspace: {specs_dir}"
        )
    children = [child for child in specs_dir.iterdir() if child.is_dir()]
    if not children:
        raise FileNotFoundError(
            f"no branch directory found under {specs_dir}"
        )
    return children[0]


def append_review_entry(workspace_path: Path, entry: dict) -> None:
    """Append ``entry`` as a JSON line to the workspace review log."""
    branch_dir = _branch_dir(workspace_path)
    log_path = branch_dir / ".review-log.jsonl"
    line = json.dumps(entry) + "\n"
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(line)


def last_entry_from_log(log_path: Path) -> dict | None:
    """Return the last valid JSON entry from ``log_path``, or None.

    Tolerates blank and malformed lines. Returns None when the file
    does not exist or contains no parseable entry. Reusable across
    callers that already know the exact `.review-log.jsonl` path,
    which avoids forcing them through `_branch_dir`'s single-child
    assumption.
    """
    if not log_path.is_file():
        return None
    last_valid: dict | None = None
    with log_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped:
                continue
            try:
                last_valid = json.loads(stripped)
            except json.JSONDecodeError:
                continue
    return last_valid


def last_review_entry(workspace_path: Path) -> dict | None:
    """Return the last valid JSON entry from the review log, or None."""
    try:
        branch_dir = _branch_dir(workspace_path)
    except FileNotFoundError:
        return None
    return last_entry_from_log(branch_dir / ".review-log.jsonl")
