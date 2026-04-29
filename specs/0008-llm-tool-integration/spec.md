# Feature specification: aiadev como ferramenta de LLM (LLM tool integration)

> Este arquivo é produzido pelo skill `specify`. Mantém o foco em **o quê** e **por quê** — planejamento e código vão para `plan.md` e `tasks.md`.

**Branch:** `feature/llm-tool-integration`
**Created:** 2026-04-16
**Status:** Implemented
**Approved on:** 2026-04-16 (pós-`clarify`; reviewer: spec-document-reviewer)
**Spec ID:** 0008
**Language:** pt-BR <!-- BCP-47; toda artefato downstream desta feature usa este idioma. -->

---

## Problem

Hoje o framework `aiadev` só é consumível por **agentes humanos** operando dentro de um harness específico (Claude Code, Cursor, Codex, etc.) que carrega skills via `.claude/skills/`. Um agente LLM rodando fora desse harness — por exemplo, um worker autônomo construído sobre Claude Agent SDK, LiteLLM, Anthropic SDK, OpenAI SDK ou um cliente MCP genérico — **não consegue invocar o pipeline `specify → clarify → plan → tasks → implement` como ferramentas estruturadas (tools)**. Para que `aiadev` sirva de "guia oficial" de geração de specs em qualquer projeto consumidor, é preciso eliminar a obrigação de cada integração reimplementar a lógica dos skills à mão.

Evidência: ao construir um pipeline autônomo de geração de issue→spec→plan→implement→PR sem `aiadev` exposto como tools, o consumidor inevitavelmente recria, ad-hoc, a mesma lógica que `aiadev` já formaliza nos skills `specify`, `plan`, `tasks`, `implement` — duplicando código e divergindo da fonte da verdade.

## Users and stakeholders

- **Usuário primário:** mantenedores e integradores que querem usar `aiadev` como guia canônico de geração de specs em projetos consumidores, sem duplicar/reimplementar a lógica dos skills.
- **Agentes LLM consumidores:** qualquer agente autônomo construído sobre Claude Agent SDK, LiteLLM, Anthropic/OpenAI SDK ou cliente MCP genérico que precise gerar/validar artefatos do pipeline.
- **Mantenedores do `aiadev`:** ganham um segundo modo de consumo (programático) sem fragmentar a fonte da verdade dos skills.
- **Outros consumidores potenciais:** projetos que adotem `aiadev` mas usem harnesses ainda não suportados (CrewAI, LangGraph, frameworks de orquestração futuros).

## Success criteria

- Um agente LLM rodando fora do Claude Code consegue invocar pelo menos os skills `specify`, `clarify`, `plan`, `tasks`, `implement`, `analyze`, `checklist`, `constitution` como **tools MCP (stdio) ou objetos de tool em biblioteca Python**, receber o prompt canônico + contexto correspondente, e — executando o prompt com seus próprios tools de filesystem — produzir os mesmos artefatos (`spec.md`, `plan.md`, etc.) que um humano obteria via `/aia:specify`.
- Quando o caller segue o prompt retornado, cada artefato resultante (ex: `spec.md`) contém **todas as seções obrigatórias do template canônico** correspondente (`templates/spec-template.md`, `templates/plan-template.md`, etc.) — verificável por checagem de presença de header de seção.
- O `plan.md` produzido após invocar a tool `plan` contém uma seção **Constitution Check** que lista os 7 artigos da `constitution.md` com status `ok | waiver | fail` para cada, conforme a estrutura definida em `templates/plan-template.md`.
- Um projeto consumidor que hoje reimplementa a geração de spec/plan ad-hoc consegue substituir essa lógica por chamadas às tools sem regressão funcional observável (mesmas seções obrigatórias presentes nos artefatos gerados).
- Há um teste de contrato (Article II) que invoca cada tool com um input-fixture e valida (i) que o prompt retornado inclui as seções/instruções esperadas e um `target_path` dentro do `workspace_path`, (ii) que, ao executar o prompt contra um LLM-fake (Article V) com filesystem real, o artefato produzido satisfaz o template.
- A documentação (`README.md` ou página dedicada) descreve **como** instalar o servidor MCP stdio e **como** usar a biblioteca Python in-process em pelo menos um stack-alvo cada.
- Zero duplicação de conteúdo: a definição da tool consome `SKILL.md` como fonte da verdade (não recopia o texto).

## Non-goals

- **Substituir o Claude Code** ou outros harnesses existentes — esta feature **adiciona** um modo de consumo, não remove os atuais (`.claude/skills/` continua funcionando).
- **Executar artefatos finais** (rodar testes, fazer commit, abrir PR) a partir da tool — escopo é geração de artefatos do pipeline. Execução fica a cargo do agente chamador.
- Reimplementar os skills em outra linguagem. A fonte da verdade permanece em Markdown (`SKILL.md`).
- Empacotar e publicar o `aiadev` como pacote `npm` ou crate Rust. Distribuição continua via PyPI (spec 0005).
- Suporte a fluxos multi-tenant ou autenticação — escopo é uso local/embarcado.

## User stories

### Story 1 — Agente autônomo invoca `specify` como tool (P1)

Como **agente LLM autônomo de um projeto consumidor**, eu quero **chamar `aiadev.specify(demand=...)` como uma tool exposta ao meu LLM**, para que **o `spec.md` gerado siga o template e a constituição do `aiadev` sem que eu precise reimplementar o skill no meu código**.

**Acceptance scenarios** (Given / When / Then):

1. **Given** o agente recebeu uma demanda em texto livre e tem o `aiadev` instalado e registrado como provedor de tools (MCP stdio ou lib Python), **When** o LLM chama a tool `specify` com `demand` e `workspace_path` como argumentos, **Then** a resposta contém um payload estruturado com (i) o conteúdo de `skills/specify/SKILL.md`, (ii) o template `templates/spec-template.md`, (iii) o `target_path = <workspace_path>/specs/<NNNN>-<slug>/spec.md` pré-computado e válido (slug derivado da demanda; `NNNN` monotonicamente incrementado).
2. **Given** o caller LLM seguiu o prompt retornado pela tool `specify` usando seus próprios tools de filesystem, **When** o `target_path` é lido após a execução, **Then** o arquivo existe e contém todos os headers de seção obrigatórios definidos em `templates/spec-template.md` (Problem, Users and stakeholders, Success criteria, Non-goals, User stories, Clarifications, Data touched, Out-of-band effects, Open risks, Traceability) e ≥1 user story com ≥3 cenários.
3. **Given** o `spec.md` produzido pelo caller contém marcadores `[NEEDS CLARIFICATION:cl-N ...]`, **When** o caller LLM consome o output da própria execução do prompt do `specify` (que instrui a enumerar os marcadores criados), **Then** o caller dispõe de um array estruturado `[{id, question, location}, ...]` para decidir se invoca `clarify` em seguida — sem necessidade de uma tool extra de enumeração.
4. **Given** a demanda do usuário está em pt-BR, **When** a tool `specify` é invocada, **Then** o prompt retornado instrui explicitamente o caller a stampar `Language: pt-BR` no header e a redigir o conteúdo das seções em pt-BR.

### Story 2 — Encadeamento `clarify → plan → tasks` via tool calls (P1)

Como **agente LLM autônomo**, eu quero **invocar `clarify`, `plan` e `tasks` em sequência como tools separadas**, para que **eu controle o fluxo (e possa pedir input ao humano entre etapas) sem precisar de um único endpoint monolítico**.

**Acceptance scenarios**:

1. **Given** existe um `spec.md` com 2 marcadores `[NEEDS CLARIFICATION:cl-1 ...]` e `[NEEDS CLARIFICATION:cl-2 ...]`, **When** o agente chama `clarify(spec_path=..., workspace_path=..., answers=[{id: "cl-1", answer: "..."}, {id: "cl-2", answer: "..."}])`, **Then** a resposta contém o prompt do skill `clarify` parametrizado com as respostas, e — ao ser seguido pelo caller — os marcadores correspondentes são substituídos no arquivo e zero marcadores remanescentes podem ser encontrados via grep.
2. **Given** o `spec.md` está limpo (zero marcadores), **When** o agente chama `plan(spec_path=..., workspace_path=...)` e segue o prompt retornado, **Then** o `plan.md` é criado no mesmo diretório do spec contendo a seção **Constitution Check** com status `ok | waiver | fail` para cada um dos 7 artigos, conforme `templates/plan-template.md`.
3. **Given** o `plan.md` está aprovado, **When** o agente chama `tasks(plan_path=..., workspace_path=...)` e segue o prompt retornado, **Then** `tasks.md` é criado no mesmo diretório com tarefas no formato "1 teste + 1 implementação + 1 commit" definido em `templates/tasks-template.md`.

### Story 3 — Erros, limites e resiliência (P2)

Como **agente LLM consumindo as tools do `aiadev`**, eu quero **respostas determinísticas para entradas inválidas, conflitos de path e falhas internas**, para que **eu possa decidir quando reintentar, quando abortar e quando pedir ajuda ao humano sem ter que parsear stack traces**.

**Acceptance scenarios**:

1. **Given** um `workspace_path` aponta para fora do diretório autorizado (tentativa de path traversal, ex: `../../etc`) ou não é um diretório existente, **When** qualquer tool é invocada com esse parâmetro, **Then** a tool retorna um erro estruturado `{code: "invalid_workspace", message: ...}` e **não retorna prompt** (logo, o caller não tem instruções para criar arquivos).
2. **Given** já existe um `spec.md` no `target_path` que `specify` calcularia (mesma slug), **When** a tool `specify` é invocada, **Then** ela retorna um erro estruturado `{code: "artifact_exists", path: ...}` em vez de devolver um prompt que sobrescreveria silenciosamente; a continuação requer flag explícita (`overwrite=true`) ou nova slug.
3. **Given** a tool `plan` é invocada com um `spec_path` que aponta para um arquivo malformado (faltam seções obrigatórias) ou inexistente, **When** o handler tenta carregá-lo para compor o contexto do prompt, **Then** a resposta é um erro estruturado (`{code: "spec_invalid", missing_sections: [...]}` ou `{code: "spec_not_found", path: ...}`) e nenhum prompt é retornado.

### Story 4 — Descobribilidade do catálogo de tools (P2)

Como **integrador construindo um agente que vai usar `aiadev`**, eu quero **listar programaticamente todas as tools/prompts disponíveis (nome, descrição, schema de input)**, para que **meu cliente MCP ou minha integração Python registre o catálogo automaticamente sem que eu tenha que ler cada `SKILL.md` à mão**.

**Acceptance scenarios**:

1. **Given** o `aiadev` está instalado, **When** invoco o comando/endpoint de listagem de tools, **Then** recebo um array com pelo menos {name, description, input_schema, output_schema} para cada skill exportável.
2. **Given** a listagem foi gerada, **When** cada definição é validada contra o JSON Schema público do MCP (`tools/list` e `prompts/list`) por um validador offline, **Then** todas validam sem erro — sem necessidade de cliente MCP real ou chamada ao LLM.
3. **Given** um skill foi adicionado ou removido em `skills/`, **When** a listagem é refeita, **Then** o resultado reflete o estado atual sem necessidade de rebuild manual de um catálogo.

## Clarifications

- **Modo de exposição:** dois transportes suportados, compartilhando a mesma lógica interna:
  1. **Servidor MCP em modo stdio** (transporte canônico) — clientes MCP-compatíveis (Claude Code, Claude Agent SDK, clientes MCP genéricos) lançam `aiadev` como subprocesso via config MCP. Sem daemon, sem porta aberta.
  2. **Biblioteca Python de tools nativas** (conveniência local) — objetos de tool importáveis para integração in-process com Anthropic SDK / LiteLLM, com latência zero. HTTP, CLI-via-subprocess e wrapper específico do Claude Agent SDK ficam **fora de escopo** desta feature.
- **Forma de execução do skill (skill-as-prompt-loader):** quando uma tool/`prompts/get` é invocada, o handler carrega `SKILL.md` + contexto necessário (template aplicável, trecho de `constitution.md`) e **retorna esse conteúdo estruturado** ao LLM chamador. O caller (LLM externo) executa as instruções usando seus próprios tools (Read/Write/Edit). Sem LLM interno no `aiadev`, sem credenciais de provedor configuradas no servidor MCP, fonte da verdade única em Markdown. Em MCP, mapeia preferencialmente para o primitivo `prompts/get`; pode ser exposto também via `tools/call` retornando o prompt para clientes que não consomem `prompts`.
- **Catálogo do v1:** apenas os 8 skills do pipeline são expostos como tools/prompts: `specify`, `clarify`, `plan`, `tasks`, `implement`, `analyze`, `checklist`, `constitution`. Skills auxiliares (`systematic-debugging`, `test-driven-development`, `frontend-design`, `requesting-code-review`, `finishing-a-branch`) e preset-specific ficam fora do v1 — entram em iterações futuras quando houver caller declarado (Article III).
- **Local de execução:** decorre das escolhas anteriores. O servidor MCP stdio roda como **subprocesso do cliente** (lançado sob demanda via config MCP; lifecycle gerenciado pelo cliente; sem daemon). A biblioteca Python roda **in-process** no consumidor. Não há modo "serviço separado" (HTTP/containerizado) no v1.
- **Workspace alvo:** `workspace_path` é parâmetro **obrigatório** no input de toda tool (`specify`, `clarify`, `plan`, `tasks`, `implement`, `analyze`, `checklist`, `constitution`). O handler valida que (i) é um diretório existente e (ii) que qualquer path derivado pelo prompt (ex.: `<workspace_path>/specs/<NNNN>-<slug>/spec.md`) não escapa dele. O prompt retornado ao caller já contém o path absoluto embutido nas instruções, eliminando ambiguidade sobre onde escrever.
- **Reviewers (`spec-document-reviewer`, `plan-document-reviewer`):** o `aiadev` honra a cláusula condicional já presente nos `SKILL.md` ("Dispatch ... if available"). Callers com `Agent` tool (Claude Code) executam o reviewer; callers sem (lib Python pura, clientes MCP genéricos) pulam. Trade-off aceito: qualidade não-uniforme entre clientes; quem precisar de gate uniforme implementa o próprio passo de revisão no harness.
- **Versionamento do schema das tools:** amarrado ao semver do `aiadev`. Mudança incompatível no schema = bump major; campo aditivo opcional = minor; bug fix = patch. O cliente identifica a versão via `aiadev --version` ou pelo metadado MCP `serverInfo.version`. Sem dimensão de versão separada (`tools.v1`).
- **Escopo de `implement`:** exposto no v1 igual aos demais skills, sem tratamento especial. Coerente com o modelo skill-as-prompt-loader — o `aiadev` não orquestra LLM nem escreve código; apenas devolve o prompt. Risco de loop, consumo de tokens e supervisão de execução são responsabilidade do caller (que controla seu próprio modelo, budget e harness).
- **Schema de input do `clarify`:** chave de identificação = **id estável** atribuído pelo `specify` no momento de criação do marcador. Novo formato: `[NEEDS CLARIFICATION:cl-3 ...]`. O input do `clarify` é `answers=[{id: "cl-3", answer: "..."}, ...]`. Implica mudança transversal no framework (template `spec-template.md`, skills `specify`/`clarify`, eventuais validators e ferramentas que enumeram marcadores) — tratada como pré-requisito desta feature.
- **Telemetria mínima:** logs estruturados em **stderr no formato JSON-lines**, uma linha por invocação, com `{ts, tool, workspace_path, latency_ms, status, error_code?}`. Stderr é convenção MCP (stdout reservado ao protocolo). O `demand` do usuário e qualquer payload com conteúdo livre **não** vão para o log (Article VI — sem PII). Sem dependências externas, sem endpoint OTel/Prometheus no v1.

## Data touched

- **Novos artefatos no `aiadev`:**
  - Módulo `aiadev/mcp/` — servidor MCP stdio que expõe os 8 skills do pipeline como `prompts` (e/ou `tools`) com `name`, `description`, `arguments`, e o conteúdo gerado dinamicamente a partir de `SKILL.md` + template + contexto.
  - Módulo `aiadev/tools/` — biblioteca Python in-process com a mesma superfície (objetos de tool importáveis), compartilhando a lógica de carregamento de skill com o servidor MCP.
  - Schemas em `schemas/` para input/output de cada tool e validação contra a spec MCP (`tools/list`, `prompts/list`, `prompts/get`).
- **Mudança transversal pré-requisito:** novo formato de marcador `[NEEDS CLARIFICATION:cl-N ...]` propagado em `templates/spec-template.md`, `skills/specify/SKILL.md`, `skills/clarify/SKILL.md`, `scripts/validate_skills.py` (se enumerar marcadores) e qualquer documentação correlata.
- **Sem mudança em:** conteúdo qualitativo de `skills/*/SKILL.md` (Article III — não duplicar conteúdo), `constitution.md`, demais `templates/*`.
- **No consumidor (qualquer projeto integrador):** entrada na config MCP do harness (para o servidor stdio) e/ou import + registro da lib Python. Substituição de qualquer lógica ad-hoc de geração de spec/plan. Migrações de dados: nenhuma esperada nesta feature.

## Out-of-band effects

- **Filesystem (no caller):** ao seguir o prompt retornado, o caller cria/modifica arquivos em `<workspace_path>/specs/`. O `aiadev` valida `workspace_path` antes de retornar o prompt e embute o `target_path` calculado nas instruções, mas a escrita em si acontece no caller (Article VI — workspace segregado por invocação).
- **Filesystem (no servidor MCP):** o servidor lê `skills/*/SKILL.md` e `templates/*` da própria instalação do `aiadev`. Sem escrita.
- **Chamadas LLM:** zero do lado do `aiadev`. O caller consome tokens do **seu** provedor ao executar o prompt. Custo e latência são contabilizados pelo caller.
- **Sem chamadas a APIs externas** a partir do `aiadev`.
- **Sem envio de notificações, cobranças, ou efeitos em terceiros.**
- **Telemetria:** o servidor MCP emite uma linha JSON em stderr por invocação (`{ts, tool, workspace_path, latency_ms, status, error_code?}`); a lib Python expõe a mesma informação via logger configurável. Sem PII ou conteúdo de `demand` no log.

## Open risks

- **Drift entre Markdown e a camada de exposição** — embora a escolha skill-as-prompt-loader minimize o risco (nenhuma reimplementação de lógica), o stamping de `target_path` e o cálculo de `NNNN`/slug ficam no handler. Qualquer mudança no template de path nos `SKILL.md` precisa ser refletida no handler — risco residual.
- **Loop / runaway no caller** — agente externo segue o prompt do `implement` e dispara subagentes que podem voltar a chamar tools do `aiadev`. Mitigação fica no harness do caller (depth bound, budget), não em `aiadev`.
- **Permissões de filesystem no caller** — `aiadev` valida `workspace_path` e instrui o caller a escrever apenas dentro dele, mas a escrita real é feita pelo caller. Caller mal-comportado pode ignorar a instrução. `aiadev` não consegue impor isolamento via filesystem (não está no caminho de escrita).
- **Maturidade do ecossistema MCP fora do Claude Code** — Claude Agent SDK consome MCP nativamente; clientes Python puros precisam de bibliotecas MCP-client maduras (existem, mas em evolução). Para esses, a lib Python in-process serve de saída.
- **Migração de marcadores existentes** — adicionar `cl-N` ao formato impacta specs já gravados no repo (7 specs `feature-*` + 0008 atual). Decidir entre: (i) deixar como estão e aplicar só em specs novos; (ii) migração one-shot via script. Definição fica no plan.
- **Cobertura de testes** — Article II exige testes falhando antes da implementação. Testar tools sob skill-as-prompt-loader exige (a) testes de unidade do handler (cálculo de path, validação, montagem do payload — sem LLM), (b) testes de integração end-to-end com um LLM-fake (Article V) que segue o prompt e produz o artefato. Fixtures precisam ser desenhadas com cuidado para serem determinísticas.

## Traceability

- **Originating issue:** demanda em conversação (não há issue formal — o usuário pode abrir uma após aprovação do spec).
- **Related specs:**
  - `specs/feature-extensions-system-mvp/` — referência informativa apenas; pode servir de inspiração arquitetural mas **não é dependência bloqueante** desta feature.
- **Convenção de diretório:** este spec adota o padrão `specs/<NNNN>-<slug>/` definido em `templates/spec-template.md` e no skill `specify`. As 7 specs anteriores (`feature-*`) precedem essa convenção e permanecem como estão; ferramentas que enumeram specs precisam aceitar ambos os padrões durante a transição.
- **Constitution articles invoked:** I (spec-first para o próprio framework), II (test-first para a camada de tools), III (não duplicar conteúdo de skills), V (provider pattern para o LLM usado em testes), VI (escrita de filesystem segregada por workspace).
