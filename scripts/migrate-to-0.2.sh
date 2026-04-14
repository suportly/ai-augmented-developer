#!/usr/bin/env bash
# migrate-to-0.2.sh — helps a v0.1 consumer project adopt v0.2.
#
# What changes between v0.1 and v0.2 that affects consumers:
#
#  1. skills/brainstorming/ and skills/writing-plans/ were removed;
#     use specify + clarify + plan + tasks instead.
#  2. skills/speckit/ and skills/subagent-driven-development/ were
#     merged into skills/implement/ .
#  3. The stack-specific skills (django-patterns, ai-integration,
#     celery-async, autodev-pipeline, deploy, run-tests) moved to
#     presets/django-drf-react/skills/ . To keep them discoverable,
#     install the django-drf-react preset.
#  4. The root CLAUDE.md is now stack-agnostic. The Django + React
#     content lives in presets/django-drf-react/CLAUDE.md and is
#     rendered into your project by `aiadev install --preset
#     django-drf-react` (or, until aiadev ships, by the symlink
#     block below).
#
# This script is read-only except for the symlinks it proposes. It
# prints what it would do by default; pass --apply to actually act.

set -euo pipefail

APPLY=false
if [ "${1:-}" = "--apply" ]; then
  APPLY=true
fi

log() {
  printf '%s\n' "$*"
}

run() {
  log "+ $*"
  if [ "$APPLY" = true ]; then
    eval "$*"
  fi
}

repo_root=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
preset_dir="$repo_root/.ai-augmented-developer/presets/django-drf-react"

if [ ! -d "$repo_root/.ai-augmented-developer" ]; then
  log "This directory does not look like a project that installs"
  log "ai-augmented-developer. Expected .ai-augmented-developer/ to exist."
  log "If you use a different install path, set AIADEV_ROOT and re-run."
  exit 1
fi

log "=== Stage 1: detect removed skills used by CLAUDE.md or scripts ==="
grep_removed() {
  grep -rIn --include '*.md' --include '*.sh' \
    -E '(brainstorming|writing-plans|subagent-driven-development|speckit)' \
    "$repo_root" 2>/dev/null | grep -v '\.ai-augmented-developer/' || true
}

refs=$(grep_removed)
if [ -n "$refs" ]; then
  log "References to removed v0.1 skills found:"
  printf '%s\n' "$refs"
  log ""
  log "Update those files to invoke the v0.2 replacements:"
  log "  brainstorming  → specify"
  log "  writing-plans  → plan (plus tasks)"
  log "  speckit        → specify + clarify + plan + tasks + implement"
  log "  subagent-driven-development → implement"
fi

log ""
log "=== Stage 2: make the django-drf-react preset discoverable ==="

# Link the preset CLAUDE.md and skills into the places Claude Code /
# Cursor / OpenCode expect, so the agent finds them automatically.
if [ ! -e "$repo_root/CLAUDE.md" ]; then
  run "ln -s .ai-augmented-developer/presets/django-drf-react/CLAUDE.md '$repo_root/CLAUDE.md'"
fi

if [ -d "$preset_dir/skills" ]; then
  mkdir -p "$repo_root/.claude/skills"
  for skill_dir in "$preset_dir"/skills/*/; do
    name=$(basename "$skill_dir")
    target="$repo_root/.claude/skills/$name"
    if [ ! -e "$target" ]; then
      run "ln -s '$skill_dir' '$target'"
    fi
  done
fi

log ""
log "=== Stage 3: constitution ==="
if [ ! -f "$repo_root/constitution.md" ]; then
  log "No project-level constitution.md found. Recommendation:"
  log "  cp .ai-augmented-developer/templates/constitution-template.md constitution.md"
  log "  \$EDITOR constitution.md   # add project-specific articles"
fi

log ""
if [ "$APPLY" = true ]; then
  log "Migration actions above have been applied."
else
  log "Dry run complete. Re-run with --apply to perform the actions."
fi
