# DEC013 - Render Fallback and Missing Data as Unavailable

Date: 2026-06-18
Status: Accepted
Task: T-028 - Incomplete Data and Fallback UI/API States

## Context

Several Match Analysis sections were rendering fallback values as if they were
authoritative:

- Default `40/30/30` forecasts appeared as model probabilities.
- Empty `team_metrics` objects produced neutral radar values.
- Squad & Style missing fields appeared only as unqualified dashes.
- Current progression estimates were labeled as Monte Carlo even though they are
  deterministic curves.
- Missing last-minute briefings were not distinguished from static baseline
  preview content.

## Decision

Expose runtime data-quality metadata from the API and make the frontend render
missing/default/fallback states explicitly.

The API may keep stored `metrics.json` values unchanged, but `/api/match/{id}/metrics`
must add `data_quality` labels so UI consumers know whether data is usable,
missing, static, proxy, or fallback.

## Runtime Labels

- `default_forecast`: stored default `40/30/30` forecast; hide as model output.
- `missing`: required values are unavailable.
- `static_curated`: local static reference metrics, not live research.
- `hardcoded_reference`: local Elo-style or deterministic reference values.
- `proxy_historical`: historical event-data proxy, not 2026 match data.
- `baseline_only`: static preview content with no last-minute `briefing.json`.
- `blocked`, `stale`, `fresh`: reserved briefing freshness states.

## Consequences

- Default forecasts render as "forecast unavailable."
- Exact scores are hidden when the forecast is default fallback only.
- Radar charts do not use neutral 50 values for missing metrics.
- Squad & Style surfaces missing or partial metrics.
- Progression estimates are no longer presented as true Monte Carlo until T-037
  replaces them with random-trial simulation.
- T-034 can safely create baseline stubs because the UI has degraded states for
  stub/default values.

## Verification

- API data-quality check for default and complete fixtures.
- `python3 -m compileall -q src`
- `npm --prefix src/frontend run lint`
- `npm --prefix src/frontend run build`
