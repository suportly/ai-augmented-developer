# Tasks: Specify reconnaissance step

> Produced by the `tasks` skill from an approved `plan.md`. Consumed by `implement`.

**Branch:** `feature/specify-reconnaissance`
**Plan:** [plan.md](./plan.md)
**Generated:** 2026-04-27
**Language:** en

---

## How to read this file

- Tasks are ordered. `implement` runs them top-to-bottom.
- One task = one commit. The commit message starts with the task id.
- Each task links back to the spec acceptance scenarios it exercises.
- `Status` is one of: `pending`, `in_progress`, `blocked`, `done`. Only `implement` mutates it.
- Each task pairs the failing test with the minimum production change that turns it green (TDD red→green→commit).

## Task list

### T001 — Schema file + cutover-pinning regression test

- **Status:** pending
- **Depends on:** —
- **Files:**
  - create: `schemas/spec-recon.schema.json`
  - create: `tests/test_spec_recon_validation.py`
- **Spec scenarios:** Story 2 (foundation); Risks-table guard
- **Acceptance:**
  - [ ] Add `test_cutover_spec_id_pinned_at_ten` first; observe `FileNotFoundError` on `schemas/spec-recon.schema.json` (red).
  - [ ] Create `schemas/spec-recon.schema.json` with three keys: `cutover_spec_id: 10`, `recon_entry_pattern` (regex matching `^- \*\*[^*]+\*\* — entry: \`[^\`]+\``), `opt_out_pattern` (regex matching `^Reconnaissance: not required \(single-surface change: [^)]+\)\s*$`).
  - [ ] Test passes; no other existing test regresses (`pytest -q`).
  - [ ] Commit message: `test(validate): T001 pin recon schema with cutover_spec_id=10`.
- **Notes:** schema is a config file — no `$schema` draft validation runs. Inline-comment the choice in the test.

### T002 — Fixtures + grandfathered + empty-recon tests + `validate_spec` skeleton

- **Status:** pending
- **Depends on:** T001
- **Files:**
  - create: `tests/fixtures/spec-recon/legacy-spec-0009.md`
  - create: `tests/fixtures/spec-recon/empty-recon.md`
  - modify: `tests/test_spec_recon_validation.py`
  - modify: `src/aiadev/validate.py`
- **Spec scenarios:** Story 2 scenario 1 (empty section → fail); Breaking-changes cutover guarantee
- **Acceptance:**
  - [ ] Add `test_grandfathered_spec_passes_without_recon` and `test_empty_recon_section_exits_nonzero`; observe `AttributeError: module 'aiadev.validate' has no attribute 'validate_spec'` (red).
  - [ ] Add `validate_spec(path) -> ValidationReport` in `src/aiadev/validate.py`. Parse `**Spec ID:** (\d+)`; short-circuit-pass when id ≤ `cutover_spec_id`. Extract body between `<!-- section: Reconnaissance -->` and the next `<!-- section:` anchor; flag empty body with `Reconnaissance section required; add at least one surface entry or opt-out line`.
  - [ ] Both tests pass; existing `test_validate.py` stays green.
  - [ ] Commit: `feat(validate): T002 add validate_spec skeleton + cutover guard`.

### T003 — Opt-out line passes validation

- **Status:** pending
- **Depends on:** T002
- **Files:**
  - create: `tests/fixtures/spec-recon/optout-recon.md`
  - modify: `tests/test_spec_recon_validation.py`
  - modify: `src/aiadev/validate.py`
- **Spec scenarios:** Story 2 scenario 2
- **Acceptance:**
  - [ ] Add `test_optout_line_passes_validation`; observe failure (validator currently rejects any non-empty body without bullet entries) — red.
  - [ ] Wire `opt_out_pattern` check: if the recon body matches the pattern, return `ok`; otherwise fall through to bullet validation.
  - [ ] Test passes.
  - [ ] Commit: `feat(validate): T003 accept single-surface opt-out line`.

### T004 — Prose-only recon (no path) fails validation

- **Status:** pending
- **Depends on:** T003
- **Files:**
  - create: `tests/fixtures/spec-recon/prose-only-recon.md`
  - modify: `tests/test_spec_recon_validation.py`
  - modify: `src/aiadev/validate.py`
- **Spec scenarios:** Story 2 scenario 3
- **Acceptance:**
  - [ ] Add `test_prose_only_recon_fails_validation`; observe red (validator passes any non-empty body).
  - [ ] Apply `recon_entry_pattern` against each non-blank, non-comment body line; require ≥ 1 match. Error message: `Reconnaissance entries must cite at least one file path per surface`.
  - [ ] Test passes.
  - [ ] Commit: `feat(validate): T004 require backticked path per recon entry`.

### T005 — Recon entry citing nonexistent path fails

- **Status:** pending
- **Depends on:** T004
- **Files:**
  - create: `tests/fixtures/spec-recon/valid-recon.md`
  - create: `tests/fixtures/spec-recon/nonexistent-path-recon.md`
  - modify: `tests/test_spec_recon_validation.py`
  - modify: `src/aiadev/validate.py`
- **Spec scenarios:** cl-2 resolution (validator is structural, paths must exist)
- **Acceptance:**
  - [ ] Add `test_recon_path_does_not_exist_fails_validation` (and a paired green test using `valid-recon.md` whose paths exist on disk); observe red.
  - [ ] For every backticked token captured by `recon_entry_pattern`, assert `(framework_root / token).exists()`; emit `Reconnaissance path '<p>' does not exist` on miss.
  - [ ] Both tests pass.
  - [ ] Commit: `feat(validate): T005 require recon paths to exist on disk`.

### T006 — Wire `validate_spec` into `validate_paths` extension dispatch

- **Status:** pending
- **Depends on:** T005
- **Files:**
  - modify: `src/aiadev/validate.py`
  - modify: `tests/test_spec_recon_validation.py`
- **Spec scenarios:** Story 3 CLI parity (Story 2 reaches `aiadev validate <spec.md>`)
- **Acceptance:**
  - [ ] Add `test_aiadev_validate_command_routes_spec_md_to_validate_spec` invoking `validate_paths` with a fixture spec path; observe red (currently misroutes to skill-frontmatter validator).
  - [ ] Add an extension-dispatch branch at the top of `validate_paths`: when `path.name == "spec.md"`, route to `validate_spec`.
  - [ ] Test passes; existing `test_all_repository_skills_pass` stays green.
  - [ ] Commit: `feat(validate): T006 dispatch spec.md paths to validate_spec`.

### T007 — Template gains `<!-- section: Reconnaissance -->` anchor

- **Status:** pending
- **Depends on:** —
- **Files:**
  - create: `tests/test_spec_template_has_recon_anchor.py`
  - modify: `templates/spec-template.md`
- **Spec scenarios:** Success criterion 5 (anchor regression guard)
- **Acceptance:**
  - [ ] Add `test_spec_template_has_reconnaissance_anchor` asserting the literal `<!-- section: Reconnaissance -->` appears exactly once in `templates/spec-template.md`; observe red.
  - [ ] Insert the new section in the template after `<!-- section: Problem -->` and before `<!-- section: Users and stakeholders -->`. Include the section heading `## Reconnaissance` and the comment guidance from the issue's proposal.
  - [ ] Test passes.
  - [ ] Commit: `feat(templates): T007 add Reconnaissance section anchor to spec template`.

### T008 — Template documents the recon micro-format

- **Status:** pending
- **Depends on:** T007
- **Files:**
  - modify: `tests/test_spec_template_has_recon_anchor.py`
  - modify: `templates/spec-template.md`
- **Spec scenarios:** Story 2 (micro-format discoverability)
- **Acceptance:**
  - [ ] Add `test_spec_template_recon_block_documents_micro_format` asserting the template body between the recon anchor and the next anchor contains a bullet matching `recon_entry_pattern` from `schemas/spec-recon.schema.json`; observe red.
  - [ ] Add an example bullet (e.g. `` - **<surface-name>** — entry: `<path>` · auth: `<path|none>` · integration: `<path-or-grep-term>` ``) and the opt-out line shape inside the comment block of the new section.
  - [ ] Test passes.
  - [ ] Commit: `feat(templates): T008 document recon micro-format and opt-out line`.

### T009 — `specify` skill mentions Reconnaissance + Loop step

- **Status:** pending
- **Depends on:** —
- **Files:**
  - create: `tests/test_specify_skill_has_recon_step.py`
  - modify: `skills/specify/SKILL.md`
- **Spec scenarios:** Story 1 scenario 1; Success criterion 6
- **Acceptance:**
  - [ ] Add `test_specify_skill_mentions_reconnaissance` asserting `skills/specify/SKILL.md` contains the literal `Reconnaissance` ≥ 1×; observe red.
  - [ ] Insert a new Loop step (between current step 2 and step 3) — `**Reconnaissance.** For each surface in the demand not yet inspected this session, read its entry point and auth/session module, grep for the integration points, and record findings in the spec's `<!-- section: Reconnaissance -->` block as bullets matching the recon micro-format. If findings contradict the demand's premise, pause and surface the mismatch to the user before drafting any user story — cite the specific file and line that contradicts the premise.`
  - [ ] Renumber subsequent Loop steps.
  - [ ] Test passes.
  - [ ] Commit: `feat(specify): T009 add Reconnaissance Loop step`.

### T010 — `specify` skill forbids analogy-driven drafts

- **Status:** pending
- **Depends on:** T009
- **Files:**
  - modify: `tests/test_specify_skill_has_recon_step.py`
  - modify: `skills/specify/SKILL.md`
- **Spec scenarios:** Story 1 scenario 1 (skill-prose half)
- **Acceptance:**
  - [ ] Add `test_specify_skill_forbids_analogy_drafts` asserting the file's "What not to do" section mentions analogy / sibling surface drafting; observe red.
  - [ ] Add a bullet under "What not to do": `Drafting user stories by analogy with another surface without recording a recon entry for the surface in question.`
  - [ ] Test passes.
  - [ ] Commit: `feat(specify): T010 forbid analogy-driven story drafting`.

### T011 — `specify` skill pauses on premise mismatch

- **Status:** pending
- **Depends on:** T009
- **Files:**
  - modify: `tests/test_specify_skill_has_recon_step.py`
- **Spec scenarios:** Story 1 scenario 2 (pause-and-surface behaviour)
- **Acceptance:**
  - [ ] Add `test_specify_skill_pauses_on_premise_mismatch` asserting `skills/specify/SKILL.md` contains both substrings `pause` and `mismatch` within the new Loop step; observe red if the T009 prose was abbreviated and missed the wording.
  - [ ] If red, tighten the T009 wording to keep both substrings; otherwise no production change needed and the test simply pins the wording.
  - [ ] Test passes.
  - [ ] Commit: `test(specify): T011 pin pause-on-mismatch wording`.
- **Notes:** this task is intentionally test-only when T009's prose already includes both substrings — its purpose is to lock the wording against future drift.

### T012 — Orientation skill mentions Reconnaissance

- **Status:** pending
- **Depends on:** —
- **Files:**
  - create: `tests/test_using_aia_mentions_recon.py`
  - modify: `skills/using-ai-augmented-developer/SKILL.md`
- **Spec scenarios:** Story 3 scenarios 1 & 2
- **Acceptance:**
  - [ ] Add `test_orientation_mentions_reconnaissance` asserting `skills/using-ai-augmented-developer/SKILL.md` contains `Reconnaissance` and a Markdown link whose target ends with `skills/specify/SKILL.md`; observe red.
  - [ ] Add a one-line callout under "Pipeline skills": `Before drafting user stories on a surface you have not yet inspected this session, perform a Reconnaissance pass — see [skills/specify/SKILL.md](../specify/SKILL.md).`
  - [ ] Test passes.
  - [ ] Commit: `feat(skills): T012 orient agents to Reconnaissance step`.

### T013 — Dogfood: backfill recon section in this spec

- **Status:** pending
- **Depends on:** T006, T007, T008
- **Files:**
  - modify: `specs/0011-specify-reconnaissance/spec.md`
- **Spec scenarios:** Success criterion 1 (recon section drafted before user stories — retroactively for spec 0011 itself)
- **Acceptance:**
  - [ ] Add a `<!-- section: Reconnaissance -->` block between `Problem` and `Users and stakeholders` in this spec, with one bullet per surface (`skills/specify`, `templates`, `schemas`, `src/aiadev/validate.py`, `skills/using-ai-augmented-developer`, `tests`), each bullet matching `recon_entry_pattern` and citing real on-disk paths.
  - [ ] Run `aiadev validate specs/0011-specify-reconnaissance/spec.md`; expect exit 0.
  - [ ] No other test regresses.
  - [ ] Commit: `docs(specs): T013 backfill recon section in spec 0011`.

### T014 — CHANGELOG entry under [Unreleased] / Added

- **Status:** pending
- **Depends on:** T001..T013
- **Files:**
  - modify: `CHANGELOG.md`
- **Spec scenarios:** Definition-of-done item from issue #26
- **Acceptance:**
  - [ ] Add an `[Unreleased] / Added` entry: `- **Specify reconnaissance step (#26).** Multi-surface specs must list inspected surfaces with file-path evidence. Validator enforces for Spec ID > 10. ([0011](specs/0011-specify-reconnaissance/spec.md))`
  - [ ] Run `pytest -q`, `python3 scripts/validate_skills.py`, `npx --yes markdownlint-cli2 '**/*.md'`, and `aiadev validate specs/0011-specify-reconnaissance/spec.md` — all four exit 0.
  - [ ] Commit: `docs(changelog): T014 record specify Reconnaissance step (#26)`.

## Parallelization hints

- Parallel group A (template + skill prose, disjoint files): T007, T009, T012 (each can land independently before the validator stack settles, but their tests depend on the schema file from T001).
- Serial: T001 → T002 → T003 → T004 → T005 → T006 (validator chain is strictly serial — each task tightens one rule); T013 and T014 are tail-serial (depend on the full stack).

## Post-task checklist

After every task:

- [ ] Commit message references the task id.
- [ ] Status in this file updated.

After all tasks:

- [ ] Full test suite passes (`pytest -q`).
- [ ] `analyze` skill runs and reports no drift vs spec / plan.
- [ ] Hand off to `requesting-code-review` to open the PR.
