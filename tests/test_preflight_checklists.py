"""preflight ``implement``: FAIL de checklist precisa de task dona (T023)."""

from __future__ import annotations

from pathlib import Path

from aiadev import preflight

CHECKS = """# Checklist

## Items

| # | Check | Status | Evidence |
|---|---|---|---|
| 1 | a | PASS | x |
| 2 | b | FAIL | y |
| 3 | c | N/A | |

## Failed items

| # | Failed check | Remediation | Owner task |
|---|---|---|---|
| 2 | b | fix | T002 |
"""


TASKS = (
    "### T001 — a\n\n- **Spec scenarios:** Story 1\n\n"
    "### T002 — b\n\n- **Spec scenarios:** Story 1\n"
)


def _feature(tmp_path: Path, checklist: str | None, tasks: str = TASKS):
    feature = tmp_path / "specs" / "0099-demo"
    feature.mkdir(parents=True)
    (feature / "spec.md").write_text("# Spec\n\n## User stories\n\n### Story 1 — A\n\n1. dado x\n", encoding="utf-8")
    (feature / "plan.md").write_text("# Plan\n", encoding="utf-8")
    (feature / "tasks.md").write_text(tasks, encoding="utf-8")
    if checklist is not None:
        (feature / "checklists").mkdir()
        (feature / "checklists" / "security.md").write_text(checklist, encoding="utf-8")
    return feature


def _msgs(tmp_path: Path, feature: Path, env=None, skill="implement"):
    return preflight.check(
        skill, feature, env=env or {}, current_branch=lambda: "", repo_root=tmp_path
    )


def test_fail_with_existing_owner_passes(tmp_path: Path) -> None:
    assert _msgs(tmp_path, _feature(tmp_path, CHECKS)) == []


def test_fail_without_owner_row_blocks(tmp_path: Path) -> None:
    text = CHECKS.replace("| 2 | b | fix | T002 |", "| | | | |")
    issues = _msgs(tmp_path, _feature(tmp_path, text))
    assert [i.message for i in issues] == [
        "pre-flight: checklists/security.md check #2 is FAIL without an owner task in tasks.md"
    ]
    assert issues[0].would_abort


def test_owner_missing_from_tasks_blocks(tmp_path: Path) -> None:
    issues = _msgs(tmp_path, _feature(tmp_path, CHECKS.replace("T002 |", "T099 |")))
    assert len(issues) == 1 and "T099" in issues[0].message


def test_template_placeholder_is_ignored(tmp_path: Path) -> None:
    template = Path(__file__).resolve().parent.parent / "templates" / "checklist-template.md"
    assert _msgs(tmp_path, _feature(tmp_path, template.read_text(encoding="utf-8"))) == []


def test_no_checklists_dir_means_no_gate(tmp_path: Path) -> None:
    assert _msgs(tmp_path, _feature(tmp_path, None)) == []


def test_warn_downgrades(tmp_path: Path) -> None:
    text = CHECKS.replace("| 2 | b | fix | T002 |", "| | | | |")
    issues = _msgs(tmp_path, _feature(tmp_path, text), env={"AIADEV_PREFLIGHT": "warn"})
    assert issues and not any(i.would_abort for i in issues)


def test_missing_failed_table_means_fail_has_no_owner(tmp_path: Path) -> None:
    text = CHECKS.split("## Failed items")[0]
    assert len(_msgs(tmp_path, _feature(tmp_path, text))) == 1


def test_malformed_row_is_an_issue_not_a_traceback(tmp_path: Path) -> None:
    text = CHECKS.replace("| 2 | b | FAIL | y |", "| 2 | b |")
    issues = _msgs(tmp_path, _feature(tmp_path, text))
    assert any("malformed" in i.message for i in issues)


def test_only_implement_runs_the_gate(tmp_path: Path) -> None:
    text = CHECKS.replace("| 2 | b | fix | T002 |", "| | | | |")
    assert _msgs(tmp_path, _feature(tmp_path, text), skill="analyze") == []


def _ok_with(checks_rows: str, failed_rows: str = "| 2 | b | fix | T002 |") -> str:
    return (
        "## Items\n\n| # | Check | Status | Evidence |\n|---|---|---|---|\n"
        f"{checks_rows}\n\n## Failed items\n\n"
        "| # | Failed check | Remediation | Owner task |\n|---|---|---|---|\n"
        f"{failed_rows}\n"
    )


def _count(tmp_path: Path, text: str) -> int:
    return len(_msgs(tmp_path, _feature(tmp_path, text)))


def test_escaped_pipe_does_not_split_a_column(tmp_path: Path) -> None:
    text = _ok_with("| 2 | a \\| b | FAIL | y |", "| | | | |")
    assert _count(tmp_path, text) == 1


import pytest  # noqa: E402


@pytest.mark.parametrize(
    "status", ["FAIL (blocking)", "❌", "❌ FAIL", "FAIL - x", "**FAIL**", "`fail`", "✗"]
)
def test_fail_status_variants_are_detected(tmp_path: Path, status: str) -> None:
    text = _ok_with(f"| 2 | b | {status} | y |", "| | | | |")
    assert _count(tmp_path, text) == 1


def test_placeholder_status_is_not_fail(tmp_path: Path) -> None:
    assert _count(tmp_path, _ok_with("| 1 | ... | PASS / FAIL / N/A | link |", "| | | | |")) == 0


def test_blank_line_inside_table_keeps_the_mode(tmp_path: Path) -> None:
    text = _ok_with("| 1 | a | PASS | |\n\n| 2 | b | FAIL | y |", "| | | | |")
    assert _count(tmp_path, text) == 1


def test_table_without_edge_pipes(tmp_path: Path) -> None:
    text = (
        "# | Check | Status | Evidence\n--|---|---|---\n2 | b | FAIL | y\n\n"
        "## Failed items\n\n# | Failed | Fix | Owner task\n--|---|---|---\n2 | b | f | T002\n"
    )
    assert _count(tmp_path, text) == 0
    other = tmp_path / "b"
    other.mkdir()
    assert _count(other, text.replace("T002\n", "T099\n")) == 1


def test_hash_prefixed_number_matches(tmp_path: Path) -> None:
    text = _ok_with("| #2 | b | FAIL | y |", "| 2 | b | fix | T002 |")
    assert _count(tmp_path, text) == 0
    other = tmp_path / "b"
    other.mkdir()
    text = _ok_with("| 2 | b | FAIL | y |", "| #2 | b | fix | T002 |")
    assert _count(other, text) == 0


def test_fenced_tables_are_ignored(tmp_path: Path) -> None:
    text = "```\n" + _ok_with("| 2 | b | FAIL | y |", "| | | | |") + "```\n"
    assert _count(tmp_path, text) == 0
