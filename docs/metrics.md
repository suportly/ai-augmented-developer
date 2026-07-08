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
| `--format {text,json}` | `text` | Formato de saída. `text` é human-friendly; `json` tem `schema_version: 1` estável. |
| `--tasks` | off | Inclui listing por-task de rework (Story 3 do spec). |
| `--show-bodies` | off | Imprime a prosa livre (`note`) das entries em `.review-log.jsonl`. Off por padrão (Article VI). Só tem efeito com `--feature`; no modo agregado é ignorado. |

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
- Sem estimativa de custo de API. Deliberadamente fora de escopo.
- `Iterações de clarify` sub-reporta: a contagem deriva do `git log -p`
  de `spec.md`, então markers `cl-N` criados **e** resolvidos antes do
  primeiro commit da spec nunca aparecem no histórico.
- O parser de `tasks.md` usa a gramática canônica estrita
  (`### TNNN — título` + `- **Status:** ...`). A extensão VSCode tolera
  formatos mais soltos (checkbox, tabela, sinônimos); em repos com esses
  formatos, os números de tasks podem divergir entre as duas superfícies.
