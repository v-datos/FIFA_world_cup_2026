# Phase Plan - FIFA World Cup 2026 Dashboard

Last updated: 2026-06-17
Current phase: Phase 5 - Framework Rebaseline & Pipeline Hardening

## Active Agents

| Agent | Status | Current task | Blocking on |
|---|---|---|---|
| Orchestrator | Routing | T-025 plan complete; assign T-026 next | None |
| QA / Reproducibility Engineer | Complete | Data contract audit delivered in `docs/data_contracts.md` | None |
| Data Pipeline Engineer | Complete | Last-minute briefing generation plan delivered in `docs/last_minute_briefing_plan.md` | T-032 assignment |
| Football Data Scientist | Queued | Review model/provenance wording and forecast fallbacks | T-026 assignment |
| Frontend Engineer | Queued | Plan incomplete-data states and multi-word team UI fixes | T-027/T-028 assignment |

## Phase 5 Objective

Bring the operating framework back in sync with the actual React/FastAPI project,
then harden the static-data pipeline before adding new features.

This phase exists because the application evolved faster than its charter,
agent roster, data contracts, task list, and deployment runbook.

## Phase 5 Exit Criteria

- [x] `PROJECT_CHARTER.md` reflects React/FastAPI as the canonical runtime and
  Streamlit as legacy/reference.
- [x] `AGENTS.md` maps each agent to current responsibilities.
- [x] `TASKS.md` contains actionable queued work by owner.
- [x] `STATUS.md` separates current local state from live/deployment caveats.
- [x] `docs/DEVELOPER_PLAYBOOK.md` describes current local, Cloud Run, and
  `accionar.xyz` workflows.
- [x] A rebaseline decision exists in `docs/decisions/`.
- [x] Active data contracts are documented for:
  - `summary.json`
  - `metrics.json`
  - `grid_state.json`
  - `/api/schedule`
  - `/api/match/{id}/summary`
  - `/api/match/{id}/metrics`
- [x] All 19 active match folders are audited for missing fields, empty metrics,
  default forecasts, and source provenance.
- [x] Legacy folders `1001`, `1002`, and `1003` are classified.
- [x] Last-minute briefing generation has a documented safety plan before
  implementation.
- [ ] Team alias and multi-word country handling are tracked as implementation
  tasks.
- [x] Local verification passes:
  `python3 -m compileall -q src && npm --prefix src/frontend run build`.

## Completed Batch - Batch 1: Framework Rebaseline

Owner: Orchestrator

Scope:

- Refresh `PROJECT_CHARTER.md`.
- Refresh `AGENTS.md`.
- Refresh this phase plan.
- Rebuild `TASKS.md` around real current deficiencies.
- Add a current `STATUS.md` entry.
- Refresh `docs/DEVELOPER_PLAYBOOK.md`.
- Refresh `README.md` and `docs/domain/README.md`.
- Add `docs/decisions/20260617_DEC007_framework_rebaseline.md`.

Exit criteria:

- [x] Framework docs no longer describe Streamlit as the active app.
- [x] The backlog has clear owners and verification notes.
- [x] Later batches can start without re-auditing the planning system.

## Completed Batch - Batch 2: Data Contract Audit

Owners: QA / Reproducibility Engineer, Data Pipeline Engineer

Scope:

- Document active JSON/API payload contracts.
- Audit all 19 active fixtures.
- Classify legacy numeric folders.
- Route missing/default/fallback fields to follow-up tasks.

Output:

- `docs/data_contracts.md`
- `docs/handoffs/2026-06-17_qa_data_contract_audit.md`

Exit criteria:

- [x] Active JSON/API payload contracts are documented.
- [x] All 19 active fixtures are audited.
- [x] Legacy numeric folders are classified.
- [x] Missing/default/fallback fields are routed to follow-up tasks.

## Completed Batch - Batch 3: Last-Minute Briefing Generation Plan

Owner: Data Pipeline Engineer

Scope:

- Re-scope T-025 from broad preview regeneration into safe last-minute match
  briefing generation.
- Keep `summary.json` as baseline curated preview content.
- Define separate planned `briefing.json` artifacts for matchday updates.
- Define dry-run/write safety rules, freshness states, source labels, review
  gates, and validation requirements.

Output:

- `docs/last_minute_briefing_plan.md`
- `docs/handoffs/2026-06-17_data_pipeline_t025_briefing_plan.md`

Exit criteria:

- [x] `summary.json` and `metrics.json` are protected from briefing generation.
- [x] Planned `briefing.json` contract is documented.
- [x] Fresh, stale, baseline-only, and blocked states are defined.
- [x] Dry-run/write behavior and validation output are specified.
- [x] Implementation is routed to T-032 and API/UI consumption to T-033.

## Next Batch - Batch 4: Model & Provenance Review

Owner: Football Data Scientist

Start condition:

- T-025 briefing plan complete.

Exit criteria:

- Dixon-Coles/Elo methodology note is current.
- Default forecast behavior is explicitly labeled.
- Deterministic progression wording is resolved.
- Briefing review rules are compatible with model/source truth.

## Later Planned Batches

### Batch 5 - Last-Minute Briefing Pipeline Implementation

Owner: Data Pipeline Engineer

Outputs:

- `generate_match_briefings.py`.
- `briefing.json` schema validation.
- Dry-run manifest and explicit write mode.
- Active-date / next-24-hour generation controls.

### Batch 6 - Frontend/API Robustness

Owners: Frontend Engineer, Data Pipeline Engineer

Outputs:

- Central team metadata/alias contract.
- Multi-word team route and UI fixes.
- Incomplete-data rendering states.
- Briefing API and Match Analysis freshness states.
- Overview source/date handling.

### Batch 7 - Deployment & Ops Runbook

Owners: Orchestrator, QA / Reproducibility Engineer

Outputs:

- Current deploy and rollback runbook.
- Local versus live status checklist.
- Cloud Run and `accionar.xyz` verification steps.

### Deferred - Streamlit Legacy Disposition

Owner: Orchestrator

Outputs:

- Decide whether `src/app/` remains reference code, is archived, or is deleted.

## Recent Decisions

| Date | Decision | File |
|---|---|---|
| 2026-06-14 | Project initialized from AI Workflow Framework | docs/decisions/20260614_DEC001_charter_v1.md |
| 2026-06-15 | Standings Corrections, Dynamic Bracket, and Previews Automation | docs/decisions/20260615_DEC002_deployment_and_previews.md |
| 2026-06-16 | Dismissed Phase 3 Standings Sync & Restricted Match Previews to Active Date | docs/decisions/20260616_DEC003_dismiss_phase3_and_limit_previews.md |
| 2026-06-16 | Archived Stale Team Tab, Implemented Researched Previews & Spanish Translation | docs/decisions/20260616_DEC004_archive_team_tab_and_customize_insights.md |
| 2026-06-16 | Decoupled React & FastAPI Migration with Interactive Visualizations | docs/decisions/20260616_DEC005_decoupled_react_migration.md |
| 2026-06-16 | Interactive Analytics Sprint (Elo / Monte Carlo Projections & xG Momentum) | docs/decisions/20260616_DEC006_interactive_analytics_sprint.md |
| 2026-06-17 | Framework Rebaseline & Pipeline Hardening | docs/decisions/20260617_DEC007_framework_rebaseline.md |
| 2026-06-17 | Separate Baseline Previews from Last-Minute Match Briefings | docs/decisions/20260617_DEC008_last_minute_briefing_scope.md |

## Open Blockers

- No blocking external dependency for the completed T-024 audit.
- BigQuery credential-dependent visualization tests remain out of local scope
  until QA/deployment verification.
