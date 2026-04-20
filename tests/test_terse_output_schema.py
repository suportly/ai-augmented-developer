"""T002 — terse-output schema validates one-line-per-finding, rejects violations."""

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, ValidationError

SCHEMA_PATH = Path(__file__).resolve().parents[1] / "schemas" / "terse-output.schema.json"


@pytest.fixture(scope="module")
def validator():
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


# ---- valid cases -----------------------------------------------------------

VALID = [
    {
        "verdict": "CHANGES_REQUESTED",
        "findings": [
            {"severity": "🔴", "location": "plan.md:42", "message": "missing Constitution Check"},
            {"severity": "🟡", "location": "spec.md:7", "message": "ambiguous success criterion"},
        ],
    },
    {"verdict": "APPROVED", "findings": []},
]


@pytest.mark.parametrize("payload", VALID)
def test_valid_payloads_pass(validator, payload):
    validator.validate(payload)  # raises on failure


# ---- invalid cases ---------------------------------------------------------

INVALID = [
    pytest.param(
        {
            "verdict": "CHANGES_REQUESTED",
            "findings": [
                {
                    "severity": "🔴",
                    "location": "plan.md:42",
                    "message": "line one\nline two — this multi-paragraph form is exactly what terse-mode rejects",
                }
            ],
        },
        id="multiline_message_rejected",
    ),
    pytest.param(
        {
            "verdict": "CHANGES_REQUESTED",
            "findings": [{"location": "plan.md:42", "message": "missing severity"}],
        },
        id="missing_severity_rejected",
    ),
    pytest.param(
        {
            "verdict": "CHANGES_REQUESTED",
            "findings": [{"severity": "🔴", "message": "missing location"}],
        },
        id="missing_location_rejected",
    ),
    pytest.param(
        {
            "verdict": "CHANGES_REQUESTED",
            "findings": [
                {"severity": "BUG", "location": "p:1", "message": "severity must be a glyph"}
            ],
        },
        id="severity_enum_rejected",
    ),
    pytest.param(
        {
            "verdict": "CHANGES_REQUESTED",
            "findings": [
                {
                    "severity": "🔴",
                    "location": "plan.md:42",
                    "message": "x" * 200,
                }
            ],
        },
        id="oversized_message_rejected",
    ),
    pytest.param(
        {
            "verdict": "MAYBE",
            "findings": [],
        },
        id="verdict_enum_rejected",
    ),
    pytest.param(
        {
            "verdict": "APPROVED",
            "findings": [],
            "extra": "no additional properties allowed",
        },
        id="additional_properties_rejected",
    ),
]


@pytest.mark.parametrize("payload", INVALID)
def test_invalid_payloads_rejected(validator, payload):
    with pytest.raises(ValidationError):
        validator.validate(payload)
