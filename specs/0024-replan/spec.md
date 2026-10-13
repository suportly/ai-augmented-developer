# Feature specification: skill `replan` — fechar o ciclo entre entrega e roadmap

> This file is produced by the `specify` skill (or by `aiadev init --feature <name>` as a stub). Keep it focused on **what** and **why** — planning and code belong in `plan.md` and `tasks.md`.

**Branch:** `feature/0024-replan`
**Created:** 2026-09-24
**Status:** Draft <!-- Draft | In review | Approved | Implemented -->
**Spec ID:** 0024 <!-- auto-incrementing integer -->
**Language:** pt-BR <!-- BCP-47 tag; every downstream artifact in this feature is written in this language. -->

---

<!-- section: Problem -->
## Problem

O pipeline termina no `finishing-a-branch`: a PR é aberta, a branch é mesclada e a spec ganha `Status: Implemented`. Nada volta para o nível do produto. O roadmap (spec 0023) ficaria desatualizado na primeira entrega, e as mudanças de escopo descobertas durante a implementação — tasks que surgiram no meio, concerns reportados pelo implementer (`DONE_WITH_CONCERNS`), gaps do `analyze`, itens empurrados para *Non-goals* — morrem na PR. O curso SDD fecha o ciclo com um passo de replanejamento após cada feature. Quem sente: o tech lead, que precisa reconstruir à mão "o que foi entregue, o que mudou e o que vem depois".

<!-- section: Reconnaissance -->
## Reconnaissance

- **fim do pipeline hoje** — entry: `skills/finishing-a-branch/SKILL.md` · auth: none · integration: seções "After PR Is Opened" (atualiza `Status` da spec) e "Merge Decision"; não há hand-off depois do merge. É onde o `replan` se encaixa.
- **mineração do rastro** — entry: `src/aiadev/learn.py` · auth: none · integration: `detect_all` / `recurring_reviewer_failures` / `recurring_task_rework` produzem padrões de **falha de processo** (reviewer que reprova, tasks com rework), e `aiadev learn --write` grava em `specs/_learnings.md`. Não sabe nada sobre features entregues nem sobre roadmap — é fonte **secundária** para o `replan` (candidatos a melhoria de processo), não a fonte do "o que foi entregue".
- **estado de specs e tasks** — entry: `src/aiadev/metrics.py` · auth: none · integration: `read_spec_header` (Status, Spec ID), `tasks_by_status` e `AGGREGATE_STATUSES` (`Implemented`, `Merged`) dão o sinal "entregue" por spec sem reimplementar parsing.
- **drift entre spec e código** — entry: `skills/analyze/SKILL.md` · auth: none · integration: as quatro classes de gap (spec sem plano, plano sem task, task sem código, código sem task) são exatamente as mudanças de escopo que o `replan` precisa classificar; o relatório opcional fica em `specs/<branch>/analysis.md`.
- **próximo passo recomendado** — entry: `src/aiadev/pipeline_state.py` · auth: none · integration: `recommend_next_command` termina em `/aiadev:finishing-a-branch`; passa a recomendar `replan` na branch principal quando o roadmap tem entrada entregue e ainda não `done` (cl-4).
- **roadmap (dependência)** — entry: `specs/0023-product-context/spec.md` · auth: none · integration: gramática definida em 0023 cl-2: `### R<NNN> — <título>` com `**Status:**` (`planned | in-progress | done | dropped`), `**Spec:**` (slug da spec) e `**Depends on:**`; arquivo em `specs/_product/roadmap.md` (0023 cl-1).

<!-- section: Users and stakeholders -->
## Users and stakeholders

- **Tech lead / dono do produto** — quer o roadmap refletindo a realidade logo após cada merge, com as mudanças de escopo explícitas.
- **Time de desenvolvimento** — quer que o trabalho pequeno descoberto no caminho seja resolvido logo, e não esquecido.
- **Agente** — precisa de um roadmap confiável para o modo roadmap do `implement` (spec 0028).

<!-- section: Success criteria -->
## Success criteria

- Depois de um merge, `replan` marca como concluídas **exatamente** as entradas do roadmap cuja spec está `Implemented`/`Merged` e cuja branch foi mesclada — nenhuma a mais (verificável contra um fixture de roadmap + specs + git log).
- Toda mudança de escopo detectada aparece no relatório com a **fonte citada** (arquivo:linha da spec/tasks/analysis, id de task ou hash de commit) e com uma classificação: *pequena → resolver agora* ou *grande → nova entrada no roadmap*.
- Nenhuma edição no `roadmap.md` é gravada sem aprovação humana; o relatório mostra o diff proposto antes.
- Quando `aiadev learn` tem padrões no período, eles aparecem como **candidatos** separados; nunca viram entrada de roadmap sem aprovação.
- Sem `roadmap.md`, a skill para com uma mensagem que aponta para `product` (spec 0023) e não cria roadmap por conta própria.

<!-- section: Non-goals -->
## Non-goals

- Criar ou reordenar o roadmap inteiro — isso é `product`. O `replan` só atualiza status, adiciona entradas de escopo descoberto e propõe reordenação.
- Executar a correção das mudanças pequenas ou abrir a branch delas; o `replan` só gera a demanda de follow-up para o `specify` (cl-2).
- Consultar issue tracker, PRs remotas ou qualquer serviço de rede.
- Alterar o que o `aiadev learn` detecta ou grava.

<!-- section: User stories -->
## User stories

### Story 1 — Marcar o que foi entregue (P1)

Como tech lead, quero que o `replan` compare o que foi mesclado com o `roadmap.md` e marque as entradas concluídas para que o roadmap não dependa de atualização manual.

**Acceptance scenarios** (Given / When / Then, ≥ 3 per story):

1. Given uma entrada do roadmap com `**Spec:** 00NN-<slug>`, a spec está `Implemented` e a branch foi mesclada em `main`, When rodo `replan`, Then a entrada é proposta como concluída com link para a spec e o commit de merge.
2. Given a spec está `Implemented` mas a branch ainda não foi mesclada, When rodo `replan`, Then a entrada **não** é marcada como concluída e o relatório diz por quê.
3. Given uma spec mesclada sem entrada correspondente no roadmap, When rodo `replan`, Then o relatório lista a spec como "entregue fora do roadmap" e propõe a entrada, sem gravá-la.
4. Given não existe `roadmap.md`, When rodo `replan`, Then a skill para e recomenda `product`.
5. Given duas features foram mescladas desde o último `replan`, When rodo `replan` uma vez, Then as duas entradas são tratadas na mesma execução, e rodar de novo sem merge novo não propõe nada.
6. Given a entrada `R004` tem `**Spec:** 0031-x` mas a spec 0031 cita `R005` na *Traceability*, When rodo `replan`, Then o relatório mostra o conflito e não marca nenhuma das duas entradas.

### Story 2 — Classificar mudanças de escopo (P1)

Como tech lead, quero que as mudanças de escopo descobertas na feature sejam classificadas em pequena ou grande para que o pequeno seja resolvido agora e o grande entre no roadmap.

**Acceptance scenarios:**

1. Given `tasks.md` tem tasks que não correspondem a nenhuma fase do `plan.md` ou o `analysis.md` lista gaps, When rodo `replan`, Then cada item aparece no relatório com a fonte citada e uma classificação: pequena se cabe numa task e não altera user story nem cenário de aceitação; grande caso contrário.
2. Given dois itens classificados como pequenos, When aprovo o relatório, Then a skill passa ao `specify` uma única demanda de follow-up com os dois itens (cada um citando a fonte) e não altera o roadmap nem abre branch.
3. Given um item classificado como grande, When aprovo o relatório, Then uma nova entrada entra no roadmap com `**Status:** planned` (gramática de 0023 cl-2) e link para a spec de origem.
4. Given um item que o critério não consegue classificar, When rodo `replan`, Then a skill pergunta ao humano em vez de escolher.

### Story 3 — `aiadev learn` como fonte secundária (P2)

Como mantenedor, quero que os padrões recorrentes do `aiadev learn` apareçam no `replan` como candidatos para que melhorias de processo entrem no mesmo ciclo de planejamento.

**Acceptance scenarios:**

1. Given `aiadev learn --format json` retorna padrões no período, When rodo `replan`, Then o relatório tem uma seção de candidatos com cada padrão e sua evidência.
2. Given `aiadev learn` retorna "evidência insuficiente", When rodo `replan`, Then a seção de candidatos diz isso e não inventa padrões.
3. Given aprovo um candidato, When a skill grava, Then ele vira entrada de roadmap; candidatos não aprovados não são gravados.

### Story 4 — Encadeamento com `finishing-a-branch` (P2)

Como usuário do pipeline, quero que o `replan` seja o passo sugerido depois do merge para que o ciclo feche sem eu precisar lembrar.

**Acceptance scenarios:**

1. Given o `finishing-a-branch` concluiu o merge, When a skill termina, Then o hand-off aponta para `replan`.
2. Given estou na branch principal e o roadmap tem uma entrada não `done` cujo `**Spec:**` aponta para uma spec `Implemented`, When rodo `/aia:help`, Then o "Próximo passo" recomenda `replan`.
3. Given a skill instalada em cada uma das 5 plataformas, When `aiadev validate` roda, Then o `SKILL.md` de `replan` passa nos dois schemas.

<!-- section: Clarifications -->
## Clarifications

- **cl-1 (pequena × grande):** pequena quando as duas condições valem: (a) cabe numa única task do `tasks.md` (um teste + uma implementação + um commit, a unidade que o pipeline já usa) e (b) não altera nenhuma user story nem cenário de aceitação da spec. Se qualquer uma falha, é grande. Se o agente não consegue afirmar as duas, pergunta ao humano (Story 2, cenário 4).
- **cl-2 (resolver agora):** os itens pequenos aprovados de uma feature viram **uma única demanda de follow-up**, que o `replan` passa ao `specify` com cada item citando a fonte; a spec resultante tem uma story por item. O `replan` não abre branch nem escreve código, e o humano decide quando começar. Como cada item cabe numa task (cl-1), plan e tasks saem curtos. Se não houver item pequeno aprovado, nenhuma spec é criada.
- **cl-3 (ligação roadmap ↔ spec):** o campo `**Spec:**` da entrada `R<NNN>` é a fonte de verdade, e o `replan` usa só ele para marcar concluído. A citação de `R<NNN>` na *Traceability* da spec (spec 0023, Story 3) segue como informação para o leitor. Se as duas divergem, o `replan` reporta o conflito e não escolhe.
- **cl-4 (recomendação no help):** sim. Na branch principal, se `specs/_product/roadmap.md` existe e tem uma entrada que não está `done` cujo `**Spec:**` aponta para uma spec `Implemented` ou `Merged`, `pipeline_state.recommend_next_command` recomenda `replan` antes de `specify`. A regra usa a fonte de verdade de cl-3, não cria estado novo e não muda nada para quem não tem roadmap.
- **cl-5 (por feature × lote):** o gatilho é por feature (hand-off do `finishing-a-branch` após cada merge, ou o `/aia:help` pela regra de cl-4), mas cada execução processa **todas** as entradas entregues e ainda não `done`, então funciona como lote quando houve vários merges desde o último `replan`. A execução é idempotente: rodar de novo sem merge novo não propõe nada. A demanda de follow-up (cl-2) continua sendo uma por feature. O modo roadmap (0028) chama `replan` depois de cada merge que observar, sem regra própria.

<!-- section: Data touched -->
## Data touched

- **Leitura:** `roadmap.md` (0023), headers de `spec.md`, `plan.md`, `tasks.md`, `analysis.md` quando existir, `.review-log.jsonl`, `git log` da branch mesclada, saída JSON do `aiadev learn`.
- **Escrita (só após aprovação):** `roadmap.md` (status de entradas e entradas novas).
- **Pacote:** `skills/replan/SKILL.md`, `commands/replan.md`, hand-off em `skills/finishing-a-branch/SKILL.md`, registros de skill (tabela do `CLAUDE.md`, `using-ai-augmented-developer`, `docs/pipeline-reference.md`, `README.md`). Skill genérica: não entra em `presets/catalog.json`, que lista presets.

<!-- section: Out-of-band effects -->
## Out-of-band effects

- Nenhum. Leitura e escrita locais; nenhuma chamada de rede; nenhuma PR ou issue aberta automaticamente.

<!-- section: Open risks -->
## Open risks

- Julgar se uma mudança "cabe numa task" ainda exige leitura do agente; o critério reduz a variação, mas não a elimina (a dúvida vai para o humano).
- Roadmap inflado: cada feature pode gerar várias entradas "grandes" e o roadmap vira backlog sem priorização.
- Um `**Spec:**` preenchido errado no roadmap produz falso "concluído"; o conflito com a *Traceability* da spec é reportado, mas depende de a spec citar a entrada.
- Prosa de reviewer vinda de `learn --show-bodies` não pode vazar para o `roadmap.md` (Artigo VI).

<!-- section: Traceability -->
## Traceability

- Originating issue: comparação do aiadev com o curso "Spec-Driven Development with Coding Agents" (DeepLearning.AI × JetBrains, Paul Everitt) — conversa de 2026-09-24, melhoria 2 de 7.
- Related specs: `0023-product-context` (bloqueante: `roadmap.md`), `0018-aiadev-learn` (fonte secundária), `0026-changelog-skill` (roda antes, no `finishing-a-branch`), `0028-implement-roadmap-mode` (consome o roadmap atualizado).
- Constitution articles invoked: I, II, III, IV, VI

### Constitution Check (preliminar)

> Avaliação no nível da spec. O `plan` refaz a checagem com evidência concreta.

| Artigo | Aplica? | Avaliação preliminar |
|---|---|---|
| I. Spec-first | Sim | Esta spec; cl-1…cl-5 resolvidas em 2026-09-24. Depende da 0023 (gramática do roadmap já definida). |
| II. Test-first | Sim | Fixtures de roadmap + specs + git log com testes de "marca exatamente o entregue" antes da skill. |
| III. Simplicity | Sim | Reaproveita `metrics.read_spec_header`, relatório do `analyze` e saída JSON do `learn`; nenhum parser novo de spec. |
| IV. Evidence over claims | Sim | Toda mudança de escopo cita arquivo:linha, id de task ou hash de commit. |
| V. Provider pattern | Não | Sem fronteira de rede. |
| VI. Privacy by design | Sim | Prosa de reviewer fora do relatório por padrão, espelhando `learn`/`metrics`. |
| VII. Attribution | Não | Nada adaptado: escrito do zero. A entrada de inspiração do curso SDD no `CREDITS.md` (spec 0023, cl-6) cobre a ideia. |
