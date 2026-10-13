# Implementation plan: pipeline enxuto — menos turnos, menos texto e medição correta de custo

> Produced by the `plan` skill from an approved `spec.md`. This file describes **how** the spec will be realized. Do not rewrite `spec.md` into `plan.md`.

**Branch:** `feature/0030-lean-pipeline`
**Date:** 2026-10-13
**Spec:** [spec.md](./spec.md)
**Plan version:** 2
**Language:** pt-BR <!-- mirrors spec.md; write plan prose in this language. -->

---

## Summary

Entregamos a spec em seis fases, cada uma mesclável sozinha, na ordem medição → motor → fluxo (CLI e prosa das stories P1) → texto (stack, triagem, progressive disclosure) → remoções → benchmark. A fase 1 conserta `aiadev metrics --tokens` e grava o baseline de instruções **antes** de qualquer corte; a fase 2 dá ao motor de instalação duas capacidades que o resto exige (instalar arquivos de apoio de uma skill e remover o que o framework deixou de distribuir); a fase 3 entrega os ganhos de turnos e a revisão única (todas as stories P1); as fases 4 e 5 enxugam texto e removem recursos (P2); a fase 6 prova o efeito. Previsão: ~50 tasks. Linha de corte combinada: se o ritmo não fechar, as fases 4–5 viram a spec seguinte; as fases 1–3 já cobrem todas as stories P1.

## Technical context

| Field | Value |
|---|---|
| Active preset | nenhum (repositório do próprio framework) |
| Language / runtime | Python ≥ 3.11 (matriz de CI 3.11 e 3.12); Markdown para skills |
| Primary dependencies | click, pyyaml (já em uso); nenhuma dependência nova |
| Storage | arquivos: `.aiadev/installed.yaml`, `tasks.md`, `docs/instruction-budget.json`, `docs/pipeline-path.yaml` |
| Testing framework | pytest (`CliRunner`, fixtures em `tests/fixtures/`), cobertura mínima 80% sobre `src/aiadev` (o `scripts/` fica fora) |
| Target platform(s) | Claude Code (benchmark); mesmas skills em Gemini, Codex, Cursor e OpenCode |
| Performance budget | `aiadev preflight` e `aiadev next` ≤ 200 ms (medido ~100–120 ms a frio; o teste de `pipeline_state` já pina 200 ms); medição de orçamento ≤ 10 s |
| Security considerations | a medição lê só transcripts locais; papel do subagente vem do `description` do `*.meta.json`, nunca de texto de mensagem; nenhum dado sai da máquina |

## Constitution check

| Article | Applies? | Status | Evidence |
|---|---|---|---|
| I. Spec-first | Yes | PASS | `spec.md` clarificada, 3 passadas do revisor, `aiadev preflight plan` com exit 0 (zero marcadores); a cobertura cenário→task é verificada em `tasks.md` na etapa `tasks` |
| II. Test-first | Yes | PASS | cada task abre com teste vermelho (verificado em `tasks.md`); tasks de texto usam teste de comportamento, não de prosa |
| III. Simplicity | Yes | PASS | cada abstração nova tem dois chamadores hoje: arquivos de apoio de skill no motor (`references/` **e** stack por preset), `spec_coverage` (preflight `implement` **e** `task_context`); uma flag nova, `--format json` no preflight (usuário: o orquestrador, Story 2 sc1; mesma forma de `metrics`/`learn`); nenhuma dependência nova; `tasks next` e `--format` em `aiadev next` ficaram de fora por não terem cenário |
| IV. Evidence over claims | Yes | PASS | meta de ≥ 40% e regra do benchmark verificadas na fase 5/6 com comandos no PR; medição conferida contra dedupe manual **com a mesma regra** (maior valor por campo e `message.id`) |
| V. Provider pattern | No | N/A | sem fronteira de rede: nada novo chama serviço externo |
| VI. Privacy by design | Yes | PASS | `read_session` continua sem ler corpo de `tool_result` (teste de privacidade existente mantido); papel do subagente só do campo `description` do `*.meta.json` |
| VII. Attribution | Yes | PASS (com task) | `CREDITS.md` ganha os mecanismos adaptados do spec-kit e a entrada do caveman é atualizada; `tests/test_credits_attribution.py` ajustado |
| Preset-specific articles | No | N/A | repositório do framework, sem preset ativo |

## Architecture decisions

**D1 — O motor passa a instalar arquivos de apoio de uma skill.**
Decision: em `src/aiadev/install_engine.py::_collect_artifacts`, além do `SKILL.md`, varrer `framework_root/skills/<n>/` e `preset_path/skills/<n>/` por `references/**/*.md` e instalá-los ao lado do `SKILL.md` instalado, com role `skill` e nome `<skill>/<caminho-relativo>`; alvo = `resolve_target("skill", <n>, root).parent / <rel>`. Só `*.md` dentro de `references/` (evita `.DS_Store` de checkouts).
Rationale: confirmado que nenhuma plataforma copia `references/` (cada handler só emite `SKILL.md`). Sem isso, mover seções para `references/` apaga o conteúdo nos projetos instalados. A mesma capacidade resolve o stack por preset sem substituir o `SKILL.md` genérico; o genérico ganha uma linha "se `references/stack.md` existir ao lado, leia-o". O wheel já empacota `references/` (`scripts/sync_assets.py` faz `copytree`; `pyproject.toml:68-69`).
Trade-offs: arquivos de preset passam por `substitute`/`find_unresolved` (`{{...}}` cru em `stack.md` falha; teste cobre). O manifesto aceita role `skill` por arquivo, schema inalterado. Cursor: `.mdc` só afeta role `rule`, então `.parent / rel` funciona.

**D2 — `install` e `sync` removem o que o framework deixou de distribuir, só na plataforma corrente.**
Decision: no fim do laço de `install()`, calcular `stale = previous_by_path − alvos esperados`, **restrito aos caminhos sob as raízes gerenciadas da plataforma corrente** (derivadas do próprio handler: skills, commands, agents, rules, wrapper); aplicar a regra de hash de `_perform_uninstall` (hash igual ao do manifesto → remove; diferente → preserva e lista como `preserved`, **sem** virar `conflicts`, exit 0, e sai do manifesto); `--force` nunca apaga arquivo editado (a regra vale em `install` e em `sync`, que chamam o mesmo `install()`); o registro do preset passa a manter as entradas anteriores fora das raízes da plataforma corrente (deduplicadas por caminho, com a entrada nova vencendo, p. ex. `AGENTS.md` e `constitution.md`), para que instalar outra plataforma não faça um `sync` posterior acusar conflito em tudo; respeitar `DRY_RUN` (o `sync` mantém o manifesto em memória entre presets, para o dono compartilhado ser lido sem registros salvos pela metade) e limpar diretórios vazios. `sync_command` agrega e imprime `removed` e `preserved`.
Rationale: `install()` regrava o registro do preset só com os `recorded_files` do run atual, então sem a restrição de plataforma `sync --platform cursor` apagaria `.claude/**`. Arquivos genéricos aparecem no registro de cada preset; antes de remover, checar se outro registro ainda é dono do caminho. `.mcp.json` (alvo único compartilhado) fica fora.

**D3 — Saída estruturada segue `--format text|json`.**
Decision: `aiadev preflight <skill> --feature <slug> --format json` é a única flag nova. No modo json os `issues` vão no stdout, o stderr fica silencioso e o exit code não muda (1 se algum `would_abort`). O texto da spec que dizia `--json` foi ajustado.
Rationale: `metrics` e `learn` já usam `--format [text|json]` (`commands/metrics.py:105-111`). `aiadev next` imprime texto (Story 2 sc5 não pede JSON) e não existe `tasks next`.
Payload do preflight: `skill`, `feature`, `feature_dir`, `ok`, `issues[]`, `docs{spec,plan,tasks,checklists}`, `template`, `test_command`. `test_command` vem de `project_introspect` quando ele detecta um (hoje não detecta pytest, então é `null` em projetos Python puros; limite documentado, não estendemos a detecção nesta spec).

**D4 — Cobertura cenário→task num módulo próprio, com um parser só.**
Decision: novo `src/aiadev/spec_coverage.py` com funções públicas que recebem **paths** (`spec_path`, `tasks_path`; não `branch_dir_for_workspace`, que assume um único filho em `specs/`), usado pelo preflight de `implement` e por `task_context`. Notação aceita: canônica do template (`Story N scenario M`, lista `scenario M, scenario K`), `Story N scenarios M, K`, intervalo `scenarios M–K`, legado `scM`, negrito `**Story N scM**`, várias stories na linha separadas por `;`, `Story N` sozinha (cobre a story) e `Success criterion #N`. Task de infra com "—" precisa citar `Success criterion #N`; sem nenhuma referência, é task órfã (erro). `task_context` passa a reutilizar o parser, o que corrige "Could not parse Spec scenarios line" para a notação do template.
Rationale: `_SCENARIO_REF_RE = sc(\d+)` não casa a notação do próprio template e `_STORY_REF_RE.search` perde a segunda story da linha; ~9 ocorrências reais de intervalo e ~15 tasks de infra com "—".
Trade-offs: features antigas fora da lista falham a checagem; mitigado por `AIADEV_PREFLIGHT=warn` e por medir todas as specs existentes antes de tornar erro (task própria).

**D5 — Fechamento de task sem `git checkout --`.**
Decision: `aiadev tasks done <ID> --feature <slug> --commit "<msg>" [FILES...]` grava o status de forma atômica (arquivo temporário e `os.replace`), faz `git add` dos arquivos e de `tasks.md` e o commit; se o commit falhar, **reescreve só a linha de status para `pending` e faz `git restore --staged tasks.md`**, sem `checkout --`. Helpers de git privados ao módulo do comando (um chamador). Não existe `tasks next` (sem cenário na spec).
Rationale: o fluxo manual faz `git checkout -- tasks.md`, que descarta qualquer outra edição não commitada naquele arquivo; `mark_done` hoje usa `write_text` direto (`tasks_status.py:140`).
Trade-offs: edição concorrente do usuário em `tasks.md` ainda pode conflitar no `git add`; o comando para com mensagem, sem tocar no resto.

**D6 — `aiadev next` estende `pipeline_state`, com a próxima etapa correta.**
Decision: `recommend_next_command` ganha o parâmetro `feature` (slug, opcional); novo `aiadev next [--feature <slug>]` imprime estado e próxima etapa em texto. Prefixo passa a `/aia:` (hoje `pipeline_state` emite `/aiadev:*` e o preflight `/aia:*`). A decisão de "revisão aprovada" deixa de olhar a última linha do `.review-log.jsonl` (que depois de D9 é a da última task) e passa a exigir `.aiadev/review.yaml` aprovado **e** com `timestamp` não anterior à última entrada do `.review-log.jsonl` da feature (o `review.yaml` só tem `status`, `timestamp` e `reason`, não é por feature e é gitignored; sem o corte por data, uma aprovação antiga faria `next` sugerir `finishing-a-branch` numa feature nova), além da regra do preflight de `finishing-a-branch`. O corte compara `timestamp` parseado como datetime, não string; uma feature sem nenhuma entrada no log (só tasks de prosa auto-verificadas) não tem corte, borda que o preflight de `finishing-a-branch` já tem hoje e que fica documentada. `plain` e `AIADEV_HELP_PLAIN` saem com a skill `help`. Slug sem diretório de spec (inclusive uma entrada do roadmap ainda sem spec) → exit 0 com `/aia:specify` e o motivo; exit 2 só para erro real (diretório ilegível).
Rationale: sem isso `aiadev next` pularia `requesting-code-review` e o preflight de `finishing-a-branch` falharia (`_review_is_approved` exige `review.yaml`). A semântica de `tests/test_pipeline_state.py` muda (não só o prefixo); ajustada na mesma task.

**D7 — Custo equivalente por papel em `token_metrics`.**
Decision:
- **Dedupe por `message.id`, maior valor por campo de `usage`** (o `usage` do streaming só cresce; o máximo equivale à última ocorrência e não depende da ordem de leitura dos arquivos). Medido nos transcripts reais: nos principais as repetições têm `usage` idêntico; nos de subagentes 498 de 737 ids repetidos têm `output_tokens` parcial de streaming, e a primeira ocorrência subconta saída em 5,7× (52,8K contra 300,7K). Evento sem `message.id` conta como único (mantém as fixtures atuais verdes). Fixture nova: parcial → final.
- Leitura de `<sessão>/subagents/**/agent-*.jsonl` (inclui `subagents/workflows/wf_*/`, excluindo `journal.jsonl`) com o `*.meta.json` ao lado; papel pelo prefixo do `description` (`implement:`, `review:`), senão "não classificado".
- Pesos constantes e documentados: leitura de cache 0,1×, entrada 1,0×, saída 5,0×; escrita de cache 1,25× (tier 5 min) ou 2,0× (tier 1 h), lidos de `cache_creation.ephemeral_*` quando existirem, senão `cache_creation_input_tokens` a 1,25×.
- Novos campos com valor padrão em `SessionTokens`/`TokenReport`; o JSON ganha chaves, não perde. Os valores pinados em `tests/test_token_metrics.py` (total 3120, 4 turnos, ordem) permanecem.
Rationale: layout confirmado por listagem local (`agentType` quase sempre `general-purpose`, por isso o prefixo; nos transcripts locais a escrita de cache das threads principais é toda de 1 h e a dos subagentes toda de 5 min, por isso os dois tiers são lidos de `cache_creation`).

**D8 — Orçamento de instruções: script, baseline e catraca em pytest.**
Decision: `scripts/instruction_budget.py` no estilo de `scripts/validate_skills.py` (argv cru, `main(argv) -> int`, saída "OK"/"FAIL"); depende de `aiadev` (rota de instalação da CLI) e de PyYAML. Instala cada preset num tmp **pela rota da CLI** (que aplica os defaults de variáveis; o engine não aplica), soma o sempre-carregado (wrapper, `AGENTS.md`, rules sem `paths:`, nome e descrição de skills, commands e agents) e o percurso de `docs/pipeline-path.yaml`, em ⌈caracteres ÷ 4⌉. No percurso conta-se o que a rota padrão lê (`review-gate.md` entra; `references/task-context.md` não, por ser condicional). `docs/instruction-budget.json` guarda `baseline` e `teto` por skill/preset; `tests/test_instruction_budget.py` falha se algo exceder o `teto` e roda no job `tests` do CI. Elevar um teto exige um campo `reason` no JSON, revisável no PR.
Rationale: reaproveita o CI sem job novo. `validate_skills.py` roda no CI via `tests/test_existing_validators_regress.py` e `aiadev validate` roda no job `skills`; o orçamento é novo e por isso ganha teste próprio.

**D9 — Um reviewer por task, um review de branch.**
Decision: o prompt do reviewer por task combina os dois checklists (conformidade primeiro; com achados, para sem avaliar qualidade) e recebe diff e saída dos testes. O reviewer fundido é registrado no review-log como `reviewer: code-reviewer` (`metrics.py:286,310` só contam esse nome) com veredito `APPROVED`/`CHANGES_REQUESTED` (`metrics.py:261,292`). O "final full-branch review" do `implement` sai; `requesting-code-review` é o único review de branch e grava `.aiadev/review.yaml`. Task só de prosa em `docs/` ou documentação raiz é auto-verificada (lint de markdown + validador), exceto o baseline e a lista de percurso. O gate de re-dispatch por falta de evidência fica em `skills/requesting-code-review/references/review-gate.md`; `implement` e os agents o referenciam.
Rationale: a auditoria de 2026-10-13 mediu 13 de 18 dispatches já fundidos na prática. Gatilho de reversão na spec (defeitos no review de branch sobem acima do baseline).

**D10 — Papel do subagente por convenção de descrição.**
Decision: `implement` despacha com `description` "implement: T003 …" e "review: T003 …"; `requesting-code-review` com "review: branch …". Reviewers de documento de `specify` e `plan` ficam fora (não classificados), como registrado na spec.

**D11 — `frontend-design` vai para o preset.**
Decision: a skill é React, MUI e Expo de ponta a ponta; passa para `presets/django-drf-react/skills/frontend-design/SKILL.md` junto com `commands/frontend-design.md` (os handlers já leem `commands/` do preset); saem a linha de `rules/slash-commands.md:22` e entram `provides.skills` do `preset.yaml` e a lista de skills de `presets/django-drf-react/CLAUDE.md`; a linha de `CLAUDE.md:24` passa a indicar o preset. As demais skills genéricas com stack (TDD, debugging, finishing, requesting-code-review, plan) ficam com núcleo genérico + `references/stack.md` do preset (D1). Agents não têm `references/`: `agents/code-reviewer.md` (persona da linha 10, §3–5 e a menção a Celery da linha 69) e `agents/plan-document-reviewer.md` (§7) perdem o stack e ganham uma linha que manda ler, se existir, o `references/stack.md` da skill `requesting-code-review` (code-reviewer) ou `plan` (plan-document-reviewer), entregue pelo preset.
Rationale: Story 4 sc1 exige `lean` sem as palavras de stack; um `references/stack.md` não serviria a uma skill inteira de stack.

**D12 — Aviso do terse-mode no `sync`.**
Decision: `aiadev sync` imprime uma linha quando encontra `aiadev.terseMode` em `.claude/settings.json` ou `AIADEV_TERSE` no ambiente, dizendo que o recurso foi removido; a verificação é inline (não resta módulo `config.py`).
Rationale: `config.py` só tinha `resolve_terse_mode` e é removido; o `sync` é o ponto de upgrade onde o usuário já olha o relatório.

**D13 — Gates "O que não muda": arquivo canônico e teste.**

| Gate | Arquivo canônico | Teste |
|---|---|---|
| Spec-first mecânico (spec existe, sem marcadores, âncoras) | `src/aiadev/preflight.py` | `tests/test_preflight*.py` (existentes) |
| RED observado por razão certa antes do GREEN | `skills/test-driven-development/SKILL.md` | `tests/test_gates_canonical.py` (novo) |
| Constitution Check com evidência | `skills/plan/SKILL.md`, `templates/plan-template.md` | `tests/test_gates_canonical.py` |
| Evidência antes de afirmação (`review.yaml` aprovado antes do PR) | `src/aiadev/preflight.py` (`_review_is_approved`), `skills/finishing-a-branch/SKILL.md` | `tests/test_preflight_review.py` (existente) |
| Flip de status atômico com o commit e rollback | `src/aiadev/tasks_status.py`, `skills/implement/SKILL.md` | `tests/test_tasks_status.py`, teste novo do `tasks done` |
| Re-dispatch por falta de evidência | `skills/requesting-code-review/references/review-gate.md` | `tests/test_review_redispatch_skills.py` (reescrito: gate em um arquivo, demais referenciam) |
| Causa-raiz antes do fix; escalada após 3 falhas | `skills/systematic-debugging/SKILL.md` | `tests/test_gates_canonical.py` |
| Exclusão de arquivos secretos na inferência de produto | `skills/product/SKILL.md` | `tests/test_product_skill.py` (existente) |
| Reconhecimento no `specify` | `skills/specify/SKILL.md` | `tests/test_specify_skill_has_recon_step.py` (existente) |

## Project structure changes

```text
src/aiadev/token_metrics.py            (modified)  dedupe por maior valor, subagentes, pesos, papel
src/aiadev/commands/metrics.py         (modified)  texto/JSON com custo por papel
src/aiadev/spec_coverage.py            (new)       parser de referências + checagem de cobertura
src/aiadev/task_context.py             (modified)  passa a usar spec_coverage
src/aiadev/preflight.py                (modified)  contexto JSON, cobertura, gate de checklists
src/aiadev/commands/preflight.py       (modified)  --format json
src/aiadev/project_introspect.py       (read-only) test_command quando detectado
src/aiadev/tasks_status.py             (modified)  escrita atômica, reverter para pending
src/aiadev/commands/tasks.py           (new)       grupo `tasks` (done)
src/aiadev/commands/next.py            (new)       `aiadev next`
src/aiadev/pipeline_state.py           (modified)  parâmetro feature, /aia:, review.yaml
src/aiadev/cli.py                      (modified)  registra tasks e next
src/aiadev/install_engine.py           (modified)  references/ de skill; remoção de órfãos por plataforma
src/aiadev/commands/sync.py            (modified)  agrega removed/preserved; aviso do terse
src/aiadev/config.py                   (removed)   só continha resolve_terse_mode
scripts/instruction_budget.py          (new)
scripts/generate_pipeline_reference.py (modified)  PIPELINE sem "help"
docs/instruction-budget.json           (new)
docs/pipeline-path.yaml                (new)
docs/gemini-tools.md                   (new)       realocado de skills/using-ai-augmented-developer/references/
skills/implement/                      (modified)  núcleo + references/task-context.md
skills/requesting-code-review/         (modified)  sem review-context.md; + references/review-gate.md
skills/{product,specify,clarify,plan,tasks,constitution,finishing-a-branch,systematic-debugging,test-driven-development}/  (modified)
skills/frontend-design/                (moved)     → presets/django-drf-react/skills/frontend-design/
commands/frontend-design.md            (moved)     → presets/django-drf-react/commands/
presets/django-drf-react/{preset.yaml,CLAUDE.md}  (modified)  provides.skills e lista de skills
skills/help/                           (removed)
skills/using-ai-augmented-developer/   (removed)
commands/using-ai-augmented-developer.md (removed)
agents/*-reviewer.md                   (modified)  sem bloco terse; stack sai de code-reviewer e plan-document-reviewer
presets/django-drf-react/skills/*/references/stack.md  (new)  conteúdo de stack movido
rules/terse-mode.md, schemas/terse-output.schema.json  (removed)
rules/{api-conventions,slash-commands}.md  (modified)  paths: e 2 linhas
templates/{spec,checklist,tasks}-template.md  (modified)  Assumptions opcional, categorias, notação
CLAUDE.md, GEMINI.md, README.md, CONTRIBUTING.md, .pre-commit-config.yaml, presets/lean/CLAUDE.md,
templates/roadmap-template.md, docs/{pipeline-reference,token-economy,README.codex,metrics}.md, CREDITS.md, CHANGELOG.md  (modified)
tests/  novos: coverage, tasks_done, next, budget, sync-removal (inclui "instalar cursor depois de claude-code não remove .claude"),
        skill-support-files, gates_canonical, lean-sem-stack, sync_terse_notice;
        removidos: `*terse*`, off_mode*, help_skill, help_skill_state_aware, using_aia_mentions_recon;
        reescritos: implement_skill_drift, implement_task_context_integration, review_redispatch_skills,
        zero_findings_halt_agents, pipeline_state, pipeline_reference_drift, generate_pipeline_reference,
        rules_content, claude_md_pointer, product_registries, credits_attribution, existing_validators_regress,
        changelog_entry, token_economy_checklist, token_metrics (novos casos)
```

## Phase breakdown

> Cada fase é um checkpoint mesclável. Dentro da fase as tasks são independentes; entre fases a ordem importa.

### Phase 1 — Medição e orçamento (Story 1, Story 4 sc4)

- Fixtures de transcript com `message.id` (inclusive parcial → final), `subagents/**/*.jsonl` e `*.meta.json` (nenhuma existe hoje).
- D7 em `token_metrics.py`; texto e JSON do `metrics --tokens`; documentar o comando em `docs/metrics.md`.
- D8: `scripts/instruction_budget.py`, `docs/pipeline-path.yaml`, **baseline registrado em `docs/instruction-budget.json` antes de qualquer corte**, catraca em pytest.
- Conferir o total contra a dedupe manual de uma sessão real (evidência do Art. IV, mesma regra).

### Phase 2 — Motor de instalação (pré-requisito das fases 4 e 5)

- D1 em todas as plataformas (teste por handler: Claude Code, Codex, Gemini, Cursor, OpenCode).
- D2 com o teste de plataforma cruzada, regra de hash, dono compartilhado, `DRY_RUN` e relatório.

### Phase 3 — Fluxo e revisão: todas as stories P1 (Story 2, Story 3)

- D4: `spec_coverage.py`, parser unificado em `task_context`; medir todas as specs existentes antes de tornar a checagem erro; notação canônica no `templates/tasks-template.md`.
- D3: preflight `--format json`, cobertura e gate de checklists no `implement` (parser: linhas FAIL da tabela de checks, ignorando a linha placeholder; chave = coluna `#` ↔ "Owner task" da tabela de falhas; a task dona precisa existir em `tasks.md`).
- D5 e D6: `aiadev tasks done` e `aiadev next`.
- **Prosa P1 sobre o `SKILL.md` monolítico atual** (a reestruturação fica na fase 4): `implement` passa a usar preflight JSON e `tasks done`, revisão única (D9) com convenção de descrição (D10), remove o "final full-branch review"; `requesting-code-review` sem `review-context.md` (a seção "Impacted subsystems" passa a ser acrescentada ao prompt do reviewer, mantendo as palavras que `tests/test_provider_followups.py` fixa). Cada edição reduz texto líquido; se algum teto tiver de subir, o `reason` entra no JSON. Os testes que fixam essa prosa (`test_implement_skill_drift`, `test_review_redispatch_skills`, `test_zero_findings_halt_agents`) são reescritos como comportamento **nesta fase**, para que ela seja mesclável sozinha.

### Phase 4 — Texto: divulgação progressiva, stack e triagem (Story 4, Story 5)

- `implement` e `requesting-code-review` em núcleo + `references/` (D1), gate em um arquivo (D9); demais testes de prosa (`test_implement_task_context_integration`, `test_product_skill`, `test_provider_followups`, `test_specify_skill_has_recon_step`) reescritos como comportamento; D13 com `tests/test_gates_canonical.py`.
- D11 (inclui tirar `frontend-design` da lista de `presets/lean/CLAUDE.md:25` na mesma task) e stack nos presets; rules com `paths:`; `lean` sem as palavras de stack (teste novo).
- Triagem: teto de 3 marcadores e `## Assumptions` opcional em `specify`, teto de 5 perguntas em `clarify`, critério de premissas no `spec-document-reviewer`, template de spec sem comentários redundantes.
- Demais skills enxutas; `templates/checklist-template.md` sem todas as categorias.

### Phase 5 — Remoções e migração (Story 6)

- terse-mode inteiro (rule, schema, `config.py`, blocos nos agents, testes e fixtures, referências em `checklist-template`, `docs/token-economy.md`, `CREDITS.md`) e D12.
- `help` e `using-ai-augmented-developer`: skills, comando, `gemini-tools.md` realocado, `CLAUDE.md`, `README.md`, `CONTRIBUTING.md`, `.pre-commit-config.yaml`, `roadmap-template.md`, `docs/pipeline-reference.md` regenerado (limite de 24 linhas), `GEMINI.md` e `docs/README.codex.md` repontados, contagens de `presets/lean/CLAUDE.md`. Story 6 sc4 usa lista de exceções: `CHANGELOG.md` e `specs/**` históricos.
- **Verificar ≥ 40% contra o baseline** e só então rebaixar o baseline para a medida pós-corte.

### Phase 6 — Benchmark e fechamento (critério de sucesso final)

- Protocolo: um par é a mesma micro-feature (spec fixa em `docs/`) executada nos dois braços, alternando a ordem; o custo da feature é a soma do custo equivalente de todas as sessões entre o primeiro e o último commit, com os ids das sessões registrados no relatório. ≥ 5 pares; regra de aceitação da spec.
- `CHANGELOG.md [Unreleased]` (Added/Changed/Removed, com nota de quebra para `lean`), `CREDITS.md`, `aiadev manifests --write`; bump minor no release.

## Risks and mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Testes que fixam prosa contradizem a estrutura nova | High | Med | Reescrever como comportamento na mesma task que move o texto; nunca apagar. `test_rules_paths*.py` não leem arquivos do framework e não são afetados |
| `sync` apaga arquivos de outra plataforma ou edições do usuário | Med | High | D2: restrito à plataforma corrente, regra de hash, nunca apaga editado; teste de plataforma cruzada |
| Subcontagem de saída por usage de streaming | High | High | D7: maior valor por campo; fixture parcial → final |
| `aiadev next` pula o review de branch | Med | Med | D6: exigir `review.yaml` aprovado; teste |
| Checagem de cobertura reprova features antigas | High | Low | Medir as specs existentes, `AIADEV_PREFLIGHT=warn`, exceções documentadas |
| Merge com a spec 0029 (mesmos `specify`/`plan`/`tasks`, `tasks-template`, reviewers de documento, `docs/README.codex.md`) | Med | Med | 0030 entra antes: a 0029 mede custo por feature e depende de `token_metrics` corrigido (cl-4 dela). As fases 1–3 só tocam prosa de `implement`/`requesting-code-review` e a notação do `tasks-template`; a fase 4 conflita e é rebaseada. A ordem de merge das specs 0024–0029 combinada com o mantenedor (registrada fora do repositório) não incluía a 0030; esta spec propõe entrar antes da 0029 e o mantenedor confirma ao aprovar o plano |
| Remoção do terse-mode quebra consumidores com a chave ligada | Low | Low | D12: aviso de uma linha e chave ignorada; nota no CHANGELOG |
| `lean` perde exemplos de stack e `frontend-design` | Med | Med | Nota de breaking, bump minor, conteúdo disponível no preset `django-drf-react` |
| Prosa da fase 3 estoura a catraca da fase 1 | Med | Low | Edições líquidas negativas; teto com `reason` quando inevitável |
| Benchmark curto subestima o ganho de contexto acumulado | Med | Low | Registrar como limite; custo por feature e turnos como métricas, nunca tokens salvos |
| Spec grande para uma branch | Med | Med | Fases mescláveis; linha de corte entre as fases 3 e 4 (P1 inteiras antes dela) |

## Complexity tracking

| Article waived | Reason | Alternatives considered | Reviewer |
|---|---|---|---|
| — | nenhum waiver: todos os artigos PASS ou N/A | — | — |

## Hand-off to `tasks`

The next skill is `tasks`. It consumes this plan and produces `tasks.md`.
Pre-conditions before hand-off:

- [x] Constitution Check is fully populated, no blank rows.
- [x] Complexity tracking is filled or empty-and-justified.
- [x] Project structure delta is accurate.
