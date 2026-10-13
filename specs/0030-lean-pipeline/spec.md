# Feature specification: pipeline enxuto — menos turnos, menos texto e medição correta de custo

> This file is produced by the `specify` skill (or by `aiadev init --feature <name>` as a stub). Keep it focused on **what** and **why** — planning and code belong in `plan.md` and `tasks.md`.

**Branch:** `feature/0030-lean-pipeline`
**Created:** 2026-10-13
**Status:** Draft <!-- Draft | In review | Approved | Implemented -->
**Spec ID:** 0030 <!-- auto-incrementing integer -->
**Language:** pt-BR <!-- BCP-47 tag; every downstream artifact in this feature is written in this language. -->

---

<!-- section: Problem -->
## Problem

O pipeline custa mais do que precisa, e hoje não há como provar quanto. Uma auditoria de 2026-10-13 sobre os transcripts de duas sessões longas deste repositório (setembro de 2026, não versionados) estimou que o texto das instruções é cerca de 1,3% do contexto médio por chamada; o custo está nos turnos da thread principal (cada chamada evitável carrega o contexto inteiro acumulado) e nos dispatches de revisão (dois reviewers por task e dois reviews de branch cobrindo o mesmo diff). Ao mesmo tempo, `aiadev metrics --tokens` soma o `usage` por evento, sem deduplicar por `message.id`, e não lê os transcripts de subagentes — superconta a thread principal e some com o custo que os subagentes geram. Sem medição correta, qualquer enxugamento vira opinião; o projeto já aprendeu isso ao remover o compressor de saída por modelo (PR #55).

As remoções desta spec têm razões distintas do custo de turnos, e cada uma é declarada: o terse-mode está sempre carregado, é opt-in e a promessa de "≥ 30% menos saída" não tem medição versionada (`specs/0009-token-economy-terse-mode/` não tem fixture de benchmark), enquanto a saída é uma parcela pequena do custo; `help` e `using-ai-augmented-developer` repetem em grande parte o que as descrições das skills e o `AGENTS.md` gerado em cada projeto já entregam (o estado de uma feature, hoje no `help`, é a pergunta aberta cl-1; e a segunda skill carrega também o mapeamento de ferramentas do Gemini, que deve ser preservado); `review-context.md` repete spec, plano e diff que o reviewer já lê. Quem sente: tech leads que pagam a conta por feature e desenvolvedores que esperam o pipeline terminar.

<!-- section: Reconnaissance -->
## Reconnaissance

- **medição de custo** — entry: `src/aiadev/token_metrics.py` · auth: none · integration: `read_session` soma `usage` de cada evento `assistant` (linhas 153-162) sem chave de deduplicação; `build_token_report` lê só os `*.jsonl` do diretório de transcripts do projeto. Nos transcripts reais os subagentes ficam em <sessão>/subagents/agent-*.jsonl, cada um com um `*.meta.json` ao lado (layout confirmado por listagem local, sem fixture no repositório). Comando exposto em `src/aiadev/commands/metrics.py`; a taxa de aprovação de primeira por reviewer já é calculada em `src/aiadev/metrics.py` (`per_reviewer_first_pass_rate`).
- **preflight e estado das tasks** — entry: `src/aiadev/preflight.py` · auth: none · integration: `check` devolve só erros e exige a branch feature/<slug> (`_git_current_branch`, linha 188); `tasks` **não** exige tasks.md (`_REQUIRES_TASKS` só lista `implement`, `analyze` e `finishing-a-branch`), então uma checagem sobre tasks.md só pode viver em `implement` ou `analyze`; `src/aiadev/tasks_status.py` expõe `parse` e `mark_done`, mas o `git add` e o commit por task são passos manuais do orquestrador em `skills/implement/SKILL.md`.
- **notação de cobertura** — entry: `src/aiadev/task_context.py` · auth: none · integration: `_SPEC_SCENARIOS_RE` e `_STORY_HEADING_RE` leem o campo "Spec scenarios" e o título de story, mas `_SCENARIO_REF_RE` só casa `sc<N>`, não a notação do template de tasks (`templates/tasks-template.md:29`, "Story 1 scenario 1, scenario 2"); parte dos tasks.md existentes cita só "Success criterion #N". A checagem de cobertura precisa de notação canônica.
- **skills do pipeline** — entry: `skills/implement/SKILL.md` · auth: none · integration: carrega sempre "Task-context integration" (linha 74, opt-in) e "Reviewer re-dispatch gate" (linha 233), e manda dois reviewers por task mais um "final full-branch review"; `skills/requesting-code-review/SKILL.md` repete o gate e cria review-context.md (linhas 29-31) com o diff colado no prompt; `skills/specify/SKILL.md` transforma toda incógnita em marcador, sem teto (passo 5); `skills/clarify/SKILL.md` não tem teto de perguntas.
- **conteúdo de stack em skills e agents genéricos** — entry: `skills/test-driven-development/SKILL.md` · auth: none · integration: Django, Celery, DRF e React aparecem também em `skills/systematic-debugging/SKILL.md`, `skills/finishing-a-branch/SKILL.md`, `skills/requesting-code-review/SKILL.md`, `skills/frontend-design/SKILL.md`, `agents/code-reviewer.md` e `agents/plan-document-reviewer.md`; a missão (Out of scope) já diz que orientação de stack pertence ao preset (`specs/_product/mission.md`).
- **presets e instalação** — entry: `src/aiadev/install_engine.py` · auth: none · integration: `_collect_artifacts` resolve por `(role, name)` e o preset **substitui** o artefato genérico de mesmo nome, nunca o estende; mover conteúdo de stack para um preset por cópia integral duplicaria o corpo genérico e criaria drift. O `lean` e o catálogo estão em `presets/lean/` e `presets/catalog.json`; o preset de stack em `presets/django-drf-react/CLAUDE.md`.
- **atualização de projetos instalados** — entry: `src/aiadev/install_manifest.py` · auth: none · integration: o manifesto registra hash por arquivo e sustenta `--uninstall`; `src/aiadev/commands/sync.py` atualiza o que o framework distribui, mas não há remoção de arquivo que o framework deixou de distribuir — é capacidade nova.
- **sempre-carregado** — entry: `rules/api-conventions.md` · auth: none · integration: `api-conventions`, `code-style`, `git-workflow` e `security` têm `alwaysApply: true`; `rules/slash-commands.md` e `rules/terse-mode.md` não têm frontmatter; só `rules/testing.md` tem `paths:`.
- **terse-mode (spec 0009)** — entry: `rules/terse-mode.md` · auth: none · integration: a chave `aiadev.terseMode` e a variável `AIADEV_TERSE` são resolvidas em `src/aiadev/config.py`; o bloco de contrato de saída está nos três arquivos de `agents/`; `schemas/terse-output.schema.json` e cerca de 12 testes (`tests/test_terse_mode_rule.py`, `tests/test_terse_mode_config.py`, `tests/test_agents_have_terse_block.py`, `tests/test_off_mode_unchanged.py`, `tests/test_sync_ships_terse_assets.py` e outros) fixam o recurso.
- **skills `help` e `using-ai-augmented-developer`** — entry: `skills/help/SKILL.md` · auth: none · integration: `/aia:help` é citado em `CLAUDE.md`, `templates/roadmap-template.md` e `docs/pipeline-reference.md`; `src/aiadev/pipeline_state.py` não tem consumidor de CLI (só `src/aiadev/review_log.py` o menciona), então um comando que informe o estado do pipeline seria novo. `using-ai-augmented-developer` é o ponto de entrada de `GEMINI.md` (importada nas primeiras linhas, junto de `skills/using-ai-augmented-developer/references/gemini-tools.md`, o mapeamento das ferramentas do Claude Code para as do Gemini, que não existe em outro lugar) e é citada em `docs/README.codex.md`, `commands/using-ai-augmented-developer.md`, `README.md`, `CONTRIBUTING.md` e `scripts/generate_pipeline_reference.py`.
- **checklists** — entry: `templates/checklist-template.md` · auth: none · integration: a tabela de falhas tem coluna "Owner task" (linha 79) e o rodapé exige que todo item não-N/A seja PASS ou tenha task dona (linha 85), o que torna o bloqueio mecânico viável; nenhuma skill lê `checklists/` depois de gerado.
- **spec-kit e atribuição** — entry: `CREDITS.md` · auth: none · integration: github/spec-kit já é creditado (linha 66); a análise de 2026-10-13 (commit `6c62e10`, v1.1.3, externo) é a fonte dos mecanismos adaptados aqui, e `tests/test_credits_attribution.py` verifica as entradas.

<!-- section: Users and stakeholders -->
## Users and stakeholders

- **Tech leads** — pagam o custo por feature e precisam de um número reprodutível para decidir.
- **Desenvolvedores que rodam o pipeline** — sentem a latência e a quantidade de rodadas.
- **Agentes que executam as skills** — recebem menos texto, menos passos manuais e nenhum conteúdo de stack que não se aplica ao projeto.
- **Autores de presets** — passam a ser donos do conteúdo de stack que hoje está no núcleo.
- **Mantenedor** — assina a remoção de recursos já publicados (terse-mode, `help`, `using-ai-augmented-developer`).

<!-- section: Success criteria -->
## Success criteria

- `aiadev metrics --tokens` numa sessão real deduplica por `message.id`, inclui os transcripts de subagentes e separa o custo da thread principal do custo dos subagentes, agrupando estes por papel (implementação, revisão) quando a descrição do dispatch segue a convenção de prefixo que `implement` e `requesting-code-review` passam a adotar (`implement:` ou `review:`) e como não classificados nos demais; o total confere, dentro de 1%, com a deduplicação manual da mesma sessão. O custo é uma **aproximação** com pesos documentados (leitura de cache, escrita de cache, entrada, saída).
- **Unidade e baseline:** "tokens" de instrução são estimados como caracteres ÷ 4 (sem tokenizador); o "percurso" é uma lista versionada de arquivos por etapa do pipeline. O baseline é registrado pela própria medição **antes** de qualquer corte, e o CI falha se o sempre-carregado ou o percurso crescerem acima dele. Meta: reduzir em ≥ 40% o sempre-carregado do preset `lean` e o percurso `specify → finish` em relação ao baseline (a auditoria estimou ~45%; a medição confirma ou corrige).
- Fechar uma task (marcar `done`, `git add`, commit) é uma chamada em vez de três ou quatro, e o `preflight` devolve de uma vez os caminhos da feature, os documentos existentes, o template e o comando de teste.
- Cobertura mecânica no `preflight implement`: cada cenário do `spec.md` é citado por ao menos uma task (diretamente ou pela story) e cada task cita um cenário, uma story ou um critério de sucesso nomeado (`Success criterion #N`, com N a ordem do bullet em Success criteria; citar uma story cobre todos os seus cenários, o que é uma checagem fraca por desenho e é aceito); a notação de cenário é `Story N scenario M` (a do template de tasks) e o legado `sc<N>` também vale; uma checklist com linha FAIL sem task dona bloqueia o `implement`.
- Uma task de código tem um reviewer e a branch tem um review; task que só altera prosa em markdown sob `docs/` ou documentação raiz é auto-verificada (o baseline e a lista de percurso do orçamento nunca entram nesse tier). Os gates de evidência e de re-dispatch seguem valendo.
- Cada gate listado em "O que não muda" tem um arquivo canônico declarado no `plan`, e um teste de comportamento falha se a frase do gate sumir desse arquivo.
- Um projeto instalado com `lean` não contém, em skills e agents, as palavras inteiras Django, Celery, DRF, React, MUI ou Expo (sem diferenciar maiúsculas) nem os termos `manage.py`, `select_related` e `on_commit`; o preset `django-drf-react` entrega esse conteúdo **sem duplicar o corpo genérico** da skill.
- O efeito é aceito por **custo por feature concluída**, não por tokens economizados: ≥ 5 pares antes/depois no Claude Code, aceito quando a mediana da razão custo depois/antes é menor que 1,0 e a taxa de aprovação de primeira agregada sobre todos os reviewers (calculada a partir da que `aiadev metrics` já registra por reviewer, porque os reviewers são fundidos) não cai mais de 5 pontos percentuais. Um par é a mesma micro-feature executada com as instruções de antes e de depois.

<!-- section: Non-goals -->
## Non-goals

- **Faixa rápida e lane de bug** — exigem emenda do Art. I; ficam em R009.
- **Modo `converge` no `analyze`** (R010), **feature ativa independente da branch** (R011), **waves paralelas de tasks** (R012) e **camada de confiança do catálogo remoto** (R013).
- Compressão de saída de ferramenta ou resumo por modelo: a evidência do PR #55 vale; nada aqui reintroduz isso.
- Medir ou ajustar o comportamento em Gemini, Codex, Cursor e OpenCode: recebem as mesmas skills, mas o benchmark roda no Claude Code.
- Os hand-offs só por artefato (R007, spec 0029): complementares; esta spec não muda o encadeamento nem o contrato de entrada e saída entre `specify`, `plan` e `tasks`. Muda o teto de marcadores no `specify`, a seção `## Assumptions` e o que o preflight verifica.
- Variar os pesos de custo por modelo: a v1 usa um conjunto único documentado.
- **O que não muda:** spec-first com preflight mecânico; RED observado por razão certa antes do GREEN; Constitution Check com evidência por artigo; evidência antes de afirmação (`review.yaml` aprovado antes do PR); flip de status atômico com o commit e rollback; causa-raiz antes do fix e escalada após 3 falhas; exclusão de arquivos secretos na inferência de produto; reconhecimento no `specify`.

<!-- section: User stories -->
## User stories

### Story 1 — Medir o custo de verdade (P1)

Como tech lead, quero que `aiadev metrics --tokens` conte cada chamada uma vez e inclua os subagentes, para decidir sobre o pipeline com números reprodutíveis.

**Acceptance scenarios** (Given / When / Then, ≥ 3 per story):

1. Given um transcript em que a mesma resposta aparece em vários eventos com o mesmo `message.id`, When rodo `aiadev metrics --tokens`, Then o `usage` dessa resposta é somado uma única vez, inclusive quando o mesmo `message.id` aparece em arquivos diferentes.
2. Given uma sessão com subagentes em `<sessão>/subagents/*.jsonl`, When rodo o comando, Then o relatório inclui o custo deles separado do da thread principal e agrupado por papel (implementação, revisão) quando o campo de descrição do `*.meta.json` segue a convenção de prefixo, ou "não classificado" quando não segue; o texto das mensagens nunca é lido para inferir o papel.
3. Given uma sessão sem diretório `subagents/` ou com um `*.meta.json` ilegível, When rodo o comando, Then o relatório sai sem erro e informa quantos subagentes ficaram sem classificação.
4. Given pesos de preço documentados, When o relatório é gerado, Then o total é um custo equivalente comparável entre sessões e o texto do relatório declara que é uma aproximação com esses pesos.

### Story 2 — Menos turnos para andar o pipeline (P1)

Como agente que executa `implement`, quero que preflight, leitura de template e fechamento de task sejam poucas chamadas, para que cada task consuma menos contexto acumulado.

**Acceptance scenarios** (Given / When / Then, ≥ 3 per story):

1. Given uma feature com `spec.md`, `plan.md` e `tasks.md`, When rodo `aiadev preflight <skill> --json`, Then recebo em uma saída os caminhos da feature, os documentos existentes, o caminho do template e o comando de teste detectado.
2. Given uma task concluída e verificada, When rodo o comando de fechamento com a mensagem e os arquivos, Then o status vira `done`, os arquivos entram no commit e o commit é feito; se o commit falhar, o status volta a `pending`.
3. Given um `spec.md` com um cenário que nenhuma task cita (nem diretamente nem pela story), When rodo o preflight de `implement`, Then ele falha apontando o cenário; o mesmo vale para uma task que não cita cenário, story nem critério de sucesso nomeado.
4. Given uma checklist com linha FAIL sem task dona, When rodo o preflight de `implement`, Then ele bloqueia e lista a linha.
5. Given uma feature em qualquer etapa do pipeline, When rodo `aiadev next --feature <slug>`, Then recebo em uma saída o estado atual (spec escrita, marcadores abertos, plano, tasks pendentes) e a próxima etapa a executar; uma entrada do roadmap sem spec informa que o próximo passo é `specify`.

### Story 3 — Uma revisão por task e uma por branch (P1)

Como tech lead, quero que a revisão cubra conformidade e qualidade sem dobrar o dispatch, para pagar um review por task e um por branch sem perder o gate.

**Acceptance scenarios** (Given / When / Then, ≥ 3 per story):

1. Given uma task que altera código, skill, agent, rule ou template, When o orquestrador despacha a revisão, Then um único reviewer recebe o diff, o resultado dos testes e os dois checklists em sequência e devolve um veredito.
2. Given uma task cujos arquivos são todos markdown de prosa sob `docs/` ou documentação raiz (README, CHANGELOG, CONTRIBUTING), e nenhum é o baseline ou a lista de percurso do orçamento, When a task termina, Then o orquestrador roda o lint de markdown e o validador do repositório sobre esses arquivos, registra o resultado e não despacha reviewer.
3. Given uma task em que a conformidade à spec e a qualidade têm problemas, When o reviewer único conclui o checklist de conformidade com achados, Then ele devolve o veredito com os achados de conformidade, sem executar o checklist de qualidade, preservando a regra de que qualidade só é avaliada depois de a conformidade estar aprovada.
4. Given o fim da implementação, When o review de branch é pedido, Then só `requesting-code-review` roda, grava `.aiadev/review.yaml`, e o `implement` não faz um segundo review completo da branch.
5. Given um reviewer que reprova a task, When o implementer corrige, Then a nova revisão continua exigida e o veredito de cada revisão é registrado no review-log com o vocabulário existente (APPROVED ou CHANGES_REQUESTED), para que `aiadev metrics` continue contando retrabalho; os dois limites de iteração existentes (correção→re-revisão e re-dispatch por falta de evidência) permanecem como estão.

### Story 4 — Instruções enxutas e sem stack alheio (P2)

Como autor de um projeto em Go ou Rust, quero que as skills genéricas não me falem de Django, para que o agente não aplique convenção de uma stack que não é a minha.

**Acceptance scenarios** (Given / When / Then, ≥ 3 per story):

1. Given um projeto instalado com o preset `lean`, When listo as skills e os agents instalados, Then nenhum arquivo contém, como palavra inteira e sem diferenciar maiúsculas, Django, Celery, DRF, React, MUI ou Expo, nem os termos `manage.py`, `select_related` ou `on_commit`.
2. Given um projeto instalado com `django-drf-react`, When o agente executa `test-driven-development` ou `systematic-debugging`, Then as orientações de stack estão disponíveis e o corpo genérico da skill não aparece duas vezes no projeto.
3. Given `implement` com a integração de task-context desligada (padrão), When a skill é carregada por padrão, Then o `SKILL.md` carregado não contém a seção de integração com task-context; o conteúdo vive em arquivo separado, referenciado e lido só quando a integração está ligada; e o gate de re-dispatch existe em um único arquivo referenciado pelos demais.
4. Given um baseline versionado de instruções, When o job de orçamento roda no CI, Then ele reporta o sempre-carregado por preset e o percurso do pipeline, e falha apontando o arquivo e o delta se algum exceder o baseline; no fechamento da spec, a redução contra o baseline é verificada uma vez contra a meta de 40% e registrada junto do benchmark, e o baseline versionado é então rebaixado para a medida pós-corte, para que as skills não reengordem até o valor antigo.

### Story 5 — Triagem em specify e clarify (P2)

Como desenvolvedor que descreve uma demanda, quero que a spec não vire um questionário, para chegar ao plano em menos rodadas sem perder as decisões que importam.

**Acceptance scenarios** (Given / When / Then, ≥ 3 per story):

1. Given uma demanda com mais de três incógnitas, When rodo `specify`, Then no máximo três viram marcadores de clarificação (priorizando escopo, segurança e UX) e as demais viram premissas explícitas em `## Assumptions`.
2. Given uma spec com `## Assumptions`, When o `spec-document-reviewer` revisa, Then ele verifica que cada premissa é de baixo impacto e reversível, e reprova a que decide escopo ou segurança.
3. Given marcadores abertos, When rodo `clarify`, Then faço no máximo cinco perguntas, uma por vez, ordenadas por impacto e incerteza, cada uma com recomendação que posso aceitar com uma palavra.

### Story 6 — Atualizar sem herdar recurso removido (P2)

Como usuário de um projeto já instalado, quero atualizar o framework sem ficar com arquivos órfãos nem configuração que não faz mais nada.

**Acceptance scenarios** (Given / When / Then, ≥ 3 per story):

1. Given um projeto com `rules/terse-mode.md` instalado pelo framework (hash igual ao do manifesto), When rodo `aiadev sync` na nova versão, Then o arquivo é removido; um arquivo que eu editei à mão (hash diferente) é preservado e listado.
2. Given `aiadev.terseMode` em `.claude/settings.json` ou `AIADEV_TERSE` no ambiente, When uso a nova versão, Then a chave é ignorada e um aviso de uma linha diz que o recurso foi removido.
3. Given uma plataforma cujo ponto de entrada era `using-ai-augmented-developer` (`GEMINI.md`, documentação do Codex), When a skill é removida, Then o ponto de entrada de cada plataforma aponta para o bloco equivalente do `AGENTS.md` gerado no projeto (a partir de `templates/agent-file-template.md`), e o mapeamento de ferramentas do Gemini continua importado pelo `GEMINI.md` a partir de um caminho que não some com a skill, sem referência quebrada.
4. Given a árvore do framework depois das remoções, When rodo a suíte de testes e a geração de `docs/pipeline-reference.md`, Then nenhum documento do repositório referencia `/aia:help` ou a skill removida sem um substituto declarado.

<!-- section: Clarifications -->
## Clarifications

Decididas (cl-1 pelo mantenedor em 2026-10-13; cl-2 e cl-3 pela evidência do reconhecimento):

- cl-1 — `/aia:help` é substituído por um comando novo, `aiadev next`, que lê o estado da feature (spec, clarificações, plano, tasks) e informa a próxima etapa; `CLAUDE.md` e `templates/roadmap-template.md` passam a apontá-lo (Story 2, cenário 5; Story 6, cenário 4).
- cl-2 — `using-ai-augmented-developer` **é** o ponto de entrada de Gemini (`GEMINI.md` a importa) e é citada como direcionadora no Codex (`docs/README.codex.md`): a remoção exige repontar cada plataforma para o bloco equivalente do `AGENTS.md` (Story 6, cenário 3), não vale só para o Claude Code.
- cl-3 — a remoção do terse-mode é imediata, com aviso de uma linha para a chave ou variável antiga (Story 6, cenário 2); precedente: remoção direta do caminho de modelo no PR #55.

<!-- section: Data touched -->
## Data touched

- Medição: relatório de `aiadev metrics --tokens` (campos por papel e subagentes não classificados); pesos de custo documentados.
- `docs/instruction-budget.json` (novo): baseline e tetos por skill e por preset; `docs/pipeline-path.yaml` (novo): arquivos lidos por etapa.
- `templates/spec-template.md` e `src/aiadev/preflight.py`: nova seção `## Assumptions`, **opcional** (validada só quando presente e fora da lista de âncoras obrigatórias `SPEC_ANCHORS`, para que as specs existentes continuem válidas); `agents/spec-document-reviewer.md`: critério de premissas.
- `src/aiadev/preflight.py` e `src/aiadev/commands/preflight.py`: saída `--json`, checagem de cobertura e bloqueio por checklist; `templates/tasks-template.md`: notação canônica de referência a cenário.
- `src/aiadev/tasks_status.py`: fechamento de task com commit e rollback.
- Comando novo `aiadev next`, sobre o estado já calculado em `src/aiadev/pipeline_state.py`; `CLAUDE.md` e `templates/roadmap-template.md` deixam de citar `/aia:help`.
- `src/aiadev/install_engine.py` e `src/aiadev/commands/sync.py`: remoção de arquivos que o framework deixou de distribuir (capacidade nova), com base em `src/aiadev/install_manifest.py`; possível mecanismo de extensão de skill por preset, a decidir no `plan`.
- `skills/implement/SKILL.md` e `skills/requesting-code-review/SKILL.md`: convenção de prefixo (`implement:`, `review:`) na descrição do dispatch, usada pela medição para classificar o papel; os reviewers de documento de `specify` e `plan` ficam fora da convenção e, portanto, não classificados.
- `.aiadev/review.yaml`: formato mantido; passa a ser o único registro de review de branch.
- `.claude/settings.json`: a chave `aiadev.terseMode` deixa de ser lida.
- `CREDITS.md`: nota dos mecanismos adaptados do spec-kit e atualização da entrada do caveman (terse-mode removido).
- Removidos: `rules/terse-mode.md`, `schemas/terse-output.schema.json`, blocos de contrato terse nos `agents/`, skills `help` e `using-ai-augmented-developer` (e seus comandos), artefato review-context.md. O `skills/using-ai-augmented-developer/references/gemini-tools.md` é realocado para um caminho fora do diretório removido e o `GEMINI.md` passa a importá-lo de lá.

<!-- section: Out-of-band effects -->
## Out-of-band effects

- Nenhum efeito externo: a medição lê só transcripts locais e não envia nada pela rede, coerente com a exclusão de envio de dados em `specs/_product/mission.md`; o papel do subagente vem de metadados, nunca do texto das mensagens (Art. VI).
- Efeito em quem já instalou: `aiadev sync` remove arquivos que o framework deixou de distribuir e muda o que o preset `lean` instala (breaking para quem dependia dos exemplos de stack no núcleo).

<!-- section: Open risks -->
## Open risks

- **Escopo grande para uma branch:** a spec reúne medição, CLI, revisão, texto e migração. O `plan` precisa fatiá-la em incrementos que possam ser mesclados e valer sozinhos, na ordem medição → fluxo → texto → migração; a medição vem antes de qualquer corte. Se o fatiamento não fechar, separar em specs.
- **Preset substitui, não estende:** o motor resolve por `(role, name)`; um preset com cópia integral da skill duplica o corpo genérico e deriva. O `plan` precisa de um mecanismo de extensão ou de uma estrutura em que o conteúdo de stack seja arquivo separado.
- **Notação de cobertura:** o template e os `tasks.md` existentes usam notações diferentes; a checagem pode reprovar features antigas. O `plan` define a notação canônica e o tratamento de features já em andamento.
- **Papel do subagente depende de convenção:** nos transcripts reais quase todo subagente tem `agentType` `general-purpose`, então o papel só é classificável pela descrição do dispatch; sem a convenção, a maior parte fica "não classificada".
- **Portabilidade:** as mesmas skills vão para Gemini, Codex, Cursor e OpenCode; compactar para modelos fortes pode reduzir a adesão em modelos menores. Mitigação: manter intactas as frases de gate e medir no Claude Code, sem prometer paridade.
- **Review combinado dilui foco:** dois checklists em um dispatch podem perder achados. Gatilho de reversão: os defeitos encontrados no review de branch por feature subirem em relação ao baseline; então volta a dois reviewers por task.
- **Benchmark curto subestima:** a reentrega de saída idêntica só aparece em sessões longas (aprendizado do PR #55); uma micro-feature de 3 tasks pode mostrar ganho de turnos e subestimar o de contexto acumulado.
- **Testes que fixam a prosa:** mover texto para arquivos de referência quebra `tests/test_implement_skill_drift.py`, `tests/test_review_redispatch_skills.py`, `tests/test_zero_findings_halt_agents.py`, `tests/test_rules_paths.py` e outros; precisam virar asserções de comportamento, não ser apagados.
- **Conflito com a spec 0029:** ambas tocam `specify`, `plan` e `tasks`, e a 0029 lista como non-goal mudar o `implement`, que esta spec reestrutura; a ordem de merge precisa ser decidida no `plan`.
- **CLI de fechamento como ponto único de falha:** se o fechamento de task falhar de forma nova, o caminho manual precisa continuar documentado.
- **Spec 0020 (token-economy-checklist):** liga o terse-mode ao checklist de economia de tokens; a remoção precisa varrer esse artefato (`tests/test_token_economy_checklist.py`).

<!-- section: Traceability -->
## Traceability

- Originating issue: pedido do mantenedor em 2026-10-13 — análise de github/spec-kit@6c62e10 e revisão das instruções para os modelos atuais, com auditoria de custo nos transcripts deste repositório; entrada R008 do roadmap.
- Related specs: `0009-token-economy-terse-mode` (recurso removido), `0010-pipeline-preflight-checks` (preflight), `0013-implement-task-status-tracking` (status por task), `0014-bmad-inspired-evolutions` (task-context), `0015-aiadev-metrics` (métricas), `0020-token-economy-checklist`, `0022-smart-mcp-proxy-token-economy` (evidência de que comprimir saída aumenta custo), `0029-artifact-only-handoffs`.
- Roadmap entry: R008.
- Constitution articles invoked: I, II, III, IV, VI, VII
