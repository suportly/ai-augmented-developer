# Tasks: aiadev como ferramenta de LLM

> Produzido pelo skill `tasks` a partir de [plan.md](./plan.md). Consumido por `implement`.

**Branch:** `feature/llm-tool-integration`
**Plan:** [plan.md](./plan.md)
**Generated:** 2026-04-16
**Language:** pt-BR

---

## How to read this file

- Tarefas são ordenadas. `implement` executa de cima para baixo respeitando `Depends on`.
- **Uma task = um commit.** Mensagem começa com o id da task.
- Cada task linka aos cenários do spec que ela exercita.
- `Status` é um de: `pending`, `in_progress`, `blocked`, `done`. Apenas `implement` muta.
- Convenção de commit: `<type>(<scope>): T<NNN> <subject>` (Conventional Commits).

## Task list

### T001 — Validator aceita grammar `cl-N`

- **Status:** pending
- **Depends on:** —
- **Files:**
  - create: `schemas/marker-grammar.schema.json`
  - create: `tests/test_markers.py`
  - modify: `scripts/validate_skills.py`
- **Spec scenarios:** —  *(infra para Story 2 sc1)*
- **Acceptance:**
  - [ ] `tests/test_markers.py::test_validator_accepts_cl_n_grammar` adicionado e observado em RED.
  - [ ] `schemas/marker-grammar.schema.json` contém a regex canônica de `contracts/marker-format.md`.
  - [ ] `validate_skills.py` consome a schema e o teste vira GREEN.
  - [ ] Nenhum teste existente regride.
  - [ ] Commit: `feat(markers): T001 add cl-N grammar schema and validator hook`.

### T002 — Validator rejeita ids malformados

- **Status:** pending
- **Depends on:** T001
- **Files:**
  - modify: `scripts/validate_skills.py`
  - test: `tests/test_markers.py`
- **Spec scenarios:** —
- **Acceptance:**
  - [ ] `test_validator_rejects_malformed_ids` cobre os 3 casos do contract (`[NEEDS CLARIFICATION:` sem id, `cl-001` zero-padded, `cl-1.2`) e foi observado em RED antes da regra estrita.
  - [ ] Validator endurece a regra; teste vira GREEN.
  - [ ] T001 continua passando.
  - [ ] Commit: `fix(markers): T002 reject malformed cl-N ids`.

### T003 — Validator tolera legacy `[NEEDS CLARIFICATION: ...]` com warning

- **Status:** pending
- **Depends on:** T001
- **Files:**
  - modify: `scripts/validate_skills.py`
  - test: `tests/test_markers.py`
- **Spec scenarios:** —  *(garante back-compat com 7 specs `feature-*` existentes)*
- **Acceptance:**
  - [ ] `test_validator_tolerates_legacy_with_warning` adicionado em RED.
  - [ ] Validator emite warning (stderr ou logger), não falha.
  - [ ] Teste GREEN; specs antigos sob `specs/feature-*/` continuam passando o `python3 scripts/validate_skills.py`.
  - [ ] Commit: `fix(markers): T003 accept legacy markers with warning`.

### T004 — Atualizar `templates/spec-template.md` para `cl-N`

- **Status:** pending
- **Depends on:** T001
- **Files:**
  - modify: `templates/spec-template.md`
  - test: `tests/test_framework_artifacts.py` (asserção adicionada)
- **Spec scenarios:** —
- **Acceptance:**
  - [ ] Asserção de teste em RED: `templates/spec-template.md` contém ao menos um exemplo `[NEEDS CLARIFICATION:cl-1 ...]` válido.
  - [ ] Exemplo do template atualizado; teste GREEN.
  - [ ] `python3 scripts/validate_skills.py` continua passando (não emite warning de legacy nesse exemplo).
  - [ ] Commit: `chore(templates): T004 stamp cl-N marker example in spec template`.

### T005 — Atualizar `skills/specify/SKILL.md` para instruir stamping `cl-N`

- **Status:** pending
- **Depends on:** T001
- **Files:**
  - modify: `skills/specify/SKILL.md`
  - test: `tests/test_framework_artifacts.py`
- **Spec scenarios:** —  *(garante que `specify` produz marcadores ids-cumpridos)*
- **Acceptance:**
  - [ ] Asserção de teste em RED: o passo 4 do Loop em `skills/specify/SKILL.md` menciona stamping de id `cl-N` monotonic.
  - [ ] Skill atualizado; teste GREEN.
  - [ ] Commit: `docs(skills): T005 instruct specify to stamp cl-N ids`.

### T006 — Atualizar `skills/clarify/SKILL.md` para `answers=[{id, answer}]`

- **Status:** pending
- **Depends on:** T001
- **Files:**
  - modify: `skills/clarify/SKILL.md`
  - test: `tests/test_framework_artifacts.py`
- **Spec scenarios:** —  *(formaliza o input que tools/clarify e mcp_server/clarify usarão)*
- **Acceptance:**
  - [ ] Asserção de teste em RED: o Loop do `clarify/SKILL.md` descreve `answers=[{id, answer}, ...]` e re-stamping de marcadores legacy.
  - [ ] Skill atualizado; teste GREEN.
  - [ ] Commit: `docs(skills): T006 update clarify input shape to id+answer pairs`.

### T007 — `aiadev._tooling.__init__` com excepções tipadas

- **Status:** pending
- **Depends on:** —
- **Files:**
  - create: `src/aiadev/_tooling/__init__.py`
  - create: `tests/test_tooling_errors.py`
- **Spec scenarios:** —  *(boundary error contract usado por todas as tools)*
- **Acceptance:**
  - [ ] `test_tooling_errors.py` exige a presença e instanciação de `InvalidWorkspaceError`, `ArtifactExistsError`, `SpecInvalidError`, `SpecNotFoundError`, `UnknownMarkerIdError`. Observa RED.
  - [ ] `__init__.py` define as 5 classes (cada uma carrega `code` estável: `invalid_workspace`, `artifact_exists`, `spec_invalid`, `spec_not_found`, `unknown_marker_id`). Teste GREEN.
  - [ ] Tamanho final < 30 linhas (verificável a olho — Article III).
  - [ ] Commit: `feat(tooling): T007 add typed errors for tool boundary`.

### T008 — `workspace.py` valida `workspace_path` e bloqueia path traversal

- **Status:** pending
- **Depends on:** T007
- **Files:**
  - create: `src/aiadev/_tooling/workspace.py`
  - create: `tests/test_workspace.py`
- **Spec scenarios:** **Story 3 sc1**
- **Acceptance:**
  - [ ] `test_workspace.py` cobre os 3 vetores do `research.md` R4: `..` literal, symlink que escapa, path absoluto fora do workspace. Cada um exige `InvalidWorkspaceError` com `code="invalid_workspace"`. Observa RED.
  - [ ] `workspace.validate(path) -> Path` resolve com `expanduser().resolve(strict=True)` e verifica `is_dir()`.
  - [ ] Helper `assert_within(workspace, candidate)` usa `Path.is_relative_to`.
  - [ ] Testes GREEN.
  - [ ] Commit: `feat(tooling): T008 validate workspace_path against traversal`.

### T009 — `workspace.compute_target_path` (NNNN + slug) com guarda `artifact_exists`

- **Status:** pending
- **Depends on:** T008
- **Files:**
  - modify: `src/aiadev/_tooling/workspace.py`
  - test: `tests/test_workspace.py`
- **Spec scenarios:** **Story 3 sc2**, suporta Story 1 sc1 e Story 2 sc2/sc3
- **Acceptance:**
  - [ ] Casos em RED: (a) workspace vazio → `NNNN=0001`; (b) workspace com `0007-foo` → `NNNN=0008`; (c) slug `aiadev como ferramenta` → `aiadev-como-ferramenta`; (d) `target_path` já existente → `ArtifactExistsError(code="artifact_exists", path=...)`; (e) `overwrite=True` ignora a guarda.
  - [ ] Implementação faz scan de `workspace_path/specs/`, extrai `NNNN`, kebab-case da slug, gera `target_path`. Teste GREEN.
  - [ ] Commit: `feat(tooling): T009 compute target_path and guard artifact_exists`.

### T010 — `skill_loader.py` lê SKILL.md + template + trecho de constitution

- **Status:** pending
- **Depends on:** T007
- **Files:**
  - create: `src/aiadev/_tooling/skill_loader.py`
  - create: `tests/test_skill_loader.py`
- **Spec scenarios:** **Story 3 sc3** (parte: `spec_not_found` quando o caller passa `spec_path` inexistente para skills que precisam de spec)
- **Acceptance:**
  - [ ] `test_skill_loader.py` em RED: (a) `load("specify")` retorna `(prompt: str, template: {path, content}, constitution_excerpt: str)`; (b) skill desconhecido → `KeyError`; (c) `load("plan", spec_path=<inexistente>)` → `SpecNotFoundError`; (d) trecho de constitution inclui pelo menos os artigos referenciados no SKILL.md.
  - [ ] Implementação usa `aiadev.paths.find_framework_root()` para resolver assets; cacheia leituras com `functools.lru_cache`.
  - [ ] Testes GREEN.
  - [ ] Commit: `feat(tooling): T010 load skill content with template and constitution`.

### T011 — `markers.py` gera ids `cl-N` e enumera marcadores em texto

- **Status:** pending
- **Depends on:** T001, T007
- **Files:**
  - create: `src/aiadev/_tooling/markers.py`
  - test: `tests/test_markers.py` (novos casos)
- **Spec scenarios:** **Story 1 sc3**
- **Acceptance:**
  - [ ] Testes em RED: (a) `next_id("texto sem marcadores") == 1`; (b) `next_id("...cl-1...cl-3...") == 4` (gaps preservados); (c) `enumerate("...[NEEDS CLARIFICATION:cl-2 X]...[NEEDS CLARIFICATION: legacy]...")` retorna lista com um `id="cl-2"` e um `id=None`; (d) `needs_renumbering(...)` é `True` quando há entry com `id=None`.
  - [ ] Implementação usa a regex de `schemas/marker-grammar.schema.json` (compartilhada via `schema_loader`).
  - [ ] Testes GREEN; T001-T003 continuam passando.
  - [ ] Commit: `feat(tooling): T011 generate cl-N ids and enumerate markers`.

### T012 — `payload.py` monta `ToolPayload` validado contra schema

- **Status:** pending
- **Depends on:** T009, T010, T011
- **Files:**
  - create: `src/aiadev/_tooling/payload.py`
  - create: `tests/test_payload.py`
  - copy/use: `specs/0008-llm-tool-integration/contracts/tool-payload.schema.json` como fixture (resolver path no teste).
- **Spec scenarios:** Story 1 sc1, Story 1 sc3 (existing_markers), Story 1 sc4 (Language stamping no prompt)
- **Acceptance:**
  - [ ] `test_payload.py` em RED: (a) payload válido para `skill="specify"` valida contra `contracts/tool-payload.schema.json` via `jsonschema`; (b) payload sem `target_path` falha; (c) `target_path` é o resolvido por `workspace.compute_target_path`; (d) `existing_markers` é uma lista (vazia para spec inexistente, populada quando `extra_files` contém spec com marcadores).
  - [ ] Implementação `build(skill, workspace, **kwargs) -> dict` orquestra workspace+skill_loader+markers e devolve dict pronto. Teste GREEN.
  - [ ] Commit: `feat(tooling): T012 assemble ToolPayload validated against schema`.

### T013 — `telemetry.py` emite JSON-lines em stderr com allowlist

- **Status:** pending
- **Depends on:** T007
- **Files:**
  - create: `src/aiadev/_tooling/telemetry.py`
  - create: `tests/test_telemetry.py`
- **Spec scenarios:** —  *(Article VI compliance, sem PII)*
- **Acceptance:**
  - [ ] `test_telemetry.py` em RED: (a) `log_invocation(tool="specify", workspace_path="/x", latency_ms=12, status="ok")` produz uma linha JSON em stderr com somente os campos da allowlist (`{ts, tool, workspace_path, latency_ms, status, error_code?}`); (b) chamada com kwarg extra (`demand="..."`) **não** vaza o campo (ou o campo extra é silenciosamente descartado, não logado); (c) `error_code` aparece apenas quando `status != "ok"`.
  - [ ] Implementação usa `logging` com handler stderr e formatter JSON; allowlist explícita.
  - [ ] Testes GREEN.
  - [ ] Commit: `feat(tooling): T013 stderr JSON-lines telemetry with PII allowlist`.

### T014 — `aiadev.tools._definitions` deriva catálogo do frontmatter de SKILL.md

- **Status:** pending
- **Depends on:** T010
- **Files:**
  - create: `src/aiadev/tools/_definitions.py`
  - create: `src/aiadev/tools/__init__.py` *(stub vazio; populado em T015+)*
  - create: `tests/test_tools_definitions.py`
- **Spec scenarios:** **Story 4 sc1** *(parcial: a lib expõe os 8; o servidor MCP refaz o teste em T022)*
- **Acceptance:**
  - [ ] `test_tools_definitions.py` em RED: `list_definitions()` retorna exatamente 8 entradas com nomes `{specify, clarify, plan, tasks, implement, analyze, checklist, constitution}`; cada uma com `description` (do frontmatter `description:`) e `input_schema` (jsonschema dict).
  - [ ] Implementação parseia frontmatter de cada `skills/<name>/SKILL.md` via `pyyaml`. Teste GREEN.
  - [ ] Commit: `feat(tools): T014 build tool catalog from SKILL.md frontmatter`.

### T015 — `aiadev.tools.specify(demand, workspace_path)`

- **Status:** pending
- **Depends on:** T012, T013, T014
- **Files:**
  - modify: `src/aiadev/tools/__init__.py`
  - create: `tests/test_tools_lib.py`
- **Spec scenarios:** **Story 1 sc1**, **Story 1 sc4**
- **Acceptance:**
  - [ ] `test_tools_lib.py::test_specify_returns_payload` em RED: `specify(demand="x", workspace_path=tmp)` retorna dict que valida contra `tool-payload.schema.json`, com `skill=="specify"`, `target_path` dentro do `workspace_path`, `marker_format.next_id == 1` em workspace vazio.
  - [ ] `test_specify_stamps_language` em RED: quando `language="pt-BR"` é passado (ou inferido por kwargs), o `prompt` retornado contém instrução literal de stampar `Language: pt-BR`.
  - [ ] Implementação delega a `_tooling.payload.build("specify", ...)`, com hook de `language` injetado no template do prompt. Teste GREEN.
  - [ ] Telemetria de T013 emite linha JSON na chamada (verificado com `caplog`/captura de stderr).
  - [ ] Commit: `feat(tools): T015 implement specify() returning ToolPayload`.

### T016 — `aiadev.tools.clarify(spec_path, workspace_path, answers)`

- **Status:** pending
- **Depends on:** T015
- **Files:**
  - modify: `src/aiadev/tools/__init__.py`
  - test: `tests/test_tools_lib.py`
- **Spec scenarios:** **Story 2 sc1**
- **Acceptance:**
  - [ ] `test_clarify_accepts_id_answer_pairs` em RED: dado um spec fixture com marcadores `cl-1` e `cl-2`, `clarify(spec_path=..., answers=[{"id":"cl-1","answer":"X"},{"id":"cl-2","answer":"Y"}])` retorna payload onde o `prompt` parametrizado embute as duas respostas e `existing_markers` documenta os ids resolvidos.
  - [ ] `test_clarify_rejects_unknown_id` em RED: `id="cl-99"` (não presente no spec) → `UnknownMarkerIdError`.
  - [ ] Implementação. Teste GREEN.
  - [ ] Commit: `feat(tools): T016 implement clarify() with id+answer pairs`.

### T017 — `aiadev.tools.plan` e `tasks` (artefatos derivados de spec/plan)

- **Status:** pending
- **Depends on:** T015
- **Files:**
  - modify: `src/aiadev/tools/__init__.py`
  - test: `tests/test_tools_lib.py`
- **Spec scenarios:** **Story 2 sc2**, **Story 2 sc3**, **Story 3 sc3** *(spec_invalid / spec_not_found)*
- **Acceptance:**
  - [ ] `test_plan_requires_spec` em RED: `plan(spec_path=<inexistente>, workspace_path=...)` → `SpecNotFoundError`.
  - [ ] `test_plan_includes_constitution_check_instruction` em RED: o `prompt` retornado por `plan(...)` contém a sub-string `Constitution Check` e referência aos 7 artigos com slot para `ok | waiver | fail`.
  - [ ] `test_tasks_includes_format_instruction` em RED: o `prompt` retornado por `tasks(...)` referencia o formato "1 teste + 1 implementação + 1 commit".
  - [ ] `test_plan_rejects_malformed_spec` em RED: spec sem seções obrigatórias → `SpecInvalidError(missing_sections=[...])`.
  - [ ] Implementação. Testes GREEN.
  - [ ] Commit: `feat(tools): T017 implement plan() and tasks() over existing artifacts`.

### T018 — `aiadev.tools.implement / analyze / checklist / constitution`

- **Status:** pending
- **Depends on:** T015
- **Files:**
  - modify: `src/aiadev/tools/__init__.py`
  - test: `tests/test_tools_lib.py`
- **Spec scenarios:** —  *(completam o catálogo de 8; cada um cobre apenas o seu próprio prompt)*
- **Acceptance:**
  - [ ] `test_implement_returns_payload`, `test_analyze_returns_payload`, `test_checklist_returns_payload`, `test_constitution_returns_payload` — cada um em RED, validando estrutura e que `skill` corresponde ao nome.
  - [ ] Implementação reutiliza `_tooling.payload.build`. Testes GREEN.
  - [ ] Commit: `feat(tools): T018 implement remaining 4 pipeline tools`.

### T019 — Vendorar JSON Schemas oficiais do MCP em `schemas/vendor/`

- **Status:** pending
- **Depends on:** —
- **Files:**
  - create: `schemas/vendor/mcp-tools-list.schema.json`
  - create: `schemas/vendor/mcp-prompts-list.schema.json`
  - create: `schemas/vendor/README.md` *(fonte, versão, hash)*
  - modify: `CREDITS.md`
  - create: `tests/test_vendored_schemas.py`
- **Spec scenarios:** —  *(infra para Story 4 sc2)*
- **Acceptance:**
  - [ ] `test_vendored_schemas.py` em RED: ambos os arquivos parseiam como JSON Schema 2020-12 válido (`jsonschema.Draft202012Validator.check_schema(...)` não levanta).
  - [ ] Schemas baixados/copiados da spec MCP oficial; `schemas/vendor/README.md` documenta versão e link permanente; `CREDITS.md` ganha entrada conforme Article VII.
  - [ ] Testes GREEN.
  - [ ] Commit: `chore(schemas): T019 vendor MCP tools/list and prompts/list schemas`.

### T020 — `pyproject.toml`: extra `[mcp]`, `pytest-asyncio`, script `aiadev-mcp-server`

- **Status:** pending
- **Depends on:** —
- **Files:**
  - modify: `pyproject.toml`
  - create: `tests/test_packaging.py`
- **Spec scenarios:** —  *(infra do servidor MCP)*
- **Acceptance:**
  - [ ] `test_packaging.py` em RED: `metadata.entry_points()['console_scripts']` inclui `aiadev-mcp-server`; `optional_dependencies` inclui `mcp` e `dev` inclui `pytest-asyncio`.
  - [ ] `pyproject.toml` atualizado: `[project.optional-dependencies].mcp = ["mcp>=1.0,<2.0"]`; `dev` ganha `pytest-asyncio>=0.23`; `[project.scripts]` ganha `aiadev-mcp-server = "aiadev.mcp_server.__main__:main"`.
  - [ ] `pip install -e '.[mcp,dev]'` (rodado pelo implementer e capturado em log do PR — Article IV) sucede.
  - [ ] Testes GREEN.
  - [ ] Commit: `chore(packaging): T020 add mcp extra and aiadev-mcp-server entrypoint`.

### T021 — `mcp_server/transport.py` provider para o SDK `mcp` (Article V)

- **Status:** pending
- **Depends on:** T020
- **Files:**
  - create: `src/aiadev/mcp_server/__init__.py`
  - create: `src/aiadev/mcp_server/transport.py`
  - create: `tests/test_mcp_transport.py`
- **Spec scenarios:** —  *(infra para Stories 1/2/4 via MCP)*
- **Acceptance:**
  - [ ] `test_mcp_transport.py` em RED: a interface define `register_prompt(name, handler)`, `register_tool(name, handler)`, `serve_stdio()`; um fake transport in-memory satisfaz a interface e expõe `invoke(name, kind, args)` que devolve o output do handler.
  - [ ] Implementação real wrappa `mcp.server.Server` com a mesma interface; testes usam o fake.
  - [ ] Testes GREEN.
  - [ ] Commit: `feat(mcp-server): T021 transport provider over mcp SDK`.

### T022 — `mcp_server/server.py` handlers `prompts/list` + `tools/list`

- **Status:** pending
- **Depends on:** T014, T019, T021
- **Files:**
  - create: `src/aiadev/mcp_server/server.py`
  - create: `tests/test_mcp_server.py`
- **Spec scenarios:** **Story 4 sc1**, **Story 4 sc2**
- **Acceptance:**
  - [ ] `test_mcp_server.py::test_listing_returns_8_pipeline_skills` em RED: chama o handler de `prompts/list` (e `tools/list`) via fake transport e espera array de 8 entradas com nomes do pipeline.
  - [ ] `test_listing_validates_against_vendored_mcp_schemas` em RED: cada item do listing valida contra `schemas/vendor/mcp-prompts-list.schema.json` (e `mcp-tools-list.schema.json`) usando `jsonschema`. **Sem cliente MCP real, sem chamada LLM** (Article V).
  - [ ] Handlers consultam `aiadev.tools._definitions.list_definitions()`. Teste GREEN.
  - [ ] Commit: `feat(mcp-server): T022 wire prompts/list and tools/list handlers`.

### T023 — `mcp_server/server.py` handlers `prompts/get` + `tools/call` (mesmo payload)

- **Status:** pending
- **Depends on:** T015, T022
- **Files:**
  - modify: `src/aiadev/mcp_server/server.py`
  - test: `tests/test_mcp_server.py`
- **Spec scenarios:** **Story 1 sc1** (via MCP)
- **Acceptance:**
  - [ ] `test_prompts_get_returns_tool_payload` em RED: invocar `prompts/get(name="specify", arguments={demand,workspace_path})` retorna estrutura compatível com `contracts/tool-payload.schema.json`.
  - [ ] `test_both_primitives_return_same_payload` (ADR 5) em RED: `prompts/get(name)` e `tools/call(name)` para o mesmo input produzem o mesmo `ToolPayload` byte-equivalente.
  - [ ] Handlers delegam a `aiadev.tools.<name>(**args)`. Testes GREEN.
  - [ ] Commit: `feat(mcp-server): T023 prompts/get and tools/call return identical ToolPayload`.

### T024 — Catálogo do servidor reflete mudanças em `skills/`

- **Status:** pending
- **Depends on:** T022
- **Files:**
  - modify: `src/aiadev/mcp_server/server.py` *(se necessário invalidar cache)*
  - test: `tests/test_mcp_server.py`
- **Spec scenarios:** **Story 4 sc3**
- **Acceptance:**
  - [ ] `test_catalog_reflects_skills_dir_changes` em RED: configura um `tmp_path` com 2 skills, lista, espera 2; adiciona um terceiro `SKILL.md`, re-lista, espera 3; remove um, re-lista, espera 2 — sem rebuild manual.
  - [ ] Se `_definitions` ou `skill_loader` cacheiam, invalidação fica explícita (mtime ou recomputação a cada listing). Teste GREEN.
  - [ ] T022 continua passando.
  - [ ] Commit: `feat(mcp-server): T024 catalog reflects skills dir changes at runtime`.

### T025 — `mcp_server/__main__.py` entry + falha rápida sem `mcp` SDK + CHANGELOG

- **Status:** pending
- **Depends on:** T021, T022, T023, T024
- **Files:**
  - create: `src/aiadev/mcp_server/__main__.py`
  - create: `tests/test_mcp_server_entrypoint.py`
  - modify: `CHANGELOG.md`
- **Spec scenarios:** —  *(empacota o servidor para uso via `python -m aiadev.mcp_server` e `aiadev-mcp-server`)*
- **Acceptance:**
  - [ ] `test_mcp_server_entrypoint.py` em RED: (a) `__main__:main()` chama `paths.find_framework_root()` no startup e exits != 0 se não achar; (b) se `mcp` SDK ausente, exit != 0 com mensagem indicando `pip install 'aiadev[mcp]'`; (c) se `cwd=/tmp` e `AIADEV_ROOT` não setado, comportamento de (a) é o esperado.
  - [ ] `CHANGELOG.md` `[Unreleased]` ganha: `Added: aiadev.tools (Python lib in-process), aiadev.mcp_server (MCP stdio); Changed: marker format requires cl-N id`.
  - [ ] Testes GREEN.
  - [ ] Commit: `feat(mcp-server): T025 entrypoint with framework_root and mcp SDK checks`.

### T026 — `tests/_fakes/llm.py` fake LLM determinístico (Article V)

- **Status:** pending
- **Depends on:** T015
- **Files:**
  - create: `tests/_fakes/__init__.py`
  - create: `tests/_fakes/llm.py`
  - create: `tests/test_fake_llm.py`
- **Spec scenarios:** —  *(infra para os E2E em T027–T028)*
- **Acceptance:**
  - [ ] `test_fake_llm.py` em RED: dado um `ToolPayload` sintético com `skill="specify"` e `target_path` apontando para `tmp_path`, o fake (a) lê `context.template.content`, (b) substitui `{{FEATURE_NAME}}`, `{{BRANCH}}`, `{{DATE}}`, `{{SPEC_ID}}` com valores derivados do payload, (c) escreve em `target_path`, (d) retorna o conteúdo escrito.
  - [ ] Implementação. Documentar no docstring as limitações (não valida qualidade de conteúdo qualitativo). Teste GREEN.
  - [ ] Commit: `test(fakes): T026 deterministic fake LLM for E2E tests`.

### T027 — E2E `test_e2e_specify.py`: prompt + fake LLM → spec.md satisfaz template

- **Status:** pending
- **Depends on:** T015, T026
- **Files:**
  - create: `tests/test_e2e_specify.py`
- **Spec scenarios:** **Story 1 sc2**
- **Acceptance:**
  - [ ] Test em RED: invoca `aiadev.tools.specify(demand="...", workspace_path=tmp)`, passa o `ToolPayload` retornado para o fake LLM (T026), depois lê o arquivo em `target_path` e afirma que ele contém **todos os headers obrigatórios** definidos em `templates/spec-template.md` (Problem, Users and stakeholders, Success criteria, Non-goals, User stories, Clarifications, Data touched, Out-of-band effects, Open risks, Traceability) e ≥1 user story com ≥3 cenários.
  - [ ] Validação de seções obrigatórias **lê o template real** (`templates/spec-template.md`), extrai os headers `## ...`, e compara com o output — não compara contra string literal (resilient a edição do template).
  - [ ] Teste GREEN.
  - [ ] Commit: `test(e2e): T027 specify produces template-compliant spec.md`.

### T028 — E2E `test_e2e_pipeline.py`: encadeia specify→clarify→plan→tasks via lib

- **Status:** pending
- **Depends on:** T016, T017, T026
- **Files:**
  - create: `tests/test_e2e_pipeline.py`
- **Spec scenarios:** **Story 2 sc1**, **Story 2 sc2**, **Story 2 sc3**
- **Acceptance:**
  - [ ] Test em RED: pipeline completo num `tmp_path`: (a) `specify` + fake LLM → spec.md; (b) `clarify` com `answers` cobrindo todos `cl-N` + fake LLM → spec.md sem marcadores; (c) `plan` + fake LLM → plan.md com seção Constitution Check (7 artigos); (d) `tasks` + fake LLM → tasks.md com pelo menos uma task no formato esperado.
  - [ ] Cada artefato validado contra seu respectivo `templates/<x>-template.md` (mesma técnica de T027).
  - [ ] Teste GREEN.
  - [ ] Commit: `test(e2e): T028 chain specify→clarify→plan→tasks via Python lib`.

### T029 — Documentação: `README.md` + `docs/articles/llm-tool-integration.md`

- **Status:** pending
- **Depends on:** T015, T020, T025
- **Files:**
  - modify: `README.md`
  - create: `docs/articles/llm-tool-integration.md`
- **Spec scenarios:** —  *(success criterion "documentação descreve como instalar e expor")*
- **Acceptance:**
  - [ ] `README.md` ganha seção "Use as LLM tools" com (a) sub-seção "MCP stdio" com snippet de `.mcp.json`; (b) sub-seção "Python lib" com import + chamada exemplo.
  - [ ] `docs/articles/llm-tool-integration.md` documenta smoke tests manuais com saída esperada (output de `aiadev-mcp-server` validado por `mcp inspector` ou equivalente; exemplo de `from aiadev.tools import specify; print(specify(...))`).
  - [ ] `npx markdownlint-cli2 '**/*.md'` continua passando.
  - [ ] Commit: `docs: T029 document MCP server and Python lib usage`.

## Parallelization hints

- **Group A (Phase 1, após T001):** T004, T005, T006 podem rodar em paralelo (3 arquivos disjuntos: `templates/spec-template.md`, `skills/specify/SKILL.md`, `skills/clarify/SKILL.md`).
- **Group B (Phase 2, após T007):** T008, T010, T013 em paralelo (módulos distintos sem dep entre si). T011 entra após T001+T007. T009 é serial após T008. T012 é serial após T009+T010+T011.
- **Group C (Phase 4, infra):** T019 e T020 em paralelo (vendor schemas vs pyproject.toml).
- **Group D (Phase 4, server):** T022, T023, T024 são **seriais** entre si — todos modificam `mcp_server/server.py`.
- **Group E (Phase 5):** T027 e T028 em paralelo (arquivos de teste distintos, ambos dependentes de T026).
- **Serial:** todo o restante.

## Post-task checklist

Após cada task:

- [ ] Mensagem de commit referencia o id (`T<NNN>`).
- [ ] Status nesta tabela atualizado (`pending` → `done`).

Após todas as tasks:

- [ ] Suite completa passa: `pytest -ra` (e, para Phase 1, `python3 scripts/validate_skills.py`).
- [ ] Lint Markdown passa: `npx markdownlint-cli2 '**/*.md'`.
- [ ] Skill `analyze` roda e reporta zero drift entre spec / plan / código.
- [ ] Hand-off para `requesting-code-review` para abrir o PR.
