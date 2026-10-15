# Implementation plan: Higiene de contexto — ver onde o contexto se acumula e avisar a hora de cortar a sessão

> Produced by the `plan` skill from an approved `spec.md`. This file describes **how** the spec will be realized. Do not rewrite `spec.md` into `plan.md`.

**Branch:** `feature/0031-context-hygiene`
**Date:** 2026-10-15
**Spec:** [spec.md](./spec.md)
**Plan version:** 2
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
Decision: `_MessageUsage` ganha `model` (`merged()` o carrega: vale o último não vazio; o modelo ausente e o `<synthetic>` viram `unknown` (o `<synthetic>` quase sempre tem uso zero; modelos com zero tokens são omitidos do relatório)) e uma propriedade `context` (`input + cache_creation + cache_read` da request já mesclada pelo máximo por campo; a saída não entra). `_add_message` acumula, na sessão que reivindicou a mensagem, requests e tokens de contexto por faixa (limites da spec: `< 50.000`, `[50.000, 150.000)`, `[150.000, 200.000]`, `> 200.000`) e tokens de contexto por modelo (a mesma definição das faixas, para a soma por modelo conferir com `total_input_tokens`). **Thread principal** = as mensagens que a sessão principal reivindicou (a mensagem que aparece no arquivo principal e num arquivo de subagente é reivindicada pelo principal, como no dedupe de hoje); **todas** = principal + subagentes. Como `_read_subagents` limpa `sidechain` e `_attach_subagents` copia só `_TOKEN_FIELDS`, `SubagentTokens` ganha os campos de faixa e de modelo e `_attach_subagents` os copia. `TokenReport` calcula: a fatia dos subagentes em requests e em tokens; as 3 sessões de maior custo, em custo equivalente da **sessão mais os seus subagentes** (participação sobre `total_equivalent_cost`); e a participação de cada modelo. Definição dos totais: a soma dos tokens de contexto das faixas é igual a `total_input_tokens` de principal + subagentes, e a soma das requests das faixas é igual ao total de requests; é isto que o teste e a conferência de 1% comparam. Texto e JSON ganham seções e chaves novas; nenhuma chave existente muda.
Rationale: o dedupe por `message.id` já existe e é a fonte correta (uso parcial de streaming); calcular as faixas depois dele evita contar a mesma request duas vezes.
Trade-offs: `SessionTokens` e `SubagentTokens` crescem em campos, todos com valor padrão, então fixtures e JSON atuais seguem verdes. Requests sem `message.id` contam uma vez, na faixa do seu uso, como hoje. Fixture nova: o mesmo `message.id` no arquivo principal e num de subagente, com as faixas somando o total.

**D2 — Um módulo novo, `session_context`, lê o fim do transcript mais recente.**
Decision: `src/aiadev/session_context.py` expõe `active_contexts(workspace, now, home=None)`, que lista os transcripts de `default_transcripts_dir(workspace)`, devolve o mais recente por `mtime` e, além dele, os modificados nos últimos 10 minutos contados de `now`. Para cada um lê o **fim do arquivo** com janela adaptativa: 256 KiB e, se nenhuma linha com `usage` aparecer, 1 MiB e depois 4 MiB (limite máximo; sem `usage` nesse trecho, o arquivo não gera linha). A primeira linha da janela é descartada **só quando o deslocamento é maior que zero** (a linha pode estar cortada). O contexto é o da última request com `usage`, com o máximo por campo entre as linhas do mesmo `message.id` **dentro da janela**; só `input + cache_creation + cache_read` importa, então a saída parcial é irrelevante e um id cuja primeira linha foi cortada ainda traz o contexto completo nas linhas restantes. `format_lines(contexts, threshold)` produz `context: <N>k tokens (session <id de 8 caracteres>, <idade>)` e, acima do limiar, `checkpoint: ...`. O limiar vem de `AIADEV_CONTEXT_WARN` (tokens; valor inválido ou ausente usa 150.000). A idade é `<n>s ago`, `<n> min ago` ou `<n> h ago`.
Rationale: o módulo tem dois chamadores (`next` e `tasks done`), então a abstração se paga (Art. III). A janela adaptativa existe porque os gaps entre linhas com `usage` medidos nos transcritos reais passam de 256 KiB em 2 de 1.138 casos na sessão de 23 MB (mais de 3% das posições de fim de arquivo ficariam sem linha, justamente nas sessões mais caras); 4 MiB cobre o máximo medido (909 KB) com folga e mantém a leitura limitada.
Trade-offs: a leitura de 1 a 4 MiB só acontece quando a janela menor falha, então o caso comum continua em 256 KiB. A "sessão corrente" é uma inferência por `mtime`, mitigada por id, idade e uma linha por sessão ativa, como a spec exige; `slug_for` e `Path.cwd()` herdam as limitações listadas nos riscos.

**D3 — Ligação em `next` e `tasks done`, sem efeito colateral.**
Decision: `commands/next.py` imprime as linhas depois do bloco de estado, usando `Path.cwd()`. `commands/tasks.py` imprime depois do `<hash> <assunto>`, usando a raiz do repositório que o comando já resolve (`git rev-parse --show-toplevel`). Qualquer `OSError` ou `ValueError` na leitura vira "nenhuma linha"; o código de saída e o commit não mudam. Saída com `escape()` do Rich nas linhas de `next`. Antes de editar `tasks done`, conferir se `tests/test_tasks_done_command.py` fixa a saída exatamente.
Rationale: o `tasks done` é o ponto em que o agente fecha cada task, o lugar natural para o aviso, e não custa texto de skill (o teto de `skill:implement` está sem folga).
Trade-offs: uma linha a mais por task fechada no contexto do orquestrador (poucas dezenas de tokens), contra o custo de uma sessão de 700k.

**D4 — Papel `doc-review` e aviso de não classificado.**
Decision: `ROLE_DOC_REVIEW = "doc-review"` entra em `ROLES` e em `_subagent_role` (prefixo de `description`, sem diferenciar maiúsculas, dois-pontos obrigatório, como `implement:` e `review:`). A tabela por papel e o JSON incluem o papel novo. Quando os não classificados passam de 30% do custo equivalente de subagentes, o relatório imprime uma linha de aviso com a participação e o critério. As skills `specify` e `plan` ganham uma frase cada, mandando despachar o revisor de documento com `description` `doc-review: spec <slug>` ou `doc-review: plan <slug>`; o texto é compensado nas mesmas skills (tetos de `docs/instruction-budget.json` só descem).
Rationale: nos transcripts medidos, 110 dos 178 subagentes (77% do custo de subagentes) são "não classificados"; o relatório precisa separar o que é conhecido.
Trade-offs: a spec 0030 deixou os revisores de documento não classificados de propósito; esta decisão reverte só isso. Sessões antigas continuam sem prefixo e o aviso vai disparar para elas, o que é informação correta, não erro. A mudança de comportamento é um teste vermelho primeiro: `tests/test_dispatch_description_convention.py` hoje afirma o contrário (`test_document_reviewers_are_not_classified`), e o docstring do módulo e o de `_subagent_role` são atualizados junto.

**D5 — Agent `implementer` com `model: sonnet`, com o texto fixo movido do prompt da skill.**
Decision: `agents/implementer.md` (frontmatter `name`, `description` curta e `model: sonnet`; **sem `tools:`**, para o implementer continuar herdando o conjunto de ferramentas do `general-purpose`, incluindo a ferramenta de skills que o TDD usa) carrega o texto fixo do prompt do implementer em `skills/implement/SKILL.md`: o fluxo test-first e a lista de status que o implementer devolve. O prompt da skill passa a levar só o que muda por task (título, recorte da spec, entrada do plano, lista de arquivos), a seção "Status handling" fica na skill (é o orquestrador quem age sobre os status) e o passo 4 manda despachar o agent `implementer` com a `description` `implement: <TID> <título>`. `docs/pipeline-path.yaml` lista `agents/implementer.md` no estágio `implement`, pela mesma regra que lista `agents/code-reviewer.md` (o agent que o estágio despacha).
Orçamento, com a conta honesta: o texto que sai da skill é de ~460 caracteres (~115 tokens) e o agent tem esse texto mais frontmatter, ~750 caracteres (~190 tokens); o percurso cresceria ~70 tokens e `path:total` está sem folga (12715 de 12715). A task de implementação é aceita só com o percurso **não maior** que o atual e **nenhum teto subido**, e compensa assim: (a) o agent é escrito o mais enxuto possível (descrição de uma linha); (b) a lista de status do agent e as linhas de "Status handling" da skill deixam de se repetir (as definições ficam no agent, as ações na skill); (c) `skill:implement` **diminui**, não só fica em 1500; (d) a `description` do novo agent aumenta `preset:lean:agents`, `preset:django-drf-react:agents` e os dois `preset:*:total`, compensada encurtando as descrições dos três revisores no mesmo componente. Se a conta não fechar, a task para e relata o saldo, em vez de subir teto.
Rationale: o texto sai da skill e entra no agent, o orquestrador emite menos texto por despacho e o modelo vem do frontmatter, como nos três revisores, sem frase de skill.
Trade-offs: nas plataformas que ignoram ou leem diferente o `model:` (por exemplo OpenCode, que espera `provider/model`), o comportamento é o já existente para os revisores; os cinco handlers repassam agents sem alteração e `framework_artifacts` descobre `agents/*.md`. Os testes que fixam o prompt do implementer passam a ler a skill mais o agent, como no gate da 0030. Um `implementer` próprio no consumidor vira conflito comum no `sync`, tratado pela regra de hash.

## Project structure changes

```text
src/aiadev/token_metrics.py            (modified)  contexto e modelo por request, faixas, participações, doc-review
src/aiadev/session_context.py          (new)       últimos contextos das sessões ativas, leitura do fim do transcript
src/aiadev/commands/next.py            (modified)  linhas context e checkpoint
src/aiadev/commands/tasks.py           (modified)  linhas context e checkpoint depois do commit
agents/implementer.md                  (new)       agent com model: sonnet, sem tools; fluxo test-first e status
agents/{code-reviewer,plan-document-reviewer,spec-document-reviewer}.md  (modified)  descrições encurtadas para compensar o sempre-carregado
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
| Janela do fim sem `usage` em sessões com tool results enormes | Med | Low | janela adaptativa de 256 KiB a 4 MiB; teste com linha de mais de 256 KiB no fim; sem `usage`, nenhuma linha |
| `slug_for` troca só `/` e `\`; se o Claude Code trocar outros caracteres do caminho, ou se `next` rodar de um subdiretório, o transcript não é achado | Low | Low | herdado de `metrics --tokens`; resulta em nenhuma linha, nunca em erro; registrado como limitação |
| Fixture de 50 MB pesa no repositório | Low | Low | gerada em tempo de teste num diretório temporário, nunca commitada |
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
