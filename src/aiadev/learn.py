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
import datetime
import pathlib
from typing import Mapping

from . import metrics as _metrics


def _entry_date(entry: dict) -> datetime.date | None:
    """Parse the ``YYYY-MM-DD`` date prefix of an entry timestamp, or None."""
    ts = entry.get("timestamp")
    if not isinstance(ts, str) or len(ts) < 10:
        return None
    try:
        return datetime.date.fromisoformat(ts[:10])
    except ValueError:
        return None


@dataclasses.dataclass(frozen=True)
class Proposal:
    """A reviewable guidance edit suggested for a pattern.

    ``target_file`` is one of two forms:

    * ``rules/<file>.md`` — a rule file to promote the snippet into;
    * ``checklist:<category>`` — a checklist category whose lens covers the
      pattern (spec 0021); a logical target, not a path on disk.

    Never ``constitution.md`` (cl-3); the constitution follows its own
    amendment process. Nothing is applied automatically either way — the
    target is a proposal for a human to act on.
    """

    snippet: str
    target_file: str


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
    # A reviewable guidance edit, attached only to sufficient patterns.
    proposal: "Proposal | None" = None


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
    *,
    min_features: int = 2,
) -> list[Pattern]:
    """Task ids that needed rework across **multiple** features.

    Uses :func:`aiadev.metrics.task_rework_counts` per feature (which already
    filters out pristine, single-``APPROVED`` tasks) and aggregates by
    ``task_id`` across features. ``occurrences`` = number of features in which
    the task needed rework; ``features`` = those spec ids. Like the reviewer
    detector, a task reworked in fewer than ``min_features`` features is
    returned with ``sufficient=False`` ("insufficient evidence", Story 3 sc2)
    rather than asserted as a recurring pattern.
    """
    features_by_task: dict[str, list[str]] = {}
    for spec_id, entries in per_spec_entries.items():
        for task_id, _rounds, _cr in _metrics.task_rework_counts(entries):
            features_by_task.setdefault(task_id, []).append(spec_id)

    patterns: list[Pattern] = []
    for task_id, specs in sorted(features_by_task.items()):
        features = tuple(sorted(specs))
        patterns.append(
            Pattern(
                kind="task-rework",
                subject=task_id,
                occurrences=len(features),
                features=features,
                sufficient=len(features) >= min_features,
            )
        )
    return patterns


def collect_per_spec_entries(
    workspace: pathlib.Path,
    *,
    since: datetime.date | None = None,
) -> dict[str, list[dict]]:
    """Read every ``specs/*/.review-log.jsonl`` under ``workspace``.

    Returns ``{spec_dir_name: entries}`` in sorted dir order. Read-only;
    reuses :func:`aiadev.metrics.read_review_log` for the JSONL grammar. Spec
    dirs without a log file (or with no entries left after the ``since``
    filter) are skipped.

    ``since`` (inclusive) drops entries dated before it. Entries whose
    timestamp cannot be parsed are kept (never silently drop evidence).
    """
    per_spec: dict[str, list[dict]] = {}
    specs_dir = workspace / "specs"
    if not specs_dir.is_dir():
        return per_spec
    for spec_dir in sorted(p for p in specs_dir.iterdir() if p.is_dir()):
        entries = _metrics.read_review_log(spec_dir / ".review-log.jsonl")
        if since is not None:
            kept = []
            for e in entries:
                date = _entry_date(e)
                if date is None or date >= since:
                    kept.append(e)
            entries = kept
        if entries:
            per_spec[spec_dir.name] = entries
    return per_spec


def detect_all(
    per_spec_entries: Mapping[str, list[dict]],
    *,
    min_features: int = 2,
    show_bodies: bool = False,
) -> list[Pattern]:
    """Run every detector and return patterns ranked for reporting.

    Ranking: sufficient patterns first, then by occurrences descending, then
    kind, then subject — so the most-evidenced actionable pattern is on top.
    """
    patterns = [
        *recurring_reviewer_failures(
            per_spec_entries, min_features=min_features, show_bodies=show_bodies
        ),
        *recurring_task_rework(per_spec_entries, min_features=min_features),
    ]
    patterns = [
        dataclasses.replace(p, proposal=propose_guidance(p)) if p.sufficient else p
        for p in patterns
    ]
    patterns.sort(
        key=lambda p: (not p.sufficient, -p.occurrences, p.kind, p.subject)
    )
    return patterns


# Conservative, hand-picked map from reviewer type to the checklist category
# whose lens most often catches that reviewer's recurring failures. Unlisted
# reviewers fall back to a rule file (spec 0021, cl-2).
_REVIEWER_CHECKLIST_CATEGORY = {
    "code-reviewer": "security",
}


def propose_guidance(pattern: Pattern) -> Proposal:
    """Build a reviewable guidance snippet + target rule file for a pattern.

    The target is always a rule under ``rules/`` (cl-3: never the
    constitution). The snippet is a starting point for a human to accept,
    edit, or reject — not final guidance.
    """
    evidence = ", ".join(pattern.features)
    if pattern.kind == "reviewer-recurrence":
        snippet = (
            f"The `{pattern.subject}` failed the first review pass in "
            f"{pattern.occurrences} features ({evidence}). Add an upstream "
            f"checklist item so the recurring cause is addressed before "
            f"review."
        )
        # Conservative reviewer → checklist-category map. A recurring reviewer
        # failure is often best captured as a checklist item in a specific
        # category; unmapped reviewers fall back to a rule file (no
        # regression). The target `checklist:<category>` is a proposal for a
        # human to act on — nothing is applied automatically.
        category = _REVIEWER_CHECKLIST_CATEGORY.get(pattern.subject)
        target = f"checklist:{category}" if category else "rules/review-recurrence.md"
    else:  # task-rework
        snippet = (
            f"Task `{pattern.subject}` needed rework in {pattern.occurrences} "
            f"features ({evidence}). Capture the pattern that caused the "
            f"repeated rework as a rule so future tasks avoid it."
        )
        target = "rules/task-rework.md"
    return Proposal(snippet=snippet, target_file=target)
