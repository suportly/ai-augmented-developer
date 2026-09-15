# Feature specification: Smart MCP Proxy — compressor local de saída de terminal

> This file is produced by the `specify` skill (or by `aiadev init --feature <name>` as a stub). Keep it focused on **what** and **why** — planning and code belong in `plan.md` and `tasks.md`.

**Branch:** `feat/smart-mcp-proxy`
**Created:** 2026-09-15
**Status:** Implemented <!-- Draft | In review | Approved | Implemented -->
**Spec ID:** 0022 <!-- auto-incrementing integer -->
**Language:** pt-BR <!-- BCP-47 tag; every downstream artifact in this feature is written in this language. -->

---

<!-- section: Problem -->
## Problem

Saídas longas de comandos de terminal (suítes de teste, builds, instalações, linters) entram inteiras no contexto do agente, custam tokens a cada turno seguinte e diluem o sinal que importa: o erro raiz e o resultado final. O `docs/token-economy.md` (specs 0020/0021) documenta como ligar um compressor externo (`rtk`, `headroom`), mas o framework não oferece nenhum caminho pronto, e os dois compressores citados não usam um modelo local para extrair o erro raiz. Um benchmark headless com Claude Code (`packages/smart-mcp-proxy/BENCHMARK.md`) mostrou que um servidor MCP com um modelo local de 3B via Ollama devolve 85% menos caracteres e custa 44% menos por sessão, mantendo 6/6 acertos de erro raiz. Quem sente: qualquer dev usando Claude Code em projetos com testes ou builds ruidosos.

<!-- section: Reconnaissance -->
## Reconnaissance

- **pacote smart-mcp-proxy** — entry: `packages/smart-mcp-proxy/src/index.ts` · auth: none · integration: hoje um único arquivo com servidor MCP + lógica de condensação; precisa ser fatorado em núcleo reutilizável + três entradas (servidor MCP, CLI, hook).
- **doc token-economy** — entry: `docs/token-economy.md` · auth: none · integration: a tabela de compressores cita só `rtk` e `headroom`; o exemplo de hook é comentado e aponta para `rtk hook pretooluse`.
- **presets opt-in** — entry: `presets/knowledge-graph/mcps.yaml` · auth: none · integration: modelo de preset opt-in que declara um MCP server; o novo preset `token-economy` espelha essa forma.
- **instalador** — entry: `src/aiadev/install_manifest.py` (`FileRole`) e `src/aiadev/platforms/claude_code.py` (`resolve_target`) · auth: none · integration: não há papel para `settings.json`/hooks; fica como follow-up (ver Non-goals).
- **métricas** — entry: `src/aiadev/metrics.py`, `src/aiadev/commands/metrics.py` · auth: none · integration: lê só `specs/**` e `git log`; não tem noção de tokens nem de sessão. Ganha um relatório separado lido dos transcripts do Claude Code.
- **skill de review** — entry: `skills/requesting-code-review/SKILL.md` · auth: none · integration: ganha um passo opcional que usa `smart_git_diff` quando o preset está ativo.

<!-- section: Users and stakeholders -->
## Users and stakeholders

- **Dev usando Claude Code** — quer que comandos ruidosos parem de inflar o contexto sem precisar lembrar de chamar uma tool diferente.
- **Tech lead** — quer evidência numérica de quanto contexto cada tool consome por sessão antes de mandar o time ligar um compressor.
- **Mantenedor do framework** — quer que o compressor exista sem violar o Artigo III (o core do aiadev não implementa compressor) nem adicionar dependência obrigatória.

<!-- section: Success criteria -->
## Success criteria

- Com o preset `token-economy` ativo e o hook registrado, **toda** chamada da tool Bash nativa do Claude Code passa pelo condensador, sem o agente escolher uma tool diferente; saídas abaixo do limite voltam byte a byte iguais.
- O resultado condensado é suficiente para o agente responder o erro raiz com `arquivo:linha` sem pedir a saída bruta, medido pelo benchmark existente: 2 turnos em todos os casos, 6/6 acertos.
- Um diff de git pode ser resumido por arquivo pela tool `smart_git_diff`, com o `--stat` verbatim e o resumo do modelo local, em menos caracteres que o diff bruto.
- `aiadev metrics --tokens` imprime, por sessão do Claude Code do workspace atual, tokens de entrada/saída/cache e caracteres devolvidos por tool, a partir dos transcripts locais; sem transcripts, sai com código 2 e mensagem clara.
- Com o Ollama fora do ar, nada quebra: hook, CLI e tools degradam para trecho truncado + assinaturas de erro.
- O core Python (`src/aiadev`) não ganha dependência nova nem código de compressão; o compressor vive em `packages/smart-mcp-proxy`.

<!-- section: Non-goals -->
## Non-goals

- O instalador (`aiadev install`) escrever ou mesclar `.claude/settings.json`. Exige um novo papel de artefato e merge parcial de um arquivo que o usuário também edita; fica como follow-up. O preset entrega o snippet pronto e o README diz onde colar.
- Resumir `spec.md`/`plan.md` no `task-context` com o modelo local. Risco de perder requisito; só depois que a métrica de tokens provar o ganho.
- Comprimir saída de subagentes revisores (o `terse-mode`, spec 0009, já cobre por convenção).
- Suportar outros backends além do Ollama (a API é uma URL configurável; outros servidores compatíveis funcionam, mas não são testados).

<!-- section: User stories -->
## User stories

### Story 1 — Bash nativo condensado via hook (P1)

As a dev usando Claude Code, I want que a saída longa de qualquer comando Bash chegue ao agente já condensada so that o contexto não infle e eu não precise ensinar o agente a usar outra tool.

**Acceptance scenarios** (Given / When / Then, ≥ 3 per story):

1. Given o hook registrado em `settings.json`, When o agente chama Bash com `npm test` e a saída tem 36 KB, Then o comando é reescrito para o CLI do pacote e o agente recebe o bloco condensado (erros verbatim, `ERROR SIGNATURES`, `RAW TAIL`, exit code).
2. Given o hook registrado, When o comando produz menos de 2000 caracteres, Then a saída chega byte a byte igual e o exit code é preservado.
3. Given o hook registrado, When o comando já começa pelo CLI do pacote, Then o hook não reescreve (idempotente).
4. Given o Ollama fora do ar, When o comando produz 36 KB, Then o agente recebe trecho truncado + assinaturas de erro + aviso, e o exit code original.

### Story 2 — Resumo de diff para revisão (P2)

As a dev abrindo um PR, I want um resumo por arquivo do diff so that o revisor (humano ou agente) leia o sumário antes do diff completo.

**Acceptance scenarios:**

1. Given o preset ativo, When chamo `smart_git_diff` com `range: "main...HEAD"`, Then recebo o `git diff --stat` verbatim seguido de um bullet por arquivo gerado pelo modelo local.
2. Given um diff maior que o limite de entrada, When chamo a tool, Then os arquivos são resumidos um a um até o limite e os restantes são listados só pelo `--stat`, com aviso.
3. Given o Ollama fora do ar, When chamo a tool, Then recebo o `--stat` e a lista de arquivos sem resumo, com aviso.

### Story 3 — Métrica de tokens por sessão (P2)

As a tech lead, I want ver quantos tokens e quantos caracteres de resultado de tool cada sessão consumiu so that eu decida com evidência se o compressor vale para o time.

**Acceptance scenarios:**

1. Given transcripts do Claude Code para o workspace em `~/.claude/projects/<slug>/*.jsonl`, When rodo `aiadev metrics --tokens`, Then vejo uma tabela por sessão com tokens de entrada, criação de cache, leitura de cache, saída, número de chamadas de tool e caracteres devolvidos, mais o top de tools por caracteres.
2. Given um diretório de transcripts vazio ou inexistente, When rodo o comando, Then sai com código 2 e uma mensagem dizendo onde procurou.
3. Given `--format json`, When rodo o comando, Then a saída é JSON estável com os mesmos campos.

<!-- section: Clarifications -->
## Clarifications

- **cl-1 (Artigo III):** o compressor **não** entra em `src/aiadev`. Vive em `packages/smart-mcp-proxy` (npm, opt-in). O framework só declara (preset) e mede (métrica). Resolvido na própria spec.
- **cl-2 (hook vs instalador):** o hook é entregue como binário do pacote + snippet no preset; o instalador não toca `settings.json` nesta feature. Resolvido: ver Non-goals.

<!-- section: Data touched -->
## Data touched

- Nenhum dado de produto. Leitura de transcripts locais em `~/.claude/projects/` (métrica), somente leitura, nunca enviados a lugar nenhum.
- Cache em memória da saída bruta por chamada no servidor MCP (últimas 20), descartado ao encerrar.

<!-- section: Out-of-band effects -->
## Out-of-band effects

- Requisições HTTP ao Ollama em `localhost:11434` (configurável). Nada sai da máquina por padrão; se o consumidor apontar `OLLAMA_URL` para um host remoto, é decisão dele (Artigo VI).

<!-- section: Open risks -->
## Open risks

- O hook reescreve todo comando Bash; um bug no CLI derruba todo Bash do agente. Mitigar no plano com modo de falha "passa o comando original".
- Comandos interativos ou de longa duração (servidores, `watch`) podem se comportar diferente sob o CLI.
- A contabilidade de tokens nos transcripts varia entre versões do Claude Code; o parser precisa ser tolerante a campos ausentes.

<!-- section: Traceability -->
## Traceability

- Originating issue: benchmark em `packages/smart-mcp-proxy/BENCHMARK.md`; fast-follow de 0020 (cl-4) e 0021 (T005)
- Related specs: `0009`, `0015`, `0020`, `0021`
- Constitution articles invoked: I, II, III, IV, VI
