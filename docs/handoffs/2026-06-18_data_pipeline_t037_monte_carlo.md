# Handoff - T-037 Real Monte Carlo Tournament Simulation

Date: 2026-06-18
Owner: Data Pipeline Engineer
Reviewers: Football Data Scientist, Frontend Engineer, QA / Reproducibility Engineer
Status: Complete

## Summary

The active FastAPI metrics route now uses a seeded random-trial tournament
simulation instead of the previous deterministic progression curve.

Default API behavior:

```bash
GET /api/match/{match_id}/metrics?simulation_count=10000&seed=20260618
```

## What Changed

- Added `src/analytics/monte_carlo_simulation.py`.
- Updated `/api/match/{match_id}/metrics` to accept `simulation_count` and
  `seed`.
- The simulation starts from `data/bracket/grid_state.json` plus the live/cached
  fixture list when available, derives current group standings from finished
  fixtures, simulates group advancement into the existing Round-of-32 template,
  and plays knockouts through the final.
- `monte_carlo_projections` now contains tournament-wide team probability maps.
- `monte_carlo_metadata` exposes simulation count, seed, generated time, model
  version, rating source, schedule source, and missing-rating caveats.
- `data_quality.monte_carlo_projections.status` is now `simulation` when the
  simulation payload is present.
- The React projection panel displays simulation count, seed, and the current
  hardcoded-reference rating provenance.

## Contract Notes

Compatibility keys preserved:

- `r16`
- `qf`
- `sf`
- `final`
- `win`

Additive keys:

- `group_advancement`
- `r32`

Metadata exposed:

- `method`
- `simulation_count`
- `seed`
- `generated_at_utc`
- `model_version`
- `rating_source`
- `rating_status`
- `neutral_default_elo`
- `missing_rating_teams`
- `schedule_source`
- `group_count`
- `team_count`

## Verification

Commands run:

```bash
python3 - <<'PY'
from src.analytics.monte_carlo_simulation import run_tournament_monte_carlo
first = run_tournament_monte_carlo(simulation_count=1000, seed=123)
second = run_tournament_monte_carlo(simulation_count=1000, seed=123)
assert first["probabilities"] == second["probabilities"]
assert first["metadata"]["method"] == "random_trial_monte_carlo"
PY

env MPLCONFIGDIR=/tmp/matplotlib-cache python3 - <<'PY'
from src.api.main import get_match_metrics
payload = get_match_metrics("canada_qatar_2026")
quality = payload["data_quality"]["monte_carlo_projections"]
assert quality["status"] == "simulation"
assert quality["simulation_count"] == 10000
assert quality["seed"] == 20260618
PY

python3 -m compileall -q src
npm --prefix src/frontend run build
```

Results:

- Fixed-seed module output was reproducible.
- Direct metrics smoke check returned `status=simulation`,
  `simulation_count=10000`, `seed=20260618`, and per-team probability values.
- Python compile passed.
- Frontend build passed with the existing chunk-size warning only.

## Not Included

- No live World Football Elo fetch was added.
- No FIFA ranking fallback was sourced.
- No stored `metrics.json` files were overwritten.
- No legacy Streamlit runtime changes were made.

## Next Routing

- T-039 should evaluate and cache source-backed World Football Elo/FIFA rating
  inputs.
- T-038 should replace hardcoded/empty Squad & Style metrics where provider
  coverage allows.
