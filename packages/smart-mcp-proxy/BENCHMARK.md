# smart-mcp-proxy — benchmark com Claude Code (headless)

Data: 2026-09-15. Agente: `claude-opus-5` via `claude -p` (Claude Code 2.1.220). Resumidor local: `qwen2.5-coder:3b` no Ollama 0.34 (Apple Silicon). Servidor na versão final (spec 0022: core compartilhado, assinaturas de erro com frame, cache de saída bruta, hook PreToolUse).

## Método

Cada caso roda o mesmo comando em três variantes, em sessões headless isoladas e sem outros MCP servers:

- **bash**: ferramenta Bash nativa do Claude Code, sem nada.
- **smart**: apenas a tool MCP `smart_bash_execute` deste pacote.
- **bash+hook**: Bash nativa com o hook `smart-bash-hook` registrado via `--settings`; o agente não sabe que o proxy existe.

O prompt pede para rodar o comando e responder em até 3 linhas se houve sucesso e qual o erro raiz com file:line. Acerto = a resposta final contém a string esperada do erro raiz (ou do resultado). Tokens de entrada = input + cache creation + cache read somados em todos os turnos; custo = `total_cost_usd` reportado pelo CLI. Uma repetição por caso e variante.

## Resultado por caso

| Caso | Variante | Turnos | Chars devolvidos pela tool | Tokens entrada | Custo | Latência | Acertou? |
| --- | --- | ---: | ---: | ---: | ---: | ---: | :---: |
| js-stack | bash | 2 | 10,039 | 16,079 | $0.1015 | 5.1 s | ✅ |
| js-stack | smart | 2 | 1,269 | 15,806 | $0.0664 | 6.8 s | ✅ |
| js-stack | bash+hook | 2 | 1,427 | 16,586 | $0.0542 | 8.8 s | ✅ |
| jest-fail | bash | 2 | 10,038 | 21,243 | $0.1011 | 6.2 s | ✅ |
| jest-fail | smart | 3 | 11,446 | 32,691 | $0.1220 | 11.1 s | ✅ |
| jest-fail | bash+hook | 2 | 892 | 17,003 | $0.0556 | 9.3 s | ✅ |
| py-trace | bash | 2 | 10,039 | 22,973 | $0.1187 | 5.6 s | ✅ |
| py-trace | smart | 2 | 1,072 | 15,808 | $0.0530 | 6.6 s | ✅ |
| py-trace | bash+hook | 2 | 1,230 | 16,579 | $0.0552 | 8.5 s | ✅ |
| build-ok | bash | 2 | 8,062 | 19,869 | $0.0862 | 5.1 s | ✅ |
| build-ok | smart | 2 | 463 | 15,498 | $0.0486 | 5.1 s | ✅ |
| build-ok | bash+hook | 2 | 601 | 16,255 | $0.0500 | 6.7 s | ✅ |
| pytest-real | bash | 2 | 10,040 | 25,041 | $0.0948 | 7.5 s | ✅ |
| pytest-real | smart | 2 | 2,750 | 16,466 | $0.0603 | 11.1 s | ✅ |
| pytest-real | bash+hook | 2 | 2,877 | 11,968 | $0.0607 | 11.0 s | ✅ |
| mdlint-real | bash | 2 | 10,040 | 29,992 | $0.0953 | 11.4 s | ✅ |
| mdlint-real | smart | 2 | 2,521 | 22,366 | $0.0635 | 16.9 s | ✅ |
| mdlint-real | bash+hook | 2 | 2,628 | 23,396 | $0.0613 | 16.5 s | ✅ |

## Descrição dos casos

- **js-stack**: 400 download-progress lines + JS TypeError stack (18 KB)
- **jest-fail**: 180 passing tests + 1 assertion failure (10 KB)
- **py-trace**: 360 pip-progress lines + Python KeyError traceback (20 KB)
- **build-ok**: 300 compile lines, build success, no errors (8 KB)
- **pytest-real**: real: repo pytest -v, 49 collection errors, ModuleNotFoundError aiadev (36 KB)
- **mdlint-real**: real: repo markdownlint, ~9.7k lint lines (1.4 MB)

## Agregado (6 casos)

| Métrica | bash | smart | bash+hook | Redução (hook vs bash) |
| --- | ---: | ---: | ---: | ---: |
| Turnos | 12 | 13 | 12 | |
| Chars devolvidos pela tool | 58,258 | 19,521 | 9,655 | 83% |
| Tokens de entrada | 135,197 | 118,635 | 101,787 | 25% |
| Custo | $0.5975 | $0.4138 | $0.3370 | 44% |
| Latência total | 41.0 s | 57.5 s | 60.8 s | -48% |
| Acertos | 6/6 | 6/6 | 6/6 | |

## Respostas finais do agente

**js-stack / bash**

> No — it failed (exit 1).
> 
> Root cause: `TypeError: Cannot read properties of undefined (reading "id")`, originating at `src/services/user.ts:42:18` in `getUser` (called from `src/routes/users.ts:17`).

**js-stack / smart**

> No — it failed (exit code 1).
> 
> Root cause: `TypeError: Cannot read properties of undefined (reading "id")`, originating at `src/services/user.ts:42` (in `getUser`, called from `src/routes/users.ts:17`).

**js-stack / bash+hook**

> No — it failed (exit code 1).
> 
> Root cause: `TypeError: Cannot read properties of undefined (reading "id")`, originating at `src/services/user.ts:42` in `getUser` (called from `src/routes/users.ts:17`).

**jest-fail / bash**

> No, it failed. One test failed: `test/auth.spec.ts › refreshes token when expired` — an assertion error `expect(received).toBe(expected)`, expected 200 but received 401.
> 
> Root cause originates at `test/auth.spec.ts:58:22` (180 other tests passed).

**jest-fail / smart**

> It failed (exit code 1): 1 test failed, 180 passed.
> 
> Root cause: assertion failure in `refreshes token when expired` — expected status `200` but received `401`, i.e. the refreshed token wasn't accepted.
> 
> Origin: `test/auth.spec.ts:58` (column 22); the log contains no deeper frame pointing into source code.

**jest-fail / bash+hook**

> It failed: 1 of 181 tests failed in `test/auth.spec.ts` ("refreshes token when expired").
> 
> Root cause: assertion `expect(received).toBe(expected)` got 401 instead of 200, at `test/auth.spec.ts:58:22`.
> 
> Caveat: the output was condensed (192 lines → error lines only), so an earlier cause upstream of the 401 may not be shown.

**py-trace / bash**

> It failed (exit 1).
> 
> Root cause: `KeyError: 'DJANGO_SECRET_KEY'` — the env var is unset, raised at `/app/config/settings.py:87` (`SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]`), surfacing via `os.py:685`.

**py-trace / smart**

> It failed (exit code 1).
> 
> Root cause: `KeyError: 'DJANGO_SECRET_KEY'` — the env var is unset, raised at `/app/config/settings.py:87` (`SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]`), reached from `manage.py:22`.

**py-trace / bash+hook**

> It failed (exit code 1, as the trailing `exit 1` forces).
> 
> Root cause: `KeyError: 'DJANGO_SECRET_KEY'` — the env var is unset, raised at `/app/config/settings.py:87` (`SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]`), entered from `manage.py:22`.

**build-ok / bash**

> Succeeded — no errors in the log.
> 
> Final result: build succeeded, 300 files compiled with 0 warnings, producing `dist/bundle.js` (412 kB).

**build-ok / smart**

> It succeeded — exit code 0, no errors.
> 
> Final result: build succeeded with 300 files compiled and 0 warnings, producing `dist/bundle.js` (412 kB).

**build-ok / bash+hook**

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

> No — it failed at collection: all 50 test files errored before any test ran (exit code 2).
> 
> Root cause: `ModuleNotFoundError: No module named 'aiadev'`, originating at `tests/test_agents_md_canonical.py:22` (same import failure in each of the 50 files).
> 
> The package isn't importable in this interpreter — likely needs an editable install (`pip install -e .`) or `PYTHONPATH`/`src` layout on the path.

**pytest-real / bash+hook**

> It failed — collection was interrupted with 49 errors, 0 tests run.
> 
> Root cause: `ModuleNotFoundError: No module named 'aiadev'`, first originating at `tests/test_agents_md_canonical.py:22` (same error in all 49 test modules).
> 
> The `aiadev` package isn't installed/importable in this Python environment — likely needs `pip install -e .`.

**mdlint-real / bash**

> No — exit code 1: markdownlint found 9757 issues across 495 of 1065 files (no crash; the failure is lint violations).
> 
> First/originating error: `.github/PULL_REQUEST_TEMPLATE.md:28:5` — MD060/table-column-style (pipe not aligned with header, style "aligned").
> 
> Notable: the `!node_modules/` glob only excludes the root, so nested `packages/*/node_modules/**/*.md` files are being linted and account for a large share of the count.

**mdlint-real / smart**

> No — it failed with exit code 1 (lint violations, not a crash).
> 
> Root cause: thousands of markdownlint rule violations, dominated by `MD007/ul-indent` in vendored files because the glob `**/*.md` scanned `vscode-extension/node_modules/` (first reported: `vscode-extension/node_modules/yauzl/README.md:657:1`); real source hits include `MD060/table-column-style` at `vscode-extension/README.md:53:9`.
> 
> Fix is to ignore `node_modules` (e.g. `'**/*.md' '!**/node_modules/**'` or an `ignores` entry in the markdownlint-cli2 config), then re-run to see only project errors.

**mdlint-real / bash+hook**

> No — it exited 1 with thousands of lint violations (no config/ignores, so it also linted `vscode-extension/node_modules`). There's no single crash; the failure is accumulated rule violations, the first reported being MD007/ul-indent at `vscode-extension/node_modules/yauzl/README.md:657`, with the tail showing MD060/table-column-style at `vscode-extension/README.md:60`.

## Achado colateral: custo dos MCP servers globais

O caso `js-stack` com Bash nativo, mas com os MCP servers globais da máquina carregados (Hostinger, Playwright, Stripe, Gmail, Calendar, Drive), como acontece numa sessão interativa normal:

| Variante | Tokens entrada | Custo |
| --- | ---: | ---: |
| bash (sem MCP globais) | 16,079 | $0.1015 |
| bash + MCP globais | 191,940 | $0.2181 |

As definições de tool desses servidores custam mais tokens por turno do que qualquer saída de comando. Esse custo independe do proxy e se resolve desligando servidores não usados ou com `--strict-mcp-config`.

## Conclusões

- **O hook é o caminho.** Com o `smart-bash-hook` registrado, a ferramenta Bash nativa devolve 83% menos caracteres, custa 44% menos por sessão e acerta 6/6 erros raiz em 2 turnos, sem que o agente saiba que o proxy existe. A variante MCP (`smart_bash_execute`) economiza menos (13 turnos contra 12) porque em uma execução o agente resolveu "confirmar" no bruto; o hook não dá essa opção e por isso é mais previsível.
- **Qualidade**: 6/6 nas três variantes. Nas duas com condensação, o agente respondeu o erro raiz com file:line a partir do resultado condensado.
- **Economia real por chamada é maior que o agregado sugere**: o Bash nativo do Claude Code já trunca em ~10 KB. Contra a saída completa (36 KB do pytest, 1,4 MB do markdownlint) a diferença é de uma a duas ordens de grandeza. Numa sessão interativa longa, a saída bruta fica no contexto em todos os turnos seguintes, então a economia acumulada favorece ainda mais o proxy.
- **Performance**: o resumo custa de 1 a 5 segundos por chamada longa no `qwen2.5-coder:3b` em Apple Silicon; a latência total das sessões subiu ~50%. Comandos curtos (abaixo de 2000 chars) não pagam nada porque nunca passam pelo Ollama.
- **O que realmente funcionou** não foi o modelo local sozinho. Ele extrai bem quando o erro está isolado e falha em saídas repetitivas (49 tracebacks iguais viram uma lista de nomes de arquivo). As garantias vieram de três blocos determinísticos que o servidor anexa sempre: `ERROR SIGNATURES` (grep de linhas de erro com contagem e o frame de projeto mais próximo), `RAW TAIL` (últimas 8 linhas verbatim) e a guarda que devolve trecho truncado quando o resumo não encolhe.
- **Comportamento do agente**: anunciar um atalho barato para a saída bruta no cabeçalho fez o Opus 5 usá-lo em 100% das vezes (rodadas intermediárias, ver histórico abaixo). O cabeçalho final é neutro e o `raw_id` vive só na descrição da tool como último recurso.

## Histórico de iterações do servidor

O servidor passou por cinco versões durante o benchmark, cada uma corrigindo um problema que o teste com o Claude real expôs. Casos `jest-fail` e `pytest-real`, variante MCP:

| Versão | O que mudou | jest-fail | pytest-real |
| --- | --- | --- | --- |
| v1 | prompt de extração verbatim + cauda bruta | 3 turnos, $0,1178 | 3 turnos, $0,1157 (o modelo omitiu o `ModuleNotFoundError`; o agente re-executou com `force_raw`) |
| v2 | + `ERROR SIGNATURES` determinístico | 3 turnos, $0,1196 | 2 turnos, $0,0596 |
| v3 | + cache de saída bruta anunciado no cabeçalho (`raw_id`) | 3 turnos em 2/2 | 3 turnos em 2/2, $0,1808 (o agente passou a buscar o bruto sempre) |
| v4 | cabeçalho neutro, `raw_id` só na descrição da tool | 3 e 2 turnos | 3 turnos em 2/2 (faltava o file:line no resumo) |
| v5 | + frame de projeto em cada assinatura (`↳ at tests/x.py:22`) | 2 turnos em 2/2 | 2 turnos em 2/2, $0,0594 |
| v6 (0.2.1) | guarda de envelope: se o condensado não for menor que o bruto, entrega o bruto; eco do comando limitado a 80 chars | sem mudança | sem mudança |

A rodada final acima usa a v5 fatorada (spec 0022: `core.ts` compartilhado por MCP, CLI e hook). A v6 veio de uso real, não do benchmark: numa sessão de trabalho com o hook ativo, 2 das 7 saídas condensadas ficaram *maiores* que o original (2.087 → 2.278 chars; 3.060 → 3.067), porque listagens de `grep` pouco acima do orçamento não têm o que resumir e o envelope (eco do comando encadeado de 400+ chars, cabeçalho, RAW TAIL) pesava mais que o conteúdo. Nas outras 5, a redução foi de 55% no agregado (29.063 → 12.957 chars), com latência mediana de 6,2 s por chamada condensada contra 2,2 s crua.

## Ressalvas

- Uma repetição por caso e variante. Os tokens variam alguns por cento entre execuções por conta da contabilidade de cache; o custo é a métrica mais estável.
- Sessões headless de um comando só. Acerto medido por substring na resposta final, não por revisão humana; as respostas completas estão na seção acima.
- Um único modelo local, pequeno, e um único agente. O reflexo de "confirmar no bruto" é comportamento do Opus 5 neste prompt.

## Reproduzir

Os scripts do benchmark (`bench.mjs`, `report2.mjs`) rodam `claude -p` com `--output-format stream-json` e ficam fora do repositório. Requisitos: Claude Code CLI autenticado, Ollama com `qwen2.5-coder:3b`, `npm run build` neste pacote e, para a variante hook, um `settings.json` com o snippet de `presets/token-economy/hooks/`. Cada rodada completa custa cerca de US$ 1 em API.
