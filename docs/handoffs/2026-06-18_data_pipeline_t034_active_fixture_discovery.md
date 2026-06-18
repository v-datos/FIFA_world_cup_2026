# Handoff - T-034 Active Fixture Discovery and Baseline Stub Generation

Date: 2026-06-18
From: Data Pipeline Engineer / QA / Reproducibility Engineer
To: Orchestrator, Data Pipeline Engineer, Frontend Engineer, Football Data Scientist
Status: Complete

## Deliverables

- Added fixture discovery script:
  `src/pipeline/discover_active_fixtures.py`.
- Added explicit baseline fixture folder:
  `data/matches/brazil_haiti_2026/`.
- Added baseline stub files:
  - `data/matches/brazil_haiti_2026/summary.json`
  - `data/matches/brazil_haiti_2026/metrics.json`
- Updated routing and contract docs for 20 active fixture folders.

## Script Behavior

The script:

- defaults to dry-run;
- accepts `--dry-run` as a no-op for documented command compatibility;
- requires `--write` before creating fixture files;
- fetches `https://worldcup26.ir/get/games`;
- falls back to `/tmp/games.json` when the live API is unavailable;
- supports `--window-hours`, `--active-date`, and `--match-id`;
- normalizes team names and match IDs through T-027 helpers;
- skips unresolved placeholder teams such as `Winner Match 95`;
- skips finished fixtures after T-040 lifecycle filtering;
- emits a machine-readable JSON manifest;
- never overwrites existing `summary.json` or `metrics.json`.

## Generated Fixture

`Brazil vs Haiti` was present in the schedule for `06/19/2026 21:00` but had no
local fixture folder.

Write command used:

```bash
python3 src/pipeline/discover_active_fixtures.py --write --active-date 2026-06-19
```

Manifest result:

- `exists`: 3
- `created`: 1
- created match: `brazil_haiti_2026`

The live API was intermittently unavailable during verification, so the write
used the approved `/tmp/games.json` fallback cache.

## Stub Contract

The generated `summary.json`:

- uses canonical metadata for Brazil and Haiti;
- labels the payload as `baseline_stub`;
- contains explicit placeholder editorial copy;
- keys `injuries` and `confirmed_tactics` by canonical slugs: `brazil`,
  `haiti`.

The generated `metrics.json`:

- preserves the current default forecast compatibility shape;
- includes six exact-score fallback rows;
- has empty team metric objects for Brazil and Haiti;
- labels the stored payload as `baseline_stub`, `default_forecast`, and
  `empty_team_metrics`.

T-028 runtime API labels render this fixture as forecast/radar unavailable.

## Verification Run

- Dry-run for June 18 wrote no files and reported four existing fixtures.
- Dry-run for June 19 wrote no files and reported:
  - `exists`: 3
  - `would_create`: 1
- Write for June 19 created only `brazil_haiti_2026`.
- A second write for June 19 was idempotent and reported all four fixtures as
  existing.
- Stub schema assertions passed.
- API smoke check passed:
  - `/api/schedule` returns 20 fixtures.
  - `/api/match/brazil_haiti_2026/summary` returns `baseline_only`.
  - `/api/match/brazil_haiti_2026/metrics` returns unavailable forecast,
    unavailable exact scores, missing team metrics, and unavailable radar.
- `python3 -m compileall -q src`
- `npm --prefix src/frontend run build`

The frontend build passes with the existing large-chunk warning.

## Residual Risks

- `/tmp/games.json` is an operational fallback, not a durable source snapshot.
- The generated fixture is only a baseline anchor. It is not source-backed
  tactical analysis.
- T-032 must write fresh matchday `briefing.json` files without modifying
  baseline `summary.json` or `metrics.json`.
- T-031/T-038 must replace empty metric profiles with source-backed data where
  source coverage allows.

## Next Routing

Recommended next Orchestrator assignment:

T-032 - Last-Minute Briefing Pipeline Implementation.
