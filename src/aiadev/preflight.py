"""Pre-flight checks for the aiadev pipeline.

A single read-only entry point — :func:`check` — verifies that a feature
directory holds the upstream artifacts a downstream pipeline skill
requires. Both the in-skill call-out and the ``aiadev preflight`` CLI
share this implementation so the diagnostics are byte-identical.

Spec: ``specs/0010-pipeline-preflight-checks/spec.md``.
"""
from __future__ import annotations

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
            PreflightIssue("pre-flight: spec.md missing — run /aiadev:specify first")
        )
    elif skill == "plan" and spec_path.is_file():
        spec_text = spec_path.read_text(encoding="utf-8")
        marker_count = _count_needs_clarification(spec_text)
        if marker_count:
            issues.append(
                PreflightIssue(
                    f"pre-flight: spec.md has {marker_count} unresolved "
                    "[NEEDS CLARIFICATION] markers — run /aiadev:clarify first"
                )
            )
        for anchor in _missing_anchors(spec_text, SPEC_ANCHORS):
            issues.append(
                PreflightIssue(
                    f"pre-flight: spec.md missing required section anchor {anchor!r}"
                )
            )

    if skill == "implement" and not (feature_dir / "tasks.md").is_file():
        issues.append(
            PreflightIssue("pre-flight: tasks.md missing — run /aiadev:tasks first")
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
                    "run /aiadev:requesting-code-review first"
                )
            )

    if not _should_abort(env):
        issues = [PreflightIssue(i.message, would_abort=False) for i in issues]

    return issues


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
    return text.count("[NEEDS CLARIFICATION")


def _missing_anchors(text: str, anchors: tuple[str, ...]) -> list[str]:
    return [a for a in anchors if f"<!-- section: {a} -->" not in text]


def _language_of(text: str) -> str:
    """Extract the language tag from a ``**Language:** <tag>`` header."""
    import re

    match = re.search(r"\*\*Language:\*\*\s*([A-Za-z][A-Za-z0-9_-]*)", text)
    return match.group(1) if match else ""


def _branch_header_of(text: str) -> str:
    """Extract the branch tag from a ``**Branch:** \`<tag>\``` header."""
    import re

    match = re.search(r"\*\*Branch:\*\*\s*`([^`]+)`", text)
    return match.group(1) if match else ""


def _review_is_approved(repo_root: Path | None) -> bool:
    if repo_root is None:
        repo_root = Path.cwd()
    review_path = repo_root / ".aiadev" / "review.yaml"
    if not review_path.is_file():
        return False

    import yaml  # local import keeps the module import-cheap

    payload = yaml.safe_load(review_path.read_text(encoding="utf-8")) or {}
    return payload.get("status") == "approved"
