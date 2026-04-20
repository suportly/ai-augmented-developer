"""T003 — resolve_terse_mode() precedence: env over settings over default."""

import json
from pathlib import Path

import pytest

from aiadev.config import resolve_terse_mode


@pytest.fixture
def settings_file(tmp_path: Path):
    def _write(payload):
        p = tmp_path / "settings.json"
        if payload is None:
            return p  # non-existent
        p.write_text(json.dumps(payload), encoding="utf-8")
        return p

    return _write


def test_default_off(monkeypatch, settings_file):
    monkeypatch.delenv("AIADEV_TERSE", raising=False)
    assert resolve_terse_mode(settings_file(None)) == (False, "default")


def test_settings_on_env_unset(monkeypatch, settings_file):
    monkeypatch.delenv("AIADEV_TERSE", raising=False)
    path = settings_file({"aiadev.terseMode": True})
    assert resolve_terse_mode(path) == (True, "settings")


def test_settings_off_env_unset(monkeypatch, settings_file):
    monkeypatch.delenv("AIADEV_TERSE", raising=False)
    path = settings_file({"aiadev.terseMode": False})
    assert resolve_terse_mode(path) == (False, "default")


def test_env_on_wins_over_missing_settings(monkeypatch, settings_file):
    monkeypatch.setenv("AIADEV_TERSE", "1")
    assert resolve_terse_mode(settings_file(None)) == (True, "env")


def test_env_off_beats_settings_on(monkeypatch, settings_file):
    monkeypatch.setenv("AIADEV_TERSE", "0")
    path = settings_file({"aiadev.terseMode": True})
    assert resolve_terse_mode(path) == (False, "env")


@pytest.mark.parametrize("v", ["yes", "true", "True"])
def test_env_truthy_accepted(monkeypatch, settings_file, v):
    monkeypatch.setenv("AIADEV_TERSE", v)
    assert resolve_terse_mode(settings_file(None)) == (True, "env")


@pytest.mark.parametrize("v", ["no", "false", "False", "0", ""])
def test_env_falsy_accepted(monkeypatch, settings_file, v):
    monkeypatch.setenv("AIADEV_TERSE", v)
    assert resolve_terse_mode(settings_file(None)) == (False, "env")


def test_malformed_settings_raises(monkeypatch, tmp_path):
    monkeypatch.delenv("AIADEV_TERSE", raising=False)
    bad = tmp_path / "settings.json"
    bad.write_text("{ not valid json", encoding="utf-8")
    with pytest.raises(ValueError):
        resolve_terse_mode(bad)


def test_non_bool_settings_value_raises(monkeypatch, tmp_path):
    monkeypatch.delenv("AIADEV_TERSE", raising=False)
    p = tmp_path / "settings.json"
    p.write_text(json.dumps({"aiadev.terseMode": "on"}), encoding="utf-8")
    with pytest.raises(ValueError):
        resolve_terse_mode(p)
