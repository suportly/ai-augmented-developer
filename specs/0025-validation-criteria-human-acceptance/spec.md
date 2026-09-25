# Feature specification: critérios de validação na spec e aceite humano antes do merge

> This file is produced by the `specify` skill (or by `aiadev init --feature <name>` as a stub). Keep it focused on **what** and **why** — planning and code belong in `plan.md` and `tasks.md`.

**Branch:** `feature/0025-validation-criteria-human-acceptance`
**Created:** 2026-09-24
**Status:** Draft <!-- Draft | In review | Approved | Implemented -->
**Spec ID:** 0025 <!-- auto-incrementing integer -->
**Language:** pt-BR <!-- BCP-47 tag; every downstream artifact in this feature is written in this language. -->

---

<!-- section: Problem -->
## Problem

Hoje todas as aprovações que liberam o merge são de agentes: o spec reviewer e o code quality reviewer por task (`implement`), o `code-reviewer` da branch (`requesting-code-review`), que grava `.aiadev/review.yaml` com `status: approved`, e o preflight do `finishing-a-branch` confia nesse arquivo. Não existe um momento em que uma pessoa confere, contra critérios escritos antes do código, se a feature faz o que devia. A spec tem *Success criteria* (resultados mensuráveis) e cenários Given/When/Then (cobertos por testes automatizados), mas nada que diga "o que um humano verifica para aceitar". O curso SDD separa a validação humana da revisão automática e fecha cada feature com ela. Quem sente: o tech lead que descobre em produção um comportamento que passou em todos os testes e revisões.

<!-- section: Reconnaissance -->
## Reconnaissance

- **template da spec** — entry: `templates/spec-template.md` · auth: none · integration: seções ancoradas por `<!-- section: … -->`; *Success criteria* já existe e precisa ser distinguida da seção nova.
- **anchors fixados em código** — entry: `src/aiadev/preflight.py` · auth: none · integration: `SPEC_ANCHORS` lista as seções obrigatórias e o `preflight plan` aborta se faltar alguma; `tests/test_preflight_requirements_coverage.py::test_every_anchor_exists_in_its_template` faz round-trip com o template. Uma seção obrigatória nova quebra o preflight de toda spec antiga sem regra de corte (cl-3).
- **segunda lista de seções** — entry: `src/aiadev/_tooling/payload.py` · auth: none · integration: `_SPEC_REQUIRED_SECTIONS` é usado por `aiadev.tools` e pelo servidor MCP; precisa ficar coerente com `SPEC_ANCHORS`.
- **fim do `implement`** — entry: `skills/implement/SKILL.md` · auth: none · integration: "After the last task: dispatch a final full-branch review; hand off to `finishing-a-branch`". A geração da checklist entra aqui.
- **gate de merge atual** — entry: `skills/requesting-code-review/SKILL.md` · auth: none · integration: seção "Recording the review verdict" grava `.aiadev/review.yaml` (`status`, `timestamp`, `reason`); `src/aiadev/preflight.py::_review_is_approved` só lê `status`. Nenhum campo distingue aprovação humana de aprovação de agente.
- **fechamento da branch** — entry: `skills/finishing-a-branch/SKILL.md` · auth: none · integration: "Pre-Flight Checklist" e "Merge Decision"; é onde o aceite humano passa a ser exigido.
- **próximo passo** — entry: `src/aiadev/pipeline_state.py` · auth: none · integration: hoje recomenda `finishing-a-branch` assim que o último review é `APPROVED`; precisa considerar o aceite humano pendente.

<!-- section: Users and stakeholders -->
## Users and stakeholders

- **Tech lead / dono do produto** — quem assina o aceite; quer um roteiro curto e objetivo do que verificar.
- **Reviewers automáticos** — continuam existindo e rodando; o aceite humano é um gate adicional, não um substituto.
- **Agente** — deixa de poder declarar a feature pronta sozinho.
- **Projetos consumidores com specs antigas** — não podem ter o pipeline quebrado pela seção nova.

<!-- section: Success criteria -->
## Success criteria

- O template da spec ganha a seção "Critérios de validação" com anchor próprio e orientação que a diferencia de *Success criteria* e dos cenários de aceitação; `specify` passa a preenchê-la.
- Ao fim do `implement`, existe em `specs/<branch>/` um artefato de checklist com **um item por critério de validação**, na mesma ordem, cada item com espaço para resultado e observação.
- `aiadev preflight finishing-a-branch` aborta enquanto a checklist tiver item sem resultado, item reprovado ou faltar o registro de aceite humano — mesmo que `.aiadev/review.yaml` diga `approved`.
- Nenhuma revisão automática existente é removida ou enfraquecida: os testes atuais de re-dispatch e zero-findings-halt (`tests/test_review_redispatch_skills.py`, `tests/test_zero_findings_halt_agents.py`) continuam verdes sem alteração.
- Specs sem o header `**Template:** 2` continuam passando no `preflight` sem a seção nova, em qualquer numeração de projeto.

<!-- section: Non-goals -->
## Non-goals

- Substituir ou relaxar os reviewers automáticos por task e por branch.
- Integrar com aprovação de PR do GitHub/GitLab ou qualquer serviço remoto (cl-1 escolheu registro local).
- Automatizar a execução dos critérios de validação; eles existem justamente para verificação humana.
- Reescrever specs antigas para incluir a seção.
- Exigir aceite de branches sem spec (isenções do Artigo I); o gate segue a spec (cl-4).

<!-- section: User stories -->
## User stories

### Story 1 — Seção "Critérios de validação" na spec (P1)

Como tech lead, quero que toda spec nova traga critérios de validação escritos antes do código para que o aceite compare a entrega com algo combinado de antemão.

**Acceptance scenarios** (Given / When / Then, ≥ 3 per story):

1. Given o template atualizado, When `specify` cria uma spec, Then a spec tem a seção "Critérios de validação" com pelo menos um critério, cada um descrevendo uma verificação que uma pessoa executa e um resultado observável.
2. Given um critério que não pode ser verificado por uma pessoa sem ler o código (ex.: "a função X é chamada"), When o `spec-document-reviewer` revisa, Then aponta o critério como inválido.
3. Given um critério de validação que repete um item de *Success criteria* sem descrever o passo que a pessoa executa, When o `spec-document-reviewer` revisa, Then aponta a duplicação.
4. Given uma spec sem o header `**Template:** 2` e sem a seção, When rodo `aiadev preflight plan`, Then não há erro de anchor ausente.
5. Given uma spec com `**Template:** 2` e sem a seção, When rodo `aiadev preflight plan`, Then o preflight aborta citando a seção ausente.

### Story 2 — `implement` termina gerando a checklist (P1)

Como tech lead, quero que o `implement` feche gerando a checklist de validação a partir da spec para que eu receba o roteiro pronto quando o trabalho automático terminar.

**Acceptance scenarios:**

1. Given todas as tasks `done` e o review final da branch concluído, When o `implement` termina, Then a checklist existe em `specs/<branch>/` com um item por critério, na ordem da spec, e o hand-off pede o aceite humano.
2. Given a spec tem N critérios, When a checklist é gerada, Then tem exatamente N itens, e cada item cita o critério de origem.
3. Given a checklist já existe de uma execução anterior com itens preenchidos, When o `implement` é retomado, Then os resultados já registrados são preservados.

### Story 3 — Merge exige aprovação humana (P1)

Como tech lead, quero que o `finishing-a-branch` só avance com o meu aceite registrado para que nenhuma feature seja mesclada só com aprovação de agentes.

**Acceptance scenarios:**

1. Given `.aiadev/review.yaml` com `status: approved` e a checklist com itens sem resultado, When rodo `aiadev preflight finishing-a-branch`, Then aborta com mensagem que aponta a checklist.
2. Given todos os itens aprovados e o aceite registrado via `aiadev accept` num terminal, When rodo o preflight, Then passa.
3. Given o aceite foi registrado e depois entrou um commit novo ou a checklist mudou, When rodo o preflight, Then aborta dizendo que o aceite está desatualizado.
4. Given o aceite registrado mas `.aiadev/review.yaml` com `changes_requested`, When rodo o preflight, Then aborta — os dois gates são exigidos.
5. Given o agente roda `aiadev accept` pelo próprio shell, sem TTY, When o comando executa, Then recusa sem gravar nada e explica que o aceite é feito por uma pessoa num terminal.
6. Given `AIADEV_PREFLIGHT=warn` definido e nenhum aceite registrado, When rodo `aiadev preflight finishing-a-branch`, Then o gate de aceite continua abortando (os demais checks viram aviso).

### Story 4 — Critério reprovado volta para o pipeline (P2)

Como tech lead, quero que um critério reprovado na validação gere trabalho rastreável para que a correção passe pelo mesmo processo.

**Acceptance scenarios:**

1. Given um item reprovado com observação, When o hand-off roda, Then a skill recomenda `systematic-debugging` ou uma nova task em `tasks.md` citando o critério.
2. Given a correção foi feita e revisada, When a checklist é reaberta, Then só os itens afetados voltam a ficar pendentes.
3. Given itens reprovados, When rodo `/aia:help`, Then o "Próximo passo" não recomenda `finishing-a-branch`.

<!-- section: Clarifications -->
## Clarifications

- **cl-1 (registro do aceite):** comando interativo `aiadev accept --feature <slug>` que **exige TTY** (recusa quando stdin/stdout não são terminal), mostra a checklist e pede confirmação digitada. Grava em `.aiadev/` o autor (`git config user.name`), o timestamp UTC, o `HEAD` e o hash da checklist. O preflight só aceita o registro se `HEAD` e hash ainda batem; qualquer commit ou edição posterior da checklist invalida o aceite. Como é CLI, funciona igual nas 5 plataformas. Limite assumido: o objetivo é impedir registro **acidental ou silencioso** pelo agente (cujo shell não tem TTY), não resistir a um agente que simule terminal de propósito.
- **cl-2 (bypass de depuração):** `AIADEV_PREFLIGHT=warn` **não** rebaixa o gate de aceite humano; continua valendo só para os checks de artefato. Como o agente consegue definir a variável sozinho, deixá-la valer aqui anularia cl-1. A única dispensa é `aiadev accept --waive "<motivo>"`, rodado por uma pessoa num terminal (mesma exigência de TTY), com o motivo registrado.
- **cl-3 (isenção de specs antigas):** header de versão do template. O `spec-template.md` ganha `**Template:** 2`; spec com esse header precisa ter a seção "Critérios de validação", spec sem header fica isenta. Não depende da numeração de specs do projeto (um `cutover_spec_id` usaria a numeração do aiadev e falharia em consumidores) e serve de novo na próxima mudança de template. `preflight` e `_tooling/payload.py` passam a derivar as seções obrigatórias da versão declarada.
- **cl-4 (branches isentas):** o gate segue a spec. O aceite é exigido exatamente quando a branch tem spec com `**Template:** 2`, porque é dela que vêm os critérios. Branches que o Artigo I dispensa de spec (typo, docs, revert, `hotfix:`) não têm critérios e ficam fora do gate, sem flag nova; um `hotfix:` entra no gate quando a spec retroativa de 72 h for escrita.
- **cl-5 (relação com *Success criteria*):** convivem com papéis distintos. *Success criteria* segue como está: resultados mensuráveis, verificados por teste ou métrica. "Critérios de validação" são passos que uma pessoa executa antes do merge, cada um com o resultado observável esperado. O template explica a diferença, e o `spec-document-reviewer` aponta critério que copia um success criterion ou que só se verifica lendo código. Nenhuma spec existente muda de sentido.

<!-- section: Data touched -->
## Data touched

- `templates/spec-template.md` (seção e anchor novos, header `**Template:** 2`); `src/aiadev/preflight.py` (`SPEC_ANCHORS`, gate de aceite); `src/aiadev/_tooling/payload.py` (`_SPEC_REQUIRED_SECTIONS`); `src/aiadev/pipeline_state.py`.
- Skills: `specify`, `implement`, `requesting-code-review` (sem remover nada), `finishing-a-branch`; agente `agents/spec-document-reviewer.md` (verifica a seção nova).
- Projeto consumidor: um artefato de checklist por feature em `specs/<branch>/` e um registro de aceite em `.aiadev/` (autor, timestamp, `HEAD`, hash da checklist).

<!-- section: Out-of-band effects -->
## Out-of-band effects

- Nenhum. O registro de aceite é local (cl-1); nenhuma chamada de rede.

<!-- section: Open risks -->
## Open risks

- **Quebra de compatibilidade:** incluir o anchor em `SPEC_ANCHORS` sem regra de corte faz o `preflight plan` abortar em toda spec existente, inclusive nos consumidores.
- **Aceite de fachada:** se o registro for fácil de forjar, o agente pode "aprovar" pelo humano e o gate vira teatro.
- **Atrito:** um gate humano por feature desacelera o modo roadmap (spec 0028); a 0028 (cl-5) decidiu acumular os aceites e seguir só com features independentes.
- **Critérios vagos:** sem orientação clara, a seção vira cópia dos *Success criteria*.

<!-- section: Traceability -->
## Traceability

- Originating issue: comparação do aiadev com o curso "Spec-Driven Development with Coding Agents" (DeepLearning.AI × JetBrains, Paul Everitt) — conversa de 2026-09-24, melhoria 3 de 7.
- Related specs: `0010-pipeline-preflight-checks` (preflight), `0014-bmad-inspired-evolutions` (zero-findings-halt, que não pode regredir), `0028-implement-roadmap-mode` (pausa no aceite humano).
- Constitution articles invoked: I, II, IV, V (condicional), VI

### Constitution Check (preliminar)

> Avaliação no nível da spec. O `plan` refaz a checagem com evidência concreta.

| Artigo | Aplica? | Avaliação preliminar |
|---|---|---|
| I. Spec-first | Sim | Esta spec; cl-1…cl-5 resolvidas em 2026-09-24. |
| II. Test-first | Sim | Testes de preflight (checklist incompleta, aceite ausente, grandfathering) e de template antes das edições. |
| III. Simplicity | Sim | Reaproveita o preflight e `.aiadev/` existentes; um único artefato de checklist por feature. |
| IV. Evidence over claims | Sim | Reforça o artigo: o aceite humano é a evidência de comportamento que os testes não cobrem; o registro é relido pelo preflight. |
| V. Provider pattern | Não | cl-1 escolheu registro local; sem fronteira de rede. |
| VI. Privacy by design | Sim | O registro de aceite guarda identidade mínima (sem e-mail em log de texto puro). |
| VII. Attribution | Não | Nada adaptado: escrito do zero. A entrada de inspiração do curso SDD no `CREDITS.md` (spec 0023, cl-6) cobre a ideia. |
