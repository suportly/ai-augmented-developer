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


# -- T004: Story 1 scenario 4 -------------------------------------------------


def _run_finishing(feature_dir: pathlib.Path, repo_root: pathlib.Path):
    from aiadev.preflight import check

    return check(
        "finishing-a-branch",
        feature_dir,
        env={},
        current_branch=_stub_branch("feature/pipeline-preflight-checks"),
        repo_root=repo_root,
    )


def test_missing_review_yaml_blocks_finishing_branch(
    feature_dir: pathlib.Path, tmp_path: pathlib.Path
) -> None:
    issues = _run_finishing(feature_dir, repo_root=tmp_path)
    messages = [i.message for i in issues]
    assert (
        "pre-flight: review approval missing — run /aiadev:requesting-code-review first"
        in messages
    )


def test_changes_requested_review_yaml_blocks_finishing_branch(
    feature_dir: pathlib.Path, tmp_path: pathlib.Path
) -> None:
    review = tmp_path / ".aiadev" / "review.yaml"
    review.parent.mkdir(parents=True, exist_ok=True)
    review.write_text(
        "status: changes_requested\ntimestamp: 2026-04-21T00:00:00Z\nreason: x\n",
        encoding="utf-8",
    )

    issues = _run_finishing(feature_dir, repo_root=tmp_path)
    messages = [i.message for i in issues]
    assert (
        "pre-flight: review approval missing — run /aiadev:requesting-code-review first"
        in messages
    )


def test_approved_review_yaml_lets_finishing_branch_pass(
    feature_dir: pathlib.Path, tmp_path: pathlib.Path
) -> None:
    review = tmp_path / ".aiadev" / "review.yaml"
    review.parent.mkdir(parents=True, exist_ok=True)
    review.write_text(
        "status: approved\ntimestamp: 2026-04-21T00:00:00Z\n",
        encoding="utf-8",
    )

    issues = _run_finishing(feature_dir, repo_root=tmp_path)
    assert not any("review approval missing" in i.message for i in issues)


# -- T005: Story 1 scenario 5 -------------------------------------------------


def test_branch_slug_mismatch_aborts(feature_dir: pathlib.Path) -> None:
    from aiadev.preflight import check

    issues = check(
        "plan",
        feature_dir,
        env={},
        current_branch=_stub_branch("feature/other-thing"),
    )

    messages = [i.message for i in issues]
    assert (
        "pre-flight: git branch 'feature/other-thing' does not match feature "
        "directory '0010-pipeline-preflight-checks'"
    ) in messages


def test_branch_slug_match_passes(feature_dir: pathlib.Path) -> None:
    from aiadev.preflight import check

    issues = check(
        "plan",
        feature_dir,
        env={},
        current_branch=_stub_branch("feature/pipeline-preflight-checks"),
    )

    assert not any("does not match feature directory" in i.message for i in issues)


# -- T006: Story 1 scenario 6 -------------------------------------------------


def test_env_warn_downgrades_to_stderr_diagnostic(feature_dir: pathlib.Path) -> None:
    from aiadev.preflight import check

    (feature_dir / "tasks.md").unlink()

    issues = check(
        "implement",
        feature_dir,
        env={"AIADEV_PREFLIGHT": "warn"},
        current_branch=_stub_branch("feature/pipeline-preflight-checks"),
    )

    assert issues, "warn mode must still report the issue"
    assert all(not i.would_abort for i in issues)


def test_default_env_aborts(feature_dir: pathlib.Path) -> None:
    from aiadev.preflight import check

    (feature_dir / "tasks.md").unlink()

    issues = check(
        "implement",
        feature_dir,
        env={},
        current_branch=_stub_branch("feature/pipeline-preflight-checks"),
    )

    assert all(i.would_abort for i in issues)


def test_env_abort_explicit(feature_dir: pathlib.Path) -> None:
    from aiadev.preflight import check

    (feature_dir / "tasks.md").unlink()

    issues = check(
        "implement",
        feature_dir,
        env={"AIADEV_PREFLIGHT": "abort"},
        current_branch=_stub_branch("feature/pipeline-preflight-checks"),
    )

    assert all(i.would_abort for i in issues)


# -- T007: Story 2 scenario 1 -------------------------------------------------


def test_missing_section_anchor_in_spec_aborts_plan(feature_dir: pathlib.Path) -> None:
    from aiadev.preflight import check

    spec = feature_dir / "spec.md"
    text = spec.read_text(encoding="utf-8").replace("<!-- section: Problem -->\n", "")
    spec.write_text(text, encoding="utf-8")

    issues = check(
        "plan",
        feature_dir,
        env={},
        current_branch=_stub_branch("feature/pipeline-preflight-checks"),
    )

    messages = [i.message for i in issues]
    assert "pre-flight: spec.md missing required section anchor 'Problem'" in messages
