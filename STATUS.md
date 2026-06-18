# STATUS

## 2026-06-18 - T-035 AI Research Source Policy Completed

Prepared by: Orchestrator

### Current State

- T-035 is complete as a policy and intake-architecture task.
- Deliverable added: `docs/ai_research_source_policy.md`.
- Handoff added:
  `docs/handoffs/2026-06-18_orchestrator_t035_ai_research_source_policy.md`.
- Decision added:
  `docs/decisions/20260618_DEC011_ai_research_source_policy.md`.
- Runtime behavior was not changed.

### Accepted User Decisions

- Default `40/30/30` forecasts should render as "forecast unavailable."
- The progression panel should become a real Monte Carlo simulation.
- Online research should feed ratings, Squad & Style metrics, lineups, injuries,
  rosters, managers, and tactical news.
- Browser automation and scraping are allowed.
- Individual displayed AI claims do not require one-to-one URL citations, but the
  collection run should retain source metadata for audit.
- Fresh last-minute analysis uses a 3-hour window before the first game of the
  daily `jornada`.

### Recommended Source Stack

- Ratings: World Football Elo, with FIFA ranking as fallback/sanity check.
- Official facts: FIFA squad/ranking/tournament pages.
- Structured live/team data: Sportmonks as preferred provider, API-Football as
  fallback.
- Market value: Transfermarkt.
- Deep style metrics such as PPDA and field tilt: Wyscout, Opta/Stats Perform,
  or paid StatsBomb/event data if available.
- Last-minute injuries/tactical news: browser automation over official/team/news
  pages, with source snapshots or source records retained.

### Routing

- Added **T-037 - Real Monte Carlo Tournament Simulation**.
- Added **T-038 - Source-Backed Squad & Style Metrics Integration**.
- Moved **T-036 - Source-Backed Research Collector Prototype** into the queued
  implementation path.
- T-028 must render default forecasts as "forecast unavailable."
- T-032/T-033 should use the 3-hour `jornada` freshness rule.

### Verification Scope

- Documentation-only change. Local compile/build verification is run after the
  full documentation batch.

---

## 2026-06-18 - T-026 Model and Provenance Truth Review Completed

Prepared by: Orchestrator

### Current State

- T-026 is complete as a truth/provenance review.
- Owner: Football Data Scientist.
- Deliverable added: `docs/model_provenance.md`.
- Handoff added:
  `docs/handoffs/2026-06-18_football_data_scientist_t026_model_provenance.md`.
- Decision added:
  `docs/decisions/20260618_DEC010_model_provenance_truth_labels.md`.
- Runtime behavior was not changed.

### Key Findings

- Current Match Analysis is not yet an AI-research-first system. It is mostly
  static `summary.json`, static `metrics.json`, local hardcoded references,
  deterministic formulas, and historical proxy visualizations.
- The Dixon-Coles forecast is an Elo-derived Poisson score-grid calculation with
  a low-score adjustment, not a fitted broad-data model.
- Current Elo ratings are local hardcoded defaults, not live SoccerData or
  ClubElo reads.
- The default `40/30/30` forecast must be labeled as fallback, not as a model
  result.
- The current "Monte Carlo" panel is deterministic and should be renamed unless
  a real simulation is implemented.
- StatsBomb/BigQuery charts are historical proxies and do not cover the full
  match-intelligence problem, including missing competitions and teams outside
  the available sample.
- Rosters, clubs, and last major standings are hardcoded frontend references.

### Routing

- Added queued task **T-035 - AI Research Source Policy and Data Intake
  Architecture**.
- Added backlog task **T-036 - Source-Backed Research Collector Prototype**.
- T-032 source-backed briefing generation now depends on T-035 for any
  web-research collection.
- T-028 must update UI/API wording and degraded states so default forecasts,
  local ratings, hardcoded references, and proxy visuals are visible.

### Policy Questions Before Implementation

- Should default `40/30/30` ever be public, or should it render as forecast
  unavailable?
- Should the deterministic progression panel be renamed now, or replaced with a
  real tournament simulation?
- Which rating source should forecasts use?
- Which web sources and collection methods are allowed for injuries, lineups,
  rosters, managers, suspensions, tactical news, and team metrics?
- Must every AI-generated current claim have URL-backed source metadata?
- Should proxy charts fail closed instead of falling back to unrelated teams?

### Verification Scope

- Documentation-only change. Local compile/build verification is still run after
  the full documentation batch.

---

## 2026-06-17 - Active Fixture Discovery Gap Routed

Prepared by: Orchestrator

### Current State

- The tournament progression gap is now explicitly tracked.
- Owner: Data Pipeline Engineer, with QA / Reproducibility Engineer review.
- Deliverable added: `docs/active_fixture_discovery_plan.md`.
- Runtime behavior was not changed.

### Why This Matters

- The app currently lists analyzable matches from local
  `data/matches/*_2026` folders.
- If a future tournament game has no local folder, `/api/schedule` will not list
  it and `/api/match/{id}/summary` or `/metrics` will return 404.
- Last-minute `briefing.json` generation depends on a baseline fixture folder
  existing first.

### Planned Procedure

- Discover active-date or next-24-hour fixtures from
  `https://worldcup26.ir/get/games`.
- Fall back to `/tmp/games.json` if the live games API fails.
- Create missing baseline folders only with explicit `--write`.
- Generate minimal `summary.json` and `metrics.json` stubs labeled
  `baseline_stub`.
- Preserve all existing curated `summary.json` and `metrics.json` files.
- Run last-minute briefing generation only after the baseline folder exists.

### Routing

- Added queued task **T-034 - Active Fixture Discovery and Baseline Stub
  Generation**.
- Added decision record
  `docs/decisions/20260617_DEC009_active_fixture_discovery_stubs.md`.
- T-034 should run before T-032.
- T-027 remains important because fixture discovery must use canonical team
  names and slugs, not fragile match ID parsing.
- T-028 must stop stub metrics from rendering as authoritative forecasts or
  radar charts.

### Verification Scope

- `python3 -m compileall -q src` passed.
- `npm --prefix src/frontend run build` passed with the existing Vite
  chunk-size warning only.

---

## 2026-06-17 - T-025 Re-scoped to Last-Minute Briefing Generation

Prepared by: Orchestrator

### Current State

- T-025 is complete as a planning task.
- Owner: Data Pipeline Engineer.
- Deliverable: `docs/last_minute_briefing_plan.md`.
- Runtime behavior was not changed.

### Completed This Update

- Re-scoped T-025 from generic safe preview regeneration into safe
  last-minute match briefing generation.
- Defined the product split between:
  - baseline preview: `summary.json`
  - matchday briefing: planned `briefing.json`
- Defined planned `briefing.json` fields for metadata, fixture copy, normalized
  team keys, briefing content, forecast snapshot, data quality, sources, and
  review status.
- Required generator safety rules:
  dry-run by default, explicit write mode, no `summary.json` or `metrics.json`
  overwrites, source/freshness validation, and review gates.
- Added implementation follow-ups:
  T-032 for the briefing pipeline and T-033 for API/UI freshness states.
- Added decision record
  `docs/decisions/20260617_DEC008_last_minute_briefing_scope.md`.

### Next Routing

- At the time, the next recommended Orchestrator assignment was **T-026 - Model
  and Provenance Truth Review**. T-026 is now complete; current routing is in the
  2026-06-18 entry above.
- T-032 should wait until T-027 clarifies team identity normalization and T-035
  clarifies source policy for web-researched inputs.
- T-033 should coordinate with T-028 so briefing freshness and incomplete-data
  states are implemented consistently.

### Verification Scope

- `python3 -m compileall -q src` passed.
- `npm --prefix src/frontend run build` passed with the existing Vite
  chunk-size warning only.

---

## 2026-06-17 - Data Contract Audit Completed (T-024)

Prepared by: Orchestrator

### Current State

- T-024 is complete.
- QA / Reproducibility Engineer owned the audit, with Data Pipeline Engineer
  support for generator/API provenance.
- Deliverable: `docs/data_contracts.md`.
- No runtime code, JSON payloads, generation scripts, or deployment assets were
  changed.

### Completed This Update

- Documented the active contracts for `summary.json`, `metrics.json`,
  `grid_state.json`, `/api/schedule`, `/api/match/{id}/summary`,
  `/api/match/{id}/metrics`, `/api/standings`, `/api/forecast`, and
  `/api/visualizations/{match_id}/{viz_type}`.
- Separated stored JSON fields from runtime API augmentation:
  `elo_ratings`, `monte_carlo_projections`, and `viz_proxies`.
- Audited all 19 active `data/matches/*_2026` fixture folders.
- Classified legacy numeric folders `1001`, `1002`, and `1003` as old
  BigQuery-style stubs outside `/api/schedule`.
- Added a QA handoff at
  `docs/handoffs/2026-06-17_qa_data_contract_audit.md`.

### Audit Findings

- `summary.json`: all 19 active fixtures pass the required metadata/editorial
  schema checks.
- `metrics.json`: all 19 active fixtures have the required stored top-level
  keys and 6 exact-score probabilities.
- Empty `team_metrics`: 8 fixtures need completion or explicit fallback states:
  `canada_qatar_2026`, `czech_republic_south_africa_2026`,
  `mexico_south_korea_2026`, `scotland_morocco_2026`,
  `switzerland_bosnia_and_herzegovina_2026`, `turkey_paraguay_2026`,
  `united_states_australia_2026`, and `uzbekistan_colombia_2026`.
- Default stored forecast: 7 fixtures use the generator fallback
  `40/30/30` split: all empty-metrics fixtures except
  `switzerland_bosnia_and_herzegovina_2026`.
- Multi-word team names remain a contract risk in frontend normalization and
  API fallback parsing. React currently misses two long-name editorial keys:
  `democratic_republic_of_the_congo` and `bosnia_and_herzegovina`.
- Overview tournament totals are hardcoded in `OverviewTab.tsx`, not sourced
  from schedule or standings payloads.

### Next Routing

- T-025 was completed after this audit as the safe last-minute match briefing
  generation plan.
- At the time, the recommended Orchestrator assignment was **T-026 - Model and
  Provenance Truth Review**. T-026 is now complete; current routing is in the
  2026-06-18 entry above.
- T-027 should centralize team identity and fix multi-word/alias handling.
- T-028 should make empty/default/fallback states visible in the UI/API.
- T-031 should complete or explicitly label the eight empty team metric
  profiles.

### Verification Scope

- `python3 -m compileall -q src` passed.
- `npm --prefix src/frontend run build` passed with the existing Vite
  chunk-size warning only.

---

## 2026-06-17 - Framework Rebaseline Batch 1

Prepared by: Orchestrator

### Current State

- The project is now treated as a **React/Vite + FastAPI** application.
- `src/app/` Streamlit code is legacy/reference unless a later decision says
  otherwise.
- Phase 5 is active: **Framework Rebaseline & Pipeline Hardening**.
- Batch 1 is docs-only and does not change runtime behavior.

### Completed This Update

- Rewrote `PROJECT_CHARTER.md` as the current operating contract.
- Updated `AGENTS.md` so the five framework agents map to the current
  React/FastAPI/static-data project.
- Replaced `docs/phase_plan.md` with Phase 5 batches and exit criteria.
- Rebuilt `TASKS.md` around the real current deficiencies:
  data contracts, last-minute briefing generation, model provenance, team
  identity, incomplete-data UI states, and deployment runbook refresh.
- Refreshed `docs/DEVELOPER_PLAYBOOK.md` for the current architecture.
- Refreshed `README.md` and `docs/domain/README.md` to stop pointing new
  readers at stale Streamlit/Antigravity assumptions.
- Added decision record `docs/decisions/20260617_DEC007_framework_rebaseline.md`.

### Known Local Findings Feeding Phase 5

- Active match folders: 19 `*_2026` fixture folders with `summary.json` and
  `metrics.json`.
- Legacy numeric folders: `1001`, `1002`, `1003` still contain old
  BigQuery-style metrics and are not part of `/api/schedule`.
- Several active fixtures have empty `team_metrics`.
- Several forecasts fall back to the default `40/30/30` outcome split because
  Elo/team profiles are missing for the exact team names in use.
- Current `summary.json` files may contain newer curated editorial copy than
  `generate_match_previews.py`; the generator must not be run again without a
  dry-run/diff/preserve plan.
- Multi-word team names and aliases are a known fragile path across generator,
  API, and frontend code.
- Some UI/model wording overstates current implementation details, especially
  static Elo defaults and deterministic "Monte Carlo" projections.

### Next Batch

- Completed after this entry: **T-024 - Data Contract Audit for Active JSON and
  API Payloads**.

### Verification Scope

- Local docs were updated only.
- Runtime behavior and live deployment were not changed in this batch.
- `python3 -m compileall -q src` passed.
- `npm --prefix src/frontend run build` passed with the existing Vite chunk-size
  warning only.

---

## 2026-06-17 - Match Analysis Deep Update, xG Distribution, Live Results Refresh

Prepared by: Orchestrator

### Completed This Update

- **Match Analysis restructure**: removed the redundant "Match Forecast" card; "Match
  Outcome Probability" moved up with **Top Exact Scores integrated**; radar fixed to
  read the real `team_metrics` fields (was always showing hardcoded defaults).
- **New sections** (real data): **Squad & Style Comparison (FBref & Club Elo)** beside
  the radar, **Monte Carlo Simulation Projections** (half-width, below the radar),
  **Coaching & Tactical Philosophies** and **Last Major Standing**.
- **xG Distribution Comparison** replaces the xG momentum timeline in the StatsBomb
  section (`get_cached_xg_distribution` — non-penalty KDE curves + shot strip plot).
- **Player tooltip** fixed (no longer clipped/behind; name tag sits below the dot;
  BigQuery cruft removed → clean name/position/club).
- **Language toggle** moved to the top-right corner; event plots labeled as proxy.
- **Live results refresh** (worldcup26.ir): group standings in `grid_state.json` and
  Overview totals updated — 19 matches played, 58 goals, top scorer L. Messi (3).

### Still pending

- Per-player stats/photos in the squad tooltips (large web curation) — not yet done.
- Cloud Run redeploy after merge.

---

## 2026-06-16 - UI Polish: Bracket Fit-to-Screen, Flags, Today-Only Selector, Sidebar/Ball Logo

Prepared by: Orchestrator

### Completed This Update

- **Bracket fits the screen**: `StandingsTab` scales the fixed-width board via a
  `ResizeObserver` so the entire bracket is always visible (no clipping/scroll);
  full-size in Full Screen.
- **Match Analysis selector decluttered**: dropdown shows only the current day's
  fixtures and auto-selects a today's match.
- **National flags** added to team names across Match Analysis (header, selector,
  forecast, injuries, squad lineups, StatsBomb labels). Flags + `TODAY_DATE`
  centralized in `src/frontend/src/lib/teamData.ts` (OverviewTab refactored to use it).
- **Sidebar**: title → "FIFA 2026 / World Cup"; collapsible toggle; brand icon →
  official FIFA World Cup 26 match-ball logo (`ball-logo.png`, resized 7.7MB → 45KB,
  moved to `src/frontend/src/assets/`). Added `vite-env.d.ts` for typed image imports.

### Live Site

- Not yet redeployed with this round (Cloud Run rebuild pending after merge).

---

## 2026-06-16 - Bracket Wood-Board Port, Full-Screen & StatsBomb Viz Fixes

Prepared by: Orchestrator

### Current Objective

Make the React Standings & Bracket tab render the full Streamlit-style painter's-tape
board, add a full-screen option, and fix the broken Bespoke Match Event (StatsBomb)
visualizations.

### Completed This Update

- **Bracket renders fully**: `StandingsTab` now falls back to the seed nested
  `rounds[]` / `third_place` shape (and uses `data.tournament` for the title), so the
  whole knockout bracket renders even when the live API has no knockout games. Verbose
  seed labels (`Winner Group A`, `Runner-up …`, `3rd Group …`, `Winner Match …`,
  `Loser Match …`) restored in `grid_state.json`.
- **No longer clipped + full-screen**: the board is wrapped in a horizontally
  scrollable container (was `overflow-hidden`, which cut off the right half), plus a
  Full Screen toggle that prefers the native Fullscreen API and falls back to a CSS
  overlay (for iframe embeds without `allowfullscreen`); Esc exits.
- **StatsBomb visualizations fixed**: forced matplotlib's non-interactive `Agg`
  backend (GUI backend crashed in FastAPI worker threads — broke every viz locally),
  and renamed `get_cached_xg_timeline(client → _client)` so Streamlit's cache stops
  failing to hash the BigQuery client (this was the live `momentum` 500). All five viz
  endpoints verified returning PNGs locally.

### Live Site Status (accionar.xyz/dashboards/fifa-2026) — NOT up to date

- Cloud Run `metrics` is missing `elo_ratings` / `monte_carlo_projections` (T-018 not deployed).
- Cloud Run `momentum` viz returns HTTP 500; other viz types work.
- None of the changes above are deployed. Requires: rebuild + deploy Docker to Cloud
  Run, and upload `src/frontend/dist` to the accionar.xyz folder.

---

## 2026-06-16 - Interactive Analytics Sprint Finished & Build Restored

Prepared by: Orchestrator

### Current Objective

Finish, verify, and commit the uncommitted interactive-analytics feature batch
that had accumulated after the React/FastAPI migration and was breaking the
frontend build.

### Completed This Update

- **Elo & Monte Carlo projections**: `/api/match/{match_id}/metrics` now returns
  per-team Elo ratings and Monte Carlo tournament-progression probabilities
  (`compute_monte_carlo_probs`).
- **xG Momentum visualization**: Added `get_cached_xg_timeline` and a `momentum`
  `viz_type`; wired the frontend momentum tab to it (it had been requesting
  `radar_chart`).
- **Build restored (exit 0)**: Removed unused imports and reconciled the
  `InteractivePitch` prop contract — the refactor to an internal `PLAYER_CLUBS_ALL`
  map dropped `playerClubs` and now requires `serverUrl`, but the committed
  `MatchAnalysisTab` caller still passed `playerClubs`. Updated the caller and
  removed the orphaned map.
- **Runtime bug fixed**: `get_cached_xg_timeline` read columns the momentum query
  never returns (`second`, `shot_statsbomb_xg`); now consumes `cumulative_xg`.
- **Efficiency**: Deduplicated a double Elo scrape in the metrics endpoint.

### Deferred

- **`/api/player/stats`** (T-019): `InteractivePitch` hover stats call an endpoint
  that was never built; tooltip degrades gracefully. Net-new BigQuery work with
  open data-model questions. See DEC006.

### Next Sprint Priorities

- Verify Cloud Run deployment and redeploy the rebuilt container.
- Upload compiled React static assets to the `accionar.xyz` folder structure.
- Decide on / implement T-019 if per-player hover stats are wanted.

---

## 2026-06-16 - Vite + React Client & FastAPI Decoupled Migration Completed

Prepared by: Orchestrator

### Current Objective

Migrate the dashboard from Streamlit to a decoupled architecture consisting of a FastAPI REST backend and a modern React client built with Vite and TailwindCSS, incorporating interactive vector charts and a dynamic lineup pitch.

### Completed This Update

- **REST API Backend**: Created `/src/api/main.py` using FastAPI, exposing REST endpoints for schedule, match summary, metrics, live standings, and dynamic StatsBomb matplotlib base64 visualizations.
- **Root Asset Serving**: Integrated FastAPI's `StaticFiles` mount at `/` to serve the compiled frontend single-page application directly from the unified python container.
- **Vite React Client**: Initialized client under `/src/frontend/` using Vite, React 19, TypeScript, and TailwindCSS v4.
- **Interactive Pitch Lineup**: Implemented the HTML5/CSS canvas pitch model in `InteractivePitch.tsx` that dynamically maps players based on formation (`4-3-3`, `4-1-4-1`, `3-5-2`) and displays player metadata and entity crosswalk IDs on hover.
- **Animated Charting**: Wired win probability shift curves and team radar comparisons utilizing interactive, responsive vector SVG components via **Recharts**.
- **Live standings & Bracket**: Built the live tournament center (`StandingsTab.tsx`) rendering standings for all 12 groups (A to L) and the live knockout tree (Round of 32 to Final).
- **Static Base Portability**: Set `base: './'` in Vite config to ensure compiled static bundles can be hosted seamlessly in a subfolder on `accionar.xyz/dashboards/fifa-2026/` or at the root path on Cloud Run.

### Next Sprint Priorities

- Verify Cloud Run deployment.
- Upload compiled React static assets to `accionar.xyz` folder structure.

---

## 2026-06-15 - Match Analysis Tab Bug Fixes & Previews Resiliency Completed

Prepared by: Orchestrator

### Current Objective

Ensure correct group standings sorting, dynamic knockout bracket updates from API, and fully automated, resilient match previews and tactical comparisons without crashes or empty views on the dashboard.

### Completed This Update

- **Standings Parsing & Sorting**: Corrected the parsing of groups from the API and sorted standings descending by points (`pts`), then goal difference (`gd`), then goals for (`gf`).
- **Dynamic API-Driven Bracket**: Configured bracket rounds mapping to the live `/get/games` schedule. Bracket advances teams and scores automatically in real time.
- **AI Match Previews & Resiliency**: Resolved the `KeyError: 'team_metrics'` crash in the Streamlit app. Configured the generation pipeline to write the `team_metrics` block containing ELO and FBref statistics for both teams.
- **New Team Profiles & Rosters**: Populated static rosters, club affiliations, and tournament standings for 8 new teams (Spain, Cape Verde, Belgium, Egypt, Saudi Arabia, Uruguay, Iran, New Zealand) and handled spelling normalization for Côte d'Ivoire.
- **Expanded upcoming games coverage**: Increased upcoming preview limits from 3 to 8 matches, resolving the missing **Iran vs New Zealand** fixture on June 15, 2026.
- **Cloud Run Deployment**: Rebuilt the Docker container and redeployed the live dashboard.
- **Tournament Board Standing Update Fix**: Installed `curl` inside the slim Docker container image to resolve the silent failure of runtime standings API calls, and updated the local `grid_state.json` fallback.
- **Portfolio Website Integration**: Synchronized the React routing changes and whitelisted the CSP `frame-src` in `.htaccess` on the remote server via SSH.
