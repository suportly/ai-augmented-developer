# Feature specification: BMAD-inspired framework evolutions

> This file is produced by the `specify` skill (or by `aiadev init --feature <name>` as a stub). Keep it focused on **what** and **why** — planning and code belong in `plan.md` and `tasks.md`.

**Branch:** `feature/bmad-inspired-evolutions`
**Created:** 2026-05-13
**Status:** Approved <!-- Draft | In review | Approved | Implemented -->
**Spec ID:** 0014 <!-- auto-incrementing integer -->
**Language:** pt-BR <!-- BCP-47 tag; every downstream artifact in this feature is written in this language. -->

---

<!-- section: Problem -->
## Problem

Uma análise comparativa do framework [BMAD-METHOD](https://github.com/bmad-code-org/BMAD-METHOD) (v6.6.0) revelou quatro lacunas no AI-Augmented Developer cuja ausência custa qualidade ou adoção: (1) `implement` dispara subagent fresco por task mas o contexto entregue ao subagent é magro — falta uma passada deliberada de *context engineering* equivalente ao `bmad-create-story`; (2) consumidores precisam forkar para sobrescrever skills/agents — não há camada de override por time/usuário sobre o preset; (3) os três reviewer subagents podem retornar APPROVED sem justificativa, o que esvazia a ideia de "review adversarial"; (4) o skill `help` é um leaf que imprime `docs/pipeline-reference.md` verbatim, sem inspecionar o estado de `specs/` para apontar o próximo comando concreto.

<!-- section: Reconnaissance -->
## Reconnaissance

- **skill `implement`** — entry: `skills/implement/SKILL.md` · auth: none · integração: `aiadev.tasks_status` (referenciado em `skills/implement/SKILL.md:53`), `agents/code-reviewer.md`, `agents/spec-document-reviewer.md`, e o template em `templates/tasks-template.md`. Pré-flight existente: `src/aiadev/commands/preflight.py` (CLI `aiadev preflight implement --feature <slug>`, citado em `skills/implement/SKILL.md:32`). O ponto de injeção do *story file* é entre os passos 3 e 4 da loop ("Treat in_progress as pending" → "Dispatch implementer"). Hoje o "Implementer prompt" em `skills/implement/SKILL.md:80-107` recebe `Spec context`, `Plan context` e `Files to create or modify` montados pelo orquestrador inline.
- **CLI `aiadev install`** — entry: `src/aiadev/commands/install.py` · install logic referenciada em `README.md:24-90` · presets em `presets/catalog.json` e `presets/<preset>/`. O resolver atual aplica apenas duas camadas (preset → projeto via `aiadev install`); não há `_aiadev/team.toml` nem `_aiadev/user.toml`. `scripts/sync_assets.py` é o ponto natural para emitir os stubs.
- **agents/ reviewers** — três arquivos: `agents/code-reviewer.md`, `agents/spec-document-reviewer.md`, `agents/plan-document-reviewer.md`. O `code-reviewer.md` (linhas 75-94) já tem seções `### APPROVED` e `### CHANGES_REQUESTED`; falta gate explícito quando APPROVED é emitido sem comentários em mudança não-trivial. Skills consumidoras dos reviewers: `skills/implement/SKILL.md:118-157` (spec + code), `skills/requesting-code-review/SKILL.md`.
- **skill `help`** — entry: `skills/help/SKILL.md` (33 linhas, leaf por design). Imprime `docs/pipeline-reference.md` verbatim e proíbe-se invocar outros skills. A inspeção de estado precisaria ler `specs/<branch>/spec.md`, `plan.md`, `tasks.md`, contar marcadores pendentes do tipo `cl-N` (mesmo padrão que o `clarify` skill resolve), e o branch atual via `git branch --show-current`. `scripts/generate_pipeline_reference.py` (citado em `skills/help/SKILL.md:24`) já existe — é a referência fonte da tabela.

<!-- section: Users and stakeholders -->
## Users and stakeholders

- **Mantenedores do framework** (Suportly) — donos das mudanças, responsáveis por compatibilidade reversa.
- **Consumidores que usam um preset bundled** (django-drf-react, lean, mobile-ops) — beneficiados pelo override de 3 camadas; afetados se o resolver introduzir regressão silenciosa.
- **Consumidores que escrevem extensões/presets próprios** — beneficiados pelo padrão `_aiadev/team.toml` para customizar sem forkar.
- **Agentes de coding (Claude Code, Cursor, Codex, Gemini, OpenCode)** — consumidores diretos do prompt mais rico do `compose-story` e do `help` state-aware.
- **Reviewers humanos de PR** — beneficiados pela disciplina adversarial reforçada (APPROVED nunca vazio em mudança não-trivial).

<!-- section: Success criteria -->
## Success criteria

- Toda invocação de `implement` em projeto com `task-context` habilitado produz, antes de cada task, um arquivo `specs/<branch>/task-context/<TID>-<slug>.md` que o subagent implementador consome no lugar do prompt inline; `aiadev preflight implement` valida a presença do task-context file quando o flag está ligado.
- Override de skill via `_aiadev/team.toml` ou `_aiadev/user.toml` aplicado por consumidor exemplo (django-drf-react) é refletido pelo resolver na próxima invocação de qualquer skill ou comando `aiadev` que carregue a configuração mergeada (nome exato do subcomando CLI pendente em cl-3/cl-4), sem perda de identidade dos itens base (matching por `code`/`id`).
- Toda saída APPROVED de um reviewer subagent (`code-reviewer`, `spec-document-reviewer`, `plan-document-reviewer`) em mudança não-trivial (definição em cl-5) contém o bloco `### Why no issues` com ≥ 3 verificações citáveis OU o orquestrador re-dispatcha com framing adversarial reforçado — verificado estruturalmente pela regra correspondente nos arquivos `agents/*.md` e por uma asserção em `aiadev preflight requesting-code-review` que falha se a saída do reviewer mais recente em `specs/<branch>/.review-log.jsonl` violar a regra.
- `/aia:help` invocado em projeto com spec ativo retorna o próximo comando correto (`/aiadev:clarify` | `/aiadev:plan` | `/aiadev:tasks` | `/aiadev:implement`) em ≤ 1 segundo de execução do skill, e o flag `--plain` continua emitindo a referência verbatim para retrocompatibilidade.
- Nenhum dos quatro movimentos quebra um `aiadev install` existente sem explicit opt-in (changeset deve ser puramente aditivo na superfície CLI).

<!-- section: Non-goals -->
## Non-goals

- **Adoção de personas nomeadas no estilo BMAD** (Mary, John, Winston, Amelia). O `code-style.md` do projeto já desencoraja shouting e gamificação; personas ficam para um spec separado se a demanda surgir.
- **Tracks adaptativos por escala** (Quick / Method / Enterprise). Mencionados na análise como Tier 2; ficam fora deste spec.
- **Sharding de spec/plan grandes** via `markdown-tree-parser`. Tier 2; spec separado se necessário.
- **Migração para o DSL XML-em-Markdown do BMAD.** A linguagem de skill atual (Markdown + frontmatter YAML) permanece; este spec não introduz `<workflow>`, `<step>`, `<action>`, etc.
- **Modo "brownfield"** (`bmad-document-project` equivalente). Fora de escopo.
- **Reescrita do `aiadev install` em outro idioma**. Continua Python.

<!-- section: User stories -->
## User stories

### Story 1 — Skill `task-context` produz arquivo de contexto rico por task (P1)

Como **orquestrador do `implement`**, quero **gerar um arquivo de contexto rico para cada task antes de dispatchar o subagent implementador**, para que **o implementador receba contexto auto-suficiente (slice de spec, slice de plan, lista exata de arquivos com excerpts relevantes, checklist TDD, ponteiro para o task-context anterior) sem depender de prompts hand-crafted reescritos a cada iteração**.

**Acceptance scenarios** (Given / When / Then):

1. **Given** `tasks.md` contém T003 com status `pending`, **when** o orquestrador roda o novo skill `task-context T003`, **then** o arquivo `specs/<branch>/task-context/T003-<slug>.md` é criado contendo: (a) o slice de `spec.md` com os acceptance scenarios mapeados para T003, (b) o bloco completo de T003 em `plan.md`, (c) lista exata de arquivos a criar/modificar com excerpts ≤ 40 linhas dos arquivos a modificar, (d) checklist TDD copiado do `test-driven-development`, (e) ponteiro para `task-context/T002-*.md` se existir.
2. **Given** o arquivo `task-context/T003-<slug>.md` existe, **when** `implement` chega em T003, **then** o "Implementer prompt" (`skills/implement/SKILL.md:80-107`) é substituído por um prompt curto que carrega o task-context por path em vez de inline-montar `Spec context` + `Plan context` + `Files to create or modify`.
3. **Given** o usuário roda `implement` em projeto **sem** habilitar `task-context` (default off), **when** o loop dispatcha o implementador, **then** o comportamento atual (prompt inline montado pelo orquestrador) roda byte-a-byte inalterado — feature é puramente aditiva.
4. **Given** `task-context/T003-<slug>.md` existe mas `git log -- <files-em-T003>` mostra commits após o `mtime` do arquivo, **when** o orquestrador inspeciona staleness no início do passo, **then** ele recompõe o task-context antes do dispatch e registra "task-context refreshed" no log.

**Modo de ativação:** opt-in via configuração de preset + flag CLI, **default off**. Preset declara `task_context: true` em `presets/<preset>/preset.yaml`; CLI aceita `aiadev preflight implement --task-context` para overridar pontualmente. Adopters validam custo/benefício antes de qualquer mudança de default. Resolvido (cl-1) — alinhado a Article III (YAGNI: sem flag sem usuário nomeado, ver cl-8).

**Nome do skill:** `task-context`. Slug em `skills/task-context/SKILL.md`; template em `templates/task-context-template.md`; artefatos por task em `specs/<branch>/task-context/<TID>-<slug>.md`. Resolvido (cl-2) — alinhado ao vocabulário do framework (`tasks.md` é a unidade existente; "story" é jargão BMAD evitado).

### Story 2 — Customização em 3 camadas (base → team → user) (P1)

Como **consumidor do framework**, quero **sobrescrever menus/principles/handoffs de skills e agents via `_aiadev/team.toml` (commitado) e `_aiadev/user.toml` (gitignored)**, para que **eu adapte o framework às convenções do meu time sem forkar o repo do AI-Augmented Developer**.

**Acceptance scenarios** (Given / When / Then):

1. **Given** projeto recém-instalado via `aiadev install --preset lean`, **when** a instalação completa, **then** os arquivos `_aiadev/team.toml` (commit-ready, com header explicando merge rules) e `.gitignore`-entry para `_aiadev/user.toml` estão criados; ambos vazios são válidos.
2. **Given** `skills/analyze/customize.toml` define `[[skill.handoffs]] code = "checklist"`, e `_aiadev/team.toml` adiciona `[[analyze.handoffs]] code = "security-review"`, e `_aiadev/user.toml` adiciona `[[analyze.handoffs]] code = "personal-notes"`, **when** o resolver Python (`src/aiadev/customization.py`) corre, **then** a lista mergeada de handoffs é `[checklist, security-review, personal-notes]` na ordem de precedência (base → team → user, replace-or-append por chave `code`).
3. **Given** o mesmo scalar `default_model` definido como `sonnet` em base, `opus` em team, `haiku` em user, **when** o resolver corre, **then** o valor efetivo é `haiku` (user vence team, team vence base) — comportamento documentado em `docs/customization.md`.
4. **Given** `_aiadev/team.toml` malformado (TOML inválido na linha 12), **when** o resolver é invocado por qualquer skill ou pelo CLI, **then** ele aborta com `ERROR: _aiadev/team.toml line 12: <parse-error>` e código de saída ≠ 0; nunca prossegue silenciosamente com o base.
5. **Given** uma extensão de terceiros instalada via `aiadev extension add`, **when** ela define `_aiadev/team.toml` no projeto, **then** as overrides aplicam-se também a skills oriundos da extensão (não só a skills bundled).

**Diretório de overrides:** `_aiadev/` na raiz do projeto consumidor. Visível no `ls`, alinha com a convenção BMAD (`_bmad/`), e o underscore-prefix sinaliza "arquivos de configuração sintetizados" sem colidir com `~/.aiadev/extensions/` (config global). Resolvido (cl-3).

**Formato dos overrides:** TOML. Arquivos: `_aiadev/team.toml` (commitado) e `_aiadev/user.toml` (gitignored). Parser via `tomllib` da stdlib (Python ≥ 3.11, zero dependência externa). Arrays-de-tabelas mergeiam por chave `code` ou `id` (replace-or-append); scalars seguem precedência base → team → user. Suporte a comentários é importante para arquivos de configuração editados à mão. Resolvido (cl-4).

### Story 3 — Reviewer subagents adotam regra "zero-findings-halt" (P2)

Como **mantenedor do framework**, quero que **os três reviewer subagents (`code-reviewer`, `spec-document-reviewer`, `plan-document-reviewer`) sejam proibidos de retornar APPROVED sem justificativa quando revisarem mudança não-trivial**, para que **o "review adversarial" seja real, não cerimônia — e PRs com problemas reais não escapem por preguiça do reviewer**.

**Acceptance scenarios** (Given / When / Then):

1. **Given** o `code-reviewer` recebe um diff com ≥ 20 linhas de código de produção alteradas, **when** ele conclui sem achados, **then** sua resposta APPROVED MUST incluir um bloco `### Why no issues` listando 3-5 verificações específicas feitas (e.g. "queryset escopado por usuário em `views.py:42`", "input validado em `serializers.py:18`", "test coverage exercita acceptance scenario AC-2"). Ausência desse bloco é um output inválido.
2. **Given** mesmo cenário do (1), **when** o reviewer retorna APPROVED sem o bloco `### Why no issues`, **then** o orquestrador (em `skills/implement/SKILL.md` ou `skills/requesting-code-review/`) detecta a ausência e re-dispatcha o reviewer com framing adversarial reforçado: "Você aprovou sem justificar — assuma que existe ao menos um bug e mostre ele OU justifique cada ausência por categoria (segurança, perf, spec, testes, complexidade)".
3. **Given** o diff é trivial (≤ 10 linhas, e.g. typo, comment, formatação), **when** APPROVED sem bloco é emitido, **then** o orquestrador NÃO re-dispatcha — a regra não se aplica a no-ops, evitando ruído (a heurística de "trivial" usa `git diff --shortstat` e ignora arquivos `*.md` puros).
4. **Given** o `spec-document-reviewer` ou `plan-document-reviewer` aprova um spec/plan novo (criação completa), **when** APPROVED é emitido, **then** o bloco `### Why no issues` é OBRIGATÓRIO independentemente do tamanho — criação de artefato governance-relevante nunca é trivial.
5. **Given** terse-mode ativo (cf. `.claude/rules/terse-mode.md`), **when** APPROVED é emitido, **then** o bloco vira uma única linha por verificação (`🟢 file:line — verificação realizada`) respeitando o schema `terse-output.schema.json`.

**Definição de "mudança não-trivial":** `git diff --shortstat --ignore-blank-lines` reporta > 10 linhas alteradas, excluindo arquivos com extensão exclusiva `.md`, `.json`, `.lock`, `.toml` e arquivos sob `docs/`. Heurística determinística, testável via fixture. **Exceção:** criação ou alteração estrutural de spec/plan (qualquer diff sob `specs/<branch>/{spec,plan}.md`) é SEMPRE não-trivial — Story 3 AC-4 cobre esse override. Resolvido (cl-5).

### Story 4 — `help` skill state-aware sugere o próximo comando (P2)

Como **usuário recém-chegado ao pipeline**, quero que **`/aia:help` inspecione o estado de `specs/` e me diga qual é o próximo comando correto** (em vez de sempre imprimir a referência completa), para que **eu não precise memorizar a ordem dos skills nem cruzar referência manualmente com o estado do meu branch**.

**Acceptance scenarios** (Given / When / Then):

1. **Given** projeto sem diretório `specs/` ou `specs/` vazio, **when** `/aia:help` corre, **then** a saída começa com `Próximo passo: rode /aiadev:specify "<sua demanda>"` e DEPOIS imprime a tabela atual de `docs/pipeline-reference.md`.
2. **Given** branch atual é `feature/X` e `specs/<NNNN>-X/spec.md` contém ≥ 1 marcador `cl-N` pendente (mesmo formato canônico que o `clarify` skill consome e resolve), **when** `/aia:help` corre, **then** a recomendação é `Próximo passo: rode /aiadev:clarify (N marcadores pendentes em specs/<NNNN>-X/spec.md)`.
3. **Given** `spec.md` sem marcadores e sem `plan.md`, **when** `/aia:help` corre, **then** recomendação é `/aiadev:plan`.
4. **Given** `spec.md` + `plan.md` com Constitution Check ticked, sem `tasks.md`, **when** `/aia:help` corre, **then** recomendação é `/aiadev:tasks`.
5. **Given** `spec.md` + `plan.md` + `tasks.md` com ao menos uma task em `**Status:** pending`, **when** `/aia:help` corre, **then** recomendação é `/aiadev:implement`.
6. **Given** o usuário passa `/aia:help --plain` (ou variável de ambiente `AIADEV_HELP_PLAIN=1`), **when** o skill corre, **then** a inspeção de estado é pulada e o output é byte-a-byte idêntico ao comportamento atual (cat de `docs/pipeline-reference.md`) — escape hatch para retrocompatibilidade e CI.
7. **Given** todas as tasks de `tasks.md` estão `done`, **when** `/aia:help` corre, **then** recomendação é `Próximo passo: /aiadev:requesting-code-review` (ou `/aiadev:finishing-a-branch` se review já passou — ver `tasks.md` para o último status).
8. **Given** múltiplos branches têm spec ativo, **when** `/aia:help` corre, **then** a recomendação cobre o spec do branch atual (`git branch --show-current`); specs órfãos não geram recomendação.

**Localização da lógica state-aware:** módulo Python `src/aiadev/pipeline_state.py`. Expõe `recommend_next_command(workspace_path: Path) -> dict` (retorna `{"command": "/aiadev:plan", "reason": "spec.md sem marcadores; plan.md ausente"}`). Reusado por (a) `skills/help/SKILL.md` via `python -c`, (b) comandos `aiadev preflight`, (c) extensão VS Code Spec Explorer (já lê `specs/` e pode ganhar surface "next step"). Testável com fixtures pytest. Resolvido (cl-6).

<!-- section: Clarifications -->
## Clarifications

<!-- cl-1 a cl-6 estão inline nas user stories correspondentes; cl-7 a cl-9
     são globais e moram aqui. O `clarify` skill varre o arquivo inteiro
     em busca de marcadores `cl-N`, então a localização é organizacional. -->

- **Forma de entrega:** UMA PR única neste branch (`feature/bmad-inspired-evolutions`). Decisão consciente do mantenedor — apesar de `git-workflow.md` recomendar PRs < 500 linhas e "one feature per branch", os 4 movimentos compartilham origem (análise BMAD), tema (evolução do framework), e dependências (Story 1 usa o flag-pattern de Story 2; Story 4 reusa o módulo `pipeline_state` que serve `aiadev preflight`). Tradeoff aceito: revisor humano olha tudo junto. Mitigação: commits por task em `tasks.md` permitem leitura incremental, e o `plan` deve ordenar tasks por risco crescente (Stories 3 e 4 primeiro, Story 2 depois, Story 1 por último). Resolvido (cl-7).
- **Article III (Simplicity / YAGNI) — named user do flag `task_context: true`:** o preset `presets/django-drf-react/` ativa `task_context: true` como dogfood, exercitando o caminho não-default em CI do próprio framework. Para `_aiadev/user.toml`, o próprio repo do framework comita um `_aiadev/user.toml.example` no `.gitignore` e documenta o uso pessoal em `docs/customization.md`. Sem essa cobertura, Story 1 e Story 2 ficariam em waiver — com ela, Article III é satisfeito sem waiver. Resolvido (cl-8).
- **Constitution Article V (Provider pattern): NÃO invocado.** `src/aiadev/customization.py` é um módulo interno de leitura/merge de TOML — não cruza fronteira de rede nem de SDK externo. Article V cobre integrações externas (LLM API, DB, storage), e merge in-process não se qualifica. Registrado como decisão explícita em Traceability. Resolvido (cl-9).

<!-- section: Data touched -->
## Data touched

- **Novos arquivos no repo do framework:**
  - `skills/task-context/SKILL.md`
  - `templates/task-context-template.md`
  - `src/aiadev/customization.py` (resolver 3-camadas)
  - `src/aiadev/pipeline_state.py` (lógica state-aware reusável)
  - `docs/customization.md` (regras de merge, exemplos)
- **Novos arquivos no projeto consumidor (criados por `aiadev install`):**
  - `_aiadev/team.toml` (commit, vazio inicialmente)
  - `_aiadev/user.toml` (gitignored, vazio)
  - Linha em `.gitignore`: `_aiadev/user.toml`
  - Diretório `specs/<branch>/task-context/` populado por demanda quando `task_context` ativo
- **Arquivos modificados:**
  - `agents/code-reviewer.md`, `agents/spec-document-reviewer.md`, `agents/plan-document-reviewer.md` (regra zero-findings-halt + bloco `### Why no issues`)
  - `skills/help/SKILL.md` (state-aware + flag `--plain`)
  - `skills/implement/SKILL.md` (passo opcional de leitura de story file; gate de re-dispatch para reviewer sem justificativa)
  - `skills/requesting-code-review/SKILL.md` (idem gate de re-dispatch)
  - `presets/catalog.json` e `presets/<preset>/install-manifest.*` (declarar `_aiadev/` stubs)
  - `schemas/terse-output.schema.json` (adicionar variante para `🟢 verification`)
- **Sem mudanças de schema de DB ou storage externo.**

<!-- section: Out-of-band effects -->
## Out-of-band effects

- Nenhuma chamada de rede nova; sem notificações; sem pagamento; sem write a storage externo.
- Story 1 aumenta o consumo de tokens por task (uma chamada de modelo extra para compor o task-context). Mensurar em `aiadev preflight implement` antes de virar default.
- Story 3 aumenta o número de re-dispatches de reviewer subagents quando justificativa estiver ausente — efeito esperado, mas precisa instrumentação para evitar loop infinito (limite de 2 re-dispatches por reviewer por task).

<!-- section: Open risks -->
## Open risks

- **Custo de tokens** do `task-context` pode tornar `implement` significativamente mais caro em projetos com tasks pequenas. Mitigação pertence ao `plan.md`, não aqui.
- **Resolver TOML 3-camadas** é a peça mais propensa a bug silencioso (merge errado de array-of-tables, key-collision misterioso). Property tests obrigatórios.
- **Regra zero-findings-halt** pode degenerar em loop reviewer ↔ orquestrador se o critério de "trivial" estiver mal calibrado. Limite duro de re-dispatches.
- **`help` state-aware** pode dar conselho errado se a inspeção de `tasks.md` ignorar status `blocked` ou tasks `in_progress` órfãs (crash de execução anterior); spec exige cobrir esses casos no `pipeline_state.py`.
- **Compatibilidade reversa**: qualquer regressão silenciosa quebra adopters atuais. Story 1 (default off), Story 2 (puramente aditivo), Story 3 (só altera saída de reviewer, comportamento default APPROVED ainda válido se justificado), Story 4 (`--plain` preserva legacy) — todos os 4 desenhados aditivos, mas a verificação fica para o `analyze` skill ao final.

<!-- section: Traceability -->
## Traceability

- Originating issue: nenhuma — análise em sessão de chat (turno anterior nesta conversa) comparando AI-Augmented Developer com [BMAD-METHOD v6.6.0](https://github.com/bmad-code-org/BMAD-METHOD).
- Related specs: `0011-specify-reconnaissance` (precedente para reconhecimento estruturado), `0013-implement-task-status-tracking` (estado canônico de task que Story 4 lê).
- Constitution articles invoked: I (Spec-first — todo o spec), II (Test-first — Story 1 inclui checklist TDD no story file; Stories 2-4 implementadas test-first), III (Simplicity — cl-8 marca a tensão YAGNI no flag `compose_stories`), IV (Evidence over claims — Story 3 é literalmente sobre evidência no review), VII (Attribution — `CREDITS.md` ganhará entrada para `bmad-code-org/BMAD-METHOD` na PR final).
- Constitution articles **not** invoked, with rationale: V (Provider pattern) — ver cl-9; VI (Privacy by design) — nenhum dado sensível tocado, apenas arquivos de configuração e artefatos de spec, sem PII e sem campos cifráveis.
