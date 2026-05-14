# Code review context — 0014 BMAD-inspired evolutions

## What was built

Four framework evolutions distilled from a comparative analysis with the BMAD-METHOD project (https://github.com/bmad-code-org/BMAD-METHOD v6.6.0). Delivered as one PR per cl-7 decision; commits are ordered by risk crescente (Foundation → Stories 3+4 → Story 2 → Story 1) and each task is its own commit.

**Scope:**
1. **Story 1 — `task-context` skill** (P1): new opt-in skill that composes a per-task context file (`specs/<branch>/task-context/<TID>-<slug>.md`) before the implementer dispatch. Rich slice of spec/plan + files-to-modify excerpts (≤40 LOC) + TDD checklist + previous-task pointer + staleness detection.
2. **Story 2 — Customização 3-camadas** (P1): TOML resolver merging `customize.toml` (base, shipped) → `_aiadev/team.toml` (committed) → `_aiadev/user.toml` (gitignored). Arrays of tables matched by `code`/`id` with replace-or-append; parse error aborts with `file:line`. `aiadev install` emits the stubs idempotently.
3. **Story 3 — Zero-findings-halt** (P2): the 3 reviewer subagents document a `### Why no issues` block requirement on APPROVED-of-non-trivial-change; orchestrator (skills `implement` and `requesting-code-review`) re-dispatches with reinforced adversarial framing on violation; hard limit 2 re-dispatches/reviewer; `aiadev preflight requesting-code-review` validates.
4. **Story 4 — `help` state-aware** (P2): `recommend_next_command()` inspects `specs/<branch>/` state; help skill prepends "Próximo passo: …"; `--plain` flag and `AIADEV_HELP_PLAIN` env preserve legacy verbatim output (byte-for-byte).

## Spec / plan / tasks

- Spec: [`spec.md`](./spec.md) — Story sections, 4 user stories with G/W/T scenarios; Constitution articles I/II/III/IV/VII invoked, V/VI explicitly N/A.
- Plan: [`plan.md`](./plan.md) — 9 ADRs (one per cl-1..cl-9), Constitution Check fully PASS/N/A, 4 phases ordered by risk.
- Tasks: [`tasks.md`](./tasks.md) — 22 atomic tasks, all `**Status:** done`.

## Changed files (104 files, +7264/-14)

```
agents/                  3 reviewer prompts modified (zero-findings-halt rule)
schemas/                 terse-output.schema.json: new 🟢 verification variant
skills/                  help/, implement/, requesting-code-review/ modified;
                         task-context/ created
src/aiadev/              4 new modules (pipeline_state, review_log,
                         customization, task_context); preflight + install_engine
                         + commands/preflight modified
templates/               task-context-template.md created;
                         _aiadev/team.toml stub created
docs/                    customization.md created
presets/                 django-drf-react/preset.yaml: task_context: true (cl-8)
scripts/                 sync_assets.py manifest entry
tests/                   13 new test files (~2300 LOC), 22 fixture dirs
specs/0014-...           spec/plan/tasks/review-context (this file)
CHANGELOG.md, CREDITS.md attribution + release notes
```

## Key decisions made

- **One PR vs split (cl-7):** decision was ONE PR despite `git-workflow.md` recommending PRs < 500 LOC. Rationale: the 4 stories share origin (BMAD analysis), theme (framework evolution), and have inter-dependencies (Story 1 uses Story 2's flag-pattern; Story 4 reuses Story 3's review-log). Mitigation: commits are atomic per task, ordered by risk; PR body lists commits grouped by story.
- **TOML format for overrides (cl-4):** `tomllib` is stdlib in 3.11+, supports comments (essential for human-edited config), and arrays-of-tables merge predictably.
- **`_aiadev/` location (cl-3, ADR-5):** visible directory at project root, paridade com BMAD's `_bmad/`; underscore prefix signals "configuration synthesized" without colliding with `~/.aiadev/extensions/`.
- **Opt-in default off for `task-context` (cl-1):** preset.yaml `task_context: true` OR `--task-context` CLI flag; default off preserves current implement behavior byte-for-byte and respects Article III's "named user" requirement (cl-8: django-drf-react preset is the dogfood adopter).
- **Zero-findings-halt non-trivial threshold (cl-5):** `git diff --shortstat --ignore-blank-lines` > 10 LOC, excluding `.md/.json/.lock/.toml/docs/`; spec/plan creation always non-trivial. Implemented as `aiadev.review_log.is_non_trivial_change`.
- **`pipeline_state.py` as shared module (cl-6, ADR-3):** consumed by skill `help` + `aiadev preflight` today; VS Code Spec Explorer is the planned third caller (Article III named-user satisfied with 2 confirmed callers; the third is in-scope of the same spec).
- **Article V (Provider pattern) NOT invoked (cl-9, ADR-9):** customization.py is internal TOML merge utility, not a network/SDK boundary.
- **DRY refactor during T008:** code-reviewer flagged duplicated JSONL parsing between preflight and review_log; extracted `last_entry_from_log(log_path: Path)` as a public helper in `review_log.py`. Both call sites now share one parser.

## Areas needing reviewer attention

- **The biggest single piece of work is the `task-context` skill chain (T016–T021):** template + Python helper + skill markdown + integration into implement skill + dogfood preset + CLI flag. Cross-cutting; please verify the opt-in semantics actually work end-to-end (the inline implementer prompt MUST be byte-for-byte preserved when both flags are off — Story 1 sc3).
- **TOML resolver is the part most prone to silent merge bugs.** `merge_layers` in `src/aiadev/customization.py:61-106` deep-merges dicts and matches arrays-of-tables by `code`/`id`. Test parametrize covers 5 fixture scenarios + boundary + mutation-safety + perf budget — but custom edge cases (empty arrays of tables, nested arrays-of-tables, `id` vs `code` collision) might be worth a second look.
- **Zero-findings-halt is META.** The very review that comes back from this PR will be subject to the new rule. The `code-reviewer` agent file (`agents/code-reviewer.md`) carries the agent-side contract; the orchestrator-side gate lives in `skills/implement/SKILL.md` and `skills/requesting-code-review/SKILL.md`. If the reviewer returns APPROVED on this PR (which IS non-trivial — 7264 insertions), it MUST include the `### Why no issues` block.
- **`pipeline_state.recommend_next_command` makes assumptions about branch detection.** Reads spec.md `**Branch:**` headers; tests pass `branch=` kwarg explicitly. Real-world git-branch detection is the caller's responsibility (skill help passes the result of `git branch --show-current`).
- **Performance budget (cl-6):** ≤ 200 ms on 50-spec workspace; current measurement is ~0.02s. Comfortable margin but worth flagging if anything slows it down.

## Test coverage

- **New tests added:** 13 files, ~2300 LOC, ~120 test cases.
  - `test_pipeline_state.py` (14 tests, AC-1..AC-8 + perf budget)
  - `test_terse_output_schema.py` (15 tests, schema variants + backward compat)
  - `test_zero_findings_halt_agents.py` (14 parametrized assertions)
  - `test_review_log.py` (14 tests, detector + writer + reader edge cases)
  - `test_preflight_review.py` (6 CliRunner tests)
  - `test_review_redispatch_skills.py` (14 parametrized content assertions)
  - `test_help_skill_state_aware.py` (10 content tests)
  - `test_customization.py` (12 tests, 5 fixtures + edges + perf)
  - `test_install_aiadev_stubs.py` (9 tests via CliRunner + tmp_path)
  - `test_customization_docs.py` (7 content tests)
  - `test_task_context_template.py` (7 content tests)
  - `test_task_context.py` (11 tests, AC-1 + AC-4 staleness)
  - `test_implement_task_context_integration.py` (7 content tests)
  - `test_preset_task_context_dogfood.py` (7 tests)
  - `test_cli_task_context_flag.py` (5 CliRunner tests)
  - `test_attribution_and_changelog.py` (4 tests)
- **Suite result:** 720 passed, 1 skipped, 7 pre-existing `test_mcp_server.py` failures (env-level FastMCP `issubclass` TypeError — confirmed not a regression by stashing the branch and re-running before any change in this branch).
- **`scripts/validate_skills.py`:** all skills validate including the new `skills/task-context/SKILL.md`.
- **Manual smoke tests (passed):**
  - `aiadev install --preset lean --non-interactive --vars PROJECT_NAME=Demo` into `/tmp/demo` creates `_aiadev/team.toml` + `.gitignore` line; idempotent on re-run.
  - `aiadev preflight requesting-code-review --feature 0014-bmad-inspired-evolutions` exits 0 (no log yet).
  - `aiadev preflight implement --task-context --feature 0014-bmad-inspired-evolutions` emits the new announcement line and exits 0.
- **Two-stage review during implementation:** all 22 tasks went through implementer → spec reviewer → code-quality reviewer with APPROVED on both stages. The code-reviewer caught a real DRY violation in T008 (extracted `last_entry_from_log`) and a markdown rendering bug in T004 (nested backticks). Both fixed before commit.
