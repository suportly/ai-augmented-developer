---
description: How to cite knowledge-graph facts and label their confidence when a graph context provider is available.
alwaysApply: true
---

# Graph facts and confidence

When a knowledge-graph context provider is configured (spec 0017), skills
may ground their claims in facts the provider returns instead of inferring
structure by grep. This rule governs **how those facts are cited** so a
reader never mistakes a discovered relationship for a guessed one.

## Confidence vocabulary (aiadev-canonical)

Every cited graph fact carries exactly one label:

| Label | Meaning |
|---|---|
| `explicit` | The relationship was extracted directly from the code (e.g. a resolved import, a direct call). Trustworthy. |
| `inferred` | The relationship was resolved heuristically across files or languages. Plausible, not proven. |
| `ambiguous` | The provider could not resolve the relationship uniquely. Treat as a hint only. |

## Mapping from the provider taxonomy

Providers emit their own labels. Map them to the aiadev vocabulary
**stably** — the displayed label is always the aiadev one, never the
provider's raw string. For the graphify reference provider:

| Provider label | aiadev label |
|---|---|
| `EXTRACTED` | `explicit` |
| `INFERRED` | `inferred` |
| `AMBIGUOUS` | `ambiguous` |

An unknown provider label maps to `ambiguous` (fail safe, never `explicit`).

## Citation rules

- Always cite a **verifiable** `path:symbol` alongside the fact, so the
  reader can check it against the code even if the graph is stale.
- Show the confidence label next to every cited fact.
- A fact labelled `inferred` or `ambiguous` must **not** be used to assert
  a gap or impact as **definitive**. Report it as a signal to verify, not a
  conclusion. Only `explicit` facts back a definitive statement.
- The provider is optional. Nothing in this rule requires a provider to be
  present; skills degrade to their provider-free behaviour when none is
  configured.
