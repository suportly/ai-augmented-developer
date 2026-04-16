# Research notes — aiadev como ferramenta de LLM

> Investigações que sustentam decisões de [plan.md](./plan.md).
> Consolidado, não diário; só o que importa para revisores.

## R1 — SDK MCP em Python

**Pergunta:** existe SDK Python oficial para implementar servidor MCP em modo stdio?
Vale como dependência?

**Achado:** sim — pacote `mcp` no PyPI (Anthropic), baseado em JSON-RPC sobre stdio.
Expõe primitivos `prompts/list`, `prompts/get`, `tools/list`, `tools/call`, `resources/list`, `resources/read`.

**Decisão (ADR 2 + 5):** dependência opcional via `[project.optional-dependencies].mcp = ["mcp>=1.0"]`.
Servidor consome o SDK; lib Python (`aiadev.tools`) **não**, ficando free de extras.

**Trade-off considerado:** implementar JSON-RPC à mão (deps zero) — rejeitado por
reinventar a roda e quebrar Article III (sem segundo caller hoje que justifique).

## R2 — Primitivo MCP correto para skill-as-prompt-loader

**Pergunta:** servir o conteúdo de SKILL.md como `prompts` ou como `tools`?

**Achado:** o spec MCP define `prompts` exatamente como "templates de prompt parametrizáveis
que o cliente carrega para injetar no contexto do LLM". Match semântico exato com nosso caso.
`tools` é para "ações com efeito colateral que retornam resultado estruturado" — encaixa pior,
porque nosso handler não tem efeito colateral além do log de telemetria.

**Decisão (ADR 5):** primitivo principal = `prompts/get`. `tools/call` exposto em paralelo
porque alguns clientes MCP ainda não consomem `prompts` (cobertura defensiva).

**Trade-off:** dois caminhos a documentar/manter; mitigado por handler único que retorna
o mesmo `ToolPayload` para os dois.

## R3 — Identificadores `cl-N` estáveis

**Pergunta:** como gerar ids estáveis para marcadores sem introduzir banco de estado?

**Opções avaliadas:**

- (a) **Inteiro monotônico por spec** (`cl-1`, `cl-2`, …) — simples, legível, requer
  contagem ao gerar/inserir um novo marcador.
- (b) **UUID-7 por marcador** — globalmente único, mas ilegível e overkill para um
  ambiente de spec único por branch.
- (c) **Hash do conteúdo** — id muda quando texto edita, viola "estável".

**Decisão (ADR 4):** (a). O `specify` enumera marcadores existentes via grep
e atribui o próximo inteiro disponível. `clarify` aceita `cl-N` como chave.

**Trade-off:** edição manual que insira marcador no meio precisa renumerar — mas a
edição manual de marcador já é exceção (o fluxo idiomático passa pelos skills).
Documentar no `clarify/SKILL.md`.

## R4 — Validação de `workspace_path`

**Pergunta:** quais classes de path traversal precisam ser barradas?

**Achado:** três vetores conhecidos:

1. `..` literal (`/work/../etc/passwd`).
2. Symlinks que escapam (`/work/escape -> /etc/`).
3. Paths absolutos passados como `target_path` que ignoram `workspace_path`.

**Decisão:** `aiadev._tooling.workspace.validate(path)` faz:
1. `Path(path).expanduser().resolve(strict=True)` — força existência e resolve symlinks.
2. Confere se é diretório.
3. Para cada `target_path` derivado, exige `Path(target).resolve().is_relative_to(workspace_resolved)`
   (Python 3.9+).

Teste `tests/test_workspace.py` cobre os três vetores.

## R5 — Como o servidor encontra `skills/` e `templates/`

**Pergunta:** o servidor MCP é lançado pelo cliente com `cwd` imprevisível.
Como localiza os assets?

**Achado:** `aiadev.paths.find_framework_root()` já implementa a resolução em 4 camadas
(`AIADEV_ROOT`, walk up, `git toplevel`, package install). Servidor reaproveita.
Quando rodando como wheel instalado (`pip install aiadev`), o fallback aponta para
`src/aiadev/_assets/` que é populado pelo `scripts/sync_assets.py` antes do build.

**Decisão:** sem mudança em `paths.py`. `mcp_server/__main__.py` chama
`find_framework_root()` no startup; se falhar, encerra com exit code != 0 e mensagem
acionável.

## R6 — Determinismo do fake LLM em testes E2E

**Pergunta:** como testar "caller LLM segue o prompt e produz artefato correto" sem
rodar LLM real?

**Achado:** o prompt do `specify` instrui passos discretos: ler template, computar
seções, preencher. Um fake que apenas (a) lê `target_path` do payload, (b) copia
`templates/spec-template.md`, (c) substitui `{{FEATURE_NAME}}`, `{{BRANCH}}`,
`{{DATE}}`, `{{SPEC_ID}}` com valores derivados do payload, (d) acrescenta
um marcador `[NEEDS CLARIFICATION:cl-1 ...]` mock — produz um artefato que
satisfaz o template (`test_e2e_specify` valida só estrutura, não conteúdo qualitativo).

**Decisão:** `tests/_fakes/llm.py` implementa o subset acima. Documenta-se que
o fake **não** valida qualidade do conteúdo (problema/users/acceptance scenarios)
porque isso exige inteligência real. Cobertura de qualidade fica para o reviewer
humano nos testes manuais documentados na Phase 5.

**Trade-off:** o fake passa testes que um LLM mau-comportado falharia — risco
aceito porque a alternativa (LLM real em CI) custa caro e é flaky.

## R7 — Coexistência com `aiadev.mcp` existente

**Pergunta:** renomear `src/aiadev/mcp.py` (loader de `mcps.yaml`) para liberar o
namespace `aiadev.mcp`?

**Achado:** `mcp.py` é importado por `framework_artifacts.py` e por `tests/test_mcp.py`.
Renomear é mecânico mas afeta CHANGELOG (mudança visível para quem importa).

**Decisão (ADR 1):** **não renomear**. Novo módulo é `aiadev.mcp_server`. Custo
é nome ligeiramente mais longo; benefício é zero risco de regressão num módulo
crítico para a fase de install.
