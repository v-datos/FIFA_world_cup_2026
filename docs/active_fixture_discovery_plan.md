# Active Fixture Discovery and Baseline Stub Generation Plan

Last updated: 2026-06-18  
Task: T-034 - Active Fixture Discovery and Baseline Stub Generation  
Owner: Data Pipeline Engineer  
Reviewers: QA / Reproducibility Engineer, Frontend Engineer, Football Data Scientist
Status: Implemented 2026-06-18

## Objective

Make the tournament workflow resilient when a match is not already present in
the existing `data/matches/*_2026` folders.

The app currently lists analyzable matches by scanning local folders. If a
future fixture has no folder, `/api/schedule` will not list it and the Match
Analysis routes will not have `summary.json` or `metrics.json` to return.

The fix is implemented in `src/pipeline/discover_active_fixtures.py`. It can
create a minimal baseline folder before last-minute briefing generation runs.

Implementation result on 2026-06-18:

- The script found the missing resolved June 19 fixture from the schedule:
  Brazil vs Haiti.
- Explicit write mode created `data/matches/brazil_haiti_2026/summary.json`
  and `data/matches/brazil_haiti_2026/metrics.json`.
- Active schedule folders increased from 19 to 20.

## Dependencies

- Completed dependency: T-027 provides shared team display names, aliases,
  slugs, and multi-word country handling.
- Completed public UI gate: T-028 renders default forecasts and empty metrics as
  fallback/incomplete.
- Informed by: T-026, for model/default/provenance wording.
- Feeds: T-032 last-minute briefing generation, T-031 metrics completion, and
  T-033 briefing API/UI.

## Current Gap

Current behavior:

- `/api/schedule` scans `data/matches/` and returns only folders ending in
  `_2026` with a `summary.json`.
- `/api/match/{match_id}/summary` returns 404 if `summary.json` is missing.
- `/api/match/{match_id}/metrics` returns 404 if `metrics.json` is missing.
- The frontend day filter depends on local schedule payloads and a hardcoded
  active date.

Result:

- A valid tournament game that is not already represented by local static files
  is invisible to normal Match Analysis workflow.

## Source Hierarchy

Fixture discovery should use sources in this order:

| Priority | Source | Use |
|---:|---|---|
| 1 | `https://worldcup26.ir/get/games` | Primary schedule source for game id, teams, date/time, stage/type, group, status, and stadium id/name when available. |
| 2 | `/tmp/games.json` | Local cache fallback already used by `generate_match_previews.py` when the live games API fails. |
| 3 | Existing `data/matches/{match_id}/summary.json` | Preserve existing local fixture facts and curated baseline content. |
| 4 | `data/bracket/grid_state.json` | Fallback tournament/team context only; not a full fixture source. |
| 5 | Shared team identity registry from T-027 | Canonical display names, slugs, aliases, and flags. |

Do not split match IDs to recover team names. Read team names from the live
schedule payload or existing `summary.json`.

## Match ID Rule

Derive IDs with the shared T-027 slug helper:

```text
{team1_slug}_{team2_slug}_2026
```

Example:

```text
england_croatia_2026
```

Do not reimplement slug logic in the discovery script.

## Minimal Baseline Folder

Path:

```text
data/matches/{match_id}/
  summary.json
  metrics.json
```

The baseline folder is not a last-minute briefing. It exists so schedule,
summary, metrics, briefing, and UI flows have a stable fixture anchor.

## Minimal `summary.json` Stub

Data sources:

- `metadata.match_id`: generated from canonical team slugs.
- `metadata.team1`, `metadata.team2`: live games API display names, normalized
  through the T-027 registry.
- `metadata.date`, `metadata.time`: live games API `date`/`time`, or parsed
  from `local_date`.
- `metadata.venue`: live games API stadium name when available; otherwise
  `Stadium {stadium_id}`; otherwise `Venue TBD`.
- `metadata.stage`: live games API `type` and `group`, such as
  `Group Stage - Group A`; otherwise a title-cased type or `Stage TBD`.
- `ai_summary`: explicit baseline placeholder content, not invented analysis.

Example:

```json
{
  "metadata": {
    "match_id": "team1_team2_2026",
    "team1": "Team 1",
    "team2": "Team 2",
    "date": "06/20/2026",
    "time": "18:00",
    "venue": "Stadium 12",
    "stage": "Group Stage - Group A"
  },
  "ai_summary": {
    "key_headline": "Baseline preview pending for Team 1 vs Team 2",
    "injuries": {
      "team1": ["No verified baseline injury update is available yet."],
      "team2": ["No verified baseline injury update is available yet."]
    },
    "confirmed_tactics": {
      "team1": {
        "formation": "TBD",
        "philosophy": "Baseline tactical preview pending.",
        "manager": "TBD"
      },
      "team2": {
        "formation": "TBD",
        "philosophy": "Baseline tactical preview pending.",
        "manager": "TBD"
      }
    },
    "tactical_insights": [
      "Baseline preview has not been curated yet.",
      "Run last-minute briefing generation inside the match window for fresh updates.",
      "Treat model and team profile sections as unavailable until metrics are populated."
    ]
  },
  "data_quality": {
    "status": "baseline_stub",
    "sources": ["worldcup26.ir/get/games"],
    "warnings": ["Editorial preview pending."]
  }
}
```

`data_quality` is optional for current frontend compatibility, but should be
included for operators and future UI fallback states.

## Minimal `metrics.json` Stub

Data sources:

- Fixture teams: from the live schedule or existing summary.
- Forecast values: current-compatible default forecast shape only, labeled as
  fallback/default in the dry-run or write manifest.
- Exact scores: current-compatible default score list only, labeled as fallback.
- Team profiles: empty until T-031 fills or explicitly labels them.

Example:

```json
{
  "dixon_coles_forecast": {
    "team1_win": 0.4,
    "draw": 0.3,
    "team2_win": 0.3,
    "confidence": 0.7
  },
  "score_probabilities": [
    {"score": "1-0", "probability": 0.15},
    {"score": "1-1", "probability": 0.14},
    {"score": "0-1", "probability": 0.13},
    {"score": "2-1", "probability": 0.10},
    {"score": "0-0", "probability": 0.09},
    {"score": "1-2", "probability": 0.08}
  ],
  "team_metrics": {
    "Team 1": {},
    "Team 2": {}
  },
  "data_quality": {
    "status": "baseline_stub",
    "forecast_status": "default_forecast",
    "team_metrics_status": "empty_team_metrics",
    "warnings": [
      "Forecast not generated.",
      "Team metrics not populated."
    ]
  }
}
```

Current contract note:

- Existing active `metrics.json` files use numeric forecast fields and six score
  probabilities.
- The stub should preserve that shape because T-028 now handles fallback
  rendering through runtime `data_quality` labels.
- The generator manifest must label these values as `default_forecast`,
  `empty_team_metrics`, and `baseline_stub`.

Frontend behavior:

- T-028 prevents missing/stub forecasts from rendering as authoritative
  probabilities.
- T-028 prevents empty team metrics from rendering as neutral radar values.

## Procedure as Tournament Progresses

Daily or pre-match workflow:

1. Fetch live games from `worldcup26.ir/get/games`.
2. Determine the active generation window:
   - active match date
   - next 24 hours
   - optional explicit `--match-id`
3. Normalize team display names and slugs through the T-027 registry.
4. For each fixture in scope:
   - If folder exists, validate `summary.json` and `metrics.json`.
   - If the fixture is already finished, skip it. Finished games stay available
     as historical/post-match records but are not candidates for last-minute
     research.
   - If the fixture still contains unresolved placeholders such as `Winner`,
     `Runner-up`, or `???`, skip it until the live schedule has real teams.
   - If folder is missing, dry-run a baseline stub creation manifest.
   - If `--write` is explicit, create `summary.json` and `metrics.json`.
5. Run last-minute briefing generation from T-032 against fixtures that now
   have baseline folders.
6. API/UI from T-033 can then show:
   - fresh briefing
   - stale briefing
   - blocked briefing
   - baseline-only state

Suggested command shape:

```bash
python3 src/pipeline/discover_active_fixtures.py --dry-run --window-hours 24
python3 src/pipeline/discover_active_fixtures.py --write --window-hours 24
python3 src/pipeline/discover_active_fixtures.py --dry-run --match-id team1_team2_2026
python3 src/pipeline/discover_active_fixtures.py --write --active-date 2026-06-19
```

## Safety Rules

- Default mode is `--dry-run`.
- `--write` is required for file creation.
- Existing curated `summary.json` must never be overwritten by stub generation.
- Existing `metrics.json` must not be replaced unless a later explicit repair
  task allows it.
- Finished fixtures must be skipped in dry-run and write mode.
- Newly generated stubs must label themselves as `baseline_stub`.
- Stub generation must emit a machine-readable manifest with create/skip/block
  status and source provenance.
- The manifest should use labels including `live_schedule`, `generated_model`,
  `default_forecast`, `missing`, `blocked`, `empty_team_metrics`, and
  `baseline_stub`.
- If live API and cache both fail, block generation rather than guessing the
  fixture.

## Verification Criteria

Implementation is complete when:

- Dry-run writes no files.
- Write mode creates only missing fixture folders and their two baseline files.
- Existing curated active folders are not overwritten.
- Newly created `summary.json` files satisfy required metadata and
  `ai_summary` fields.
- Newly created `metrics.json` files satisfy required top-level shape and label
  default forecast/team metrics as stubs.
- Six score probabilities exist for current compatibility.
- T-028 prevents stub metrics from rendering as authoritative forecast/radar
  output.
- `python3 -m compileall -q src` passes.
- `npm --prefix src/frontend run build` passes.

## Completion Record

Completed on 2026-06-18.

Verified behavior:

- Default dry-run wrote no fixture files.
- June 19 dry-run reported three existing folders and one would-create folder:
  `brazil_haiti_2026`.
- June 19 write mode created exactly that folder and its two baseline files.
- A second June 19 write run was idempotent and reported all four June 19
  fixtures as existing.
- `/api/schedule` now returns 20 fixture folders.
- `/api/match/brazil_haiti_2026/metrics` reports the default forecast,
  exact-score list, team metrics, and radar as unavailable/missing through the
  T-028 runtime `data_quality` contract.
