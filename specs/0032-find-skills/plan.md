# Implementation plan: find-skills — descobrir skills existentes antes de construir

> Produced by the `plan` skill: **how** the spec is realized. Do not rewrite `spec.md` here.

**Branch:** `feature/0032-find-skills`
**Date:** 2026-10-28
**Spec:** [spec.md](./spec.md)
**Plan version:** 1
**Language:** pt-BR

---

## Summary

Uma skill nova, `skills/find-skills/SKILL.md`, curta e genérica, que ensina o agente a procurar uma skill existente, verificar a fonte e deixar a instalação na mão do usuário. Todo diretório de `skills/` já é instalado em todo preset, então nenhum código do instalador muda. O trabalho está em três frentes pequenas: o texto da skill (com testes que fixam suas regras), o orçamento de instrução (nova entrada `skill:find-skills` e tetos de preset com razão registrada) e a atribuição em `CREDITS.md`. O percurso do pipeline não muda.

## Technical context

| Field | Value |
|---|---|
| Active preset | lean (a skill vai no núcleo, vale para todos os presets) |
| Language / runtime | Markdown + Python 3.11 (testes) |
| Primary dependencies | nenhuma nova; a skill cita `npx skills` como ferramenta externa |
| Storage | n/a |
| Testing framework | pytest (`.venv/bin/python -m pytest`) |
| Target platform(s) | Claude Code, Codex, Gemini, Cursor, OpenCode (mesmo `SKILL.md`) |
| Performance budget | descrição ≤ 30 tokens; corpo ≤ ~600 tokens (medido por `scripts/instruction_budget.py`) |
| Security considerations | a skill não instala; sem `-y`; consulta só com termos genéricos; leitura do `SKILL.md` do candidato antes da instalação |

Divergência com `tech-stack.md`/auto-stack: não há `tech-stack.md` relevante; nada a listar.

## Constitution check

| Article | Applies? | Status | Evidence |
|---|---|---|---|
| I. Spec-first | Yes | PASS | `spec.md` 0032 revisada (APPROVED após correções de 2026-10-28) |
| II. Test-first | Yes | PASS | cada task começa por teste que falha: presença da skill nos 5 presets, frases-chave, teto de orçamento, entrada em `CREDITS.md` |
| III. Simplicity | Yes | PASS | um arquivo de skill; sem CLI novo, sem lista de padrão, sem slash command |
| IV. Evidence over claims | Yes | PASS | a skill exige verificação antes de recomendar; o PR lista os comandos e a medição do orçamento antes/depois |
| V. Provider pattern | No | N/A | nenhum provider adicionado |
| VI. Privacy by design | Yes | PASS | regra na skill: consulta só com termos genéricos; teste fixa a frase |
| VII. Attribution | Yes | PASS | `CREDITS.md` ganha entrada (repositório, material, licença MIT); nome fora do texto da skill |
| Preset-specific articles | No | N/A | skill genérica, fora de qualquer preset |

## Architecture decisions

- **Decisão:** skill no núcleo (`skills/find-skills/`), não em preset. **Rationale:** o instalador copia todo `skills/`; é o único caminho que cobre todos os presets sem código. **Trade-off:** custo fixo em todo preset, aceito pelo mantenedor.
- **Decisão:** a skill só recomenda; instalação é ação do usuário, sem `-y`. **Rationale:** uma skill é instrução que o agente executa; instalar sem confirmar é risco de cadeia de suprimentos. **Trade-off:** um passo a mais para o usuário.
- **Decisão:** verificação por critério escrito na skill (1.000 instalações preferidas, desconfiar de <100, repositório <100 estrelas com ceticismo, ler o `SKILL.md` do candidato). **Rationale:** sem CLI de pontuação, que seria o R013. **Trade-off:** depende do agente aplicar; mitigado por teste que fixa as frases.
- **Decisão:** sem slash command e fora de `docs/pipeline-path.yaml`. **Rationale:** precedente de `task-context` (lida só sob demanda); o percurso não pode crescer.
- **Decisão:** subir só o `teto` (o `baseline` fica, para o aumento exato continuar visível) de `preset:lean:total`, `preset:lean:skills`, `preset:django-drf-react:total` e `preset:django-drf-react:skills`, com `reason`, e criar `skill:find-skills` à mão com baseline == teto. O orçamento mede só esses dois presets (`DEFAULT_PRESETS`); a presença nos cinco presets do catálogo é um teste de instalação separado. **Rationale:** autorização explícita do mantenedor em 2026-10-28; o aumento é exatamente o custo da descrição.

## Project structure changes

```text
skills/find-skills/SKILL.md                     (new)
CREDITS.md                                      (modified)
docs/instruction-budget.json                    (modified: skill:find-skills manual, baseline == teto; teto de preset:lean|django-drf-react:skills/total sobe, baseline fica, reason registrada)
CHANGELOG.md                                    (modified)
README.md                                       (modified: lista as skills por nome)
tests/test_find_skills.py                       (new)
```

## Phase breakdown

### Phase 1 — Skill e testes

- Teste que falha: `skills/find-skills/SKILL.md` existe, passa `aiadev validate`, descrição ≤ 30 tokens, corpo sem nome de fornecedor nem exemplo de stack, sem `-y`, com as regras de verificação, de confirmação e de privacidade da consulta, e com o caminho "nada encontrado" e "sem rede".
- Escrever a skill (adaptação enxuta, em inglês como as demais skills genéricas ou no idioma do repositório, a confirmar pelo padrão das outras).

### Phase 2 — Instalação e orçamento

- Teste que falha: instalar cada preset do catálogo em tmp contém `find-skills`.
- Medir antes/depois com `scripts/instruction_budget.py --check` (nunca `--write-baseline --force`, que descarta os `reason`); subir só os tetos afetados em `docs/instruction-budget.json` com `reason`; confirmar que `path:total` não muda e que o aumento por preset é igual ao custo da descrição.

### Phase 3 — Atribuição e docs

- Teste que falha: `CREDITS.md` tem a entrada com repositório, material e licença.
- Entrada em `CREDITS.md`, CHANGELOG `[Unreleased]`, README (lista de skills); um `grep` por enumerações de skills em `tests/` e `docs/` confirma que nada mais muda.

## Risks and mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Skill recomendada é maliciosa | Med | High | critério de verificação, leitura do `SKILL.md`, confirmação humana, sem `-y` |
| Teste de orçamento reprova por outro total | Med | Low | medir antes; subir só o necessário, com razão |
| Descrição acima de 30 tokens | Low | Low | teste dedicado |
| Gerador de referência ou README enumeram skills e driftam | Med | Low | rodar a suíte completa na Phase 3 |

## Complexity tracking

Nenhuma linha `FAIL`; vazio justificado. A subida do teto não é waiver de artigo (é regra de orçamento do repositório, autorizada pelo mantenedor).

## Hand-off to `tasks`

Next skill: `tasks`. Constitution Check completo, Complexity tracking justificado vazio, delta de estrutura conferido contra o instalador (todo `skills/` é copiado).
