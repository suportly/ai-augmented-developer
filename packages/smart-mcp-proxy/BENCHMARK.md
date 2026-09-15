# smart-mcp-proxy — benchmark com Claude Code (headless)

Data: 2026-09-15. Agente: `claude-opus-5` via `claude -p` (Claude Code 2.1.220). Resumidor local: `qwen2.5-coder:3b` no Ollama 0.34 (Apple Silicon).

## Método

Cada caso roda o mesmo comando duas vezes, em sessões headless isoladas e sem outros MCP servers:

- **bash**: ferramenta Bash nativa do Claude Code.
- **smart**: apenas a tool `smart_bash_execute` deste pacote, com limite de 2000 chars antes de resumir.

O prompt pede para rodar o comando e responder em até 3 linhas se houve sucesso e qual o erro raiz com file:line. Acerto = a resposta final contém a string esperada do erro raiz (ou do resultado). Tokens de entrada = input + cache creation + cache read somados em todos os turnos; custo = `total_cost_usd` reportado pelo CLI.

## Resultado por caso

| Caso | Variante | Chars devolvidos pela tool | Tokens entrada | Custo | Latência total | Acertou? |
| --- | --- | ---: | ---: | ---: | ---: | :---: |
| js-stack | bash | 10,039 | 16,079 | $0.1015 | 5.1 s | ✅ |
| js-stack | bash+globalmcp | 10,039 | 191,940 | $0.2181 | 7.9 s | ✅ |
| js-stack | smart | 1,103 | 19,352 | $0.0524 | 6.9 s | ✅ |
| jest-fail | bash | 10,038 | 21,243 | $0.1011 | 6.2 s | ✅ |
| jest-fail | smart | 734 | 19,726 | $0.0586 | 13.6 s | ✅ |
| jest-fail | smart+rule | 734 | 10,073 | $0.0618 | 6.1 s | ✅ |
| py-trace | bash | 10,039 | 22,973 | $0.1187 | 5.6 s | ✅ |
| py-trace | smart | 812 | 14,135 | $0.0526 | 9.5 s | ✅ |
| build-ok | bash | 8,062 | 19,869 | $0.0862 | 5.1 s | ✅ |
| build-ok | smart | 505 | 13,971 | $0.0481 | 6.4 s | ✅ |
| pytest-real | bash | 10,040 | 25,041 | $0.0948 | 7.5 s | ✅ |
| pytest-real | smart | 2,775 | 15,364 | $0.0594 | 11.4 s | ✅ |
| pytest-real | smart+rule | 2,775 | 10,959 | $0.0599 | 10.9 s | ✅ |
| mdlint-real | bash | 10,040 | 29,992 | $0.0953 | 11.4 s | ✅ |
| mdlint-real | smart | 2,563 | 20,326 | $0.0612 | 16.4 s | ✅ |

## Descrição dos casos

- **js-stack**: 400 download-progress lines + JS TypeError stack (18 KB)
- **jest-fail**: 180 passing tests + 1 assertion failure (10 KB)
- **py-trace**: 360 pip-progress lines + Python KeyError traceback (20 KB)
- **build-ok**: 300 compile lines, build success, no errors (8 KB)
- **pytest-real**: real: repo pytest -v, 49 collection errors, ModuleNotFoundError aiadev (36 KB)
- **mdlint-real**: real: repo markdownlint, ~9.7k lint lines (1.4 MB)

## Agregado (6 casos)

| Métrica | bash | smart | Redução |
| --- | ---: | ---: | ---: |
| Chars devolvidos pela tool | 58,258 | 8,492 | 85% |
| Tokens de entrada | 135,197 | 102,874 | 24% |
| Custo | $0.5975 | $0.3324 | 44% |
| Latência total | 41.0 s | 64.2 s | -57% |
| Acertos | 6/6 | 6/6 | |

Nos 2 casos em que a variante **smart + regra** foi medida (os dois casos difíceis):

| Métrica | bash | smart | smart + regra |
| --- | ---: | ---: | ---: |
| Turnos | 4 | 4 | 4 |
| Chars devolvidos pela tool | 20,078 | 3,509 | 3,509 |
| Tokens de entrada | 46,284 | 35,090 | 21,032 |
| Custo | $0.1958 | $0.1180 | $0.1217 |
| Acertos | 2/2 | 2/2 | 2/2 |

## Respostas finais do agente

**js-stack / bash**

> No — it failed (exit 1).
> 
> Root cause: `TypeError: Cannot read properties of undefined (reading "id")`, originating at `src/services/user.ts:42:18` in `getUser` (called from `src/routes/users.ts:17`).

**js-stack / bash+globalmcp**

> No, it failed (exit code 1). Root cause: `TypeError: Cannot read properties of undefined (reading "id")`, originating at `src/services/user.ts:42:18` in `getUser`, called from `src/routes/users.ts:17:5`.

**js-stack / smart**

> No, it failed (exit code 1).
> 
> Root cause: `TypeError: Cannot read properties of undefined (reading "id")`, originating at `src/services/user.ts:42` (in `getUser`, called from `src/routes/users.ts:17`).

**jest-fail / bash**

> No, it failed. One test failed: `test/auth.spec.ts › refreshes token when expired` — an assertion error `expect(received).toBe(expected)`, expected 200 but received 401.
> 
> Root cause originates at `test/auth.spec.ts:58:22` (180 other tests passed).

**jest-fail / smart**

> It failed (exit code 1): 1 of 181 tests failed.
> 
> Root cause: assertion failure in "refreshes token when expired" — expected 200, received 401 (token refresh not returning an authorized response).
> 
> Origin: `test/auth.spec.ts:58` (col 22).

**jest-fail / smart+rule**

> It failed: 1 test failed of 181 (`refreshes token when expired`).
> 
> Root cause: the assertion `expect(received).toBe(200)` got 401 — expired-token refresh isn't returning a valid session.
> 
> Origin: `test/auth.spec.ts:58`.

**py-trace / bash**

> It failed (exit 1).
> 
> Root cause: `KeyError: 'DJANGO_SECRET_KEY'` — the env var is unset, raised at `/app/config/settings.py:87` (`SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]`), surfacing via `os.py:685`.

**py-trace / smart**

> It failed (exit code 1).
> 
> Root cause: `KeyError: 'DJANGO_SECRET_KEY'` — the `DJANGO_SECRET_KEY` env var is unset, originating at `/app/config/settings.py:87` (`SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]`).
> 
> Note: the ~360 lines of output were condensed by the tool, so the summarized traceback above is what I saw; the verbatim tail matches it.

**build-ok / bash**

> Succeeded — no errors in the log.
> 
> Final result: build succeeded, 300 files compiled with 0 warnings, producing `dist/bundle.js` (412 kB).

**build-ok / smart**

> It succeeded (exit code 0).
> 
> Final result: build succeeded — 300 files compiled, 0 warnings, output `dist/bundle.js` (412 kB).

**pytest-real / bash**

> Failed — collection aborted with exit code 2: 392 tests collected but 49 errors, zero tests run.
> 
> Root cause: `ModuleNotFoundError: No module named 'aiadev'` — the package isn't installed/importable in this interpreter (Python 3.14.7); first occurrence at `tests/test_agents_md_canonical.py:22`.
> 
> Likely fix (not run, per your instruction): `python3 -m pip install -e .` in that repo.

**pytest-real / smart**

> It failed — collection was interrupted with 49 errors, 0 tests run.
> 
> Root cause: `ModuleNotFoundError: No module named 'aiadev'`, first raised at `tests/test_agents_md_canonical.py:22` (same import failure in all 49 test files).
> 
> Fix is to install the package into the environment (e.g. `pip install -e .`) so `aiadev` is importable.

**pytest-real / smart+rule**

> No — it failed at collection: 49 errors, 0 tests run (exit code 2).
> 
> Root cause: `ModuleNotFoundError: No module named 'aiadev'`, first raised at `tests/test_agents_md_canonical.py:22` and identically in all 49 test modules — the `aiadev` package isn't installed/importable in this environment.

**mdlint-real / bash**

> No — exit code 1: markdownlint found 9757 issues across 495 of 1065 files (no crash; the failure is lint violations).
> 
> First/originating error: `.github/PULL_REQUEST_TEMPLATE.md:28:5` — MD060/table-column-style (pipe not aligned with header, style "aligned").
> 
> Notable: the `!node_modules/` glob only excludes the root, so nested `packages/*/node_modules/**/*.md` files are being linted and account for a large share of the count.

**mdlint-real / smart**

> No — it exited 1 with thousands of style violations (~9.7k lines of output), not a crash. There's no single root cause: the glob `**/*.md` swept in `vscode-extension/node_modules/**`, so most errors are vendored docs, e.g. `vscode-extension/node_modules/yauzl/README.md:657` MD007/ul-indent; real project files also fail, e.g. `vscode-extension/README.md:53` MD060/table-column-style.
> 
> Note the output was condensed by the proxy, so those are representative first/last entries, not a guaranteed complete picture.

## Iterações do servidor durante o benchmark

Dois casos revelaram problemas na primeira rodada e o servidor foi corrigido entre rodadas. Histórico das execuções da variante smart nesses casos:

| Caso | Versão do servidor | Turnos | Chars devolvidos | Tokens entrada | Custo | Acertou? |
| --- | --- | ---: | ---: | ---: | ---: | :---: |
| jest-fail | v1: prompt+tail | 3 | 10,581 | 29,566 | $0.1178 | ✅ |
| pytest-real | v1: prompt+tail | 3 | 12,430 | 36,953 | $0.1157 | ✅ |
| jest-fail | v2: +error signatures | 3 | 10,718 | 34,763 | $0.1196 | ✅ |
| pytest-real | v2: +error signatures | 2 | 2,705 | 14,895 | $0.0596 | ✅ |
| jest-fail | v3: +raw cache/header | 3 | 11,549 | 30,910 | $0.1279 | ✅ |
| jest-fail | v3: +raw cache/header (rep 2) | 3 | 11,549 | 31,001 | $0.1207 | ✅ |
| pytest-real | v3: +raw cache/header | 3 | 27,057 | 39,046 | $0.1808 | ✅ |
| pytest-real | v3: +raw cache/header (rep 2) | 3 | 27,057 | 39,062 | $0.1807 | ✅ |
| jest-fail | v4: neutral header | 3 | 11,416 | 30,840 | $0.1309 | ✅ |
| jest-fail | v4: neutral header (rep 2) | 2 | 704 | 19,692 | $0.0595 | ✅ |
| pytest-real | v4: neutral header | 3 | 14,924 | 33,315 | $0.1242 | ✅ |
| pytest-real | v4: neutral header (rep 2) | 3 | 14,924 | 33,361 | $0.1250 | ✅ |
| jest-fail | v5: +frames on signatures | 2 | 734 | 19,726 | $0.0586 | ✅ |
| jest-fail | v5: +frames on signatures + regra | 2 | 734 | 10,073 | $0.0618 | ✅ |
| jest-fail | v5: +frames on signatures (rep 2) | 2 | 734 | 19,722 | $0.0584 | ✅ |
| jest-fail | v5: +frames on signatures + regra (rep 2) | 2 | 734 | 14,885 | $0.0515 | ✅ |
| pytest-real | v5: +frames on signatures | 2 | 2,775 | 15,364 | $0.0594 | ✅ |
| pytest-real | v5: +frames on signatures + regra | 2 | 2,775 | 10,959 | $0.0599 | ✅ |
| pytest-real | v5: +frames on signatures (rep 2) | 2 | 2,775 | 15,391 | $0.0591 | ✅ |
| pytest-real | v5: +frames on signatures + regra (rep 2) | 2 | 2,775 | 10,965 | $0.0603 | ✅ |

- **v1 → v2**: no pytest real, o `qwen2.5-coder:3b` listou os 49 módulos com `ERROR` e omitiu o `ModuleNotFoundError`. O agente percebeu, chamou de novo com `force_raw=true` (re-executando o pytest) e acertou, mas o turno extra anulou a economia. Correção: bloco `ERROR SIGNATURES`, um grep determinístico de linhas de erro deduplicadas com contagem, anexado sempre.
- **v2 → v3**: no jest, o agente às vezes re-executava para "confirmar" porque o cabeçalho dizia apenas "condensed", e na v2 o contador "2 distinct" (✕ e ● da mesma falha) pareceu indicar duas falhas. Correção: cabeçalho explica que as linhas de erro são verbatim e que há blocos determinísticos, e a saída bruta fica em cache com `raw_id` para consulta sem re-executar o comando.
- **v3 → v4**: anunciar o `raw_id` no cabeçalho de toda resposta teve efeito inverso: com a busca do bruto barata e visível, o agente passou a fazê-la em 4 de 4 execuções. Correção: cabeçalho mínimo e neutro, `raw_id` documentado só na descrição da tool como último recurso, e retorno do cache limitado a 12 KB.
- **v4 → v5**: ainda assim o agente buscava o bruto no pytest, e com razão: o prompt exige file:line e o resumo trazia `ModuleNotFoundError ×49` sem a linha do frame. Correção determinística: cada assinatura ganha o frame de projeto mais próximo (`↳ at tests/x.py:22`), ignorando node_modules/site-packages. A variante **+ regra** adiciona ao system prompt do consumidor uma instrução para tratar o resultado condensado como suficiente, o que é o que um `.claude/rules/` do framework faria.

## Achado colateral: custo dos MCP servers globais

O mesmo caso `js-stack` com Bash nativo, mas com os MCP servers globais da máquina carregados (Hostinger, Playwright, Stripe, Gmail, Calendar, Drive), como acontece numa sessão interativa normal:

| Variante | Tokens entrada | Custo |
| --- | ---: | ---: |
| bash (sem MCP globais) | 16,079 | $0.1015 |
| bash + MCP globais | 191,940 | $0.2181 |

As definições de tool desses servidores custam mais tokens por turno do que qualquer saída de comando. Esse custo independe do proxy e se resolve desligando servidores não usados ou com `--strict-mcp-config`.

## Conclusões

- **Qualidade**: 6/6 acertos nas duas variantes. Com a versão final do servidor (v5), o agente respondeu o erro raiz com file:line a partir do resultado condensado em todos os casos, sem pedir a saída bruta.
- **Economia**: 85% menos caracteres devolvidos pela tool, 24% menos tokens de entrada e 44% menos custo no agregado dos 6 casos. A economia real por chamada é maior do que o agregado sugere, porque o Bash nativo do Claude Code já trunca a saída em ~10 KB; contra a saída completa (36 KB do pytest, 1.4 MB do markdownlint) a diferença seria de uma a duas ordens de grandeza.
- **Performance**: o resumo custa de 1 a 5 segundos de latência por chamada longa no `qwen2.5-coder:3b` em Apple Silicon. A latência total das sessões smart foi 57% maior. É o preço do contexto limpo; comandos curtos (abaixo de 2000 chars) não pagam nada.
- **O que realmente funcionou**: não foi o modelo local sozinho. O modelo 3B extrai bem quando o erro está isolado, mas em saídas repetitivas (49 tracebacks iguais) ele lista nomes de arquivos e perde a exceção. As garantias vieram de três blocos determinísticos que o servidor anexa sempre: `ERROR SIGNATURES` (grep de linhas de erro com contagem e frame de projeto mais próximo), `RAW TAIL` (últimas 8 linhas verbatim) e a guarda que devolve trecho truncado quando o resumo não encolhe.
- **Comportamento do agente**: anunciar um atalho barato para a saída bruta no cabeçalho fez o Opus 5 usá-lo em 100% das vezes (v3/v4). O cabeçalho final é neutro e o `raw_id` vive só na descrição da tool como último recurso.

## Ressalvas

- Uma repetição por caso na rodada principal (duas nas rodadas de correção). Os números de tokens variam alguns por cento entre execuções por conta da contabilidade de cache; o custo é a métrica mais estável.
- Sessões headless com um único comando por sessão. Numa sessão interativa longa, a saída bruta fica no contexto por todos os turnos seguintes, então a economia acumulada favorece ainda mais o proxy.
- O acerto foi medido por substring na resposta final, não por revisão humana. As respostas completas estão na seção acima.
- Modelo local pequeno e único. Um modelo de 7B ou mais deve extrair melhor, ao custo de latência; o servidor aceita qualquer modelo via `OLLAMA_MODEL`.

## Reproduzir

Os scripts do benchmark (`bench.mjs`, `report.mjs`) rodam `claude -p` com `--output-format stream-json` e ficam fora do repositório. Requisitos: Claude Code CLI autenticado, Ollama com `qwen2.5-coder:3b`, e `npm run build` neste pacote. Cada rodada completa custa cerca de US$ 1 em API.
