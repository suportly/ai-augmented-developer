"""Tests for ``aiadev preflight implement --task-context`` CLI flag.

T021 — Story 1 sc1 from
``specs/0014-bmad-inspired-evolutions/spec.md``: the orchestrator can be
opted into the per-task context composition either via preset.yaml
(``task_context: true``) or via the CLI flag ``--task-context``. This
file tests only the CLI-flag side of the trigger.

Design choice for non-implement skills:
    The flag is **silently ignored** when ``<skill>`` is not
    ``implement``. Rationale: emitting a stderr warning would noise
    every chained pipeline invocation that re-uses the same flag set,
    and the flag has no semantic effect outside ``implement``. The
    silent path keeps backwards-compatible exit codes intact while the
    explicit ``implement`` path emits the diagnostic.

Mirrors the style of ``tests/test_preflight_review.py`` (CliRunner
against ``aiadev.cli.main``, ``tmp_path`` for the workspace).
"""
from __future__ import annotations

import pathlib

import pytest


FEATURE_SLUG = "0014-bmad-inspired-evolutions"
BRANCH_NAME = "feature/bmad-inspired-evolutions"


def _write(path: pathlib.Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


@pytest.fixture
def feature_dir(tmp_path: pathlib.Path) -> pathlib.Path:
    """Build the minimum feature dir so ``preflight implement`` exits zero.

    ``check`` for ``implement`` requires spec.md, plan.md and tasks.md.
    We populate them with the canonical anchors and a matching branch
    header so the only signal under test is the new ``--task-context``
    flag.
    """
    root = tmp_path / "specs" / FEATURE_SLUG
    _write(
        root / "spec.md",
        "# Feature\n\n"
        f"**Branch:** `{BRANCH_NAME}`\n"
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
        f"**Branch:** `{BRANCH_NAME}`\n"
        "**Language:** en\n",
    )
    _write(root / "tasks.md", "# Tasks\n\n**Language:** en\n")
    return root


def _run_cli(args: list[str], cwd: pathlib.Path):
    from click.testing import CliRunner

    from aiadev.cli import main

    runner = CliRunner()
    return runner.invoke(main, args, catch_exceptions=False, env={"PWD": str(cwd)})


def _patch_branch(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "aiadev.preflight._git_current_branch",
        lambda: BRANCH_NAME,
    )


# -- happy path: flag accepted and announced ---------------------------------


def test_preflight_implement_accepts_task_context_flag(
    feature_dir: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = feature_dir.parents[1]
    monkeypatch.chdir(repo)
    _patch_branch(monkeypatch)

    result = _run_cli(
        ["preflight", "implement", "--task-context", "--feature", FEATURE_SLUG],
        cwd=repo,
    )

    assert result.exit_code == 0, result.output
    assert "task-context enabled" in result.output, result.output


# -- default-off: no flag, no announcement -----------------------------------


def test_preflight_implement_without_task_context_flag_defaults_off(
    feature_dir: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = feature_dir.parents[1]
    monkeypatch.chdir(repo)
    _patch_branch(monkeypatch)

    result = _run_cli(
        ["preflight", "implement", "--feature", FEATURE_SLUG],
        cwd=repo,
    )

    assert result.exit_code == 0, result.output
    assert "task-context enabled" not in result.output, result.output


# -- explicit --no-task-context behaves like default ------------------------


def test_preflight_implement_explicit_no_task_context_flag_silent(
    feature_dir: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = feature_dir.parents[1]
    monkeypatch.chdir(repo)
    _patch_branch(monkeypatch)

    result = _run_cli(
        ["preflight", "implement", "--no-task-context", "--feature", FEATURE_SLUG],
        cwd=repo,
    )

    assert result.exit_code == 0, result.output
    assert "task-context enabled" not in result.output, result.output


# -- non-implement skill: flag is silently ignored (design choice) ----------


def test_preflight_other_skills_silently_ignore_task_context(
    feature_dir: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Passing ``--task-context`` to ``plan`` (or any non-implement skill)
    must not crash and must not emit the ``task-context enabled``
    announcement — the flag has no semantic effect outside ``implement``.
    """
    repo = feature_dir.parents[1]
    monkeypatch.chdir(repo)
    _patch_branch(monkeypatch)

    result = _run_cli(
        ["preflight", "plan", "--task-context", "--feature", FEATURE_SLUG],
        cwd=repo,
    )

    assert result.exit_code == 0, result.output
    assert "task-context enabled" not in result.output, result.output


# -- help text mentions the opt-in semantics --------------------------------


def test_preflight_help_documents_task_context_flag() -> None:
    from click.testing import CliRunner

    from aiadev.cli import main

    runner = CliRunner()
    result = runner.invoke(main, ["preflight", "--help"], catch_exceptions=False)

    assert result.exit_code == 0, result.output
    assert "--task-context" in result.output, result.output
    # Help must telegraph the opt-in nature so users know the default is off.
    assert "implement" in result.output.lower(), result.output
