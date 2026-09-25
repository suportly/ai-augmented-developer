# Feature specification: skill `product` e templates de contexto de produto (mission, tech-stack, roadmap)

> This file is produced by the `specify` skill (or by `aiadev init --feature <name>` as a stub). Keep it focused on **what** and **why** — planning and code belong in `plan.md` and `tasks.md`.

**Branch:** `feature/0023-product-context`
**Created:** 2026-09-24
**Status:** Implemented — PR #56 <!-- Draft | In review | Approved | Implemented -->
**Spec ID:** 0023 <!-- auto-incrementing integer -->
**Language:** pt-BR <!-- BCP-47 tag; every downstream artifact in this feature is written in this language. -->

---

<!-- section: Problem -->
## Problem

O pipeline do aiadev trabalha **uma feature por vez**: cada `specify` parte de uma demanda solta e cada `plan` preenche o *Technical context* a partir do preset ativo. Não existe artefato durável que diga **por que o produto existe, para quem, com qual stack e em que ordem as features devem vir**. Resultado: specs que não conversam entre si, decisões de stack re-derivadas a cada plano e nenhuma noção de "próxima feature". O curso *Spec-Driven Development with Coding Agents* (DeepLearning.AI × JetBrains) trata esse contexto como a "constituição do produto" (mission / tech-stack / roadmap), camada que o aiadev não tem. Quem sente: o tech lead que abre uma sessão nova e precisa reexplicar o produto ao agente, e o próprio agente, que especifica sem saber o que está dentro ou fora da missão.

<!-- section: Reconnaissance -->
## Reconnaissance

- **bootstrap por inferência (padrão a espelhar)** — entry: `skills/constitution/SKILL.md` · auth: none · integration: o *Bootstrap mode* já lê `CLAUDE.md`, `.claude/rules/*`, arquivos de pacote e `README.md`, renderiza um template e só pergunta o que não dá para inferir; regra "inferred is not the same as fabricated". A skill `product` segue o mesmo contrato.
- **inferência de stack já existente** — entry: `src/aiadev/project_introspect.py` · auth: none · integration: `introspect()` devolve `StackReport` (linguagens, frameworks, comandos, serviços, CI) e alimenta o bloco `<!-- aiadev:auto-stack -->` via `src/aiadev/commands/sync.py`. É sobreposição parcial com `tech-stack.md`; resolvida em cl-3 (decisão × inventário).
- **templates canônicos** — entry: `templates/README.md` · auth: none · integration: tabela "Produced by / Consumed by" e convenções (`{{UPPER_SNAKE}}`, anchors estáveis, marcador de clarificação como marcador vivo). Os três templates novos entram aqui.
- **consumidores do contexto** — entry: `skills/specify/SKILL.md` · auth: none · integration: passo 2 "Read the demand" e passo 3 "Reconnaissance"; `skills/plan/SKILL.md` passo 2 "Technical context ... from the active preset". São os dois pontos que passam a ler os artefatos de produto.
- **distribuição para as 5 plataformas** — entry: `src/aiadev/framework_artifacts.py` · auth: none · integration: todo diretório em `skills/` com `SKILL.md` é emitido como artefato `skill` e instalado pelos handlers em `src/aiadev/platforms/` (claude-code, cursor, codex, opencode, gemini). Slash command segue o padrão de `commands/specify.md`.
- **registros de catálogo** — entry: `presets/catalog.json` · auth: none · integration: o catálogo lista **presets**, não skills; `presets/lean/preset.yaml` declara `skills: []` (só skills de preset). Skill genérica em `skills/` não se registra no catálogo; os registros que precisam de atualização são a tabela de skills em `CLAUDE.md`, `skills/using-ai-augmented-developer/SKILL.md`, `docs/pipeline-reference.md` (gerado por `scripts/generate_pipeline_reference.py`, com teste de drift) e a seção "What's Inside" do `README.md`.
- **modo LLM-tool / MCP** — entry: `src/aiadev/_tooling/skill_loader.py` · auth: none · integration: `PIPELINE_SKILLS` e `SKILL_TEMPLATE_MAP` definem as 8 skills expostas por `aiadev.tools` e pelo servidor MCP; `product` fica fora dessa lista na v1 (cl-4).

<!-- section: Users and stakeholders -->
## Users and stakeholders

- **Tech lead / dono do produto consumidor** — quer registrar uma vez missão, stack e roadmap e ter o agente respeitando isso em toda spec.
- **Agente de código** — passa a especificar e planejar com o contexto do produto em disco, sem depender do histórico da conversa.
- **Mantenedores do aiadev** — donos de templates e skills; precisam garantir que nada específico de produto entre no pacote.
- **Specs futuras 0024–0028** — dependem do `roadmap.md` e do `tech-stack.md` definidos aqui.

<!-- section: Success criteria -->
## Success criteria

- O pacote ganha `templates/mission-template.md`, `templates/tech-stack-template.md` e `templates/roadmap-template.md`, cada um com anchors `<!-- section: … -->` estáveis e **somente** placeholders `{{UPPER_SNAKE}}` — um teste confirma que nenhum dos três contém nome de produto, empresa ou stack concreta.
- A skill `product` gera os três arquivos num projeto consumidor a partir do contexto do repositório; **todo valor preenchido cita a fonte** (arquivo, e linha quando houver) e todo valor não inferível vira marcador de clarificação `cl-N` — zero valores sem fonte.
- Quando os artefatos de produto existem, `specify` e `plan` os leem; quando não existem, o comportamento dos dois é idêntico ao atual (verificável por teste de regressão sobre o texto das skills e por um e2e sem os arquivos).
- `aiadev validate` passa com a skill nova; a skill é instalada pelas 5 plataformas (um teste de instalação por plataforma lista o `SKILL.md` de `product` no destino).
- A skill nunca lê arquivos de segredo (`.env*`, chaves, credenciais) durante a inferência.
- O próprio repositório do aiadev passa a ter `specs/_product/` preenchido (cl-5), e um teste confirma que nenhum desses arquivos entra no sdist, no wheel ou na instalação em consumidores.

<!-- section: Non-goals -->
## Non-goals

- Implementar o `replan` (spec 0024), o bootstrap brownfield com specs retroativas (spec 0027) ou o modo roadmap do `implement` (spec 0028) — aqui só nascem os artefatos e a skill que os cria.
- Buscar informação fora do repositório (issue tracker, web, analytics). A inferência é local.
- Transformar `mission.md` em artigos constitucionais; a constituição continua sendo o único documento de governança e segue o próprio processo de emenda.
- Gerar conteúdo de produto dentro do pacote aiadev (exemplos preenchidos, missão de amostra).
- Expor `product` em `aiadev.tools`, no servidor MCP ou no `aiadev preflight` (cl-4).

<!-- section: User stories -->
## User stories

### Story 1 — Gerar o contexto de produto por inferência (P1)

Como tech lead de um projeto que instalou o aiadev, quero invocar a skill `product` e receber rascunhos de mission, tech-stack e roadmap inferidos do repositório para que eu só precise responder o que o código e os documentos não dizem.

**Acceptance scenarios** (Given / When / Then, ≥ 3 per story):

1. Given um projeto com `README.md`, um arquivo de pacote (`pyproject.toml`, `package.json` ou equivalente) e um `AGENTS.md`/`CLAUDE.md`, When invoco `product` e nenhum artefato de produto existe, Then a skill apresenta os três rascunhos em que cada valor preenchido traz a fonte citada, e só grava após aprovação explícita.
2. Given o repositório não diz para quem o produto é, When `product` renderiza `mission.md`, Then o campo de público vira marcador de clarificação `cl-N` com uma pergunta precisa, em vez de um público inventado.
3. Given os três artefatos já existem, When invoco `product` sem texto, Then a skill lista as seções atuais e pergunta qual atualizar (mesmo contrato do `constitution` com arquivo existente), sem sobrescrever nada.
4. Given o projeto tem `.env` e arquivos de chave na raiz, When `product` faz a inferência, Then nenhum desses arquivos é lido.

### Story 2 — Templates genéricos no pacote (P1)

Como mantenedor do aiadev, quero três templates novos com anchors estáveis e só placeholders para que qualquer produto use o mesmo molde e os validadores possam checar a forma.

**Acceptance scenarios:**

1. Given o pacote após esta feature, When listo `templates/`, Then existem `mission-template.md` (por quê, para quem, problema), `tech-stack-template.md` (linguagens, frameworks, decisões) e `roadmap-template.md` (features em ordem, status), e `templates/README.md` os lista na tabela "Produced by / Consumed by".
2. Given qualquer um dos três templates, When um teste procura texto fora de placeholders, comentários-guia e headings, Then não encontra conteúdo de produto concreto.
3. Given o `roadmap-template.md`, When um consumidor preenche uma entrada, Then a entrada tem heading `### R<NNN> — <título>`, os campos `**Status:**` (um de `planned | in-progress | done | dropped`), `**Spec:**` e, opcionalmente, `**Depends on:**`.

### Story 3 — `specify` e `plan` consomem o contexto (P1)

Como agente executando o pipeline, quero que `specify` e `plan` leiam mission, tech-stack e roadmap quando existirem para que as specs se alinhem à missão e os planos respeitem a stack declarada.

**Acceptance scenarios:**

1. Given `roadmap.md` tem uma entrada que corresponde à demanda, When `specify` roda, Then a spec cita a entrada do roadmap em *Traceability*.
2. Given a demanda contradiz um item fora de escopo declarado em `mission.md`, When `specify` roda, Then a skill pausa e expõe o conflito ao usuário citando o trecho da missão, antes de escrever user stories (mesmo tratamento do "premise mismatch" do passo 3).
3. Given `tech-stack.md` existe, When `plan` preenche *Technical context*, Then usa os valores do `tech-stack.md`, e qualquer desvio (nova linguagem, framework ou dependência) vira uma entrada em *Architecture decisions* com justificativa.
4. Given `tech-stack.md` declara um framework que o bloco auto-stack não detecta (ou o contrário), When `plan` roda, Then o plano lista a divergência citando os dois lados e não escolhe um deles sozinho.
5. Given nenhum artefato de produto existe, When `specify` e `plan` rodam, Then produzem o mesmo resultado de hoje, sem erro nem aviso bloqueante.

### Story 4 — Paridade entre as 5 plataformas (P2)

Como usuário de Cursor, Codex, OpenCode ou Gemini, quero a skill `product` disponível como nas demais skills genéricas para que o fluxo não dependa do Claude Code.

**Acceptance scenarios:**

1. Given `aiadev install --preset lean --platform <p>` para cada uma das 5 plataformas, When a instalação termina, Then o `SKILL.md` de `product` está no diretório de skills da plataforma.
2. Given o frontmatter de `skills/product/SKILL.md`, When `aiadev validate` roda, Then passa nos dois schemas (Agent Skills e interno).
3. Given o Claude Code, When o usuário digita `/aia:product`, Then o comando invoca a skill (arquivo em `commands/`).

<!-- section: Clarifications -->
## Clarifications

- **cl-1 (local dos artefatos):** `specs/_product/` no projeto consumidor, com os arquivos `mission.md`, `tech-stack.md` e `roadmap.md`. Segue o precedente de `specs/_learnings.md`, que `aiadev learn --write` grava (`src/aiadev/commands/learn.py:140`); o prefixo `_` mantém o diretório fora do que `pipeline_state._list_spec_dirs` (exige prefixo `^\d{3,4}-`) e `metrics.iter_specs_in_window` (exige `spec.md`) enumeram. Caminho fixo, sem configuração.
- **cl-2 (gramática do roadmap):** um bloco por entrada, na mesma gramática de heading + `**Status:**` que `tasks.md` já usa (analisada por `aiadev.tasks_status`): heading `### R<NNN> — <título>` com id monotônico e estável; campos `- **Status:**` (conjunto fechado `planned | in-progress | done | dropped`), `- **Spec:**` (slug `NNNN-<slug>`, vazio até o `specify`) e `- **Depends on:**` (ids `R<NNN>`, opcional); uma ou duas linhas de porquê abaixo. Se a feature está pronta para implementar não é status do roadmap: sai do estado da própria spec (`pipeline_state`), para não duplicar informação que pode divergir.
- **cl-3 (tech-stack × auto-stack):** papéis distintos. `tech-stack.md` guarda **decisões** — linguagens e frameworks adotados, o porquê e as alternativas descartadas —, com a primeira versão preenchida a partir de `project_introspect.introspect()` citando a fonte. O bloco `<!-- aiadev:auto-stack -->` segue como **inventário detectado**, regenerado pelo `aiadev sync`. Nenhum prevalece em silêncio: quando divergem, o `plan` aponta a divergência (declarado = intenção, detectado = realidade) e o humano decide.
- **cl-4 (exposição via tools/MCP):** não na v1. `product` é skill de agente (com `/aia:product`) nas 5 plataformas e **não** entra em `PIPELINE_SKILLS` nem no `aiadev preflight`. Motivos: o modo tools/MCP impõe *Single required artifact* (`_SKILL_EXCLUSIVE_ARTIFACT`, um arquivo por chamada) e `product` escreve três; a skill não tem artefato anterior para o preflight verificar. Entra depois se houver usuário nomeado (Artigo III).
- **cl-5 (dogfooding):** sim. O repositório do aiadev adota os próprios `specs/_product/mission.md`, `tech-stack.md` e `roadmap.md`, no mesmo caminho dos consumidores, e é o primeiro usuário real de `product`, `replan` (0024) e do modo roadmap (0028). Não vazam para o pacote: `specs/` não entra no sdist (`MANIFEST.in`) nem no wheel (`package-data`), e `framework_artifacts` não emite nada de `specs/`. Um teste garante que nenhum arquivo de `specs/_product/` aparece nos artefatos instaláveis.
- **cl-6 (origem dos templates):** escritos do zero; nenhum texto é copiado. O `CREDITS.md` ganha uma entrada em "Direct inspirations" para o curso "Spec-Driven Development with Coding Agents" (DeepLearning.AI × JetBrains), dizendo que só a ideia (mission / tech-stack / roadmap como contexto de produto) foi adaptada, no mesmo formato das entradas de BMAD-METHOD e headroom. O material do curso não tem licença aberta, então copiar texto dele está fora de questão.

<!-- section: Data touched -->
## Data touched

- **Pacote:** entrada nova em `CREDITS.md` (cl-6); três templates novos em `templates/`; uma skill nova `skills/product/SKILL.md`; um comando `commands/product.md`; edições em `skills/specify/SKILL.md`, `skills/plan/SKILL.md`, `templates/README.md` e nos registros de skill (tabela do `CLAUDE.md`, `using-ai-augmented-developer`, `docs/pipeline-reference.md`, `README.md`).
- **Repositório do aiadev (dogfooding, cl-5):** `specs/_product/mission.md`, `tech-stack.md` e `roadmap.md` do próprio aiadev, fora do pacote.
- **Projeto consumidor:** três arquivos Markdown novos (mission, tech-stack, roadmap) em `specs/_product/` (`mission.md`, `tech-stack.md`, `roadmap.md`), com header `Language:` na mesma convenção das specs.

<!-- section: Out-of-band effects -->
## Out-of-band effects

- Nenhum. A inferência lê só arquivos locais; nada é enviado pela rede; a escrita acontece apenas no projeto consumidor e só após aprovação.

<!-- section: Open risks -->
## Open risks

- Duplicação com o bloco auto-stack: dois lugares descrevendo a stack podem divergir (cl-3).
- Inferência "criativa": o agente pode preencher missão ou público a partir de pistas fracas. O contrato "cita a fonte ou marca clarificação" precisa ser verificável pelo revisor.
- Custo de contexto: `specify` e `plan` passam a ler até três arquivos extras em toda execução; em produtos com roadmap longo isso pesa.
- Se o `roadmap.md` virar lista de desejos sem dono, `replan` e o modo roadmap (0024, 0028) herdam o ruído.

<!-- section: Traceability -->
## Traceability

- Originating issue: comparação do aiadev com o curso "Spec-Driven Development with Coding Agents" (DeepLearning.AI × JetBrains, Paul Everitt) — conversa de 2026-09-24, melhoria 1 de 7.
- Related specs: `0024-replan`, `0027-brownfield-bootstrap`, `0028-implement-roadmap-mode` (dependem desta); `0016-agent-skills-interop` (frontmatter e distribuição multiplataforma).
- Constitution articles invoked: I, II, III, IV, VI, VII

### Constitution Check (preliminar)

> Avaliação no nível da spec. O `plan` refaz a checagem com evidência concreta.

| Artigo | Aplica? | Avaliação preliminar |
|---|---|---|
| I. Spec-first | Sim | Esta spec; cl-1…cl-6 resolvidas em 2026-09-24. |
| II. Test-first | Sim | Testes de forma dos templates (anchors, ausência de conteúdo de produto), de texto das skills (`specify`/`plan` citam os artefatos) e de instalação nas 5 plataformas precedem as edições. |
| III. Simplicity | Sim | Reaproveitar `project_introspect` e o contrato de bootstrap do `constitution`; nenhuma flag nova sem usuário nomeado; cl-3 e cl-4 evitam camada duplicada. |
| IV. Evidence over claims | Sim | Cada valor inferido cita a fonte; PR lista comandos (`aiadev validate`, `pytest`) com saída. |
| V. Provider pattern | Não | Sem dependência externa com fronteira de rede. |
| VI. Privacy by design | Sim | A inferência exclui `.env*`, chaves e credenciais; nada sai da máquina. |
| VII. Attribution | Sim | Templates escritos do zero; entrada de inspiração (só a ideia) para o curso SDD em `CREDITS.md` (cl-6). |
