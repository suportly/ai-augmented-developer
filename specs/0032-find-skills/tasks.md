# Tasks: find-skills — descobrir skills existentes antes de construir

**Branch:** `feature/0032-find-skills`
**Plan:** [plan.md](./plan.md)
**Generated:** 2026-10-28
**Language:** pt-BR

---

## How to read this file

- Tasks run top-to-bottom, one commit each, message starting with the task id.
- `Status` (`pending`, `in_progress`, `blocked`, `done`) is owned by `implement`.

## Task list

**Phase 1 — Skill e testes**

### T001 — Skill find-skills com regras fixadas por teste

- **Status:** pending
- **Depends on:** —
- **Files:**
  - create: `skills/find-skills/SKILL.md`
  - test: `tests/test_find_skills.py`
- **Spec scenarios:** Story 1 scenario 1, scenario 2, scenario 3; Story 2 scenario 1, scenario 2, scenario 3; Story 4 scenario 2, scenario 3
- **Acceptance:**
  - [ ] Failing test written and observed failing for the stated reason: o teste lê `skills/find-skills/SKILL.md` e exige descrição ≤ 30 tokens (ceil(chars/4)), ausência de nome de fornecedor e de exemplo de stack, ausência de `-y`, frases que fixam: apresentar nome, o que faz, fonte e comando; verificação (1.000 instalações, menos de 100, repositório com menos de 100 estrelas, ressalva quando um dado não pôde ser confirmado); não instalar antes da confirmação; ler o `SKILL.md` do candidato e sinalizar rede, escrita fora do projeto e instalação de pacotes; consulta só com termos genéricos; caminho "nada encontrado" e "sem rede ou CLI". Cada asserção é checada com mutação (remover a frase faz o teste falhar).
  - [ ] Minimum implementation makes the test pass; `aiadev validate` aceita a skill; corpo ≤ ~600 tokens.
  - [ ] No other existing test regresses.
  - [ ] Commit message: `feat(find-skills): T001 skill find-skills com regras fixadas por teste`.
- **Notes:** adaptação enxuta, sem citar a origem no texto; a atribuição vai em `CREDITS.md` (T004). Citar `npx skills find` e `npx skills add` como ferramenta externa; a instalação é comando mostrado ao usuário, nunca executado pela skill.

**Phase 2 — Instalação e orçamento**

### T002 — Skill presente em todo preset do catálogo

- **Status:** pending
- **Depends on:** T001
- **Files:**
  - test: `tests/test_find_skills_install.py`
- **Spec scenarios:** Story 3 scenario 1
- **Acceptance:**
  - [ ] Failing test written and observed failing for the stated reason: instala cada preset de `presets/catalog.json` em diretório temporário pela rota do CLI e exige `find-skills` instalada (o teste falha antes de T001 existir; com a skill presente, deve passar sem mudar o instalador).
  - [ ] Minimum implementation makes the test pass (nenhuma mudança de código esperada).
  - [ ] No other existing test regresses.
  - [ ] Commit message: `test(find-skills): T002 skill presente nos presets do catálogo`.
- **Notes:** se algum preset não instalar a skill, a causa é investigada antes de qualquer mudança no instalador.

### T003 — Orçamento: teto sobe pelo custo da descrição, com razão

- **Status:** pending
- **Depends on:** T001
- **Files:**
  - modify: `docs/instruction-budget.json`
  - test: `tests/test_find_skills_budget.py`
- **Spec scenarios:** Story 3 scenario 2, scenario 3; Success criterion #4
- **Acceptance:**
  - [ ] Failing test written and observed failing for the stated reason: mede com `scripts/instruction_budget.py` e exige que `preset:lean:skills` e `preset:django-drf-react:skills` subam exatamente o custo da descrição de `find-skills`, que `skill:find-skills` exista com baseline == teto, que todo teto acima do baseline traga `reason`, e que `path:total` seja idêntico a 12.624 (o valor medido antes).
  - [ ] Minimum implementation makes the test pass: subir só o `teto` (o `baseline` fica) de `preset:lean:total`, `preset:lean:skills`, `preset:django-drf-react:total` e `preset:django-drf-react:skills`, com `reason`, mais a entrada manual `skill:find-skills`; nunca `--write-baseline --force`.
  - [ ] No other existing test regresses; `scripts/instruction_budget.py --check` sai 0.
  - [ ] Commit message: `feat(find-skills): T003 orçamento sobe pelo custo da descrição`.
- **Notes:** autorização do mantenedor em 2026-10-28 vai citada na `reason`.

**Phase 3 — Atribuição e docs**

### T004 — Atribuição em CREDITS.md

- **Status:** pending
- **Depends on:** T001
- **Files:**
  - modify: `CREDITS.md`
  - test: `tests/test_find_skills_credits.py`
- **Spec scenarios:** Story 4 scenario 1; Success criterion #5
- **Acceptance:**
  - [ ] Failing test written and observed failing for the stated reason: `CREDITS.md` precisa conter a entrada com link do repositório de origem, o material adaptado e a licença MIT, e `skills/find-skills/SKILL.md` não pode conter o nome do repositório nem do fornecedor.
  - [ ] Minimum implementation makes the test pass.
  - [ ] No other existing test regresses (inclui `tests/test_attribution_and_changelog.py`).
  - [ ] Commit message: `docs(find-skills): T004 atribuição em CREDITS.md`.

### T005 — CHANGELOG e README

- **Status:** pending
- **Depends on:** T001, T003
- **Files:**
  - modify: `CHANGELOG.md`
  - modify: `README.md`
  - test: `tests/test_find_skills_docs.py`
- **Spec scenarios:** Success criterion #1
- **Acceptance:**
  - [ ] Failing test written and observed failing for the stated reason: `[Unreleased]` menciona 0032 e `find-skills`, e o README lista a skill junto das demais.
  - [ ] Minimum implementation makes the test pass; um `grep` por enumerações de skills em `tests/` e `docs/` confirma que nada mais precisa mudar.
  - [ ] Full suite passes (`.venv/bin/python -m pytest`), exceto as falhas pré-existentes de `tests/test_mcp_server.py`.
  - [ ] Commit message: `docs(find-skills): T005 changelog e readme`.

## Parallelization hints

- Parallel group A: T002, T003, T004 (arquivos disjuntos, todos dependem só de T001); o resto serial.

## Post-task checklist

After every task: commit references the task id; status updated.

After all tasks:

- [ ] Full test suite passes (`.venv/bin/python -m pytest`).
- [ ] `analyze` skill runs and reports no drift vs spec / plan.
- [ ] Hand off to `requesting-code-review` to open the PR.
