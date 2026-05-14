# Feature specification: task-context sample fixture

**Branch:** `feature/x`
**Created:** 2026-05-13
**Status:** Approved
**Spec ID:** 1
**Language:** en

---

<!-- section: Problem -->
## Problem

Synthetic mini-spec used by `tests/test_task_context.py` to exercise the
`task-context` skill's compose helper. Carries two user stories, each with
three acceptance scenarios so the spec-slice extractor has something to
narrow down.

<!-- section: User stories -->
## User stories

### Story 1 — Foo loader (P1)

As a user, I want to load `foo.py` so that downstream code can call it.

**Acceptance scenarios** (Given / When / Then):

1. Story 1 sc1: Given an empty foo, When the loader runs, Then it returns the literal string "story-1-scenario-1-marker".
2. Story 1 sc2: Given a populated foo, When the loader runs, Then it returns the literal string "story-1-scenario-2-marker".
3. Story 1 sc3: Given a corrupt foo, When the loader runs, Then it raises and emits the literal string "story-1-scenario-3-marker".

### Story 2 — Bar emitter (P2)

As a user, I want bar.py emitted so that the downstream subscriber wakes.

**Acceptance scenarios** (Given / When / Then):

1. Story 2 sc1: Given a quiet system, When the emitter fires, Then it logs the literal string "story-2-scenario-1-marker".
2. Story 2 sc2: Given a noisy system, When the emitter fires, Then it logs the literal string "story-2-scenario-2-marker".
3. Story 2 sc3: Given a saturated system, When the emitter fires, Then it logs the literal string "story-2-scenario-3-marker".

<!-- section: Traceability -->
## Traceability

- Originating issue: n/a (fixture).
- Constitution articles invoked: II.
