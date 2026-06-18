# Last-Minute Match Briefing Generation Plan

Last updated: 2026-06-18  
Task: T-025 - Safe Last-Minute Match Briefing Generation Plan  
Owner: Data Pipeline Engineer  
Reviewers: Football Data Scientist, Frontend Engineer, QA / Reproducibility Engineer

## Objective

Separate long-lived baseline match previews from fresh matchday intelligence.

The current `summary.json` files are useful as baseline fixture previews, but
they should not be presented as last-minute AI analysis. The next pipeline
iteration should add a separate `briefing.json` artifact for near-kickoff
updates instead of overwriting curated `summary.json` content.

## Product Rule

Use two distinct editorial layers:

| Layer | File | Time horizon | Purpose |
|---|---|---:|---|
| Baseline preview | `summary.json` | Days or weeks before kickoff | Fixture facts, tactical baseline, expected formations, evergreen match framing. |
| Last-minute briefing | `briefing.json` | Same day or configurable pre-kickoff window | Fresh team news, injury/lineup deltas, model/provenance deltas, matchday tactical watchpoints. |

The UI must label these separately. If no fresh briefing exists, the app should
say baseline preview only instead of implying the content is current.

## Prerequisite: Baseline Fixture Folder

Last-minute briefing generation requires a fixture folder to exist first:

```text
data/matches/{match_id}/summary.json
data/matches/{match_id}/metrics.json
```

If a tournament match is not already represented by local files, T-034 must
discover the fixture and create baseline stubs before this briefing plan can run.
The briefing generator should not create baseline summary/metrics stubs itself.

## Planned `briefing.json` Contract

Path:

```text
data/matches/{match_id}/briefing.json
```

Proposed shape:

```json
{
  "metadata": {
    "schema_version": "1.0",
    "match_id": "england_croatia_2026",
    "generated_at_utc": "2026-06-17T12:00:00Z",
    "generator": "generate_match_briefings.py",
    "mode": "last_minute_briefing",
    "freshness": "fresh",
    "valid_until_utc": "2026-06-17T18:00:00Z",
    "briefing_window_hours": 3
  },
  "fixture": {
    "team1": "England",
    "team2": "Croatia",
    "date": "06/17/2026",
    "time": "18:00",
    "venue": "Stadium ...",
    "stage": "Group Stage - Group ..."
  },
  "team_keys": {
    "team1": "england",
    "team2": "croatia"
  },
  "briefing": {
    "headline": "",
    "short_context": "",
    "injury_watch": [],
    "tactical_updates": [],
    "three_keys": [],
    "operator_notes": []
  },
  "forecast_snapshot": {
    "dixon_coles_forecast": {},
    "score_probabilities": [],
    "forecast_status": "model"
  },
  "data_quality": {
    "team_metrics_status": "complete",
    "elo_status": "complete",
    "warnings": [],
    "blocked_reasons": []
  },
  "sources": [
    {
      "name": "summary.json",
      "path_or_url": "data/matches/england_croatia_2026/summary.json",
      "label": "static_curated",
      "status": "used",
      "checked_at_utc": "2026-06-17T12:00:00Z"
    }
  ],
  "review": {
    "status": "draft",
    "reviewer": null,
    "reviewed_at_utc": null,
    "notes": ""
  }
}
```

Field requirements:

- `metadata` records schema/version, generator, freshness, and validity.
- `fixture` copies `summary.metadata` fields. It must not be reparsed from the
  match ID.
- `team_keys` stores normalized slugs once so frontend/API code does not repeat
  fragile team-name parsing.
- `briefing` stores the reader-facing last-minute content.
- `forecast_snapshot` copies stored forecast fields and labels the status as
  `model`, `default`, or `missing`.
- `data_quality` records missing metrics, Elo gaps, default forecasts, blocked
  source checks, and other warnings.
- `sources` uses the project source labels documented in
  `docs/model_provenance.md`, including `live_schedule`, `static_curated`,
  `generated_model`, `default_forecast`, `hardcoded_reference`,
  `proxy_historical`, `web_researched`, `missing`, and `blocked`.
- `review` gates whether the briefing is draft, football-reviewed, or approved.

Required freshness values:

| Value | Meaning |
|---|---|
| `fresh` | Generated inside the configured briefing window and source checks succeeded. |
| `stale` | Existing briefing is outside the freshness window. |
| `baseline_only` | No briefing exists; use `summary.json` with explicit baseline labeling. |
| `blocked` | Briefing generation was attempted but required source access failed. |

## Generation Window

Default generation scope:

- Identify the active match date's `jornada`.
- Determine the first kickoff of that `jornada`.
- Generate fresh briefings only inside the 3-hour window before that first
  kickoff.
- Do not generate fresh briefings for all future static folders by default.

Configurable arguments for the future generator:

```bash
python3 src/pipeline/generate_match_briefings.py --dry-run --window-hours 3
python3 src/pipeline/generate_match_briefings.py --write --window-hours 3
python3 src/pipeline/generate_match_briefings.py --match-id england_croatia_2026 --dry-run
```

## Safety Rules

The implementation must obey these rules:

- Never overwrite `summary.json` as part of last-minute briefing generation.
- Write only `briefing.json` unless an explicit future task changes the
  contract.
- Default mode must be `--dry-run`.
- `--write` must be explicit.
- Dry run must show target files, freshness status, source status, and a compact
  diff or create/update/no-op summary.
- Existing fresh `briefing.json` files must be preserved unless
  `--force-refresh` is provided.
- Existing stale `briefing.json` files may be regenerated only with `--write`.
- Approved status is blocked when team metrics are empty, the forecast is the
  default 40/30/30 split, or Football Data Scientist review is missing.
- Failed source retrieval must produce a blocked/stale status, not invented
  last-minute news.
- Missing team metrics or default forecasts must be surfaced as warnings in
  `data_quality.warnings`.
- Generator output must include machine-readable validation results.

## Source Strategy

First implementation should be conservative:

- Always use local `summary.json` and `metrics.json` as baseline inputs.
- Read fixture/team names from existing `summary.json`; do not split match IDs.
- Use schedule/kickoff data from existing summary metadata or the live games
  API when available.
- Use live tournament API only for match status and schedule freshness.
- Do not claim lineup, injury, or news freshness unless a source was actually
  checked.
- Web/news source collection is approved under T-035.
- Every collection run must list sources in `sources[]` with URL/path, source
  name, retrieval time, status, and review metadata where available.
- Individual displayed AI claims do not require one-to-one URL citations, but the
  source set used by the run must be auditable.
- Browser automation or scraping is a collection mechanism, not a source label;
  the collected fact still needs source metadata.

## API and UI Follow-Up

Planned API route:

```text
GET /api/match/{match_id}/briefing
```

Planned response behavior:

- Return `briefing.json` when present.
- Return a generated baseline-only status when missing.
- Do not fail the whole Match Analysis tab because briefing data is missing.

Planned UI behavior:

- Show "Last-minute briefing refreshed X hours ago" for fresh briefings.
- Show "Baseline preview only" when no fresh briefing exists.
- Show blocked/stale source warnings in a compact operator-facing state.
- Keep baseline tactical sections separate from late deltas.

## Implementation Slices

Recommended follow-up tasks:

1. Build `generate_match_briefings.py` with dry-run validation and no default
   writes.
2. Add `briefing.json` schema validation.
3. Add `/api/match/{match_id}/briefing`.
4. Add Match Analysis UI freshness states.
5. Add an operator command to refresh the active `jornada` inside the 3-hour
   freshness window.
6. Add approved source-backed web research collection.

## Verification Criteria

T-025 is complete when this plan is documented and routed. Implementation tasks
are separate.

Future implementation is complete only when:

- Dry-run lists the intended `briefing.json` changes without writing files.
- Write mode creates or updates only `briefing.json`.
- `summary.json` and `metrics.json` remain unchanged during briefing
  generation.
- Fresh/stale/baseline-only/blocked states are testable with sample fixtures.
- Frontend build and Python compile pass.
- QA can inspect generated source/freshness metadata without reading logs.
