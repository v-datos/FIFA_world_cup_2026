# Handoff - T-024 Data Contract Audit

Date: 2026-06-17  
From: QA / Reproducibility Engineer  
To: Orchestrator, Data Pipeline Engineer, Football Data Scientist, Frontend Engineer

## Summary

T-024 is complete. The active JSON and API payload contracts are documented in
`docs/data_contracts.md`.

No runtime code, JSON payloads, generator scripts, frontend code, or deployment
assets were changed.

## Evidence Reviewed

- `data/matches/*_2026/summary.json`
- `data/matches/*_2026/metrics.json`
- `data/matches/1001`, `data/matches/1002`, `data/matches/1003`
- `data/bracket/grid_state.json`
- `src/api/main.py`
- `src/pipeline/generate_match_previews.py`
- `src/analytics/soccerdata_client.py`
- `src/frontend/src/components/MatchAnalysisTab.tsx`
- `src/frontend/src/components/MatchPredictionGraph.tsx`
- `src/frontend/src/components/TeamRadarComparison.tsx`
- `src/frontend/src/components/SquadStyleComparison.tsx`
- `src/frontend/src/components/MonteCarloProjections.tsx`
- `src/frontend/src/components/OverviewTab.tsx`

## Results

- Active fixture folders: 19.
- Legacy numeric folders: `1001`, `1002`, `1003`.
- `summary.json` schema status: 19 pass, 0 fail.
- React editorial key lookup status: 17 pass, 2 fail.
- `metrics.json` top-level status: 19 pass, 0 fail.
- Populated team metric profiles: 11 pass, 8 fail.
- Default stored forecasts: 7 fixtures.

## Empty Team Metric Fixtures

- `canada_qatar_2026`
- `czech_republic_south_africa_2026`
- `mexico_south_korea_2026`
- `scotland_morocco_2026`
- `switzerland_bosnia_and_herzegovina_2026`
- `turkey_paraguay_2026`
- `united_states_australia_2026`
- `uzbekistan_colombia_2026`

## Default Forecast Fixtures

- `canada_qatar_2026`
- `czech_republic_south_africa_2026`
- `mexico_south_korea_2026`
- `scotland_morocco_2026`
- `turkey_paraguay_2026`
- `united_states_australia_2026`
- `uzbekistan_colombia_2026`

## Known Consumer Lookup Failures

`summary.json` stores correct keys, but `MatchAnalysisTab.tsx` currently derives
team slugs with first-space-only replacement. That misses:

- `democratic_republic_of_the_congo`
- `bosnia_and_herzegovina`

The affected fixtures are:

- `portugal_democratic_republic_of_the_congo_2026`
- `switzerland_bosnia_and_herzegovina_2026`

## Routed Follow-Ups

- T-025: Completed after this handoff as the safe last-minute match briefing
  generation plan.
- T-026: Review model/provenance truth for Dixon-Coles, local Elo defaults,
  default forecasts, confidence, and deterministic projection wording.
- T-027: Centralize team identity and replace fragile frontend/API parsing.
- T-028: Add explicit incomplete/fallback states for empty metrics and default
  forecasts.
- T-031: Fill or explicitly label missing active fixture metric profiles.

## Recommended Next Step

After T-025 completion, assign T-026 to the Football Data Scientist. Model and
source-provenance wording should be settled before implementing approved
last-minute briefing output.
