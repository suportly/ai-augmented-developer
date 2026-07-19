# Tasks: `aiadev learn` — minerar o rastro e propor guia durável

> Produced by the `tasks` skill from an approved `plan.md`. Consumed by `implement`.

**Branch:** `claude/graphify-aiadev-analysis-oiggl4`
**Plan:** [plan.md](./plan.md)
**Generated:** 2026-07-18
**Language:** pt-BR <!-- mirrors spec.md; write task descriptions in this language. -->

---

## How to read this file

- Tasks are ordered. `implement` runs them top-to-bottom.
- One task = one commit. The commit message starts with the task id.
- Each task links back to the spec acceptance scenarios it exercises.
- `Status` is one of: `pending`, `in_progress`, `blocked`, `done`. Owned by the `implement` skill — it flips `pending` → `done` inside each task's commit. Do not edit by hand; manual edits are overwritten on the next `implement` run.

**Escopo v1:** estas tasks realizam as Fases 1–3 do plano e cobrem as Stories 1, 2 e 3 completas. `AGENTS.md`/`checklist` como alvos de escrita e a promoção automática de propostas ficam para fast-follow (cl-1).

## Task list

### T001 — Motor: recorrência de reprovação por reviewer

- **Status:** done
- **Depends on:** —
- **Files:**
  - create: `src/aiadev/learn.py`
  - test: `tests/test_learn.py`
- **Spec scenarios:** Story 1 scenario 1
- **Acceptance:**
  - [ ] Failing test written and observed failing: `test_detects_recurring_reviewer_failure`.
  - [ ] `learn.py` consome as primitivas do `metrics`/`review_log` e retorna um padrão quando o mesmo reviewer reprova o first-pass em ≥ N features, com evidência (specs + contagem). O rastro não tem "categoria"; o sinal é por reviewer.
  - [ ] No other existing test regresses.
  - [ ] Commit message: `feat(learn): T001 motor detecta recorrência de reviewer`.
- **Notes:** Depende só de funções públicas de `src/aiadev/metrics.py`.

### T002 — Motor: recorrência de rework de tasks

- **Status:** done
- **Depends on:** T001
- **Files:**
  - modify: `src/aiadev/learn.py`
  - test: `tests/test_learn.py`
- **Spec scenarios:** Story 1 scenario 2
- **Acceptance:**
  - [ ] Failing test written and observed failing: `test_detects_task_rework_pattern`.
  - [ ] Via `task_rework_counts`, o motor reporta o padrão de rework com os ids de task/spec de evidência.
  - [ ] No other existing test regresses.
  - [ ] Commit message: `feat(learn): T002 motor detecta rework de tasks`.
- **Notes:** Mesmo módulo de T001 — serial.

### T003 — Motor: limiar de evidência e "evidência insuficiente"

- **Status:** done
- **Depends on:** T002
- **Files:**
  - modify: `src/aiadev/learn.py`
  - test: `tests/test_learn.py`
- **Spec scenarios:** Story 3 scenario 2
- **Acceptance:**
  - [ ] Failing test written and observed failing: `test_thin_trail_marks_insufficient_evidence`.
  - [ ] Abaixo do limiar (mín. de ocorrências/features), o padrão é marcado "evidência insuficiente" em vez de afirmado.
  - [ ] No other existing test regresses.
  - [ ] Commit message: `feat(learn): T003 limiar de evidência`.
- **Notes:** Limiar conservador e configurável.

### T004 — Motor: prosa de reviewer fora do padrão por default (Artigo VI)

- **Status:** done
- **Depends on:** T003
- **Files:**
  - modify: `src/aiadev/learn.py`
  - test: `tests/test_learn.py`
- **Spec scenarios:** Story 3 scenario 1
- **Acceptance:**
  - [ ] Failing test written and observed failing: `test_bodies_excluded_by_default`.
  - [ ] Os objetos de padrão não carregam a prosa livre do reviewer a menos que `show_bodies=True`.
  - [ ] No other existing test regresses.
  - [ ] Commit message: `feat(learn): T004 exclui prosa de reviewer por default`.
- **Notes:** Espelha a política do `metrics --show-bodies`.

### T005 — Comando `aiadev learn` com saída texto ranqueada

- **Status:** pending
- **Depends on:** T001
- **Files:**
  - create: `src/aiadev/commands/learn.py`
  - modify: `src/aiadev/cli.py`
  - test: `tests/test_learn_command.py`
- **Spec scenarios:** Story 1 scenario 1, Story 1 scenario 2
- **Acceptance:**
  - [ ] Failing test written and observed failing: `test_learn_text_output_ranks_patterns`.
  - [ ] `aiadev learn` (click) imprime os padrões ranqueados com evidência; registrado em `cli.py` via `main.add_command`.
  - [ ] No other existing test regresses.
  - [ ] Commit message: `feat(learn): T005 comando learn (saída texto)`.
- **Notes:** Espelha a forma de `src/aiadev/commands/metrics.py`.

### T006 — Comando: `--format json` estável (sem timestamp)

- **Status:** pending
- **Depends on:** T005
- **Files:**
  - modify: `src/aiadev/commands/learn.py`
  - test: `tests/test_learn_command.py`
- **Spec scenarios:** Story 1 scenario 3
- **Acceptance:**
  - [ ] Failing test written and observed failing: `test_learn_json_is_stable`.
  - [ ] `--format json` emite schema fixo, sem timestamp de execução, consumível por CI.
  - [ ] No other existing test regresses.
  - [ ] Commit message: `feat(learn): T006 saída json estável`.
- **Notes:** Mesmo arquivo de T005 — serial.

### T007 — Comando: janela `--since` (default 90 dias)

- **Status:** pending
- **Depends on:** T006
- **Files:**
  - modify: `src/aiadev/commands/learn.py`
  - test: `tests/test_learn_command.py`
- **Spec scenarios:** Story 1 scenario 3
- **Acceptance:**
  - [ ] Failing test written and observed failing: `test_learn_since_window_defaults_90d`.
  - [ ] `--since` filtra a janela de agregação; default 90 dias, espelhando `metrics`.
  - [ ] No other existing test regresses.
  - [ ] Commit message: `feat(learn): T007 janela --since`.
- **Notes:** Mesmo arquivo de T005 — serial.

### T008 — Comando: read-only por default e sem rede

- **Status:** pending
- **Depends on:** T007
- **Files:**
  - modify: `src/aiadev/commands/learn.py`
  - test: `tests/test_learn_command.py`
- **Spec scenarios:** Story 2 scenario 3, Story 3 scenario 3
- **Acceptance:**
  - [ ] Failing test written and observed failing: `test_learn_readonly_default_no_writes`.
  - [ ] Sem `--write`, nenhum arquivo é modificado; nenhuma chamada de rede é feita.
  - [ ] No other existing test regresses.
  - [ ] Commit message: `feat(learn): T008 read-only default`.
- **Notes:** Mesmo arquivo de T005 — serial.

### T009 — Motor: proposta de guia por padrão (trecho + arquivo-alvo)

- **Status:** pending
- **Depends on:** T004
- **Files:**
  - modify: `src/aiadev/learn.py`
  - test: `tests/test_learn.py`
- **Spec scenarios:** Story 2 scenario 1
- **Acceptance:**
  - [ ] Failing test written and observed failing: `test_pattern_carries_proposal_and_target`.
  - [ ] Cada padrão traz um trecho de guia sugerido e o arquivo-alvo proposto (uma regra em `rules/`).
  - [ ] No other existing test regresses.
  - [ ] Commit message: `feat(learn): T009 propostas de guia por padrão`.
- **Notes:** O alvo é `rules/`; nunca `constitution.md` (cl-3).

### T010 — Comando: `--write` grava em `specs/_learnings.md`

- **Status:** pending
- **Depends on:** T008, T009
- **Files:**
  - modify: `src/aiadev/commands/learn.py`
  - test: `tests/test_learn_command.py`
- **Spec scenarios:** Story 2 scenario 2
- **Acceptance:**
  - [ ] Failing test written and observed failing: `test_learn_write_lands_in_learnings_file`.
  - [ ] `--write` grava as propostas em `specs/_learnings.md` (não em arquivos de guia finais) e relata o caminho.
  - [ ] No other existing test regresses.
  - [ ] Commit message: `feat(learn): T010 --write em specs/_learnings.md`.
- **Notes:** Único destino de escrita da v1 (cl-1/cl-5).

### T011 — Docs, README e atribuição (Artigo VII)

- **Status:** pending
- **Depends on:** T005
- **Files:**
  - create: `docs/learn.md`
  - modify: `README.md`
  - modify: `CREDITS.md`
  - test: `tests/test_learn_docs_and_credits.py`
- **Spec scenarios:** Story 2 scenario 1
- **Acceptance:**
  - [ ] Failing test written and observed failing: `test_learn_documented_and_credits_headroom`.
  - [ ] `docs/learn.md` documenta o uso; `README.md` ganha a seção do comando; `CREDITS.md` credita `headroomlabs-ai/headroom` (link + ideia adaptada).
  - [ ] No other existing test regresses.
  - [ ] Commit message: `docs(learn): T011 docs, README e atribuição`.
- **Notes:** Artigo VII não é waivable.

## Parallelization hints

- Parallel group A: T001 e T011-CREDITS tocam arquivos disjuntos, mas T011 depende de T005 (README cita o comando) — mantê-lo serial após a Fase 2 é mais seguro.
- Serial: T001→T002→T003→T004→T009 (mesmo `learn.py`); T005→T006→T007→T008→T010 (mesmo `commands/learn.py`); T010 depende de T009.

## Post-task checklist

After every task:

- [ ] Commit message references the task id.
- [ ] Status in this file updated.

After all tasks:

- [ ] Full test suite passes (`python3 -m pytest && python3 scripts/validate_skills.py`).
- [ ] `analyze` skill runs and reports no drift vs spec / plan.
- [ ] Hand off to `requesting-code-review` to open the PR.
