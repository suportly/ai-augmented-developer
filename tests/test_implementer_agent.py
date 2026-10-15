"""Agent ``implementer`` (spec 0031 Story 4): definition and installation."""
from __future__ import annotations

import filecmp
import pathlib

import pytest
import yaml
from click.testing import CliRunner

from aiadev.commands.install import install_command
from aiadev.commands.sync import sync_command

REPO = pathlib.Path(__file__).resolve().parent.parent
AGENT = REPO / "agents" / "implementer.md"
REVIEWERS = ("code-reviewer", "plan-document-reviewer", "spec-document-reviewer")
PLATFORMS = {
    "claude-code": ".claude",
    "cursor": ".cursor",
    "codex": ".codex",
    "opencode": ".opencode",
    "gemini": ".gemini",
}


def _split() -> tuple[dict, str]:
    text = AGENT.read_text(encoding="utf-8")
    _, fm, body = text.split("---\n", 2)
    return yaml.safe_load(fm), body


def test_frontmatter_has_name_oneline_description_sonnet_no_tools() -> None:
    meta, _ = _split()
    assert meta["name"] == "implementer"
    assert meta["model"] == "sonnet"
    assert "tools" not in meta
    desc = meta["description"]
    assert desc.strip() and "\n" not in desc.strip()
    raw = AGENT.read_text(encoding="utf-8").split("---", 2)[1].splitlines()
    idx = [i for i, line in enumerate(raw) if line.startswith("description:")]
    assert len(idx) == 1, "exactly one description line"
    nxt = raw[idx[0] + 1] if idx[0] + 1 < len(raw) else ""
    assert not nxt.startswith((" ", "\t")), "description must be a single raw line"


def test_body_carries_test_first_flow_and_four_statuses() -> None:
    _, body = _split()
    assert "failing test" in body and "right reason" in body
    assert "Run only the tests that exercise the changed code" in body
    for status in ("DONE", "DONE_WITH_CONCERNS", "NEEDS_CONTEXT", "BLOCKED"):
        assert f"- {status} " in body


@pytest.fixture
def _env(isolated_framework, monkeypatch):
    monkeypatch.setenv("AIADEV_ROOT", str(isolated_framework))


def _agents(project: pathlib.Path, d: str) -> dict[str, bytes]:
    return {p.name: p.read_bytes() for p in (project / d / "agents").glob("*.md")}


@pytest.mark.parametrize("platform", sorted(PLATFORMS))
def test_install_and_sync_keep_agents(_env, tmp_path, platform: str) -> None:
    d = PLATFORMS[platform]
    project = tmp_path / "p"
    project.mkdir()
    runner = CliRunner()
    res = runner.invoke(
        install_command,
        ["--project-root", str(project), "--platform", platform, "--preset", "lean",
         "--non-interactive", "--vars", "PROJECT_NAME=t"],
    )
    assert res.exit_code == 0, res.output
    before = _agents(project, d)
    assert "implementer.md" in before
    for name in REVIEWERS:
        installed = project / d / "agents" / f"{name}.md"
        assert filecmp.cmp(installed, REPO / "agents" / f"{name}.md", shallow=False)
    res = runner.invoke(sync_command, ["--project-root", str(project), "--platform", platform])
    assert res.exit_code == 0, res.output
    assert _agents(project, d) == before
