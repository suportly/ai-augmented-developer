# AI-Augmented Developer: o framework que transforma seu agente de IA num engenheiro disciplinado

> Em 48 horas, do v0.3 ao v0.11 — nove releases, cinco plataformas, distribuição no PyPI, sistema de extensões e suporte a MCP.

## O problema que ninguém quer admitir

Quem desenvolve com IA conhece o ciclo: você descreve uma feature, o agente sai escrevendo código antes de entender o problema, ignora os testes, inventa contexto, e três horas depois você está revisando um diff de 800 linhas para descobrir que metade não faz o que você pediu.

A culpa não é (só) do modelo. É da ausência de processo. Engenheiros sêniores não saem programando — eles especificam, planejam, testam, revisam. Faltava ao agente esse mesmo método.

É exatamente isso que o **AI-Augmented Developer** entrega.

## O que é

AI-Augmented Developer (`aiadev`) é um framework de workflow completo para agentes de codificação. Ele instala um conjunto de **skills componíveis** e instruções iniciais que garantem que o agente as use **automaticamente** — sem você precisar lembrar de nada.

A filosofia é direta:

- **Spec-first**: nada de código sem especificação aprovada.
- **Test-first**: RED-GREEN-REFACTOR como contrato, não sugestão.
- **Evidência sobre afirmação**: verificar antes de declarar sucesso.
- **Simplicidade como meta primária**: YAGNI e DRY são leis, não dicas.

O fluxo padrão é uma esteira de oito etapas:

```text
specify → clarify → plan → tasks → implement
                                       │
                          test-driven-development (por tarefa)
                          systematic-debugging (em falhas)
                          checklist (segurança, perf, a11y, i18n…)
                                       ↓
                               analyze → requesting-code-review → finishing-a-branch
```

Cada etapa é uma skill que dispara sozinha quando faz sentido. O agente não pula etapas. Ele não inventa contexto. Ele te mostra a spec antes de escrever o primeiro teste.

## A constituição: sete artigos não-negociáveis

O coração do framework é a [`constitution.md`](../../constitution.md), com sete princípios que toda decisão técnica precisa respeitar:

1. **Spec-first** — sem spec aprovada, sem código.
2. **Test-first** — teste falhando antes da implementação.
3. **Simplicidade** — a solução mais simples que funciona.
4. **Evidência sobre afirmação** — rode, prove, mostre.
5. **Provider pattern** — dependências externas atrás de interfaces.
6. **Privacy by design** — dados sensíveis nunca vazam para LLMs.
7. **Atribuição** — créditos para todo trabalho derivado.

Todo plano gerado pela skill `plan` carrega um **Constitution Check**. Quebrou um artigo? Vai para a tabela de Complexity Tracking com justificativa. Sem essa disciplina, o framework recusa avançar.

## A evolução recente: dois dias que mudaram o jogo

Entre **14 e 15 de abril de 2026**, o projeto saiu da v0.3 e chegou na v0.11. Cada release resolveu uma fricção real de quem usa o framework no dia a dia.

### v0.3 — `aiadev install` interativo

A CLI Python finalmente assume o lugar dos scripts manuais. Um único comando renderiza um preset (variáveis substituídas, arquivos posicionados) dentro do projeto, com modo `--dry-run`, `--uninstall` e detecção de drift contra edições à mão.

### v0.4 — Cursor

Primeiro handler de plataforma além do Claude Code. Round-trip end-to-end completo, com docs.

### v0.5 — Codex, OpenCode, Gemini

Em uma única release, mais três plataformas. Agora as cinco principais ferramentas de IA para desenvolvimento estão cobertas: **Claude Code, Cursor, Codex, OpenCode e Gemini CLI**. Cada handler é um módulo isolado de ~30 linhas, com 100% de cobertura de testes.

### v0.6 — Escopo de usuário

`--scope user` instala as skills uma vez por máquina, sob `~/.<plataforma>/skills/`. Todo projeto na sua estação passa a herdar o mesmo catálogo, sem repetir setup. Arquivos com variáveis específicas do projeto (CLAUDE.md, constitution.md) seguem locais.

### v0.7 — PyPI

`pip install aiadev` passa a funcionar. O wheel embute `constitution.md`, `templates/`, `schemas/`, `skills/`, `presets/` e `agents/` — não precisa mais clonar o repo. Publish via OIDC trusted publishing, sem tokens guardados.

### v0.8 — Sistema de extensões

`aiadev extension add <git-url>` permite distribuir presets de terceiros. Catálogos comunitários, presets corporativos privados, presets experimentais — qualquer um pode publicar. Built-ins ganham em colisão de nome, com aviso amarelo quando uma extensão é eclipsada.

### v0.9 — Full install + `aiadev sync`

Talvez a maior virada. O `install` agora equipa o projeto com **toda a esteira** de uma vez: 14 slash commands, 3 agentes, 5 regras de codificação e o catálogo completo de skills genéricas. O novo `aiadev sync` puxa atualizações do framework para projetos já instalados e regenera um bloco `<!-- aiadev:auto-stack -->` dentro do `CLAUDE.md` a partir da introspecção do projeto (package.json, pyproject.toml, Cargo.toml, go.mod, pubspec.yaml, docker-compose, Makefile, workflows do GitHub).

### v0.10 — Namespacing e specs sequenciais

Slash commands ganham namespace: `/aia:specify`, `/aia:plan`, `/aia:implement`. Specs deixam o esquema `feature-<slug>/` e adotam IDs sequenciais zero-padded: `specs/0001-<slug>/`, `0002-…`. Plus: `aiadev init --language pt-BR` faz toda a esteira (clarify, plan, tasks, implement, analyze, checklist) responder no idioma escolhido.

### v0.11 — MCP em todas as plataformas

O **Model Context Protocol** entra como cidadão de primeira classe. Você declara servidores uma vez em `mcps.yaml` e o `aiadev install` traduz para o formato nativo de cada plataforma:

- Claude Code → `.mcp.json`
- Cursor → `.cursor/mcp.json`
- Gemini CLI → `.gemini/settings.json`
- Codex → `.codex/config.toml`
- OpenCode → `opencode.json`

Quarenta testes cobrem o loader, a tradução por plataforma e o pickup em presets. MCP deixa de ser um setup repetitivo e vira um detalhe de configuração.

## Por que isso importa

Olhe a curva: nove releases em 48 horas, cada uma resolvendo uma dor concreta — sem regredir, sem quebrar usuários existentes, com testes e docs em todas. Isso é literalmente o framework se aplicando a si mesmo. As specs vivem em [`specs/`](../../specs/), os planos foram gerados pela skill `plan`, os commits seguem o padrão `feat(<área>): T<N> <título>` da skill `tasks`.

Para quem desenvolve com IA, o `aiadev` resolve quatro problemas simultaneamente:

| Dor | Resposta do framework |
|---|---|
| Agente codifica sem entender | Skill `specify` força a especificação primeiro |
| Código sem teste / teste depois | Skill `test-driven-development` enforca RED-GREEN-REFACTOR |
| Decisões esquecidas / drift | Skill `analyze` reporta divergência entre spec/plan/tasks/código |
| Setup manual em cada projeto | `aiadev install` + `--scope user` + extensions cobrem tudo |

E o melhor: você não precisa lembrar de invocar nada. As skills disparam sozinhas no momento certo, em todas as cinco plataformas suportadas, com uma única declaração de servidores MCP, com PRs limpos no fim.

## Como começar

```bash
# 1. Instale a CLI
pip install aiadev

# 2. Entre num projeto e instale o preset que cabe nele
cd seu-projeto
aiadev install --preset lean              # pipeline genérico
aiadev install --preset django-drf-react  # web full-stack
aiadev install --preset mobile-ops        # Cloud Run + Expo

# 3. Escolha a plataforma (default: claude-code)
aiadev install --preset lean --platform cursor

# 4. Em PT-BR? Inicialize com a flag de idioma
aiadev init --language pt-BR

# 5. Verifique
aiadev doctor
```

Inicie uma nova sessão, peça uma feature em linguagem natural, e veja o agente puxar a `specify` antes de qualquer linha de código.

## Quem deveria usar

- **Devs solo** que querem produtividade sem perder qualidade.
- **Times** que precisam de processo consistente entre múltiplos contribuidores e agentes.
- **Empresas** que precisam padronizar o uso de IA sem virar refém de uma única ferramenta.
- **Quem mantém presets internos** — o sistema de extensões resolve distribuição corporativa.

## O que vem a seguir

A esteira está completa, as cinco plataformas estão wired, MCP está integrado. Os próximos passos naturais são presets temáticos (data, ML, infra), telemetria opt-in para entender quais skills geram mais valor, e ferramental para validar specs por agentes especializados.

Mas o ponto mais importante já foi atingido: o framework é **completo** o suficiente para uso diário, **disciplinado** o suficiente para projetos sérios, e **aberto** o suficiente para a comunidade evoluir.

---

**Repositório:** <https://github.com/suportly/ai-augmented-developer>
**Versão atual:** 0.11.0 (15/abr/2026)
**Licença:** MIT
**Instalar:** `pip install aiadev`
