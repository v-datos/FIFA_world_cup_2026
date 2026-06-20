# DEC024 - Runtime Match Analysis Data Contracts (Forecast, Lineups, Overview Time/Venue)

Date: 2026-06-20

## Status

Accepted.

## Context

The Match Analysis tab rendered several sections blank because the active
fixtures shipped as stubs and T-028 deliberately hides missing/default data
rather than faking it. The live tournament API (`worldcup26.ir`) was also
unreachable from local development, freezing the visible data. The user
directed that the app should present real, source-backed analysis, served from
caches refreshed per matchday (not live-scraped per request).

## Decision

- **Runtime forecast (T-045):** `/api/match/{id}/metrics` computes an
  Elo-derived Dixon-Coles forecast from the World Football Elo cache when the
  stored `dixon_coles_forecast` is the `40/30/30` stub, and keeps the top-level
  `score_probabilities` in sync. Provenance is labelled from the Elo source
  (`web_researched`); the stub only shows when both ratings are missing.
- **Squad & Style values (T-045):** researched squad market values and ages are
  stored in `data/source_cache/squad_style/latest_metrics.json` and merged at
  runtime. Unsupported advanced metrics (xG, PPDA, field tilt, possession) stay
  `missing` rather than inferred.
- **Matchday lineups (T-046):** `data/source_cache/lineups/latest.json` holds
  source-backed XIs (formation, manager, philosophy, ordered players, clubs).
  `get_match_summary` merges it into `ai_summary.confirmed_tactics` and adds
  slug-keyed `rosters` + a `player_clubs` map. The React lineup pitch prefers
  API rosters over the legacy hardcoded map.
- **Overview venue/time (T-048):** fixtures carry an optional `kickoff_utc`;
  `/api/schedule` passes it through; the Overview renders kickoffs in Edmonton
  (`America/Edmonton`, MT) and the venue as a Google Maps search link. The
  day's real fixtures are added as fixture folders when discovery cannot run.
- **Standings (T-047):** `data/bracket/grid_state.json` group standings are the
  refreshable fallback; Cloud Run additionally serves a live recompute when
  `worldcup26.ir` is reachable.

## Consequences

- Match Analysis and Overview present real, provenance-labelled data while the
  live feed is down, refreshed per matchday through disk caches.
- New route-affecting code must be verified over real HTTP, not only via
  in-process calls (a misplaced decorator on the summary route was caught only
  during live deploy verification).
- Advanced radar metrics and some lineups remain unsourced and render as
  missing until a provider feed or further research supplies them.

## Verification

- Live Cloud Run revision `fifa-2026-dashboard-00021-z9r`:
  summary returns rosters/tactics, schedule exposes `kickoff_utc`, standings
  show current results, metrics return an Elo-derived forecast.
- `python3 -m compileall -q src`; `npm --prefix src/frontend run build`.
