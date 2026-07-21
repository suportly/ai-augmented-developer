# Tasks: Categoria de checklist "token-economy" + integração opcional

> Produced by the `tasks` skill from an approved `plan.md`. Consumed by `implement`.

**Branch:** `claude/graphify-aiadev-analysis-oiggl4`
**Plan:** [plan.md](./plan.md)
**Generated:** 2026-07-20
**Language:** pt-BR <!-- mirrors spec.md; write task descriptions in this language. -->

---

## How to read this file

- Tasks are ordered. `implement` runs them top-to-bottom.
- One task = one commit. The commit message starts with the task id.
- Each task links back to the spec acceptance scenarios it exercises.
- `Status` is one of: `pending`, `in_progress`, `blocked`, `done`. Owned by the `implement` skill — it flips `pending` → `done` inside each task's commit. Do not edit by hand; manual edits are overwritten on the next `implement` run.

## Task list

### T001 — Itens default `Token economy` no template (referencia terse-mode)

- **Status:** done
- **Depends on:** —
- **Files:**
  - modify: `templates/checklist-template.md`
  - test: `tests/test_token_economy_checklist.py`
- **Spec scenarios:** Story 1 scenario 2, Story 1 scenario 3
- **Acceptance:**
  - [ ] Failing test written and observed failing: `test_template_has_token_economy_items`.
  - [ ] O template tem uma seção `Token economy (default items)` com itens (saída ruidosa, logs não-truncados, oportunidades de compressão) e um item que **referencia** `terse-mode`.
  - [ ] No other existing test regresses.
  - [ ] Commit message: `feat(token-economy): T001 itens no template do checklist`.
- **Notes:** Espelha o formato das seções `Security/Performance (default items)`.

### T002 — Registrar a categoria em `skills/checklist/SKILL.md`

- **Status:** done
- **Depends on:** —
- **Files:**
  - modify: `skills/checklist/SKILL.md`
  - test: `tests/test_token_economy_checklist.py`
- **Spec scenarios:** Story 1 scenario 1
- **Acceptance:**
  - [ ] Failing test written and observed failing: `test_checklist_skill_registers_token_economy`.
  - [ ] A `description` e a lista de categorias em `inputs` incluem `token-economy` (categoria conhecida, não "desconhecida").
  - [ ] No other existing test regresses.
  - [ ] Commit message: `feat(token-economy): T002 registra categoria no checklist`.
- **Notes:** Frontmatter da skill deve continuar válido (`validate_skills.py`).

### T003 — `docs/token-economy.md` (integração externa + Non-goal)

- **Status:** pending
- **Depends on:** —
- **Files:**
  - create: `docs/token-economy.md`
  - modify: `templates/checklist-template.md`
  - test: `tests/test_token_economy_checklist.py`
- **Spec scenarios:** Story 2 scenario 1, Story 2 scenario 2
- **Acceptance:**
  - [ ] Failing test written and observed failing: `test_token_economy_doc_covers_external_and_nongoal`.
  - [ ] O doc cita `rtk`/`headroom` como compressores externos e o mecanismo (hook `PreToolUse`/MCP), com Non-goal explícito (não implementar compressor — Artigo III); a seção da categoria no template linka o doc.
  - [ ] No other existing test regresses.
  - [ ] Commit message: `docs(token-economy): T003 doc de integração opcional`.
- **Notes:** Descritivo na v1 (cl-4); vive em `docs/` (cl-5).

### T004 — Atribuição a rtk e headroom (Artigo VII)

- **Status:** pending
- **Depends on:** —
- **Files:**
  - modify: `CREDITS.md`
  - test: `tests/test_token_economy_checklist.py`
- **Spec scenarios:** Story 2 scenario 3
- **Acceptance:**
  - [ ] Failing test written and observed failing: `test_credits_rtk_and_headroom`.
  - [ ] `CREDITS.md` credita `rtk-ai/rtk` e `headroomlabs-ai/headroom` (links + ideia da economia de tokens).
  - [ ] No other existing test regresses.
  - [ ] Commit message: `docs(token-economy): T004 atribuição a rtk e headroom`.
- **Notes:** Artigo VII não é waivable.

## Parallelization hints

- Parallel group A: T001, T002, T004 tocam arquivos disjuntos (template, skill, credits). T003 modifica o template (link) — serial após T001 para evitar conflito no mesmo arquivo.
- Serial: T003 após T001 (mesmo `checklist-template.md`).

## Post-task checklist

After every task:

- [ ] Commit message references the task id.
- [ ] Status in this file updated.

After all tasks:

- [ ] Full test suite passes (`python3 -m pytest && python3 scripts/validate_skills.py`).
- [ ] `analyze` skill runs and reports no drift vs spec / plan.
- [ ] Hand off to `requesting-code-review` to open the PR.
