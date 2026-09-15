# Tasks: Smart MCP Proxy — compressor local de saída de terminal

> Produced by the `tasks` skill from an approved `plan.md`. Consumed by `implement`.

**Branch:** `feat/smart-mcp-proxy`
**Plan:** [plan.md](./plan.md)
**Generated:** 2026-09-15
**Language:** pt-BR <!-- mirrors spec.md; write task descriptions in this language. -->

---

## How to read this file

- Tasks are ordered. `implement` runs them top-to-bottom.
- One task = one commit. The commit message starts with the task id.
- Each task links back to the spec acceptance scenarios it exercises.
- `Status` is one of: `pending`, `in_progress`, `blocked`, `done`. Owned by the `implement` skill — it flips `pending` → `done` inside each task's commit. Do not edit by hand; manual edits are overwritten on the next `implement` run.

## Task list

### T001 — Extrair `core.ts` do servidor MCP

- **Status:** done
- **Depends on:** —
- **Files:**
  - create: `packages/smart-mcp-proxy/src/core.ts`
  - modify: `packages/smart-mcp-proxy/src/index.ts`
  - test: `packages/smart-mcp-proxy/test/core.test.mjs`
- **Spec scenarios:** Story 1 scenario 2, Story 1 scenario 4
- **Acceptance:**
  - [ ] Testes `node --test` de `errorSignatures`, `headTail`, `normalizeOutput`, `cleanSummary` e `condense` (com Ollama simulado offline) escritos e observados falhando por falta do módulo.
  - [ ] `core.ts` exporta essas funções e `runCommand`; `index.ts` só monta o servidor.
  - [ ] Smoke test MCP dos quatro casos continua idêntico.
  - [ ] Commit message: `refactor(smart-mcp-proxy): T001 extrai core.ts`.
- **Notes:** Nenhuma mudança de comportamento nesta task.

### T002 — CLI `smart-bash`

- **Status:** done
- **Depends on:** T001
- **Files:**
  - create: `packages/smart-mcp-proxy/src/cli.ts`
  - modify: `packages/smart-mcp-proxy/package.json`
  - test: `packages/smart-mcp-proxy/test/cli.test.mjs`
- **Spec scenarios:** Story 1 scenario 2, Story 1 scenario 4
- **Acceptance:**
  - [ ] Teste: `smart-bash --b64 <base64("echo hi; exit 3")>` imprime `hi` e sai com 3.
  - [ ] Teste: saída longa com Ollama offline imprime trecho truncado + `ERROR SIGNATURES` + aviso, exit code original.
  - [ ] Primeira linha da saída condensada mostra o comando original.
  - [ ] Commit message: `feat(smart-mcp-proxy): T002 CLI smart-bash`.
- **Notes:** Aceita também `-c "<cmd>"` para uso manual.

### T003 — Hook `smart-bash-hook` (PreToolUse)

- **Status:** done
- **Depends on:** T002
- **Files:**
  - create: `packages/smart-mcp-proxy/src/hook.ts`
  - modify: `packages/smart-mcp-proxy/package.json`
  - test: `packages/smart-mcp-proxy/test/hook.test.mjs`
- **Spec scenarios:** Story 1 scenario 1, Story 1 scenario 3
- **Acceptance:**
  - [ ] Teste: stdin com `tool_name: "Bash"` e `command: "npm test"` produz JSON `hookSpecificOutput.updatedInput.command` começando por `smart-bash --b64`.
  - [ ] Teste: comando que já começa por `smart-bash` não é reescrito (stdout vazio, exit 0).
  - [ ] Teste: stdin inválido resulta em exit 0 sem stdout (modo de falha).
  - [ ] Commit message: `feat(smart-mcp-proxy): T003 hook PreToolUse`.
- **Notes:** `tool_name` diferente de `Bash` também passa sem reescrever.

### T004 — Preset `token-economy`

- **Status:** pending
- **Depends on:** T003
- **Files:**
  - create: `presets/token-economy/preset.yaml`
  - create: `presets/token-economy/mcps.yaml`
  - create: `presets/token-economy/hooks/claude-code-settings.snippet.json`
  - create: `presets/token-economy/README.md`
  - test: `tests/test_token_economy_preset.py`
- **Spec scenarios:** Story 1 scenario 1
- **Acceptance:**
  - [ ] Teste: `mcps.yaml` do preset parseia e declara o servidor `smart-bash`.
  - [ ] Teste: o snippet é JSON válido com `hooks.PreToolUse[0].matcher == "Bash"`.
  - [ ] README diz como instalar o pacote, colar o snippet e desligar.
  - [ ] Commit message: `feat(presets): T004 preset token-economy`.
- **Notes:** Espelha `presets/knowledge-graph/`.

### T005 — Tool `smart_git_diff`

- **Status:** pending
- **Depends on:** T001
- **Files:**
  - modify: `packages/smart-mcp-proxy/src/index.ts`
  - modify: `packages/smart-mcp-proxy/src/core.ts`
  - test: `packages/smart-mcp-proxy/test/diff.test.mjs`
- **Spec scenarios:** Story 2 scenario 1, scenario 2, scenario 3
- **Acceptance:**
  - [ ] Teste: `splitDiffByFile` separa um diff em blocos por arquivo com nomes corretos.
  - [ ] Teste: orçamento de entrada limita quantos arquivos vão ao modelo; o resto é listado com aviso.
  - [ ] Smoke: com Ollama online, a tool devolve `--stat` verbatim + um bullet por arquivo.
  - [ ] Commit message: `feat(smart-mcp-proxy): T005 tool smart_git_diff`.
- **Notes:** `git diff --stat` sempre verbatim.

### T006 — Passo opcional em `requesting-code-review`

- **Status:** pending
- **Depends on:** T005
- **Files:**
  - modify: `skills/requesting-code-review/SKILL.md`
  - test: `tests/test_token_economy_preset.py`
- **Spec scenarios:** Story 2 scenario 1
- **Acceptance:**
  - [ ] Teste: a skill menciona `smart_git_diff` como passo opcional com cláusula de degradação.
  - [ ] `python3 scripts/validate_skills.py` passa.
  - [ ] Commit message: `docs(skills): T006 smart_git_diff opcional no review`.

### T007 — `token_metrics.py` + `aiadev metrics --tokens`

- **Status:** pending
- **Depends on:** —
- **Files:**
  - create: `src/aiadev/token_metrics.py`
  - modify: `src/aiadev/commands/metrics.py`
  - create: `tests/fixtures/token_metrics/sample.jsonl`
  - test: `tests/test_token_metrics.py`
- **Spec scenarios:** Story 3 scenario 1, scenario 2, scenario 3
- **Acceptance:**
  - [ ] Teste: fixture com 2 sessões produz totais corretos de tokens e chars por tool.
  - [ ] Teste: diretório inexistente → exit 2 com o caminho na mensagem.
  - [ ] Teste: `--format json` estável.
  - [ ] Commit message: `feat(metrics): T007 relatório de tokens por sessão`.
- **Notes:** Slug do diretório = cwd absoluto com `/` trocado por `-`; `--transcripts-dir` sobrescreve (usado nos testes).

### T008 — Docs e README

- **Status:** pending
- **Depends on:** T004, T007
- **Files:**
  - modify: `docs/token-economy.md`
  - modify: `packages/smart-mcp-proxy/README.md`
  - test: `tests/test_provider_followups.py`
- **Spec scenarios:** Story 1 scenario 1
- **Acceptance:**
  - [ ] `docs/token-economy.md` cita o pacote na tabela de compressores e o hook real, mantendo o Non-goal (core não implementa).
  - [ ] Testes existentes de docs continuam passando.
  - [ ] Commit message: `docs: T008 token-economy cita smart-mcp-proxy`.

### T009 — Benchmark com a variante hook

- **Status:** pending
- **Depends on:** T003
- **Files:**
  - modify: `packages/smart-mcp-proxy/BENCHMARK.md`
- **Spec scenarios:** Story 1 scenario 1, scenario 2
- **Acceptance:**
  - [ ] Variante `bash+hook` (Bash nativo + settings com o hook) nos 6 casos, mesma metodologia.
  - [ ] Tabela agregada com três variantes e conclusões atualizadas.
  - [ ] Commit message: `docs(smart-mcp-proxy): T009 benchmark com hook`.

## Parallelization hints

- Parallel group A: T005, T007 (não compartilham arquivos com T002–T004)
- Serial: T001 → T002 → T003 → T004; T008 e T009 por último

## Post-task checklist

After every task:

- [ ] Commit message references the task id.
- [ ] Status in this file updated.

After all tasks:

- [ ] Full test suite passes (`.venv/bin/python -m pytest tests` e `npm test` no pacote).
- [ ] `analyze` skill runs and reports no drift vs spec / plan.
- [ ] Hand off to `requesting-code-review` to open the PR.
