# Implementation plan: Smart MCP Proxy — compressor local de saída de terminal

> Produced by the `plan` skill from an approved `spec.md`. This file describes **how** the spec will be realized. Do not rewrite `spec.md` into `plan.md`.

**Branch:** `feat/smart-mcp-proxy`
**Date:** 2026-09-15
**Spec:** [spec.md](./spec.md)
**Plan version:** 1
**Language:** pt-BR <!-- mirrors spec.md; write plan prose in this language. -->

---

## Summary

Fatoramos o pacote `packages/smart-mcp-proxy` em um núcleo (`core.ts`: execução, condensação, assinaturas de erro, cache) e três entradas: o servidor MCP já existente (`index.ts`, que ganha a tool `smart_git_diff`), um CLI `smart-bash` que executa um comando e imprime a saída condensada, e um hook `smart-bash-hook` que implementa o contrato `PreToolUse` do Claude Code reescrevendo o `command` da tool Bash para passar pelo CLI. O framework ganha o preset opt-in `presets/token-economy/` (mcps.yaml + snippet de settings + README), a doc `docs/token-economy.md` passa a citar o pacote, e `aiadev metrics --tokens` lê os transcripts locais do Claude Code para reportar tokens e caracteres de tool por sessão. Nada entra em `src/aiadev` além da métrica (somente leitura). ~9 tasks em 4 fases.

## Technical context

| Field | Value |
|---|---|
| Active preset | Nenhum — repositório do próprio framework aiadev |
| Language / runtime | TypeScript/Node ≥ 18 (pacote); Python 3.10+ (métrica); Markdown (preset/docs) |
| Primary dependencies | Pacote: `@modelcontextprotocol/sdk`, `axios`, `zod` (já presentes). Core Python: nenhuma nova |
| Storage | Filesystem; cache em memória no servidor MCP |
| Testing framework | `pytest` (métrica); smoke test via cliente MCP stdio + `node --test` (pacote); benchmark headless com `claude -p` |
| Target platform(s) | Claude Code (hook e MCP); as demais plataformas recebem só o MCP via `mcps.yaml` |
| Performance budget | Condensação ≤ 5 s por chamada longa no `qwen2.5-coder:3b`; comandos curtos sem custo extra |
| Security considerations | Hook reescreve comandos: usar base64 para o comando original, nunca interpolar em shell; modo de falha = passa o comando original |

## Constitution check

| Article | Applies? | Status | Evidence |
|---|---|---|---|
| I. Spec-first | Yes | PASS | `spec.md` aprovado em 2026-09-15, zero marcadores |
| II. Test-first | Yes | PASS | Métrica com `pytest` sobre fixture de transcript; pacote com testes `node --test` do núcleo (assinaturas, headTail, hook) antes das entradas |
| III. Simplicity | Yes | PASS | Compressor fora do core (`packages/`); preset só declara; nenhuma abstração nova em `src/aiadev` além de um módulo de leitura |
| IV. Evidence over claims | Yes | PASS | `BENCHMARK.md` atualizado com a variante hook; PR enumera `pytest`, `npm run build`, smoke e benchmark |
| V. Provider pattern | Yes | PASS | Backend de resumo é uma URL (`OLLAMA_URL`); o servidor não sabe qual modelo há atrás |
| VI. Privacy by design | Yes | PASS | Tudo local por padrão; transcripts lidos, nunca enviados; `--tokens` não imprime conteúdo de mensagens |
| VII. Attribution | Yes | PASS | `CREDITS.md` já cita rtk/headroom (0020); o padrão do hook segue o de `rtk init`, creditar na doc |
| Preset-specific articles | N/A | N/A | Feature de nível framework |

## Architecture decisions

- **Decisão:** um núcleo (`core.ts`) e três entradas finas (MCP, CLI, hook) no mesmo pacote.
  **Rationale:** o benchmark mostrou que a lógica que importa (assinaturas, cauda, guarda) é a mesma em todos os caminhos; três cópias divergiriam.
  **Trade-offs:** o pacote ganha dois binários a mais; aceitável.

- **Decisão:** o hook reescreve `command` para `smart-bash --b64 <base64>` e devolve `updatedInput` só com esse campo.
  **Rationale:** base64 elimina qualquer problema de quoting do comando original; `updatedInput` faz merge, então `description`/`timeout` ficam intactos.
  **Trade-offs:** o comando visível no log do agente fica opaco; o CLI imprime uma linha `[smart-bash] <comando original>` no início da saída para compensar.

- **Decisão:** modo de falha do hook é "não reescrever". Qualquer exceção ao ler stdin ou montar a saída resulta em exit 0 sem JSON.
  **Rationale:** risco aberto do spec: um bug no hook não pode derrubar todo Bash do agente.
  **Trade-offs:** falhas do hook ficam silenciosas; o CLI loga em stderr.

- **Decisão:** `smart_git_diff` faz `git diff --stat` verbatim (determinístico) e resume arquivo a arquivo com o modelo, até um orçamento de entrada; o resto fica só no stat.
  **Rationale:** mesma lição do benchmark: contagens e nomes vêm de código, o modelo só narra.
  **Trade-offs:** diffs enormes não são totalmente resumidos; aviso explícito.

- **Decisão:** `--tokens` vive em um módulo novo `src/aiadev/token_metrics.py`, chamado por uma flag do comando `metrics` existente, e sai antes do fluxo atual.
  **Rationale:** não mexer no relatório de specs (0015); o slug do diretório de transcripts é derivado do cwd como o Claude Code faz (`/` → `-`).
  **Trade-offs:** dois relatórios sob um comando; aceitável enquanto a métrica é nova.

- **Decisão:** o instalador não escreve `settings.json` (Non-goal). O preset entrega `hooks/claude-code-settings.snippet.json` e o README diz onde colar.
  **Rationale:** merge parcial de um arquivo editado pelo usuário exige um papel novo de artefato e política de conflito; escopo próprio.
  **Trade-offs:** um passo manual para o consumidor.

## Project structure changes

```text
packages/smart-mcp-proxy/src/core.ts                 (new)      # runCommand, condense, errorSignatures, headTail, cache
packages/smart-mcp-proxy/src/index.ts                (modified) # só o servidor MCP; ganha smart_git_diff
packages/smart-mcp-proxy/src/cli.ts                  (new)      # bin smart-bash: executa e imprime condensado
packages/smart-mcp-proxy/src/hook.ts                 (new)      # bin smart-bash-hook: contrato PreToolUse
packages/smart-mcp-proxy/test/core.test.mjs          (new)      # node --test sobre dist/core.js
packages/smart-mcp-proxy/test/hook.test.mjs          (new)      # node --test sobre dist/hook.js
packages/smart-mcp-proxy/package.json                (modified) # bins, script test
packages/smart-mcp-proxy/README.md                   (modified) # hook, CLI, smart_git_diff
packages/smart-mcp-proxy/BENCHMARK.md                (modified) # variante bash+hook
presets/token-economy/preset.yaml                    (new)
presets/token-economy/mcps.yaml                      (new)      # declara smart-bash
presets/token-economy/hooks/claude-code-settings.snippet.json (new)
presets/token-economy/README.md                      (new)
docs/token-economy.md                                (modified) # cita o pacote e o hook real
skills/requesting-code-review/SKILL.md               (modified) # passo opcional com smart_git_diff
src/aiadev/token_metrics.py                          (new)
src/aiadev/commands/metrics.py                       (modified) # flag --tokens
tests/test_token_metrics.py                          (new)
tests/fixtures/token_metrics/sample.jsonl            (new)
```

## Phase breakdown

### Phase 1 — Núcleo e hook (Story 1)

- Extrair `core.ts` do `index.ts` sem mudar comportamento (smoke test igual).
- `cli.ts` (`smart-bash`) e `hook.ts` (`smart-bash-hook`) com testes `node --test`.
- Preset `token-economy` com `mcps.yaml`, snippet de settings e README.

### Phase 2 — Diff (Story 2)

- Tool `smart_git_diff` no servidor MCP, sobre o núcleo.
- Passo opcional em `requesting-code-review`.

### Phase 3 — Métrica (Story 3)

- `token_metrics.py` + fixture + testes; flag `--tokens` em `metrics`.

### Phase 4 — Evidência

- Benchmark: variante `bash+hook` nos 6 casos; `BENCHMARK.md` e `docs/token-economy.md` atualizados.

## Risks and mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Hook com bug derruba todo Bash do agente | Med | High | Modo de falha "não reescrever"; testes do contrato; CLI preserva exit code |
| Comandos interativos/longos sob o CLI | Med | Med | CLI não usa TTY; `SMART_MCP_EXEC_TIMEOUT_MS`; documentar exclusão por padrão de `run_in_background` |
| Formato dos transcripts muda entre versões | Med | Low | Parser tolerante: campos ausentes contam zero; testes com fixture real |
| Modelo local resume mal diffs grandes | Med | Low | `--stat` sempre verbatim; orçamento por arquivo; aviso |

## Complexity tracking

| Article waived | Reason | Alternatives considered | Reviewer |
|---|---|---|---|
| | | | |

## Hand-off to `tasks`

The next skill is `tasks`. It consumes this plan and produces `tasks.md`.
Pre-conditions before hand-off:

- [x] Constitution Check is fully populated, no blank rows.
- [x] Complexity tracking is filled or empty-and-justified.
- [x] Project structure delta is accurate.
