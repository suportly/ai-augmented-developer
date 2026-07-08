"""T011 — AGENTS.md as the canonical agent file the sync writes into.

Spec: specs/0016-agent-skills-interop/spec.md, Story 3 scenario 1 + 4.
Plan: ADR-5 — ``_PLATFORM_AGENT_FILE`` converges on ``AGENTS.md`` as the
destination for generated content (including the
``<!-- aiadev:auto-stack -->`` block). The claude-code and gemini
handlers now emit ``CLAUDE.md`` / ``GEMINI.md`` as thin (~3 line)
wrappers pointing at ``AGENTS.md``; cursor/codex/opencode already share
``AGENTS.md`` as their one physical agent file and keep doing so.

Scope note: this task covers a *fresh* install/sync producing the
canonical layout. Preserving/migrating hand-edited content that already
lives in a consumer's CLAUDE.md/AGENTS.md is T012's job, not this one.
"""
from __future__ import annotations

import pathlib

import pytest
from click.testing import CliRunner

from aiadev.commands.install import install_command
from aiadev.commands.sync import sync_command
from aiadev.install_manifest import load as load_manifest


def _install(
    project: pathlib.Path,
    *,
    platform: str | None = None,
    project_name: str = "CanonDemo",
) -> object:
    runner = CliRunner()
    args = [
        "--project-root",
        str(project),
        "--preset",
        "lean",
        "--non-interactive",
        "--vars",
        f"PROJECT_NAME={project_name}",
    ]
    if platform is not None:
        args += ["--platform", platform]
    return runner.invoke(install_command, args)


def _sync(project: pathlib.Path, *, platform: str | None = None):
    runner = CliRunner()
    args = ["--project-root", str(project)]
    if platform is not None:
        args += ["--platform", platform]
    return runner.invoke(sync_command, args)


@pytest.fixture
def claude_project(isolated_framework: pathlib.Path, tmp_path: pathlib.Path, monkeypatch):
    monkeypatch.setenv("AIADEV_ROOT", str(isolated_framework))
    project = tmp_path / "claude-consumer"
    project.mkdir()
    result = _install(project, platform="claude-code")
    assert result.exit_code == 0, result.output
    return project


@pytest.fixture
def gemini_project(isolated_framework: pathlib.Path, tmp_path: pathlib.Path, monkeypatch):
    monkeypatch.setenv("AIADEV_ROOT", str(isolated_framework))
    project = tmp_path / "gemini-consumer"
    project.mkdir()
    result = _install(project, platform="gemini")
    assert result.exit_code == 0, result.output
    return project


class TestClaudeCodeCanonicalLayout:
    def test_fresh_install_writes_agents_md_and_claude_wrapper(
        self, claude_project: pathlib.Path
    ):
        agents_md = claude_project / "AGENTS.md"
        claude_md = claude_project / "CLAUDE.md"
        assert agents_md.is_file()
        assert claude_md.is_file()
        assert "CanonDemo" in agents_md.read_text(encoding="utf-8")

    def test_claude_wrapper_is_short_and_points_at_agents_md(
        self, claude_project: pathlib.Path
    ):
        claude_md = claude_project / "CLAUDE.md"
        text = claude_md.read_text(encoding="utf-8")
        lines = [line for line in text.splitlines() if line.strip()]
        assert len(lines) <= 5
        assert "AGENTS.md" in text

    def test_sync_writes_stack_block_only_in_agents_md(
        self, claude_project: pathlib.Path
    ):
        result = _sync(claude_project)
        assert result.exit_code == 0, result.output

        agents_text = (claude_project / "AGENTS.md").read_text(encoding="utf-8")
        claude_text = (claude_project / "CLAUDE.md").read_text(encoding="utf-8")

        assert "<!-- aiadev:auto-stack:start -->" in agents_text
        assert "<!-- aiadev:auto-stack:start -->" not in claude_text
        assert "## Detected stack" not in claude_text

    def test_second_sync_is_a_noop_no_false_conflicts(
        self, claude_project: pathlib.Path
    ):
        first = _sync(claude_project)
        assert first.exit_code == 0, first.output

        second = _sync(claude_project)
        assert second.exit_code == 0, second.output
        assert "conflict" not in second.output.lower()

    def test_manifest_tracks_both_agent_files_with_correct_hashes(
        self, claude_project: pathlib.Path
    ):
        result = _sync(claude_project)
        assert result.exit_code == 0, result.output

        manifest_path = claude_project / ".aiadev" / "installed.yaml"
        manifest = load_manifest(manifest_path)
        preset = manifest.find_preset("lean")
        assert preset is not None

        by_path = {f.path: f for f in preset.files}
        assert "AGENTS.md" in by_path
        assert "CLAUDE.md" in by_path
        assert by_path["AGENTS.md"].role == "agent_file"
        assert by_path["CLAUDE.md"].role == "agent_file"

        from aiadev.install_manifest import compute_sha256

        assert by_path["AGENTS.md"].sha256 == compute_sha256(
            claude_project / "AGENTS.md"
        )
        assert by_path["CLAUDE.md"].sha256 == compute_sha256(
            claude_project / "CLAUDE.md"
        )


class TestGeminiCanonicalLayout:
    def test_fresh_install_writes_agents_md_and_gemini_wrapper(
        self, gemini_project: pathlib.Path
    ):
        agents_md = gemini_project / "AGENTS.md"
        gemini_md = gemini_project / "GEMINI.md"
        assert agents_md.is_file()
        assert gemini_md.is_file()
        assert "CanonDemo" in agents_md.read_text(encoding="utf-8")
        assert not (gemini_project / "CLAUDE.md").exists()

    def test_gemini_wrapper_is_short_and_points_at_agents_md(
        self, gemini_project: pathlib.Path
    ):
        text = (gemini_project / "GEMINI.md").read_text(encoding="utf-8")
        lines = [line for line in text.splitlines() if line.strip()]
        assert len(lines) <= 5
        assert "AGENTS.md" in text

    def test_sync_writes_stack_block_only_in_agents_md(
        self, gemini_project: pathlib.Path
    ):
        result = _sync(gemini_project)
        assert result.exit_code == 0, result.output

        agents_text = (gemini_project / "AGENTS.md").read_text(encoding="utf-8")
        gemini_text = (gemini_project / "GEMINI.md").read_text(encoding="utf-8")

        assert "<!-- aiadev:auto-stack:start -->" in agents_text
        assert "<!-- aiadev:auto-stack:start -->" not in gemini_text


class TestCursorCodexShareAgentsMd:
    def test_cursor_and_codex_handlers_resolve_the_same_agent_file_path(
        self, tmp_path: pathlib.Path
    ):
        """cursor and codex must target the identical physical file.

        No divergent per-platform copy: both handlers' ``agent_file``
        role resolves to the same ``AGENTS.md`` path under a shared
        project root, so installing/syncing either platform reads and
        writes the one file (sha256-skip semantics apply as today).
        """
        from aiadev.platforms import codex, cursor, opencode

        cursor_target = cursor.resolve_target("agent_file", "", tmp_path)
        codex_target = codex.resolve_target("agent_file", "", tmp_path)
        opencode_target = opencode.resolve_target("agent_file", "", tmp_path)

        assert cursor_target == tmp_path / "AGENTS.md"
        assert codex_target == tmp_path / "AGENTS.md"
        assert opencode_target == tmp_path / "AGENTS.md"
        assert cursor_target == codex_target == opencode_target

    def test_codex_install_alone_produces_single_agents_md_no_wrapper(
        self, isolated_framework: pathlib.Path, tmp_path: pathlib.Path, monkeypatch
    ):
        monkeypatch.setenv("AIADEV_ROOT", str(isolated_framework))
        project = tmp_path / "codex-consumer"
        project.mkdir()

        result = _install(project, platform="codex", project_name="MultiDemo")
        assert result.exit_code == 0, result.output

        assert (project / "AGENTS.md").is_file()
        assert not (project / "CLAUDE.md").exists()
        assert not (project / "GEMINI.md").exists()

        sync_result = _sync(project, platform="codex")
        assert sync_result.exit_code == 0, sync_result.output
        assert "conflict" not in sync_result.output.lower()

    def test_sync_stack_block_lands_in_agents_md_for_cursor(
        self, isolated_framework: pathlib.Path, tmp_path: pathlib.Path, monkeypatch
    ):
        monkeypatch.setenv("AIADEV_ROOT", str(isolated_framework))
        project = tmp_path / "cursor-consumer"
        project.mkdir()
        result = _install(project, platform="cursor")
        assert result.exit_code == 0, result.output

        sync_result = _sync(project, platform="cursor")
        assert sync_result.exit_code == 0, sync_result.output

        agents_text = (project / "AGENTS.md").read_text(encoding="utf-8")
        assert "<!-- aiadev:auto-stack:start -->" in agents_text
