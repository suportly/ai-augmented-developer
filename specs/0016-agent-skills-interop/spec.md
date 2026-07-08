# Feature specification: Interoperabilidade com o padrão aberto Agent Skills

> This file is produced by the `specify` skill (or by `aiadev init --feature <name>` as a stub). Keep it focused on **what** and **why** — planning and code belong in `plan.md` and `tasks.md`.

**Branch:** `feature/agent-skills-interop`
**Created:** 2026-07-08
**Status:** Draft <!-- Draft | In review | Approved | Implemented | PR Open | Merged -->
**Spec ID:** 0016 <!-- auto-incrementing integer -->
**Language:** pt-BR <!-- BCP-47 tag; every downstream artifact in this feature is written in this language. -->

---

<!-- section: Problem -->
## Problem

Em dezembro de 2025 a spec de Agent Skills virou padrão aberto (agentskills.io, governada via Agentic AI Foundation) e foi adotada por Claude Code, Codex CLI, Cursor, Gemini CLI, Copilot e outras ferramentas — exatamente as plataformas que o `aiadev sync` já suporta. O frontmatter das skills deste framework, porém, usa cinco campos proprietários em nível de topo (`version`, `inputs`, `outputs`, `requires`, `handoffs`) que estão **fora** da spec aberta; ferramentas que validam contra o padrão podem rejeitá-los ou ignorá-los silenciosamente. Ao mesmo tempo, três oportunidades da mesma onda de padronização ficaram na mesa: (1) `.claude/rules/*.md` agora tem carregamento condicional nativo por `paths:` — as rules cross-cutting do framework gastam contexto global mesmo quando irrelevantes; (2) `AGENTS.md` virou o artefato de convenção cross-tool (60k+ repos) e o Claude Code passou a lê-lo, mas o sync ainda trata o agent file por plataforma sem uma fonte canônica única; (3) os manifests de plugin do Claude Code (`.claude-plugin/plugin.json`, `marketplace.json`) existem no repo mas são escritos à mão, já estão dessincronizados do `VERSION` (dizem `1.0.0`; o framework está em `0.20.0`) e não são validados por nada no CI.

<!-- section: Reconnaissance -->
## Reconnaissance

- **skill frontmatter schema** — entry: `schemas/skill-frontmatter.schema.json` · auth: none · integração: `additionalProperties: false` com os campos proprietários (`version`, `inputs`, `outputs`, `requires`, `handoffs`) enumerados em nível de topo; sem `metadata` nem `compatibility`. Consumido por `src/aiadev/validate.py` (via helper `skill_frontmatter_schema` em `src/aiadev/paths.py`) e pelo fallback `scripts/validate_skills.py`.
- **skills do catálogo** — entry: `skills/implement/SKILL.md` · auth: none · integração: frontmatter representativo com os 5 campos proprietários; 16 skills no catálogo raiz + 6 em `presets/django-drf-react/skills/`; algumas usam só `name`+`description` (`skills/finishing-a-branch/SKILL.md`) e `skills/frontend-design/SKILL.md` já usa `license` (campo que É da spec aberta).
- **rules** — entry: `rules/code-style.md` · auth: none · integração: 5 rules com frontmatter `description`+`alwaysApply: true` e 2 sem frontmatter (`rules/terse-mode.md`, `rules/slash-commands.md`); instaladas em todos os projetos por `src/aiadev/framework_artifacts.py` (`iter_framework_artifacts`), com destino por plataforma via `resolve_target(role="rule")` — nota: Cursor grava `.cursor/rules/<n>.mdc`.
- **platform handlers do sync** — entry: `src/aiadev/commands/sync.py` · auth: none · integração: 5 plataformas (`claude-code`, `cursor`, `codex`, `opencode`, `gemini`) com handlers em `src/aiadev/platforms/`; o mapa `_PLATFORM_AGENT_FILE` já emite `AGENTS.md` para cursor/codex/opencode (renderizado do `CLAUDE.md` do preset, com skip por sha256 quando idêntico), `CLAUDE.md` para claude-code e `GEMINI.md` para gemini; o bloco `<!-- aiadev:auto-stack -->` de `src/aiadev/project_introspect.py` é o mecanismo existente de regeneração de bloco em agent file.
- **manifests de plugin** — entry: `.claude-plugin/plugin.json` · auth: none · integração: `plugin.json` + `.claude-plugin/marketplace.json` + `.cursor-plugin/plugin.json` escritos à mão em `version: 1.0.0` (dessincronizados de `VERSION` = 0.20.0); docstring de `src/aiadev/platforms/claude_code.py` declara manifests fora de escopo no v0.3; conceito paralelo de "extension" em `src/aiadev/extensions.py` + `schemas/extension-manifest.schema.json`.
- **catálogo de presets** — entry: `presets/catalog.json` · auth: none · integração: 3 presets (`lean`, `django-drf-react`, `mobile-ops`) validados por `schemas/preset-catalog.schema.json`; candidatos naturais a plugins separados num marketplace.

<!-- section: Users and stakeholders -->
## Users and stakeholders

- **Consumidores multi-ferramenta do framework** — times que usam Claude Code + Cursor/Codex/Gemini no mesmo repo; beneficiários diretos da conformidade com a spec aberta e do AGENTS.md canônico.
- **Mantenedores do framework** — deixam de manter matriz de handlers divergentes e manifests à mão; ganham validação mecânica no CI.
- **Usuários Claude Code** — instalam/atualizam o framework via `/plugin` (marketplace) em vez de `pip install` + `aiadev sync`.
- **Autores de skills de terceiros** — um frontmatter conforme o padrão vira exemplo replicável; skills do framework funcionam em qualquer runtime compatível com agentskills.io.

<!-- section: Success criteria -->
## Success criteria

- Toda `SKILL.md` do repo (catálogo + presets) valida contra a spec aberta de Agent Skills: em nível de topo, apenas campos padrão (`name`, `description`, `license`, `compatibility`, `metadata`, `allowed-tools`) e as duas extensões de runtime documentadas (`disable-model-invocation`, `argument-hint` — cl-7), com os campos proprietários do pipeline relocados sob `metadata` — e `aiadev validate` continua verificando o conteúdo relocado com a mesma severidade de hoje (nada vira warning).
- O schema do padrão aberto, vendorizado em `schemas/` (cl-2), é verificado pelo `aiadev validate` no CI e passa em 100% das skills.
- Rules com escopo de arquivo declaram `paths:` (globs) no frontmatter e o `aiadev sync` propaga a condicionalidade para cada plataforma que a suporte; em plataformas sem suporte, o comportamento atual (sempre carregada) é preservado sem erro.
- `aiadev sync` produz um único `AGENTS.md` canônico por projeto consumidor, e os agent files específicos (`CLAUDE.md`, `GEMINI.md`) não divergem dele em conteúdo gerado — qualquer bloco gerado existe numa única fonte.
- `.claude-plugin/plugin.json` e `marketplace.json` são gerados/verificados a partir de `VERSION` e do catálogo de presets: um comando (ou passo de CI) falha quando os manifests divergem da fonte, e nenhuma release futura ships com manifest órfão como o `1.0.0` atual.

<!-- section: Non-goals -->
## Non-goals

- Reescrever o **conteúdo** (corpo Markdown) de qualquer skill — a migração é exclusivamente de frontmatter.
- Abandonar ou depreciar `aiadev sync` / `pip install` — o plugin é canal adicional para Claude Code, não substituto (Codex/Gemini/Cursor continuam via sync).
- Publicação automatizada em marketplaces de terceiros (Cursor store etc.) — só os arquivos no repo.
- Catálogo comunitário de extensões remotas estilo spec-kit — fica para spec futura (onda 3 do radar).
- Adotar campos experimentais da spec aberta sem consumidor real (`allowed-tools` permanece como está hoje).

<!-- section: User stories -->
## User stories

### Story 1 — Frontmatter conforme a spec aberta (P1)

Como **autor/mantenedor de skills**, quero que o frontmatter de toda SKILL.md use apenas campos do padrão agentskills.io em nível de topo, com os campos do pipeline (`requires`, `handoffs`, `inputs`, `outputs`, `version`) preservados sob `metadata`, para que as skills instalem limpas em qualquer runtime compatível sem perder a semântica que o `aiadev` usa.

**Acceptance scenarios** (Given / When / Then, ≥ 3 per story):

1. Given uma skill migrada (ex.: `skills/implement/SKILL.md`) com `requires`/`handoffs` sob `metadata`, When eu rodo `aiadev validate`, Then a validação passa e continua reportando erro se um campo relocado tiver shape inválido (ex.: `metadata` com `handoffs` que não é lista de strings).
2. Given o repo completo migrado, When eu rodo o validador de referência do padrão em todas as SKILL.md, Then zero violações são reportadas (nenhum campo desconhecido em nível de topo, `name` == diretório, `description` presente).
3. Given uma SKILL.md nova escrita no formato **antigo** (campo proprietário em nível de topo), When eu rodo `aiadev validate`, Then a validação falha com mensagem citando o campo ofensor e a localização correta sob `metadata` (proteção contra regressão de formato).
4. Given um projeto consumidor com skills instaladas no formato antigo, When eu rodo `aiadev sync` após atualizar o framework, Then as skills instaladas são reescritas no formato novo sem intervenção manual.

### Story 2 — Rules com carregamento condicional por `paths:` (P2)

Como **consumidor do framework num projeto grande**, quero que rules com escopo claro de arquivo (ex.: convenções de API, testing) declarem `paths:` e só carreguem quando arquivos correspondentes forem tocados, para que rules irrelevantes parem de consumir contexto em toda sessão.

**Acceptance scenarios**:

1. Given a rule `rules/testing.md` com `paths: ["tests/**", "**/*.test.*"]` no frontmatter, When `aiadev sync` instala num projeto com plataforma claude-code, Then `.claude/rules/testing.md` carrega o frontmatter com `paths:` intacto e sem `alwaysApply: true`.
2. Given a mesma rule sincada para uma plataforma sem suporte a carregamento condicional, When o sync roda, Then a rule é instalada no formato que a plataforma entende (comportamento de hoje) e nenhum erro ou warning falso é emitido.
3. Given uma rule sem `paths:` (ex.: `rules/git-workflow.md`, que é global por natureza), When o sync roda em qualquer plataforma, Then o comportamento atual é preservado byte a byte (a feature é opt-in por rule).
4. Given a rule instalada no Cursor (`.cursor/rules/<n>.mdc`), When o sync roda, Then os `paths:` são traduzidos para o campo de globs nativo do formato `.mdc`.

### Story 3 — AGENTS.md como artefato canônico do sync (P1)

Como **time multi-ferramenta**, quero que o `aiadev sync` gere um único `AGENTS.md` canônico e trate `CLAUDE.md`/`GEMINI.md` como derivados, para que a orientação do agente viva numa fonte só e as 5 plataformas parem de poder divergir silenciosamente.

**Acceptance scenarios**:

1. Given um projeto com claude-code e codex detectados, When eu rodo `aiadev sync`, Then existe um `AGENTS.md` na raiz e o conteúdo gerado (bloco auto-stack incluído) aparece **somente** nele — o `CLAUDE.md` referencia o `AGENTS.md` em vez de duplicar o bloco.
2. Given um projeto que já tem `AGENTS.md` com conteúdo manual do time, When o sync roda, Then o conteúdo manual é preservado e apenas os blocos gerenciados (`<!-- aiadev:... -->`) são regenerados — mesma semântica do auto-stack block de hoje.
3. Given as plataformas cursor, codex e opencode no mesmo repo, When o sync roda, Then as três continuam lendo o mesmo `AGENTS.md` físico (sem cópias divergentes) e o resultado é idêntico ao de hoje quando os hashes coincidem.
4. Given um projeto gemini-only, When o sync roda, Then `GEMINI.md` existe como derivado fino apontando para `AGENTS.md` e nenhuma informação gerada fica exclusiva do `GEMINI.md`.

### Story 4 — Manifests de plugin gerados e verificados (P1)

Como **mantenedor**, quero que os manifests `.claude-plugin/plugin.json` e `marketplace.json` sejam derivados de `VERSION` + catálogo de presets e verificados no CI, para que o canal de distribuição via `/plugin` do Claude Code fique confiável e nunca mais dessincronize da release.

**Acceptance scenarios**:

1. Given `VERSION` = `0.21.0` e manifests dizendo `0.20.0`, When o passo de verificação roda (CI ou `aiadev doctor`), Then ele falha citando o arquivo e os dois valores divergentes.
2. Given o comando de geração executado num repo limpo, When ele termina, Then `plugin.json` reflete `VERSION` e os metadados do repo, `marketplace.json` lista o plugin core com `source` válido — e rodar o comando duas vezes é idempotente (segunda execução não muda nada).
3. Given um preset marcado `stable` no `presets/catalog.json`, When os manifests são gerados, Then o `marketplace.json` lista um plugin para esse preset (cl-4) e presets `beta`/`experimental` são omitidos — adicionar um preset stable novo ao catálogo produz o plugin correspondente sem edição manual de manifest.
4. Given um usuário Claude Code com o marketplace adicionado, When ele instala o plugin, Then as skills e agents empacotados carregam sem erro de validação de frontmatter (dependência da Story 1).

<!-- section: Clarifications -->
## Clarifications

- **cl-1 (resolved):** Os campos relocados ficam **aninhados num namespace único**: `metadata.aiadev: {version, inputs, outputs, requires, handoffs}`. Um só ponto de colisão com outros frameworks, legível nos 22 arquivos, e o schema valida o shape interno do namespace inteiro.
- **cl-2 (resolved):** O schema do padrão aberto é **vendorizado em `schemas/`** (snapshot com data/versão da spec registrada em comentário) e verificado pelo próprio `aiadev validate` — CI permanece hermético, alinhado à filosofia zero-install do repo. Atualização do snapshot é manutenção deliberada, não drift automático.
- **cl-3 (resolved):** `CLAUDE.md` (e `GEMINI.md`) dos consumidores viram **ponteiro fino** (~3 linhas apontando para `AGENTS.md`). O Claude Code lê AGENTS.md nativamente desde 2026; a divergência entre agent files é eliminada por construção. Conteúdo manual pré-existente em CLAUDE.md é preservado pelo caminho de migração (Story 3 sc2).
- **cl-4 (resolved):** **Um plugin por preset stable** além do `aiadev-core`, todos **gerados de `presets/catalog.json`** — preset novo no catálogo vira plugin no marketplace sem manifest escrito à mão (zero-toque). Presets `beta`/`experimental` ficam fora até promoção.
- **cl-5 (resolved):** **Corte seco com auto-migração**: o formato antigo vira erro no `aiadev validate` já na minor desta feature, mas `aiadev sync` reescreve automaticamente skills instaladas no formato novo (Story 1 sc4) e a mensagem de erro do validate ensina a localização correta sob `metadata.aiadev`. Justificativa: pré-1.0 + migração automática cobre o caminho comum.
- **cl-6 (resolved):** Primeira leva de `paths:` é **mínima: apenas `rules/testing.md`** (globs `tests/**`, `**/*.test.*`, `**/*_test.*`, `conftest.py`). As demais rules permanecem globais; atribuir `paths:` a outras (inclusive por preset) é evolução de conteúdo pós-merge, sem mudança de mecanismo.
- **cl-7 (resolved, descoberto durante implement/T001):** Verificação da spec publicada e do validador de referência `skills-ref` revelou três fatos que refinam cl-1/cl-2: (a) `compatibility` é **string** de 1-500 chars, não mapa; (b) a prosa da spec diz que `metadata` mapeia string→string, mas o `skills-ref` **não valida tipos de valores** — o objeto aninhado `metadata.aiadev` (cl-1) passa no validador e permanece a decisão; (c) o `skills-ref` **rejeita campos desconhecidos no topo**, mas `disable-model-invocation` e `argument-hint` são extensões de runtime que o Claude Code lê do topo e que protegem skills de deploy (`disable-model-invocation: true` em 10+ skills) — movê-los quebraria comportamento. Decisão: o snapshot vendorizado aceita os 6 campos do padrão **+ essas 2 extensões documentadas**, como desvio deliberado e registrado no `$comment` do schema; os 5 campos proprietários do pipeline continuam hard-rejeitados no topo.

<!-- section: Data touched -->
## Data touched

- `schemas/skill-frontmatter.schema.json` — reescrito para o shape do padrão aberto (+ `metadata`, `compatibility`).
- 22 arquivos `SKILL.md` (16 catálogo + 6 preset django) — frontmatter relocado; corpo intocado.
- `rules/*.md` — frontmatter ganha `paths:` opcional nas rules escolhidas em cl-6.
- `src/aiadev/validate.py`, `scripts/validate_skills.py`, `src/aiadev/platforms/*.py`, `src/aiadev/commands/sync.py`, `src/aiadev/framework_artifacts.py` — validação e sync.
- `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `.cursor-plugin/plugin.json` — passam a ser gerados/verificados.
- Projetos consumidores: `AGENTS.md` (novo canônico), `CLAUDE.md`/`GEMINI.md` (derivados), `.{claude,cursor,codex,opencode,gemini}/rules/*` e `skills/*` (formato migrado via sync).

<!-- section: Out-of-band effects -->
## Out-of-band effects

Nenhum efeito de rede em runtime. Se cl-2 resolver por dependência externa no CI, o workflow de validação passa a baixar o validador de referência (efeito restrito ao CI). A instalação via marketplace do Claude Code é iniciada pelo usuário final, não pelo framework.

<!-- section: Open risks -->
## Open risks

- **Breaking change em consumidores** (cl-5): skills customizadas no formato antigo quebram no `aiadev validate` novo. Mitigação: migração automática no `sync` (Story 1 sc4) + mensagem de erro que ensina o formato novo.
- **Spec aberta ainda evolui**: `allowed-tools` é experimental e `compatibility` é recente; acoplar demais ao snapshot atual pode exigir retrabalho. Mitigação: vendorizar o snapshot da spec com data/versão registrada.
- **Divergência AGENTS.md ↔ CLAUDE.md durante a transição** (cl-3): consumidores com CLAUDE.md customizado precisam de um caminho de migração que não descarte conteúdo manual — a semântica de blocos gerenciados precisa estar impecável antes do flip.
- **Superfície de manifests cresce**: se cl-4 resolver por plugin-por-preset, cada preset novo exige manifest novo — o gerador precisa tornar isso zero-toque ou o custo de manutenção volta.

<!-- section: Traceability -->
## Traceability

- Originating issue: pesquisa de ecossistema em sessão com mantenedor (2026-07-08) — radar out/2025→jul/2026; achados 1, 2, 3 e 10 (spec aberta Agent Skills, plugins/marketplace, `paths:` em rules, convergência AGENTS.md/AAIF).
- Related specs: [0014](../0014-bmad-inspired-evolutions/spec.md) (precedente de spec multi-story inspirado em ecossistema externo), [0015](../0015-aiadev-metrics/spec.md) (mesma onda de evolução), [extensions-system-mvp](../feature-extensions-system-mvp/spec.md) (conceito de extension que o marketplace tangencia).
- Constitution articles invoked: I (Spec-first), III (Simplicity — migração de frontmatter sem reescrever conteúdo), V (Provider pattern — handlers por plataforma continuam isolando diferenças), VII (Attribution — spec aberta e validador de referência creditados em CREDITS.md quando adotados).
