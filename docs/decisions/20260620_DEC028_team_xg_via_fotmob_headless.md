# DEC028 - Team xG via FotMob (headless browser)

Date: 2026-06-20

## Status

Accepted.

## Context

`expected_goals_per_90` / `expected_goals_conceded_per_90` were MISSING for all
teams. No free, no-browser, server-automatable source exposes 2026 World Cup team
xG. Tested empirically:

- **API-Football** (free key): the free plan blocks the 2026 season, and the
  2022 World Cup (which the free plan *can* access) returns no `expected_goals`
  at all — API-Football has no World Cup xG, free or paid.
- **FBref** (the real source): HTTP 403 via plain `requests`, via `curl_cffi`
  Chrome TLS impersonation, and via a full session+cookie+fingerprint recipe;
  headless Playwright hits the Cloudflare "Just a moment…" challenge.
- **Sofascore**: HTTP 403 even with full browser headers (datacenter-IP block).
- **ESPN**: exposes shots/possession but no xG.

## Decision

Drive a real browser. `src/pipeline/update_team_xg.py` loads the FotMob World Cup
league page with Playwright and intercepts `/api/data/leagues?id=77`. FotMob has
no Cloudflare challenge; its only barrier is a signed request header, which the
browser generates automatically. The league payload carries a per-team xG table
(`xg`, `xgConceded`, `played`) for every group, so per-90 values come from the
cumulative xG divided by matches played — no per-match fetching.

It writes only `expected_goals_per_90` / `expected_goals_conceded_per_90` into
the squad_style cache (the collector preserves them — it merges). Wired into the
matchday GitHub Action behind `pip install playwright` + `playwright install
chromium`, run with `|| true`.

## Consequences

- All 48 teams get real xG (e.g. Germany 3.06 xG/90, Japan 0.93, Tunisia 0.15),
  verified over HTTP on `/api/match/.../metrics`.
- This is the project's first headless-browser dependency and is **fragile**: it
  depends on FotMob's page structure and may be blocked from datacenter IPs. The
  workflow tolerates failure, so xG simply keeps its last committed values if a
  run is blocked; it can always be refreshed by running the pipeline from a
  residential IP.
- Playwright/Chromium are installed only in the Action (and locally), not in the
  Cloud Run image — the API never runs the scraper, so the image stays lean.

## Verification

- `python3 -m src.pipeline.update_team_xg --write` → 48/48 teams updated.
- `python3 -m compileall -q src`; API `/api/match/tunisia_japan_2026/metrics`
  returns xG for both teams.
