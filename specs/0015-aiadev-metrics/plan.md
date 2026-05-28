# Implementation plan: Métricas do aiadev a partir do audit trail existente

> Produced by the `plan` skill from an approved `spec.md`. This file describes **how** the spec will be realized. Do not rewrite `spec.md` into `plan.md`.

**Branch:** `feature/aiadev-metrics`
**Date:** 2026-05-28
**Spec:** [spec.md](./spec.md)
**Plan version:** 1
**Language:** pt-BR <!-- mirrors spec.md; write plan prose in this language. -->

---

## Summary

Adicionar o subcomando `aiadev metrics` que lê o audit trail já existente (`.review-log.jsonl`, `tasks.md`, headers de `spec.md`, git log) e emite indicadores estruturados em dois formatos (`text` default + `--format json`). A implementação separa um *core* puro (calculadora) de uma camada CLI fina, espelhando o padrão `review_log.py` ↔ `commands/preflight.py` já estabelecido. Trabalho dividido em 4 fases (core → formatters → CLI → docs) sobre ~10-12 tasks, em ~6-8 horas de implementação. Nenhum schema novo, nenhuma rede, nenhuma escrita no repo.

## Technical context

| Field | Value |
| --- | --- |
| Active preset | framework root (sem preset de consumidor ativo) |
| Language / runtime | Python ≥ 3.10 (alinhado com `pyproject.toml` deste repo) |
| Primary dependencies | stdlib (`json`, `pathlib`, `datetime`, `subprocess`, `dataclasses`, `re`); `click` (já presente em `src/aiadev/cli.py`) |
| Storage | leitura somente: `specs/<NNNN-slug>/{spec.md,tasks.md,.review-log.jsonl}` + `git log` via `subprocess` |
| Testing framework | pytest (convenção atual de `tests/`); fixtures em `tests/fixtures/metrics/` espelhando o padrão de `tests/fixtures/pipeline_state/` |
| Target platform(s) | qualquer plataforma onde `aiadev` já roda (macOS, Linux, Windows via pipx) |
| Performance budget | `aiadev metrics --feature <slug>`: p95 < 2 s · `aiadev metrics` (agregado em janela 90 d, repo com ≤ 100 specs): p95 < 3 s |
| Security considerations | nenhuma chamada de rede; nenhuma credencial; nenhuma nova linha de log; corpos livres de reviewer só vazam com `--show-bodies` (cl-3 resolvido) |

## Constitution check

| Article | Applies? | Status | Evidence |
| --- | --- | --- | --- |
| I. Spec-first | Yes | PASS | [spec.md](./spec.md) aprovado em 2026-05-28; `aiadev preflight plan --feature 0015-aiadev-metrics` retornou exit 0; zero markers `cl-N` pendentes |
| II. Test-first | Yes | PASS | cada task na fase 1 começa por um teste vermelho em `tests/test_metrics.py` que exercita um cenário do spec; fixtures em `tests/fixtures/metrics/` são montadas antes do implementador escrever a calculadora |
| III. Simplicity | Yes | PASS | `MetricsReport` é a única abstração nova e tem ≥ 2 chamadores reais (text formatter + json formatter); zero novas dependências; cada flag (`--feature`, `--since`, `--format`, `--tasks`, `--show-bodies`) tem user story nomeada no spec |
| IV. Evidence over claims | Yes | PASS | a feature *é* sobre evidência (tornar o audit trail consultável); o PR final lista comandos `pytest tests/test_metrics.py tests/test_metrics_format.py tests/test_metrics_command.py -v` com saída anexada |
| V. Provider pattern | No | N/A | nenhuma dependência externa com network boundary; `subprocess.run(["git", ...])` é uso de ferramenta local, mesmo padrão de `review_log.py` |
| VI. Privacy by design | Yes | PASS | output default é contagens/timestamps/flags estruturadas; corpos livres de reviewer só com `--show-bodies` explícito (cl-3); nenhuma nova log line; nenhum dado persistido fora do que já existe |
| VII. Attribution | No | N/A | nada adaptado de outro projeto; código novo greenfield sobre substrato existente do próprio repo |
| Preset-specific articles | None | N/A | framework root não tem preset ativo |

## Architecture decisions

**ADR-1: Separar core puro (`metrics.py`) da camada CLI (`commands/metrics.py`)**
- *Decision:* `src/aiadev/metrics.py` expõe `MetricsReport` (dataclass) + funções puras de leitura/cálculo; `src/aiadev/commands/metrics.py` é só registro Click e parsing de flags.
- *Rationale:* Espelha exatamente o split que já existe entre `src/aiadev/review_log.py` (core) e `src/aiadev/commands/preflight.py` (CLI). Permite testar a calculadora sem invocar Click runner; permite reusar o core se um dia houver skill thin-wrapper (cl-5 deixou essa porta aberta sem abrir agora).
- *Trade-off:* Dois arquivos em vez de um. Custo trivial; alinha com convenção estabelecida.

**ADR-2: `MetricsReport` é a única abstração nova; formatters são funções puras**
- *Decision:* `src/aiadev/metrics_format.py` expõe `format_text(report: MetricsReport) -> str` e `format_json(report: MetricsReport) -> str`. Sem classe Formatter abstrata, sem registry.
- *Rationale:* Article III. Duas projections puras sobre a mesma estrutura são o caminho mais simples; cada nova projeção (markdown no futuro, se vier) é uma função adicional, não uma subclasse.
- *Trade-off:* Se um dia houver 5+ formatos, refatorar pra registry; mas YAGNI agora.

**ADR-3: Janela temporal filtra sobre `Created:` do spec header, não sobre git timestamps**
- *Decision:* `--since` (e o default de 90 dias) compara contra `Created: YYYY-MM-DD` parseado do header de `spec.md`.
- *Rationale:* `Created:` é declarado pelo skill `specify` no momento da autoria; git timestamps mudam em rebase/cherry-pick e não refletem quando a spec foi de fato escrita. Determinismo histórico (success criterion #4) exige fonte estável.
- *Trade-off:* Se alguém editar `Created:` manualmente, a janela desloca. Caso raro; aceitável e detectável (git blame).

**ADR-4: `coverage=` = fração de specs no intervalo que têm `.review-log.jsonl` presente, independente de tamanho**
- *Decision:* Um JSONL vazio (tocado, nunca escrito) conta como "covered" mas reporta `n=0` nas métricas dependentes.
- *Rationale:* Definição simples e determinística. Distinção covered/n explicita a diferença entre "feature alcançou o estágio de review" e "feature acumulou entries".
- *Trade-off:* Documentado na linha "o que isso NÃO significa" do output text.

**ADR-5: Stdlib + `subprocess` para git; zero dependências novas**
- *Decision:* Sem `gitpython`, sem `tabulate`, sem `rich`. Output text é montado por f-strings; tabelas com `str.ljust`/`rjust`.
- *Rationale:* Article III. O codebase já invoca git por subprocess em `review_log.py`; sem precedente de dependência nova só para formatação.
- *Trade-off:* Output text menos bonito que `rich` produziria, mas legível e copiável.

**ADR-6: "1ª passada" é inferida no momento da agregação, sem materializar no JSONL**
- *Decision:* `metrics.py` agrupa entries por `(task_id, reviewer)`, ordena por timestamp, e marca a primeira entry de cada grupo como first-pass. Nada é escrito no `.review-log.jsonl`.
- *Rationale:* cl-6 resolvido — JSONL é append-only em ordem cronológica de dispatch, então a ordem do arquivo é o sinal canônico. Adicionar campo `attempt_number` seria mudança de schema sem ganho.
- *Trade-off:* Se um dia o orquestrador re-dispatchar fora de ordem (não ocorre hoje), o cálculo precisa ser revisitado. Risco aceito; documentado no spec.

**ADR-7: Exit codes — 0 com dados, 2 sem dados-na-janela, 1 erro de parse**
- *Decision:* `0` = sucesso (mesmo que `coverage=0%`, desde que pelo menos um spec exista no intervalo). `2` = nenhum spec no intervalo OU 100% dos specs no intervalo são pré-cutoff sem `.review-log.jsonl`. `1` = erro estrutural (spec.md com header não-parseável que não pode ser bucketizado como "other").
- *Rationale:* Convenção Unix: 0 ok, 1 erro, 2 "tudo certo estruturalmente mas amostra vazia" (não erro). Permite scripts em CI distinguirem "métrica caiu pra zero" de "rode novamente, deu erro".
- *Trade-off:* Mais uma regra que precisa ser testada; vale.

## Project structure changes

```text
src/aiadev/metrics.py                            (new)        — MetricsReport dataclass + readers/calculators
src/aiadev/metrics_format.py                     (new)        — format_text, format_json
src/aiadev/commands/metrics.py                   (new)        — Click subcommand, flag parsing, exit-code policy
src/aiadev/cli.py                                (modified)   — register the new metrics subcommand
tests/test_metrics.py                            (new)        — calculator unit tests (per metric)
tests/test_metrics_format.py                     (new)        — snapshot tests for text + json outputs
tests/test_metrics_command.py                    (new)        — Click CliRunner integration; exit-code assertions
tests/fixtures/metrics/                          (new)        — fixture specs with varied trail states
tests/fixtures/metrics/pristine_first_pass/      (new)        — spec mergeada, todos reviews APPROVED em 1ª passada
tests/fixtures/metrics/with_rework/              (new)        — spec com CHANGES_REQUESTED → APPROVED em pelo menos uma task
tests/fixtures/metrics/pre_cutoff_no_log/        (new)        — spec antiga sem .review-log.jsonl
tests/fixtures/metrics/empty_log/                (new)        — .review-log.jsonl presente mas vazio
docs/pipeline-reference.md                       (modified)   — adicionar entrada para metrics subcommand
README.md                                        (modified)   — Usage adiciona exemplo de aiadev metrics
CHANGELOG.md                                     (modified)   — Unreleased "Added: aiadev metrics subcommand"
```

## Phase breakdown

### Phase 1 — Core calculator (read-only, sem CLI ainda)

Foco: ter `metrics.py` cobrindo todos os indicadores do success criteria #1, exercitado por fixtures.

- Definir `MetricsReport` dataclass (campos: `window`, `n_specs_in_window`, `coverage_percent`, `per_reviewer_first_pass_rate`, `tasks_by_status`, `tasks_with_rework`, `specify_to_last_commit_median_days`, `unresolved_clarifications_count`, `disclaimer_lines`).
- Implementar readers: `iter_specs_in_window`, `read_spec_header`, `read_review_log`, `read_tasks_status`, `iter_clarify_versions` (via `git log -p`).
- Implementar calculators: `first_pass_rate_by_reviewer`, `task_rework_counts`, `specify_to_merge_timeline`, `clarify_iterations`.
- Cobrir os edge cases do spec: header não-canônico → bucket "other"; log vazio → `n=0`; pré-cutoff → `coverage` deduz; specs sem tasks.md → ignora gracefully.

### Phase 2 — Formatters

Foco: dois formatos puros sobre `MetricsReport`, com snapshot tests.

- `format_text(report)` — saída humana, inclui linha "o que isso NÃO significa" por métrica.
- `format_json(report)` — schema estável; campos snake_case; sem timestamps de execução (determinismo histórico).
- Snapshot tests para cada fixture × cada formato.

### Phase 3 — CLI integration

Foco: subcomando registrado, flags conforme cl-resolutions, exit codes corretos.

- Registrar `metrics` em `src/aiadev/cli.py` via Click group.
- Flags: `--feature TEXT` (single-feature mode), `--since DATE` (sobrescreve default 90d), `--format [text|json]` (default text), `--tasks` (ativa Story 3 listing), `--show-bodies` (gate de privacy).
- Exit-code policy do ADR-7.
- CliRunner tests cobrindo cada combinação de flag relevante e cada exit code.

### Phase 4 — Docs e changelog

- `docs/pipeline-reference.md`: nova seção descrevendo o subcomando, com exemplos copy-paste.
- `README.md`: bloco curto na seção Usage demonstrando `aiadev metrics --feature 0015-aiadev-metrics`.
- `CHANGELOG.md`: entrada `[Unreleased] Added: aiadev metrics subcommand`.

## Risks and mitigations

| Risk | Likelihood | Impact | Mitigation |
| --- | --- | --- | --- |
| Goodhart — métricas vira target de OKR e degrada como sinal | Med | High | Linha "o que isso NÃO significa" por métrica no output text; explicitamente Non-goal exportar pra dashboard no MVP |
| Amostra pequena pós-0014 produz números ruidosos | High (curto prazo) | Med | `n=` e `coverage=` sempre na saída; `--help` documenta que `n<10` é leitura precoce |
| Specs antigas com header `Status:` não-canônico ("PR Open", legado) quebram parser | Med | Med | Parser defensivo: valores fora do enum atual bucketizam como "other"; warn no stderr (text mode), `unknown_status_count` no json |
| `.review-log.jsonl` grande (feature longa, 500+ entries) estoura budget de 2s | Low | Low | Profilar com fixture de 500 entries durante Phase 1; se virar problema, processar streaming line-by-line (já é JSONL — trivial) |
| Git log lookup em repo com muitas specs (50+) fica lento por causa de N invocações de `git log -- specs/<N>/spec.md` | Med | Med | Phase 1 mede; se virar problema, fazer **uma** invocação de `git log -p --name-only -- specs/` e parsear em memória |
| Mudança no schema da entry futura (campo novo) quebra leitor | Low | Low | Reader tolera campos desconhecidos; assert apenas dos campos que consome (`timestamp`, `reviewer`, `verdict`, `has_why_no_issues_block`, `task_id`) |

## Complexity tracking

> Required when any Constitution Check row is `FAIL`. Empty table if no waivers.

| Article waived | Reason | Alternatives considered | Reviewer |
| --- | --- | --- | --- |
| *(none)* | | | |

## Hand-off to `tasks`

The next skill is `tasks`. It consumes this plan and produces `tasks.md`.
Pre-conditions before hand-off:

- [x] Constitution Check is fully populated, no blank rows.
- [x] Complexity tracking is filled or empty-and-justified.
- [x] Project structure delta is accurate.
