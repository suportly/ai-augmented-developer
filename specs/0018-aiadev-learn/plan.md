# Implementation plan: `aiadev learn` — minerar o rastro e propor guia durável

> Produced by the `plan` skill from an approved `spec.md`. This file describes **how** the spec will be realized. Do not rewrite `spec.md` into `plan.md`.

**Branch:** `claude/graphify-aiadev-analysis-oiggl4`
**Date:** 2026-07-18
**Spec:** [spec.md](./spec.md)
**Plan version:** 1
**Language:** pt-BR <!-- mirrors spec.md; write plan prose in this language. -->

---

## Summary

Vamos adicionar um subcomando `aiadev learn` que **consome as primitivas que o `metrics` já expõe** (`read_review_log`, `task_rework_counts`, `first_pass_rate_by_reviewer`, `clarify_iteration_count`) para detectar **padrões de falha recorrentes** entre features, com evidência (specs/reviewers/tasks + contagens) e um **limiar** que evita inventar padrões em amostra pequena. Cada padrão vem com uma **proposta de guia revisável**; `--write` grava as propostas apenas em `specs/_learnings.md` (nunca nos arquivos de guia finais). Read-only por padrão, local, com a prosa de reviewer fora da saída padrão (Artigo VI). O trabalho cabe em ~3 fases / ~9–11 tasks, tocando um novo `src/aiadev/learn.py`, `src/aiadev/commands/learn.py`, `src/aiadev/cli.py`, `docs/learn.md`, `CREDITS.md`, `README.md` e `tests/`.

## Technical context

| Field | Value |
|---|---|
| Active preset | Nenhum — repositório do próprio framework aiadev |
| Language / runtime | Python 3 (CLI `aiadev`, `click`) |
| Primary dependencies | Nenhuma nova. Reusa `src/aiadev/metrics.py` e `src/aiadev/review_log.py` |
| Storage | Filesystem, read-only por padrão; `--write` grava só `specs/_learnings.md` |
| Testing framework | `pytest` + `scripts/validate_skills.py` |
| Target platform(s) | CLI `aiadev` (as 5 plataformas consomem o output, mas o comando é a CLI) |
| Performance budget | Leitura do rastro é O(nº de entradas de review); sem chamada de rede |
| Security considerations | Local, read-only default; prosa de reviewer só com `--show-bodies` (Artigo VI); sem log novo com PII |

## Constitution check

| Article | Applies? | Status | Evidence |
|---|---|---|---|
| I. Spec-first | Yes | PASS | `spec.md` aprovado em 2026-07-18, zero marcadores |
| II. Test-first | Yes | PASS | Toda task começa por um teste que falha (`pytest` sobre `learn.py`/comando) |
| III. Simplicity | Yes | PASS | Reusa as primitivas do `metrics`; detecção determinística com limiar, sem ML; nenhuma abstração nova sem chamador hoje |
| IV. Evidence over claims | Yes | PASS | Saída JSON estável + testes; o PR enumera `pytest`, `aiadev learn --format json` e cola a saída |
| V. Provider pattern | No | N/A | Nenhuma dependência externa com fronteira de rede — comando local read-only |
| VI. Privacy by design | Yes | PASS | Prosa de reviewer fora da saída padrão (espelha `metrics --show-bodies`); read-only default; zero rede; nenhum log novo com PII |
| VII. Attribution | Yes | PASS | `CREDITS.md` credita `headroomlabs-ai/headroom` (comando `headroom learn`) como origem da ideia |
| Preset-specific articles | N/A | N/A | Feature de nível framework |

## Architecture decisions

- **Decisão:** O `learn` consome as funções públicas de `src/aiadev/metrics.py`/`review_log.py`, não relê o rastro por conta própria.
  **Rationale:** Fonte única de verdade para a gramática do `.review-log.jsonl` e das métricas; evita divergência com o `metrics`.
  **Trade-offs:** Acoplamento à superfície pública do módulo `metrics` — mitigado usando só funções documentadas.

- **Decisão:** Detecção **determinística com limiar de evidência** (mínimo de ocorrências / mínimo de features), sem ML/embeddings.
  **Rationale:** Simplicidade (Artigo III), reprodutibilidade e o cenário de "evidência insuficiente" (Story 3 sc2).
  **Trade-offs:** Padrões sutis podem escapar; o limiar precisa de calibração (ver Risks).

- **Decisão:** `--write` grava **somente** `specs/_learnings.md` (artefato de propostas), nunca `rules/` ou `constitution.md`.
  **Rationale:** cl-1/cl-3/cl-5 — humano no loop; a constituição segue o processo de emenda.
  **Trade-offs:** Uma etapa manual a mais para promover uma proposta a regra — desejável.

- **Decisão:** Saída JSON com **schema estável e sem timestamp de execução**, espelhando `metrics --format json`; janela `--since` default 90 dias.
  **Rationale:** Consumo em CI (Story 1 sc3) e consistência com o comando irmão (cl-4).
  **Trade-offs:** Um schema novo a versionar.

## Project structure changes

```text
src/aiadev/learn.py                                (new)      # motor: detecta padrões + monta propostas
src/aiadev/commands/learn.py                       (new)      # subcomando click (--format/--since/--write/--show-bodies)
src/aiadev/cli.py                                  (modified) # registra learn_command
specs/0018-aiadev-learn/contracts/learn-output.schema.json  (follow-up) # schema do JSON (próxima invocação de plan)
docs/learn.md                                      (new)      # uso do comando (espelha docs/metrics.md)
README.md                                          (modified) # seção "Inspecionando... com aiadev learn"
CREDITS.md                                         (modified) # atribuição a headroomlabs-ai/headroom
tests/test_learn.py                                (new)      # motor: padrões + limiar + privacidade
tests/test_learn_command.py                        (new)      # comando: text/json, --write, read-only default
```

## Phase breakdown

### Phase 1 — Motor de detecção de padrões (`learn.py`)

- Consumir as primitivas do `metrics` para agregar sinais recorrentes (reviewer reprovando a mesma categoria; tasks com rework; clarificação repetida) entre features na janela `--since`.
- Aplicar o limiar de evidência; abaixo dele, marcar "evidência insuficiente". Testes primeiro.

### Phase 2 — Comando e saída

- Subcomando `aiadev learn` com saída **texto** (ranqueada, com evidência) e **JSON estável** (`--format json`), `--since` (default 90d) e `--show-bodies` (prosa de reviewer só sob demanda — Artigo VI).
- Registrar em `cli.py`. Testes de text/json e do default read-only.

### Phase 3 — Propostas, docs e atribuição

- Para cada padrão, montar uma proposta de guia; `--write` grava só em `specs/_learnings.md` e relata o caminho.
- `docs/learn.md`, seção no `README.md`, e `CREDITS.md` (Artigo VII).

## Risks and mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Limiar mal calibrado → padrões falsos | Med | Med | Limiar conservador e configurável; teste do caminho "evidência insuficiente" (Story 3 sc2) |
| Acoplamento à superfície interna do `metrics` | Med | Low | Depender só de funções públicas; teste de fumaça se a assinatura mudar |
| Prosa de reviewer vazando para saída compartilhável | Low | High | Default exclui bodies; teste assegura ausência sem `--show-bodies` (Artigo VI) |
| Repo com rastro fino (poucas specs) | High | Low | Caminho "evidência insuficiente" em vez de afirmar padrão |
| Proposta contradiz regra/constituição existente | Med | Low | `learn` só propõe; humano decide; nunca edita `constitution.md` |

## Complexity tracking

> Required when any Constitution Check row is `FAIL`. Empty table if no waivers.

| Article waived | Reason | Alternatives considered | Reviewer |
|---|---|---|---|
| — | Nenhum waiver | — | — |

## Hand-off to `tasks`

The next skill is `tasks`. It consumes this plan and produces `tasks.md`.
Pre-conditions before hand-off:

- [x] Constitution Check is fully populated, no blank rows.
- [x] Complexity tracking is filled or empty-and-justified.
- [x] Project structure delta is accurate.
