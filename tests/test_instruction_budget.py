"""T007-T009 — instruction budget: always-loaded cost per preset and the
pipeline path (spec 0030, Story 4).

``scripts/instruction_budget.py`` estimates "tokens" as ceil(chars / 4) (no
tokenizer) and sums what the Claude Code platform loads without being
invoked: the wrapper ``CLAUDE.md``, ``AGENTS.md``, rules WITHOUT a ``paths:``
frontmatter key, and only the ``name`` + ``description`` frontmatter of
skills, commands and agents (a command's name is derived from its path:
``.claude/commands/aia/plan.md`` -> ``aia:plan``).

Unit tests drive ``measure_always_loaded`` against a hand-built project tree;
the integration tests install real presets through the CLI route.

T008 adds the pipeline path: ``docs/pipeline-path.yaml`` lists, per stage of
``specify -> finish``, the framework files the default route reads;
``measure_pipeline_path`` sums ceil(chars / 4) per file, per stage, and fails
(strictly, unlike the optional ``AGENTS.md``) when a cited file is missing.

T009 adds the ratchet: ``docs/instruction-budget.json`` versions a ``baseline``
(the pre-cut measurement) and a ``teto`` (ceiling) per key. ``check_budget``
fails when a measurement exceeds its ``teto``; a ``teto`` above the
``baseline`` needs a ``reason``. One test runs the real measurement against
the committed file: that is the CI catraca (it runs in the pytest job).
"""
from __future__ import annotations

import importlib.util
import json
import math
import os
import pathlib
import re
import subprocess
import sys
import textwrap

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "instruction_budget.py"

COMPONENTS = ("agent_file", "wrapper", "rules", "skills", "commands", "agents")

UNIT = "ceil(chars/4)"


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


# --- unit: pipeline path (T008) -------------------------------------------


def _framework(
    tmp_path: pathlib.Path, path_yaml: str, files: dict[str, str] | None = None
) -> pathlib.Path:
    """A tiny framework tree: *files* on disk plus ``docs/pipeline-path.yaml``."""
    framework = tmp_path / "framework"
    framework.mkdir(exist_ok=True)
    for rel, text in (files or {}).items():
        _write(framework / rel, text)
    _write(framework / "docs" / "pipeline-path.yaml", textwrap.dedent(path_yaml))
    return framework


def test_pipeline_path_sums_ceil_tokens_per_file_then_per_stage(budget, tmp_path):
    framework = _framework(
        tmp_path,
        """\
        stages:
          - name: one
            files: [a.md, d.md]
          - name: two
            files: [b.md, c.md]
        """,
        {"a.md": "a", "d.md": "d", "b.md": "b" * 5, "c.md": "c" * 9},
    )

    result = budget.measure_pipeline_path(framework)

    # ceil per file (1 + 1 = 2), not ceil of the summed characters (2 / 4 = 1).
    assert result["stages"] == {"one": 2, "two": 5}
    assert result["files"] == {"a.md": 1, "d.md": 1, "b.md": 2, "c.md": 3}
    assert result["total"] == 7 == sum(result["stages"].values())


def test_pipeline_path_counts_characters_not_bytes(budget, tmp_path):
    framework = _framework(
        tmp_path,
        "stages:\n  - name: s\n    files: [pt.md]\n",
        {"pt.md": "ação"},  # 4 characters, 6 bytes
    )
    assert budget.measure_pipeline_path(framework)["total"] == 1


def test_pipeline_path_preserves_the_order_of_the_file(budget, tmp_path):
    framework = _framework(
        tmp_path,
        """\
        stages:
          - {name: zeta, files: [z.md, a.md]}
          - {name: alpha, files: [m.md]}
          - {name: mid, files: [b.md]}
        """,
        {name: "x" for name in ("z.md", "a.md", "m.md", "b.md")},
    )

    result = budget.measure_pipeline_path(framework)

    assert list(result["stages"]) == ["zeta", "alpha", "mid"]
    assert list(result["files"]) == ["z.md", "a.md", "m.md", "b.md"]


def test_only_listed_files_count_so_conditional_references_stay_out(budget, tmp_path):
    """The path is the list, not the directory: ``review-gate.md`` is read by
    the default route and is cited; ``task-context.md`` sits on disk but is
    conditional, so it is not."""
    gate = "skills/requesting-code-review/references/review-gate.md"
    framework = _framework(
        tmp_path,
        f"""\
        stages:
          - name: requesting-code-review
            files: [skills/requesting-code-review/SKILL.md, {gate}]
        """,
        {
            "skills/requesting-code-review/SKILL.md": "s" * 8,
            gate: "g" * 40,
            "skills/implement/references/task-context.md": "t" * 4000,
        },
    )

    result = budget.measure_pipeline_path(framework)

    assert result["files"] == {"skills/requesting-code-review/SKILL.md": 2, gate: 10}
    assert result["total"] == 12


def test_a_file_listed_in_two_stages_counts_in_both(budget, tmp_path):
    """A file the route reads again at a later stage is paid for again (the
    constitution at ``plan`` and at ``implement``): stage figures are what each
    stage reads, so ``total`` is the sum of stages and can exceed the sum of
    the distinct files. ``files`` lists each distinct file once, under one
    spelling (``./constitution.md`` is ``constitution.md``)."""
    framework = _framework(
        tmp_path,
        """\
        stages:
          - {name: plan, files: [constitution.md, plan.md]}
          - {name: implement, files: ['./constitution.md']}
        """,
        {"constitution.md": "c" * 40, "plan.md": "p" * 8},
    )

    result = budget.measure_pipeline_path(framework)

    assert result["stages"] == {"plan": 12, "implement": 10}
    assert result["total"] == 22
    assert result["files"] == {"constitution.md": 10, "plan.md": 2}


def test_a_file_listed_twice_in_one_stage_is_rejected_whatever_the_spelling(
    budget, tmp_path
):
    framework = _framework(
        tmp_path,
        "stages:\n  - {name: plan, files: ['./a.md', a.md]}\n",
        {"a.md": "a"},
    )
    with pytest.raises(budget.PipelinePathError, match=r"'plan'.*a\.md.*more than once"):
        budget.measure_pipeline_path(framework)


def test_a_stage_name_listed_twice_is_rejected(budget, tmp_path):
    framework = _framework(
        tmp_path,
        "stages:\n  - {name: plan, files: [a.md]}\n  - {name: plan, files: [a.md]}\n",
        {"a.md": "a"},
    )
    with pytest.raises(budget.PipelinePathError, match="'plan'.*more than once"):
        budget.measure_pipeline_path(framework)


def test_a_cited_file_that_does_not_exist_fails_naming_it(budget, tmp_path):
    """Unlike an optional ``AGENTS.md`` (0 when absent), a path file that
    vanished must not silently shrink the budget."""
    framework = _framework(
        tmp_path,
        """\
        stages:
          - name: plan
            files: [skills/plan/SKILL.md, skills/gone/SKILL.md]
        """,
        {"skills/plan/SKILL.md": "plan"},
    )

    with pytest.raises(budget.PipelinePathError, match="does not exist or is not a file") as excinfo:
        budget.measure_pipeline_path(framework)

    message = str(excinfo.value)
    assert "skills/gone/SKILL.md" in message
    assert "'plan'" in message  # the stage that cites it


def test_a_cited_directory_is_not_a_file(budget, tmp_path):
    framework = _framework(
        tmp_path, "stages:\n  - {name: plan, files: [skills]}\n", {"skills/x.md": "x"}
    )
    with pytest.raises(budget.PipelinePathError, match="does not exist or is not a file"):
        budget.measure_pipeline_path(framework)


def test_a_missing_path_file_fails_naming_it(budget, tmp_path):
    with pytest.raises(budget.PipelinePathError, match="pipeline-path.yaml"):
        budget.measure_pipeline_path(tmp_path / "empty-framework")


def test_a_path_file_that_is_not_utf8_is_a_value_error(budget, tmp_path):
    """No wrapper: ``main`` reports any ``ValueError`` as ``FAIL``, and a
    ``UnicodeDecodeError`` is one."""
    framework = _framework(tmp_path, "stages: []\n")
    (framework / "docs" / "pipeline-path.yaml").write_bytes(b"stages: \xff\xfe\n")
    with pytest.raises(ValueError):
        budget.measure_pipeline_path(framework)


def test_malformed_yaml_fails_clearly(budget, tmp_path):
    framework = _framework(
        tmp_path, "stages:\n  - {name: plan, files: [a.md\n", {"a.md": "a"}
    )
    with pytest.raises(budget.PipelinePathError, match="invalid YAML"):
        budget.measure_pipeline_path(framework)


@pytest.mark.parametrize(
    ("path_yaml", "match"),
    [
        pytest.param("", "non-empty 'stages' list", id="empty-file"),
        pytest.param("stages: []\n", "non-empty 'stages' list", id="stages-empty"),
        pytest.param("stages:\n  - {name: plan}\n", "stage #1 needs", id="files-absent"),
        pytest.param(
            "stages:\n  - {name: plan, files: []}\n", "stage #1 needs", id="files-empty"
        ),
        pytest.param(
            "stages:\n  - {name: plan, files: [3]}\n", "stage #1 needs", id="file-not-a-string"
        ),
    ],
)
def test_malformed_structure_fails_clearly(budget, tmp_path, path_yaml, match):
    framework = _framework(tmp_path, path_yaml, {"a.md": "a"})
    with pytest.raises(budget.PipelinePathError, match=match):
        budget.measure_pipeline_path(framework)


@pytest.mark.parametrize("cited", ["/etc/hosts", "../outside.md"])
def test_cited_paths_must_stay_under_the_framework_root(budget, tmp_path, cited):
    framework = _framework(
        tmp_path, f"stages:\n  - {{name: plan, files: ['{cited}']}}\n", {"a.md": "a"}
    )
    with pytest.raises(budget.PipelinePathError, match="relative to the framework root"):
        budget.measure_pipeline_path(framework)


def test_real_pipeline_path_measures_the_framework_tree(budget):
    """Strict: every cited file exists, or this raises. The invariants pin the
    plan's decisions without re-parsing the YAML."""
    result = budget.measure_pipeline_path()
    files = result["files"]

    assert result["total"] > 0
    # requesting-code-review dispatches the code-reviewer agent, so it counts there.
    assert result["stages"]["requesting-code-review"] >= (
        files["skills/requesting-code-review/SKILL.md"] + files["agents/code-reviewer.md"]
    )
    # Conditional (opt-in) integration stays off the default route.
    assert not [f for f in files if "task-context" in f]


# --- CLI ------------------------------------------------------------------


def test_main_prints_one_block_per_preset_and_exits_zero(budget, capsys):
    assert budget.main(["lean"]) == 0
    out = capsys.readouterr().out
    assert "lean" in out
    for name in (*COMPONENTS, "total"):
        assert name in out
    assert "OK" in out


def test_main_prints_the_pipeline_path_after_the_presets(budget, capsys):
    assert budget.main(["lean"]) == 0
    out = capsys.readouterr().out
    result = budget.measure_pipeline_path()

    assert out.index("OK   lean:") < out.index("OK   pipeline path:")
    for name, tokens in result["stages"].items():
        assert re.search(rf"^\s+{re.escape(name)}\s+{tokens}$", out, re.MULTILINE), name
    assert f"OK   pipeline path: ~{result['total']} tokens (chars / 4)" in out


def test_main_fails_with_exit_1_when_the_path_cites_a_missing_file(
    budget, tmp_path, monkeypatch, capsys
):
    """Only the path is broken: the presets are stubbed to succeed so the
    exit code and the FAIL line can only come from the path block."""
    framework = _framework(
        tmp_path, "stages:\n  - {name: plan, files: [skills/gone/SKILL.md]}\n"
    )
    real = budget.measure_pipeline_path
    monkeypatch.setattr(budget, "install_preset", lambda preset, dest: None)
    monkeypatch.setattr(
        budget,
        "measure_always_loaded",
        lambda root: {**{name: 0 for name in COMPONENTS}, "total": 0},
    )
    monkeypatch.setattr(budget, "measure_pipeline_path", lambda *a, **k: real(framework))

    assert budget.main(["lean"]) == 1

    out = capsys.readouterr().out
    assert "OK   lean:" in out
    assert re.search(r"^FAIL pipeline path: .*skills/gone/SKILL\.md", out, re.MULTILINE)
    assert "OK   pipeline path" not in out


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


# --- unit: budget, check_budget and write_baseline (T009) ------------------


def _budget(entries: dict) -> dict:
    return {"version": 1, "unit": UNIT, "entries": entries}


def _entry(baseline: int, teto: int | None = None, **extra) -> dict:
    return {"baseline": baseline, "teto": baseline if teto is None else teto, **extra}


def test_check_budget_passes_at_the_teto_and_below(budget):
    limits = _budget({"skill:plan": _entry(100), "path:total": _entry(500, 400)})
    assert budget.check_budget({"skill:plan": 100, "path:total": 400}, limits) == []
    assert budget.check_budget({"skill:plan": 3, "path:total": 0}, limits) == []


def test_one_token_over_the_teto_fails_naming_key_current_teto_and_delta(budget):
    limits = _budget({"skill:plan": _entry(100)})
    assert budget.check_budget({"skill:plan": 101}, limits) == [
        "FAIL skill:plan: 101 > teto 100 (+1)"
    ]


def test_the_delta_is_measured_against_the_teto_not_the_baseline(budget):
    limits = _budget({"preset:lean:total": _entry(1000, 900)})
    assert budget.check_budget({"preset:lean:total": 990}, limits) == [
        "FAIL preset:lean:total: 990 > teto 900 (+90)"
    ]


def test_every_exceeded_entry_gets_its_own_line(budget):
    limits = _budget(
        {"a": _entry(10), "b": _entry(10), "c": _entry(10), "path:x.md": _entry(5)}
    )
    lines = budget.check_budget({"a": 11, "b": 10, "c": 15, "path:x.md": 6}, limits)
    assert lines == [
        "FAIL a: 11 > teto 10 (+1)",
        "FAIL c: 15 > teto 10 (+5)",
        "FAIL path:x.md: 6 > teto 5 (+1)",
    ]


def test_a_measured_key_absent_from_the_budget_is_not_a_failure(budget):
    limits = _budget({"skill:plan": _entry(100)})
    assert budget.check_budget({"skill:plan": 100, "skill:new": 99999}, limits) == []


def test_a_budget_entry_that_is_no_longer_measured_is_ignored(budget):
    limits = _budget({"skill:plan": _entry(100), "skill:gone": _entry(1)})
    assert budget.check_budget({"skill:plan": 100}, limits) == []


@pytest.mark.parametrize(
    "extra",
    [{}, {"reason": ""}, {"reason": "   "}, {"reason": None}, {"reason": 3}],
    ids=["absent", "empty", "blank", "null", "not-a-string"],
)
def test_a_teto_above_the_baseline_without_a_reason_is_a_malformed_budget(budget, extra):
    limits = _budget({"skill:plan": _entry(100, 120, **extra)})
    lines = budget.check_budget({"skill:plan": 100}, limits)

    assert len(lines) == 1
    assert lines[0].startswith("FAIL skill:plan: ")
    assert "teto 120 > baseline 100" in lines[0]
    assert "reason" in lines[0]


def test_a_malformed_entry_fails_even_when_it_is_no_longer_measured(budget):
    limits = _budget({"skill:gone": _entry(100, 120)})
    assert len(budget.check_budget({}, limits)) == 1


def test_a_teto_above_the_baseline_with_a_reason_is_accepted(budget):
    limits = _budget({"skill:plan": _entry(100, 120, reason="new review gate (spec 0031)")})
    assert budget.check_budget({"skill:plan": 120}, limits) == []
    assert budget.check_budget({"skill:plan": 121}, limits) == [
        "FAIL skill:plan: 121 > teto 120 (+1)"
    ]


def test_write_baseline_records_every_measurement_as_baseline_and_teto(budget, tmp_path):
    target = tmp_path / "instruction-budget.json"
    measured = {"preset:lean:total": 1000, "path:total": 2000, "skill:plan": 300}

    budget.write_baseline(target, measured)

    text = target.read_text(encoding="utf-8")
    assert text.endswith("\n")
    assert json.loads(text) == {
        "version": 1,
        "unit": UNIT,
        "entries": {key: {"baseline": n, "teto": n} for key, n in measured.items()},
    }
    assert budget.check_budget(measured, budget.load_budget(target)) == []


@pytest.mark.parametrize(
    ("content", "match"),
    [
        pytest.param("{not json", "invalid JSON", id="not-json"),
        pytest.param("[]", "JSON object", id="not-an-object"),
        pytest.param(json.dumps({"version": 2, "unit": UNIT, "entries": {}}), "version", id="version"),
        pytest.param(json.dumps({"version": 1, "unit": "words", "entries": {}}), "unit", id="unit"),
        pytest.param(json.dumps({"version": 1, "unit": UNIT}), "entries", id="no-entries"),
        pytest.param(
            json.dumps({"version": 1, "unit": UNIT, "entries": {"k": {"baseline": "9", "teto": 9}}}),
            "k.*baseline",
            id="baseline-not-int",
        ),
        pytest.param(
            json.dumps({"version": 1, "unit": UNIT, "entries": {"k": 9}}), "k", id="entry-not-object"
        ),
    ],
)
def test_load_budget_rejects_a_malformed_file(budget, tmp_path, content, match):
    target = _write(tmp_path / "instruction-budget.json", content)
    with pytest.raises(budget.BudgetError, match=match):
        budget.load_budget(target)


def test_load_budget_names_a_missing_file(budget, tmp_path):
    with pytest.raises(budget.BudgetError, match="not found"):
        budget.load_budget(tmp_path / "nope.json")


# --- unit: skill keys (T009) -----------------------------------------------


def test_measure_skills_counts_each_whole_skill_file_under_its_directory_name(
    budget, tmp_path
):
    framework = tmp_path / "framework"
    plan = "---\nname: plan\ndescription: d\n---\n" + "body " * 10
    _write(framework / "skills" / "plan" / "SKILL.md", plan)
    _write(framework / "skills" / "tasks" / "SKILL.md", "t" * 5)
    _write(framework / "skills" / "plan" / "references" / "gate.md", "g" * 4000)
    _write(framework / "skills" / "README.md", "r" * 4000)

    assert budget.measure_skills(framework) == {
        "skill:plan": _tokens(plan),
        "skill:tasks": 2,
    }


# --- the committed budget and the CI ratchet (T009) ------------------------


@pytest.fixture(scope="module")
def measured_repo(budget):
    return budget.measure_all()


HEADLINE = {"preset:lean:total", "preset:django-drf-react:total", "path:total"}


def test_repo_is_within_the_committed_budget(budget, measured_repo):
    """The CI catraca: nothing measured may exceed its ``teto``. To raise one,
    edit docs/instruction-budget.json with a ``reason`` (reviewed in the PR).

    The headline keys must be both budgeted and measured: ``check_budget``
    skips keys that do not match, so a budget whose keys were renamed would
    otherwise pass while checking nothing."""
    data = budget.load_budget(budget.BUDGET_FILE)
    assert HEADLINE <= data["entries"].keys() & measured_repo.keys()

    failures = budget.check_budget(measured_repo, data)
    assert not failures, "\n".join(failures)


# --- CLI: --check / --write-baseline (T009) --------------------------------


@pytest.fixture
def stubbed(budget, monkeypatch):
    """Deterministic measurements, so the CLI tests exercise only the budget
    logic. Keys: 2 presets x (6 components + total), the path and one skill."""
    monkeypatch.setattr(budget, "install_preset", lambda preset, dest: None)
    monkeypatch.setattr(
        budget,
        "measure_always_loaded",
        lambda root: {**{name: 1 for name in COMPONENTS}, "total": 6},
    )
    monkeypatch.setattr(
        budget,
        "measure_pipeline_path",
        lambda *a, **k: {
            "stages": {"plan": 7},
            "files": {"skills/plan/SKILL.md": 7},
            "total": 7,
        },
    )
    monkeypatch.setattr(budget, "measure_skills", lambda *a, **k: {"skill:plan": 9})


def test_write_baseline_then_check_passes_and_reports_the_blocks(
    budget, stubbed, tmp_path, capsys
):
    target = tmp_path / "instruction-budget.json"

    assert budget.main(["--write-baseline", "--budget", str(target)]) == 0
    entries = json.loads(target.read_text(encoding="utf-8"))["entries"]
    assert entries["preset:lean:total"] == {"baseline": 6, "teto": 6}
    assert entries["path:total"] == {"baseline": 7, "teto": 7}
    assert entries["skill:plan"] == {"baseline": 9, "teto": 9}
    assert entries["path:skills/plan/SKILL.md"] == {"baseline": 7, "teto": 7}
    assert entries["preset:django-drf-react:rules"] == {"baseline": 1, "teto": 1}
    capsys.readouterr()

    assert budget.main(["--check", "--budget", str(target)]) == 0

    out = capsys.readouterr().out
    assert "OK   lean:" in out
    assert "OK   django-drf-react:" in out
    assert "OK   pipeline path:" in out
    assert "OK   budget" in out
    assert "FAIL" not in out


def test_check_fails_with_exit_1_naming_the_key_and_the_delta(
    budget, stubbed, tmp_path, capsys
):
    target = tmp_path / "instruction-budget.json"
    budget.write_baseline(
        target,
        {"preset:lean:total": 6, "path:total": 6, "skill:plan": 9},
    )

    assert budget.main(["--check", "--budget", str(target)]) == 1

    out = capsys.readouterr().out
    assert re.findall(r"^FAIL .*$", out, re.MULTILINE) == [
        "FAIL path:total: 7 > teto 6 (+1)"
    ]
    assert "OK   budget" not in out


def test_check_reports_a_missing_budget_file(budget, stubbed, tmp_path, capsys):
    target = tmp_path / "nope.json"

    assert budget.main(["--check", "--budget", str(target)]) == 1

    out = capsys.readouterr().out
    assert re.search(r"^FAIL .*nope\.json", out, re.MULTILINE)


def test_check_fails_when_no_budget_entry_matches_the_measurement(
    budget, stubbed, tmp_path, capsys
):
    target = tmp_path / "instruction-budget.json"
    budget.write_baseline(target, {"preset:renamed:total": 1000})

    assert budget.main(["--check", "--budget", str(target)]) == 1

    out = capsys.readouterr().out
    assert "FAIL budget: no budget entry matches the current measurement" in out
    assert "OK   budget" not in out


def test_check_does_not_judge_the_budget_when_a_measurement_failed(
    budget, stubbed, tmp_path, monkeypatch, capsys
):
    target = tmp_path / "instruction-budget.json"
    budget.write_baseline(target, {"path:total": 999})

    def boom(*args, **kwargs):
        raise budget.PipelinePathError("cannot measure")

    monkeypatch.setattr(budget, "measure_pipeline_path", boom)

    assert budget.main(["--check", "--budget", str(target)]) == 1

    out = capsys.readouterr().out
    assert "FAIL pipeline path: cannot measure" in out
    assert "OK   budget" not in out


def test_write_baseline_refuses_to_overwrite_from_the_cli_unless_forced(
    budget, stubbed, tmp_path, capsys
):
    target = _write(tmp_path / "instruction-budget.json", "keep me")

    assert budget.main(["--write-baseline", "--budget", str(target)]) == 1
    out = capsys.readouterr().out
    assert "--force" in out
    assert target.read_text(encoding="utf-8") == "keep me"

    assert budget.main(["--write-baseline", "--force", "--budget", str(target)]) == 0
    assert json.loads(target.read_text(encoding="utf-8"))["version"] == 1


@pytest.mark.parametrize(
    "argv",
    [
        ["--check", "--write-baseline"],
        ["--check", "lean"],
        ["--write-baseline", "lean"],
    ],
    ids=["both-modes", "check-with-preset", "write-with-preset"],
)
def test_incompatible_options_are_a_usage_error(budget, argv):
    with pytest.raises(SystemExit) as excinfo:
        budget.main(argv)
    assert excinfo.value.code == 2
