"""preflight ``implement``: cobertura cenário -> task como erro (T022)."""

from __future__ import annotations

from pathlib import Path

import pytest

from aiadev import preflight
from aiadev.spec_coverage import load_exceptions

SPEC = """# Spec

## Success criteria

- um critério

## User stories

### Story 1 — A (P1)

1. dado x
2. dado y
"""


def _feature(tmp_path: Path, tasks_body: str, name: str = "0099-demo") -> Path:
    feature = tmp_path / "specs" / name
    feature.mkdir(parents=True)
    (feature / "spec.md").write_text(SPEC, encoding="utf-8")
    (feature / "plan.md").write_text("# Plan\n", encoding="utf-8")
    (feature / "tasks.md").write_text(
        "# Tasks\n\n## Task list\n\n" + tasks_body, encoding="utf-8"
    )
    return feature


def _run(tmp_path: Path, feature: Path, env=None, skill: str = "implement"):
    return preflight.check(
        skill, feature, env=env or {}, current_branch=lambda: "", repo_root=tmp_path
    )


CLEAN = "### T001 — a\n\n- **Spec scenarios:** Story 1 scenario 1, scenario 2\n"


def test_clean_feature_has_no_issue(tmp_path: Path) -> None:
    assert _run(tmp_path, _feature(tmp_path, CLEAN)) == []


def test_uncovered_scenario_aborts_and_names_it(tmp_path: Path) -> None:
    body = "### T001 — a\n\n- **Spec scenarios:** Story 1 scenario 1\n"
    issues = _run(tmp_path, _feature(tmp_path, body))
    assert [i.message for i in issues] == [
        "pre-flight: scenario Story 1 scenario 2 is not covered by any task — "
        "add it to a task's Spec scenarios"
    ]
    assert issues[0].would_abort


def test_orphan_task_aborts_and_names_it(tmp_path: Path) -> None:
    body = CLEAN + "\n### T002 — b\n\n- **Spec scenarios:** —\n"
    issues = _run(tmp_path, _feature(tmp_path, body))
    assert [i.message for i in issues] == [
        "pre-flight: T002 cites no scenario, story or success criterion"
    ]


def test_unknown_reference_and_criterion_are_reported(tmp_path: Path) -> None:
    body = CLEAN + "\n### T002 — b\n\n- **Spec scenarios:** Story 7; Success criterion #4\n"
    messages = [i.message for i in _run(tmp_path, _feature(tmp_path, body))]
    assert len(messages) == 2
    assert all(m.startswith("pre-flight: ") and "T002" in m for m in messages)


def test_warn_downgrades_to_non_aborting(tmp_path: Path) -> None:
    body = "### T001 — a\n\n- **Spec scenarios:** —\n"
    issues = _run(tmp_path, _feature(tmp_path, body), env={"AIADEV_PREFLIGHT": "warn"})
    assert issues and not any(i.would_abort for i in issues)


def test_other_skills_do_not_run_coverage(tmp_path: Path) -> None:
    body = "### T001 — a\n\n- **Spec scenarios:** —\n"
    feature = _feature(tmp_path, body)
    assert _run(tmp_path, feature, skill="analyze") == []


def test_listed_exception_is_skipped(tmp_path: Path) -> None:
    body = "### T001 — a\n\n- **Spec scenarios:** —\n"
    feature = _feature(tmp_path, body)
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "coverage-exceptions.yaml").write_text(
        "0099-demo: legado anterior à linha Spec scenarios\n", encoding="utf-8"
    )
    assert _run(tmp_path, feature) == []


def test_unreadable_tasks_becomes_issue_not_traceback(tmp_path: Path) -> None:
    feature = _feature(tmp_path, CLEAN)
    (feature / "tasks.md").write_bytes(b"\xff\xfe\x00bad")
    issues = _run(tmp_path, feature)
    assert len(issues) == 1 and "tasks.md" in issues[0].message


def test_invalid_exceptions_file_becomes_issue(tmp_path: Path) -> None:
    feature = _feature(tmp_path, CLEAN)
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "coverage-exceptions.yaml").write_text("- a\n", encoding="utf-8")
    issues = _run(tmp_path, feature)
    assert len(issues) == 1 and "coverage-exceptions.yaml" in issues[0].message


def test_load_exceptions(tmp_path: Path) -> None:
    assert load_exceptions(tmp_path / "missing.yaml") == {}
    ok = tmp_path / "ok.yaml"
    ok.write_text("a: motivo\n", encoding="utf-8")
    assert load_exceptions(ok) == {"a": "motivo"}


@pytest.mark.parametrize("text", ["- a\n", "a:\n", "a: ''\n", "a: 3\n", "a: '  '\n"])
def test_load_exceptions_rejects_bad_shapes(tmp_path: Path, text: str) -> None:
    bad = tmp_path / "bad.yaml"
    bad.write_text(text, encoding="utf-8")
    with pytest.raises(ValueError):
        load_exceptions(bad)


_ROOT = Path(__file__).resolve().parent.parent


def test_consumer_without_exceptions_file_applies_the_gate(tmp_path: Path) -> None:
    body = "### T001 — a\n\n- **Spec scenarios:** —\n"
    feature = _feature(tmp_path, body)
    assert not (tmp_path / "docs" / "coverage-exceptions.yaml").exists()
    assert any(i.would_abort for i in _run(tmp_path, feature))


def _real_features() -> list[Path]:
    return [
        d
        for d in sorted((_ROOT / "specs").iterdir())
        if (d / "spec.md").is_file() and (d / "tasks.md").is_file()
    ]


@pytest.mark.parametrize("feature", _real_features(), ids=lambda p: p.name)
def test_real_features_have_no_coverage_issue(feature: Path) -> None:
    issues = preflight.check(
        "implement", feature, env={}, current_branch=lambda: "", repo_root=_ROOT
    )
    coverage = [
        i.message
        for i in issues
        if "scenario" in i.message or "cites" in i.message or "coverage" in i.message
    ]
    assert coverage == []


def test_legacy_tasks_without_scenario_lines_warn_once(tmp_path: Path) -> None:
    body = "### T001 — a\n\n- **Status:** pending\n\n### T002 — b\n\n- **Status:** pending\n"
    issues = _run(tmp_path, _feature(tmp_path, body))
    assert [i.message for i in issues] == [
        "pre-flight: tasks.md has no Spec scenarios lines (legacy format) — "
        "scenario coverage not checked"
    ]
    assert not issues[0].would_abort


def test_any_scenarios_line_keeps_coverage_aborting(tmp_path: Path) -> None:
    body = "### T001 — a\n\n- **Spec scenarios:** Story 1 scenario 1\n\n### T002 — b\n\n- x\n"
    issues = _run(tmp_path, _feature(tmp_path, body))
    assert issues and all(i.would_abort for i in issues)
