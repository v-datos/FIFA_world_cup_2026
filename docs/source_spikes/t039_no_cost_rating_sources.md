# T-039 No-Cost Rating Source Spike

Last updated: 2026-06-19
Owner: Data Pipeline Engineer

## Finding

World Football Elo is practical as the no-cost national-team rating source. The current cache parsed 244 ratings and covered 48/48 tournament teams.

FIFA ranking remains useful as an official sanity check and fallback reference, but the public page is a dynamic application. This spike captures update metadata instead of using FIFA as the primary machine-readable rating feed.

## Source Metadata

- World Football Elo source: `https://www.eloratings.net/World.tsv`
- World Football Elo checked at: `2026-06-19T02:57:16Z`
- World Football Elo last modified: `Fri, 19 Jun 2026 00:13:16 GMT`
- World Football Elo status: `used`
- World Football Elo parser version: `world_football_elo_tsv_v1`
- World Football Elo raw ratings snapshot: `data/source_cache/world_football_elo/raw/World.tsv`
- World Football Elo raw team dictionary snapshot: `data/source_cache/world_football_elo/raw/en.teams.tsv`
- FIFA ranking page: `https://inside.fifa.com/fifa-world-ranking/men`
- FIFA metadata status: `metadata_only`
- FIFA last update date: `2026-06-11T10:00:59.636Z`
- FIFA next update date: `2026-07-20T00:00:00.000Z`

## Coverage

- Tournament teams checked: 48
- World Football Elo matches: 48
- Missing teams: None

## Sample Tournament Ratings

| Rank | Team | Elo | Code |
|---:|---|---:|---|
| 1 | Spain | 2129 | ES |
| 2 | Argentina | 2128 | AR |
| 3 | France | 2084 | FR |
| 4 | England | 2055 | EN |
| 5 | Colombia | 1998 | CO |
| 6 | Brazil | 1978 | BR |
| 7 | Portugal | 1967 | PT |
| 8 | Netherlands | 1944 | NL |
| 9 | Germany | 1939 | DE |
| 10 | Norway | 1929 | NO |
| 11 | Japan | 1910 | JP |
| 12 | Ecuador | 1890 | EC |

## Recommended Cache Contract

- Cache parsed source rows in `data/source_cache/world_football_elo/latest_ratings.json`.
- Cache raw source snapshots in `data/source_cache/world_football_elo/raw/`.
- Keep `source_url`, `team_dictionary_url`, `checked_at_utc`, `source_last_modified`, `parser_version`, `status`, `warnings`, and `blocked_reasons` in metadata.
- Use World Football Elo ratings for model strength. Use FIFA ranking only for official sanity checks or fallback ranking context.
- Do not use ClubElo as a national-team source.

## Risks

- World Football Elo has no documented public API contract; the TSV path is public but could change.
- Fetch frequency should be low and cached; refresh once per matchday or before the 3-hour jornada window, not per API request.
- FIFA official ranking rows are not as easy to consume from a stable public data endpoint; use the page metadata and manual/automated browser verification until a stable official feed is identified.
