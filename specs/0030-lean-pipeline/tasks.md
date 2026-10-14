# Tasks: pipeline enxuto — menos turnos, menos texto e medição correta de custo

> Produced by the `tasks` skill from an approved `plan.md`. Consumed by `implement`.

**Branch:** `feature/0030-lean-pipeline`
**Plan:** [plan.md](./plan.md)
**Generated:** 2026-10-13
**Language:** pt-BR <!-- mirrors spec.md; write task descriptions in this language. -->

---

## How to read this file

- Tasks are ordered. `implement` runs them top-to-bottom.
- One task = one commit. The commit message starts with the task id.
- Each task links back to the spec acceptance scenarios it exercises. Tasks de infraestrutura citam `Success criterion #N` (N = ordem do bullet em Success criteria da spec).
- `Status` is one of: `pending`, `in_progress`, `blocked`, `done`. Owned by the `implement` skill — it flips `pending` → `done` inside each task's commit. Do not edit by hand; manual edits are overwritten on the next `implement` run.
- As fases do plano são pontos de corte mescláveis: 1, 2 e 3 cobrem todas as stories P1 (T001–T035); 4 e 5 são P2.
- **T009 (baseline) precede qualquer task que corte texto** (T031, T034, T036 em diante).

## Task list

**Fase 1 — Medição e orçamento**

### T001 — Dedupe por message.id com maior valor por campo

- **Status:** done
- **Depends on:** —
- **Files:**
  - modify: `src/aiadev/token_metrics.py`
  - create: `tests/fixtures/token_metrics/dedupe_partial.jsonl`
  - test: `tests/test_token_metrics.py`
- **Spec scenarios:** Story 1 scenario 1
- **Acceptance:**
  - [ ] Teste vermelho: dois eventos com o mesmo `message.id` e `output_tokens` 1 e 214 somam 214; o mesmo id em dois arquivos soma uma vez.
  - [ ] Evento sem `message.id` continua contado como único; os valores pinados (total 3120, 4 turnos, ordem) seguem verdes.
  - [ ] Commit message: `feat(metrics): T001 dedupe de tokens por message.id`.

### T002 — Ler subagentes em subagents/ (recursivo)

- **Status:** done
- **Depends on:** T001
- **Files:**
  - modify: `src/aiadev/token_metrics.py`
  - create: `tests/fixtures/token_metrics/with_subagents/` (sessão com `subagents/agent-*.jsonl`, `subagents/workflows/wf_x/agent-*.jsonl` e `journal.jsonl`)
  - test: `tests/test_token_metrics.py`
- **Spec scenarios:** Story 1 scenario 2, scenario 3
- **Acceptance:**
  - [ ] Teste vermelho: o custo dos subagentes entra no relatório e `sidechain_turns` deixa de ser zero; `journal.jsonl` é ignorado.
  - [ ] Sessão sem diretório `subagents/` não gera erro.
  - [ ] Commit message: `feat(metrics): T002 inclui transcripts de subagentes`.

### T003 — Papel do subagente por prefixo da descrição

- **Status:** done
- **Depends on:** T002
- **Files:**
  - modify: `src/aiadev/token_metrics.py`
  - test: `tests/test_token_metrics.py`
- **Spec scenarios:** Story 1 scenario 2, scenario 3
- **Acceptance:**
  - [ ] Teste vermelho: `description` "implement: T003 …" vira papel implementação; "review: …" vira revisão; sem prefixo ou `*.meta.json` ilegível vira "não classificado" e é contado.
  - [ ] O texto das mensagens nunca é lido para inferir o papel (teste de privacidade existente continua verde).
  - [ ] Commit message: `feat(metrics): T003 papel do subagente por convenção de descrição`.

### T004 — Pesos e custo equivalente documentados

- **Status:** done
- **Depends on:** T003
- **Files:**
  - modify: `src/aiadev/token_metrics.py`
  - test: `tests/test_token_metrics.py`
- **Spec scenarios:** Story 1 scenario 4
- **Acceptance:**
  - [ ] Teste vermelho: custo equivalente = 0,1×leitura + 1,0×entrada + 5,0×saída + escrita (1,25× no tier de 5 min, 2,0× no de 1 h lido de `cache_creation.ephemeral_*`; sem o detalhe, 1,25×).
  - [ ] Os pesos são constantes nomeadas e citadas no texto do relatório como aproximação.
  - [ ] Commit message: `feat(metrics): T004 custo equivalente com pesos documentados`.

### T005 — Relatório de tokens por papel (texto e JSON)

- **Status:** done
- **Depends on:** T004
- **Files:**
  - modify: `src/aiadev/commands/metrics.py`
  - modify: `src/aiadev/token_metrics.py`
  - modify: `docs/metrics.md`
  - test: `tests/test_token_metrics.py`
- **Spec scenarios:** Story 1 scenario 2, scenario 4
- **Acceptance:**
  - [ ] Teste vermelho: o texto separa thread principal e subagentes por papel, mostra "não classificados" e a nota de aproximação; o JSON ganha chaves sem remover as existentes.
  - [ ] Corpo de `tool_result` continua ausente da saída.
  - [ ] Carry-over da T002: reescrever a linha "Subagent (sidechain) turns included: N" de `format_text` (hoje enganosa: os turnos de subagentes não entram no TOTAL) e serializar `SessionTokens.subagents` e `TokenReport.subagent_totals` (`to_dict()` ainda os omite).
  - [ ] Carry-over da T003: `_iter_lines` captura só `JSONDecodeError`; uma linha de transcript com aninhamento além do limite do interpretador levanta `RecursionError` e derruba `build_token_report` (contradiz a docstring "never raises on malformed lines"). Tratar com teste ou registrar como limite conhecido. A linha "TOTAL" de `subagent_totals` tem `role == "unclassified"` sem significado: agrupar por papel iterando `session.subagents`.
  - [ ] Commit message: `feat(metrics): T005 custo por papel em metrics --tokens`.

### T006 — Total confere com a dedupe independente

- **Status:** done
- **Depends on:** T001
- **Files:**
  - create: `tests/test_token_metrics_manual_rule.py`
  - modify: `docs/metrics.md`
- **Spec scenarios:** Success criterion #1
- **Acceptance:**
  - [ ] Teste vermelho: sobre uma fixture com repetições parciais, o total do relatório é igual a uma dedupe escrita de forma independente no teste (maior valor por campo e `message.id`), dentro de 1%.
  - [ ] A regra de dedupe manual está documentada em `docs/metrics.md` (usada como evidência do Art. IV).
  - [ ] Commit message: `test(metrics): T006 regra de dedupe manual como evidência`.

### T007 — Orçamento: sempre-carregado por preset

- **Status:** done
- **Depends on:** —
- **Files:**
  - create: `scripts/instruction_budget.py`
  - test: `tests/test_instruction_budget.py`
- **Spec scenarios:** Story 4 scenario 4
- **Acceptance:**
  - [ ] Teste vermelho: o script instala `lean` e `django-drf-react` num tmp pela rota da CLI e soma ⌈caracteres ÷ 4⌉ de wrapper, `AGENTS.md`, rules sem `paths:` e nome+descrição de skills, commands e agents.
  - [ ] Falta de PyYAML ou de `aiadev` sai com exit 2 e mensagem.
  - [ ] Commit message: `feat(budget): T007 medição do sempre-carregado por preset`.

### T008 — Orçamento: percurso do pipeline

- **Status:** done
- **Depends on:** T007
- **Files:**
  - create: `docs/pipeline-path.yaml`
  - modify: `scripts/instruction_budget.py`
  - test: `tests/test_instruction_budget.py`
- **Spec scenarios:** Story 4 scenario 4
- **Acceptance:**
  - [ ] Teste vermelho: o percurso `specify → finish` soma os arquivos listados por etapa; referência condicional (`task-context.md`) não conta, `review-gate.md` conta.
  - [ ] Arquivo citado no YAML que não existe falha a medição.
  - [ ] Commit message: `feat(budget): T008 percurso do pipeline`.

### T009 — Baseline versionado e catraca no CI

- **Status:** done
- **Depends on:** T008
- **Files:**
  - create: `docs/instruction-budget.json`
  - modify: `scripts/instruction_budget.py`
  - test: `tests/test_instruction_budget.py`
- **Spec scenarios:** Story 4 scenario 4; Success criterion #2
- **Acceptance:**
  - [ ] Teste vermelho: com o baseline gravado, o teste falha se skill, sempre-carregado ou percurso excederem o `teto`; elevar um teto exige o campo `reason`.
  - [ ] O baseline é gerado **antes** de qualquer corte de texto (esta task precede T031, T034 e a fase 4).
  - [ ] O relatório aponta arquivo e delta quando falha.
  - [ ] Commit message: `feat(budget): T009 baseline e catraca de instruções`.

**Fase 2 — Motor de instalação**

### T010 — Coletar references/ de skill (framework e preset)

- **Status:** done
- **Depends on:** —
- **Files:**
  - modify: `src/aiadev/install_engine.py`
  - create: `tests/fixtures/mini-preset/skills/hello-world/references/stack.md`
  - test: `tests/test_install_engine.py`
- **Spec scenarios:** Story 4 scenario 2, scenario 3
- **Acceptance:**
  - [ ] Teste vermelho: uma função de coleta própria (`_collect_skill_references`) devolve `references/**/*.md` de uma skill do framework e de uma skill do preset como role `skill`, nome `<skill>/<rel>`, com `verbatim` True (framework) e False (preset); outros arquivos (ex. `.DS_Store`) são ignorados. `_collect_artifacts` e o fluxo de `install()` ficam intactos nesta task (a T011 liga a coleta ao fluxo).
  - [ ] Preset com a mesma `<skill>/<rel>` do framework vence.
  - [ ] Commit message: `feat(install): T010 coleta references/ de skills`.

### T011 — Instalar references/ ao lado do SKILL.md em todas as plataformas

- **Status:** done
- **Depends on:** T010
- **Files:**
  - modify: `src/aiadev/install_engine.py`
  - test: `tests/test_install_engine.py` (classe parametrizada pelas 5 plataformas; os arquivos `test_install_<plataforma>.py` só testam contrato de handler e não chamam `install()`)
- **Spec scenarios:** Story 4 scenario 3
- **Acceptance:**
  - [ ] Teste vermelho por plataforma: o arquivo cai em `<destino da skill>/references/<arquivo>` e entra no manifesto com role `skill` e sha256.
  - [ ] Uninstall remove esses arquivos e limpa diretórios vazios.
  - [ ] Carry-over da T010: o fixture `mini-preset` ganhou `skills/hello-world/references/stack.md` (com `{{PROJECT_NAME}}`); toda instalação do mini-preset passa a escrever um arquivo a mais, então atualizar as contagens `len(report.written)`, `len(report.removed)` e `len(report.skipped)` em `tests/test_install_engine.py` (~linhas 116, 125, 200, 235, 257) e provar a substituição de variáveis no arquivo de referência.
  - [ ] Commit message: `feat(install): T011 instala references/ de skills nas 5 plataformas`.

### T012 — Placeholders em references de preset

- **Status:** done
- **Depends on:** T011
- **Files:**
  - modify: `src/aiadev/install_engine.py`
  - test: `tests/test_install_engine.py`
- **Spec scenarios:** Story 4 scenario 2
- **Acceptance:**
  - [ ] Teste vermelho: `references/` de preset passa por `substitute`/`find_unresolved`; `{{TOKEN}}` não resolvido falha com mensagem que cita o arquivo (hoje a mensagem lista só as chaves). A verbatim dos do framework já tem teste da T011 (`test_framework_reference_is_copied_verbatim`): não repetir.
  - [ ] Carry-over da revisão da T011: `install()` escreve arquivos durante o laço e só levanta o erro de placeholders no fim, sem salvar o manifesto — uma execução que falha deixa `SKILL.md` (e references) no disco sem rastreio e a re-execução os acusa como conflito. Validar os placeholders de TODOS os artefatos antes de escrever o primeiro (falha sem efeito colateral), com teste que prova que nada foi escrito.
  - [ ] Commit message: `feat(install): T012 substituição de variáveis em references de preset`.

### T013 — Remover órfãos pela regra de hash

- **Status:** done
- **Depends on:** —
- **Files:**
  - modify: `src/aiadev/install_engine.py`
  - test: `tests/test_install_engine.py`
- **Spec scenarios:** Story 6 scenario 1
- **Acceptance:**
  - [ ] Teste vermelho: arquivo do manifesto que o framework não distribui mais e com hash igual é removido; com hash diferente é preservado, listado em `preserved`, sai do manifesto e **não** vira `conflicts`; `--force` não o apaga.
  - [ ] Diretórios vazios são limpos.
  - [ ] Commit message: `feat(install): T013 remove arquivos que o framework deixou de distribuir`.

### T014 — Restringir à plataforma corrente e manter o registro

- **Status:** done
- **Depends on:** T013
- **Files:**
  - modify: `src/aiadev/install_engine.py`
  - test: `tests/test_install_engine.py`
- **Spec scenarios:** Story 6 scenario 1
- **Acceptance:**
  - [ ] Teste vermelho: instalar `cursor` depois de `claude-code` **não** remove `.claude/**` nem `CLAUDE.md`.
  - [ ] O registro do preset mantém as entradas fora das raízes da plataforma corrente, deduplicadas por caminho com a nova vencendo; um `sync --platform claude-code` seguinte não acusa conflito.
  - [ ] Carry-over da revisão da T013: (a) normalizar `entry.path` uma vez no topo de `_split_previous` (chave de `handled` e de dedupe), porque um alias não normalizado de arquivo ainda distribuído (`./AGENTS.md`) num manifesto adulterado hoje cai em stale e é apagado dentro da raiz; teste com a entrada alias. (b) A contenção atual é "dentro de `install_root`", não "dentro das raízes do framework": a restrição desta task às raízes da plataforma corrente é o que limita o que um manifesto forjado pode aposentar (ex. `src/app.py`); teste com entrada forjada fora das raízes gerenciadas. (c) Fundir o carry-over por escopo de usuário (hoje baseado em role) com o carry-over por raízes, em vez de manter dois mecanismos.
  - [ ] Commit message: `fix(install): T014 remoção restrita à plataforma corrente`.

### T015 — Dono compartilhado e DRY_RUN em memória

- **Status:** done
- **Depends on:** T014
- **Files:**
  - modify: `src/aiadev/install_engine.py`
  - modify: `src/aiadev/commands/sync.py`
  - test: `tests/test_install_engine.py`
- **Spec scenarios:** Story 6 scenario 1
- **Acceptance:**
  - [ ] Teste vermelho: caminho ainda registrado por outro preset não é removido; em `DRY_RUN` com dois presets o relatório de remoções é igual ao da execução real.
  - [ ] `.mcp.json` nunca entra em remoção.
  - [ ] Commit message: `feat(install): T015 dono compartilhado e dry-run fiel`.

### T016 — sync agrega e imprime removed e preserved

- **Status:** done
- **Depends on:** T015
- **Files:**
  - modify: `src/aiadev/commands/sync.py`
  - modify: `src/aiadev/commands/install.py`
  - test: `tests/test_sync_removal.py`
- **Spec scenarios:** Story 6 scenario 1
- **Acceptance:**
  - [ ] Teste vermelho: `aiadev sync` lista removidos e preservados, e sai com 0 quando só há preservados.
  - [ ] Carry-over da T013: `aiadev install` (`commands/install.py` ~:281-286) renderiza `removed` mas não `preserved`, e o seu gate "nothing to do" ignora `preserved`, então um órfão editado fica silencioso; renderizar `preserved` lá também e contá-lo no gate.
  - [ ] Um arquivo editado à mão é preservado na saída.
  - [ ] Commit message: `feat(sync): T016 relatório de arquivos removidos e preservados`.

**Fase 3 — Fluxo e revisão (stories P1)**

### T017 — spec_coverage: parser de referências

- **Status:** done
- **Depends on:** —
- **Files:**
  - create: `src/aiadev/spec_coverage.py`
  - test: `tests/test_spec_coverage.py`
- **Spec scenarios:** Story 2 scenario 3
- **Acceptance:**
  - [ ] Teste vermelho: reconhece `Story N scenario M`, `scenario M, scenario K`, `scenarios M, K`, intervalo `M–K`, legado `scM`, `**Story N scM**`, várias stories separadas por `;`, `Story N` sozinha e `Success criterion #N`.
  - [ ] "—" sem critério é reportado como sem referência.
  - [ ] Commit message: `feat(coverage): T017 parser de referências a cenários`.

### T018 — spec_coverage: checagem de cobertura

- **Status:** done
- **Depends on:** T017
- **Files:**
  - modify: `src/aiadev/spec_coverage.py`
  - test: `tests/test_spec_coverage.py`
- **Spec scenarios:** Story 2 scenario 3
- **Acceptance:**
  - [ ] Teste vermelho: recebe `spec_path` e `tasks_path`; cenário que nenhuma task cita (nem pela story) e task sem cenário, story nem critério nomeado são erros; citar uma story cobre seus cenários.
  - [ ] Não usa `branch_dir_for_workspace`.
  - [ ] Commit message: `feat(coverage): T018 cobertura cenário→task`.

### T019 — task_context reutiliza o parser

- **Status:** done
- **Depends on:** T018
- **Files:**
  - modify: `src/aiadev/task_context.py`
  - test: `tests/test_task_context.py`
- **Spec scenarios:** Story 2 scenario 3
- **Acceptance:**
  - [ ] Teste vermelho: `**Spec scenarios:** Story 1 scenario 1, scenario 2` produz o recorte correto (hoje devolve "Could not parse"); duas stories na linha produzem as duas.
  - [ ] Os testes existentes de `task_context` seguem verdes.
  - [ ] Commit message: `fix(task-context): T019 notação de cenário do template`.

### T020 — Medir a cobertura nas specs existentes

- **Status:** done
- **Depends on:** T018
- **Files:**
  - create: `docs/coverage-baseline.md`
  - test: `tests/test_spec_coverage.py`
- **Spec scenarios:** Success criterion #4
- **Acceptance:**
  - [ ] Teste vermelho: roda `check` sobre cada `specs/*/` com `spec.md` e `tasks.md` e compara com a lista de exceções versionada (feature → motivo).
  - [ ] `docs/coverage-baseline.md` registra quantas features passam e por que as demais não.
  - [ ] Commit message: `test(coverage): T020 baseline de cobertura das specs existentes`.

### T021 — Notação canônica em template e skill tasks

- **Status:** done
- **Depends on:** T018
- **Files:**
  - modify: `templates/tasks-template.md`
  - modify: `skills/tasks/SKILL.md`
  - test: `tests/test_tasks_template_constraints.py`
- **Spec scenarios:** Story 2 scenario 3
- **Acceptance:**
  - [ ] Teste vermelho: o template documenta a notação canônica e `Success criterion #N` para tasks de infra; a skill manda rodar o preflight de cobertura em vez de "grep to verify".
  - [ ] A skill cita literalmente restrições do data-model nas tasks (tamanho, enum, nulidade).
  - [ ] Commit message: `docs(tasks): T021 notação canônica de cobertura`.

### T022 — Preflight implement: cobertura como erro

- **Status:** done
- **Depends on:** T018, T020
- **Files:**
  - modify: `src/aiadev/preflight.py`
  - test: `tests/test_preflight_requirements_coverage.py`
- **Spec scenarios:** Story 2 scenario 3
- **Acceptance:**
  - [ ] Teste vermelho: cenário sem task faz `preflight implement` falhar apontando o cenário; task órfã idem.
  - [ ] `AIADEV_PREFLIGHT=warn` rebaixa para aviso; features na lista de exceções de T020 passam.
  - [ ] Commit message: `feat(preflight): T022 cobertura cenário→task no implement`.

### T023 — Preflight implement: gate de checklists

- **Status:** done
- **Depends on:** T022
- **Files:**
  - modify: `src/aiadev/preflight.py`
  - modify: `templates/checklist-template.md`
  - test: `tests/test_preflight_checklists.py`
- **Spec scenarios:** Story 2 scenario 4
- **Acceptance:**
  - [ ] Teste vermelho: linha FAIL na tabela de checks sem linha correspondente (`#`) na tabela de falhas com "Owner task" existente em `tasks.md` bloqueia e lista a linha; a linha placeholder `PASS / FAIL / N/A` é ignorada.
  - [ ] Sem `checklists/` o gate não se aplica.
  - [ ] Commit message: `feat(preflight): T023 bloqueio por checklist FAIL sem task dona`.

### T024 — Preflight com saída JSON

- **Status:** done
- **Depends on:** —
- **Files:**
  - modify: `src/aiadev/preflight.py`
  - modify: `src/aiadev/commands/preflight.py`
  - test: `tests/test_preflight_pipeline.py`
- **Spec scenarios:** Story 2 scenario 1
- **Acceptance:**
  - [ ] Teste vermelho: `--format json` devolve `skill`, `feature`, `feature_dir`, `ok`, `issues[]`, `docs{spec,plan,tasks,checklists}` e `template` no stdout; stderr silencioso; exit 1 se algum issue aborta.
  - [ ] O modo texto não muda.
  - [ ] Commit message: `feat(preflight): T024 --format json com contexto da feature`.

### T025 — test_command no payload do preflight

- **Status:** done
- **Depends on:** T024
- **Files:**
  - modify: `src/aiadev/preflight.py`
  - test: `tests/test_preflight_pipeline.py`
- **Spec scenarios:** Story 2 scenario 1
- **Acceptance:**
  - [ ] Teste vermelho: projeto Node com script `test` devolve o comando; projeto sem comando detectável devolve `null`.
  - [ ] A detecção reutiliza `project_introspect` sem estendê-la.
  - [ ] Commit message: `feat(preflight): T025 test_command detectado no payload`.

### T026 — tasks_status: escrita atômica e retorno a pending

- **Status:** done
- **Depends on:** —
- **Files:**
  - modify: `src/aiadev/tasks_status.py`
  - test: `tests/test_tasks_status.py`
- **Spec scenarios:** Story 2 scenario 2
- **Acceptance:**
  - [ ] Teste vermelho: `mark_done` grava por arquivo temporário e `os.replace` (falha no meio não corrompe `tasks.md`); nova função reverte uma task para `pending` mexendo só na linha de status.
  - [ ] Idempotência de `mark_done` preservada.
  - [ ] Commit message: `fix(tasks): T026 escrita atômica e reversão de status`.

### T027 — aiadev tasks done

- **Status:** done
- **Depends on:** T026
- **Files:**
  - create: `src/aiadev/commands/tasks.py`
  - modify: `src/aiadev/cli.py`
  - test: `tests/test_tasks_done_command.py`
- **Spec scenarios:** Story 2 scenario 2
- **Acceptance:**
  - [ ] Teste vermelho (repo git real em tmp): `aiadev tasks done T001 --feature <slug> --commit "<msg>" FILES...` marca `done`, faz `git add` dos arquivos e de `tasks.md` e comita.
  - [ ] Commit que falha: o status volta a `pending` na linha e o `done` sai do índice (`git restore --staged tasks.md`), sem `checkout --` e sem tocar em outras edições.
  - [ ] Commit message: `feat(tasks): T027 aiadev tasks done com commit e rollback`.

### T028 — pipeline_state: feature, prefixo e review.yaml

- **Status:** done
- **Depends on:** —
- **Files:**
  - modify: `src/aiadev/pipeline_state.py`
  - test: `tests/test_pipeline_state.py`
  - create: `tests/fixtures/pipeline_state/review_yaml_stale/`
- **Spec scenarios:** Story 2 scenario 5
- **Acceptance:**
  - [ ] Teste vermelho: `recommend_next_command(feature=<slug>)` escolhe a spec pelo slug; comandos usam `/aia:`; slug sem diretório devolve `/aia:specify` com motivo.
  - [ ] "Revisão aprovada" exige `review.yaml` aprovado com `timestamp` (datetime parseado) não anterior à última entrada do log; um `review.yaml` antigo não leva a `finishing-a-branch`.
  - [ ] `plain` e `AIADEV_HELP_PLAIN` removidos.
  - [ ] Commit message: `feat(next): T028 estado por feature e revisão de branch`.

### T029 — aiadev next

- **Status:** done
- **Depends on:** T028
- **Files:**
  - create: `src/aiadev/commands/next.py`
  - modify: `src/aiadev/cli.py`
  - test: `tests/test_next_command.py`
- **Spec scenarios:** Story 2 scenario 5
- **Acceptance:**
  - [ ] Teste vermelho: `aiadev next --feature <slug>` imprime estado (spec, marcadores abertos, plano, tasks pendentes) e a próxima etapa; sem spec, a próxima etapa é `/aia:specify`; exit 0.
  - [ ] Leva ≤ 200 ms nas fixtures (orçamento do teste de `pipeline_state`).
  - [ ] Commit message: `feat(next): T029 comando aiadev next`.

### T030 — Reescrever testes de prosa de implement/review como comportamento

- **Status:** done
- **Depends on:** —
- **Files:**
  - modify: `tests/test_implement_skill_drift.py`
  - modify: `tests/test_review_redispatch_skills.py`
  - modify: `tests/test_zero_findings_halt_agents.py`
- **Spec scenarios:** Success criterion #6
- **Acceptance:**
  - [ ] Os três testes passam a asserir comportamento (gate presente, status atômico e rollback descritos, regra de "Why no issues" nos agents) sem fixar a posição nem a prosa literal da seção do loop; continuam verdes sobre o texto atual.
  - [ ] Commit message: `test(skills): T030 testes de prosa de implement e review como comportamento`.

### T031 — implement: preflight JSON, tasks done e revisão única

- **Status:** done
- **Depends on:** T009, T024, T027, T030
- **Files:**
  - modify: `skills/implement/SKILL.md`
  - test: `tests/test_implement_skill_drift.py`
- **Spec scenarios:** Story 3 scenario 1, scenario 4; Success criterion #3
- **Acceptance:**
  - [ ] Teste vermelho: o loop manda emitir preflight (`--format json`) e leituras em paralelo, fechar task com `aiadev tasks done` (caminho manual como fallback) e despachar **um** reviewer por task.
  - [ ] O "final full-branch review" sai do `implement`; o orçamento de T009 não é excedido.
  - [ ] Commit message: `feat(implement): T031 fluxo com tasks done e revisão única`.

### T032 — Reviewer único: checklists em sequência e log

- **Status:** done
- **Depends on:** T030
- **Files:**
  - modify: `skills/implement/SKILL.md`
  - modify: `agents/code-reviewer.md`
  - test: `tests/test_review_redispatch_skills.py`
- **Spec scenarios:** Story 3 scenario 1, scenario 3, scenario 5
- **Acceptance:**
  - [ ] Teste vermelho: o prompt combina conformidade e qualidade em sequência e **para** com achados de conformidade, sem rodar qualidade; recebe diff e saída dos testes.
  - [ ] O veredito é gravado no review-log com `reviewer: code-reviewer` e `APPROVED`/`CHANGES_REQUESTED`; `aiadev metrics` continua contando retrabalho (teste sobre log sintético).
  - [ ] Os dois limites de iteração existentes permanecem.
  - [ ] Commit message: `feat(review): T032 reviewer único por task`.

### T033 — Tier de auto-verificação para prosa

- **Status:** done
- **Depends on:** T032
- **Files:**
  - modify: `skills/implement/SKILL.md`
  - test: `tests/test_implement_skill_drift.py`
- **Spec scenarios:** Story 3 scenario 2
- **Acceptance:**
  - [ ] Teste vermelho: a skill define o tier (só markdown de prosa sob `docs/` ou documentação raiz) com lint de markdown e validador do repositório, sem dispatch.
  - [ ] `docs/instruction-budget.json` e `docs/pipeline-path.yaml` ficam explicitamente fora do tier.
  - [ ] Commit message: `feat(implement): T033 auto-verificação de tasks de prosa`.

### T034 — requesting-code-review: sem review-context.md

- **Status:** done
- **Depends on:** T009, T030
- **Files:**
  - modify: `skills/requesting-code-review/SKILL.md`
  - test: `tests/test_provider_followups.py`
  - test: `tests/test_review_redispatch_skills.py`
- **Spec scenarios:** Story 3 scenario 4
- **Acceptance:**
  - [ ] Teste vermelho: a skill não cria `review-context.md`; passa ao reviewer caminhos e ref base; a seção "Impacted subsystems" é acrescentada ao prompt do reviewer, mantendo as palavras que o teste fixa.
  - [ ] É o único review de branch e grava `.aiadev/review.yaml`.
  - [ ] Commit message: `feat(review): T034 review de branch sem review-context.md`.

### T035 — Convenção de descrição do dispatch

- **Status:** done
- **Depends on:** T031, T034
- **Files:**
  - modify: `skills/implement/SKILL.md`
  - modify: `skills/requesting-code-review/SKILL.md`
  - test: `tests/test_dispatch_description_convention.py`
- **Spec scenarios:** Story 1 scenario 2
- **Acceptance:**
  - [ ] Teste vermelho: `implement` manda `description` com prefixo `implement:` e `review:`; `requesting-code-review` com `review: branch`.
  - [ ] Reviewers de documento de `specify` e `plan` ficam fora, e a medição os conta como não classificados.
  - [ ] Commit message: `docs(skills): T035 convenção de descrição do dispatch`.

**Fase 4 — Texto: divulgação progressiva, stack e triagem (P2)**

### T036 — Gate de re-dispatch em um arquivo canônico

- **Status:** pending
- **Depends on:** T011, T031, T034
- **Files:**
  - create: `skills/requesting-code-review/references/review-gate.md`
  - modify: `skills/implement/SKILL.md`
  - modify: `skills/requesting-code-review/SKILL.md`
  - modify: `agents/code-reviewer.md`
  - modify: `agents/plan-document-reviewer.md`
  - modify: `agents/spec-document-reviewer.md`
  - test: `tests/test_review_redispatch_skills.py`
- **Spec scenarios:** Story 4 scenario 3
- **Acceptance:**
  - [ ] Teste vermelho: o texto do gate existe só em `references/review-gate.md`; `implement`, `requesting-code-review` e os agents o referenciam.
  - [ ] O percurso medido por T008 passa a contar o arquivo (baseline não excedido).
  - [ ] Commit message: `refactor(review): T036 gate de re-dispatch em um arquivo`.

### T037 — Teste de task-context como comportamento

- **Status:** done
- **Depends on:** —
- **Files:**
  - modify: `tests/test_implement_task_context_integration.py`
- **Spec scenarios:** Story 4 scenario 3
- **Acceptance:**
  - [ ] O teste passa a asserir que a integração está descrita em algum arquivo referenciado pelo `implement` (não necessariamente no `SKILL.md`) e que a flag `task_context: true` e `--task-context` seguem documentadas; continua verde sobre o texto atual.
  - [ ] Commit message: `test(implement): T037 integração de task-context como comportamento`.

### T038 — implement em núcleo mais references/task-context.md

- **Status:** pending
- **Depends on:** T011, T036, T037
- **Files:**
  - create: `skills/implement/references/task-context.md`
  - modify: `skills/implement/SKILL.md`
  - test: `tests/test_implement_task_context_integration.py`
- **Spec scenarios:** Story 4 scenario 3
- **Acceptance:**
  - [ ] Teste vermelho: o `SKILL.md` carregado por padrão não contém a seção de integração com task-context; ela vive em `references/task-context.md`, lida só quando a integração está ligada.
  - [ ] `skills/implement/SKILL.md` ≤ 1.500 tokens estimados; o teto de T009 é rebaixado com `reason`.
  - [ ] Commit message: `refactor(implement): T038 núcleo curto e task-context em references`.

### T039 — Stack para os presets (references/stack.md)

- **Status:** pending
- **Depends on:** T011
- **Files:**
  - create: `presets/django-drf-react/skills/test-driven-development/references/stack.md`
  - create: `presets/django-drf-react/skills/systematic-debugging/references/stack.md`
  - create: `presets/django-drf-react/skills/finishing-a-branch/references/stack.md`
  - create: `presets/django-drf-react/skills/requesting-code-review/references/stack.md`
  - create: `presets/django-drf-react/skills/plan/references/stack.md`
  - modify: `skills/test-driven-development/SKILL.md`
  - modify: `skills/systematic-debugging/SKILL.md`
  - modify: `skills/finishing-a-branch/SKILL.md`
  - modify: `skills/requesting-code-review/SKILL.md`
  - modify: `skills/plan/SKILL.md`
  - test: `tests/test_stack_in_preset.py`
- **Spec scenarios:** Story 4 scenario 1, scenario 2
- **Acceptance:**
  - [ ] Teste vermelho: o preset instalado traz os cinco `references/stack.md`; cada skill genérica tem a linha "se `references/stack.md` existir ao lado, leia-o" e nenhuma menção de stack.
  - [ ] O corpo genérico de cada skill aparece uma vez no projeto instalado.
  - [ ] Commit message: `refactor(skills): T039 stack movido para o preset`.

### T040 — Agents sem stack

- **Status:** pending
- **Depends on:** T039
- **Files:**
  - modify: `agents/code-reviewer.md`
  - modify: `agents/plan-document-reviewer.md`
  - test: `tests/test_stack_in_preset.py`
- **Spec scenarios:** Story 4 scenario 1
- **Acceptance:**
  - [ ] Teste vermelho: `code-reviewer` (persona da linha 10, §3–5 e menção a Celery) e `plan-document-reviewer` (§7) não têm as palavras de stack e mandam ler, se existir, o `references/stack.md` de `requesting-code-review` e `plan`.
  - [ ] Commit message: `refactor(agents): T040 reviewers sem stack`.

### T041 — frontend-design vai para o preset

- **Status:** pending
- **Depends on:** T039
- **Files:**
  - modify: `presets/django-drf-react/preset.yaml`
  - modify: `presets/django-drf-react/CLAUDE.md`
  - modify: `presets/lean/CLAUDE.md`
  - modify: `rules/slash-commands.md`
  - modify: `CLAUDE.md`
  - modify: `docs/pipeline-reference.md`
  - test: `tests/test_pipeline_reference_drift.py`
- **Spec scenarios:** Story 4 scenario 1
- **Acceptance:**
  - [ ] Teste vermelho: `skills/frontend-design/` e `commands/frontend-design.md` passam para `presets/django-drf-react/{skills,commands}/`; `provides.skills` e a lista do `CLAUDE.md` do preset os incluem; `lean` não lista a skill.
  - [ ] A linha de `CLAUDE.md:24` indica o preset; `docs/pipeline-reference.md` regenerado (≤ 24 linhas) e sem drift.
  - [ ] Commit message: `refactor(presets): T041 frontend-design no preset django-drf-react`.

### T042 — Teste "lean sem palavras de stack"

- **Status:** pending
- **Depends on:** T040, T041
- **Files:**
  - create: `tests/test_lean_has_no_stack.py`
- **Spec scenarios:** Story 4 scenario 1; Success criterion #7
- **Acceptance:**
  - [ ] Guarda de regressão: instala `lean` num tmp e falha se skills ou agents contêm, como palavra inteira sem diferenciar maiúsculas, Django, Celery, DRF, React, MUI ou Expo, nem `manage.py`, `select_related` ou `on_commit`.
  - [ ] Evidência de vermelho (Art. II): antes de iniciar T039, rodar este teste contra `main` (worktree) e colar a saída falhando no commit; depois de T041 ele passa.
  - [ ] Commit message: `test(presets): T042 lean sem conteúdo de stack`.

### T043 — rules: paths e slash-commands curto

- **Status:** done
- **Depends on:** T009
- **Files:**
  - modify: `rules/api-conventions.md`
  - modify: `rules/slash-commands.md`
  - test: `tests/test_rules_content.py`
- **Spec scenarios:** Success criterion #2
- **Acceptance:**
  - [ ] Teste vermelho: `api-conventions` tem `paths:` (deixa de ser sempre carregada) e `slash-commands` cabe em duas linhas; o inventário de `test_rules_content` é atualizado.
  - [ ] O sempre-carregado medido do `lean` diminui em relação ao baseline.
  - [ ] Commit message: `refactor(rules): T043 api-conventions com paths e slash-commands curto`.

### T044 — specify: teto de marcadores e Assumptions

- **Status:** pending
- **Depends on:** T009
- **Files:**
  - modify: `skills/specify/SKILL.md`
  - modify: `templates/spec-template.md`
  - test: `tests/test_specify_skill_has_recon_step.py`
  - test: `tests/test_spec_template_has_recon_anchor.py`
- **Spec scenarios:** Story 5 scenario 1
- **Acceptance:**
  - [ ] Teste vermelho: a skill limita a 3 marcadores (escopo, segurança, UX primeiro) e manda as demais incógnitas para `## Assumptions`; o template ganha a seção, sem comentários HTML redundantes e sem "Constitution Check (preliminar)".
  - [ ] As frases do reconhecimento seguem presentes.
  - [ ] Commit message: `feat(specify): T044 teto de marcadores e Assumptions`.

### T045 — Preflight: Assumptions opcional

- **Status:** pending
- **Depends on:** T044
- **Files:**
  - modify: `src/aiadev/preflight.py`
  - test: `tests/test_preflight_requirements_coverage.py`
- **Spec scenarios:** Story 5 scenario 1, scenario 2
- **Acceptance:**
  - [ ] Teste vermelho: spec sem `## Assumptions` continua válida (specs existentes e a própria 0030); com a seção presente, premissa vazia ou sem marcador de impacto é apontada.
  - [ ] `SPEC_ANCHORS` não ganha a âncora.
  - [ ] Commit message: `feat(preflight): T045 Assumptions opcional e validada quando presente`.

### T046 — spec-document-reviewer: critério de premissas

- **Status:** pending
- **Depends on:** T044
- **Files:**
  - modify: `agents/spec-document-reviewer.md`
  - test: `tests/test_spec_document_reviewer_assumptions.py`
- **Spec scenarios:** Story 5 scenario 2
- **Acceptance:**
  - [ ] Teste vermelho: o agente verifica que cada premissa é de baixo impacto e reversível e reprova a que decide escopo ou segurança.
  - [ ] Commit message: `feat(agents): T046 critério de premissas no spec-document-reviewer`.

### T047 — clarify: teto e uma pergunta por vez

- **Status:** done
- **Depends on:** T009
- **Files:**
  - modify: `skills/clarify/SKILL.md`
  - test: `tests/test_clarify_skill_triage.py`
- **Spec scenarios:** Story 5 scenario 3
- **Acceptance:**
  - [ ] Teste vermelho: a skill limita a 5 perguntas, uma por vez, ordenadas por impacto e incerteza, cada uma com recomendação aceitável com uma palavra; o excedente vira premissa.
  - [ ] Commit message: `feat(clarify): T047 teto de 5 perguntas com recomendação`.

### T048 — Skills restantes enxutas e gates canônicos

- **Status:** pending
- **Depends on:** T036, T038
- **Files:**
  - modify: `skills/product/SKILL.md`
  - modify: `skills/plan/SKILL.md`
  - modify: `skills/tasks/SKILL.md`
  - modify: `skills/constitution/SKILL.md`
  - modify: `skills/finishing-a-branch/SKILL.md`
  - modify: `skills/systematic-debugging/SKILL.md`
  - modify: `skills/test-driven-development/SKILL.md`
  - create: `tests/test_gates_canonical.py`
  - test: `tests/test_product_skill.py`
- **Spec scenarios:** Success criterion #6
- **Acceptance:**
  - [ ] Teste vermelho: cada gate da tabela D13 do plano tem a frase-chave no arquivo canônico (RED por razão certa, Constitution Check com evidência, causa-raiz e 3 falhas, exclusão de secretos, `review.yaml` antes do PR).
  - [ ] Os testes que fixam seções (`test_product_skill`, `test_provider_followups`) seguem verdes; nenhum teto de T009 excedido.
  - [ ] Commit message: `refactor(skills): T048 skills enxutas com gates canônicos`.

### T049 — Checklist sem todas as categorias

- **Status:** done
- **Depends on:** T023
- **Files:**
  - modify: `templates/checklist-template.md`
  - modify: `skills/checklist/SKILL.md`
  - test: `tests/test_token_economy_checklist.py`
- **Spec scenarios:** Story 2 scenario 4
- **Acceptance:**
  - [ ] Teste vermelho: o template carrega só a categoria pedida e mantém a coluna "Owner task" que o gate de T023 lê.
  - [ ] Commit message: `refactor(checklist): T049 template só com a categoria pedida`.

**Fase 5 — Remoções e migração (P2)**

### T050 — Remover o terse-mode (código, rule, schema, agents, testes)

- **Status:** pending
- **Depends on:** T009
- **Files:**
  - modify: `rules/terse-mode.md` (removed)
  - modify: `schemas/terse-output.schema.json` (removed)
  - modify: `src/aiadev/config.py` (removed)
  - modify: `agents/code-reviewer.md`
  - modify: `agents/plan-document-reviewer.md`
  - modify: `agents/spec-document-reviewer.md`
  - modify: `tests/test_off_mode_unchanged.py` (removed)
  - test: `tests/test_rules_content.py`
- **Spec scenarios:** Story 6 scenario 2
- **Acceptance:**
  - [ ] Os testes só do terse (`test_terse_mode_rule`, `test_terse_mode_config`, `test_terse_output_schema`, `test_agents_have_terse_block`, `test_off_mode_unchanged` e `tests/fixtures/off_mode/`) saem; o inventário de rules é atualizado.
  - [ ] Os agents mantêm a regra "APPROVED em mudança não trivial" e perdem só o bloco terse.
  - [ ] Commit message: `refactor(terse): T050 remove o terse-mode`.

### T051 — terse-mode: referências restantes

- **Status:** pending
- **Depends on:** T050
- **Files:**
  - modify: `templates/checklist-template.md`
  - modify: `docs/token-economy.md`
  - modify: `CREDITS.md`
  - modify: `skills/implement/SKILL.md`
  - modify: `skills/requesting-code-review/SKILL.md`
  - test: `tests/test_token_economy_checklist.py`
  - test: `tests/test_credits_attribution.py`
  - test: `tests/test_existing_validators_regress.py`
  - test: `tests/test_sync_ships_terse_assets.py`
- **Spec scenarios:** Story 6 scenario 2
- **Acceptance:**
  - [ ] Teste vermelho: nenhuma referência a `AIADEV_TERSE` ou `aiadev.terseMode` fora do `CHANGELOG.md` e do aviso do `sync`; `CREDITS.md` mantém o caveman com nota "removido na 0030".
  - [ ] `test_existing_validators_regress` perde o parametrize terse; `test_sync_ships_terse_assets` mantém só o teste genérico de caminhos.
  - [ ] Commit message: `docs(terse): T051 referências remanescentes ao terse-mode`.

### T052 — sync: aviso da chave e variável antigas

- **Status:** pending
- **Depends on:** T016, T050
- **Files:**
  - modify: `src/aiadev/commands/sync.py`
  - test: `tests/test_sync_terse_notice.py`
- **Spec scenarios:** Story 6 scenario 2
- **Acceptance:**
  - [ ] Teste vermelho: `aiadev.terseMode` em `.claude/settings.json` ou `AIADEV_TERSE` no ambiente produz uma linha de aviso no relatório do `sync` e é ignorado.
  - [ ] Sem a chave e sem a variável não há aviso.
  - [ ] Commit message: `feat(sync): T052 aviso do terse-mode removido`.

### T053 — Remover help e using-ai-augmented-developer

- **Status:** pending
- **Depends on:** T029
- **Files:**
  - modify: `skills/help/SKILL.md` (removed)
  - modify: `skills/using-ai-augmented-developer/SKILL.md` (removed)
  - modify: `commands/using-ai-augmented-developer.md` (removed)
  - create: `docs/gemini-tools.md`
  - modify: `GEMINI.md`
  - test: `tests/test_help_skill.py` (removed)
  - test: `tests/test_help_skill_state_aware.py` (removed)
  - test: `tests/test_using_aia_mentions_recon.py` (removed)
- **Spec scenarios:** Story 6 scenario 3
- **Acceptance:**
  - [ ] `gemini-tools.md` é realocado para `docs/gemini-tools.md` com o mesmo conteúdo e o `GEMINI.md` o importa de lá, não de `skills/`.
  - [ ] Teste vermelho: o `GEMINI.md` não importa mais `skills/using-ai-augmented-developer/`; `aiadev sync` remove as skills e comandos antigos (T013) sem tocar em arquivos editados.
  - [ ] Commit message: `refactor(skills): T053 remove help e using-ai-augmented-developer`.

### T054 — Repontar documentação e regenerar a referência

- **Status:** pending
- **Depends on:** T053
- **Files:**
  - modify: `CLAUDE.md`
  - modify: `README.md`
  - modify: `CONTRIBUTING.md`
  - modify: `.pre-commit-config.yaml`
  - modify: `templates/roadmap-template.md`
  - modify: `docs/README.codex.md`
  - modify: `presets/lean/CLAUDE.md`
  - modify: `scripts/generate_pipeline_reference.py`
  - modify: `docs/pipeline-reference.md`
  - test: `tests/test_claude_md_pointer.py`
  - test: `tests/test_generate_pipeline_reference.py`
  - test: `tests/test_pipeline_reference_drift.py`
  - test: `tests/test_product_registries.py`
- **Spec scenarios:** Story 6 scenario 3, scenario 4
- **Acceptance:**
  - [ ] Teste vermelho: `/aia:help` é substituído por `aiadev next` nos documentos citados; `PIPELINE` do gerador não lista `help`; `docs/pipeline-reference.md` é regenerado byte a byte, com ≤ 24 linhas.
  - [ ] `docs/README.codex.md` aponta o bloco equivalente do `AGENTS.md` gerado (a partir de `templates/agent-file-template.md`); as contagens de `presets/lean/CLAUDE.md` batem com o instalado.
  - [ ] Commit message: `docs: T054 pontos de entrada sem help e using-aia`.

### T055 — Teste de referências sem substituto

- **Status:** pending
- **Depends on:** T054
- **Files:**
  - create: `tests/test_no_dangling_removed_refs.py`
- **Spec scenarios:** Story 6 scenario 4
- **Acceptance:**
  - [ ] Guarda de regressão: nenhum documento do repositório referencia `/aia:help`, a skill removida ou `skills/using-ai-augmented-developer` sem substituto declarado.
  - [ ] Exceções explícitas: `CHANGELOG.md` e `specs/**`.
  - [ ] Evidência de vermelho (Art. II): antes de iniciar T053, rodar este teste contra `main` (worktree) e colar a saída falhando no commit; depois de T054 ele passa.
  - [ ] Commit message: `test(docs): T055 guarda contra referências a recursos removidos`.

### T056 — Verificar a meta de 40% e rebaixar o baseline

- **Status:** pending
- **Depends on:** T038, T043, T048, T049, T051, T055
- **Files:**
  - modify: `docs/instruction-budget.json`
  - modify: `scripts/instruction_budget.py`
  - test: `tests/test_instruction_budget.py`
- **Spec scenarios:** Story 4 scenario 4; Success criterion #2
- **Acceptance:**
  - [ ] Teste vermelho: a redução do sempre-carregado do `lean` e do percurso contra o baseline de T009 é ≥ 40% (verificada uma vez e registrada); se não for, a task falha e as sobras são listadas.
  - [ ] Só depois o baseline é rebaixado para a medida pós-corte, com `reason`.
  - [ ] Commit message: `chore(budget): T056 meta de 40% verificada e baseline rebaixado`.

**Fase 6 — Benchmark e fechamento**

### T057 — Harness e protocolo do benchmark

- **Status:** pending
- **Depends on:** T005, T035
- **Files:**
  - create: `docs/benchmark-0030.md`
  - create: `scripts/benchmark_pairs.py`
  - test: `tests/test_benchmark_pairs.py`
- **Spec scenarios:** Success criterion #8
- **Acceptance:**
  - [ ] Teste vermelho: dada uma lista de pares com os ids das sessões, o script soma o custo equivalente por feature (todas as sessões entre o primeiro e o último commit), calcula a mediana da razão depois/antes e a variação da aprovação de primeira agregada, e aplica a regra da spec (mediana < 1,0 e queda ≤ 5 pontos percentuais).
  - [ ] O protocolo (mesma micro-feature, ordem alternada, ≥ 5 pares) está em `docs/benchmark-0030.md`.
  - [ ] Commit message: `feat(benchmark): T057 harness de pares antes/depois`.

### T058 — Executar os pares e registrar o resultado

- **Status:** pending
- **Depends on:** T056, T057
- **Files:**
  - modify: `docs/benchmark-0030.md`
- **Spec scenarios:** Success criterion #8
- **Acceptance:**
  - [ ] ≥ 5 pares executados no Claude Code; o relatório lista ids de sessão, custo por par, mediana, aprovação de primeira e o veredito pela regra da spec, com os comandos usados.
  - [ ] Se a regra reprovar, o resultado e a reversão sugerida (dois reviewers) ficam registrados, sem mascarar.
  - [ ] Commit message: `docs(benchmark): T058 resultado dos pares antes/depois`.

### T059 — CHANGELOG, CREDITS, manifests e versão

- **Status:** pending
- **Depends on:** T058
- **Files:**
  - modify: `CHANGELOG.md`
  - modify: `CREDITS.md`
  - modify: `VERSION`
  - modify: `.claude-plugin/plugin.json`
  - modify: `.claude-plugin/marketplace.json`
  - modify: `.cursor-plugin/plugin.json`
  - test: `tests/test_credits_attribution.py`
  - test: `tests/test_manifests_in_sync.py`
- **Spec scenarios:** Success criterion #8
- **Acceptance:**
  - [ ] `CHANGELOG.md [Unreleased]` com Added, Changed e Removed, nota de quebra para `lean` e o Spec ID 0030; `CREDITS.md` registra os mecanismos adaptados do spec-kit.
  - [ ] `aiadev manifests --write` regrava os três manifests; `aiadev manifests --check` passa; `VERSION` sobe um minor.
  - [ ] Commit message: `chore(release): T059 changelog, credits e manifests da 0030`.

## Parallelization hints

<!-- Tasks que não compartilham arquivos podem ser tentadas em paralelo se a plataforma suportar. -->

- Parallel group A (fase 1): T001–T006 (token_metrics) e T007–T009 (scripts/docs) — arquivos disjuntos; T006 só depende de T001.
- Parallel group B (fase 3): T026–T027 (tasks_status), T028–T029 (pipeline_state) e T017–T019 (spec_coverage) — disjuntos entre si; T022–T025 compartilham `preflight.py` e são seriais.
- Parallel group C (fase 4): T044–T047 (specify/clarify/reviewer) e T039–T042 (stack) — disjuntos.
- Serial: tudo que toca `src/aiadev/install_engine.py` (T010–T016), `skills/implement/SKILL.md` (T031, T033, T036, T038) e `skills/requesting-code-review/SKILL.md` (T034, T035, T036, T039).

## Post-task checklist

After every task:

- [ ] Commit message references the task id.
- [ ] Status in this file updated (`aiadev tasks done` a partir da T027).

After all tasks:

- [ ] Full test suite passes (`PYTHONPATH=src python3 -m pytest -q`; no CI, `pytest --cov=src/aiadev --cov-fail-under=80`).
- [ ] `python3 scripts/instruction_budget.py` passa contra o baseline rebaixado.
- [ ] `analyze` skill runs and reports no drift vs spec / plan.
- [ ] Hand off to `requesting-code-review` to open the PR.
