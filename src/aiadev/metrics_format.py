"""Output formatters for ``aiadev metrics``.

Spec: ``specs/0015-aiadev-metrics/spec.md``.

Two pure projections over ``MetricsReport``:

* ``format_text`` — human-friendly default for terminals.
* ``format_json`` — stable, versioned schema for CI/scripts.

Both functions are side-effect-free; the CLI layer prints the result.
They share no state beyond the report. New formatters in the future
should add a third function rather than introducing a registry.

cl-3 (Privacy by design): neither formatter emits the free-text
``note`` field from review log entries by default. The ``--show-bodies``
flag travels as the ``show_bodies`` parameter through both functions
and is the only path that prints raw reviewer prose.
"""

from __future__ import annotations

import json
from typing import Iterable

from .metrics import MetricsReport


# ---------------------------------------------------------------------
# Text formatter
# ---------------------------------------------------------------------


def format_text(
    report: MetricsReport,
    *,
    show_tasks: bool = False,
    show_bodies: bool = False,
    review_entries: Iterable[dict] | None = None,
) -> str:
    """Render the report as human-readable text.

    ``show_tasks``: when True, append the per-task rework listing
    (Story 3).

    ``show_bodies``: when True (and ``review_entries`` is provided),
    append the raw ``note`` field of each review entry. Off by default
    per cl-3 — the CLI must pass the flag explicitly.

    ``review_entries``: the raw review log entries the report was
    aggregated from. Only consumed when ``show_bodies`` is True.
    """
    lines: list[str] = []

    since, until = report.window
    lines.append(f"Janela: [{since.isoformat()}, {until.isoformat()}]")
    lines.append(
        f"n={report.n_specs_in_window} coverage={report.coverage_percent}%"
    )
    lines.append("")

    if report.per_reviewer_first_pass_rate:
        lines.append("First-pass approval rate (por reviewer):")
        for reviewer in sorted(report.per_reviewer_first_pass_rate):
            approved, total = report.per_reviewer_first_pass_rate[reviewer]
            pct = (100.0 * approved / total) if total else 0.0
            lines.append(f"  {reviewer}: {approved}/{total} ({pct:.0f}%)")
    else:
        lines.append("review trail: vazio (feature ainda no estágio de implement, ou pré-cutoff)")
    lines.append("")

    lines.append("Tasks por status:")
    for status in ("pending", "in_progress", "blocked", "done"):
        lines.append(f"  {status}: {report.tasks_by_status.get(status, 0)}")
    lines.append("")

    lines.append(
        f"Markers cl-N não resolvidos (snapshot atual): {report.unresolved_clarifications_count}"
    )
    if report.total_clarify_iterations is not None:
        lines.append(
            f"Iterações de clarify acumuladas no histórico: {report.total_clarify_iterations}"
        )
    if report.specify_to_last_commit_median_days is not None:
        lines.append(
            f"Specify→último commit (mediana, dias): {report.specify_to_last_commit_median_days}"
        )
    if report.unknown_status_count:
        lines.append(
            f"Specs com Status fora do enum canônico (bucket 'other'): {report.unknown_status_count}"
        )
    lines.append("")

    if show_tasks:
        # Story 3 sc3: header announcing the sample size, emitted
        # unconditionally when --tasks is on. ``tasks_reached_review`` is
        # distinct task ids that received ≥ 1 code-reviewer entry;
        # ``total_tasks`` is the row count summed across every spec in
        # the window. When they match we omit the header (no value in
        # showing "10/10").
        if report.total_tasks and report.tasks_reached_review < report.total_tasks:
            lines.append(
                f"{report.tasks_reached_review}/{report.total_tasks} tasks reached review"
            )
        if report.tasks_with_rework:
            lines.append("Tasks com rework (rounds desc):")
            for task_id, rounds, cr_count in report.tasks_with_rework:
                # Story 3 sc1 wording: "T003: 3 review rounds (2 changes_requested → approved)".
                lines.append(
                    f"  {task_id}: {rounds} review rounds "
                    f"({cr_count} changes_requested → approved)"
                )
        else:
            lines.append("Tasks com rework: todas as tasks aprovadas em 1ª passada")
        lines.append("")

    if show_bodies and review_entries is not None:
        lines.append("Bodies (--show-bodies):")
        for e in review_entries:
            ts = e.get("timestamp", "?")
            reviewer = e.get("reviewer", "?")
            task_id = e.get("task_id", "?")
            verdict = e.get("verdict", "?")
            note = e.get("note", "")
            lines.append(f"  [{ts}] {reviewer} {task_id} {verdict}: {note}")
        lines.append("")

    lines.append("o que estes números NÃO significam:")
    for d in report.disclaimer_lines:
        lines.append(f"  · {d}")

    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------
# JSON formatter
# ---------------------------------------------------------------------


JSON_SCHEMA_VERSION = 1


def format_json(
    report: MetricsReport,
    *,
    show_tasks: bool = False,
    show_bodies: bool = False,
    review_entries: Iterable[dict] | None = None,
) -> str:
    """Render the report as JSON with a stable schema (``schema_version``).

    The schema is stable across patch releases of aiadev — additive
    fields land as ``schema_version: 2`` only.

    No execution timestamp is included. The output is a pure function
    of the report (and the optional ``review_entries`` when
    ``show_bodies`` is True), which gives the determinism property the
    spec asks for in Story 2 sc3.
    """
    since, until = report.window
    payload: dict = {
        "schema_version": JSON_SCHEMA_VERSION,
        "window": {
            "since": since.isoformat(),
            "until": until.isoformat(),
        },
        "n_specs_in_window": report.n_specs_in_window,
        "coverage_percent": round(report.coverage_percent, 1),
        "per_reviewer_first_pass_rate": {
            reviewer: {"approved": a, "total": t}
            for reviewer, (a, t) in sorted(report.per_reviewer_first_pass_rate.items())
        },
        "tasks_by_status": {
            status: report.tasks_by_status.get(status, 0)
            for status in ("pending", "in_progress", "blocked", "done")
        },
        "specify_to_last_commit_median_days": report.specify_to_last_commit_median_days,
        "unresolved_clarifications_count": report.unresolved_clarifications_count,
        "total_clarify_iterations": report.total_clarify_iterations,
        "unknown_status_count": report.unknown_status_count,
        "disclaimer_lines": list(report.disclaimer_lines),
    }

    if show_tasks:
        payload["tasks_with_rework"] = [
            {"task_id": tid, "rounds": rounds, "changes_requested_count": cr}
            for tid, rounds, cr in report.tasks_with_rework
        ]
        payload["tasks_reached_review"] = report.tasks_reached_review
        payload["total_tasks"] = report.total_tasks

    if show_bodies and review_entries is not None:
        payload["bodies"] = [
            {
                "timestamp": e.get("timestamp"),
                "reviewer": e.get("reviewer"),
                "task_id": e.get("task_id"),
                "verdict": e.get("verdict"),
                "note": e.get("note", ""),
            }
            for e in review_entries
        ]

    return json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
