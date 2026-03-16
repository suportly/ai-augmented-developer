# Installing AI-Augmented Developer for OpenCode

## Prerequisites

- [OpenCode](https://opencode.ai) installed
- Git installed

## Installation Steps

### 1. Clone the Repository

```bash
git clone https://github.com/suportly/ai-augmented-developer.git ~/.config/opencode/ai-augmented-developer
```

### 2. Symlink Skills

```bash
mkdir -p ~/.config/opencode/skills
rm -rf ~/.config/opencode/skills/ai-augmented-developer
ln -s ~/.config/opencode/ai-augmented-developer/skills ~/.config/opencode/skills/ai-augmented-developer
```

### 3. Restart OpenCode

Restart OpenCode. Skills will be available via the native `skill` tool.

Verify by asking: "do you have ai-augmented-developer skills?"

## Usage

### Finding Skills
Use OpenCode's native `skill` tool to list available skills.

### Loading a Skill
Use OpenCode's native `skill` tool, e.g. `ai-augmented-developer/brainstorming`.

### Skill Priority
Project skills (`.opencode/skills/`) > Personal skills > AI-Augmented Developer skills

## Updating

```bash
cd ~/.config/opencode/ai-augmented-developer && git pull
```

## Uninstalling

```bash
rm -rf ~/.config/opencode/skills/ai-augmented-developer
rm -rf ~/.config/opencode/ai-augmented-developer
```
