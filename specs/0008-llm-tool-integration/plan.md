# Implementation plan: aiadev como ferramenta de LLM

> Produzido pelo skill `plan` a partir de [spec.md](./spec.md) aprovado.
> Descreve **como** a spec será realizada — não duplicar o spec aqui.

**Branch:** `feature/llm-tool-integration`
**Date:** 2026-04-16
**Spec:** [spec.md](./spec.md)
**Plan version:** 1
**Language:** pt-BR <!-- espelha o spec; toda prosa deste plan em pt-BR. -->

---

## Summary

Vamos expor os 8 skills do pipeline (`specify`, `clarify`, `plan`, `tasks`, `implement`, `analyze`, `checklist`, `constitution`) como tools invocáveis por LLM em **dois transportes que compartilham o mesmo core**: um servidor MCP em modo stdio (`python -m aiadev.mcp_server`) e uma biblioteca Python in-process (`aiadev.tools`). Ambos seguem o modelo **skill-as-prompt-loader**: o handler valida `workspace_path`, calcula `target_path`, monta um payload estruturado contendo `SKILL.md` + template + contexto + path computado, e devolve ao caller — que é responsável por seguir as instruções com seus próprios tools de filesystem. Como pré-requisito mecânico, o formato de marcador `[NEEDS CLARIFICATION: ...]` é alterado em todo o framework para `[NEEDS CLARIFICATION:cl-N ...]` (id estável). Trabalho dividido em **5 fases** (~28 tasks projetadas) tocando `src/aiadev/`, `templates/`, `skills/specify`, `skills/clarify`, `pyproject.toml`, `schemas/`, `tests/` e `README.md`.

## Technical context

| Field | Value |
|---|---|
| Active preset | `lean` (do próprio `installed.yaml` deste repo) |
| Language / runtime | Python 3.11+ (alinhado a `pyproject.toml`) |
| Primary dependencies | `click`, `pyyaml`, `jsonschema`, `rich` (já existentes); **novas:** `mcp>=1.0` como **optional extra** `[mcp]`, e `pytest-asyncio>=0.23` em `[dev]` para testar handlers MCP assíncronos |
| Storage | N/A — sem persistência; o servidor lê assets bundled via `paths.find_framework_root` e a lib opera sobre o filesystem do consumidor |
| Testing framework | `pytest` (já configurado em `[tool.pytest.ini_options]`) |
| Target platform(s) | Linux e macOS (mesmas plataformas suportadas pelo CI atual). Windows nativo fora do escopo do v1 — não temos infra de teste. |
| Performance budget | Latência por invocação ≤ 50ms p95 (handler puro: leitura de SKILL.md + template + montagem do payload, sem rede e sem LLM). Logs JSON ≤ 200 bytes/linha. |
| Security considerations | Validação estrita de `workspace_path` (rejeitar `..`, links simbólicos que escapem, paths inexistentes). Telemetria nunca contém `demand` nem payload livre (Article VI). Sem credenciais LLM no servidor MCP. |

## Constitution check

> Uma linha por artigo aplicável de `constitution.md`. `N/A` permitido quando o
> artigo não se aplica. Todo `FAIL` precisa de linha em **Complexity tracking**.

| Article | Applies? | Status | Evidence |
|---|---|---|---|
| I. Spec-first | Yes | PASS | [spec.md](./spec.md) aprovado pelo `spec-document-reviewer` em 2026-04-16; zero marcadores remanescentes (resolvidos via `clarify`). |
| II. Test-first | Yes | PASS | Tasks 1-N começam por `tests/test_*.py` (red) antes de tocar `src/aiadev/`. Ver Phase breakdown — cada fase é um ciclo red→green→refactor. |
| III. Simplicity | Yes | PASS | Cada sub-módulo de `aiadev._tooling` tem **dois callers declarados hoje** (`aiadev.mcp_server` e `aiadev.tools`): `workspace` (validação + cálculo de `target_path`), `skill_loader` (monta `context.template` + `context.constitution_excerpt`), `markers` (geração de `cl-N` e enumeração de `existing_markers`), `payload` (montagem final do `ToolPayload`), `telemetry` (logger JSON-lines consumido por ambos). **Consolidação:** `errors` não é sub-módulo — as exceções ficam em `aiadev/_tooling/__init__.py` (<30 linhas). Skills auxiliares (`systematic-debugging`, `test-driven-development`, `frontend-design`, `requesting-code-review`, `finishing-a-branch`) e preset-specific **não** entram — sem segundo caller hoje. |
| IV. Evidence over claims | Yes | PASS | PR final lista comandos exatos (`pytest tests/test_mcp_server.py`, `python -m aiadev.mcp_server` com fixture, `pip install -e '.[mcp,dev]'`) e cola a saída de `pytest -ra` no body. **Nota sobre ADR 5 (escolha `prompts/get` vs `tools/call`):** a preferência por `prompts/get` é uma judgment call, não obviedade — a evidência é o teste de contrato `test_mcp_server.py::test_both_primitives_return_same_payload`, que prova que quem escolher errado ainda recebe a mesma estrutura. |
| V. Provider pattern | Yes | PASS | LLM externo é o caller (não consumimos LLM). Para testes E2E (Story 1 cenário 2), criamos `tests/_fakes/llm.py` que executa o prompt deterministicamente; nenhuma chamada real a Anthropic/LiteLLM nos testes. SDK `mcp` é um boundary externo encapsulado em `aiadev.mcp_server.transport`. |
| VI. Privacy by design | Yes | PASS | Logger em `aiadev._tooling.telemetry` aplica allowlist de campos (`{ts, tool, workspace_path, latency_ms, status, error_code}`); teste `tests/test_telemetry.py` afirma que `demand` e qualquer payload livre nunca aparecem em stderr. |
| VII. Attribution | Yes | PASS | Sem material adaptado de outros projetos. SDK `mcp` consumido como dependência declarada (não fork). `CREDITS.md` não muda. |
| Preset-specific articles | N/A — preset `lean` não define artigos próprios além dos 7 da framework. | N/A | — |

## Architecture decisions

**ADR 1 — Namespace do servidor MCP: `aiadev.mcp_server`, não `aiadev.mcp`.**
*Rationale:* `src/aiadev/mcp.py` já existe (loader de `mcps.yaml` consumido por `framework_artifacts.py` e `tests/test_mcp.py`). Renomear quebraria 2 imports + asset bundling. Coexistir com prefixo `_server` é zero-risk.
*Trade-offs:* nome ligeiramente mais longo; ambíguo para humanos lendo o tree (mitigado por docstrings).

**ADR 2 — `mcp` SDK como optional extra `[mcp]`, não core.**
*Rationale:* CLI de uso comum (`aiadev init`, `aiadev sync`, `aiadev validate`) não precisa do SDK. Tornar opcional mantém install lean para 80% dos usuários.
*Trade-offs:* usuário do servidor precisa de `pip install 'aiadev[mcp]'`; o entrypoint `aiadev mcp-server` (ou `python -m aiadev.mcp_server`) deve falhar com mensagem útil se `mcp` não estiver instalado.

**ADR 3 — Core compartilhado em `aiadev._tooling`, não duplicado entre servidor e lib.**
*Rationale:* Skill loader, validação de workspace, cálculo de slug/`NNNN`, geração de id `cl-N` e montagem de payload são idênticos para os dois transportes. Manter num único módulo evita drift e deixa o código de transporte fino.
*Trade-offs:* nome com underscore sinaliza "interno"; consumidores que importarem direto perdem garantia de estabilidade — aceitável (lib pública é `aiadev.tools`, servidor é `aiadev.mcp_server`).

**ADR 4 — Marcador estampa id na criação, não no momento de leitura.**
*Rationale:* a opção A do clarify pede "id estável atribuído pelo `specify`". Estampar na leitura geraria ids voláteis (mudam quando o spec é editado por humano). Estampar na criação requer mudança no template e nos skills `specify`/`clarify`, mas é a única que cumpre "estável".
*Trade-offs:* migração de marcadores existentes em outros specs (decisão: deixar como estão; aplicar só em specs novos — ver Risks).

**ADR 5 — Payload de saída: usar `prompts/get` do MCP, expor `tools/call` como fallback.**
*Rationale:* o primitivo `prompts` do MCP foi pensado para "templates parametrizáveis injetados no contexto do LLM". Nosso payload não é exatamente isso (ele carrega `target_path` e `existing_markers`, mais próximos de um retorno de tool), então a escolha é **uma judgment call**, não óbvia. Optamos por `prompts/get` porque (i) a maior parte do payload **é** prompt + contexto, (ii) clientes MCP renderizam `prompts/get` na conversa de forma natural, (iii) `tools/call` permanece exposto em paralelo cobrindo clientes que ignoram `prompts`.
*Trade-offs:* dois caminhos a manter; mitigado por handler único que emite a mesma struct para ambos. Risco residual de o ecossistema MCP futuro recomendar formalmente um sobre o outro — aceitamos.

**ADR 6 — `target_path` calculado pelo handler, embutido no prompt como string literal.**
*Rationale:* o caller LLM não deve recalcular path; o handler conhece convenções (`<NNNN>-<slug>/`, kebab-case, monotonic ID via `os.scandir(workspace_path / "specs")`). O prompt traz o path absoluto pronto, eliminando ambiguidade.
*Trade-offs:* lógica de computação de path duplica regras que vivem implícitas em `SKILL.md` — mitigada por teste de contrato que afirma que o path computado satisfaz a regex do template.

## Project structure changes

```text
src/aiadev/_tooling/__init__.py                    (new) — fachada + exceções (InvalidWorkspaceError, ArtifactExistsError, SpecInvalidError, SpecNotFoundError, UnknownMarkerIdError); pequeno (<30 linhas).
src/aiadev/_tooling/skill_loader.py                (new) — lê SKILL.md + template + trecho relevante de constitution.md (callers: server + lib).
src/aiadev/_tooling/workspace.py                   (new) — validação de workspace_path; cálculo de target_path (callers: server + lib).
src/aiadev/_tooling/markers.py                     (new) — geração de cl-N, parsing/listagem de marcadores (callers: server + lib).
src/aiadev/_tooling/payload.py                     (new) — monta o ToolPayload validado contra schema (callers: server + lib).
src/aiadev/_tooling/telemetry.py                   (new) — JSON-lines stderr com allowlist (callers: server emite via logger configurado, lib Python emite via mesmo logger).

src/aiadev/tools/__init__.py                       (new) — API pública: specify(), clarify(), plan(), tasks(), implement(), analyze(), checklist(), constitution().
src/aiadev/tools/_definitions.py                   (new) — registro {nome → {description, input_schema, skill_name}} derivado do frontmatter de SKILL.md.

src/aiadev/mcp_server/__init__.py                  (new)
src/aiadev/mcp_server/__main__.py                  (new) — entry para `python -m aiadev.mcp_server` (e script `aiadev-mcp-server`).
src/aiadev/mcp_server/server.py                    (new) — wiring com SDK `mcp`: prompts/list, prompts/get, tools/list, tools/call.
src/aiadev/mcp_server/transport.py                 (new) — provider-pattern wrapper sobre o SDK `mcp` (Article V); permite fake nos testes.

schemas/tool-input-base.schema.json                (new) — campos comuns: workspace_path obrigatório.
schemas/tool-payload.schema.json                   (new) — shape do retorno (ver contracts/tool-payload.schema.json).
schemas/marker-grammar.schema.json                 (new) — regex e shape do `[NEEDS CLARIFICATION:cl-N ...]`.
schemas/vendor/mcp-tools-list.schema.json          (new, vendored) — JSON Schema oficial do MCP `tools/list` (cópia versionada do spec MCP, com link para a fonte em CREDITS).
schemas/vendor/mcp-prompts-list.schema.json        (new, vendored) — idem para `prompts/list`.

templates/spec-template.md                         (modified) — exemplo de marcador atualizado para `cl-N`.
skills/specify/SKILL.md                            (modified) — passo 4 instrui stamping de `cl-N` (monotonic dentro do spec).
skills/clarify/SKILL.md                            (modified) — input dos answers passa a ser `[{id, answer}]`; passo de re-stamping para legacy.
scripts/validate_skills.py                         (modified) — aceitar nova grammar `cl-N`; tolerar legacy com warning.

pyproject.toml                                     (modified) — `[project.optional-dependencies].mcp = ["mcp>=1.0,<2.0"]`; `[project.optional-dependencies].dev` adiciona `pytest-asyncio>=0.23`; `[project.scripts]` adiciona `aiadev-mcp-server = "aiadev.mcp_server.__main__:main"`.
README.md                                          (modified) — seção "Use as LLM tools" com sub-seções MCP stdio e Python lib.
CHANGELOG.md                                       (modified, fim da Phase 4) — `[Unreleased] Added: aiadev.tools (Python lib in-process), aiadev.mcp_server (MCP stdio); Changed: marker format now requires cl-N id`.
CREDITS.md                                         (modified) — entrada para o JSON Schema oficial do MCP vendored sob `schemas/vendor/`.

tests/_fakes/__init__.py                           (new)
tests/_fakes/llm.py                                (new) — fake LLM determinístico que segue o prompt e cria artefato (Article V).

tests/test_skill_loader.py                         (new)
tests/test_workspace.py                            (new) — path traversal, dir inexistente, computação de NNNN/slug, cross-platform absolute path.
tests/test_markers.py                              (new) — cl-N geração monotônica, parsing, gaps, duplicatas, **regressão da grammar para validate_skills** (Phase 1).
tests/test_payload.py                              (new) — validação de schema, embedding de target_path.
tests/test_telemetry.py                            (new) — allowlist; afirma ausência de PII.
tests/test_tools_lib.py                            (new) — API pública (specify(), clarify() etc.).
tests/test_mcp_server.py                           (new) — prompts/list, prompts/get, tools/list, tools/call usando o `mcp` SDK in-memory; inclui `test_both_primitives_return_same_payload` (ADR 5) e `test_listing_validates_against_vendored_mcp_schemas` (Story 4 sc2) e `test_catalog_reflects_skills_dir_changes` (Story 4 sc3).
tests/test_e2e_specify.py                          (new) — invoca specify() → fake LLM segue prompt → artefato satisfaz template.
tests/test_e2e_pipeline.py                         (new) — encadeia specify → clarify → plan → tasks via lib Python com fake LLM.

docs/articles/llm-tool-integration.md              (new) — guia "Como usar aiadev como tool de LLM" (smoke tests manuais documentados, exemplos MCP config + Python lib).

specs/0008-llm-tool-integration/research.md        (new, see ./research.md)
specs/0008-llm-tool-integration/contracts/marker-format.md      (new)
specs/0008-llm-tool-integration/contracts/tool-payload.schema.json (new)
```

## Phase breakdown

> Cada fase é um checkpoint. Dentro de uma fase, tasks são independentes;
> entre fases, ordem importa.

### Phase 1 — Mudança transversal de marcadores (pré-requisito) — ~6 tasks

Sem isso, `clarify(answers=[{id, ...}])` não tem como referenciar marcadores. É a única mudança que toca `templates/`/`skills/` antes de qualquer código novo. **Toda mudança de comportamento abaixo é precedida por teste vermelho** (Article II).

- **(test-first)** `tests/test_markers.py::test_validator_accepts_cl_n_grammar` e `::test_validator_rejects_malformed_ids` — RED antes de qualquer alteração em `validate_skills.py`. Cobre os 3 casos inválidos do contract (`marker-format.md`).
- **(test-first)** `tests/test_markers.py::test_validator_tolerates_legacy_with_warning` — RED antes da regra de back-compat ser implementada.
- Adicionar `schemas/marker-grammar.schema.json` (novo) com regex canônica do contract.
- Atualizar `scripts/validate_skills.py` para passar os testes acima (consumir a grammar, aceitar `cl-N`, tolerar legacy).
- Atualizar `templates/spec-template.md` (exemplo de marcador → `cl-N`).
- Atualizar `skills/specify/SKILL.md` (passo 4 do Loop: stamping monotonic) e `skills/clarify/SKILL.md` (input dos answers usa `[{id, answer}]`; passo de re-stamping para legacy).

### Phase 2 — Core compartilhado em `aiadev._tooling` — ~6 tasks

Toda a lógica que servidor e lib usam, atrás de uma fachada testada em isolamento.
Cada módulo é precedido pelo seu teste (red → green → refactor).

- `_tooling/__init__.py` (excepções tipadas inline + fachada). **Não há módulo `errors.py`** — exceções são poucas e ficam no `__init__` para reduzir indireção.
- `workspace.py` (validação + cálculo de NNNN/slug/target_path) — precedido por `tests/test_workspace.py`.
- `skill_loader.py` (carrega SKILL.md + template aplicável + trecho relevante da constitution) — precedido por `tests/test_skill_loader.py`.
- `markers.py` (geração de `cl-N` runtime, enumeração de `existing_markers`) — testes adicionais ao `test_markers.py` da Phase 1 (geração in-memory, gaps, duplicatas).
- `payload.py` (monta o `ToolPayload` validado contra `schemas/tool-payload.schema.json`) — precedido por `tests/test_payload.py`.
- `telemetry.py` (logger JSON-lines em stderr; allowlist; consumido pelo server e pela lib) — precedido por `tests/test_telemetry.py` que afirma ausência de PII.

### Phase 3 — Biblioteca Python in-process `aiadev.tools` — ~5 tasks

Superfície pública mais simples — entrega valor primeiro a callers Python diretos (LiteLLM/Anthropic SDK).

- `tools/_definitions.py` (registro a partir do frontmatter de cada SKILL.md).
- `tools/__init__.py` (8 funções públicas: `specify()`, `clarify()`, …).
- Documentação inline (docstrings curtas).
- `tests/test_tools_lib.py` (cada função; happy path + erros).
- `tests/test_e2e_pipeline.py` (encadeamento via lib + fake LLM).

### Phase 4 — Servidor MCP stdio `aiadev.mcp_server` — ~7 tasks

Empacota o core no protocolo MCP. Depende do SDK `mcp` (optional extra).
Sem fake MCP client custom — `tests/test_mcp_server.py` usa as utilities in-memory do próprio SDK `mcp` (`mcp.shared.memory.create_connected_server_and_client_session` ou equivalente), evitando criar `tests/_fakes/mcp_client.py` que duplicaria infra.

- Vendorar `schemas/vendor/mcp-tools-list.schema.json` e `schemas/vendor/mcp-prompts-list.schema.json` (cópia versionada do spec MCP); atualizar `CREDITS.md` (Article VII).
- `pyproject.toml` (extra `[mcp]`, `pytest-asyncio` em `[dev]`, script `aiadev-mcp-server`).
- `mcp_server/transport.py` (provider sobre o SDK `mcp`, Article V; permite fake nos testes).
- `mcp_server/server.py` (handlers `prompts/list`, `prompts/get`, `tools/list`, `tools/call`).
- `mcp_server/__main__.py` (entry point; valida `mcp` instalado com mensagem útil; chama `find_framework_root()` no startup).
- `tests/test_mcp_server.py` precedendo cada handler — incluindo (Story 4 sc1+sc2) `test_listing_returns_8_pipeline_skills` + `test_listing_validates_against_vendored_mcp_schemas` (offline, sem cliente real); (Story 4 sc3) `test_catalog_reflects_skills_dir_changes` (mocka `skills/` e re-lista); (ADR 5) `test_both_primitives_return_same_payload`.
- Atualizar `CHANGELOG.md` `[Unreleased]` ao concluir o servidor: `Added: aiadev.mcp_server (MCP stdio); Changed: marker format requires cl-N id`.

### Phase 5 — Integração end-to-end + documentação — ~4 tasks

- `tests/_fakes/llm.py` (fake LLM determinístico — segue o prompt, cria artefato; provider-pattern per Article V).
- `tests/test_e2e_specify.py` (Story 1 cenário 2: prompt + fake LLM → spec.md satisfaz template real, não literal).
- `tests/test_e2e_pipeline.py` (encadeia specify → clarify → plan → tasks via lib Python com fake LLM, valida cada artefato contra seu template).
- Documentação: `README.md` ganha seção "Use as LLM tools" (config MCP + exemplo lib Python); `docs/articles/llm-tool-integration.md` (novo, destino canônico) descreve smoke tests manuais com saída esperada e referencia o `README.md` para o quick-start.

## Risks and mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Mudança de marcador quebra specs antigos (`feature-*/spec.md`) que ainda têm `[NEEDS CLARIFICATION: ...]` sem id. | Med | Low | Manter `clarify` retro-compatível (parser aceita marcadores sem id como `null` e instrui o usuário a re-stampar). Documentar em CHANGELOG. Sem migração automática. |
| `mcp` SDK ainda em evolução (pré-1.0 em alguns wrappers de cliente). | Med | Med | Encapsular SDK em `mcp_server/transport.py` (Article V); pinar `mcp>=1.0,<2.0` no extra; cobrir handlers com testes via fake transport, não SDK real. |
| Fake LLM nos testes E2E divergir do comportamento real (testes verdes, prod quebrado). | Med | High | Fake só implementa o subset que executa o prompt: localizar `target_path`, criar arquivo, copiar template, preencher seções obrigatórias. Validar o output **contra o template real** (não contra string literal), o mesmo que um LLM real produziria. Documentar limitações no fake. |
| Drift entre regra de naming de path (`<NNNN>-<slug>/`) embutida no handler e o template. | Low | Med | Teste `test_workspace.py` afirma que `target_path` computado bate com a regex declarada em `schemas/marker-grammar.schema.json` e com o exemplo do `templates/spec-template.md`. |
| Latência do handler explodir com leitura repetida de SKILL.md (8 leituras por sessão). | Low | Low | Cache em memória dentro do processo (`functools.lru_cache` em `skill_loader`). Invalidação por mtime se necessário (provavelmente desnecessário — assets são imutáveis em runtime). |
| Caller MCP lança o servidor com cwd imprevisível e `paths.find_framework_root` falha. | Low | High | `mcp_server/__main__.py` resolve `find_framework_root()` no startup e falha rápido com mensagem clara. Validar via teste que invoca o módulo com `cwd=/tmp`. |

## Complexity tracking

> Obrigatória quando alguma linha do Constitution Check é `FAIL`. Vazia se sem waivers.

| Article waived | Reason | Alternatives considered | Reviewer |
|---|---|---|---|
| — | Sem waivers. | — | — |

## Hand-off to `tasks`

O próximo skill é `tasks`. Ele consome este plan e produz `tasks.md`.

Pré-condições para o hand-off:

- [x] Constitution Check totalmente preenchido, sem linhas em branco.
- [x] Complexity tracking explícito como vazio + justificado.
- [x] Project structure delta listado arquivo a arquivo.
- [x] Phase breakdown sem enumerar tarefas individuais (deixado para `tasks`).
- [x] Auxiliary artifacts (`research.md`, `contracts/`) escritos.
