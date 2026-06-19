# DEC016 - Seeded Monte Carlo Tournament Simulation

Date: 2026-06-18
Status: Accepted
Task: T-037 - Real Monte Carlo Tournament Simulation

## Context

The active Match Analysis API previously exposed tournament progression values
from a deterministic Elo curve. T-028 correctly stopped labeling those values
as true Monte Carlo output, but T-037 required a real random-trial tournament
simulation with seed, trial count, model version, generated time, and rating
source metadata.

World Football Elo sourcing is not implemented yet. The only available runtime
rating input is the existing local Elo-style default map in
`SoccerDataClient.fetch_club_elo_ratings()`.

## Decision

Replace the active FastAPI progression calculation with
`src/analytics/monte_carlo_simulation.py`.

The simulation:

- uses `random.Random(seed)` for reproducible random trials,
- defaults to `10000` API trials,
- starts from `data/bracket/grid_state.json` plus the live/cached fixture list
  when available,
- derives current group standings from finished fixtures when available and
  simulates remaining group-stage fixtures,
- advances top two teams plus the best eight third-place teams into the
  existing Round-of-32 bracket template,
- simulates knockouts through the final,
- returns `group_advancement`, `r32`, `r16`, `qf`, `sf`, `final`, and `win`
  probabilities per team,
- exposes metadata through `monte_carlo_metadata`.

The API accepts optional `simulation_count` and `seed` query parameters. Requests
must use at least `10000` trials and are capped at `50000`.

## Provenance

Current rating source remains `hardcoded_reference`.

Teams missing local Elo entries receive a neutral `1500.0` rating fallback for
simulation continuity. This is recorded in metadata through `rating_status`,
`neutral_default_elo`, and `missing_rating_teams`.

T-039/T-038 remain responsible for replacing or validating the rating input with
source-backed World Football Elo/FIFA-approved sources.

## Consequences

- The frontend may again use "Monte Carlo" for the progression panel because
  the payload now comes from random trials.
- The UI must still surface that ratings are local hardcoded references.
- Existing frontend keys remain compatible; `group_advancement` and `r32` are
  additive for the 2026 format.
- Legacy Streamlit code remains reference-only and is not the production
  runtime.

## Verification

- Fixed-seed module reproducibility check.
- Direct metrics smoke check for `canada_qatar_2026`.
- `python3 -m compileall -q src`
- `npm --prefix src/frontend run build`
