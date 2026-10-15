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

### R008 — Pipeline enxuto: menos turnos, menos texto e medição correta de custo

- **Status:** done
- **Spec:** 0030-lean-pipeline
- **Depends on:**

Reduzir o custo por feature (turnos da thread principal e dispatches de revisão pesam mais que o texto das skills) sem remover nenhum gate, e corrigir a medição que hoje soma usage por evento e ignora subagentes, para que todo ganho seja provado por custo por feature e nunca por "tokens salvos". Inclui os gates mecânicos novos (cobertura cenário→task e bloqueio por checklist no preflight de implement), a triagem em specify e clarify, o conteúdo de stack movido para os presets, a remoção, pelo sync, de arquivos que o framework deixou de distribuir e a remoção do terse-mode, das skills help e using-ai-augmented-developer e do review-context.md. Fontes: src/aiadev/token_metrics.py:153-159 (usage somado por evento, sem dedupe por message.id); skills/implement/SKILL.md:74,233 (seções condicionais e gate de re-dispatch repetido); skills/requesting-code-review/SKILL.md:29-31 (review-context.md); comparação com github/spec-kit@6c62e10. Status `done`: mesclada na `main` pela PR #58 (commit `2ee682f`), release 0.25.0 (`c7bfa65`).

### R009 — Faixa rápida: spec compacto e lane de bug para mudanças pequenas

- **Status:** planned
- **Spec:**
- **Depends on:** R008

Dar às mudanças pequenas e a correções de bug um caminho com um único spec.md, TDD mantido e um revisor, em vez do pipeline completo — o que exige emenda do Art. I, que hoje só dispensa typo, revert e `hotfix:`. Fontes: constitution.md:25-27; presets/lean e extensions/bug de github/spec-kit@6c62e10 como referência.

### R010 — Modo `converge` no `analyze`: gaps viram tasks anexadas

- **Status:** planned
- **Spec:**
- **Depends on:** R008

Transformar gaps entre código e spec/plan/tasks em tasks rastreáveis anexadas ao tasks.md, em vez de só reportá-los; a checagem mecânica cenário→task nasce em R008 e aqui alimenta o modo converge. Fontes: skills/analyze/SKILL.md (hoje só reporta); github/spec-kit@6c62e10 templates/commands/converge.md.

### R011 — Feature ativa independente do nome da branch

- **Status:** planned
- **Spec:**
- **Depends on:**

Permitir worktrees e branches criadas por agentes sem renomear para `feature/<slug>`, hoje exigido pelo preflight. Fontes: src/aiadev/preflight.py:188 (_git_current_branch); github/spec-kit@6c62e10 scripts/bash/common.sh (.specify/feature.json).

### R012 — Waves paralelas de tasks independentes

- **Status:** planned
- **Spec:**
- **Depends on:** R008

Reduzir tempo de relógio executando juntas as tasks sem dependência e com arquivos disjuntos — só se a medição de R008 mostrar que o custo por tarefa não sobe. Fontes: templates/tasks-template.md:24-25 (Depends on e Files por task); implement hoje é serial (skills/implement/SKILL.md:44).

### R013 — Catálogo remoto com camada de confiança

- **Status:** planned
- **Spec:**
- **Depends on:**

Antes de aceitar presets e extensões de um catálogo remoto, exigir HTTPS, pin de sha256 e limites de download, porque eles carregam prompts executáveis. Fontes: src/aiadev/extensions.py:170-172 (`git clone --depth 1` de URL sem pin); github/spec-kit@6c62e10 docs/reference/extensions.md.

### R014 — Higiene de contexto: ver onde o contexto se acumula e avisar a hora de cortar a sessão

- **Status:** done
- **Spec:** 0031-context-hygiene
- **Depends on:** R008

Mostrar, com os transcripts locais, quanto do custo vem de sessões de contexto longo e dar ao agente um aviso determinístico de que é hora de cortar a sessão, porque o custo medido nos transcripts deste repositório está na thread principal (contexto médio de 250k a 400k por request, máximo 741k; requests acima de 200k são 25,6% das requests e 62,2% dos tokens), não no número de subagentes. Fontes: artigo https://dev.to/alairjt/i-burned-95-of-my-ai-coding-quota-in-2-days-heres-what-the-logs-revealed-2omf; medição sobre os 3 transcripts de ~/.claude/projects/ deste repositório em 2026-10-15; src/aiadev/token_metrics.py:424-484 (só agrega, não guarda o contexto por request); src/aiadev/commands/next.py (sem informação de sessão); skills/implement/SKILL.md (nenhuma instrução de compactar ou cortar sessão). Status `done`: mesclada na `main` pela PR #59 (commit `9ffe2e3`).
