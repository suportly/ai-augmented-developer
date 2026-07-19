# Feature specification: `aiadev learn` — minerar o rastro e propor guia durável

> This file is produced by the `specify` skill (or by `aiadev init --feature <name>` as a stub). Keep it focused on **what** and **why** — planning and code belong in `plan.md` and `tasks.md`.

**Branch:** `claude/graphify-aiadev-analysis-oiggl4`
**Created:** 2026-07-18
**Status:** Approved <!-- Draft | In review | Approved | Implemented -->
**Spec ID:** 0018 <!-- auto-incrementing integer -->
**Language:** pt-BR <!-- BCP-47 tag; every downstream artifact in this feature is written in this language. -->

---

<!-- section: Problem -->
## Problem

O pipeline produz um rastro rico (`.review-log.jsonl`, status de tasks, headers de spec, churn de clarificação) e o `aiadev metrics` já o agrega em indicadores — mas o loop para aí. Sinais recorrentes de falha (um reviewer reprovando sempre a mesma categoria, tasks que sempre precisam de rework, a mesma clarificação pedida spec após spec) nunca viram **guia durável**; o time re-aprende a mesma lição a cada feature. Quem sente: o tech lead que lê o `metrics`, vê o padrão repetir e não tem como cristalizá-lo.

<!-- section: Reconnaissance -->
## Reconnaissance

- **motor de métricas** — entry: `src/aiadev/metrics.py` · auth: none · integration: já expõe `read_review_log`, `first_pass_rate_by_reviewer`, `task_rework_counts`, `tasks_reached_review`, `clarify_iteration_count`, `read_spec_header` — as primitivas que o `learn` agrega.
- **comando metrics (irmão)** — entry: `src/aiadev/commands/metrics.py` · auth: none · integration: `learn` espelha sua forma (click subcommand, `--format json`, `--since`, `--show-bodies` para prosa Artigo VI).
- **log de review** — entry: `src/aiadev/review_log.py` · auth: none · integration: dono da gramática de `.review-log.jsonl` (`append_review_entry`, `read`), fonte primária dos padrões.
- **router da CLI** — entry: `src/aiadev/cli.py` · auth: none · integration: registra subcomandos via `main.add_command(...)`; `learn` entra ao lado de `metrics_command`.
- **alvos de escrita** — entry: `rules/` (guia cross-cutting) e `constitution.md`; o arquivo de agente canônico (`AGENTS.md`) é gerado no consumidor por `src/aiadev/commands/sync.py` · auth: none · integration: destinos possíveis das propostas de edição; nenhum é editado sem revisão humana.

<!-- section: Users and stakeholders -->
## Users and stakeholders

- **Tech lead** — quer que padrões recorrentes de falha virem regra explícita, com evidência, não opinião.
- **Devs do projeto** — beneficiam-se de menos erros repetidos capturados como guia.
- **Mantenedores** — donos dos arquivos que as propostas tocam (`rules/`, `AGENTS.md`); precisam revisar antes de aplicar.

<!-- section: Success criteria -->
## Success criteria

- `aiadev learn` lê o rastro existente (via primitivas do `metrics`) e emite uma lista **ranqueada de padrões de falha recorrentes**, cada um com **evidência** (quais specs/reviewers/tasks, contagens) — não prosa de opinião.
- Para cada padrão, propõe uma **edição de guia concreta e revisável** (um trecho/diff sugerido) apontando um arquivo-alvo; **nunca aplica automaticamente**.
- **Read-only por padrão**: a mineração não escreve nada; propostas só são gravadas com uma flag explícita (`--write`).
- **Privacidade (Artigo VI)**: a prosa livre dos reviewers fica **fora** da saída padrão (espelha `metrics --show-bodies`); nada trafega pela rede — o comando é local e read-only.
- Saída **JSON estável** para CI (como `metrics --format json`), sem timestamp de execução.
- **Degrada com rastro fino**: com poucas specs/entradas, diz "evidência insuficiente" em vez de inventar padrões.

<!-- section: Non-goals -->
## Non-goals

- Aplicar edições automaticamente em qualquer arquivo de guia — proposta é sempre revisada por humano.
- ML/embeddings: é agregação **determinística** sobre o rastro que já existe.
- Mudar o que o pipeline registra (consome o rastro atual; nenhuma telemetria nova).
- Emendar a `constitution.md` automaticamente — emendas seguem o processo documentado (issue + RFC + revisor).
- Mineração de sessões brutas do agente (fora do rastro estruturado do pipeline).

<!-- section: User stories -->
## User stories

### Story 1 — Padrões de falha recorrentes a partir do rastro (P1)

As a tech lead, I want que o `aiadev learn` me mostre os padrões de falha que se repetem entre features, com evidência so that eu decida o que merece virar guia sem vasculhar logs à mão.

**Acceptance scenarios** (Given / When / Then, ≥ 3 per story):

1. Given o mesmo reviewer reprovou o first-pass em ≥ N features (via `first_pass_rate_by_reviewer`), When rodo `aiadev learn`, Then o padrão aparece no topo, citando as specs e a contagem de ocorrências. (Nota: o rastro não carrega "categoria" de reprovação; o sinal é por reviewer, e a prosa do `note` só aparece sob `--show-bodies`.)
2. Given várias tasks precisaram de rework (via `task_rework_counts`), When rodo `aiadev learn`, Then o padrão de rework é reportado com os ids de task/spec de evidência.
3. Given rodo `aiadev learn --format json`, When a saída é gerada, Then é JSON estável (schema fixo, sem timestamp de execução) consumível por CI.

### Story 2 — Propostas de guia revisáveis (P1)

As a mantenedor, I want que cada padrão venha com uma proposta de edição concreta a um arquivo-alvo so that eu possa aceitar/rejeitar com um diff, não reescrever do zero.

**Acceptance scenarios:**

1. Given um padrão recorrente identificado, When rodo `aiadev learn`, Then cada padrão traz um trecho de guia sugerido e o arquivo-alvo proposto (ex.: uma regra em `rules/`).
2. Given rodo `aiadev learn --write`, When há propostas, Then elas são gravadas num artefato de propostas revisável (não nos arquivos de guia finais), e o comando relata o caminho.
3. Given rodo sem `--write`, When o comando termina, Then nenhum arquivo foi modificado (read-only confirmado).

### Story 3 — Privacidade e degradação com rastro fino (P2)

As a tech lead, I want que a mineração respeite privacidade e não invente padrões so that a saída seja confiável e segura de compartilhar.

**Acceptance scenarios:**

1. Given entradas de review contêm prosa livre do reviewer, When rodo `aiadev learn` (sem `--show-bodies`), Then a prosa não aparece na saída padrão (Artigo VI).
2. Given o rastro tem poucas features/entradas abaixo de um limiar, When rodo `aiadev learn`, Then a saída diz "evidência insuficiente" para os padrões afetados em vez de afirmá-los.
3. Given rodo `aiadev learn`, When o comando executa, Then nenhuma chamada de rede é feita (local, read-only).

<!-- section: Clarifications -->
## Clarifications

- **cl-2 (escopo v1):** A v1 entrega o **relatório + `--write`**, mas o `--write` grava apenas num **artefato de propostas** (não nos arquivos de guia finais). Fecha o loop com risco baixo.
- **cl-1 (alvos de escrita):** Só **`rules/`** + o artefato de propostas. `AGENTS.md` e categorias de `checklist` ficam para fast-follow (Artigo III).
- **cl-5 (onde grava):** Um único **`specs/_learnings.md`** — propostas revisáveis, fora dos arquivos de guia vivos.
- **cl-4 (janela):** Espelha o `metrics`: flag **`--since`** com default de **90 dias**.
- **cl-3 (constituição):** O `learn` **nunca** propõe diff na `constitution.md`; no máximo sugere no relatório "considere emendar", deixando o processo documentado (issue + RFC + revisor) intacto.

<!-- section: Data touched -->
## Data touched

- Nenhum dado de produto. Leitura: `.review-log.jsonl`, `tasks.md`, headers de `spec.md` (via primitivas do `metrics`). Escrita (só com `--write`): um artefato de propostas revisável.
- Possível novo schema de saída JSON (padrões + evidência + proposta) para consumo em CI.

<!-- section: Out-of-band effects -->
## Out-of-band effects

- Nenhum. O comando é local e read-only por padrão; não envia notificações, não chama rede, não escreve fora do workspace. `--write` grava apenas um artefato de propostas dentro do próprio repositório.

<!-- section: Open risks -->
## Open risks

- Padrões falsos a partir de amostra pequena — mitigado por limiar de evidência (Story 3 cenário 2), mas o limiar precisa ser calibrado.
- Prosa de reviewer vazando para saída compartilhável (Artigo VI) se `--show-bodies` for mal-usado.
- Uma proposta pode contradizer a constituição ou uma regra existente; o `learn` não resolve conflito — apenas propõe, humano decide.

<!-- section: Traceability -->
## Traceability

- Originating issue: análise comparativa de `headroomlabs-ai/headroom` (comando `headroom learn`) — conversa de 2026-07-18
- Related specs: `0015-aiadev-metrics`, `0014-bmad-inspired-evolutions`, `0009-token-economy-terse-mode`
- Constitution articles invoked: III (Simplicity), IV (Evidence over claims), VI (Privacy by design), VII (Attribution — creditar headroom na implementação)
