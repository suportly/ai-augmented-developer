"""Unit tests for ``aiadev.preflight``.

Each test maps 1-1 to an acceptance scenario in
``specs/0010-pipeline-preflight-checks/spec.md``. See the task list for
the exact mapping.
"""
from __future__ import annotations

import pathlib

import pytest


def _write(path: pathlib.Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


@pytest.fixture
def feature_dir(tmp_path: pathlib.Path) -> pathlib.Path:
    """A canonical feature dir with spec.md, plan.md, tasks.md present.

    Tests delete or mutate the artifacts they care about.
    """
    root = tmp_path / "specs" / "0010-pipeline-preflight-checks"
    _write(
        root / "spec.md",
        "# Feature\n\n"
        "**Branch:** `feature/pipeline-preflight-checks`\n"
        "**Language:** en\n\n"
        "<!-- section: Problem -->\n## Problem\n\nx\n\n"
        "<!-- section: Users and stakeholders -->\n## Users and stakeholders\n\nx\n\n"
        "<!-- section: Success criteria -->\n## Success criteria\n\nx\n\n"
        "<!-- section: Non-goals -->\n## Non-goals\n\nx\n\n"
        "<!-- section: User stories -->\n## User stories\n\nx\n\n"
        "<!-- section: Clarifications -->\n## Clarifications\n\nx\n\n"
        "<!-- section: Data touched -->\n## Data touched\n\nx\n\n"
        "<!-- section: Out-of-band effects -->\n## Out-of-band effects\n\nx\n\n"
        "<!-- section: Open risks -->\n## Open risks\n\nx\n\n"
        "<!-- section: Traceability -->\n## Traceability\n\nx\n",
    )
    _write(
        root / "plan.md",
        "# Plan\n\n"
        "**Branch:** `feature/pipeline-preflight-checks`\n"
        "**Language:** en\n",
    )
    _write(root / "tasks.md", "# Tasks\n\n**Language:** en\n")
    return root


def _stub_branch(name: str):
    return lambda: name


# -- T001: Story 1 scenario 1 -------------------------------------------------


def test_missing_tasks_md_emits_run_tasks_message(feature_dir: pathlib.Path) -> None:
    from aiadev.preflight import check

    (feature_dir / "tasks.md").unlink()

    issues = check(
        "implement",
        feature_dir,
        env={},
        current_branch=_stub_branch("feature/pipeline-preflight-checks"),
    )

    messages = [issue.message for issue in issues]
    assert "pre-flight: tasks.md missing — run /aiadev:tasks first" in messages


# -- T002: Story 1 scenario 2 -------------------------------------------------


@pytest.mark.parametrize(
    "skill",
    [
        "clarify",
        "plan",
        "tasks",
        "implement",
        "analyze",
        "requesting-code-review",
        "finishing-a-branch",
    ],
)
def test_missing_spec_aborts_all_downstream_skills(
    feature_dir: pathlib.Path, skill: str
) -> None:
    from aiadev.preflight import check

    (feature_dir / "spec.md").unlink()

    issues = check(
        skill,
        feature_dir,
        env={},
        current_branch=_stub_branch("feature/pipeline-preflight-checks"),
    )

    messages = [issue.message for issue in issues]
    assert "pre-flight: spec.md missing — run /aiadev:specify first" in messages


def test_specify_skill_does_not_require_spec_md(feature_dir: pathlib.Path) -> None:
    from aiadev.preflight import check

    (feature_dir / "spec.md").unlink()

    issues = check(
        "specify",
        feature_dir,
        env={},
        current_branch=_stub_branch("feature/pipeline-preflight-checks"),
    )

    assert not any("spec.md missing" in issue.message for issue in issues)


# -- T003: Story 1 scenario 3 -------------------------------------------------


def test_needs_clarification_markers_block_plan(feature_dir: pathlib.Path) -> None:
    from aiadev.preflight import check

    spec = feature_dir / "spec.md"
    spec.write_text(
        spec.read_text(encoding="utf-8")
        + "\n[NEEDS CLARIFICATION: foo?]\n[NEEDS CLARIFICATION: bar?]\n",
        encoding="utf-8",
    )

    issues = check(
        "plan",
        feature_dir,
        env={},
        current_branch=_stub_branch("feature/pipeline-preflight-checks"),
    )

    messages = [issue.message for issue in issues]
    assert (
        "pre-flight: spec.md has 2 unresolved [NEEDS CLARIFICATION] markers — "
        "run /aiadev:clarify first"
    ) in messages
