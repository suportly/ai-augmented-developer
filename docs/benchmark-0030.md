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

Executado em 2026-10-14, no Claude Code 2.1.291 (modelo `sonnet`, que resolveu
para `claude-sonnet-5-5` nos dois braços), com `claude -p` real: 20 sessões,
10 pares, 2 rodadas. Braço **antes** = framework em `cc072ef` (pré-0030);
braço **depois** = `03bf8b1`. Projeto de exemplo `hello-cli` limpo por
execução, preset `lean`, mesma demanda ([`microfeature.md`](./benchmark-0030/microfeature.md)),
sessões com `--setting-sources project,local` e `--strict-mcp-config` (sem
plugins nem MCP do usuário), `--max-budget-usd 8` por sessão.

### Veredito pela regra da spec

| Rodada | Pares | Mediana depois/antes (regra < 1,0) | Aprovação de 1ª antes → depois (regra ≥ −5 pp) | Veredito |
|---|---|---|---|---|
| 1 — decomposição livre | 1–5 | **1,1704** | 85,7% → 100% (+14,3 pp) | **FAIL** |
| 2 — decomposição fixa em 3 tasks | 6–10 | **0,8510** | 80,0% → 100% (+20,0 pp) | **PASS** |

Os dois veredictos valem como foram: a regra foi fixada antes da execução,
cada rodada é avaliada isoladamente e nenhuma foi descartada. A rodada 2 foi
feita **depois** de ver a rodada 1 e existe por causa dela, então não é
confirmação independente.

### Por que há duas rodadas

Na rodada 1 o prompt deixava o agente decidir quantas tasks criar. Isso virou
a variável dominante: o par 2 (depois) fez 4 tasks contra 2 do antes, e o par 5
(depois) fez 2 contra 4 do antes, com razões 2,03 e 0,26. A razão por par
variou de 0,26 a 2,03, e o custo médio em USD ficou praticamente igual entre os
braços (1,17 antes, 1,19 depois). Para isolar o efeito das instruções, a
rodada 2 repetiu o protocolo com a decomposição fixa no prompt (as 3 tasks da
micro-feature). A mediana pooled das 10 razões é 0,865, descritiva apenas.

### Dados por par

| Rodada | Par | 1º braço | Antes (eq.) | Depois (eq.) | Razão | USD antes | USD depois | Sessão antes | Sessão depois |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 1 | antes | 939,992.45 | 554,448.45 | 0.5898 | 1.66 | 1.11 | `e2ac711b` | `811559db` |
| 1 | 2 | depois | 355,057.70 | 719,661.80 | 2.0269 | 0.71 | 1.44 | `8d7fa50b` | `3dd90944` |
| 1 | 3 | antes | 493,139.40 | 707,606.35 | 1.4349 | 0.99 | 1.42 | `4323b113` | `08a3aff2` |
| 1 | 4 | depois | 684,254.05 | 800,830.45 | 1.1704 | 1.19 | 1.60 | `7a8c37fa` | `b455c368` |
| 1 | 5 | antes | 755,955.95 | 197,642.25 | 0.2614 | 1.29 | 0.40 | `c721edb9` | `b0f37519` |
| 2 | 6 | depois | 718,572.90 | 691,464.30 | 0.9623 | 1.44 | 1.38 | `12c2b463` | `4fe5c0d9` |
| 2 | 7 | antes | 617,935.95 | 454,237.50 | 0.7351 | 1.24 | 0.91 | `b716dbf2` | `f04573f4` |
| 2 | 8 | depois | 569,191.70 | 484,356.50 | 0.8510 | 1.14 | 0.97 | `41c33d86` | `00c14a15` |
| 2 | 9 | antes | 757,050.90 | 368,449.05 | 0.4867 | 1.52 | 0.74 | `7f7f3d84` | `743c2b15` |
| 2 | 10 | depois | 417,591.50 | 368,025.75 | 0.8813 | 0.84 | 0.74 | `607613c6` | `72f00b55` |

"Eq." é o custo equivalente de `aiadev.token_metrics` (sessão principal e
subagentes, pesos documentados); USD é o `total_cost_usd` reportado pelo
próprio `claude -p`. Pares ímpares rodaram com o braço **antes** primeiro, os
pares pares com **depois** primeiro; dois pares rodaram em paralelo por rodada.
Arquivos por execução em [`benchmark-0030/runs/`](./benchmark-0030/runs/) (meta,
verificação e review-log derivado); pares em `benchmark-0030/pares-r1.json` e
`pares-r2.json`; prompts em `prompt-r1.txt` e `prompt-r2.txt`.

### Verificação funcional (testes reais)

Nas 20 execuções: `pytest` do projeto verde, `greet World` imprime
`Hello, World!`, `--shout` imprime `HELLO, WORLD!`, `greet` sem NAME sai com
2 e a mensagem de uso, `review.yaml` aprovado, árvore limpa, branch
`feature/greet` com a linha de specs, plano, tasks e um commit por task. Os
dois braços chegaram ao fim do pipeline sem intervenção.

### Comandos usados

```bash
# por execução (docs/benchmark-0030/run_arm.py, mkproj.sh, verify.py)
python3 run_arm.py <before|after> <par>
python3 verify.py runs/par-<n>-<arm>
python3 derive_log.py runs/par-<n>-<arm>
# veredito
python3 scripts/benchmark_pairs.py docs/benchmark-0030/pares-r1.json
python3 scripts/benchmark_pairs.py docs/benchmark-0030/pares-r2.json
```

### Limites e ressalvas (leia antes de citar o número)

- **O review-log real quase não foi escrito em nenhum braço** (no máximo uma
  entrada por execução, quase sempre a do review de branch). A aprovação de
  primeira acima vem de um review-log **derivado** dos transcripts dos
  subagentes `code-reviewer` (veredito da última mensagem de cada um, `task_id`
  pela descrição do dispatch), pelo mesmo método nos dois braços. É um proxy
  da métrica de `aiadev metrics`, não a métrica gravada. Achado à parte: o
  passo que grava o review-log por task não é seguido de forma confiável.
- **Aprovação de primeira em 100% no braço depois** significa que nenhum
  reviewer pediu mudanças nas 5+5 execuções do braço, o que também é
  compatível com um reviewer mais permissivo: este benchmark não separa as
  duas hipóteses (não há defeitos plantados).
- n = 5 por rodada, uma micro-feature de 3 tasks, um modelo, uma máquina.
  A variância entre pares é grande (razão de 0,26 a 2,03 na rodada 1). A
  mediana da rodada 2 é menor que 1,0, mas o intervalo entre pares (0,49 a
  0,96) não permite cravar a magnitude.
- Em sessões curtas o texto de instrução é ~1–3% do contexto; o ganho de
  turnos de sessões longas (`aiadev tasks done`, preflight JSON) aparece pouco
  aqui. Custo por feature é a métrica; "tokens economizados" não é afirmado.
- Só Claude Code. Nada foi medido em Gemini, Codex, Cursor ou OpenCode.
- Reversão para dois reviewers: **não recomendada** — nenhuma das duas rodadas
  mostrou queda de aprovação de primeira, e dois reviewers aumentariam o custo.
