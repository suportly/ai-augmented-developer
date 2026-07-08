"""Tests for the internal skill-frontmatter schema (aiadev pipeline shape).

Spec: specs/0016-agent-skills-interop/spec.md, Story 1, sc1 + cl-1 + cl-7.
Plan: ADR-1 — schemas/skill-frontmatter.schema.json is rewritten to the
Agent Skills standard shape at the top level (name, description, license,
compatibility, metadata, allowed-tools, plus the two documented runtime
extensions disable-model-invocation and argument-hint). The 5 proprietary
pipeline fields (version, inputs, outputs, requires, handoffs) move under
the single namespaced key ``metadata.aiadev``, preserving their previous
internal shapes.
"""

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "skill-frontmatter.schema.json"


def _load_schema():
    assert SCHEMA_PATH.exists(), f"expected {SCHEMA_PATH} to exist"
    with SCHEMA_PATH.open(encoding="utf-8") as fh:
        return json.load(fh)


def _validator():
    return Draft202012Validator(_load_schema())


def test_schema_file_exists():
    assert SCHEMA_PATH.exists(), f"expected {SCHEMA_PATH} to exist"


def test_schema_loads_as_valid_json_and_is_itself_valid():
    schema = _load_schema()
    Draft202012Validator.check_schema(schema)


def test_accepts_minimal_conforming_frontmatter():
    validator = _validator()
    minimal = {
        "name": "my-skill",
        "description": "Does a thing when invoked, sufficiently descriptive.",
    }
    errors = list(validator.iter_errors(minimal))
    assert not errors, f"minimal conforming frontmatter should validate: {errors}"


def test_accepts_migrated_frontmatter_with_pipeline_fields_under_metadata_aiadev():
    """Story 1 sc1: a migrated skill nests the 5 proprietary fields under
    metadata.aiadev and still validates."""
    validator = _validator()
    migrated = {
        "name": "implement",
        "description": "Execute an approved plan and tasks list, one task at a time.",
        "license": "MIT",
        "compatibility": "Requires git and a POSIX shell.",
        "allowed-tools": "Read, Write, Bash",
        "disable-model-invocation": False,
        "argument-hint": "[task-id]",
        "metadata": {
            "aiadev": {
                "version": "0.2.0",
                "inputs": [
                    {"type": "file", "path": "specs/<branch>/plan.md"},
                    {"type": "file", "path": "specs/<branch>/tasks.md"},
                ],
                "outputs": [
                    {
                        "type": "commit",
                        "description": "One commit per task, in order.",
                    }
                ],
                "requires": ["constitution", "test-driven-development"],
                "handoffs": ["analyze"],
            }
        },
    }
    errors = list(validator.iter_errors(migrated))
    assert not errors, f"migrated frontmatter should validate: {errors}"


def test_metadata_allows_third_party_keys_alongside_aiadev():
    validator = _validator()
    payload = {
        "name": "my-skill",
        "description": "Does a thing when invoked, sufficiently descriptive.",
        "metadata": {
            "aiadev": {"version": "0.1.0"},
            "org.example.category": "productivity",
            "org.example.nested": {"foo": "bar", "count": 3},
        },
    }
    errors = list(validator.iter_errors(payload))
    assert not errors, f"third-party metadata keys should be allowed: {errors}"


def test_metadata_aiadev_is_optional_and_all_its_keys_are_optional():
    validator = _validator()
    payload = {
        "name": "my-skill",
        "description": "Does a thing when invoked, sufficiently descriptive.",
        "metadata": {"aiadev": {}},
    }
    errors = list(validator.iter_errors(payload))
    assert not errors, f"empty metadata.aiadev should validate: {errors}"

    payload_no_metadata = {
        "name": "my-skill",
        "description": "Does a thing when invoked, sufficiently descriptive.",
    }
    errors = list(validator.iter_errors(payload_no_metadata))
    assert not errors, f"missing metadata entirely should validate: {errors}"


def test_rejects_metadata_aiadev_handoffs_with_non_string_item():
    validator = _validator()
    payload = {
        "name": "my-skill",
        "description": "Does a thing when invoked, sufficiently descriptive.",
        "metadata": {
            "aiadev": {
                "handoffs": ["ok-one", 42],
            }
        },
    }
    errors = list(validator.iter_errors(payload))
    assert errors, "metadata.aiadev.handoffs must reject non-string items"


def test_rejects_metadata_aiadev_requires_with_non_string_item():
    validator = _validator()
    payload = {
        "name": "my-skill",
        "description": "Does a thing when invoked, sufficiently descriptive.",
        "metadata": {
            "aiadev": {
                "requires": [{"nested": "object"}],
            }
        },
    }
    errors = list(validator.iter_errors(payload))
    assert errors, "metadata.aiadev.requires must reject non-string items"


def test_rejects_metadata_aiadev_unknown_key():
    validator = _validator()
    payload = {
        "name": "my-skill",
        "description": "Does a thing when invoked, sufficiently descriptive.",
        "metadata": {
            "aiadev": {
                "unknown-pipeline-field": "nope",
            }
        },
    }
    errors = list(validator.iter_errors(payload))
    assert errors, "metadata.aiadev must reject unknown keys (additionalProperties: false)"


def test_rejects_metadata_aiadev_bad_version_pattern():
    validator = _validator()
    payload = {
        "name": "my-skill",
        "description": "Does a thing when invoked, sufficiently descriptive.",
        "metadata": {"aiadev": {"version": "not-a-semver"}},
    }
    errors = list(validator.iter_errors(payload))
    assert errors, "metadata.aiadev.version must enforce the semver pattern"


def test_rejects_metadata_aiadev_input_with_bad_type_enum():
    validator = _validator()
    payload = {
        "name": "my-skill",
        "description": "Does a thing when invoked, sufficiently descriptive.",
        "metadata": {
            "aiadev": {
                "inputs": [{"type": "not-a-real-type"}],
            }
        },
    }
    errors = list(validator.iter_errors(payload))
    assert errors, "metadata.aiadev.inputs items must enforce the type enum"


def test_rejects_metadata_aiadev_output_with_bad_type_enum():
    validator = _validator()
    payload = {
        "name": "my-skill",
        "description": "Does a thing when invoked, sufficiently descriptive.",
        "metadata": {
            "aiadev": {
                "outputs": [{"type": "not-a-real-type"}],
            }
        },
    }
    errors = list(validator.iter_errors(payload))
    assert errors, "metadata.aiadev.outputs items must enforce the type enum"


@pytest.mark.parametrize("proprietary_field", ["version", "inputs", "outputs", "requires", "handoffs"])
def test_rejects_proprietary_fields_at_top_level(proprietary_field):
    """Story 1 sc1/sc3: the old top-level shape must now be a hard error."""
    validator = _validator()
    value = "0.1.0" if proprietary_field == "version" else ["something"]
    payload = {
        "name": "my-skill",
        "description": "Does a thing when invoked, sufficiently descriptive.",
        proprietary_field: value,
    }
    errors = list(validator.iter_errors(payload))
    assert errors, (
        f"proprietary field {proprietary_field!r} must NOT be accepted at the "
        "top level any more; it belongs under metadata.aiadev"
    )


def test_accepts_allowed_tools_as_array_or_string():
    """The internal schema keeps today's tolerance: existing consumer
    skills may use either shape for allowed-tools."""
    validator = _validator()
    as_string = {
        "name": "my-skill",
        "description": "Does a thing when invoked, sufficiently descriptive.",
        "allowed-tools": "Read, Write",
    }
    as_array = {
        "name": "my-skill",
        "description": "Does a thing when invoked, sufficiently descriptive.",
        "allowed-tools": ["Read", "Write"],
    }
    assert not list(validator.iter_errors(as_string))
    assert not list(validator.iter_errors(as_array))


def test_accepts_compatibility_as_string():
    validator = _validator()
    payload = {
        "name": "my-skill",
        "description": "Does a thing when invoked, sufficiently descriptive.",
        "compatibility": "Designed for Claude Code; requires git and jq.",
    }
    errors = list(validator.iter_errors(payload))
    assert not errors, f"compatibility as a string should validate: {errors}"


def test_rejects_compatibility_as_object():
    validator = _validator()
    payload = {
        "name": "my-skill",
        "description": "Does a thing when invoked, sufficiently descriptive.",
        "compatibility": {"claude-code": ">=1.0.0"},
    }
    errors = list(validator.iter_errors(payload))
    assert errors, "compatibility must be a string, not an object"


def test_accepts_documented_runtime_extension_fields_at_top_level():
    validator = _validator()
    payload = {
        "name": "deploy",
        "description": "Deploys the app when the user explicitly asks for it.",
        "disable-model-invocation": True,
        "argument-hint": "[backend|frontend] [--skip-checks]",
    }
    errors = list(validator.iter_errors(payload))
    assert not errors, f"documented runtime extensions should validate: {errors}"


def test_rejects_unknown_top_level_field():
    validator = _validator()
    payload = {
        "name": "my-skill",
        "description": "Does a thing when invoked, sufficiently descriptive.",
        "some-third-party-top-level-field": "nope",
    }
    errors = list(validator.iter_errors(payload))
    assert errors, "unknown top-level fields must still be rejected"


def test_rejects_missing_required_fields():
    validator = _validator()
    errors = list(validator.iter_errors({"name": "my-skill"}))
    assert errors, "description is required and must be reported missing"

    errors = list(validator.iter_errors({"description": "Does a thing, long enough."}))
    assert errors, "name is required and must be reported missing"
