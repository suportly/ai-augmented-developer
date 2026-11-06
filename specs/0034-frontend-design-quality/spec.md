# Feature specification: frontend-design com direção de arte, auditoria anti-genérico e verificação no navegador

> Produced by `specify`. **What** and **why** only; planning and code belong in `plan.md` and `tasks.md`.

**Branch:** `feature/0034-frontend-design-quality`
**Created:** 2026-11-06
**Status:** Implemented <!-- Draft | In review | Approved | Implemented -->
**Spec ID:** 0034 <!-- auto-incrementing integer -->
**Language:** pt-BR <!-- BCP-47 tag; downstream artifacts use it. -->
**UI:** no <!-- yes if the feature adds or changes screens -->
<!-- UI: no de propósito — só muda Markdown e testes do framework; nenhuma tela é criada aqui. As capturas de tela são o que a skill passa a exigir dos projetos consumidores; este PR não precisa de captura (Art. IV: não se aplica a mudança só de texto). -->

---

<!-- section: Problem -->
## Problem

A skill `frontend-design` do preset `django-drf-react` pede um "estilo ousado" e lista o que nunca fazer, mas para aí: o agente escolhe o estilo sem justificar, não revisa o próprio resultado contra os sinais típicos de interface feita por IA e entrega sem nunca ter visto a tela renderizada. O checklist final cobre estados de carregamento, erro e vazio só como item a marcar, sem prova de que a tela os mostra. O resultado é interface genérica ou quebrada que só é percebida na revisão humana. Um carrossel público sobre "7 skills de web design" (direção de arte, vocabulário de design, componentes animados, animação, teste no navegador, transições, extração de design) mostra que esses três hábitos (decidir a direção, auditar, ver a tela) são o que separa o resultado de IA do resultado cuidado. Este trabalho traz os três hábitos para a skill com texto original, sem embutir nada de terceiros.

<!-- section: Reconnaissance -->
## Reconnaissance

- **skill frontend-design** — entry: `presets/django-drf-react/skills/frontend-design/SKILL.md` · auth: none · integration: `Checklist Before Submitting`
- **orçamento de instruções** — entry: `scripts/instruction_budget.py` · auth: none · integration: `_listing_tokens`
- **testes da skill no preset** — entry: `tests/test_frontend_design_in_preset.py` · auth: none · integration: `frontend-design`
- **recomendação de skills externas** — entry: `skills/find-skills/SKILL.md` · auth: none · integration: `npx skills find`

<!-- section: Users and stakeholders -->
## Users and stakeholders

- Desenvolvedores de projetos que instalam o preset `django-drf-react` e pedem telas ao agente.
- Revisores humanos, que hoje descobrem o genérico e o quebrado no fim.
- Mantenedor do framework, responsável pelo orçamento de instruções e pela atribuição.

<!-- section: Success criteria -->
## Success criteria

- A skill instrui, antes de qualquer código, a registrar a direção de arte em no máximo 6 linhas: estilo, tipografia, paleta e a razão de cada escolha para o propósito da tela.
- A skill instrui, antes de entregar, uma auditoria com uma lista de exatamente 8 sinais nomeados de interface genérica, e a correção de cada sinal encontrado.
- A skill instrui a abrir a tela renderizada num navegador, capturar cada estado (sucesso, vazio, erro, carregando) e só então declarar a tela pronta; sem navegador disponível, diz isso e não declara pronta.
- O checklist final deixa de aceitar "estado tratado" sem a captura correspondente.
- A `description` da skill não muda e nenhum teto de `docs/instruction-budget.json` sobe; `python3 scripts/instruction_budget.py --check` sai 0.
- Nenhum trecho, nome de regra ou lista de terceiros é copiado; `CREDITS.md` não ganha entrada nova por este trabalho, e este trabalho não piora a lacuna de atribuição herdada: nenhuma linha nova é adaptada de outro projeto, e a regularização fica nomeada como follow-up (Open risks).
- O corpo da skill tem no máximo 1.400 tokens (chars / 4), medido por teste.
- Os critérios descrevem o conteúdo da instrução: cada cenário abaixo é fixado por frase-chave no texto da skill, não por execução de agente.
- Cada regra nova é fixada por teste de frase-chave, como nas skills anteriores.

<!-- section: Non-goals -->
## Non-goals

- Embutir, copiar ou adaptar o conteúdo das sete ferramentas do carrossel (decisão do mantenedor: escopo "melhorar frontend-design").
- Criar skill nova no núcleo ou subir tetos de instrução.
- Instalar Playwright ou qualquer pacote por conta própria: a skill só usa o navegador quando o projeto ou a plataforma já o oferece.
- Mudar a skill `design` (spec 0033) ou o pipeline.
- Regularizar a licença herdada da skill (ver Open risks): follow-up nomeado "regularizar atribuição da frontend-design (Strivex)", a abrir como spec própria se o mantenedor autorizar.

<!-- section: User stories -->
## User stories

### Story 1 — Direção de arte registrada antes do código (P1)

As a desenvolvedor, I want que o agente declare e justifique estilo, tipografia e paleta antes de codar so that eu possa corrigir a direção em segundos em vez de refazer a tela.

**Acceptance scenarios** (≥ 3 per story):

1. Given um pedido de tela nova, When o agente segue a skill, Then ele escreve a direção de arte (estilo, tipografia, paleta, razão de cada uma) antes de gerar qualquer arquivo de componente.
2. Given que o projeto já tem tokens de tema, When a direção é registrada, Then ela parte dos tokens existentes e diz explicitamente onde diverge deles.
3. Given um pedido que já traz a direção (marca ou protótipo aprovado), When o agente segue a skill, Then ele usa a direção dada, não escolhe outra, e registra só o mapeamento para os tokens.
4. Given um projeto sem tokens de tema, When a direção é registrada, Then ela propõe os tokens mínimos (cores e fontes) que o código passará a usar, em vez de valores soltos.

### Story 2 — Auditoria de sinais de interface genérica (P1)

As a revisor, I want que o agente audite o próprio resultado contra sinais conhecidos de IA genérica so that o que chega à revisão já passou por um filtro.

**Acceptance scenarios** (≥ 3 per story):

1. Given uma tela pronta, When o agente roda a auditoria, Then cada sinal da lista é marcado como presente ou ausente, com o trecho ou a captura que sustenta.
2. Given um sinal presente, When a auditoria termina, Then o agente corrige o sinal e repete a checagem desse item antes de entregar.
3. Given um sinal presente que o pedido exige (ex.: a marca usa o estilo), When a auditoria termina, Then o agente o mantém e registra a razão em vez de removê-lo às cegas.

### Story 3 — Tela vista no navegador, estado por estado (P1)

As a desenvolvedor, I want que o agente abra a tela renderizada e capture cada estado so that "pronto" signifique "visto funcionando".

**Acceptance scenarios** (≥ 3 per story):

1. Given um navegador disponível (ferramenta do projeto ou da plataforma), When a tela está implementada, Then o agente a abre, captura sucesso, vazio, erro e carregando, e confere cada captura contra a direção de arte.
2. Given um estado que a tela não consegue mostrar (ex.: erro sem como forçá-lo), When o agente verifica, Then ele registra o estado como não verificado com o motivo, em vez de marcá-lo tratado.
3. Given nenhum navegador disponível, When o agente chega à verificação, Then ele diz que não pôde ver a tela, lista o que ficou sem verificação e não declara a tela pronta.
4. Given dados de uma conta real na tela aberta, When o agente captura, Then a captura usa dados de teste ou do ambiente local, nunca de produção, e a captura não é commitada.
5. Given um navegador disponível mas o servidor de desenvolvimento que não sobe, When o agente tenta verificar, Then ele reporta a falha com a saída do erro e trata a tela como não verificada.
6. Given uma tela que por desenho não tem um dos estados (ex.: sem carregamento), When o agente verifica, Then ele registra o estado como não aplicável com a razão, em vez de forçá-lo.

<!-- section: Clarifications -->
## Clarifications

Nenhum marcador: as decisões de escopo e de atribuição foram dadas pelo mantenedor.

<!-- section: Data touched -->
## Data touched

- `presets/django-drf-react/skills/frontend-design/SKILL.md` e o teste que fixa as regras.

<!-- section: Out-of-band effects -->
## Out-of-band effects

- A skill passa a pedir abrir o app local no navegador e gravar capturas; as capturas ficam fora do repositório, a menos que o usuário as peça.

<!-- section: Open risks -->
## Open risks

- A skill herda `license: Adapted from Strivex — Complete terms in LICENSE.txt`, mas a pasta da skill não tem `LICENSE.txt` e o `CREDITS.md` não tem entrada para esse projeto (Art. VII); fora do escopo por decisão do mantenedor ("sem atribuição nova"); follow-up nomeado: regularizar atribuição da frontend-design (Strivex), com `LICENSE.txt` e entrada no `CREDITS.md`.
- O corpo da skill cresce; o orçamento mede só a listagem (nome e descrição), então o custo extra é carregado sob demanda, limitado pelo teto de 1.400 tokens do corpo.
- Agentes sem navegador sempre cairão no caminho "não pude ver a tela"; aceito.

## Assumptions

- O corpo da skill não entra no teto do percurso do pipeline, só a listagem entra. [impact: low]
- Um navegador "disponível" é o que a plataforma ou o projeto já expõe (por exemplo, um servidor MCP de navegador ou o CLI do Playwright já instalado). [impact: low]
- A lista de 8 sinais é escrita do zero na fase de plano, a partir da lista "What NEVER to Do" da própria skill (reformulada, sem copiar a redação) e de práticas gerais de design; seu conteúdo não é decidido nesta spec. [impact: low]

<!-- section: Traceability -->
## Traceability

- Originating issue: pedido do mantenedor em 2026-11-06, a partir do carrossel público "7 skills de web design" (instagram.com/p/DfKdxCdkZ_q)
- Related specs: 0032-find-skills, 0033-design-step
- Constitution articles invoked: I, II, III, IV, VI, VII
