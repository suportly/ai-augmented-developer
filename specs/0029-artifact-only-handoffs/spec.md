# Feature specification: contexto limpo entre etapas — `specify`, `plan` e `tasks` passam o trabalho só pelos artefatos em disco

> This file is produced by the `specify` skill (or by `aiadev init --feature <name>` as a stub). Keep it focused on **what** and **why** — planning and code belong in `plan.md` and `tasks.md`.

**Branch:** `feature/0029-artifact-only-handoffs`
**Created:** 2026-09-24
**Status:** Draft <!-- Draft | In review | Approved | Implemented -->
**Spec ID:** 0029 <!-- auto-incrementing integer -->
**Language:** pt-BR <!-- BCP-47 tag; every downstream artifact in this feature is written in this language. -->

---

<!-- section: Problem -->
## Problem

O `implement` já trabalha com contexto limpo: cada task vai para um subagente novo com um prompt montado a partir dos artefatos, e a skill proíbe repassar o histórico da sessão. As etapas anteriores não têm essa disciplina. `specify`, `clarify`, `plan` e `tasks` costumam rodar na mesma conversa, e o hand-off de cada uma é "invoke `plan`" / "invoke `tasks`" na mesma sessão. O `plan` pode então apoiar-se em algo que foi dito na conversa e nunca entrou no `spec.md`; o `tasks` pode herdar uma decisão que não está no `plan.md`. Essa informação escondida não é revisada pelos reviewers de documento, não aparece para quem retoma a feature em outra sessão ou plataforma e é a origem do drift que o `analyze` depois tenta encontrar. O curso SDD roda cada etapa com contexto limpo, passando o trabalho só pelos arquivos. Quem sente: quem retoma uma feature dias depois ou em outra ferramenta e encontra um plano que a spec não explica.

<!-- section: Reconnaissance -->
## Reconnaissance

- **modelo a seguir** — entry: `skills/implement/SKILL.md` · auth: none · integration: passo 4 "Hand-craft the context — do not forward full conversation history" e a regra "Never forward the full session transcript to a subagent"; seção "Task-context integration" (skill `task-context`) compõe o contexto por task a partir do disco.
- **hand-offs atuais** — entry: `skills/specify/SKILL.md` · auth: none · integration: seção "Hand-off" (`clarify` ou `plan`) sem instrução de contexto; o mesmo vale para `skills/plan/SKILL.md` ("Plan approved … → invoke `tasks`") e `skills/tasks/SKILL.md`.
- **já existe montagem a partir do disco (parcial)** — entry: `src/aiadev/_tooling/payload.py` · auth: none · integration: no modo LLM-tool/MCP, `aiadev.tools.specify/plan/tasks` montam um `ToolPayload` com SKILL.md + template + trecho da constituição + artefato de entrada lidos do disco, e a diretiva *Single required artifact* limita a saída a um arquivo. Ou seja, **nesse modo o hand-off já é por artefato**; falta o mesmo no uso interativo pelas skills.
- **checagem de artefatos** — entry: `src/aiadev/preflight.py` · auth: none · integration: `check` já exige os artefatos anteriores de cada etapa (spec sem marcadores para `plan`, `plan.md` para `tasks`); não verifica se o artefato é **suficiente**, só se existe.
- **suporte a subagentes por plataforma** — entry: `src/aiadev/platforms/opencode.py` · auth: none · integration: os handlers instalam artefatos do papel `agent` (ex.: `.opencode/agents/`), mas o mecanismo de contexto limpo difere entre as plataformas; a escolha por plataforma está em cl-1.
- **revisores de documento** — entry: `agents/plan-document-reviewer.md` · auth: none · integration: os critérios atuais (alinhamento com a spec, TDD, granularidade) não verificam proveniência; detectar decisão no `plan.md` sem origem no `spec.md` é um critério **novo** a acrescentar.

<!-- section: Users and stakeholders -->
## Users and stakeholders

- **Quem retoma uma feature** (outra pessoa, outro dia, outra plataforma) — precisa que os artefatos bastem.
- **Reviewers de documento** — só conseguem revisar o que está escrito.
- **Tech lead** — quer menos drift entre spec, plano e código.

<!-- section: Success criteria -->
## Success criteria

- Cada etapa (`specify` → `plan` → `tasks`) declara na própria skill a lista fechada de entradas que pode ler (artefatos, constituição, templates e, quando existirem, os artefatos de produto da spec 0023) e termina com um hand-off que referencia a próxima etapa **só por caminho de arquivo**.
- Rodar `plan` numa sessão nova, só com os artefatos em disco, gera um plano que cobre as mesmas user stories e decisões que o plano gerado na mesma sessão do `specify` (verificável com um e2e de duas execuções sobre o mesmo `spec.md`).
- O `plan-document-reviewer` aponta como problema qualquer decisão do `plan.md` que não tenha origem no `spec.md`, na constituição ou nos artefatos de produto; o mesmo para o `tasks.md` em relação ao `plan.md`.
- Nas 5 plataformas existe um caminho documentado para rodar a etapa seguinte com contexto limpo, na cascata de cl-1: subagente (Claude Code, Cursor, Gemini), comando de sessão nova (`codex exec`, `opencode run`) ou instrução de chat novo.
- O efeito é medido por **custo por feature concluída e número de turnos**, não por tokens economizados: comparação pareada em ≥ 5 features no Claude Code (cl-4). O despacho só vira padrão se o custo por feature não subir e a aprovação de primeira do `plan-document-reviewer` não piorar.

<!-- section: Non-goals -->
## Non-goals

- Mudar o `clarify`: ele é interativo por definição e já grava as respostas no `spec.md`.
- Mudar o `implement`, que já tem contexto limpo por task.
- Reescrever o modo LLM-tool/MCP, que já é baseado em artefato.
- Verificação mecânica de proveniência (header ou hash dos artefatos lidos) — fora da v1 (cl-2).
- Bloquear o uso na mesma sessão: continua possível, mas o artefato passa a ser a única fonte aceita.

<!-- section: User stories -->
## User stories

### Story 1 — Cada etapa lê só os artefatos (P1)

Como quem retoma uma feature em outra sessão, quero que `plan` e `tasks` dependam apenas dos arquivos em disco para que o resultado não mude conforme a conversa em que foram rodados.

**Acceptance scenarios** (Given / When / Then, ≥ 3 per story):

1. Given um `spec.md` aprovado, When rodo `plan` numa sessão nova, Then o plano gerado cobre todas as user stories da spec sem pedir informação que não esteja nos artefatos.
2. Given uma decisão foi discutida na conversa do `specify` mas não entrou no `spec.md`, When o `plan` roda, Then a decisão não aparece no plano; se for necessária, a skill pede que ela entre na spec via `clarify` antes.
3. Given `plan.md` aprovado, When rodo `tasks` numa sessão nova, Then as tasks cobrem todas as fases do plano e cada task cita a fase de origem.

### Story 2 — Hand-off só por caminho (P1)

Como usuário do pipeline, quero que o fim de cada etapa diga o que rodar em seguida e com quais arquivos para que eu possa continuar em qualquer sessão ou plataforma.

**Acceptance scenarios:**

1. Given o `specify` terminou com spec sem marcadores, When a skill entrega, Then o hand-off diz "rodar `plan` com `specs/<NNNN-slug>/spec.md`" e não resume a conversa.
2. Given a flag de despacho ligada no preset e uma plataforma com subagentes, When o hand-off acontece, Then a etapa seguinte é despachada num subagente com prompt montado só a partir dos caminhos.
3. Given a flag de despacho ligada no Codex ou no OpenCode, When o hand-off acontece, Then a etapa seguinte roda via `codex exec` ou `opencode run` com prompt montado só a partir dos caminhos; onde nenhum mecanismo estiver confirmado, a skill instrui abrir chat novo com o comando e os caminhos exatos.
4. Given a flag de despacho desligada (padrão), When o hand-off acontece, Then a skill só indica o comando e os caminhos e a etapa seguinte roda onde o usuário escolher.

### Story 3 — Reviewer detecta informação que não veio dos artefatos (P2)

Como reviewer de plano, quero apontar decisões sem origem nos artefatos para que o conteúdo implícito seja trazido para a spec.

**Acceptance scenarios:**

1. Given o `plan.md` introduz uma restrição que não está no `spec.md`, na constituição nem nos artefatos de produto, When o `plan-document-reviewer` revisa, Then retorna `ISSUES_FOUND` citando a linha do plano.
2. Given todas as decisões do plano têm origem citável, When o reviewer revisa, Then essa verificação aparece no bloco `### Why no issues`.
3. Given o `tasks.md` tem uma task sem fase correspondente no `plan.md`, When o `analyze` roda, Then a task aparece na nova classe de gap "Task without plan coverage", ao lado das quatro existentes.

<!-- section: Clarifications -->
## Clarifications

- **cl-1 (mecanismo por plataforma):** cascata por evidência — em cada plataforma, o primeiro mecanismo confirmado. **Subagente** em Claude Code (`.claude/agents/*.md`), Cursor (`.cursor/agents/`) e Gemini CLI (`.gemini/agents/*.md`, contexto isolado documentado). **Comando de sessão nova** no Codex (`codex exec`, que sempre começa sem histórico; o formato de subagente tem fontes divergentes, Markdown ou TOML, e exige `collab = true`, cf. `docs/README.codex.md`) e no OpenCode (`opencode run`; o isolamento de histórico do subagente não está documentado). Se nada estiver confirmado, a skill instrui abrir um chat novo e mostra o comando e os caminhos. Pesquisa de 2026-09-24 em code.claude.com/docs, cursor.com/docs/subagents, learn.chatgpt.com/docs, opencode.ai/docs e geminicli.com/docs. O plan inclui uma task de verificação na plataforma real antes de cada célula não confirmada virar mecanismo padrão.
- **cl-2 (verificação):** instrução nas skills + reviewer, sem mecanismo novo. As skills declaram as entradas permitidas e fazem o hand-off só por caminho; a garantia vem do `plan-document-reviewer`, que reprova decisão sem origem nos artefatos (Story 3). Não há header de proveniência nem hash. Um mecanismo só entra se a medição de cl-4 mostrar vazamento que o reviewer não pega (Artigo III).
- **cl-3 (padrão × opt-in):** a disciplina é padrão: ler só os artefatos declarados e fazer o hand-off só por caminho vale para todos, porque é texto das skills e custa pouco. O **despacho** da etapa seguinte com contexto limpo (subagente ou sessão nova) é opt-in, com uma flag no `preset.yaml` no mesmo molde de `task_context: true`, até a medição de cl-4 mostrar ganho em custo por feature e turnos. Precedente: a 0.24.0 removeu uma "otimização" de contexto que aumentava o custo por tarefa.
- **cl-4 (linha de base):** comparação pareada no Claude Code, a única plataforma cujos transcripts locais o `src/aiadev/token_metrics.py` lê. O mesmo `spec.md` roda `plan` + `tasks` uma vez na mesma sessão e outra com despacho limpo, em **pelo menos 5 features**. Métricas: custo (tokens ponderados por preço) e turnos via `token_metrics`, e a aprovação de primeira do `plan-document-reviewer`. Regra de decisão: o despacho só vira padrão se o custo por feature não subir e a aprovação de primeira não piorar. O relatório mostra a diferença por feature, sem p-valor.
- **cl-5 (task sem fase de origem):** quinta classe de gap no `analyze`, "Task without plan coverage", simétrica à "Plan without task coverage" existente. Detectável porque cada task passa a citar a fase de origem (Story 1, cenário 3). Só relatório: é mudança de texto em `skills/analyze/SKILL.md`, sem mecanismo novo (coerente com cl-2).

<!-- section: Data touched -->
## Data touched

- Skills: `skills/specify/SKILL.md`, `skills/plan/SKILL.md`, `skills/tasks/SKILL.md` (entradas declaradas e hand-off); `skills/analyze/SKILL.md` ganha a classe "Task without plan coverage" (cl-5). Agentes: `agents/plan-document-reviewer.md` ganha critério de proveniência; `agents/spec-document-reviewer.md` se couber.
- Documentação por plataforma: `docs/README.codex.md`, `docs/README.opencode.md` e equivalentes.

<!-- section: Out-of-band effects -->
## Out-of-band effects

- Nenhum. Muda a forma de encadear etapas locais; nada é enviado para fora.

<!-- section: Open risks -->
## Open risks

- **Mais turnos e mais custo:** reler artefatos em contexto novo pode custar mais do que continuar na mesma sessão; a medição de cl-4 decide se a mudança se paga.
- **Specs mais longas:** trazer para o `spec.md` o que antes ficava na conversa aumenta o documento.
- **Assimetria entre plataformas:** Codex e OpenCode usam sessão nova em vez de subagente, e onde nada está confirmado o contexto limpo depende do usuário abrir chat novo. Fatos de plataforma mudam rápido; as células não confirmadas precisam de verificação no plan.

<!-- section: Traceability -->
## Traceability

- Originating issue: comparação do aiadev com o curso "Spec-Driven Development with Coding Agents" (DeepLearning.AI × JetBrains, Paul Everitt) — conversa de 2026-09-24, melhoria 7 de 7.
- Related specs: `0008-llm-tool-integration` (payload por artefato já existente), `0014-bmad-inspired-evolutions` (skill `task-context`), `0023-product-context` (artefatos de produto como entrada permitida), `0016-agent-skills-interop` (paridade entre plataformas).
- Constitution articles invoked: I, II, III, IV

### Constitution Check (preliminar)

> Avaliação no nível da spec. O `plan` refaz a checagem com evidência concreta.

| Artigo | Aplica? | Avaliação preliminar |
|---|---|---|
| I. Spec-first | Sim | Reforça o artigo: a spec passa a ser a única fonte do plano. cl-1…cl-5 resolvidas em 2026-09-24. |
| II. Test-first | Sim | Testes de texto das skills (entradas declaradas, hand-off por caminho) e e2e de duas execuções do `plan` antes das edições. |
| III. Simplicity | Sim | Reaproveita o padrão do `implement` e o payload do modo LLM-tool; sem header nem hash de proveniência (cl-2). |
| IV. Evidence over claims | Sim | Efeito medido por custo por feature e turnos em ≥ 5 pares no Claude Code, com regra de decisão explícita (cl-4); fatos de plataforma com fonte (cl-1). |
| V. Provider pattern | Não | Sem fronteira de rede. |
| VI. Privacy by design | Não | Nenhum dado novo é registrado (cl-2 descartou header de proveniência). |
| VII. Attribution | Não | Nada adaptado: escrito do zero. A entrada de inspiração do curso SDD no `CREDITS.md` (spec 0023, cl-6) cobre a ideia. |
