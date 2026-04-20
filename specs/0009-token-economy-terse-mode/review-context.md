# Code Review Context — Spec 0009: Token economy & terse-mode

## What was built

An opt-in **terse-mode** output contract for the three reviewer subagents
(`spec-document-reviewer`, `plan-document-reviewer`, `code-reviewer`), a
generated `/aia:help` pipeline quick-reference with drift enforcement,
and a **breaking** rename of the slash-command prefix `/aiadev:` → `/aia:`.
Phase 4 (live Sonnet 4.6 benchmark measuring the ≥ 30 % token reduction)
is explicitly deferred to a follow-up release — T013–T016 remain pending;
off-mode golden files are hand-crafted representatives today.

## Spec reference

- Spec: [specs/0009-token-economy-terse-mode/spec.md](./spec.md)
- Plan (v2): [specs/0009-token-economy-terse-mode/plan.md](./plan.md)
- Tasks (16 + planning + rename done, 4 deferred): [tasks.md](./tasks.md)
- Analysis: [analysis.md](./analysis.md)

## Changed files (18 commits on `feature/token-economy-terse-mode`)

45 files, +2,105 / −36. Highlights:

- **New framework source**: `rules/terse-mode.md`, `skills/help/SKILL.md`,
  `schemas/terse-output.schema.json`, `scripts/generate_pipeline_reference.py`,
  `docs/pipeline-reference.md`, `src/aiadev/config.py`.
- **Modified framework source**: 3 reviewer agents (`agents/*.md`),
  `CLAUDE.md`, `CREDITS.md`, `CHANGELOG.md`, 5 platform handlers
  (`src/aiadev/platforms/*.py` — rename), 13 markdown files for the
  `/aiadev:` → `/aia:` bulk substitution.
- **CI**: `.pre-commit-config.yaml` (new), `.github/workflows/pipeline-reference-drift.yml` (new).
- **Tests**: 14 new test modules (339 new test lines). Each task has a
  failing-test precondition documented in `tasks.md`.

## Key decisions

1. **Phase 4 deferred, not abandoned.** `T013` (provider), `T014` (benchmark
   inputs + runner), `T015` (push-to-main workflow), `T016` (≥ 30 % delta)
   remain pending. The committed `test_pipeline_reference_drift.py` has a
   `@pytest.mark.skip` token-budget assertion with a TODO pointing at T013;
   the off-mode golden fixtures in `tests/fixtures/off_mode/` are
   hand-crafted representatives the benchmark runner will overwrite.
2. **Echo lives in the rule file, not `cli.py`.** Gap C in `analysis.md`
   surfaced that `cli.py` has no pipeline subcommands — the echo would be
   YAGNI. The authoritative instruction is in `rules/terse-mode.md`,
   loaded by every Claude Code session via `.claude/rules/`.
3. **Three rule copies via existing tooling.** `rules/terse-mode.md` is
   the single tracked source; `scripts/sync_assets.py` already copies
   `rules/` → `_assets/rules/`; `.claude/rules/` is a gitignored local
   mirror populated by hand for the framework's own session. Test
   `test_terse_mode_rule.py` asserts the copy plan + optional mirrors.
4. **Breaking rename (`T022`).** `/aiadev:` → `/aia:` across 5 platform
   handlers + 67 prose occurrences in 13 files. Consumers must re-run
   `aiadev sync`. Flagged with a `feat!` commit and a CHANGELOG entry
   under **Changed → BREAKING**.
5. **No new LLM provider yet.** Article V check in `plan.md` describes
   the provider, but it lands with T013 in Phase 4. No `anthropic` import
   in the current diff.

## Areas needing careful attention

- **Breaking change surface.** Please verify no other slash-prefix
  reference slipped through: `grep -rn "/aiadev:" .` should return only
  HTML markers like `<!-- aiadev:auto-stack -->` (internal, different
  thing, left intentionally).
- **Platform-handler symmetry.** Five handlers changed one string each
  (`"aiadev"` → `"aia"`). Cursor/Codex/OpenCode use `.md`, Gemini uses
  `.toml`, Claude Code uses `.md`. Confirm no other hardcoded `"aiadev"`
  path segment remains.
- **Terse schema edge cases.** `schemas/terse-output.schema.json` has
  `message` regex `^[^\r\n]+$` + `maxLength: 140`. Intentional:
  `\t`-containing messages pass; empty messages fail via `minLength: 1`.
- **Config precedence.** `resolve_terse_mode()` returns `(False, "default")`
  when settings has `aiadev.terseMode: false` (by design — the source is
  honestly "default" because no layer opted in). Covered by a dedicated
  test (`test_settings_off_env_unset`).
- **Pipeline-reference drift test** trims CLAUDE.md table comparison with
  `CLAUDE_ONLY_NON_PIPELINE = {test-driven-development, systematic-debugging,
  frontend-design, constitution}` and `REFERENCE_ONLY = {help}`. Verify
  these exclusions reflect the intent (pipeline table vs. cookbook table).

## Test coverage

- Full suite: **505 passed, 1 skipped** (the deferred token-budget
  assertion). `validate_skills.py` clean.
- New tests: 14 modules covering schema validation, config precedence,
  agent terse blocks, golden-file guard, generator determinism, drift
  check, pre-commit + CI, CLAUDE.md pointer, terse-mode rule copies,
  `aiadev sync` artifact discovery, existing-validator regression under
  both `AIADEV_TERSE` modes, CHANGELOG entry.
- Manual verification: `python scripts/generate_pipeline_reference.py`
  produces the committed `docs/pipeline-reference.md` byte-for-byte
  (drift test passes); help surface is 16 lines (budget 24);
  `validate_skills.py` succeeds under `AIADEV_TERSE=0` and `AIADEV_TERSE=1`.

## What this PR is **not**

- Not a benchmark PR. No ≥ 30 % token-reduction measurement yet — that
  lands with Phase 4.
- Not a consumer-side migration. `aiadev sync` on existing consumer
  projects will reshape their `.claude/commands/aia/` tree on next run;
  coordinating that migration is outside this PR.
- Not a Django/React change. Despite `code-reviewer.md` mentioning
  "Django 5.2 + React 18", this repo is the framework itself — a
  Python CLI + Markdown package. Please frame review feedback
  accordingly.
