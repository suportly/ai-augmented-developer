# Implementation plan: Atribuição correta da frontend-design e folga no corpo da skill

> Produced by the `plan` skill: **how** the spec is realized. Do not rewrite `spec.md` here.

**Branch:** `feature/0035-frontend-design-attribution`
**Date:** 2026-11-06
**Spec:** [spec.md](./spec.md)
**Plan version:** 1
**Language:** pt-BR

---

## Summary

Quatro mudanças pequenas. (1) `LICENSE.txt` com o texto da Apache-2.0 idêntico ao de `anthropics/skills`, na pasta da skill. (2) Frontmatter e `CREDITS.md` corrigidos: o campo `license` passa a citar a Apache-2.0, `anthropics/skills` e que o arquivo foi modificado (aviso no próprio arquivo, Apache-2.0 §4(b)), e a entrada nova do `CREDITS.md` repete a adaptação e a modificação; `name` e `description` não mudam. (3) O instalador passa a copiar o `LICENSE.txt` da pasta da skill junto do `SKILL.md`, porque hoje só `SKILL.md` e `references/**/*.md` viajam. (4) O corpo da skill é enxugado de 1.396 para no máximo 1.300 tokens sem enfraquecer nenhuma regra fixada pela 0034.

## Technical context

| Field | Value |
|---|---|
| Active preset | django-drf-react (a skill) e núcleo (instalador) |
| Language / runtime | Python 3.11 + Markdown |
| Primary dependencies | nenhuma nova |
| Storage | arquivos |
| Testing framework | pytest (`.venv/bin/python -m pytest`) |
| Target platform(s) | todas as plataformas que recebem skills |
| Performance budget | corpo da skill ≤ 1.300 tokens; `description` inalterada |
| Security considerations | nenhuma; só texto e cópia de arquivo dentro de `skills/` |

Divergência com `tech-stack.md`/auto-stack: nenhuma relevante.

## Constitution check

| Article | Applies? | Status | Evidence |
|---|---|---|---|
| I. Spec-first | Yes | PASS | `spec.md` 0035 revisada antes deste plano |
| II. Test-first | Yes | PASS | compromisso: RED observado antes de cada mudança (licença, instalador, enxugamento, créditos), registrado no PR |
| III. Simplicity | Yes | PASS | uma linha no coletor do instalador, sem mecanismo novo de licenças; nenhum texto reescrito além do enxugamento |
| IV. Evidence over claims | Yes | PASS | PR cita o diff do `LICENSE.txt` contra o upstream, os testes e `instruction_budget.py --check` |
| V. Provider pattern | No | N/A | nenhum provider |
| VI. Privacy by design | No | N/A | sem dados de usuário |
| VII. Attribution | Yes | PASS | este trabalho é a correção do Art. VII: licença Apache-2.0 junto da skill, crédito a `anthropics/skills` e nota de modificação no `CREDITS.md` |
| Preset-specific articles | No | N/A | texto e instalador |

## Architecture decisions

- **Decisão:** copiar o `LICENSE.txt` verbatim do upstream (sem reformatar). **Rationale:** a Apache-2.0 exige entregar o texto da licença e o critério da spec é identidade com o upstream. **Trade-off:** arquivo de ~11 KB por skill atribuída; só esta skill por ora.
- **Decisão:** estender `_collect_skill_references` para incluir `skills/<skill>/LICENSE.txt` como entrada `<skill>/LICENSE.txt`, com a mesma regra de fronteira (não segue symlink para fora de `skills/`) e a precedência existente framework/preset. **Rationale:** é o menor ponto de extensão; as demais skills não têm o arquivo e não mudam. **Trade-off:** o nome da função fala em "references"; a docstring é ajustada, sem renomear.
- **Decisão:** o campo `license` fica como texto livre, por exemplo `Apache-2.0 — adapted and modified from anthropics/skills (frontend-design); complete terms in LICENSE.txt`. **Rationale:** o §4(b) pede o aviso de modificação no próprio arquivo modificado; o esquema aceita string; não muda `name` nem `description`, então o orçamento de listagem não se move. **Trade-off:** nenhum.
- **Decisão:** sem `NOTICE`; o `CREDITS.md` repete a nota. **Rationale:** o upstream não traz `NOTICE`; o aviso exigido já está no campo `license`. **Trade-off:** nenhum.
- **Decisão:** enxugar cortando redundância das seções herdadas e dos exemplos, mantendo as asserções da 0034 intactas. **Rationale:** critério da spec; os testes de frase-chave são a guarda. **Trade-off:** menos exemplos de código.

## Project structure changes

```text
presets/django-drf-react/skills/frontend-design/LICENSE.txt   (new: Apache-2.0 verbatim)
presets/django-drf-react/skills/frontend-design/SKILL.md      (modified: campo license; corpo enxugado)
src/aiadev/install_engine.py                                  (modified: coletor inclui LICENSE.txt da skill)
CREDITS.md                                                    (modified: entrada anthropics/skills)
CHANGELOG.md                                                  (modified: [Unreleased])
tests/test_install_engine.py                                  (modified: coletor com LICENSE.txt)
tests/test_frontend_design_attribution.py                     (new; embute a constante sha256 do upstream, sem rede)
tests/test_frontend_design_quality.py                         (modified: teto do corpo 1.300)
```

## Phase breakdown

### Phase 1 — Instalador e licença

- Testes que falham: o coletor devolve `<skill>/LICENSE.txt` quando existe, ignora quando não existe e respeita a fronteira; a instalação do preset django-drf-react entrega `LICENSE.txt` ao lado do `SKILL.md` em cada plataforma que copia skills.
- Implementar o mínimo no coletor; adicionar o `LICENSE.txt` verbatim e conferir identidade com o upstream.

### Phase 2 — Crédito e enxugamento

- Testes que falham: `license` no frontmatter cita Apache-2.0 e `anthropics/skills` sem "Strivex"; `name` e `description` inalterados; `CREDITS.md` tem a entrada com adaptação, licença e nota de modificação; nenhum arquivo fora do histórico cita "Strivex" como origem; corpo ≤ 1.300 tokens com a suíte da 0034 verde.
- Corrigir o frontmatter, escrever a entrada, enxugar o corpo, atualizar o teto no teste da 0034 e o `CHANGELOG.md`.

## Risks and mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| O mapeamento de plataformas assume que todo arquivo de skill é `.md` | Low | Low | revisão confirmou que `_resolve_artifact_target` e os cinco handlers tratam qualquer `<skill>/<rel>`; teste de instalação por plataforma como guarda |
| Enxugamento enfraquece uma regra | Low | Med | asserções da 0034 intactas e revisão de branch |
| Texto do upstream mudou desde 2025-12 | Low | Low | comparar com a versão atual do upstream e registrar a data conferida |

## Complexity tracking

Nenhuma linha `FAIL`; vazio justificado.

## Hand-off to `tasks`

Next skill: `tasks`. Constitution Check completo, estrutura conferida contra o instalador e os testes existentes.
