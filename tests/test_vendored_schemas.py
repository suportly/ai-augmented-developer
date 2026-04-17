"""T019 — vendored MCP schemas are valid JSON Schema 2020-12."""
from __future__ import annotations

import json
import pathlib

from jsonschema import Draft202012Validator

VENDOR_DIR = pathlib.Path(__file__).resolve().parents[1] / "schemas" / "vendor"


def test_mcp_tools_list_schema_is_valid() -> None:
    schema = json.loads((VENDOR_DIR / "mcp-tools-list.schema.json").read_text())
    Draft202012Validator.check_schema(schema)


def test_mcp_prompts_list_schema_is_valid() -> None:
    schema = json.loads((VENDOR_DIR / "mcp-prompts-list.schema.json").read_text())
    Draft202012Validator.check_schema(schema)
