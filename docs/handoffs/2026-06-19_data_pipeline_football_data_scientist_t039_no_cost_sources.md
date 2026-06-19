# Handoff - T-039 No-Cost Football Data Source Spike

Date: 2026-06-19  
From: Data Pipeline Engineer, Football Data Scientist  
To: Orchestrator, Frontend Engineer, QA / Reproducibility Engineer  
Status: Complete

## Summary

T-039 replaced the open question around hardcoded rating inputs with a concrete
no-cost rating source path.

World Football Elo is accepted as the primary national-team rating source.
FIFA/Coca-Cola Men's World Ranking remains an official sanity check and fallback
reference. ClubElo is not approved as a national-team rating source.

## Implemented Artifacts

- `src/analytics/rating_sources.py`
- `src/pipeline/collect_rating_sources.py`
- `data/source_cache/world_football_elo/latest_ratings.json`
- `data/source_cache/world_football_elo/raw/World.tsv`
- `data/source_cache/world_football_elo/raw/en.teams.tsv`
- `docs/no_cost_football_data_source_spike.md`
- `docs/source_spikes/t039_no_cost_rating_sources.md`
- `docs/decisions/20260619_DEC017_no_cost_rating_source_cache.md`

## Source Run Result

Command:

```bash
python3 src/pipeline/collect_rating_sources.py --write
```

Result:

- World Football Elo status: `used`
- Parsed rating rows: `244`
- Current tournament team coverage: `48/48`
- Missing tournament teams: none
- FIFA ranking metadata status: `metadata_only`
- World Football Elo last modified: `Fri, 19 Jun 2026 00:13:16 GMT`
- FIFA last official update metadata: `2026-06-11T10:00:59.636Z`
- FIFA next official update metadata: `2026-07-20T00:00:00.000Z`

Sample checked teams:

- Canada: `1777`
- Mexico: `1881`
- United States: `1780`
- Ivory Coast: `1743`
- Democratic Republic of the Congo: `1674`

## Runtime Impact

- `SoccerDataClient.fetch_club_elo_ratings()` now reads the World Football Elo
  cache first.
- Local hardcoded rating values remain fallback only.
- `/api/match/{match_id}/metrics.data_quality.elo_ratings` now reports
  `source_label=web_researched` when a cache-backed rating is used.
- Monte Carlo metadata now reports `rating_source=world_football_elo` and
  `source_label=web_researched` when cache coverage is complete.
- The collector defaults to dry-run and writes only when `--write` is explicit.

## Football Methodology Decisions

- Use World Football Elo for model strength because it rates national teams.
- Use FIFA ranking metadata as official context, not as the primary model scale.
- Do not convert FIFA ranking points to Elo without a future documented model
  decision.
- Do not use ClubElo as a national-team source.
- True PPDA and true field tilt still require event/spatial data. Aggregate
  no-cost proxies may be tested in T-038 only if they are clearly labeled with
  `approximation_method`.

## Verification

- `python3 src/pipeline/collect_rating_sources.py --write`
- Direct cache coverage smoke check: 48/48 tournament teams matched.
- Direct metrics smoke check: Elo and Monte Carlo data-quality labels returned
  `web_researched` where cache values were present.
- `python3 -m compileall -q src`
- `npm --prefix src/frontend run build`

## Next Step

Proceed to T-038 - Source-Backed Squad & Style Metrics Integration.

T-038 should use the T-039 findings:

- Start with no-cost/public sources only where field coverage is proven.
- Use missing states for unsupported fields.
- Label aggregate PPDA or field-tilt proxies explicitly as approximations.
- Keep paid event providers as the source for true PPDA, true field tilt,
  pressure, progressive actions, and spatial metrics unless a no-cost event feed
  is proven.
