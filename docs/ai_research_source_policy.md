# AI Research Source Policy and Data Intake Architecture

Last updated: 2026-06-18  
Task: T-035 - AI Research Source Policy and Data Intake Architecture  
Owner: Orchestrator  
Reviewers: Football Data Scientist, Data Pipeline Engineer, Frontend Engineer, QA / Reproducibility Engineer

## User Decisions Captured

The following policy decisions are accepted for the next implementation phase:

1. Default `40/30/30` forecasts should not render as probabilities. The UI should
   show "forecast unavailable" when only the default fallback exists.
2. The current deterministic progression panel should be replaced with a real
   Monte Carlo simulation, not merely renamed.
3. The project should go online for source-backed data and select the best source
   stack for forecast ratings, Squad & Style Comparison, injuries, lineups,
   rosters, managers, and tactical news.
4. Browser automation and scraping are allowed.
5. Individual current claims do not all require one-to-one URL-backed citation in
   the UI. The collection run should still retain source metadata so operators
   can audit what the AI reviewed.
6. "Last-minute" means a 3-hour freshness window before the beginning of the
   day's first game (`jornada`), not a broad all-day pre-generation.

## Source Policy

Browser automation and scraping are allowed, but the implementation must follow
these operating rules:

- Prefer official or structured sources before scraping HTML pages.
- Do not bypass logins, paywalls, anti-bot systems, or access controls.
- Cache raw source snapshots or API responses used for each run.
- Record source name, URL/path, retrieval time, collection method, status, and
  warning/block reason when available.
- Allow AI synthesis from a source set instead of requiring every displayed
  sentence to carry a separate URL.
- Treat unsupported facts as `missing` or `ai_inferred`, not confirmed.
- Keep `summary.json` as baseline preview content; current research belongs in
  `briefing.json` or a future research cache.

## Recommended Source Stack

No single source covers every data family needed by Match Analysis. Use a layered
stack.

| Data need | Recommended source | Why | Intake method | Label |
|---|---|---|---|---|
| Official squads, team facts, manager facts when available | FIFA official tournament pages and squad PDFs | Most authoritative for tournament roster context. | Browser/API/PDF extraction | `web_researched` or `live_schedule` |
| Official ranking sanity check | FIFA men's ranking | Official ranking baseline and fallback when Elo is missing. | Browser/API/PDF/CSV when available | `web_researched` |
| Model rating input | World Football Elo | Better suited than club Elo for national-team match strength. | Scrape/cache ratings table | `web_researched` |
| Lineups, injuries, squads, fixture statistics, formations | Sportmonks Football API | Broad structured API with lineups, injuries, squads, statistics, and xG-oriented endpoints on supported plans. | API | `web_researched` |
| Lower-cost structured fallback | API-Football | Broad fixture/team/player/lineup/injury coverage; useful fallback if Sportmonks plan or coverage is insufficient. | API | `web_researched` |
| Market value and squad value | Transfermarkt national team pages | Strongest public reference for market value and squad value. | Browser scrape/cache | `web_researched` |
| Deep event-style metrics: PPDA, field tilt, xG per shot, pressure, progressive actions | Wyscout, Opta/Stats Perform, StatsBomb paid/event feeds | Needed for reliable style metrics across competitions beyond the limited BigQuery/StatsBomb sample. | Paid API/export if available | `web_researched` |
| Historical visual proxies | Existing StatsBomb/BigQuery pipeline | Useful visual reference only; not enough for current broad tournament research. | Existing BigQuery path | `proxy_historical` |
| News, injury updates, tactical reports | Official federation/team pages, FIFA match centre, trusted news pages selected by browser search | Best for last-minute changes not captured in structured APIs. | Browser automation + source snapshot | `web_researched` or `ai_inferred` |

Recommended first implementation stack:

1. World Football Elo for forecast ratings.
2. FIFA official squad/ranking pages for official baseline facts.
3. Sportmonks as the primary structured data provider for squads, lineups,
   injuries, formations, and statistics if an API key/plan is available.
4. API-Football as the fallback structured provider.
5. Transfermarkt for market value and squad value.
6. Browser automation over official/team/news pages for late injury and tactical
   updates.
7. Keep StatsBomb/BigQuery as historical proxy visuals only.

## Squad & Style Comparison Intake

The current section needs these fields:

- `squad_market_value_m`
- `average_age`
- `possession_avg`
- `pass_completion_pct`
- `expected_goals_per_90`
- `expected_goals_conceded_per_90`
- `shots_per_90`
- `ppda`
- `field_tilt_pct`
- `goals_per_90`
- `goals_conceded_per_90`
- `shots_on_target_pct`
- `passes_per_90`
- `xg_per_shot`
- `shots_against_per_90`

Recommended field sources:

| Field group | Source plan |
|---|---|
| Squad value | Transfermarkt national team pages; fallback to `missing`. |
| Average age | FIFA squad list or structured provider squad endpoint; fallback to Transfermarkt if available. |
| Goals, goals conceded, shots, shots on target, passes, pass completion, possession | Sportmonks or API-Football fixture/team statistics over a configurable recent-match window. |
| xG, xGA, xG per shot | Sportmonks xG data if plan supports it; otherwise paid event provider or `missing`. |
| PPDA and field tilt | Paid event-level source preferred. If unavailable, do not fake these fields; show unavailable or approximate only with a separate `approximation_method`. |

Important product rule:

- Do not populate Squad & Style fields with invented values.
- If a provider does not support a field, set it to `missing` and let T-028 show
  the unavailable state.
- Approximate metrics must be labeled separately from sourced metrics.

## Real Monte Carlo Simulation Requirements

Replace the deterministic progression curve with a real simulation.

Minimum simulation contract:

- Use current tournament group/bracket structure.
- Use model ratings from the approved rating source, initially World Football Elo
  with FIFA ranking fallback.
- Simulate remaining group-stage matches and knockout matches.
- Run enough trials for stable UI output, for example 10,000 or more.
- Record simulation count, generated time, rating source, model version, and RNG
  seed.
- Return per-team probabilities for group advancement, Round of 32, Round of 16,
  quarterfinal, semifinal, final, and title.
- Label output as Monte Carlo only when random trials are actually used.

The current `compute_monte_carlo_probs()` deterministic curve should be removed
or renamed as an internal fallback once this is implemented.

## Last-Minute Briefing Window

Default briefing generation should target the daily `jornada`:

- Determine the first kickoff of the active match day.
- Treat briefings as fresh only if generated inside the 3-hour window before
  that first kickoff.
- Do not pre-generate all future fixtures as fresh briefings.
- If a briefing is outside that window, show `stale` or `baseline_only`.

Example:

- First game of the day kicks off at 12:00 local tournament time.
- Briefing generation window starts at 09:00.
- A briefing generated at 08:00 is not "last-minute"; it is stale or baseline
  support content.

## Proposed Research Payload

Future `briefing.json` or research-cache source record:

```json
{
  "source_id": "sportmonks-fixture-123",
  "source_name": "Sportmonks Football API",
  "source_url": "https://api.sportmonks.com/...",
  "collection_method": "api",
  "source_label": "web_researched",
  "checked_at_utc": "2026-06-18T15:00:00Z",
  "status": "used",
  "claim_scope": ["lineups", "injuries", "team_statistics"],
  "warnings": [],
  "blocked_reasons": []
}
```

Future derived claim record:

```json
{
  "claim_type": "injury_watch",
  "text": "Team news synthesis goes here.",
  "basis": "source_set",
  "source_ids": ["sportmonks-fixture-123", "official-team-news-456"],
  "confidence": "medium",
  "review_status": "draft"
}
```

## Implementation Routing

- T-028: show "forecast unavailable" for default `40/30/30`; show missing states
  for unavailable Squad & Style fields.
- T-037: build the real Monte Carlo simulation.
- T-036: prototype source-backed research collection for one fixture.
- T-038: integrate source-backed Squad & Style metrics.
- T-032/T-033: wire source-backed `briefing.json` generation/API/UI after the
  source collector is proven.

## References Checked

- FIFA official squad/ranking materials: `https://digitalhub.fifa.com/`,
  `https://inside.fifa.com/fifa-world-ranking/men`
- World Football Elo: `https://www.eloratings.net/`
- Sportmonks Football API docs/pricing: `https://docs.sportmonks.com/football/`,
  `https://www.sportmonks.com/football-api/pricing/`
- API-Football docs/pricing: `https://www.api-football.com/documentation-v3`,
  `https://www.api-football.com/pricing`
- Wyscout API docs: `https://apidocs.wyscout.com/`
- Stats Perform / Opta: `https://www.statsperform.com/opta/`
- Transfermarkt national team market values: `https://www.transfermarkt.us/`
