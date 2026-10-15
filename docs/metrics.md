# `aiadev metrics`

Agrega métricas do audit trail que o framework já produz
(`specs/<branch>/.review-log.jsonl`, `tasks.md`, `spec.md` headers, `git log`)
e emite indicadores estruturados em terminal ou JSON.

Toda métrica é derivada de arquivos versionados ou do git log — nenhuma
chamada de rede, nenhuma escrita em arquivo do repo. Reexecutar o
comando em um commit antigo (via `git checkout`) produz o mesmo
resultado daquele commit.

Spec: [`specs/0015-aiadev-metrics/spec.md`](../specs/0015-aiadev-metrics/spec.md).

## Quick start

```bash
# Visão de uma feature específica
aiadev metrics --feature 0015-aiadev-metrics

# Visão agregada da janela default (últimos 90 dias);
# só entram specs com Status Implemented ou Merged
aiadev metrics

# Em CI / scripts (JSON estável)
aiadev metrics --format json --since 2026-01-01
```

## Flags

| Flag | Default | Efeito |
| --- | --- | --- |
| `--feature SLUG` | _(omitido)_ | Restringe a uma feature. Aceita `0015-aiadev-metrics` ou o slug `aiadev-metrics`. |
| `--since YYYY-MM-DD` | `today - 90` dias | Início da janela. Filtra sobre o campo `Created:` do header de `spec.md`. |
| `--format {text,json}` | `text` | Formato de saída. `text` é human-friendly; `json` tem `schema_version: 1` estável (modo agregado). |
| `--tasks` | off | Inclui listing por-task de rework (Story 3 do spec). |
| `--show-bodies` | off | Imprime a prosa livre (`note`) das entries em `.review-log.jsonl`. Off por padrão (Article VI). Só tem efeito com `--feature`; no modo agregado é ignorado. |
| `--tokens` | off | Relatório de tokens por sessão do Claude Code, lido dos transcripts locais. Relatório à parte, não usa `specs/`; ver [Tokens por sessão](#tokens-por-sessão---tokens). |
| `--transcripts-dir DIR` | `~/.claude/projects/<slug do cwd>/` | Diretório de transcripts a usar com `--tokens`. |

## Amostra do modo agregado

Sem `--feature`, entram na amostra apenas specs cujo header tem
`Status:` **Implemented** ou **Merged** e cujo `Created:` cai na janela.
Specs em andamento (`Draft`, `In review`, `Approved`) ficam de fora —
use `--feature` para inspecioná-las individualmente. Valores decorados
como `Merged — \`ed0554f\` (v0.19.0)` são reconhecidos por prefixo;
valores fora do enum (ex.: `PR Open — #34`, legado) são excluídos e
contados na linha "Specs com Status fora do enum canônico".

No listing de rework agregado, os task ids vêm qualificados pelo
diretório do spec (ex.: `0014-bmad-inspired-evolutions/T003`) para que
tasks homônimas de specs diferentes não se confundam.

## Tokens por sessão (`--tokens`)

```bash
# Transcripts do workspace atual, em texto
aiadev metrics --tokens

# Mesmas medidas em JSON (byte-estável: duas execuções com o mesmo input saem idênticas)
aiadev metrics --tokens --format json

# Outro diretório de transcripts
aiadev metrics --tokens --transcripts-dir ~/.claude/projects/-caminho-do-projeto
```

Lê os transcripts locais do Claude Code (somente leitura, sem rede) e reporta
**contagens**: tokens, turnos e caracteres devolvidos por ferramenta. O texto
das mensagens e o corpo dos `tool_result` nunca saem no relatório, e a
`description` de um subagente só é consultada para derivar o papel (não é
guardada nem impressa; Article VI). Sai com código `2` quando não há
transcripts com uso de tokens. Este payload não tem `schema_version`: as chaves
existentes não mudam de significado e o JSON só ganha chaves.

O leitor é tolerante: uma linha de transcript que não é JSON válido (ou que é
aninhada demais, ou traz um inteiro enorme) é ignorada sem contagem, e um campo
de `usage` ausente, que não é inteiro, negativo ou maior ou igual a 2^63 conta
como 0. Um transcript malformado nunca aborta o relatório.

### Deduplicação por `message.id`

O Claude Code grava a mesma resposta em vários eventos enquanto faz streaming,
todos com o mesmo `message.id`, e o `usage` gravado é parcial e só cresce
(`output_tokens` 1, depois 214). Cada `message.id` conta **uma vez**, com o
**maior valor de cada campo** de `usage` (nem o último evento, nem a soma),
então o resultado não depende da ordem de leitura. A regra vale também entre
arquivos: um `message.id` repetido na thread principal e num subagente, ou em
duas sessões, é somado uma vez e atribuído à sessão que começou primeiro (a
thread principal reclama antes de qualquer subagente). Um evento sem
`message.id` conta como único.

### Conferir o total à mão

A mesma regra, escrita à parte, é a evidência de que o total do relatório está
certo (Art. IV; critério de sucesso #1 do spec 0030, que tolera 1%). Sobre os
arquivos da sessão, sem importar nada de `aiadev`:

```python
import json, pathlib, sys

root = pathlib.Path(sys.argv[1])  # o mesmo --transcripts-dir
keys = ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens", "output_tokens")
mains = sorted(root.glob("*.jsonl"))
files = mains + [p for m in mains for p in sorted((root / m.stem).glob("subagents/**/agent-*.jsonl"))]
best, loose = {}, dict.fromkeys(keys, 0)
for path in files:  # cada sessão e os agent-*.jsonl dela; journal.jsonl fica de fora
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        message = event.get("message") if event.get("type") == "assistant" else None
        usage = message.get("usage") if isinstance(message, dict) else None
        if not isinstance(usage, dict):
            continue
        if message.get("id"):  # com message.id: o maior valor de cada campo
            kept = best.setdefault(message["id"], dict.fromkeys(keys, 0))
            for k in keys:
                kept[k] = max(kept[k], usage.get(k) or 0)
        else:  # sem message.id: evento único, soma direto
            for k in keys:
                loose[k] += usage.get(k) or 0
print({k: sum(m[k] for m in best.values()) + loose[k] for k in keys})
```

Compare com `totals` **mais** `subagent_totals` de `aiadev metrics --tokens
--format json`, campo a campo (`cache_creation_input_tokens` e
`cache_read_input_tokens` são `cache_creation_tokens` e `cache_read_tokens` no
JSON; `input_tokens` e `output_tokens` não mudam). A soma é a comparável, não
cada parte: um `message.id` repetido entre a thread principal e um subagente é
atribuído à thread principal, e o trecho acima não faz essa divisão. Os campos
de `usage` fora do normal (negativos, não inteiros) o leitor trata como 0; o
trecho supõe inteiros comuns, como os de uma sessão real.

O teste `tests/test_token_metrics_manual_rule.py` faz essa conferência sobre
transcripts gerados com sementes fixas (ids repetidos com `usage` parcial,
eventos sem id, duas sessões, subagentes aninhados, um `journal.jsonl` e um
`subagents/` sem sessão ao lado, que não contam) e exige igualdade exata, mais
rígida que o 1% do spec.

### Subagentes e papel

Os transcripts de subagentes ficam em `<sessão>/subagents/**/agent-*.jsonl`
(inclui `subagents/workflows/wf_*/`; o `journal.jsonl` ao lado não é um
transcript e nunca é aberto). O custo deles é reportado **separado** da thread
principal: a tabela por sessão e a linha `TOTAL` são só da thread principal, e
os subagentes aparecem no bloco "Subagents by role" (texto) e em `subagents`,
`subagent_totals` e `subagents_by_role` (JSON).

O papel vem do campo `description` do `agent-<id>.meta.json` ao lado do
transcript, pelo prefixo `implement:`, `review:` ou `doc-review:` (sem diferenciar maiúsculas,
espaços iniciais tolerados, os dois pontos são obrigatórios). Qualquer outra
descrição, ou um `meta.json` ausente, ilegível ou malformado, deixa o subagente
como `unclassified`, e o relatório informa quantos ficaram assim
(`Unclassified subagents: N` / `unclassified_subagents`; acima de 30% do custo dos subagentes o texto avisa e o JSON traz `unclassified_share`). Nem o texto das
mensagens nem o `agentType` entram na decisão. Para o relatório agrupar, quem
despacha o subagente precisa pôr esse prefixo na descrição.

### Custo equivalente (aproximação)

`equivalent_cost` pondera os quatro componentes de `usage` e soma, em "tokens de
entrada equivalentes":

| Componente | Peso (× token de entrada) |
| --- | --- |
| leitura de cache (`cache_read_input_tokens`) | 0,1 |
| entrada (`input_tokens`) | 1,0 |
| saída (`output_tokens`) | 5,0 |
| escrita de cache, tier de 5 min | 1,25 |
| escrita de cache, tier de 1 h | 2,0 |

O tier da escrita de cache vem de `usage.cache_creation.ephemeral_*`; o que o
detalhe não cobre (ou um transcript sem detalhe) conta como 5 min. É uma
**aproximação** para comparar sessões entre si, **não um preço**: um único
conjunto de pesos para todos os modelos. O relatório declara isso: o texto traz
a nota com os pesos e o JSON traz `cost_model` (`approximation: true`, `unit`,
`weights`). Os pesos são as constantes `WEIGHT_*` de
`src/aiadev/token_metrics.py`; a nota e o JSON são montados a partir delas.

### Distribuição de contexto (spec 0031)

Além dos blocos acima, `--tokens` mostra, depois do custo equivalente e antes de
"Top tools by result chars", quatro seções. Todas somam a thread principal e os
subagentes, exceto onde está dito.

- **Context distribution**: quantas requests (e quantos tokens de contexto)
  caíram em cada faixa de tamanho do contexto da própria request. Tabela com as
  quatro faixas, colunas `requests`/`tokens` (todas as requests) e
  `main requests`/`main tokens` (só a thread principal) e linha `TOTAL`. As
  faixas ficam sempre presentes, com zero quando vazias.
- **Top sessions by cost**: as 3 sessões mais caras (id cortado em 8
  caracteres), com o custo equivalente da thread principal mais os subagentes
  da mesma sessão e a participação (%).
- **Tokens by model**: tokens de contexto por modelo, em ordem decrescente, com
  a participação (%). Request sem modelo conta como `unknown`.
- **Subagent share**: `x% of requests, y% of tokens` que passaram por subagentes.

Faixas (contexto da request): `<50k` (menos de 50.000), `50k-150k`
(\[50.000, 150.000)), `150k-200k` (\[150.000, 200.000], o 200.000 inclusive) e
`>200k` (mais de 200.000).

**Contexto** de uma request é `input + cache_creation + cache_read` da request
já deduplicada por `message.id` (a saída não entra). A soma dos tokens das
faixas é, portanto, o `total_input_tokens` da thread principal mais o dos
subagentes, e a soma das requests é o total de turnos dos dois.

**Participação** é a fração do total: na sessão, o custo equivalente dela sobre
`total_equivalent_cost`; no modelo, os tokens dele sobre os tokens de todos os
modelos; no subagente, requests e tokens dos subagentes sobre os totais. O top é
ordenado por custo equivalente (empate pelo id da sessão).

No JSON (`--format json`) entram cinco chaves novas no objeto de topo, sem
alterar as existentes: `context_distribution` (`all` e `main_thread`, cada um
com `requests` e `context_tokens` por faixa), `top_sessions`
(`session_id`, `cost`, `share`), `model_shares` (`model`, `tokens`, `share`) e
`subagent_share` (`requests`, `tokens`; frações de 0 a 1) e
`unclassified_share` (fração do custo dos subagentes sem papel).

### Chaves do JSON

Mantidas como estavam: `transcripts_dir`, `sessions[]` e `totals` (só a thread
principal). Acrescentadas:

| Chave | Conteúdo |
| --- | --- |
| `sessions[].equivalent_cost`, `totals.equivalent_cost` | Custo equivalente da thread principal. |
| `sessions[].subagents[]` | `agent_id`, `role`, `turns`, `input_tokens`, `cache_creation_tokens`, `cache_read_tokens`, `output_tokens`, `equivalent_cost`. |
| `subagent_totals` | Soma de todos os subagentes (`agents`, os mesmos campos de uso e `equivalent_cost`). |
| `subagents_by_role` | `implement`, `review`, `doc-review` e `unclassified` (sempre os quatro, com zeros quando vazios): `agents`, os campos de uso e `equivalent_cost`. |
| `unclassified_subagents` | Quantos subagentes ficaram sem papel. |
| `total_equivalent_cost` | Thread principal mais subagentes: o número para comparar entre sessões. |
| `context_distribution` | `all` e `main_thread`, cada um com `requests` e `context_tokens` por faixa (`<50k`, `50k-150k`, `150k-200k`, `>200k`). |
| `top_sessions` | As 3 sessões de maior custo: `session_id`, `cost`, `share`. |
| `model_shares` | `model`, `tokens`, `share`, por tokens decrescentes. |
| `subagent_share` | `requests` e `tokens`, frações de 0 a 1. |
| `unclassified_share` | Fração do custo dos subagentes sem papel. |
| `cost_model` | `approximation: true`, `unit` e `weights`. |

`sidechain_turns` continua somando duas coisas: turnos da thread principal
marcados como sidechain (esses entram em `turns`) e turnos de subagentes (esses
não). O texto separa as duas no relatório.

## Exit codes

| Code | Quando |
| --- | --- |
| `0` | Sucesso. Pode haver `coverage=0%` se nenhum spec na janela tiver `.review-log.jsonl` — não é erro. |
| `1` | Erro de parse (spec.md com header não-recuperável) ou feature inexistente. |
| `2` | Nenhum spec `Implemented`/`Merged` na janela, OU feature solicitada está antes do cutoff `0014` (sem `.review-log.jsonl`). |

## Métricas reportadas

- **First-pass approval rate** por reviewer (`code-reviewer`, `spec-document-reviewer`, `plan-document-reviewer`). Definido como: para cada par `(task_id, reviewer)` em ordem cronológica de entrada no JSONL, a primeira entry conta como 1ª passada (cl-6 resolution).
- **Tasks por status** somadas em todas as specs da janela (`pending` / `in_progress` / `blocked` / `done`).
- **Tasks com rework** (`--tasks`): lista de `(task_id, rounds)` ordenada por número de rodadas descendente, considerando apenas entries do `code-reviewer` em tasks reais (não `branch-review`).
- **Specify → último commit (mediana, em dias)** quando há git log disponível.
- **Markers `cl-N` não resolvidos** (snapshot atual).
- **Specs com `Status:` fora do enum canônico** (bucket `other` — legacy).
- **`n=` e `coverage=%`** sempre presentes; comunica honestamente o tamanho da amostra.

## O que estes números **não** significam

Cada métrica vem acompanhada de uma linha "anti-Goodhart" explicando seu
limite. Exemplos:

- `first-pass rate` alta NÃO implica qualidade — pode indicar reviewer permissivo ou specs triviais.
- `tasks com rework` NÃO implica engenheiro ruim — pode indicar spec ambígua.
- `coverage < 100%` reflete specs pré-cutoff (≤ 0014) sem `.review-log.jsonl`, não falha de processo.

## Privacy

A prosa livre do reviewer (campo `note` em `.review-log.jsonl`, incluindo
o bloco `### Why no issues` em mudança non-trivial) **não** aparece na
saída padrão. Apenas contagens, timestamps e flags estruturadas são
emitidas. Para inspecionar bodies, use `--show-bodies` explicitamente
(decisão cl-3 do spec).

## Schema JSON

`--format json` emite um payload com `schema_version: 1`. O schema é
estável dentro de uma major version do `aiadev`; campos novos entram
como `schema_version: 2`. O payload **não inclui timestamp de
execução** — duas execuções com o mesmo input produzem byte-idêntico
output (success criterion #4 do spec).

## Limites conhecidos do MVP

- Single-repo apenas (cl-2). Agregação cross-repo é spec futura.
- Sem dashboard / persistência. Cada execução recalcula do audit trail.
- Sem estimativa de custo de API: o custo de `--tokens` é um equivalente em
  tokens de entrada com pesos fixos, uma aproximação para comparar sessões, não
  um preço.
- `Iterações de clarify` sub-reporta: a contagem deriva do `git log -p`
  de `spec.md`, então markers `cl-N` criados **e** resolvidos antes do
  primeiro commit da spec nunca aparecem no histórico.
- O parser de `tasks.md` usa a gramática canônica estrita
  (`### TNNN — título` + `- **Status:** ...`). A extensão VSCode tolera
  formatos mais soltos (checkbox, tabela, sinônimos); em repos com esses
  formatos, os números de tasks podem divergir entre as duas superfícies.
