# DEC014 - Add Fixture Lifecycle Filter for Last-Minute Analysis

Date: 2026-06-18
Status: Accepted
Task: T-040 - Fixture Lifecycle Filter for Analysis and Briefing Scope

## Context

After T-034, the local Match Analysis set contained 20 fixture folders. Twelve
of those fixtures were already completed according to schedule date and/or the
live games feed. The app still exposed them through `/api/schedule` because the
route scans local folders, not fixture lifecycle.

That creates unnecessary work for the planned T-032 briefing pipeline. A
last-minute AI research run should not collect news, lineups, or tactical
updates for games that have already finished.

## Decision

Add a fixture lifecycle contract to `/api/schedule` and make the default
frontend analysis view use only not-finished games from the current active day.

Lifecycle values:

- `finished`
- `today`
- `upcoming`
- `unresolved`
- `archived`

Rules:

- Finished fixtures remain available as historical/post-match records through
  direct summary and metrics routes.
- Finished fixtures are excluded from default Match Analysis selection.
- Finished fixtures must be skipped by fixture discovery and T-032 briefing
  generation.
- The frontend day view shows only `lifecycle=today` fixtures.
- Future fixtures remain in local/API data but are not shown in the default day
  view to avoid clutter.
- T-032 may use next-24-hour upcoming fixtures for preparation only when
  explicitly in scope, but fresh last-minute status still follows the 3-hour
  `jornada` window.

## Consequences

- `/api/schedule` now returns lifecycle/source-status fields and schedule-level
  `active_date`, `default_match_id`, `lifecycle_counts`, and `briefing_window`.
- React no longer depends on a hardcoded `TODAY_DATE`.
- `discover_active_fixtures.py` skips finished fixtures in dry-run and write
  mode.
- T-032 must use `source_status=not_finished` as a hard generation gate.

## Verification

- API schedule smoke check showed:
  - `finished`: 12
  - `today`: 4
  - `upcoming`: 4
- Discovery dry-run for 2026-06-17 skipped four finished fixtures.
- Discovery dry-run for 2026-06-19 retained four not-finished fixtures.
- Frontend lint/build passed.
