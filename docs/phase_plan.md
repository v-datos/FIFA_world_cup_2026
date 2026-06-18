# Phase Plan - FIFA World Cup 2026 Dashboard

Last updated: 2026-06-18
Current phase: Phase 5 - Framework Rebaseline & Pipeline Hardening

## Active Agents

| Agent | Status | Current task | Blocking on |
|---|---|---|---|
| Orchestrator | Routing | T-028 complete; assign T-034 next | None |
| QA / Reproducibility Engineer | Complete | Data contract audit delivered in `docs/data_contracts.md` | None |
| Data Pipeline Engineer | Queued | Active fixture discovery, source-backed research collector, real simulation support | None for T-034 start |
| Football Data Scientist | Complete | T-026 model/provenance review delivered in `docs/model_provenance.md` | None |
| Frontend Engineer | Queued | Real Monte Carlo UI and later source-backed metric states | T-037 assignment |

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
- [x] Model/provenance truth is documented for Dixon-Coles, Elo defaults,
  default forecasts, deterministic progression, and proxy/hardcoded data.
- [x] Team alias and multi-word country handling are implemented through T-027.
- [x] Default forecasts and missing metrics render with explicit fallback states
  through T-028.
- [x] AI research source policy is approved before web scraping, browser
  automation, or source-backed matchday collection is implemented.
- [ ] Real Monte Carlo simulation replaces the deterministic progression curve.
- [ ] Source-backed Squad & Style metrics can replace hardcoded/empty fields.
- [ ] Active fixture discovery and baseline stub generation are implemented so
  new tournament games can enter the Match Analysis workflow.
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

## Completed Batch - Batch 4: Model & Provenance Review

Owner: Football Data Scientist

Scope:

- Document the actual Dixon-Coles/Elo formula and model caveats.
- Document local Elo defaults and default `40/30/30` forecast behavior.
- Classify deterministic progression projections.
- Classify hardcoded rosters, static team metrics, and StatsBomb/BigQuery
  historical proxies.
- Define source/provenance labels for future UI/API/JSON work.
- Route AI web research and browser automation decisions to a source-policy task
  instead of assuming them.

Output:

- `docs/model_provenance.md`
- `docs/handoffs/2026-06-18_football_data_scientist_t026_model_provenance.md`
- `docs/decisions/20260618_DEC010_model_provenance_truth_labels.md`

Exit criteria:

- [x] Dixon-Coles/Elo methodology note is current.
- [x] Default forecast behavior is explicitly labeled.
- [x] Deterministic progression wording is classified as not Monte Carlo.
- [x] Briefing review rules are compatible with model/source truth.
- [x] Web-research implementation choices are routed to T-035.

## Completed Batch - Batch 5: AI Research Source Policy & Intake Architecture

Owners: Orchestrator, Football Data Scientist, Data Pipeline Engineer

Scope:

- Capture user decisions after T-026.
- Research and shortlist source options for ratings, Squad & Style metrics,
  lineups, injuries, rosters, and tactical news.
- Approve browser automation and scraping with source metadata retained.
- Define the 3-hour `jornada` freshness window.
- Route implementation to collector, real simulation, UI states, and Squad &
  Style integration tasks.

Outputs:

- `docs/ai_research_source_policy.md`
- `docs/handoffs/2026-06-18_orchestrator_t035_ai_research_source_policy.md`
- `docs/decisions/20260618_DEC011_ai_research_source_policy.md`

Exit criteria:

- [x] The project knows which sources can be collected.
- [x] Browser automation and scraping are approved with guardrails.
- [x] The project knows that individual AI claims do not need one-to-one
  URL-backed UI citations, while collection runs retain source metadata.
- [x] Data Pipeline Engineer can implement T-036 without source-policy ambiguity.
- [x] Real Monte Carlo is routed to T-037.
- [x] Source-backed Squad & Style metrics are routed to T-038.

## Next Batch - Batch 6: Team Identity, Unavailable Forecasts, and Real Simulation Foundation

Owners: Data Pipeline Engineer, Frontend Engineer, Football Data Scientist

Start condition:

- T-035 source policy complete.

Outputs:

- T-027 centralized team identity contract. Complete 2026-06-18.
- T-028 UI/API states for "forecast unavailable" and missing Squad & Style
  fields. Complete 2026-06-18.
- T-037 implementation plan or first slice for real Monte Carlo simulation.
- T-039 no-cost source spike before paid provider integration.

Exit criteria:

- [x] Default `40/30/30` no longer renders as authoritative probability.
- [x] Team IDs and aliases are safe enough for source-backed collectors.
- [ ] Real Monte Carlo implementation path is unblocked.
- [ ] Free-source feasibility is known before T-038 relies on paid APIs.

## Later Planned Batches

### Batch 7 - Active Fixture Discovery & Baseline Stub Generation

Owner: Data Pipeline Engineer

Outputs:

- `discover_active_fixtures.py` or equivalent pipeline entrypoint.
- Dry-run manifest for active-date / next-24-hour fixture discovery.
- Missing-folder baseline stub generation for `summary.json` and
  `metrics.json`.
- No-overwrite validation for existing curated folders.

### Batch 8 - Source-Backed Research Collector Prototype

Owner: Data Pipeline Engineer

Outputs:

- T-036 dry-run collector for one fixture.
- Source records from the approved stack.
- Proposed `briefing.json` or research-cache output.
- No writes to `summary.json`.

### Batch 9 - Source-Backed Squad & Style Integration

Owners: Data Pipeline Engineer, Football Data Scientist, Frontend Engineer

Outputs:

- T-039 no-cost source feasibility report.
- T-038 field-source mapping implemented for at least one fixture.
- Missing/approximate states for unsupported PPDA, field tilt, or xG fields.
- Frontend display of sourced, missing, or approximate metric states.

### Batch 10 - Last-Minute Briefing Pipeline Implementation

Owner: Data Pipeline Engineer

Outputs:

- `generate_match_briefings.py`.
- `briefing.json` schema validation.
- Dry-run manifest and explicit write mode.
- Active-date / next-24-hour generation controls.

### Batch 11 - Frontend/API Robustness

Owners: Frontend Engineer, Data Pipeline Engineer

Outputs:

- Central team metadata/alias contract.
- Multi-word team route and UI fixes.
- Incomplete-data rendering states.
- Briefing API and Match Analysis freshness states.
- Overview source/date handling.

### Batch 12 - Deployment & Ops Runbook

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
| 2026-06-17 | Add Active Fixture Discovery and Baseline Stubs | docs/decisions/20260617_DEC009_active_fixture_discovery_stubs.md |
| 2026-06-18 | Adopt Model and Provenance Truth Labels | docs/decisions/20260618_DEC010_model_provenance_truth_labels.md |
| 2026-06-18 | Approve AI Research Source Policy | docs/decisions/20260618_DEC011_ai_research_source_policy.md |
| 2026-06-18 | Adopt Shared Team Identity Contract | docs/decisions/20260618_DEC012_team_identity_contract.md |
| 2026-06-18 | Render Fallback and Missing Data as Unavailable | docs/decisions/20260618_DEC013_fallback_rendering_contract.md |

## Open Blockers

- No blocking external dependency for the completed T-024 audit.
- BigQuery credential-dependent visualization tests remain out of local scope
  until QA/deployment verification.
