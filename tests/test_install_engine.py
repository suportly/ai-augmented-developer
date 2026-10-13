"""Tests for :mod:`aiadev.install_engine`.

The engine's behaviour is exercised end-to-end against the
``tests/fixtures/mini-preset/`` fixture introduced by T003. Every
branch the spec cares about (install, idempotent re-install, conflict,
force, dry-run, unresolved placeholders, uninstall, uninstall with
conflicts, uninstall with force) has a dedicated test.
"""
from __future__ import annotations

import hashlib
import pathlib
import shutil

import pytest

from aiadev.install_engine import (
    InstallError,
    InstallMode,
    _collect_skill_references,
    install,
)
from aiadev.install_manifest import (
    InstalledFile,
    Manifest,
    compute_sha256,
    load as load_manifest,
    save as save_manifest,
)
from aiadev.placeholders import find_unresolved

FIXTURES = pathlib.Path(__file__).parent / "fixtures" / "mini-preset"
VARIABLES = {"PROJECT_NAME": "Demo App", "GREETING": "Howdy"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _agent_file(project_root: pathlib.Path) -> pathlib.Path:
    """The canonical agent file (spec 0016 Story 3, ADR-5)."""
    return project_root / "AGENTS.md"


def _wrapper_file(project_root: pathlib.Path) -> pathlib.Path:
    """The thin claude-code wrapper pointing at :func:`_agent_file`."""
    return project_root / "CLAUDE.md"


# platform -> where that platform keeps ``<skill>/SKILL.md`` (the layout
# the handlers produce); a reference must land in the same skill directory.
_SKILLS_DIR = {
    "claude_code": ".claude/skills",
    "codex": ".codex/skills",
    "gemini": ".gemini/skills",
    "cursor": ".cursor/skills",
    "opencode": ".opencode/skills",
}


def _skill_file(project_root: pathlib.Path, name: str) -> pathlib.Path:
    return project_root / ".claude" / "skills" / name / "SKILL.md"


def _reference_file(
    project_root: pathlib.Path, platform: str = "claude_code"
) -> pathlib.Path:
    """The mini-preset's ``hello-world/references/stack.md`` once installed."""
    skills_dir = project_root / _SKILLS_DIR[platform]
    return skills_dir / "hello-world" / "references" / "stack.md"


def _manifest_file(project_root: pathlib.Path) -> pathlib.Path:
    return project_root / ".aiadev" / "installed.yaml"


# ---------------------------------------------------------------------------
# Fresh install
# ---------------------------------------------------------------------------


class TestFreshInstall:
    def test_writes_agent_file_and_skill(self, tmp_path: pathlib.Path) -> None:
        report = install(FIXTURES, tmp_path, VARIABLES, now="2026-04-14T12:00:00Z")

        assert report.mode is InstallMode.INSTALL
        assert report.ok
        assert _agent_file(tmp_path).is_file()
        assert _skill_file(tmp_path, "hello-world").is_file()

        agent_text = _agent_file(tmp_path).read_text(encoding="utf-8")
        assert "Demo App" in agent_text
        assert "Howdy" in agent_text
        assert find_unresolved(agent_text) == []  # every placeholder resolved

        skill_text = _skill_file(tmp_path, "hello-world").read_text(encoding="utf-8")
        assert "Demo App" in skill_text
        assert find_unresolved(skill_text) == []

    def test_writes_thin_claude_md_wrapper_pointing_at_agents_md(
        self, tmp_path: pathlib.Path
    ) -> None:
        """Spec 0016 Story 3 / ADR-5: claude-code emits a wrapper too."""
        install(FIXTURES, tmp_path, VARIABLES, now="2026-04-14T12:00:00Z")
        wrapper_text = _wrapper_file(tmp_path).read_text(encoding="utf-8")
        assert "AGENTS.md" in wrapper_text
        assert len([line for line in wrapper_text.splitlines() if line.strip()]) <= 5

    def test_writes_manifest(self, tmp_path: pathlib.Path) -> None:
        install(FIXTURES, tmp_path, VARIABLES, now="2026-04-14T12:00:00Z")
        manifest_path = _manifest_file(tmp_path)
        assert manifest_path.is_file()
        manifest = load_manifest(manifest_path)
        record = manifest.find_preset("mini")
        assert record is not None
        assert record.variables == VARIABLES
        assert {f.role for f in record.files} == {"agent_file", "skill"}
        # Both the canonical agent file and its wrapper are tracked.
        paths = {f.path for f in record.files}
        assert "AGENTS.md" in paths
        assert "CLAUDE.md" in paths

    def test_report_lists_every_new_file(self, tmp_path: pathlib.Path) -> None:
        report = install(FIXTURES, tmp_path, VARIABLES, now="2026-04-14T12:00:00Z")
        assert sorted(p.name for p in report.written) == sorted(
            [
                _agent_file(tmp_path).name,
                _wrapper_file(tmp_path).name,
                "SKILL.md",
                "stack.md",
            ]
        )
        assert report.skipped == []
        assert report.conflicts == []
        assert report.removed == []


# ---------------------------------------------------------------------------
# Idempotent re-install
# ---------------------------------------------------------------------------


class TestReInstall:
    def test_same_variables_produces_only_skips(self, tmp_path: pathlib.Path) -> None:
        install(FIXTURES, tmp_path, VARIABLES, now="2026-04-14T12:00:00Z")
        report = install(FIXTURES, tmp_path, VARIABLES, now="2026-04-14T13:00:00Z")
        assert report.written == []
        assert len(report.skipped) == 4  # + the skill's references/stack.md
        assert report.conflicts == []

    def test_new_values_rewrite_files(self, tmp_path: pathlib.Path) -> None:
        install(FIXTURES, tmp_path, VARIABLES, now="2026-04-14T12:00:00Z")
        updated = {**VARIABLES, "GREETING": "Bonjour"}
        report = install(FIXTURES, tmp_path, updated, now="2026-04-14T13:00:00Z")
        # AGENTS.md + SKILL.md pick up new content; the CLAUDE.md wrapper
        # and references/stack.md (which only uses PROJECT_NAME) are
        # GREETING-independent and stay skips.
        assert len(report.written) == 2
        assert "Bonjour" in _agent_file(tmp_path).read_text(encoding="utf-8")

    def test_changed_variable_rewrites_the_reference(
        self, tmp_path: pathlib.Path
    ) -> None:
        install(FIXTURES, tmp_path, VARIABLES, now="2026-04-14T12:00:00Z")
        updated = {**VARIABLES, "PROJECT_NAME": "Other App"}
        report = install(FIXTURES, tmp_path, updated, now="2026-04-14T13:00:00Z")
        assert _reference_file(tmp_path) in report.written
        assert "Other App" in _reference_file(tmp_path).read_text(encoding="utf-8")

    def test_reinstall_preserves_previous_values_for_unspecified_keys(
        self, tmp_path: pathlib.Path
    ) -> None:
        install(FIXTURES, tmp_path, VARIABLES, now="2026-04-14T12:00:00Z")
        # Second call passes only GREETING; PROJECT_NAME must be kept.
        install(
            FIXTURES,
            tmp_path,
            {"GREETING": "Oi"},
            now="2026-04-14T13:00:00Z",
            allow_unresolved=True,
        )
        manifest = load_manifest(_manifest_file(tmp_path))
        record = manifest.find_preset("mini")
        assert record is not None
        assert record.variables["PROJECT_NAME"] == "Demo App"
        assert record.variables["GREETING"] == "Oi"


# ---------------------------------------------------------------------------
# Conflicts
# ---------------------------------------------------------------------------


class TestConflicts:
    def test_hand_edited_file_is_reported_as_conflict(
        self, tmp_path: pathlib.Path
    ) -> None:
        install(FIXTURES, tmp_path, VARIABLES, now="2026-04-14T12:00:00Z")
        _agent_file(tmp_path).write_text("edited by user\n", encoding="utf-8")

        report = install(FIXTURES, tmp_path, VARIABLES, now="2026-04-14T13:00:00Z")
        assert _agent_file(tmp_path) in report.conflicts
        assert _agent_file(tmp_path).read_text(encoding="utf-8") == "edited by user\n"

    def test_hand_edited_reference_is_reported_as_conflict(
        self, tmp_path: pathlib.Path
    ) -> None:
        install(FIXTURES, tmp_path, VARIABLES, now="2026-04-14T12:00:00Z")
        _reference_file(tmp_path).write_text("edited by user\n", encoding="utf-8")

        report = install(FIXTURES, tmp_path, VARIABLES, now="2026-04-14T13:00:00Z")
        assert _reference_file(tmp_path) in report.conflicts
        assert _reference_file(tmp_path).read_text(encoding="utf-8") == "edited by user\n"

    def test_force_overwrites_hand_edited_file(self, tmp_path: pathlib.Path) -> None:
        install(FIXTURES, tmp_path, VARIABLES, now="2026-04-14T12:00:00Z")
        _agent_file(tmp_path).write_text("edited by user\n", encoding="utf-8")

        report = install(
            FIXTURES,
            tmp_path,
            VARIABLES,
            force=True,
            now="2026-04-14T13:00:00Z",
        )
        assert report.conflicts == []
        assert "Demo App" in _agent_file(tmp_path).read_text(encoding="utf-8")

    def test_pre_existing_file_on_first_install_is_conflict(
        self, tmp_path: pathlib.Path
    ) -> None:
        # No prior manifest. An existing CLAUDE.md is unknown territory.
        _agent_file(tmp_path).write_text("my own CLAUDE.md\n", encoding="utf-8")
        report = install(FIXTURES, tmp_path, VARIABLES, now="2026-04-14T12:00:00Z")
        assert _agent_file(tmp_path) in report.conflicts


# ---------------------------------------------------------------------------
# Dry run
# ---------------------------------------------------------------------------


class TestDryRun:
    def test_dry_run_reports_but_writes_nothing(self, tmp_path: pathlib.Path) -> None:
        report = install(
            FIXTURES,
            tmp_path,
            VARIABLES,
            mode=InstallMode.DRY_RUN,
            now="2026-04-14T12:00:00Z",
        )
        # AGENTS.md + CLAUDE.md wrapper + SKILL.md + references/stack.md
        assert len(report.written) == 4
        assert _reference_file(tmp_path) in report.written
        assert not _agent_file(tmp_path).exists()
        assert not _wrapper_file(tmp_path).exists()
        assert not _skill_file(tmp_path, "hello-world").exists()
        assert not _reference_file(tmp_path).exists()
        assert not _manifest_file(tmp_path).exists()


# ---------------------------------------------------------------------------
# Unresolved placeholders
# ---------------------------------------------------------------------------


_SKILL_REL = "skills/hello-world/SKILL.md"
_REFERENCE_REL = "skills/hello-world/references/stack.md"


def _preset_with_token(tmp_path: pathlib.Path, relative: str) -> pathlib.Path:
    """Copy the mini fixture and append an unresolvable token to one preset file."""
    preset = tmp_path / "preset"
    shutil.copytree(FIXTURES, preset)
    broken = preset / relative
    broken.write_text(
        broken.read_text(encoding="utf-8") + "\nMissing: {{MISSING_TOKEN}}\n",
        encoding="utf-8",
    )
    return preset


class TestUnresolvedPlaceholders:
    def test_missing_variable_errors_by_default(self, tmp_path: pathlib.Path) -> None:
        with pytest.raises(InstallError, match="unresolved placeholders"):
            install(
                FIXTURES,
                tmp_path,
                {"PROJECT_NAME": "Demo"},  # GREETING omitted
                now="2026-04-14T12:00:00Z",
            )

    def test_allow_unresolved_writes_files_and_reports_keys(
        self, tmp_path: pathlib.Path
    ) -> None:
        # --allow-unresolved is the escape hatch: files are written even
        # when placeholders survive substitution; the report enumerates
        # which keys remained so the user can fix the preset later.
        report = install(
            FIXTURES,
            tmp_path,
            {"PROJECT_NAME": "Demo"},
            allow_unresolved=True,
            now="2026-04-14T12:00:00Z",
        )
        # AGENTS.md + CLAUDE.md wrapper + SKILL.md + references/stack.md
        assert len(report.written) == 4
        assert "GREETING" in report.unresolved
        # The literal {{GREETING}} survives in the output.
        agent_text = _agent_file(tmp_path).read_text(encoding="utf-8")
        assert "{{GREETING}}" in agent_text

    @pytest.mark.parametrize("mode", [InstallMode.INSTALL, InstallMode.DRY_RUN])
    def test_error_cites_the_offending_reference_file_and_key(
        self, tmp_path: pathlib.Path, mode: InstallMode
    ) -> None:
        # Spec 0030 Story 4 sc2: a preset author must learn *which* file
        # holds the stray token; a dry run predicts the same failure.
        preset = _preset_with_token(tmp_path, _REFERENCE_REL)

        with pytest.raises(InstallError) as excinfo:
            install(
                preset,
                tmp_path / "project",
                VARIABLES,
                mode=mode,
                now="2026-04-14T12:00:00Z",
            )

        message = str(excinfo.value)
        assert "unresolved placeholders" in message
        assert _REFERENCE_REL in message
        assert "MISSING_TOKEN" in message
        assert "SKILL.md" not in message  # only the offender is cited

    @pytest.mark.parametrize("broken", [_SKILL_REL, _REFERENCE_REL])
    def test_failed_install_leaves_nothing_behind_and_rerun_after_fix_succeeds(
        self, tmp_path: pathlib.Path, broken: str
    ) -> None:
        # Every artifact is validated before the first write: a failing
        # install leaves no file and no manifest, so fixing the variable
        # and re-running is a clean first install, not a wall of conflicts.
        preset = _preset_with_token(tmp_path, broken)
        project = tmp_path / "project"
        project.mkdir()

        with pytest.raises(InstallError):
            install(preset, project, VARIABLES, now="2026-04-14T12:00:00Z")
        assert list(project.rglob("*")) == []  # no artifact, no manifest

        report = install(
            preset,
            project,
            {**VARIABLES, "MISSING_TOKEN": "fixed"},
            now="2026-04-14T13:00:00Z",
        )
        assert report.ok
        assert _skill_file(project, "hello-world") in report.written


# ---------------------------------------------------------------------------
# Uninstall
# ---------------------------------------------------------------------------


class TestUninstall:
    def test_removes_files_and_clears_manifest(self, tmp_path: pathlib.Path) -> None:
        install(FIXTURES, tmp_path, VARIABLES, now="2026-04-14T12:00:00Z")
        report = install(
            FIXTURES,
            tmp_path,
            VARIABLES,
            mode=InstallMode.UNINSTALL,
        )
        assert report.ok
        # AGENTS.md + CLAUDE.md wrapper + SKILL.md + references/stack.md
        assert len(report.removed) == 4
        assert not _agent_file(tmp_path).exists()
        assert not _wrapper_file(tmp_path).exists()
        assert not _skill_file(tmp_path, "hello-world").exists()
        assert not _reference_file(tmp_path).exists()
        assert not _manifest_file(tmp_path).exists()

    def test_uninstall_without_prior_install_is_noop(
        self, tmp_path: pathlib.Path
    ) -> None:
        report = install(
            FIXTURES,
            tmp_path,
            VARIABLES,
            mode=InstallMode.UNINSTALL,
        )
        assert report.removed == []
        assert report.conflicts == []

    def test_edited_file_blocks_uninstall(self, tmp_path: pathlib.Path) -> None:
        install(FIXTURES, tmp_path, VARIABLES, now="2026-04-14T12:00:00Z")
        _agent_file(tmp_path).write_text("user-added content\n", encoding="utf-8")
        report = install(
            FIXTURES,
            tmp_path,
            VARIABLES,
            mode=InstallMode.UNINSTALL,
        )
        assert _agent_file(tmp_path) in report.conflicts
        assert _agent_file(tmp_path).exists()
        # Manifest must still describe the preset — we did not uninstall it.
        assert _manifest_file(tmp_path).is_file()

    def test_force_uninstall_removes_edited_file(self, tmp_path: pathlib.Path) -> None:
        install(FIXTURES, tmp_path, VARIABLES, now="2026-04-14T12:00:00Z")
        _agent_file(tmp_path).write_text("user-added content\n", encoding="utf-8")
        report = install(
            FIXTURES,
            tmp_path,
            VARIABLES,
            mode=InstallMode.UNINSTALL,
            force=True,
        )
        assert _agent_file(tmp_path) in report.removed
        assert not _manifest_file(tmp_path).exists()


# ---------------------------------------------------------------------------
# Misconfiguration
# ---------------------------------------------------------------------------


class TestUserScope:
    """Tests for --scope user behaviour.

    Every test in this class monkeypatches HOME to a tmp_path so nothing
    touches the real user home directory.
    """

    @pytest.fixture
    def fake_home(self, tmp_path: pathlib.Path, monkeypatch) -> pathlib.Path:
        home = tmp_path / "home"
        home.mkdir()
        monkeypatch.setenv("HOME", str(home))
        # Path.home() on POSIX honours HOME; make absolutely sure.
        monkeypatch.setattr(pathlib.Path, "home", staticmethod(lambda: home))
        return home

    def test_user_scope_writes_skill_under_home(
        self, fake_home: pathlib.Path, tmp_path: pathlib.Path
    ) -> None:
        project = tmp_path / "unused-project"
        project.mkdir()
        report = install(
            FIXTURES,
            project,
            VARIABLES,
            scope="user",
            now="2026-04-14T12:00:00Z",
        )
        # Agent file is skipped under user scope (not installable).
        assert report.skipped_unsupported
        # The only skill in the mini-preset lands under .claude/skills/.
        skill_target = fake_home / ".claude" / "skills" / "hello-world" / "SKILL.md"
        assert skill_target.is_file()
        # No CLAUDE.md at home root or project root.
        assert not (fake_home / "CLAUDE.md").exists()
        assert not (project / "CLAUDE.md").exists()

    def test_user_scope_installs_references_with_their_skill(
        self, fake_home: pathlib.Path, tmp_path: pathlib.Path
    ) -> None:
        project = tmp_path / "unused-project"
        project.mkdir()
        install(FIXTURES, project, VARIABLES, scope="user", now="2026-04-14T12:00:00Z")
        reference = fake_home / ".claude" / "skills" / "hello-world" / "references" / "stack.md"
        assert "Demo App" in reference.read_text(encoding="utf-8")
        assert not (project / ".claude").exists()

    def test_user_scope_manifest_is_under_home(
        self, fake_home: pathlib.Path, tmp_path: pathlib.Path
    ) -> None:
        project = tmp_path / "unused"
        project.mkdir()
        install(FIXTURES, project, VARIABLES, scope="user", now="2026-04-14T12:00:00Z")
        assert (fake_home / ".aiadev" / "installed.yaml").is_file()
        # No project-scope manifest was created.
        assert not (project / ".aiadev").exists()

    def test_user_scope_uninstall_round_trip(
        self, fake_home: pathlib.Path, tmp_path: pathlib.Path
    ) -> None:
        project = tmp_path / "unused"
        project.mkdir()
        install(FIXTURES, project, VARIABLES, scope="user", now="2026-04-14T12:00:00Z")
        uninstall_report = install(
            FIXTURES,
            project,
            VARIABLES,
            scope="user",
            mode=InstallMode.UNINSTALL,
        )
        assert uninstall_report.ok
        assert not (fake_home / ".claude").exists()
        assert not (fake_home / ".aiadev").exists()

    def test_user_and_project_scopes_are_independent(
        self, fake_home: pathlib.Path, tmp_path: pathlib.Path
    ) -> None:
        project = tmp_path / "real-project"
        project.mkdir()
        # Install at project scope first.
        install(FIXTURES, project, VARIABLES, now="2026-04-14T12:00:00Z")
        assert (project / "CLAUDE.md").is_file()
        assert (project / ".aiadev" / "installed.yaml").is_file()

        # Now install at user scope; project artifacts untouched.
        install(FIXTURES, project, VARIABLES, scope="user", now="2026-04-14T13:00:00Z")
        assert (fake_home / ".claude" / "skills" / "hello-world" / "SKILL.md").is_file()
        assert (fake_home / ".aiadev" / "installed.yaml").is_file()
        assert (project / "CLAUDE.md").is_file()  # still there
        assert (project / ".aiadev" / "installed.yaml").is_file()

    def test_unknown_scope_raises(self, tmp_path: pathlib.Path) -> None:
        with pytest.raises(InstallError, match="unknown scope"):
            install(FIXTURES, tmp_path, VARIABLES, scope="moon")


class TestMisconfiguration:
    def test_unknown_platform_raises(self, tmp_path: pathlib.Path) -> None:
        with pytest.raises(InstallError, match="unknown platform"):
            install(FIXTURES, tmp_path, VARIABLES, platform="typewriter")

    def test_missing_preset_yaml_raises(self, tmp_path: pathlib.Path) -> None:
        empty = tmp_path / "preset"
        empty.mkdir()
        with pytest.raises(InstallError, match="preset.yaml not found"):
            install(empty, tmp_path / "project", VARIABLES)

    def test_preset_yaml_not_a_mapping_raises(self, tmp_path: pathlib.Path) -> None:
        preset_dir = tmp_path / "preset"
        preset_dir.mkdir()
        (preset_dir / "preset.yaml").write_text("- a\n- b\n", encoding="utf-8")
        with pytest.raises(InstallError, match="mapping"):
            install(preset_dir, tmp_path / "project", VARIABLES)


# ---------------------------------------------------------------------------
# Skill references/ collection (spec 0030 Story 4, plan D1)
# ---------------------------------------------------------------------------


def _write(path: pathlib.Path, text: str = "# ref\n") -> pathlib.Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _make_skill(root: pathlib.Path, name: str, *, skill_md: bool = True) -> pathlib.Path:
    """Create ``<root>/skills/<name>/`` (with a minimal SKILL.md unless told not to)."""
    skill_dir = root / "skills" / name
    skill_dir.mkdir(parents=True)
    if skill_md:
        _write(skill_dir / "SKILL.md", f"---\nname: {name}\n---\n")
    return skill_dir


class TestCollectSkillReferences:
    def test_framework_reference_is_collected_verbatim(self, tmp_path: pathlib.Path) -> None:
        framework = tmp_path / "framework"
        skill = _make_skill(framework, "alpha")
        ref = _write(skill / "references" / "guide.md")
        preset = tmp_path / "preset"
        preset.mkdir()

        assert _collect_skill_references(framework, preset) == [
            ("skill", "alpha/references/guide.md", ref, True)
        ]

    def test_preset_reference_is_collected_not_verbatim(self) -> None:
        # The mini-preset ships hello-world/references/stack.md.
        collected = _collect_skill_references(None, FIXTURES)

        assert collected == [
            (
                "skill",
                "hello-world/references/stack.md",
                FIXTURES / "skills" / "hello-world" / "references" / "stack.md",
                False,
            )
        ]

    def test_preset_wins_on_same_skill_and_relative_path(
        self, tmp_path: pathlib.Path
    ) -> None:
        framework = tmp_path / "framework"
        fw_skill = _make_skill(framework, "alpha")
        _write(fw_skill / "references" / "shared.md", "framework\n")
        fw_only = _write(fw_skill / "references" / "fw-only.md")
        preset = tmp_path / "preset"
        pr_skill = _make_skill(preset, "alpha")
        pr_shared = _write(pr_skill / "references" / "shared.md", "preset\n")
        pr_only = _write(pr_skill / "references" / "pr-only.md")

        assert _collect_skill_references(framework, preset) == [
            ("skill", "alpha/references/fw-only.md", fw_only, True),
            ("skill", "alpha/references/pr-only.md", pr_only, False),
            ("skill", "alpha/references/shared.md", pr_shared, False),
        ]

    def test_ignores_everything_that_is_not_a_markdown_reference(
        self, tmp_path: pathlib.Path
    ) -> None:
        framework = tmp_path / "framework"
        skill = _make_skill(framework, "alpha")
        kept = _write(skill / "references" / "kept.md")
        _write(skill / "references" / ".DS_Store", "junk")
        _write(skill / "references" / "notes.txt", "plain text")
        (skill / "references" / "folder.md").mkdir()  # a directory named like a file
        _write(skill / "notes.md")  # markdown beside SKILL.md, not under references/
        preset = tmp_path / "preset"
        preset.mkdir()

        assert _collect_skill_references(framework, preset) == [
            ("skill", "alpha/references/kept.md", kept, True)
        ]

    def test_skill_without_skill_md_is_ignored(self, tmp_path: pathlib.Path) -> None:
        framework = tmp_path / "framework"
        orphan = _make_skill(framework, "orphan", skill_md=False)
        _write(orphan / "references" / "lost.md")
        preset = tmp_path / "preset"
        pr_orphan = _make_skill(preset, "orphan-preset", skill_md=False)
        _write(pr_orphan / "references" / "lost.md")

        assert _collect_skill_references(framework, preset) == []

    def test_preset_references_only_extend_a_framework_skill(
        self, tmp_path: pathlib.Path
    ) -> None:
        # Plan D1/D11: a preset delivers stack guidance WITHOUT replacing
        # the generic SKILL.md — only references/ in the preset.
        framework = tmp_path / "framework"
        _make_skill(framework, "alpha")
        preset = tmp_path / "preset"
        stack = _write(
            _make_skill(preset, "alpha", skill_md=False) / "references" / "stack.md"
        )

        assert _collect_skill_references(framework, preset) == [
            ("skill", "alpha/references/stack.md", stack, False)
        ]

    def test_order_is_deterministic(self, tmp_path: pathlib.Path) -> None:
        framework = tmp_path / "framework"
        # Created out of alphabetical order on purpose.
        for skill_name, rel in (
            ("zeta", "references/z.md"),
            ("alpha", "references/b.md"),
            ("alpha", "references/a/c.md"),
            ("alpha", "references/a.md"),
            ("mid", "references/m.md"),
        ):
            skill = framework / "skills" / skill_name
            if not skill.exists():
                _make_skill(framework, skill_name)
            _write(skill / rel)
        preset = tmp_path / "preset"
        pr_skill = _make_skill(preset, "beta")
        _write(pr_skill / "references" / "p.md")

        first = _collect_skill_references(framework, preset)
        second = _collect_skill_references(framework, preset)

        names = [name for (_role, name, _path, _verbatim) in first]
        assert names == sorted(names)
        assert names == [
            "alpha/references/a.md",
            "alpha/references/a/c.md",
            "alpha/references/b.md",
            "beta/references/p.md",
            "mid/references/m.md",
            "zeta/references/z.md",
        ]
        assert first == second

    def test_symlink_pointing_outside_the_skills_tree_is_not_followed(
        self, tmp_path: pathlib.Path
    ) -> None:
        outside = tmp_path / "outside"
        secret = _write(outside / "secret.md", "do not install me\n")
        _write(outside / "dir" / "nested.md")
        framework = tmp_path / "framework"
        skill = _make_skill(framework, "alpha")
        kept = _write(skill / "references" / "kept.md")
        refs = skill / "references"
        try:
            (refs / "leak.md").symlink_to(secret)
            (refs / "leakdir").symlink_to(outside / "dir", target_is_directory=True)
        except OSError:  # pragma: no cover - platform without symlink support
            pytest.skip("symlinks not supported on this platform")
        preset = tmp_path / "preset"
        preset.mkdir()

        assert _collect_skill_references(framework, preset) == [
            ("skill", "alpha/references/kept.md", kept, True)
        ]

    def test_missing_roots_yield_nothing(self, tmp_path: pathlib.Path) -> None:
        # No framework root, and a preset without a skills/ directory.
        assert _collect_skill_references(None, tmp_path) == []


# ---------------------------------------------------------------------------
# Skill references/ installation (spec 0030 Story 4 sc3, plan D1)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("platform", sorted(_SKILLS_DIR))
class TestInstallSkillReferences:
    """What varies per handler: the destination and the manifest entry."""

    def test_preset_reference_lands_next_to_the_skill_and_is_recorded(
        self, tmp_path: pathlib.Path, platform: str
    ) -> None:
        report = install(
            FIXTURES, tmp_path, VARIABLES, platform=platform, now="2026-04-14T12:00:00Z"
        )

        reference = _reference_file(tmp_path, platform)
        assert (reference.parent.parent / "SKILL.md").is_file()
        assert reference in report.written
        text = reference.read_text(encoding="utf-8")
        assert "Demo App" in text  # {{PROJECT_NAME}} substituted
        assert find_unresolved(text) == []

        record = load_manifest(_manifest_file(tmp_path)).find_preset("mini")
        assert record is not None
        entry = next(f for f in record.files if f.path.endswith("references/stack.md"))
        assert entry.path == reference.relative_to(tmp_path).as_posix()
        assert entry.role == "skill"
        assert entry.sha256 == hashlib.sha256(text.encode("utf-8")).hexdigest()

    def test_uninstall_removes_the_reference_and_empty_directories(
        self, tmp_path: pathlib.Path, platform: str
    ) -> None:
        install(FIXTURES, tmp_path, VARIABLES, platform=platform, now="2026-04-14T12:00:00Z")
        reference = _reference_file(tmp_path, platform)

        report = install(
            FIXTURES, tmp_path, VARIABLES, platform=platform, mode=InstallMode.UNINSTALL
        )

        assert reference in report.removed
        assert not reference.parent.exists()  # references/
        assert not (tmp_path / _SKILLS_DIR[platform]).exists()  # skill dirs went too


def test_framework_reference_is_copied_verbatim(tmp_path: pathlib.Path) -> None:
    # Guards the ``verbatim`` flag of framework references: their
    # ``{{UPPER_SNAKE}}`` tokens are runtime markers, never substituted.
    framework = tmp_path / "framework"
    skill = _make_skill(framework, "alpha")
    body = "Runtime markers stay: {{TASK_ID}} and {{PROJECT_NAME}}\n"
    _write(skill / "references" / "guide.md", body)
    project = tmp_path / "project"

    report = install(
        FIXTURES,
        project,
        VARIABLES,
        framework_root=framework,
        now="2026-04-14T12:00:00Z",
    )

    installed = project / _SKILLS_DIR["claude_code"] / "alpha" / "references" / "guide.md"
    assert installed.read_text(encoding="utf-8") == body
    assert report.unresolved == []


# ---------------------------------------------------------------------------
# Files the framework stopped shipping (spec 0030 Story 6 sc1, plan D2)
# ---------------------------------------------------------------------------

# What a "new version" of the preset drops, as (preset-relative source,
# project-relative installed path): a rule, and a skill's references/ file
# while the skill itself stays.
_RULE = ("rules/terse-mode.md", ".claude/rules/terse-mode.md")
_REFERENCE = (_REFERENCE_REL, ".claude/skills/hello-world/references/stack.md")


def _installed_v1(tmp_path: pathlib.Path) -> tuple[pathlib.Path, pathlib.Path]:
    """Install the mini preset plus a rule; return ``(preset, project)``."""
    preset = tmp_path / "preset"
    shutil.copytree(FIXTURES, preset)
    _write(preset / _RULE[0], "# Terse mode\n")
    project = tmp_path / "project"
    install(preset, project, VARIABLES, now="2026-04-14T12:00:00Z")
    return preset, project


def _ship_v2_without(preset: pathlib.Path, *dropped: tuple[str, str]) -> None:
    for source, _ in dropped:
        (preset / source).unlink()


def _tracked_paths(project: pathlib.Path) -> set[str]:
    record = load_manifest(_manifest_file(project)).find_preset("mini")
    assert record is not None
    return {f.path for f in record.files}


class TestStaleFiles:
    @pytest.mark.parametrize("dropped", [_RULE, _REFERENCE], ids=["rule", "reference"])
    def test_unedited_file_the_preset_dropped_is_removed(
        self, tmp_path: pathlib.Path, dropped: tuple[str, str]
    ) -> None:
        preset, project = _installed_v1(tmp_path)
        stale = project / dropped[1]
        assert stale.is_file()
        _ship_v2_without(preset, dropped)

        report = install(preset, project, VARIABLES, now="2026-04-14T13:00:00Z")

        assert report.ok
        assert report.removed == [stale]
        assert report.preserved == []
        assert not stale.parent.exists()  # the directory it left empty goes too
        assert dropped[1] not in _tracked_paths(project)
        assert _agent_file(project).is_file()  # what is still shipped stays

    @pytest.mark.parametrize("force", [False, True])
    def test_hand_edited_file_is_preserved_and_leaves_the_manifest(
        self, tmp_path: pathlib.Path, force: bool
    ) -> None:
        preset, project = _installed_v1(tmp_path)
        stale = project / _RULE[1]
        stale.write_text("my own terse rules\n", encoding="utf-8")
        _ship_v2_without(preset, _RULE)

        report = install(
            preset, project, VARIABLES, force=force, now="2026-04-14T13:00:00Z"
        )

        assert stale.read_text(encoding="utf-8") == "my own terse rules\n"
        assert report.preserved == [stale]
        assert report.removed == []
        assert report.conflicts == []
        assert report.ok  # the edit is kept and listed, never a failure
        assert _RULE[1] not in _tracked_paths(project)

    def test_file_the_user_already_deleted_is_dropped_quietly(
        self, tmp_path: pathlib.Path
    ) -> None:
        preset, project = _installed_v1(tmp_path)
        (project / _RULE[1]).unlink()
        _ship_v2_without(preset, _RULE)

        report = install(preset, project, VARIABLES, now="2026-04-14T13:00:00Z")

        assert report.ok
        assert report.removed == [] and report.preserved == []
        assert _RULE[1] not in _tracked_paths(project)

    def test_directory_holding_another_file_survives(
        self, tmp_path: pathlib.Path
    ) -> None:
        preset, project = _installed_v1(tmp_path)
        mine = _write(project / ".claude" / "rules" / "mine.md", "# mine\n")
        _ship_v2_without(preset, _RULE)

        report = install(preset, project, VARIABLES, now="2026-04-14T13:00:00Z")

        assert report.removed == [project / _RULE[1]]
        assert mine.is_file()

    def test_file_still_shipped_but_in_conflict_is_not_stale(
        self, tmp_path: pathlib.Path
    ) -> None:
        # A conflict is "kept because edited", not "no longer shipped": it
        # must stay tracked and must not show up as preserved.
        preset, project = _installed_v1(tmp_path)
        _agent_file(project).write_text("edited by user\n", encoding="utf-8")

        report = install(preset, project, VARIABLES, now="2026-04-14T13:00:00Z")

        assert report.conflicts == [_agent_file(project)]
        assert report.preserved == [] and report.removed == []
        assert "AGENTS.md" in _tracked_paths(project)

    def test_dry_run_lists_removals_and_preservations_but_deletes_nothing(
        self, tmp_path: pathlib.Path
    ) -> None:
        preset, project = _installed_v1(tmp_path)
        edited = project / _REFERENCE[1]
        edited.write_text("my own stack notes\n", encoding="utf-8")
        _ship_v2_without(preset, _RULE, _REFERENCE)
        manifest_before = _manifest_file(project).read_bytes()

        report = install(
            preset,
            project,
            VARIABLES,
            mode=InstallMode.DRY_RUN,
            now="2026-04-14T13:00:00Z",
        )

        assert report.removed == [project / _RULE[1]]
        assert report.preserved == [edited]
        assert (project / _RULE[1]).is_file()
        assert edited.read_text(encoding="utf-8") == "my own stack notes\n"
        assert _manifest_file(project).read_bytes() == manifest_before

    def test_user_scope_run_does_not_retire_files_it_cannot_install(
        self, tmp_path: pathlib.Path, monkeypatch
    ) -> None:
        # Agent files are skipped under --scope user, so a project install
        # that happened to target $HOME left AGENTS.md/CLAUDE.md that this
        # run never looked at: out of scope, not dropped by the framework.
        home = tmp_path / "home"
        home.mkdir()
        monkeypatch.setattr(pathlib.Path, "home", staticmethod(lambda: home))
        install(FIXTURES, home, VARIABLES, now="2026-04-14T12:00:00Z")

        report = install(
            FIXTURES, home, VARIABLES, scope="user", now="2026-04-14T13:00:00Z"
        )

        assert report.removed == [] and report.preserved == []
        assert _agent_file(home).is_file() and _wrapper_file(home).is_file()
        assert {"AGENTS.md", "CLAUDE.md"} <= _tracked_paths(home)


class TestManifestPathContainment:
    """A manifest entry is only ever a path *inside* the install root."""

    @pytest.mark.parametrize("mode", [InstallMode.INSTALL, InstallMode.UNINSTALL])
    @pytest.mark.parametrize("escape", ["relative", "absolute"])
    def test_entry_outside_the_root_is_never_touched(
        self, tmp_path: pathlib.Path, mode: InstallMode, escape: str
    ) -> None:
        preset, project = _installed_v1(tmp_path)
        victim = _write(tmp_path / "victim.txt", "not ours\n")  # beside the project
        recorded = "../victim.txt" if escape == "relative" else str(victim)
        manifest = load_manifest(_manifest_file(project))
        record = manifest.find_preset("mini")
        assert record is not None
        record.files.append(InstalledFile(recorded, compute_sha256(victim), "rule"))
        save_manifest(manifest, _manifest_file(project))
        _ship_v2_without(preset, _RULE)  # a legitimate stale file goes too

        report = install(
            preset,
            project,
            VARIABLES,
            mode=mode,
            force=True,
            now="2026-04-14T13:00:00Z",
        )

        assert victim.read_text(encoding="utf-8") == "not ours\n"
        legit = project / _RULE[1]
        assert legit in report.removed  # inside the root, still retired
        assert not legit.exists()
        # An install lists the unmanaged entry as preserved and drops it from
        # the manifest; an uninstall just skips it.
        assert len(report.preserved) == (0 if mode is InstallMode.UNINSTALL else 1)
        if mode is InstallMode.INSTALL:
            assert recorded not in _tracked_paths(project)
