# Domain Knowledge - FIFA World Cup 2026 Dashboard

Last updated: 2026-06-18

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
- safe draft matchday briefing artifacts
- source-backed AI-researched matchday briefings once T-036 implements the
  approved source policy

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

### Active Fixture Discovery

- Implemented source: `worldcup26.ir/get/games`, with `/tmp/games.json` cache
  fallback.
- Script: `src/pipeline/discover_active_fixtures.py`.
- Product role: make sure matches entering the active date or next-24-hour
  window have local baseline folders before briefing generation.
- Stub rule: if a fixture is missing locally, create explicit `baseline_stub`
  `summary.json` and `metrics.json` files using schedule facts only; do not
  invent tactical analysis, forecast probabilities, or team metrics.
- Lifecycle rule: finished fixtures stay available as historical records but
  are skipped by last-minute research and hidden from the default day view.

### Last-Minute Match Briefing

- Source: `data/matches/{match_id}/briefing.json`.
- Generator: `src/pipeline/generate_match_briefings.py`.
- Plan: `docs/last_minute_briefing_plan.md`.
- Product role: same-day or near-kickoff update layer with freshness, source,
  validation, and review metadata.
- Current T-032 behavior: dry-run by default, explicit `--write`, skip finished
  fixtures, require `source_status=not_finished`, and write only
  `briefing.json`.
- Current limitation: generated content is a draft baseline-support briefing
  until T-036 adds source-backed web/news research.
- Web/news collection is approved under T-035. Browser automation and scraping
  are allowed with retained source metadata and source-policy guardrails.
- UI expectation: show fresh/stale/baseline-only/blocked states instead of
  implying old baseline copy is current.

### Forecast and Team Profiles

- Source: `data/matches/{match_id}/metrics.json`.
- Current active fields: `dixon_coles_forecast`, `score_probabilities`,
  `team_metrics`.
- Runtime augmentation: Elo ratings, progression estimates, and visualization
  proxy labels.
- Known caveat: after T-034, nine fixtures have empty team metric profiles and
  eight fixtures have default stored forecasts.
- Current caveat from T-026: Elo ratings are local hardcoded defaults, and the
  progression panel is deterministic even though the UI currently labels it
  Monte Carlo.

### Historical Event Visualizations

- Source: BigQuery-backed StatsBomb historical matches.
- Use: proxy plots only, because live 2026 event data is not available.
- UI: xG distribution comparison, passing networks, shot maps, heatmaps,
  progressive action maps.
- Known limitation: BigQuery/StatsBomb proxy coverage is not broad enough to
  supply every current team, competition, or confederation context the Match
  Analysis tab needs.

### AI-Researched Matchday Data

- Policy: `docs/ai_research_source_policy.md`.
- Planned implementation: T-036 collector prototype.
- Intended use: current injuries, lineups, suspensions, roster changes, manager
  updates, tactical news, and team context that static files and BigQuery proxies
  do not cover.
- Product rule: AI may collect, normalize, and summarize source-backed facts.
  Individual displayed claims do not require one-to-one URL citations, but the
  run must retain source URL/path, retrieval time, status, and review metadata
  for audit.

## Domain Principles

- Label `live_schedule`, `static_curated`, `generated_model`,
  `default_forecast`, `hardcoded_reference`, `proxy_historical`,
  `web_researched`, `missing`, and `blocked` data honestly.
- Do not overwrite curated editorial previews without review.
- Do not hide missing model inputs behind neutral-looking charts.
- Treat team aliases and multi-word country names as explicit data contracts.
- Keep football claims reviewable by the Football Data Scientist role.
- Do not call hardcoded defaults, deterministic formulas, or proxy data live,
  scraped, simulated, or fully researched.
