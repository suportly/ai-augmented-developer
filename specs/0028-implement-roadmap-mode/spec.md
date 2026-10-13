# Feature specification: modo roadmap no `implement` — várias features em sequência, com métricas de qualidade de spec

> This file is produced by the `specify` skill (or by `aiadev init --feature <name>` as a stub). Keep it focused on **what** and **why** — planning and code belong in `plan.md` and `tasks.md`.

**Branch:** `feature/0028-implement-roadmap-mode`
**Created:** 2026-09-24
**Status:** Draft <!-- Draft | In review | Approved | Implemented -->
**Spec ID:** 0028 <!-- auto-incrementing integer -->
**Language:** pt-BR <!-- BCP-47 tag; every downstream artifact in this feature is written in this language. -->

---

<!-- section: Problem -->
## Problem

O `implement` executa **uma** feature: percorre o `tasks.md` de uma branch, com subagente novo e duas revisões por task, e entrega para o `finishing-a-branch`. Quando o roadmap (spec 0023) tem várias features prontas — spec aprovada, plano e tasks gerados —, alguém precisa disparar cada uma, acompanhar e decidir quando parar. O curso SDD roda features do roadmap em sequência e usa o resultado para avaliar a qualidade das specs: specs boas passam sem retrabalho, specs ruins travam na revisão. O aiadev já coleta os sinais disso (`.review-log.jsonl`, status de tasks, iterações de clarify via `aiadev metrics`), mas não os liga à execução em sequência nem os apresenta como qualidade de spec. Quem sente: o tech lead que quer deixar o agente avançar pelo roadmap sem vigiar cada feature e saber, no fim, quais specs precisam melhorar.

<!-- section: Reconnaissance -->
## Reconnaissance

- **loop por feature** — entry: `skills/implement/SKILL.md` · auth: none · integration: "The loop" (ler linha → pular se `done` → implementer → spec reviewer → code quality reviewer → flip de status + commit), "Reviewer re-dispatch gate" (limite de 2 re-dispatches) e "Error handling for the pipeline itself" (pausar, nota em `tasks.md`, avisar). O modo roadmap reaproveita esse loop por feature sem alterá-lo.
- **retomada segura** — entry: `src/aiadev/tasks_status.py` · auth: none · integration: `parse` / `validate` / `mark_done` e a regra "`in_progress` é tratado como `pending`" dão o guard de retomada por task; o modo roadmap precisa de um equivalente por feature.
- **preflight por branch** — entry: `src/aiadev/preflight.py` · auth: none · integration: `check` falha se a branch atual não for `feature/<slug>` do diretório da spec. Logo, **toda** feature da sequência exige trocar de branch antes do dispatch, com ou sem dependência entre features; o loop atual do `implement` não faz essa troca. A estratégia para features dependentes é cl-2.
- **custo e turnos** — entry: `src/aiadev/token_metrics.py` · auth: none · integration: `read_session` / `build_token_report` contam turnos e tokens por **sessão**, lendo só transcripts do Claude Code (`~/.claude/projects/<slug>`), sem atribuir sessão a feature e sem custo monetário. Não há hoje fonte de custo por feature nem de turnos nas outras 4 plataformas (cl-7).
- **métricas existentes** — entry: `src/aiadev/metrics.py` · auth: none · integration: `first_pass_rate_by_reviewer`, `task_rework_counts`, `clarify_iteration_count`, `specify_to_last_commit_days`, `build_report`; o CLI em `src/aiadev/commands/metrics.py` tem `--feature`, `--since`, `--format`, `--tasks`, `--show-bodies` (prosa de reviewer, Artigo VI), `--tokens` e `--transcripts-dir`. É aqui que a qualidade de spec aparece.
- **rastro de revisão** — entry: `src/aiadev/review_log.py` · auth: none · integration: `append_review_entry` e o esquema de `.review-log.jsonl` (reviewer, verdict, `has_why_no_issues_block`, `task_id`) — fonte primária do sinal de pausa e das métricas.
- **roadmap e aceite (dependências)** — entry: `specs/0023-product-context/spec.md` · auth: none · integration: ordem e status das features vêm do `roadmap.md`; o aceite humano (acumulado; dependentes pausam, cl-5) vem de `specs/0025-validation-criteria-human-acceptance/spec.md`; a marcação de concluído vem de `specs/0024-replan/spec.md`, que o modo chama depois de cada merge que observar (0024 cl-5).

<!-- section: Users and stakeholders -->
## Users and stakeholders

- **Tech lead** — dispara uma sequência de features e recebe, no fim, o que foi entregue, onde parou e por quê.
- **Autores de spec** — recebem um indicador de qualidade da própria spec baseado no que aconteceu na implementação.
- **Revisores humanos** — continuam com a palavra final: o modo não pula revisão nem aceite.

<!-- section: Success criteria -->
## Success criteria

- Com N features prontas no roadmap, uma única invocação do modo roadmap as executa **na ordem do roadmap**, cada uma pelo loop atual do `implement`, sem alteração no loop por task (os testes de drift da skill `implement` continuam verdes).
- A execução **pausa** na primeira ocorrência de: revisão que continua reprovando após o limite de re-dispatch, status `BLOCKED`, preflight falhando, feature sem artefatos prontos, ou próxima feature dependente de outra sem aceite e merge (cl-2, cl-5); atingir o limite de N features também encerra a execução (cl-4). A pausa registra feature, task e motivo, e não inicia a feature seguinte.
- Retomar depois de uma pausa continua da feature e task onde parou, sem refazer tasks `done` (verificável com fixture de roadmap + tasks).
- `aiadev metrics` mostra, por feature executada, os cinco indicadores de qualidade de spec de cl-3, e no modo agregado distingue features executadas em sequência das executadas uma a uma.
- A comparação entre execução em sequência e execução uma a uma usa **custo por feature concluída e número de turnos** (no Claude Code, pela janela de cada feature; nas outras plataformas "indisponível", cl-7), não tokens economizados.

<!-- section: Non-goals -->
## Non-goals

- Paralelizar features; a execução é sequencial.
- Pular ou afrouxar qualquer revisão, preflight ou aceite humano para "não parar a fila".
- Mesclar branches automaticamente.
- Uma nota única de "qualidade de spec" sem decomposição; os indicadores ficam separados e com evidência.

<!-- section: User stories -->
## User stories

### Story 1 — Executar features do roadmap em sequência (P1)

Como tech lead, quero executar várias features do roadmap numa invocação para que o agente avance pela fila sem eu disparar cada uma.

**Acceptance scenarios** (Given / When / Then, ≥ 3 per story):

1. Given o roadmap tem três features prontas em ordem A, B, C, When invoco o modo roadmap, Then A, B e C são executadas nessa ordem, cada uma pelo loop atual do `implement` e na própria branch.
2. Given a feature B depende de A e A ainda não foi mesclada, When chego em B, Then a execução pausa em B e informa que A precisa de aceite e merge antes.
3. Given uma feature já tem todas as tasks `done`, When o modo roadmap passa por ela, Then ela é pulada sem novo dispatch.
4. Given invoco o modo com limite de 2 features e há 3 prontas, When a segunda termina, Then a execução para e registra que a terceira não foi iniciada.

### Story 2 — Pausar quando algo falha (P1)

Como tech lead, quero que a sequência pare na primeira falha de revisão ou bloqueio para que nenhuma feature seguinte comece sobre base ruim.

**Acceptance scenarios:**

1. Given o code quality reviewer reprova a task T004 da feature B após o limite de re-dispatch, When isso acontece, Then a execução para, registra feature B / T004 / motivo e não inicia C.
2. Given a feature C não tem `tasks.md` aprovado, When a execução chega em C, Then pausa informando o artefato que falta, sem rodar as skills anteriores.
3. Given uma pausa registrada, When retomo o modo roadmap, Then continua em B / T004 sem refazer T001–T003.
4. Given uma pausa, When rodo `/aia:help`, Then o "Próximo passo" aponta o motivo da pausa.

### Story 3 — Medir a qualidade das specs com `aiadev metrics` (P2)

Como autor de spec, quero ver indicadores de qualidade da minha spec derivados da execução para que eu saiba o que corrigir no jeito de especificar.

**Acceptance scenarios:**

1. Given uma sequência executada, When rodo `aiadev metrics --feature <slug>`, Then vejo os cinco indicadores de cl-3 dessa feature com a evidência (reviewer, task, contagem).
2. Given várias sequências no período, When rodo `aiadev metrics --format json`, Then a saída tem schema estável, sem timestamp de execução, com os indicadores por feature e a origem da execução (sequência ou avulsa).
3. Given rodo `aiadev metrics` sem ter usado o modo roadmap, When a saída é gerada, Then é idêntica à de hoje.

<!-- section: Clarifications -->
## Clarifications

- **cl-1 (escopo da execução):** só features já prontas: spec sem marcadores e aprovada, `plan.md` e `tasks.md` existentes. O modo não roda `specify`, `clarify`, `plan` nem `tasks`: `clarify` exige humano, e o Artigo I não admite especificar sem ele. Feature não pronta faz a execução pausar.
- **cl-2 (branches e dependências):** cada feature sai da branch principal numa branch própria; não há branches empilhadas. Uma entrada cujo `**Depends on:**` aponta para outra que não está `done` (mesclada) faz a execução pausar. Na prática, só features independentes correm em sequência sem supervisão.
- **cl-3 (qualidade de spec):** cinco indicadores tirados do rastro que já existe, reportados lado a lado, cada um com evidência: (1) aprovação de primeira do spec reviewer por task, (2) tasks com retrabalho, (3) iterações de `clarify`, (4) tasks sem fase de origem no plano (a classe "Task without plan coverage" da spec 0029), (5) critérios de validação reprovados no aceite (spec 0025). Sem nota composta e sem limiar de "spec ruim" na v1; um limiar só entra quando houver dados para calibrar.
- **cl-4 (limite sem supervisão):** a invocação exige um número explícito de features ("até N"); não existe execução ilimitada. Ao atingir N, a execução para como numa pausa, com registro de onde parou. Toda pausa (Story 2) também encerra a execução.
- **cl-5 (aceite humano):** os aceites se acumulam. Terminada a revisão automática de uma feature, a próxima feature **independente** começa, e os aceites pendentes da spec 0025 aparecem no relatório final. Uma feature que depende de outra ainda sem aceite e merge pausa, pela regra de cl-2. Nenhum merge acontece sem o aceite.
- **cl-6 (invocação):** seção nova da skill `implement`, acionada por argumento (ex.: `implement --roadmap <N>`). Não é skill separada nem subcomando do CLI. `PIPELINE_SKILLS` e `aiadev.tools` não mudam; o loop por task continua intocado.
- **cl-7 (custo e turnos):** só no Claude Code, a única plataforma cujos transcripts o `token_metrics` lê. O registro de progresso da execução guarda início e fim de cada feature, e as sessões cujos timestamps caem nessa janela são atribuídas a ela. "Custo" é reportado em tokens por categoria (input, cache creation, cache read, output) mais turnos, sem conversão para moeda. Nas outras plataformas o relatório diz "custo indisponível" e não estima.
- **cl-8 (escopo da branch):** fica numa spec só, como pedido no item 6, mas a Story 3 é a última fase do plano e pode sair num PR próprio. Com cl-3 os indicadores são derivados das primitivas atuais do `metrics`, então a parte de métricas é pequena.

<!-- section: Data touched -->
## Data touched

- **Leitura:** `roadmap.md` (0023), `spec.md`/`plan.md`/`tasks.md` de cada feature, `.review-log.jsonl`.
- **Escrita:** commits por task (inalterado); um registro de progresso/pausa da execução em sequência (formato no plano); campos novos na saída do `aiadev metrics` (texto e JSON).
- **Pacote:** `skills/implement/SKILL.md` (seção nova, loop por task intocado), `src/aiadev/metrics.py`, `src/aiadev/metrics_format.py`, `src/aiadev/commands/metrics.py`, `src/aiadev/pipeline_state.py`, `docs/metrics.md`.

<!-- section: Out-of-band effects -->
## Out-of-band effects

- Nenhum além do que o `implement` já faz (commits locais). Nenhum push ou merge automático.

<!-- section: Open risks -->
## Open risks

- **Erro que se propaga:** uma falha sutil que passa pela revisão na feature A contamina B e C antes de um humano ver.
- **Custo por execução:** limitado pelo N explícito (cl-4), mas cada feature ainda pode custar muito antes da primeira pausa.
- **Escopo largo:** orquestração e métricas na mesma spec; mitigado deixando a Story 3 como última fase, com PR próprio se necessário (cl-8).
- **Métrica que vira meta:** autores podem escrever specs para agradar o indicador e não para esclarecer o problema.
- **Esquema do `.review-log.jsonl`:** marcar a origem (sequência ou avulsa) pode exigir campo novo; mudança de esquema afeta `learn` e `metrics`.

<!-- section: Traceability -->
## Traceability

- Originating issue: comparação do aiadev com o curso "Spec-Driven Development with Coding Agents" (DeepLearning.AI × JetBrains, Paul Everitt) — conversa de 2026-09-24, melhoria 6 de 7.
- Related specs: `0023-product-context` (bloqueante: roadmap), `0024-replan` (marca concluído entre features), `0025-validation-criteria-human-acceptance` (aceites acumulados; dependentes pausam), `0013-implement-task-status-tracking` (guard de retomada), `0015-aiadev-metrics` (indicadores), `0022-smart-mcp-proxy-token-economy` (medição de custo por tarefa).
- Constitution articles invoked: I, II, III, IV, VI

### Constitution Check (preliminar)

> Avaliação no nível da spec. O `plan` refaz a checagem com evidência concreta.

| Artigo | Aplica? | Avaliação preliminar |
|---|---|---|
| I. Spec-first | Sim | Esta spec (cl-1…cl-8 resolvidas em 2026-09-24); o modo nunca executa feature sem spec aprovada, plano e tasks (cl-1). |
| II. Test-first | Sim | Fixtures de roadmap + tasks + review-log com testes de ordem, pausa e retomada; regressão da saída atual do `metrics`. |
| III. Simplicity | Sim | Reaproveita o loop por task do `implement` sem alterá-lo; indicadores derivados das primitivas atuais do `metrics`. |
| IV. Evidence over claims | Sim | Cada pausa registra feature/task/motivo; cada indicador cita sua evidência; comparação por custo por feature e turnos. |
| V. Provider pattern | Não | Sem fronteira de rede nova. |
| VI. Privacy by design | Sim | Prosa de reviewer fora da saída padrão do `metrics` (mantém `--show-bodies`). |
| VII. Attribution | Não | Nada adaptado: escrito do zero. A entrada de inspiração do curso SDD no `CREDITS.md` (spec 0023, cl-6) cobre a ideia. |
