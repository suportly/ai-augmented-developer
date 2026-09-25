---
name: product
description: Bootstrap or update the project's product context — mission, tech stack, roadmap — in specs/_product/, inferred from the repository. Use when a project has no product context yet or it needs updating.
metadata:
  aiadev:
    version: 0.1.0
    inputs:
    - type: text
      description: What to update (optional; omit to bootstrap or refresh all three documents).
      optional: true
    outputs:
    - type: file
      path: specs/_product/mission.md
    - type: file
      path: specs/_product/tech-stack.md
    - type: file
      path: specs/_product/roadmap.md
    requires:
    - templates/mission-template.md
    - templates/tech-stack-template.md
    - templates/roadmap-template.md
    handoffs:
    - specify
---

# Product

Bootstrap or refresh the project's product context — mission, tech stack, and roadmap — in `specs/_product/`, inferred from the repository itself. This context grounds `specify` so specs stay consistent with what the product actually is and where it is headed.

**Announce at start:** "Using the product skill. I will bootstrap or update specs/_product/mission.md, tech-stack.md, and roadmap.md."
