# STATUS

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
