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


# ── Payload contract regression tests (issues #14–#19) ─────────────────

class TestPayloadContract:
    def test_specify_embeds_demand_verbatim(
        self, framework_root: pathlib.Path, tmp_path: pathlib.Path
    ) -> None:
        from aiadev.tools import specify

        demand = "MY_UNIQUE_STRING_xyz build a TODO app"
        result = specify(demand=demand, workspace_path=str(tmp_path))
        assert demand in result["prompt"]

    def test_specify_emits_target_path_directive(
        self, framework_root: pathlib.Path, tmp_path: pathlib.Path
    ) -> None:
        from aiadev.tools import specify

        result = specify(demand="x", workspace_path=str(tmp_path))
        assert result["target_path"] in result["prompt"]
        assert "Target path (authoritative)" in result["prompt"]

    def test_specify_respects_explicit_slug(
        self, framework_root: pathlib.Path, tmp_path: pathlib.Path
    ) -> None:
        from aiadev.tools import specify

        result = specify(
            demand="short", workspace_path=str(tmp_path),
            slug="my-chosen-slug",
        )
        assert "0001-my-chosen-slug/spec.md" in result["target_path"]

    def test_specify_non_english_adds_header_guard(
        self, framework_root: pathlib.Path, tmp_path: pathlib.Path
    ) -> None:
        from aiadev.tools import specify

        result = specify(
            demand="x", workspace_path=str(tmp_path), language="pt-BR",
        )
        assert "Language and schema invariant" in result["prompt"]
        assert "<!-- section: <name> -->" in result["prompt"]
        assert "Problem" in result["prompt"]

    def test_specify_inlines_template_body(
        self, framework_root: pathlib.Path, tmp_path: pathlib.Path
    ) -> None:
        from aiadev.tools import specify

        result = specify(demand="x", workspace_path=str(tmp_path))
        assert "{{FEATURE_NAME}}" in result["prompt"]

    def test_specify_declares_single_artifact(
        self, framework_root: pathlib.Path, tmp_path: pathlib.Path
    ) -> None:
        from aiadev.tools import specify

        result = specify(demand="x", workspace_path=str(tmp_path))
        assert "Single required artifact" in result["prompt"]
        assert "spec.md" in result["prompt"]

    def test_clarify_embeds_resolved_answers(
        self, framework_root: pathlib.Path, tmp_path: pathlib.Path
    ) -> None:
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

        magic = "UNIQUE_ANSWER_ZZZ"
        result = clarify(
            spec_path=str(spec),
            workspace_path=str(tmp_path),
            answers=[{"id": "cl-1", "answer": f"{magic} the actual answer"}],
        )
        assert magic in result["prompt"]
        assert "cl-1" in result["prompt"]
        assert "AUTOMATED EXECUTION" in result["prompt"]

    def test_plan_inlines_plan_template(
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
        assert "Skill template" in result["prompt"]
        assert result["context"]["template"]["content"].splitlines()[0] in result["prompt"]

    def test_tasks_prompt_forbids_auxiliary_outputs(
        self, framework_root: pathlib.Path, tmp_path: pathlib.Path
    ) -> None:
        from aiadev.tools import tasks

        plan_file = tmp_path / "specs" / "0001-test" / "plan.md"
        plan_file.parent.mkdir(parents=True)
        plan_file.write_text("# Plan\n")

        result = tasks(plan_path=str(plan_file), workspace_path=str(tmp_path))
        assert "Single required artifact" in result["prompt"]
        assert "tasks.md" in result["prompt"]
        assert "contracts/" in result["prompt"]

    def test_locate_latest_artifact_finds_divergent_slug(
        self, framework_root: pathlib.Path, tmp_path: pathlib.Path
    ) -> None:
        from aiadev.tools import locate_latest_artifact

        written = tmp_path / "specs" / "0001-llm-chose-this" / "spec.md"
        written.parent.mkdir(parents=True)
        written.write_text("# Spec\n")

        found = locate_latest_artifact(str(tmp_path), artifact="spec.md")
        assert found == written.resolve()

    def test_locate_latest_artifact_returns_none_when_missing(
        self, framework_root: pathlib.Path, tmp_path: pathlib.Path
    ) -> None:
        from aiadev.tools import locate_latest_artifact

        assert locate_latest_artifact(str(tmp_path), artifact="spec.md") is None

    @pytest.mark.parametrize(
        "skill, min_tokens",
        [
            ("specify", 16_384),
            ("clarify", 16_384),
            ("plan", 32_768),
            ("tasks", 32_768),
            ("implement", 32_768),
            ("analyze", 8_192),
            ("checklist", 8_192),
            ("constitution", 16_384),
        ],
    )
    def test_payload_includes_recommended_max_tokens(
        self, framework_root: pathlib.Path, tmp_path: pathlib.Path,
        skill: str, min_tokens: int,
    ) -> None:
        """#20 — consumers should not need to read docs to size max_tokens."""
        import aiadev.tools as tools

        if skill == "specify":
            result = tools.specify(demand="x", workspace_path=str(tmp_path))
        elif skill in ("plan", "clarify"):
            spec = tmp_path / "specs" / "0001-test" / "spec.md"
            spec.parent.mkdir(parents=True)
            sections = [
                "Problem", "Users and stakeholders", "Success criteria",
                "Non-goals", "User stories", "Clarifications", "Data touched",
                "Out-of-band effects", "Open risks", "Traceability",
            ]
            spec.write_text(
                "# F\n" + "\n\n".join(f"## {s}\nx" for s in sections)
            )
            result = getattr(tools, skill)(
                spec_path=str(spec), workspace_path=str(tmp_path),
            )
        elif skill == "tasks":
            plan_file = tmp_path / "specs" / "0001-test" / "plan.md"
            plan_file.parent.mkdir(parents=True)
            plan_file.write_text("# Plan\n")
            result = tools.tasks(
                plan_path=str(plan_file), workspace_path=str(tmp_path),
            )
        else:
            result = getattr(tools, skill)(workspace_path=str(tmp_path))

        assert result["recommended_max_tokens"] == min_tokens

    def test_spec_with_html_anchors_passes_validation(
        self, framework_root: pathlib.Path, tmp_path: pathlib.Path
    ) -> None:
        """#15 — translated headings with anchors must not fail validation."""
        from aiadev.tools import clarify

        spec = tmp_path / "specs" / "0001-test" / "spec.md"
        spec.parent.mkdir(parents=True)
        pt_sections = {
            "Problem": "Problema",
            "Users and stakeholders": "Usuários e stakeholders",
            "Success criteria": "Critérios de sucesso",
            "Non-goals": "Fora do escopo",
            "User stories": "Histórias de usuário",
            "Clarifications": "Esclarecimentos",
            "Data touched": "Dados afetados",
            "Out-of-band effects": "Efeitos colaterais",
            "Open risks": "Riscos em aberto",
            "Traceability": "Rastreabilidade",
        }
        body_parts = ["# Especificação\n"]
        for english, localized in pt_sections.items():
            body_parts.append(f"<!-- section: {english} -->")
            body_parts.append(f"## {localized}")
            body_parts.append("conteúdo em português\n")
        body_parts.append(
            "\n[NEEDS CLARIFICATION:cl-1 pergunta aberta?]\n"
        )
        spec.write_text("\n".join(body_parts))

        # Should not raise SpecInvalidError even though every heading is
        # translated — the HTML section anchors carry the schema.
        result = clarify(
            spec_path=str(spec), workspace_path=str(tmp_path),
            answers=[{"id": "cl-1", "answer": "resposta"}],
        )
        assert result["skill"] == "clarify"
