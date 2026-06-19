# DEC018 - Documentation Clutter Map and Retention Rules

Date: 2026-06-19
Task: T-041 - Documentation Clutter Audit and Current-State Alignment
Status: Accepted
Owner: Orchestrator

## Context

The project has accumulated current operating docs, model/source methodology
docs, implemented design plans, source-spike reports, decision records, and
handoff records. This is useful for auditability, but it creates clutter risk:
older files can contain accurate historical statements that are false for the
current runtime after later tasks.

Examples found during the T-041 audit:

- README still described Monte Carlo as future deterministic-replacement work.
- Developer playbook still listed deterministic progression as a current
  pitfall.
- `PROJECT_CONTEXT.md` still read like active architecture even though it
  describes initial setup context.
- Historical decisions and handoffs correctly preserve pre-T-037/T-039 facts.

## Decision

Adopt `docs/documentation_clutter_audit.md` as the current documentation map.

Use these retention rules:

1. Current-facing docs must be kept aligned after each completed task:
   `PROJECT_CHARTER.md`, `AGENTS.md`, `TASKS.md`, `STATUS.md`,
   `docs/phase_plan.md`, `docs/DEVELOPER_PLAYBOOK.md`,
   `docs/data_contracts.md`, and `docs/model_provenance.md`.
2. Decision records in `docs/decisions/` are append-only historical records.
   New decisions supersede old ones; old decisions should not be rewritten just
   because the implementation later changed.
3. Handoff records in `docs/handoffs/` are append-only delivery records.
   Older next-step recommendations can be superseded by newer `TASKS.md` and
   `STATUS.md` entries.
4. Initial setup context such as `PROJECT_CONTEXT.md` can be retained, but it
   must be labeled as background-only when it no longer represents the active
   runtime.
5. If `STATUS.md` becomes too large to navigate, create a future archival task
   rather than mixing history deletion into feature work.

## Consequences

- Current state starts from `TASKS.md`, `STATUS.md`, `docs/phase_plan.md`, and
  `docs/documentation_clutter_audit.md`.
- Historical records remain available for traceability.
- Future Orchestrator closeouts should update stale current-facing docs but
  avoid rewriting old decisions/handoffs unless the user explicitly requests a
  historical correction.
- T-038 remains the next implementation task; the documentation audit does not
  change product sequencing.

## Verification

- Added `docs/documentation_clutter_audit.md`.
- Updated stale current-facing docs identified by the audit.
- Added T-041 to `TASKS.md`, `STATUS.md`, and `docs/phase_plan.md`.
