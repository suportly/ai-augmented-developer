# Feature specification: Atribuição correta da frontend-design e folga no corpo da skill

> Produced by `specify`. **What** and **why** only; planning and code belong in `plan.md` and `tasks.md`.

**Branch:** `feature/0035-frontend-design-attribution`
**Created:** 2026-11-06
**Status:** Approved <!-- Draft | In review | Approved | Implemented -->
**Spec ID:** 0035 <!-- auto-incrementing integer -->
**Language:** pt-BR <!-- BCP-47 tag; downstream artifacts use it. -->
**UI:** no <!-- yes if the feature adds or changes screens -->
<!-- UI: no — só Markdown, um arquivo de licença e testes. -->

---

<!-- section: Problem -->
## Problem

O frontmatter da skill `frontend-design` do preset `django-drf-react` diz `Adapted from Strivex — Complete terms in LICENSE.txt`, mas a pasta da skill não tem `LICENSE.txt` e o `CREDITS.md` não tem entrada para essa origem. Conferindo o repositório público `anthropics/skills` (licença Apache-2.0, com `LICENSE.txt`), o `description` (mesma frase inicial e mesma frase final, com o meio encurtado) e a seção "Design Thinking" (Purpose, Tone, Constraints, Differentiation, a linha CRITICAL) da versão de 2025-12-04 daquele repositório coincidem com os desta skill; "Strivex" não aparece em nenhuma fonte consultada. A atribuição declarada está, portanto, errada e incompleta, e o Art. VII (não renunciável) exige crédito citável e licença junto do material derivado; a Apache-2.0 (seção 4) também exige entregar o texto da licença e indicar que o arquivo foi modificado. Além disso, o corpo da skill ficou a cerca de 4 tokens do teto de 1.400 fixado pela spec 0034, de modo que qualquer ajuste futuro quebra um teste.

<!-- section: Reconnaissance -->
## Reconnaissance

- **skill frontend-design** — entry: `presets/django-drf-react/skills/frontend-design/SKILL.md` · auth: none · integration: `Adapted from Strivex`
- **créditos do projeto** — entry: `CREDITS.md` · auth: none · integration: `Direct inspirations`
- **testes da skill** — entry: `tests/test_frontend_design_quality.py` · auth: none · integration: `test_body_within_1400_tokens`
- **instalador** — entry: `src/aiadev/install_engine.py` · auth: none · integration: `_collect_skill_references` (hoje copia só `SKILL.md` e `references/**/*.md`; um `LICENSE.txt` na pasta da skill não seria instalado)

<!-- section: Users and stakeholders -->
## Users and stakeholders

- Mantenedor do framework, responsável pelo Art. VII e pela conformidade de licença.
- Projetos consumidores do preset, que recebem a skill e a licença dela.
- Autores do material original, que precisam ser creditados.

<!-- section: Success criteria -->
## Success criteria

- A pasta `presets/django-drf-react/skills/frontend-design/` contém `LICENSE.txt` com o texto da Apache-2.0 idêntico ao de `anthropics/skills`.
- O frontmatter da skill deixa de citar "Strivex" e cita `anthropics/skills`, a Apache-2.0 e que o arquivo foi modificado (Apache-2.0 §4(b): o próprio arquivo modificado carrega o aviso); `name` e `description` ficam idênticos (nenhum teto de orçamento muda).
- `CREDITS.md` tem uma entrada para `anthropics/skills` que diz o que foi adaptado (a skill `frontend-design`), a licença (Apache-2.0) e que o arquivo foi modificado por este projeto (Apache-2.0 seção 4).
- Nenhum arquivo versionado cita "Strivex" como origem, exceto o histórico (`CHANGELOG.md`, `vscode-extension/CHANGELOG.md`, `specs/**`), a nota de correção do `CREDITS.md` e o teste que fixa a ausência.
- O corpo da skill mede no máximo 1.300 tokens (chars / 4), e todos os testes de frase-chave da 0034 continuam passando sem alteração de asserção.
- O `LICENSE.txt` chega ao projeto consumidor junto da skill instalada (teste de instalação).
- `python3 scripts/instruction_budget.py --check` sai 0 sem alterar `docs/instruction-budget.json`.

<!-- section: Non-goals -->
## Non-goals

- Reescrever a skill para remover o material derivado.
- Auditar a atribuição das outras skills do repositório (o achado vale só para esta; as demais ficam como follow-up se o mantenedor quiser).
- Mudar o comportamento da skill ou os tetos de orçamento.
- Publicar uma versão sem autorização do mantenedor.

<!-- section: User stories -->
## User stories

### Story 1 — Licença e crédito corretos (P1)

As a mantenedor, I want que a skill derivada carregue a licença e o crédito certos so that o framework cumpra o Art. VII e a Apache-2.0.

**Acceptance scenarios** (≥ 3 per story):

1. Given o repositório após a mudança, When se lê a pasta da skill, Then existe `LICENSE.txt` com o texto da Apache-2.0 idêntico ao do upstream.
2. Given o frontmatter da skill, When se lê o campo `license`, Then ele cita a Apache-2.0, `anthropics/skills` e que o arquivo foi modificado, não cita "Strivex", e `name` e `description` não mudaram.
3. Given `CREDITS.md`, When se procura `anthropics/skills`, Then há uma entrada com o que foi adaptado, a licença Apache-2.0 e a nota de que o arquivo foi modificado.
4. Given o preset instalado num projeto novo, When se lista a pasta da skill instalada, Then `LICENSE.txt` está presente ao lado do `SKILL.md`.

### Story 2 — Folga no corpo da skill (P2)

As a mantenedor, I want folga sob o teto de tokens so that ajustes futuros não quebrem o teste.

**Acceptance scenarios** (≥ 3 per story):

1. Given o corpo atual (1.396 tokens), When o texto é enxugado, Then ele mede no máximo 1.300 tokens.
2. Given os testes de frase-chave da 0034, When a suíte roda, Then todos passam sem mudar nenhuma asserção.
3. Given o enxugamento, When se compara com a versão anterior, Then nenhuma regra fixada pela 0034 (direção de arte, verificação no navegador, 8 sinais, checklist com captura) foi removida ou enfraquecida.

<!-- section: Clarifications -->
## Clarifications

Nenhum marcador: a origem foi conferida em fonte pública e o pedido do mantenedor ("ajuste as pendências") cobre as duas pendências.

<!-- section: Data touched -->
## Data touched

- `presets/django-drf-react/skills/frontend-design/` (SKILL.md, novo LICENSE.txt), `CREDITS.md`, testes e `CHANGELOG.md`.

<!-- section: Out-of-band effects -->
## Out-of-band effects

- Consumidores do preset passam a receber `LICENSE.txt` com a skill.

<!-- section: Open risks -->
## Open risks

- A coincidência foi conferida por texto contra o upstream; o histórico do repositório ("Strivex") não permite saber como o rótulo errado entrou. A correção segue a evidência textual e a licença do upstream.
- Outras skills do repositório podem ter o mesmo problema; não foram auditadas.
- O instalador não copia `LICENSE.txt`; o critério de instalação exige uma mudança pequena e testada nele (decidida no plano), sem alterar o que já é instalado para as demais skills.
- A evidência da origem (comandos e URLs usados na conferência contra o upstream) vai citada no corpo do PR, para ser auditável (Art. IV).
- O enxugamento pode afrouxar uma regra por acidente; o teste de frases-chave da 0034 e a revisão de branch são a guarda.

## Assumptions

- O texto da Apache-2.0 do upstream hoje é o mesmo da versão de 2025-12 (a licença não mudou entre versões). [impact: low]
- A Apache-2.0 não exige `NOTICE` aqui porque o upstream não traz um; o aviso de modificação vai no campo `license` do `SKILL.md` (§4(b)) e é repetido no `CREDITS.md`. [impact: low]

<!-- section: Traceability -->
## Traceability

- Originating issue: pendências da spec 0034, pedido do mantenedor em 2026-11-06
- Related specs: 0034-frontend-design-quality
- Constitution articles invoked: I, II, III, IV, VII
