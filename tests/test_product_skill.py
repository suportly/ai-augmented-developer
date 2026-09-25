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


def test_tech_stack_seeded_from_introspect(framework_root: pathlib.Path) -> None:
    text = _body(framework_root)
    bootstrap = _section(text, "Bootstrap mode")

    assert "auto-stack" in bootstrap
    assert "AGENTS.md" in bootstrap
    assert "tech-stack.md" in bootstrap
    assert "rejected alternatives" in bootstrap.lower()
    assert "src/aiadev" not in text


def test_render_drops_template_guidance_comments(framework_root: pathlib.Path) -> None:
    """Rendered files must not keep the templates' guidance comments: they
    quote the clarification-marker grammar and would trip the CI marker gate."""
    bootstrap = _section(_body(framework_root), "Bootstrap mode").lower()
    assert "guidance comment" in bootstrap


def test_roadmap_field_lines_carry_no_citation(framework_root: pathlib.Path) -> None:
    """`**Status:**`-style field lines are machine-parsed; citations go in the
    entry's paragraph instead."""
    rules = _section(_body(framework_root), "Rules")
    assert "**Status:**" in rules
    assert "paragraph" in rules.lower()


def test_bootstrap_reads_nested_manifests(framework_root: pathlib.Path) -> None:
    """Stack detection only reads the root; monorepo subprojects need their own
    manifests read too."""
    bootstrap = _section(_body(framework_root), "Bootstrap mode").lower()
    assert "nested" in bootstrap or "subproject" in bootstrap


def test_mode_detection_handles_partial_product_dir(framework_root: pathlib.Path) -> None:
    """A `specs/_product/` with a missing file bootstraps only the missing file."""
    mode = _section(_body(framework_root), "Mode detection").lower()
    assert "missing" in mode
    assert "bootstrap" in mode


def test_rendering_keeps_section_anchors(framework_root: pathlib.Path) -> None:
    """Dropping guidance comments must not drop the `<!-- section: -->` anchors."""
    bootstrap = _section(_body(framework_root), "Bootstrap mode")
    assert "<!-- section:" in bootstrap


def test_input_description_matches_update_mode(framework_root: pathlib.Path) -> None:
    """Omitting the input never refreshes all three files wholesale."""
    text = (framework_root / "skills" / "product" / "SKILL.md").read_text(encoding="utf-8")
    assert "refresh all three" not in text
