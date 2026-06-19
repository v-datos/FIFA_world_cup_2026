# TASKS

Last updated: 2026-06-19
Current phase: Phase 5 - Framework Rebaseline & Pipeline Hardening

## In Progress

- No tasks currently in progress.

## Queued

- [ ] **T-038 - Source-Backed Squad & Style Metrics Integration**
  Owner: Data Pipeline Engineer / Football Data Scientist / Frontend Engineer
  Phase: Phase 5
  Notes: Replace empty/hardcoded Squad & Style values with sourced metrics where
  provider coverage allows. Start with the no-cost path from T-039, use
  Transfermarkt for squad value, FIFA/provider squads for average age,
  Sportmonks/API-Football for match/team stats if needed, and paid event-level
  data for true PPDA/field tilt if available. Unsupported fields must render
  unavailable or explicitly approximate; do not invent values.
  Verify: For one fixture, every displayed Squad & Style metric has source,
  status, checked time, and missing/approximate handling.

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
  active fixtures. The current empty/default set includes the T-034 baseline
  stub `brazil_haiti_2026` plus
  `canada_qatar_2026`, `czech_republic_south_africa_2026`,
  `mexico_south_korea_2026`, `scotland_morocco_2026`,
  `switzerland_bosnia_and_herzegovina_2026`, `turkey_paraguay_2026`,
  `united_states_australia_2026`, and `uzbekistan_colombia_2026`. The default
  40/30/30 forecast applies to all of those except
  `switzerland_bosnia_and_herzegovina_2026`. T-026 completed the truth review;
  T-039 now supplies runtime World Football Elo ratings from an auditable cache.
  Replacing remaining team metric values should follow T-035 policy and T-038,
  while explicit fallback labeling is now handled by T-028.

- [ ] **T-033 - Briefing API and Match Analysis Freshness UI**
  Owner: Data Pipeline Engineer / Frontend Engineer
  Notes: Add `/api/match/{match_id}/briefing` and render briefing freshness in
  Match Analysis. T-028 already exposes baseline-only status through the summary
  payload; T-033 should add the dedicated briefing route and full freshness UI.
  Verify: Fresh, stale, baseline-only, and blocked briefing states are visible
  and do not mask static baseline preview content.

## Done

- [x] **T-041 - Documentation Clutter Audit and Current-State Alignment**
  Owner: Orchestrator
  Completed: 2026-06-19
  Notes: Added `docs/documentation_clutter_audit.md` as the current
  documentation map, added DEC018 retention rules, marked `PROJECT_CONTEXT.md`
  as initial context only, corrected stale README/playbook/data-contract
  routing, and refreshed current-facing governance docs. No historical decision
  or handoff files were deleted; they remain append-only audit records.
  Verify: `git diff --check`; `python3 -m compileall -q src`;
  `npm --prefix src/frontend run build`.
  Handoff: docs/handoffs/2026-06-19_orchestrator_t041_documentation_clutter_audit.md

- [x] **T-039 - No-Cost Football Data Source Spike**
  Owner: Data Pipeline Engineer / Football Data Scientist
  Completed: 2026-06-19
  Notes: Added a no-cost national-team rating source path using World Football
  Elo TSV data as the primary source and FIFA/Coca-Cola Men's World Ranking
  metadata as the official sanity check. The T-039 collector writes an audited
  cache at `data/source_cache/world_football_elo/latest_ratings.json`, raw TSV
  snapshots under `data/source_cache/world_football_elo/raw/`, and a spike
  report at `docs/source_spikes/t039_no_cost_rating_sources.md`. Runtime Elo
  calls now read the World Football Elo cache first and fall back to local
  references only when the cache is unavailable; Monte Carlo/API data-quality
  metadata now exposes `web_researched` rating provenance when the cache is
  present. The live T-039 run parsed 244 ratings and covered 48/48 tournament
  teams.
  Verify: `python3 src/pipeline/collect_rating_sources.py --write`;
  `python3 -m compileall -q src`; `npm --prefix src/frontend run build`.
  Handoff: docs/handoffs/2026-06-19_data_pipeline_football_data_scientist_t039_no_cost_sources.md

- [x] **T-037 - Real Monte Carlo Tournament Simulation**
  Owner: Data Pipeline Engineer / Frontend Engineer
  Completed: 2026-06-18
  Notes: Replaced the active FastAPI deterministic progression curve with
  `src/analytics/monte_carlo_simulation.py`, a seeded random-trial tournament
  simulation that starts from `data/bracket/grid_state.json` plus the
  live/cached fixture list, simulates group advancement into the existing
  Round-of-32 bracket, and returns `group_advancement`, `r32`, `r16`, `qf`,
  `sf`, `final`, and `win` probabilities. `/api/match/{match_id}/metrics`
  defaults to 10,000 trials, accepts `simulation_count` and `seed`, exposes
  `monte_carlo_metadata`, and at T-037 closeout labeled rating inputs as
  `hardcoded_reference`; T-039 later superseded that rating source caveat with
  the World Football Elo cache.
  Verify: `python3 -m compileall -q src`; `npm --prefix src/frontend run build`.
  Handoff: docs/handoffs/2026-06-18_data_pipeline_t037_monte_carlo.md

- [x] **T-036 - Source-Backed Research Collector Prototype**
  Owner: Data Pipeline Engineer / Football Data Scientist
  Completed: 2026-06-18
  Notes: Added `src/pipeline/collect_match_research.py` for one-fixture
  source-backed research collection. It defaults to dry-run, supports explicit
  `--write`, accepts offline HTML/text/JSON sources and optional public URLs,
  normalizes fixture teams through T-027 identity helpers, retains auditable
  source records and draft claim records, and writes only
  `data/matches/{match_id}/research_cache.json` by default. Production
  `summary.json`, `metrics.json`, and `briefing.json` are forbidden write
  targets.
  Handoff: docs/handoffs/2026-06-18_data_pipeline_t036_research_collector.md

- [x] **T-032 - Last-Minute Briefing Pipeline Implementation**
  Owner: Data Pipeline Engineer / QA / Reproducibility Engineer
  Completed: 2026-06-18
  Notes: Added `src/pipeline/generate_match_briefings.py` as a separate
  `briefing.json` generator. It defaults to dry-run, requires explicit
  `--write`, supports `--window-hours`, `--match-id`, `--active-date`,
  `--force-refresh`, temp `--data-dir`, and QA `--now`, preserves existing
  fresh briefings unless forced, skips finished fixtures, and requires
  live/cache `source_status=not_finished` for in-scope generation. The manifest
  reports target paths, source status, freshness, validation, warnings,
  blocked reasons, and create/update/preserve/skip actions. T-032 intentionally
  does not perform web/news collection; T-036 later added the source-backed
  research-cache prototype.
  Handoff: docs/handoffs/2026-06-18_data_pipeline_t032_briefing_pipeline.md

- [x] **T-034 - Active Fixture Discovery and Baseline Stub Generation**
  Owner: Data Pipeline Engineer / QA / Reproducibility Engineer
  Completed: 2026-06-18
  Notes: Added `src/pipeline/discover_active_fixtures.py` with default dry-run,
  explicit `--write`, active-date, next-window, and match-id selection. The
  script fetches `worldcup26.ir/get/games`, falls back to `/tmp/games.json`,
  normalizes teams through T-027 identity helpers, emits a machine-readable
  manifest, skips unresolved knockout placeholders, and never overwrites
  existing curated `summary.json` or `metrics.json` files. Ran write mode for
  `--active-date 2026-06-19`, creating only
  `data/matches/brazil_haiti_2026/summary.json` and `metrics.json` as
  `baseline_stub` payloads.
  Handoff: docs/handoffs/2026-06-18_data_pipeline_t034_active_fixture_discovery.md

- [x] **T-040 - Fixture Lifecycle Filter for Analysis and Briefing Scope**
  Owner: Data Pipeline Engineer / Frontend Engineer
  Completed: 2026-06-18
  Notes: Added lifecycle/source-status fields to `/api/schedule`, including
  `finished`, `today`, `upcoming`, `unresolved`, and `archived`; default
  selection now targets the current day's not-finished fixtures. Updated
  `discover_active_fixtures.py` to skip finished fixtures so downstream
  research does not waste time on completed games. Updated React Overview and
  Match Analysis to show only `lifecycle=today` fixtures by default; past games
  remain available through stored folders/API routes for historical use.
  Handoff: docs/handoffs/2026-06-18_data_pipeline_frontend_t040_fixture_lifecycle.md

- [x] **T-028 - Incomplete Data and Fallback UI/API States**
  Owner: Frontend Engineer / Data Pipeline Engineer
  Completed: 2026-06-18
  Notes: Added runtime `data_quality` labels to `/api/match/{id}/metrics` for
  default forecasts, score probabilities, team metrics, radar metrics, Elo
  references, deterministic progression estimates, and historical visualization
  proxies. Added `briefing_status` to `/api/match/{id}/summary` so missing
  `briefing.json` renders as `baseline_only`. Updated Match Analysis so default
  `40/30/30` forecasts render as "forecast unavailable," empty radar metrics do
  not draw neutral charts, Squad & Style shows unavailable/missing states, and
  deterministic progression is no longer labeled as true Monte Carlo.
  Handoff: docs/handoffs/2026-06-18_frontend_t028_fallback_states.md

- [x] **T-027 - Team Identity and Multi-Word Name Normalization**
  Owner: Data Pipeline Engineer / Frontend Engineer
  Completed: 2026-06-18
  Notes: Added the canonical `data/reference/team_identity.json` contract plus
  Python and TypeScript helpers. Replaced duplicated API/team-ID alias maps,
  unsafe FastAPI match-ID splitting, preview-generator slugging, React
  editorial key derivation, frontend flag lookup, and bracket fallback variants
  with shared identity normalization. All 20 active fixtures now resolve by
  match ID, display name, alias, and `ai_summary` slug.
  Contract: data/reference/team_identity.json
  Handoff: docs/handoffs/2026-06-18_data_pipeline_t027_team_identity.md

- [x] **T-035 - AI Research Source Policy and Data Intake Architecture**
  Owner: Orchestrator / Football Data Scientist / Data Pipeline Engineer
  Completed: 2026-06-18
  Notes: Added `docs/ai_research_source_policy.md`, DEC011, and a handoff. The
  policy accepts browser automation/scraping, sets the last-minute window to 3
  hours before the day's first match, requires default forecasts to render as
  unavailable, selects World Football Elo/FIFA/Sportmonks/API-Football/
  Transfermarkt as the first implementation stack, routes real Monte Carlo to
  T-037, routes Squad & Style sourcing to T-038, and adds T-039 for the no-cost
  football-data spike.
  Plan: docs/ai_research_source_policy.md
  Handoff: docs/handoffs/2026-06-18_orchestrator_t035_ai_research_source_policy.md

- [x] **T-026 - Model and Provenance Truth Review**
  Owner: Football Data Scientist
  Completed: 2026-06-18
  Notes: Added `docs/model_provenance.md`, a Football Data Scientist handoff,
  and DEC010. The review documents the Dixon-Coles/Elo formula, local Elo
  defaults, default `40/30/30` forecast behavior, frontend fallback behavior,
  deterministic progression projection, BigQuery/StatsBomb proxy limits, and
  source/provenance taxonomy. It routes web scraping/browser automation and
  AI-researched Match Analysis population to T-035 because those require user
  policy decisions.
  Plan: docs/model_provenance.md
  Handoff: docs/handoffs/2026-06-18_football_data_scientist_t026_model_provenance.md

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
  augmentation, visualization payloads, the original 19 active fixture
  statuses, and the legacy numeric folders `1001`, `1002`, and `1003`. T-034
  later added the `brazil_haiti_2026` baseline stub addendum.
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
