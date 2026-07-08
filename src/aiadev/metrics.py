"""Core calculator for ``aiadev metrics``.

Spec: ``specs/0015-aiadev-metrics/spec.md``.

This module is the read-only core. It does not call ``subprocess`` (git
interaction lives in ``aiadev.commands.metrics``) and it does not
format output (``aiadev.metrics_format`` owns that). The CLI layer is
the orchestrator that wires the three together.

The module is intentionally small: a frozen ``MetricsReport`` dataclass
holds the aggregated shape; the rest are free functions that take a
workspace path or a list of entries and return primitives. This keeps
test setup trivial (inject a fixture path) and lets future callers
reuse the calculators without forcing a CLI dependency.
"""

from __future__ import annotations

import dataclasses
import datetime
import json
import pathlib
import re
import statistics
from typing import Iterable, Iterator


# ---------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------

# Canonical Status enum recognised by the framework today. Anything outside
# this set bucketises as "other" rather than raising, so legacy specs
# (e.g. "PR Open" from before the enum was tightened) do not break the
# aggregator. The raw value is preserved under ``status_raw`` for
# diagnostics.
CANONICAL_STATUSES = frozenset({
    "Draft",
    "In review",
    "Approved",
    "Implemented",
    "Merged",
})

# Statuses that qualify a spec for the aggregate (no ``--feature``)
# sample — spec success criterion 2. In-flight specs (Draft, In review,
# Approved) are excluded from the aggregate so a repo full of drafts
# does not deflate coverage; ``--feature`` mode bypasses this filter.
AGGREGATE_STATUSES = frozenset({"Implemented", "Merged"})


# Header field regexes. Each field is matched independently to tolerate
# specs whose field order drifts (the template orders them
# Branch / Created / Status / Spec ID, but downstream callers should
# not break if a spec authored under an earlier template uses a
# different order).
_SPEC_ID_RE = re.compile(r"^\*\*Spec ID:\*\*\s*(\d+)", re.MULTILINE)
_STATUS_RE = re.compile(r"^\*\*Status:\*\*\s*([^\n<]+?)\s*(?:<!--|$)", re.MULTILINE)
_CREATED_RE = re.compile(r"^\*\*Created:\*\*\s*(\d{4}-\d{2}-\d{2})", re.MULTILINE)


# ---------------------------------------------------------------------
# MetricsReport
# ---------------------------------------------------------------------


@dataclasses.dataclass(frozen=True)
class MetricsReport:
    """Aggregated metrics over a window of specs.

    All fields are pre-computed; formatters are pure projections over
    this dataclass. The shape is the contract between the calculator
    and the formatters.
    """

    # Window the metrics cover (inclusive).
    window: tuple[datetime.date, datetime.date]

    # Sample size: in aggregate mode, specs whose ``Created:`` fell in
    # the window AND whose Status is in ``AGGREGATE_STATUSES``; in
    # ``--feature`` mode, the single resolved spec (any status).
    n_specs_in_window: int

    # Fraction of those specs that have a non-missing ``.review-log.jsonl``.
    # Expressed as percent rounded to one decimal place.
    coverage_percent: float

    # ``{reviewer_type: (first_pass_approved_count, total_first_attempt_count)}``.
    # First-attempt = first chronological entry per ``(task_id, reviewer)``
    # pair (cl-6 resolution).
    per_reviewer_first_pass_rate: dict[str, tuple[int, int]]

    # ``{status: count}`` summed across every spec in the window.
    tasks_by_status: dict[str, int]

    # ``[(task_id, code_reviewer_rounds, changes_requested_count), ...]``
    # sorted by rounds descending, only including tasks with ≥ 1
    # ``CHANGES_REQUESTED`` entry. The CR count exists so the formatter
    # can emit the Story 3 sc1 wording "N review rounds (M
    # changes_requested → approved)".
    tasks_with_rework: list[tuple[str, int, int]]

    # Number of distinct task ids that received at least one
    # ``code-reviewer`` entry. Numerator for the Story 3 sc3 "M/N
    # tasks reached review" header.
    tasks_reached_review: int

    # Total task rows summed across every spec in the window (across
    # any status). Denominator for the Story 3 sc3 header.
    total_tasks: int

    # Median days between the first commit that creates spec.md and the
    # most recent commit on the spec's directory. ``None`` if git history
    # is unavailable (test injection of empty git log).
    specify_to_last_commit_median_days: float | None

    # Number of ``cl-N`` markers still unresolved across specs in the
    # window (snapshot of the current spec.md).
    unresolved_clarifications_count: int

    # Total distinct ``cl-N`` ids ever introduced across the specs in
    # the window (derived from git history). Reflects how often
    # ``clarify`` had to be invoked, not the current backlog. ``None``
    # when no git log was provided.
    total_clarify_iterations: int | None

    # One-line disclaimers explaining what each metric does NOT mean
    # (anti-Goodhart). Formatters render these alongside the numbers.
    disclaimer_lines: tuple[str, ...]

    # Count of specs in the window whose header ``Status:`` value is
    # outside ``CANONICAL_STATUSES`` (bucketised as "other"). In
    # aggregate mode these specs are EXCLUDED from the sample — the
    # count exists so the reader can see the sample lost specs it
    # could not classify.
    unknown_status_count: int


# ---------------------------------------------------------------------
# Header parsing
# ---------------------------------------------------------------------


def _canonicalize_status(status_raw: str) -> str:
    """Map a raw ``Status:`` value onto the canonical enum.

    The repo's real-world convention decorates the canonical value with
    provenance — e.g. ``Merged — `ed0554f` (v0.19.0)`` or
    ``PR Open — #34`` — so an exact match alone would misfile every
    merged spec as "other". A canonical value followed by a
    non-alphanumeric separator matches; ``Drafting`` does not become
    ``Draft``.
    """
    if status_raw in CANONICAL_STATUSES:
        return status_raw
    for canonical in CANONICAL_STATUSES:
        if status_raw.startswith(canonical):
            tail = status_raw[len(canonical):]
            if tail and not tail[0].isalnum():
                return canonical
    return "other"


def read_spec_header(spec_md_path: pathlib.Path) -> dict:
    """Parse the canonical header fields out of ``spec.md``.

    Returns a dict with ``spec_id`` (int), ``status`` (canonical value
    or the string ``"other"``), ``status_raw`` (the value as written in
    the file), and ``created`` (``datetime.date``).

    Raises ``ValueError`` if Spec ID or Created are missing /
    unparseable — the calculator cannot place such a spec on the
    timeline at all, so silently skipping would distort coverage.
    A non-canonical Status value is tolerated (bucketised as "other")
    because the spec still has a place on the timeline.
    """
    text = spec_md_path.read_text(encoding="utf-8")
    spec_id_m = _SPEC_ID_RE.search(text)
    status_m = _STATUS_RE.search(text)
    created_m = _CREATED_RE.search(text)

    if not spec_id_m:
        raise ValueError(f"{spec_md_path}: missing or unparseable Spec ID header")
    if not created_m:
        raise ValueError(f"{spec_md_path}: missing or unparseable Created header")

    status_raw = status_m.group(1).strip() if status_m else ""
    status = _canonicalize_status(status_raw)

    return {
        "spec_id": int(spec_id_m.group(1)),
        "status": status,
        "status_raw": status_raw,
        "created": datetime.date.fromisoformat(created_m.group(1)),
    }


# ---------------------------------------------------------------------
# Spec iteration
# ---------------------------------------------------------------------


def read_review_log(jsonl_path: pathlib.Path) -> list[dict]:
    """Return every parseable JSON object from a ``.review-log.jsonl`` file.

    Missing file → ``[]``. Empty file → ``[]``. Blank lines and lines
    that fail JSON decoding are silently dropped — the same tolerance
    ``aiadev.review_log.last_entry_from_log`` already applies. Entries
    are returned in file order, which the orchestrator guarantees to
    match dispatch order (the ``first-pass`` calculation in T004
    depends on this ordering).
    """
    if not jsonl_path.is_file():
        return []
    entries: list[dict] = []
    with jsonl_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped:
                continue
            try:
                entries.append(json.loads(stripped))
            except json.JSONDecodeError:
                continue
    return entries


def first_pass_rate_by_reviewer(
    entries: Iterable[dict],
) -> dict[str, tuple[int, int]]:
    """Compute first-pass APPROVED rate per reviewer type.

    cl-6 (resolved): "first pass" is the **first chronological entry**
    for each ``(task_id, reviewer)`` pair. Entries with
    ``task_id == "branch-review"`` collapse to a per-reviewer pair (no
    task component), since the spec/plan reviewers run once per branch,
    not per task.

    Returns ``{reviewer: (first_pass_approved_count, total_pair_count)}``.
    The denominator is the number of distinct
    ``(task_id_or_branch, reviewer)`` pairs — i.e. how many "first
    attempts" happened.
    """
    # Group entries by (group_key, reviewer), preserving file order.
    # For branch-review entries, group_key is None so all branch-review
    # entries from the same reviewer collapse into one pair.
    grouped: dict[tuple[str | None, str], list[dict]] = {}
    for entry in entries:
        reviewer = entry["reviewer"]
        task_id = entry.get("task_id")
        group_key: str | None = None if task_id == "branch-review" else task_id
        grouped.setdefault((group_key, reviewer), []).append(entry)

    # For each pair, the first entry is the first-pass attempt.
    rates: dict[str, list[int]] = {}  # reviewer -> [approved, total]
    for (_, reviewer), pair_entries in grouped.items():
        pair_entries.sort(key=lambda e: e["timestamp"])
        first = pair_entries[0]
        bucket = rates.setdefault(reviewer, [0, 0])
        bucket[1] += 1
        if first["verdict"] == "APPROVED":
            bucket[0] += 1

    return {r: (a, t) for r, (a, t) in rates.items()}


def task_rework_counts(
    entries: Iterable[dict],
) -> list[tuple[str, int, int]]:
    """Count code-reviewer rounds + CR count per task, descending by rounds.

    Only counts entries where ``reviewer == "code-reviewer"`` and
    ``task_id`` is a real task id (i.e. not ``"branch-review"``).
    A task is included only if it had at least one
    ``CHANGES_REQUESTED`` entry — pristine tasks (single APPROVED
    entry) are filtered out.

    Returns ``[(task_id, total_rounds, changes_requested_count), ...]``.
    The CR count exists so the formatter can emit the Story 3 sc1
    wording "N review rounds (M changes_requested → approved)" without
    re-walking the entries.
    """
    rounds: dict[str, int] = {}
    cr_counts: dict[str, int] = {}
    for entry in entries:
        if entry.get("reviewer") != "code-reviewer":
            continue
        task_id = entry.get("task_id")
        if not task_id or task_id == "branch-review":
            continue
        rounds[task_id] = rounds.get(task_id, 0) + 1
        if entry.get("verdict") == "CHANGES_REQUESTED":
            cr_counts[task_id] = cr_counts.get(task_id, 0) + 1

    return sorted(
        ((tid, n, cr_counts[tid]) for tid, n in rounds.items() if tid in cr_counts),
        key=lambda item: (-item[1], item[0]),
    )


def tasks_reached_review(entries: Iterable[dict]) -> int:
    """Count distinct task ids that received ≥ 1 ``code-reviewer`` entry.

    Numerator for the Story 3 sc3 "M/N tasks reached review" header.
    Entries with ``task_id == "branch-review"`` are ignored — they are
    branch-level reviews, not task-level.
    """
    seen: set[str] = set()
    for entry in entries:
        if entry.get("reviewer") != "code-reviewer":
            continue
        task_id = entry.get("task_id")
        if not task_id or task_id == "branch-review":
            continue
        seen.add(task_id)
    return len(seen)


def tasks_by_status(spec_dir: pathlib.Path) -> dict[str, int]:
    """Return ``{status: count}`` for the spec dir's ``tasks.md``.

    Delegates the actual parse to ``aiadev.tasks_status.parse`` so the
    grammar lives in exactly one place. A missing ``tasks.md`` returns
    all-zero counts rather than raising — a feature may be in spec/plan
    stage without a tasks list yet.
    """
    from aiadev import tasks_status as _tasks_status

    buckets = {"pending": 0, "in_progress": 0, "blocked": 0, "done": 0}
    tasks_md = spec_dir / "tasks.md"
    if not tasks_md.is_file():
        return buckets

    for row in _tasks_status.parse(tasks_md):
        if row.status in buckets:
            buckets[row.status] += 1
    return buckets


# ---------------------------------------------------------------------
# Git-based metrics
#
# These functions take a git log payload as a string. The CLI layer
# (``aiadev.commands.metrics``) is responsible for invoking
# ``subprocess.run(["git", "log", ...])`` and feeding the output here.
# That split lets the core be tested without a real repo and makes the
# determinism contract from spec story 2 sc3 trivial — same input,
# same output.
# ---------------------------------------------------------------------


_CL_MARKER_ADDED_RE = re.compile(r"^\+.*\[NEEDS CLARIFICATION:cl-(\d+)", re.MULTILINE)
_COMMIT_DATE_RE = re.compile(r"^Date:\s+(\d{4}-\d{2}-\d{2})", re.MULTILINE)
_DIFF_FILE_RE = re.compile(
    r"^diff --git a/(specs/(\d+)-[^/]+/spec\.md)", re.MULTILINE
)


def clarify_iteration_count(spec_id: int, git_log_output: str) -> int:
    """Count distinct ``cl-N`` markers ever introduced for a spec.

    The metric is a proxy for "how many clarify rounds the spec went
    through" — each new ``cl-N`` id added in any commit counts once.
    Markers later resolved do not subtract; the question is how often
    the author hit ambiguity, not the current backlog.

    Implementation reads the ``git log -p`` output and looks for added
    lines (``+...``) introducing a ``cl-N`` marker on a path matching
    ``specs/<NNNN-...>/spec.md`` where ``<NNNN>`` matches the requested
    spec_id. Each distinct id (``cl-1``, ``cl-2``, …) is counted once.
    """
    if not git_log_output:
        return 0
    target_prefix = f"specs/{spec_id:04d}-"

    # Walk the log diff-section by diff-section, tracking which file is
    # active. Within a section for our spec.md, count distinct added ids.
    seen: set[str] = set()
    current_is_target = False
    for line in git_log_output.splitlines():
        m = _DIFF_FILE_RE.match(line)
        if m:
            current_is_target = m.group(1).startswith(target_prefix)
            continue
        if not current_is_target:
            continue
        m2 = _CL_MARKER_ADDED_RE.match(line)
        if m2:
            seen.add(m2.group(1))
    return len(seen)


def specify_to_last_commit_days(spec_id: int, git_log_output: str) -> int | None:
    """Days between the earliest and latest commit that touched the spec dir.

    Returns ``None`` when the log contains no commit referencing the
    spec — the caller's report leaves the field as null rather than
    forcing a sentinel.

    Expected input: ``git log --date=short --name-only --no-patch -- specs/``.
    Each commit block is ``commit <sha>`` + an ``Author:`` line +
    ``Date: YYYY-MM-DD`` + a blank line + the commit message body
    (4-space indented) + a blank line + the touched paths (one per
    line, flush-left).

    The parser distinguishes path lines from message-body lines by
    column-zero match — ``--name-only`` paths are flush-left, while
    message-body lines are 4-space-indented. Earlier versions used
    ``line.strip().startswith(target_prefix)`` which silently
    misclassified a commit body that *mentioned* a spec path as
    touching it. Regression: a commit whose body said
    ``specs/0001-x/...`` would attribute the commit's date to spec 1.
    """
    if not git_log_output:
        return None
    target_prefix = f"specs/{spec_id:04d}-"

    dates: list[datetime.date] = []
    current_date: datetime.date | None = None
    for line in git_log_output.splitlines():
        if line.startswith("commit "):
            current_date = None
            continue
        m = _COMMIT_DATE_RE.match(line)
        if m:
            current_date = datetime.date.fromisoformat(m.group(1))
            continue
        if current_date is None:
            continue
        # Only flush-left lines come from the ``--name-only`` block.
        # Any indentation marks a commit-message-body line, which must
        # not influence the touched-path computation.
        if line.startswith(target_prefix):
            dates.append(current_date)

    if not dates:
        return None
    return (max(dates) - min(dates)).days


# ---------------------------------------------------------------------
# Disclaimer lines (anti-Goodhart)
# ---------------------------------------------------------------------

DISCLAIMER_LINES: tuple[str, ...] = (
    "first-pass rate alta NÃO implica qualidade — pode indicar reviewer permissivo ou specs triviais.",
    "tasks com rework NÃO implica engenheiro ruim — pode indicar spec ambígua que só virou clara no review.",
    "coverage< 100% reflete specs pré-cutoff (≤ 0014) sem .review-log.jsonl, não falha de processo.",
    "specify→merge em dias NÃO mede esforço — uma spec parada 30 dias esperando aprovação conta igual a 30 dias de trabalho.",
    "n=N pequeno (N<10) significa leitura precoce; tendência ainda não está estabelecida.",
)


def _find_feature_dir(workspace: pathlib.Path, feature: str) -> pathlib.Path | None:
    """Resolve a feature slug to a spec dir, like ``aiadev preflight`` does.

    Accepts both ``0001-x`` (exact dir name) and ``x`` (slug without
    the numeric prefix).
    """
    specs_dir = workspace / "specs"
    if not specs_dir.is_dir():
        return None
    direct = specs_dir / feature
    if direct.is_dir():
        return direct
    for child in specs_dir.iterdir():
        if child.is_dir() and child.name.endswith("-" + feature):
            return child
    return None


def build_report(
    workspace: pathlib.Path,
    *,
    feature: str | None = None,
    since: datetime.date | None = None,
    until: datetime.date | None = None,
    now: datetime.date | None = None,
    git_log_output: str = "",
) -> "MetricsReport":
    """Top-level composer: walk specs, aggregate, return a ``MetricsReport``.

    ``feature``: when set, restricts the aggregation to a single spec
    (window and status checks are bypassed). Otherwise every spec whose
    ``Created:`` falls in ``[since, until]`` AND whose header Status is
    in ``AGGREGATE_STATUSES`` is aggregated.

    ``now``: the calendar reference used to compute defaults for
    ``since`` (``now − 90 days``) and ``until`` (``now``). Required to
    be injected for the determinism contract (Story 2 sc3): two runs
    with the same ``now`` produce byte-identical output even when the
    system clock has rolled. When ``None``, falls back to
    ``datetime.date.today()`` — convenient for ad-hoc invocation, but
    callers that care about reproducibility (CI snapshots, historical
    checkouts) MUST pass the value explicitly.

    ``git_log_output``: pre-fetched ``git log -p --name-only`` payload
    spanning the relevant specs. The default empty string makes the
    git-derived metrics (``clarify_iteration_count``,
    ``specify_to_last_commit_days``) skip silently — the report still
    builds. The CLI layer is responsible for collecting this string
    via ``subprocess`` (T011).
    """
    if now is None:
        now = datetime.date.today()
    if since is None:
        since = now - datetime.timedelta(days=90)
    if until is None:
        until = now

    if feature is not None:
        feature_dir = _find_feature_dir(workspace, feature)
        spec_dirs = [feature_dir] if feature_dir is not None else []
    else:
        spec_dirs = list(iter_specs_in_window(workspace, since=since, until=until))

    aggregate = feature is None

    # Resolve headers first. Aggregate mode filters the sample to
    # ``AGGREGATE_STATUSES`` (spec success criterion 2): in-flight
    # specs (Draft / In review / Approved) drop out silently, while
    # non-canonical statuses drop out but are surfaced via
    # ``unknown_status_count``. ``--feature`` mode bypasses the filter —
    # the caller named the spec explicitly.
    unknown_status = 0
    included: list[tuple[pathlib.Path, dict]] = []
    for spec_dir in spec_dirs:
        try:
            header = read_spec_header(spec_dir / "spec.md")
        except ValueError:
            continue
        if header["status"] == "other":
            unknown_status += 1
            if aggregate:
                continue
        elif aggregate and header["status"] not in AGGREGATE_STATUSES:
            continue
        included.append((spec_dir, header))

    n = len(included)
    specs_with_log = 0
    tasks_buckets = {"pending": 0, "in_progress": 0, "blocked": 0, "done": 0}
    unresolved_cl_total = 0
    spec_to_commit_samples: list[int] = []
    historical_cl_total = 0
    rates_acc: dict[str, list[int]] = {}
    rework: list[tuple[str, int, int]] = []
    reached = 0

    for spec_dir, header in included:
        log_path = spec_dir / ".review-log.jsonl"
        entries: list[dict] = []
        if log_path.exists():
            specs_with_log += 1
            entries = read_review_log(log_path)

        # Review-trail metrics are computed per spec and merged, never
        # over a pooled entry list: entries carry no spec identifier,
        # so pooling would collide ``(task_id, reviewer)`` pairs from
        # different features (every spec has a T003; every branch has
        # a ``branch-review`` sentinel) and undercount first attempts.
        for reviewer, (approved, total) in first_pass_rate_by_reviewer(entries).items():
            bucket = rates_acc.setdefault(reviewer, [0, 0])
            bucket[0] += approved
            bucket[1] += total
        # In aggregate mode, qualify task ids with the spec dir so two
        # specs' T003 rows stay distinguishable in the listing.
        prefix = f"{spec_dir.name}/" if aggregate else ""
        rework.extend(
            (prefix + task_id, rounds, cr_count)
            for task_id, rounds, cr_count in task_rework_counts(entries)
        )
        reached += tasks_reached_review(entries)

        for tid_status, count in tasks_by_status(spec_dir).items():
            tasks_buckets[tid_status] += count

        # Count surviving ``cl-N`` markers in the current spec.md as
        # "unresolved clarifications" — the spec validator already
        # forbids them downstream but the snapshot is useful while
        # specs are in draft.
        text = (spec_dir / "spec.md").read_text(encoding="utf-8")
        unresolved_cl_total += len(re.findall(r"\[NEEDS CLARIFICATION:cl-\d+", text))

        if git_log_output:
            sample = specify_to_last_commit_days(header["spec_id"], git_log_output)
            if sample is not None:
                spec_to_commit_samples.append(sample)
            historical_cl_total += clarify_iteration_count(
                header["spec_id"], git_log_output
            )

    rework.sort(key=lambda item: (-item[1], item[0]))
    rates = {r: (a, t) for r, (a, t) in rates_acc.items()}
    total_tasks = sum(tasks_buckets.values())
    coverage = round(100.0 * specs_with_log / n, 1) if n else 0.0
    median = statistics.median(spec_to_commit_samples) if spec_to_commit_samples else None

    return MetricsReport(
        window=(since, until),
        n_specs_in_window=n,
        coverage_percent=coverage,
        per_reviewer_first_pass_rate=rates,
        tasks_by_status=tasks_buckets,
        tasks_with_rework=rework,
        tasks_reached_review=reached,
        total_tasks=total_tasks,
        specify_to_last_commit_median_days=median,
        unresolved_clarifications_count=unresolved_cl_total,
        total_clarify_iterations=historical_cl_total if git_log_output else None,
        disclaimer_lines=DISCLAIMER_LINES,
        unknown_status_count=unknown_status,
    )


def iter_specs_in_window(
    workspace: pathlib.Path,
    *,
    since: datetime.date,
    until: datetime.date,
) -> Iterator[pathlib.Path]:
    """Yield ``specs/<NNNN-slug>/`` dirs whose spec.md ``Created:`` falls in ``[since, until]``.

    ``workspace`` is the repo root containing a top-level ``specs/`` dir.
    A workspace without a ``specs/`` directory yields nothing (does not
    raise). Spec directories whose ``spec.md`` cannot be parsed (no Spec
    ID or no Created) are silently skipped — they will be reflected via
    ``unknown_status_count`` only if they made it past header parse.
    """
    specs_dir = workspace / "specs"
    if not specs_dir.is_dir():
        return
    for child in sorted(specs_dir.iterdir()):
        spec_md = child / "spec.md"
        if not spec_md.is_file():
            continue
        try:
            header = read_spec_header(spec_md)
        except ValueError:
            continue
        if since <= header["created"] <= until:
            yield child
