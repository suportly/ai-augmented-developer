# Feature specification: Fast-follows dos providers + token-economy (polish)

> This file is produced by the `specify` skill (or by `aiadev init --feature <name>` as a stub). Keep it focused on **what** and **why** — planning and code belong in `plan.md` and `tasks.md`.

**Branch:** `claude/graphify-aiadev-analysis-oiggl4`
**Created:** 2026-07-20
**Status:** Approved <!-- Draft | In review | Approved | Implemented -->
**Spec ID:** 0021 <!-- auto-incrementing integer -->
**Language:** pt-BR <!-- BCP-47 tag; every downstream artifact in this feature is written in this language. -->

---

<!-- section: Problem -->
## Problem

As features 0017–0020 deixaram quatro fast-follows pequenos e relacionados registrados nos próprios specs: (1) o provider de grafo só ancora o `analyze`, não o `plan`/review (blast-radius); (2) o `aiadev learn` só propõe guia em `rules/`, não em categorias de `checklist`; (3) o preset `knowledge-graph` documenta LSP mas não traz um exemplo de declaração; (4) o `docs/token-economy.md` é descritivo sem um exemplo concreto de hook. Cada um é lacuna conhecida; juntá-los num spot de polish evita 4 mini-features. Quem sente: o dev que esperava a lente de impacto no `plan`/review e o consumidor que quer um exemplo copiável de configuração.

<!-- section: Reconnaissance -->
## Reconnaissance

- **skill plan** — entry: `skills/plan/SKILL.md` · auth: none · integration: ganha um passo opcional de "Superfícies afetadas / blast-radius" via a query `impact` do provider, espelhando o passo do `analyze`.
- **skill requesting-code-review** — entry: `skills/requesting-code-review/SKILL.md` · auth: none · integration: o Review Context Document ganha uma seção opcional de subsistemas impactados.
- **motor learn** — entry: `src/aiadev/learn.py` · auth: none · integration: `propose_guidance` passa a poder apontar uma categoria de `checklist` como alvo, além de `rules/`.
- **preset mcps** — entry: `presets/knowledge-graph/mcps.yaml` · auth: none · integration: ganha um bloco **comentado** de exemplo de provider LSP (inerte; não altera o server ativo).
- **doc token-economy** — entry: `docs/token-economy.md` · auth: none · integration: ganha um exemplo **comentado/descritivo** de hook `PreToolUse`.
- **contrato do provider** — entry: `specs/0017-knowledge-graph-context-provider/contracts/graph-provider.schema.json` · auth: none · integration: a query `impact` já existe; o blast-radius a consome.

<!-- section: Users and stakeholders -->
## Users and stakeholders

- **Dev do projeto** — quer impacto/blast-radius no `plan` e no review, não só no `analyze`.
- **Tech lead** — quer que o `learn` proponha itens de checklist, não só regras.
- **Consumidor** — quer exemplos copiáveis de configuração (LSP no mcps.yaml, hook de compressor).

<!-- section: Success criteria -->
## Success criteria

- O `plan` e o `requesting-code-review` têm um passo **opcional** de blast-radius via a query `impact` do provider, com **degradação graciosa** (sem provider, saída idêntica à atual) e citando `arquivo:símbolo` + confiança por `graph-facts.md`.
- O `aiadev learn` pode propor uma **categoria de `checklist`** como alvo de uma proposta (além de `rules/`), sem quebrar o comportamento atual.
- O `mcps.yaml` do preset traz um **bloco comentado** de exemplo LSP; o parse segue válido (server ativo inalterado).
- O `docs/token-economy.md` traz um exemplo **descritivo/comentado** de hook `PreToolUse`, mantendo o Non-goal (framework não implementa o hook).
- Nada obrigatório muda; nenhuma dependência nova.

<!-- section: Non-goals -->
## Non-goals

- Um provider LSP ou compressor executável de verdade (segue fora — Artigos III; só exemplos/docs).
- Aplicar automaticamente propostas do `learn` em arquivos de checklist (continua sendo `specs/_learnings.md`, revisável).
- Mudar o contrato do 0017 ou o vocabulário de confiança.

<!-- section: User stories -->
## User stories

### Story 1 — Blast-radius no `plan` e no code review (P1)

As a dev, I want ver as superfícies afetadas por uma mudança no `plan` e no review so that eu dimensione risco/esforço sem caçar dependências na mão.

**Acceptance scenarios** (Given / When / Then, ≥ 3 per story):

1. Given um provider configurado, When rodo `plan`, Then `plan.md` inclui uma seção "Superfícies afetadas / blast-radius" derivada da query `impact`, citando `arquivo:símbolo` + confiança.
2. Given um provider configurado, When rodo `requesting-code-review`, Then o Review Context Document lista os subsistemas impactados pelo diff.
3. Given nenhum provider (ou indisponível), When rodo `plan`/review, Then a seção é omitida com uma nota e o resto é produzido normalmente (degradação graciosa).

### Story 2 — `learn` propõe categoria de checklist (P2)

As a tech lead, I want que uma proposta do `learn` possa apontar uma categoria de `checklist` so that padrões recorrentes virem itens de revisão, não só regras.

**Acceptance scenarios:**

1. Given um padrão de reviewer-recurrence, When o `learn` monta a proposta, Then o alvo pode ser uma categoria de `checklist` (ex.: `token-economy`/`security`) além de um arquivo em `rules/`.
2. Given `--write`, When gravo as propostas, Then o alvo de checklist aparece em `specs/_learnings.md` como proposta revisável (não aplicada).
3. Given o comportamento atual (alvo em `rules/`), When não há mapeamento de categoria, Then a proposta continua apontando `rules/` como antes (sem regressão).

### Story 3 — Exemplos de configuração copiáveis (P2)

As a consumidor, I want exemplos comentados de LSP e de hook so that eu ligue as integrações sem adivinhar a sintaxe.

**Acceptance scenarios:**

1. Given o `presets/knowledge-graph/mcps.yaml`, When o abro, Then há um bloco **comentado** de exemplo de server LSP; o parse do YAML segue válido (server ativo inalterado).
2. Given o `docs/token-economy.md`, When leio a seção de hook, Then há um exemplo descritivo/comentado de `PreToolUse`, com o Non-goal preservado.
3. Given a suíte de testes, When rodo os testes do preset e das docs, Then continuam passando (exemplos comentados não quebram validação).

<!-- section: Clarifications -->
## Clarifications

- **cl-1 (Story 1):** A v1 cobre **`plan` e review** — simétricos e pequenos, reusando o mesmo vocabulário/cláusula de degradação do `analyze`.
- **cl-2 (learn→checklist):** Um **mapa fixo e conservador** por tipo de reviewer (ex.: `code-reviewer`→`security`), com **fallback para `rules/`** quando não há mapeamento.
- **cl-3 (exemplos de config):** **Estritamente comentados/inertes** — não mudam parse/schema nem impõem server/hook; a validação segue passando.

<!-- section: Data touched -->
## Data touched

- Nenhum dado de produto. Artefatos: edições em `skills/plan/SKILL.md`, `skills/requesting-code-review/SKILL.md`, `src/aiadev/learn.py`, `presets/knowledge-graph/mcps.yaml`, `docs/token-economy.md`, e testes.

<!-- section: Out-of-band effects -->
## Out-of-band effects

- Nenhum. Tudo local; provider e compressor seguem opcionais e consumidor-configurados.

<!-- section: Open risks -->
## Open risks

- Blast-radius no `plan`/review pode divergir do passo do `analyze` se copiado sem cuidado — mitigar reusando o mesmo vocabulário/cláusula de degradação.
- Mapa learn→checklist pode ficar arbitrário — manter conservador e com fallback.

<!-- section: Traceability -->
## Traceability

- Originating issue: fast-follows registrados em 0017 (Story 2), 0018 (cl-1), 0019 (cl-3), 0020 (cl-4)
- Related specs: `0017`, `0018`, `0019`, `0020`
- Constitution articles invoked: III (Simplicity), IV (Evidence), V (Provider pattern), VI (Privacy)
