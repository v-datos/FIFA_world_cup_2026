# Decision: Add Active Fixture Discovery and Baseline Stubs

Date: 2026-06-17  
Owner: Orchestrator  
Status: Accepted

## Context

The Match Analysis workflow currently depends on local static folders under
`data/matches/*_2026`. If a valid tournament game is not represented by a local
folder, it is not returned by `/api/schedule`, and direct summary/metrics routes
will not have files to serve.

The last-minute briefing plan requires a stable baseline fixture folder first.
Without active fixture discovery and baseline stub generation, tournament
progression would still require manual folder preparation.

## Decision

Add T-034: Active Fixture Discovery and Baseline Stub Generation.

The future pipeline will:

- Discover active-date or next-24-hour fixtures from
  `https://worldcup26.ir/get/games`.
- Fall back to `/tmp/games.json` when the live games API is unavailable.
- Create missing `data/matches/{match_id}/summary.json` and `metrics.json`
  baseline stubs only when `--write` is explicit.
- Preserve existing curated files.
- Label generated stubs as `baseline_stub`.
- Run before last-minute `briefing.json` generation.

## Baseline Stub Source Rules

Use schedule facts for:

- teams
- date
- time
- venue or stadium id
- stage/type/group

Use explicit placeholders for:

- tactical preview
- injury updates
- confirmed tactics
- exact scores
- team metrics

For current compatibility, stub `metrics.json` should keep the existing
numeric default forecast and six-score fallback shape, but the discovery
manifest must label those values as `default_forecast`, `empty_team_metrics`,
and `baseline_stub`. T-028 now makes fallback labels visible before this reaches
public UI as authoritative analysis.

Do not invent unavailable football intelligence during stub generation.

## Consequences

- T-034 becomes a prerequisite for T-032.
- T-027 is complete and centralizes team slugs/display names.
- T-028 is complete and renders stubbed metrics and missing forecasts as
  incomplete.
- T-040 adds lifecycle filtering: finished fixtures are skipped and must not
  receive last-minute briefing research.
- The app can eventually progress through the tournament without pre-creating
  every future match folder manually.

## References

- `docs/active_fixture_discovery_plan.md`
- `docs/last_minute_briefing_plan.md`
- `docs/data_contracts.md`
- `TASKS.md`
- `docs/phase_plan.md`
