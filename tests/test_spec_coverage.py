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
