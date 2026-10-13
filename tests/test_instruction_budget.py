"""T007 — instruction budget: always-loaded cost per preset (spec 0030, Story 4).

``scripts/instruction_budget.py`` estimates "tokens" as ceil(chars / 4) (no
tokenizer) and sums what the Claude Code platform loads without being
invoked: the wrapper ``CLAUDE.md``, ``AGENTS.md``, rules WITHOUT a ``paths:``
frontmatter key, and only the ``name`` + ``description`` frontmatter of
skills, commands and agents (a command's name is derived from its path:
``.claude/commands/aia/plan.md`` -> ``aia:plan``).

Unit tests drive ``measure_always_loaded`` against a hand-built project tree;
the integration tests install real presets through the CLI route.
"""
from __future__ import annotations

import importlib.util
import math
import os
import pathlib
import subprocess
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "instruction_budget.py"

COMPONENTS = ("agent_file", "wrapper", "rules", "skills", "commands", "agents")


@pytest.fixture(scope="module")
def budget():
    """The script as a module (scripts/ is not a package)."""
    assert SCRIPT.is_file(), f"expected {SCRIPT} to exist"
    spec = importlib.util.spec_from_file_location("instruction_budget", SCRIPT)
    module = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


def _tokens(text: str) -> int:
    return math.ceil(len(text) / 4)


def _write(path: pathlib.Path, text: str) -> pathlib.Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _project(tmp_path: pathlib.Path) -> pathlib.Path:
    project = tmp_path / "project"
    project.mkdir()
    return project


# --- unit: agent file + wrapper -------------------------------------------


def test_empty_project_measures_zero(budget, tmp_path):
    counts = budget.measure_always_loaded(_project(tmp_path))
    assert counts == {**{name: 0 for name in COMPONENTS}, "total": 0}


@pytest.mark.parametrize(
    ("chars", "expected"), [(0, 0), (1, 1), (4, 1), (5, 2), (8, 2), (9, 3)]
)
def test_tokens_are_ceil_of_chars_over_4(budget, tmp_path, chars, expected):
    project = _project(tmp_path)
    _write(project / "AGENTS.md", "a" * chars)
    counts = budget.measure_always_loaded(project)
    assert counts["agent_file"] == expected


def test_agent_file_and_wrapper_are_counted_in_full(budget, tmp_path):
    project = _project(tmp_path)
    agents = "# Agents\n\n" + "rule text. " * 20  # 10 + 220 chars
    wrapper = "# AGENTS.md\n\nRead that file first.\n"
    _write(project / "AGENTS.md", agents)
    _write(project / "CLAUDE.md", wrapper)

    counts = budget.measure_always_loaded(project)

    assert counts["agent_file"] == _tokens(agents) == 58
    assert counts["wrapper"] == _tokens(wrapper)
    assert counts["total"] == counts["agent_file"] + counts["wrapper"]


def test_characters_are_counted_not_bytes(budget, tmp_path):
    project = _project(tmp_path)
    _write(project / "AGENTS.md", "ação")  # 4 characters, 6 bytes
    assert budget.measure_always_loaded(project)["agent_file"] == 1


# --- unit: rules ----------------------------------------------------------


def test_rules_with_paths_are_conditional_and_excluded(budget, tmp_path):
    project = _project(tmp_path)
    rules = project / ".claude" / "rules"
    always = (
        "---\ndescription: Always on.\nalwaysApply: true\n---\n\n# Always\n\nBody text.\n"
    )
    no_frontmatter = "# Terse\n\nNo frontmatter at all, so it is always loaded.\n"
    conditional = (
        "---\ndescription: Only for tests.\npaths:\n- tests/**\n- conftest.py\n---\n\n"
        "# Testing\n\n" + "long conditional body " * 50
    )
    _write(rules / "always.md", always)
    _write(rules / "terse.md", no_frontmatter)
    _write(rules / "testing.md", conditional)

    counts = budget.measure_always_loaded(project)

    # Whole file (frontmatter included) for every always-loaded rule; none
    # of the conditional rule.
    assert counts["rules"] == _tokens(always) + _tokens(no_frontmatter)
    assert counts["total"] == counts["rules"]


def test_rule_with_empty_paths_key_still_counts_as_always_loaded(budget, tmp_path):
    project = _project(tmp_path)
    rule = "---\ndescription: Empty paths.\npaths: []\n---\n\n# R\n"
    _write(project / ".claude" / "rules" / "r.md", rule)
    assert budget.measure_always_loaded(project)["rules"] == _tokens(rule)


def test_rules_in_subdirectories_are_found(budget, tmp_path):
    project = _project(tmp_path)
    rule = "# Nested rule\n\nBody.\n"
    _write(project / ".claude" / "rules" / "team" / "nested.md", rule)
    assert budget.measure_always_loaded(project)["rules"] == _tokens(rule)


# --- unit: skills, commands, agents (frontmatter only) --------------------


def test_skill_counts_only_name_and_description(budget, tmp_path):
    project = _project(tmp_path)
    skill = (
        "---\n"
        "name: plan\n"
        "description: Turn an approved spec into a plan.\n"
        "metadata:\n"
        "  aiadev:\n"
        "    version: 0.2.0\n"
        "    handoffs:\n"
        "    - tasks\n"
        "---\n\n"
        "# Plan\n\n" + "A very long skill body that must not be counted. " * 100
    )
    _write(project / ".claude" / "skills" / "plan" / "SKILL.md", skill)

    counts = budget.measure_always_loaded(project)

    expected = _tokens("name: plan\ndescription: Turn an approved spec into a plan.")
    assert counts["skills"] == expected
    assert counts["skills"] < _tokens(skill)


def test_skills_sum_ceil_per_file(budget, tmp_path):
    project = _project(tmp_path)
    skills = project / ".claude" / "skills"
    # Each listing is 22 chars -> 6 tokens. Per-file ceil gives 6 + 6 = 12;
    # ceil of the summed chars (44 / 4) would give 11, so this pins the rule.
    for name in ("a", "b"):
        _write(
            skills / name / "SKILL.md",
            f"---\nname: {name}\ndescription: x\n---\nbody\n",
        )
    counts = budget.measure_always_loaded(project)
    assert _tokens("name: a\ndescription: x") == 6
    assert counts["skills"] == 12


def test_command_counts_derived_name_and_description(budget, tmp_path):
    """Commands carry no ``name`` in frontmatter; Claude Code exposes them as
    ``<namespace>:<stem>`` (``.claude/commands/aia/plan.md`` -> ``aia:plan``)."""
    project = _project(tmp_path)
    command = (
        "---\n"
        "description: Turn an approved spec.md into a plan.md.\n"
        "allowed-tools: Read, Write, Edit, Glob, Grep, Bash\n"
        'argument-hint: "<optional: feature dir under specs/>"\n'
        "---\n\n"
        "Invoke the `plan` skill. " + "Instruction body. " * 50
    )
    _write(project / ".claude" / "commands" / "aia" / "plan.md", command)

    counts = budget.measure_always_loaded(project)

    assert counts["commands"] == _tokens(
        "name: aia:plan\n"
        "description: Turn an approved spec.md into a plan.md."
    )


def test_command_name_comes_from_the_path_relative_to_commands(budget, tmp_path):
    project = _project(tmp_path)
    commands = project / ".claude" / "commands"
    _write(commands / "top.md", "---\ndescription: d\n---\n")
    _write(commands / "team" / "deep" / "ship.md", "---\ndescription: d\n---\n")

    counts = budget.measure_always_loaded(project)

    assert counts["commands"] == _tokens("name: top\ndescription: d") + _tokens(
        "name: team:deep:ship\ndescription: d"
    )


def test_command_frontmatter_name_wins_over_the_derived_one(budget, tmp_path):
    project = _project(tmp_path)
    _write(
        project / ".claude" / "commands" / "aia" / "plan.md",
        "---\nname: custom-plan\ndescription: d\n---\n",
    )
    counts = budget.measure_always_loaded(project)
    assert counts["commands"] == _tokens("name: custom-plan\ndescription: d")


def test_agent_counts_only_name_and_description(budget, tmp_path):
    project = _project(tmp_path)
    agent = (
        "---\n"
        "name: code-reviewer\n"
        "description: Reviews code for bugs and returns APPROVED or CHANGES_REQUESTED.\n"
        "tools: Read, Glob, Grep, Bash\n"
        "model: sonnet\n"
        "---\n\n"
        "# Code Reviewer\n\n" + "Long reviewer prompt. " * 100
    )
    _write(project / ".claude" / "agents" / "code-reviewer.md", agent)

    counts = budget.measure_always_loaded(project)

    assert counts["agents"] == _tokens(
        "name: code-reviewer\n"
        "description: Reviews code for bugs and returns APPROVED or CHANGES_REQUESTED."
    )


def test_folded_multiline_description_counts_like_a_plain_one(budget, tmp_path):
    project = _project(tmp_path)
    folded = "---\nname: x\ndescription: >\n  Turn a spec\n  into a plan.\n---\nbody\n"
    plain = "---\nname: x\ndescription: Turn a spec into a plan.\n---\nbody\n"
    _write(project / ".claude" / "skills" / "folded" / "SKILL.md", folded)
    folded_tokens = budget.measure_always_loaded(project)["skills"]

    other = tmp_path / "other"
    other.mkdir()
    _write(other / ".claude" / "skills" / "plain" / "SKILL.md", plain)
    assert folded_tokens == budget.measure_always_loaded(other)["skills"]


def test_listed_components_without_frontmatter_contribute_nothing(budget, tmp_path):
    project = _project(tmp_path)
    body = "# No frontmatter\n\n" + "text " * 100
    _write(project / ".claude" / "skills" / "bare" / "SKILL.md", body)
    _write(project / ".claude" / "commands" / "aia" / "bare.md", body)
    _write(project / ".claude" / "agents" / "bare.md", body)

    counts = budget.measure_always_loaded(project)

    assert counts["skills"] == counts["commands"] == counts["agents"] == 0
    assert counts["total"] == 0


def test_frontmatter_that_strict_yaml_rejects_is_still_measured(budget, tmp_path):
    """An unquoted ``: `` in a description is invalid YAML, yet the platform
    reads it (``commands/finishing-a-branch.md`` does exactly this)."""
    project = _project(tmp_path)
    description = "description: Finalize an approved branch: push, open PR, and clean up."
    _write(
        project / ".claude" / "commands" / "aia" / "finish.md",
        f"---\n{description}\nallowed-tools: Read\n---\n\n" + "body " * 100,
    )
    _write(
        project / ".claude" / "skills" / "odd" / "SKILL.md",
        "---\nname: odd\ndescription: Does X: then Y.\n---\n" + "body " * 100,
    )

    counts = budget.measure_always_loaded(project)

    assert counts["commands"] == _tokens(f"name: aia:finish\n{description}")
    assert counts["skills"] == _tokens("name: odd\ndescription: Does X: then Y.")


def test_conditional_rule_that_strict_yaml_rejects_is_still_excluded(budget, tmp_path):
    project = _project(tmp_path)
    rule = (
        "---\ndescription: Only for tests: yes.\npaths:\n- tests/**\n---\n\n"
        "# Testing\n\n" + "body " * 100
    )
    _write(project / ".claude" / "rules" / "testing.md", rule)
    assert budget.measure_always_loaded(project)["rules"] == 0


def test_total_is_the_sum_of_components(budget, tmp_path):
    project = _project(tmp_path)
    _write(project / "AGENTS.md", "agents file")
    _write(project / "CLAUDE.md", "wrapper")
    _write(project / ".claude" / "rules" / "r.md", "# rule\n")
    _write(
        project / ".claude" / "skills" / "s" / "SKILL.md",
        "---\nname: s\ndescription: d\n---\n",
    )
    _write(project / ".claude" / "commands" / "aia" / "c.md", "---\ndescription: d\n---\n")
    _write(project / ".claude" / "agents" / "a.md", "---\nname: a\ndescription: d\n---\n")

    counts = budget.measure_always_loaded(project)

    assert set(counts) == {*COMPONENTS, "total"}
    assert all(counts[name] > 0 for name in COMPONENTS)
    assert counts["total"] == sum(counts[name] for name in COMPONENTS)


# --- integration: real install through the CLI route ----------------------


@pytest.mark.parametrize("preset", ["lean", "django-drf-react"])
def test_real_install_through_cli_route_is_measured(budget, tmp_path, preset):
    project = tmp_path / preset
    budget.install_preset(preset, project)

    agents_md = (project / "AGENTS.md").read_text(encoding="utf-8")
    # The CLI route applies preset.yaml defaults; nothing is left unresolved
    # (django-drf-react declares BACKEND_DIR, FRONTEND_DIR, GCP_* defaults).
    assert "{{" not in agents_md

    counts = budget.measure_always_loaded(project)

    for name in COMPONENTS:
        assert counts[name] > 0, f"{preset}: component {name} measured zero"
    assert counts["total"] == sum(counts[name] for name in COMPONENTS)

    # Conditional rules (frontmatter ``paths:``) are excluded from the total.
    rule_files = sorted((project / ".claude" / "rules").rglob("*.md"))
    every_rule = sum(_tokens(p.read_text(encoding="utf-8")) for p in rule_files)
    assert any("paths:" in p.read_text(encoding="utf-8") for p in rule_files)
    assert counts["rules"] < every_rule


# --- CLI ------------------------------------------------------------------


def test_main_prints_one_block_per_preset_and_exits_zero(budget, capsys):
    assert budget.main(["lean"]) == 0
    out = capsys.readouterr().out
    assert "lean" in out
    for name in (*COMPONENTS, "total"):
        assert name in out
    assert "OK" in out


def test_install_preset_raises_for_an_unknown_preset(budget, tmp_path):
    with pytest.raises(RuntimeError, match="no-such-preset"):
        budget.install_preset("no-such-preset", tmp_path / "p")


def test_main_reports_an_install_failure_and_exits_1(budget, monkeypatch, capsys):
    def boom(preset, dest):
        raise RuntimeError("boom")

    monkeypatch.setattr(budget, "install_preset", boom)

    assert budget.main(["lean"]) == 1
    assert "FAIL lean: boom" in capsys.readouterr().out


def test_script_is_executable():
    assert os.access(SCRIPT, os.X_OK), f"{SCRIPT} must be chmod +x (Usage runs it directly)"


def test_main_unknown_preset_fails_with_exit_1(budget, capsys):
    assert budget.main(["no-such-preset"]) == 1
    out = capsys.readouterr().out
    assert "FAIL" in out and "no-such-preset" in out


@pytest.mark.parametrize(
    ("module", "hint"), [("yaml", "pyyaml"), ("aiadev.commands.install", "aiadev")]
)
def test_missing_dependency_exits_2_with_a_message(
    budget, monkeypatch, capsys, module, hint
):
    monkeypatch.setitem(sys.modules, module, None)  # makes `import` raise
    assert budget.main(["lean"]) == 2
    err = capsys.readouterr().err
    assert "error:" in err and hint in err


def test_script_runs_standalone_without_pythonpath_from_any_directory(tmp_path):
    env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "lean"],
        capture_output=True,
        text=True,
        env=env,
        cwd=tmp_path,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "lean" in result.stdout and "total" in result.stdout
