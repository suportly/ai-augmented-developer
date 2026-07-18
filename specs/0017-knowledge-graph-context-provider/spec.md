# Feature specification: Provedor de contexto de knowledge-graph para o pipeline

> This file is produced by the `specify` skill (or by `aiadev init --feature <name>` as a stub). Keep it focused on **what** and **why** — planning and code belong in `plan.md` and `tasks.md`.

**Branch:** `claude/graphify-aiadev-analysis-oiggl4`
**Created:** 2026-07-18
**Status:** Approved <!-- Draft | In review | Approved | Implemented -->
**Spec ID:** 0017 <!-- auto-incrementing integer -->
**Language:** pt-BR <!-- BCP-47 tag; every downstream artifact in this feature is written in this language. -->

---

<!-- section: Problem -->
## Problem

As skills `analyze`, `plan` e `requesting-code-review` raciocinam sobre estrutura e impacto do codebase via grep + inferência do LLM, sem uma fonte determinística de fatos. Isso produz afirmações não verificadas ("esta task não tocou código", "estes arquivos foram afetados") — exatamente o que o Artigo IV (Evidence over claims) desaconselha. Quem sente: o tech lead que lê o relatório do `analyze`/review e o dev que confia no blast-radius do `plan`.

<!-- section: Reconnaissance -->
## Reconnaissance

- **skill analyze** — entry: `skills/analyze/SKILL.md` · auth: none · integration: passo 1–3 lê `spec.md`/`plan.md`/`tasks.md` + diff e infere as classes de gap ("code without task", "task without code") sem fonte de fatos determinística.
- **skill plan** — entry: `skills/plan/SKILL.md` · auth: none · integration: passo 5 "Project structure changes" e passo 6 "Phase breakdown" descrevem arquivos afetados por julgamento do LLM, sem mapa de dependências.
- **skill requesting-code-review** — entry: `skills/requesting-code-review/SKILL.md` · auth: none · integration: monta o "Review Context Document" sem seção de subsistemas impactados.
- **declaração de MCP** — entry: `mcps.yaml` (`servers: {}`) · auth: none · integration: `aiadev install` já traduz servers para o config nativo de cada plataforma (Claude/Cursor/Gemini/Codex/OpenCode); é o ponto de injeção natural para um provider de grafo.
- **constituição** — entry: `constitution.md` · auth: none · integration: Artigo V (Provider pattern, linha 86) e Artigo VI (Privacy by design, linha 102) governam qualquer dependência externa com fronteira de rede.

<!-- section: Users and stakeholders -->
## Users and stakeholders

- **Dev do projeto consumidor** — roda o pipeline e ganha impacto/drift ancorado em fatos em vez de palpite do LLM.
- **Tech lead** — lê `analyze`/review e o `aiadev metrics`; quer rastreabilidade citável (arquivo:símbolo), não prosa.
- **Mantenedores do framework** — assinam o contrato do provider e a mudança nas skills; garantem que nada quebra sem o provider configurado.

<!-- section: Success criteria -->
## Success criteria

- Com um provider de grafo configurado, o relatório do `analyze` cita fatos derivados do grafo (`arquivo:símbolo` ou `aresta`) para pelo menos as classes "code without task" e "task without code", e **cada fato citado carrega um metadado de confiança** (proveniência).
- O `plan` passa a emitir uma seção "Superfícies afetadas / blast-radius" derivada do provider quando ele existe.
- O contexto de code review inclui a lista de subsistemas impactados pelo diff.
- **Degradação graciosa**: sem provider configurado, cada skill se comporta exatamente como hoje — zero nova dependência obrigatória, zero mudança de saída.
- O provider é declarado via o mecanismo existente de `mcps.yaml` (Artigo V), sem nada vendor-specific hardcoded nas skills.
- Nada trafega para fora da máquina a menos que o consumidor opte explicitamente por um backend LLM do provider (Artigo VI); o opt-in é documentado.

<!-- section: Non-goals -->
## Non-goals

- Reimplementar um motor de grafo (tree-sitter, clustering, visualização) dentro do aiadev — violaria o Artigo III (Simplicity). O aiadev **consome** um provider, não o constrói.
- Hook git post-commit para rebuild automático (rec #3) — spec separado.
- Merge driver / cache incremental para artefatos gerados como `tasks.md` e `.review-log.jsonl` (rec #6) — spec separado.
- Publicar benchmarks do efeito do pipeline (rec #7) — spec separado, apoiado no `aiadev metrics`.
- Generalizar tags de proveniência para **todos** os artefatos (spec/plan) — aqui a confiança cobre só os fatos citados de origem no grafo.

<!-- section: User stories -->
## User stories

### Story 1 — Drift ancorado em fatos no `analyze` (P1)

As a tech lead, I want que o `analyze` fundamente cada gap num fato do grafo citável so that o relatório deixa de ser palpite do LLM e vira evidência auditável.

**Acceptance scenarios** (Given / When / Then, ≥ 3 per story):

1. Given um provider de grafo configurado e uma task marcada `done` cujos símbolos não aparecem no diff, When rodo `analyze`, Then o gap "task without code" é reportado citando o `arquivo:símbolo` esperado e ausente.
2. Given arquivos alterados no branch que nenhuma task pediu, When rodo `analyze`, Then o gap "code without task" lista cada arquivo com a aresta do grafo que o conecta a um subsistema.
3. Given nenhum provider configurado, When rodo `analyze`, Then o relatório é idêntico ao comportamento atual (mesmas 4 classes de gap por inferência) e nenhum erro é emitido por provider ausente.

### Story 2 — Blast-radius no `plan` e no code review (P2, fast-follow pós-v1)

As a dev do projeto consumidor, I want ver as superfícies afetadas por uma mudança derivadas do grafo so that eu dimensione o esforço e o risco sem caçar dependências na mão.

**Acceptance scenarios:**

1. Given um spec aprovado e um provider configurado, When rodo `plan`, Then `plan.md` inclui uma seção "Superfícies afetadas / blast-radius" com os subsistemas que as mudanças propostas tocam, cada um citando uma aresta do grafo.
2. Given um branch pronto para review e um provider configurado, When rodo `requesting-code-review`, Then o Review Context Document inclui a lista de subsistemas impactados pelo diff.
3. Given um provider configurado mas indisponível em runtime (timeout/erro), When rodo `plan`, Then a seção de blast-radius é omitida com uma nota de "provider indisponível" e o resto do plano é produzido normalmente.

### Story 3 — Metadado de confiança nos fatos citados (P2)

As a tech lead, I want que todo fato de grafo citado pelas skills declare sua proveniência so that eu não confunda uma relação explícita com uma inferida.

**Acceptance scenarios:**

1. Given um fato derivado de uma aresta explícita (ex.: import direto), When ele é citado em qualquer skill, Then ele é rotulado como de alta confiança/explícito.
2. Given um fato derivado de uma resolução inferida ou ambígua, When ele é citado, Then ele é rotulado como inferido/ambíguo e não é usado para afirmar um gap como definitivo.
3. Given a taxonomia de confiança do provider difere do vocabulário do aiadev, When um fato é citado, Then o rótulo exibido segue o vocabulário canônico do aiadev (mapeado de forma estável).

<!-- section: Clarifications -->
## Clarifications

- **cl-1 (escopo):** Este spec cobre **apenas** a integração do provider de grafo. Hook post-commit (#3), merge driver (#6) e benchmarks publicados (#7) são specs separados.
- **cl-2 (modelo do provider):** Definimos um **contrato de provider genérico** (Artigo V); o graphify é a implementação de referência e os testes usam um fake do contrato, não o SDK.
- **cl-3 (skills na v1):** A v1 entrega o provider **apenas no `analyze`** (fatia vertical mínima que prova o contrato end-to-end). `plan` e `requesting-code-review` são fast-follow pós-v1.
- **cl-4 (taxonomia de confiança):** O aiadev usa um **vocabulário de confiança próprio**, mapeado de forma estável a partir da taxonomia do provider (ex.: `EXTRACTED`/`INFERRED`/`AMBIGUOUS` do graphify).
- **cl-5 (declaração):** O provider é declarado num **preset opcional** que o consumidor liga sob demanda; nenhum preset existente ganha dependência nova.

<!-- section: Data touched -->
## Data touched

- Nenhum dado de produto. Novos elementos apenas em artefatos do pipeline: seção "Superfícies afetadas / blast-radius" em `plan.md`, subsistemas impactados no Review Context Document, e rótulos de confiança nos fatos citados pelo `analyze`.
- Possível novo documento de contrato do provider (nomes/shapes das consultas: impacto, drift, proveniência) — sem implementação aqui.

<!-- section: Out-of-band effects -->
## Out-of-band effects

- Por padrão, nada sai da máquina: o provider de grafo opera localmente. **Se** o consumidor configurar um backend LLM do provider (para docs/imagens), código ou documentos podem ser enviados a esse backend — isso deve ser opt-in explícito e documentado (Artigo VI).
- Nenhuma notificação, cobrança ou escrita em storage externo.

<!-- section: Open risks -->
## Open risks

- Disponibilidade do provider varia entre as 5 plataformas; o contrato precisa tolerar ausência sem quebrar o pipeline.
- Risco de creep de complexidade contra o Artigo III se o acoplamento ao provider vazar para dentro das skills em vez de ficar atrás do contrato.
- Staleness: o grafo pode estar desatualizado em relação ao diff atual, gerando fatos enganosos — daí a importância do metadado de confiança e de citar sempre `arquivo:símbolo` verificável.

<!-- section: Traceability -->
## Traceability

- Originating issue: análise do repositório `Graphify-Labs/graphify` (conversa de 2026-07-18)
- Related specs: `0008-llm-tool-integration`, `0010-pipeline-preflight-checks`, `0015-aiadev-metrics`
- Constitution articles invoked: III (Simplicity), IV (Evidence over claims), V (Provider pattern), VI (Privacy by design)
