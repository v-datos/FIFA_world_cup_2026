# Phase Plan - FIFA World Cup 2026 Dashboard

Last updated: 2026-06-19
Current phase: Phase 5 - Framework Rebaseline & Pipeline Hardening

## Active Agents

| Agent | Status | Current task | Blocking on |
|---|---|---|---|
| Orchestrator | Routing | T-038 complete; route T-029 next | None |
| QA / Reproducibility Engineer | Complete | Data contract audit delivered in `docs/data_contracts.md` | None |
| Data Pipeline Engineer | Complete | T-038 source-backed Squad & Style integration delivered | None |
| Football Data Scientist | Complete | T-039 no-cost source methodology delivered | None |
| Frontend Engineer | Complete | T-038 field-level Squad & Style states delivered | None |

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
- [x] All 20 active match folders are audited for missing fields, empty metrics,
  default forecasts, and source provenance.
- [x] Legacy folders `1001`, `1002`, and `1003` are classified.
- [x] Last-minute briefing generation has a documented safety plan before
  implementation.
- [x] Model/provenance truth is documented for Dixon-Coles, Elo defaults,
  default forecasts, seeded progression simulation, and proxy/hardcoded data.
- [x] Team alias and multi-word country handling are implemented through T-027.
- [x] Default forecasts and missing metrics render with explicit fallback states
  through T-028.
- [x] AI research source policy is approved before web scraping, browser
  automation, or source-backed matchday collection is implemented.
- [x] Real Monte Carlo simulation replaces the deterministic progression curve.
- [x] No-cost national-team rating source spike is complete and runtime ratings
  can use the World Football Elo cache.
- [ ] Source-backed Squad & Style metrics can replace hardcoded/empty fields.
- [x] Active fixture discovery and baseline stub generation are implemented so
  new tournament games can enter the Match Analysis workflow.
- [x] Fixture lifecycle filtering excludes finished games from default
  last-minute analysis and briefing scope.
- [x] Last-minute `briefing.json` generation is implemented with dry-run/write
  safety and source-status validation.
- [x] Source-backed research collector prototype is implemented as a draft
  `research_cache.json` flow.
- [x] Documentation clutter audit identifies current docs, historical records,
  and initial-context files.
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
- Audit the original 19 active fixtures.
- Classify legacy numeric folders.
- Route missing/default/fallback fields to follow-up tasks.

Output:

- `docs/data_contracts.md`
- `docs/handoffs/2026-06-17_qa_data_contract_audit.md`

Exit criteria:

- [x] Active JSON/API payload contracts are documented.
- [x] The original 19 active fixtures are audited.
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

## Active Batch - Batch 6: Team Identity, Unavailable Forecasts, and Real Simulation Foundation

Owners: Data Pipeline Engineer, Frontend Engineer, Football Data Scientist

Start condition:

- T-035 source policy complete.

Outputs:

- T-027 centralized team identity contract. Complete 2026-06-18.
- T-028 UI/API states for "forecast unavailable" and missing Squad & Style
  fields. Complete 2026-06-18.
- T-037 real Monte Carlo simulation. Complete 2026-06-18.
- T-039 no-cost source spike before paid provider integration. Complete
  2026-06-19.

Exit criteria:

- [x] Default `40/30/30` no longer renders as authoritative probability.
- [x] Team IDs and aliases are safe enough for source-backed collectors.
- [x] Real Monte Carlo simulation is implemented for the active API/UI runtime.
- [x] Free-source feasibility is known before T-038 relies on paid APIs.
- [x] Runtime rating inputs can use source-backed World Football Elo cache
  values before falling back to local references.

## Completed Batch - Batch 10: No-Cost Rating Source Spike

Owners: Data Pipeline Engineer, Football Data Scientist

Scope:

- Evaluate the free/open-source path for replacing hardcoded national-team
  rating inputs.
- Use World Football Elo as the no-cost rating source when practical.
- Use FIFA/Coca-Cola Men's World Ranking as official metadata/fallback context.
- Reject ClubElo as the primary national-team rating source.
- Preserve source metadata, parser version, cache path, raw snapshots, and
  coverage results.

Outputs:

- `src/analytics/rating_sources.py`
- `src/pipeline/collect_rating_sources.py`
- `data/source_cache/world_football_elo/latest_ratings.json`
- `data/source_cache/world_football_elo/raw/World.tsv`
- `data/source_cache/world_football_elo/raw/en.teams.tsv`
- `docs/no_cost_football_data_source_spike.md`
- `docs/source_spikes/t039_no_cost_rating_sources.md`
- `docs/handoffs/2026-06-19_data_pipeline_football_data_scientist_t039_no_cost_sources.md`

Exit criteria:

- [x] World Football Elo source fetch succeeds and writes only with `--write`.
- [x] FIFA ranking page metadata is captured as official sanity-check context.
- [x] Current tournament coverage is documented; T-039 run covered 48/48 teams.
- [x] Runtime Elo and Monte Carlo metadata prefer source-backed cache values.
- [x] Local hardcoded ratings remain fallback only when cache values are absent.

## Completed Batch - Batch 14: Documentation Clutter Audit

Owner: Orchestrator

Scope:

- Audit current Markdown/agent docs for stale current-state claims.
- Separate current operating docs from historical decisions/handoffs.
- Mark initial setup context as background-only.
- Add durable retention rules for future documentation closeouts.

Outputs:

- `docs/documentation_clutter_audit.md`
- `docs/decisions/20260619_DEC018_documentation_clutter_map.md`
- `docs/handoffs/2026-06-19_orchestrator_t041_documentation_clutter_audit.md`

Exit criteria:

- [x] Current-facing stale claims found in README/playbook/contracts are fixed.
- [x] Historical decisions and handoffs are retained as append-only records.
- [x] Current-first reading order is documented.
- [x] Next project step remains T-038.

## Completed Batch - Batch 7: Active Fixture Discovery & Baseline Stub Generation

Owner: Data Pipeline Engineer

Scope:

- `discover_active_fixtures.py` or equivalent pipeline entrypoint.
- Dry-run manifest for active-date / next-24-hour fixture discovery.
- Missing-folder baseline stub generation for `summary.json` and
  `metrics.json`.
- No-overwrite validation for existing curated folders.

Outputs:

- `src/pipeline/discover_active_fixtures.py`
- `data/matches/brazil_haiti_2026/summary.json`
- `data/matches/brazil_haiti_2026/metrics.json`
- `docs/handoffs/2026-06-18_data_pipeline_t034_active_fixture_discovery.md`

Exit criteria:

- [x] Dry-run writes no fixture files.
- [x] Write mode creates only missing baseline files.
- [x] Existing curated folders are not overwritten.
- [x] Stub forecast and team metrics are labeled as fallback/incomplete.
- [x] `/api/schedule` sees the generated baseline folder.

## Completed Batch - Batch 8: Fixture Lifecycle Filter

Owners: Data Pipeline Engineer, Frontend Engineer

Scope:

- Add lifecycle/source-status fields to `/api/schedule`.
- Exclude finished fixtures from discovery/briefing scope.
- Remove hardcoded frontend date filtering.
- Show only current-day not-finished fixtures in Overview and Match Analysis.

Outputs:

- `/api/schedule` lifecycle contract.
- React day-view lifecycle filter.
- `docs/decisions/20260618_DEC014_fixture_lifecycle_filter.md`
- `docs/handoffs/2026-06-18_data_pipeline_frontend_t040_fixture_lifecycle.md`

Exit criteria:

- [x] Finished fixtures remain available as historical records.
- [x] Finished fixtures are excluded from default Match Analysis selection.
- [x] Discovery dry-run/write scope skips finished fixtures.
- [x] T-032 has a documented `source_status=not_finished` generation gate.

## Completed Batch - Batch 11: Last-Minute Briefing Pipeline Implementation

Owner: Data Pipeline Engineer

Scope:

- Add `generate_match_briefings.py`.
- Emit dry-run manifests by default.
- Write only `briefing.json` when `--write` is explicit.
- Preserve existing fresh briefings unless forced.
- Skip finished fixtures and require `source_status=not_finished`.
- Surface empty metrics/default forecasts as warnings and blocked reasons.

Outputs:

- `src/pipeline/generate_match_briefings.py`
- `/api/match/{id}/summary` compatibility for generated briefing freshness
- `docs/handoffs/2026-06-18_data_pipeline_t032_briefing_pipeline.md`

Exit criteria:

- [x] Dry-run writes no fixture files.
- [x] Temp write mode creates only `briefing.json`.
- [x] `summary.json` and `metrics.json` remain unchanged.
- [x] Finished fixtures return skipped rows.
- [x] Fresh existing briefings are preserved unless forced.

## Completed Batch - Batch 9: Source-Backed Research Collector Prototype

Owner: Data Pipeline Engineer

Scope:

- Add one-fixture source-backed research collector.
- Emit dry-run manifests by default.
- Write only `research_cache.json` when `--write` is explicit.
- Accept offline HTML/text/JSON source snapshots and public source URLs.
- Retain auditable source records and draft claim records.
- Embed a proposed briefing draft for review without mutating `briefing.json`.

Outputs:

- `src/pipeline/collect_match_research.py`
- `docs/handoffs/2026-06-18_data_pipeline_t036_research_collector.md`

Exit criteria:

- [x] Dry-run emits a valid research-cache manifest.
- [x] Temp write mode creates only `research_cache.json`.
- [x] `summary.json`, `metrics.json`, and `briefing.json` are protected.
- [x] Live URL failures become blocked source records instead of invented data.
- [x] Live URL success retains `web_researched` source metadata and draft claims.

## Completed Batch - Batch 13: Source-Backed Squad & Style Integration

Owners: Data Pipeline Engineer, Football Data Scientist, Frontend Engineer

Scope:

- T-038 field-source mapping implemented for at least one fixture.
- Missing/approximate states for unsupported PPDA, field tilt, or xG fields.
- Frontend display of sourced, missing, or approximate metric states.

Outputs:

- `docs/squad_style_source_methodology.md`
- `data/source_cache/squad_style/latest_metrics.json`
- `src/analytics/squad_style_sources.py`
- `src/pipeline/collect_squad_style_sources.py`
- `/api/match/{id}/metrics` field-level team metric provenance
- `docs/decisions/20260619_DEC019_squad_style_field_source_cache.md`
- `docs/handoffs/2026-06-19_data_pipeline_football_data_scientist_frontend_t038_squad_style.md`

Exit criteria:

- [x] Field-source mapping implemented for one not-finished fixture:
  `brazil_haiti_2026`.
- [x] Source-backed values are merged at runtime without overwriting
  `metrics.json`.
- [x] Unsupported and absent fields remain missing instead of invented.
- [x] Existing unsourced local profiles are labeled `hardcoded_reference`.
- [x] Squad & Style UI renders per-value provenance states.

## Later Planned Batches

### Batch 12 - Frontend/API Robustness

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
| 2026-06-18 | Add Fixture Lifecycle Filter for Last-Minute Analysis | docs/decisions/20260618_DEC014_fixture_lifecycle_filter.md |
| 2026-06-18 | Adopt Task Completion Commit and Push Closeout | docs/decisions/20260618_DEC015_task_completion_closeout.md |
| 2026-06-18 | Seeded Monte Carlo Tournament Simulation | docs/decisions/20260618_DEC016_real_monte_carlo_simulation.md |
| 2026-06-19 | Adopt World Football Elo Cache as No-Cost Rating Source | docs/decisions/20260619_DEC017_no_cost_rating_source_cache.md |
| 2026-06-19 | Documentation Clutter Map and Retention Rules | docs/decisions/20260619_DEC018_documentation_clutter_map.md |
| 2026-06-19 | Squad & Style Field Source Cache | docs/decisions/20260619_DEC019_squad_style_field_source_cache.md |

## Open Blockers

- No blocking external dependency for the completed T-024 audit.
- BigQuery credential-dependent visualization tests remain out of local scope
  until QA/deployment verification.
