"""Tests for T009: ``paths:`` -> Cursor ``.mdc`` glob translation.

Story 2 sc4 of specs/0016-agent-skills-interop/spec.md + ADR-6: Cursor's
native rule format (``.cursor/rules/<name>.mdc``) is documented to use
``description`` / ``globs`` / ``alwaysApply`` frontmatter keys, where
``globs`` is a comma-separated string (Cursor's frontmatter parser is
non-standard YAML, and the comma-separated-string form is the safer,
widely-used convention — see the docstring on
``cursor._render_rule_frontmatter`` for the full rationale).

At install time:

* A rule with ``paths: [a, b]`` installs with ``paths:`` replaced by
  ``globs: a,b`` and ``alwaysApply: false`` forced (paths-scoped rules
  are conditional, never "always apply", on Cursor).
* A rule without ``paths:`` installs byte-identical to today's
  behavior (opt-in feature).
* Malformed inputs (mirroring T008's four cases) pass through
  byte-identical, silently.
* End-to-end: installing a preset with a paths-scoped rule into a tmp
  workspace via ``aiadev.install_engine.install`` produces the
  expected ``.cursor/rules/<name>.mdc`` content on disk.
"""
from __future__ import annotations

import pathlib

import pytest
import yaml

from aiadev.platforms import cursor


def _frontmatter(text: str) -> dict:
    assert text.startswith("---\n"), "expected a YAML frontmatter block"
    _, _, rest = text.partition("---\n")
    fm_text, _, _ = rest.partition("\n---\n")
    parsed = yaml.safe_load(fm_text)
    assert isinstance(parsed, dict)
    return parsed


RULE_WITH_PATHS = """---
description: Only applies to test files.
alwaysApply: true
paths:
  - "tests/**"
  - "**/*.test.*"
---

# Test-only rule

Body content that should survive untouched.
"""

RULE_WITHOUT_PATHS = """---
description: Baseline rule with no paths scoping.
alwaysApply: true
---

# Always-applies rule

Body content, unrelated to paths.
"""


class TestCursorTranslatesPathsToGlobs:
    def test_rule_with_paths_gets_globs_key(self) -> None:
        rendered = cursor.render_target("rule", "test-only", RULE_WITH_PATHS)
        fm = _frontmatter(rendered)
        assert "paths" not in fm
        assert "globs" in fm

    def test_globs_is_comma_separated_string_with_both_patterns(self) -> None:
        rendered = cursor.render_target("rule", "test-only", RULE_WITH_PATHS)
        fm = _frontmatter(rendered)
        globs = fm["globs"]
        assert isinstance(globs, str)
        patterns = [p.strip() for p in globs.split(",")]
        assert patterns == ["tests/**", "**/*.test.*"]

    def test_rule_with_paths_forces_always_apply_false(self) -> None:
        rendered = cursor.render_target("rule", "test-only", RULE_WITH_PATHS)
        fm = _frontmatter(rendered)
        assert fm["alwaysApply"] is False

    def test_rule_with_paths_preserves_body(self) -> None:
        rendered = cursor.render_target("rule", "test-only", RULE_WITH_PATHS)
        assert "Body content that should survive untouched." in rendered

    def test_rule_with_paths_preserves_description(self) -> None:
        rendered = cursor.render_target("rule", "test-only", RULE_WITH_PATHS)
        fm = _frontmatter(rendered)
        assert fm.get("description") == "Only applies to test files."

    def test_rule_without_paths_is_byte_identical(self) -> None:
        rendered = cursor.render_target("rule", "baseline", RULE_WITHOUT_PATHS)
        assert rendered == RULE_WITHOUT_PATHS


class TestMalformedRulePassthrough:
    """Malformed rule inputs must pass through byte-identical, silently.

    Mirrors T008's ``TestMalformedRulePassthrough`` guarantee: the
    transform only acts on well-formed frontmatter containing a
    ``paths:`` key; anything else survives untouched.
    """

    MALFORMED_INPUTS = (
        pytest.param("# just a body, no frontmatter at all\n", id="no-frontmatter"),
        pytest.param(
            "---\ndescription: [unclosed\n---\n\n# body\n", id="malformed-yaml"
        ),
        pytest.param("---\n- a\n- b\n---\n\n# body\n", id="non-dict-frontmatter"),
        pytest.param(
            "---\ndescription: never closed\n\n# body without closing fence\n",
            id="unterminated-frontmatter",
        ),
    )

    @pytest.mark.parametrize("text", MALFORMED_INPUTS)
    def test_malformed_input_passes_through_byte_identical(self, text: str) -> None:
        rendered = cursor.render_target("rule", "weird", text)
        assert rendered == text


class TestNonRuleRolesUnaffected:
    def test_non_rule_role_passthrough_unchanged(self) -> None:
        text = "plain agent file content, no frontmatter here\n"
        rendered = cursor.render_target("agent_file", "", text)
        assert rendered == text


class TestInstallEngineEndToEnd:
    """Exercise the full install pipeline for a rule with ``paths:``.

    Mirrors the tmp_path preset-fixture pattern used in
    ``tests/test_rules_paths.py``'s ``TestInstallEngineEndToEnd``.
    """

    @pytest.fixture
    def preset_with_paths_rule(self, tmp_path: pathlib.Path) -> pathlib.Path:
        preset_root = tmp_path / "preset"
        rules_dir = preset_root / "rules"
        rules_dir.mkdir(parents=True)
        (rules_dir / "test-only.md").write_text(RULE_WITH_PATHS, encoding="utf-8")
        (rules_dir / "baseline.md").write_text(RULE_WITHOUT_PATHS, encoding="utf-8")
        (preset_root / "CLAUDE.md").write_text("Agent file body.\n", encoding="utf-8")
        (preset_root / "preset.yaml").write_text(
            "name: paths-cursor-test\nversion: 0.0.1\n", encoding="utf-8"
        )
        return preset_root

    def test_cursor_install_translates_paths_to_globs(
        self, preset_with_paths_rule: pathlib.Path, tmp_path: pathlib.Path
    ) -> None:
        from aiadev.install_engine import install

        project = tmp_path / "project"
        project.mkdir()
        install(
            preset_with_paths_rule,
            project,
            {},
            platform="cursor",
            allow_unresolved=True,
        )
        installed = project / ".cursor" / "rules" / "test-only.mdc"
        assert installed.is_file()
        fm = _frontmatter(installed.read_text(encoding="utf-8"))
        assert "paths" not in fm
        patterns = [p.strip() for p in fm["globs"].split(",")]
        assert patterns == ["tests/**", "**/*.test.*"]
        assert fm["alwaysApply"] is False

    def test_baseline_rule_byte_identical(
        self, preset_with_paths_rule: pathlib.Path, tmp_path: pathlib.Path
    ) -> None:
        from aiadev.install_engine import install

        project = tmp_path / "project"
        project.mkdir()
        install(
            preset_with_paths_rule,
            project,
            {},
            platform="cursor",
            allow_unresolved=True,
        )
        installed = project / ".cursor" / "rules" / "baseline.mdc"
        assert installed.is_file()
        assert installed.read_text(encoding="utf-8") == RULE_WITHOUT_PATHS
