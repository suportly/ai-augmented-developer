---
name: brainstorming
description: "Use BEFORE any feature, component, or behavior change. Refines requirements and generates a spec before any code."
---

# Brainstorming → Design → Spec

Turn ideas into approved designs before touching any code.

<HARD-GATE>
Do NOT invoke any implementation skill, write any code, or scaffold any project until you have presented a design and the user has approved it. This applies to EVERY feature, no matter how simple it seems.
</HARD-GATE>

## Anti-Pattern: "It's too simple to need a design"

Every project goes through this process. A one-line change can have unexamined assumptions that cause rework. The design can be short (a few sentences for truly simple things), but it MUST be presented and approved.

## Checklist (in order)

1. **Explore project context** — read relevant files, CLAUDE.md, recent commits
2. **Identify active stack** — Django, React, Mobile, AI/Celery
3. **Ask clarifying questions** — one at a time, understand purpose/constraints/success criteria
4. **Propose 2-3 approaches** — with trade-offs and recommendation
5. **Present design** — in sections, get approval after each section
6. **Write spec** — save to `specs/YYYY-MM-DD-<topic>/spec.md`
7. **Spec review loop** — dispatch spec-document-reviewer subagent until approved
8. **User reviews spec** — wait for approval before proceeding
9. **Transition to implementation** — invoke `writing-plans` or `speckit`

## Process

### Understanding the Idea

- Check the current project state first
- Assess scope: if the request describes multiple independent subsystems, decompose before detailing
- Ask one question at a time — prefer multiple choice when possible
- Focus on: purpose, constraints, success criteria

### Stack — Contextual Questions by Type

**Django backend feature:**
- Which existing Django app is closest? (accounts, ai, autodev, gamification, etc.)
- Will it need an async Celery task? Or can it be synchronous?
- Will there be new models/migrations?
- Any public endpoint (DRF) or internal only?

**React frontend feature:**
- Is it an admin page, public page, or reusable component?
- Will it use TanStack Query for server state? Which endpoint?
- Does it need animations (Framer Motion)?
- Mobile-first or desktop?

**Mobile feature (React Native/Expo):**
- Does it affect native functionality? (new lib = new EAS build)
- Needs OTA update or full build?

**AI/LiteLLM feature:**
- Preferred provider? (gemini, groq, anthropic)
- Needs SSE streaming?
- Goes to Celery task or synchronous response?

### Exploring Approaches

- Propose 2-3 approaches with trade-offs
- Lead with the recommendation and reasoning
- For Django features: consider patterns from existing apps (gitdata, integrations, autodev)

### Presenting the Design

- One section at a time, ask if it looks right before moving on
- Cover: architecture, components, data flow, error handling, testing
- Design for isolation: each module with single responsibility

## Documentation

After design approval:

1. Write spec to `specs/YYYY-MM-DD-<topic>/spec.md` following the template:
   ```markdown
   # Feature Specification: <Name>
   **Branch**: `XXX-<name>`
   **Status**: Draft

   ## User Scenarios & Testing
   ### User Story 1 - <Title> (Priority: P1)
   As a <role>, I want <action> so that <benefit>.
   **Acceptance Scenarios**: Given/When/Then
   ```
2. Commit the spec
3. Run review loop (dispatch `spec-document-reviewer` subagent)
4. Wait for user approval

## Transition

After spec is approved:
- Invoke `speckit` for features with auto-dev pipeline
- Invoke `writing-plans` for manual implementation
- **NEVER** invoke implementation skills directly
