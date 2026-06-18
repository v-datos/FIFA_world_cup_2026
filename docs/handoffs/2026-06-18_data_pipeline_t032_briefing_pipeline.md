# Handoff - T-032 Last-Minute Briefing Pipeline Implementation

Date: 2026-06-18  
Owner: Data Pipeline Engineer  
Reviewers: QA / Reproducibility Engineer, Orchestrator  
Status: Complete

## Summary

Implemented the safe last-minute briefing artifact pipeline as a separate flow
from baseline preview generation.

New entrypoint:

```bash
python3 src/pipeline/generate_match_briefings.py --dry-run --window-hours 3
```

Write mode is explicit:

```bash
python3 src/pipeline/generate_match_briefings.py --write --window-hours 3
```

## What Changed

- Added `src/pipeline/generate_match_briefings.py`.
- Default mode is dry-run.
- `--write` is required to create/update `briefing.json`.
- Supported controls:
  - `--window-hours`
  - `--match-id`
  - `--active-date`
  - `--force-refresh`
  - `--cache-path`
  - `--data-dir`
  - `--now`
- Generator reads existing `summary.json` and `metrics.json`; it does not
  create baseline stubs.
- Generator writes only `data/matches/{match_id}/briefing.json`.
- Finished fixtures are skipped.
- Generation requires `source_status=not_finished` from live/cache schedule
  validation.
- Existing fresh briefings are preserved unless `--force-refresh` is supplied.
- `/api/match/{id}/summary` now reads `metadata.freshness` from generated
  briefing artifacts and derives source labels from `sources[]`.

## Current Artifact Behavior

The generated `briefing.json` contains:

- `metadata`
- `fixture`
- `team_keys`
- `briefing`
- `forecast_snapshot`
- `data_quality`
- `sources`
- `review`

The content is intentionally conservative. It uses local baseline summary and
metrics plus live/cache schedule validation. It does not claim fresh injury,
lineup, or tactical news because T-036 has not collected source-backed research
yet.

## Current Data Quality Result

The active day has four not-finished fixtures:

- `czech_republic_south_africa_2026`
- `switzerland_bosnia_and_herzegovina_2026`
- `canada_qatar_2026`
- `mexico_south_korea_2026`

Dry-run reported all four as `would_create` with `freshness=blocked`.

Reason:

- all four have empty `team_metrics`
- three use the default `40/30/30` forecast

This is expected and prevents draft artifacts from being presented as approved
last-minute analysis.

## Verification

Commands run:

```bash
python3 src/pipeline/generate_match_briefings.py --dry-run --window-hours 3
python3 src/pipeline/generate_match_briefings.py --dry-run --match-id england_croatia_2026 --now 2026-06-18T10:30
python3 src/pipeline/generate_match_briefings.py --dry-run --match-id brazil_haiti_2026 --now 2026-06-18T10:30
```

Temp write-mode checks:

- copied `data/matches` to a temporary directory
- ran `--write --match-id canada_qatar_2026`
- verified only `briefing.json` was created
- verified copied `summary.json` and `metrics.json` stayed byte-identical
- verified generated `briefing.json` parses as JSON
- verified existing fresh briefing preservation without `--force-refresh`

Build checks:

```bash
python3 -m compileall -q src
npm --prefix src/frontend run build
```

The frontend build passed with the existing chunk-size warning only.

## Not Included

- No production `briefing.json` files were written during closeout.
- No web/news research collection was implemented.
- No dedicated `/api/match/{match_id}/briefing` route was added.
- No Match Analysis freshness UI beyond the existing summary-level
  `briefing_status` compatibility was implemented.

## Next Routing

Next Orchestrator assignment:

- T-036 - Source-Backed Research Collector Prototype

Reason:

- T-032 created the safe storage and validation path.
- T-036 should now collect auditable source records and proposed current
  briefing content for one active fixture.

T-033 remains the API/UI follow-up for a dedicated briefing route and richer
Match Analysis freshness states.
