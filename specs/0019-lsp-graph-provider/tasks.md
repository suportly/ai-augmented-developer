# Tasks: LSP como segundo provider do contrato de knowledge-graph

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

### T001 — Fake LSP conforme ao mesmo schema do 0017

- **Status:** done
- **Depends on:** —
- **Files:**
  - create: `tests/fixtures/lsp_provider_fake/__init__.py`
  - create: `tests/test_lsp_provider_conformance.py`
- **Spec scenarios:** Story 1 scenario 1
- **Acceptance:**
  - [ ] Failing test written and observed failing: `test_lsp_fake_conforms_to_0017_schema`.
  - [ ] O fake retorna `impact`/`drift`/`provenance` que validam contra o **mesmo** `graph-provider.schema.json` do 0017, sem alterá-lo.
  - [ ] No other existing test regresses.
  - [ ] Commit message: `feat(lsp): T001 fake LSP conforme ao contrato`.
- **Notes:** Espelha `tests/fixtures/graph_provider_fake/`; operações LSP (references/call-hierarchy/symbols/definition) por trás das respostas.

### T002 — Rótulos de confiança do LSP (resolvido → explicit)

- **Status:** pending
- **Depends on:** T001
- **Files:**
  - modify: `tests/fixtures/lsp_provider_fake/__init__.py`
  - modify: `tests/test_lsp_provider_conformance.py`
- **Spec scenarios:** Story 1 scenario 2
- **Acceptance:**
  - [ ] Failing test written and observed failing: `test_lsp_facts_carry_confidence_from_resolution`.
  - [ ] Cada fato cita `arquivo:símbolo` e um rótulo do vocabulário aiadev: referência/definição resolvida → `explicit`; match textual → `inferred`; múltiplos candidatos → `ambiguous`.
  - [ ] No other existing test regresses.
  - [ ] Commit message: `feat(lsp): T002 confiança a partir da resolução LSP`.
- **Notes:** Reusa o vocabulário de `presets/knowledge-graph/rules/graph-facts.md`.

### T003 — Doc de mapeamento LSP→contrato (queries)

- **Status:** pending
- **Depends on:** —
- **Files:**
  - create: `specs/0019-lsp-graph-provider/contracts/lsp-provider-mapping.md`
  - create: `tests/test_lsp_mapping_doc.py`
- **Spec scenarios:** Story 2 scenario 1
- **Acceptance:**
  - [ ] Failing test written and observed failing: `test_mapping_doc_covers_the_three_queries`.
  - [ ] O doc mapeia `impact` (`textDocument/references` + `callHierarchy`), `drift` (symbols) e `provenance` (`definition`) para as queries do contrato, com Non-goal explícito (sem adaptador executável).
  - [ ] No other existing test regresses.
  - [ ] Commit message: `docs(lsp): T003 doc de mapeamento LSP->contrato`.
- **Notes:** Vive em `specs/0019-*/contracts/` (cl-2).

### T004 — Doc: tabela de mapeamento de confiança

- **Status:** pending
- **Depends on:** T003
- **Files:**
  - modify: `specs/0019-lsp-graph-provider/contracts/lsp-provider-mapping.md`
  - modify: `tests/test_lsp_mapping_doc.py`
- **Spec scenarios:** Story 2 scenario 2
- **Acceptance:**
  - [ ] Failing test written and observed failing: `test_mapping_doc_defines_confidence_mapping`.
  - [ ] O doc define: resolvido → `explicit`; textual/heurístico → `inferred`; múltiplos candidatos → `ambiguous`.
  - [ ] No other existing test regresses.
  - [ ] Commit message: `docs(lsp): T004 tabela de confiança no mapeamento`.
- **Notes:** Mesmo arquivo de T003 — serial.

### T005 — Preset README menciona LSP como provider alternativo

- **Status:** pending
- **Depends on:** T003
- **Files:**
  - modify: `presets/knowledge-graph/README.md`
  - create: `tests/test_lsp_preset_readme.py`
- **Spec scenarios:** Story 2 scenario 3
- **Acceptance:**
  - [ ] Failing test written and observed failing: `test_preset_readme_mentions_lsp_provider`.
  - [ ] O README cita LSP como provider alternativo (graphify segue de referência) e linka o doc de mapeamento.
  - [ ] No other existing test regresses.
  - [ ] Commit message: `docs(lsp): T005 README do preset menciona LSP`.
- **Notes:** Link relativo ao doc de T003.

### T006 — Atribuição + reescrita do waiver do Artigo III do 0017

- **Status:** pending
- **Depends on:** T001
- **Files:**
  - modify: `CREDITS.md`
  - modify: `specs/0017-knowledge-graph-context-provider/plan.md`
  - create: `tests/test_lsp_credits_and_waiver.py`
- **Spec scenarios:** Story 1 scenario 3
- **Acceptance:**
  - [ ] Failing test written and observed failing: `test_credits_lsps_and_0017_waiver_updated`.
  - [ ] `CREDITS.md` credita `Piebald-AI/claude-code-lsps` (link + ideia). O waiver do Artigo III no `plan.md` do 0017 é reescrito para refletir 2 implementações de referência (graphify + LSP).
  - [ ] No other existing test regresses.
  - [ ] Commit message: `docs(lsp): T006 atribuição + atualiza waiver do 0017`.
- **Notes:** Artigo VII não é waivable; a edição do 0017 é pontual e referencia o 0019.

## Parallelization hints

- Parallel group A: T001, T003, T006 tocam arquivos disjuntos (fixture, doc novo, credits/plan) — mas T005/T004 dependem de T003.
- Serial: T001→T002 (mesma fixture); T003→T004 (mesmo doc); T005 após T003.

## Post-task checklist

After every task:

- [ ] Commit message references the task id.
- [ ] Status in this file updated.

After all tasks:

- [ ] Full test suite passes (`python3 -m pytest && python3 scripts/validate_skills.py`).
- [ ] `analyze` skill runs and reports no drift vs spec / plan.
- [ ] Hand off to `requesting-code-review` to open the PR.
