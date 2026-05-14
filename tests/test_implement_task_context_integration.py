"""Content tests for ``skills/implement/SKILL.md`` task-context integration.

Spec: ``specs/0014-bmad-inspired-evolutions/spec.md`` Story 1 sc2 and sc3.

T019 adds an opt-in section to the implement skill that wires in the
``task-context`` skill (T018) ahead of the implementer dispatch:

- sc2: when task-context is enabled (preset flag or CLI flag), the
  implementer prompt is replaced by a SHORT prompt that references the
  composed per-task context file by path, instead of inlining the
  ``Spec context`` / ``Plan context`` / ``Files to create or modify``
  blocks.
- sc3: when task-context is NOT enabled (default off), the existing
  inline implementer prompt runs byte-for-byte unchanged. The new
  integration is purely additive.

These tests assert the SKILL.md content carries the wiring, the
preserved default behavior, and the staleness contract.
"""
from __future__ import annotations

import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
SKILL = ROOT / "skills" / "implement" / "SKILL.md"


def _read() -> str:
    return SKILL.read_text(encoding="utf-8")


def _section(text: str, heading: str) -> str:
    """Return the slice of ``text`` from ``heading`` (an H2 ``## `` line)
    up to the next H2 heading, exclusive."""
    start = text.index(heading)
    try:
        end = text.index("\n## ", start + 1)
    except ValueError:
        end = len(text)
    return text[start:end]


def test_task_context_integration_section_exists() -> None:
    """A dedicated H2 (or H3) section documents the integration so a
    reader scanning the file finds it without grepping the loop steps."""
    text = _read()
    assert (
        "## Task-context integration" in text
        or "### Task-context integration" in text
    ), "implement SKILL.md missing a Task-context integration section"


def test_integration_mentions_opt_in_triggers() -> None:
    """sc2/sc3: both opt-in triggers are documented — the preset flag
    AND the preflight CLI flag. Either one activates the integration."""
    text = _read()
    assert "task_context: true" in text, (
        "integration section must reference the preset.yaml `task_context: true` flag"
    )
    assert "--task-context" in text, (
        "integration section must reference the `--task-context` preflight flag"
    )
    assert "preset.yaml" in text, (
        "integration section must point at preset.yaml as the per-preset switch"
    )


def test_integration_invokes_task_context_helper() -> None:
    """The orchestrator composes the per-task context BEFORE dispatching
    the implementer. The skill describes invoking the helper (the
    ``aiadev.task_context.compose`` callable referenced by the
    task-context skill)."""
    text = _read()
    assert "aiadev.task_context" in text, (
        "integration must describe invoking the aiadev.task_context helper"
    )
    assert "compose" in text, (
        "integration must mention the compose() entry point"
    )
    assert "task-context" in text, (
        "integration must reference the task-context skill by name"
    )


def test_integration_replaces_inline_prompt_with_path_loader() -> None:
    """sc2: when active, the implementer receives a SHORT prompt that
    points at the composed file by path, rather than the inline
    Spec context / Plan context / Files-to-modify blocks."""
    text = _read()
    assert "task-context/" in text, (
        "integration must show the task-context file path the implementer reads"
    )
    # The short prompt must instruct the implementer to read the file
    # before doing anything else — not just receive it as ambient context.
    assert "Read it first" in text or "read it first" in text, (
        "short prompt must instruct the implementer to read the task-context file first"
    )


def test_integration_documents_staleness_check() -> None:
    """The orchestrator skips recompose when the existing brief is
    fresh (``is_stale()`` returns False) — keeps the same artifact
    across retries within a session."""
    text = _read()
    assert "is_stale" in text, (
        "integration must describe the is_stale() staleness check"
    )


def test_integration_preserves_default_inline_prompt_unchanged() -> None:
    """sc3: when NEITHER trigger is set, the existing inline prompt
    runs byte-for-byte unchanged. The original ``## Implementer prompt``
    H2 section and its ``Spec context`` / ``Plan context`` /
    ``Files to create or modify`` markers must still be present."""
    text = _read()
    assert "## Implementer prompt" in text, (
        "default ## Implementer prompt section must still exist (sc3)"
    )

    inline_block = _section(text, "## Implementer prompt")
    for marker in (
        "Spec context (relevant excerpt only):",
        "Plan context:",
        "Files to create or modify:",
    ):
        assert marker in inline_block, (
            f"default Implementer prompt block missing inline marker: {marker!r}"
        )


def test_integration_explicitly_calls_out_backward_compatibility() -> None:
    """sc3: the new section spells out that without the flags the
    existing behavior runs unchanged — purely additive."""
    text = _read()
    assert "byte-for-byte unchanged" in text or "purely additive" in text, (
        "integration must explicitly preserve sc3 backward compatibility"
    )
