"""End-to-end smoke test for ``aiadev install``.

Runs the full install -> doctor -> re-install -> uninstall cycle against
a tmpdir to make sure the pieces wired in T001..T006 actually cooperate.
CI runs this with --cov-fail-under so a regression in the engine that
sneaks past unit tests still trips up the smoke.
"""
from __future__ import annotations

import os
import pathlib
import subprocess
import sys

import pytest
from click.testing import CliRunner

from aiadev.commands.doctor import doctor_command
from aiadev.commands.install import install_command


def _invoke_install(runner: CliRunner, project_root: pathlib.Path, *args: str):
    return runner.invoke(install_command, ["--project-root", str(project_root), *args])


@pytest.fixture
def aiadev_root_env(isolated_framework: pathlib.Path, monkeypatch) -> pathlib.Path:
    """Pin AIADEV_ROOT so the install command uses the isolated tree."""
    monkeypatch.setenv("AIADEV_ROOT", str(isolated_framework))
    return isolated_framework


def test_install_doctor_reinstall_uninstall_round_trip(
    aiadev_root_env: pathlib.Path, tmp_path: pathlib.Path, monkeypatch
) -> None:
    project = tmp_path / "demo-project"
    project.mkdir()
    # The doctor command uses the same framework resolver, so AIADEV_ROOT
    # is inherited from the fixture.
    runner = CliRunner()

    # 1. Install.
    install = _invoke_install(
        runner,
        project,
        "--preset",
        "lean",
        "--non-interactive",
        "--vars",
        "PROJECT_NAME=RoundTrip",
    )
    assert install.exit_code == 0, install.output
    # Spec 0016 Story 3 / ADR-5: AGENTS.md is canonical; CLAUDE.md is a
    # thin wrapper pointing at it.
    agents_md = project / "AGENTS.md"
    claude_md = project / "CLAUDE.md"
    manifest = project / ".aiadev" / "installed.yaml"
    assert agents_md.is_file()
    assert claude_md.is_file()
    assert manifest.is_file()
    assert "RoundTrip" in agents_md.read_text(encoding="utf-8")
    assert "AGENTS.md" in claude_md.read_text(encoding="utf-8")

    # 2. Doctor (targets the framework, not the project; still must
    #    pass since we did not touch the framework).
    monkeypatch.chdir(aiadev_root_env)
    doctor = runner.invoke(doctor_command, [])
    assert doctor.exit_code == 0, doctor.output

    # 3. Re-install with identical variables: everything skips.
    reinstall = _invoke_install(
        runner,
        project,
        "--preset",
        "lean",
        "--non-interactive",
        "--vars",
        "PROJECT_NAME=RoundTrip",
    )
    assert reinstall.exit_code == 0, reinstall.output
    assert "write" not in reinstall.output  # no new writes
    assert agents_md.is_file()
    assert claude_md.is_file()

    # 4. Uninstall cleans up every file the install wrote.
    uninstall = _invoke_install(runner, project, "--preset", "lean", "--uninstall")
    assert uninstall.exit_code == 0, uninstall.output
    assert not agents_md.exists()
    assert not claude_md.exists()
    assert not manifest.exists()
    assert not (project / ".aiadev").exists()


def test_mobile_ops_preset_smoke(
    aiadev_root_env: pathlib.Path, tmp_path: pathlib.Path
) -> None:
    """Install the multi-skill mobile-ops preset to exercise the skill-copy path."""
    project = tmp_path / "mobile-project"
    project.mkdir()
    runner = CliRunner()

    install = _invoke_install(
        runner,
        project,
        "--preset",
        "mobile-ops",
        "--non-interactive",
        "--vars",
        (
            "PROJECT_NAME=MobileDemo"
            ",APP_NAME=DemoApp"
            ",BACKEND_DIR=backend"
            ",MOBILE_DIR=mobile"
            ",ADMIN_DIR=admin"
            ",BACKEND_ASGI_MODULE=backend.asgi"
            ",CELERY_APP=backend"
            ",GCP_PROJECT=demo-gcp"
            ",GCP_REGION=us-central1"
            ",ARTIFACT_REPO=demo"
            ",BACKEND_SERVICE=api"
            ",ADMIN_SERVICE=admin"
            ",CLOUD_SQL_INSTANCE=demo-gcp:us-central1:demo"
            ",PROD_API_URL=api.example.com"
            ",PROD_ADMIN_URL=admin.example.com"
        ),
    )
    assert install.exit_code == 0, install.output

    # Every operational skill landed under .claude/skills/.
    preset_skills = (
        "build-android",
        "build-ios",
        "deploy-backend",
        "ota-update",
        "release-notes",
    )
    for skill in preset_skills:
        assert (project / ".claude" / "skills" / skill / "SKILL.md").is_file()

    # No install-time placeholder survived substitution in preset skills.
    # Framework-generic skills carry runtime placeholders intentionally
    # (e.g. {{BRANCH}}, {{TEST_COMMAND}}) so we don't assert over them.
    import re

    for skill in preset_skills:
        text = (project / ".claude" / "skills" / skill / "SKILL.md").read_text(
            encoding="utf-8"
        )
        assert re.search(r"\{\{[A-Z][A-Z0-9_]*\}\}", text) is None


def test_cursor_platform_round_trip(
    aiadev_root_env: pathlib.Path, tmp_path: pathlib.Path
) -> None:
    """Install the mobile-ops preset for Cursor; assert layout, skills, and uninstall."""
    project = tmp_path / "cursor-project"
    project.mkdir()
    runner = CliRunner()

    install = _invoke_install(
        runner,
        project,
        "--preset",
        "mobile-ops",
        "--platform",
        "cursor",
        "--non-interactive",
        "--vars",
        (
            "PROJECT_NAME=CursorDemo"
            ",APP_NAME=DemoApp"
            ",BACKEND_DIR=backend"
            ",MOBILE_DIR=mobile"
            ",ADMIN_DIR=admin"
            ",BACKEND_ASGI_MODULE=backend.asgi"
            ",CELERY_APP=backend"
            ",GCP_PROJECT=demo-gcp"
            ",GCP_REGION=us-central1"
            ",ARTIFACT_REPO=demo"
            ",BACKEND_SERVICE=api"
            ",ADMIN_SERVICE=admin"
            ",CLOUD_SQL_INSTANCE=demo-gcp:us-central1:demo"
            ",PROD_API_URL=api.example.com"
            ",PROD_ADMIN_URL=admin.example.com"
        ),
    )
    assert install.exit_code == 0, install.output

    # Agent file is AGENTS.md (Cursor convention), NOT CLAUDE.md.
    assert (project / "AGENTS.md").is_file()
    assert not (project / "CLAUDE.md").exists()

    # Skills under .cursor/skills (Cursor convention), NOT .claude/skills.
    assert not (project / ".claude").exists()
    preset_skills = ("build-android", "deploy-backend", "ota-update")
    for skill in preset_skills:
        assert (project / ".cursor" / "skills" / skill / "SKILL.md").is_file()

    import re

    for skill in preset_skills:
        text = (project / ".cursor" / "skills" / skill / "SKILL.md").read_text(
            encoding="utf-8"
        )
        assert re.search(r"\{\{[A-Z][A-Z0-9_]*\}\}", text) is None

    # Uninstall cleans up.
    uninstall = _invoke_install(
        runner, project, "--preset", "mobile-ops", "--platform", "cursor", "--uninstall"
    )
    assert uninstall.exit_code == 0, uninstall.output
    assert not (project / "AGENTS.md").exists()
    assert not (project / ".cursor").exists()
    assert not (project / ".aiadev").exists()


def test_codex_platform_round_trip(
    aiadev_root_env: pathlib.Path, tmp_path: pathlib.Path
) -> None:
    """Install mobile-ops for Codex end-to-end; verify layout + uninstall."""
    project = tmp_path / "codex-project"
    project.mkdir()
    runner = CliRunner()

    install = _invoke_install(
        runner,
        project,
        "--preset",
        "mobile-ops",
        "--platform",
        "codex",
        "--non-interactive",
        "--vars",
        (
            "PROJECT_NAME=CodexDemo"
            ",APP_NAME=DemoApp"
            ",BACKEND_DIR=backend"
            ",MOBILE_DIR=mobile"
            ",ADMIN_DIR=admin"
            ",BACKEND_ASGI_MODULE=backend.asgi"
            ",CELERY_APP=backend"
            ",GCP_PROJECT=demo-gcp"
            ",GCP_REGION=us-central1"
            ",ARTIFACT_REPO=demo"
            ",BACKEND_SERVICE=api"
            ",ADMIN_SERVICE=admin"
            ",CLOUD_SQL_INSTANCE=demo-gcp:us-central1:demo"
            ",PROD_API_URL=api.example.com"
            ",PROD_ADMIN_URL=admin.example.com"
        ),
    )
    assert install.exit_code == 0, install.output
    assert (project / "AGENTS.md").is_file()
    assert not (project / "CLAUDE.md").exists()
    assert not (project / "GEMINI.md").exists()
    assert not (project / ".cursor").exists()
    assert not (project / ".claude").exists()

    preset_skills = ("build-android", "deploy-backend", "ota-update")
    for skill in preset_skills:
        assert (project / ".codex" / "skills" / skill / "SKILL.md").is_file()

    import re

    for skill in preset_skills:
        text = (project / ".codex" / "skills" / skill / "SKILL.md").read_text(
            encoding="utf-8"
        )
        assert re.search(r"\{\{[A-Z][A-Z0-9_]*\}\}", text) is None

    uninstall = _invoke_install(
        runner, project, "--preset", "mobile-ops", "--platform", "codex", "--uninstall"
    )
    assert uninstall.exit_code == 0, uninstall.output
    assert not (project / "AGENTS.md").exists()
    assert not (project / ".codex").exists()
    assert not (project / ".aiadev").exists()


def test_user_scope_round_trip_with_fake_home(
    aiadev_root_env: pathlib.Path, tmp_path: pathlib.Path, monkeypatch
) -> None:
    """Install mobile-ops at --scope user end-to-end under a fake HOME.

    Exercises every moving piece of the per-home install model: the
    engine's scope branching, the handler user-scope target paths, and
    the CLI --scope flag. The real $HOME is never touched because we
    monkeypatch HOME and Path.home to tmp_path.
    """
    fake_home = tmp_path / "fake-home"
    fake_home.mkdir()
    monkeypatch.setenv("HOME", str(fake_home))
    monkeypatch.setattr(pathlib.Path, "home", staticmethod(lambda: fake_home))

    project = tmp_path / "unused-project"
    project.mkdir()
    runner = CliRunner()

    install = _invoke_install(
        runner,
        project,
        "--preset",
        "mobile-ops",
        "--platform",
        "codex",
        "--scope",
        "user",
        "--non-interactive",
        "--vars",
        (
            "PROJECT_NAME=UserScope"
            ",APP_NAME=DemoApp"
            ",BACKEND_DIR=backend"
            ",MOBILE_DIR=mobile"
            ",ADMIN_DIR=admin"
            ",BACKEND_ASGI_MODULE=backend.asgi"
            ",CELERY_APP=backend"
            ",GCP_PROJECT=demo-gcp"
            ",GCP_REGION=us-central1"
            ",ARTIFACT_REPO=demo"
            ",BACKEND_SERVICE=api"
            ",ADMIN_SERVICE=admin"
            ",CLOUD_SQL_INSTANCE=demo-gcp:us-central1:demo"
            ",PROD_API_URL=api.example.com"
            ",PROD_ADMIN_URL=admin.example.com"
        ),
    )
    assert install.exit_code == 0, install.output

    # Every skill landed under ~/.codex/skills/ (fake_home, not the real one).
    for skill in ("build-android", "deploy-backend", "ota-update"):
        assert (fake_home / ".codex" / "skills" / skill / "SKILL.md").is_file()

    # No agent file or constitution was written — user scope skips them.
    assert not (fake_home / "AGENTS.md").exists()
    assert not (fake_home / "CLAUDE.md").exists()
    assert not (fake_home / "constitution.md").exists()
    # Nothing landed in the project either.
    assert not (project / ".codex").exists()
    assert not (project / "AGENTS.md").exists()

    # Manifest is at ~/.aiadev/, not at project/.aiadev/.
    assert (fake_home / ".aiadev" / "installed.yaml").is_file()
    assert not (project / ".aiadev").exists()

    # Uninstall removes every trace.
    uninstall = _invoke_install(
        runner,
        project,
        "--preset",
        "mobile-ops",
        "--platform",
        "codex",
        "--scope",
        "user",
        "--uninstall",
    )
    assert uninstall.exit_code == 0, uninstall.output
    assert not (fake_home / ".codex").exists()
    assert not (fake_home / ".aiadev").exists()


def test_extension_round_trip(
    aiadev_root_env: pathlib.Path, tmp_path: pathlib.Path, monkeypatch
) -> None:
    """End-to-end: extension add -> install --preset (from extension) -> uninstall.

    Uses the `aiadev extension` CLI subcommand and the `aiadev install`
    command via CliRunner; HOME is monkeypatched so the real
    ~/.aiadev/extensions/ is never touched.
    """
    import shutil
    import subprocess

    from aiadev.commands.extension import extension_command

    fake_home = tmp_path / "fake-home"
    fake_home.mkdir()
    monkeypatch.setenv("HOME", str(fake_home))
    monkeypatch.setattr(pathlib.Path, "home", staticmethod(lambda: fake_home))

    fixture = (
        pathlib.Path(__file__).parent
        / "fixtures"
        / "extensions"
        / "sample-extension"
    )

    work = tmp_path / "ext-work"
    bare = tmp_path / "ext-source.git"
    shutil.copytree(fixture, work)
    subprocess.check_call(["git", "init", "-q", "-b", "main"], cwd=str(work))
    subprocess.check_call(
        ["git", "-c", "user.email=t@t", "-c", "user.name=t", "add", "."],
        cwd=str(work),
    )
    subprocess.check_call(
        ["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "init"],
        cwd=str(work),
    )
    subprocess.check_call(
        ["git", "init", "--bare", "-q", "-b", "main", str(bare)],
    )
    subprocess.check_call(
        ["git", "remote", "add", "origin", str(bare)], cwd=str(work)
    )
    subprocess.check_call(["git", "push", "-q", "origin", "main"], cwd=str(work))

    runner = CliRunner()

    add = runner.invoke(extension_command, ["add", str(bare)])
    assert add.exit_code == 0, add.output
    assert (fake_home / ".aiadev" / "extensions" / "sample-extension").is_dir()

    project = tmp_path / "ext-project"
    project.mkdir()
    install = _invoke_install(
        runner,
        project,
        "--preset",
        "sample",
        "--non-interactive",
        "--vars",
        "PROJECT_NAME=ExtDemo",
    )
    assert install.exit_code == 0, install.output
    # Spec 0016 Story 3 / ADR-5: AGENTS.md is canonical; CLAUDE.md is a
    # thin wrapper pointing at it.
    agent = project / "AGENTS.md"
    wrapper = project / "CLAUDE.md"
    assert agent.is_file()
    assert "ExtDemo" in agent.read_text(encoding="utf-8")
    assert wrapper.is_file()

    uninstall = _invoke_install(
        runner, project, "--preset", "sample", "--uninstall"
    )
    assert uninstall.exit_code == 0, uninstall.output
    assert not agent.exists()
    assert not wrapper.exists()

    remove = runner.invoke(extension_command, ["remove", "sample-extension"])
    assert remove.exit_code == 0, remove.output
    assert not (fake_home / ".aiadev" / "extensions" / "sample-extension").exists()


def test_module_entrypoint_round_trip(
    aiadev_root_env: pathlib.Path, tmp_path: pathlib.Path
) -> None:
    """Exercise `python -m aiadev install ...` so the entry point shipped via
    ``src/aiadev/__main__.py`` stays wired."""
    project = tmp_path / "subprocess-project"
    project.mkdir()

    # Use sys.executable so the subprocess inherits the same Python
    # (and therefore the same editable install) as the pytest run.
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "aiadev",
            "install",
            "--project-root",
            str(project),
            "--preset",
            "lean",
            "--non-interactive",
            "--vars",
            "PROJECT_NAME=SubprocessDemo",
        ],
        capture_output=True,
        text=True,
        env={
            **os.environ,
            "AIADEV_ROOT": str(aiadev_root_env),
        },
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert (project / "CLAUDE.md").is_file()
