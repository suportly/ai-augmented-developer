# aiadev Spec Explorer

Browse [AI-Augmented Developer](https://github.com/suportly/ai-augmented-developer) specs (`spec.md`, `plan.md`, `tasks.md`) directly from the VS Code activity bar — no terminal hop required.

## What it does

The extension watches each workspace folder's `specs/` directory (configurable) and renders a tree view that mirrors the aiadev pipeline state for every feature:

- **Pipeline state badge** on every spec — `draft`, `clarifying`, `planned`, `tasked`, or `implementing` — derived from which artifacts are present and their `Status:` headers.
- **Task children** with per-task status icons, plus a `D / N done` rollup on the parent.
- **Clarification groups** that surface `[NEEDS CLARIFICATION: cl-N]` markers and jump to the exact line in `spec.md` on click.
- **Branch highlight** — the spec matching the current Git branch is bolded and tagged with a current-branch dot.
- **Multi-root aware** — when several folders are open, each spec label is prefixed with its workspace folder.
- **Debounced refresh** (≤ 500 ms) on file system changes, plus a manual `Refresh` action in the view title bar.

Click a `tasks.md` row and the editor jumps to the corresponding `T###` heading. Click a clarification row and the editor lands on the marker line.

## Screenshots

Screenshots will be added in a follow-up release once the Marketplace listing is published. Run the extension locally to see the tree in action.

## Install

### From the Marketplace

```text
ext install aiadev.aiadev-spec-explorer
```

Or search for **aiadev Spec Explorer** in the VS Code Extensions view.

### From a `.vsix`

Each tagged release attaches a `.vsix` artifact built by CI. Download it from the [Releases page](https://github.com/suportly/ai-augmented-developer/releases) and install via:

```bash
code --install-extension aiadev-spec-explorer-<version>.vsix
```

### From source

```bash
git clone https://github.com/suportly/ai-augmented-developer.git
cd ai-augmented-developer/vscode-extension
npm install
npm run package    # produces a .vsix in the current directory
code --install-extension aiadev-spec-explorer-*.vsix
```

## Configuration

| Setting | Default | Description |
|---|---|---|
| `aiadev.specExplorer.specsRoot` | `specs` | Root directory under each workspace folder where aiadev specs live. Resource-scoped, so you can override it per folder. |

## Commands

| Command | Title |
|---|---|
| `aiadev.specExplorer.refresh` | aiadev: Refresh |

The refresh action is also bound to the navigation group of the Spec Explorer view title bar.

## Supported platforms

- VS Code `^1.85.0` on Linux, macOS, and Windows.
- Untrusted workspaces are supported — the extension only reads Markdown files and never executes workspace code.

## Framework

This extension is one surface on top of the AI-Augmented Developer framework. The framework itself ships skills, presets, and a CLI that drive a spec-first, test-first pipeline for coding agents. See the [framework README](../README.md) for the full workflow.

## License

MIT — see [`LICENSE`](../LICENSE) at the repository root.
