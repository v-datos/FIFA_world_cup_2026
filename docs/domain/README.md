# Domain Knowledge - FIFA World Cup 2026 Dashboard

Last updated: 2026-06-17

This document summarizes the current product/domain model. Detailed JSON/API
contracts are documented in `docs/data_contracts.md`.

## Product Goal

The dashboard helps a small targeted audience follow the FIFA World Cup 2026
with:

- tournament overview
- group standings and knockout bracket
- daily fixture selection
- tactical match previews
- transparent outcome forecasts
- historical StatsBomb proxy visualizations

## Canonical Runtime

- React/Vite frontend: `src/frontend/`
- FastAPI backend: `src/api/main.py`
- Static data: `data/matches/` and `data/bracket/grid_state.json`
- Historical visualization helpers: `src/analytics/`
- Legacy/reference Streamlit code: `src/app/`

## Main Data Families

### Tournament State

- Live source: `worldcup26.ir` groups and games endpoints.
- Local fallback: `data/bracket/grid_state.json`.
- UI: Overview totals, Standings & Bracket tab.

### Fixture Metadata and Editorial Preview

- Source: `data/matches/{match_id}/summary.json`.
- Fields: fixture facts plus curated `ai_summary`.
- UI: Match Analysis header, dropdown, tactical headline, injury updates,
  coaching/tactics cards, formation pitch, and insights.
- Product role: baseline preview. This can exist well before matchday and must
  not be described as fresh last-minute analysis.

### Last-Minute Match Briefing

- Planned source: `data/matches/{match_id}/briefing.json`.
- Plan: `docs/last_minute_briefing_plan.md`.
- Product role: same-day or near-kickoff update layer with freshness, source,
  validation, and review metadata.
- UI expectation: show fresh/stale/baseline-only/blocked states instead of
  implying old baseline copy is current.

### Forecast and Team Profiles

- Source: `data/matches/{match_id}/metrics.json`.
- Current active fields: `dixon_coles_forecast`, `score_probabilities`,
  `team_metrics`.
- Runtime augmentation: Elo ratings, progression estimates, and visualization
  proxy labels.
- Known caveat: the Phase 5 data contract audit found eight fixtures with empty
  team metric profiles and seven fixtures with default stored forecasts.

### Historical Event Visualizations

- Source: BigQuery-backed StatsBomb historical matches.
- Use: proxy plots only, because live 2026 event data is not available.
- UI: xG distribution comparison, passing networks, shot maps, heatmaps,
  progressive action maps.

## Domain Principles

- Label live, static, curated, generated, fallback, and proxy data honestly.
- Do not overwrite curated editorial previews without review.
- Do not hide missing model inputs behind neutral-looking charts.
- Treat team aliases and multi-word country names as explicit data contracts.
- Keep football claims reviewable by the Football Data Scientist role.
