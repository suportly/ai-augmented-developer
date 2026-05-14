"""Tests for ``aiadev preflight requesting-code-review`` review-log validator.

T008 — Story 3 sc1, sc2 from
``specs/0014-bmad-inspired-evolutions/spec.md``: when the latest reviewer
output in ``specs/<branch>/.review-log.jsonl`` is APPROVED on a non-trivial
change without the ``### Why no issues`` block, the preflight CLI must
exit non-zero with a diagnostic naming the violation. Otherwise it must
exit silently.

Mirrors the style of ``tests/test_preflight.py`` (CliRunner against
``aiadev.cli.main``, ``tmp_path`` for the workspace).
"""
from __future__ import annotations

import json
import pathlib

import pytest


FEATURE_SLUG = "0014-bmad-inspired-evolutions"
BRANCH_NAME = "feature/bmad-inspired-evolutions"


def _write(path: pathlib.Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


@pytest.fixture
def feature_dir(tmp_path: pathlib.Path) -> pathlib.Path:
    """Build the minimum feature dir so the upstream artefact checks pass.

    ``check`` for ``requesting-code-review`` already requires
    ``spec.md``, ``plan.md`` and ``tasks.md`` (per the existing
    ``_REQUIRES_*`` tables). We populate them with the canonical anchors
    and a matching branch header so that the only signal under test is
    the new review-log validator.
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


def _write_log(feature_dir: pathlib.Path, entries: list[dict]) -> None:
    log_path = feature_dir / ".review-log.jsonl"
    log_path.write_text(
        "\n".join(json.dumps(e) for e in entries) + "\n", encoding="utf-8"
    )


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


# -- happy path --------------------------------------------------------------


def test_preflight_requesting_code_review_compliant_entry_exits_zero(
    feature_dir: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = feature_dir.parents[1]
    monkeypatch.chdir(repo)
    _patch_branch(monkeypatch)
    _write_log(
        feature_dir,
        [
            {
                "timestamp": "2026-05-13T11:00:00Z",
                "reviewer": "code-reviewer",
                "verdict": "APPROVED",
                "has_why_no_issues_block": True,
                "task_id": "T008",
            }
        ],
    )

    result = _run_cli(
        ["preflight", "requesting-code-review", "--feature", FEATURE_SLUG],
        cwd=repo,
    )

    assert result.exit_code == 0, result.output


# -- sad path: APPROVED without Why-no-issues block --------------------------


def test_preflight_requesting_code_review_approved_without_block_exits_nonzero(
    feature_dir: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = feature_dir.parents[1]
    monkeypatch.chdir(repo)
    _patch_branch(monkeypatch)
    _write_log(
        feature_dir,
        [
            {
                "timestamp": "2026-05-13T11:00:00Z",
                "reviewer": "code-reviewer",
                "verdict": "APPROVED",
                "has_why_no_issues_block": False,
                "task_id": "T008",
            }
        ],
    )

    result = _run_cli(
        ["preflight", "requesting-code-review", "--feature", FEATURE_SLUG],
        cwd=repo,
    )

    assert result.exit_code != 0, result.output
    assert "Why no issues" in result.output, result.output


# -- CHANGES_REQUESTED is fine: review will continue -------------------------


def test_preflight_requesting_code_review_changes_requested_exits_zero(
    feature_dir: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = feature_dir.parents[1]
    monkeypatch.chdir(repo)
    _patch_branch(monkeypatch)
    _write_log(
        feature_dir,
        [
            {
                "timestamp": "2026-05-13T11:00:00Z",
                "reviewer": "code-reviewer",
                "verdict": "CHANGES_REQUESTED",
                "has_why_no_issues_block": False,
                "task_id": "T008",
            }
        ],
    )

    result = _run_cli(
        ["preflight", "requesting-code-review", "--feature", FEATURE_SLUG],
        cwd=repo,
    )

    assert result.exit_code == 0, result.output


# -- edge case: no .review-log.jsonl yet -------------------------------------


def test_preflight_requesting_code_review_no_log_file_exits_zero(
    feature_dir: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = feature_dir.parents[1]
    monkeypatch.chdir(repo)
    _patch_branch(monkeypatch)
    # No .review-log.jsonl created — conservative default: nothing to validate.

    result = _run_cli(
        ["preflight", "requesting-code-review", "--feature", FEATURE_SLUG],
        cwd=repo,
    )

    assert result.exit_code == 0, result.output


# -- edge case: feature directory does not exist -----------------------------


def test_preflight_requesting_code_review_missing_feature_dir_exits_nonzero(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # No specs/<slug> directory at all in the workspace.
    (tmp_path / "specs").mkdir()
    monkeypatch.chdir(tmp_path)
    _patch_branch(monkeypatch)

    result = _run_cli(
        ["preflight", "requesting-code-review", "--feature", "0099-ghost"],
        cwd=tmp_path,
    )

    assert result.exit_code != 0, result.output


# -- last-entry semantics: a stale APPROVED-without-block followed by a
#    compliant APPROVED entry must not trigger the violation ----------------


def test_preflight_requesting_code_review_uses_only_last_entry(
    feature_dir: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = feature_dir.parents[1]
    monkeypatch.chdir(repo)
    _patch_branch(monkeypatch)
    _write_log(
        feature_dir,
        [
            {
                "timestamp": "2026-05-13T10:00:00Z",
                "reviewer": "code-reviewer",
                "verdict": "APPROVED",
                "has_why_no_issues_block": False,
                "task_id": "T007",
            },
            {
                "timestamp": "2026-05-13T11:00:00Z",
                "reviewer": "code-reviewer",
                "verdict": "APPROVED",
                "has_why_no_issues_block": True,
                "task_id": "T008",
            },
        ],
    )

    result = _run_cli(
        ["preflight", "requesting-code-review", "--feature", FEATURE_SLUG],
        cwd=repo,
    )

    assert result.exit_code == 0, result.output
