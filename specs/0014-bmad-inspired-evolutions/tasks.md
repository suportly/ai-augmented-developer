# Tasks: BMAD-inspired framework evolutions

> Produced by the `tasks` skill from an approved `plan.md`. Consumed by `implement`.

**Branch:** `feature/bmad-inspired-evolutions`
**Plan:** [plan.md](./plan.md)
**Generated:** 2026-05-13
**Language:** pt-BR

---

## How to read this file

- Tasks are ordered. `implement` runs them top-to-bottom.
- One task = one commit. The commit message starts with the task id.
- Each task links back to the spec acceptance scenarios it exercises.
- `Status` is one of: `pending`, `in_progress`, `blocked`, `done`. Owned by the `implement` skill — it flips `pending` → `done` inside each task's commit. Do not edit by hand.

## Task list

**Phase 1 — Foundation: `pipeline_state.py`**

### T001 — Criar 10 fixtures de estado de pipeline + fixture sintética de 50 specs

- **Status:** done
- **Depends on:** —
- **Files:**
  - create: `tests/fixtures/pipeline_state/empty/.gitkeep`
  - create: `tests/fixtures/pipeline_state/draft_spec/specs/0001-x/spec.md`
  - create: `tests/fixtures/pipeline_state/clarified_spec/specs/0001-x/spec.md`
  - create: `tests/fixtures/pipeline_state/planned/specs/0001-x/{spec.md,plan.md}`
  - create: `tests/fixtures/pipeline_state/tasked/specs/0001-x/{spec.md,plan.md,tasks.md}`
  - create: `tests/fixtures/pipeline_state/half_done/specs/0001-x/{spec.md,plan.md,tasks.md}`
  - create: `tests/fixtures/pipeline_state/all_done/specs/0001-x/{spec.md,plan.md,tasks.md}`
  - create: `tests/fixtures/pipeline_state/review_pending/specs/0001-x/{spec.md,plan.md,tasks.md,.review-log.jsonl}`
  - create: `tests/fixtures/pipeline_state/review_approved/specs/0001-x/{spec.md,plan.md,tasks.md,.review-log.jsonl}`
  - create: `tests/fixtures/pipeline_state/orphan_branch/specs/{0001-x,0002-y}/spec.md`
  - create: `tests/fixtures/pipeline_state/perf_50_specs/specs/<...>` (script gerador opcional em `tests/fixtures/pipeline_state/_generate_perf.py`)
- **Spec scenarios:** Story 4 sc1, sc2, sc3, sc4, sc5, sc6, sc7, sc8 (provê os inputs que cada cenário lê).
- **Acceptance:**
  - [ ] Cada fixture é um diretório autocontido reproduzível por `pytest`.
  - [ ] Nenhum teste roda neste commit — pure scaffolding para T002.
  - [ ] Commit message: `test(pipeline_state): T001 add pipeline state fixtures`.

### T002 — RED: `tests/test_pipeline_state.py` cobrindo Story 4 AC-1 a AC-8 + budget

- **Status:** done
- **Depends on:** T001
- **Files:**
  - create: `tests/test_pipeline_state.py`
- **Spec scenarios:** Story 4 sc1, sc2, sc3, sc4, sc5, sc6, sc7, sc8.
- **Acceptance:**
  - [ ] Failing tests escritos e observados falhando porque `aiadev.pipeline_state` ainda não existe (`ImportError`).
  - [ ] Cada cenário do spec é um caso parametrizado distinto (8 transições + 1 budget de performance ≤ 200 ms em 50 specs).
  - [ ] Asserts retornam o dict `{"command": ..., "reason": ...}`.
  - [ ] Commit message: `test(pipeline_state): T002 red tests for recommend_next_command`.

### T003 — GREEN: implementar `src/aiadev/pipeline_state.py`

- **Status:** done
- **Depends on:** T002
- **Files:**
  - create: `src/aiadev/pipeline_state.py`
- **Spec scenarios:** Story 4 sc1, sc2, sc3, sc4, sc5, sc6, sc7, sc8.
- **Acceptance:**
  - [ ] Mínimo código necessário para os testes de T002 passarem.
  - [ ] Função pública `recommend_next_command(workspace_path: Path) -> dict` com docstring.
  - [ ] Performance: ≤ 200 ms em fixture com 50 specs.
  - [ ] Nenhuma regressão na suite existente (rodar `pytest tests/`).
  - [ ] Commit message: `feat(pipeline_state): T003 implement recommend_next_command`.

**Phase 2 — Story 3 (zero-findings-halt) e Story 4 (help state-aware) em paralelo**

### T004 — Adicionar regra "Output for APPROVED on non-trivial change" nos 3 reviewer agents

- **Status:** done
- **Depends on:** T003
- **Files:**
  - modify: `agents/code-reviewer.md`
  - modify: `agents/spec-document-reviewer.md`
  - modify: `agents/plan-document-reviewer.md`
  - create: `tests/test_zero_findings_halt_agents.py`
- **Spec scenarios:** Story 3 sc1, sc4, sc5.
- **Acceptance:**
  - [ ] Failing test em `test_zero_findings_halt_agents.py` que asserta presença da seção `### Output rule for APPROVED on non-trivial change` + bloco `### Why no issues` (≥ 3 verificações) em cada um dos 3 arquivos — observado falhando antes da edição.
  - [ ] Edição dos 3 arquivos torna o teste verde.
  - [ ] Para `spec-document-reviewer.md` e `plan-document-reviewer.md`: regra reforça que criação de spec/plan é SEMPRE não-trivial (spec sc4).
  - [ ] Commit message: `feat(agents): T004 add zero-findings-halt rule to reviewer subagents`.

### T005 — Estender `schemas/terse-output.schema.json` com variante `🟢 verification`

- **Status:** done
- **Depends on:** —
- **Files:**
  - modify: `schemas/terse-output.schema.json`
  - create: `tests/test_terse_output_schema.py`
- **Spec scenarios:** Story 3 sc5.
- **Acceptance:**
  - [ ] Failing test que valida uma linha `🟢 file:line — verificação realizada` contra o schema atual (deve falhar).
  - [ ] Edição do schema permite a variante; teste passa.
  - [ ] Linhas existentes (`🔴`, `🟡`, `🟢` nit) continuam válidas.
  - [ ] Commit message: `feat(schemas): T005 add 🟢 verification variant to terse-output schema`.

### T006 — RED: detector de "non-trivial change" + leitor/escritor de `.review-log.jsonl`

- **Status:** done
- **Depends on:** T003
- **Files:**
  - create: `tests/test_review_log.py`
  - create: `tests/fixtures/review_log/{trivial_diff,nontrivial_diff,spec_creation}/`
- **Spec scenarios:** Story 3 sc1, sc2, sc3, sc4.
- **Acceptance:**
  - [ ] Failing tests para `is_non_trivial_change(diff_stat, paths)` cobrindo cl-5: > 10 LOC excluindo `.md/.json/.lock/.toml/docs/`; spec/plan SEMPRE não-trivial.
  - [ ] Failing tests para `append_review_entry(workspace, entry)` e `last_review_entry(workspace)` (formato JSONL em `specs/<branch>/.review-log.jsonl`).
  - [ ] Fixtures cobrem 3 estados: diff trivial, diff não-trivial, criação de spec.
  - [ ] Commit message: `test(review_log): T006 red tests for non-trivial detector + review log io`.

### T007 — GREEN: implementar `src/aiadev/review_log.py`

- **Status:** done
- **Depends on:** T006
- **Files:**
  - create: `src/aiadev/review_log.py`
- **Spec scenarios:** Story 3 sc1, sc2, sc3, sc4.
- **Acceptance:**
  - [ ] Mínimo código para os testes de T006 passarem.
  - [ ] Funções públicas com docstring.
  - [ ] Sem regressão na suite.
  - [ ] Commit message: `feat(review_log): T007 implement non-trivial detector and review log io`.

### T008 — Estender `aiadev preflight` com validador `requesting-code-review`

- **Status:** done
- **Depends on:** T007
- **Files:**
  - modify: `src/aiadev/commands/preflight.py`
  - modify: `src/aiadev/preflight.py`
  - create: `tests/test_preflight_review.py`
- **Spec scenarios:** Story 3 sc1, sc2.
- **Acceptance:**
  - [ ] Failing test asserta que `aiadev preflight requesting-code-review --feature <slug>` retorna exit ≠ 0 quando o último entry em `.review-log.jsonl` é APPROVED em mudança não-trivial sem bloco `### Why no issues`.
  - [ ] Failing test asserta exit 0 quando o entry é compliant.
  - [ ] Implementação faz os testes passarem.
  - [ ] Commit message: `feat(preflight): T008 validate review log for requesting-code-review`.

### T009 — Editar `skills/implement/SKILL.md` e `skills/requesting-code-review/SKILL.md` com gate de re-dispatch

- **Status:** done
- **Depends on:** T004, T008
- **Files:**
  - modify: `skills/implement/SKILL.md`
  - modify: `skills/requesting-code-review/SKILL.md`
  - create: `tests/test_review_redispatch_skills.py`
- **Spec scenarios:** Story 3 sc2, sc3.
- **Acceptance:**
  - [ ] Failing content test asserta presença de uma seção "Re-dispatch gate" descrevendo: detecção de APPROVED sem `### Why no issues` em diff não-trivial → re-dispatch com framing adversarial reforçado; limite duro de 2 re-dispatches/reviewer/task.
  - [ ] Edição dos 2 arquivos torna o teste verde.
  - [ ] Commit message: `feat(skills): T009 add reviewer re-dispatch gate to implement and requesting-code-review`.

### T010 — Editar `skills/help/SKILL.md`: state-aware via `pipeline_state` + flag `--plain`

- **Status:** done
- **Depends on:** T003
- **Files:**
  - modify: `skills/help/SKILL.md`
  - create: `tests/test_help_skill_state_aware.py`
- **Spec scenarios:** Story 4 sc1, sc2, sc3, sc4, sc5, sc6, sc7, sc8.
- **Acceptance:**
  - [ ] Failing content tests assertam que o skill: (a) chama `python -c "from aiadev.pipeline_state import recommend_next_command; ..."`, (b) prepende a recomendação à saída atual, (c) suporta `--plain` e env `AIADEV_HELP_PLAIN=1` que pulam a inspeção e caem no comportamento legacy byte-a-byte.
  - [ ] Edição do skill torna os testes verdes.
  - [ ] Atualizar `docs/pipeline-reference.md` apenas se o output do `help` em modo state-aware modificar o cabeçalho da referência (critério explícito do plan).
  - [ ] Commit message: `feat(skills): T010 make help skill state-aware`.

**Phase 3 — Story 2: customização 3-camadas**

### T011 — Criar fixtures TOML em `tests/fixtures/customization/`

- **Status:** done
- **Depends on:** —
- **Files:**
  - create: `tests/fixtures/customization/scalar_override/{base,team,user}.toml`
  - create: `tests/fixtures/customization/table_deep_merge/{base,team,user}.toml`
  - create: `tests/fixtures/customization/array_replace_or_append/{base,team,user}.toml`
  - create: `tests/fixtures/customization/parse_error/{base,team,user}.toml` (team.toml malformado)
  - create: `tests/fixtures/customization/passthrough/{base,team,user}.toml` (team e user vazios)
  - create: `tests/fixtures/customization/extension_override/{base,team,user}.toml`
- **Spec scenarios:** Story 2 sc1, sc2, sc3, sc4, sc5 (provê inputs).
- **Acceptance:**
  - [ ] 6 diretórios de fixtures cobrem todas as regras de merge do ADR-2.
  - [ ] Pure scaffolding para T012.
  - [ ] Commit message: `test(customization): T011 add TOML merge fixtures`.

### T012 — RED: `tests/test_customization.py` cobrindo Story 2 AC-1 a AC-5

- **Status:** done
- **Depends on:** T011
- **Files:**
  - create: `tests/test_customization.py`
- **Spec scenarios:** Story 2 sc1, sc2, sc3, sc4, sc5.
- **Acceptance:**
  - [ ] Failing tests para: precedência de scalars (sc3), deep-merge de tables, replace-vs-append por chave `code`/`id` (sc2), parse error abortando com `file:line` (sc4), passthrough do base quando overrides vazios, overrides em skills oriundos de extensão (sc5), e a integração de install criando `_aiadev/team.toml` + `.gitignore` (sc1 — pode ser teste separado em T014).
  - [ ] Tests falham por `ImportError` (`aiadev.customization` ausente).
  - [ ] Commit message: `test(customization): T012 red tests for merge_layers`.

### T013 — GREEN: implementar `src/aiadev/customization.py`

- **Status:** done
- **Depends on:** T012
- **Files:**
  - create: `src/aiadev/customization.py`
- **Spec scenarios:** Story 2 sc2, sc3, sc4, sc5.
- **Acceptance:**
  - [ ] API `merge_layers(base: dict, team: dict, user: dict) -> dict` honra ADR-2.
  - [ ] Helpers `load_layer(path: Path) -> dict` que abortam com `ERROR: <path> line <N>: <parse-error>` em TOML inválido.
  - [ ] Mínimo código para tests de T012 passarem.
  - [ ] Performance: ≤ 50 ms para merge típico.
  - [ ] Commit message: `feat(customization): T013 implement 3-tier TOML resolver`.

### T014 — Editar `install.py` + `sync_assets.py`: emitir `_aiadev/` stubs

- **Status:** done
- **Depends on:** T013
- **Files:**
  - modify: `src/aiadev/commands/install.py`
  - modify: `scripts/sync_assets.py`
  - create: `tests/test_install_aiadev_stubs.py`
- **Spec scenarios:** Story 2 sc1.
- **Acceptance:**
  - [ ] Failing integration test asserta que `aiadev install --preset lean --non-interactive --vars PROJECT_NAME=Demo` em diretório temporário cria `_aiadev/team.toml` (commit-ready, com header explicando merge rules) e adiciona linha `_aiadev/user.toml` ao `.gitignore`.
  - [ ] `sync_assets.py` inclui `_aiadev/team.toml` no manifesto de stubs (critério: o stub é gerado por `install.py`; `sync_assets.py` só atualiza o manifesto quando o template do stub muda).
  - [ ] Tests passam após edição.
  - [ ] Commit message: `feat(install): T014 emit _aiadev stubs and update sync manifest`.

### T015 — Escrever `docs/customization.md`

- **Status:** done
- **Depends on:** T013
- **Files:**
  - create: `docs/customization.md`
  - create: `tests/test_customization_docs.py`
- **Spec scenarios:** Story 2 sc2, sc3 (documenta as regras de merge para o consumidor).
- **Acceptance:**
  - [ ] Failing content test asserta presença das seções: "Layer precedence", "Merge rules" (com sub-seções "Scalars", "Tables", "Arrays of tables"), e "Examples" (≥ 3 exemplos: override de menu de skill, override de `principles[]` em agent, override de scalar `default_model`).
  - [ ] Documentação criada faz o teste passar.
  - [ ] Commit message: `docs(customization): T015 document 3-tier TOML resolver`.

**Phase 4 — Story 1: skill `task-context`**

### T016 — Criar `templates/task-context-template.md`

- **Status:** done
- **Depends on:** —
- **Files:**
  - create: `templates/task-context-template.md`
  - create: `tests/test_task_context_template.py`
- **Spec scenarios:** Story 1 sc1 (provê o shape do output).
- **Acceptance:**
  - [ ] Failing content test asserta presença dos slots: `{{TASK_ID}}`, `{{TASK_TITLE}}`, seções "Spec slice (acceptance scenarios)", "Plan slice (task block)", "Files to modify with excerpts", "TDD checklist", "Previous task-context pointer".
  - [ ] Template criado faz o teste passar.
  - [ ] Commit message: `feat(templates): T016 add task-context template`.

### T017 — RED: `tests/test_task_context.py` cobrindo Story 1 AC-1 a AC-4

- **Status:** done
- **Depends on:** T016
- **Files:**
  - create: `tests/test_task_context.py`
  - create: `tests/fixtures/task_context/{spec.md,plan.md,tasks.md,src/...}` (mini-projeto sintético)
- **Spec scenarios:** Story 1 sc1, sc2, sc3, sc4.
- **Acceptance:**
  - [ ] Failing tests para: (sc1) skill produz `task-context/T003-<slug>.md` com todos os 5 sub-itens; (sc4) detecção de staleness via `mtime` vs último `git log -- <files>`; cobertura do conteúdo correto (slice de spec, slice de plan, excerpts ≤ 40 linhas).
  - [ ] Tests falham porque `skills/task-context/SKILL.md` ainda não existe.
  - [ ] Commit message: `test(task_context): T017 red tests for task-context skill`.

### T018 — Criar `skills/task-context/SKILL.md`

- **Status:** done
- **Depends on:** T017
- **Files:**
  - create: `skills/task-context/SKILL.md`
- **Spec scenarios:** Story 1 sc1, sc4.
- **Acceptance:**
  - [ ] Skill recebe `<TID>` e produz `specs/<branch>/task-context/<TID>-<slug>.md` a partir do template.
  - [ ] Implementa staleness check: se `mtime` do arquivo < último commit em arquivos referenciados, recompõe.
  - [ ] Tests de T017 passam.
  - [ ] Commit message: `feat(skills): T018 add task-context skill`.

### T019 — Editar `skills/implement/SKILL.md`: invocação opt-in de `task-context`

- **Status:** pending
- **Depends on:** T018
- **Files:**
  - modify: `skills/implement/SKILL.md`
  - create: `tests/test_implement_task_context_integration.py`
- **Spec scenarios:** Story 1 sc2, sc3.
- **Acceptance:**
  - [ ] Failing content test asserta que entre os passos 3 e 4 da loop, o skill descreve: (a) checar `task_context: true` no preset OU flag `--task-context`; (b) se ativo, invocar `task-context <TID>` antes do dispatch; (c) substituir o "Implementer prompt" por versão curta carregando o arquivo por path; (d) se inativo, comportamento atual roda byte-a-byte inalterado (sc3 — feature aditiva).
  - [ ] Edição do skill faz o teste passar.
  - [ ] Commit message: `feat(skills): T019 wire task-context into implement loop (opt-in)`.

### T020 — Ativar `task_context: true` em `presets/django-drf-react/preset.yaml` (dogfood)

- **Status:** pending
- **Depends on:** T019
- **Files:**
  - modify: `presets/django-drf-react/preset.yaml`
  - modify: `presets/catalog.json` (apenas se a schema do catalog precisar do novo campo opcional)
  - create: `tests/test_preset_task_context_dogfood.py`
- **Spec scenarios:** atende cl-8 (named user para Article III).
- **Acceptance:**
  - [ ] Failing test asserta que `presets/django-drf-react/preset.yaml` contém `task_context: true` e que o campo é validado pela schema do preset.
  - [ ] Edição faz o teste passar.
  - [ ] `presets/catalog.json` editado SOMENTE se a validação atual recusar o campo novo.
  - [ ] Commit message: `feat(presets): T020 enable task_context dogfood in django-drf-react`.

### T021 — Adicionar flag `--task-context` ao CLI `aiadev preflight implement`

- **Status:** pending
- **Depends on:** T019
- **Files:**
  - modify: `src/aiadev/cli.py`
  - modify: `src/aiadev/commands/preflight.py`
  - create: `tests/test_cli_task_context_flag.py`
- **Spec scenarios:** Story 1 sc1 (suporte ao opt-in via CLI).
- **Acceptance:**
  - [ ] Failing test (Click `CliRunner`) asserta que `aiadev preflight implement --task-context --feature <slug>` é parseado e propaga o flag.
  - [ ] Implementação faz o teste passar.
  - [ ] Commit message: `feat(cli): T021 add --task-context flag to preflight implement`.

### T022 — Atualizar `CREDITS.md` (atribuição BMAD) + `CHANGELOG.md` (Unreleased)

- **Status:** pending
- **Depends on:** T003, T010, T013, T018
- **Files:**
  - modify: `CREDITS.md`
  - modify: `CHANGELOG.md`
  - create: `tests/test_attribution_and_changelog.py`
- **Spec scenarios:** atende Article VII (Attribution); fecha Unreleased para o release.
- **Acceptance:**
  - [ ] Failing test asserta presença de entrada em `CREDITS.md` para `bmad-code-org/BMAD-METHOD` com link, license notice, e descrição "inspiration for task-context skill, 3-tier customization resolver, and zero-findings-halt review pattern".
  - [ ] Failing test asserta linha em `CHANGELOG.md` `[Unreleased]` mencionando as 4 stories.
  - [ ] Edições fazem os tests passarem.
  - [ ] Commit message: `docs: T022 attribute BMAD-METHOD and update changelog`.

## Parallelization hints

> Tasks que tocam arquivos disjuntos podem ser tentadas em paralelo. Tudo o resto é serial.

- **Parallel group A (após T003):** T004, T005, T010 — 3 reviewer agents, schema, e help skill são arquivos disjuntos.
- **Parallel group B (após T013):** T014 (install + sync_assets) e T015 (docs) são disjuntos.
- **Parallel group C (após T019):** T020 (preset.yaml) e T021 (cli.py + preflight.py) são disjuntos.
- **Serial:** todo o resto, incluindo as cadeias RED → GREEN dentro de cada fase (T001 → T002 → T003; T006 → T007 → T008; T011 → T012 → T013; T016 → T017 → T018).

## Post-task checklist

After every task:

- [ ] Commit message references the task id.
- [ ] Status in this file updated (owned by `implement`).

After all tasks:

- [ ] Full test suite passes (`pytest`).
- [ ] `analyze` skill runs and reports no drift vs spec / plan.
- [ ] Hand off to `requesting-code-review` to open the PR.
