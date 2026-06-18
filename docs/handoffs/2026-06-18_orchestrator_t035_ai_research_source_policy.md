# Handoff - T-035 AI Research Source Policy and Data Intake Architecture

Date: 2026-06-18  
From: Orchestrator  
To: Football Data Scientist, Data Pipeline Engineer, Frontend Engineer, QA / Reproducibility Engineer

## Summary

T-035 is complete as a source-policy and intake-architecture task. The policy is
documented in `docs/ai_research_source_policy.md`, and DEC011 records the
accepted direction.

## User Decisions

- Default `40/30/30` forecasts should render as "forecast unavailable."
- Build a real Monte Carlo simulation instead of keeping the deterministic curve.
- Use online source research for Squad & Style, ratings, injuries, lineups,
  rosters, managers, and tactical news.
- Browser automation and scraping are allowed.
- Individual AI claims do not need one-to-one displayed URL citations, but the
  collection run should retain source metadata for audit.
- Last-minute freshness window is 3 hours before the first game of the day's
  `jornada`.

## Recommended Source Stack

- World Football Elo for national-team ratings.
- FIFA official sources for squads, rankings, and tournament facts.
- `soccerdata` as the first no-cost Python extraction layer for FBref,
  Sofascore, WhoScored, ClubElo, and related public sources where coverage is
  adequate.
- Sportmonks as preferred structured provider.
- API-Football as structured fallback.
- Transfermarkt for market values.
- Wyscout, Opta/Stats Perform, or paid StatsBomb/event feeds for reliable PPDA,
  field tilt, and deep event-style metrics.
- Browser automation over official/team/news pages for late tactical and injury
  updates.

## Handoff to Data Pipeline Engineer

Next implementation should be T-028/T-039 before full collector wiring because
T-027 is now complete:

- T-039: evaluate the no-cost football-data path and PPDA/field-tilt proxy
  feasibility.
- T-036: prototype source-backed research collection for one fixture.
- T-037: replace deterministic progression with a real Monte Carlo simulation.

Do not overwrite `summary.json`. Use `briefing.json` or a documented cache for
source-backed research.

Do not use ClubElo as the national-team rating source. If ClubElo is used later,
limit it to a player-club-strength blend after player-to-club and starting-XI
mapping are reliable.

## Handoff to Frontend Engineer

T-028 is complete and now renders:

- `forecast unavailable` when the default forecast is the only data,
- missing Squad & Style fields as unavailable,
- true Monte Carlo only after T-037 produces random-trial results,
- baseline-only briefing status through the summary payload. T-033 should add
  the dedicated briefing route and full freshness UI.

## Handoff to QA

Future checks should verify:

- no `40/30/30` default renders as a real forecast,
- Monte Carlo output includes simulation count, generated time, rating source,
  model version, and seed,
- source-backed research records collection method and checked time,
- stale briefings are outside the 3-hour `jornada` window,
- PPDA and field tilt are not populated unless sourced or explicitly approximate.
