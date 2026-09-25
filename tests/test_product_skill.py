"""T006 — `product` skill: bootstrap mode with cited sources.

Spec: specs/0023-product-context/spec.md, Story 1 scenario 1 and scenario 2.

``product`` mirrors the two-mode contract of ``skills/constitution/SKILL.md``
(plan ADR-1): mode is chosen by whether ``specs/_product/`` exists. This
file covers bootstrap mode only — mode detection (both branches, but
bootstrap fully specified) and the bootstrap procedure itself: read repo
context, render the three templates citing the source of every filled
value, turn non-inferable values into ``cl-N`` clarification markers, and
write only after explicit approval.
"""
from __future__ import annotations

import pathlib
import re

import pytest

PRODUCT_SKILL = pathlib.Path("skills/product/SKILL.md")


def _body(framework_root: pathlib.Path) -> str:
    return (framework_root / PRODUCT_SKILL).read_text(encoding="utf-8")


def _section(text: str, heading: str) -> str:
    """Return the text between ``## <heading>`` and the next ``## `` heading."""
    pattern = rf"^## {re.escape(heading)}[^\n]*\n(.*?)(?=^## |\Z)"
    match = re.search(pattern, text, flags=re.MULTILINE | re.DOTALL)
    assert match is not None, f"missing '## {heading}' section in {PRODUCT_SKILL}"
    return match.group(1)


def test_bootstrap_reads_repo_context(framework_root: pathlib.Path) -> None:
    text = _body(framework_root)
    bootstrap = _section(text, "Bootstrap mode").lower()

    assert "readme.md" in bootstrap
    assert "pyproject.toml" in bootstrap
    assert "package.json" in bootstrap
    assert "agents.md" in bootstrap
    assert ".claude/rules" in bootstrap


def test_every_value_cites_source(framework_root: pathlib.Path) -> None:
    text = _body(framework_root)
    bootstrap = _section(text, "Bootstrap mode").lower()

    assert "cite" in bootstrap
    assert "source" in bootstrap
    assert "mission-template.md" in bootstrap
    assert "tech-stack-template.md" in bootstrap
    assert "roadmap-template.md" in bootstrap


def test_unknown_values_become_cl_markers(framework_root: pathlib.Path) -> None:
    text = _body(framework_root)
    bootstrap = _section(text, "Bootstrap mode")

    assert "NEEDS CLARIFICATION:cl-" in bootstrap
    assert "never invent" in bootstrap.lower() or "not invent" in bootstrap.lower()


def test_writes_only_after_approval(framework_root: pathlib.Path) -> None:
    text = _body(framework_root)
    bootstrap = _section(text, "Bootstrap mode").lower()

    assert "approval" in bootstrap
    assert "specs/_product/" in bootstrap


def test_mode_detection_uses_specs_product(framework_root: pathlib.Path) -> None:
    text = _body(framework_root)
    mode_detection = _section(text, "Mode detection")

    assert "specs/_product/" in mode_detection


def test_rules_section_present(framework_root: pathlib.Path) -> None:
    text = _body(framework_root)
    rules = _section(text, "Rules")

    assert "inferred is not the same as fabricated" in rules.lower()


def test_hand_off_section_present(framework_root: pathlib.Path) -> None:
    text = _body(framework_root)
    hand_off = _section(text, "Hand-off")

    assert "specify" in hand_off.lower()


def test_update_mode_lists_sections_without_overwrite(framework_root: pathlib.Path) -> None:
    text = _body(framework_root)
    update_mode = _section(text, "Update mode").lower()

    assert "list" in update_mode
    assert "section" in update_mode
    assert "which to update" in update_mode
    assert "never overwrite" in update_mode


def test_never_reads_secret_files(framework_root: pathlib.Path) -> None:
    text = _body(framework_root)
    rules = _section(text, "Rules").lower()

    assert ".env" in rules
    assert "*.pem" in rules
    assert "*.key" in rules
    assert "id_rsa" in rules
    assert "credentials" in rules


def test_no_forward_pointers_left(framework_root: pathlib.Path) -> None:
    text = _body(framework_root)

    assert "added in a later task" not in text.lower()
