# Tech stack: AI-Augmented Developer

**Language:** pt-BR <!-- fonte: convenção das specs recentes, specs/0023-product-context/spec.md:9; nome do produto: README.md:1 -->

---

<!-- section: Languages -->
## Languages

Não há `AGENTS.md` com bloco `aiadev:auto-stack` na raiz; a lista abaixo vem dos arquivos que a detecção lê. A detecção (`project_introspect.introspect()`) só olha a raiz e acha apenas Python; as entradas TypeScript/Node vêm dos manifestos de `vscode-extension/` e `packages/smart-mcp-proxy/`.

- Python >=3.11 — pyproject.toml:11 (CI em 3.11 e 3.12, .github/workflows/validate.yml:18).
- TypeScript ^5 — vscode-extension/package.json:114 (^5.3.3) e vscode-extension/tsconfig.json; packages/smart-mcp-proxy/package.json:51 (^5.7.2) e packages/smart-mcp-proxy/tsconfig.json. A extensão VS Code e o smart-mcp-proxy fazem parte da stack adotada: os dois saem deste repositório com release próprio (.github/workflows/vscode-extension.yml, .github/workflows/smart-mcp-proxy.yml); a frase "Python-only tooling" do CLAUDE.md estava desatualizada e foi corrigida (decisão do mantenedor, 2026-09-25).
- Node.js >=18 (runtime do smart-mcp-proxy) — packages/smart-mcp-proxy/package.json:22; CI em Node 20 (.github/workflows/vscode-extension.yml:27) e Node 22 (.github/workflows/smart-mcp-proxy.yml:38).
- Markdown (skills, templates, specs) — CLAUDE.md:65.

<!-- section: Frameworks -->
## Frameworks

- Click >=8.1 (CLI `aiadev`) — pyproject.toml:25, pyproject.toml:43.
- Rich >=13.7, PyYAML >=6.0, jsonschema >=4.20 — pyproject.toml:26-28.
- MCP Python SDK `mcp>=1.0,<2.0` (extra opcional `aiadev[mcp]`) — pyproject.toml:32-34.
- pytest >=8.0, pytest-cov, pytest-asyncio — pyproject.toml:36-38.
- setuptools >=68 + setuptools-scm (build) — pyproject.toml:2.
- API de extensões do VS Code ^1.85.0, empacotada com esbuild ^0.20.0, testada com Mocha + Chai — vscode-extension/package.json:31, :110, :112, :109.
- `@modelcontextprotocol/sdk` ^1.12.0 e zod ^3.24.1 (smart-mcp-proxy) — packages/smart-mcp-proxy/package.json:46-47; testes com `node --test` — packages/smart-mcp-proxy/package.json:28.
- GitHub Actions (CI e publicação no PyPI, npm e VS Code Marketplace) — .github/workflows/validate.yml, .github/workflows/publish.yml, .github/workflows/smart-mcp-proxy.yml, .github/workflows/vscode-extension.yml.

<!-- section: Decisions -->
## Decisions

### CLI Python `aiadev` como caminho suportado de instalação

- **Choice:** CLI Python que renderiza um preset no projeto; caminho suportado a partir da v0.3 (README.md:21-22).
- **Why:** o CLI renderiza o preset no projeto com variáveis substituídas e mantém um manifest que permite reinstalar, sincronizar (`aiadev sync`), verificar (`aiadev doctor`) e desinstalar (README.md:21-22, README.md:45-53, README.md:63) — coisas que um plugin por plataforma não faz.
- **Rejected alternatives:** nenhuma rejeitada: os plugins por plataforma continuam como caminho legado mantido, sem manifest de instalação (README.md:92-95). Decisão do mantenedor, 2026-09-25.

### TypeScript/Node para a extensão VS Code e o smart-mcp-proxy

- **Choice:** TypeScript nos dois pacotes (vscode-extension/package.json:114, packages/smart-mcp-proxy/package.json:51), distribuídos no VS Code Marketplace e no npm (.github/workflows/vscode-extension.yml:105-110, .github/workflows/smart-mcp-proxy.yml:105-110).
- **Why:** na extensão VS Code, é requisito da plataforma: a API de extensões do VS Code roda em Node (vscode-extension/package.json:31). No smart-mcp-proxy, distribuição por npm e hook em Node — inferência aprovada pelo mantenedor em 2026-09-25, não registrada no repositório.
- **Rejected alternatives:** nenhuma registrada.

### `AGENTS.md` como arquivo de agente canônico

- **Choice:** `aiadev sync` gera um único `AGENTS.md` na raiz; `CLAUDE.md`/`GEMINI.md` viram ponteiros de ~3 linhas (README.md:148-152).
- **Why:** para que as cinco plataformas não possam mais divergir silenciosamente (README.md:152-153).
- **Rejected alternatives:** duplicar o conteúdo gerado em cada arquivo de plataforma (README.md:151-152).

### Manifestos de plugin gerados, não editados à mão

- **Choice:** `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` e `.cursor-plugin/plugin.json` gerados de `VERSION` + `pyproject.toml` + `presets/catalog.json` (README.md:214-216).
- **Why:** acabar com manifestos que divergem da versão de release (README.md:216-217).
- **Rejected alternatives:** manifestos editados à mão (README.md:216-217).

### smart-mcp-proxy determinístico, sem modelo e sem rede

- **Choice:** condensação por bloco verbatim `ERROR SIGNATURES` + trecho head/tail, sem modelo e sem rede (packages/smart-mcp-proxy/package.json:4, CHANGELOG.md:42-48).
- **Why:** o modelo local teve a mesma acurácia (6/6) com ~4 s por chamada e inventou conteúdo duas vezes; estudos externos mediram que condensar saída de ferramenta aumenta o custo por tarefa (CHANGELOG.md:50-57, packages/smart-mcp-proxy/BENCHMARK.md:252).
- **Rejected alternatives:** resumo por modelo local via Ollama (`qwen2.5-coder:3b`), removido na 0.4.0 (CHANGELOG.md:42-45, packages/smart-mcp-proxy/BENCHMARK.md:3).
