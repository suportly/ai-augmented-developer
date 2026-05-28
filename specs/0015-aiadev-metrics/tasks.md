# Tasks: Métricas do aiadev a partir do audit trail existente

> Produced by the `tasks` skill from an approved `plan.md`. Consumed by `implement`.

**Branch:** `feature/aiadev-metrics`
**Plan:** [plan.md](./plan.md)
**Generated:** 2026-05-28
**Language:** pt-BR <!-- mirrors spec.md; write task descriptions in this language. -->

---

## How to read this file

- Tasks são ordenadas. `implement` roda top-to-bottom.
- Uma task = um commit. Mensagem do commit começa com o id da task.
- Cada task aponta de volta para as scenarios de aceitação que exercita.
- `Status` é um de: `pending`, `in_progress`, `blocked`, `done`. Owned pelo skill `implement` — ele vira `pending` → `done` dentro do commit da task. Não editar à mão; edições manuais são sobrescritas no próximo `implement`.

## Task list

### T001 — Montar fixtures de specs em estados variados

- **Status:** done
- **Depends on:** —
- **Files:**
  - create: `tests/fixtures/metrics/pristine_first_pass/specs/0001-x/{spec.md,tasks.md,.review-log.jsonl}`
  - create: `tests/fixtures/metrics/with_rework/specs/0002-y/{spec.md,tasks.md,.review-log.jsonl}`
  - create: `tests/fixtures/metrics/pre_cutoff_no_log/specs/0001-old/{spec.md,tasks.md}` (sem `.review-log.jsonl`, Spec ID ≤ cutoff 10)
  - create: `tests/fixtures/metrics/empty_log/specs/0003-empty/{spec.md,tasks.md,.review-log.jsonl}` (JSONL existe mas é zero-bytes)
  - create: `tests/fixtures/metrics/non_canonical_status/specs/0004-pr-open/{spec.md,tasks.md}` (header com `Status: PR Open` legado)
  - test: `tests/test_metrics_fixtures.py`
- **Spec scenarios:** habilitador para Story 1 sc1/sc2/sc3, Story 2 sc1, Story 3 sc1/sc2/sc3
- **Acceptance:**
  - [ ] `tests/test_metrics_fixtures.py` falha (RED) por cada fixture path não existir.
  - [ ] Fixtures criadas; teste valida (a) cada `spec.md` tem header parseável (`Spec ID`, `Status`, `Created`); (b) cada `.review-log.jsonl` quando presente é JSONL válido linha-a-linha; (c) `pre_cutoff_no_log` não tem `.review-log.jsonl`; (d) `empty_log/.review-log.jsonl` existe com 0 bytes.
  - [ ] Nenhum outro teste regride: `pytest tests/`.
  - [ ] Commit message: `test(metrics): T001 fixtures de specs em estados variados`.
- **Notes:**
  - Use Spec IDs ≥ 14 para fixtures pós-cutoff e ≤ 10 para `pre_cutoff_no_log` (cutoff vem de `schemas/spec-recon.schema.json`).
  - `with_rework` precisa de pelo menos 1 task (ex.: T003) com sequência APPROVED em primeira passada + outra task com CHANGES_REQUESTED → APPROVED.

### T002 — `MetricsReport` + iter_specs_in_window + read_spec_header

- **Status:** done
- **Depends on:** T001
- **Files:**
  - create: `src/aiadev/metrics.py`
  - test: `tests/test_metrics.py` (adiciona `test_metrics_report_shape`, `test_iter_specs_in_window`, `test_read_spec_header`, `test_read_spec_header_tolerates_non_canonical_status`)
- **Spec scenarios:** Story 1 sc2 (header pre-cutoff detectável), Story 2 sc2 (filtro por `Created:`), spec "Open risks" item 5 (parser defensivo)
- **Acceptance:**
  - [ ] RED: testes falham por `MetricsReport`, `iter_specs_in_window`, `read_spec_header` não existirem.
  - [ ] GREEN: `MetricsReport` é dataclass frozen com os campos do plan/ADR (`window`, `n_specs_in_window`, `coverage_percent`, `per_reviewer_first_pass_rate`, `tasks_by_status`, `tasks_with_rework`, `specify_to_last_commit_median_days`, `unresolved_clarifications_count`, `disclaimer_lines`, `unknown_status_count`).
  - [ ] `iter_specs_in_window(workspace, since, until)` percorre `workspace/specs/*/spec.md` e yielda apenas os com `Created:` ∈ [since, until].
  - [ ] `read_spec_header(path)` retorna dict com `spec_id` (int), `status` (one of canonical | `"other"`), `created` (`datetime.date`); status `"PR Open"` bucketiza como `"other"` sem raise.
  - [ ] Nenhum outro teste regride.
  - [ ] Commit: `feat(metrics): T002 MetricsReport + iter_specs_in_window + read_spec_header`.

### T003 — read_review_log (tolerante a log vazio e linhas malformadas)

- **Status:** done
- **Depends on:** T001
- **Files:**
  - modify: `src/aiadev/metrics.py`
  - test: `tests/test_metrics.py` (adiciona `test_read_review_log_empty_file`, `test_read_review_log_missing_file`, `test_read_review_log_skips_blank_lines`, `test_read_review_log_returns_entries_in_file_order`)
- **Spec scenarios:** Story 1 sc3 (log vazio → `n=0` sem falhar)
- **Acceptance:**
  - [ ] RED: testes falham por `read_review_log` não existir.
  - [ ] GREEN: `read_review_log(jsonl_path)` retorna `list[dict]` em ordem de arquivo; missing file → `[]`; empty file → `[]`; linhas em branco e JSON malformado são puladas silenciosamente (mesma tolerância de `aiadev.review_log.last_entry_from_log`).
  - [ ] Reuso: a função delega a leitura tolerante a `aiadev.review_log` quando útil em vez de duplicar o parser.
  - [ ] Commit: `feat(metrics): T003 read_review_log tolerante`.

### T004 — first_pass_rate_by_reviewer (cl-6: ordem cronológica)

- **Status:** done
- **Depends on:** T003
- **Files:**
  - modify: `src/aiadev/metrics.py`
  - test: `tests/test_metrics.py` (adiciona `test_first_pass_pristine_all_approved`, `test_first_pass_with_rework`, `test_first_pass_groups_branch_review_separately`, `test_first_pass_per_reviewer_type`)
- **Spec scenarios:** Story 1 sc1, Story 3 sc2 (todas 1ª passada)
- **Acceptance:**
  - [ ] RED: testes falham por `first_pass_rate_by_reviewer` não existir.
  - [ ] GREEN: agrupa entries por `(task_id, reviewer)`, ordena por `timestamp`, marca a primeira como first-pass; retorna dict `{reviewer_type: (first_pass_count, total_count)}`. Para entries com `task_id == "branch-review"`, agrupa apenas por `(reviewer,)` (sem prefixar task).
  - [ ] Fixture `pristine_first_pass` deve produzir 100% em todos os reviewer types; `with_rework` deve produzir < 100% no `code-reviewer`.
  - [ ] Commit: `feat(metrics): T004 first_pass_rate cl-6`.

### T005 — task_rework_counts (Story 3)

- **Status:** done
- **Depends on:** T003
- **Files:**
  - modify: `src/aiadev/metrics.py`
  - test: `tests/test_metrics.py` (adiciona `test_task_rework_counts_returns_rounds_descending`, `test_task_rework_counts_empty_when_pristine`, `test_task_rework_counts_only_counts_code_reviewer_rounds`)
- **Spec scenarios:** Story 3 sc1 (ordem descendente), Story 3 sc2 (vazio quando pristine)
- **Acceptance:**
  - [ ] RED: testes falham.
  - [ ] GREEN: `task_rework_counts(entries)` retorna `list[tuple[task_id, rounds]]` ordenado por `rounds` desc, considerando apenas entries do `code-reviewer` por task (não branch-level). Inclui só tasks com ≥ 1 `CHANGES_REQUESTED`.
  - [ ] Commit: `feat(metrics): T005 task_rework_counts`.

### T006 — read_tasks_status integration

- **Status:** done
- **Depends on:** T001
- **Files:**
  - modify: `src/aiadev/metrics.py`
  - test: `tests/test_metrics.py` (adiciona `test_tasks_by_status_counts_buckets`, `test_tasks_by_status_handles_missing_tasks_md`)
- **Spec scenarios:** Story 1 sc1 (contagem de tasks por status), Story 1 sc2 (tasks count ainda funciona sem trail)
- **Acceptance:**
  - [ ] RED: testes falham.
  - [ ] GREEN: `tasks_by_status(spec_dir)` retorna `dict[str, int]` com chaves `pending|in_progress|blocked|done` (zero para ausentes); delega o parse para `aiadev.tasks_status` (sem duplicar regex); `tasks.md` ausente → todos zeros.
  - [ ] Commit: `feat(metrics): T006 tasks_by_status via aiadev.tasks_status`.

### T007 — Métricas git-based: clarify_iterations + specify_to_last_commit (injetáveis)

- **Status:** done
- **Depends on:** T001
- **Files:**
  - modify: `src/aiadev/metrics.py`
  - test: `tests/test_metrics.py` (adiciona `test_clarify_iteration_count_from_log_text`, `test_specify_to_last_commit_days`, `test_git_metrics_no_history_yields_none`)
- **Spec scenarios:** Story 2 sc3 (determinismo histórico — funções aceitam input puro), Recon bullet "markers cl-N"
- **Acceptance:**
  - [ ] RED: testes falham.
  - [ ] GREEN: `clarify_iteration_count(spec_id, git_log_output: str)` parseia ocorrências de markers `cl-N` adicionados/removidos por commit no arquivo `specs/<NNNN>-*/spec.md`; `specify_to_last_commit_days(spec_id, git_log_output: str, today: date)` extrai a diferença em dias entre o primeiro commit que cria `spec.md` e o commit mais recente. Ambas aceitam string injetada — não chamam `subprocess` diretamente (subprocess fica no CLI layer, T011).
  - [ ] Sem histórico (output vazio) → retorna `None` em ambas, sem raise.
  - [ ] Commit: `feat(metrics): T007 git-based metrics com input injetável`.

### T008 — build_report top-level composition

- **Status:** done
- **Depends on:** T002, T003, T004, T005, T006, T007
- **Files:**
  - modify: `src/aiadev/metrics.py`
  - test: `tests/test_metrics.py` (adiciona `test_build_report_single_feature_pristine`, `test_build_report_aggregate_window`, `test_build_report_coverage_calculation`, `test_build_report_includes_disclaimer_lines`)
- **Spec scenarios:** Story 1 sc1, Story 2 sc1 (coverage% explícito)
- **Acceptance:**
  - [ ] RED: testes falham por `build_report` não existir.
  - [ ] GREEN: `build_report(workspace, *, feature=None, since=None, until=None, git_log_provider=None) -> MetricsReport`. Quando `feature` é dado, restringe a uma spec; senão usa `iter_specs_in_window`. `coverage_percent = round(100 * specs_with_review_log / n_specs_in_window, 1)`. `disclaimer_lines` é lista fixa de strings, uma por métrica (texto definido no spec — "o que isso NÃO significa").
  - [ ] Commit: `feat(metrics): T008 build_report composition`.

### T009 — format_text com disclaimer lines

- **Status:** done
- **Depends on:** T008
- **Files:**
  - create: `src/aiadev/metrics_format.py`
  - test: `tests/test_metrics_format.py` (snapshot tests `test_format_text_pristine`, `test_format_text_with_rework`, `test_format_text_empty_log`, `test_format_text_partial_sample_header`)
- **Spec scenarios:** Story 2 sc1 (coverage), Story 1 sc3 (mensagem "review trail: vazio"), Story 3 sc3 (header `6/10 tasks reached review`)
- **Acceptance:**
  - [ ] RED: arquivo não existe.
  - [ ] GREEN: `format_text(report) -> str` emite saída human-friendly; inclui linha por métrica explicando "o que NÃO significa"; quando `n=0` para review trail, imprime "review trail: vazio (feature ainda no estágio de implement)" em vez de números zerados; quando Story 3 está ativa e amostra é parcial, prefixa com `M/N tasks reached review`.
  - [ ] Snapshot files em `tests/snapshots/metrics/text/*.txt` (criados na 1ª passada do test runner).
  - [ ] Commit: `feat(metrics): T009 format_text com disclaimers`.

### T010 — format_json com schema estável

- **Status:** done
- **Depends on:** T008
- **Files:**
  - modify: `src/aiadev/metrics_format.py`
  - test: `tests/test_metrics_format.py` (adiciona `test_format_json_pristine`, `test_format_json_includes_schema_version`, `test_format_json_no_execution_timestamps`, `test_format_json_keys_are_snake_case`)
- **Spec scenarios:** Story 2 sc3 (determinismo histórico — output JSON estável e reproduzível)
- **Acceptance:**
  - [ ] RED: testes falham.
  - [ ] GREEN: `format_json(report) -> str` produz JSON válido com `schema_version: 1` no top-level; **não** inclui timestamp de execução (apenas timestamps que vêm dos dados); todas as chaves são `snake_case`; floats arredondados a 1 casa decimal.
  - [ ] Commit: `feat(metrics): T010 format_json schema v1`.

### T011 — Registrar subcomando `metrics` com `--feature` + wire git subprocess

- **Status:** done
- **Depends on:** T008, T009, T010
- **Files:**
  - create: `src/aiadev/commands/metrics.py`
  - modify: `src/aiadev/cli.py` (registra o novo subcomando no group)
  - test: `tests/test_metrics_command.py` (adiciona `test_metrics_feature_pristine_exit_0`, `test_metrics_feature_pre_cutoff_exit_2`, `test_metrics_feature_empty_log_exit_0`)
- **Spec scenarios:** Story 1 sc1, sc2, sc3
- **Acceptance:**
  - [ ] RED: testes falham por subcomando não existir.
  - [ ] GREEN: `aiadev metrics --feature <slug>` resolve `<slug>` da mesma forma que `aiadev preflight` (aceita `NNNN-slug` ou o slug bare); o CLI layer faz `subprocess.run(["git", "log", "-p", "--name-only", "--", "specs/"])` e passa o output para `build_report` via `git_log_provider`; chama `format_text` por default; exit code: 0 se `n_specs_in_window > 0` OR feature específica encontrada, 2 se feature pre-cutoff sem `.review-log.jsonl` (Story 1 sc2).
  - [ ] CliRunner: cada cenário roda contra fixtures de T001 e asserta exit code + substring esperada.
  - [ ] Commit: `feat(metrics): T011 subcomando metrics --feature`.

### T012 — Flags `--since` + `--format` + window default 90d

- **Status:** done
- **Depends on:** T011
- **Files:**
  - modify: `src/aiadev/commands/metrics.py`
  - test: `tests/test_metrics_command.py` (adiciona `test_metrics_since_filters_on_created`, `test_metrics_format_json_emits_valid_json`, `test_metrics_default_window_is_90_days`, `test_metrics_aggregate_shows_interval_in_first_line`)
- **Spec scenarios:** Story 2 sc1, sc2, sc3
- **Acceptance:**
  - [ ] RED: testes falham.
  - [ ] GREEN: `--since YYYY-MM-DD` sobrescreve o default 90 dias; default é `today - 90d` (relativo ao clock real, mas testes injetam `--today` se necessário — adicionar esse parâmetro escondido `--today` que aceita override em test mode); `--format json` chama `format_json`; primeira linha do `text` output mostra `Janela: [YYYY-MM-DD, YYYY-MM-DD]`.
  - [ ] Commit: `feat(metrics): T012 flags --since e --format`.

### T013 — Flags `--tasks` + `--show-bodies` + exit-code policy

- **Status:** done
- **Depends on:** T011
- **Files:**
  - modify: `src/aiadev/commands/metrics.py`
  - modify: `src/aiadev/metrics_format.py` (adiciona seção Story 3 e gate de bodies)
  - test: `tests/test_metrics_command.py` (adiciona `test_metrics_tasks_lists_rework_descending`, `test_metrics_tasks_no_rework_message`, `test_metrics_show_bodies_includes_note_field`, `test_metrics_no_show_bodies_omits_note_field`, `test_metrics_parse_error_exit_1`, `test_metrics_no_data_in_window_exit_2`)
- **Spec scenarios:** Story 3 sc1, sc2, sc3; exit-code policy do plan ADR-7
- **Acceptance:**
  - [ ] RED: testes falham.
  - [ ] GREEN: `--tasks` ativa a listagem de tasks com rework em ordem desc + header parcial-sample quando aplicável; quando não há rework, emite "todas as tasks aprovadas em 1ª passada"; `--show-bodies` é o **único** caminho que faz o `note` field aparecer no output (text ou json); spec.md com header não-parseável tolera bucket "other" e segue; spec.md inteiramente quebrado (sem `Spec ID` parseável) → exit 1 com mensagem citando o path; janela sem nenhum spec coberto → exit 2 citando o cutoff `spec 0014`.
  - [ ] Commit: `feat(metrics): T013 flags --tasks --show-bodies + exit codes`.

### T014 — Documentação e changelog

- **Status:** done
- **Depends on:** T013
- **Files:**
  - modify: `docs/pipeline-reference.md`
  - modify: `README.md`
  - modify: `CHANGELOG.md`
  - test: `tests/test_metrics_docs.py` (novo — asserta presença de seção `## aiadev metrics` em `docs/pipeline-reference.md` e bloco de exemplo em `README.md` mencionando `aiadev metrics`)
- **Spec scenarios:** Article IV (Evidence over claims) — PR test plan precisa apontar para docs atualizadas
- **Acceptance:**
  - [ ] RED: teste falha.
  - [ ] GREEN: `docs/pipeline-reference.md` ganha seção descrevendo o subcomando, suas flags, e os 3 exit codes; `README.md` ganha um exemplo de 4-6 linhas em Usage demonstrando uma invocação real; `CHANGELOG.md [Unreleased]` ganha entrada `### Added` com link para [spec 0015](../specs/0015-aiadev-metrics/spec.md).
  - [ ] `markdownlint-cli2` continua passando em todos os arquivos tocados.
  - [ ] Commit: `docs(metrics): T014 pipeline reference + README + CHANGELOG`.

## Parallelization hints

Tasks que tocam arquivos disjuntos podem ser executadas em paralelo se a plataforma suportar. `implement` ainda dispatcha serial — esta seção é informativa.

- Parallel group A (após T001): **T002, T003, T006** — disjuntos em metrics.py via funções distintas (mas todas mexem no mesmo arquivo, então sequenciais na prática).
- Parallel group B (após T003): **T004, T005** — ambos consomem review log mas implementam funções independentes.
- Parallel group C (após T008): **T009, T010** — arquivos distintos (`metrics_format.py` aceita ambos, mas as funções não compartilham estado).
- Parallel group D (após T011): **T012, T013** — mesma file mas seções diferentes; safer rodar serial.
- Serial: T001 → (A) → (B) → T007 → T008 → (C) → T011 → (D) → T014.

## Post-task checklist

Comando de teste padrão para validar o estado completo após cada commit:

```bash
pytest tests/test_metrics.py tests/test_metrics_format.py tests/test_metrics_command.py tests/test_metrics_fixtures.py tests/test_metrics_docs.py -v
```

E o smoke run do subcomando contra o próprio repo (deve passar sem erro após T011+):

```bash
aiadev metrics --feature 0015-aiadev-metrics
aiadev metrics --format json --since 2026-02-28
```
