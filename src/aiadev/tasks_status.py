"""Parse, validate, and mutate ``tasks.md`` status lines.

Spec: ``specs/0013-implement-task-status-tracking/spec.md``.

Why this module exists: the ``implement`` skill prose mandates that
each per-task commit flips ``**Status:** pending`` → ``**Status:** done``
on the active ``### TNNN`` block of ``specs/<branch>/tasks.md``. Centralising
the parse/validate/mutate logic here keeps the semantics testable in
isolation and gives any future tooling (preflight, analyze) a single
home for the rule.

Public API:

- ``parse(path)`` returns a list of ``TaskRow`` (tolerant — missing
  status produces ``status=None``; ``validate`` is the strict layer).
- ``validate(rows)`` raises ``TasksMdError`` if any block is malformed
  or if the ``done`` ids do not form a contiguous prefix of the
  declared task order.
- ``mark_done(path, task_id)`` flips the targeted block's status
  in place; idempotent on already-``done`` rows.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

VALID_STATUSES: tuple[str, ...] = ("pending", "in_progress", "blocked", "done")

# Single source of truth for the line shapes parse and mark_done both edit.
# Re-using the same regex prevents the two operations from disagreeing on
# what counts as a status line.
_TASK_HEADER_RE = re.compile(r"^### (T\d{3,}) — (.+)$", re.MULTILINE)
_STATUS_LINE_RE = re.compile(r"^- \*\*Status:\*\* (\S+)\s*$", re.MULTILINE)


class TasksMdError(Exception):
    """Raised on any malformed or inconsistent ``tasks.md`` state.

    Carries a single-line message suitable for printing directly to
    the user — the ``implement`` skill prose treats the message body as
    the abort string the agent surfaces.
    """


@dataclass(frozen=True)
class TaskRow:
    id: str
    title: str
    status: Optional[str]
    line: int  # 1-based line number of the ``### TNNN`` header


def parse(path: Path | str) -> list[TaskRow]:
    text = Path(path).read_text(encoding="utf-8")
    headers = list(_TASK_HEADER_RE.finditer(text))
    rows: list[TaskRow] = []
    for i, header in enumerate(headers):
        body_start = header.end()
        body_end = headers[i + 1].start() if i + 1 < len(headers) else len(text)
        body = text[body_start:body_end]
        status_match = _STATUS_LINE_RE.search(body)
        rows.append(
            TaskRow(
                id=header.group(1),
                title=header.group(2).strip(),
                status=status_match.group(1) if status_match else None,
                line=text.count("\n", 0, header.start()) + 1,
            )
        )
    return rows


def validate(rows: list[TaskRow]) -> None:
    for row in rows:
        if row.status is None:
            raise TasksMdError(
                f"ERROR: tasks.md malformed at {row.id} (line {row.line}): "
                f"missing or unparseable **Status:** line. "
                f"Fix manually before resuming."
            )
        if row.status not in VALID_STATUSES:
            raise TasksMdError(
                f"ERROR: tasks.md malformed at {row.id} (line {row.line}): "
                f"status {row.status!r} is not in the allowed taxonomy "
                f"{VALID_STATUSES}. Fix manually before resuming."
            )

    # ``done`` ids must form a contiguous prefix of the declared order.
    # The earliest non-``done`` row pins the prefix boundary; any
    # ``done`` row past that boundary is the inconsistency we report.
    first_non_done: Optional[TaskRow] = None
    for row in rows:
        if row.status != "done":
            if first_non_done is None:
                first_non_done = row
            continue
        if first_non_done is not None:
            raise TasksMdError(
                f"ERROR: tasks.md inconsistency — {row.id} is done but "
                f"{first_non_done.id} is {first_non_done.status}. "
                f"Fix tasks.md manually before resuming."
            )


def mark_done(path: Path | str, task_id: str) -> None:
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    headers = list(_TASK_HEADER_RE.finditer(text))

    target_index = next(
        (i for i, h in enumerate(headers) if h.group(1) == task_id),
        None,
    )
    if target_index is None:
        raise TasksMdError(f"task {task_id} not found in {p}")

    header = headers[target_index]
    body_start = header.end()
    body_end = (
        headers[target_index + 1].start()
        if target_index + 1 < len(headers)
        else len(text)
    )
    body = text[body_start:body_end]
    status_match = _STATUS_LINE_RE.search(body)
    if status_match is None:
        raise TasksMdError(
            f"task {task_id} has no parseable **Status:** line in {p}"
        )
    if status_match.group(1) == "done":
        return  # idempotent — Story 2 sc1 resume safety

    new_body = (
        body[: status_match.start()]
        + "- **Status:** done"
        + body[status_match.end() :]
    )
    p.write_text(text[:body_start] + new_body + text[body_end:], encoding="utf-8")
