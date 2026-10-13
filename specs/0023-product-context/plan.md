# Implementation plan: skill `product` e templates de contexto de produto (mission, tech-stack, roadmap)

> Produced by the `plan` skill from an approved `spec.md`. This file describes **how** the spec will be realized. Do not rewrite `spec.md` into `plan.md`.

**Branch:** `feature/0023-product-context`
**Date:** 2026-09-24
**Spec:** [spec.md](./spec.md)
**Plan version:** 1
**Language:** pt-BR <!-- mirrors spec.md; write plan prose in this language. -->

---

## Summary

Vamos criar três templates genéricos (`mission`, `tech-stack`, `roadmap`) e uma skill de agente `product` que os preenche num projeto consumidor, em `specs/_product/`, por inferência citada a partir do repositório, no mesmo contrato de bootstrap/atualização da skill `constitution`. `specify` e `plan` passam a ler esses arquivos quando existem, sem mudar nada quando não existem. A skill é registrada nos sete lugares que listam skills por nome e instalada nas 5 plataformas pelo caminho já existente (`framework_artifacts` → handlers). Não entra em `PIPELINE_SKILLS` nem em `aiadev preflight` (cl-4). Fecha com o dogfooding: o próprio aiadev ganha seu `specs/_product/`, e um teste garante que esses arquivos ficam fora do pacote. São cerca de 14 tasks em 5 fases, quase todas em Markdown com testes pytest de forma e texto, no padrão dos testes de skill já existentes.

## Technical context

| Field | Value |
|---|---|
| Active preset | nenhum (repositório do framework; ferramentas repo-locais) |
| Language / runtime | Markdown (skills, templates) + Python 3 (testes, `scripts/generate_pipeline_reference.py`) |
| Primary dependencies | nenhuma nova; `pytest`, `jsonschema`, `pyyaml` já presentes |
| Storage | arquivos Markdown: `templates/`, `skills/product/`, e `specs/_product/` no consumidor |
| Testing framework | pytest (`tests/`), `aiadev validate`, `markdownlint-cli2` no CI |
| Target platform(s) | claude-code, cursor, codex, opencode, gemini (via `src/aiadev/platforms/`) |
| Performance budget | N/A — nenhum caminho de execução novo em código; `specify`/`plan` leem até 3 arquivos extras |
| Security considerations | a skill não lê `.env*`, chaves nem credenciais; nada sai da máquina (Artigo VI) |

## Constitution check

| Article | Applies? | Status | Evidence |
|---|---|---|---|
| I. Spec-first | Yes | PASS | `spec.md` sem marcadores, cl-1…cl-6 resolvidas e aprovado pelo `spec-document-reviewer` em 2026-09-24 (commit `5ac056e`). |
| II. Test-first | Yes | PASS | Toda task começa com teste que falha: forma dos templates, texto da skill, instalação nas 5 plataformas, integração com `specify`/`plan`, CREDITS e não-empacotamento (ver fases). |
| III. Simplicity | Yes | PASS | Sem parser de roadmap nesta feature (só a 0024 precisa ler o roadmap); sem configuração de caminho (`specs/_product/` fixo, cl-1); sem entrada em `PIPELINE_SKILLS` (cl-4); reaproveita `introspect()` e o contrato do `constitution`. Nenhuma dependência nova. |
| IV. Evidence over claims | Yes | PASS | A skill exige fonte citada para cada valor inferido; o PR lista `pytest`, `aiadev validate` e `python scripts/generate_pipeline_reference.py` + `pytest tests/test_pipeline_reference_drift.py` (regeneração limpa) com saída. |
| V. Provider pattern | No | N/A | Sem fronteira de rede. |
| VI. Privacy by design | Yes | PASS | Lista de exclusão de segredos no texto da skill, fixada por teste (`tests/test_product_skill.py`). |
| VII. Attribution | Yes | PASS | Templates escritos do zero; entrada de inspiração do curso SDD em `CREDITS.md`, fixada por `tests/test_credits_sdd_course.py` (cl-6). |

## Architecture decisions

- **ADR-1 — Dois modos, espelhando `constitution`.**
  Decision: `product` detecta o modo pela existência de `specs/_product/`. Sem os arquivos, entra em **bootstrap**: lê `README.md`, arquivos de pacote, `AGENTS.md`/`CLAUDE.md` e `.claude/rules/*`, renderiza os três templates com valor e fonte citada, e grava só após aprovação. Com os arquivos, entra em **atualização**: lista as seções e pergunta qual mudar, sem sobrescrever.
  Rationale: o contrato "inferir, não inventar" já existe e é conhecido pelos usuários.
  Trade-offs: não há regeneração automática; atualizar é sempre um pedido explícito.

- **ADR-2 — Caminho fixo `specs/_product/`, sem configuração (cl-1).**
  Decision: `specify`, `plan` e a própria skill usam o caminho literal.
  Rationale: `pipeline_state._list_spec_dirs` (prefixo `^\d{3,4}-`) e `metrics.iter_specs_in_window` (exige `spec.md`) já ignoram o diretório. Nenhum código de enumeração muda.
  Trade-offs: quem quiser outro local não tem como mudar (Artigo III: sem usuário nomeado).

- **ADR-3 — Gramática do roadmap só no template, sem parser (cl-2).**
  Decision: o template define `### R<NNN> — <título>` com `**Status:**`, `**Spec:**` e `**Depends on:**`, no formato bullet que `tasks_status` já usa. O parser em Python fica para a spec 0024, o primeiro código que precisa ler o roadmap.
  Rationale: nesta feature quem escreve o roadmap é a skill (Markdown) e quem lê é o agente; um parser agora não teria chamador.
  Trade-offs: a gramática só é verificada pela forma do template e pela revisão, até a 0024.

- **ADR-4 — `tech-stack.md` = decisões; auto-stack = inventário (cl-3).**
  Decision: no bootstrap, a skill semeia linguagens e frameworks a partir de `project_introspect.introspect()` (a mesma função do `aiadev sync`), citando a fonte, e pede ao humano o porquê e as alternativas descartadas. O `plan` compara `tech-stack.md` com o bloco `<!-- aiadev:auto-stack -->` e lista as divergências sem resolvê-las. `sync` e `project_introspect` não mudam.
  Rationale: separa intenção de realidade sem uma segunda fonte automática.
  Trade-offs: a comparação é feita pelo agente lendo dois textos, não por código.

- **ADR-5 — `product` entra na quick-reference antes de `specify`.**
  Decision: acrescentar `product` ao `PIPELINE` de `scripts/generate_pipeline_reference.py`, antes de `specify`, com `handoffs: [specify]`, e ao `CLAUDE.md` na tabela "Skill to invoke". O teste de drift exige que as duas listas batam.
  Rationale: é o primeiro passo de um projeto novo e deve aparecer no `/aia:help`. O orçamento de 24 linhas do reference comporta mais uma linha (hoje são cerca de 14).
  Trade-offs: `product` aparece como "etapa" do pipeline, embora rode uma vez por projeto e não por feature. A descrição da linha deixa isso claro.

- **ADR-6 — Testes de texto e forma, no padrão da casa.**
  Decision: skills e templates são Markdown, então os testes fixam o comportamento pelo texto (como `tests/test_specify_skill_has_recon_step.py`) e pela instalação real em diretório temporário (como `tests/test_install_cursor.py`). A regressão de "sem arquivos, nada muda" é coberta por um teste que exige que o texto novo de `specify`/`plan` seja condicional ("quando existir"), mais a suíte e2e atual (`tests/test_e2e_specify.py`, `tests/test_e2e_pipeline.py`) verde sem alteração.
  Rationale: é o único jeito verificável de testar instruções de agente sem chamar LLM.
  Trade-offs: texto certo não garante agente obediente; a revisão humana da primeira execução (dogfooding, fase 5) cobre essa lacuna.

- **ADR-7 — Dogfooding com garantia de não empacotamento (cl-5).**
  Decision: gerar `specs/_product/*` do próprio aiadev rodando a skill nova, como a última fase. Um teste garante que `MANIFEST.in` não inclui `specs`, que `COPY_PLAN` em `scripts/sync_assets.py` não inclui `specs`, e que `framework_artifacts.iter_framework_artifacts` não emite nenhum caminho sob `specs/`.
  Rationale: primeira execução real da skill e roadmap real para a 0024 e a 0028.
  Trade-offs: o conteúdo do aiadev fica no repositório (não no pacote) e precisa de manutenção.

## Project structure changes

```text
templates/mission-template.md                   (new)
templates/tech-stack-template.md                (new)
templates/roadmap-template.md                   (new)
templates/README.md                             (modified — tabela Produced/Consumed)
skills/product/SKILL.md                         (new)
commands/product.md                             (new — /aia:product)
skills/specify/SKILL.md                         (modified — lê mission/roadmap quando existirem)
skills/plan/SKILL.md                            (modified — lê tech-stack; compara com auto-stack)
skills/using-ai-augmented-developer/SKILL.md    (modified — tabela de skills)
templates/agent-file-template.md                (modified — tabela de estágios)
presets/lean/CLAUDE.md                          (modified — linha do pipeline)
rules/slash-commands.md                         (modified — /aia:product)
CLAUDE.md                                       (modified — tabela "Skill to invoke")
scripts/generate_pipeline_reference.py          (modified — PIPELINE inclui product)
docs/pipeline-reference.md                      (regenerated)
README.md                                       (modified — What's Inside + Basic Workflow)
CREDITS.md                                      (modified — inspiração: curso SDD)
CHANGELOG.md                                    (modified — [Unreleased] cita 0023)
specs/_product/mission.md                       (new — dogfooding)
specs/_product/tech-stack.md                    (new — dogfooding)
specs/_product/roadmap.md                       (new — dogfooding)
tests/test_product_templates.py                 (new)
tests/test_product_skill.py                     (new)
tests/test_product_install_platforms.py         (new)
tests/test_specify_plan_product_context.py      (new)
tests/test_product_registries.py                (new)
tests/test_credits_sdd_course.py                (new)
tests/test_product_not_packaged.py              (new)
```

`CLAUDE.md` muda junto com `README.md` e não toca a `constitution.md`, como pede a seção "When you change this file" do `CLAUDE.md`.

## Phase breakdown

### Phase 1 — Templates

- Três templates com anchors `<!-- section: … -->` estáveis e apenas placeholders `{{UPPER_SNAKE}}`, comentários-guia e headings. `mission`: por quê, para quem, problema, fora de escopo. `tech-stack`: linguagens, frameworks, decisões com porquê e alternativas descartadas. `roadmap`: gramática da cl-2. Os três com header `Language:`.
- Teste de "sem conteúdo de produto": toda linha fora de comentário HTML é heading, placeholder ou esqueleto de tabela/lista.
- Tabela do `templates/README.md` atualizada.

### Phase 2 — Skill `product` e registros

- `skills/product/SKILL.md` com frontmatter válido nos dois schemas (`metadata.aiadev`: inputs, outputs em `specs/_product/*`, `requires` com os três templates, `handoffs: [specify]`), os dois modos do ADR-1, a regra de fonte citada, marcadores `cl-N` para o que não é inferível e a lista de exclusão de segredos.
- `commands/product.md` e os sete registros: `CLAUDE.md`, `using-ai-augmented-developer`, `agent-file-template`, `presets/lean/CLAUDE.md`, `rules/slash-commands.md`, o gerador + o `docs/pipeline-reference.md` regenerado, e o README.
- Instalação verificada nas 5 plataformas, com teste parametrizado por plataforma.

### Phase 3 — `specify` e `plan` consomem o contexto

- `specify`: ler `mission.md` e `roadmap.md` quando existirem; citar a entrada `R<NNN>` em *Traceability*; pausar em conflito com o fora-de-escopo da missão, como o "premise mismatch" já existente.
- `plan`: preencher *Technical context* a partir de `tech-stack.md`; transformar desvio em ADR; listar divergências com o bloco auto-stack.
- Toda instrução nova é condicional à existência do arquivo, e a suíte e2e continua verde sem alteração.

### Phase 4 — Atribuição e documentação

- Entrada em `CREDITS.md` ("Direct inspirations"), no formato das entradas de BMAD e headroom, dizendo que só a ideia foi adaptada.
- `CHANGELOG.md [Unreleased]` citando 0023.

### Phase 5 — Dogfooding

- Rodar `product` neste repositório e revisar a saída com o mantenedor, gravando `specs/_product/*`. Divergências entre o que a skill inferiu e a realidade viram ajustes no texto da skill, dentro desta branch.
- Teste de não empacotamento do ADR-7.

## Risks and mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Agente inventa missão ou público a partir de pistas fracas | Med | High | Regra "cita a fonte ou marca `cl-N`" no texto da skill, fixada por teste; o dogfooding da fase 5 é a primeira checagem real. |
| `product` na quick-reference estoura o orçamento de linhas | Low | Low | `test_reference_line_budget` roda na fase 2; hoje há folga de cerca de 10 linhas. |
| Texto novo de `specify`/`plan` muda o comportamento sem arquivos de produto | Med | Med | Instruções condicionais fixadas por teste; e2e atual como regressão. |
| Divergência tech-stack × auto-stack vira ruído em todo plano | Med | Low | Só divergências de linguagem ou framework; dependências menores ficam fora. |
| Dogfooding vaza para o pacote | Low | High | `tests/test_product_not_packaged.py` (ADR-7). |

## Complexity tracking

> Nenhuma linha do Constitution Check está `FAIL`; sem waivers.

| Article waived | Reason | Alternatives considered | Reviewer |
|---|---|---|---|
| | | | |

## Hand-off to `tasks`

The next skill is `tasks`. It consumes this plan and produces `tasks.md`.
Pre-conditions before hand-off:

- [x] Constitution Check is fully populated, no blank rows.
- [x] Complexity tracking is filled or empty-and-justified.
- [x] Project structure delta is accurate.
