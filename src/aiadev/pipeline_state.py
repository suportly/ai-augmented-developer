"""Pipeline-state detector for the AI-Augmented Developer pipeline.

Inspects a workspace's ``specs/<NNNN>-<slug>/`` tree and recommends the
next slash command in the spec → clarify → plan → tasks → implement →
review → finish pipeline.

Story 4 / AC-1..AC-8 of ``specs/0014-bmad-inspired-evolutions/spec.md``
defines the eight observable state transitions; the ≤ 200 ms perf
budget for a 50-spec workspace lives in ``plan.md``.

The module is an internal utility (cl-9: not a provider boundary).
Consumers: the ``help`` skill (T010) and the CLI flag (T021).
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

__all__ = ["recommend_next_command"]


_PLAIN_TRUTHY = frozenset({"1", "true", "yes", "on"})

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
    plain: bool = False,
) -> dict[str, Any]:
    """Return the next pipeline command for ``workspace_path``.

    Result shape::

        {"command": str | None, "reason": str}

    ``command`` is one of the ``/aiadev:*`` slash commands, or ``None``
    when plain mode is active. ``reason`` is a short free-form string
    suitable for debug surfaces; it is not part of the contract.
    """
    if plain or _plain_env_active():
        return {"command": None, "reason": "plain mode"}

    specs_dir = workspace_path / "specs"
    spec_dirs = _list_spec_dirs(specs_dir)
    if not spec_dirs:
        return {
            "command": "/aiadev:specify",
            "reason": "no specs/ tree (or empty)",
        }

    active = _find_active_spec_dir(spec_dirs, branch)
    if active is None:
        return {
            "command": "/aiadev:specify",
            "reason": "no spec.md matches the current branch",
        }

    spec_md = active / "spec.md"
    if not spec_md.is_file():
        return {
            "command": "/aiadev:specify",
            "reason": "active spec dir is missing spec.md",
        }

    pending_clarifications = _count_pending_clarifications(spec_md)
    if pending_clarifications:
        return {
            "command": "/aiadev:clarify",
            "reason": f"spec.md has {pending_clarifications} pending cl-N marker(s)",
        }

    if not (active / "plan.md").is_file():
        return {
            "command": "/aiadev:plan",
            "reason": "spec.md is clean; plan.md missing",
        }

    tasks_md = active / "tasks.md"
    if not tasks_md.is_file():
        return {
            "command": "/aiadev:tasks",
            "reason": "plan.md ticked; tasks.md missing",
        }

    pending_tasks = _count_pending_tasks(tasks_md)
    if pending_tasks:
        return {
            "command": "/aiadev:implement",
            "reason": f"tasks.md has {pending_tasks} pending task(s)",
        }

    last_review = _last_review_entry(active / ".review-log.jsonl")
    if (
        last_review is not None
        and last_review.get("verdict") == "APPROVED"
        and last_review.get("has_why_no_issues_block") is True
    ):
        return {
            "command": "/aiadev:finishing-a-branch",
            "reason": "all tasks done; review APPROVED with Why no issues block",
        }

    return {
        "command": "/aiadev:requesting-code-review",
        "reason": "all tasks done; review log missing or needs Why no issues block",
    }


def _plain_env_active() -> bool:
    """Return True when ``AIADEV_HELP_PLAIN`` is set to a truthy value."""
    raw = os.environ.get("AIADEV_HELP_PLAIN")
    if raw is None:
        return False
    return raw.strip().lower() in _PLAIN_TRUTHY


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


def _last_review_entry(review_log: Path) -> dict[str, Any] | None:
    """Return the last JSON object in ``.review-log.jsonl``, or None."""
    if not review_log.is_file():
        return None
    last_line: str | None = None
    with review_log.open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if stripped:
                last_line = stripped
    if last_line is None:
        return None
    try:
        parsed = json.loads(last_line)
    except json.JSONDecodeError:
        return None
    if not isinstance(parsed, dict):
        return None
    return parsed
