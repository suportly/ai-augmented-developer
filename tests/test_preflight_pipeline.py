"""End-to-end pre-flight pipeline tests.

Spec: ``specs/0010-pipeline-preflight-checks/spec.md`` Success criterion #5
("deleting any prior-stage artifact causes the immediately following
pipeline skill to fail with the actionable message").
"""
from __future__ import annotations

import pathlib
import shutil
import time

import pytest
from click.testing import CliRunner

REFERENCE_FIXTURE = (
    pathlib.Path(__file__).resolve().parent / "fixtures" / "preflight" / "reference"
)


def _build_repo(tmp_path: pathlib.Path) -> tuple[pathlib.Path, pathlib.Path]:
    """Lay out tmp/specs/<slug>/ from the reference fixture and return paths."""
    repo = tmp_path / "repo"
    repo.mkdir()
    feature_slug = "0001-reference"
    feature_dir = repo / "specs" / feature_slug
    shutil.copytree(REFERENCE_FIXTURE, feature_dir)
    review = repo / ".aiadev" / "review.yaml"
    review.parent.mkdir(parents=True, exist_ok=True)
    review.write_text(
        "status: approved\ntimestamp: 2026-04-21T00:00:00Z\n",
        encoding="utf-8",
    )
    return repo, feature_dir


def _run_cli(args: list[str], cwd: pathlib.Path):
    from aiadev.cli import main

    runner = CliRunner()
    return runner.invoke(main, args, catch_exceptions=False)


# -- T023: Success criterion #5, Story 1 scenario 1 --------------------------


def test_deleting_tasks_md_causes_implement_preflight_failure(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, feature_dir = _build_repo(tmp_path)
    (feature_dir / "tasks.md").unlink()

    monkeypatch.chdir(repo)
    monkeypatch.setattr(
        "aiadev.preflight._git_current_branch", lambda: "feature/reference"
    )

    result = _run_cli(
        ["preflight", "implement", "--feature", feature_dir.name],
        cwd=repo,
    )

    assert result.exit_code != 0
    assert "pre-flight: tasks.md missing — run /aiadev:tasks first" in result.output


# -- T024: Success criterion #5 (parametrised) ------------------------------


@pytest.mark.parametrize(
    ("skill", "deleted", "needle"),
    [
        ("plan", "spec.md", "spec.md missing"),
        ("tasks", "spec.md", "spec.md missing"),
        ("tasks", "plan.md", "plan.md missing"),
        ("implement", "spec.md", "spec.md missing"),
        ("implement", "plan.md", "plan.md missing"),
        ("implement", "tasks.md", "tasks.md missing"),
        ("analyze", "tasks.md", "tasks.md missing"),
        ("finishing-a-branch", ".aiadev/review.yaml", "review approval missing"),
    ],
)
def test_deleting_each_prior_artifact_fails_the_next_skill(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    skill: str,
    deleted: str,
    needle: str,
) -> None:
    repo, feature_dir = _build_repo(tmp_path)
    monkeypatch.chdir(repo)
    monkeypatch.setattr(
        "aiadev.preflight._git_current_branch", lambda: "feature/reference"
    )

    target = repo / deleted if deleted.startswith(".aiadev") else feature_dir / deleted
    if target.exists():
        target.unlink()

    result = _run_cli(
        ["preflight", skill, "--feature", feature_dir.name],
        cwd=repo,
    )

    assert result.exit_code != 0, f"{skill}/{deleted}: expected failure, got 0"
    assert needle in result.output, (
        f"{skill}/{deleted}: expected {needle!r} in {result.output!r}"
    )


# -- T025: Success criterion #3 ----------------------------------------------


def test_reference_dir_completes_under_500ms(tmp_path: pathlib.Path) -> None:
    from aiadev.preflight import check

    repo, feature_dir = _build_repo(tmp_path)

    start = time.perf_counter()
    check(
        "analyze",
        feature_dir,
        env={},
        current_branch=lambda: "feature/reference",
        repo_root=repo,
    )
    elapsed = time.perf_counter() - start

    assert elapsed < 0.5, f"pre-flight took {elapsed:.3f}s — exceeds 500ms budget"
