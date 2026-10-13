# Tech stack: {{PRODUCT_NAME}}

<!-- Produced by the `product` skill in bootstrap mode (or updated by it in
     update mode). Read by `plan` to fill the Technical context section. -->

**Language:** {{DOC_LANGUAGE}} <!-- BCP-47 tag; render this file in the consumer project's spec language. -->

---

<!-- section: Languages -->
## Languages

<!-- Languages adopted by this product. One bullet per language, with the
     version or range if known. This is a DECISION record, not detected
     inventory: the aiadev:auto-stack block that `aiadev sync` writes to the
     project's AGENTS.md is the detected inventory instead. The `product`
     skill seeds this list from that block (the stack detection `aiadev sync`
     runs), citing the project file each entry came from (e.g. package.json,
     pyproject.toml). Use
     [NEEDS CLARIFICATION:cl-N ...] for anything not inferable. -->

- {{LANGUAGE_1}}

<!-- section: Frameworks -->
## Frameworks

<!-- Frameworks and major libraries adopted by this product. One bullet per
     framework, with the version if known. Same sourcing rule as Languages:
     seed from the auto-stack block and cite the source. -->

- {{FRAMEWORK_1}}

<!-- section: Decisions -->
## Decisions

<!-- Each decision below is a record of what was chosen, why, and what was
     rejected — this is the human-owned rationale that the detected
     aiadev:auto-stack inventory cannot capture on its own. When the
     decisions here and the auto-stack block diverge, `plan` lists the
     divergence and the human decides which one is stale. One
     `### {{DECISION_TITLE}}` block per decision. -->

### {{DECISION_TITLE}}

- **Choice:** {{DECISION_CHOICE}}
- **Why:** {{DECISION_RATIONALE}}
- **Rejected alternatives:** {{DECISION_REJECTED_ALTERNATIVES}}
