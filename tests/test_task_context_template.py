"""Content tests for templates/task-context-template.md (T016, spec 0014).

Why these tests exist: Story 1 sc1 in `specs/0014-bmad-inspired-evolutions/spec.md`
requires that the per-task context file produced by the `task-context` skill
exposes a stable shape — a fixed set of section anchors and Jinja-style
placeholders — so the skill (T018) and the implementer prompt rewrite (T019)
can rely on it without re-parsing free-form prose.

Anchors are HTML comments (`<!-- section: name -->`) following the same
schema-contract convention as `templates/spec-template.md`. Placeholders are
`{{NAME}}` Jinja-style tokens. These tests pin both.
"""
from __future__ import annotations

import pathlib
import re

TEMPLATE_REL = "templates/task-context-template.md"

REQUIRED_SECTION_ANCHORS = (
    "spec-slice",
    "plan-slice",
    "files",
    "tdd-checklist",
    "previous-task-context",
)

REQUIRED_PLACEHOLDERS = (
    "{{TASK_ID}}",
    "{{TASK_TITLE}}",
    "{{BRANCH}}",
    "{{DATE}}",
    "{{SPEC_PATH}}",
    "{{PLAN_PATH}}",
    "{{SPEC_SLICE}}",
    "{{PLAN_SLICE}}",
    "{{FILES_TO_MODIFY_WITH_EXCERPTS}}",
    "{{TDD_CHECKLIST}}",
    "{{PREVIOUS_TASK_CONTEXT_POINTER}}",
)

# Placeholder → anchor of the section that must contain it.
PLACEHOLDER_TO_ANCHOR = {
    "{{SPEC_SLICE}}": "spec-slice",
    "{{PLAN_SLICE}}": "plan-slice",
    "{{FILES_TO_MODIFY_WITH_EXCERPTS}}": "files",
    "{{TDD_CHECKLIST}}": "tdd-checklist",
    "{{PREVIOUS_TASK_CONTEXT_POINTER}}": "previous-task-context",
}


def _read(framework_root: pathlib.Path) -> str:
    return (framework_root / TEMPLATE_REL).read_text(encoding="utf-8")


def _section_block(template: str, anchor: str) -> str:
    """Return the slice of `template` from `<!-- section: anchor -->` up to
    (but not including) the next `<!-- section: -->` anchor or EOF."""
    marker = f"<!-- section: {anchor} -->"
    start = template.find(marker)
    assert start != -1, f"missing anchor {marker!r}"
    next_anchor = template.find("<!-- section:", start + len(marker))
    if next_anchor == -1:
        return template[start:]
    return template[start:next_anchor]


def test_template_file_exists(framework_root: pathlib.Path) -> None:
    assert (framework_root / TEMPLATE_REL).is_file(), (
        f"expected {TEMPLATE_REL} to exist"
    )


def test_template_has_single_h1_with_task_placeholders(
    framework_root: pathlib.Path,
) -> None:
    template = _read(framework_root)
    h1_lines = [
        line for line in template.splitlines() if re.match(r"^#\s+", line)
    ]
    assert len(h1_lines) == 1, (
        f"expected exactly one H1 in {TEMPLATE_REL}, found {len(h1_lines)}: "
        f"{h1_lines!r}"
    )
    h1 = h1_lines[0]
    assert "{{TASK_ID}}" in h1, f"H1 must include {{TASK_ID}} placeholder: {h1!r}"
    assert "{{TASK_TITLE}}" in h1, (
        f"H1 must include {{TASK_TITLE}} placeholder: {h1!r}"
    )


def test_template_has_required_section_anchors(
    framework_root: pathlib.Path,
) -> None:
    template = _read(framework_root)
    for anchor in REQUIRED_SECTION_ANCHORS:
        marker = f"<!-- section: {anchor} -->"
        count = template.count(marker)
        assert count == 1, (
            f"expected exactly one {marker!r} in {TEMPLATE_REL}, found {count}"
        )


def test_template_has_required_placeholders(
    framework_root: pathlib.Path,
) -> None:
    template = _read(framework_root)
    for placeholder in REQUIRED_PLACEHOLDERS:
        assert placeholder in template, (
            f"missing placeholder {placeholder!r} in {TEMPLATE_REL}"
        )


def test_each_content_placeholder_is_inside_its_section(
    framework_root: pathlib.Path,
) -> None:
    """Skill (T018) reads each section by anchor and substitutes the
    placeholder it carries. If the placeholder drifts out of its section,
    the substitution will silently miss."""
    template = _read(framework_root)
    for placeholder, anchor in PLACEHOLDER_TO_ANCHOR.items():
        block = _section_block(template, anchor)
        assert placeholder in block, (
            f"placeholder {placeholder!r} must live inside the "
            f"<!-- section: {anchor} --> block"
        )


def test_template_ends_with_trailing_newline(
    framework_root: pathlib.Path,
) -> None:
    template = _read(framework_root)
    assert template.endswith("\n"), (
        f"{TEMPLATE_REL} must end with a trailing newline"
    )


def test_template_has_no_emojis(framework_root: pathlib.Path) -> None:
    """Project house style: templates carry no emojis (terse-mode glyphs
    are runtime-only)."""
    template = _read(framework_root)
    # Match anything in the common emoji blocks. Keeps the assertion narrow
    # so legitimate punctuation passes.
    emoji_re = re.compile(
        "["
        "\U0001F300-\U0001FAFF"  # symbols & pictographs (extended)
        "\U0001F600-\U0001F64F"  # emoticons
        "\U00002600-\U000027BF"  # dingbats
        "]"
    )
    found = emoji_re.findall(template)
    assert not found, f"{TEMPLATE_REL} must not contain emojis: {found!r}"
