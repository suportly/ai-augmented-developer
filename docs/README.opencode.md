# AI-Augmented Developer for OpenCode

Complete guide for using AI-Augmented Developer with [OpenCode.ai](https://opencode.ai).

## Quick Install

Tell OpenCode:

```
Fetch and follow instructions from https://raw.githubusercontent.com/suportly/ai-augmented-developer/refs/heads/main/.opencode/INSTALL.md
```

## Manual Installation

### macOS / Linux

```bash
# 1. Clone (or update)
if [ -d ~/.config/opencode/ai-augmented-developer ]; then
  cd ~/.config/opencode/ai-augmented-developer && git pull
else
  git clone https://github.com/suportly/ai-augmented-developer.git ~/.config/opencode/ai-augmented-developer
fi

# 2. Create directories
mkdir -p ~/.config/opencode/skills

# 3. Remove old symlink if exists
rm -rf ~/.config/opencode/skills/ai-augmented-developer

# 4. Create skills symlink
ln -s ~/.config/opencode/ai-augmented-developer/skills ~/.config/opencode/skills/ai-augmented-developer

# 5. Restart OpenCode
```

### Windows (PowerShell)

```powershell
git clone https://github.com/suportly/ai-augmented-developer.git "$env:USERPROFILE\.config\opencode\ai-augmented-developer"
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.config\opencode\skills"
Remove-Item "$env:USERPROFILE\.config\opencode\skills\ai-augmented-developer" -Force -ErrorAction SilentlyContinue
New-Item -ItemType Junction -Path "$env:USERPROFILE\.config\opencode\skills\ai-augmented-developer" -Target "$env:USERPROFILE\.config\opencode\ai-augmented-developer\skills"
```

## Verify

```bash
ls -l ~/.config/opencode/skills/ai-augmented-developer
```

Should show a symlink pointing to the skills directory.

## Usage

### Finding Skills
Use OpenCode's native `skill` tool to list available skills.

### Loading a Skill
```
use skill tool to load ai-augmented-developer/brainstorming
```

### Skill Priority
Project skills (`.opencode/skills/`) > Personal skills > AI-Augmented Developer skills

## Updating

```bash
cd ~/.config/opencode/ai-augmented-developer && git pull
```

Restart OpenCode to load updates.

## Uninstalling

```bash
rm -rf ~/.config/opencode/skills/ai-augmented-developer
rm -rf ~/.config/opencode/ai-augmented-developer
```
