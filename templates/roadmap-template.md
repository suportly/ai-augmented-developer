# Roadmap: {{PRODUCT_NAME}}

<!-- Produced by the `product` skill in bootstrap mode (or updated by it in
     update mode, and later by `replan` / roadmap mode). Read by `specify`,
     which cites the matching R{{NNN}} id in a new spec's Traceability
     section once the roadmap entry has been turned into a spec. -->

**Language:** {{DOC_LANGUAGE}} <!-- BCP-47 tag; render this file in the consumer project's spec language. -->

---

<!-- section: Entries -->
## Entries

<!-- One block per entry, headed `### R<NNN> — <title>` with a
     zero-padded id. The id is monotonic and stable: once assigned it is
     never reused or renumbered, even if the entry is later dropped.

     Each heading is followed by exactly three bullet fields, in this
     order:
     - Status: one value from the closed set planned, in-progress, done,
       dropped. No other value is valid.
     - Spec: the slug of the spec this entry became, in the form
       four-digit-number dash slug. Leave the value empty until `specify`
       has run for this entry.
     - Depends on: zero or more other entry ids, comma-separated. Leave
       empty when the entry has no dependency.

     After the three fields, one or two sentences explain why this entry
     exists (the outcome it serves, not implementation detail).

     "Ready to implement" is deliberately NOT a roadmap status. Readiness
     is a property of the spec's own pipeline state (spec written, clarified,
     planned, tasked), not of the roadmap entry, so it is never duplicated
     here — duplicated state drifts. Run `/aia:help` on the spec's branch
     to know whether a planned entry is ready to implement. -->

### R{{NNN}} — {{ENTRY_TITLE}}

- **Status:** {{STATUS}}
- **Spec:** {{SPEC_SLUG}}
- **Depends on:** {{DEPENDS_ON}}

{{ENTRY_WHY}}
