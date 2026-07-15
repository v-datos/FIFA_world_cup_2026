# T-039 No-Cost Rating Source Spike

Last updated: 2026-07-15
Owner: Data Pipeline Engineer

## Finding

World Football Elo is practical as the no-cost national-team rating source. The current cache parsed 0 ratings and covered 0/48 tournament teams.

FIFA ranking remains useful as an official sanity check and fallback reference, but the public page is a dynamic application. This spike captures update metadata instead of using FIFA as the primary machine-readable rating feed.

## Source Metadata

- World Football Elo source: `https://www.eloratings.net/World.tsv`
- World Football Elo checked at: `2026-07-15T07:07:51Z`
- World Football Elo last modified: `None`
- World Football Elo status: `blocked`
- World Football Elo parser version: `world_football_elo_tsv_v1`
- World Football Elo raw ratings snapshot: `None`
- World Football Elo raw team dictionary snapshot: `None`
- FIFA ranking page: `https://inside.fifa.com/fifa-world-ranking/men`
- FIFA metadata status: `metadata_only`
- FIFA last update date: `2026-06-11T10:00:59.636Z`
- FIFA next update date: `2026-07-20T12:00:00.000Z`

## Coverage

- Tournament teams checked: 48
- World Football Elo matches: 0
- Missing teams: Algeria, Argentina, Australia, Austria, Belgium, Bosnia and Herzegovina, Brazil, Canada, Cape Verde, Colombia, Croatia, Curacao, Czech Republic, Democratic Republic of the Congo, Ecuador, Egypt, England, France, Germany, Ghana, Haiti, Iran, Iraq, Ivory Coast, Japan, Jordan, Mexico, Morocco, Netherlands, New Zealand, Norway, Panama, Paraguay, Portugal, Qatar, Saudi Arabia, Scotland, Senegal, South Africa, South Korea, Spain, Sweden, Switzerland, Tunisia, Turkey, United States, Uruguay, Uzbekistan

## Sample Tournament Ratings

| Rank | Team | Elo | Code |
|---:|---|---:|---|

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
