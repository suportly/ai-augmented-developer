"""T017 — the terse-mode rule exists in three synchronized copies."""

import hashlib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CANONICAL = ROOT / "rules" / "terse-mode.md"
LOCAL_MIRROR = ROOT / ".claude" / "rules" / "terse-mode.md"
ASSETS_MIRROR = ROOT / "src" / "aiadev" / "_assets" / "rules" / "terse-mode.md"


def test_canonical_rule_exists():
    assert CANONICAL.exists(), (
        "rules/terse-mode.md is the tracked source of truth — must exist"
    )


def test_sync_assets_ships_the_rule():
    """scripts/sync_assets.py copies rules/ to _assets/rules/, so the packaged
    wheel must end up with an identical copy. We assert the copy plan here
    rather than at runtime so CI catches any missing source before a build."""
    sync_plan = (ROOT / "scripts" / "sync_assets.py").read_text(encoding="utf-8")
    assert '("rules", "rules")' in sync_plan, (
        "sync_assets.py must copy rules/ into _assets/rules/"
    )


def test_local_mirror_matches_when_present():
    if not LOCAL_MIRROR.exists():
        pytest.skip(".claude/ is gitignored; local copy optional in CI")
    expected = CANONICAL.read_bytes()
    assert LOCAL_MIRROR.read_bytes() == expected, (
        ".claude/rules/terse-mode.md drifted from rules/terse-mode.md"
    )


def test_assets_mirror_matches_when_present():
    if not ASSETS_MIRROR.exists():
        pytest.skip("_assets/ is build-generated; run scripts/sync_assets.py first")
    expected_sha = hashlib.sha256(CANONICAL.read_bytes()).hexdigest()
    actual_sha = hashlib.sha256(ASSETS_MIRROR.read_bytes()).hexdigest()
    assert expected_sha == actual_sha, (
        "src/aiadev/_assets/rules/terse-mode.md drifted — rerun sync_assets.py"
    )


def test_rule_names_switch_and_echo_template():
    body = CANONICAL.read_text(encoding="utf-8")

    # Settings key + env var precedence.
    assert "aiadev.terseMode" in body, "rule must name the settings key"
    assert "AIADEV_TERSE" in body, "rule must name the env var"
    assert "env wins" in body.lower() or "env overrides" in body.lower(), (
        "rule must state env-over-settings precedence"
    )

    # Echo template and source labels.
    assert "terse-mode: <on|off> (<source>)" in body, (
        "rule must declare the exact echo template"
    )
    for label in ("default", "settings", "env"):
        assert f"`{label}`" in body, f"rule must list `{label}` as a source label"
