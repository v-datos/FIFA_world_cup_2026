# TASKS

Last updated: 2026-06-17
Current phase: Phase 5 - Framework Rebaseline & Pipeline Hardening

## In Progress

- No tasks currently in progress.

## Queued

- [ ] **T-026 - Model and Provenance Truth Review**
  Owner: Football Data Scientist
  Phase: Phase 5
  Notes: Document Dixon-Coles formula, Elo source, confidence formula, default
  forecast behavior, and runtime projection logic. Decide whether current
  "Monte Carlo" wording should be renamed or replaced with an actual simulation.
  Verify: UI/docs wording matches implementation and fallback states are
  explicitly named.

- [ ] **T-027 - Team Identity and Multi-Word Name Normalization Plan**
  Owner: Data Pipeline Engineer / Frontend Engineer
  Phase: Phase 5
  Notes: Centralize team aliases/display names and fix fragile parsing across
  `generate_match_previews.py`, FastAPI routes, React components, flags, rosters,
  and JSON keys. Known risk: multi-word teams such as `United States`,
  `South Korea`, `Bosnia and Herzegovina`, and
  `Democratic Republic of the Congo`. T-024 confirmed the React editorial lookup
  currently misses the two longest summary keys:
  `democratic_republic_of_the_congo` and `bosnia_and_herzegovina`.
  Verify: All 19 active fixtures can be resolved by ID and display name without
  first-space-only replacement or positional string splitting.

- [ ] **T-028 - Incomplete Data and Fallback UI/API States**
  Owner: Frontend Engineer / Data Pipeline Engineer
  Phase: Phase 5
  Notes: Prevent empty `team_metrics` or default forecasts from rendering as
  misleading neutral charts. Add explicit degraded states and API/source labels
  for fallback/proxy/static data. Include briefing freshness states:
  fresh, stale, baseline-only, and blocked.
  Verify: Fixtures with empty metrics and default forecasts render visibly as
  incomplete/fallback, not as authoritative model output.

- [ ] **T-034 - Active Fixture Discovery and Baseline Stub Generation**
  Owner: Data Pipeline Engineer / QA / Reproducibility Engineer
  Phase: Phase 5
  Notes: Build the procedure in `docs/active_fixture_discovery_plan.md`:
  discover active-date or next-24-hour fixtures from `worldcup26.ir/get/games`,
  fall back to `/tmp/games.json`, and create missing
  `data/matches/{match_id}/summary.json` and `metrics.json` baseline stubs only
  with explicit `--write`. Existing curated folders must not be overwritten.
  This should run before T-032. Hard dependency: T-027 team identity rules.
  Public UI gate: T-028 fallback/incomplete states.
  Verify: Dry-run writes nothing; write mode creates only missing baseline
  folders; stubs are labeled `baseline_stub`; existing 19 folders are unchanged.

- [ ] **T-029 - Deployment and Operations Runbook Refresh**
  Owner: Orchestrator / QA / Reproducibility Engineer
  Phase: Phase 5
  Notes: Update Cloud Run and `accionar.xyz` procedures for the current
  React/FastAPI architecture. Separate local verification from live deployment
  verification and document rollback/status snapshot steps.
  Verify: One current runbook covers local build, container deploy, live smoke
  checks, and remote/static asset status.

## Backlog

- [ ] **T-019 - Player Career-Stats Hover Endpoint (`/api/player/stats`)**
  Owner: Data Pipeline Engineer / Football Data Scientist
  Notes: Deferred 2026-06-16 (DEC006). `InteractivePitch` already fetches
  per-player career stats on hover, but neither the route nor a backing BigQuery
  query exists. Requires data-model decisions (dataset/competition scope,
  2026 roster to StatsBomb `player` name mapping) and cannot be runtime-verified
  locally without GCP credentials.

- [ ] **T-030 - Streamlit Legacy Disposition**
  Owner: Orchestrator
  Notes: Decide whether `src/app/` remains reference code, is archived, or is
  deleted after React/FastAPI live deployment is verified.

- [ ] **T-031 - Active Match Metrics Completion**
  Owner: Data Pipeline Engineer / Football Data Scientist
  Notes: Fill or explicitly mark missing `team_metrics` and Elo entries for
  active fixtures. T-024 identified empty team profiles for
  `canada_qatar_2026`, `czech_republic_south_africa_2026`,
  `mexico_south_korea_2026`, `scotland_morocco_2026`,
  `switzerland_bosnia_and_herzegovina_2026`, `turkey_paraguay_2026`,
  `united_states_australia_2026`, and `uzbekistan_colombia_2026`. It also
  identified default 40/30/30 forecasts for all of those except
  `switzerland_bosnia_and_herzegovina_2026`. This depends on T-026.

- [ ] **T-032 - Last-Minute Briefing Pipeline Implementation**
  Owner: Data Pipeline Engineer
  Notes: Implement the T-025 plan by creating a separate
  `generate_match_briefings.py` flow that writes only
  `data/matches/{match_id}/briefing.json`. Default to dry-run, require
  explicit `--write`, support `--window-hours` and `--match-id`, preserve
  existing fresh briefings unless forced, and emit machine-readable validation
  for source freshness, empty metrics, and default forecasts. Depends on T-034
  so every in-scope fixture has a baseline folder.
  Verify: Dry-run writes nothing; write mode creates/updates only
  `briefing.json`; `summary.json` and `metrics.json` stay unchanged.

- [ ] **T-033 - Briefing API and Match Analysis Freshness UI**
  Owner: Data Pipeline Engineer / Frontend Engineer
  Notes: Add `/api/match/{match_id}/briefing` and render briefing freshness in
  Match Analysis. Missing briefing data should return/render a baseline-only
  state instead of failing the tab.
  Verify: Fresh, stale, baseline-only, and blocked briefing states are visible
  and do not mask static baseline preview content.

## Done

- [x] **T-025 - Safe Last-Minute Match Briefing Generation Plan**
  Owner: Data Pipeline Engineer
  Completed: 2026-06-17
  Notes: Re-scoped the old safe preview generation task into a separate
  last-minute briefing generation plan. The plan keeps `summary.json` as the
  baseline preview, adds planned `briefing.json` artifacts for matchday updates,
  defines freshness/source states, and requires dry-run/write safety.
  Plan: docs/last_minute_briefing_plan.md
  Handoff: docs/handoffs/2026-06-17_data_pipeline_t025_briefing_plan.md

- [x] **T-024 - Data Contract Audit for Active JSON and API Payloads**
  Owner: QA / Reproducibility Engineer / Data Pipeline Engineer
  Completed: 2026-06-17
  Notes: Added `docs/data_contracts.md` documenting `summary.json`,
  `metrics.json`, `grid_state.json`, `/api/schedule`,
  `/api/match/{id}/summary`, `/api/match/{id}/metrics`, runtime metrics
  augmentation, visualization payloads, all 19 active fixture statuses, and
  the legacy numeric folders `1001`, `1002`, and `1003`.
  Handoff: docs/handoffs/2026-06-17_qa_data_contract_audit.md

- [x] **T-023 - Framework Rebaseline Batch 1**
  Owner: Orchestrator
  Completed: 2026-06-17
  Notes: Rewrote the operating charter around React/FastAPI, updated agent
  responsibilities, reactivated Phase 5 planning, rebuilt the task queue,
  refreshed status/playbook/README/domain docs, and added DEC007.

- [x] **T-022 - Match Analysis Deep Update, xG Distribution, Live Results Refresh**
  Owner: Frontend Engineer / Data Pipeline Engineer
  Completed: 2026-06-17
  Notes: Restructured Match Analysis; integrated top exact scores; fixed radar
  to read `team_metrics`; added Squad & Style Comparison, Monte Carlo
  Projections, tactics, and last-standing sections; replaced xG momentum with
  xG Distribution Comparison; fixed player tooltip; moved language toggle.

- [x] **T-021 - UI Polish: Bracket Fit-to-Screen, Flags, Today Selector, Sidebar/Ball Logo**
  Owner: Frontend Engineer
  Completed: 2026-06-16
  Notes: Bracket scales to fit viewport; Match Analysis selector filters to the
  current date; flags are centralized in `src/frontend/src/lib/teamData.ts`;
  sidebar was retitled and updated with the match-ball logo.

- [x] **T-020 - Bracket Wood-Board Port, Full-Screen & StatsBomb Viz Fixes**
  Owner: Frontend Engineer / Data Pipeline Engineer
  Completed: 2026-06-16
  Notes: React StandingsTab renders the full fallback bracket, supports
  full-screen, and StatsBomb visualizations were fixed for FastAPI worker use.

- [x] **T-018 - Interactive Analytics Sprint (Elo / Monte Carlo Projections & xG Momentum)**
  Owner: Football Data Scientist / Frontend Engineer
  Completed: 2026-06-16
  Notes: Added Elo and tournament-progression projections to metrics endpoint,
  wired visualization changes, restored frontend build, and deferred
  `/api/player/stats` as T-019.

- [x] **T-017 - Decoupled React Client & FastAPI REST Backend Migration**
  Owner: Frontend Engineer / Data Pipeline Engineer
  Completed: 2026-06-16

- [x] **T-016 - Curate High-Quality Tactical Previews & Archive team_tab.py**
  Owner: Football Data Scientist / Frontend Engineer
  Completed: 2026-06-16

- [x] **T-015 - Match Analysis Tab Spanish Translation Toggle**
  Owner: Frontend Engineer
  Completed: 2026-06-16

- [x] **T-014 - Portfolio Website Integration & Deploy**
  Owner: Frontend Engineer
  Completed: 2026-06-15

- [x] **T-013 - Live Standings, Dynamic Bracket, and AI Previews Automation**
  Owner: Football Data Scientist / Data Pipeline Engineer
  Completed: 2026-06-15

- [x] **T-012 - Player Clubs & International Standings Integration**
  Owner: Frontend Engineer
  Completed: 2026-06-15

- [x] **T-011 - Direct DOM Injection & Styling Refactoring**
  Owner: Frontend Engineer
  Completed: 2026-06-15

- [x] **T-010 - Bespoke Tactical Visualizations Integration**
  Owner: Frontend Engineer
  Completed: 2026-06-14

- [x] **T-009 - Consolidated Match Analysis & Player Crosswalk selectors**
  Owner: Frontend Engineer
  Completed: 2026-06-14

- [x] **T-000 - Bootstrap project from framework**
  Owner: Orchestrator
  Completed: 2026-06-14
  Handoff: docs/handoffs/2026-06-14_orchestrator.md

- [x] **T-001 - Customize charter and agent roster**
  Owner: Orchestrator
  Completed: 2026-06-14

- [x] **T-002 - Define first producer deliverable**
  Owner: Orchestrator
  Completed: 2026-06-14

- [x] **T-003 - Replace generic data contracts with project-specific contracts**
  Owner: QA / Reproducibility Engineer
  Completed: 2026-06-14

- [x] **T-004 - Symmetrical World Cup 2026 Bracket UI**
  Owner: Frontend Engineer
  Completed: 2026-06-14

- [x] **T-005 - Dixon-Coles Forecasting & NLP AI Summary Integration**
  Owner: Football Data Scientist
  Completed: 2026-06-14

- [x] **T-006 - Tableless HTML/CSS visual redesign**
  Owner: Frontend Engineer
  Completed: 2026-06-14

- [x] **T-007 - Comparative Team Analysis mode**
  Owner: Frontend Engineer
  Completed: 2026-06-14

## Cancelled

- [-] **T-008 - PostgreSQL Live Standings Ingestion Sync**
  Phase: Phase 3
  Owner: Data Pipeline Engineer
  Cancelled: 2026-06-16
  Notes: Local fallback and direct API polling satisfy current requirements;
  PostgreSQL standings sync was dismissed in DEC003.

## Blockers

- No blockers currently filed for Phase 5.
