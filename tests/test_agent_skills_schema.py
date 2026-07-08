"""Tests for the vendorized Agent Skills standard schema snapshot.

Spec: specs/0016-agent-skills-interop/spec.md, Story 1, sc2.
Plan: ADR-2/ADR-3 — schemas/agent-skills.schema.json is the EXTERNAL
conformance check for the open Agent Skills spec (agentskills.io). It must
NOT encode aiadev-internal shapes (those live in skill-frontmatter.schema.json).
"""

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "agent-skills.schema.json"


def _load_schema():
    assert SCHEMA_PATH.exists(), f"expected {SCHEMA_PATH} to exist"
    with SCHEMA_PATH.open(encoding="utf-8") as fh:
        return json.load(fh)


def test_schema_file_exists():
    assert SCHEMA_PATH.exists(), f"expected {SCHEMA_PATH} to exist"


def test_schema_loads_as_valid_json_and_is_itself_valid():
    schema = _load_schema()
    # The schema document must itself be a valid draft 2020-12 schema.
    Draft202012Validator.check_schema(schema)


def test_schema_records_snapshot_date_and_source():
    schema = _load_schema()
    comment = schema.get("$comment", "")
    assert comment, "expected a top-level $comment recording the spec snapshot"
    assert "2025-12-18" in comment, "expected the snapshot date in $comment"
    assert "agentskills.io" in comment.lower() or "agent skills" in comment.lower()


def test_accepts_minimal_conforming_frontmatter():
    schema = _load_schema()
    validator = Draft202012Validator(schema)
    minimal = {
        "name": "my-skill",
        "description": "Does a thing when invoked.",
    }
    errors = list(validator.iter_errors(minimal))
    assert not errors, f"minimal conforming frontmatter should validate: {errors}"


def test_accepts_optional_standard_fields_including_nested_metadata():
    schema = _load_schema()
    validator = Draft202012Validator(schema)
    full = {
        "name": "my-skill",
        "description": "Does a thing when invoked.",
        "license": "MIT",
        "compatibility": {"claude-code": ">=1.0.0"},
        "metadata": {
            "org.example.category": "productivity",
            "org.example.nested": {"foo": "bar", "count": 3},
        },
        "allowed-tools": ["Read", "Write"],
    }
    errors = list(validator.iter_errors(full))
    assert not errors, f"full standard frontmatter should validate: {errors}"


def test_accepts_allowed_tools_as_space_or_comma_separated_string():
    schema = _load_schema()
    validator = Draft202012Validator(schema)
    payload = {
        "name": "my-skill",
        "description": "Does a thing when invoked.",
        "allowed-tools": "Read, Write, Bash",
    }
    errors = list(validator.iter_errors(payload))
    assert not errors, f"string allowed-tools should validate: {errors}"


@pytest.mark.parametrize("proprietary_field", ["requires", "handoffs"])
def test_rejects_proprietary_top_level_fields(proprietary_field):
    schema = _load_schema()
    validator = Draft202012Validator(schema)
    payload = {
        "name": "my-skill",
        "description": "Does a thing when invoked.",
        proprietary_field: ["something"],
    }
    errors = list(validator.iter_errors(payload))
    assert errors, (
        f"proprietary field {proprietary_field!r} must NOT be accepted by the "
        "external Agent Skills conformance schema"
    )


def test_rejects_missing_required_fields():
    schema = _load_schema()
    validator = Draft202012Validator(schema)
    errors = list(validator.iter_errors({"name": "my-skill"}))
    assert errors, "description is required and must be reported missing"

    errors = list(validator.iter_errors({"description": "Does a thing."}))
    assert errors, "name is required and must be reported missing"
