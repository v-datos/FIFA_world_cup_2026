# T-039 No-Cost Football Data Source Spike - Football Methodology Note

Last updated: 2026-06-19  
Task: T-039 - No-Cost Football Data Source Spike  
Owner: Football Data Scientist  
Scope: Methodology and source feasibility only. Pipeline code, task routing, and
status closeout remain owned by the Orchestrator/Data Pipeline Engineer.

## Decision Summary

The no-cost path is viable for replacing the current hardcoded rating input, but
the first implementation should be narrow:

1. Use World Football Elo as the primary national-team rating source.
2. Use FIFA/Coca-Cola Men's World Ranking as the official fallback and sanity
   check.
3. Do not use ClubElo as a national-team rating source.
4. Treat `soccerdata` as a useful no-cost extraction wrapper for FBref,
   Sofascore, WhoScored, and ClubElo, but not as the rating authority.
5. Use no-cost aggregate sources for simple Squad & Style fields only where
   coverage is confirmed for the relevant national team, competition, and date
   window.
6. Keep true PPDA, true field tilt, pressure, progressive actions, and other
   event/spatial metrics unavailable unless event-level data is available.

## Implementation Result

The rating-source portion of this spike has been implemented.

- `src/pipeline/collect_rating_sources.py --write` fetches World Football Elo
  TSV data and writes an audited cache.
- `data/source_cache/world_football_elo/latest_ratings.json` is now the runtime
  cache for national-team ratings.
- Raw source snapshots are retained in
  `data/source_cache/world_football_elo/raw/`.
- The accepted run parsed 244 World Football Elo ratings and covered 48/48
  current tournament teams.
- FIFA/Coca-Cola Men's World Ranking metadata was captured as official context:
  last update `2026-06-11T10:00:59.636Z`, next update
  `2026-07-20T00:00:00.000Z`.

The Squad & Style metric portion remains routed to T-038.

## Rating Source Hierarchy

| Priority | Source | Product use | Source label | Notes |
|---|---|---|---|---|
| 1 | World Football Elo | Primary rating input for Dixon-Coles and Monte Carlo. | `web_researched` | Best fit because it rates national teams, not clubs. Cache the ratings table with retrieval time, source URL, parser version, and normalized team IDs. |
| 2 | FIFA/Coca-Cola Men's World Ranking | Official fallback and sanity check. | `web_researched` | Use when World Football Elo is missing, blocked, or stale. FIFA's page is official and currently exposes last/next update metadata. Ranking points are not the same scale as World Football Elo, so any conversion to model Elo must be documented. |
| 3 | Local checked-in last-good ratings cache | Offline continuity when source retrieval fails. | `web_researched_stale` or `hardcoded_reference` depending on cache provenance | If the cache was created from an auditable source run, label it stale web research with `checked_at_utc`. If it is manually typed, keep `hardcoded_reference`. |
| 4 | Neutral model fallback | Simulation continuity only. | `missing` plus `neutral_default` warning | Use only when no rated source exists. Do not present as a forecast-quality rating. |

Rejected as primary rating source:

- ClubElo. It rates clubs through `api.clubelo.com`, and the `soccerdata`
  wrapper returns club-level tables. It can be useful later for a
  player-club-strength feature, for example weighting a projected starting XI by
  club strength, but it should not replace World Football Elo for national-team
  match probabilities.

Required metadata for every rating run:

- `source_name`
- `source_url`
- `checked_at_utc`
- `collection_method`
- `parser_version`
- `team_id`
- `source_team_name`
- `rating_value`
- `rating_rank` when available
- `source_label`
- `status`
- `warnings`
- `blocked_reasons`

## No-Cost Source Feasibility

| Source | Best use | Fit for this project | Main risks |
|---|---|---|---|
| World Football Elo | National-team strength rating. | High for T-039. It directly matches the national-team rating need. | HTML/table format may change; cache and parser validation are mandatory. |
| FIFA ranking | Official fallback/sanity check. | High as official reference; medium as model input because point scale differs from World Football Elo. | Ranking update cadence may lag recent friendlies or matchday results. |
| `soccerdata` | Python wrapper for public football data sources. | High as a spike tool because it is already in `requirements.txt` and returns Pandas DataFrames. | It does not make unsupported competitions or blocked pages reliable. Each source/league must be tested explicitly. |
| FBref through `soccerdata` | Team season/match stats, schedule, passing/shooting/possession columns, xG where available. | Medium. Good for basic and some advanced aggregate fields when the competition is covered. Must verify 2026 international coverage before writing UI data. | Scraping can be blocked; international tournament coverage may be incomplete before or during the tournament. |
| Sofascore through `soccerdata` | Schedule/table and potentially match-level public data depending on supported competitions. | Medium as a fallback for schedules/basic match stats. | Coverage, terms, and endpoint stability need a live spike; source may not expose all needed aggregate columns. |
| WhoScored through `soccerdata` | Missing-player records and event stream data where available. | Medium-high for late injury/suspension checks and event-backed metrics when a match is covered. | Browser blocking/anti-bot risk; event feed availability for 2026 World Cup must be proven before relying on it. |
| worldfootballR | Reference implementation for extraction ideas. | Low for runtime; useful for comparing source coverage patterns. | Adds R runtime complexity and should not become production dependency without a separate decision. |

## Squad & Style Field Classification

| Field | No-cost status | Recommended source path | Labeling rule |
|---|---|---|---|
| `average_age` | Source-backed if squad list is available. | FIFA squad list first, then FBref/Transfermarkt-style squad pages if available. | `web_researched`; otherwise `missing`. |
| `squad_market_value_m` | Source-backed from public pages, but scrape-sensitive. | Transfermarkt national-team page with cached snapshot. | `web_researched` only when the page and currency/date are cached. |
| `goals_per_90`, `goals_conceded_per_90` | Source-backed from match results. | FIFA/Sofascore/FBref recent match window. | `web_researched`; include window size and competition filter. |
| `shots_per_90`, `shots_against_per_90`, `shots_on_target_pct` | Source-backed when aggregate match/team stats exist. | FBref or Sofascore. | `web_researched`; otherwise `missing`. |
| `possession_avg`, `pass_completion_pct`, `passes_per_90` | Source-backed when passing/possession tables exist. | FBref team match/season stats first; Sofascore fallback if equivalent columns exist. | `web_researched`; otherwise `missing`. |
| `expected_goals_per_90`, `expected_goals_conceded_per_90`, `xg_per_shot` | Source-backed only where xG tables exist for the national-team competition/window. | FBref if available; otherwise paid/event provider or unavailable. | `web_researched` when explicit xG columns exist; do not infer from goals/shots. |
| `field_tilt_pct` | Approximation only on the no-cost track. | FBref attacking-third touches or final-third passes if columns exist. | `approximation_method=field_tilt_proxy_*`; never label as true field tilt. |
| `ppda` | Approximation only on the no-cost track unless event data exists. | Aggregate proxy: opponent passes divided by defensive actions in attacking/middle thirds plus interceptions, only when all columns exist. | `approximation_method=ppda_proxy_aggregate_defensive_actions`; never label as true PPDA. |

Unavailable without event/spatial data:

- true PPDA,
- true field tilt,
- pressure regains,
- progressive passes/carries with reliable spatial definition,
- possession-chain value,
- line-breaking passes,
- pressing trap locations,
- formation heatmaps from tracking/event coordinates.

## Review Gates Before UI Use

No value from T-039 should appear as sourced in Match Analysis until these gates
pass:

1. Team names normalize through `data/reference/team_identity.json`.
2. Source snapshots are cached with retrieval time and parser version.
3. Coverage is checked for the specific national team, competition/date window,
   and metric columns.
4. The source payload records `used`, `missing`, `blocked`, or `stale`.
5. Any proxy field has an explicit `approximation_method` and UI copy that says
   "proxy" or "estimate."
6. A Football Data Scientist reviews the first generated sample for football
   plausibility before wider automation.
7. If a site blocks scraping, the collector records `blocked`; it must not
   switch to proxy rotation, login bypass, or anti-bot evasion.

## Recommended T-039 Data Pipeline Spike

The Data Pipeline Engineer should produce one sample cache for a single active
fixture/team pair:

1. Fetch World Football Elo ratings and normalize both teams.
2. Fetch FIFA ranking rows for both teams as fallback/sanity check.
3. Attempt `soccerdata` FBref coverage for the relevant international
   competition/window and report available columns.
4. Attempt Sofascore and WhoScored only as coverage probes; do not treat them as
   production sources until access and field stability are documented.
5. Emit a sample source manifest plus one small cached DataFrame per successful
   source.
6. Mark unsupported Squad & Style fields as `missing`, not estimated.

Success criteria:

- Current hardcoded rating input can be replaced for the sample fixture by a
  cached World Football Elo value or a documented FIFA fallback.
- Any remaining neutral rating fallback is explained by a source miss or block.
- The sample manifest shows which Squad & Style fields are source-backed,
  approximate, unavailable, stale, or blocked.

## References Checked

- World Football Elo: `https://www.eloratings.net/`
- FIFA/Coca-Cola Men's World Ranking:
  `https://inside.fifa.com/fifa-world-ranking/men`
- SoccerData documentation: `https://soccerdata.readthedocs.io/en/latest/`
- SoccerData FBref source:
  `https://soccerdata.readthedocs.io/en/latest/datasources/FBref.html`
- SoccerData Sofascore source:
  `https://soccerdata.readthedocs.io/en/latest/datasources/Sofascore.html`
- SoccerData WhoScored source:
  `https://soccerdata.readthedocs.io/en/latest/datasources/WhoScored.html`
- SoccerData ClubElo source:
  `https://soccerdata.readthedocs.io/en/latest/datasources/ClubElo.html`
