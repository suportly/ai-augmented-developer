# Implementation plan: Fast-follows dos providers + token-economy (polish)

> Produced by the `plan` skill from an approved `spec.md`. This file describes **how** the spec will be realized. Do not rewrite `spec.md` into `plan.md`.

**Branch:** `claude/graphify-aiadev-analysis-oiggl4`
**Date:** 2026-07-20
**Spec:** [spec.md](./spec.md)
**Plan version:** 1
**Language:** pt-BR <!-- mirrors spec.md; write plan prose in this language. -->

---

## Summary

Fecha os quatro fast-follows das features 0017–0020: (1) `plan` e `requesting-code-review` ganham um passo **opcional** de blast-radius via a query `impact` do provider (espelhando o `analyze`, com a mesma cláusula de degradação graciosa); (2) `learn.propose_guidance` passa a poder apontar uma **categoria de `checklist`** por um mapa conservador de reviewer→categoria, com fallback para `rules/`; (3) o `mcps.yaml` do preset ganha um bloco **comentado** de exemplo LSP; (4) `docs/token-economy.md` ganha um exemplo **comentado** de hook `PreToolUse`. Tudo aditivo/inerte; nenhuma dependência nova. ~5 tasks em 3 fases.

## Technical context

| Field | Value |
|---|---|
| Active preset | Nenhum — repositório do próprio framework aiadev |
| Language / runtime | Markdown (skills/docs/config) + Python (`learn.py`); `pytest` |
| Primary dependencies | Nenhuma nova. Reusa o contrato do 0017 e `graph-facts.md` |
| Storage | Filesystem |
| Testing framework | `pytest` + `scripts/validate_skills.py` |
| Target platform(s) | As 5 plataformas (skills genéricas) |
| Performance budget | N/A (passos opcionais, degradam sem provider) |
| Security considerations | Nenhuma; exemplos comentados e passos opcionais |

## Constitution check

| Article | Applies? | Status | Evidence |
|---|---|---|---|
| I. Spec-first | Yes | PASS | `spec.md` aprovado em 2026-07-20, zero marcadores |
| II. Test-first | Yes | PASS | Testes: seções em plan/review; alvo de checklist no learn; bloco LSP comentado; hook no doc |
| III. Simplicity | Yes | PASS | Aditivo; nenhuma abstração nova; exemplos inertes |
| IV. Evidence over claims | Yes | PASS | PR enumera `pytest` + `validate_skills.py` |
| V. Provider pattern | Yes | PASS | Blast-radius consome a query `impact` do contrato existente; nada vendor-specific nas skills |
| VI. Privacy by design | Yes | PASS | Passos opcionais e locais; degradação sem provider; nenhum log novo |
| VII. Attribution | No | N/A | Sem material novo adaptado; LSP/rtk/headroom já creditados nas features 0019/0020 |
| Preset-specific articles | N/A | N/A | Feature de nível framework |

## Architecture decisions

- **Decisão:** Blast-radius em `plan`/review **reusa** o vocabulário e a cláusula de degradação do passo do `analyze` (0017).
  **Rationale:** Consistência; evita divergência entre skills.
  **Trade-offs:** Texto parecido em 3 skills — aceitável (são instruções, não código).

- **Decisão:** `learn` usa um **mapa fixo conservador** reviewer→categoria com fallback `rules/`.
  **Rationale:** cl-2; evita mapeamento arbitrário; sem regressão (fallback preserva o comportamento atual).
  **Trade-offs:** Cobertura limitada de categorias — ampliável depois.

- **Decisão:** Exemplos de config são **comentados/inertes**.
  **Rationale:** cl-3; não muda parse/schema, não impõe server/hook.
  **Trade-offs:** Consumidor precisa descomentar — desejável (opt-in).

## Project structure changes

```text
skills/plan/SKILL.md                     (modified) # passo opcional blast-radius + degradação
skills/requesting-code-review/SKILL.md   (modified) # seção opcional de subsistemas impactados + degradação
src/aiadev/learn.py                      (modified) # propose_guidance: alvo de categoria de checklist + fallback
presets/knowledge-graph/mcps.yaml        (modified) # bloco comentado de exemplo LSP
docs/token-economy.md                    (modified) # exemplo comentado de hook PreToolUse
tests/test_provider_followups.py         (new)      # cobre as 3 stories
```

## Phase breakdown

### Phase 1 — Blast-radius no `plan` e no review (Story 1)

- Passo opcional em `skills/plan/SKILL.md` (seção "Superfícies afetadas / blast-radius" via `impact`) + cláusula de degradação.
- Seção opcional de subsistemas impactados em `skills/requesting-code-review/SKILL.md` + degradação. Testes primeiro.

### Phase 2 — `learn` propõe categoria de checklist (Story 2)

- `propose_guidance` ganha um mapa reviewer→categoria com fallback `rules/`; `--write` mostra o alvo de checklist. Testes.

### Phase 3 — Exemplos de config (Story 3)

- Bloco comentado LSP em `presets/knowledge-graph/mcps.yaml`; exemplo comentado de hook em `docs/token-economy.md`. Testes garantem parse/validação intactos.

## Risks and mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Divergência do passo do `analyze` | Med | Low | Reusar vocabulário/cláusula; teste checa a cláusula de degradação nas 3 skills |
| Mapa learn→categoria arbitrário | Low | Low | Conservador + fallback `rules/`; teste do fallback |
| Bloco comentado quebrar o parse do mcps.yaml | Low | Med | Comentário YAML puro; teste valida o preset contra o schema após a edição |

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
