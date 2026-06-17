# TASKS

Last updated: 2026-06-16

## In Progress

- No tasks currently in progress.

## Queued

- No tasks currently queued.

## Backlog

- [ ] **T-019 - Player Career-Stats Hover Endpoint (`/api/player/stats`)**
  Owner: Data Pipeline Engineer / Football Data Scientist
  Notes: Deferred 2026-06-16 (DEC006). `InteractivePitch` already fetches per-player
  career stats on hover, but neither the route nor a backing BigQuery query exists;
  the tooltip degrades gracefully to "No data available in BigQuery". Requires
  data-model decisions (dataset/competition scope, 2026 roster → StatsBomb `player`
  name mapping) and cannot be runtime-verified locally without GCP credentials.

- [-] **T-008 - PostgreSQL Live Standings Ingestion Sync (Cancelled)**
  Phase: Phase 3
  Owner: Data Pipeline Engineer
  Notes: Cancelled on 2026-06-16. Local fallback and direct API polling satisfy all requirements; Postgres standings sync dismissed.

## Done

- [x] **T-022 - Match Analysis Deep Update, xG Distribution, Live Results Refresh**
  Owner: Frontend Engineer / Data Pipeline Engineer
  Completed: 2026-06-17
  Notes: Restructured Match Analysis (removed redundant forecast card, integrated top
  scores, fixed radar to real fields); added Squad & Style Comparison, Monte Carlo
  Projections, tactics & last-standing sections; replaced xG momentum with an xG
  Distribution Comparison chart; fixed the player tooltip; moved language toggle
  top-right; refreshed live standings + Overview totals from worldcup26.ir.

- [x] **T-021 - UI Polish: Bracket Fit-to-Screen, Flags, Today Selector, Sidebar/Ball Logo**
  Owner: Frontend Engineer
  Completed: 2026-06-16
  Notes: Bracket scales to fit the viewport (full bracket always visible); Match
  Analysis selector filtered to today's games with national flags on team names
  (shared `lib/teamData.ts`); sidebar retitled "FIFA 2026 / World Cup", collapsible,
  with the official match-ball logo. Pending Cloud Run redeploy.

- [x] **T-020 - Bracket Wood-Board Port, Full-Screen & StatsBomb Viz Fixes**
  Owner: Frontend Engineer / Data Pipeline Engineer
  Completed: 2026-06-16
  Notes: StandingsTab renders the full painter's-tape bracket from the seed `rounds[]`
  fallback (verbose labels restored); fixed right-half clipping with a scroll container
  and added a native/overlay Full Screen toggle. Fixed StatsBomb visualizations:
  matplotlib `Agg` backend + `get_cached_xg_timeline(_client)` cache-hash fix. Live
  site still pending redeploy (Cloud Run + accionar.xyz upload).

- [x] **T-018 - Interactive Analytics Sprint (Elo / Monte Carlo Projections & xG Momentum)**
  Owner: Football Data Scientist / Frontend Engineer
  Completed: 2026-06-16
  Notes: Added Elo + Monte Carlo tournament-progression projections to the metrics
  endpoint and an xG momentum timeline visualization; shipped StandingsTab /
  OverviewTab / MatchPredictionGraph / InteractivePitch upgrades. Restored a green
  build and fixed a momentum-chart wiring bug, a `get_cached_xg_timeline` runtime
  `KeyError`, and a duplicate Elo scrape. See DEC006.

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

## Blockers

- No blockers currently filed.
