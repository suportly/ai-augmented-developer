# Implementation plan: Provedor de contexto de knowledge-graph para o pipeline

> Produced by the `plan` skill from an approved `spec.md`. This file describes **how** the spec will be realized. Do not rewrite `spec.md` into `plan.md`.

**Branch:** `claude/graphify-aiadev-analysis-oiggl4`
**Date:** 2026-07-18
**Spec:** [spec.md](./spec.md)
**Plan version:** 1
**Language:** pt-BR <!-- mirrors spec.md; write plan prose in this language. -->

---

## Summary

Vamos dar à skill `analyze` a capacidade **opcional** de ancorar seus gaps em fatos de um knowledge-graph, definindo um **contrato de provider genérico** (queries de impacto, drift e proveniência) declarado via MCP, com o graphify como implementação de referência. A confiança de cada fato citado segue um vocabulário próprio do aiadev, mapeado da taxonomia do provider, documentado numa regra cross-cutting. O provider é distribuído por um **preset opcional** que o consumidor liga sob demanda; sem provider, o `analyze` se comporta exatamente como hoje. O trabalho cabe em ~3 fases / ~8–10 tasks, tocando `skills/analyze/SKILL.md`, `rules/`, um novo `presets/knowledge-graph/`, `presets/catalog.json`, `CREDITS.md` e `tests/`.

## Technical context

| Field | Value |
|---|---|
| Active preset | Nenhum — este é o repositório do próprio framework aiadev |
| Language / runtime | Python 3 (CLI `aiadev`) + skills em Markdown |
| Primary dependencies | Nenhuma nova obrigatória. graphify entra **apenas** como MCP opcional que o consumidor instala |
| Storage | Filesystem (`specs/`, `rules/`, `presets/`); saída do grafo (`graphify-out/`) vive no projeto consumidor |
| Testing framework | `pytest` + `scripts/validate_skills.py` + `markdownlint-cli2` |
| Target platform(s) | As 5 plataformas: claude-code, cursor, codex, opencode, gemini |
| Performance budget | `analyze` sem provider: zero chamada de rede nova, zero regressão. Com provider: consulta com timeout limitado; em falha, degrada |
| Security considerations | Local por padrão; qualquer backend LLM do provider é opt-in explícito e documentado (Artigo VI). Nenhuma credencial/PII em log novo |

## Constitution check

| Article | Applies? | Status | Evidence |
|---|---|---|---|
| I. Spec-first | Yes | PASS | `spec.md` aprovado em 2026-07-18, zero marcadores `[NEEDS CLARIFICATION]` |
| II. Test-first | Yes | PASS | Toda task começa por um teste que falha: asserts de validação sobre os artefatos (skill/rule/preset) e teste de conformidade contra o fake do contrato |
| III. Simplicity | Yes | **FAIL → waiver** | O contrato de provider é uma nova indireção com **um único** consumidor hoje (`analyze`); `plan`/review são fast-follow. Abstração forçada pelo Artigo V — ver Complexity tracking |
| IV. Evidence over claims | Yes | PASS | O test plan do PR enumera os comandos (`pytest`, `validate_skills.py`, `aiadev install --dry-run`) e cola a saída; a degradação graciosa é demonstrada com e sem provider |
| V. Provider pattern | Yes | PASS | O grafo é acessado por um contrato declarado (mcps.yaml + contrato de queries documentado); o graphify é referenciado só por config, nunca importado nas skills/CLI; testes usam um **fake** do contrato |
| VI. Privacy by design | Yes | PASS | Padrão local; backend LLM é opt-in documentado; a regra proíbe o `analyze` de enviar código para fora sem opt-in; nenhum log novo com segredo/PII |
| VII. Attribution | Yes | PASS | `CREDITS.md` ganha entrada creditando `Graphify-Labs/graphify` como origem da ideia (contrato, tags de confiança, blast-radius) |
| Preset-specific articles | N/A | N/A | Feature de nível framework; o preset opcional novo não adiciona artigos constitucionais |

## Architecture decisions

- **Decisão:** Definir um contrato de provider genérico com 3 queries — `impact(paths)`, `drift(tasks, diff)`, `provenance(fact)` — em vez de acoplar ao graphify.
  **Rationale:** Artigo V; permite fake nos testes e troca de implementação sem tocar skills.
  **Trade-offs:** Uma indireção a mais com um só consumidor hoje (waiver de Artigo III).

- **Decisão:** Vocabulário de confiança próprio (`explicit` / `inferred` / `ambiguous`) mapeado da taxonomia do provider (ex.: `EXTRACTED`/`INFERRED`/`AMBIGUOUS`), num arquivo `rules/graph-facts.md`.
  **Rationale:** Desacopla a saída do aiadev do vocabulário de qualquer provider; a regra cross-cutting propaga para `plan`/review no fast-follow via `aiadev sync`.
  **Trade-offs:** Uma camada de mapeamento a manter se um provider mudar seus rótulos.

- **Decisão:** Distribuir o provider como preset opcional `presets/knowledge-graph/` (declara o MCP no seu `mcps.yaml`), registrado no catálogo como opt-in/experimental.
  **Rationale:** cl-5 — ninguém ganha dependência nova; consumidor liga sob demanda.
  **Trade-offs:** Se o mecanismo de presets não suportar overlay aditivo limpo, cai-se no fallback de um bloco opt-in comentado em `mcps.yaml` (ver Risks).

- **Decisão:** No `analyze`, o passo de provider é **aditivo e condicional**; ausência de provider mantém as 4 classes de gap por inferência, sem erro.
  **Rationale:** Success criterion de degradação graciosa; não regride o comportamento atual.
  **Trade-offs:** Duas trilhas de comportamento a testar (com e sem provider).

## Project structure changes

```text
rules/graph-facts.md                                   (new)      # como citar fatos + mapa de confiança
skills/analyze/SKILL.md                                (modified) # passo opcional provider-aware + degradação graciosa
presets/knowledge-graph/mcps.yaml                      (new)      # declara o provider MCP (graphify de referência)
presets/knowledge-graph/README.md                      (new)      # opt-in, instalação, aviso de privacidade
presets/catalog.json                                   (modified) # registra o preset opcional
CREDITS.md                                             (modified) # atribuição a Graphify-Labs/graphify
tests/test_analyze_graph_provider.py                   (new)      # asserts skill + degradação + conformidade do fake
tests/fixtures/graph_provider_fake/…                   (new)      # fake do contrato para os testes
specs/0017-knowledge-graph-context-provider/contracts/ (follow-up) # contrato de queries (próxima invocação de plan)
```

## Phase breakdown

### Phase 1 — Contrato do provider e vocabulário de confiança

- Documentar o contrato de queries (`impact`/`drift`/`provenance`) e criar `rules/graph-facts.md` com o mapa taxonomia-do-provider → vocabulário-aiadev.
- Adicionar o fake do contrato em `tests/fixtures/` e um teste de conformidade que falha antes de o fake existir.

### Phase 2 — Integração no `analyze`

- Editar `skills/analyze/SKILL.md`: passo opcional que consulta o provider para as classes "code without task" e "task without code", citando `arquivo:símbolo` com rótulo de confiança; cláusula explícita de degradação graciosa (sem provider → saída idêntica à atual).
- Testes que asseguram tanto a seção provider-aware quanto a cláusula de degradação, e que não há regressão sem provider.

### Phase 3 — Preset opcional e atribuição

- Criar `presets/knowledge-graph/` (mcps.yaml + README de opt-in/privacidade) e registrá-lo em `presets/catalog.json`.
- Atualizar `CREDITS.md` (Artigo VII). Verificar `aiadev install --preset knowledge-graph --dry-run` e `aiadev doctor`.

## Risks and mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Presets não suportam overlay aditivo "opt-in" limpo | Med | Med | Fallback: bloco opt-in comentado em `mcps.yaml`; validar com `aiadev install --dry-run` antes de fechar a fase 3 |
| Grafo desatualizado gera fato enganoso | Med | Med | Sempre citar `arquivo:símbolo` verificável; rotular fatos inferidos; degradar em vez de afirmar gap como definitivo |
| Provider indisponível em runtime (timeout/erro) | Med | Low | Consulta com timeout; omitir a contribuição do provider com nota, manter o comportamento base |
| Indireção com um só consumidor (Artigo III) | High | Low | Waiver citando Artigo V; contrato limitado às 3 queries que o `analyze` precisa hoje |
| Vazamento de código para backend LLM | Low | High | Padrão local; opt-in explícito e documentado; regra proíbe envio sem opt-in (Artigo VI) |

## Complexity tracking

| Article waived | Reason | Alternatives considered | Reviewer |
|---|---|---|---|
| III. Simplicity | O contrato de provider introduz uma indireção; é **forçado pelo Artigo V**, que exige interface em torno de serviço externo com fronteira de rede | (a) acoplar `analyze` direto ao graphify — rejeitado por ferir o Artigo V; (b) adiar o contrato até o segundo consumidor — rejeitado porque a v1 já cruza a fronteira de rede | Pendente (aprovador humano) |

> **Atualização (spec 0019):** o waiver está **enfraquecido** — o contrato deixou de ter uma única implementação. O `0019-lsp-graph-provider` adicionou uma **segunda implementação de referência** (um provider LSP conforme ao mesmo `graph-provider.schema.json`), então a indireção agora tem 2 implementações, não uma. A justificativa via Artigo V permanece, mas a preocupação de "abstração para um único caller" já não se aplica.

## Hand-off to `tasks`

The next skill is `tasks`. It consumes this plan and produces `tasks.md`.
Pre-conditions before hand-off:

- [x] Constitution Check is fully populated, no blank rows.
- [x] Complexity tracking is filled or empty-and-justified.
- [x] Project structure delta is accurate.
