# Feature specification: skill `changelog` — entrada do `[Unreleased]` a partir da spec e dos commits

> This file is produced by the `specify` skill (or by `aiadev init --feature <name>` as a stub). Keep it focused on **what** and **why** — planning and code belong in `plan.md` and `tasks.md`.

**Branch:** `feature/0026-changelog-skill`
**Created:** 2026-09-24
**Status:** Draft <!-- Draft | In review | Approved | Implemented -->
**Spec ID:** 0026 <!-- auto-incrementing integer -->
**Language:** pt-BR <!-- BCP-47 tag; every downstream artifact in this feature is written in this language. -->

---

<!-- section: Problem -->
## Problem

A entrada de `CHANGELOG.md` de cada feature é escrita à mão, fora do pipeline. As informações de que ela precisa já estão em disco — o *porquê* na spec (Problem, user stories), o *o quê* nos commits da branch (conventional commits, `!` para breaking) — mas nenhuma skill junta as duas. O resultado são entradas que esquecem stories, omitem o Spec ID (que os testes de rastreabilidade exigem) ou chegam só no commit de release. O `constitution` já escreve no `CHANGELOG.md` para emendas; features não têm equivalente. Quem sente: quem prepara a release e reconstrói o changelog a partir do `git log`, e o leitor do changelog, que perde o *porquê*.

<!-- section: Reconnaissance -->
## Reconnaissance

- **formato do changelog** — entry: `CHANGELOG.md` · auth: none · integration: Keep a Changelog 1.1.0 + SemVer; `## [Unreleased]` no topo; blocos por versão com `### Added/Changed/Fixed/Removed`; entradas em prosa por feature, com parágrafo "**Why:**" e o Spec ID citado. Escrito em inglês, enquanto as specs recentes são pt-BR; a entrada segue o idioma do arquivo (cl-2).
- **testes que o formato precisa respeitar** — entry: `tests/test_attribution_and_changelog.py` · auth: none · integration: exige `## [Unreleased]`; `_blocks_mentioning` ancora no **Spec ID** e aceita a entrada sob `[Unreleased]` ou sob o bloco de versão da release; exige que o bloco que cita `0014` mencione cada uma das 4 stories.
- **segundo teste de changelog** — entry: `tests/test_changelog_entry.py` · auth: none · integration: fatia o bloco `## [0.15.0]` e exige Spec ID `0009`, menção à feature e marcação de breaking (`breaking` ou `!`). Blocos de versões já lançadas nunca podem ser alterados.
- **promoção na release** — entry: `docs/RELEASING.md` · auth: none · integration: a release move `[Unreleased]` para `[X.Y.Z]`; a skill só escreve em `[Unreleased]`.
- **ponto de integração** — entry: `skills/finishing-a-branch/SKILL.md` · auth: none · integration: "Pre-Flight Checklist" e "Commit Cleanup" antecedem o push; a entrada precisa estar commitada antes da PR.
- **precedente de escrita no changelog** — entry: `skills/constitution/SKILL.md` · auth: none · integration: bootstrap grava `Added` e emendas gravam `Changed` em `CHANGELOG.md [Unreleased]`.
- **convenção de commits** — entry: `rules/git-workflow.md` · auth: none · integration: conventional commits `<type>(<scope>): …`; é a gramática de onde sai a categoria da entrada.
- **changelogs múltiplos** — entry: `vscode-extension/CHANGELOG.md` · auth: none · integration: o próprio repositório já tem dois changelogs; o alvo é o changelog mais próximo de cada arquivo alterado (cl-4).

<!-- section: Users and stakeholders -->
## Users and stakeholders

- **Quem prepara a release** — recebe `[Unreleased]` já preenchido e rastreável por Spec ID.
- **Leitores do changelog** (usuários e mantenedores de projetos consumidores) — querem o *porquê*, não a lista de commits.
- **Revisor da PR** — vê a entrada de changelog junto com o código.

<!-- section: Success criteria -->
## Success criteria

- A skill gera, a partir de `spec.md` + commits da branch (`main...HEAD`), uma entrada sob `## [Unreleased]` que: cita o Spec ID; menciona cada user story da spec; classifica em `Added`/`Changed`/`Fixed`/`Removed` segundo o tipo dos commits; marca breaking quando algum commit tem `!` ou `BREAKING CHANGE`.
- Rodar a skill no próprio repositório mantém `tests/test_changelog_entry.py` e `tests/test_attribution_and_changelog.py` verdes, sem editar esses testes.
- Nenhum byte fora de `[Unreleased]` muda (verificável por diff dos blocos de versão antes/depois).
- Rodar duas vezes na mesma branch não duplica a entrada.
- O `finishing-a-branch` mostra a entrada para aprovação e a inclui num commit antes do push.

<!-- section: Non-goals -->
## Non-goals

- Cortar a release (mover `[Unreleased]` para `[X.Y.Z]`, bump de `VERSION`, tag) — continua no processo de `docs/RELEASING.md`.
- Release notes de GitHub/marketplace ou changelogs de pacotes que não sejam o alvo escolhido.
- Reescrever entradas antigas ou impor conventional commits via hook.

<!-- section: User stories -->
## User stories

### Story 1 — Gerar a entrada a partir da spec e dos commits (P1)

Como quem prepara a release, quero que a skill `changelog` redija a entrada do `[Unreleased]` a partir da spec e dos commits da branch para que ela cite o porquê, cubra todas as stories e seja rastreável.

**Acceptance scenarios** (Given / When / Then, ≥ 3 per story):

1. Given uma branch com commits `feat(...)` e `fix(...)` e uma spec com 3 stories, When invoco `changelog`, Then a entrada tem as seções `Added` e `Fixed`, cita o Spec ID e menciona as 3 stories.
2. Given um commit `refactor(x)!: …`, When a entrada é gerada, Then ela marca a mudança como breaking.
3. Given commits fora do padrão conventional commits, When a entrada é gerada, Then a skill lista esses commits e pergunta a categoria em vez de adivinhar.
4. Given a mensagem de um commit contém linhas `Co-Authored-By:` ou e-mails, When a entrada é gerada, Then esses dados não são copiados.

### Story 2 — Integração com `finishing-a-branch` (P1)

Como usuário do pipeline, quero que o `finishing-a-branch` chame o `changelog` antes do push para que nenhuma PR saia sem a entrada.

**Acceptance scenarios:**

1. Given o preflight do `finishing-a-branch` passou, When chego ao passo de push, Then a skill invoca `changelog`, mostra a entrada e só commita após aprovação.
2. Given a entrada já existe em `[Unreleased]` citando o Spec ID, When invoco de novo, Then a skill propõe atualizá-la em vez de criar outra.
3. Given recuso a entrada, When o `finishing-a-branch` continua, Then o push é bloqueado até haver entrada aprovada ou dispensa registrada (header `**Changelog:** none — <motivo>` na spec ou `changelog = "off"` em `_aiadev/team.toml`).
4. Given a branch não tem spec (typo, docs, revert), When o `finishing-a-branch` roda, Then não exige entrada de changelog.

### Story 3 — Respeitar o formato e os testes existentes (P1)

Como mantenedor do aiadev, quero que a entrada gerada respeite o formato que os testes de rastreabilidade já exigem para que a skill não quebre o CI do próprio repositório.

**Acceptance scenarios:**

1. Given o `CHANGELOG.md` do repositório, When a skill grava uma entrada, Then `pytest tests/test_changelog_entry.py tests/test_attribution_and_changelog.py` passa.
2. Given blocos de versões já lançadas, When a skill grava, Then nenhum deles muda.
3. Given `[Unreleased]` já tem entradas de outras features, When a skill grava, Then as entradas existentes ficam intactas e a nova entra na seção de categoria correta.
4. Given o changelog está em inglês e a spec em pt-BR, When a skill grava, Then a entrada sai em inglês.

### Story 4 — Projetos consumidores sem changelog ou com vários (P2)

Como usuário de um projeto consumidor, quero comportamento definido quando não há `CHANGELOG.md` ou há mais de um para que a skill funcione fora do repositório do aiadev.

**Acceptance scenarios:**

1. Given o projeto não tem `CHANGELOG.md`, When invoco `changelog`, Then a skill pergunta se deve criar o arquivo; se eu aceito, cria com o cabeçalho Keep a Changelog e grava a entrada; se recuso, grava `changelog = "off"` em `_aiadev/team.toml` e não cria nada.
2. Given o projeto tem `CHANGELOG.md` na raiz e em `pkg/`, e a branch altera arquivos nos dois lugares, When invoco `changelog`, Then a skill propõe uma entrada em cada changelog, cada uma cobrindo só os arquivos do seu escopo, e mostra as duas para aprovação.
3. Given a skill instalada nas 5 plataformas, When `aiadev validate` roda, Then o `SKILL.md` de `changelog` passa nos dois schemas.

<!-- section: Clarifications -->
## Clarifications

- **cl-1 (projeto sem `CHANGELOG.md`):** a skill pergunta na primeira vez se deve criar o arquivo com o cabeçalho Keep a Changelog e `## [Unreleased]`. Se a pessoa aceitar, cria e grava a entrada. Se recusar, a recusa fica registrada como `changelog = "off"` em `_aiadev/team.toml` (cl-3) e o `finishing-a-branch` não volta a bloquear. Nada é criado sem a pessoa pedir.
- **cl-2 (idioma da entrada):** o idioma das entradas que já estão no changelog alvo (neste repositório, inglês). O changelog tem outro leitor que a spec e não mistura idiomas. Só quando o arquivo é criado do zero (cl-1) vale o `Language:` da spec.
- **cl-3 (dispensa):** três casos, todos em arquivos que passam por revisão. (a) Branch sem spec (isenções do Artigo I): a entrada não é exigida, como o aceite da spec 0025. (b) Branch com spec e sem mudança visível: header `**Changelog:** none — <motivo>` na spec. (c) Projeto que recusou changelog (cl-1): `changelog = "off"` em `_aiadev/team.toml`, a camada versionada da customização da spec 0014.
- **cl-4 (monorepos):** cada arquivo alterado na branch pertence ao `CHANGELOG.md` mais próximo acima dele no caminho; o da raiz é o padrão. A skill escreve uma entrada em cada changelog atingido e mostra todas para aprovação. Neste repositório: mudanças em `vscode-extension/` vão para `vscode-extension/CHANGELOG.md`, o resto para a raiz, como `docs/RELEASING.md` já faz à mão.

<!-- section: Data touched -->
## Data touched

- **Leitura:** `spec.md` (Problem, user stories, Spec ID), `git log main...HEAD` (assunto e corpo de commits), `CHANGELOG.md` existente.
- **Escrita (após aprovação):** somente a seção `## [Unreleased]` de cada changelog alvo (cl-4).
- **Dispensas:** header `**Changelog:**` na spec; chave `changelog` em `_aiadev/team.toml`.
- **Pacote:** `skills/changelog/SKILL.md`, `commands/changelog.md`, passo novo em `skills/finishing-a-branch/SKILL.md`, registros de skill (tabela do `CLAUDE.md`, `using-ai-augmented-developer`, `docs/pipeline-reference.md`, `README.md`). Skill genérica: não entra em `presets/catalog.json`.

<!-- section: Out-of-band effects -->
## Out-of-band effects

- Nenhum. Leitura de git local e escrita num arquivo do repositório; nada é publicado.

<!-- section: Open risks -->
## Open risks

- Commits mal classificados geram categoria errada; o revisor humano é a última barreira.
- Merge de branches paralelas com entradas em `[Unreleased]` gera conflito de texto no changelog.
- O `finishing-a-branch` atual tem comandos de stack específica (pytest/jest/Django) no texto; integrar a skill não deve aumentar esse acoplamento.

<!-- section: Traceability -->
## Traceability

- Originating issue: comparação do aiadev com o curso "Spec-Driven Development with Coding Agents" (DeepLearning.AI × JetBrains, Paul Everitt) — conversa de 2026-09-24, melhoria 4 de 7.
- Related specs: `0024-replan` (roda depois, pode ler a entrada gerada), `0025-validation-criteria-human-acceptance` (mesmo ponto de integração no `finishing-a-branch`).
- Constitution articles invoked: I, II, III, IV, VI

### Constitution Check (preliminar)

> Avaliação no nível da spec. O `plan` refaz a checagem com evidência concreta.

| Artigo | Aplica? | Avaliação preliminar |
|---|---|---|
| I. Spec-first | Sim | Esta spec; cl-1…cl-4 resolvidas em 2026-09-24. |
| II. Test-first | Sim | Fixtures de changelog + git log; testes de idempotência, blocos lançados intocados e os dois testes existentes como regressão. |
| III. Simplicity | Sim | Uma skill; alvos derivados do caminho dos arquivos, sem configuração; categorias derivadas dos tipos de commit, sem taxonomia nova. |
| IV. Evidence over claims | Sim | A entrada cita o Spec ID; o PR mostra a saída dos testes de changelog. |
| V. Provider pattern | Não | Sem fronteira de rede. |
| VI. Privacy by design | Sim | Linhas `Co-Authored-By:` e e-mails de commits não entram na entrada. |
| VII. Attribution | Não | Keep a Changelog já é o formato adotado; sem material adaptado novo previsto. |
