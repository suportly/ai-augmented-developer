# Implementation plan: Passo /aia:design — protótipo no Claude Design a partir das tasks

> Produced by the `plan` skill: **how** the spec is realized. Do not rewrite `spec.md` here.

**Branch:** `feature/0033-design-step`
**Date:** 2026-10-28
**Spec:** [spec.md](./spec.md)
**Plan version:** 1
**Language:** pt-BR

---

## Summary

Um passo opcional entre `tasks` e `implement`, em quatro peças pequenas. (1) A spec ganha uma linha de cabeçalho `**UI:** yes|no`, lida por máquina. (2) O código reconhece o passo: `pipeline_state` recomenda `/aia:design` quando a spec declara UI, há `tasks.md` com nenhuma task feita e falta `design.md`; o `preflight` ganha a skill `design` (exige spec, plan e tasks) e um aviso não bloqueante em `implement`; `token_metrics` classifica o papel `design`. (3) A skill `design`, o comando `/aia:design` e o template `design-template.md`: o agente escolhe as tasks de interface, o usuário confirma, o brief leva só conteúdo de tela, o protótipo é criado pelo Claude Design num subagente `design: <slug>` e o resultado vai para `design.md`. (4) Orçamento, documentação e atribuição. O percurso do pipeline não ganha arquivo; o único custo nele é a linha nova do template da spec.

## Technical context

| Field | Value |
|---|---|
| Active preset | lean (núcleo, vale para todo preset, conforme cl-1) |
| Language / runtime | Python 3.11 + Markdown |
| Primary dependencies | nenhuma nova; a ferramenta `Artifact` da plataforma, quando existe |
| Storage | `specs/<feature>/design.md` (texto) |
| Testing framework | pytest (`.venv/bin/python -m pytest`) |
| Target platform(s) | Claude Code (protótipo); Codex, Gemini, Cursor, OpenCode (wireframes em markdown) |
| Performance budget | `aiadev next` continua na casa de 0,1 s; a skill ≤ ~650 tokens, template ≤ ~300 |
| Security considerations | brief só com conteúdo de tela; confirmação antes de publicar; canvas privado |

Divergência com `tech-stack.md`/auto-stack: não há `tech-stack.md` relevante; nada a listar.

## Constitution check

| Article | Applies? | Status | Evidence |
|---|---|---|---|
| I. Spec-first | Yes | PASS | `spec.md` 0033 revisada (reviewer + `cl-1` resolvida em 2026-10-28); o brief só cita cenários e textos que estão na spec |
| II. Test-first | Yes | PASS | toda task começa por teste que falha: recomendação em `pipeline_state`, aviso do `preflight`, papel `design`, frases-chave da skill, orçamento |
| III. Simplicity | Yes | PASS | sem CLI novo (`aiadev design brief` é non-goal), sem heurística de UI no código, sem provider; um campo de cabeçalho e uma skill |
| IV. Evidence over claims | Yes | PASS | PR lista os comandos; medição do orçamento antes/depois; o custo do passo fica mensurável por papel |
| V. Provider pattern | No | N/A | a ferramenta `Artifact` é da plataforma, não um provider do framework; nenhum provider adicionado |
| VI. Privacy by design | Yes | PASS | regra e teste: brief sem caminhos, commits, ids de task ou módulos internos; confirmação antes de publicar; canvas privado |
| VII. Attribution | No | N/A | nenhum material adaptado de outro projeto; o formato do canvas é delegado ao próprio tipo, sem cópia |
| Preset-specific articles | No | N/A | passo genérico, fora de qualquer preset |

## Architecture decisions

- **Decisão:** a UI é declarada por uma linha de cabeçalho `**UI:** yes|no` no `templates/spec-template.md`, lida por regex como `**Branch:**` e `**Language:**`; ausente ou `no` = sem UI. **Rationale:** declaração explícita, barata de ler (sem varrer a spec), e specs antigas continuam valendo. **Trade-off:** o template cresce alguns tokens no percurso (`specify`); mede-se e, se passar da folga do teto do percurso, sobe só o excesso, com razão.
- **Decisão:** `/aia:design` só é recomendado quando UI = yes, `tasks.md` existe, nenhuma task está `done` e não há `design.md`. **Rationale:** depois de começar a implementar, recomendar design seria ruído; o usuário ainda pode rodar o comando à mão. **Trade-off:** quem já implementou metade sem design não é lembrado.
- **Decisão:** o aviso do `preflight implement` é `would_abort=False`. **Rationale:** a spec exige que nenhum gate seja enfraquecido ou criado como bloqueio; é só lembrete. **Trade-off:** pode ser ignorado, aceito.
- **Decisão:** a skill pede o tipo de protótipo pela chamada `Artifact` com `action: quickstart` e `intent: design`, e segue o resultado, em vez de fixar a URL do tipo no texto. **Rationale:** a URL e o contrato do canvas mudam; o quickstart devolve o tipo vigente. **Trade-off:** depende de a plataforma expor o quickstart; sem a ferramenta, cai no caminho de wireframes (Story 5).
- **Decisão:** o protótipo é criado por subagente com `description` `design: <slug>`; novo papel `design` em `token_metrics`. **Rationale:** gerar artboards é volumoso, e o subagente devolve só o link e o mapa à thread principal (precedente da 0031); o prefixo permite medir o custo por papel. **Trade-off:** mais um papel nas tabelas de métricas.
- **Decisão:** a skill `design` e o comando entram no núcleo e na listagem de todo preset; `skills/design` fica fora de `docs/pipeline-path.yaml`. **Rationale:** `cl-1` (autorização do mantenedor); precedente de `task-context`. **Trade-off:** custo fixo de instrução, medido e registrado.
- **Decisão:** `design` entra em `PIPELINE_SKILLS` do `preflight`, mas não no `PIPELINE_SKILLS` de `_tooling/skill_loader.py`. **Rationale:** o segundo define as ferramentas MCP (hoje 8, com testes que fixam o número); o passo opcional não precisa ser exposto por MCP. **Trade-off:** o passo não aparece no servidor MCP.

## Project structure changes

```text
skills/design/SKILL.md                      (new)
commands/design.md                          (new)
templates/design-template.md                (new, lido só sob demanda)
templates/spec-template.md                  (modified: linha **UI:**)
src/aiadev/pipeline_state.py                (modified: campo ui, recomendação /aia:design)
src/aiadev/commands/next.py                 (modified: linha "ui:" no estado, se necessário)
src/aiadev/preflight.py                     (modified: skill design, aviso em implement, template)
src/aiadev/token_metrics.py                 (modified: papel design)
docs/metrics.md                             (modified: papel design)
docs/instruction-budget.json                (modified: tetos de listagem, skill:design, razão)
CREDITS.md                                  (sem mudança)
CHANGELOG.md                                (modified)
README.md                                   (modified: skill e comando)
CLAUDE.md                                   (modified: linha na tabela de skills)
tests/test_design_state.py                  (new)
tests/test_design_preflight.py              (new)
tests/test_design_skill.py                  (new)
tests/test_design_budget.py                 (new)
tests/test_dispatch_description_convention.py  (modified: design:)
tests/test_token_metrics.py                 (modified: papel design)
```

## Phase breakdown

### Phase 1 — Código: estado, preflight e papel

- Testes que falham: `pipeline_snapshot` recomenda `/aia:design` só com UI yes + `tasks.md` + zero tasks done + sem `design.md`; volta a `/aia:implement` com `design.md`; igual a hoje sem UI; `preflight design` exige spec, plan e tasks; `preflight implement` avisa (código 0) com UI yes e sem `design.md`; `design:` é classificado como papel `design`.
- Implementar o mínimo em `pipeline_state.py`, `preflight.py`, `token_metrics.py` e a linha `**UI:**` no template da spec.

### Phase 2 — Skill, comando e template

- Testes que falham: a skill existe, valida, tem as regras (lista de tasks de interface confirmada pelo usuário, brief só com conteúdo de tela e sem caminho/commit/id/módulo, confirmação antes de publicar, canvas privado, subagente `design: <slug>`, quickstart `intent: design`, emenda de tasks só com aprovação, degradação para wireframes, nenhum link falso na falha); o comando existe e invoca a skill; o template tem os blocos link, mapa e lacunas.
- Escrever `skills/design/SKILL.md`, `commands/design.md` e `templates/design-template.md`.

### Phase 3 — Orçamento e documentação

- Teste que falha: medir com `scripts/instruction_budget.py --check`; os tetos de `skills` e `commands` sobem exatamente pelo custo das listagens, `total` pelo que a medição exige, `skill:design` entra com baseline == teto, e `path:total` só muda pela linha do template (excesso, se houver, com razão).
- Atualizar `docs/instruction-budget.json` à mão (nunca `--write-baseline --force`), CHANGELOG, README, CLAUDE.md e `docs/metrics.md`.

## Risks and mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Brief vaza contexto interno | Med | High | regra explícita, confirmação antes de publicar, teste que fixa as frases |
| Linha `**UI:**` estoura a folga do teto do percurso | Med | Low | medir; subir só o excesso, com razão |
| `design` em `PIPELINE_SKILLS` quebra testes que enumeram skills | Med | Low | rodar a suíte; manter o MCP em 8 |
| Plataforma sem `Artifact` | High | Med | caminho de wireframes testado por frases-chave na skill |
| Canvas muda de contrato | Low | Med | skill delega o formato ao tipo via quickstart e não copia regras |

## Complexity tracking

Nenhuma linha `FAIL`; vazio justificado.

## Hand-off to `tasks`

Next skill: `tasks`. Constitution Check completo, Complexity tracking justificado vazio, delta de estrutura conferido contra `preflight.py`, `pipeline_state.py` e `token_metrics.py`.
