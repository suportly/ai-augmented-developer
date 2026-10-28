---
name: design
description: Turn a feature's UI scenarios into a private prototype and a design.md with a screen map and gaps.
metadata:
  aiadev:
    version: 0.1.0
    inputs:
    - type: file
      path: specs/<branch>/spec.md
      description: Approved spec declaring the UI.
    - type: file
      path: specs/<branch>/plan.md
      description: Approved plan.
    - type: file
      path: specs/<branch>/tasks.md
      description: Task list to map screens onto.
    outputs:
    - type: file
      path: specs/<branch>/design.md
      description: Prototype link, screen to scenario to task map, and gaps.
    requires: []
    handoffs:
    - tasks
    - implement
---

# Design

Make a prototype of the interface tasks and record it in `design.md`.

## Steps

1. **Preflight.** Run `aiadev preflight design --feature <slug>`. If the spec lacks `**UI:** yes`, warn that the feature declares no UI and ask whether to continue.
2. **Pick tasks.** Read `spec.md`, `plan.md` and `tasks.md`. Select the tasks that have an interface. Show the list and continue only after the user confirms or adjusts it.
3. **Write the brief** with screen content only: screens, Given/When/Then scenarios, states (empty, error, loading) and texts defined in the spec. Never include file paths, commit hashes, task ids or internal module names. Quote only scenarios and texts present in the spec.
4. **Confirm.** Show exactly what will be sent. Publish only after explicit user confirmation. The canvas is private, one artboard per screen.
5. **Create the prototype** with the `Artifact` tool: `action: quickstart` with `intent: design`, then follow its result. Run it in a subagent with `description` `design: <slug>` that returns only the link and the screen map. Do not configure or ask for a design system.
6. **Record.** Write `specs/<feature>/design.md` from `templates/design-template.md`: the link, a screen to scenario to task map, and gaps. Each gap cites the spec scenario that motivates it, or says there is none.
7. **Amend.** Turn gaps into proposed new tasks. Add them to `tasks.md` only after approval, through the `tasks` skill.

## Fallbacks

- No `Artifact` tool: say you could not create the prototype and write markdown wireframes in `design.md`.
- Creation fails (network or refusal): record no link, give the reason, and offer wireframes.

Hand off to `implement`.
