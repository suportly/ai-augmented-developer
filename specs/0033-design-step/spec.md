# Feature specification: Passo /aia:design — protótipo no Claude Design a partir das tasks

> Produced by `specify`. **What** and **why** only; planning and code belong in `plan.md` and `tasks.md`.

**Branch:** `feature/0033-design-step`
**Created:** 2026-10-28
**Status:** Draft <!-- Draft | In review | Approved | Implemented -->
**Spec ID:** 0033 <!-- auto-incrementing integer -->
**Language:** pt-BR <!-- BCP-47 tag; downstream artifacts use it. -->

---

<!-- section: Problem -->
## Problem

Numa feature com interface, o pipeline vai de `tasks` direto para `implement`: a primeira vez que alguém vê as telas é depois do código escrito, quando mudar custa caro. O Claude Design permite desenhar as telas como protótipo antes do código, mas hoje nada liga as tasks aprovadas a esse protótipo: o usuário teria de descrever tudo de novo, e o agente poderia mandar para fora da máquina mais do que as telas (caminhos de arquivo, commits, nomes internos). Também nada registra no repositório qual protótipo vale para a feature nem quais lacunas ele revelou.

<!-- section: Reconnaissance -->
## Reconnaissance

- **comando e skill de pipeline** — entry: `commands/tasks.md` · auth: none · integration: `skills/tasks/SKILL.md` (cada passo é um comando fino que invoca uma skill; `/aia:design` seguiria o mesmo molde)
- **próximo passo do pipeline** — entry: `src/aiadev/pipeline_state.py` · auth: none · integration: `src/aiadev/commands/next.py` (hoje `tasks.md` presente com tasks pendentes recomenda `/aia:implement`, sem noção de UI nem de design)
- **gates antes de implementar** — entry: `src/aiadev/preflight.py` · auth: none · integration: `src/aiadev/task_context.py` (o preflight de `implement` valida cenário→task; `task_context.py` já lê os cenários que cada task cita)
- **âncoras da spec** — entry: `templates/spec-template.md` · auth: none · integration: `src/aiadev/preflight.py` (âncoras `<!-- section: X -->` são validadas; uma declaração de UI na spec precisa de lugar nelas)
- **papéis de subagente** — entry: `src/aiadev/token_metrics.py` · auth: none · integration: `tests/test_dispatch_description_convention.py` (o papel sai do prefixo da `description` do dispatch: `implement:`, `review:`, `doc-review:`; um prefixo novo `design:` precisa ser classificado)
- **percurso e orçamento** — entry: `docs/pipeline-path.yaml` · auth: none · integration: `docs/instruction-budget.json` (skill lida só sob demanda fica fora do percurso, como `skills/task-context/SKILL.md`; a listagem de skill e comando conta no sempre-carregado e o teto só sobe com razão)
- **skill de interface existente** — entry: `presets/django-drf-react/skills/frontend-design/SKILL.md` · auth: none · integration: none (orienta como escrever o código da interface; não produz protótipo e não é o mesmo que este passo)
- **Claude Design** — fora do repositório: o protótipo é um Artifact do tipo Design (canvas privado no claude.ai, uma tela por artboard), criado pela ferramenta `Artifact`, que existe só no Claude Code; Codex, Gemini, Cursor e OpenCode instalam as mesmas skills sem ela.

<!-- section: Users and stakeholders -->
## Users and stakeholders

- Quem desenvolve uma feature com interface com o aiadev e quer ver as telas antes do código.
- Quem revisa a feature: o `design.md` mostra qual protótipo e quais cenários cada tela cobre.
- Mantenedor do aiadev: carrega o custo fixo de instrução e a responsabilidade pelo que sai da máquina do usuário.

<!-- section: Success criteria -->
## Success criteria

- `/aia:design` existe como passo opcional depois de `/aia:tasks` e produz `specs/<feature>/design.md` com o link do protótipo, o mapa tela → cenário da spec → task e a lista de lacunas.
- O brief enviado ao Claude Design contém só conteúdo de tela (telas, cenários Given/When/Then, estados, textos da spec): nenhum caminho de arquivo, hash de commit, id de task nem nome de módulo interno.
- Nada é publicado sem confirmação do usuário, e o protótipo nasce privado.
- `aiadev next` recomenda `/aia:design` só quando a spec declara UI, o `tasks.md` existe e o `design.md` não; sem essa declaração, o comportamento atual não muda.
- O `preflight implement` avisa (sem falhar) quando a spec declara UI e não há `design.md`; nenhum gate existente é removido ou enfraquecido.
- Sem a ferramenta `Artifact`, o passo gera wireframes em markdown no `design.md` e diz ao usuário que não pôde criar o protótipo.
- O percurso do pipeline (`docs/pipeline-path.yaml`) não muda; qualquer aumento de teto em `docs/instruction-budget.json` tem razão registrada e autorização explícita do mantenedor.

<!-- section: Non-goals -->
## Non-goals

- Um comando `aiadev design brief` que monte o brief por código: o agente monta o brief nesta versão; só vale se a medição mostrar que isso é caro.
- Gerar código a partir do protótipo ou integrar o `design:design-handoff`; a saída é o protótipo e o `design.md`.
- Tornar o passo obrigatório, ou bloquear `implement` por falta de design.
- Depender do claude.ai/design standalone, que o aviso da ferramenta de design da sessão informa estar programado para fechar; o caminho é o Artifact do tipo Design.
- Sincronizar design system (`DesignSync`); se o usuário tiver um design system padrão, o próprio Claude Design o aplica.

<!-- section: User stories -->
## User stories

### Story 1 — Brief só com conteúdo de tela (P1)

Como desenvolvedor de uma feature com UI, quero que o passo monte o brief a partir das tasks para eu não ter de descrever as telas de novo, sem expor o que não é tela.

**Acceptance scenarios** (≥ 3 per story):

1. Given uma spec que declara UI e um `tasks.md` aprovado, When o usuário roda `/aia:design`, Then a skill lista as tasks que considera de interface e só segue depois de o usuário confirmar ou ajustar a lista.
2. Given a lista confirmada, When a skill monta o brief, Then ele traz telas, cenários Given/When/Then, estados (vazio, erro, carregando) e textos definidos na spec.
3. Given o brief montado, When o usuário o lê, Then não há caminho de arquivo, hash de commit, id de task nem nome de módulo interno.
4. Given uma spec que não declara UI, When o usuário roda `/aia:design`, Then a skill avisa que a feature não declara UI e pergunta se deve seguir mesmo assim.

### Story 2 — Protótipo no Claude Design e registro no design.md (P1)

Como desenvolvedor, quero o protótipo criado no Claude Design e registrado na feature, para o time ver as telas antes do código.

**Acceptance scenarios**:

1. Given o brief pronto, When a skill vai publicar, Then mostra o que será enviado e só publica após confirmação explícita do usuário.
2. Given a confirmação, When o protótipo é criado, Then há um artboard por tela, o canvas é privado e o dispatch usa `description` `design: <slug>`.
3. Given o protótipo criado, When o passo termina, Then `specs/<feature>/design.md` traz o link, o mapa tela → cenário → task e as lacunas encontradas.
4. Given que o usuário já tem um design system padrão no Claude Design, When o protótipo é criado, Then a skill não pede nem reconfigura nada sobre ele.

### Story 3 — Lacunas viram emenda de tasks (P2)

Como desenvolvedor, quero que o que o protótipo revelou (tela ou estado sem task) vire task, sem alteração silenciosa.

**Acceptance scenarios**:

1. Given que o protótipo revela um estado ou uma tela sem task correspondente, When o `design.md` é gravado, Then a lacuna aparece na lista de lacunas citando o cenário da spec que a motiva ou dizendo que não há.
2. Given uma lacuna, When a skill propõe a emenda, Then mostra as tasks novas e só as acrescenta ao `tasks.md` depois de o usuário aprovar.
3. Given uma emenda aprovada, When o `preflight implement` roda, Then a cobertura cenário → task continua sem erro.

### Story 4 — O fluxo recomenda o passo sem bloquear (P1)

Como desenvolvedor, quero que `aiadev next` me lembre do design quando faz sentido, sem travar quem não precisa.

**Acceptance scenarios**:

1. Given uma spec que declara UI, com `tasks.md` e sem `design.md`, When rodo `aiadev next`, Then a recomendação é `/aia:design`, com o motivo.
2. Given a mesma feature com `design.md` presente, When rodo `aiadev next`, Then a recomendação volta a ser a do fluxo normal (`/aia:implement`).
3. Given uma spec sem UI declarada, When rodo `aiadev next`, Then o resultado é idêntico ao de hoje.
4. Given uma spec com UI declarada e sem `design.md`, When rodo `aiadev preflight implement`, Then sai com aviso e código de saída 0, e o `implement` continua possível.

### Story 5 — Funciona fora do Claude Code (P2)

Como usuário de outra plataforma, quero o mesmo passo mesmo sem a ferramenta de protótipo.

**Acceptance scenarios**:

1. Given uma plataforma sem a ferramenta `Artifact`, When rodo `/aia:design`, Then a skill diz que não pode criar o protótipo e gera wireframes em markdown no `design.md`.
2. Given os wireframes, When leio o `design.md`, Then ele tem o mesmo mapa tela → cenário → task e a mesma lista de lacunas.
3. Given uma falha ao criar o protótipo (rede ou recusa), When o passo termina, Then nenhum link falso é gravado e o usuário recebe o motivo e a opção de seguir com wireframes.

<!-- section: Clarifications -->
## Clarifications

- **cl-1 (resolvida em 2026-10-28):** a skill `design` e o comando `/aia:design` entram no núcleo, instalados em todo preset. O mantenedor escolheu essa opção sabendo que ela sobe o teto de instrução, e isso vale como autorização explícita para subir os tetos afetados em `docs/instruction-budget.json`, com razão registrada e só pelo custo da listagem (skill e comando).

## Assumptions

- A declaração de UI na spec é um campo explícito preenchido pelo `specify`, lido por máquina; a forma exata (linha de cabeçalho ou âncora) é decisão do plan. [impact: low]
- O brief é montado pelo agente nesta versão; um `aiadev design brief` determinístico fica para depois. [impact: low]
- A escolha das tasks de interface é do agente, sempre confirmada pelo usuário; nenhuma heurística por palavra-chave no código. [impact: low]
- O protótipo vive no claude.ai e pode mudar de acesso ou sumir; o `design.md` guarda o link e o mapa, não os arquivos do canvas, e o mapa continua útil sem o link. [impact: low]

<!-- section: Data touched -->
## Data touched

- Conteúdo de tela da spec (telas, cenários, estados, textos) enviado ao claude.ai para criar o protótipo.
- Arquivo novo por feature: `specs/<feature>/design.md` (link, mapa, lacunas).
- Possível emenda do `tasks.md`, aprovada pelo usuário.

<!-- section: Out-of-band effects -->
## Out-of-band effects

- Rede: criar o protótipo publica um canvas privado no claude.ai da conta do usuário; nada sai sem confirmação.
- Custo: o dispatch com `description` `design: <slug>` permite medir o custo do passo por papel em `aiadev metrics --tokens`; a decisão de manter o passo opcional se apoia nessa medição, sem limiar fixado nesta spec.

<!-- section: Open risks -->
## Open risks

- Vazamento de contexto interno no brief: mitigado por regra explícita, confirmação antes de publicar e teste que fixa a regra no texto da skill.
- Brief que descreve tela por analogia e não pela spec (Art. I): o brief só pode citar cenários e textos que estão na spec.
- Link do protótipo que deixa de abrir: aceito; o mapa no `design.md` continua útil sem ele.
- Custo de instrução dos novos comando e skill: sobe o teto de cada preset pelo custo da listagem (autorizado em cl-1); a medição vai para o plan.
- Deriva do Claude Design (mudança de tipo ou de contrato do canvas): a skill descreve o resultado esperado e delega o formato ao próprio tipo, sem copiar as regras dele.

<!-- section: Traceability -->
## Traceability

- Originating issue: pedido do mantenedor em 2026-10-28 (novo passo `/aia:design` depois de `/aia:tasks`); sem entrada `R<NNN>` no roadmap
- Related specs: 0030-lean-pipeline (orçamento de instrução, papéis de dispatch), 0031-context-hygiene (subagente para manter o contexto principal limpo), 0032-find-skills (precedente de skill genérica e subida de teto autorizada)
- Constitution articles invoked: I, III, IV, VI
