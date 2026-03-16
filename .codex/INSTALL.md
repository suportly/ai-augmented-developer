# Installing AI-Augmented Developer for Codex

Enable AI-Augmented Developer skills in Codex via native skill discovery.

## Prerequisites

- Git

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/suportly/ai-augmented-developer.git ~/.codex/ai-augmented-developer
   ```

2. **Create the skills symlink:**
   ```bash
   mkdir -p ~/.agents/skills
   ln -s ~/.codex/ai-augmented-developer/skills ~/.agents/skills/ai-augmented-developer
   ```

   **Windows (PowerShell):**
   ```powershell
   New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.agents\skills"
   cmd /c mklink /J "$env:USERPROFILE\.agents\skills\ai-augmented-developer" "$env:USERPROFILE\.codex\ai-augmented-developer\skills"
   ```

3. **Restart Codex** to discover the skills.

## Verify

```bash
ls -la ~/.agents/skills/ai-augmented-developer
```

You should see a symlink pointing to the skills directory.

## Updating

```bash
cd ~/.codex/ai-augmented-developer && git pull
```

## Uninstalling

```bash
rm ~/.agents/skills/ai-augmented-developer
rm -rf ~/.codex/ai-augmented-developer
```
