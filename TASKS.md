# TASKS

Last updated: 2026-06-20
Current phase: Phase 5 - Framework Rebaseline & Pipeline Hardening

## In Progress

- No tasks currently in progress.

## Queued

- No tasks currently queued.

## Backlog

- [ ] **T-019 - Player Career-Stats Hover Endpoint (`/api/player/stats`)**
  Owner: Data Pipeline Engineer / Football Data Scientist
  Notes: Deferred 2026-06-16 (DEC006). `InteractivePitch` already fetches
  per-player career stats on hover, but neither the route nor a backing BigQuery
  query exists. Requires data-model decisions (dataset/competition scope,
  2026 roster to StatsBomb `player` name mapping) and cannot be runtime-verified
  locally without GCP credentials.

## Done

- [x] **T-030 - Streamlit Legacy Disposition**
  Owner: Orchestrator
  Completed: 2026-06-20
  Notes: Stopped the running Streamlit server process locally (PID 31437) as the React/FastAPI app is now fully verified and production-ready. The legacy Streamlit code in `src/app/` will be kept on disk strictly as reference/archive material and is no longer an active runtime target.
  Verify: Verify no python process runs the streamlit app in the background (`ps aux | grep streamlit`).

- [x] **T-043 - Schedule Fallback Match IDs When Live API Is Unavailable**
  Owner: Data Pipeline Engineer / Frontend Engineer
  Completed: 2026-06-20
  Notes: Resolved the schedule fallback gap. When `worldcup26.ir/get/games` is unreachable and `/tmp/games.json` is missing, `/api/schedule` now falls back to loading a committed games cache (`data/reference/games_cache.json`) or scanning local fixture folders to reconstruct match ID mappings and details. The day-view selector listing and match details now remain fully populated with correct IDs during Nestor API outages. Hardened data pipeline scripts (`discover_active_fixtures.py`, `generate_match_previews.py`) to use the committed fallback cache.
  Verify: Simulate API outage and cache absence; confirm non-null match IDs and `"cache"` / `"local_folders"` source in schedule payload; compile and build verification checks pass.

- [x] **T-049 - Align Standings & Bracket Tab UI with Streamlit Wood Board & Tape Layout**
  Owner: Frontend Engineer
  Completed: 2026-06-20
  Notes: Realigned the React standings and bracket tab visually to match the Streamlit wood board and painter's tape look. Restored individual tape rotations for the standings strips, set the Permanent Marker font on numbers (removing font-mono), removed matchup scores from tapes to maintain a clean layout, and set the board dimensions and vertical lines to match the original proportions.
  Verify: compile React app (`npm run build`), verify standings and bracket tree alignment visually in browser.

- [x] **T-048 - Overview Real Fixtures, Stadium Links, and Edmonton Time**
  Owner: Data Pipeline Engineer / Frontend Engineer
  Completed: 2026-06-20
  Notes: Added the day's real 2026 WC fixtures (Netherlands-Sweden,
  Germany-Ivory Coast, Ecuador-Curacao, Tunisia-Japan) as fixture folders with
  real venue and a `kickoff_utc` field. `/api/schedule` now passes
  `kickoff_utc`. Overview renders the venue as a Google Maps link and the
  kickoff in Edmonton (America/Edmonton, MT) via `Intl.DateTimeFormat`, falling
  back to the stored local string when no UTC kickoff exists. Historical
  placeholder venues ("Stadium N") are unchanged.
  Verify: in-process `/api/schedule` shows 4 today fixtures with venue +
  kickoff_utc; browser Overview shows Maps links and MT times (11:00/14:00/
  18:00/22:00 MT); `npm run build`.

- [x] **T-045 - Real Forecast + Source-Backed Squad & Style Values**
  Owner: Data Pipeline Engineer / Football Data Scientist
  Completed: 2026-06-20
  Notes: `/api/match/{id}/metrics` computes an Elo-derived Dixon-Coles forecast
  from the World Football Elo cache when the stored forecast is the 40/30/30
  stub (and syncs top-level `score_probabilities`), so Match Outcome Probability
  and Top Exact Scores render real model output labelled with rating provenance.
  Researched squad market values (8 current-fixture teams) and average ages were
  added to the squad/style source cache; advanced style metrics stay missing.
  Verify: in-process metrics smoke + browser preview.

- [x] **T-046 - Source-Backed Matchday Lineups**
  Owner: Data Pipeline Engineer / Frontend Engineer
  Completed: 2026-06-20
  Notes: Added `data/source_cache/lineups/latest.json` (formation, manager,
  philosophy, ordered XI, clubs per team). `get_match_summary` merges it into
  `confirmed_tactics` and adds slug-keyed `rosters` + `player_clubs`;
  `MatchAnalysisTab` prefers API rosters over the legacy hardcoded map and
  `InteractivePitch` takes a `playerClubs` prop. API-verified for all 8
  current-fixture teams.
  Verify: in-process `get_match_summary` rosters/tactics; `npm run build`.

- [x] **T-047 - Standings Refresh to Current Results**
  Owner: Data Pipeline Engineer
  Completed: 2026-06-20
  Notes: Refreshed `data/bracket/grid_state.json` group standings to the
  researched 2026-06-20 results (all 12 groups; 32 matches, 96 goals). Stale
  because worldcup26.ir is unreachable; the live auto-update path is unchanged
  and would resume when the API returns. T-043 (schedule fallback match IDs)
  remains the open robustness item.
  Verify: in-process `get_standings`; browser Standings tab.

- [x] **T-044 - Live Overview Tournament Stats**
  Owner: Data Pipeline Engineer / Frontend Engineer
  Completed: 2026-06-19
  Notes: The Overview tab's three stat cards (Matches Played, Total Goals, Top
  Scorers) were hardcoded constants frozen "as of June 17." Replaced them with
  live values from the same `/api/standings` source the bracket uses.
  `/api/standings` now returns a `tournament_stats` object: `matches_played`
  (`sum(p)//2`) and `total_goals` (`sum(gf)`) derived from the live group
  standings, plus `goals_per_game` and a curated `top_scorer` read from a new
  `grid_state.json` field (no live scorers feed exists, so it stays curated and
  surfaces through the same data path as the bracket). `OverviewTab` fetches
  `/api/standings` like `StandingsTab` and renders `—` fallbacks until loaded.
  Verify: in-process `/api/standings` returned
  `matches_played=20, total_goals=62, goals_per_game=3.1, top_scorer=L. Messi/3`;
  browser preview confirmed the cards render those values with no console errors;
  `python3 -m compileall -q src`; `npm --prefix src/frontend run build`.

- [x] **T-042 - Live Deployment Execution and Docker Build Fix**
  Owner: Orchestrator / Data Pipeline Engineer
  Completed: 2026-06-19
  Notes: Executed the deployment the T-029 runbook flagged as a separate task.
  Pre-flight found Cloud Run frozen at revision `fifa-2026-dashboard-00017-6z7`
  (2026-06-17), predating the T-027 identity contract (2026-06-18) -- the root
  cause of the live drift. The first `gcloud builds submit` failed at the Docker
  `frontend-builder` stage because `src/frontend/src/lib/teamIdentity.ts` imports
  the repo-canonical `data/reference/team_identity.json` via `../../../../`, a
  path the stage did not include, so `tsc` raised TS2307. The local `npm run
  build` gate did not catch it because it runs in the real repo layout. Fixed the
  Dockerfile to mirror the repo layout inside `frontend-builder` (DEC023). The
  rebuilt Cloud Build `88ef8a94` succeeded and deployed revision
  `fifa-2026-dashboard-00018-tm5` at 100% traffic. Cloud Run smoke verified live:
  20 fixtures with lifecycle fields, `brazil_haiti_2026` routes 200 (was 404),
  metrics expose `data_quality`, `world_football_elo` Monte Carlo ratings, and
  `web_researched` Brazil squad value. Two findings filed: schedule fallback gap
  (T-043) and an `accionar.xyz` browser-confirm follow-up. Deploy emitted a
  non-fatal IAM `setIamPolicy` warning; public access persists (unauth `/health`
  200).
  Verify: `gcloud builds submit --config cloudbuild.yaml .`; Cloud Run smoke per
  `docs/deployment_verification_checklist.md`; `git diff --check`.
  Decision: docs/decisions/20260619_DEC023_docker_frontend_data_context.md
  Handoff: docs/handoffs/2026-06-19_orchestrator_t042_live_deployment_execution.md

- [x] **T-031 - Active Match Metrics Completion**
  Owner: Data Pipeline Engineer / Football Data Scientist
  Completed: 2026-06-19
  Notes: Preserved unavailable active `team_metrics` gaps under the T-035 source
  policy without rewriting curated `data/matches/**/metrics.json` files.
  Extended the T-038 squad/style source-cache pattern with explicit missing rows
  for the remaining active metric-gap teams, so `/api/match/{id}/metrics`
  exposes machine-readable `missing_reasons` and per-field `source_cache_status`
  for unsupported local values. The only source-backed Squad & Style values
  remain Brazil `squad_market_value_m` and `average_age`; all other active empty
  team-metric fields are intentionally `missing` until an approved source-cache
  collector supplies auditable records. Default 40/30/30 forecasts remain
  `default_forecast`, including `brazil_haiti_2026` and the listed empty/default
  fixtures except `switzerland_bosnia_and_herzegovina_2026`, which keeps its
  non-default stored forecast.
  Verify: `python3 src/pipeline/collect_squad_style_sources.py`;
  `python3 -m json.tool data/source_cache/squad_style/latest_metrics.json`;
  direct API smoke for `canada_qatar_2026`, `brazil_haiti_2026`,
  `switzerland_bosnia_and_herzegovina_2026`, and `argentina_algeria_2026`;
  `python3 -m compileall -q src`; `npm --prefix src/frontend run build`;
  `git diff --check`.
  Decision: docs/decisions/20260619_DEC022_active_metric_gap_preservation.md
  Handoff: docs/handoffs/2026-06-19_data_pipeline_t031_active_metric_gap_preservation.md

- [x] **T-033 - Briefing API and Match Analysis Freshness UI**
  Owner: Data Pipeline Engineer / Frontend Engineer
  Completed: 2026-06-19
  Notes: Added `GET /api/match/{match_id}/briefing` with safe baseline,
  invalid, stale, blocked, skipped, and source-backed freshness handling. Missing
  `briefing.json` now returns a contract-compliant `baseline_only` payload
  instead of a 404, and expired fresh artifacts are downgraded to `stale` at
  response time. Match Analysis now fetches the dedicated briefing endpoint,
  falls back to summary status when needed, and renders a compact freshness badge
  without masking static baseline preview content.
  Verify: Direct API smoke for `brazil_haiti_2026`; temp-data smoke for missing,
  fresh, expired-to-stale, and invalid briefing states; `python3 -m compileall
  -q src`; `npm --prefix src/frontend run build`; `git diff --check`.
  Decision: docs/decisions/20260619_DEC021_briefing_api_freshness_contract.md
  Handoff: docs/handoffs/2026-06-19_data_pipeline_frontend_t033_briefing_api_freshness.md

- [x] **T-029 - Deployment and Operations Runbook Refresh**
  Owner: Orchestrator / QA / Reproducibility Engineer
  Completed: 2026-06-19
  Notes: Added current deployment and operations runbook plus QA verification
  checklist for React/Vite, FastAPI static mount, Docker, Cloud Run,
  `accionar.xyz`, local-vs-live status snapshots, smoke checks, and rollback
  procedures. Read-only live checks found Cloud Run reachable but stale versus
  local code: 19 fixtures, no lifecycle/source-status fields, no
  `brazil_haiti_2026`, and no current `data_quality`/source-cache metadata.
  `accionar.xyz` returned HTTP 200 but appeared to serve an older portfolio
  shell/static route. No deploy was performed.
  Verify: `python3 -m compileall -q src`; `npm --prefix src/frontend run build`;
  `git diff --check`; read-only Cloud Run and `accionar.xyz` HTTP checks.
  Handoff: docs/handoffs/2026-06-19_orchestrator_qa_t029_deployment_runbook.md

- [x] **T-038 - Source-Backed Squad & Style Metrics Integration**
  Owner: Data Pipeline Engineer / Football Data Scientist / Frontend Engineer
  Completed: 2026-06-19
  Notes: Added the T-038 field-level Squad & Style source methodology, a
  disk-only source cache at `data/source_cache/squad_style/latest_metrics.json`,
  runtime source-backed field merging, per-field quality records under
  `/api/match/{id}/metrics.data_quality.team_metrics[team].field_sources`, and
  compact `team_metric_sources` payloads. The first active sample is
  `brazil_haiti_2026`: Brazil has source-backed Transfermarkt header values for
  `squad_market_value_m` and `average_age`; Haiti and unsupported fields remain
  explicitly missing. Existing unsourced local profiles now render as
  `hardcoded_reference`, not live research. The Squad & Style UI shows sourced,
  reference, approximate, missing, unsupported, and blocked states per displayed
  value and uses the T-039 World Football Elo provenance for the rating row.
  Verify: `python3 src/pipeline/collect_squad_style_sources.py`;
  `python3 -m json.tool data/source_cache/squad_style/latest_metrics.json`;
  direct API smoke checks for `brazil_haiti_2026` and a non-sample fixture;
  `python3 -m compileall -q src`; `npm --prefix src/frontend run build`.
  Handoff: docs/handoffs/2026-06-19_data_pipeline_football_data_scientist_frontend_t038_squad_style.md

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
