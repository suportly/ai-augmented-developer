# Roadmap: AI-Augmented Developer

**Language:** pt-BR <!-- fonte: convenção das specs recentes, specs/0023-product-context/spec.md:9; nome do produto: README.md:1 -->

---

<!-- Fontes dos campos: as linhas de campo ficam sem citação porque a gramática
     (specs/0023-product-context/spec.md:106) exige um valor por linha; a
     fonte de cada entrada está na última frase do seu parágrafo. -->

<!-- section: Entries -->
## Entries

### R001 — Contexto de produto: skill `product` e templates de mission, tech-stack e roadmap

- **Status:** done
- **Spec:** 0023-product-context
- **Depends on:**

Dar ao pipeline um artefato durável que diga por que o produto existe, para quem, com qual stack e em que ordem as features vêm, para que as specs conversem entre si. Fontes: título e porquê em specs/0023-product-context/spec.md:1,16; status `done`: mesclada na `main` pela PR #56 (commit `8571f69`, 2026-10-13), com as 15 tasks concluídas (specs/0023-product-context/tasks.md).

### R002 — Skill `replan`: fechar o ciclo entre entrega e roadmap

- **Status:** planned
- **Spec:** 0024-replan
- **Depends on:** R001

Trazer de volta ao roadmap o que foi entregue e o que mudou de escopo em cada feature, em vez de o tech lead reconstruir isso à mão. Fontes: specs/0024-replan/spec.md:1,16 (spec em Draft, :7); dependência bloqueante da 0023 em :132.

### R003 — Critérios de validação na spec e aceite humano antes do merge

- **Status:** planned
- **Spec:** 0025-validation-criteria-human-acceptance
- **Depends on:**

Criar um momento em que uma pessoa confere a feature contra critérios escritos antes do código, porque hoje todas as aprovações que liberam o merge são de agentes. Fontes: specs/0025-validation-criteria-human-acceptance/spec.md:1,16 (Draft, :7); sem dependência bloqueante em :136.

### R004 — Skill `changelog`: entrada do `[Unreleased]` a partir da spec e dos commits

- **Status:** planned
- **Spec:** 0026-changelog-skill
- **Depends on:**

Gerar a entrada de changelog de cada feature a partir do porquê da spec e do quê dos commits, em vez de escrevê-la à mão e perder stories ou o Spec ID. Fontes: specs/0026-changelog-skill/spec.md:1,16 (Draft, :7); só specs relacionadas, sem bloqueio, em :131.

### R005 — Bootstrap brownfield: contexto de produto e specs retroativas

- **Status:** planned
- **Spec:** 0027-brownfield-bootstrap
- **Depends on:** R001

Dar a projetos legados um ponto de partida inferido do código (módulos, testes, TODOs), para que o pipeline não comece com roadmap vazio e sem specs das features existentes. Fontes: specs/0027-brownfield-bootstrap/spec.md:1,16 (Draft, :7); dependência bloqueante da 0023 em :123.

### R006 — Modo roadmap no `implement`: várias features em sequência, com métricas de qualidade de spec

- **Status:** planned
- **Spec:** 0028-implement-roadmap-mode
- **Depends on:** R001, R002, R003

Deixar o agente avançar pelas features prontas do roadmap sem vigiar cada uma e mostrar, no fim, quais specs precisam melhorar. Fontes: specs/0028-implement-roadmap-mode/spec.md:1,16 (Draft, :7); dependências de 0023, 0024 e 0025 em :27 e :125.

### R007 — Contexto limpo entre etapas: hand-offs só por artefatos em disco

- **Status:** planned
- **Spec:** 0029-artifact-only-handoffs
- **Depends on:**

Fazer `specify`, `plan` e `tasks` passarem o trabalho só pelos arquivos, para que nada decidido na conversa fique fora dos artefatos revisados. Fontes: specs/0029-artifact-only-handoffs/spec.md:1,16 (Draft, :7); a 0023 aparece só como relacionada em :118.
