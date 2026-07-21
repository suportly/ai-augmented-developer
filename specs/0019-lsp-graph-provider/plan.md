# Implementation plan: LSP como segundo provider do contrato de knowledge-graph

> Produced by the `plan` skill from an approved `spec.md`. This file describes **how** the spec will be realized. Do not rewrite `spec.md` into `plan.md`.

**Branch:** `claude/graphify-aiadev-analysis-oiggl4`
**Date:** 2026-07-20
**Spec:** [spec.md](./spec.md)
**Plan version:** 1
**Language:** pt-BR <!-- mirrors spec.md; write plan prose in this language. -->

---

## Summary

Vamos provar que o contrato `graph-provider.schema.json` (spec 0017) é provider-agnóstico adicionando um **segundo fake conforme** — desta vez mapeando operações LSP (`references`/`call-hierarchy` → `impact`, `document/workspace symbols` → `drift`, `definition` resolvida → `provenance`) para as mesmas 3 queries — e um **documento de mapeamento** LSP→contrato com a taxonomia de confiança (resolvido→`explicit`, textual→`inferred`, múltiplos→`ambiguous`). O README do preset ganha uma menção a LSP como provider alternativo, o `CREDITS.md` credita `Piebald-AI/claude-code-lsps`, e o **waiver do Artigo III do 0017 é reescrito** para refletir 2 implementações de referência. Sem código de produto novo, sem adaptador executável (Artigo III). ~6 tasks em 2 fases.

## Technical context

| Field | Value |
|---|---|
| Active preset | Nenhum — repositório do próprio framework aiadev |
| Language / runtime | Python 3 (fixtures + testes); Markdown (docs) |
| Primary dependencies | Nenhuma nova. Reusa `graph-provider.schema.json` (0017) e o padrão de fake |
| Storage | Filesystem (fixtures, docs) |
| Testing framework | `pytest` + `scripts/validate_skills.py` |
| Target platform(s) | N/A (prova de conformidade + docs) |
| Performance budget | N/A |
| Security considerations | Nenhuma; fixtures de teste + documentação, sem rede |

## Constitution check

| Article | Applies? | Status | Evidence |
|---|---|---|---|
| I. Spec-first | Yes | PASS | `spec.md` aprovado em 2026-07-20, zero marcadores |
| II. Test-first | Yes | PASS | Fake validado contra o schema do 0017; docs guardadas por teste de presença |
| III. Simplicity | Yes | PASS | Nenhuma abstração nova; **reduz** o waiver do 0017 (contrato agora com 2 implementações) |
| IV. Evidence over claims | Yes | PASS | PR enumera `pytest` + validação do fake LSP contra o schema |
| V. Provider pattern | Yes | PASS | É literalmente a segunda implementação atrás do contrato do 0017 |
| VI. Privacy by design | No | N/A | Fixtures de teste + docs; sem log, sem rede, sem dado sensível |
| VII. Attribution | Yes | PASS | `CREDITS.md` credita `Piebald-AI/claude-code-lsps` |
| Preset-specific articles | N/A | N/A | Feature de nível framework |

## Architecture decisions

- **Decisão:** O segundo provider é um **fake de conformidade**, não um adaptador LSP→MCP executável.
  **Rationale:** cl-1 / Artigo III — o objetivo é provar que o contrato serve o LSP e documentar como; construir o servidor é trabalho de um provider, não do framework.
  **Trade-offs:** Não há um provider LSP rodável ainda; fica como caminho documentado.

- **Decisão:** O fake LSP valida contra o **mesmo** `graph-provider.schema.json`, sem alterá-lo.
  **Rationale:** Prova real de agnosticismo; se o LSP não couber, vira marcador de clarificação (não mudança silenciosa).
  **Trade-offs:** Se o contrato precisar evoluir, é um follow-up separado.

- **Decisão:** Mapeamento de confiança LSP fixo — resolvido→`explicit`, textual/heurístico→`inferred`, múltiplos candidatos→`ambiguous`.
  **Rationale:** cl-4; reusa `graph-facts.md` sem inventar vocabulário.
  **Trade-offs:** Nenhum relevante.

## Project structure changes

```text
tests/fixtures/lsp_provider_fake/__init__.py          (new)      # 2º fake, conforme ao schema do 0017
tests/test_lsp_provider_conformance.py                (new)      # valida o fake LSP contra graph-provider.schema.json
specs/0019-lsp-graph-provider/contracts/lsp-provider-mapping.md (new) # doc LSP→contrato + confiança
presets/knowledge-graph/README.md                     (modified) # menção a LSP como provider alternativo + link
CREDITS.md                                             (modified) # atribuição a Piebald-AI/claude-code-lsps
specs/0017-knowledge-graph-context-provider/plan.md    (modified) # reescreve o waiver do Artigo III (2 implementações)
```

## Phase breakdown

### Phase 1 — Fake LSP conforme ao contrato

- Criar `tests/fixtures/lsp_provider_fake/` retornando `impact`/`drift`/`provenance` derivados de operações LSP, validando contra o **mesmo** schema do 0017. Testes primeiro.
- Assegurar rótulos de confiança conforme a taxonomia (resolvido→`explicit`, etc.).

### Phase 2 — Doc de mapeamento, preset, atribuição e waiver

- `contracts/lsp-provider-mapping.md`: qual operação LSP satisfaz cada query + tabela de confiança.
- README do preset: LSP como provider alternativo, apontando para o doc.
- `CREDITS.md` (Artigo VII) e edição pontual do waiver do Artigo III no `plan.md` do 0017.

## Risks and mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Contrato do 0017 não cobre nuance do LSP | Med | Med | Se aparecer, marcador de clarificação + follow-up no contrato; não alterar o schema silenciosamente |
| Doc induzir scope-creep para um adaptador executável | Low | Low | Non-goal explícito no topo do doc de mapeamento |
| Editar o `plan.md` do 0017 (já mergeado) causar confusão | Low | Low | Edição pontual e comentada, referenciando o 0019 |

## Complexity tracking

> Required when any Constitution Check row is `FAIL`. Empty table if no waivers.

| Article waived | Reason | Alternatives considered | Reviewer |
|---|---|---|---|
| — | Nenhum waiver (esta feature **reduz** o waiver do 0017) | — | — |

## Hand-off to `tasks`

The next skill is `tasks`. It consumes this plan and produces `tasks.md`.
Pre-conditions before hand-off:

- [x] Constitution Check is fully populated, no blank rows.
- [x] Complexity tracking is filled or empty-and-justified.
- [x] Project structure delta is accurate.
