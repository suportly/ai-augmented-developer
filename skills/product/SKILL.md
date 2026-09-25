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

## Mode detection (run before anything else)

1. **Check whether `specs/_product/` exists** in the project root.
2. **If `specs/_product/` does not exist** (no `mission.md`, `tech-stack.md`, or `roadmap.md` yet), enter **Bootstrap mode** below.
3. **If `specs/_product/` exists**, enter **Update mode** below.

## Bootstrap mode

1. **Read what describes the project.** `README.md`, package files (`package.json`, `pyproject.toml`, `requirements.txt`, `Cargo.toml`, `go.mod`, and equivalents), `AGENTS.md`/`CLAUDE.md`, `.claude/rules/*`, and the top-level folder layout. In a monorepo, also read the manifests of nested subprojects (e.g. `packages/*/package.json`): stack detection only looks at the repository root. This is the same reconnaissance `constitution` does in its own bootstrap mode.
2. **Render the three templates into drafts**: `templates/mission-template.md`, `templates/tech-stack-template.md`, `templates/roadmap-template.md`. Every filled value must cite its source inline — the file path, and the line number when there is one (e.g. "audience inferred from README.md:12"). A value with no traceable source does not get filled. Drop the templates' guidance comments from the rendered files: they quote the clarification-marker grammar and would read as open markers.
3. **Seed `tech-stack.md`'s Languages and Frameworks from the stack detection `aiadev sync` already does.** `tech-stack.md` records decisions (what was adopted, why, what was rejected); the auto-stack block that `aiadev sync` writes into `AGENTS.md`, between the `aiadev:auto-stack:start` and `aiadev:auto-stack:end` markers, is the detected inventory.
   - If `AGENTS.md` has that block, take the languages and frameworks from it.
   - If not, read the files that detection reads: `package.json`, `tsconfig.json`, `pyproject.toml`, `requirements.txt`, `Cargo.toml`, `go.mod`, `pubspec.yaml`, `docker-compose.yml`, `Makefile`, `Taskfile.yml`, and `.github/workflows/*.yml`.
   - Cite the project file each entry was detected from (e.g. "Python — pyproject.toml").
   - Never invent the why or the rejected alternatives: ask the human for both, per decision, and mark them `[NEEDS CLARIFICATION:cl-N …]` until answered.
4. **Replace every other non-inferable value** with a `[NEEDS CLARIFICATION:cl-N <precise question>]` marker, with ids monotonic per file starting at `cl-1`. Never invent — an audience, a problem statement, or a decision rationale the repository does not state becomes a marker, not a guess. Example: when the repository never says who the product is for, the audience field becomes a marker with a precise question.
5. **Present the three drafts** and ask only the targeted questions needed to resolve the clarification markers — no open-ended "tell me about your product" questions when the repository context already answers them.
6. **Write only after explicit approval.** Create `specs/_product/` if it does not exist, then write `mission.md`, `tech-stack.md`, and `roadmap.md`. Do not write before approval, and do not write partial drafts.

## Update mode

Same contract as the `constitution` skill when a constitution already exists, applied to three files instead of one.

1. **With user text naming what to change**: edit only the section(s) that text points to — in whichever of `mission.md`, `tech-stack.md`, `roadmap.md` it belongs to. Show the diff before writing. Write only after approval.
2. **With no user text**: list the current sections of the three files (file + heading, e.g. `mission.md — For whom`) and ask which to update. Never overwrite a file wholesale — always target a specific section.
3. Values added or changed in update mode follow the same cite-or-mark rule as bootstrap: cite the source, or mark it `[NEEDS CLARIFICATION:cl-N ...]` when it cannot be traced.

## Rules

- Every filled value cites its source (file, and line when there is one) — zero values without a source.
- Inferred is not the same as fabricated. When a value cannot be traced to something in the repository, it becomes a `cl-N` marker, never a plausible-sounding guess.
- Never read secret files during inference: `.env*`, `*.pem`, `*.key`, `id_rsa*`, `*credentials*`. Product context must not carry secrets (Article VI, Privacy by design).
- Do not write any file in `specs/_product/` before the user has explicitly approved the drafts.
- In update mode, never overwrite a file wholesale — edit only the targeted section.
- Roadmap field lines (`- **Status:**`, `- **Spec:**`, `- **Depends on:**`) are machine-parsed: keep them bare and put their citations in the entry's paragraph.

## Hand-off

- After writing `specs/_product/`, run `specify` for the next demand — it reads `mission.md` and `roadmap.md` so new specs stay consistent with the product's scope and traceable to a roadmap entry.
- Roadmap entries become specs one at a time: pick the next `planned` entry, run `specify` on it, and update its `Spec:` field once the spec exists.
