"""T019 — aiadev sync ships the terse-mode rule and the help skill.

``framework_artifacts.iter_framework_artifacts`` auto-discovers any
``rules/*.md`` and ``skills/*/SKILL.md`` under the framework root, so no
code change is needed; this test is the evidence that the discovery
covers the new assets.
"""

from pathlib import Path

from aiadev.framework_artifacts import iter_framework_artifacts

ROOT = Path(__file__).resolve().parents[1]


def test_terse_mode_rule_is_discovered():
    artifacts = list(iter_framework_artifacts(ROOT))
    rules = [(role, name, path) for role, name, path in artifacts if role == "rule"]
    names = {name for _, name, _ in rules}
    assert "terse-mode" in names, (
        f"aiadev sync must pick up the terse-mode rule; discovered rules: {sorted(names)}"
    )


def test_help_skill_is_discovered():
    artifacts = list(iter_framework_artifacts(ROOT))
    skills = [(role, name, path) for role, name, path in artifacts if role == "skill"]
    names = {name for _, name, _ in skills}
    assert "help" in names, (
        f"aiadev sync must pick up the help skill; discovered skills: {sorted(names)}"
    )


def test_discovered_artifact_paths_resolve():
    artifacts = list(iter_framework_artifacts(ROOT))
    for role, name, path in artifacts:
        assert path.exists(), f"{role} '{name}' resolves to missing path {path}"
