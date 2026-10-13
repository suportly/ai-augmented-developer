# Feature specification: bootstrap para projetos legados (brownfield) — contexto de produto e specs retroativas

> This file is produced by the `specify` skill (or by `aiadev init --feature <name>` as a stub). Keep it focused on **what** and **why** — planning and code belong in `plan.md` and `tasks.md`.

**Branch:** `feature/0027-brownfield-bootstrap`
**Created:** 2026-09-24
**Status:** Draft <!-- Draft | In review | Approved | Implemented -->
**Spec ID:** 0027 <!-- auto-incrementing integer -->
**Language:** pt-BR <!-- BCP-47 tag; every downstream artifact in this feature is written in this language. -->

---

<!-- section: Problem -->
## Problem

A maior parte dos projetos que adotam o aiadev já existe há tempo: tem código, README, TODOs espalhados e nenhuma spec. A skill `product` (spec 0023) infere mission/tech-stack/roadmap de documentos de alto nível, mas um projeto legado guarda a maior parte da verdade no **código** — módulos, comandos, rotas, testes, `TODO`/`FIXME`. Sem um bootstrap que leia isso, o time começa o pipeline com um roadmap vazio e sem nenhuma spec das features que já existem, e a primeira spec nova não tem com o que se alinhar. O curso SDD trata o caso brownfield explicitamente. Quem sente: o time que instala o aiadev num produto em produção e precisa de um ponto de partida sem escrever a documentação do zero.

<!-- section: Reconnaissance -->
## Reconnaissance

- **inferência de stack existente** — entry: `src/aiadev/project_introspect.py` · auth: none · integration: `introspect()` é deliberadamente raso ("AST or LSP-level introspection is deferred; cf. spec 0007 non-goals"); lê só arquivos de configuração. O brownfield precisa de leitura de código além disso — e deve respeitar o mesmo princípio de determinismo onde for possível.
- **bootstrap do `product`** — entry: `specs/0023-product-context/spec.md` · auth: none · integration: esta spec **amplia** o modo de inferência da skill `product`; não cria uma skill paralela (Artigo III). Os artefatos ficam em `specs/_product/` (0023 cl-1, resolvido); a gramática do roadmap é a de 0023 cl-2 (resolvido).
- **precedente de spec retroativa** — entry: `constitution.md` · auth: none · integration: o Artigo I já prevê "retrospective `spec.md`" para `hotfix:` em 72 h; specs retroativas de features existentes são uma extensão desse conceito.
- **numeração de specs** — entry: `src/aiadev/commands/init.py` · auth: none · integration: `_find_next_spec_id` calcula o próximo Spec ID monotônico; specs retroativas consomem IDs da mesma sequência.
- **métricas contam `Implemented`** — entry: `src/aiadev/metrics.py` · auth: none · integration: `AGGREGATE_STATUSES = {"Implemented", "Merged"}` e `CANONICAL_STATUSES`; spec retroativa marcada `Implemented` entraria no agregado do `aiadev metrics` sem ter passado pelo pipeline e distorceria as taxas (cl-2).
- **validador de recon** — entry: `schemas/spec-recon.schema.json` · auth: none · integration: `cutover_spec_id` = 10; toda spec retroativa nova precisa de *Reconnaissance* válida (caminhos que existem), o que casa bem com specs derivadas de código.
- **visualização de specs** — entry: `vscode-extension/src/views/specTreeProvider.ts` · auth: none · integration: renderiza status das specs; um status novo para retroativas precisaria ser reconhecido aqui.
- **provider de grafo opcional** — entry: `skills/analyze/SKILL.md` · auth: none · integration: seção "Graph provider (optional)" mostra o padrão de degradação graciosa quando o preset `knowledge-graph` (spec 0017) está ausente — o brownfield pode usar o grafo quando houver, sem depender dele.

<!-- section: Users and stakeholders -->
## Users and stakeholders

- **Time de um produto legado** — quer começar o pipeline com contexto de produto e mapa das features existentes.
- **Tech lead** — aprova o que foi inferido; precisa distinguir fato citado de suposição.
- **Quem lê `aiadev metrics`** — não pode ter as taxas distorcidas por specs que não passaram pelo pipeline.

<!-- section: Success criteria -->
## Success criteria

- Num repositório legado sem artefatos de produto, o modo brownfield produz mission/tech-stack/roadmap em que **cada item cita evidência** do repositório (arquivo, e linha quando aplicável: README, arquivo de pacote, código, comentário `TODO`/`FIXME`); o que não tem evidência vira marcador de clarificação `cl-N`.
- `TODO`/`FIXME` viram candidatos de roadmap agrupados e citados, nunca entradas gravadas sem aprovação.
- Specs retroativas são **opt-in**: sem pedido explícito, nenhuma é criada.
- Cada spec retroativa é identificável como retroativa por um marcador estável e **fica fora do agregado** do `aiadev metrics` (verificável com fixture).
- A varredura ignora diretórios de dependência e build (`node_modules`, `.venv`, `dist`, vendor) e nunca lê arquivos de segredo (`.env*`, chaves, credenciais).

<!-- section: Non-goals -->
## Non-goals

- Análise estática profunda (AST/LSP) como requisito; o grafo de conhecimento é usado se configurado, nunca exigido.
- Gerar planos, tasks ou testes para features existentes; specs retroativas descrevem o que existe, não o que construir.
- Ler issue tracker, wiki ou qualquer fonte remota.
- Marcar as specs retroativas como aprovadas; elas nascem em revisão humana.
- Varrer sem confirmação: o modo brownfield é oferecido, nunca disparado sozinho (cl-4).

<!-- section: User stories -->
## User stories

### Story 1 — Contexto de produto a partir do código legado (P1)

Como time de um produto legado, quero que o bootstrap gere mission, tech-stack e roadmap lendo código, README e TODOs para que o pipeline comece com o contexto real do produto.

**Acceptance scenarios** (Given / When / Then, ≥ 3 per story):

1. Given um repositório com código, README e nenhum artefato de produto, When rodo o `product` em modo brownfield, Then os três rascunhos citam arquivo (e linha) de cada item inferido.
2. Given o código tem `TODO`/`FIXME`, When o roadmap é rascunhado, Then os comentários aparecem agrupados como candidatos, cada grupo citando as ocorrências, sem virar entrada gravada sem aprovação.
3. Given o README descreve uma funcionalidade que não aparece no código, When o bootstrap roda, Then a divergência é reportada ao usuário em vez de a funcionalidade ser tratada como existente.
4. Given o repositório tem `.env` e `node_modules/`, When a varredura roda, Then nenhum dos dois é lido.

### Story 2 — Specs retroativas opcionais (P2)

Como tech lead, quero opcionalmente gerar specs retroativas das features existentes para que as specs novas tenham com o que se alinhar e o `analyze` tenha base de comparação.

**Acceptance scenarios:**

1. Given peço specs retroativas, When o bootstrap roda, Then propõe a lista de features candidatas, cada uma com o ponto de entrada e os testes que a sustentam, e só escreve as que eu aprovar, uma spec por feature, com Spec IDs da sequência normal.
2. Given uma feature com testes existentes, When a spec retroativa é escrita, Then os cenários de aceitação derivam desses testes e citam os arquivos de teste.
3. Given uma feature sem testes, When a spec retroativa é escrita, Then os cenários que não têm evidência viram marcadores de clarificação `cl-N`.
4. Given specs retroativas existem, When rodo `aiadev metrics` sem `--feature`, Then elas não entram no agregado.

### Story 3 — Limites de varredura em repositórios grandes (P2)

Como usuário de um monorepo grande, quero que o bootstrap tenha limites de varredura previsíveis para que o custo seja controlado e o resultado reproduzível.

**Acceptance scenarios:**

1. Given um repositório com mais arquivos versionados que o orçamento de cl-3, When o bootstrap roda, Then ele informa o que foi amostrado e o que ficou de fora, em vez de truncar em silêncio.
2. Given o preset `knowledge-graph` configurado, When o bootstrap roda, Then usa o provider para delimitar features e cita os fatos com o rótulo de confiança de `presets/knowledge-graph/rules/graph-facts.md`; sem o provider, segue sem erro.
3. Given duas execuções no mesmo commit, When comparo as listas de features detectadas, Then são iguais.

<!-- section: Clarifications -->
## Clarifications

- **cl-1 (o que é uma feature):** o agente propõe a lista e o humano recorta. Cada candidata cita a evidência que a sustenta: um ponto de entrada visível ao usuário (comando, rota, tela, API pública) e, quando houver, os testes que o exercitam. Nenhuma unidade estrutural fixa (módulo, pacote, diretório) é imposta, porque ela não é genérica entre stacks. Com o provider de grafo configurado, a lista usa os subsistemas dele.
- **cl-2 (marcador de retroativa):** header dedicado `**Origin:** retroactive`; o `Status` segue o conjunto canônico. O `aiadev metrics` exclui do agregado as specs com esse header. `CANONICAL_STATUSES` e a extensão VS Code não mudam (um novo `Status` obrigaria a mexer no union exaustivo `SpecStatus`).
- **cl-3 (orçamento e exclusões):** varre só arquivos versionados (`git ls-files`), o que já respeita `.gitignore` e dá o mesmo resultado no mesmo commit. Exclusão fixa, mesmo se versionados: dependências e builds (`node_modules/`, `.venv/`, `venv/`, `vendor/`, `dist/`, `build/`, `target/`, `__pycache__/`, `coverage/`), arquivos minificados ou gerados, lockfiles, binários e segredos (`.env*`, `*.pem`, `*.key`, `id_rsa*`, `*credentials*`). Orçamento inicial de 2.000 arquivos, a calibrar no plan contra repositórios de fixture; acima disso, amostra por diretório de primeiro nível e informa o que ficou de fora.
- **cl-4 (gatilho):** detecção com confirmação. Quando `product` roda num repositório com código versionado e sem `specs/`, a skill oferece o modo brownfield e só varre após confirmação. Nunca varre sem pedir. As specs retroativas continuam opt-in à parte (Story 2).
- **cl-5 (fluxo das retroativas):** o mesmo fluxo das specs normais, sem trilha paralela (Artigo III): marcadores de clarificação vão para o `clarify` e a spec passa pelo `spec-document-reviewer`, que verifica também se cada cenário de aceitação cita um teste existente ou está marcado. Aprovada, a spec vai direto para `Status: Implemented`, sem plan nem tasks.

<!-- section: Data touched -->
## Data touched

- **Leitura:** árvore do repositório (com exclusões), README, arquivos de pacote, `TODO`/`FIXME`, testes existentes; provider de grafo quando configurado.
- **Escrita (após aprovação):** artefatos de produto (0023) e, opcionalmente, `specs/<NNNN>-<slug>/spec.md` retroativas.
- **Pacote:** extensão de `skills/product/SKILL.md` (criada em 0023); `src/aiadev/metrics.py` passa a excluir do agregado as specs com `**Origin:** retroactive` (cl-2); a extensão VS Code não muda.

<!-- section: Out-of-band effects -->
## Out-of-band effects

- Nenhum. Varredura local; nenhuma chamada de rede.

<!-- section: Open risks -->
## Open risks

- **Specs retroativas que descrevem bug como comportamento desejado:** derivar cenários do código congela defeitos como requisito.
- **Custo de contexto:** varrer código de um produto grande é caro; o orçamento de cl-3 limita isso, mas o valor inicial ainda precisa de calibração.
- **Falsa completude:** um roadmap montado só com TODOs representa dívida técnica, não direção de produto.
- **Distorção de métricas:** mitigada pelo header `**Origin:** retroactive` (cl-2); outra ferramenta que conte specs `Implemented` sem olhar o header continua sujeita a ela.

<!-- section: Traceability -->
## Traceability

- Originating issue: comparação do aiadev com o curso "Spec-Driven Development with Coding Agents" (DeepLearning.AI × JetBrains, Paul Everitt) — conversa de 2026-09-24, melhoria 5 de 7.
- Related specs: `0023-product-context` (bloqueante: skill e artefatos), `0015-aiadev-metrics` (isolamento das retroativas), `0017-knowledge-graph-context-provider` (provider opcional), `0011-specify-reconnaissance` (recon válido nas retroativas).
- Constitution articles invoked: I, II, III, IV, VI

### Constitution Check (preliminar)

> Avaliação no nível da spec. O `plan` refaz a checagem com evidência concreta.

| Artigo | Aplica? | Avaliação preliminar |
|---|---|---|
| I. Spec-first | Sim | Esta spec; cl-1…cl-5 resolvidas em 2026-09-24; depende da 0023. As specs retroativas seguem o precedente de spec retroativa do próprio Artigo I. |
| II. Test-first | Sim | Repositório legado de fixture (código, README, TODOs, `.env`, `node_modules`) com testes de exclusão, citação e isolamento em métricas antes da implementação. |
| III. Simplicity | Sim | Amplia a skill `product` em vez de criar outra; grafo só quando configurado. |
| IV. Evidence over claims | Sim | Todo item inferido cita arquivo:linha; features sem evidência viram marcador. |
| V. Provider pattern | Condicional | Só o provider de grafo já existente (0017), acessado pelo contrato atual. |
| VI. Privacy by design | Sim | Exclusão fixa de `.env*`, chaves e credenciais; nenhum conteúdo sai da máquina. |
| VII. Attribution | Não | Nada adaptado: escrito do zero. A entrada de inspiração do curso SDD no `CREDITS.md` (spec 0023, cl-6) cobre a ideia. |
