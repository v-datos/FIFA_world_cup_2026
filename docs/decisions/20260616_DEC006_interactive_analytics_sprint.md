# Decision: Interactive Analytics Sprint (Elo / Monte Carlo Projections & xG Momentum)

Date: 2026-06-16
Authority: Orchestrator
Status: Decided

## Context

After the React/FastAPI migration (DEC005) the working tree accumulated an
uncommitted feature batch that was never recorded in the tracking docs and that
broke the frontend build. The batch added tournament-progression projections, an
xG momentum visualization, and several UI upgrades (StandingsTab, OverviewTab,
MatchPredictionGraph, InteractivePitch).

## Ruling

Finish, verify, and commit the in-flight batch. Specifically:

- Enrich `/api/match/{match_id}/metrics` with per-team **Elo ratings** and
  **Monte Carlo tournament-progression projections** (`compute_monte_carlo_probs`).
- Add an **xG momentum timeline** visualization (`get_cached_xg_timeline`) wired
  to a new `momentum` `viz_type` in the visualizations route.
- Ship the StandingsTab / OverviewTab / MatchPredictionGraph / InteractivePitch
  UI upgrades and English/Spanish translation additions.

## Fixes applied while finishing the batch

- Restored a green build: removed unused imports (`Award`, `ShieldAlert`,
  `drawVal`) and reconciled the `InteractivePitch` contract — the refactor to an
  internal `PLAYER_CLUBS_ALL` map dropped the `playerClubs` prop and now requires
  `serverUrl`, but the committed `MatchAnalysisTab` caller still passed
  `playerClubs`. Updated the caller and removed the orphaned `PLAYER_CLUBS` map.
- Wired the xG momentum tab to the `momentum` endpoint (it was requesting
  `radar_chart`).
- Fixed a runtime `KeyError` in `get_cached_xg_timeline`: it read `second` and
  `shot_statsbomb_xg`, columns `get_match_momentum_timeline` does not return. It
  now consumes the `cumulative_xg` the query already provides.
- Deduplicated a double Elo scrape in the metrics endpoint.

## Deferred

- **`/api/player/stats` endpoint** — `InteractivePitch` fetches per-player career
  stats on hover, but neither the route nor a backing query exists. The tooltip
  degrades gracefully ("No data available in BigQuery"). Building it is net-new
  BigQuery work with unresolved data-model questions (dataset/competition scope,
  2026 roster → StatsBomb `player` name mapping) and cannot be runtime-verified
  locally. Tracked as T-019.

## Verification

- `python -m py_compile` over changed modules: passes.
- `npm --prefix src/frontend run build`: passes (exit 0).
- `import src.api.main`: succeeds; all routes register.
- Live BigQuery/Cloud Run behavior not exercised locally (no GCP credentials).
