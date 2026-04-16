"""T012 — payload.build() assembles a ToolPayload validated against schema."""
from __future__ import annotations

import json
import pathlib

import jsonschema
import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
PAYLOAD_SCHEMA_PATH = (
    REPO_ROOT / "specs" / "0008-llm-tool-integration" / "contracts" / "tool-payload.schema.json"
)


def _load_schema() -> dict:
    return json.loads(PAYLOAD_SCHEMA_PATH.read_text(encoding="utf-8"))


class TestBuildPayload:
    def test_specify_payload_validates_against_schema(
        self, framework_root: pathlib.Path, tmp_path: pathlib.Path
    ) -> None:
        from aiadev._tooling.payload import build

        result = build("specify", framework_root, tmp_path, demand="test demand")
        schema = _load_schema()
        jsonschema.validate(instance=result, schema=schema)

    def test_payload_has_target_path_inside_workspace(
        self, framework_root: pathlib.Path, tmp_path: pathlib.Path
    ) -> None:
        from aiadev._tooling.payload import build

        result = build("specify", framework_root, tmp_path, demand="x")
        assert result["target_path"].startswith(str(tmp_path.resolve()))

    def test_marker_format_next_id_starts_at_1(
        self, framework_root: pathlib.Path, tmp_path: pathlib.Path
    ) -> None:
        from aiadev._tooling.payload import build

        result = build("specify", framework_root, tmp_path, demand="x")
        assert result["marker_format"]["next_id"] == 1

    def test_existing_markers_populated_for_clarify(
        self, framework_root: pathlib.Path, tmp_path: pathlib.Path
    ) -> None:
        from aiadev._tooling.payload import build

        spec = tmp_path / "specs" / "0001-test" / "spec.md"
        spec.parent.mkdir(parents=True)
        spec.write_text("[NEEDS CLARIFICATION:cl-1 question one]\nSome text.\n")

        result = build(
            "clarify", framework_root, tmp_path,
            spec_path=str(spec),
        )
        assert len(result["existing_markers"]) == 1
        assert result["existing_markers"][0]["id"] == "cl-1"
