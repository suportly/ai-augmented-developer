# Implementation plan: BMAD-inspired framework evolutions

> Produced by the `plan` skill from an approved `spec.md`. This file describes **how** the spec will be realized. Do not rewrite `spec.md` into `plan.md`.

**Branch:** `feature/bmad-inspired-evolutions`
**Date:** 2026-05-13
**Spec:** [spec.md](./spec.md)
**Plan version:** 1
**Language:** pt-BR <!-- mirrors spec.md; write plan prose in this language. -->

---

## Summary

Vamos implementar as 4 user stories do `spec.md` em uma única PR neste branch (cl-7), divididas em 4 fases ordenadas por risco crescente: Fase 1 entrega o módulo `pipeline_state.py` (foundation); Fase 2 paraleliza Story 4 (help state-aware) e Story 3 (zero-findings-halt nos reviewers); Fase 3 entrega o resolver de customização TOML em 3 camadas (Story 2); Fase 4 entrega o skill `task-context` (Story 1) consumindo o flag-pattern de Fase 3. O trabalho é puramente aditivo na superfície CLI e Markdown — nenhum default existente muda. Estimativa: ≈ 18-22 tasks distribuídas em 4 fases, ≈ 800-1200 linhas líquidas (Python + Markdown), tudo dentro do framework repo (`src/aiadev/`, `skills/`, `agents/`, `presets/`, `templates/`, `docs/`).

## Technical context

| Field | Value |
|---|---|
| Active preset | framework repo (sem preset; usa diretamente seus próprios skills) |
| Language / runtime | Python ≥ 3.11 (stdlib `tomllib`); Markdown |
| Primary dependencies | nenhuma nova; `pytest` (já presente), `click` (já presente para CLI) |
| Storage | filesystem (`_aiadev/*.toml`, `specs/<branch>/task-context/*.md`, `specs/<branch>/.review-log.jsonl`) |
| Testing framework | `pytest` (unit + integração); `tests/fixtures/` para resolver/state inspection |
| Target platform(s) | Linux/macOS (CI), Windows (best-effort via `pathlib`) |
| Performance budget | `pipeline_state.recommend_next_command()` ≤ 200 ms em projeto com 50 specs; resolver TOML ≤ 50 ms para merge típico (3 layers, < 200 chaves) |
| Security considerations | parser TOML é stdlib (sem code-exec); `_aiadev/user.toml` em `.gitignore` (não vaza credenciais individuais); nenhum log novo de PII |

## Constitution check

> One row per applicable article from `constitution.md`. `N/A` is allowed
> if the article does not apply to this plan. Every `FAIL` must have a
> corresponding row in **Complexity tracking** below.

| Article | Applies? | Status | Evidence |
|---|---|---|---|
| I. Spec-first | Yes | PASS | `specs/0014-bmad-inspired-evolutions/spec.md` aprovado pelo `spec-document-reviewer` em 2026-05-13 (2ª passada APPROVED após correções) |
| II. Test-first | Yes | PASS | Toda task em `tasks.md` começará com teste falhando (regra do skill `tasks` + Article II); fixtures pytest cobrem resolver TOML, `pipeline_state`, e regra zero-findings-halt antes de qualquer código de implementação |
| III. Simplicity | Yes | PASS | Sem nova abstração sem segundo caller: `pipeline_state.py` tem 2 callers confirmados nesta entrega (skill `help` em Phase 2 + `aiadev preflight` em Phase 2/3) e 1 caller planejado no mesmo spec (extensão VS Code Spec Explorer ganhará surface "next step" — Story 4 do `spec.md` registra como ponto de extensão futuro, ainda no escopo deste feature); resolver TOML tem named user via preset `django-drf-react` (cl-8); flag `task_context: true` ativado no preset principal — sem flags órfãs |
| IV. Evidence over claims | Yes | PASS | Story 3 é literalmente sobre evidência no review (bloco `### Why no issues`); o `aiadev preflight requesting-code-review` falha se a saída do reviewer mais recente em `specs/<branch>/.review-log.jsonl` violar a regra; PR final lista comandos `pytest` e diff stats |
| V. Provider pattern | No | N/A | cl-9: `src/aiadev/customization.py` é módulo interno de leitura/merge TOML, não cruza fronteira de SDK externo (sem rede, sem vendor SDK); resolver é utility puro |
| VI. Privacy by design | No | N/A | Nenhum dado sensível: arquivos de configuração TOML, artefatos de spec, contexto de task — sem PII, sem credenciais, sem campos cifráveis |
| VII. Attribution | Yes | PASS | `CREDITS.md` ganhará entrada para `bmad-code-org/BMAD-METHOD` na Fase 4 (origem das ideias para `task-context`, override 3-camadas, e zero-findings-halt) |
| Preset-specific articles | None applicable | N/A | Trabalho é no repo do framework, não em consumidor de preset |

## Architecture decisions

- **ADR-1 — Opt-in por flag de preset, não automático.** Decisão: `task-context` roda só quando `task_context: true` no `preset.yaml` ativo, ou quando `aiadev preflight implement --task-context` é passado. Rationale: sem usuário nomeado validando custo/benefício real (≈ +1 chamada de modelo por task), virar default fere Article III. Trade-off: adopters precisam opt-in explícito; padrão preserva comportamento atual byte-a-byte.

- **ADR-2 — Resolver de customização: 3 camadas TOML, merge por chave determinístico.** Decisão: `src/aiadev/customization.py` carrega `customize.toml` (base, do skill) → `_aiadev/team.toml` (commitado) → `_aiadev/user.toml` (gitignored), nessa ordem. Regras: (a) scalars seguem precedência (user vence team vence base); (b) tables fazem deep-merge; (c) arrays-of-tables matcham por chave `code` ou `id` (replace-or-append); (d) parse error em qualquer camada aborta com `file:line` — nunca silencia. Rationale: padrão BMAD validado em produção, `tomllib` é stdlib (zero dep), suporta comentários (essencial para arquivos de config humanos). Trade-off: não usa YAML existente (`mcps.yaml`) — heterogeneidade de formatos no repo, mas ganho de tipagem explícita justifica.

- **ADR-3 — `pipeline_state.py` como módulo único reusado por superfícies múltiplas.** Decisão: lógica de "qual o próximo comando" mora em `src/aiadev/pipeline_state.py` exposta como `recommend_next_command(workspace_path: Path) -> dict`. Consumida por (a) `skills/help/SKILL.md` via `python -c` — confirmado nesta entrega, (b) comandos `aiadev preflight` — confirmado nesta entrega, (c) extensão VS Code Spec Explorer — surface "next step" planejada como ponto de extensão futuro registrado na Story 4 do `spec.md`. Rationale: 2 callers confirmados nesta entrega + 1 planejado, evita duplicação de regras de transição (spec → clarify → plan → tasks → implement → review → finishing). Testável determinísticamente via fixtures de filesystem. Trade-off: skill `help` deixa de ser leaf puro — passa a depender do módulo Python; mitigado por flag `--plain` que mantém comportamento legacy.

- **ADR-4 — Zero-findings-halt enforcement: estrutural, não comportamental.** Decisão: a regra é codificada como contrato de output nos 3 arquivos `agents/*-reviewer.md` (bloco obrigatório `### Why no issues`) E como assertion no orquestrador (skill `implement` + `requesting-code-review`) que detecta ausência do bloco e re-dispatcha com framing adversarial reforçado, com limite duro de 2 re-dispatches por reviewer por task. Rationale: confiar só no agente seguir a instrução é frágil — orquestrador valida o output mecanicamente. Trade-off: 2 re-dispatches × N tasks pode aumentar custo; mitigado pela exceção a mudanças triviais (cl-5: ≤ 10 LOC, exclui `.md/.json/.lock/.toml/docs/`).

- **ADR-5 — Diretório de overrides: `_aiadev/` na raiz do projeto.** Decisão: arquivos `_aiadev/team.toml` e `_aiadev/user.toml` ficam na raiz, visíveis no `ls`. Rationale: paridade com BMAD (`_bmad/`); evita choque com config global em `~/.aiadev/extensions/`; underscore-prefix sinaliza "configuração sintetizada". Trade-off: mais um diretório top-level no consumidor; aceito porque a alternativa (`.aiadev/` oculto) reduz descoberta e versionamento.

- **ADR-6 — PR única, mas commits ordenados por risco crescente.** Decisão: cl-7 escolheu PR única apesar do `git-workflow.md` recomendar PRs < 500 linhas. Mitigação: `tasks.md` ordena tasks por fase (Fase 1 → Fase 4), cada task é um commit, e o PR body lista commits agrupados por story. Rationale: as 4 stories compartilham origem (análise BMAD), tema (evolução do framework), e dependências internas (Story 1 usa o flag-pattern de Story 2; Story 4 reusa `pipeline_state` que serve `aiadev preflight`). Trade-off: revisor humano lê PR maior; mitigado pela leitura incremental commit-by-commit e pelo `code-reviewer` agente passar antes do PR.

- **ADR-7 — Naming `task-context` em vez de `compose-story` (cl-2).** Decisão: o skill chama-se `task-context` (não `compose-story`/`prepare-task`). Rationale: alinha com o vocabulário do framework (`tasks.md` é a unidade existente; "story" é jargão BMAD/agile que não usamos); slug curto e composável. Trade-off: leitor vindo de BMAD não reconhece o nome de imediato — mitigado pela entrada em `CREDITS.md` cruzando os termos.

- **ADR-8 — Article III YAGNI satisfeito por dogfood do preset principal (cl-8).** Decisão: `presets/django-drf-react/preset.yaml` ativa `task_context: true` na própria entrega, exercitando o caminho não-default em CI do framework; `_aiadev/user.toml.example` é commitado como documentação viva. Rationale: Article III proíbe flag sem named user — aqui o framework é seu próprio adopter inicial. Trade-off: CI do framework paga o custo de tokens extras do `task-context` em todo PR; aceito como sinal de saúde da feature.

- **ADR-9 — Article V Provider pattern: N/A (cl-9).** Decisão: o resolver `customization.py` não é tratado como provider. Rationale: Article V cobre fronteiras de rede e SDK externo (LLM API, DB, storage); merge in-process de TOML é utility puro, não cruza essa fronteira. Trade-off: se um dia decidirmos plugar fontes alternativas de configuração (env vars, key-value remoto), o resolver teria de ser refatorado para provider — risco baixo e revisitável.

## Project structure changes

```text
# NEW
src/aiadev/customization.py                                       (new)  — resolver TOML 3-camadas
src/aiadev/pipeline_state.py                                      (new)  — recomendação de próximo comando
skills/task-context/SKILL.md                                      (new)  — skill que produz task-context
templates/task-context-template.md                                (new)  — template do artefato por task
docs/customization.md                                             (new)  — regras de merge, exemplos
tests/test_customization.py                                       (new)  — unit tests do resolver
tests/test_pipeline_state.py                                      (new)  — unit tests da inspeção de estado
tests/test_task_context.py                                        (new)  — unit tests do skill task-context
tests/test_zero_findings_halt.py                                  (new)  — testa contrato dos reviewers
tests/fixtures/customization/                                     (new)  — fixtures TOML de base/team/user
tests/fixtures/pipeline_state/                                    (new)  — fixtures de specs/ em vários estados

# MODIFIED
agents/code-reviewer.md                                           (modified) — bloco `### Why no issues` obrigatório
agents/spec-document-reviewer.md                                  (modified) — idem
agents/plan-document-reviewer.md                                  (modified) — idem
skills/help/SKILL.md                                              (modified) — passa a chamar pipeline_state; flag --plain mantém legacy
skills/implement/SKILL.md                                         (modified) — leitura de task-context (opt-in); gate de re-dispatch para reviewer
skills/requesting-code-review/SKILL.md                            (modified) — gate de re-dispatch
src/aiadev/commands/install.py                                    (modified) — emitir _aiadev/team.toml e .gitignore entry
src/aiadev/commands/preflight.py                                  (modified) — preflight requesting-code-review valida .review-log.jsonl
src/aiadev/cli.py                                                 (modified) — registrar flag --task-context em preflight implement
scripts/sync_assets.py                                            (modified) — sincronizar _aiadev/ stubs
presets/django-drf-react/preset.yaml                              (modified) — task_context: true (dogfood, cl-8)
presets/catalog.json                                              (modified) — declarar campo task_context (opcional)
schemas/terse-output.schema.json                                  (modified) — adicionar variante 🟢 verification
.gitignore                                                        (modified) — adicionar `_aiadev/user.toml`
CREDITS.md                                                        (modified) — entrada para BMAD-METHOD
CHANGELOG.md                                                      (modified) — entrada Unreleased descrevendo as 4 stories
```

## Phase breakdown

> Each phase is a checkpoint. Within a phase, tasks are independent enough
> that order does not matter — across phases, order does matter.

### Phase 1 — Foundation: `pipeline_state.py`

Entrega o módulo Python que vira foundation para Story 4 (Phase 2) e para o preflight de Story 3. Sem ele, Phase 2 fica bloqueada.

- Criar fixtures pytest em `tests/fixtures/pipeline_state/` (10 estados: empty, draft-spec, clarified-spec, planned, tasked, half-done, all-done-no-review, review-pending, review-approved, finished) + 1 fixture sintética com 50 specs para o teste de performance.
- Escrever `tests/test_pipeline_state.py` (RED) com asserts para todas as 8 transições do `spec.md` Story 4 AC-1 a AC-8 e o budget de ≤ 200 ms.
- Implementar `src/aiadev/pipeline_state.py` (GREEN) com `recommend_next_command(workspace_path: Path) -> dict` — código mínimo para os testes acima passarem.
- Documentação inline mínima (docstring na função pública).

### Phase 2 — Stories 3 & 4 (paralelizáveis)

Duas stories independentes que tocam superfícies diferentes; podem ser feitas em paralelo após Phase 1. **Story 4** consome `pipeline_state.py`; **Story 3** edita só `agents/*` e adiciona um preflight assertion.

**Story 4 — `help` state-aware:**

- Editar `skills/help/SKILL.md`: passar a chamar `python -c "from aiadev.pipeline_state import recommend_next_command; ..."`, prepender a recomendação à saída atual; suportar `--plain` (e env `AIADEV_HELP_PLAIN=1`) que pula a inspeção e cai no comportamento legacy byte-a-byte.
- Atualizar `docs/pipeline-reference.md` (regra explícita: atualizar **se e somente se** o output do `help` skill em modo state-aware modificar o cabeçalho da referência; caso contrário, deixar inalterado).

**Story 3 — zero-findings-halt:**

- Editar `agents/code-reviewer.md`, `agents/spec-document-reviewer.md`, `agents/plan-document-reviewer.md`: adicionar seção "Output rule for APPROVED on non-trivial change" com requisito do bloco `### Why no issues` (≥ 3 verificações citáveis); definir "non-trivial" via cl-5; documentar a regra de exceção para mudança trivial.
- Editar `skills/implement/SKILL.md` (na seção "Spec reviewer prompt" e "Code quality reviewer prompt"): orquestrador detecta ausência do bloco em diff não-trivial e re-dispatcha com framing adversarial (limite: 2 re-dispatches/reviewer/task).
- Editar `skills/requesting-code-review/SKILL.md`: mesma regra de re-dispatch.
- Estender `src/aiadev/commands/preflight.py` com `requesting-code-review` validando o último entry em `specs/<branch>/.review-log.jsonl` (orquestrador grava cada APPROVED/CHANGES_REQUESTED com timestamp e presença/ausência do bloco).
- Editar `schemas/terse-output.schema.json` para incluir variante `🟢 file:line — verificação realizada`.

### Phase 3 — Story 2: customização 3-camadas

- Criar fixtures TOML em `tests/fixtures/customization/` (base, team, user; permutações de cada regra de merge: scalar override, table deep-merge, array-of-tables replace-or-append por `code`/`id`, parse error).
- Escrever `tests/test_customization.py` (RED) cobrindo: precedência de scalars, deep-merge de tables, replace-vs-append por chave, parse error abortando com `file:line`, ausência de override (passthrough do base), e overrides em skills oriundos de extensão.
- Implementar `src/aiadev/customization.py` (GREEN) com a API `merge_layers(base: dict, team: dict, user: dict) -> dict` honrando ADR-2 (scalars override, tables deep-merge, arrays-of-tables match por `code`/`id` replace-or-append) — código mínimo para os testes da etapa anterior passarem.
- Editar `src/aiadev/commands/install.py`: emitir `_aiadev/team.toml` (commit-ready, header explicando merge rules), adicionar linha `_aiadev/user.toml` ao `.gitignore` do projeto consumidor.
- Editar `scripts/sync_assets.py` para incluir `_aiadev/team.toml` no manifesto de stubs gerados pelo `aiadev install` (critério explícito: o stub é gerado por `install.py`; `sync_assets.py` apenas garante que `aiadev sync` mantém o manifesto atualizado quando o template do stub muda).
- Escrever `docs/customization.md` com exemplos: override de menu de skill, override de `principles[]` em agent, override de scalar `default_model`.
- Atualizar `presets/catalog.json` se a schema precisar do novo campo opcional `task_context`.

### Phase 4 — Story 1: skill `task-context`

- Criar `templates/task-context-template.md` com slots: spec slice (acceptance scenarios mapeados), plan slice (bloco completo da task), files-to-modify list com excerpts ≤ 40 linhas, checklist TDD copiado de `test-driven-development`, ponteiro para task-context anterior se existir.
- Criar `skills/task-context/SKILL.md` com loop: lê `tasks.md` para a task alvo, monta o template, escreve em `specs/<branch>/task-context/<TID>-<slug>.md`.
- Editar `skills/implement/SKILL.md`: na "Loop" entre passos 3 e 4, se `task_context: true` no preset OU flag `--task-context` no preflight, invocar `task-context <TID>` antes do dispatch; novo "Implementer prompt curto" que carrega o arquivo por path. Detecção de staleness (comparar `mtime` do arquivo vs último commit nos arquivos referenciados): se stale, recompor.
- Editar `presets/django-drf-react/preset.yaml` para `task_context: true` (dogfood per cl-8).
- Editar `src/aiadev/cli.py` e `src/aiadev/commands/preflight.py` para aceitar `--task-context`.
- Atualizar `CREDITS.md` com entrada para `bmad-code-org/BMAD-METHOD`.
- Atualizar `CHANGELOG.md` Unreleased section.

## Risks and mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Resolver TOML faz merge errado em arrays-of-tables (chave duplicada, ordem inesperada) | Med | High | Property tests exaustivos em `tests/test_customization.py` cobrindo permutações de base/team/user; pareceres documentados em `docs/customization.md` |
| Loop infinito reviewer ↔ orquestrador no zero-findings-halt | Med | Med | Limite duro de 2 re-dispatches/reviewer/task gravado no orquestrador; após o limite, log warning e prossegue como APPROVED-com-warning |
| `pipeline_state.recommend_next_command()` dá conselho errado em projeto com tasks `blocked`/`in_progress` órfãs | Med | Med | Cobertura explícita em `tests/test_pipeline_state.py` para esses estados; documentação inline da regra de transição |
| Custo de tokens do `task-context` torna `implement` proibitivamente caro | Low (default off) | Med | Default off via cl-1; quando ativo, instrumentar custo em `aiadev preflight implement` para reportar tokens incrementais; preset `django-drf-react` mede em CI antes de qualquer mudança de default |
| PR única excede 500 linhas (cl-7 trade-off) e aumenta carga do reviewer humano | High | Low | Commits ordenados por fase + por story; PR body com sumário por commit; código revisado pelo `code-reviewer` agente antes do PR |
| Falsos positivos do `preflight clarify` (substring naïve já visto neste plano) | Low | Low | Documentar como follow-up: refatorar `preflight.py:199` para regex `\[NEEDS CLARIFICATION:cl-` em PR separada (fora deste spec) |
| `_aiadev/team.toml` em conflito de merge entre branches paralelos no projeto consumidor | Med | Low | `docs/customization.md` documenta padrão de uso (usar `_aiadev/user.toml` para configs pessoais; manter `_aiadev/team.toml` minimal e revisado em PR como qualquer arquivo) |

## Complexity tracking

> Required when any Constitution Check row is `FAIL`. Empty table if no waivers.

| Article waived | Reason | Alternatives considered | Reviewer |
|---|---|---|---|
| _(nenhum)_ | Todos os 7 articles passam (5 PASS, 2 N/A com justificativa). cl-7 (PR única apesar de `git-workflow.md`) é uma regra de processo, não constitucional. | — | — |

## Hand-off to `tasks`

The next skill is `tasks`. It consumes this plan and produces `tasks.md`.
Pre-conditions before hand-off:

- [x] Constitution Check is fully populated, no blank rows.
- [x] Complexity tracking is filled or empty-and-justified.
- [x] Project structure delta is accurate.
