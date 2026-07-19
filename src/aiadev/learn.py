"""Core engine for ``aiadev learn`` (spec 0018).

Read-only. Mines the pipeline audit trail for **recurring failure patterns**
and reuses the public primitives in :mod:`aiadev.metrics` (which own the
``.review-log.jsonl`` grammar) — it never re-parses the trail itself and
never calls the network or ``subprocess``.

Like :mod:`aiadev.metrics`, this module is intentionally small: a frozen
``Pattern`` dataclass holds one detected pattern, and the rest are free
functions that take injected data and return patterns. The CLI layer
(:mod:`aiadev.commands.learn`) walks the workspace and formats output.
"""
from __future__ import annotations

import dataclasses
from typing import Mapping

from . import metrics as _metrics


@dataclasses.dataclass(frozen=True)
class Pattern:
    """One recurring failure pattern with its evidence.

    ``subject`` is the reviewer name (for ``reviewer-recurrence``) or the
    task id (for ``task-rework``). ``features`` are the spec ids that
    evidence the pattern. ``occurrences`` is how many features/rounds it
    was seen in.
    """

    kind: str
    subject: str
    occurrences: int
    features: tuple[str, ...]
    sufficient: bool = True
    # Reviewer free-text prose (the ``note`` field). Empty unless the caller
    # opts in with ``show_bodies=True`` — kept out of the default output per
    # Article VI (mirrors ``metrics --show-bodies``).
    notes: tuple[str, ...] = ()


def recurring_reviewer_failures(
    per_spec_entries: Mapping[str, list[dict]],
    *,
    min_features: int = 2,
    show_bodies: bool = False,
) -> list[Pattern]:
    """Reviewers that failed the **first pass** across multiple features.

    A reviewer "failed first pass" in a feature when, for that feature's
    review log, its first-pass approved count is below its total (i.e. at
    least one first attempt was not ``APPROVED``) — computed via
    :func:`aiadev.metrics.first_pass_rate_by_reviewer`. The trail carries no
    "category" of rejection, so the signal is per reviewer.

    Returns one ``Pattern`` per reviewer that failed first pass in ≥ 1
    feature, sorted by reviewer name. A pattern seen in fewer than
    ``min_features`` features is returned with ``sufficient=False`` (thin
    trail → "insufficient evidence", Story 3 sc2) rather than dropped.
    """
    failures: dict[str, list[str]] = {}
    notes: dict[str, list[str]] = {}
    for spec_id, entries in per_spec_entries.items():
        rates = _metrics.first_pass_rate_by_reviewer(entries)
        for reviewer, (approved, total) in rates.items():
            if approved < total:
                failures.setdefault(reviewer, []).append(spec_id)
                if show_bodies:
                    for entry in entries:
                        if (
                            entry.get("reviewer") == reviewer
                            and entry.get("verdict") == "CHANGES_REQUESTED"
                            and entry.get("note")
                        ):
                            notes.setdefault(reviewer, []).append(entry["note"])

    patterns: list[Pattern] = []
    for reviewer, specs in sorted(failures.items()):
        features = tuple(sorted(specs))
        patterns.append(
            Pattern(
                kind="reviewer-recurrence",
                subject=reviewer,
                occurrences=len(features),
                features=features,
                sufficient=len(features) >= min_features,
                notes=tuple(notes.get(reviewer, ())),
            )
        )
    return patterns


def recurring_task_rework(
    per_spec_entries: Mapping[str, list[dict]],
) -> list[Pattern]:
    """Tasks that needed rework (≥ 1 ``CHANGES_REQUESTED`` code review round).

    Uses :func:`aiadev.metrics.task_rework_counts` per feature, which already
    filters out pristine (single-``APPROVED``) tasks. Returns one ``Pattern``
    per reworked task, ``occurrences`` = total review rounds, ``features`` =
    the spec id it belongs to. Sorted by rounds descending, then task id.
    """
    patterns: list[Pattern] = []
    for spec_id, entries in per_spec_entries.items():
        for task_id, rounds, _cr in _metrics.task_rework_counts(entries):
            patterns.append(
                Pattern(
                    kind="task-rework",
                    subject=task_id,
                    occurrences=rounds,
                    features=(spec_id,),
                )
            )
    patterns.sort(key=lambda p: (-p.occurrences, p.subject))
    return patterns
