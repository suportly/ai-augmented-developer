# Terse mode

This rule governs the optional **terse-mode** output contract for
reviewer subagents spawned by the aiadev pipeline. It is off by default;
opting in is a single-line config change.

## The switch

Two sources resolve the setting. **Env wins** over settings.

| Layer     | Where                                        | Value                      |
|-----------|----------------------------------------------|----------------------------|
| Settings  | `.claude/settings.json` → `aiadev.terseMode` | `true` \| `false`          |
| Env       | `AIADEV_TERSE`                               | `1`/`true`/`yes`/`on` or `0`/`false`/`no`/`off`/`""` |

The resolved `(enabled, source)` pair lives in
`aiadev.config.resolve_terse_mode()`. `source` is one of `default`,
`settings`, `env`.

## The echo

Before your first substantive line of output, emit exactly one line:

```
terse-mode: <on|off> (<source>)
```

Where `<source>` is one of `default`, `settings`, `env`. This keeps the
resolved state visible in every hand-off, so CI logs and user sessions
can confirm which layer decided.

## The contract (when terse-mode is on)

Reviewer subagents (`spec-document-reviewer`, `plan-document-reviewer`,
`code-reviewer`) emit findings as **one line per finding**. Each line:

- starts with a severity glyph — `🔴` blocking, `🟡` should-fix, `🟢` nit,
- carries a `file:line` location,
- holds a ≤ 140-char single-line message.

The structured shape lives in
[`schemas/terse-output.schema.json`](../schemas/terse-output.schema.json).
Multi-paragraph findings fail validation.

When terse-mode is off, reviewers fall back to their verbose prose
format — spec Story 1 scenario 1 requires that default behaviour stay
byte-for-byte unchanged.
