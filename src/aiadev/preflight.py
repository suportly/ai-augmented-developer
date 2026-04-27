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
        marker_count = _count_needs_clarification(spec_path.read_text(encoding="utf-8"))
        if marker_count:
            issues.append(
                PreflightIssue(
                    f"pre-flight: spec.md has {marker_count} unresolved "
                    "[NEEDS CLARIFICATION] markers — run /aiadev:clarify first"
                )
            )

    if skill == "implement" and not (feature_dir / "tasks.md").is_file():
        issues.append(
            PreflightIssue("pre-flight: tasks.md missing — run /aiadev:tasks first")
        )

    if skill == "finishing-a-branch":
        if not _review_is_approved(repo_root):
            issues.append(
                PreflightIssue(
                    "pre-flight: review approval missing — "
                    "run /aiadev:requesting-code-review first"
                )
            )

    return issues


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


def _review_is_approved(repo_root: Path | None) -> bool:
    if repo_root is None:
        repo_root = Path.cwd()
    review_path = repo_root / ".aiadev" / "review.yaml"
    if not review_path.is_file():
        return False

    import yaml  # local import keeps the module import-cheap

    payload = yaml.safe_load(review_path.read_text(encoding="utf-8")) or {}
    return payload.get("status") == "approved"
