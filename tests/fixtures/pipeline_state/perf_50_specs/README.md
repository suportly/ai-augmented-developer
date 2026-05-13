# perf_50_specs fixture

Synthetic load fixture for the pipeline-state detector. Used by T002+ to
measure the detector's traversal budget against a 50-spec corpus.

## How to populate

```bash
python _generate_perf.py
```

This writes 50 minimal `spec.md` files under `specs/0001-x1/` …
`specs/0050-x50/`. Each spec is a clean, Approved single-surface fixture
with no clarification markers.

## Why the generated content is gitignored

Committing 50 near-identical Markdown files would inflate the repo and
churn diffs without information value. The script is the source of
truth; tests regenerate on demand.
