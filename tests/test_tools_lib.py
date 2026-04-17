"""T015-T018 — aiadev.tools public API (specify, clarify, plan, tasks, etc.)."""
from __future__ import annotations

import json
import pathlib

import jsonschema
import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
PAYLOAD_SCHEMA = json.loads(
    (REPO_ROOT / "specs" / "0008-llm-tool-integration" / "contracts" / "tool-payload.schema.json")
    .read_text(encoding="utf-8")
)


# ── T015 — specify ─────────────────────────────────────────────────────

class TestSpecify:
    def test_returns_valid_payload(
        self, framework_root: pathlib.Path, tmp_path: pathlib.Path
    ) -> None:
        from aiadev.tools import specify

        result = specify(demand="test demand", workspace_path=str(tmp_path))
        jsonschema.validate(instance=result, schema=PAYLOAD_SCHEMA)
        assert result["skill"] == "specify"

    def test_target_path_inside_workspace(
        self, framework_root: pathlib.Path, tmp_path: pathlib.Path
    ) -> None:
        from aiadev.tools import specify

        result = specify(demand="x", workspace_path=str(tmp_path))
        assert result["target_path"].startswith(str(tmp_path.resolve()))

    def test_language_stamping(
        self, framework_root: pathlib.Path, tmp_path: pathlib.Path
    ) -> None:
        from aiadev.tools import specify

        result = specify(demand="x", workspace_path=str(tmp_path), language="pt-BR")
        assert "pt-BR" in result["prompt"] or "pt-BR" in json.dumps(result["context"])


# ── T016 — clarify ─────────────────────────────────────────────────────

class TestClarify:
    def test_accepts_id_answer_pairs(
        self, framework_root: pathlib.Path, tmp_path: pathlib.Path
    ) -> None:
        from aiadev.tools import clarify

        spec = tmp_path / "specs" / "0001-test" / "spec.md"
        spec.parent.mkdir(parents=True)
        spec.write_text(
            "# Spec\n## Problem\nX\n## Users and stakeholders\nX\n"
            "## Success criteria\nX\n## Non-goals\nX\n## User stories\nX\n"
            "## Clarifications\n[NEEDS CLARIFICATION:cl-1 question one]\n"
            "## Data touched\nX\n## Out-of-band effects\nX\n"
            "## Open risks\nX\n## Traceability\nX\n"
        )

        result = clarify(
            spec_path=str(spec),
            workspace_path=str(tmp_path),
            answers=[{"id": "cl-1", "answer": "resolved"}],
        )
        assert result["skill"] == "clarify"
        assert len(result["existing_markers"]) == 1

    def test_rejects_unknown_id(
        self, framework_root: pathlib.Path, tmp_path: pathlib.Path
    ) -> None:
        from aiadev._tooling import UnknownMarkerIdError
        from aiadev.tools import clarify

        spec = tmp_path / "specs" / "0001-test" / "spec.md"
        spec.parent.mkdir(parents=True)
        spec.write_text(
            "# Spec\n## Problem\nX\n## Users and stakeholders\nX\n"
            "## Success criteria\nX\n## Non-goals\nX\n## User stories\nX\n"
            "## Clarifications\n[NEEDS CLARIFICATION:cl-1 question]\n"
            "## Data touched\nX\n## Out-of-band effects\nX\n"
            "## Open risks\nX\n## Traceability\nX\n"
        )

        with pytest.raises(UnknownMarkerIdError):
            clarify(
                spec_path=str(spec),
                workspace_path=str(tmp_path),
                answers=[{"id": "cl-99", "answer": "bad"}],
            )


# ── T017 — plan + tasks ────────────────────────────────────────────────

class TestPlanAndTasks:
    def test_plan_rejects_malformed_spec(
        self, framework_root: pathlib.Path, tmp_path: pathlib.Path
    ) -> None:
        from aiadev._tooling import SpecInvalidError
        from aiadev.tools import plan

        spec = tmp_path / "specs" / "0001-test" / "spec.md"
        spec.parent.mkdir(parents=True)
        spec.write_text("# Spec\nNo real sections here.\n")
        with pytest.raises(SpecInvalidError):
            plan(spec_path=str(spec), workspace_path=str(tmp_path))

    def test_plan_prompt_mentions_constitution_check(
        self, framework_root: pathlib.Path, tmp_path: pathlib.Path
    ) -> None:
        from aiadev.tools import plan

        spec = tmp_path / "specs" / "0001-test" / "spec.md"
        spec.parent.mkdir(parents=True)
        spec.write_text(
            "# Spec\n## Problem\nX\n## Users and stakeholders\nX\n"
            "## Success criteria\nX\n## Non-goals\nX\n## User stories\nX\n"
            "## Clarifications\nX\n## Data touched\nX\n## Out-of-band effects\nX\n"
            "## Open risks\nX\n## Traceability\nX\n"
        )
        result = plan(spec_path=str(spec), workspace_path=str(tmp_path))
        assert "Constitution" in result["prompt"]

    def test_plan_requires_spec(
        self, framework_root: pathlib.Path, tmp_path: pathlib.Path
    ) -> None:
        from aiadev._tooling import SpecNotFoundError
        from aiadev.tools import plan

        with pytest.raises(SpecNotFoundError):
            plan(spec_path=str(tmp_path / "missing.md"), workspace_path=str(tmp_path))

    def test_plan_payload_references_constitution(
        self, framework_root: pathlib.Path, tmp_path: pathlib.Path
    ) -> None:
        from aiadev.tools import plan

        spec = tmp_path / "specs" / "0001-test" / "spec.md"
        spec.parent.mkdir(parents=True)
        spec.write_text(
            "# Spec\n## Problem\nX\n## Users and stakeholders\nX\n"
            "## Success criteria\nX\n## Non-goals\nX\n## User stories\nX\n"
            "## Clarifications\nX\n## Data touched\nX\n## Out-of-band effects\nX\n"
            "## Open risks\nX\n## Traceability\nX\n"
        )

        result = plan(spec_path=str(spec), workspace_path=str(tmp_path))
        assert result["skill"] == "plan"
        assert "Article" in result["context"]["constitution_excerpt"]

    def test_tasks_returns_payload(
        self, framework_root: pathlib.Path, tmp_path: pathlib.Path
    ) -> None:
        from aiadev.tools import tasks

        plan_file = tmp_path / "specs" / "0001-test" / "plan.md"
        plan_file.parent.mkdir(parents=True)
        plan_file.write_text("# Plan\n## Phase 1\nStuff.\n")

        result = tasks(plan_path=str(plan_file), workspace_path=str(tmp_path))
        assert result["skill"] == "tasks"


# ── T018 — implement / analyze / checklist / constitution ───────────────

class TestRemainingTools:
    @pytest.mark.parametrize("tool_name", ["implement", "analyze", "checklist", "constitution"])
    def test_returns_payload_with_correct_skill(
        self, framework_root: pathlib.Path, tmp_path: pathlib.Path, tool_name: str
    ) -> None:
        from aiadev import tools

        func = getattr(tools, tool_name)
        result = func(workspace_path=str(tmp_path))
        assert result["skill"] == tool_name
        assert "prompt" in result
