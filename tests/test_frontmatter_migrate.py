"""Tests for the pure frontmatter migrator (old shape -> metadata.aiadev shape).

Spec: specs/0016-agent-skills-interop/spec.md, Story 1, sc4 + cl-1/cl-5/cl-7.
Plan: ADR-4 — ``migrate_frontmatter`` is a pure function (no filesystem) that
moves the 5 proprietary pipeline fields (version, inputs, outputs, requires,
handoffs) from the top level into a nested ``metadata.aiadev`` object.
``migrate_skill_file`` is the file-level helper (same module) that parses a
SKILL.md frontmatter block, applies ``migrate_frontmatter``, and rewrites
only the frontmatter, leaving the Markdown body byte-identical.

This module is reused by the one-shot repo migration (T004) and by
``aiadev sync`` auto-migration of installed consumer skills (T007).
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from aiadev.frontmatter_migrate import (
    FrontmatterError,
    migrate_frontmatter,
    migrate_skill_file,
)

PROPRIETARY_KEYS = ("version", "inputs", "outputs", "requires", "handoffs")


# ---------------------------------------------------------------------------
# migrate_frontmatter
# ---------------------------------------------------------------------------


def test_moves_all_five_proprietary_fields_under_metadata_aiadev():
    fm = {
        "name": "implement",
        "description": "Execute an approved plan and tasks list.",
        "version": "0.2.0",
        "inputs": [{"type": "file", "path": "specs/<branch>/plan.md"}],
        "outputs": [{"type": "commit", "description": "One commit per task."}],
        "requires": ["constitution", "test-driven-development"],
        "handoffs": ["requesting-code-review", "finishing-a-branch"],
    }

    new_fm, changed = migrate_frontmatter(fm)

    assert changed is True
    for key in PROPRIETARY_KEYS:
        assert key not in new_fm
    assert new_fm["metadata"]["aiadev"] == {
        "version": "0.2.0",
        "inputs": [{"type": "file", "path": "specs/<branch>/plan.md"}],
        "outputs": [{"type": "commit", "description": "One commit per task."}],
        "requires": ["constitution", "test-driven-development"],
        "handoffs": ["requesting-code-review", "finishing-a-branch"],
    }
    # Unrelated fields survive.
    assert new_fm["name"] == "implement"
    assert new_fm["description"] == "Execute an approved plan and tasks list."


def test_noop_for_already_conformant_frontmatter():
    fm = {
        "name": "implement",
        "description": "Execute an approved plan and tasks list.",
        "metadata": {"aiadev": {"version": "0.2.0"}},
    }

    new_fm, changed = migrate_frontmatter(fm)

    assert changed is False
    assert new_fm == fm


def test_noop_for_minimal_frontmatter_with_no_pipeline_fields():
    fm = {"name": "finishing-a-branch", "description": "Wrap up an approved branch."}

    new_fm, changed = migrate_frontmatter(fm)

    assert changed is False
    assert new_fm == fm


def test_preserves_license_allowed_tools_disable_model_invocation_argument_hint():
    fm = {
        "name": "frontend-design",
        "description": "UI or component work, adapted from an external project.",
        "license": "MIT",
        "allowed-tools": ["Read", "Edit"],
        "disable-model-invocation": True,
        "argument-hint": "<component-name>",
        "version": "1.0.0",
    }

    new_fm, changed = migrate_frontmatter(fm)

    assert changed is True
    assert new_fm["license"] == "MIT"
    assert new_fm["allowed-tools"] == ["Read", "Edit"]
    assert new_fm["disable-model-invocation"] is True
    assert new_fm["argument-hint"] == "<component-name>"
    assert new_fm["metadata"]["aiadev"]["version"] == "1.0.0"
    assert "version" not in new_fm


def test_preserves_third_party_metadata_keys():
    fm = {
        "name": "my-skill",
        "description": "Does a thing when invoked, sufficiently descriptive.",
        "metadata": {"otherTool": {"foo": "bar"}, "shared-key": "value"},
        "requires": ["constitution"],
    }

    new_fm, changed = migrate_frontmatter(fm)

    assert changed is True
    assert new_fm["metadata"]["otherTool"] == {"foo": "bar"}
    assert new_fm["metadata"]["shared-key"] == "value"
    assert new_fm["metadata"]["aiadev"] == {"requires": ["constitution"]}


def test_idempotent_migrating_twice_equals_migrating_once():
    fm = {
        "name": "implement",
        "description": "Execute an approved plan and tasks list.",
        "version": "0.2.0",
        "requires": ["constitution"],
        "handoffs": ["finishing-a-branch"],
    }

    once, changed_once = migrate_frontmatter(fm)
    twice, changed_twice = migrate_frontmatter(once)

    assert changed_once is True
    assert changed_twice is False
    assert twice == once


def test_does_not_mutate_input_dict():
    fm = {
        "name": "implement",
        "description": "Execute an approved plan and tasks list.",
        "version": "0.2.0",
        "metadata": {"otherTool": {"foo": "bar"}},
    }
    original_copy = {
        "name": "implement",
        "description": "Execute an approved plan and tasks list.",
        "version": "0.2.0",
        "metadata": {"otherTool": {"foo": "bar"}},
    }

    new_fm, changed = migrate_frontmatter(fm)

    assert changed is True
    assert fm == original_copy
    assert new_fm is not fm
    assert new_fm["metadata"] is not fm.get("metadata")


def test_duplicate_key_precedence_prefers_existing_metadata_aiadev_value():
    """When a proprietary key exists BOTH at the top level and already under
    metadata.aiadev, the ambiguous state is resolved by preferring the
    existing metadata.aiadev value; the top-level duplicate is dropped and
    the migration is still reported as changed (since the top-level key was
    removed)."""
    fm = {
        "name": "implement",
        "description": "Execute an approved plan and tasks list.",
        "version": "0.1.0",  # stale top-level duplicate
        "metadata": {"aiadev": {"version": "0.2.0"}},  # authoritative
    }

    new_fm, changed = migrate_frontmatter(fm)

    assert changed is True
    assert new_fm["metadata"]["aiadev"]["version"] == "0.2.0"
    assert "version" not in new_fm


def test_only_present_proprietary_keys_are_moved():
    fm = {
        "name": "my-skill",
        "description": "Does a thing when invoked, sufficiently descriptive.",
        "requires": ["constitution"],
    }

    new_fm, changed = migrate_frontmatter(fm)

    assert changed is True
    assert new_fm["metadata"]["aiadev"] == {"requires": ["constitution"]}
    assert "inputs" not in new_fm["metadata"]["aiadev"]
    assert "outputs" not in new_fm["metadata"]["aiadev"]
    assert "version" not in new_fm["metadata"]["aiadev"]
    assert "handoffs" not in new_fm["metadata"]["aiadev"]


def test_creates_metadata_when_absent():
    fm = {
        "name": "my-skill",
        "description": "Does a thing when invoked, sufficiently descriptive.",
        "handoffs": ["finishing-a-branch"],
    }

    new_fm, changed = migrate_frontmatter(fm)

    assert changed is True
    assert "metadata" in new_fm
    assert new_fm["metadata"]["aiadev"]["handoffs"] == ["finishing-a-branch"]


# ---------------------------------------------------------------------------
# migrate_skill_file
# ---------------------------------------------------------------------------

_BODY = """
# Implement

Take a `plan.md` + `tasks.md` that have already been specified, clarified and approved.

**Announce at start:** "Using the implement skill."

## When to use

Run pre-flight first: `aiadev preflight implement --feature <slug>`.
"""


def _write_skill_md(path: Path, frontmatter: dict, body: str = _BODY) -> str:
    """Write a realistic SKILL.md and return its full original text."""
    fm_text = yaml.safe_dump(frontmatter, sort_keys=False, allow_unicode=True)
    text = f"---\n{fm_text}---\n{body}"
    path.write_text(text, encoding="utf-8")
    return text


def test_migrate_skill_file_rewrites_frontmatter_and_preserves_body_byte_for_byte(tmp_path):
    skill_path = tmp_path / "SKILL.md"
    original_text = _write_skill_md(
        skill_path,
        {
            "name": "implement",
            "description": "Execute an approved plan and tasks list, one task at a time.",
            "version": "0.2.0",
            "requires": ["constitution"],
            "handoffs": ["finishing-a-branch"],
        },
    )
    original_body = original_text.split("---", 2)[2]

    changed = migrate_skill_file(skill_path)

    assert changed is True
    new_text = skill_path.read_text(encoding="utf-8")
    new_body = new_text.split("---", 2)[2]
    assert new_body == original_body

    new_fm_text = new_text.split("---", 2)[1]
    new_fm = yaml.safe_load(new_fm_text)
    assert "version" not in new_fm
    assert "requires" not in new_fm
    assert "handoffs" not in new_fm
    assert new_fm["metadata"]["aiadev"]["version"] == "0.2.0"
    assert new_fm["metadata"]["aiadev"]["requires"] == ["constitution"]
    assert new_fm["metadata"]["aiadev"]["handoffs"] == ["finishing-a-branch"]
    assert new_fm["name"] == "implement"
    assert new_fm["description"] == (
        "Execute an approved plan and tasks list, one task at a time."
    )


def test_migrate_skill_file_noop_returns_false_and_leaves_file_byte_identical(tmp_path):
    skill_path = tmp_path / "SKILL.md"
    original_text = _write_skill_md(
        skill_path,
        {
            "name": "finishing-a-branch",
            "description": "Wrap up an approved branch after review passes cleanly.",
        },
    )

    changed = migrate_skill_file(skill_path)

    assert changed is False
    assert skill_path.read_text(encoding="utf-8") == original_text


def test_migrate_skill_file_key_order_is_deterministic(tmp_path):
    skill_path = tmp_path / "SKILL.md"
    _write_skill_md(
        skill_path,
        {
            "name": "implement",
            "description": "Execute an approved plan and tasks list, one task at a time.",
            "version": "0.2.0",
            "inputs": [{"type": "file", "path": "specs/<branch>/plan.md"}],
            "requires": ["constitution"],
            "license": "MIT",
            "handoffs": ["finishing-a-branch"],
        },
    )

    migrate_skill_file(skill_path)

    new_text = skill_path.read_text(encoding="utf-8")
    new_fm_text = new_text.split("---", 2)[1]
    new_fm = yaml.safe_load(new_fm_text)
    keys = list(new_fm.keys())
    # name and description always come first, in that order.
    assert keys[0] == "name"
    assert keys[1] == "description"
    # license (a surviving original-order field) still precedes metadata,
    # since metadata is appended (new or moved to the end) deterministically.
    assert keys.index("license") < keys.index("metadata")


def test_migrate_skill_file_idempotent_second_run_is_noop(tmp_path):
    skill_path = tmp_path / "SKILL.md"
    _write_skill_md(
        skill_path,
        {
            "name": "implement",
            "description": "Execute an approved plan and tasks list, one task at a time.",
            "version": "0.2.0",
            "requires": ["constitution"],
        },
    )

    first = migrate_skill_file(skill_path)
    assert first is True
    text_after_first = skill_path.read_text(encoding="utf-8")

    second = migrate_skill_file(skill_path)
    assert second is False
    assert skill_path.read_text(encoding="utf-8") == text_after_first


# ---------------------------------------------------------------------------
# failure modes
# ---------------------------------------------------------------------------


def test_migrate_frontmatter_rejects_non_dict_input():
    with pytest.raises(FrontmatterError, match="not a mapping"):
        migrate_frontmatter(["a", "b"])  # YAML frontmatter parsed to a list


def test_migrate_skill_file_malformed_yaml_raises_frontmatter_error(tmp_path):
    skill_path = tmp_path / "SKILL.md"
    skill_path.write_text(
        "---\nname: [unclosed\ndescription: broken\n---\n\n# Body\n",
        encoding="utf-8",
    )

    with pytest.raises(FrontmatterError, match="malformed YAML frontmatter") as exc:
        migrate_skill_file(skill_path)
    assert str(skill_path) in str(exc.value)


def test_migrate_skill_file_non_dict_frontmatter_raises_frontmatter_error(tmp_path):
    skill_path = tmp_path / "SKILL.md"
    skill_path.write_text("---\n- a\n- b\n---\n\n# Body\n", encoding="utf-8")

    with pytest.raises(FrontmatterError, match="not a mapping") as exc:
        migrate_skill_file(skill_path)
    assert str(skill_path) in str(exc.value)


def test_migrate_skill_file_without_frontmatter_raises_frontmatter_error(tmp_path):
    skill_path = tmp_path / "SKILL.md"
    skill_path.write_text("# Just a heading\n\nNo frontmatter here.\n", encoding="utf-8")

    with pytest.raises(FrontmatterError, match="missing YAML frontmatter") as exc:
        migrate_skill_file(skill_path)
    assert str(skill_path) in str(exc.value)


def test_migrate_skill_file_unterminated_frontmatter_raises_frontmatter_error(tmp_path):
    skill_path = tmp_path / "SKILL.md"
    skill_path.write_text(
        "---\nname: my-skill\ndescription: never closed\n\n# Body without closing delimiter\n",
        encoding="utf-8",
    )

    with pytest.raises(FrontmatterError, match="unterminated YAML frontmatter") as exc:
        migrate_skill_file(skill_path)
    assert str(skill_path) in str(exc.value)


def test_frontmatter_error_messages_are_single_line(tmp_path):
    skill_path = tmp_path / "SKILL.md"
    skill_path.write_text(
        "---\nname: [unclosed\ndescription: broken\n---\n\n# Body\n",
        encoding="utf-8",
    )

    with pytest.raises(FrontmatterError) as exc:
        migrate_skill_file(skill_path)
    assert "\n" not in str(exc.value)
