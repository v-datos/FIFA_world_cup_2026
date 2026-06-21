# DEC030 - Squad Market Value via FotMob (headless browser)

Date: 2026-06-21

## Status

Accepted.

## Context

`squad_market_value_m` was hand-researched from Transfermarkt for only 16 of 48
teams, so 32 (including every team in later matchdays) showed MISSING — the same
manual-data trap fixed earlier for average age and xG. No free *no-browser*
source carries it: Transfermarkt's World Cup overview pages 404/504, and ESPN has
no market value.

## Decision

Reuse the FotMob headless-browser path from DEC028. FotMob's per-team data
exposes per-player `marketValue` in `overview.lastLineupStats`. Add
`src/pipeline/update_team_market_value.py`: it loads the FotMob league page to get
all team ids, then each team's page, and sums the starters + named subs market
values (the matchday 18, which covers nearly all the valuable players) into
`squad_market_value_m` (EUR millions) for every team. Same backup/restore safety
as xG (a snapshot at `data/source_cache/team_market_value/latest.json`, restored
if a live fetch fails).

It is **not** wired into the daily matchday Action: market value barely changes
mid-tournament, so loading 48 team pages twice a day is wasteful. Run it on
demand; the value persists in the cache (the collector preserves it) and can be
refreshed periodically.

## Consequences

- 48/48 teams now have a squad market value from one consistent source (e.g.
  France EUR 1.43bn, Spain EUR 1.27bn, Belgium EUR 529M, Iran EUR 13M).
- The figure is the matchday-squad value, slightly below a full 26-man
  Transfermarkt squad value, but consistent across all teams so comparisons are
  valid. The previous 16 Transfermarkt values are overwritten for consistency.
- Slow-changing, so it is refreshed manually/periodically rather than every
  matchday.

## Verification

- `python3 -m src.pipeline.update_team_market_value --write` → 48/48 teams.
- `/api/match/.../metrics` returns `squad_market_value_m` for both teams.
