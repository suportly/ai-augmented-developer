"""T003 — graph-facts rule: confidence vocabulary + provider mapping.

Story 3 (spec 0017): every graph-derived fact a skill cites declares its
provenance. This rule is the single source of truth for the aiadev-canonical
confidence vocabulary and the stable mapping from a provider's native
taxonomy (e.g. graphify's EXTRACTED/INFERRED/AMBIGUOUS). It ships **with the
opt-in `knowledge-graph` preset** (not framework-global) so only projects
that enable the provider get it; `plan`/review inherit it in the fast-follow.
"""
from __future__ import annotations

import pathlib

import yaml

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
RULE = REPO_ROOT / "presets" / "knowledge-graph" / "rules" / "graph-facts.md"

AIADEV_LABELS = ("explicit", "inferred", "ambiguous")
PROVIDER_LABELS = ("EXTRACTED", "INFERRED", "AMBIGUOUS")


def _split_frontmatter(text: str) -> tuple[dict | None, str]:
    if not text.startswith("---\n"):
        return None, text
    _, _, rest = text.partition("---\n")
    fm_text, sep, body = rest.partition("\n---\n")
    if not sep:
        return None, text
    return yaml.safe_load(fm_text), body


def test_rule_exists() -> None:
    assert RULE.exists(), f"expected the graph-facts rule at {RULE}"


def test_rule_is_always_apply_within_the_preset() -> None:
    fm, _ = _split_frontmatter(RULE.read_text(encoding="utf-8"))
    assert fm is not None, "graph-facts.md must carry YAML frontmatter"
    assert "description" in fm and fm["description"].strip()
    # alwaysApply within the preset: once the opt-in knowledge-graph preset is
    # installed, the rule applies everywhere in that project.
    assert fm.get("alwaysApply") is True
    assert "paths" not in fm


def test_rule_defines_vocabulary_and_mapping() -> None:
    body = RULE.read_text(encoding="utf-8")
    for label in AIADEV_LABELS:
        assert label in body, f"rule must define the '{label}' confidence label"
    for provider_label in PROVIDER_LABELS:
        assert provider_label in body, (
            f"rule must map the provider label '{provider_label}'"
        )


def test_rule_forbids_definitive_gaps_from_low_confidence_facts() -> None:
    body = RULE.read_text(encoding="utf-8").lower()
    assert "definitive" in body or "não afirmar" in body or "nao afirmar" in body, (
        "rule must state that inferred/ambiguous facts cannot assert a gap "
        "as definitive"
    )
