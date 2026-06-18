# Handoff - T-028 Incomplete Data and Fallback UI/API States

Date: 2026-06-18
From: Frontend Engineer / Data Pipeline Engineer
To: Orchestrator, Data Pipeline Engineer, Football Data Scientist, QA / Reproducibility Engineer
Status: Complete

## Deliverables

- Added runtime `data_quality` metadata to `/api/match/{match_id}/metrics`.
- Added runtime `briefing_status` metadata to `/api/match/{match_id}/summary`.
- Updated `MatchPredictionGraph` so default `40/30/30` forecasts render as
  "forecast unavailable."
- Updated `TeamRadarComparison` so missing metrics do not render as neutral 50.
- Updated `SquadStyleComparison` so empty and partial metrics render with
  unavailable/missing states.
- Updated `MonteCarloProjections` so the current deterministic curve is labeled
  as a tournament progression estimate, not true Monte Carlo.
- Passed source/fallback quality props through `MatchAnalysisTab`.

## New API Contract

`/api/match/{match_id}/metrics` now includes:

```json
{
  "data_quality": {
    "forecast": {"status": "available|unavailable", "source_label": "default_forecast|hardcoded_reference"},
    "score_probabilities": {"status": "available|unavailable", "source_label": "default_forecast|hardcoded_reference"},
    "team_metrics": {
      "Team": {"status": "missing|partial|complete", "source_label": "missing|static_curated"}
    },
    "radar_metrics": {"status": "available|unavailable", "source_label": "static_curated|missing"},
    "elo_ratings": {
      "Team": {"status": "available|missing", "source_label": "hardcoded_reference|missing"}
    },
    "monte_carlo_projections": {"status": "deterministic_fallback|unavailable", "source_label": "hardcoded_reference"},
    "visualizations": {"status": "proxy_historical", "source_label": "proxy_historical"}
  }
}
```

`/api/match/{match_id}/summary` now includes:

```json
{
  "briefing_status": {
    "freshness_state": "fresh|stale|baseline_only|blocked",
    "source_label": "static_curated|web_researched|blocked",
    "message": "Reader-facing status message."
  }
}
```

## Verification Run

- API data-quality check:
  - `canada_qatar_2026` forecast is `unavailable/default_forecast`.
  - `canada_qatar_2026` team metrics are `missing`.
  - `france_senegal_2026` forecast and radar metrics remain available.
  - missing briefing renders as `baseline_only`.
- `python3 -m compileall -q src`
- `npm --prefix src/frontend run lint`
- `npm --prefix src/frontend run build`

The frontend build passed with the existing chunk-size warning only.

## Next Routing

Recommended next Orchestrator task: T-034 - Active Fixture Discovery and
Baseline Stub Generation.

Reason: T-027 identity and T-028 fallback rendering are now complete, so
baseline stubs can be generated without new fixtures breaking identity or
misleading the public UI.
