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
) -> list[PreflightIssue]:
    """Return the pre-flight issues for ``skill`` against ``feature_dir``.

    An empty list means the feature directory satisfies the rules for
    ``skill``. ``env`` defaults to the process environment; ``current_branch``
    defaults to a git ``rev-parse`` shell-out (introduced in T005).
    """

    issues: list[PreflightIssue] = []

    if skill == "implement" and not (feature_dir / "tasks.md").is_file():
        issues.append(
            PreflightIssue("pre-flight: tasks.md missing — run /aiadev:tasks first")
        )

    return issues
