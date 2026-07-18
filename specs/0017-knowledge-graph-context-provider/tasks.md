# Tasks: Provedor de contexto de knowledge-graph para o pipeline

> Produced by the `tasks` skill from an approved `plan.md`. Consumed by `implement`.

**Branch:** `claude/graphify-aiadev-analysis-oiggl4`
**Plan:** [plan.md](./plan.md)
**Generated:** 2026-07-18
**Language:** pt-BR <!-- mirrors spec.md; write task descriptions in this language. -->

---

## How to read this file

- Tasks are ordered. `implement` runs them top-to-bottom.
- One task = one commit. The commit message starts with the task id.
- Each task links back to the spec acceptance scenarios it exercises.
- `Status` is one of: `pending`, `in_progress`, `blocked`, `done`. Owned by the `implement` skill — it flips `pending` → `done` inside each task's commit. Do not edit by hand; manual edits are overwritten on the next `implement` run.

**Escopo v1:** estas tasks realizam as Fases 1–3 do plano e cobrem a **Story 1** (drift ancorado no `analyze`) e a **Story 3** (metadado de confiança). A **Story 2** (blast-radius em `plan`/review, P2) é fast-follow pós-v1 e **não** é decomposta aqui, por decisão de escopo do plano (cl-3).

## Task list

### T001 — Contrato de queries do provider (schema)

- **Status:** pending
- **Depends on:** —
- **Files:**
  - create: `specs/0017-knowledge-graph-context-provider/contracts/graph-provider.schema.json`
  - test: `tests/test_graph_provider_contract.py`
- **Spec scenarios:** Story 1 scenario 1, Story 1 scenario 2
- **Acceptance:**
  - [ ] Failing test written and observed failing (schema ausente): `test_schema_declares_queries`.
  - [ ] Schema declara as 3 queries `impact`, `drift`, `provenance` com request/response shapes e um campo `confidence` (enum).
  - [ ] No other existing test regresses.
  - [ ] Commit message: `feat(graph): T001 contrato de queries do provider`.
- **Notes:** O schema é o contrato do Artigo V; nenhum SDK de provider é referenciado aqui.

### T002 — Fake do provider conforme ao contrato

- **Status:** pending
- **Depends on:** T001
- **Files:**
  - create: `tests/fixtures/graph_provider_fake/__init__.py`
  - test: `tests/test_graph_provider_contract.py`
- **Spec scenarios:** Story 1 scenario 1, Story 1 scenario 2
- **Acceptance:**
  - [ ] Failing test written and observed failing (fake ausente): `test_fake_conforms_to_schema`.
  - [ ] O fake retorna respostas canônicas de `impact`/`drift`/`provenance` que validam contra o schema de T001.
  - [ ] No other existing test regresses.
  - [ ] Commit message: `feat(graph): T002 fake do provider conforme ao contrato`.
- **Notes:** Artigo V exige que os testes usem um fake, não um mock de SDK. Este fake é a base das tasks do `analyze`.

### T003 — Regra `graph-facts` com vocabulário de confiança e mapeamento

- **Status:** pending
- **Depends on:** —
- **Files:**
  - create: `rules/graph-facts.md`
  - test: `tests/test_graph_facts_rule.py`
- **Spec scenarios:** Story 3 scenario 1, Story 3 scenario 2, Story 3 scenario 3
- **Acceptance:**
  - [ ] Failing test written and observed failing (regra ausente): `test_rule_defines_vocabulary_and_mapping`.
  - [ ] A regra define os rótulos canônicos aiadev (`explicit`/`inferred`/`ambiguous`) e o mapa estável a partir da taxonomia do provider (`EXTRACTED`/`INFERRED`/`AMBIGUOUS`).
  - [ ] No other existing test regresses.
  - [ ] Commit message: `feat(graph): T003 regra graph-facts (confiança + mapeamento)`.
- **Notes:** Cross-cutting; propaga a `plan`/review no fast-follow via `aiadev sync`.

### T004 — `analyze`: gap "task without code" ancorado no provider

- **Status:** pending
- **Depends on:** T001, T003
- **Files:**
  - modify: `skills/analyze/SKILL.md`
  - test: `tests/test_analyze_graph_provider.py`
- **Spec scenarios:** Story 1 scenario 1
- **Acceptance:**
  - [ ] Failing test written and observed failing: `test_analyze_declares_task_without_code_provider_step`.
  - [ ] A skill descreve o passo opcional que, com provider, reporta "task without code" citando o `arquivo:símbolo` esperado e ausente.
  - [ ] No other existing test regresses.
  - [ ] Commit message: `feat(graph): T004 analyze ancora task-without-code`.
- **Notes:** Passo aditivo e condicional; não altera as demais classes de gap.

### T005 — `analyze`: gap "code without task" ancorado no provider

- **Status:** pending
- **Depends on:** T004
- **Files:**
  - modify: `skills/analyze/SKILL.md`
  - test: `tests/test_analyze_graph_provider.py`
- **Spec scenarios:** Story 1 scenario 2
- **Acceptance:**
  - [ ] Failing test written and observed failing: `test_analyze_declares_code_without_task_provider_step`.
  - [ ] A skill descreve o passo que lista cada arquivo alterado sem task com a aresta do grafo que o conecta a um subsistema.
  - [ ] No other existing test regresses.
  - [ ] Commit message: `feat(graph): T005 analyze ancora code-without-task`.
- **Notes:** Mesmo arquivo de T004 — serial.

### T006 — `analyze`: degradação graciosa sem provider

- **Status:** pending
- **Depends on:** T005
- **Files:**
  - modify: `skills/analyze/SKILL.md`
  - test: `tests/test_analyze_graph_provider.py`
- **Spec scenarios:** Story 1 scenario 3
- **Acceptance:**
  - [ ] Failing test written and observed failing: `test_analyze_graceful_degradation_clause`.
  - [ ] A skill contém a cláusula explícita: sem provider configurado, a saída é idêntica ao comportamento atual (4 classes por inferência) e nenhum erro é emitido por provider ausente.
  - [ ] No other existing test regresses.
  - [ ] Commit message: `feat(graph): T006 analyze degradação graciosa`.
- **Notes:** Success criterion central; garante zero regressão sem provider.

### T007 — `analyze`: rótulos de confiança e regra do inferido não-definitivo

- **Status:** pending
- **Depends on:** T006
- **Files:**
  - modify: `skills/analyze/SKILL.md`
  - test: `tests/test_analyze_graph_provider.py`
- **Spec scenarios:** Story 3 scenario 1, Story 3 scenario 2
- **Acceptance:**
  - [ ] Failing test written and observed failing: `test_analyze_labels_and_non_definitive_inferred`.
  - [ ] A skill instrui a citar cada fato com o rótulo de confiança de `rules/graph-facts.md`, e proíbe usar fato `inferred`/`ambiguous` para afirmar um gap como definitivo.
  - [ ] No other existing test regresses.
  - [ ] Commit message: `feat(graph): T007 analyze rótulos de confiança`.
- **Notes:** Depende do vocabulário de T003; mesmo arquivo de T004–T006 — serial.

### T008 — Preset opcional `knowledge-graph` (mcps.yaml + README)

- **Status:** pending
- **Depends on:** T001
- **Files:**
  - create: `presets/knowledge-graph/mcps.yaml`
  - create: `presets/knowledge-graph/README.md`
  - test: `tests/test_knowledge_graph_preset.py`
- **Spec scenarios:** Story 1 scenario 1, Story 1 scenario 2
- **Acceptance:**
  - [ ] Failing test written and observed failing: `test_preset_declares_graph_provider`.
  - [ ] `mcps.yaml` declara um server de grafo (graphify de referência); o README documenta opt-in e o aviso de privacidade (backend LLM é opcional).
  - [ ] No other existing test regresses.
  - [ ] Commit message: `feat(graph): T008 preset opcional knowledge-graph`.
- **Notes:** Se o mecanismo de presets não suportar overlay aditivo, aplicar o fallback do plano (bloco opt-in comentado) — decidir com `aiadev install --dry-run`.

### T009 — Registrar o preset no catálogo como opt-in

- **Status:** pending
- **Depends on:** T008
- **Files:**
  - modify: `presets/catalog.json`
  - test: `tests/test_knowledge_graph_preset.py`
- **Spec scenarios:** Story 1 scenario 3
- **Acceptance:**
  - [ ] Failing test written and observed failing: `test_catalog_registers_optin_preset`.
  - [ ] Entrada válida contra o schema do catálogo, marcada como opt-in/experimental.
  - [ ] No other existing test regresses.
  - [ ] Commit message: `feat(graph): T009 registra preset no catálogo`.
- **Notes:** `aiadev install --preset knowledge-graph --dry-run` deve resolver sem impor a nenhum preset existente.

### T010 — Atribuição a Graphify-Labs/graphify (Artigo VII)

- **Status:** pending
- **Depends on:** —
- **Files:**
  - modify: `CREDITS.md`
  - test: `tests/test_credits_graphify.py`
- **Spec scenarios:** Story 3 scenario 3
- **Acceptance:**
  - [ ] Failing test written and observed failing: `test_credits_has_graphify_entry`.
  - [ ] `CREDITS.md` credita `Graphify-Labs/graphify` (link + ideia adaptada: contrato, tags de confiança, blast-radius).
  - [ ] No other existing test regresses.
  - [ ] Commit message: `docs(graph): T010 atribuição ao graphify`.
- **Notes:** Artigo VII não é waivable.

## Parallelization hints

- Parallel group A: T001, T003, T010 (arquivos disjuntos).
- Serial: T002 depende de T001; T004→T005→T006→T007 (mesmo `skills/analyze/SKILL.md`); T008→T009.

## Post-task checklist

After every task:

- [ ] Commit message references the task id.
- [ ] Status in this file updated.

After all tasks:

- [ ] Full test suite passes (`python3 -m pytest && python3 scripts/validate_skills.py`).
- [ ] `analyze` skill runs and reports no drift vs spec / plan.
- [ ] Hand off to `requesting-code-review` to open the PR.
