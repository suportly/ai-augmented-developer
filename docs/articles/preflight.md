# Pipeline pre-flight checks

`aiadev preflight` is a read-only checker that verifies a feature
directory holds the upstream artifacts a downstream pipeline skill
needs before that skill runs. Same code path serves both CI and the
in-skill call-out, so the diagnostics are byte-identical.

## What it checks

For a given `<skill>` and feature slug:

- **Artifact presence.** `spec.md` for every skill except `specify`,
  `plan.md` for `tasks` / `implement` / `analyze` / `finishing-a-branch`,
  and `tasks.md` for `implement` / `analyze` / `finishing-a-branch`.
- **`spec.md` shape.** Required `<!-- section: ... -->` anchors and zero
  unresolved `[NEEDS CLARIFICATION]` markers (the latter blocks `plan`).
- **Header coherence.** The `**Language:**` header in `spec.md` and
  `plan.md` must match. The `**Branch:**` header in `plan.md` must
  match the feature directory.
- **Git branch alignment.** The current git branch must match the
  feature directory (`feature/<slug>` or `feature/<slug>` with the
  numeric prefix stripped).
- **Review approval.** `finishing-a-branch` requires
  `.aiadev/review.yaml` at the repo root with `status: approved`.

Failures emit one single-line diagnostic per issue to stderr and exit
non-zero.

## CLI usage

```bash
# Check one feature for one upcoming skill.
aiadev preflight plan --feature 0010-pipeline-preflight-checks

# Check every feature directory in one shot. Use this on first upgrade
# to discover which in-flight branches need manual attention.
aiadev preflight --all
```

`--all` runs the highest stage already started for each feature
directory (the highest artifact present): if `tasks.md` exists it runs
the `implement` check, otherwise `tasks`, otherwise `plan`, otherwise
`specify`.

## Bypass for debugging

```bash
AIADEV_PREFLIGHT=warn aiadev preflight implement --feature my-thing
```

When `AIADEV_PREFLIGHT=warn`, diagnostics still print to stderr but the
exit code stays 0 and downstream skills continue. **This is a debugging
switch.** Setting it in CI defeats the whole point — keep it unset in
shared environments and document any exception in your project's
`CLAUDE.md`.

## Migration from older feature directories

Branches that completed review before this change need a
`.aiadev/review.yaml` stub before `finishing-a-branch` will run:

```yaml
status: approved
timestamp: 2026-04-21T00:00:00Z
```

Branches whose `spec.md` predates the section-anchor contract may need
the missing anchors added back. `aiadev preflight --all` lists them.

## Diagnostic format

Each issue is one line:

```
pre-flight: <what is wrong> — <how to fix it>
```

Examples:

```
pre-flight: tasks.md missing — run /aia:tasks first
pre-flight: spec.md has 2 unresolved [NEEDS CLARIFICATION] markers — run /aia:clarify first
pre-flight: language mismatch — spec.md=en, plan.md=pt-BR
pre-flight: git branch 'feature/other-thing' does not match feature directory '0010-pipeline-preflight-checks'
pre-flight: review approval missing — run /aia:requesting-code-review first
```

The string is stable: scripts and CI may grep for it. Changes to the
wording follow the constitution's amendment process.
