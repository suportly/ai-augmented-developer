# Implementation plan: frontend-design com direção de arte, auditoria anti-genérico e verificação no navegador

> Produced by the `plan` skill: **how** the spec is realized. Do not rewrite `spec.md` here.

**Branch:** `feature/0034-frontend-design-quality`
**Date:** 2026-11-06
**Spec:** [spec.md](./spec.md)
**Plan version:** 1
**Language:** pt-BR

---

## Summary

Uma mudança de texto em um único arquivo, `presets/django-drf-react/skills/frontend-design/SKILL.md`, mais o teste que a fixa. A skill ganha uma seção curta de fluxo com três passos, na ordem em que o agente os executa: (1) registrar a direção de arte (≤ 6 linhas) antes de gerar componentes; (2) verificar a tela renderizada no navegador, capturando os quatro estados; (3) auditar o resultado contra 8 sinais nomeados de interface genérica e corrigir cada um. O checklist final passa a exigir a captura de cada estado, em vez de "estado tratado". A `description` não muda, então nenhum teto do orçamento sobe; o corpo cresce de 1.061 para no máximo 1.400 tokens, com teto medido por teste. Nada de terceiros é copiado.

## Technical context

| Field | Value |
|---|---|
| Active preset | django-drf-react (a skill vive no preset, não no núcleo) |
| Language / runtime | Markdown + Python 3.11 (pytest) |
| Primary dependencies | nenhuma; o navegador é o que a plataforma ou o projeto já oferece |
| Storage | nenhum |
| Testing framework | pytest (`.venv/bin/python -m pytest`) |
| Target platform(s) | todas as que recebem o preset; a verificação em navegador depende de a plataforma expor um |
| Performance budget | corpo ≤ 1.400 tokens (chars / 4); `description` inalterada |
| Security considerations | capturas só com dados de teste ou locais e nunca commitadas (Art. VI) |

Divergência com `tech-stack.md`/auto-stack: nenhuma relevante.

## Constitution check

| Article | Applies? | Status | Evidence |
|---|---|---|---|
| I. Spec-first | Yes | PASS | `spec.md` 0034 aprovada por revisor em duas rodadas |
| II. Test-first | Yes | PASS | compromisso: RED observado antes de editar o `SKILL.md` e registrado no PR (`tests/test_frontend_design_quality.py`) |
| III. Simplicity | Yes | PASS | um arquivo de skill, sem script nem skill nova; descrição e orçamento intocados |
| IV. Evidence over claims | Yes | PASS | PR cita o teste, a medição do corpo e `instruction_budget.py --check`; sem captura de tela por ser mudança só de texto |
| V. Provider pattern | No | N/A | nenhum provider adicionado |
| VI. Privacy by design | Yes | PASS | regra fixada por teste: capturas com dados de teste ou locais, não commitadas |
| VII. Attribution | Yes | PASS | nenhuma linha nova é adaptada de outro projeto; os 8 sinais são reformulados a partir de princípios gerais de design, não do texto herdado da lista "What NEVER to Do"; a lacuna herdada (Strivex) não piora e o follow-up está nomeado na spec |
| Preset-specific articles | No | N/A | só se aplicam a código Django/React; esta mudança é texto da skill |

## Architecture decisions

- **Decisão:** a seção nova entra na própria `SKILL.md`, sem arquivo de referência. **Rationale:** são três passos curtos que todo uso da skill percorre, então carregá-los junto é mais barato que um segundo arquivo lido sob demanda. **Trade-off:** o corpo cresce; o teto de 1.400 tokens limita.
- **Decisão:** a ordem é direção → implementação → verificação no navegador → auditoria. **Rationale:** a auditoria precisa da tela renderizada como prova (Story 2 cenário 1), então vem depois da captura. **Trade-off:** o agente só audita depois de gastar a verificação; aceito.
- **Decisão:** os 8 sinais são escritos do zero, reformulando a lista "What NEVER to Do" e práticas gerais de design, sem copiar a redação de nenhum projeto. **Rationale:** spec e decisão do mantenedor ("sem atribuição nova"). **Trade-off:** menos completa que a lista de uma ferramenta dedicada; as ferramentas do carrossel seguem como sugestão do `find-skills`.
- **Decisão:** sem navegador disponível, a skill manda dizer que não viu a tela e não declarar pronta, e não instala nada. **Rationale:** instalar pacote sozinho foge do escopo e do cuidado do `find-skills`. **Trade-off:** parte dos agentes cairá sempre nesse caminho.
- **Decisão:** substituir os dois blocos de código de exemplo menos úteis só se o corpo passar de 1.400 tokens. **Rationale:** o teto é critério da spec; a poda é o último recurso. **Trade-off:** nenhum se couber.

## Project structure changes

```text
presets/django-drf-react/skills/frontend-design/SKILL.md   (modified: seção de fluxo, checklist com captura)
tests/test_frontend_design_quality.py                      (new: frases-chave, 8 sinais, teto de corpo, description inalterada)
CHANGELOG.md                                               (modified: [Unreleased])
```

## Phase breakdown

### Phase 1 — Skill e teste

- Teste que falha: lê o `SKILL.md` e fixa por frase-chave a direção de arte (≤ 6 linhas, parte dos tokens do projeto, usa a direção dada, propõe tokens mínimos sem tema), a verificação (quatro estados, estado não forçável registrado como não verificado, estado inexistente como não aplicável, servidor que não sobe, sem navegador não declara pronta, dados de teste, captura não commitada), a auditoria (exatamente 8 sinais numerados; cada sinal marcado presente ou ausente com o trecho ou a captura que o sustenta; sinal corrigido é checado de novo antes de entregar; sinal exigido pelo pedido é mantido com razão), cada captura conferida contra a direção de arte, o checklist final com captura e o teto de 1.400 tokens para o corpo; e fixa a `description` atual como string exata no próprio teste (sem depender de git ou do ref `main`).
- Implementar o mínimo na skill. Medir o corpo; podar só se passar do teto.

### Phase 2 — Orçamento e changelog

- Rodar `python3 scripts/instruction_budget.py --check` (deve sair 0 sem editar `docs/instruction-budget.json`) e a suíte completa.
- Registrar em `CHANGELOG.md` [Unreleased]: a mudança da skill, que o orçamento não mudou e a lacuna herdada de atribuição como limitação conhecida.

## Risks and mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Corpo estoura 1.400 tokens | Med | Low | teste mede; poda dos exemplos de código como último recurso |
| Redação dos 8 sinais próxima demais à de ferramenta de terceiros | Low | Med | escrever a partir da lista da própria skill e de princípios gerais; revisão confere |
| Orçamento de listagem muda por acidente | Low | Med | teste fixa a `description` como string exata; `--check` na Phase 2 |
| Agente sem navegador ignora o aviso | Med | Low | a instrução manda listar o que ficou sem verificação e não declarar pronta |

## Complexity tracking

Nenhuma linha `FAIL`; vazio justificado.

## Hand-off to `tasks`

Next skill: `tasks`. Constitution Check completo, Complexity tracking justificado vazio, estrutura conferida contra o repositório.
