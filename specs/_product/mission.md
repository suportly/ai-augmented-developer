# Mission: AI-Augmented Developer

**Language:** pt-BR <!-- fonte: convenção das specs recentes, specs/0023-product-context/spec.md:9; nome do produto: README.md:1 -->

---

<!-- section: Why -->
## Why

O AI-Augmented Developer existe para dar aos agentes de código um fluxo completo de desenvolvimento de software, construído sobre skills componíveis e instruções que garantem que o agente as use (README.md:3). Em vez de ir direto ao código, o agente extrai uma spec da conversa, monta um plano com TDD, YAGNI e DRY e implementa task a task com revisão de conformidade à spec e de qualidade de código (README.md:7-13). As skills são fluxos obrigatórios, não sugestões (README.md:298), regidos por uma constituição de sete artigos: spec-first, test-first, simplicidade, evidência, provider pattern, privacidade e atribuição (CLAUDE.md:32).

<!-- section: For whom -->
## For whom

- Desenvolvedores que usam agentes de código em Claude Code, Cursor, Codex, OpenCode ou Gemini CLI (README.md:3, README.md:36-37; público "Developers" em pyproject.toml:16).
- Tech leads que acompanham a saúde das features pelo rastro de auditoria (`aiadev metrics`, "the indicators a tech lead actually needs", README.md:164-165).
- Agentes LLM que invocam as skills do pipeline programaticamente, pela biblioteca Python ou pelo servidor MCP (README.md:234, README.md:276).
- Autores de presets de terceiros, distribuídos como extensões (README.md:88-90).
- Público principal: tech leads e times que adotam agentes de código; o desenvolvedor individual é público secundário. Priorização decidida pelo mantenedor em 2026-09-25 (inferência, não escrita no repositório), apoiada na trilha de auditoria e em `aiadev metrics` (README.md:160-187) e no revisor não-autor exigido pela constituição (constitution.md:144).

<!-- section: Problem -->
## Problem

Agentes de código vão direto ao código: sem spec aprovada, sem plano e sem teste falhando antes, o que foi pedido e o que foi construído divergem, e o erro só aparece tarde, quando corrigir é caro (constitution.md:15, racional do Artigo I). A divergência entre arquivos de agente de plataformas diferentes é um sintoma secundário do mesmo problema (README.md:151-153). Enunciado aprovado pelo mantenedor em 2026-09-25.

<!-- section: Out of scope -->
## Out of scope

- Registro central, assinatura ou auto-update de extensões: extensões são só URLs git (README.md:83-84).
- Envio de dados pela rede nos comandos de auditoria: `aiadev metrics` e `aiadev learn` são locais e read-only (README.md:183, README.md:207).
- Aplicar automaticamente mudanças de guidance: as propostas do `aiadev learn` vão para revisão humana (README.md:208-210).
- Orientação específica de stack no núcleo do framework: ela pertence ao preset (CLAUDE.md:3, CLAUDE.md:55, CLAUDE.md:80).
- Ser um serviço hospedado: o aiadev roda localmente, no repositório do projeto. Exclusão decidida pelo mantenedor em 2026-09-25.
- Executar trabalho sem um agente de código por trás: o aiadev é processo e ferramentas, não um agente. Exclusão decidida pelo mantenedor em 2026-09-25.
