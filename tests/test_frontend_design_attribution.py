"""frontend-design attribution (spec 0035)."""
from __future__ import annotations

import hashlib
import importlib.util
import pathlib

import pytest
import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "presets" / "django-drf-react" / "skills" / "frontend-design"

# sha256 of anthropics/skills skills/frontend-design/LICENSE.txt (Apache-2.0).
UPSTREAM_LICENSE_SHA256 = "0d542e0c8804e39aa7f37eb00da5a762149dc682d7829451287e11b938e94594"

CURRENT_DESC = (
    "Create distinctive, production-grade frontend interfaces with high design quality. "
    "Use when building web components, pages, or React Native screens. "
    "Generates creative, polished code that avoids generic AI aesthetics."
)


def _frontmatter() -> dict:
    text = (SKILL_DIR / "SKILL.md").read_text("utf-8")
    return yaml.safe_load(text.split("---", 2)[1])


def test_license_file_is_upstream_apache_text() -> None:
    data = (SKILL_DIR / "LICENSE.txt").read_bytes()
    assert hashlib.sha256(data).hexdigest() == UPSTREAM_LICENSE_SHA256
    head = data.decode("utf-8").split()
    assert head[:5] == ["Apache", "License", "Version", "2.0,", "January"]


def test_license_field_credits_upstream_and_modification() -> None:
    lic = _frontmatter()["license"]
    assert "Apache-2.0" in lic
    assert "anthropics/skills" in lic
    assert "modified" in lic
    assert "Strivex" not in lic


def test_name_and_description_unchanged() -> None:
    fm = _frontmatter()
    assert fm["name"] == "frontend-design"
    assert fm["description"] == CURRENT_DESC


@pytest.fixture(scope="module")
def installed(tmp_path_factory: pytest.TempPathFactory) -> pathlib.Path:
    spec = importlib.util.spec_from_file_location(
        "instruction_budget", ROOT / "scripts" / "instruction_budget.py"
    )
    module = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    dest = tmp_path_factory.mktemp("django")
    module.install_preset("django-drf-react", dest)
    return dest


def test_install_leaves_license_next_to_skill_md(installed: pathlib.Path) -> None:
    skill_md = next(installed.rglob("frontend-design/SKILL.md"))
    license_file = skill_md.parent / "LICENSE.txt"
    assert license_file.is_file()
    assert hashlib.sha256(license_file.read_bytes()).hexdigest() == UPSTREAM_LICENSE_SHA256


ALLOWED_STRIVEX = {
    "CHANGELOG.md",
    "vscode-extension/CHANGELOG.md",
    "CREDITS.md",
    "tests/test_frontend_design_attribution.py",
    "tests/test_frontend_design_quality.py",
}


def _credits_entry() -> str:
    body = (ROOT / "CREDITS.md").read_text(encoding="utf-8")
    return body.split("### [anthropics/skills]", 1)[1].split("\n### ", 1)[0].split("\n## ", 1)[0]


def test_credits_entry_for_anthropics_skills() -> None:
    entry = _credits_entry()
    for needle in ("frontend-design", "Apache-2.0", "modified", "2026-11-06", "Strivex"):
        assert needle in entry, needle
    assert "mislabel" in entry.lower() or "wrong" in entry.lower()


def test_strivex_only_in_history_and_the_correction_note() -> None:
    import subprocess

    import pytest

    try:
        files = subprocess.run(
            ["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True
        ).stdout.splitlines()
    except (OSError, subprocess.CalledProcessError):
        pytest.skip("not a git checkout (e.g. sdist)")
    hits = []
    for name in files:
        if name in ALLOWED_STRIVEX or name.startswith("specs/"):
            continue
        path = ROOT / name
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, FileNotFoundError):
            continue
        if "strivex" in text.lower():
            hits.append(name)
    assert hits == []


def test_changelog_unreleased_records_0035() -> None:
    body = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    sec = body.split("## [Unreleased]", 1)[1].split("\n## [", 1)[0]
    for needle in ("0035", "anthropics/skills", "LICENSE.txt", "Strivex"):
        assert needle in sec, needle
