# Checklist items: Token economy

Lens for tool-output bloat. Compressors: see docs/token-economy.md in the framework repository (not installed in projects).

- Noisy tool output (test logs, `git status`, build) is filtered or summarized, not dumped into context.
- Long command output is truncated or paginated; no unbounded logs in context.
- Near-duplicate output is de-duplicated rather than repeated.
- Compression opportunities on high-volume commands are identified (and applied if a compressor is wired).
