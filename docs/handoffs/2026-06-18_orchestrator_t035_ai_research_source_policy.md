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
- Sportmonks as preferred structured provider.
- API-Football as structured fallback.
- Transfermarkt for market values.
- Wyscout, Opta/Stats Perform, or paid StatsBomb/event feeds for reliable PPDA,
  field tilt, and deep event-style metrics.
- Browser automation over official/team/news pages for late tactical and injury
  updates.

## Handoff to Data Pipeline Engineer

Next implementation should be T-036 or T-037:

- T-036: prototype source-backed research collection for one fixture.
- T-037: replace deterministic progression with a real Monte Carlo simulation.

Do not overwrite `summary.json`. Use `briefing.json` or a documented cache for
source-backed research.

## Handoff to Frontend Engineer

T-028 should render:

- `forecast unavailable` when the default forecast is the only data,
- missing Squad & Style fields as unavailable,
- true Monte Carlo only after T-037 produces random-trial results,
- source/freshness status for briefings when T-033 is implemented.

## Handoff to QA

Future checks should verify:

- no `40/30/30` default renders as a real forecast,
- Monte Carlo output includes simulation count, generated time, rating source,
  model version, and seed,
- source-backed research records collection method and checked time,
- stale briefings are outside the 3-hour `jornada` window,
- PPDA and field tilt are not populated unless sourced or explicitly approximate.
