# T-038 Squad & Style Source Methodology

Last updated: 2026-06-19
Task: T-038 - Source-Backed Squad & Style Metrics Integration
Owner: Football Data Scientist
Scope: Methodology and source policy only. This document does not change
frontend, backend, pipeline code, or checked-in `metrics.json` values.

## Purpose

T-039 removed ratings as the main blocker by adding the World Football Elo cache.
T-038 should now focus on `metrics.json.team_metrics`, especially the Squad &
Style fields shown in Match Analysis.

The first implementation must be conservative:

- Do not invent values.
- Do not copy existing static profile values forward as sourced facts.
- Write a numeric field only when the source and date/window support that exact
  field.
- Render unsupported fields as unavailable with `source_label=missing`.
- Label current checked-in values without source records as
  `source_label=hardcoded_reference`.
- Keep historical StatsBomb/BigQuery values out of current `team_metrics`; if
  used as context, label them `source_label=proxy_historical`.
- For no-cost PPDA or field-tilt proxies, write both `source_label=web_researched`
  and an explicit `approximation_method`.

## Current State

The active `metrics.json.team_metrics` contract contains 15 numeric fields per
team. Some active fixtures have full local profile values and some have empty
objects. For T-038, full local profiles without source records are not
source-backed; treat them as `hardcoded_reference` until replaced field by field.

Runtime World Football Elo values are separate from `team_metrics`. They may be
shown in Squad & Style, but their accepted source path is already T-039:
`source_label=web_researched` when read from
`data/source_cache/world_football_elo/latest_ratings.json`, and
`source_label=hardcoded_reference` only when the local fallback is used.

## Source Hierarchy

Use source paths in this order when building T-038 fields:

| Priority | Source path | Use | Label rule |
|---|---|---|---|
| 1 | FIFA official squad pages/PDFs or structured provider squad endpoints | Squad age and official roster context. | `web_researched` when cached with URL/path, retrieval time, and squad status. |
| 2 | Transfermarkt national-team pages | Squad market value and fallback squad age only when page/date/currency are captured. | `web_researched`; otherwise `missing`. |
| 3 | `soccerdata` FBref, then Sofascore, then WhoScored coverage probes | Team match aggregates such as shots, passes, possession, and explicit xG where columns exist. | `web_researched` per field and per window; otherwise `missing` or `blocked`. |
| 4 | T-039 World Football Elo cache | Rating display only, not style fields. | `web_researched` for cache-backed ratings; `hardcoded_reference` for local fallback ratings. |
| 5 | Existing checked-in metric values | Compatibility display until replaced. | `hardcoded_reference`; not enough for T-038 source-backed completion. |
| 6 | StatsBomb/BigQuery historical proxy matches | Visual context only. | `proxy_historical`; do not merge into current `team_metrics`. |

Browser automation and scraping are allowed only under the T-035 source policy:
no login/paywall/anti-bot bypass, raw snapshots cached, and every source record
must include source name, URL or path, checked time, collection method, status,
warnings, and blocked reasons.

## Field-Level Classification

The implementation should evaluate each field independently. A team can have a
partial sourced profile; missing fields should remain unavailable rather than
blocking sourced fields that did pass review.

| `team_metrics` field | First acceptable no-cost source | Allowed field label now | Missing rule |
|---|---|---|---|
| `squad_market_value_m` | Transfermarkt national-team squad/market-value page with cached page, currency, and as-of date. | `web_researched`; existing unsourced values are `hardcoded_reference`. | `missing` if no cached public value, currency, or date. |
| `average_age` | FIFA official squad list with birth dates or ages; structured provider squad endpoint; Transfermarkt only as fallback if cached. | `web_researched`; existing unsourced values are `hardcoded_reference`. | `missing` if the current senior squad cannot be identified or the roster status is ambiguous. |
| `goals_per_90` | Final senior national-team match results over a declared recent-match window. | `web_researched`; existing unsourced values are `hardcoded_reference`. | `missing` if the window cannot be sourced or normalized. |
| `goals_conceded_per_90` | Same results window as `goals_per_90`. | `web_researched`; existing unsourced values are `hardcoded_reference`. | `missing` if the window cannot be sourced or normalized. |
| `shots_per_90` | FBref/Sofascore/WhoScored team match stats with shot totals for the declared window. | `web_researched`; existing unsourced values are `hardcoded_reference`. | `missing` if shot columns are absent or coverage is incomplete for the team/window. |
| `shots_against_per_90` | Same stats source/window, using opponent shots. | `web_researched`; existing unsourced values are `hardcoded_reference`. | `missing` if opponent shot columns are unavailable. |
| `shots_on_target_pct` | Explicit shots-on-target and total-shots columns from the same stats window. | `web_researched`; existing unsourced values are `hardcoded_reference`. | `missing` if either numerator or denominator is missing. |
| `possession_avg` | FBref/Sofascore/WhoScored possession percentage over the declared window. | `web_researched`; existing unsourced values are `hardcoded_reference`. | `missing` if possession is absent or mixes incompatible competitions/windows. |
| `pass_completion_pct` | Completed and attempted passes, or explicit completion percentage, over the declared window. | `web_researched`; existing unsourced values are `hardcoded_reference`. | `missing` if pass completion is unavailable. |
| `passes_per_90` | Attempted passes over the declared window. | `web_researched`; existing unsourced values are `hardcoded_reference`. | `missing` if attempted pass totals are unavailable. |
| `expected_goals_per_90` | Explicit team xG column from FBref or another documented source. | `web_researched`; existing unsourced values are `hardcoded_reference`. | `missing` if xG is not explicitly provided; do not infer from goals or shots. |
| `expected_goals_conceded_per_90` | Explicit opponent xG or xGA column from the same source/window. | `web_researched`; existing unsourced values are `hardcoded_reference`. | `missing` if xGA is unavailable. |
| `xg_per_shot` | Explicit xG and shot totals from the same source/window. | `web_researched`; existing unsourced values are `hardcoded_reference`. | `missing` if either xG or shots are missing; do not approximate from goals. |
| `field_tilt_pct` | No true no-cost source approved. May use aggregate attacking-third touches or final-third passes only when both teams have matching source columns. | `web_researched` plus `approximation_method=field_tilt_proxy_attacking_third_touches` or `approximation_method=field_tilt_proxy_final_third_passes`; existing unsourced values are `hardcoded_reference`. | `missing` unless the proxy inputs are present and the UI/source metadata says proxy or estimate. |
| `ppda` | No true no-cost source approved. May use aggregate opponent passes divided by defensive actions only when all source columns exist. | `web_researched` plus `approximation_method=ppda_proxy_aggregate_defensive_actions`; existing unsourced values are `hardcoded_reference`. | `missing` unless all proxy inputs are present and the UI/source metadata says proxy or estimate. |

`proxy_historical` is not an acceptable label for current Squad & Style numeric
values. It remains valid for historical StatsBomb/BigQuery visual context, but a
historical proxy should not satisfy a missing current `team_metrics` field.

## Recent-Match Window Policy

For the safe first implementation, use one declared window for performance and
style aggregates:

- Default window: most recent 10 completed senior men's national-team matches
  before the fixture kickoff.
- Maximum lookback: 18 months before kickoff unless fewer than five matches are
  available, in which case record the smaller sample and add a warning.
- Include: World Cup, continental championship, qualifiers, Nations League, and
  senior international friendlies when the source classifies them as senior
  national-team matches.
- Exclude: youth, women's, club, training, abandoned, forfeited, and matches
  after the fixture kickoff.
- Penalty shootout goals are excluded from goals-for/goals-against.
- Extra-time handling must be explicit. If the source does not expose minutes,
  use regulation match count and record `minutes_basis=match_90_assumption`.

Do not mix windows silently. If one source only covers a different competition
or date range, either write a separate warning for that field or leave it
`missing`.

## Source Record Requirements

Every populated field should have source metadata, either in a future companion
manifest or a future `team_metric_sources` block. The minimum field-level record
is:

```json
{
  "field": "shots_per_90",
  "team": "Canada",
  "source_label": "web_researched",
  "status": "used",
  "source_name": "FBref via soccerdata",
  "source_url": "https://fbref.com/en/comps/1/World-Cup-Stats",
  "collection_method": "soccerdata_fbref_cache",
  "checked_at_utc": "2026-06-19T00:00:00Z",
  "window": {
    "match_count": 10,
    "starts_after": "2025-01-01",
    "ends_before_fixture": true,
    "minutes_basis": "match_90_assumption"
  },
  "approximation_method": null,
  "review_status": "football_reviewed",
  "warnings": [],
  "blocked_reasons": []
}
```

For `ppda` and `field_tilt_pct`, `approximation_method` must be non-null unless
a future paid/event source supplies the true metric. For `missing` fields, keep
the record short but explicit:

```json
{
  "field": "ppda",
  "team": "Canada",
  "source_label": "missing",
  "status": "missing",
  "approximation_method": null,
  "warnings": ["No event-level PPDA source and no approved aggregate proxy columns were available."],
  "blocked_reasons": []
}
```

## Sample Fixture Policy: `brazil_haiti_2026`

Use `Brazil` and `Haiti` as the first no-cost T-038 sample because the fixture
is in the current not-finished default workflow on 2026-06-19. Brazil has an
auditable Transfermarkt national-team profile header for the first two squad
fields. Haiti remains explicitly `missing` until a reliable national-team
profile source is identified.

Sample implementation policy:

1. Normalize both teams through `data/reference/team_identity.json`.
2. Keep Elo/rating separate from `team_metrics`.
   - Brazil and Haiti ratings can be `web_researched` only when read from the
     T-039 World Football Elo cache.
   - Do not call this row "Club Elo" in future UI or docs.
3. Try FIFA official squad pages/PDFs first for current squad birth dates.
   - If both teams have cached official squad lists, write `average_age` with
     `source_label=web_researched`.
   - If a squad list is unavailable, provisional, or not team-specific, leave
     `average_age` as `missing`.
4. Try Transfermarkt national-team pages for `squad_market_value_m`.
   - Write only if the page snapshot includes team, value, currency, and
     retrieval date.
   - Otherwise leave the field `missing`.
5. Use `soccerdata` FBref coverage first for recent senior national-team match
   stats. If FBref lacks the relevant team/window, probe Sofascore and
   WhoScored.
   - Write goals, goals conceded, shots, shots against, shots on target,
     possession, passes, and pass completion only for columns that exist and
     cover the declared window.
   - Do not backfill absent columns from local profile values.
6. For xG fields, require explicit xG/xGA columns from the same window.
   - If no explicit xG source is available, set
     `expected_goals_per_90`, `expected_goals_conceded_per_90`, and
     `xg_per_shot` to `missing`.
7. For `field_tilt_pct`, allow only these no-cost proxies:
   - `approximation_method=field_tilt_proxy_attacking_third_touches`
   - `approximation_method=field_tilt_proxy_final_third_passes`
   If neither source column set exists for both teams, set `field_tilt_pct` to
   `missing`.
8. For `ppda`, allow only:
   - `approximation_method=ppda_proxy_aggregate_defensive_actions`
   If opponent passes, attacking/middle-third tackles or equivalent defensive
   actions, and interceptions are not all present, set `ppda` to `missing`.
9. If a source blocks collection, record `status=blocked`, `source_label=blocked`,
   and the block reason. Do not retry through anti-bot bypass, login bypass, or
   proxy rotation.

Expected safe outcome for the first sample may be partial. A valid T-038 sample
can have `squad_market_value_m`, `average_age`, and simple match aggregates
source-backed while xG, PPDA, and field tilt remain unavailable.

## Decision and Handoff Suggestions

The Orchestrator should consider folding these items into governance docs after
T-038 implementation starts:

- Update the runtime data-quality wording from `static_curated` to
  `hardcoded_reference` for unsourced local team profiles, or add a decision
  explaining why both labels are kept distinct.
- Rename the Squad & Style rating row from "Club Elo Rating" to "World Football
  Elo Rating" when the T-039 cache is used.
- Add a companion source-manifest contract for `team_metrics` before broad
  writes, so source truth is not inferred from the existence of numeric values.
- Treat a partial field-level source-backed sample as acceptable for T-038
  phase progress; do not wait for true PPDA or true field tilt without an
  event/spatial provider.

## Verification

This methodology artifact is internally complete when:

- All 15 `team_metrics` fields have a field-level label rule.
- The rules include `web_researched`, `missing`, `hardcoded_reference`, and
  `proxy_historical` handling.
- Approximate PPDA and field tilt require explicit `approximation_method`.
- The sample fixture policy uses the no-cost T-039 path without inventing
  unsupported values.
- No frontend, backend, pipeline, or data JSON files are changed by this task.
