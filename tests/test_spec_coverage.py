"""Parser da linha ``**Spec scenarios:**`` de uma task (T017)."""

from __future__ import annotations

import pytest

from aiadev.spec_coverage import parse_scenario_refs


def _s(refs):
    return {story: set(nums) for story, nums in refs.scenarios.items()}


def test_story_scenario_canonical() -> None:
    refs = parse_scenario_refs("Story 1 scenario 2")
    assert _s(refs) == {1: {2}}
    assert refs.has_reference


def test_repeated_scenario_keyword_shares_story() -> None:
    assert _s(parse_scenario_refs("Story 1 scenario 1, scenario 2")) == {1: {1, 2}}


def test_scenarios_plural_list() -> None:
    assert _s(parse_scenario_refs("Story 3 scenarios 1, 4")) == {3: {1, 4}}


@pytest.mark.parametrize("dash", ["–", "-", "—"])
def test_range_with_dash_variants(dash: str) -> None:
    assert _s(parse_scenario_refs(f"Story 2 scenarios 1{dash}3")) == {2: {1, 2, 3}}


def test_legacy_sc_notation() -> None:
    assert _s(parse_scenario_refs("Story 2 sc3")) == {2: {3}}


def test_bold_notation() -> None:
    assert _s(parse_scenario_refs("**Story 4 sc1**")) == {4: {1}}


def test_label_prefix_is_tolerated() -> None:
    assert _s(parse_scenario_refs("- **Spec scenarios:** Story 1 scenario 1")) == {1: {1}}


def test_multiple_stories_separated_by_semicolon() -> None:
    refs = parse_scenario_refs("Story 1 scenario 1; Story 2 scenarios 2, 3")
    assert _s(refs) == {1: {1}, 2: {2, 3}}


def test_multiple_stories_with_comma_keep_second_story() -> None:
    assert _s(parse_scenario_refs("Story 1 sc1, Story 2 sc2")) == {1: {1}, 2: {2}}


def test_story_alone_covers_whole_story() -> None:
    refs = parse_scenario_refs("Story 5")
    assert refs.whole_stories == frozenset({5})
    assert refs.scenarios == {}
    assert refs.has_reference


def test_story_whole_and_other_story_scenarios() -> None:
    refs = parse_scenario_refs("Story 1; Story 2 scenario 1")
    assert refs.whole_stories == frozenset({1})
    assert _s(refs) == {2: {1}}


def test_success_criterion() -> None:
    refs = parse_scenario_refs("Success criterion #3")
    assert refs.criteria == frozenset({3})
    assert refs.has_reference


def test_success_criterion_with_stories() -> None:
    refs = parse_scenario_refs("Story 1 scenario 1; Success criterion #2")
    assert refs.criteria == frozenset({2})
    assert _s(refs) == {1: {1}}


@pytest.mark.parametrize("text", ["—", "", "  ", "-", "n/a"])
def test_no_reference(text: str) -> None:
    refs = parse_scenario_refs(text)
    assert not refs.has_reference
    assert refs.scenarios == {} and not refs.whole_stories and not refs.criteria


def test_inverted_range_is_normalised() -> None:
    assert _s(parse_scenario_refs("Story 1 scenarios 4–2")) == {1: {2, 3, 4}}


def test_huge_range_keeps_only_endpoints() -> None:
    refs = parse_scenario_refs("Story 1 scenarios 1–100000")
    assert _s(refs) == {1: {1, 100000}}


def test_leading_zeros_and_zero() -> None:
    assert _s(parse_scenario_refs("Story 01 scenario 002")) == {1: {2}}
    assert not parse_scenario_refs("Story 0 scenario 0").has_reference


def test_garbage_text() -> None:
    assert not parse_scenario_refs("see the spec, somewhere; scenario soon").has_reference


def test_mixed_case() -> None:
    assert _s(parse_scenario_refs("story 1 Scenario 2")) == {1: {2}}



def test_semicolon_closes_story_group_comma_does_not() -> None:
    semi = parse_scenario_refs("Story 1 scenario 1; scenario 2")
    assert _s(semi) == {1: {1}}
    assert semi.orphan_scenarios == frozenset({2})
    assert _s(parse_scenario_refs("Story 1 scenario 1, scenario 2")) == {1: {1, 2}}


@pytest.mark.parametrize("lead", ["—", "–", "-", "n/a", "N/A"])
def test_dash_value_only_accepts_success_criterion(lead: str) -> None:
    assert not parse_scenario_refs(f"{lead} *(infra para Story 4 sc2)*").has_reference
    refs = parse_scenario_refs(f"{lead} Success criterion #2")
    assert refs.criteria == frozenset({2})
    assert refs.scenarios == {} and not refs.whole_stories


def test_dash_value_after_label() -> None:
    line = "- **Spec scenarios:** — *(infra para Story 4 sc2)*"
    assert not parse_scenario_refs(line).has_reference


def test_orphan_scenarios_do_not_count_as_reference() -> None:
    refs = parse_scenario_refs("scenario 2")
    assert refs.orphan_scenarios == frozenset({2})
    assert not refs.has_reference


def test_story_cited_alone_then_with_scenario_stays_whole() -> None:
    refs = parse_scenario_refs("Story 1; Story 1 scenario 2")
    assert refs.whole_stories == frozenset({1})
    assert _s(refs) == {1: {2}}
    refs = parse_scenario_refs("Story 1 scenario 2; Story 1")
    assert refs.whole_stories == frozenset({1})


# --- check(): cobertura cenário -> task (T018) ---------------------------------

from pathlib import Path  # noqa: E402

from aiadev.spec_coverage import check, load_exceptions, spec_scenarios  # noqa: E402

_SPEC = """# Spec

## Success criteria

- primeiro critério
  continuação indentada
- segundo critério

## User stories

### Story 1 — A (P1)

1. dado x, quando y, então z
2. dado a, quando b, então c

### Story 2 — B (P2)

1. dado m, quando n, então o

## Clarifications
"""


def _tasks(*blocks: tuple[str, str]) -> str:
    out = ["# Tasks", "", "## Task list", ""]
    for task_id, line in blocks:
        out += [f"### {task_id} — título", "", "- **Status:** pending"]
        if line is not None:
            out.append(f"- **Spec scenarios:** {line}")
        out.append("")
    return "\n".join(out)


def _run(tmp_path: Path, tasks: str, spec: str = _SPEC):
    spec_path = tmp_path / "spec.md"
    tasks_path = tmp_path / "tasks.md"
    spec_path.write_text(spec, encoding="utf-8")
    tasks_path.write_text(tasks, encoding="utf-8")
    return check(spec_path, tasks_path)


def _kinds(issues) -> list[tuple[str, str]]:
    return sorted((i.kind, i.ref) for i in issues)


def test_spec_scenarios_extracts_per_story() -> None:
    assert spec_scenarios(_SPEC) == {1: [1, 2], 2: [1]}


def test_only_dash_task_is_reported(tmp_path: Path) -> None:
    tasks = _tasks(
        ("T001", "Story 1 scenario 1, scenario 2"),
        ("T002", "Story 2 scenario 1"),
        ("T003", "—"),
    )
    # T003 é órfã (— sem critério); as demais cobrem tudo.
    assert _kinds(_run(tmp_path, tasks)) == [("orphan_task", "T003")]


def test_story_alone_covers_its_scenarios(tmp_path: Path) -> None:
    tasks = _tasks(("T001", "Story 1; Story 2"))
    assert _run(tmp_path, tasks) == []


def test_uncovered_scenario(tmp_path: Path) -> None:
    tasks = _tasks(("T001", "Story 1 scenario 1; Story 2 scenario 1"))
    issues = _run(tmp_path, tasks)
    assert _kinds(issues) == [("uncovered_scenario", "Story 1 scenario 2")]
    assert issues[0].message


def test_orphan_task_without_reference(tmp_path: Path) -> None:
    tasks = _tasks(("T001", "Story 1; Story 2"), ("T002", None), ("T003", "scenario 2"))
    assert _kinds(_run(tmp_path, tasks)) == [("orphan_task", "T002"), ("orphan_task", "T003")]


def test_success_criterion_makes_infra_task_valid(tmp_path: Path) -> None:
    tasks = _tasks(("T001", "Story 1; Story 2"), ("T002", "— Success criterion #2"))
    assert _run(tmp_path, tasks) == []


def test_unknown_criterion(tmp_path: Path) -> None:
    tasks = _tasks(("T001", "Story 1; Story 2"), ("T002", "Success criterion #3"))
    assert _kinds(_run(tmp_path, tasks)) == [("unknown_criterion", "Success criterion #3")]


def test_unknown_story_and_scenario(tmp_path: Path) -> None:
    tasks = _tasks(("T001", "Story 1; Story 2"), ("T002", "Story 9 scenario 1; Story 2 scenario 7"))
    assert _kinds(_run(tmp_path, tasks)) == [
        ("unknown_reference", "Story 2 scenario 7"),
        ("unknown_reference", "Story 9 scenario 1"),
    ]


def test_missing_files_raise(tmp_path: Path) -> None:
    (tmp_path / "tasks.md").write_text(_tasks(), encoding="utf-8")
    with pytest.raises(FileNotFoundError, match="spec.md"):
        check(tmp_path / "spec.md", tmp_path / "tasks.md")
    (tmp_path / "spec.md").write_text(_SPEC, encoding="utf-8")
    with pytest.raises(FileNotFoundError, match="nope.md"):
        check(tmp_path / "spec.md", tmp_path / "nope.md")


def test_real_lean_pipeline_spec_is_clean() -> None:
    root = Path(__file__).resolve().parent.parent / "specs" / "0030-lean-pipeline"
    assert check(root / "spec.md", root / "tasks.md") == []


# --- T020: baseline de cobertura das specs existentes -----------------------

import collections
from pathlib import Path

import yaml

from aiadev.spec_coverage import check

_ROOT = Path(__file__).resolve().parent.parent
_EXCEPTIONS_FILE = _ROOT / "docs" / "coverage-exceptions.yaml"


def _load_exceptions(path: Path = _EXCEPTIONS_FILE) -> dict[str, str]:
    return load_exceptions(path)


def _features() -> list[Path]:
    return [
        d
        for d in sorted((_ROOT / "specs").iterdir())
        if (d / "spec.md").is_file() and (d / "tasks.md").is_file()
    ]


def _issues_by_feature() -> dict[str, list]:
    return {d.name: check(d / "spec.md", d / "tasks.md") for d in _features()}


def test_every_exception_has_a_reason_and_names_a_feature() -> None:
    exceptions = _load_exceptions()
    names = {d.name for d in _features()}
    assert exceptions, "lista de exceções vazia: remova o arquivo e este teste"
    for feature, reason in exceptions.items():
        assert feature in names, f"{feature}: não é uma feature de specs/"
        assert reason.strip(), f"{feature}: motivo vazio"


def test_dirty_features_are_listed_as_exceptions() -> None:
    exceptions = _load_exceptions()
    unlisted = {
        name: dict(collections.Counter(i.kind for i in issues))
        for name, issues in _issues_by_feature().items()
        if issues and name not in exceptions
    }
    assert not unlisted, f"features com issues fora de coverage-exceptions.yaml: {unlisted}"


def test_no_stale_exceptions() -> None:
    exceptions = _load_exceptions()
    by_feature = _issues_by_feature()
    stale = [f for f in exceptions if f in by_feature and not by_feature[f]]
    assert not stale, f"exceções obsoletas (já passam limpas), remova: {stale}"


def test_exception_loader_rejects_non_mapping(tmp_path: Path) -> None:
    bad = tmp_path / "x.yaml"
    bad.write_text("- a\n- b\n", encoding="utf-8")
    with pytest.raises(ValueError):
        _load_exceptions(bad)
