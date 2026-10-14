# Benchmark 0030: custo por feature, antes e depois

Critério de sucesso #8 da spec `specs/0030-lean-pipeline/spec.md`: o efeito do
pipeline enxuto é aceito por **custo por feature concluída**, não por tokens
economizados.

## Regra de aceitação

- Pelo menos 5 pares.
- Mediana da razão de custo depois/antes menor que 1,0.
- A aprovação de primeira agregada (aprovados na 1ª tentativa sobre reviews,
  todos os reviewers) não cai mais de 5 pontos percentuais.

Se a regra reprovar, o resultado é registrado sem mascarar e a reversão
sugerida é manter os dois reviewers separados (ver T058).

## Protocolo

1. **Micro-feature.** Sempre a mesma, com spec fixa em
   [`docs/benchmark-0030/microfeature.md`](./benchmark-0030/microfeature.md)
   (3 tasks pequenas). Cada execução parte de um projeto de exemplo limpo.
2. **Braços.** `antes` = commit `cc072ef` (pré-0030); `depois` = `HEAD` da
   branch `feature/0030-lean-pipeline`. Instale o framework do checkout
   correspondente em cada braço (`git checkout <commit>` num worktree
   separado, `aiadev install` no projeto de exemplo).
3. **Pares e ordem.** Um par é a mesma micro-feature nos dois braços. Alterne a
   ordem entre pares (par 1: antes primeiro; par 2: depois primeiro; ...) para
   não confundir braço com cache aquecido ou cansaço.
4. **Execução.** No Claude Code, pipeline completo do `specify` ao
   `finishing-a-branch`, mesmo modelo nos dois braços. Uma feature pode usar
   várias sessões: registre todas, entre o primeiro e o último commit.
5. **Registro por par.** Ids das sessões
   (`~/.claude/projects/<projeto>/<id>.jsonl`) e o `.review-log.jsonl` da
   feature, copiado para fora do projeto de exemplo.
6. **Custo.** Soma do custo equivalente (`aiadev.token_metrics`: sessão
   principal e subagentes) de todas as sessões do braço. O número é uma
   aproximação relativa, não faturamento.

## Arquivo de pares

JSON ou YAML; caminhos relativos resolvem a partir da pasta do arquivo, `~` e
caminhos absolutos são aceitos:

```json
[
  {
    "feature": "par-1",
    "before": {
      "sessions": ["~/.claude/projects/-tmp-exemplo/aaaa.jsonl"],
      "review_log": "runs/par-1-antes.review-log.jsonl"
    },
    "after": {
      "sessions": ["~/.claude/projects/-tmp-exemplo/bbbb.jsonl"],
      "review_log": "runs/par-1-depois.review-log.jsonl"
    }
  }
]
```

## Comandos

```bash
python3 scripts/benchmark_pairs.py pares.json            # texto
python3 scripts/benchmark_pairs.py pares.json --format json
python3 scripts/benchmark_pairs.py pares.json --allow-fewer   # exploratório
```

Saída: custo por feature, razão por par, mediana, aprovação de primeira por
braço, variação em pontos percentuais e o veredito. Código de saída: 0
`PASS`, 1 `FAIL`, 2 entrada inválida (inclui menos de 5 pares:
"insufficient pairs").

## Limites

- Uma micro-feature de 3 tasks pode subestimar o ganho de contexto acumulado
  em sessões longas (a reentrega de saída idêntica só aparece nelas); custo
  por feature e turnos são as métricas, nunca tokens salvos.
- Só Claude Code; Gemini, Codex, Cursor e OpenCode não são medidos.

## Resultado

Status: `pending` (preenchido pela T058: ids de sessão, custo por par,
mediana, aprovação de primeira, veredito e os comandos usados).
