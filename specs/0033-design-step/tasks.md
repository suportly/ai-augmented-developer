# Tasks: Passo /aia:design — protótipo no Claude Design a partir das tasks

**Branch:** `feature/0033-design-step`
**Plan:** [plan.md](./plan.md)
**Generated:** 2026-10-28
**Language:** pt-BR

---

## How to read this file

- Tasks run top-to-bottom, one commit each, message starting with the task id.
- `Status` (`pending`, `in_progress`, `blocked`, `done`) is owned by `implement`.

## Task list

**Phase 1 — Código: estado, preflight e papel**

### T001 — Linha UI na spec e recomendação de /aia:design em aiadev next

- **Status:** done
- **Depends on:** —
- **Files:**
  - modify: `templates/spec-template.md`
  - modify: `src/aiadev/pipeline_state.py`
  - test: `tests/test_design_state.py`
- **Spec scenarios:** Story 4 scenario 1, scenario 2, scenario 3
- **Acceptance:**
  - [ ] Failing test written and observed failing for the stated reason: com `**UI:** yes` na spec, `tasks.md` com todas as tasks pendentes e sem `design.md`, `pipeline_snapshot` recomenda `/aia:design` com motivo; com `design.md` volta a `/aia:implement`; com `**UI:** no`, linha ausente ou o placeholder `yes|no` não preenchido, o resultado é idêntico ao de hoje; com alguma task `done` não recomenda design; o template da spec tem a linha `**UI:**` com o comentário de preenchimento.
  - [ ] Minimum implementation makes the test pass: função `declares_ui(text)` exportada (regex `^\*\*UI:\*\*\s*yes\b`), campo `ui` em `PipelineSnapshot` com default e no dict `state`, recomendação com `total == pending and total > 0` entre `total is None` e `if pending`.
  - [ ] No other existing test regresses (inclui os de `pipeline_state`, `next` e os que leem o template da spec).
  - [ ] Commit message: `feat(design): T001 linha UI na spec e recomendação de /aia:design`.
- **Notes:** `skills/specify/SKILL.md` não muda; o comentário do template instrui o preenchimento. O orçamento é tratado em T007.

### T002 — Aviso do preflight implement quando falta design

- **Status:** pending
- **Depends on:** T001
- **Files:**
  - modify: `src/aiadev/preflight.py`
  - test: `tests/test_design_preflight.py`
- **Spec scenarios:** Story 4 scenario 4
- **Acceptance:**
  - [ ] Failing test written and observed failing for the stated reason: `preflight implement` com `**UI:** yes` e sem `design.md` devolve um `PreflightIssue` com `would_abort=False` e o CLI sai com 0; com `design.md` ou sem UI não há aviso; um erro real do `implement` continua abortando (o aviso não mascara nada).
  - [ ] Minimum implementation makes the test pass, usando `declares_ui` de `pipeline_state`.
  - [ ] No other existing test regresses.
  - [ ] Commit message: `feat(design): T002 aviso do preflight implement sem design`.

### T003 — Papel design em token_metrics

- **Status:** done
- **Depends on:** —
- **Files:**
  - modify: `src/aiadev/token_metrics.py`
  - modify: `docs/metrics.md`
  - test: `tests/test_token_metrics.py`
- **Spec scenarios:** Story 2 scenario 2
- **Acceptance:**
  - [ ] Failing test written and observed failing for the stated reason: um subagente com `description` `design: 0033-x` é classificado como papel `design` (hoje cai em `unclassified`); o papel aparece no texto e no JSON; os testes que fixam os quatro papéis, a tabela de oito linhas e o `+1+8` passam a refletir cinco papéis.
  - [ ] Minimum implementation makes the test pass: constante e `ROLES`, laço de `_subagent_role`, docstrings e as duas mensagens com a lista de prefixos, mais `docs/metrics.md`.
  - [ ] No other existing test regresses (inclui `tests/test_token_metrics_manual_rule.py`).
  - [ ] Commit message: `feat(design): T003 papel design em aiadev metrics`.

**Phase 2 — Skill, comando e template**

### T004 — Skill design com as regras fixadas por teste

- **Status:** done
- **Depends on:** —
- **Files:**
  - create: `skills/design/SKILL.md`
  - test: `tests/test_design_skill.py`
- **Spec scenarios:** Story 1 scenario 1, scenario 2, scenario 3, scenario 4; Story 2 scenario 1, scenario 2, scenario 4; Story 3 scenario 1, scenario 2; Story 5 scenario 1, scenario 3
- **Acceptance:**
  - [ ] Failing test written and observed failing for the stated reason: o teste lê `skills/design/SKILL.md` e fixa, por frase-chave com prova de mutação: lista das tasks de interface confirmada pelo usuário antes de seguir; spec sem `**UI:** yes` → avisar e perguntar; brief só com telas, cenários Given/When/Then, estados e textos da spec, sem caminho de arquivo, hash de commit, id de task nem nome de módulo interno; mostrar o que será enviado e só publicar após confirmação explícita; canvas privado, um artboard por tela; subagente com `description` `design: <slug>`; protótipo pedido por `Artifact` com `action: quickstart` e `intent: design`, sem URL fixa no texto; não configurar design system; lacunas citam o cenário que as motiva ou dizem que não há; emenda de tasks só após aprovação, via `tasks`; sem a ferramenta `Artifact` → dizer que não pôde criar o protótipo e gerar wireframes em markdown; falha ao criar → nenhum link falso gravado, dar o motivo e oferecer wireframes. Descrição ≤ 30 tokens, corpo ≤ ~700 tokens, sem "Announce at start", `aiadev validate` verde.
  - [ ] Minimum implementation makes the test pass.
  - [ ] No other existing test regresses.
  - [ ] Commit message: `feat(design): T004 skill design com regras fixadas por teste`.
- **Notes:** em inglês como as demais skills genéricas; a skill delega o formato do canvas ao tipo e não copia as regras dele.

### T005 — Comando /aia:design e template do design.md

- **Status:** done
- **Depends on:** T004
- **Files:**
  - create: `commands/design.md`
  - create: `templates/design-template.md`
  - test: `tests/test_design_command_template.py`
- **Spec scenarios:** Story 2 scenario 3; Story 5 scenario 2; Success criterion #1
- **Acceptance:**
  - [ ] Failing test written and observed failing for the stated reason: o comando existe com o mesmo molde dos demais (descrição, `argument-hint`, invoca a skill `design`); o template tem os blocos link do protótipo, mapa tela → cenário → task e lacunas, e um bloco de wireframes marcado como alternativa sem protótipo; o template não pede caminho de arquivo nem hash de commit; `design` não está em `docs/pipeline-path.yaml`.
  - [ ] Minimum implementation makes the test pass.
  - [ ] No other existing test regresses (inclui os testes que enumeram `commands/` por plataforma).
  - [ ] Commit message: `feat(design): T005 comando /aia:design e template do design.md`.

### T006 — Preflight da skill design e cobertura após emenda

- **Status:** pending
- **Depends on:** T002, T005
- **Files:**
  - modify: `src/aiadev/preflight.py`
  - modify: `tests/test_preflight.py`
  - test: `tests/test_design_preflight.py`
- **Spec scenarios:** Story 3 scenario 3
- **Acceptance:**
  - [ ] Failing test written and observed failing for the stated reason: `preflight design` exige `spec.md`, `plan.md` e `tasks.md` (mensagens de sempre); a mensagem de `unknown skill` lista `design` logo depois de `tasks`; e, num `tasks.md` emendado com uma task nova que cita o cenário da lacuna, o `preflight implement` continua sem erro de cobertura cenário → task.
  - [ ] Minimum implementation makes the test pass: `design` em `PIPELINE_SKILLS` (logo depois de `tasks`), em `_REQUIRES_TASKS` e `_SKILL_TEMPLATE`; o `PIPELINE_SKILLS` de `_tooling/skill_loader.py` fica intacto (MCP segue com 8).
  - [ ] No other existing test regresses (inclui `tests/test_preflight_requirements_coverage.py` e os de MCP).
  - [ ] Commit message: `feat(design): T006 preflight da skill design`.

**Phase 3 — Orçamento e documentação**

### T007 — Orçamento: tetos pelo custo medido, com razão

- **Status:** pending
- **Depends on:** T001, T004, T005, T006
- **Files:**
  - modify: `docs/instruction-budget.json`
  - test: `tests/test_design_budget.py`
- **Spec scenarios:** Success criterion #7
- **Acceptance:**
  - [ ] Failing test written and observed failing for the stated reason: mede com `scripts/instruction_budget.py` e exige que o teto de `skills` e o de `commands` de lean e django-drf-react subam exatamente o custo das listagens de `design`, que `total` cubra a medição, que `skill:design` exista com baseline == teto, que `path:total` e `path:templates/spec-template.md` subam só pelo excesso medido da linha `**UI:**` (ou não subam, se couber na folga), que `skills/design` não esteja em `docs/pipeline-path.yaml` e que todo teto acima do baseline tenha `reason`.
  - [ ] Minimum implementation makes the test pass: editar `docs/instruction-budget.json` à mão (nunca `--write-baseline --force`); `scripts/instruction_budget.py --check` sai 0.
  - [ ] No other existing test regresses.
  - [ ] Commit message: `feat(design): T007 orçamento sobe pelo custo medido`.
- **Notes:** a autorização de `cl-1` cobre as listagens; um excesso no percurso, se existir, vai explícito no relatório ao mantenedor.

### T008 — CHANGELOG, README e CLAUDE.md

- **Status:** pending
- **Depends on:** T007
- **Files:**
  - modify: `CHANGELOG.md`
  - modify: `README.md`
  - modify: `CLAUDE.md`
  - test: `tests/test_design_docs.py`
- **Spec scenarios:** Success criterion #1
- **Acceptance:**
  - [ ] Failing test written and observed failing for the stated reason: `[Unreleased]` menciona 0033, `/aia:design`, `**UI:**`, o aviso não bloqueante e o papel `design`; o README lista a skill e o comando; a tabela de skills do `CLAUDE.md` tem a linha do passo.
  - [ ] Minimum implementation makes the test pass; um `grep` por enumerações de skills e comandos em `tests/` e `docs/` confirma que nada mais muda.
  - [ ] Full suite passes (`.venv/bin/python -m pytest`), exceto as falhas locais pré-existentes de `tests/test_mcp_server.py`.
  - [ ] Commit message: `docs(design): T008 changelog, readme e claude.md`.

## Parallelization hints

- Parallel group A: T001, T003, T004 (arquivos disjuntos); o resto serial.

## Post-task checklist

After every task: commit references the task id; status updated.

After all tasks:

- [ ] Full test suite passes (`.venv/bin/python -m pytest`).
- [ ] `analyze` skill runs and reports no drift vs spec / plan.
- [ ] Hand off to `requesting-code-review` to open the PR.
