"""Pre-flight checks for the aiadev pipeline.

A single read-only entry point — :func:`check` — verifies that a feature
directory holds the upstream artifacts a downstream pipeline skill
requires. Both the in-skill call-out and the ``aiadev preflight`` CLI
share this implementation so the diagnostics are byte-identical.

Spec: ``specs/0010-pipeline-preflight-checks/spec.md``.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Mapping

PIPELINE_SKILLS = (
    "specify",
    "clarify",
    "plan",
    "tasks",
    "implement",
    "analyze",
    "requesting-code-review",
    "finishing-a-branch",
)

# Skills that consume an upstream spec.md. ``specify`` produces it and is
# therefore exempt.
_REQUIRES_SPEC = tuple(s for s in PIPELINE_SKILLS if s != "specify")

# Skills that consume plan.md (i.e. run after `plan`).
_REQUIRES_PLAN = ("tasks", "implement", "analyze", "finishing-a-branch")

# Skills that consume tasks.md (i.e. run after `tasks`).
_REQUIRES_TASKS = ("implement", "analyze", "finishing-a-branch")

# Required ``<!-- section: ... -->`` anchors per artifact. These are pinned
# literals — ``test_every_anchor_exists_in_its_template`` round-trips them
# against the live templates so drift fails CI.
SPEC_ANCHORS: tuple[str, ...] = (
    "Problem",
    "Users and stakeholders",
    "Success criteria",
    "Non-goals",
    "User stories",
    "Clarifications",
    "Data touched",
    "Out-of-band effects",
    "Open risks",
    "Traceability",
)
PLAN_ANCHORS: tuple[str, ...] = ()
TASKS_ANCHORS: tuple[str, ...] = ()


@dataclass(frozen=True)
class PreflightIssue:
    """A single pre-flight diagnostic.

    ``message`` is the literal string written to stderr / returned by the
    CLI; ``would_abort`` is ``True`` for a hard failure and ``False`` when
    ``AIADEV_PREFLIGHT=warn`` downgrades the abort to a warning.
    """

    message: str
    would_abort: bool = True


def check(
    skill: str,
    feature_dir: Path,
    *,
    env: Mapping[str, str] | None = None,
    current_branch: Callable[[], str] | None = None,
    repo_root: Path | None = None,
) -> list[PreflightIssue]:
    """Return the pre-flight issues for ``skill`` against ``feature_dir``.

    An empty list means the feature directory satisfies the rules for
    ``skill``. ``env`` defaults to the process environment; ``current_branch``
    defaults to a git ``rev-parse`` shell-out (introduced in T005).
    """

    issues: list[PreflightIssue] = []

    feature_slug = feature_dir.name
    branch_name = (current_branch or _git_current_branch)()
    expected_branch = f"feature/{_strip_numeric_prefix(feature_slug)}"
    if branch_name and branch_name != expected_branch and branch_name != f"feature/{feature_slug}":
        issues.append(
            PreflightIssue(
                f"pre-flight: git branch {branch_name!r} does not match feature "
                f"directory {feature_slug!r}"
            )
        )

    spec_path = feature_dir / "spec.md"
    if skill in _REQUIRES_SPEC and not spec_path.is_file():
        issues.append(
            PreflightIssue("pre-flight: spec.md missing — run /aia:specify first")
        )
    elif skill == "plan" and spec_path.is_file():
        spec_text = spec_path.read_text(encoding="utf-8")
        marker_count = _count_needs_clarification(spec_text)
        if marker_count:
            issues.append(
                PreflightIssue(
                    f"pre-flight: spec.md has {marker_count} unresolved "
                    "[NEEDS CLARIFICATION] markers — run /aia:clarify first"
                )
            )
        for anchor in _missing_anchors(spec_text, SPEC_ANCHORS):
            issues.append(
                PreflightIssue(
                    f"pre-flight: spec.md missing required section anchor {anchor!r}"
                )
            )
        for number in _bad_assumptions(spec_text):
            issues.append(
                PreflightIssue(
                    f"pre-flight: spec.md Assumptions item {number} "
                    "lacks [impact: low|medium]"
                )
            )

    if skill in _REQUIRES_PLAN and not (feature_dir / "plan.md").is_file():
        issues.append(
            PreflightIssue("pre-flight: plan.md missing — run /aia:plan first")
        )

    if skill in _REQUIRES_TASKS and not (feature_dir / "tasks.md").is_file():
        issues.append(
            PreflightIssue("pre-flight: tasks.md missing — run /aia:tasks first")
        )

    if skill == "tasks" and spec_path.is_file():
        plan_path = feature_dir / "plan.md"
        if plan_path.is_file():
            plan_text = plan_path.read_text(encoding="utf-8")
            spec_lang = _language_of(spec_path.read_text(encoding="utf-8"))
            plan_lang = _language_of(plan_text)
            if spec_lang and plan_lang and spec_lang != plan_lang:
                issues.append(
                    PreflightIssue(
                        f"pre-flight: language mismatch — spec.md={spec_lang}, "
                        f"plan.md={plan_lang}"
                    )
                )
            plan_branch = _branch_header_of(plan_text)
            if plan_branch and plan_branch != expected_branch and plan_branch != f"feature/{feature_slug}":
                issues.append(
                    PreflightIssue(
                        f"pre-flight: plan.md branch header {plan_branch!r} does not "
                        f"match feature directory {feature_slug!r}"
                    )
                )

    if skill == "finishing-a-branch":
        if not _review_is_approved(repo_root):
            issues.append(
                PreflightIssue(
                    "pre-flight: review approval missing — "
                    "run /aia:requesting-code-review first"
                )
            )

    if skill == "requesting-code-review":
        violation = _last_review_violates_zero_findings_halt(feature_dir)
        if violation is not None:
            issues.append(PreflightIssue(violation))

    if skill == "implement" and spec_path.is_file():
        tasks_path = feature_dir / "tasks.md"
        if tasks_path.is_file():
            issues.extend(_coverage_issues(feature_dir, spec_path, tasks_path, repo_root))

    if skill == "implement":
        issues.extend(_checklist_issues(feature_dir))

    if skill == "implement" and spec_path.is_file() and not (feature_dir / "design.md").is_file():
        from .pipeline_state import declares_ui

        try:
            ui = declares_ui(spec_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            ui = False
        if ui:
            issues.append(
                PreflightIssue(
                    "pre-flight: spec.md declares **UI:** yes but design.md is missing — "
                    "consider /aia:design (not blocking)",
                    would_abort=False,
                )
            )

    if not _should_abort(env):
        issues = [PreflightIssue(i.message, would_abort=False) for i in issues]

    return issues


# Artifact template each skill produces (``templates/<name>``); other skills
# produce none and report ``template: null``.
_SKILL_TEMPLATE = {
    "specify": "spec-template.md",
    "plan": "plan-template.md",
    "tasks": "tasks-template.md",
}


def build_payload(
    skill: str,
    feature_dir: Path,
    issues: list[PreflightIssue],
    repo_root: Path,
) -> dict[str, object]:
    """Structured context for ``aiadev preflight --format json``.

    ``ok`` is true when no issue ``would_abort`` (so ``AIADEV_PREFLIGHT=warn``
    yields ``ok: true`` with the downgraded issues still listed). Paths are
    POSIX strings relative to ``repo_root`` when possible.
    """

    def rel(path: Path) -> str:
        try:
            return path.relative_to(repo_root).as_posix()
        except ValueError:
            return path.as_posix()

    def existing(name: str) -> str | None:
        path = feature_dir / name
        return rel(path) if path.is_file() else None

    checklists_dir = feature_dir / "checklists"
    checklists = (
        sorted(rel(p) for p in checklists_dir.glob("*.md") if p.is_file())
        if checklists_dir.is_dir()
        else []
    )
    template_name = _SKILL_TEMPLATE.get(skill)
    template_path = repo_root / "templates" / template_name if template_name else None
    return {
        "skill": skill,
        "feature": feature_dir.name,
        "feature_dir": rel(feature_dir),
        "ok": not any(i.would_abort for i in issues),
        "issues": [
            {"message": i.message, "would_abort": i.would_abort} for i in issues
        ],
        "docs": {
            "spec": existing("spec.md"),
            "plan": existing("plan.md"),
            "tasks": existing("tasks.md"),
            "checklists": checklists,
        },
        "template": rel(template_path)
        if template_path is not None and template_path.is_file()
        else None,
        "test_command": _detect_test_command(repo_root),
    }


def _detect_test_command(repo_root: Path) -> str | None:
    """Test command reported by ``project_introspect``, or ``None``.

    Introspection reads manifests from disk; an unreadable or non-UTF-8 file
    must not break the preflight, so detection failures yield ``None``.
    """
    from aiadev import project_introspect

    try:
        report = project_introspect.introspect(repo_root)
    except (OSError, ValueError):
        return None
    for command in report.run_commands:
        if command.split()[-1:] == ["test"] or " test " in f"{command} ":
            return command
    return None


def _coverage_issues(
    feature_dir: Path, spec_path: Path, tasks_path: Path, repo_root: Path | None
) -> list[PreflightIssue]:
    """Scenario-to-task coverage as preflight issues (D4); never raises."""
    from . import spec_coverage

    exceptions_path = (repo_root or Path.cwd()) / "docs" / "coverage-exceptions.yaml"
    try:
        exceptions = spec_coverage.load_exceptions(exceptions_path)
    except (OSError, ValueError) as exc:
        return [PreflightIssue(f"pre-flight: cannot read coverage-exceptions.yaml — {exc}")]
    if feature_dir.name in exceptions:
        return []
    try:
        if "Spec scenarios" not in tasks_path.read_text(encoding="utf-8"):
            return [
                PreflightIssue(
                    "pre-flight: tasks.md has no Spec scenarios lines (legacy format) — "
                    "scenario coverage not checked",
                    would_abort=False,
                )
            ]
        found = spec_coverage.check(spec_path, tasks_path)
    except (OSError, ValueError) as exc:  # UnicodeDecodeError is a ValueError
        return [PreflightIssue(f"pre-flight: cannot check scenario coverage in tasks.md — {exc}")]
    out: list[PreflightIssue] = []
    for item in found:
        if item.kind == "uncovered_scenario":
            text = (
                f"scenario {item.ref} is not covered by any task — "
                "add it to a task's Spec scenarios"
            )
        elif item.kind == "orphan_task":
            text = f"{item.ref} cites no scenario, story or success criterion"
        else:
            text = item.message
        out.append(PreflightIssue(f"pre-flight: {text}"))
    return out


def _table_cells(line: str) -> list[str] | None:
    """Cells of a markdown table row, or ``None`` for non-rows and separators.

    Edge pipes are optional and ``\\|`` stays inside its cell.
    """
    import re

    text = line.strip()
    if "|" not in text:
        return None
    if text.startswith("|"):
        text = text[1:]
    if text.endswith("|") and not text.endswith("\\|"):
        text = text[:-1]
    cells = [c.replace("\\|", "|").strip() for c in re.split(r"(?<!\\)\|", text)]
    if all(c and set(c) <= set("-: ") for c in cells):
        return None
    return cells


_FAIL_PREFIXES = ("FAIL", "❌", "✗")


def _checklist_issues(feature_dir: Path) -> list[PreflightIssue]:
    """Block on a FAIL check with no owner task in ``tasks.md`` (D3); never raises.

    Checks table = header with ``#`` and ``Status``; failures table = header
    with ``#`` and ``Owner task``. The template placeholder row (status
    ``PASS / FAIL / N/A``) is not a FAIL.
    """
    import re

    checklists = feature_dir / "checklists"
    if not checklists.is_dir():
        return []
    try:
        tasks_text = (feature_dir / "tasks.md").read_text(encoding="utf-8")
    except FileNotFoundError:
        tasks_text = ""
    except (OSError, ValueError) as exc:
        return [PreflightIssue(f"pre-flight: cannot read tasks.md for checklists — {exc}")]
    task_ids = set(re.findall(r"^###\s+(T\d+)\b", tasks_text, re.MULTILINE))

    out: list[PreflightIssue] = []
    for path in sorted(checklists.glob("*.md")):
        label = f"checklists/{path.name}"
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except (OSError, ValueError) as exc:
            out.append(PreflightIssue(f"pre-flight: cannot read {label} — {exc}"))
            continue
        fails: list[str] = []
        owners: dict[str, str] = {}
        mode = ""
        width = column = 0
        in_fence = False
        for line in lines:
            if line.lstrip().startswith("```"):
                in_fence = not in_fence
                continue
            if in_fence or not line.strip():
                continue
            cells = _table_cells(line)
            if cells is None:
                if "|" not in line:
                    mode = ""  # prose or heading ends the table
                continue
            names = [c.lower() for c in cells]
            if "#" in names and "status" in names:
                mode, width, column = "checks", len(cells), names.index("status")
                continue
            if "#" in names and "owner task" in names:
                mode, width, column = "failed", len(cells), names.index("owner task")
                continue
            if not mode:
                continue
            if len(cells) < width:
                out.append(PreflightIssue(f"pre-flight: {label} has a malformed table row"))
                continue
            number = cells[0].strip().lstrip("#").strip()
            if mode == "checks":
                status = re.sub(r"[*`\s]", "", cells[column]).upper()
                if status.startswith(_FAIL_PREFIXES):
                    fails.append(number)
            elif number:
                owners[number] = cells[column]
        for number in fails:
            owner_cell = owners.get(number, "")
            owner_ids = re.findall(r"T\d+", owner_cell)
            if not owner_ids:
                out.append(PreflightIssue(
                    f"pre-flight: {label} check #{number} is FAIL without an owner "
                    "task in tasks.md"
                ))
            elif not any(t in task_ids for t in owner_ids):
                out.append(PreflightIssue(
                    f"pre-flight: {label} check #{number} is FAIL and its owner task "
                    f"{owner_ids[0]} is not in tasks.md"
                ))
    return out


def _should_abort(env: Mapping[str, str] | None) -> bool:
    """Return ``True`` unless ``AIADEV_PREFLIGHT=warn`` (case-insensitive)."""
    if env is None:
        import os

        env = os.environ
    return env.get("AIADEV_PREFLIGHT", "").strip().lower() != "warn"


def _strip_numeric_prefix(slug: str) -> str:
    """Drop a leading ``NNNN-`` from a feature directory name."""
    head, sep, tail = slug.partition("-")
    if sep and head.isdigit():
        return tail
    return slug


def _git_current_branch() -> str:
    import subprocess

    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        return ""
    return result.stdout.strip() if result.returncode == 0 else ""


def _count_needs_clarification(text: str) -> int:
    from .pipeline_state import count_needs_clarification

    return count_needs_clarification(text)


_IMPACT_RE = re.compile(r"\[impact:\s*([^\]]*?)\s*\]", re.IGNORECASE)


def _bad_assumptions(text: str) -> list[int]:
    """1-based numbers of ``## Assumptions`` bullets without a valid impact tag.

    The section is optional; fenced blocks are ignored and the section ends at
    the next heading. A bullet is valid with non-empty text plus exactly an
    ``[impact: low]`` or ``[impact: medium]`` marker.
    """
    bullets: list[str] = []
    in_section = in_fence = False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if line.startswith("#"):
            in_section = line.strip().lower() == "## assumptions"
            continue
        if not in_section:
            continue
        stripped = line.strip()
        if stripped[:1] in {"-", "*"} and (len(stripped) == 1 or stripped[1] == " "):
            bullets.append(stripped[1:].strip())
        elif stripped and bullets and line[:1].isspace():
            bullets[-1] += " " + stripped
    bad: list[int] = []
    for number, bullet in enumerate(bullets, start=1):
        tags = _IMPACT_RE.findall(bullet)
        body = _IMPACT_RE.sub("", bullet).strip()
        if not body or len(tags) != 1 or tags[0].lower() not in {"low", "medium"}:
            bad.append(number)
    return bad


def _missing_anchors(text: str, anchors: tuple[str, ...]) -> list[str]:
    return [a for a in anchors if f"<!-- section: {a} -->" not in text]


def _language_of(text: str) -> str:
    """Extract the language tag from a ``**Language:** <tag>`` header."""
    import re

    match = re.search(r"\*\*Language:\*\*\s*([A-Za-z][A-Za-z0-9_-]*)", text)
    return match.group(1) if match else ""


def _branch_header_of(text: str) -> str:
    r"""Extract the branch tag from a ``**Branch:** `<tag>` `` header."""
    import re

    match = re.search(r"\*\*Branch:\*\*\s*`([^`]+)`", text)
    return match.group(1) if match else ""


def _last_review_violates_zero_findings_halt(feature_dir: Path) -> str | None:
    """Return a diagnostic if the last review entry breaks zero-findings-halt.

    Story 3 sc1/sc2 from ``specs/0014-bmad-inspired-evolutions/spec.md``:
    an APPROVED reviewer output on a non-trivial change MUST carry the
    ``### Why no issues`` block. The reviewer subagents record each run
    as a JSON line in ``<feature_dir>/.review-log.jsonl``; we inspect the
    last valid entry. Returns ``None`` when there is nothing to flag
    (no log, last entry is CHANGES_REQUESTED, or APPROVED with the
    block present).
    """
    from .review_log import last_entry_from_log

    last_valid = last_entry_from_log(feature_dir / ".review-log.jsonl")
    if last_valid is None:
        return None
    if last_valid.get("verdict") != "APPROVED":
        return None
    if last_valid.get("has_why_no_issues_block"):
        return None
    return (
        "pre-flight: last APPROVED review missing the `### Why no issues` "
        "block — re-dispatch the reviewer with adversarial framing"
    )


def _review_is_approved(repo_root: Path | None) -> bool:
    if repo_root is None:
        repo_root = Path.cwd()
    review_path = repo_root / ".aiadev" / "review.yaml"
    if not review_path.is_file():
        return False

    import yaml  # local import keeps the module import-cheap

    payload = yaml.safe_load(review_path.read_text(encoding="utf-8")) or {}
    return payload.get("status") == "approved"
