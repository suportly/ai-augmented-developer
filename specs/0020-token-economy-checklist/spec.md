# Feature specification: Categoria de checklist "token-economy" + integração opcional de compressor

> This file is produced by the `specify` skill (or by `aiadev init --feature <name>` as a stub). Keep it focused on **what** and **why** — planning and code belong in `plan.md` and `tasks.md`.

**Branch:** `claude/graphify-aiadev-analysis-oiggl4`
**Created:** 2026-07-20
**Status:** Implemented <!-- Draft | In review | Approved | Implemented -->
**Spec ID:** 0020 <!-- auto-incrementing integer -->
**Language:** pt-BR <!-- BCP-47 tag; every downstream artifact in this feature is written in this language. -->

---

<!-- section: Problem -->
## Problem

O aiadev já tem uma disciplina de economia de tokens para **saída de reviewer** (o `terse-mode`, spec 0009), mas nada que ajude o time a olhar a **economia de tokens de contexto como um todo** — saída ruidosa de ferramentas (logs de teste, `git status`, build) que incha o contexto do agente. Ferramentas como `rtk-ai/rtk` e `headroomlabs-ai/headroom` mostram que comprimir/filtrar essa saída corta 60–90% dos tokens, mas o aiadev não tem nem uma **lente de revisão** para isso nem um caminho documentado de integração. Quem sente: o tech lead pagando por contexto inflado e o dev cujas sessões ficam lentas.

<!-- section: Reconnaissance -->
## Reconnaissance

- **skill checklist** — entry: `skills/checklist/SKILL.md` · auth: none · integration: roda uma passada por categoria (security/performance/…); uma categoria `token-economy` entra aqui como lente de revisão.
- **template do checklist** — entry: `templates/checklist-template.md` · auth: none · integration: as listas de itens default por categoria vivem aqui; a categoria nova ganha sua seção de itens.
- **regra terse-mode (0009)** — entry: `rules/terse-mode.md` · auth: none · integration: ativo de economia de tokens existente (saída de reviewer); a nova categoria referencia, não duplica.
- **atribuição** — entry: `CREDITS.md` · auth: none · integration: creditar `rtk-ai/rtk` e `headroomlabs-ai/headroom` pela ideia da economia de tokens de saída.

<!-- section: Users and stakeholders -->
## Users and stakeholders

- **Tech lead** — quer uma lente que sinalize contexto inflado antes de virar custo/lentidão.
- **Dev do projeto** — usa a categoria para encontrar onde a saída de ferramenta pode ser comprimida.
- **Mantenedores** — donos do template do checklist e do CREDITS.

<!-- section: Success criteria -->
## Success criteria

- Existe uma categoria **`token-economy`** que o `checklist` sabe rodar, com uma **lista de itens default** (ex.: saída ruidosa de ferramenta entrando no contexto; logs não-truncados; oportunidades de compressão; verbosidade além do `terse-mode`).
- A categoria **referencia** o `terse-mode` (0009) em vez de duplicá-lo (a lente é sobre saída de ferramenta, não só de reviewer).
- Existe um **documento de integração opcional** que descreve como ligar um compressor externo (`rtk`/`headroom`) via hook/MCP — **sem** o aiadev implementar compressor (Artigo III).
- Nada obrigatório muda: rodar o `checklist` sem a categoria segue igual; nenhuma dependência nova é imposta.

<!-- section: Non-goals -->
## Non-goals

- Implementar um compressor de tokens dentro do aiadev — `rtk`/`headroom` são binários dedicados; o caminho é integração opcional documentada (Artigo III).
- Instalar/empacotar `rtk` ou `headroom`.
- Um hook `PreToolUse` pronto no framework (fica como fast-follow; a v1 só documenta o caminho).
- Mexer no `terse-mode` (0009) — a categoria referencia, não altera.

<!-- section: User stories -->
## User stories

### Story 1 — Categoria `token-economy` no checklist (P1)

As a tech lead, I want rodar `checklist` na categoria `token-economy` so that eu tenha uma lente estruturada para achar contexto inflado com evidência.

**Acceptance scenarios** (Given / When / Then, ≥ 3 per story):

1. Given o `checklist` conhece as categorias default, When peço a categoria `token-economy`, Then ela é aceita (não é "categoria desconhecida") e produz `specs/<branch>/checklists/token-economy.md`.
2. Given o template do checklist, When abro a seção de itens de `token-economy`, Then há uma lista de itens default (saída ruidosa, logs não-truncados, oportunidades de compressão, verbosidade além do terse-mode).
3. Given um item sobre verbosidade de reviewer, When o leio, Then ele **referencia** o `terse-mode` (0009) em vez de repetir suas regras.

### Story 2 — Caminho de integração opcional documentado (P2)

As a dev, I want um doc que explique como ligar um compressor externo so that eu reduza tokens de saída sem esperar o framework implementar isso.

**Acceptance scenarios:**

1. Given o doc de integração, When leio a seção de compressor, Then ela cita `rtk`/`headroom` como opções externas e o mecanismo (hook `PreToolUse` / MCP) — deixando claro que o aiadev não os implementa.
2. Given o doc, When procuro o Non-goal, Then está explícito que reimplementar compressor está fora de escopo (Artigo III).
3. Given o `CREDITS.md`, When procuro a origem da ideia, Then há atribuição a `rtk-ai/rtk` e `headroomlabs-ai/headroom`.

<!-- section: Clarifications -->
## Clarifications

- **cl-1 (escopo v1):** As **duas** coisas — a categoria de checklist (a lente) **e** o doc de integração opcional (o caminho).
- **cl-2 (default/preset):** A categoria `token-economy` é um **default do framework**, como as outras categorias.
- **cl-3 (vs terse-mode):** A categoria **só referencia** o `terse-mode` (0009); escopos distintos (saída de ferramenta vs saída de reviewer), sem absorver itens.
- **cl-4 (hook no doc):** O doc fica **descritivo** na v1; um exemplo concreto de hook `PreToolUse` comentado é fast-follow.
- **cl-5 (onde vive o doc):** Em **`docs/token-economy.md`**, linkado pela categoria.

<!-- section: Data touched -->
## Data touched

- Nenhum dado de produto. Artefatos: nova seção de itens no `templates/checklist-template.md`, registro da categoria em `skills/checklist/SKILL.md`, um `docs/token-economy.md`, e uma entrada em `CREDITS.md`.

<!-- section: Out-of-band effects -->
## Out-of-band effects

- Nenhum. Tudo é conteúdo de skill/template/docs, local. Um compressor externo (fora de escopo) rodaria localmente; a decisão de enviar saída a qualquer backend é do consumidor.

<!-- section: Open risks -->
## Open risks

- Scope-creep para implementar compressor/hook (Artigo III) — mitigado por Non-goal explícito no doc e na categoria.
- Sobreposição conceitual com `terse-mode` confundir o usuário — mitigado por a categoria referenciar e delimitar escopos.

<!-- section: Traceability -->
## Traceability

- Originating issue: análise comparativa de `rtk-ai/rtk` e `headroomlabs-ai/headroom` (ideia C) — conversa de 2026-07-18/20
- Related specs: `0009-token-economy-terse-mode`
- Constitution articles invoked: III (Simplicity — não reimplementar compressor), IV (Evidence), VII (Attribution — rtk + headroom)
