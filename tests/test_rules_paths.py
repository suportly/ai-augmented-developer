"""Tests for T008: ``paths:`` rule-frontmatter propagation per platform.

Story 2 (sc1-sc3) of specs/0016-agent-skills-interop/spec.md + ADR-6 in
plan.md: rules may declare an optional ``paths: [globs]`` list in their
YAML frontmatter. At install time:

* claude-code: installs the rule with ``paths:`` intact, and if the rule
  declares ``paths:`` the installed output must NOT carry
  ``alwaysApply: true`` (paths-scoped rules are conditional).
* codex / opencode / gemini: install with the ``paths:`` key stripped
  from the frontmatter (today's behavior otherwise preserved).
* Rules WITHOUT ``paths:``: installed byte-identical to today's behavior
  on all four platforms (the feature is opt-in per rule).

No glob evaluation happens anywhere in aiadev — this is pure declaration
transport through each platform's ``render_target`` hook, mirroring the
existing Gemini command md->TOML mechanism.

Cursor is out of scope here (T009 handles the ``.mdc`` translation).
"""
from __future__ import annotations

import pathlib

import pytest
import yaml

from aiadev.platforms import claude_code, codex, gemini, opencode

PLATFORMS_STRIP_PATHS = (codex, opencode, gemini)
ALL_PLATFORMS = (claude_code, codex, opencode, gemini)


def _frontmatter(text: str) -> dict:
    assert text.startswith("---\n"), "expected a YAML frontmatter block"
    _, _, rest = text.partition("---\n")
    fm_text, _, _ = rest.partition("\n---\n")
    parsed = yaml.safe_load(fm_text)
    assert isinstance(parsed, dict)
    return parsed


RULE_WITH_PATHS = """---
description: Only applies to Python source files.
alwaysApply: true
paths:
  - "**/*.py"
  - "src/**"
---

# Python-only rule

Body content that should survive untouched.
"""

RULE_WITHOUT_PATHS = """---
description: Baseline rule with no paths scoping.
alwaysApply: true
---

# Always-applies rule

Body content, unrelated to paths.
"""


class TestClaudeCodeKeepsPaths:
    def test_rule_with_paths_keeps_paths_key(self) -> None:
        rendered = claude_code.render_target("rule", "python-only", RULE_WITH_PATHS)
        fm = _frontmatter(rendered)
        assert fm["paths"] == ["**/*.py", "src/**"]

    def test_rule_with_paths_drops_always_apply(self) -> None:
        rendered = claude_code.render_target("rule", "python-only", RULE_WITH_PATHS)
        fm = _frontmatter(rendered)
        assert "alwaysApply" not in fm or fm["alwaysApply"] is not True

    def test_rule_with_paths_preserves_body(self) -> None:
        rendered = claude_code.render_target("rule", "python-only", RULE_WITH_PATHS)
        assert "Body content that should survive untouched." in rendered

    def test_rule_without_paths_is_byte_identical(self) -> None:
        rendered = claude_code.render_target("rule", "baseline", RULE_WITHOUT_PATHS)
        assert rendered == RULE_WITHOUT_PATHS


class TestOtherPlatformsStripPaths:
    @pytest.mark.parametrize("platform", PLATFORMS_STRIP_PATHS)
    def test_rule_with_paths_strips_paths_key(self, platform) -> None:
        rendered = platform.render_target("rule", "python-only", RULE_WITH_PATHS)
        fm = _frontmatter(rendered)
        assert "paths" not in fm

    @pytest.mark.parametrize("platform", PLATFORMS_STRIP_PATHS)
    def test_rule_with_paths_strip_does_not_error(self, platform) -> None:
        # No exception, and the rest of the frontmatter / body survives.
        rendered = platform.render_target("rule", "python-only", RULE_WITH_PATHS)
        fm = _frontmatter(rendered)
        assert fm.get("alwaysApply") is True
        assert fm.get("description") == "Only applies to Python source files."
        assert "Body content that should survive untouched." in rendered

    @pytest.mark.parametrize("platform", PLATFORMS_STRIP_PATHS)
    def test_rule_without_paths_is_byte_identical(self, platform) -> None:
        rendered = platform.render_target("rule", "baseline", RULE_WITHOUT_PATHS)
        assert rendered == RULE_WITHOUT_PATHS


class TestMalformedRulePassthrough:
    """Malformed rule inputs must pass through byte-identical, silently.

    Story 2 sc2 guarantees "no error, no warning" — the transform only
    acts on well-formed frontmatter; anything else is not this layer's
    problem and must survive untouched on every platform.
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

    @pytest.mark.parametrize("platform", ALL_PLATFORMS)
    @pytest.mark.parametrize("text", MALFORMED_INPUTS)
    def test_malformed_input_passes_through_byte_identical(
        self, platform, text: str
    ) -> None:
        rendered = platform.render_target("rule", "weird", text)
        assert rendered == text


class TestNonRuleRolesUnaffected:
    @pytest.mark.parametrize("platform", ALL_PLATFORMS)
    def test_non_rule_role_passthrough_unchanged(self, platform) -> None:
        # Sanity: the new rule-transform branch must not leak into other
        # roles' render_target behavior for plain text roles.
        text = "plain agent file content, no frontmatter here\n"
        rendered = platform.render_target("agent_file", "", text)
        assert rendered == text


class TestInstallEngineEndToEnd:
    """Exercise the full install pipeline for a rule with ``paths:``.

    Mirrors the tmp_path preset-fixture pattern used across
    ``tests/test_install_*.py``: build a minimal preset on disk, run
    ``aiadev.install_engine.install`` for each platform, and assert on
    the installed rule file's frontmatter.
    """

    @pytest.fixture
    def preset_with_paths_rule(self, tmp_path: pathlib.Path) -> pathlib.Path:
        preset_root = tmp_path / "preset"
        rules_dir = preset_root / "rules"
        rules_dir.mkdir(parents=True)
        (rules_dir / "python-only.md").write_text(RULE_WITH_PATHS, encoding="utf-8")
        (rules_dir / "baseline.md").write_text(RULE_WITHOUT_PATHS, encoding="utf-8")
        (preset_root / "CLAUDE.md").write_text("Agent file body.\n", encoding="utf-8")
        (preset_root / "preset.yaml").write_text(
            "name: paths-test\nversion: 0.0.1\n", encoding="utf-8"
        )
        return preset_root

    def test_claude_code_install_keeps_paths_and_drops_always_apply(
        self, preset_with_paths_rule: pathlib.Path, tmp_path: pathlib.Path
    ) -> None:
        from aiadev.install_engine import install

        project = tmp_path / "project"
        project.mkdir()
        install(
            preset_with_paths_rule,
            project,
            {},
            platform="claude_code",
            allow_unresolved=True,
        )
        installed = project / ".claude" / "rules" / "python-only.md"
        assert installed.is_file()
        fm = _frontmatter(installed.read_text(encoding="utf-8"))
        assert fm["paths"] == ["**/*.py", "src/**"]
        assert fm.get("alwaysApply") is not True

    @pytest.mark.parametrize(
        "platform_name,rules_subdir",
        [
            ("codex", ".codex"),
            ("opencode", ".opencode"),
            ("gemini", ".gemini"),
        ],
    )
    def test_other_platforms_install_strips_paths(
        self,
        preset_with_paths_rule: pathlib.Path,
        tmp_path: pathlib.Path,
        platform_name: str,
        rules_subdir: str,
    ) -> None:
        from aiadev.install_engine import install

        project = tmp_path / f"project-{platform_name}"
        project.mkdir()
        install(
            preset_with_paths_rule,
            project,
            {},
            platform=platform_name,
            allow_unresolved=True,
        )
        installed = project / rules_subdir / "rules" / "python-only.md"
        assert installed.is_file()
        fm = _frontmatter(installed.read_text(encoding="utf-8"))
        assert "paths" not in fm

    def test_baseline_rule_byte_identical_across_platforms(
        self, preset_with_paths_rule: pathlib.Path, tmp_path: pathlib.Path
    ) -> None:
        from aiadev.install_engine import install

        targets = {
            "claude_code": (".claude", claude_code),
            "codex": (".codex", codex),
            "opencode": (".opencode", opencode),
            "gemini": (".gemini", gemini),
        }
        for platform_name, (subdir, _module) in targets.items():
            project = tmp_path / f"baseline-{platform_name}"
            project.mkdir()
            install(
                preset_with_paths_rule,
                project,
                {},
                platform=platform_name,
                allow_unresolved=True,
            )
            installed = project / subdir / "rules" / "baseline.md"
            assert installed.is_file()
            assert installed.read_text(encoding="utf-8") == RULE_WITHOUT_PATHS
