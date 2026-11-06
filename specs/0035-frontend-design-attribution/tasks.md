# Tasks: Atribuição correta da frontend-design e folga no corpo da skill

**Branch:** `feature/0035-frontend-design-attribution`
**Plan:** [plan.md](./plan.md)
**Generated:** 2026-11-06
**Language:** pt-BR

---

## How to read this file

- Tasks run top-to-bottom, one commit each, message starting with the task id.
- `Status` (`pending`, `in_progress`, `blocked`, `done`) is owned by `implement`.

## Task list

**Phase 1 — Instalador e licença**

### T001 — Instalador copia o LICENSE.txt da skill

- **Status:** pending
- **Depends on:** —
- **Files:**
  - modify: `src/aiadev/install_engine.py`
  - test: `tests/test_install_engine.py`
- **Spec scenarios:** Story 1 scenario 4
- **Acceptance:**
  - [ ] Failing test written and observed failing for the stated reason: `_collect_skill_references` devolve a entrada `<skill>/LICENSE.txt` quando a pasta da skill tem o arquivo, não devolve nada quando não tem, não segue symlink para fora de `skills/`, ignora skill sem `SKILL.md` em nenhuma raiz, mantém a mesma precedência framework/preset das referências, e as entradas atuais (`references/**/*.md`) continuam idênticas; instalar com `scope="user"` deixa o arquivo ao lado do `SKILL.md`, e desinstalar/sync-retire remove o `LICENSE.txt` instalado.
  - [ ] Minimum implementation makes the test pass: o coletor inclui `LICENSE.txt` da skill com a mesma regra de fronteira e a docstring é ajustada.
  - [ ] No other existing test regresses (inclui toda a `tests/test_install_engine.py`).
  - [ ] Commit message: `feat(install): T001 instalador copia o LICENSE.txt da skill`.

### T002 — LICENSE.txt verbatim e campo license corrigido

- **Status:** pending
- **Depends on:** T001
- **Files:**
  - create: `presets/django-drf-react/skills/frontend-design/LICENSE.txt`
  - modify: `presets/django-drf-react/skills/frontend-design/SKILL.md`
  - test: `tests/test_frontend_design_attribution.py`
- **Spec scenarios:** Story 1 scenario 1, scenario 2, scenario 4; Success criterion #6
- **Acceptance:**
  - [ ] Failing test written and observed failing for the stated reason (novo arquivo): `LICENSE.txt` existe e começa com o cabeçalho "Apache License / Version 2.0, January 2004" e bate com a constante sha256 embutida no teste (texto do upstream `anthropics/skills`, baixado com `gh api repos/anthropics/skills/contents/skills/frontend-design/LICENSE.txt`; o teste não usa rede e a data da conferência vai no `CREDITS.md` e no PR); o campo `license` cita "Apache-2.0", "anthropics/skills" e "modified" e não cita "Strivex"; `name` e `description` são strings fixas no teste (sem depender de git); instalar o preset django-drf-react num diretório temporário deixa `LICENSE.txt` ao lado do `SKILL.md` da skill (todas as plataformas que copiam skills).
  - [ ] Minimum implementation makes the test pass: arquivo copiado verbatim, sem reformatar; frontmatter com `license: Apache-2.0 — adapted and modified from anthropics/skills (frontend-design); complete terms in LICENSE.txt`.
  - [ ] No other existing test regresses; grep por testes que contam arquivos de uma instalação completa do django-drf-react (o preset ganha um arquivo por plataforma) e ajustar o que contar; se alguma plataforma recusar arquivo que não é `.md`, ajustar só o ponto de cópia dela e registrar.
  - [ ] Commit message: `feat(frontend-design): T002 LICENSE.txt Apache-2.0 e campo license corrigido`.

**Phase 2 — Crédito e enxugamento**

### T003 — Entrada no CREDITS.md e nenhum Strivex como origem

- **Status:** pending
- **Depends on:** T002
- **Files:**
  - modify: `CREDITS.md`
  - modify: `CHANGELOG.md`
  - test: `tests/test_frontend_design_attribution.py`
- **Spec scenarios:** Story 1 scenario 3; Success criterion #4
- **Acceptance:**
  - [ ] Failing test written and observed failing for the stated reason: `CREDITS.md` tem a entrada `anthropics/skills` com a skill adaptada (`frontend-design`), a licença `Apache-2.0` e a nota de que o arquivo foi modificado por este projeto; nenhum arquivo de `git ls-files` fora de `CHANGELOG.md`, `vscode-extension/CHANGELOG.md`, `specs/**`, `CREDITS.md` (nota de correção) e do próprio teste cita "Strivex", e o `CREDITS.md` diz que o rótulo anterior estava errado; o `[Unreleased]` do `CHANGELOG.md` menciona 0035, a correção da atribuição (de Strivex para anthropics/skills) e o `LICENSE.txt` instalado.
  - [ ] Minimum implementation makes the test pass; a entrada cita a data em que o texto foi conferido contra o upstream e repete o aviso de modificação.
  - [ ] No other existing test regresses.
  - [ ] Commit message: `docs(credits): T003 anthropics/skills no CREDITS e changelog`.

### T004 — Enxugar o corpo para ter folga

- **Status:** pending
- **Depends on:** T003
- **Files:**
  - modify: `presets/django-drf-react/skills/frontend-design/SKILL.md`
  - modify: `tests/test_frontend_design_quality.py`
- **Spec scenarios:** Story 2 scenario 1, scenario 2, scenario 3; Success criterion #5, #7
- **Acceptance:**
  - [ ] Failing test written and observed failing for the stated reason: o teto do corpo em `tests/test_frontend_design_quality.py` passa de 1.400 para 1.300 tokens (chars / 4) e falha com o corpo atual (1.396); nenhuma outra asserção desse arquivo muda.
  - [ ] Minimum implementation makes the test pass: cortar redundância das seções herdadas e dos exemplos de código, sem remover nem enfraquecer direção de arte, verificação no navegador, os 8 sinais e o checklist com captura (a guarda são as asserções de frase-chave da 0034, sem alteração, mais a revisão de branch); `python3 scripts/instruction_budget.py --check` sai 0 sem alterar `docs/instruction-budget.json`.
  - [ ] Full suite passes (`.venv/bin/python -m pytest`), exceto as falhas locais pré-existentes de `tests/test_mcp_server.py`.
  - [ ] Commit message: `refactor(frontend-design): T004 corpo enxuto com folga sob o teto`.

## Parallelization hints

- T001 e a parte de texto de T004 tocam arquivos disjuntos, mas T004 depende de T003 só por ordem de commit; execução serial.

## Post-task checklist

After every task: commit references the task id; status updated.

After all tasks:

- [ ] Full test suite passes (`.venv/bin/python -m pytest`).
- [ ] `analyze` skill runs and reports no drift vs spec / plan.
- [ ] Hand off to `requesting-code-review` to open the PR.
