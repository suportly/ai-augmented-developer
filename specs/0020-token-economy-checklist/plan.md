# Implementation plan: Categoria de checklist "token-economy" + integração opcional

> Produced by the `plan` skill from an approved `spec.md`. This file describes **how** the spec will be realized. Do not rewrite `spec.md` into `plan.md`.

**Branch:** `claude/graphify-aiadev-analysis-oiggl4`
**Date:** 2026-07-20
**Spec:** [spec.md](./spec.md)
**Plan version:** 1
**Language:** pt-BR <!-- mirrors spec.md; write plan prose in this language. -->

---

## Summary

Vamos adicionar uma categoria `token-economy` ao `checklist` — itens default no `templates/checklist-template.md` (saída ruidosa de ferramenta, logs não-truncados, oportunidades de compressão, verbosidade além do `terse-mode`), registrada em `skills/checklist/SKILL.md`. E um `docs/token-economy.md` documentando como ligar um compressor **externo** (`rtk`/`headroom`) via hook/MCP, com Non-goal explícito de não implementar compressor (Artigo III). `CREDITS.md` credita as duas origens. Tudo é conteúdo de skill/template/docs; sem código de produto, sem dependência nova. ~4 tasks em 2 fases.

## Technical context

| Field | Value |
|---|---|
| Active preset | Nenhum — repositório do próprio framework aiadev |
| Language / runtime | Markdown (skill/template/docs); testes em `pytest` |
| Primary dependencies | Nenhuma nova. Referencia `rules/terse-mode.md` (0009) |
| Storage | Filesystem |
| Testing framework | `pytest` + `scripts/validate_skills.py` |
| Target platform(s) | As 5 plataformas (checklist é skill genérica) |
| Performance budget | N/A |
| Security considerations | Nenhuma; conteúdo de documentação |

## Constitution check

| Article | Applies? | Status | Evidence |
|---|---|---|---|
| I. Spec-first | Yes | PASS | `spec.md` aprovado em 2026-07-20, zero marcadores |
| II. Test-first | Yes | PASS | Testes: categoria registrada na skill; template com itens; doc com rtk/headroom + Non-goal; CREDITS |
| III. Simplicity | Yes | PASS | **É a disciplina anti-scope-creep**: só uma categoria + doc; nenhum compressor/hook implementado |
| IV. Evidence over claims | Yes | PASS | PR enumera `pytest` + `validate_skills.py` |
| V. Provider pattern | No | N/A | O framework não adiciona dependência externa; o doc descreve integração opcional que o consumidor liga |
| VI. Privacy by design | No | N/A | Conteúdo de skill/template/docs; sem log, sem rede |
| VII. Attribution | Yes | PASS | `CREDITS.md` credita `rtk-ai/rtk` e `headroomlabs-ai/headroom` |
| Preset-specific articles | N/A | N/A | Feature de nível framework |

## Architecture decisions

- **Decisão:** `token-economy` é uma **categoria de checklist default**, não um preset.
  **Rationale:** cl-2; consistência com as outras categorias (todos os consumidores ganham a lente).
  **Trade-offs:** Uma categoria a mais no template — custo baixo.

- **Decisão:** A categoria **referencia** o `terse-mode` (0009), não o duplica.
  **Rationale:** cl-3; escopos distintos (saída de ferramenta vs de reviewer).
  **Trade-offs:** O leitor precisa seguir um link — aceitável.

- **Decisão:** Compressor é **integração externa documentada**, não implementada (`docs/token-economy.md`).
  **Rationale:** cl-1/cl-4 + Artigo III; `rtk`/`headroom` são binários dedicados.
  **Trade-offs:** Sem compressão "de fábrica"; fica como caminho opt-in.

## Project structure changes

```text
templates/checklist-template.md      (modified) # nova seção "Token economy (default items)"
skills/checklist/SKILL.md            (modified) # registra a categoria token-economy
docs/token-economy.md                (new)      # integração opcional (rtk/headroom) + Non-goal + mecanismo
CREDITS.md                           (modified) # atribuição a rtk-ai/rtk e headroomlabs-ai/headroom
```

## Phase breakdown

### Phase 1 — Categoria no checklist

- Adicionar a seção de itens default `Token economy` ao `templates/checklist-template.md`, com um item que **referencia** o `terse-mode`.
- Registrar a categoria em `skills/checklist/SKILL.md` (description + inputs). Testes primeiro.

### Phase 2 — Doc de integração + atribuição

- `docs/token-economy.md`: `rtk`/`headroom` como compressores externos, mecanismo (hook `PreToolUse`/MCP), Non-goal explícito; linkado pela categoria.
- `CREDITS.md` (Artigo VII).

## Risks and mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Scope-creep para implementar compressor/hook | Med | Med | Non-goal explícito no doc e na categoria; plano não prevê código de compressor |
| Confusão com `terse-mode` | Low | Low | Categoria referencia e delimita escopo; doc separa saída de ferramenta vs reviewer |
| Um teste enumera as categorias e quebra | Low | Low | Recon não achou tal teste; rodar a suíte completa após a Fase 1 |

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
