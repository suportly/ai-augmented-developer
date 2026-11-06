# Tasks: frontend-design com direção de arte, auditoria anti-genérico e verificação no navegador

**Branch:** `feature/0034-frontend-design-quality`
**Plan:** [plan.md](./plan.md)
**Generated:** 2026-11-06
**Language:** pt-BR

---

## How to read this file

- Tasks run top-to-bottom, one commit each, message starting with the task id.
- `Status` (`pending`, `in_progress`, `blocked`, `done`) is owned by `implement`.

## Task list

**Phase 1 — Skill e teste**

### T001 — Direção de arte antes do código

- **Status:** pending
- **Depends on:** —
- **Files:**
  - modify: `presets/django-drf-react/skills/frontend-design/SKILL.md`
  - test: `tests/test_frontend_design_quality.py`
- **Spec scenarios:** Story 1 scenario 1, scenario 2, scenario 3, scenario 4
- **Acceptance:**
  - [ ] Failing test written and observed failing for the stated reason: o teste (novo arquivo) lê o `SKILL.md`, fixa a `description` atual como string exata e fixa por frase-chave que a direção de arte (estilo, tipografia, paleta e a razão de cada uma) é registrada em no máximo 6 linhas antes de gerar qualquer componente, que parte dos tokens de tema existentes e diz onde diverge, que usa a direção dada pelo pedido (marca ou protótipo aprovado) registrando só o mapeamento, e que sem tokens propõe os tokens mínimos de cores e fontes.
  - [ ] Minimum implementation makes the test pass: seção curta no `SKILL.md`, texto original, sem copiar redação de terceiros.
  - [ ] No other existing test regresses (inclui `tests/test_frontend_design_in_preset.py`).
  - [ ] Commit message: `feat(frontend-design): T001 direção de arte antes do código`.
- **Notes:** o corpo atual mede 1.061 tokens; cada task acrescenta o mínimo para caber em 1.400 no fim (T003 mede).

### T002 — Verificação da tela no navegador, estado por estado

- **Status:** pending
- **Depends on:** T001
- **Files:**
  - modify: `presets/django-drf-react/skills/frontend-design/SKILL.md`
  - test: `tests/test_frontend_design_quality.py`
- **Spec scenarios:** Story 3 scenario 1, scenario 2, scenario 3, scenario 4, scenario 5, scenario 6
- **Acceptance:**
  - [ ] Failing test written and observed failing for the stated reason: frases-chave para abrir a tela renderizada e capturar sucesso, vazio, erro e carregando conferindo cada captura contra a direção de arte; estado que não dá para forçar registrado como não verificado com o motivo; estado que a tela não tem por desenho registrado como não aplicável com a razão; servidor de desenvolvimento que não sobe reportado com a saída do erro e a tela tratada como não verificada; sem navegador disponível, dizer que não viu a tela, listar o que ficou sem verificação e não declarar a tela pronta; capturas só com dados de teste ou locais e nunca commitadas; sem instalar pacote por conta própria.
  - [ ] Minimum implementation makes the test pass.
  - [ ] No other existing test regresses.
  - [ ] Commit message: `feat(frontend-design): T002 verificação da tela no navegador`.

### T003 — Auditoria de 8 sinais e checklist com captura

- **Status:** pending
- **Depends on:** T002
- **Files:**
  - modify: `presets/django-drf-react/skills/frontend-design/SKILL.md`
  - test: `tests/test_frontend_design_quality.py`
- **Spec scenarios:** Story 2 scenario 1, scenario 2, scenario 3; Success criterion #2, #4, #7, #8
- **Acceptance:**
  - [ ] Failing test written and observed failing for the stated reason: a seção de auditoria tem exatamente 8 sinais numerados; cada sinal é marcado presente ou ausente com o trecho ou a captura que o sustenta; o sinal corrigido é checado de novo antes de entregar; um sinal que o pedido exige é mantido com a razão registrada; o checklist final exige a captura de cada estado em vez de "estado tratado"; o corpo mede no máximo 1.400 tokens (chars / 4).
  - [ ] Minimum implementation makes the test pass: 8 sinais escritos do zero, reformulados de princípios gerais e não do texto herdado; se o corpo passar de 1.400, podar primeiro os comentários dos exemplos de código e, só depois, um dos blocos.
  - [ ] No other existing test regresses.
  - [ ] Commit message: `feat(frontend-design): T003 auditoria de sinais e checklist com captura`.

**Phase 2 — Orçamento e changelog**

### T004 — Orçamento intacto e CHANGELOG

- **Status:** pending
- **Depends on:** T003
- **Files:**
  - modify: `CHANGELOG.md`
  - test: `tests/test_frontend_design_quality.py`
- **Spec scenarios:** Success criterion #5, #6
- **Acceptance:**
  - [ ] Failing test written and observed failing for the stated reason: `[Unreleased]` do `CHANGELOG.md` menciona 0034, `frontend-design`, a direção de arte, a auditoria, a verificação no navegador, que o orçamento não mudou e a lacuna de atribuição herdada como limitação conhecida; `python3 scripts/instruction_budget.py --check` sai 0 com `docs/instruction-budget.json` sem diff; `CREDITS.md` sem diff.
  - [ ] Minimum implementation makes the test pass.
  - [ ] Full suite passes (`.venv/bin/python -m pytest`), exceto as falhas locais pré-existentes de `tests/test_mcp_server.py`.
  - [ ] Commit message: `docs(frontend-design): T004 changelog e orçamento intacto`.

## Parallelization hints

- Todas as tasks tocam o mesmo `SKILL.md`: execução serial.

## Post-task checklist

After every task: commit references the task id; status updated.

After all tasks:

- [ ] Full test suite passes (`.venv/bin/python -m pytest`).
- [ ] `analyze` skill runs and reports no drift vs spec / plan.
- [ ] Hand off to `requesting-code-review` to open the PR.
