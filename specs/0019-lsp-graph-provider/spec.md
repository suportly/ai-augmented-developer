# Feature specification: LSP como segundo provider do contrato de knowledge-graph

> This file is produced by the `specify` skill (or by `aiadev init --feature <name>` as a stub). Keep it focused on **what** and **why** — planning and code belong in `plan.md` and `tasks.md`.

**Branch:** `claude/graphify-aiadev-analysis-oiggl4`
**Created:** 2026-07-20
**Status:** Draft <!-- Draft | In review | Approved | Implemented -->
**Spec ID:** 0019 <!-- auto-incrementing integer -->
**Language:** pt-BR <!-- BCP-47 tag; every downstream artifact in this feature is written in this language. -->

---

<!-- section: Problem -->
## Problem

O contrato de provider de knowledge-graph (spec 0017) foi desenhado para ser genérico (Artigo V), mas hoje tem **uma única implementação de referência** (graphify) — o que motivou o waiver do Artigo III no plano do 0017. Sem um segundo provider concreto, não há prova de que o contrato é de fato provider-agnóstico, e ideias óbvias (como usar LSP, que dá `find-references`/`call-hierarchy` determinísticos em 40+ linguagens, inspirado em `Piebald-AI/claude-code-lsps`) ficam sem caminho. Quem sente: o mantenedor que carrega o waiver e o consumidor que já tem um language server e não quer rodar um build de grafo.

<!-- section: Reconnaissance -->
## Reconnaissance

- **contrato do provider** — entry: `specs/0017-knowledge-graph-context-provider/contracts/graph-provider.schema.json` · auth: none · integration: define as queries `impact`/`drift`/`provenance` + vocabulário de confiança; é o contrato que um provider LSP precisa satisfazer.
- **fake de referência (graphify)** — entry: `tests/fixtures/graph_provider_fake/__init__.py` · auth: none · integration: o padrão de fixture que um segundo fake (LSP) espelha para provar conformidade.
- **preset opt-in** — entry: `presets/knowledge-graph/README.md` e `presets/knowledge-graph/mcps.yaml` · auth: none · integration: onde um provider LSP alternativo seria documentado/declarado.
- **regra de confiança** — entry: `presets/knowledge-graph/rules/graph-facts.md` · auth: none · integration: define `explicit`/`inferred`/`ambiguous`; o mapeamento LSP (resolvido → `explicit`) reusa esse vocabulário.
- **waiver do Artigo III** — entry: `specs/0017-knowledge-graph-context-provider/plan.md` · auth: none · integration: a Complexity Tracking cita "um único consumidor/implementação hoje"; um segundo provider enfraquece esse waiver.

<!-- section: Users and stakeholders -->
## Users and stakeholders

- **Mantenedor do framework** — quer o contrato provado como agnóstico (2 implementações) para reduzir o peso do waiver do Artigo III.
- **Consumidor com language server** — já tem `rust-analyzer`/`pyright`/`gopls` e prefere LSP a um build de grafo.
- **Autor de um provider** — usa o mapeamento LSP como guia de como satisfazer o contrato.

<!-- section: Success criteria -->
## Success criteria

- Existe um **segundo fake** que satisfaz **o mesmo** `graph-provider.schema.json` do 0017, mapeando operações LSP (`references`, `call-hierarchy`, `document/workspace symbols`, `definition`) para as queries `impact`/`drift`/`provenance` — provando que o contrato é provider-agnóstico.
- Existe um **documento de mapeamento** LSP→contrato (qual operação LSP satisfaz cada query, e como o resultado LSP vira `explicit`/`inferred`/`ambiguous`).
- O README do preset `knowledge-graph` documenta **LSP como provider alternativo** (graphify continua sendo o de referência).
- Nada obrigatório muda: sem provider configurado, o `analyze` segue degradando como hoje; nenhuma nova dependência é imposta.
- O waiver do Artigo III do 0017 é **atualizado/enfraquecido** (o contrato agora tem 2 implementações de referência).

<!-- section: Non-goals -->
## Non-goals

- Construir um adaptador LSP→MCP executável de verdade (um servidor real). O aiadev **prova conformidade e documenta**, não implementa o provider — Artigo III.
- Empacotar ou distribuir language servers (é o que o `Piebald-AI/claude-code-lsps` já faz).
- Ligar o LSP no `plan`/review (isso é o fast-follow Story 2 do 0017).
- Mudar o contrato do 0017 (só provar que ele já serve o LSP; se faltar algo, vira `[NEEDS CLARIFICATION]`).

<!-- section: User stories -->
## User stories

### Story 1 — Segundo provider (LSP) conforme ao contrato (P1)

As a mantenedor, I want um fake LSP que satisfaz o mesmo contrato do 0017 so that eu prove que o contrato é provider-agnóstico e reduza o waiver do Artigo III.

**Acceptance scenarios** (Given / When / Then, ≥ 3 per story):

1. Given o schema `graph-provider.schema.json` do 0017, When valido as respostas do fake LSP, Then `impact`/`drift`/`provenance` validam contra o mesmo schema, sem alterá-lo.
2. Given o fake LSP responde `impact`, When inspeciono as arestas, Then cada fato cita um `arquivo:símbolo` e um rótulo de confiança do vocabulário aiadev.
3. Given a Complexity Tracking do 0017 dizia "uma implementação hoje", When esta feature entra, Then o waiver do Artigo III é reescrito para refletir 2 implementações de referência.

### Story 2 — Mapeamento LSP→contrato documentado (P1)

As a autor de provider, I want um documento que mapeia operações LSP para as 3 queries so that eu saiba como satisfazer o contrato com um language server.

**Acceptance scenarios:**

1. Given o documento de mapeamento, When leio a seção `impact`, Then ela indica a operação LSP (`textDocument/references` + `callHierarchy`) que a satisfaz.
2. Given o documento de mapeamento, When leio a seção de confiança, Then ela define que uma referência/definição **resolvida** pelo LSP vira `explicit`, e um match textual não-resolvido vira `inferred`/`ambiguous`.
3. Given o README do preset `knowledge-graph`, When procuro por provider alternativo, Then há uma menção a LSP apontando para o documento de mapeamento.

<!-- section: Clarifications -->
## Clarifications

- [NEEDS CLARIFICATION:cl-1 Escopo da v1: só o fake de conformidade + doc de mapeamento (prova + guia), ou também um adaptador LSP→MCP executável? Recomendação: fake + doc; adaptador executável fica fora (Artigo III).]
- [NEEDS CLARIFICATION:cl-2 Onde vive o doc de mapeamento: em `specs/0019-*/contracts/`, na pasta de contratos do 0017, ou no preset? Recomendação: `specs/0019-*/contracts/` + link no README do preset.]
- [NEEDS CLARIFICATION:cl-3 O `mcps.yaml` do preset ganha um bloco (comentado) de exemplo LSP, ou LSP fica só documentado no README na v1?]
- [NEEDS CLARIFICATION:cl-4 Mapeamento de confiança: "resolvido pelo LSP → `explicit`; match textual/heurístico → `inferred`; múltiplos candidatos → `ambiguous`" — confirmar essa taxonomia.]
- [NEEDS CLARIFICATION:cl-5 Reescrever o waiver do Artigo III diretamente no `plan.md` do 0017 (já mergeado), ou registrar a atualização só aqui e referenciar? Recomendação: nota aqui + edição pontual no plano do 0017.]

<!-- section: Data touched -->
## Data touched

- Nenhum dado de produto. Artefatos: um segundo fixture de fake (LSP), um doc de mapeamento, uma menção no README do preset, e uma edição pontual na Complexity Tracking do plano do 0017.

<!-- section: Out-of-band effects -->
## Out-of-band effects

- Nenhum. Tudo é fixture de teste + documentação, local. Um provider LSP real (fora de escopo) rodaria localmente e não enviaria código para fora — igual ao graphify.

<!-- section: Open risks -->
## Open risks

- O contrato do 0017 pode não cobrir alguma nuance do LSP (ex.: hierarquia de chamadas com profundidade) — se aparecer, é `[NEEDS CLARIFICATION]` e possivelmente um follow-up no contrato, não uma mudança silenciosa.
- Risco de o doc de mapeamento sugerir um adaptador executável e induzir scope-creep (Artigo III) — o Non-goal deve ser explícito no doc.

<!-- section: Traceability -->
## Traceability

- Originating issue: análise comparativa de `Piebald-AI/claude-code-lsps` (ideia B) — conversa de 2026-07-18/20
- Related specs: `0017-knowledge-graph-context-provider`
- Constitution articles invoked: III (Simplicity — e a redução do waiver do 0017), IV (Evidence), V (Provider pattern — segunda implementação), VII (Attribution — creditar claude-code-lsps)
