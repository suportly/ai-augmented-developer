# Implementation plan: Specify reconnaissance step

> Produced by the `plan` skill from an approved `spec.md`. This file describes **how** the spec will be realized. Do not rewrite `spec.md` into `plan.md`.

**Branch:** `feature/specify-reconnaissance`
**Date:** 2026-04-27
**Spec:** [spec.md](./spec.md)
**Plan version:** 1
**Language:** en

---

## Summary

Add a `Reconnaissance` section to `templates/spec-template.md`, a matching step in `skills/specify/SKILL.md`, a structural rule in the schema validator, and a one-line orientation note in `skills/using-ai-augmented-developer/SKILL.md`. Wire the validator into `aiadev validate` so it runs on every `spec.md` whose `Spec ID` exceeds the cutover (pinned in this PR). Test-first: every artifact change ships with a regression test under `tests/`. Work splits into 4 phases over an estimated ~10 small tasks.

## Technical context

| Field | Value |
|---|---|
| Active preset | framework (`ai-augmented-developer` itself) |
| Language / runtime | Python 3.11+ |
| Primary dependencies | `click`, `jsonschema`, `pyyaml`, `rich` (already in `pyproject.toml`) |
| Storage | files on disk (no DB) |
| Testing framework | `pytest` (existing test suite under `tests/`) |
| Target platform(s) | local CLI + Claude Code Skill tool |
| Performance budget | validator must add < 50 ms to a `aiadev validate` run on a single spec |
| Security considerations | read-only file inspection; no new network or shell-out paths |

## Constitution check

| Article | Applies? | Status | Evidence |
|---|---|---|---|
| I. Spec-first | Yes | PASS | `specs/0011-specify-reconnaissance/spec.md` reviewer-approved 2026-04-27 |
| II. Test-first | Yes | PASS | each phase opens with a failing test (see Phase breakdown); `tests/test_validate.py` and a new `tests/test_spec_recon_validation.py` carry the assertions before implementation |
| III. Simplicity | Yes | PASS | no new abstraction layer — extends existing `validate_paths` with one rule and adds one schema; no new CLI subcommand |
| IV. Evidence over claims | Yes | PASS | every recon entry must cite a file path (validator-checked); plan exit criteria are runnable `pytest` commands |
| V. Provider pattern | No | N/A | no provider added |
| VI. Privacy by design | No | N/A | no PII; read-only on local files |
| VII. Attribution | No | N/A | no adapted material |

No `FAIL` rows. **Complexity tracking** below stays empty.

## Architecture decisions

- **Decision:** The `Reconnaissance` rule lives inside the existing `aiadev.validate` module, gated by a per-rule `applies_to` predicate that reads the spec's `Spec ID` header.
  **Rationale:** keeps the validator surface single (`aiadev validate` already shells the rule set); a separate command would force users to remember two entry points.
  **Trade-offs:** the validate module grows; mitigated by extracting a small `spec_rules.py` submodule when the second spec rule lands (YAGNI for now — only one rule).

- **Decision:** Surface detection is structural, not heuristic. The validator counts entries inside the recon block; it does not parse `Problem` for noun phrases.
  **Rationale:** spec cl-1 resolution; deterministic, locale-independent, no NLP dependency.
  **Trade-offs:** an agent that omits a real surface from the recon list bypasses detection. Mitigated by skill prose ("name every surface from the demand") and the reviewer subagent's behavioural check.

- **Decision:** Cutover by `Spec ID` (strict greater-than), pinned in `schemas/spec-recon.schema.json` at merge time.
  **Rationale:** spec cl-3 resolution; date-based cutover is fragile; free opt-out defeats the purpose.
  **Trade-offs:** the cutover number is a magic constant in the schema. Mitigated by a single-source comment in the schema and a test that asserts the cutover stays monotonic.

- **Decision:** No new CLI subcommand (`aiadev validate-spec` was considered and rejected).
  **Rationale:** spec rule extends the same validator pipeline; `aiadev validate <path-to-spec.md>` already accepts arbitrary paths.
  **Trade-offs:** validator entry point now mixes SKILL.md and spec.md; mitigated by file-extension dispatch inside `validate_paths`.

- **Decision:** Recon entries use a Markdown bullet list with a fixed micro-format. Exact line shape:
  `` - **<surface-name>** — entry: `<path>` · auth: `<path|none>` · integration: `<path-or-grep-term>` ``
  Single-surface opt-out line shape (must be the *only* non-comment content in the section):
  `Reconnaissance: not required (single-surface change: <surface-name>)`.
  **Rationale:** cheap to author by hand, cheap to parse with a regex (`^- \*\*[^*]+\*\* — entry: ` + backticked path), survives translation of the heading.
  **Trade-offs:** a stricter YAML or table format would be easier to validate, but harder to write inline; the regex approach matches the existing anchor-comment style in templates.

- **Decision:** Schema file `schemas/spec-recon.schema.json` is a thin JSON document with three top-level keys:
  - `cutover_spec_id` (integer constant, pinned at `10` for this PR — every spec with id `> 10` must satisfy the rule).
  - `recon_entry_pattern` (regex string used by the Python validator, not by jsonschema directly).
  - `opt_out_pattern` (regex string for the single-surface opt-out line).
  The validator loads the JSON, reads the three values, and applies them. No `$schema` draft validation runs against `spec.md` — the schema is a config file with the JSON-Schema name only for repository consistency.
  **Rationale:** spec is Markdown, not JSON; jsonschema cannot validate it directly. A config-as-schema pattern keeps everything under `schemas/` for discoverability without a fake JSON envelope around Markdown.
  **Trade-offs:** the file does not strictly conform to a JSON-Schema draft; mitigated by a unit test that asserts the three keys exist and have the expected types.

- **Decision:** `validate_spec(path: pathlib.Path) -> ValidationReport` lives in `src/aiadev/validate.py` next to the existing `validate_paths()`. It reuses the existing `SkillIssue` dataclass (rename to `ValidationIssue` is out of scope; the field names already work for spec issues — `path` and `message`). `validate_paths` gains an extension-dispatch branch: `.md` paths whose basename is `spec.md` route to `validate_spec`; everything else continues to the existing skill-frontmatter path. No new public types, no new CLI subcommand.
  **Rationale:** smallest surface change; one entry point for users.
  **Trade-offs:** the dataclass name `SkillIssue` is now misleading; an inline comment documents the reuse decision. Rename can land later if the file grows another rule.

## Project structure changes

```text
templates/spec-template.md                                       (modified — new <!-- section: Reconnaissance --> block + bullet micro-format)
skills/specify/SKILL.md                                          (modified — Loop step 2.5 "Reconnaissance" + step 5 prose)
skills/using-ai-augmented-developer/SKILL.md                     (modified — one-line note under "Pipeline skills")
schemas/spec-recon.schema.json                                   (new — JSON schema with cutover_spec_id constant + recon-entry pattern)
src/aiadev/validate.py                                           (modified — file-type dispatch; new validate_spec()/recon rule)
src/aiadev/commands/validate.py                                  (modified — accept .md paths that resolve to spec.md and route to validate_spec())
tests/test_spec_recon_validation.py                              (new — covers Story 2 acceptance scenarios)
tests/test_specify_skill_has_recon_step.py                       (new — covers Success criterion 6 + Story 3 scenario 2)
tests/test_using_aia_mentions_recon.py                           (new — covers Story 3 scenario 1)
tests/test_spec_template_has_recon_anchor.py                     (new — covers Success criterion 5: anchor + micro-format example in template)
tests/fixtures/spec-recon/                                       (new — three fixture spec.md files: valid, empty-recon, prose-only)
CHANGELOG.md                                                     (modified — entry under [Unreleased] / Added)
```

`presets/*/templates/spec-template.md` files — none currently exist in the repo (verified with `find presets -name spec-template.md`); the cl-4 decision is forward-looking and applies whenever a preset adds its own template.

## Phase breakdown

> Each phase is a checkpoint. Within a phase, tasks are independent enough that order does not matter — across phases, order does matter.

### Phase 1 — Tests first (red)

Failing tests that pin the contract before any production code is written. Each test name below is the exact `def test_*` symbol the `tasks` skill should produce.

- `tests/test_spec_recon_validation.py`
  - `test_empty_recon_section_exits_nonzero` — empty section, no opt-out → `validate_spec` reports `Reconnaissance section required`.
  - `test_optout_line_passes_validation` — single-surface opt-out line → exits 0.
  - `test_prose_only_recon_fails_validation` — bullet without a backticked path → reports `Reconnaissance entries must cite at least one file path per surface`.
  - `test_recon_path_does_not_exist_fails_validation` — entry cites a path that is not on disk → reports `Reconnaissance path '<p>' does not exist`.
  - `test_grandfathered_spec_passes_without_recon` — fixture `spec.md` with `Spec ID: 0009` and no recon section → exits 0 (cutover guard).
  - `test_cutover_spec_id_pinned_at_ten` — loads `schemas/spec-recon.schema.json` and asserts `cutover_spec_id == 10` (regression guard from the Risks table).
- `tests/test_specify_skill_has_recon_step.py`
  - `test_specify_skill_mentions_reconnaissance` — `skills/specify/SKILL.md` contains the literal `Reconnaissance` ≥ 1× and a numbered Loop step that introduces it.
  - `test_specify_skill_forbids_analogy_drafts` — same file contains a "What not to do" entry mentioning analogy/sibling-surface drafting (covers Story 1 scenario 2 indirectly via skill prose).
  - `test_specify_skill_pauses_on_premise_mismatch` — same file contains a Loop instruction that the agent must **pause and surface the mismatch to the user** when recon contradicts the demand's premise (covers Story 1 scenario 2 directly).
- `tests/test_using_aia_mentions_recon.py`
  - `test_orientation_mentions_reconnaissance` — `skills/using-ai-augmented-developer/SKILL.md` contains the literal `Reconnaissance` and a Markdown link to `skills/specify/SKILL.md`.
- `tests/test_spec_template_has_recon_anchor.py` (new file — covers Success criterion 5 explicitly)
  - `test_spec_template_has_reconnaissance_anchor` — `templates/spec-template.md` contains the exact comment `<!-- section: Reconnaissance -->`.
  - `test_spec_template_recon_block_documents_micro_format` — same file contains an example bullet matching the `recon_entry_pattern` regex.
- Fixtures under `tests/fixtures/spec-recon/`: `valid-recon.md`, `empty-recon.md`, `optout-recon.md`, `prose-only-recon.md`, `nonexistent-path-recon.md`, `legacy-spec-0009.md`.

Exit criterion: running `pytest tests/test_spec_recon_validation.py tests/test_specify_skill_has_recon_step.py tests/test_using_aia_mentions_recon.py tests/test_spec_template_has_recon_anchor.py` reports every new test failing for the right reason — `ImportError`/`AttributeError` on `aiadev.validate.validate_spec` for Phase-2 tests, and `AssertionError: expected substring 'Reconnaissance' not found` for Phase-3 tests. No green tests until Phase 2 lands.

### Phase 2 — Schema and validator

- Add `schemas/spec-recon.schema.json` with three keys (see Architecture decisions above): `cutover_spec_id: 10`, `recon_entry_pattern`, `opt_out_pattern`.
- Add `validate_spec(path) -> ValidationReport` to `src/aiadev/validate.py` that:
  1. parses the spec's YAML-ish header for `Spec ID` (regex `^\*\*Spec ID:\*\* (\d+)`); short-circuit-pass when id ≤ `cutover_spec_id`.
  2. extracts the body between `<!-- section: Reconnaissance -->` and the next `<!-- section:` anchor.
  3. accepts an opt-out line matching `opt_out_pattern`.
  4. otherwise: at least one bullet must match `recon_entry_pattern` and every backticked path it cites must exist (`(framework_root / path).exists()`).
- Extend `validate_paths` with extension-dispatch: `path.name == "spec.md"` → `validate_spec`; otherwise existing skill-frontmatter logic.
- `src/aiadev/commands/validate.py` requires no behavioural change — it already forwards to `validate_paths`.

Exit criterion: Phase 1 tests for schema/validator turn green; `pytest tests/test_validate.py` (existing) stays green (no regression to SKILL.md validation).

### Phase 3 — Templates and skills

- Update `templates/spec-template.md`: insert the `<!-- section: Reconnaissance -->` block immediately after the `Problem` block (per the issue's proposal) and before `Users and stakeholders`; include the example bullet matching `recon_entry_pattern` and the opt-out line shape so a copy-paste produces a passing draft.
- Update `skills/specify/SKILL.md`:
  - new Loop step (between current 2 and 3) — "**Reconnaissance.** For each surface in the demand not yet inspected this session, read its entry point and auth/session module, grep for the integration points the demand claims to use, record findings in the spec's `<!-- section: Reconnaissance -->` block as bullets matching the recon micro-format. If findings contradict the demand's premise, **pause and surface the mismatch to the user before drafting any user story** — cite the specific file and line that contradicts the premise."
  - new entry under "What not to do" — "Drafting user stories by analogy with another surface without recording a recon entry for the surface in question."
- Update `skills/using-ai-augmented-developer/SKILL.md`: add one line under "Pipeline skills" or as a separate one-line callout — "Before drafting user stories on a surface you have not yet inspected this session, perform a Reconnaissance pass — see [skills/specify/SKILL.md](../specify/SKILL.md)."

Exit criterion: Phase 1 tests for skill/orientation/template prose turn green; `python3 scripts/validate_skills.py` stays clean; no SKILL.md frontmatter regression.

### Phase 4 — Backfill this spec & changelog

- Backfill `specs/0011-specify-reconnaissance/spec.md` with its own Reconnaissance section (eat-our-own-dogfood; the spec was drafted before the template change shipped). Surfaces to record: `skills/specify`, `templates`, `schemas`, `src/aiadev/validate.py`, `skills/using-ai-augmented-developer`, `tests`.
- Add a `CHANGELOG.md` entry under `[Unreleased] / Added` referencing issue #26 and naming the cutover id (`spec.md` recon validation enforced for Spec ID > 10).

Exit criterion (copy-pasteable):

```bash
pytest -q
python3 scripts/validate_skills.py
npx --yes markdownlint-cli2 '**/*.md'
aiadev validate specs/0011-specify-reconnaissance/spec.md
```

All four commands exit 0; the `Reconnaissance` section in `0011-specify-reconnaissance/spec.md` validates against the new schema.

## Risks and mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Cutover-id off-by-one ships a validator that rejects the very spec that introduces it | Med | High | Phase 4 explicitly backfills 0011's recon section and the test fixtures pin the cutover at `0011 - 1 = 0010` so 0011 is the first required spec; a regression test asserts `cutover_spec_id == 10`. |
| Existing in-flight specs (0010-pipeline-preflight-checks) suddenly fail validation | Low | Med | Cutover puts 0010 below the gate; a fixture replicates the situation and asserts it passes. |
| Template change without skill change (or vice-versa) lands in main mid-PR | Low | High | Phase 1 tests assert presence of the recon section in *both* the template and the skill; PR cannot land green if only one is updated. |
| Markdownlint trips on the recon micro-format bullet | Low | Low | Phase 4 runs `markdownlint-cli2`; the micro-format uses standard bullet syntax. |
| Reviewer subagent rejects the recon section because "anchors must not be translated" rule is overlooked in non-English presets | Low | Low | cl-4 decision codified in template comment; no preset templates exist today, so no immediate breakage. |

## Complexity tracking

> Required when any Constitution Check row is `FAIL`. Empty table if no waivers.

| Article waived | Reason | Alternatives considered | Reviewer |
|---|---|---|---|
| | | | |

## Hand-off to `tasks`

The next skill is `tasks`. It consumes this plan and produces `tasks.md`.
Pre-conditions before hand-off:

- [x] Constitution Check is fully populated, no blank rows.
- [x] Complexity tracking is empty (no FAIL rows).
- [x] Project structure delta is accurate.
