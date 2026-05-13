"""T002 — terse-output schema validates one-line-per-finding, rejects violations.

T005 (Story 3 sc5) extends the schema with a `kind` discriminator that
distinguishes a "verification" finding (an explicit audit check listed
under APPROVED's `### Why no issues` block) from a regular nit.
"""

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
    pytest.param(
        {
            "verdict": "APPROVED",
            "findings": [
                {
                    "severity": "🟢",
                    "location": "views.py:42",
                    "message": "queryset escopado por usuário",
                    "kind": "verification",
                },
                {
                    "severity": "🟢",
                    "location": "serializers.py:18",
                    "message": "input validado via DRF serializer",
                    "kind": "verification",
                },
                {
                    "severity": "🟢",
                    "location": "tests/test_orders.py:30",
                    "message": "test coverage exercita acceptance scenario AC-2",
                    "kind": "verification",
                },
            ],
        },
        id="approved_with_verification_block",
    ),
    pytest.param(
        {
            "verdict": "CHANGES_REQUESTED",
            "findings": [
                {
                    "severity": "🟢",
                    "location": "tests/test_x.py:5",
                    "message": "consider extracting helper",
                    "kind": "nit",
                }
            ],
        },
        id="explicit_nit_kind_still_valid",
    ),
    pytest.param(
        {
            "verdict": "CHANGES_REQUESTED",
            "findings": [
                {
                    "severity": "🟢",
                    "location": "tests/test_x.py:5",
                    "message": "missing kind defaults to nit semantics — backward compat",
                }
            ],
        },
        id="kind_omitted_backward_compatible",
    ),
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
    pytest.param(
        {
            "verdict": "APPROVED",
            "findings": [
                {
                    "severity": "🟢",
                    "location": "views.py:42",
                    "message": "verificação realizada",
                    "kind": "audit",  # not in enum
                }
            ],
        },
        id="kind_enum_rejected",
    ),
    pytest.param(
        {
            "verdict": "APPROVED",
            "findings": [
                {
                    "severity": "🔴",
                    "location": "views.py:42",
                    "message": "verification kind only valid with green severity",
                    "kind": "verification",
                }
            ],
        },
        id="verification_requires_green_severity",
    ),
]


@pytest.mark.parametrize("payload", INVALID)
def test_invalid_payloads_rejected(validator, payload):
    with pytest.raises(ValidationError):
        validator.validate(payload)


# ---- Story 3 sc5: literal `🟢 file:line — verificação realizada` line ------


def test_verification_line_round_trips_through_schema(validator):
    """Spec sc5 mandates the human-readable line shape:
    `🟢 file:line — verificação realizada`. The structured form below is what
    a reviewer subagent emits and the orchestrator validates against the
    schema; rendering back to the line happens at the presentation layer.
    """
    payload = {
        "verdict": "APPROVED",
        "findings": [
            {
                "severity": "🟢",
                "location": "src/aiadev/cli.py:120",
                "message": "verificação realizada",
                "kind": "verification",
            }
        ],
    }
    validator.validate(payload)

    finding = payload["findings"][0]
    rendered = f"{finding['severity']} {finding['location']} — {finding['message']}"
    assert rendered == "🟢 src/aiadev/cli.py:120 — verificação realizada"
