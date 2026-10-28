# Feature specification: find-skills — descobrir skills existentes antes de construir

> Produced by `specify`. **What** and **why** only; planning and code belong in `plan.md` and `tasks.md`.

**Branch:** `feature/0032-find-skills`
**Created:** 2026-10-28
**Status:** Implemented <!-- Draft | In review | Approved | Implemented -->
**Spec ID:** 0032 <!-- auto-incrementing integer -->
**Language:** pt-BR <!-- BCP-47 tag; downstream artifacts use it. -->

---

<!-- section: Problem -->
## Problem

Quando o usuário pede algo especializado (testes e2e, vídeo, deploy, acessibilidade), o agente constrói do zero mesmo que exista uma skill pública pronta e mantida, e o usuário não sabe que o ecossistema de skills existe. O aiadev instala o pipeline e os presets, mas nada ensina o agente a procurar uma skill existente, a julgar se ela é confiável e a deixar a instalação na mão do usuário. Instalar uma skill é instalar instrução que o agente executa; sem um critério de verificação e sem confirmação, o caminho mais curto (instalar direto) é também o mais arriscado.

<!-- section: Reconnaissance -->
## Reconnaissance

- **instalação de skills** — entry: `src/aiadev/install_engine.py` · auth: none · integration: `skills/` (todo diretório de `skills/` é instalado em todo preset; não há lista de skills padrão a editar)
- **orçamento de instrução** — entry: `scripts/instruction_budget.py` · auth: none · integration: `docs/instruction-budget.json` (a descrição de cada skill instalada conta no sempre-carregado; o teto só desce, e subir exige razão registrada)
- **atribuição** — entry: `CREDITS.md` · auth: none · integration: `constitution.md` (Art. VII, não renunciável: material adaptado exige entrada em CREDITS.md com repositório, material e licença)
- **precedente de skill fora do caminho** — entry: `skills/task-context/SKILL.md` · auth: none · integration: `docs/pipeline-path.yaml` (skills lidas só sob demanda ficam fora do percurso)

<!-- section: Users and stakeholders -->
## Users and stakeholders

- Quem instala o aiadev em qualquer preset e pede ao agente algo que pode já existir como skill.
- Mantenedor do aiadev: carrega o custo fixo de instrução e a responsabilidade pelo que o framework recomenda.

<!-- section: Success criteria -->
## Success criteria

- `aiadev install` com qualquer preset instala `find-skills`; `aiadev sync` a mantém.
- A skill nunca instala nada: apresenta a recomendação e o comando, e quem instala é o usuário, sem flag de confirmação automática.
- O corpo da skill não cita fornecedor nem empresa, não traz exemplo de stack, e a descrição tem no máximo 30 tokens medidos por `scripts/instruction_budget.py`.
- O teto de `skills` de cada preset medido sobe exatamente o custo da listagem (nome e descrição) e o teto de `total` sobe só o que a medição exige (Story 3, cenário 2), com razão registrada no `docs/instruction-budget.json`; o percurso do pipeline não muda.
- `CREDITS.md` registra a origem do material, com repositório, o que foi adaptado e a licença.

<!-- section: Non-goals -->
## Non-goals

- Um comando `aiadev skills find` ou um catálogo próprio (continua sendo a entrada R013 do roadmap).
- Instalar skills por conta própria, em qualquer modo.
- Avaliar ou pontuar skills com código; a verificação é um critério que o agente aplica e mostra.
- Entrar no percurso `specify -> finish`.

<!-- section: User stories -->
## User stories

### Story 1 — Descobrir antes de construir (P1)

Como usuário do aiadev, quero que o agente procure uma skill existente quando peço uma capacidade especializada, para não reconstruir o que já existe.

**Acceptance scenarios** (≥ 3 per story):

1. Given um projeto com o aiadev instalado em qualquer preset, When o usuário pergunta "existe uma skill para X?", Then o agente aplica `find-skills` e apresenta nome, o que faz, fonte e o comando de instalação.
2. Given que a busca não encontra nada relevante, When o agente responde, Then diz isso e se oferece para fazer a tarefa direto, sem inventar uma skill.
3. Given que a busca retorna candidatos, When o agente os apresenta, Then cada um traz os dados de verificação (popularidade, reputação da fonte, atividade do repositório) e uma ressalva explícita quando algum dado não pôde ser confirmado.

### Story 2 — Instalar só com confirmação (P1)

Como usuário, quero decidir o que entra no meu projeto, porque uma skill é instrução que o agente passa a seguir.

**Acceptance scenarios**:

1. Given uma skill recomendada, When o usuário ainda não confirmou, Then o agente não executa nenhum comando de instalação.
2. Given que o usuário confirma, Then o agente mostra o comando de instalação, sem flag que pule a confirmação do instalador, e é o usuário quem o executa.
3. Given uma skill candidata, When o usuário vai instalar, Then o agente lê o `SKILL.md` dela e resume o que ela manda executar, sinalizando comandos de rede, escrita fora do projeto ou instalação de pacotes.

### Story 3 — Presente em todo preset sem estourar o orçamento (P1)

Como mantenedor, quero a skill em toda instalação e o custo fixo medido e justificado.

**Acceptance scenarios**:

1. Given cada preset de `presets/catalog.json` (hoje cinco), When cada um é instalado em diretório temporário, Then `find-skills` existe em todos.
2. Given a medição de `scripts/instruction_budget.py`, When roda depois da mudança, Then o aumento do sempre-carregado de cada preset é igual ao custo da descrição, e o novo teto traz razão registrada.
3. Given `docs/pipeline-path.yaml`, When a mudança termina, Then o total do percurso é idêntico ao anterior.

### Story 4 — Atribuição e privacidade da busca (P2)

Como mantenedor, quero cumprir o Art. VII e não vazar contexto do projeto na busca.

**Acceptance scenarios**:

1. Given a skill pronta, When `CREDITS.md` é lido, Then há entrada com repositório de origem, o que foi adaptado e a licença (MIT), sem que o nome apareça no texto da skill.
2. Given que a busca consulta um serviço externo, When o agente monta a consulta, Then ela contém só termos genéricos do domínio, nunca nomes de cliente, caminhos, segredos ou trechos de código do projeto.
3. Given que o agente precisa de rede para buscar, When a rede ou o CLI não estão disponíveis, Then ele diz que não pôde buscar e segue sem a skill.

<!-- section: Clarifications -->
## Clarifications

Nenhum marcador pendente.

## Assumptions

- O CLI de busca e instalação (`npx skills`) já é o de uso corrente do usuário e do ecossistema; a skill o referencia como ferramenta externa, sem embuti-lo. [impact: low]
- Basta `skills/find-skills/`: o instalador copia todo diretório de `skills/`, então nenhuma lista de padrão precisa mudar. [impact: low]
- Não há slash command `/aia:find-skills`; a skill dispara pela descrição. [impact: low]
- Os limiares de verificação são: preferir 1.000 instalações ou mais, desconfiar de menos de 100, e tratar com ceticismo repositório com menos de 100 estrelas; ajustá-los é editar uma linha da skill. [impact: low]
- A verificação dos cenários de comportamento (Stories 1 e 2) é por inspeção do `SKILL.md`, que deve conter cada regra de forma testável, e por um teste que fixa as frases-chave. [impact: low]

<!-- section: Data touched -->
## Data touched

- Consulta de busca enviada a um serviço externo (termos genéricos apenas).
- Arquivos novos: `skills/find-skills/SKILL.md`, entrada em `CREDITS.md`, razão no `docs/instruction-budget.json`.

<!-- section: Out-of-band effects -->
## Out-of-band effects

- Rede: a busca e a leitura do repositório candidato saem da máquina do usuário; nada disso roda sem o agente ter motivo.
- Instalação de skill de terceiro: só por ação do usuário, fora da skill.

<!-- section: Open risks -->
## Open risks

- Skill maliciosa recomendada: mitigada por verificação, leitura do `SKILL.md` e confirmação humana, mas não eliminada.
- Teto de instrução sobe, contrariando a regra de nunca subir: autorizado pelo usuário em 2026-10-28, com a menor descrição possível e razão registrada.
- Deriva do ecossistema (CLI muda de comandos): a skill cita só `find` e `add`, os mais estáveis.

<!-- section: Traceability -->
## Traceability

- Originating issue: pedido do mantenedor em 2026-10-28 (instalar para todo usuário do aiadev); sem entrada `R<NNN>` no roadmap
- Related specs: 0030-lean-pipeline (orçamento de instrução), 0031-context-hygiene; R013 (catálogo remoto) continua separada
- Constitution articles invoked: I, III, IV, VI, VII
