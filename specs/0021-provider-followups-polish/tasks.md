# Tasks: Fast-follows dos providers + token-economy (polish)

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

### T001 — `plan`: seção opcional de blast-radius + degradação

- **Status:** done
- **Depends on:** —
- **Files:**
  - modify: `skills/plan/SKILL.md`
  - test: `tests/test_provider_followups.py`
- **Spec scenarios:** Story 1 scenario 1, Story 1 scenario 3
- **Acceptance:**
  - [ ] Failing test written and observed failing: `test_plan_has_optional_blast_radius`.
  - [ ] A skill descreve uma seção opcional "Superfícies afetadas / blast-radius" via a query `impact`, citando `arquivo:símbolo` + confiança, com cláusula de degradação graciosa (sem provider, saída idêntica).
  - [ ] No other existing test regresses.
  - [ ] Commit message: `feat(followups): T001 blast-radius opcional no plan`.
- **Notes:** Reusa vocabulário do passo do `analyze` (0017).

### T002 — `requesting-code-review`: subsistemas impactados + degradação

- **Status:** done
- **Depends on:** —
- **Files:**
  - modify: `skills/requesting-code-review/SKILL.md`
  - test: `tests/test_provider_followups.py`
- **Spec scenarios:** Story 1 scenario 2, Story 1 scenario 3
- **Acceptance:**
  - [ ] Failing test written and observed failing: `test_review_has_optional_impacted_subsystems`.
  - [ ] O Review Context Document ganha uma seção opcional de subsistemas impactados via `impact`, com a mesma cláusula de degradação graciosa.
  - [ ] No other existing test regresses.
  - [ ] Commit message: `feat(followups): T002 subsistemas impactados no review`.
- **Notes:** Simétrico ao T001.

### T003 — `learn`: proposta pode apontar categoria de checklist (fallback rules/)

- **Status:** done
- **Depends on:** —
- **Files:**
  - modify: `src/aiadev/learn.py`
  - test: `tests/test_provider_followups.py`
- **Spec scenarios:** Story 2 scenario 1, Story 2 scenario 2, Story 2 scenario 3
- **Acceptance:**
  - [ ] Failing test written and observed failing: `test_learn_proposal_can_target_checklist_category`.
  - [ ] `propose_guidance` mapeia reviewer→categoria (ex.: `code-reviewer`→`security`); sem mapeamento, mantém o alvo em `rules/` (sem regressão). O alvo de checklist aparece no artefato de propostas (`specs/_learnings.md`) via `--write`.
  - [ ] No other existing test regresses.
  - [ ] Commit message: `feat(followups): T003 learn propõe categoria de checklist`.
- **Notes:** Não aplica nada; o alvo continua indo para `specs/_learnings.md` via `--write`.

### T004 — Bloco comentado de exemplo LSP no `mcps.yaml`

- **Status:** done
- **Depends on:** —
- **Files:**
  - modify: `presets/knowledge-graph/mcps.yaml`
  - test: `tests/test_provider_followups.py`
- **Spec scenarios:** Story 3 scenario 1, Story 3 scenario 3
- **Acceptance:**
  - [ ] Failing test written and observed failing: `test_mcps_has_commented_lsp_example`.
  - [ ] Há um bloco **comentado** de exemplo de server LSP; o parse do YAML segue válido contra o schema (server ativo inalterado).
  - [ ] No other existing test regresses.
  - [ ] Commit message: `docs(followups): T004 exemplo LSP comentado no mcps.yaml`.
- **Notes:** Comentário YAML puro; `test_knowledge_graph_preset` deve continuar passando.

### T005 — Exemplo comentado de hook `PreToolUse` no doc de token-economy

- **Status:** pending
- **Depends on:** —
- **Files:**
  - modify: `docs/token-economy.md`
  - test: `tests/test_provider_followups.py`
- **Spec scenarios:** Story 3 scenario 2, Story 3 scenario 3
- **Acceptance:**
  - [ ] Failing test written and observed failing: `test_token_economy_doc_has_hook_example`.
  - [ ] O doc traz um exemplo (bloco de código) de hook `PreToolUse`, preservando o Non-goal (framework não implementa o hook).
  - [ ] No other existing test regresses.
  - [ ] Commit message: `docs(followups): T005 exemplo de hook no doc de token-economy`.
- **Notes:** Descritivo/exemplo; não altera comportamento do framework.

## Parallelization hints

- Parallel group A: todas as 5 tasks tocam arquivos disjuntos (plan skill, review skill, learn.py, mcps.yaml, doc) — podem ser feitas em qualquer ordem.
- Serial: nenhuma dependência entre elas.

## Post-task checklist

After every task:

- [ ] Commit message references the task id.
- [ ] Status in this file updated.

After all tasks:

- [ ] Full test suite passes (`python3 -m pytest && python3 scripts/validate_skills.py`).
- [ ] `analyze` skill runs and reports no drift vs spec / plan.
- [ ] Hand off to `requesting-code-review` to open the PR.
