"""T001/T002 — an LSP-backed provider conforms to the SAME 0017 contract.

Spec 0019: proving the graph-provider contract is provider-agnostic. This
second fake maps LSP operations (references / call-hierarchy / symbols /
definition) onto the impact/drift/provenance queries and must validate
against the unchanged ``graph-provider.schema.json`` from spec 0017.
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


def _schema() -> dict:
    return json.loads(CONTRACT.read_text(encoding="utf-8"))


def _subschema_validator(schema: dict, ref: str) -> Draft202012Validator:
    return Draft202012Validator({"allOf": [{"$ref": ref}], "$defs": schema["$defs"]})


def test_lsp_fake_conforms_to_0017_schema() -> None:
    lsp = pytest.importorskip("tests.fixtures.lsp_provider_fake")
    schema = _schema()

    impact = lsp.impact(paths=["src/aiadev/cli.py"])
    _subschema_validator(schema, "#/$defs/impactResponse").validate(impact)

    drift = lsp.drift(tasks=["T001"], diff_paths=["src/aiadev/cli.py"])
    _subschema_validator(schema, "#/$defs/driftResponse").validate(drift)

    prov = lsp.provenance(symbol="src/aiadev/cli.py:main")
    _subschema_validator(schema, "#/$defs/provenanceResponse").validate(prov)


# --- T002: confidence derives from LSP resolution ---------------------------


def test_lsp_facts_carry_confidence_from_resolution() -> None:
    lsp = pytest.importorskip("tests.fixtures.lsp_provider_fake")
    # A resolved reference is explicit.
    resolved = lsp.provenance(symbol="src/aiadev/cli.py:main")
    assert resolved["confidence"] == "explicit"

    # Every impact edge carries a valid aiadev confidence label.
    impact = lsp.impact(paths=["src/aiadev/cli.py"])
    edges = [e for sub in impact["subsystems"] for e in sub["edges"]]
    assert edges
    for edge in edges:
        assert edge["confidence"] in CONFIDENCE_VALUES

    # An unresolved / textual match degrades to inferred or ambiguous.
    unresolved = lsp.provenance(symbol="src/aiadev/unknown.py:mystery", resolved=False)
    assert unresolved["confidence"] in ("inferred", "ambiguous")
