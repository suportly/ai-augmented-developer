# Implementation plan: Interoperabilidade com o padrão aberto Agent Skills

> Produced by the `plan` skill from an approved `spec.md`. This file describes **how** the spec will be realized. Do not rewrite `spec.md` into `plan.md`.

**Branch:** `feature/agent-skills-interop`
**Date:** 2026-07-08
**Spec:** [spec.md](./spec.md)
**Plan version:** 1
**Language:** pt-BR <!-- mirrors spec.md; write plan prose in this language. -->

---

## Summary

Vamos alinhar o framework ao padrão aberto Agent Skills em quatro frentes que compartilham um mesmo tema (conformidade + fonte única): (1) reescrever `schemas/skill-frontmatter.schema.json` no shape do padrão com os campos do pipeline aninhados sob `metadata.aiadev`, migrar os 22 `SKILL.md` via um migrador puro reutilizado depois pelo `sync` (corte seco, cl-5); (2) aceitar `paths:` opcional nas rules com propagação por plataforma (passthrough no claude-code, tradução para globs no `.mdc` do Cursor, no-op nas demais); (3) promover `AGENTS.md` a agent file canônico do sync com `CLAUDE.md`/`GEMINI.md` como ponteiros finos; (4) gerar e verificar os manifests de plugin a partir de `VERSION` + `presets/catalog.json` via novo subcomando `aiadev manifests`. O trabalho aterrissa em ~30 arquivos (22 são migração mecânica de frontmatter) e se divide em 4 fases / previsão de 15-17 tasks.

## Technical context

| Field | Value |
|---|---|
| Active preset | nenhum (repo do próprio framework) |
| Language / runtime | Python 3.11+ (click, PyYAML, jsonschema) + Markdown |
| Primary dependencies | nenhuma nova em runtime; snapshot do schema agentskills.io vendorizado (sem dependência de rede) |
| Storage | nenhum |
| Testing framework | pytest |
| Target platform(s) | CLI multiplataforma; artefatos p/ claude-code, cursor, codex, opencode, gemini |
| Performance budget | n/a (sync/validate permanecem O(nº de arquivos), sem rede) |
| Security considerations | manifests são públicos por natureza; nenhum segredo tocado; sem telemetria nova |

## Constitution check

| Article | Applies? | Status | Evidence |
|---|---|---|---|
| I. Spec-first | Yes | PASS | `spec.md` 0016 aprovado pelo spec-document-reviewer em 2026-07-08 (`.review-log.jsonl`), cl-1..cl-6 resolvidos |
| II. Test-first | Yes | PASS | toda task de código começa com teste falhando (pytest); migração dos 22 SKILL.md é guiada por teste de conformidade que falha antes da migração |
| III. Simplicity | Yes | PASS | duas unidades novas com ≥ 2 consumidores cada: `frontmatter_migrate` (migrador one-shot + `sync`) e `manifests` (subcomando + CI); nenhuma abstração especulativa |
| IV. Evidence over claims | Yes | PASS | conformidade verificada mecanicamente no CI (`aiadev validate` contra schema vendorizado); PR test plan enumera comandos executados |
| V. Provider pattern | Yes | PASS | diferenças por plataforma (paths:→.mdc, agent file, ponteiros) ficam isoladas em `src/aiadev/platforms/*.py`; nenhum if-por-plataforma fora dos handlers |
| VI. Privacy by design | No | N/A | nenhum dado sensível, log ou telemetria tocados |
| VII. Attribution | Yes | PASS | `CREDITS.md` ganha entrada para a spec Agent Skills (agentskills.io / Agentic AI Foundation) quando o snapshot for vendorizado |
| Preset-specific articles | n/a | N/A | repo do framework, sem preset ativo |

## Architecture decisions

- **ADR-1 — Namespace único `metadata.aiadev` (cl-1).**
  Decision: os campos `version`, `inputs`, `outputs`, `requires`, `handoffs` migram para `metadata.aiadev.*`; o schema novo define o shape interno reaproveitando as definições atuais como `$defs`.
  Rationale: um só ponto de colisão com outros frameworks; validação continua estrita (nada vira mapa livre não-validado).
  Trade-offs: um nível a mais de indentação nos 22 arquivos; ferramentas que exibem `metadata` cru mostram um objeto aninhado.

- **ADR-2 — Snapshot vendorizado do schema do padrão (cl-2).**
  Decision: novo `schemas/agent-skills.schema.json` vendorizado com data/versão da spec registrada em `$comment`; `aiadev validate` valida cada SKILL.md contra **dois** schemas: o do padrão (conformidade externa) e o interno (shape de `metadata.aiadev`).
  Rationale: CI hermético (filosofia zero-install do repo); atualização do snapshot é decisão deliberada com diff revisável.
  Trade-offs: risco de defasagem em relação ao padrão vivo — mitigado registrando a versão e revisando a cada minor.

- **ADR-3 — Dupla validação em vez de schema único.**
  Decision: não fundir os dois schemas num só; `validate.py` roda os dois em sequência e reporta a origem (padrão vs aiadev) em cada erro.
  Rationale: quando o padrão evoluir, o snapshot troca sem tocar a validação interna — e a mensagem de erro diz ao autor qual contrato ele violou.
  Trade-offs: dois arquivos de schema para manter; custo de execução desprezível.

- **ADR-4 — Migrador puro compartilhado (cl-5).**
  Decision: função pura `migrate_frontmatter(dict) -> tuple[dict, bool]` em módulo novo `src/aiadev/frontmatter_migrate.py`; consumida (a) pelo passo one-shot que migra os 22 arquivos do repo e (b) pelo `install_engine`/`sync` para reescrever skills instaladas em consumidores (Story 1 sc4).
  Rationale: mesma transformação nos dois contextos elimina divergência; testável sem filesystem.
  Trade-offs: o one-shot vira código permanente — aceito, pois é exatamente o caminho de migração dos consumidores.

- **ADR-5 — AGENTS.md canônico com ponteiros finos (cl-3).**
  Decision: `_PLATFORM_AGENT_FILE` converge para `AGENTS.md` como destino do conteúdo gerado (inclusive o bloco `<!-- aiadev:auto-stack -->`); os handlers claude-code e gemini passam a emitir `CLAUDE.md`/`GEMINI.md` como wrapper de ~3 linhas apontando para `AGENTS.md`, preservando conteúdo manual pré-existente fora de blocos gerenciados.
  Rationale: divergência entre agent files eliminada por construção; cursor/codex/opencode já compartilham o mesmo arquivo físico hoje (skip por sha256) — a mudança estende o comportamento existente, não cria um novo.
  Trade-offs: quem abre `CLAUDE.md` direto vê um ponteiro; migração de consumidores com `CLAUDE.md` customizado exige mover conteúdo manual para `AGENTS.md` uma única vez (o sync faz isso preservando blocos, com backup `.bak`).

- **ADR-6 — `paths:` como passthrough tipado, não engine própria (cl-6).**
  Decision: o frontmatter de rule aceita `paths: [globs]` opcional; claude-code instala o campo intacto; cursor traduz para o campo de globs do `.mdc`; codex/opencode/gemini removem o campo na instalação (comportamento atual preservado). Nenhuma avaliação de glob acontece no aiadev.
  Rationale: o carregamento condicional é responsabilidade do runtime de cada ferramenta; o framework só transporta a declaração (Provider pattern).
  Trade-offs: em plataformas sem suporte a rule continua global — comportamento documentado, não um bug.

- **ADR-7 — Subcomando `aiadev manifests` com modos `--check`/`--write` (cl-4).**
  Decision: novo `src/aiadev/manifests.py` deriva `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` e `.cursor-plugin/plugin.json` de `VERSION`, `pyproject.toml` e `presets/catalog.json` (um plugin por preset `stable`); `--write` regrava idempotente, `--check` sai 1 em divergência e roda no CI.
  Rationale: mesma mecânica check/write dos geradores existentes no repo; presets novos viram plugins sem manifest manual.
  Trade-offs: os manifests continuam versionados no git (o Claude Code os lê do repo) — o gerador é a fonte, o arquivo é o artefato.

## Project structure changes

```text
schemas/agent-skills.schema.json                    (new)      snapshot vendorizado do padrão
schemas/skill-frontmatter.schema.json               (modified) shape novo: padrão + metadata.aiadev
src/aiadev/frontmatter_migrate.py                   (new)      migrador puro antigo→novo
src/aiadev/manifests.py                             (new)      derivação/checagem dos manifests
src/aiadev/commands/manifests.py                    (new)      subcomando aiadev manifests
src/aiadev/cli.py                                   (modified) registra o subcomando
src/aiadev/validate.py                              (modified) dupla validação + erro didático p/ formato antigo
scripts/validate_skills.py                          (modified) espelha a dupla validação (fallback zero-install)
src/aiadev/platforms/{claude_code,gemini}.py        (modified) agent file → wrapper fino; AGENTS.md canônico
src/aiadev/platforms/cursor.py                      (modified) paths: → globs no .mdc
src/aiadev/platforms/{codex,opencode}.py            (modified) strip de paths: na instalação de rule
src/aiadev/commands/sync.py                         (modified) _PLATFORM_AGENT_FILE canônico + migração de skills instaladas
src/aiadev/install_engine.py                        (modified) hook de migração de frontmatter no install de skill
skills/*/SKILL.md                        (16 files) (modified) frontmatter migrado (corpo intocado)
presets/django-drf-react/skills/*/SKILL.md (6 files)(modified) idem
presets/mobile-ops/skills/*/SKILL.md    (11 files) (unchanged) já conformes; cobertos pela validação nova
rules/testing.md                                    (modified) ganha paths: (cl-6)
.claude-plugin/plugin.json                          (generated) via aiadev manifests --write
.claude-plugin/marketplace.json                     (generated) idem (core + 2 presets stable)
.cursor-plugin/plugin.json                          (generated) idem
.github/workflows/validate.yml                      (modified) passo manifests --check
CREDITS.md                                          (modified) atribuição agentskills.io (Article VII)
CHANGELOG.md, README.md, docs/                      (modified) registro e documentação
tests/test_frontmatter_migrate.py                   (new)
tests/test_manifests.py                             (new)
tests/test_validate*.py, tests/test_install*.py,
tests/test_sync*.py                                 (modified) cobrem shape novo, wrappers e paths:
```

## Phase breakdown

### Phase 1 — Schema e migração de frontmatter (Story 1)

- Vendorizar `schemas/agent-skills.schema.json`; reescrever `skill-frontmatter.schema.json` (padrão + `metadata.aiadev` via `$defs`).
- `frontmatter_migrate.py` puro com testes; migração one-shot dos 22 arquivos com campos proprietários; dupla validação em `validate.py` + `scripts/validate_skills.py` com erro didático para formato antigo. Nota de escopo: as 11 skills de `presets/mobile-ops/skills/` entram na validação nova (o sweep de `iter_skill_files` cobre `presets/*/skills`), mas já são conformes (usam só `name`+`description`) — nenhuma migração de conteúdo, apenas cobertura do teste de conformidade repo-wide.
- Hook de migração no `install_engine`/`sync` (Story 1 sc4).

### Phase 2 — Sync: AGENTS.md canônico e rules com `paths:` (Stories 2 e 3)

- `_PLATFORM_AGENT_FILE` converge para `AGENTS.md`; wrappers finos em claude-code/gemini com preservação de conteúdo manual e blocos gerenciados.
- `paths:` em rule frontmatter: passthrough claude-code, tradução `.mdc` cursor, strip nas demais; `rules/testing.md` recebe a primeira leva.

### Phase 3 — Manifests e marketplace (Story 4)

- `manifests.py` + subcomando `--check`/`--write`; geração inicial versionada (core + presets stable do `catalog.json`); passo `--check` no workflow de CI.

### Phase 4 — Documentação e verificação end-to-end

- CREDITS.md (Article VII), CHANGELOG, README, docs; smoke end-to-end: `aiadev sync` num projeto sintético multi-plataforma + instalação do plugin local no Claude Code.

## Risks and mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Consumidores com skills custom no formato antigo quebram no validate | Med | Med | auto-migração no sync (ADR-4) + mensagem de erro que ensina o formato novo + release notes destacadas |
| Padrão agentskills.io evolui e o snapshot defasa | Med | Low | versão/data no `$comment` do snapshot; revisão a cada minor (ADR-2) |
| Wrapper fino descarta conteúdo manual de CLAUDE.md customizado | Low | High | migração move conteúdo manual para AGENTS.md preservando blocos gerenciados, com backup `.bak`; teste dedicado de round-trip |
| Runtime de alguma plataforma rejeitar frontmatter de rule com campo desconhecido | Low | Med | strip explícito de `paths:` nas plataformas sem suporte (ADR-6), validado por teste por plataforma |
| Superfície de manifests cresce a cada preset novo | Med | Low | ADR-7: manifests 100% derivados de `catalog.json` — preset stable novo vira plugin sem manifest manual; `--check` no CI impede drift |

## Complexity tracking

> Required when any Constitution Check row is `FAIL`. Empty table if no waivers.

| Article waived | Reason | Alternatives considered | Reviewer |
|---|---|---|---|
| | | | |

## Hand-off to `tasks`

The next skill is `tasks`. It consumes this plan and produces `tasks.md`.
Pre-conditions before hand-off:

- [x] Constitution Check is fully populated, no blank rows.
- [x] Complexity tracking is filled or empty-and-justified (sem waivers).
- [x] Project structure delta is accurate.
