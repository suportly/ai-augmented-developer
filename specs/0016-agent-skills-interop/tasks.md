# Tasks: Interoperabilidade com o padrão aberto Agent Skills

> Produced by the `tasks` skill from an approved `plan.md`. Consumed by `implement`.

**Branch:** `feature/agent-skills-interop`
**Plan:** [plan.md](./plan.md)
**Generated:** 2026-07-08
**Language:** pt-BR <!-- mirrors spec.md; write task descriptions in this language. -->

---

## How to read this file

- Tasks are ordered. `implement` runs them top-to-bottom.
- One task = one commit. The commit message starts with the task id.
- Each task links back to the spec acceptance scenarios it exercises.
- `Status` is one of: `pending`, `in_progress`, `blocked`, `done`. Owned by the `implement` skill — it flips `pending` → `done` inside each task's commit. Do not edit by hand; manual edits are overwritten on the next `implement` run.

## Task list

**Fase 1 — Schema e migração de frontmatter (Story 1)**

### T001 — Vendorizar snapshot do schema Agent Skills

- **Status:** done
- **Depends on:** —
- **Files:**
  - create: `schemas/agent-skills.schema.json`
  - test: `tests/test_agent_skills_schema.py`
- **Spec scenarios:** Story 1 scenario 2
- **Acceptance:**
  - [ ] Failing test written and observed failing for the stated reason (schema ausente).
  - [ ] Snapshot vendorizado com data/versão da spec em `$comment`; valida frontmatter mínimo (`name`+`description`) e rejeita campo proprietário em nível de topo.
  - [ ] No other existing test regresses.
  - [ ] Commit message: `feat(schemas): T001 vendorizar snapshot do schema Agent Skills`.
- **Notes:**
  Campos padrão: `name` (== diretório), `description`, `license`, `compatibility`, `metadata` (mapa), `allowed-tools`. ADR-2/ADR-3: este schema é a validação de conformidade EXTERNA; não incluir shape interno do aiadev aqui.

### T002 — Reescrever skill-frontmatter.schema.json no shape novo

- **Status:** done
- **Depends on:** —
- **Files:**
  - modify: `schemas/skill-frontmatter.schema.json`
  - test: `tests/test_skill_frontmatter_schema.py`
- **Spec scenarios:** Story 1 scenario 1
- **Acceptance:**
  - [ ] Failing test written and observed failing for the stated reason (schema atual rejeita `metadata`).
  - [ ] Schema novo aceita `metadata.aiadev.{version,inputs,outputs,requires,handoffs}` (shapes atuais preservados como `$defs`), mantém `additionalProperties: false` no topo, e rejeita `metadata.aiadev.handoffs` com item não-string.
  - [ ] No other existing test regresses (testes que usam o shape antigo são atualizados nesta task).
  - [ ] Commit message: `feat(schemas): T002 skill-frontmatter no shape do padrão com metadata.aiadev`.
- **Notes:**
  ADR-1. Os 5 campos proprietários saem do nível de topo. `disable-model-invocation` e `argument-hint` são reconhecidos por runtimes reais — mantê-los no topo só se o snapshot do padrão os aceitar; caso contrário, movê-los para `metadata.aiadev` também (decidir pelo snapshot de T001).

### T003 — Migrador puro de frontmatter (antigo → novo)

- **Status:** done
- **Depends on:** T002
- **Files:**
  - create: `src/aiadev/frontmatter_migrate.py`
  - test: `tests/test_frontmatter_migrate.py`
- **Spec scenarios:** Story 1 scenario 4
- **Acceptance:**
  - [ ] Failing test written and observed failing for the stated reason (módulo inexistente).
  - [ ] `migrate_frontmatter(dict) -> tuple[dict, bool]` move os campos proprietários para `metadata.aiadev`, é no-op (changed=False) para frontmatter já conforme, preserva `license`/`allowed-tools`/chaves `metadata` de terceiros, e é idempotente (migrar duas vezes == migrar uma).
  - [ ] No other existing test regresses.
  - [ ] Commit message: `feat(aiadev): T003 migrador puro de frontmatter antigo→novo`.
- **Notes:**
  ADR-4: função pura sem filesystem; a serialização YAML preservando o corpo do arquivo fica em helper separado no mesmo módulo (`migrate_skill_file(path) -> bool`).

### T004 — Migração one-shot dos 22 SKILL.md do repo

- **Status:** done
- **Depends on:** T003
- **Files:**
  - modify: `skills/*/SKILL.md` (16), `presets/django-drf-react/skills/*/SKILL.md` (6)
  - test: `tests/test_skills_conformance.py`
- **Spec scenarios:** Story 1 scenario 2
- **Acceptance:**
  - [ ] Failing test written and observed failing for the stated reason (teste de conformidade repo-wide: nenhum SKILL.md pode ter campo proprietário no topo; falha nos 22 arquivos).
  - [ ] Migração aplicada via `frontmatter_migrate`; corpo Markdown byte-idêntico (só frontmatter muda); as 11 skills de `presets/mobile-ops/` passam sem modificação.
  - [ ] No other existing test regresses.
  - [ ] Commit message: `feat(skills): T004 migrar frontmatter dos 22 SKILL.md para metadata.aiadev`.
- **Notes:**
  Rodar a migração com o próprio módulo de T003 (não à mão) — é o ensaio do caminho do consumidor.

### T005 — Dupla validação no aiadev validate + erro didático

- **Status:** done
- **Depends on:** T001, T004
- **Files:**
  - modify: `src/aiadev/validate.py`, `src/aiadev/paths.py`
  - test: `tests/test_validate_dual_schema.py`
- **Spec scenarios:** Story 1 scenario 1, scenario 3
- **Acceptance:**
  - [ ] Failing test written and observed failing for the stated reason (formato antigo hoje passa; deve falhar com mensagem citando o campo e a localização sob `metadata.aiadev`).
  - [ ] `aiadev validate` valida cada SKILL.md contra o snapshot do padrão E o schema interno, reportando a origem (padrão vs aiadev) em cada erro; repo inteiro passa.
  - [ ] No other existing test regresses.
  - [ ] Commit message: `feat(validate): T005 dupla validação (padrão + metadata.aiadev) com erro didático`.
- **Notes:**
  ADR-3 + cl-5 (corte seco). A mensagem para campo proprietário no topo deve dizer exatamente: mover para `metadata.aiadev.<campo>`.

### T006 — Espelhar dupla validação no fallback zero-install

- **Status:** done
- **Depends on:** T005
- **Files:**
  - modify: `scripts/validate_skills.py`
  - test: `tests/test_validate_script_parity.py`
- **Spec scenarios:** Story 1 scenario 3
- **Acceptance:**
  - [ ] Failing test written and observed failing for the stated reason (script aceita formato antigo).
  - [ ] `python3 scripts/validate_skills.py` reproduz o veredito do `aiadev validate` nos mesmos fixtures (conforme passa, antigo falha).
  - [ ] No other existing test regresses.
  - [ ] Commit message: `feat(scripts): T006 validate_skills.py espelha a dupla validação`.

### T007 — Auto-migração de skills instaladas no sync

- **Status:** pending
- **Depends on:** T003
- **Files:**
  - modify: `src/aiadev/install_engine.py`, `src/aiadev/commands/sync.py`
  - test: `tests/test_sync_migrates_frontmatter.py`
- **Spec scenarios:** Story 1 scenario 4
- **Acceptance:**
  - [ ] Failing test written and observed failing for the stated reason (sync não toca skill instalada em formato antigo).
  - [ ] `aiadev sync` num workspace com skill instalada no formato antigo reescreve o frontmatter no formato novo sem alterar o corpo; segunda execução é no-op.
  - [ ] No other existing test regresses.
  - [ ] Commit message: `feat(sync): T007 auto-migração de frontmatter de skills instaladas`.

**Fase 2 — Sync: rules com `paths:` e AGENTS.md canônico (Stories 2 e 3)**

### T008 — `paths:` em rule frontmatter com propagação por plataforma

- **Status:** done
- **Depends on:** —
- **Files:**
  - modify: `src/aiadev/platforms/claude_code.py`, `src/aiadev/platforms/codex.py`, `src/aiadev/platforms/opencode.py`, `src/aiadev/platforms/gemini.py`
  - test: `tests/test_rules_paths.py`
- **Spec scenarios:** Story 2 scenario 1, scenario 2, scenario 3
- **Acceptance:**
  - [ ] Failing test written and observed failing for the stated reason (paths: hoje é copiado cru para todas as plataformas).
  - [ ] Rule com `paths:` instala intacta (sem `alwaysApply`) no claude-code; codex/opencode/gemini recebem a rule com `paths:` removido; rule sem `paths:` instala byte-idêntica ao comportamento atual em todas.
  - [ ] No other existing test regresses.
  - [ ] Commit message: `feat(platforms): T008 propagação tipada de paths: em rules`.
- **Notes:**
  ADR-6: nenhuma avaliação de glob no aiadev — só transporte da declaração.

### T009 — Tradução de `paths:` para globs no `.mdc` do Cursor

- **Status:** pending
- **Depends on:** T008
- **Files:**
  - modify: `src/aiadev/platforms/cursor.py`
  - test: `tests/test_rules_paths_cursor.py`
- **Spec scenarios:** Story 2 scenario 4
- **Acceptance:**
  - [ ] Failing test written and observed failing for the stated reason (.mdc sai sem globs).
  - [ ] Rule com `paths: [a, b]` instala em `.cursor/rules/<n>.mdc` com o campo de globs nativo do formato preenchido e `alwaysApply: false`.
  - [ ] No other existing test regresses.
  - [ ] Commit message: `feat(cursor): T009 paths: → globs no formato .mdc`.

### T010 — Primeira leva: `paths:` em rules/testing.md

- **Status:** done
- **Depends on:** T008
- **Files:**
  - modify: `rules/testing.md`
  - test: `tests/test_rules_content.py`
- **Spec scenarios:** Story 2 scenario 1
- **Acceptance:**
  - [ ] Failing test written and observed failing for the stated reason (testing.md ainda é alwaysApply).
  - [ ] `rules/testing.md` declara `paths: ["tests/**", "**/*.test.*", "**/*_test.*", "conftest.py"]` e não declara `alwaysApply`; as demais rules permanecem intocadas (verificado por hash no teste).
  - [ ] No other existing test regresses.
  - [ ] Commit message: `feat(rules): T010 paths: condicional em testing.md (cl-6)`.

### T011 — AGENTS.md como agent file canônico do sync

- **Status:** pending
- **Depends on:** —
- **Files:**
  - modify: `src/aiadev/commands/sync.py`, `src/aiadev/platforms/claude_code.py`, `src/aiadev/platforms/gemini.py`
  - test: `tests/test_agents_md_canonical.py`
- **Spec scenarios:** Story 3 scenario 1, scenario 4
- **Acceptance:**
  - [ ] Failing test written and observed failing for the stated reason (claude-code ainda escreve conteúdo pleno em CLAUDE.md).
  - [ ] Sync em projeto claude-code produz `AGENTS.md` com o conteúdo gerado (incl. bloco auto-stack) e `CLAUDE.md` wrapper de ~3 linhas apontando para ele; projeto gemini-only idem com `GEMINI.md`; cursor/codex/opencode seguem lendo o mesmo `AGENTS.md` físico.
  - [ ] No other existing test regresses.
  - [ ] Commit message: `feat(sync): T011 AGENTS.md canônico com wrappers finos (cl-3)`.
- **Notes:**
  ADR-5. `_PLATFORM_AGENT_FILE` passa a expressar destino-do-wrapper, não destino-do-conteúdo.

### T012 — Migração preservando conteúdo manual dos agent files

- **Status:** pending
- **Depends on:** T011
- **Files:**
  - modify: `src/aiadev/commands/sync.py`, `src/aiadev/project_introspect.py`
  - test: `tests/test_agents_md_migration.py`
- **Spec scenarios:** Story 3 scenario 2, scenario 3
- **Acceptance:**
  - [ ] Failing test written and observed failing for the stated reason (conteúdo manual fora de blocos gerenciados é perdido no flip).
  - [ ] Sync num projeto com `CLAUDE.md` customizado move o conteúdo manual para `AGENTS.md` uma única vez (com backup `.bak`), regenera apenas blocos `<!-- aiadev:... -->`, e round-trip (sync 2×) é idempotente; `AGENTS.md` manual pré-existente é preservado.
  - [ ] No other existing test regresses.
  - [ ] Commit message: `feat(sync): T012 migração de agent files preservando conteúdo manual`.

**Fase 3 — Manifests e marketplace (Story 4)**

### T013 — Derivação pura dos manifests de plugin

- **Status:** pending
- **Depends on:** —
- **Files:**
  - create: `src/aiadev/manifests.py`
  - test: `tests/test_manifests.py`
- **Spec scenarios:** Story 4 scenario 2, scenario 3
- **Acceptance:**
  - [ ] Failing test written and observed failing for the stated reason (módulo inexistente).
  - [ ] Funções puras derivam `plugin.json`/`marketplace.json`/`.cursor-plugin/plugin.json` de `VERSION` + metadados do repo + `presets/catalog.json`: um plugin por preset `stable` (lean, django-drf-react), `beta`/`experimental` omitidos; saída determinística e idempotente.
  - [ ] No other existing test regresses.
  - [ ] Commit message: `feat(aiadev): T013 derivação pura dos manifests de plugin (cl-4)`.

### T014 — Subcomando `aiadev manifests --check/--write`

- **Status:** pending
- **Depends on:** T013
- **Files:**
  - create: `src/aiadev/commands/manifests.py`
  - modify: `src/aiadev/cli.py`
  - test: `tests/test_manifests_command.py`
- **Spec scenarios:** Story 4 scenario 1, scenario 2
- **Acceptance:**
  - [ ] Failing test written and observed failing for the stated reason (subcomando inexistente).
  - [ ] `--check` sai 0 quando manifests batem com a derivação e 1 citando arquivo + valores divergentes (ex.: VERSION 0.21.0 vs manifest 0.20.0); `--write` regrava e é idempotente (segunda execução não muda nada, exit 0).
  - [ ] No other existing test regresses.
  - [ ] Commit message: `feat(cli): T014 subcomando aiadev manifests`.

### T015 — Gerar manifests iniciais + gate no CI

- **Status:** pending
- **Depends on:** T014, T004
- **Files:**
  - modify: `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `.cursor-plugin/plugin.json`, `.github/workflows/validate.yml`
  - test: `tests/test_manifests_in_sync.py`
- **Spec scenarios:** Story 4 scenario 1, scenario 3, scenario 4
- **Acceptance:**
  - [ ] Failing test written and observed failing for the stated reason (manifests versionados dizem 1.0.0; teste roda o equivalente a `--check` e falha).
  - [ ] Manifests regravados via `--write` (core + presets stable), `validate.yml` ganha passo `aiadev manifests --check`, e o teste `--check` passa no repo limpo.
  - [ ] No other existing test regresses.
  - [ ] Commit message: `feat(manifests): T015 manifests gerados + gate --check no CI`.
- **Notes:**
  Depende de T004 para o sc4 da Story 4 (skills empacotadas precisam validar no formato novo).

**Fase 4 — Documentação e verificação end-to-end**

### T016 — Documentação, CREDITS e CHANGELOG

- **Status:** pending
- **Depends on:** T005, T010, T012, T015
- **Files:**
  - modify: `CREDITS.md`, `CHANGELOG.md`, `README.md`, `docs/`
  - test: `tests/test_interop_docs.py`
- **Spec scenarios:** Story 1 scenario 3 (mensagem documentada), Story 3 scenario 1 (convenção documentada)
- **Acceptance:**
  - [ ] Failing test written and observed failing for the stated reason (drift tests: CREDITS sem agentskills.io; CHANGELOG sem entrada 0016).
  - [ ] `CREDITS.md` credita a spec Agent Skills (agentskills.io / Agentic AI Foundation) com URL e licença do snapshot (Article VII); `CHANGELOG.md [Unreleased]` registra as 4 stories; README/docs descrevem AGENTS.md canônico, paths: e `aiadev manifests`.
  - [ ] No other existing test regresses.
  - [ ] Commit message: `docs(interop): T016 CREDITS, CHANGELOG e docs da 0016`.

### T017 — Smoke end-to-end multi-plataforma

- **Status:** pending
- **Depends on:** T007, T009, T012, T015
- **Files:**
  - test: `tests/test_interop_end_to_end.py`
- **Spec scenarios:** Story 1 scenario 4, Story 2 scenario 2, Story 3 scenario 3, Story 4 scenario 4
- **Acceptance:**
  - [ ] Failing test written and observed failing for the stated reason (fluxo composto ainda não coberto por teste único).
  - [ ] Teste de integração: projeto sintético com `.claude/`+`.cursor/`+`.codex/` roda install+sync → um único `AGENTS.md` com bloco gerado, wrappers finos, rules com paths: corretas por plataforma, skills instaladas conformes (validadas contra o snapshot), e `aiadev manifests --check` verde.
  - [ ] No other existing test regresses.
  - [ ] Commit message: `test(interop): T017 smoke end-to-end multi-plataforma`.

## Parallelization hints

- Parallel group A (pós-T003, arquivos disjuntos): T004, T007
- Parallel group B (fases independentes entre si): {T008→T009/T010}, {T011→T012}, {T013→T014}
- Serial: T001/T002 antes de T003/T005; T016 e T017 por último.

## Post-task checklist

After every task:

- [ ] Commit message references the task id.
- [ ] Status in this file updated.

After all tasks:

- [ ] Full test suite passes (`python3 -m pytest tests/ -q` com `PYTHONPATH=src` ou install editável).
- [ ] `analyze` skill runs and reports no drift vs spec / plan.
- [ ] Hand off to `requesting-code-review` to open the PR.
