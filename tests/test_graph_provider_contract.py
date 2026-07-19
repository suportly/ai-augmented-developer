"""T001/T002 — the knowledge-graph provider contract (spec 0017).

Story 1 sc1 + sc2: the `analyze` skill grounds its gaps in facts from a
graph provider. Article V requires that provider to sit behind a project
contract, not a vendor SDK. This module guards the contract schema
(`specs/0017-.../contracts/graph-provider.schema.json`) and the fake
provider fixture that conforms to it.
"""
from __future__ import annotations

import json
import pathlib

import pytest
from jsonschema import Draft202012Validator

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
CONTRACT = (
    REPO_ROOT
    / "specs"
    / "0017-knowledge-graph-context-provider"
    / "contracts"
    / "graph-provider.schema.json"
)

CONFIDENCE_VALUES = ["explicit", "inferred", "ambiguous"]


def _load() -> dict:
    assert CONTRACT.exists(), f"expected contract schema at {CONTRACT}"
    return json.loads(CONTRACT.read_text(encoding="utf-8"))


def test_schema_is_itself_a_valid_draft202012_schema() -> None:
    Draft202012Validator.check_schema(_load())


def test_schema_declares_the_three_queries() -> None:
    schema = _load()
    queries = schema["properties"]["queries"]["properties"]
    assert set(queries) == {"impact", "drift", "provenance"}, (
        "the contract must declare exactly impact/drift/provenance queries"
    )
    for name in ("impact", "drift", "provenance"):
        props = queries[name]["properties"]
        assert "request" in props and "response" in props, (
            f"query {name} must declare a request and a response shape"
        )


def test_confidence_enum_is_the_aiadev_vocabulary() -> None:
    schema = _load()
    assert schema["$defs"]["confidence"]["enum"] == CONFIDENCE_VALUES


def _subschema_validator(schema: dict, ref: str) -> Draft202012Validator:
    """Build a validator for one $def, keeping internal $ref resolution."""
    return Draft202012Validator({"allOf": [{"$ref": ref}], "$defs": schema["$defs"]})


# --- T002: the fake provider must conform to the contract ------------------


def test_fake_conforms_to_schema() -> None:
    fake = pytest.importorskip("tests.fixtures.graph_provider_fake")
    schema = _load()

    impact = fake.impact(paths=["src/aiadev/cli.py"])
    _subschema_validator(schema, "#/$defs/impactResponse").validate(impact)

    drift = fake.drift(tasks=["T001"], diff_paths=["src/aiadev/cli.py"])
    _subschema_validator(schema, "#/$defs/driftResponse").validate(drift)

    prov = fake.provenance(symbol="src/aiadev/cli.py:main")
    _subschema_validator(schema, "#/$defs/provenanceResponse").validate(prov)


def test_fake_labels_every_fact_with_a_confidence_value() -> None:
    fake = pytest.importorskip("tests.fixtures.graph_provider_fake")
    impact = fake.impact(paths=["src/aiadev/cli.py"])
    edges = [e for sub in impact["subsystems"] for e in sub["edges"]]
    assert edges, "impact response should carry at least one edge"
    for edge in edges:
        assert edge["confidence"] in CONFIDENCE_VALUES
