# Baseline de contexto (spec 0031)

Medição pontual de 2026-10-15, feita nos transcripts reais deste repositório
(`~/.claude/projects/-Users-alairjt-Workspace-ai-augmented-developer/`: 3
sessões e os subagentes de cada uma). Os números mudam a cada nova sessão
porque o transcript da sessão corrente cresce; use-os como ponto de partida
para comparar, não como constante.

## Comando e conferência

```bash
aiadev metrics --tokens --transcripts-dir <cópia dos transcripts>
```

A medição foi feita sobre uma cópia dos transcripts (a sessão corrente cresce
a cada request). Um script independente (dedupe por `message.id` com o máximo
por campo, subagentes lidos recursivamente, a request que aparece no arquivo
principal e no de subagente contada uma vez, como principal) deu **os mesmos
tokens por faixa**, para todas as requests e só para a thread principal. A
contagem de requests do relatório é uma a mais que a do script (4.394 contra
4.393): o relatório conta a mensagem sintética sem uso, pela regra de `turns`
que já existia; os tokens não mudam.

| Faixa de contexto | Requests | Tokens de contexto | Requests (principal) | Tokens (principal) |
|---|---|---|---|---|
| `< 50k` | 636 | 26.769.706 | 2 | 48.696 |
| `50k-150k` | 2.386 | 195.318.933 | 201 | 22.289.433 |
| `150k-200k` | 213 | 36.486.594 | 119 | 20.729.834 |
| `> 200k` | 1.159 | 487.616.119 | 1.093 | 471.036.047 |
| Total | 4.394 | 746.191.352 | 1.415 | 514.104.010 |

Requests acima de 200k: 26,4% das requests e 65,3% dos tokens de contexto. Na
thread principal, 1.093 das 1.415 requests (77%) passam de 200k.

## `aiadev next` com o transcript real

O maior transcript tem 44 MB (a sessão que construiu esta spec). Resultados:

- `last_context` lê o fim do arquivo e devolve o contexto da última request em
  0,27 ms.
- `aiadev next --feature 0031-context-hygiene` leva 0,12 a 0,15 s de parede,
  incluindo a partida do Python, dentro do orçamento de 200 ms.
- A linha impressa identifica a sessão certa:
  `context: 768k tokens (session 8b8621a8, 0s ago)`, seguida de `checkpoint:`
  porque 768k passa do limiar de 150k.

## Nada é gravado

Depois de `aiadev metrics --tokens --format json` e de cinco execuções de
`aiadev next`, o tamanho e o `mtime` dos outros dois transcripts ficaram
idênticos e `git status` ficou limpo. Os comandos só leem arquivos locais e
não abrem conexão.

## Como repetir

Gere uma cópia dos transcripts, rode o comando acima e compare as faixas com um
dedupe independente por `message.id`. A regra do total é a mesma de
`tests/test_token_metrics_manual_rule.py`.
