# Handoff - T-040 Fixture Lifecycle Filter for Analysis and Briefing Scope

Date: 2026-06-18
From: Data Pipeline Engineer / Frontend Engineer
To: Orchestrator, Data Pipeline Engineer, Frontend Engineer, Football Data Scientist, QA / Reproducibility Engineer
Status: Complete

## Deliverables

- Updated `/api/schedule` in `src/api/main.py` to expose lifecycle/source
  status.
- Updated `src/pipeline/discover_active_fixtures.py` to skip finished fixtures.
- Updated React Overview and Match Analysis to show only current-day
  not-finished fixtures by default.
- Removed the stale hardcoded frontend `TODAY_DATE` filter.
- Added decision record:
  `docs/decisions/20260618_DEC014_fixture_lifecycle_filter.md`.

## API Contract

Each `/api/schedule` match now includes:

- `lifecycle`: `finished`, `today`, `upcoming`, `unresolved`, or `archived`
- `source_status`: `finished`, `not_finished`, or `unknown`
- `source_game_id`
- `is_finished`
- `is_today`
- `is_upcoming_24h`
- `is_briefing_candidate`

The schedule response also includes:

- `schedule_source`
- `active_date`
- `default_match_id`
- `lifecycle_counts`
- `briefing_window`

Past schedule dates are treated as finished even if the live/cache source omits
or stales the finished flag.

## Frontend Behavior

- Overview "Fixtures of the Day" renders only `lifecycle=today` matches.
- Match Analysis dropdown renders only `lifecycle=today` matches.
- The default selected match comes from `/api/schedule.default_match_id`.
- Finished fixtures are not deleted; they remain available through direct
  summary/metrics routes for historical or post-match work.

## T-032 Requirement

The briefing generator must:

- skip `lifecycle=finished` fixtures;
- require `source_status=not_finished` for research generation;
- keep finished games as historical records, not last-minute research targets;
- keep the 3-hour pre-first-kickoff `jornada` freshness rule.

## Verification Run

- `/api/schedule` smoke check:
  - `finished`: 12
  - `today`: 4
  - `upcoming`: 4
  - `default_match_id`: `czech_republic_south_africa_2026`
- `discover_active_fixtures.py --dry-run --active-date 2026-06-17` skipped
  four finished fixtures.
- `discover_active_fixtures.py --dry-run --active-date 2026-06-19` retained
  four not-finished fixtures.
- `python3 -m compileall -q src`
- `npm --prefix src/frontend run lint`
- `npm --prefix src/frontend run build`

The frontend build passes with the existing large-chunk warning.
