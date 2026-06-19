# DEC017 - World Football Elo Cache for No-Cost Rating Inputs

Date: 2026-06-19  
Task: T-039 - No-Cost Football Data Source Spike  
Status: Accepted  
Owner: Orchestrator  
Reviewers: Football Data Scientist, Data Pipeline Engineer

## Context

The project needed to replace hardcoded national-team rating inputs before
source-backed match analysis could advance. Review comments proposed free
football data sources such as FBref, Sofascore, WhoScored, `soccerdata`, and
ClubElo, but ClubElo is a club rating source and should not be used as the
primary national-team model input.

T-037 already implemented a real seeded Monte Carlo tournament simulation, but
its rating inputs were still local fallback references. T-039 needed to find a
no-cost rating path that could support the simulation and API provenance labels
without fetching external pages on every user request.

## Decision

Use World Football Elo TSV data as the primary no-cost national-team rating
source.

The source is collected by:

```bash
python3 src/pipeline/collect_rating_sources.py --write
```

The collector writes:

- `data/source_cache/world_football_elo/latest_ratings.json`
- `data/source_cache/world_football_elo/raw/World.tsv`
- `data/source_cache/world_football_elo/raw/en.teams.tsv`
- `docs/source_spikes/t039_no_cost_rating_sources.md`

Runtime code reads the checked-in/cache artifact first through
`src.analytics.rating_sources`. `SoccerDataClient.fetch_club_elo_ratings()`
keeps its compatibility name but now prefers the World Football Elo cache before
falling back to local hardcoded reference ratings.

FIFA/Coca-Cola Men's World Ranking remains the official sanity-check/fallback
reference. Its public page is a dynamic app, so T-039 records page metadata
such as last and next official update dates instead of using it as the primary
machine-readable rating feed.

ClubElo is rejected as the national-team rating source. It may be evaluated
later only for a separate player-club-strength feature.

## Consequences

- Runtime Elo ratings can be labeled `web_researched` when cache-backed.
- Monte Carlo metadata can use `rating_source=world_football_elo` and
  `source_label=web_researched` when the cache covers all teams.
- Local hardcoded ratings remain a compatibility fallback only.
- The API must not fetch World Football Elo on each request.
- Refresh cadence should be once per matchday or before the 3-hour jornada
  window.
- T-038 can focus on Squad & Style metric sourcing instead of solving rating
  source selection again.

## T-039 Evidence

The accepted T-039 run parsed 244 World Football Elo rows and covered 48/48
current tournament teams through `data/reference/team_identity.json`.

Source metadata from the run:

- World Football Elo source: `https://www.eloratings.net/World.tsv`
- Team dictionary source: `https://www.eloratings.net/en.teams.tsv`
- World Football Elo last modified: `Fri, 19 Jun 2026 00:13:16 GMT`
- FIFA ranking page: `https://inside.fifa.com/fifa-world-ranking/men`
- FIFA last official update metadata: `2026-06-11T10:00:59.636Z`
- FIFA next official update metadata: `2026-07-20T00:00:00.000Z`

## Verification

- `python3 src/pipeline/collect_rating_sources.py --write`
- Direct cache coverage smoke check: 48/48 tournament teams matched.
- Direct metrics smoke check: Elo and Monte Carlo data-quality labels returned
  `source_label=web_researched` when cache values were present.
- `python3 -m compileall -q src`
- `npm --prefix src/frontend run build`
