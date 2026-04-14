# AI-Augmented Developer for Codex

Guide for using AI-Augmented Developer with OpenAI Codex via native skill discovery.

## Quick Install

Tell Codex:

```
Fetch and follow instructions from https://raw.githubusercontent.com/suportly/ai-augmented-developer/refs/heads/main/.codex/INSTALL.md
```

## Manual Installation

### Prerequisites

- OpenAI Codex CLI
- Git

### Steps

1. Clone the repo:
   ```bash
   git clone https://github.com/suportly/ai-augmented-developer.git ~/.codex/ai-augmented-developer
   ```

2. Create the skills symlink:
   ```bash
   mkdir -p ~/.agents/skills
   ln -s ~/.codex/ai-augmented-developer/skills ~/.agents/skills/ai-augmented-developer
   ```

3. Restart Codex.

4. **For subagent skills** (optional): Skills like `implement` require Codex's collab feature. Add to your Codex config:
   ```toml
   [features]
   collab = true
   ```

### Windows (PowerShell)

```powershell
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.agents\skills"
cmd /c mklink /J "$env:USERPROFILE\.agents\skills\ai-augmented-developer" "$env:USERPROFILE\.codex\ai-augmented-developer\skills"
```

## Verify

```bash
ls -la ~/.agents/skills/ai-augmented-developer
```

You should see a symlink pointing to the skills directory with all 16 skills listed.

## Usage

Skills are discovered automatically. Codex activates them when:
- You mention a skill by name (e.g., "use specify")
- The task matches a skill's description
- The `using-ai-augmented-developer` skill directs Codex to use one

## Updating

```bash
cd ~/.codex/ai-augmented-developer && git pull
```

Skills update instantly through the symlink.

## Uninstalling

```bash
rm ~/.agents/skills/ai-augmented-developer
rm -rf ~/.codex/ai-augmented-developer
```
