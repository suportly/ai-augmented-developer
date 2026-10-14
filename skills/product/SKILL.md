---
name: product
description: Bootstrap or update the project's product context — mission, tech stack, roadmap — in specs/_product/, inferred from the repository. Use when a project has no product context yet or it needs updating.
metadata:
  aiadev:
    version: 0.1.0
    inputs:
    - type: text
      description: What to update (optional; omit it to bootstrap, or to pick a section to update).
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

Bootstrap or refresh the project's product context (mission, tech stack, roadmap) in `specs/_product/`, inferred from the repository. It grounds `specify`.

## Mode detection (run before anything else)

1. No `specs/_product/` → **Bootstrap mode**.
2. It exists → **Update mode** for the files present; if any of the three is missing, bootstrap only the missing ones.

## Bootstrap mode

1. **Read what describes the project.** `README.md`, package files (`package.json`, `pyproject.toml`, `requirements.txt`, `Cargo.toml`, `go.mod`, equivalents), `AGENTS.md`/`CLAUDE.md`, `.claude/rules/*`, top-level layout. In a monorepo also read nested subproject manifests (e.g. `packages/*/package.json`): stack detection only looks at the root.
2. **Render the three templates** (`templates/mission-template.md`, `templates/tech-stack-template.md`, `templates/roadmap-template.md`) into drafts. Every filled value cites its source inline (file, plus line when there is one). A value with no traceable source is not filled. Drop the templates' guidance comments (they quote the marker grammar and would read as open markers) but keep the `<!-- section: … -->` anchors.
3. **Seed `tech-stack.md` Languages and Frameworks** from the `aiadev:auto-stack:start`/`end` block in `AGENTS.md`; if absent, read the files detection reads (manifests, `tsconfig.json`, `docker-compose.yml`, `Makefile`, `.github/workflows/*.yml`). Cite the file for each entry. Never invent the why or the rejected alternatives: ask per decision and mark `[NEEDS CLARIFICATION:cl-N …]` until answered.
4. **Every other non-inferable value** becomes `[NEEDS CLARIFICATION:cl-N <precise question>]`, ids monotonic per file from `cl-1`. Never invent an audience, problem statement, or rationale the repository does not state.
5. **Present the drafts** and ask only the targeted questions the markers need.
6. **Write only after explicit approval**: create `specs/_product/` and write the three files; no partial drafts.

## Update mode

1. With text naming what to change: edit only the section(s) it points to, show the diff, write after approval.
2. With no text: list the current sections (file + heading, e.g. `mission.md — For whom`) and ask which to update.
3. Never overwrite a file wholesale. Added or changed values follow the same cite-or-mark rule.

## Rules

- Zero values without a source. Inferred is not the same as fabricated: untraceable means a `cl-N` marker, never a guess.
- Never read secret files during inference: `.env*`, `*.pem`, `*.key`, `id_rsa*`, `*credentials*`. Product context must not carry secrets (Article VI).
- Never overwrite a file wholesale; nothing is written in `specs/_product/` before approval.
- Roadmap field lines (`- **Status:**`, `- **Spec:**`, `- **Depends on:**`) are machine-parsed: keep them bare and put citations in the entry's paragraph.

## Hand-off

Run `specify` for the next demand; it reads `mission.md` and `roadmap.md`. Roadmap entries become specs one at a time: pick the next `planned` entry, run `specify`, then update its `Spec:` field.
