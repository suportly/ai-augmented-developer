"""Pipeline-state detector for the AI-Augmented Developer pipeline.

Inspects a workspace's ``specs/<NNNN>-<slug>/`` tree and recommends the
next slash command in the spec → clarify → plan → tasks → implement →
review → finish pipeline.

Story 4 / AC-1..AC-8 of ``specs/0014-bmad-inspired-evolutions/spec.md``
defines the eight observable state transitions; the ≤ 200 ms perf
budget for a 50-spec workspace lives in ``plan.md``.

The module is an internal utility (cl-9: not a provider boundary).
Consumer: ``aiadev next`` (spec 0030, D6).
"""
from __future__ import annotations

import json
import re
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

__all__ = ["recommend_next_command"]


_BRANCH_LINE_RE = re.compile(r"^\*\*Branch:\*\*\s*`([^`]+)`", re.MULTILINE)
_CLARIFICATION_RE = re.compile(r"\[NEEDS CLARIFICATION:cl-\d+")
_TASK_STATUS_RE = re.compile(
    r"^- \*\*Status:\*\*\s*(pending|in_progress|blocked|done)\b",
    re.MULTILINE,
)


def recommend_next_command(
    workspace_path: Path,
    *,
    branch: str | None = None,
    feature: str | None = None,
) -> dict[str, Any]:
    """Return the next pipeline command for ``workspace_path``.

    Result shape::

        {"command": str, "reason": str}

    ``command`` is one of the ``/aia:*`` slash commands. ``reason`` is a
    short free-form string suitable for debug surfaces; it is not part of
    the contract.

    ``feature`` (a ``specs/<slug>/`` directory name) selects the spec
    directly and takes precedence over ``branch``. A slug without a spec
    directory recommends ``/aia:specify``; it is not an error.
    """
    specs_dir = workspace_path / "specs"

    if feature is not None:
        active = _feature_dir(specs_dir, feature)
        if active is None:
            return {
                "command": "/aia:specify",
                "reason": f"feature {feature!r} has no spec yet (specs/{feature}/ missing)",
            }
    else:
        spec_dirs = _list_spec_dirs(specs_dir)
        if not spec_dirs:
            return {
                "command": "/aia:specify",
                "reason": "no specs/ tree (or empty)",
            }
        active = _find_active_spec_dir(spec_dirs, branch)
        if active is None:
            return {
                "command": "/aia:specify",
                "reason": "no spec.md matches the current branch",
            }

    spec_md = active / "spec.md"
    if not _is_file_strict(spec_md):
        return {
            "command": "/aia:specify",
            "reason": "active spec dir is missing spec.md",
        }

    pending_clarifications = _count_pending_clarifications(spec_md)
    if pending_clarifications:
        return {
            "command": "/aia:clarify",
            "reason": f"spec.md has {pending_clarifications} pending cl-N marker(s)",
        }

    if not (active / "plan.md").is_file():
        return {
            "command": "/aia:plan",
            "reason": "spec.md is clean; plan.md missing",
        }

    tasks_md = active / "tasks.md"
    if not tasks_md.is_file():
        return {
            "command": "/aia:tasks",
            "reason": "plan.md ticked; tasks.md missing",
        }

    pending_tasks = _count_pending_tasks(tasks_md)
    if pending_tasks:
        return {
            "command": "/aia:implement",
            "reason": f"tasks.md has {pending_tasks} pending task(s)",
        }

    if _branch_review_approved(workspace_path, active / ".review-log.jsonl"):
        return {
            "command": "/aia:finishing-a-branch",
            "reason": "all tasks done; .aiadev/review.yaml approved after the last review-log entry",
        }

    return {
        "command": "/aia:requesting-code-review",
        "reason": "all tasks done; branch review missing, not approved or older than the review log",
    }


def _is_file_strict(path: Path) -> bool:
    """``is_file`` that only treats "not found" as False; other OSErrors raise."""
    try:
        return path.stat().st_mode & 0o170000 == 0o100000
    except (FileNotFoundError, NotADirectoryError):
        return False


def _feature_dir(specs_dir: Path, feature: str) -> Path | None:
    """Return ``specs/<feature>/`` or None; the slug must be a bare name."""
    if not feature or feature in {".", ".."} or "/" in feature or "\\" in feature:
        return None
    candidate = specs_dir / feature
    return candidate if candidate.is_dir() else None


def _branch_review_approved(workspace_path: Path, review_log: Path) -> bool:
    """True when ``review.yaml`` is approved and not older than the log.

    Fail-closed: a missing/unreadable ``timestamp`` is "not approved".
    A feature with no review-log entries has no cutoff; this is the same
    known edge the ``finishing-a-branch`` preflight has (it only checks
    ``status``), so prose-only features stay finishable.
    """
    import yaml  # local import keeps the module import-cheap

    review_path = workspace_path / ".aiadev" / "review.yaml"
    if not review_path.is_file():
        return False
    try:
        payload = yaml.safe_load(review_path.read_text(encoding="utf-8"))
    except (yaml.YAMLError, UnicodeDecodeError):
        return False
    if not isinstance(payload, dict) or payload.get("status") != "approved":
        return False
    approved_at = _parse_timestamp(payload.get("timestamp"))
    if approved_at is None:
        return False
    try:
        cutoff, log_has_entries = _last_log_timestamp(review_log)
    except UnicodeDecodeError:
        return False
    if cutoff is None:
        # Entries with no readable timestamp cannot be ordered: fail closed.
        return not log_has_entries
    return approved_at >= cutoff


def _parse_timestamp(value: Any) -> datetime | None:
    """Parse an ISO-8601 string (``Z`` or offset) or YAML datetime to aware UTC."""
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, date):
        parsed = datetime(value.year, value.month, value.day)
    elif isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.strip())
        except ValueError:
            return None
    else:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _last_log_timestamp(review_log: Path) -> tuple[datetime | None, bool]:
    """Return (newest parseable entry timestamp, whether any entry exists)."""
    if not review_log.is_file():
        return None, False
    newest: datetime | None = None
    has_entries = False
    with review_log.open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped:
                continue
            has_entries = True
            try:
                entry = json.loads(stripped)
            except json.JSONDecodeError:
                continue
            if not isinstance(entry, dict):
                continue
            stamp = _parse_timestamp(entry.get("timestamp"))
            if stamp is not None and (newest is None or stamp > newest):
                newest = stamp
    return newest, has_entries


def _list_spec_dirs(specs_dir: Path) -> list[Path]:
    """Return ``<NNNN>-<slug>/`` subdirs of ``specs/`` (empty if missing)."""
    if not specs_dir.is_dir():
        return []
    pattern = re.compile(r"^\d{3,4}-")
    return [
        child
        for child in specs_dir.iterdir()
        if child.is_dir() and pattern.match(child.name)
    ]


def _find_active_spec_dir(
    spec_dirs: list[Path], branch: str | None
) -> Path | None:
    """Pick the spec dir matching ``branch`` (or the most recent one)."""
    if branch is None:
        return max(spec_dirs, key=lambda d: d.stat().st_mtime)
    for spec_dir in spec_dirs:
        if _spec_branch(spec_dir / "spec.md") == branch:
            return spec_dir
    return None


def _spec_branch(spec_md: Path) -> str | None:
    """Return the branch declared in the ``**Branch:**`` header, or None."""
    if not spec_md.is_file():
        return None
    with spec_md.open("r", encoding="utf-8") as handle:
        for _ in range(15):
            line = handle.readline()
            if not line:
                break
            match = _BRANCH_LINE_RE.match(line)
            if match:
                return match.group(1)
    return None


def _count_pending_clarifications(spec_md: Path) -> int:
    """Count ``[NEEDS CLARIFICATION:cl-N`` markers in ``spec_md``."""
    text = spec_md.read_text(encoding="utf-8")
    return len(_CLARIFICATION_RE.findall(text))


def _count_pending_tasks(tasks_md: Path) -> int:
    """Count tasks whose ``**Status:**`` is not ``done``."""
    text = tasks_md.read_text(encoding="utf-8")
    pending = 0
    for status in _TASK_STATUS_RE.findall(text):
        if status != "done":
            pending += 1
    return pending
