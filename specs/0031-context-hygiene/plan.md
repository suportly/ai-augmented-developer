# Implementation plan: Higiene de contexto — ver onde o contexto se acumula e avisar a hora de cortar a sessão

> Produced by the `plan` skill from an approved `spec.md`. This file describes **how** the spec will be realized. Do not rewrite `spec.md` into `plan.md`.

**Branch:** `feature/0031-context-hygiene`
**Date:** 2026-10-15
**Spec:** [spec.md](./spec.md)
**Plan version:** 1
**Language:** pt-BR <!-- mirrors spec.md; write plan prose in this language. -->

---

## Summary

Entregamos a spec em cinco fases pequenas, cada uma mesclável sozinha. A fase 1 (Story 1) faz `token_metrics` guardar o contexto e o modelo de cada request deduplicada e mostrar faixas, concentração por sessão, participação por modelo e fatia dos subagentes. A fase 2 (Story 2) cria um módulo pequeno que lê só o fim do transcript mais recente e liga uma linha `context:` e, acima do limiar, uma linha `checkpoint:` em `aiadev next` e `aiadev tasks done`. A fase 3 (Story 3) dá ao revisor de documento o papel `doc-review`. A fase 4 (Story 4) cria o agent `implementer` com `model: sonnet`, movendo para ele o que hoje é texto fixo do prompt do implementer, para o percurso não crescer. A fase 5 fecha com documentação e a medição nos transcripts reais. Tudo é leitura local de campos de uso e modelo; nada sai da máquina e nada novo é gravado.

## Technical context

| Field | Value |
|---|---|
| Active preset | nenhum (repositório do próprio framework) |
| Language / runtime | Python ≥ 3.11 (matriz de CI 3.11 e 3.12); Markdown para skills e agents |
| Primary dependencies | click, pyyaml, rich (já em uso); nenhuma dependência nova |
| Storage | nenhum novo; leitura de `~/.claude/projects/<slug do cwd>/*.jsonl` |
| Testing framework | pytest (`CliRunner`, fixtures em `tests/fixtures/token_metrics/`), cobertura mínima 80% sobre `src/aiadev` |
| Target platform(s) | Claude Code (formato do transcript); o agent `implementer` é instalado nas 5 plataformas, como os revisores |
| Performance budget | `aiadev next` ≤ 200 ms (orçamento da spec 0030), medido com transcript de 50 MB; leitura do transcript limitada a um trecho fixo do fim |
| Security considerations | só campos de uso, modelo, `message.id`, `agentType` e `description` são lidos; o corpo de `tool_result` e o texto das mensagens nunca (teste de privacidade existente mantido); sem rede, sem escrita |

## Constitution check

| Article | Applies? | Status | Evidence |
|---|---|---|---|
| I. Spec-first | Yes | PASS | `spec.md` revisada duas vezes pelo revisor de documento, cl-1 resolvido em `a68eb9b`, `aiadev preflight plan` com exit 0 |
| II. Test-first | Yes | PASS | cada task abre com teste vermelho; as tasks de texto (skills e agent) usam teste de comportamento, como na 0030 |
| III. Simplicity | Yes | PASS | `session_context.py` tem dois chamadores hoje (`next` e `tasks done`); o agent `implementer` foi pedido na spec (cl-1); nenhuma flag nova (só a variável `AIADEV_CONTEXT_WARN`); sem dependência nova |
| IV. Evidence over claims | Yes | PASS | total de `--tokens` conferido contra a dedupe independente de `tests/test_token_metrics_manual_rule.py`; orçamento de 200 ms medido com fixture de 50 MB; a fase 5 roda o relatório nos transcripts reais e cola o comando no PR |
| V. Provider pattern | No | N/A | sem fronteira de rede; nada novo chama serviço externo |
| VI. Privacy by design | Yes | PASS | `read_session` continua sem ler corpo de `tool_result`; o módulo novo lê só campos de uso do fim do arquivo; teste de privacidade cobre o módulo novo |
| VII. Attribution | No | N/A | a ideia vem do artigo do próprio mantenedor, já citado em R014 e na spec; nenhum código ou texto de terceiros é adaptado |
| Preset-specific articles | No | N/A | repositório do framework, sem preset ativo |

## Architecture decisions

**D1 — `token_metrics` guarda o contexto e o modelo de cada request deduplicada.**
Decision: `_MessageUsage` ganha `model` e uma propriedade `context` (`input + cache_creation + cache_read` da request já mesclada pelo máximo por campo). `_add_message` acumula, em `SessionTokens`, requests e tokens por faixa (limites da spec: `< 50.000`, `[50.000, 150.000)`, `[150.000, 200.000]`, `> 200.000`), separados entre thread principal e sidechain, e tokens por modelo (`unknown` quando ausente). `TokenReport` soma as sessões e calcula: fatia dos subagentes em requests e em tokens (a partir de `sidechain_turns` e dos totais), as 3 sessões de maior custo equivalente com a sua participação, e a participação de cada modelo. Texto e JSON ganham seções e chaves novas; nenhuma chave existente muda.
Rationale: o dedupe por `message.id` já existe e é a fonte correta (uso parcial de streaming); calcular as faixas depois dele evita contar a mesma request duas vezes. O custo equivalente por sessão já está em `SessionTokens.equivalent_cost`.
Trade-offs: `SessionTokens` cresce em campos; todos com valor padrão, então fixtures e JSON atuais seguem verdes. Requests sem `message.id` contam uma vez, na faixa do seu uso, como hoje.

**D2 — Um módulo novo, `session_context`, lê o fim do transcript mais recente.**
Decision: `src/aiadev/session_context.py` expõe `active_contexts(workspace, now, home=None)`, que lista os transcripts de `default_transcripts_dir(workspace)`, escolhe o mais recente por `mtime` e todos os demais modificados há menos de 10 minutos dele ou de `now`, e para cada um lê **um trecho fixo do fim do arquivo** (256 KiB), descarta a primeira linha possivelmente cortada, e devolve o contexto da última request (máximo por campo entre linhas com o mesmo `message.id`, como em D1) com o id de 8 caracteres e a idade. `format_lines(contexts, threshold)` produz `context: <N>k tokens (session <id>, <idade>)` e, acima do limiar, `checkpoint: ...`. O limiar vem de `AIADEV_CONTEXT_WARN` (tokens; valor inválido ou ausente usa 150.000). A idade é `<n>s`, `<n> min` ou `<n> h`, seguida de `ago`.
Rationale: o módulo tem dois chamadores (`next` e `tasks done`), então a abstração se paga (Art. III). Ler o fim é o que mantém `next` dentro de 200 ms: o transcript chega a centenas de MB. O slug do transcript é o de `token_metrics.slug_for`, o mesmo que `metrics --tokens` usa.
Trade-offs: a janela de 256 KiB pode não conter nenhuma request com `usage` se as últimas mensagens forem enormes (tool results); nesse caso a função devolve nada e as linhas somem, sem erro. A "sessão corrente" continua uma inferência por `mtime`, mitigada por id, idade e uma linha por sessão ativa, como a spec exige.

**D3 — Ligação em `next` e `tasks done`, sem efeito colateral.**
Decision: `commands/next.py` imprime as linhas depois do bloco de estado, usando `Path.cwd()`. `commands/tasks.py` imprime depois do `<hash> <assunto>`, usando a raiz do repositório que o comando já resolve (`git rev-parse --show-toplevel`). Qualquer `OSError` ou `ValueError` na leitura vira "nenhuma linha"; o código de saída e o commit não mudam. Saída com `escape()` do Rich nas linhas de `next`.
Rationale: o `tasks done` é o ponto em que o agente fecha cada task, o lugar natural para o aviso, e não custa texto de skill (o teto de `skill:implement` está sem folga).
Trade-offs: uma linha a mais por task fechada no contexto do orquestrador (poucas dezenas de tokens), contra o custo de uma sessão de 700k.

**D4 — Papel `doc-review` e aviso de não classificado.**
Decision: `ROLE_DOC_REVIEW = "doc-review"` entra em `ROLES` e em `_subagent_role` (prefixo de `description`, sem diferenciar maiúsculas, dois-pontos obrigatório, como `implement:` e `review:`). A tabela por papel e o JSON incluem o papel novo. Quando os não classificados passam de 30% do custo equivalente de subagentes, o relatório imprime uma linha de aviso com a participação e o critério. As skills `specify` e `plan` ganham uma frase cada, mandando despachar o revisor de documento com `description` `doc-review: spec <slug>` ou `doc-review: plan <slug>`; o texto é compensado nas mesmas skills (tetos de `docs/instruction-budget.json` só descem).
Rationale: nos transcripts medidos, 110 dos 178 subagentes (77% do custo de subagentes) são "não classificados"; o relatório precisa separar o que é conhecido.
Trade-offs: a spec 0030 deixou os revisores de documento não classificados de propósito; esta decisão reverte só isso. Sessões antigas continuam sem prefixo e o aviso vai disparar para elas, o que é informação correta, não erro.

**D5 — Agent `implementer` com `model: sonnet`, com o texto fixo movido do prompt da skill.**
Decision: `agents/implementer.md` (frontmatter `name`, `description`, `tools: Read, Glob, Grep, Edit, Write, Bash`, `model: sonnet`) carrega o que hoje é texto fixo do prompt do implementer em `skills/implement/SKILL.md`: o fluxo test-first e a taxonomia de status (`DONE`, `DONE_WITH_CONCERNS`, `NEEDS_CONTEXT`, `BLOCKED`). O prompt da skill passa a levar só o que muda por task (título, recorte da spec, entrada do plano, lista de arquivos), e o passo 4 manda despachar o agent `implementer` com a `description` `implement: <TID> <título>`. `docs/pipeline-path.yaml` lista `agents/implementer.md` no estágio `implement`.
Rationale: assim o texto sai da skill e entra no agent, e o percurso `specify → finish` não cresce (critério da Story 4); o orquestrador também emite menos texto em cada despacho. O modelo é definido no frontmatter, como nos três revisores, e não por frase da skill.
Trade-offs: o agent só vale para plataformas que instalam agents com `model`; nas demais o frontmatter é tratado como já é para os revisores. Os testes que fixam o prompt do implementer (`tests/test_implement_skill_drift.py`) passam a ler a skill mais o agent, como fizemos com o gate da 0030. Quem já tem um `implementer` próprio no consumidor recebe um conflito comum de arquivo no `sync`, tratado pela regra de hash existente.

## Project structure changes

```text
src/aiadev/token_metrics.py            (modified)  contexto e modelo por request, faixas, participações, doc-review
src/aiadev/session_context.py          (new)       últimos contextos das sessões ativas, leitura do fim do transcript
src/aiadev/commands/next.py            (modified)  linhas context e checkpoint
src/aiadev/commands/tasks.py           (modified)  linhas context e checkpoint depois do commit
agents/implementer.md                  (new)       agent com model: sonnet; fluxo test-first e status
skills/implement/SKILL.md              (modified)  despacha o agent; prompt só com campos da task
skills/specify/SKILL.md                (modified)  convenção doc-review (texto compensado)
skills/plan/SKILL.md                   (modified)  convenção doc-review (texto compensado)
docs/pipeline-path.yaml                (modified)  agents/implementer.md no estágio implement
docs/instruction-budget.json           (modified)  novas entradas; nenhum teto sobe além do necessário
docs/metrics.md, docs/token-economy.md (modified)  seções novas e a higiene de contexto
CHANGELOG.md                           (modified)  Added e Changed
tests/test_token_metrics.py            (modified)  faixas, modelo, participações, doc-review
tests/test_session_context.py          (new)       tail de 50 MB, sessões ativas, limiar, formato
tests/test_next_command.py, tests/test_tasks_done_command.py  (modified)  linhas novas, sem mudar saída antiga
tests/test_implement_skill_drift.py, tests/test_dispatch_description_convention.py  (modified)  skill mais agent; doc-review
tests/test_implementer_agent.py        (new)       frontmatter, instalação nas plataformas, papel implement
tests/fixtures/token_metrics/          (modified)  faixas e modelos
```

## Phase breakdown

> Each phase is a checkpoint; order matters across phases, not within.

### Phase 1 — Distribuição de contexto em `metrics --tokens` (Story 1)

- Fixtures com requests de 30k, 50k, 120k, 150k, 200k e 250k, cinco sessões com subagentes e dois modelos.
- D1 em `token_metrics.py`; texto, JSON e `docs/metrics.md`; conferência do total contra a dedupe independente.

### Phase 2 — Aviso de contexto em `next` e `tasks done` (Story 2)

- D2 e D3: módulo, leitura do fim, sessões ativas, limiar por variável, formato das linhas.
- Teste com transcript de 50 MB (orçamento de 200 ms de `next`), transcript ausente, duas sessões ativas.

### Phase 3 — Papel `doc-review` (Story 3)

- D4: papel em `token_metrics.py`, aviso de 30%, convenção em `specify` e `plan` com o texto compensado, teste de convenção atualizado.

### Phase 4 — Agent `implementer` com modelo definido (Story 4)

- D5: agent, `implement` e `pipeline-path.yaml`; testes de prosa reescritos para ler skill mais agent; instalação nas cinco plataformas; orçamento sem subir teto.

### Phase 5 — Documentação e medição (critérios de sucesso)

- `docs/token-economy.md` e `CHANGELOG.md`; rodar `aiadev metrics --tokens` nos transcripts reais deste repositório e registrar os números e o comando no PR (Art. IV).

## Risks and mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| A "sessão corrente" por `mtime` aponta para outra sessão do mesmo diretório | Med | Low | id e idade na linha; uma linha por sessão ativa (janela de 10 minutos) |
| O formato do transcript muda ou a janela do fim não tem `usage` | Med | Low | qualquer falha resulta em nenhuma linha, nunca em erro; teste com arquivo truncado e sem `usage` |
| Ler o fim de um arquivo de centenas de MB estoura 200 ms | Low | Med | trecho fixo de 256 KiB; teste com 50 MB fixa o orçamento |
| Mover texto do prompt do implementer para o agent esconde regra de quem lê só a skill | Med | Med | testes de prosa leem skill mais agent; compare regra a regra com o texto anterior (como na T038 da 0030) |
| Prosa nova em `specify` e `plan` estoura a catraca de instruções | Med | Low | frases compensadas nas mesmas skills; teto só desce |
| Consumidor com agent `implementer` próprio | Low | Low | regra de hash do `sync` trata como conflito comum; nota no CHANGELOG |
| Limiar de 150k inadequado | Med | Low | variável `AIADEV_CONTEXT_WARN`; as novas métricas mostram, com o tempo, se o ponto está certo |

## Complexity tracking

| Article waived | Reason | Alternatives considered | Reviewer |
|---|---|---|---|
| — | nenhum waiver: todos os artigos PASS ou N/A | — | — |

## Hand-off to `tasks`

The next skill is `tasks`. It consumes this plan and produces `tasks.md`.
Pre-conditions before hand-off:

- [x] Constitution Check is fully populated, no blank rows.
- [x] Complexity tracking is filled or empty-and-justified.
- [x] Project structure delta is accurate.
