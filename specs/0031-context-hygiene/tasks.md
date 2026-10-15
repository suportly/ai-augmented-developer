# Tasks: Higiene de contexto — ver onde o contexto se acumula e avisar a hora de cortar a sessão

**Branch:** `feature/0031-context-hygiene`
**Plan:** [plan.md](./plan.md)
**Generated:** 2026-10-15
**Language:** pt-BR <!-- mirrors spec.md; write task descriptions in this language. -->

---

## How to read this file

- Tasks run top-to-bottom, one commit each, message starting with the task id.
- `Status` (`pending`, `in_progress`, `blocked`, `done`) is owned by `implement`.
- Tasks de infraestrutura citam `Success criterion #N` (N = ordem do bullet em Success criteria da spec).
- As fases do plano são pontos de corte mescláveis: 1 e 2 cobrem as stories P1; 3 e 4 são P2.
- **Orçamento de instruções:** nenhuma task sobe teto de `docs/instruction-budget.json`; T011 e T013 podem pedir compensação e, se ela não fechar, a task para e relata o saldo.

## Task list

**Fase 1 — Distribuição de contexto em `metrics --tokens` (Story 1)**

### T001 — Contexto, modelo e faixa de cada request

- **Status:** done
- **Depends on:** —
- **Files:**
  - modify: `src/aiadev/token_metrics.py`
  - test: `tests/test_token_metrics.py`
- **Spec scenarios:** Story 1 scenario 1, scenario 4
- **Acceptance:**
  - [ ] Teste vermelho: `_MessageUsage` expõe `context` (`input + cache_creation + cache_read`, sem a saída) e `model`; `merged()` carrega o modelo (vale o último não vazio); a função de faixa classifica 30k, 50.000, 120k, 150.000, 200.000 e 250k nas faixas `< 50k`, `50k–150k`, `50k–150k`, `150k–200k`, `150k–200k` e `> 200k`, com os limites da spec.
  - [ ] Modelo ausente vira `unknown`; `<synthetic>` fica fora da participação por modelo.
  - [ ] Os valores pinados em `tests/test_token_metrics.py` seguem verdes.
  - [ ] Commit message: `feat(metrics): T001 contexto, modelo e faixa por request`.

### T002 — Faixas e modelos acumulados por sessão e por subagente

- **Status:** done
- **Depends on:** T001
- **Files:**
  - modify: `src/aiadev/token_metrics.py`
  - modify: `tests/fixtures/token_metrics/` (fixture do mesmo `message.id` nos arquivos principal e de subagente)
  - test: `tests/test_token_metrics.py`
- **Spec scenarios:** Story 1 scenario 1, scenario 2, scenario 4
- **Acceptance:**
  - [ ] Teste vermelho: `_add_message` acumula requests e tokens de contexto por faixa e tokens por modelo na sessão que reivindicou a mensagem; `SubagentTokens` ganha os mesmos campos e `_attach_subagents` os copia.
  - [ ] A mensagem presente no arquivo principal e num de subagente conta uma vez, como principal; a soma das faixas (requests e tokens de contexto) de principal mais subagentes é igual ao total.
  - [ ] Request sem `message.id` e com uso parcial de streaming cai na faixa do máximo por campo, sem erro.
  - [ ] Commit message: `feat(metrics): T002 faixas e modelos por sessão e subagente`.

### T003 — Participações no `TokenReport`

- **Status:** done
- **Depends on:** T002
- **Files:**
  - modify: `src/aiadev/token_metrics.py`
  - test: `tests/test_token_metrics.py`
- **Spec scenarios:** Story 1 scenario 2
- **Acceptance:**
  - [ ] Teste vermelho: com 5 sessões de tamanhos diferentes, subagentes e dois modelos, o relatório calcula a fatia dos subagentes em requests e em tokens, a participação de cada modelo e as 3 sessões de maior custo (custo equivalente da sessão mais os seus subagentes, sobre `total_equivalent_cost`).
  - [ ] Caso com uma sessão de subagentes pesados fica fora do top-3 se só o custo principal for usado (o teste falha com o cálculo errado).
  - [ ] Commit message: `feat(metrics): T003 participações por sessão, modelo e subagente`.

### T004 — Texto e JSON do relatório, e docs/metrics.md

- **Status:** done
- **Depends on:** T003
- **Files:**
  - modify: `src/aiadev/token_metrics.py`
  - modify: `docs/metrics.md`
  - test: `tests/test_token_metrics.py`
- **Spec scenarios:** Story 1 scenario 1, scenario 2, scenario 3
- **Acceptance:**
  - [ ] Teste vermelho: o texto de `aiadev metrics --tokens` mostra as faixas (todas as requests e só a thread principal), o top-3, os modelos e a fatia dos subagentes; `--format json` traz os mesmos campos como chaves novas e nenhuma chave existente muda de nome ou de valor (comparação com o JSON anterior das fixtures).
  - [ ] `docs/metrics.md` descreve as seções novas, os limites das faixas e a definição de contexto.
  - [ ] Commit message: `feat(metrics): T004 relatório de contexto em texto e JSON`.

### T005 — Totais conferem com a dedupe independente

- **Status:** pending
- **Depends on:** T004
- **Files:**
  - test: `tests/test_token_metrics_manual_rule.py`
- **Spec scenarios:** Success criterion #1
- **Acceptance:**
  - [ ] Teste vermelho (gerador com semente, como o existente): a soma dos tokens de contexto das faixas confere, dentro de 1%, com a dedupe independente por `message.id` (máximo por campo), e a soma das requests das faixas é igual ao total de requests; vale para principal mais subagentes.
  - [ ] O teste de privacidade existente (nenhum corpo de `tool_result` é lido) segue verde.
  - [ ] Commit message: `test(metrics): T005 faixas conferem com a dedupe independente`.

**Fase 2 — Aviso de contexto em `next` e `tasks done` (Story 2)**

### T006 — Ler o fim do transcript

- **Status:** done
- **Depends on:** T001
- **Files:**
  - create: `src/aiadev/session_context.py`
  - test: `tests/test_session_context.py`
- **Spec scenarios:** Story 2 scenario 4, scenario 5
- **Acceptance:**
  - [ ] Teste vermelho: a função de leitura devolve o contexto da última request com `usage`, lendo uma janela do fim do arquivo (256 KiB, depois 1 MiB e 4 MiB enquanto não achar `usage`); a primeira linha só é descartada quando o deslocamento é maior que zero; o máximo por campo entre linhas do mesmo `message.id` vale só dentro da janela.
  - [ ] Teste com uma linha de `tool_result` de mais de 256 KiB no fim, arquivo menor que a janela, arquivo sem nenhuma linha com `usage` (devolve nada) e arquivo truncado; nenhum erro em linha malformada.
  - [ ] Teste de privacidade: o módulo não lê o texto das mensagens nem o corpo de `tool_result` além de localizar as linhas de uso.
  - [ ] Commit message: `feat(context): T006 contexto da última request pelo fim do transcript`.

### T007 — Sessões ativas, limiar e formato das linhas

- **Status:** done
- **Depends on:** T006
- **Files:**
  - modify: `src/aiadev/session_context.py`
  - test: `tests/test_session_context.py`
- **Spec scenarios:** Story 2 scenario 1, scenario 3, scenario 6
- **Acceptance:**
  - [ ] Teste vermelho: `active_contexts` devolve o transcript mais recente e, além dele, os modificados nos últimos 10 minutos contados de `now`; dois transcripts dentro da janela geram duas entradas, um fora da janela não.
  - [ ] `format_lines` produz `context: <N>k tokens (session <id de 8 caracteres>, <n>s|<n> min|<n> h ago)` e, acima do limiar, `checkpoint:` com o estado em `tasks.md` e no git e a retomada por `aiadev next`; abaixo do limiar, só `context:`.
  - [ ] O limiar vem de `AIADEV_CONTEXT_WARN` (tokens); valor inválido ou ausente usa 150.000; o contexto igual ao limiar não avisa.
  - [ ] Commit message: `feat(context): T007 sessões ativas, limiar e formato das linhas`.

### T008 — Linhas de contexto em `aiadev next`

- **Status:** done
- **Depends on:** T007
- **Files:**
  - modify: `src/aiadev/commands/next.py`
  - test: `tests/test_next_command.py`
- **Spec scenarios:** Story 2 scenario 1, scenario 3, scenario 4, scenario 5, scenario 6
- **Acceptance:**
  - [ ] Teste vermelho (`HOME` apontado para um diretório temporário com um transcript de 412k modificado há 3 minutos): a saída inclui `context:` e `checkpoint:`; abaixo do limiar, só `context:`; sem transcript, a saída e o código de saída são os de hoje.
  - [ ] Dois transcripts ativos geram uma linha `context:` por sessão e `checkpoint:` só para as que passam do limiar.
  - [ ] Transcript de 50 MB gerado no teste (nunca commitado): `aiadev next` termina em até 200 ms; o orçamento de 200 ms já pinado nos testes de `pipeline_state` segue verde.
  - [ ] Falha de leitura vira nenhuma linha, nunca erro; linhas com `escape()` do Rich.
  - [ ] Commit message: `feat(next): T008 contexto da sessão e aviso de checkpoint`.

### T009 — Linhas de contexto em `aiadev tasks done`

- **Status:** done
- **Depends on:** T007
- **Files:**
  - modify: `src/aiadev/commands/tasks.py`
  - test: `tests/test_tasks_done_command.py`
- **Spec scenarios:** Story 2 scenario 2, scenario 3, scenario 4
- **Acceptance:**
  - [ ] Antes de editar, conferir se `tests/test_tasks_done_command.py` fixa a saída exatamente e ajustar só o que for necessário.
  - [ ] Teste vermelho (repositório git real em tmp, `HOME` temporário com transcript de 412k): depois de `<hash> <assunto>`, o comando imprime `context:` e `checkpoint:`, sem alterar o commit nem o código de saída; abaixo do limiar, só `context:`; sem transcript, a saída é a de hoje.
  - [ ] O slug do transcript vem da raiz do repositório que o comando já resolve.
  - [ ] Commit message: `feat(tasks): T009 contexto da sessão ao fechar a task`.

**Fase 3 — Papel `doc-review` (Story 3)**

### T010 — Papel doc-review e aviso de não classificado

- **Status:** done
- **Depends on:** T004
- **Files:**
  - modify: `src/aiadev/token_metrics.py`
  - test: `tests/test_token_metrics.py`
- **Spec scenarios:** Story 3 scenario 1, scenario 2, scenario 3
- **Acceptance:**
  - [ ] Teste vermelho: `description` iniciada por `doc-review:` (sem diferenciar maiúsculas, com dois-pontos) é classificada no papel `doc-review`; `implement:` e `review:` seguem como hoje; sem prefixo reconhecido é `unclassified`.
  - [ ] A tabela por papel e o JSON incluem o papel novo; quando os não classificados passam de 30% do custo equivalente de subagentes, o relatório imprime uma linha de aviso com a participação e o critério; em 30% ou menos, nenhuma linha.
  - [ ] O docstring de `_subagent_role` é atualizado.
  - [ ] Commit message: `feat(metrics): T010 papel doc-review e aviso de não classificado`.

### T011 — Convenção doc-review em specify e plan

- **Status:** done
- **Depends on:** T010
- **Files:**
  - modify: `skills/specify/SKILL.md`
  - modify: `skills/plan/SKILL.md`
  - modify: `docs/instruction-budget.json`
  - test: `tests/test_dispatch_description_convention.py`
- **Spec scenarios:** Story 3 scenario 1; Success criterion #5
- **Acceptance:**
  - [ ] Teste vermelho: o teste que hoje afirma que `specify` e `plan` não têm prefixo (`test_document_reviewers_are_not_classified`) é substituído por um que exige a convenção `doc-review:` nas duas skills e que `_subagent_role` a reconhece; o docstring do módulo é atualizado.
  - [ ] Cada frase nova é compensada no mesmo arquivo; `scripts/instruction_budget.py --check` passa sem subir nenhum teto e o percurso não cresce; se não fechar, a task para e relata o saldo.
  - [ ] As frases do reconhecimento, o teto de 3 marcadores e a linha de stack seguem presentes (testes existentes verdes).
  - [ ] Commit message: `docs(skills): T011 convenção doc-review em specify e plan`.

**Fase 4 — Agent `implementer` com modelo definido (Story 4)**

### T012 — Agent implementer e descrições dos revisores

- **Status:** done
- **Depends on:** —
- **Files:**
  - create: `agents/implementer.md`
  - modify: `agents/code-reviewer.md`
  - modify: `agents/plan-document-reviewer.md`
  - modify: `agents/spec-document-reviewer.md`
  - test: `tests/test_implementer_agent.py`
- **Spec scenarios:** Story 4 scenario 2
- **Acceptance:**
  - [ ] Teste vermelho: `agents/implementer.md` tem frontmatter com `name: implementer`, `description` de uma linha e `model: sonnet`, **sem `tools:`**, e carrega o fluxo test-first e a lista de status que o implementer devolve (`DONE`, `DONE_WITH_CONCERNS`, `NEEDS_CONTEXT`, `BLOCKED`).
  - [ ] Instalação real nas cinco plataformas (`install` e `sync` em diretório temporário): o arquivo chega a `<plataforma>/agents/implementer.md`, os agents existentes ficam intactos e o `sync` não remove nem altera nenhum deles.
  - [ ] As descrições dos três revisores são encurtadas, sem perder a regra de saída nem "Why no issues"; `preset:*:agents` e `preset:*:total` do orçamento não sobem (a `description` do novo agent é compensada ali).
  - [ ] Commit message: `feat(agents): T012 agent implementer com model: sonnet`.

### T013 — implement despacha o agent e o percurso não cresce

- **Status:** done
- **Depends on:** T012
- **Files:**
  - modify: `skills/implement/SKILL.md`
  - modify: `docs/pipeline-path.yaml`
  - modify: `docs/instruction-budget.json`
  - test: `tests/test_implement_skill_drift.py`
  - test: `tests/test_dispatch_description_convention.py`
- **Spec scenarios:** Story 4 scenario 1, scenario 3, scenario 4; Success criterion #4
- **Acceptance:**
  - [ ] Teste vermelho: o passo 4 de `implement` manda despachar o agent `implementer` com `description` `implement: <TID> <título>`; o prompt da skill leva só título, recorte da spec, entrada do plano e lista de arquivos; o fluxo test-first e a lista de status estão no agent; os testes de prosa leem skill mais agent e seguem asserindo as regras sem afrouxar.
  - [ ] Compare regra a regra com o prompt anterior e liste no relatório o destino de cada trecho removido da skill; "Status handling" fica na skill.
  - [ ] `docs/pipeline-path.yaml` lista `agents/implementer.md` no estágio `implement`; `path:total` não cresce, `skill:implement` diminui e nenhum teto sobe; se a conta não fechar, a task para e relata o saldo.
  - [ ] Um subagente despachado com `description` `implement:` continua classificado no papel `implement` pelo relatório de `--tokens`.
  - [ ] Commit message: `refactor(implement): T013 despacho pelo agent implementer`.

**Fase 5 — Documentação e medição**

### T014 — Documentação e CHANGELOG

- **Status:** done
- **Depends on:** T009, T011, T013
- **Files:**
  - modify: `docs/token-economy.md`
  - modify: `CHANGELOG.md`
  - test: `tests/test_changelog_entry.py`
- **Spec scenarios:** Success criterion #2
- **Acceptance:**
  - [ ] Teste vermelho: `CHANGELOG.md [Unreleased]` registra, em Added e Changed, o relatório de contexto, as linhas `context:`/`checkpoint:`, `AIADEV_CONTEXT_WARN`, o papel `doc-review` e o agent `implementer`, citando o Spec ID 0031.
  - [ ] `docs/token-economy.md` ganha uma seção de higiene de contexto: o que as linhas significam, quando cortar a sessão, e que o estado está em `tasks.md` e no git.
  - [ ] Markdown passa no lint do repositório.
  - [ ] Commit message: `docs(0031): T014 higiene de contexto no CHANGELOG e no token-economy`.

### T015 — Medição nos transcripts reais

- **Status:** pending
- **Depends on:** T008, T009, T014
- **Files:**
  - create: `docs/context-hygiene-baseline.md`
  - test: `tests/test_token_metrics_manual_rule.py`
- **Spec scenarios:** Success criterion #1; Success criterion #3; Success criterion #6
- **Acceptance:**
  - [ ] Rodar `aiadev metrics --tokens` nos transcripts reais deste repositório e registrar em `docs/context-hygiene-baseline.md` o comando, a data e os números (faixas, top-3, modelos, fatia dos subagentes), conferidos contra um script independente de dedupe.
  - [ ] Registrar o tempo de `aiadev next` com o transcript real de maior tamanho e confirmar que as linhas `context:` mostram o id e a idade da sessão correta.
  - [ ] Confirmar que nada é gravado: `git status` limpo e nenhum arquivo novo ou alterado em `~/.claude/projects/` depois dos comandos (comparar a listagem com `mtime` antes e depois); o relatório só lê e não abre conexão.
  - [ ] Commit message: `docs(0031): T015 baseline de contexto nos transcripts reais`.

## Parallelization hints

- Parallel group A (fases 1 e 4): T001–T005 (`token_metrics`) e T012 (agent) tocam arquivos disjuntos.
- Parallel group B: T006–T007 (`session_context`) depois de T001; T008 e T009 depois de T007, arquivos disjuntos.
- Serial: tudo que toca `src/aiadev/token_metrics.py` (T001–T004, T010), `skills/implement/SKILL.md` (T013) e `docs/instruction-budget.json` (T011–T013).

## Post-task checklist

After every task: commit references the task id; status updated (`aiadev tasks done`).

After all tasks:

- [ ] Full test suite passes (`PYTHONPATH=src python3 -m pytest -q --ignore=tests/test_mcp_server.py`).
- [ ] `python3 scripts/instruction_budget.py --check` passa, sem nenhum teto subido.
- [ ] `analyze` skill runs and reports no drift vs spec / plan.
- [ ] Hand off to `requesting-code-review` to open the PR.
