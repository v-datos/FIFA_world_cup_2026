# Documentation Clutter Audit

Last updated: 2026-06-21
Task: T-041 - Documentation Clutter Audit and Current-State Alignment
Owner: Orchestrator

## Scope

This audit reviewed the tracked Markdown and operating documents after T-039.
The repository currently has 52 tracked Markdown/agent docs excluding
`node_modules`, including 17 decision records and 15 handoff records.

The goal is not to delete historical records. The goal is to make it clear which
documents describe current state and which documents are historical evidence
that may contain superseded implementation details.

## Current-First Reading Order

Use this order when trying to understand the project today:

1. `PROJECT_CHARTER.md` - current mission, architecture, source rules, risks.
2. `AGENTS.md` - agent roles, handoff rules, closeout expectations.
3. `TASKS.md` - current queue, backlog, and completed task routing.
4. `STATUS.md` - newest status entry first; older entries are chronological
   history and may be superseded by newer entries.
5. `docs/phase_plan.md` - phase gates, active batch map, recent decisions.
6. `docs/data_contracts.md` - active JSON/API/source-cache contracts.
7. `docs/model_provenance.md` - current model/source truth and label wording.
8. `docs/DEVELOPER_PLAYBOOK.md` - local verification, source refresh commands,
   deployment caveats, common pitfalls.

## Documentation Classes

| Class | Files | Rule |
|---|---|---|
| Current operating docs | `PROJECT_CHARTER.md`, `AGENTS.md`, `TASKS.md`, `STATUS.md`, `docs/phase_plan.md`, `docs/DEVELOPER_PLAYBOOK.md` | Keep aligned after each completed task. |
| Current contracts and methodology | `docs/data_contracts.md`, `docs/model_provenance.md`, `docs/ai_research_source_policy.md`, `docs/domain/README.md`, `README.md` | Update when runtime behavior, source truth, or user-facing claims change. |
| Implemented design plans | `docs/last_minute_briefing_plan.md`, `docs/active_fixture_discovery_plan.md`, `docs/no_cost_football_data_source_spike.md`, `docs/source_spikes/t039_no_cost_rating_sources.md` | Retain as implemented plans/source reports; update only when their implemented behavior changes. |
| Historical decisions | `docs/decisions/*.md` | Append-only decision history. Older decisions may describe prior state; use the newest applicable decision for current truth. |
| Historical handoffs | `docs/handoffs/*.md` | Append-only delivery history. Older handoffs may contain superseded next-step advice. |
| Initial context | `PROJECT_CONTEXT.md` | Background only; not current architecture. It is now labeled as initial setup context. |
| Optional/reference docs | `docs/style_guide.md`, `src/frontend/README.md` | Keep if useful; update opportunistically when their owned area changes. |

## Findings

| ID | Finding | Action taken |
|---|---|---|
| DCA-1 | Main `README.md` still described tournament progression as deterministic future work. | Updated to describe the active seeded Monte Carlo simulation and World Football Elo cache. |
| DCA-2 | `docs/DEVELOPER_PLAYBOOK.md` still listed deterministic Monte Carlo and fragile multi-word parsing as current pitfalls. | Updated pitfalls to point to shared team identity and active random-trial Monte Carlo; legacy Streamlit caveat remains. |
| DCA-3 | `docs/data_contracts.md` still suggested T-036 and T-039 as next assignments. | Updated next assignments to T-038, T-033, and T-029. |
| DCA-4 | `PROJECT_CONTEXT.md` described initial Streamlit/BigQuery assets without a current-state warning. | Added a background-only status note and current-doc pointers. |
| DCA-5 | `PROJECT_CHARTER.md` decision/risk lists lagged recent DEC012-DEC017 records. | Added DEC012-DEC018 references, source-cache architecture note, and documentation-clutter risk. |
| DCA-6 | Decisions and handoffs intentionally preserve old statements such as deterministic progression or hardcoded ratings. | No rewrite. Current docs and DEC018 now state retention rules. |
| DCA-7 | `STATUS.md` is large and historical. | Retained because newest-first status is useful; future archival is optional if it becomes hard to navigate. |
| DCA-8 | Stale `generate_match_headlines.py` documentation and comments still referenced Anthropic Claude and billing API keys. | Updated code comments and docstrings to match the Vertex AI Gemini implementation. |
| DCA-9 | `docs/data_contracts.md` suggested `T-019` as a future assignment despite the task being dropped. | Removed the T-019 player stats hover task reference. |

## Retention Decision

No documentation files were deleted in this pass.

Rationale:

- Decision and handoff files are audit records.
- Current-facing stale statements were corrected directly.
- Initial context is now labeled instead of removed.
- The biggest remaining clutter source is chronological volume in `STATUS.md`,
  not broken current-state routing.

## Current Next Step

All sprint backlog tasks and phase objectives are complete. The project is fully operational on Cloud Run with Google SDK integration. Upcoming assignments focus on scheduled automation monitoring:

- Monitor and verify the daily ESPN matchday refresh GitHub Actions workflow.
- Monitor Vertex AI Gemini tactical insights generation for subsequent fixtures.

## Verification

Closeout verification for this audit:

- Markdown/current-state scan over tracked docs excluding `node_modules`.
- `git diff --check`
- `python3 -m compileall -q src`
- `npm --prefix src/frontend run build`
