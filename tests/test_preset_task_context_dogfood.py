"""T020 — dogfood ``task_context: true`` in the django-drf-react preset.

Spec context: ``specs/0014-bmad-inspired-evolutions/spec.md`` cl-8.
Article III (Simplicity / YAGNI) forbids "a new configuration flag
without a named user of the non-default value". The django-drf-react
preset is that named user — it activates the non-default
``task_context: true`` so the framework's own CI exercises the
opt-in path on every PR.

These tests pin three invariants:

1. ``presets/django-drf-react/preset.yaml`` parses cleanly as YAML and
   exposes ``task_context: true`` at the top level.
2. The other shipped presets (``lean``, ``mobile-ops``) do *not* set
   ``task_context: true`` — only the dogfood preset opts in. This guards
   against the flag silently flipping to default-on for every preset.
3. ``presets/catalog.json`` still parses as JSON and validates against
   ``schemas/preset-catalog.schema.json`` — the dogfood change must not
   break the catalog contract. (The catalog schema describes the preset
   *registry*, not per-preset fields, so the new flag should require no
   catalog change. This test will fail loudly if T020 ever drifts and
   adds an unrelated catalog edit that breaks validation.)
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml
from jsonschema import Draft202012Validator

REPO_ROOT = Path(__file__).resolve().parents[1]
PRESETS_DIR = REPO_ROOT / "presets"
CATALOG_PATH = PRESETS_DIR / "catalog.json"
CATALOG_SCHEMA_PATH = REPO_ROOT / "schemas" / "preset-catalog.schema.json"
DJANGO_PRESET_YAML = PRESETS_DIR / "django-drf-react" / "preset.yaml"


def _load_yaml(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise AssertionError(f"{path}: expected mapping at the root, got {type(data).__name__}")
    return data


# ---------------------------------------------------------------------------
# Invariant 1: dogfood preset has task_context: true at the top level.
# ---------------------------------------------------------------------------


def test_django_preset_yaml_parses_cleanly() -> None:
    assert DJANGO_PRESET_YAML.is_file(), (
        f"expected dogfood preset at {DJANGO_PRESET_YAML}"
    )
    data = _load_yaml(DJANGO_PRESET_YAML)
    # Sanity: the basic preset shape is intact (we did not corrupt the file).
    assert data.get("name") == "django-drf-react", (
        f"preset name regressed: {data.get('name')!r}"
    )


def test_django_preset_enables_task_context_dogfood() -> None:
    data = _load_yaml(DJANGO_PRESET_YAML)

    assert "task_context" in data, (
        "django-drf-react preset must declare `task_context` at the top "
        "level (cl-8: Article III named user). Missing key entirely."
    )
    assert data["task_context"] is True, (
        f"`task_context` must be exactly the boolean True (dogfood ON), "
        f"got {data['task_context']!r}"
    )


def test_django_preset_yaml_keeps_trailing_newline() -> None:
    raw = DJANGO_PRESET_YAML.read_bytes()
    assert raw.endswith(b"\n"), (
        "preset.yaml must end with a trailing newline (POSIX text file rule)"
    )


# ---------------------------------------------------------------------------
# Invariant 2: other presets do NOT silently enable task_context.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("preset_name", ["lean", "mobile-ops"])
def test_other_presets_do_not_enable_task_context(preset_name: str) -> None:
    preset_yaml = PRESETS_DIR / preset_name / "preset.yaml"
    assert preset_yaml.is_file(), f"missing preset.yaml for {preset_name}"
    data = _load_yaml(preset_yaml)

    # Either the field is absent (default off) or explicitly False.
    # It must NOT be True — only the django-drf-react preset is the
    # named user of the non-default value (cl-8).
    assert data.get("task_context", False) is False, (
        f"{preset_name} preset unexpectedly enables task_context "
        f"({data.get('task_context')!r}); only django-drf-react is the "
        f"declared dogfood named user."
    )


# ---------------------------------------------------------------------------
# Invariant 3: catalog.json still parses + validates after the edit.
# ---------------------------------------------------------------------------


def test_catalog_json_still_parses() -> None:
    payload = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    assert isinstance(payload, dict), "catalog.json root must be an object"
    assert "presets" in payload, "catalog.json must list `presets`"


def test_catalog_json_validates_against_schema() -> None:
    schema = json.loads(CATALOG_SCHEMA_PATH.read_text(encoding="utf-8"))
    payload = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))

    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(payload), key=lambda e: list(e.path))

    assert not errors, (
        "catalog.json must still validate against the catalog schema "
        "after enabling task_context dogfood; got: "
        + "; ".join(f"{list(e.path)}: {e.message}" for e in errors)
    )
