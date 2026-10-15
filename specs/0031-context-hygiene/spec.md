# Feature specification: Higiene de contexto — ver onde o contexto se acumula e avisar a hora de cortar a sessão

> Produced by `specify`. **What** and **why** only; planning and code belong in `plan.md` and `tasks.md`.

**Branch:** `feature/0031-context-hygiene`
**Created:** 2026-10-15
**Status:** Draft <!-- Draft | In review | Approved | Implemented -->
**Spec ID:** 0031 <!-- auto-incrementing integer -->
**Language:** pt-BR <!-- BCP-47 tag; downstream artifacts use it. -->

---

<!-- section: Problem -->
## Problem

Cada request reenvia a conversa inteira; por isso o custo de uma sessão cresce com o **contexto acumulado vezes o número de turnos**, não com o que o agente escreve. Nos 3 transcripts deste repositório (cerca de 4.050 requests, deduplicadas por `message.id`, medidas em 2026-10-15; os números mudam um pouco a cada nova sessão, porque o transcript da sessão corrente cresce), 96,8% dos tokens são leitura de cache e 0,27% são saída. A thread principal tem contexto médio de 250k, 400k e 355k tokens por request (máximo 741k), e as requests acima de 200k são 25,6% das requests e **62,2% dos tokens**. Os subagentes pesam menos por request (contexto médio de 46k a 85k, por sessão). O artigo que motivou esta spec (https://dev.to/alairjt/i-burned-95-of-my-ai-coding-quota-in-2-days-heres-what-the-logs-revealed-2omf) descreve o mesmo padrão: poucas sessões longas, nunca reiniciadas, dominam o volume.

O framework já reduziu turnos e despachos (spec 0030), mas continua sem duas coisas: (1) enxergar essa distribuição — `aiadev metrics --tokens` só soma por sessão e por papel, e quem quer a distribuição precisa de um script avulso; (2) qualquer sinal de que é hora de cortar a sessão — nenhuma skill, rule ou comando fala em compactar ou recomeçar, embora o estado do trabalho já viva em artefatos (`tasks.md`, git, o guarda "pular task `done`" do `implement`) e uma sessão nova retome de onde parou. Além disso, cerca de 110 dos 178 subagentes dos transcripts aparecem como "não classificados" (77% do custo de subagentes), o que esconde onde o custo de subagente está.

<!-- section: Reconnaissance -->
## Reconnaissance

- **aiadev metrics --tokens** — entry: `src/aiadev/commands/metrics.py` · auth: none · integration: `src/aiadev/token_metrics.py` (hoje agrega por sessão e por papel; não guarda o contexto de cada request)
- **aiadev next** — entry: `src/aiadev/commands/next.py` · auth: none · integration: `src/aiadev/pipeline_state.py` (estado da feature; sem informação de sessão ou de contexto)
- **aiadev tasks done** — entry: `src/aiadev/commands/tasks.py` · auth: none · integration: `src/aiadev/tasks_status.py` (imprime só `<hash> <assunto>` ao fechar a task)
- **dispatch de subagentes** — entry: `skills/implement/SKILL.md` · auth: none · integration: `agents/code-reviewer.md` (papel pelo prefixo da `description`; o implementer é despachado sem modelo e sem agent próprio, e os três revisores têm `model: sonnet`)

<!-- section: Users and stakeholders -->
## Users and stakeholders

- Mantenedor ou tech lead que acompanha o custo e a cota das sessões do Claude Code.
- Agente que executa `implement` (ou qualquer etapa) e hoje não tem sinal de quando o contexto ficou caro.

<!-- section: Success criteria -->
## Success criteria

<!-- Each criterion testable. -->

- `aiadev metrics --tokens` (texto e JSON) informa: requests e tokens por faixa de contexto, contando todas as requests (thread principal e subagentes) e mostrando também a parte da thread principal; a participação das 3 sessões de maior custo no total (custo = custo equivalente de `cost_model()`); a participação de cada modelo nos tokens; e a participação dos subagentes em requests e em tokens. O contexto de uma request é `input + cache_creation + cache_read` da request deduplicada. As faixas são `< 50k` (contexto < 50.000), `50k–150k` (50.000 ≤ contexto < 150.000), `150k–200k` (150.000 ≤ contexto ≤ 200.000) e `> 200k` (contexto > 200.000); somam o total, e o total confere, dentro de 1%, com a deduplicação manual da mesma sessão (mesma regra de `tests/test_token_metrics_manual_rule.py`).
- `aiadev next` e `aiadev tasks done` imprimem uma linha `context: <N>k tokens (session <id de 8 caracteres>, <idade>)` com o contexto da última request da sessão corrente e, acima do limiar (padrão 150k tokens, variável `AIADEV_CONTEXT_WARN` em tokens), uma linha `checkpoint:` que diz que o estado está em `tasks.md` e no git e que a sessão pode ser compactada ou recomeçada retomando com `aiadev next`. A sessão corrente é o transcript modificado mais recentemente no diretório do projeto; se outro transcript do mesmo diretório foi modificado nos últimos 10 minutos, o comando imprime uma linha `context:` por sessão ativa, cada uma com o seu id. Sem transcript legível, nada é impresso e o código de saída não muda.
- A leitura do transcript para essas linhas lê só um trecho de tamanho fixo do fim do arquivo e mantém `aiadev next` dentro do orçamento de 200 ms já fixado pela spec 0030, medido com um transcript de 50 MB.
- O `implement` despacha o implementer por um agent próprio, `agents/implementer.md`, com `model: sonnet` no frontmatter (como os revisores), e o orçamento de instruções não sobe nenhum teto de `docs/instruction-budget.json` além da descrição do novo agent, que é compensada.
- Os revisores de documento passam a ter papel próprio, `doc-review`: as skills `specify` e `plan` documentam o prefixo `doc-review:` na `description` do despacho, `_subagent_role` em `src/aiadev/token_metrics.py` o reconhece, e o relatório de `--tokens` avisa quando mais de 30% do custo de subagentes é não classificado.
- Nada sai da máquina e nada é gravado: a leitura usa só campos de uso e modelo, nunca o corpo de `tool_result` (teste de privacidade existente mantido).

<!-- section: Non-goals -->
## Non-goals

- Compactar ou limpar a sessão automaticamente: o framework não executa `/compact` nem `/clear`; ele só informa.
- Instalar hooks, statusline ou configurações do Claude Code no consumidor (continuam do consumidor, como em `docs/token-economy.md`).
- Provar que o aviso reduz custo: o efeito é observável pelas novas métricas (a fatia de requests acima de 200k ao longo do tempo), não é um gate desta spec.
- Medir outros agentes além do Claude Code: o formato de transcript é o dele.
- Compressão de saída de ferramenta (o `smart-mcp-proxy` já cobre) e novos cortes de texto de skills.

<!-- section: User stories -->
## User stories

### Story 1 — Ver onde o contexto se acumula (P1)

Como mantenedor, quero que `aiadev metrics --tokens` mostre a distribuição por contexto, a concentração por sessão, a participação por modelo e a fatia dos subagentes, para diagnosticar a cota sem script avulso.

**Acceptance scenarios** (≥ 3 per story):

1. Given transcripts com requests de 30k, 50k, 120k, 150k, 200k e 250k de contexto, When rodo `aiadev metrics --tokens`, Then cada request cai na faixa pela regra de limites (50.000 vai para `50k–150k`, 150.000 e 200.000 para `150k–200k`), vejo requests e tokens por faixa, para todas as requests e só para a thread principal, e as faixas somam o total do relatório.
2. Given 5 sessões de tamanhos diferentes com subagentes e mais de um modelo, When rodo o relatório, Then vejo a participação das 3 sessões de maior custo no total, a participação de cada modelo nos tokens e a fatia dos subagentes em requests e em tokens.
3. Given `--format json`, When rodo o relatório, Then os mesmos campos aparecem como chaves novas e nenhuma chave existente muda de nome ou de valor.
4. Given uma request sem `message.id`, sem modelo ou com `usage` parcial de streaming, When rodo o relatório, Then ela é contada uma vez, na faixa do seu uso (máximo por campo, como hoje), e o modelo ausente aparece como `unknown`, sem erro.

### Story 2 — Saber a hora de cortar a sessão (P1)

Como agente que executa `implement`, quero ver o contexto da sessão e um aviso quando ele passa do limiar, para cortar a sessão entre tasks em vez de arrastar contexto caro.

**Acceptance scenarios** (≥ 3 per story):

1. Given um transcript cuja última request tem 412k de contexto, modificado há 3 minutos, e o limiar padrão de 150k, When rodo `aiadev next`, Then a saída inclui `context: 412k tokens (session <id>, 3 min ago)` e a linha `checkpoint:`, que diz que o estado está em `tasks.md` e no git e que se retoma com `aiadev next`.
2. Given a mesma sessão, When fecho uma task com `aiadev tasks done`, Then, depois do `<hash> <assunto>`, o comando imprime a linha `context:` e a linha `checkpoint:`, sem alterar o commit nem o código de saída.
3. Given uma última request abaixo do limiar (ou `AIADEV_CONTEXT_WARN` acima do contexto), When rodo `aiadev next` ou `aiadev tasks done`, Then a saída mostra só a linha `context:`, sem `checkpoint:`.
4. Given que não há transcript legível para o diretório corrente, When rodo qualquer um dos dois comandos, Then nenhuma linha de contexto aparece e a saída e o código de saída são os de hoje.
5. Given um transcript de 50 MB, When rodo `aiadev next`, Then o comando termina dentro de 200 ms lendo só um trecho de tamanho fixo do fim do arquivo.
6. Given dois transcripts do mesmo diretório, ambos modificados nos últimos 10 minutos, When rodo `aiadev next`, Then a saída traz uma linha `context:` para cada sessão ativa, com o id de cada uma, e o `checkpoint:` aparece só para as que passam do limiar.

### Story 3 — Custo de subagente classificado (P2)

Como mantenedor, quero que os revisores de documento tenham papel próprio no relatório, para que "não classificado" deixe de esconder a maior parte do custo de subagentes.

**Acceptance scenarios** (≥ 3 per story):

1. Given um subagente despachado por `specify` ou `plan` seguindo a convenção documentada nas duas skills, com `description` iniciada por `doc-review:`, When rodo `aiadev metrics --tokens`, Then ele aparece no papel `doc-review`, e não em `unclassified`.
2. Given subagentes sem prefixo reconhecido que somam mais de 30% do custo de subagentes, When rodo o relatório, Then uma linha de aviso informa a participação e o critério.
3. Given subagentes com os prefixos `implement:` e `review:`, When rodo o relatório, Then a classificação de hoje não muda.

### Story 4 — Implementer com modelo definido (P2)

Como mantenedor, quero que o implementer tenha agent e modelo próprios, para que o custo de implementação não herde o modelo mais caro da sessão.

**Acceptance scenarios** (≥ 3 per story):

1. Given um projeto com o framework instalado, When o `implement` despacha a task, Then o despacho usa o agent `implementer`, cujo frontmatter declara `model: sonnet`, em vez de `general-purpose`.
2. Given o agent `implementer` instalado em cada plataforma com suporte a agents, When rodo `aiadev install` e `aiadev sync`, Then o arquivo chega a cada uma, sem remover nem alterar os agents existentes.
3. Given o orçamento de instruções, When rodo `scripts/instruction_budget.py --check`, Then nenhum teto sobe além do necessário para a descrição do novo agent, e o percurso `specify → finish` não cresce.
4. Given que a `description` do despacho segue a convenção `implement:`, When o agent `implementer` é usado, Then o relatório de `--tokens` continua classificando o subagente no papel `implement`.

<!-- section: Clarifications -->
## Clarifications

- cl-1 — Os subagentes de rotina usam modelo menor por padrão: o framework passa a ter um agent `implementer` (`agents/implementer.md`) com `model: sonnet` no frontmatter, e o `implement` despacha o implementer por ele; os três revisores já têm `model: sonnet`. A escolha é por agent, e não por frase no despacho, para não consumir texto de `skills/implement/SKILL.md` (teto de 1.500 tokens sem folga). Resposta do mantenedor em 2026-10-15.

<!-- section: Data touched -->
## Data touched

- Leitura dos transcripts locais em `~/.claude/projects/<slug do cwd>/` (campos de uso, modelo, `message.id`, `agentType` e `description` dos subagentes); nenhuma escrita.
- Saída de `aiadev metrics --tokens`, `aiadev next` e `aiadev tasks done` (linhas novas).

<!-- section: Out-of-band effects -->
## Out-of-band effects

- Nenhum efeito fora da máquina: sem rede, sem escrita fora do que os comandos já escrevem (`tasks done` continua comitando como hoje).

<!-- section: Open risks -->
## Open risks

- A "sessão corrente" é inferida pelo transcript mais recente do diretório; duas sessões no mesmo diretório (por exemplo, rodadas em paralelo) podem fazer a linha citar a outra; a mitigação é exigida acima (id e idade na linha; uma linha por sessão ativa), mas sessões antigas e paradas continuam ignoradas.
- O formato do transcript é interno do Claude Code e pode mudar: a ausência ou a mudança do formato tem de resultar em "nenhuma linha", nunca em erro.
- A janela de contexto dos modelos atuais chega a 1M tokens, então o limiar de 150k reflete custo por turno, não limite técnico.
- Uma linha de convenção (`doc-review:`) em `specify` e `plan` consome texto de skill que a catraca de `docs/instruction-budget.json` mede; precisa ser compensada, sem subir teto.
- O limiar padrão é arbitrário (vem do artigo); só a evidência de uso mostra se 150k é o ponto certo.

## Assumptions

- O limiar padrão é 150.000 tokens (valor do artigo) e o nome da variável que o troca é `AIADEV_CONTEXT_WARN`. [impact: low]
- A janela de "sessão ativa" é de 10 minutos. [impact: low]
- As faixas de contexto são fixas (`< 50k`, `50k–150k`, `150k–200k`, `> 200k`), as do artigo. [impact: low]
- O aviso de não classificado dispara acima de 30% do custo de subagentes. [impact: low]
- O prefixo do novo papel é `doc-review:`, na mesma convenção de `implement:` e `review:`. [impact: low]

<!-- section: Traceability -->
## Traceability

- Originating issue: artigo https://dev.to/alairjt/i-burned-95-of-my-ai-coding-quota-in-2-days-heres-what-the-logs-revealed-2omf (pedido do mantenedor em 2026-10-15)
- Roadmap: R014 (depende de R008)
- Related specs: 0015-aiadev-metrics, 0022-smart-mcp-proxy-token-economy, 0030-lean-pipeline (decidiu deixar os revisores de documento não classificados; esta spec reverte só essa parte)
- Constitution articles invoked: I, II, III, IV, VI
