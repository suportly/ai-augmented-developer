# Tasks: skill `product` e templates de contexto de produto (mission, tech-stack, roadmap)

> Produced by the `tasks` skill from an approved `plan.md`. Consumed by `implement`.

**Branch:** `feature/0023-product-context`
**Plan:** [plan.md](./plan.md)
**Generated:** 2026-09-24
**Language:** pt-BR <!-- mirrors spec.md; write task descriptions in this language. -->

---

## How to read this file

- Tasks are ordered. `implement` runs them top-to-bottom.
- One task = one commit. The commit message starts with the task id.
- Each task links back to the spec acceptance scenarios it exercises.
- `Status` is one of: `pending`, `in_progress`, `blocked`, `done`. Owned by the `implement` skill — it flips `pending` → `done` inside each task's commit. Do not edit by hand; manual edits are overwritten on the next `implement` run.

**Fases do plano:** T001–T004 = Fase 1 (templates); T005–T011 = Fase 2 (skill e registros); T012–T013 = Fase 3 (`specify`/`plan`); T014 = Fase 4 (atribuição); T015 = Fase 5 (dogfooding).

## Task list

### T001 — Template de missão

- **Status:** done
- **Depends on:** —
- **Files:**
  - create: `templates/mission-template.md`
  - test: `tests/test_product_templates.py`
- **Spec scenarios:** Story 2 scenario 1, scenario 2
- **Acceptance:**
  - [ ] Failing test written and observed failing: `test_mission_template_shape` (arquivo ausente) e `test_mission_template_has_no_product_content`.
  - [ ] O template tem header `Language:` e anchors `<!-- section: … -->` para por quê, para quem, problema e fora de escopo. Toda linha fora de comentário HTML é heading, contém placeholder `{{UPPER_SNAKE}}` ou é esqueleto de lista/tabela.
  - [ ] No other existing test regresses.
  - [ ] Commit message: `feat(product): T001 template de missão`.
- **Notes:** O helper de "sem conteúdo de produto" fica neste arquivo de teste e é reutilizado por T002 e T003. A seção "fora de escopo" é o que `specify` usa em T012 para detectar conflito.

### T002 — Template de tech-stack

- **Status:** done
- **Depends on:** —
- **Files:**
  - create: `templates/tech-stack-template.md`
  - test: `tests/test_product_templates.py`
- **Spec scenarios:** Story 2 scenario 1, scenario 2
- **Acceptance:**
  - [ ] Failing test written and observed failing: `test_tech_stack_template_shape` e `test_tech_stack_template_has_no_product_content`.
  - [ ] Anchors para linguagens, frameworks e decisões; cada decisão tem campos de porquê e alternativas descartadas (cl-3: `tech-stack.md` guarda decisões, o auto-stack guarda o inventário). O comentário-guia diz que a primeira versão vem de `project_introspect.introspect()` com fonte citada.
  - [ ] No other existing test regresses.
  - [ ] Commit message: `feat(product): T002 template de tech-stack`.

### T003 — Template de roadmap com a gramática de entrada

- **Status:** pending
- **Depends on:** —
- **Files:**
  - create: `templates/roadmap-template.md`
  - test: `tests/test_product_templates.py`
- **Spec scenarios:** Story 2 scenario 1, scenario 2, scenario 3
- **Acceptance:**
  - [ ] Failing test written and observed failing: `test_roadmap_template_entry_grammar` e `test_roadmap_template_has_no_product_content`.
  - [ ] Entrada de exemplo com placeholders no formato `### R{{NNN}} — {{TITLE}}`, com os campos `- **Status:**`, `- **Spec:**` e `- **Depends on:**`. O comentário-guia lista o conjunto fechado `planned | in-progress | done | dropped` e diz que "pronto para implementar" não é status do roadmap (cl-2).
  - [ ] No other existing test regresses.
  - [ ] Commit message: `feat(product): T003 template de roadmap`.
- **Notes:** Sem parser em Python (plan ADR-3); o teste verifica a forma com regex.

### T004 — Tabela do `templates/README.md`

- **Status:** pending
- **Depends on:** T001, T002, T003
- **Files:**
  - modify: `templates/README.md`
  - test: `tests/test_product_templates.py`
- **Spec scenarios:** Story 2 scenario 1
- **Acceptance:**
  - [ ] Failing test written and observed failing: `test_templates_readme_lists_product_templates`.
  - [ ] A tabela "Produced by / Consumed by" tem uma linha por template: produzido por `product`; consumido por `specify` (mission, roadmap) e `plan` (tech-stack).
  - [ ] No other existing test regresses.
  - [ ] Commit message: `docs(templates): T004 lista os templates de produto`.

### T005 — Skill `product`: esqueleto e instalação nas 5 plataformas

- **Status:** pending
- **Depends on:** T001, T002, T003
- **Files:**
  - create: `skills/product/SKILL.md`
  - test: `tests/test_product_install_platforms.py`
- **Spec scenarios:** Story 4 scenario 1, scenario 2
- **Acceptance:**
  - [ ] Failing test written and observed failing: `test_product_skill_installed[<platform>]`, parametrizado nas 5 plataformas (instala `lean` num `tmp_path` e confere o `SKILL.md` no diretório de skills de cada plataforma), e `test_product_skill_frontmatter_validates`.
  - [ ] Frontmatter com `name` e `description` no topo e `metadata.aiadev` com inputs, outputs `specs/_product/{mission,tech-stack,roadmap}.md`, `requires` com os três templates e `handoffs: [specify]`. `aiadev validate skills/product/SKILL.md` passa.
  - [ ] No other existing test regresses (inclusive `tests/test_skills_conformance.py`).
  - [ ] Commit message: `feat(product): T005 skill product instalável nas 5 plataformas`.
- **Notes:** Corpo mínimo com o anúncio de início; o comportamento entra em T006–T008. Não tocar `PIPELINE_SKILLS` nem o preflight (cl-4).

### T006 — Skill `product`: modo bootstrap com fonte citada

- **Status:** pending
- **Depends on:** T005
- **Files:**
  - modify: `skills/product/SKILL.md`
  - test: `tests/test_product_skill.py`
- **Spec scenarios:** Story 1 scenario 1, scenario 2
- **Acceptance:**
  - [ ] Failing test written and observed failing: `test_bootstrap_reads_repo_context`, `test_every_value_cites_source`, `test_unknown_values_become_cl_markers`, `test_writes_only_after_approval`.
  - [ ] Sem `specs/_product/`, a skill lê `README.md`, os arquivos de pacote, `AGENTS.md`/`CLAUDE.md` e `.claude/rules/*`, renderiza os três templates com cada valor citando arquivo (e linha quando houver), transforma o que não é inferível em marcador de clarificação `cl-N` e só grava após aprovação explícita. Contém a regra "inferido não é inventado".
  - [ ] No other existing test regresses.
  - [ ] Commit message: `feat(product): T006 modo bootstrap com fonte citada`.
- **Notes:** Espelha o *Bootstrap mode* de `skills/constitution/SKILL.md` (plan ADR-1).

### T007 — Skill `product`: modo atualização e exclusão de segredos

- **Status:** pending
- **Depends on:** T006
- **Files:**
  - modify: `skills/product/SKILL.md`
  - test: `tests/test_product_skill.py`
- **Spec scenarios:** Story 1 scenario 3, scenario 4
- **Acceptance:**
  - [ ] Failing test written and observed failing: `test_update_mode_lists_sections_without_overwrite` e `test_never_reads_secret_files`.
  - [ ] Com os arquivos existentes e sem texto do usuário, a skill lista as seções e pergunta qual atualizar, sem sobrescrever nada. A seção de regras proíbe ler `.env*`, `*.pem`, `*.key`, `id_rsa*` e `*credentials*`.
  - [ ] No other existing test regresses.
  - [ ] Commit message: `feat(product): T007 modo atualização e exclusão de segredos`.

### T008 — Skill `product`: tech-stack semeado pelo introspect

- **Status:** pending
- **Depends on:** T007
- **Files:**
  - modify: `skills/product/SKILL.md`
  - test: `tests/test_product_skill.py`
- **Spec scenarios:** Story 1 scenario 1
- **Acceptance:**
  - [ ] Failing test written and observed failing: `test_tech_stack_seeded_from_introspect`.
  - [ ] A skill instrui a semear linguagens e frameworks a partir de `project_introspect.introspect()` (a mesma fonte do bloco auto-stack), citando-o, e a pedir ao humano o porquê e as alternativas descartadas de cada decisão (cl-3, plan ADR-4).
  - [ ] No other existing test regresses.
  - [ ] Commit message: `feat(product): T008 tech-stack semeado pelo introspect`.

### T009 — Comando `/aia:product`

- **Status:** pending
- **Depends on:** T005
- **Files:**
  - create: `commands/product.md`
  - test: `tests/test_product_install_platforms.py`
- **Spec scenarios:** Story 4 scenario 3
- **Acceptance:**
  - [ ] Failing test written and observed failing: `test_product_command_installed_for_claude_code` (o comando aparece em `.claude/commands/aia/product.md` após instalar `lean`) e `test_product_command_invokes_skill`.
  - [ ] Mesmo formato de `commands/specify.md`: frontmatter com `description`, `allowed-tools` e `argument-hint`; corpo invoca a skill `product`.
  - [ ] No other existing test regresses.
  - [ ] Commit message: `feat(product): T009 comando /aia:product`.

### T010 — `CLAUDE.md` e pipeline-reference com `product`

- **Status:** pending
- **Depends on:** T005
- **Files:**
  - modify: `CLAUDE.md`
  - modify: `scripts/generate_pipeline_reference.py`
  - modify: `docs/pipeline-reference.md`
  - test: `tests/test_product_registries.py`
- **Spec scenarios:** Story 4 scenario 3
- **Acceptance:**
  - [ ] Failing test written and observed failing: `test_pipeline_lists_product_before_specify` e `test_claude_md_table_has_product`.
  - [ ] `product` entra em `PIPELINE` antes de `specify`; a tabela "Skill to invoke" do `CLAUDE.md` ganha uma linha com `product` (condição: projeto sem contexto de produto em `specs/_product/`); `docs/pipeline-reference.md` é regenerado com `python3 scripts/generate_pipeline_reference.py`.
  - [ ] `tests/test_pipeline_reference_drift.py` e `tests/test_generate_pipeline_reference.py` continuam verdes, inclusive o orçamento de 24 linhas.
  - [ ] Commit message: `docs(product): T010 product no CLAUDE.md e na quick-reference`.
- **Notes:** `CLAUDE.md` e o reference **têm de mudar no mesmo commit**: o teste de drift compara os dois, e mudar só um quebra a suíte.

### T011 — Demais registros de skills e README

- **Status:** pending
- **Depends on:** T009, T010
- **Files:**
  - modify: `skills/using-ai-augmented-developer/SKILL.md`
  - modify: `templates/agent-file-template.md`
  - modify: `presets/lean/CLAUDE.md`
  - modify: `rules/slash-commands.md`
  - modify: `README.md`
  - test: `tests/test_product_registries.py`
- **Spec scenarios:** Story 4 scenario 3
- **Acceptance:**
  - [ ] Failing test written and observed failing: `test_product_listed_in_every_registry`, parametrizado nos cinco arquivos.
  - [ ] Tabela de skills em `using-ai-augmented-developer`, tabela de estágios do `agent-file-template`, linha do pipeline do `lean` (`product → specify → …`), `/aia:product` em `rules/slash-commands.md`, e no README as seções "What's Inside" e "The Basic Workflow".
  - [ ] No other existing test regresses.
  - [ ] Commit message: `docs(product): T011 registra product nos catálogos de skills`.

### T012 — `specify` lê mission e roadmap

- **Status:** pending
- **Depends on:** T001, T003
- **Files:**
  - modify: `skills/specify/SKILL.md`
  - test: `tests/test_specify_plan_product_context.py`
- **Spec scenarios:** Story 3 scenario 1, scenario 2, scenario 5
- **Acceptance:**
  - [ ] Failing test written and observed failing: `test_specify_reads_mission_and_roadmap_when_present`, `test_specify_cites_roadmap_entry_in_traceability`, `test_specify_pauses_on_mission_out_of_scope_conflict`, `test_specify_product_reading_is_conditional`.
  - [ ] Os passos 2–3 do loop passam a ler `specs/_product/mission.md` e `roadmap.md` **quando existirem**. A entrada `R<NNN>` correspondente é citada em *Traceability*. Conflito com o fora-de-escopo da missão pausa a skill, como o "premise mismatch" já existente.
  - [ ] `tests/test_specify_skill_has_recon_step.py`, `tests/test_e2e_specify.py` e `tests/test_e2e_pipeline.py` continuam verdes sem alteração.
  - [ ] Commit message: `feat(specify): T012 lê mission e roadmap quando existirem`.

### T013 — `plan` lê tech-stack e aponta divergência com o auto-stack

- **Status:** pending
- **Depends on:** T002
- **Files:**
  - modify: `skills/plan/SKILL.md`
  - test: `tests/test_specify_plan_product_context.py`
- **Spec scenarios:** Story 3 scenario 3, scenario 4, scenario 5
- **Acceptance:**
  - [ ] Failing test written and observed failing: `test_plan_uses_tech_stack_for_technical_context`, `test_plan_deviation_becomes_adr`, `test_plan_lists_tech_stack_auto_stack_divergence`, `test_plan_product_reading_is_conditional`.
  - [ ] O passo 2 do loop usa `specs/_product/tech-stack.md` quando existir; desvio de linguagem ou framework vira entrada em *Architecture decisions*; divergência com o bloco `<!-- aiadev:auto-stack -->` é listada citando os dois lados, sem escolher um.
  - [ ] `tests/test_e2e_pipeline.py` continua verde sem alteração.
  - [ ] Commit message: `feat(plan): T013 lê tech-stack e aponta divergência com o auto-stack`.

### T014 — Atribuição ao curso SDD e CHANGELOG

- **Status:** pending
- **Depends on:** T011
- **Files:**
  - modify: `CREDITS.md`
  - modify: `CHANGELOG.md`
  - test: `tests/test_credits_sdd_course.py`
- **Spec scenarios:** Story 2 scenario 2 (conteúdo próprio, não copiado)
- **Acceptance:**
  - [ ] Failing test written and observed failing: `test_credits_names_sdd_course_as_idea_only` e `test_changelog_mentions_0023`.
  - [ ] Entrada em "Direct inspirations" do `CREDITS.md` para "Spec-Driven Development with Coding Agents" (DeepLearning.AI × JetBrains), no formato das entradas de BMAD-METHOD e headroom, dizendo que só a ideia foi adaptada e nenhum texto foi copiado. Entrada em `CHANGELOG.md [Unreleased]` citando `0023`, a skill `product` e os três templates.
  - [ ] No other existing test regresses (inclusive `tests/test_attribution_and_changelog.py` e `tests/test_changelog_entry.py`).
  - [ ] Commit message: `docs(product): T014 atribuição ao curso SDD e changelog`.
- **Notes:** O CHANGELOG é escrito em inglês, como o resto do arquivo. A URL do curso precisa ser confirmada antes de gravar; não inventar.

### T015 — Dogfooding: `specs/_product/` do aiadev, fora do pacote

- **Status:** pending
- **Depends on:** T008, T011, T012, T013, T014
- **Files:**
  - create: `specs/_product/mission.md`
  - create: `specs/_product/tech-stack.md`
  - create: `specs/_product/roadmap.md`
  - test: `tests/test_product_not_packaged.py`
- **Spec scenarios:** Story 1 scenario 1 (execução real); success criterion de dogfooding (cl-5)
- **Acceptance:**
  - [ ] Failing test written and observed failing: `test_repo_has_product_context` (os três arquivos existem e têm os anchors dos templates) e `test_product_context_not_packaged` (`MANIFEST.in` e `COPY_PLAN` de `scripts/sync_assets.py` não incluem `specs`, e `framework_artifacts.iter_framework_artifacts` não emite nenhum caminho sob `specs/`).
  - [ ] Os três arquivos são gerados **rodando a skill `product`** neste repositório. O mantenedor revisa e aprova antes de gravar. O `roadmap.md` inclui as specs 0024–0029 como entradas `planned` com o `**Spec:**` preenchido.
  - [ ] Qualquer ajuste de texto da skill descoberto aqui entra neste commit, com teste em `tests/test_product_skill.py`.
  - [ ] No other existing test regresses.
  - [ ] Commit message: `feat(product): T015 dogfooding do contexto de produto do aiadev`.
- **Notes:** Precisa de revisão humana do conteúdo (missão e porquês são do mantenedor); a task fica `blocked` até essa aprovação.

## Parallelization hints

- Parallel group A: T001, T002, T003 (arquivos disjuntos; o arquivo de teste é compartilhado, então fundir com cuidado ou rodar em série).
- Parallel group B: T012, T013 (skills diferentes; o arquivo de teste é compartilhado).
- Serial: T005 → T006 → T007 → T008 (mesmo `SKILL.md`); T010 → T011 (registros); T015 por último.

## Post-task checklist

After every task:

- [ ] Commit message references the task id.
- [ ] Status in this file updated.

After all tasks:

- [ ] Full test suite passes (`python3 -m pytest && python3 scripts/validate_skills.py && aiadev validate`).
- [ ] `npx markdownlint-cli2 '**/*.md'` passes (CI runs it).
- [ ] `analyze` skill runs and reports no drift vs spec / plan.
- [ ] Hand off to `requesting-code-review` to open the PR.
