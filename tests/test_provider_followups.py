"""0021 — provider + token-economy fast-follows (polish)."""
from __future__ import annotations

import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
PLAN = ROOT / "skills" / "plan" / "SKILL.md"
REVIEW = ROOT / "skills" / "requesting-code-review" / "SKILL.md"
MCPS = ROOT / "presets" / "knowledge-graph" / "mcps.yaml"
DOC = ROOT / "docs" / "token-economy.md"


# --- T001: blast-radius in plan --------------------------------------------


def test_plan_has_optional_blast_radius() -> None:
    body = PLAN.read_text(encoding="utf-8")
    assert "blast-radius" in body.lower()
    assert "`impact`" in body
    assert "graceful degradation" in body.lower() or "degradação graciosa" in body.lower()


# --- T002: impacted subsystems in review -----------------------------------


def test_review_has_optional_impacted_subsystems() -> None:
    body = REVIEW.read_text(encoding="utf-8")
    lower = body.lower()
    assert "impacted subsystems" in lower
    assert "`impact`" in body
    assert "graceful degradation" in lower or "degradação graciosa" in lower


# --- T003: learn proposal can target a checklist category -------------------


def test_learn_proposal_can_target_checklist_category() -> None:
    import dataclasses

    from aiadev import learn
    from aiadev.commands.learn import _render_learnings

    mapped = learn.Pattern(
        kind="reviewer-recurrence", subject="code-reviewer",
        occurrences=2, features=("0001", "0002"), sufficient=True,
    )
    prop = learn.propose_guidance(mapped)
    assert prop.target_file.startswith("checklist:")  # S2.1

    # S2.3: an unmapped reviewer keeps the rules/ target (no regression).
    unmapped = dataclasses.replace(mapped, subject="plan-document-reviewer")
    assert learn.propose_guidance(unmapped).target_file.startswith("rules/")

    # S2.2: the checklist target shows up in the --write proposals artifact.
    rendered = _render_learnings([dataclasses.replace(mapped, proposal=prop)])
    assert "checklist:" in rendered


# --- T004: commented LSP example in the preset mcps.yaml --------------------


def test_mcps_has_commented_lsp_example() -> None:
    import json

    import yaml
    from jsonschema import Draft202012Validator

    body = MCPS.read_text(encoding="utf-8")
    # a commented example mentioning an LSP provider exists
    assert any(
        line.lstrip().startswith("#") and "lsp" in line.lower()
        for line in body.splitlines()
    )
    # parse stays valid against the schema, and the ACTIVE server is unchanged
    data = yaml.safe_load(body)
    schema = json.loads((ROOT / "schemas" / "mcps.schema.json").read_text())
    Draft202012Validator(schema).validate(data)
    assert set(data["servers"]) == {"graphify"}  # commented block is inert


# --- T005: PreToolUse hook example in the token-economy doc -----------------


def test_token_economy_doc_has_hook_example() -> None:
    body = DOC.read_text(encoding="utf-8")
    lower = body.lower()
    assert "pretooluse" in lower
    # a concrete example: a fenced code block that mentions the hook
    assert "```" in body and "hooks" in lower
    # Non-goal preserved (framework implements no compressor/hook)
    assert "non-goal" in lower or "fora de escopo" in lower
