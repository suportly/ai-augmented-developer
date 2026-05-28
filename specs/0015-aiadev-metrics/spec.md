# Feature specification: Métricas do aiadev a partir do audit trail existente

> This file is produced by the `specify` skill (or by `aiadev init --feature <name>` as a stub). Keep it focused on **what** and **why** — planning and code belong in `plan.md` and `tasks.md`.

**Branch:** `feature/aiadev-metrics`
**Created:** 2026-05-27
**Status:** Draft <!-- Draft | In review | Approved | Implemented -->
**Spec ID:** 0015 <!-- auto-incrementing integer -->
**Language:** pt-BR <!-- BCP-47 tag; every downstream artifact in this feature is written in this language. -->

---

<!-- section: Problem -->
## Problem

O framework já produz um audit trail estruturado por feature (status de spec, status por task, JSONL de reviews com APPROVED/CHANGES_REQUESTED + presença do bloco `### Why no issues`, commits por task), mas não há nenhum agregador desses dados. Hoje, um líder técnico que queira responder "minhas specs estão sendo aprovadas em primeira passada?" ou "quais tasks estão custando re-implementação?" precisa ler arquivo a arquivo. O custo é duplo: (1) a evidência que o framework gera com disciplina permanece invisível pra gestão de engenharia, e (2) regressões silenciosas no funcionamento dos próprios skills (prompt mudou, taxa de aprovação caiu) só são percebidas em retrospectiva qualitativa. A partir do [0014](../0014-bmad-inspired-evolutions/spec.md) (mergeado em `ed0554f`, v0.19.0) o substrato `.review-log.jsonl` é gravado por toda invocação de reviewer — temos a série temporal, falta o agregador.

<!-- section: Reconnaissance -->
## Reconnaissance

- **review log** — entry: `src/aiadev/review_log.py` · auth: none · integração: `append_review_entry`/`last_review_entry` referenciados em [skills/implement/SKILL.md:241-259](../../skills/implement/SKILL.md) e em `tests/test_review_log.py`; o arquivo JSONL fica em `specs/<branch>/.review-log.jsonl` (uma entry por dispatch de reviewer, com `outcome`, timestamp, presença do bloco `### Why no issues` e classificação non-trivial).
- **task status** — entry: `src/aiadev/tasks_status.py` (introduzido pelo [spec 0013](../0013-implement-task-status-tracking/spec.md)) · auth: none · integração: leitor/escritor das rows `**Status:** pending|in_progress|blocked|done` em `specs/<branch>/tasks.md`; é a fonte para "quantas tasks por feature, em qual estágio".
- **pipeline state** — entry: `src/aiadev/pipeline_state.py` · auth: none · integração: já enumera specs e seus arquivos (`spec.md`, `plan.md`, `tasks.md`) por workspace; é o iterador natural pra varrer todas as features de uma vez.
- **spec header** — entry: `templates/spec-template.md` · auth: none · integração: os campos `Status:` (Draft|In review|Approved|Implemented|Merged) e `Created:` (linhas 5-9 do template) no header de cada `specs/<NNNN-slug>/spec.md` formam a linha do tempo "specify→merge" por feature.
- **CLI subcomandos** — entry: `src/aiadev/cli.py` · auth: none · integração: padrão de registro em `src/aiadev/commands/` (ver `commands/sync.py`, `commands/lang.py`, `commands/preflight.py`); é onde `aiadev metrics` se conecta.
- **markers `cl-N` (clarify)** — entry: `skills/clarify/SKILL.md` · auth: none · integração: contagem dos markers de clarificação no formato canônico do skill `clarify` (id `cl-N`) por versão do spec, derivada via `git log -p` sobre `specs/<branch>/spec.md`, é o sinal pra "número de iterações em clarify".

<!-- section: Users and stakeholders -->
## Users and stakeholders

- **Líderes técnicos / mantenedores do framework** — donos da decisão "estou regredindo ou progredindo na qualidade dos artefatos?". Beneficiários primários.
- **Engenheiros consumindo o framework** — leem o relatório pra ver se um spec específico vale revisar agora ou se ainda está em maturação.
- **Reviewers humanos de PR** — usam o sumário por feature como atalho de contexto antes de abrir o PR.
- **Mantenedores das skills do framework** — usam a métrica "taxa de APPROVED em primeira passada" como sinal de regressão quando alteram prompts de skill (especialmente relevante porque o framework suporta 5 agentes — uma mudança pode regredir só em um deles).

<!-- section: Success criteria -->
## Success criteria

- `aiadev metrics --feature <slug>` em qualquer feature com `.review-log.jsonl` retorna, em < 2 segundos, ao menos: (a) taxa de APPROVED em primeira passada por tipo de reviewer (spec / plan / code), (b) número de tasks por status atual, (c) número de tasks que receberam ≥ 1 CHANGES_REQUESTED no code review, (d) tempo decorrido entre o `Created:` do spec e o último commit na branch, (e) número de markers `cl-N` resolvidos vs. ainda abertos.
- `aiadev metrics` (sem `--feature`) emite o mesmo conjunto agregado sobre todas as specs do repo cujo header tem `Status:` em {Implemented, Merged}, dentro do intervalo de tempo padrão (definição em cl-4), com cada métrica acompanhada de `n=` (tamanho da amostra) e `coverage=` (fração das specs no intervalo que têm `.review-log.jsonl` — o resto é pré-0014).
- O exit code é 0 quando dados existem, 2 quando o intervalo selecionado não cobre nenhum spec com substrato (`.review-log.jsonl` ausente em 100% dos specs do intervalo), e a mensagem em ambos os casos cita o cutoff (`spec 0014`) pra deixar claro porque a amostra é parcial.
- Toda métrica reportada é derivada **somente** de arquivos versionados ou do git log — nenhuma chamada de rede, nenhuma escrita em arquivo do repo. Reexecutar `aiadev metrics` em commit antigo via `git checkout` produz o mesmo resultado daquele commit (determinismo histórico).
- O comando documenta, ao final da saída, **uma linha por métrica** dizendo "o que esse número não significa" (anti-Goodhart) — por exemplo, "taxa de APPROVED 1ª passada alta não implica qualidade; pode indicar reviewer permissivo ou specs triviais".

<!-- section: Non-goals -->
## Non-goals

- Dashboard, UI web, ou qualquer interface que não seja saída de CLI.
- Persistência de métricas em arquivo do repo (cada execução recalcula do audit trail).
- Comparação cross-repo / agregação entre múltiplos projetos consumidores (tratado em cl-2).
- Estimativa de custo de API ou tokens consumidos (deliberadamente fora — argumentado em conversa anterior; estimativas pré-execução são notoriamente imprecisas e geram número que ninguém confia).
- Telemetria por usuário ou identificação de quem invocou qual skill (privacy by design; ver Article VI da constitution).
- Detecção automática de "regressão" com alertas — o comando reporta números, interpretação é humana.

<!-- section: User stories -->
## User stories

### Story 1 — Inspecionar saúde de uma feature em andamento (P1)

Como **tech lead do framework**, quero rodar um único comando dentro de uma branch de feature e ver indicadores estruturados de quanto a spec/plan/tasks daquela feature passaram limpo, para decidir se a feature está madura para merge ou ainda precisa de iteração.

**Acceptance scenarios** (Given / When / Then, ≥ 3 per story):

1. Given uma branch `feature/xyz` cujo `specs/0099-xyz/.review-log.jsonl` tem 4 entries (2 spec reviewer APPROVED em 1ª passada, 1 code reviewer CHANGES_REQUESTED → 1 code reviewer APPROVED), When eu rodo `aiadev metrics --feature xyz`, Then a saída lista "spec reviewer: 2/2 (100%) approved on first pass · code reviewer: 1/2 (50%) approved on first pass · 1 task with re-implementation".
2. Given uma branch `feature/legacy` cuja spec foi escrita antes de 0014 e o `.review-log.jsonl` não existe, When eu rodo `aiadev metrics --feature legacy`, Then o comando termina com exit 2 e mensagem citando "spec antes do cutoff 0014; review trail indisponível; status de tasks ainda é reportado", e ainda assim imprime a contagem de tasks por status (que vem do `tasks.md`, não do JSONL).
3. Given uma branch `feature/in-progress` com `tasks.md` válido mas zero entries em `.review-log.jsonl` (nenhuma task chegou a review ainda), When eu rodo `aiadev metrics --feature in-progress`, Then a saída reporta "review trail: vazio (feature ainda no estágio de implement)" sem falhar, mostra `n=0` nas métricas dependentes do JSONL e `coverage=` apropriado, e exit 0.

### Story 2 — Visão agregada do repositório (P1)

Como **mantenedor do framework**, quero ver indicadores agregados sobre todas as specs implementadas/mergeadas num intervalo, para detectar tendência (a taxa de aprovação em 1ª passada está caindo? specs estão demorando mais entre `specify` e merge?) antes que vire problema percebido.

**Acceptance scenarios**:

1. Given um repositório com 20 specs com `Status: Merged` nos últimos 90 dias, sendo 12 com `.review-log.jsonl` (pós-0014) e 8 sem, When eu rodo `aiadev metrics`, Then o relatório mostra cada métrica do trail com `n=12 coverage=60%` e métricas baseadas em git/tasks com `n=20 coverage=100%`, com nota explícita de que a amostra do trail é parcial.
2. Given o mesmo repositório, When eu rodo `aiadev metrics --since 2026-03-01`, Then o filtro aplica sobre o `Created:` do spec header (não sobre o commit) e a saída inclui o intervalo efetivo `[2026-03-01, today]` na primeira linha.
3. Given dois snapshots do mesmo repo em commits diferentes (separados por 30 dias e 5 features novas), When eu rodo `aiadev metrics --since <30d-ago>` em cada um, Then a saída do snapshot mais recente reflete as 5 features novas e o valor `n=` cresce de forma monotônica entre os snapshots (regression test para determinismo histórico).

### Story 3 — Detecção de tasks que custaram caro (P2)

Como **engenheiro do framework**, quero ver quais tasks de uma feature precisaram de mais de uma rodada do code reviewer, para entender onde a complexidade real estava (e calibrar `tasks.md` no futuro).

**Acceptance scenarios**:

1. Given uma feature cuja `.review-log.jsonl` tem entries `T003: CHANGES_REQUESTED, T003: CHANGES_REQUESTED, T003: APPROVED`, When eu rodo `aiadev metrics --feature xxx --tasks`, Then a saída lista `T003: 3 review rounds (2 changes_requested → approved)` ordenando por número de rodadas decrescente.
2. Given uma feature onde nenhuma task teve mais de 1 rodada, When eu rodo `aiadev metrics --feature xxx --tasks`, Then a saída diz "todas as tasks aprovadas em 1ª passada" sem listar nada.
3. Given uma feature com 10 tasks mas só 6 alcançaram review (4 ainda em pending), When eu rodo `aiadev metrics --feature xxx --tasks`, Then a saída inclui um header `6/10 tasks reached review` antes da lista, deixando explícito que a amostra é parcial.

<!-- section: Clarifications -->
## Clarifications

- **cl-1 (resolved):** O MVP entrega **dois formatos**: `--format text` (default, humano-friendly em terminal) e `--format json` (estruturado, estável para CI/scripts). Markdown fica fora do MVP — adicionável em spec futura sem quebrar o contrato dos dois formatos atuais.
- **cl-2 (resolved):** Escopo do MVP é **single-repo (cwd)** — `aiadev metrics` opera apenas sobre o workspace corrente. Cross-repo aggregation fica explicitamente fora deste spec (já reforçado no Non-goals) e vira spec própria quando os outros consumidores do framework tiverem trail consistente.
- **cl-3 (resolved):** Saída padrão emite **apenas contagens, timestamps e flags estruturadas** dos entries de `.review-log.jsonl`. A prosa livre dos reviewers (corpo das entries, incluindo o bloco `### Why no issues`) só aparece quando o usuário passa `--show-bodies` explicitamente. Article VI (Privacy by design) endereçado pela inversão do default.
- **cl-4 (resolved):** Janela temporal default é **últimos 90 dias** — `aiadev metrics` sem `--since` filtra specs cujo `Created:` está em `[today - 90d, today]`. Os campos `n=` e `coverage=` na saída comunicam honestamente quando a janela cai em zona pré-cutoff (specs pré-0014 sem `.review-log.jsonl`). 90 dias é o intervalo onde tendência ganha sinal sem virar histórico-distante; e o default permanente não fica acoplado à situação temporária de cobertura baixa imediatamente pós-0014.
- **cl-5 (resolved):** Superfície é **CLI only** (`aiadev metrics`). Não há skill espelhada no MVP — o precedente é `aiadev preflight` ([spec 0010](../0010-pipeline-preflight-checks/spec.md)), que existe como subcomando sem skill correspondente. Adicionar skill thin-wrapper fica como decisão de spec futura caso surja demanda real de invocação pelo agente.
- **cl-6 (resolved):** "1ª passada APPROVED" é definido como **a primeira entry cronológica de cada par `(task_id, reviewer)`** ter `verdict == "APPROVED"`. JSONL é append-only e escrito pelo orquestrador em ordem de dispatch, então ordem do arquivo = ordem de tentativa. Nenhuma mudança no schema da entry (`{timestamp, reviewer, verdict, has_why_no_issues_block, task_id, note}`). Para reviews de branch-level (entries com `task_id == "branch-review"`), o agrupamento é apenas por `(reviewer,)`. Se eventualmente o orquestrador passar a re-dispatchar fora de ordem (não ocorre hoje), o campo explícito de tentativa entra em spec própria.

<!-- section: Data touched -->
## Data touched

Leitura somente; nenhuma escrita em arquivo do repo:

- `specs/<NNNN-slug>/spec.md` — header (`Spec ID`, `Status`, `Created`, `Branch`).
- `specs/<NNNN-slug>/tasks.md` — rows `**Status:** ...` (via `aiadev.tasks_status`).
- `specs/<NNNN-slug>/.review-log.jsonl` — todos os campos da entry (timestamp, reviewer type, outcome, presença do bloco `### Why no issues`, classificação non-trivial, task id quando aplicável).
- `git log` — commit timestamps e mensagens (para "spec→merge" e contagem de iterações de clarify via histórico de `spec.md`).

Nenhum campo novo é criado em qualquer arquivo.

<!-- section: Out-of-band effects -->
## Out-of-band effects

Nenhum. O comando é puramente local, sem rede, sem escrita, sem credenciais. (Se uma futura versão for exportar para um endpoint, isso entra em spec próprio.)

<!-- section: Open risks -->
## Open risks

- **Goodhart**: qualquer métrica que vire OKR de time degrada como sinal. A mitigação proposta (uma linha de "o que isto não significa" por métrica) reduz, não elimina, o risco. Decidir se as métricas devem ser tornadas exportáveis pra dashboard é uma decisão estratégica separada — este spec mantém saída local justamente pra preservar essa decisão pra depois.
- **Amostra pequena pós-0014**: o cutoff é o spec 0014 (mergeado há ~14 dias). No início, `n=` será baixo e ruidoso; relatórios podem dar conclusões enganosas. Mitigação: sempre exibir `n=` e `coverage=`; documentar no help do comando que `n < 10` é leitura precoce.
- **Definição de "first-pass APPROVED" depende do schema da entry** (cl-6). Se o schema atual não tem `attempt_number`, o cálculo precisa inferir por ordem cronológica, o que é frágil se o orquestrador re-dispatcha fora da ordem esperada. Pode forçar uma extensão pequena ao schema de `.review-log.jsonl` — mas isso é decisão de plan, não de spec.
- **Sub-relato de tasks de features grandes**: features com 30+ tasks geram saída longa e ruidosa. Sem `--tasks`, agregamos; com `--tasks`, possivelmente truncar ou paginar (decisão de plan).
- **Specs com header não-canônico**: specs antigas têm `Status:` com valores fora do enum atual (ex.: "PR Open"). Parser precisa tolerar e classificar como "outro" ao invés de quebrar.

<!-- section: Traceability -->
## Traceability

- Originating issue: discussão em sessão com mantenedor (2026-05-27); sem issue formal aberta.
- Related specs: [0013](../0013-implement-task-status-tracking/spec.md) (substrato de tasks status), [0014](../0014-bmad-inspired-evolutions/spec.md) (substrato `.review-log.jsonl`), [0010](../0010-pipeline-preflight-checks/spec.md) (padrão de subcomando `aiadev preflight` que serve como referência).
- Constitution articles invoked: II (Test-first — calculadores são test-friendly), III (Simplicity — MVP local-only sem persistência), IV (Evidence over claims — feature é literalmente sobre tornar a evidência consultável), VI (Privacy by design — cl-3 endereça).
