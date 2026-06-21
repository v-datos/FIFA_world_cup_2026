# DEC029 - Deterministic Standings & Bracket Automation

Date: 2026-06-21

## Status

Accepted.

## Context

Group standings (P/W/D/L/GF/GA/GD/Pts for all 48 teams) and the knockout bracket
were hand-typed in `data/bracket/grid_state.json`, so they went stale after every
match — the same manual-data trap that affected top scorers, average age, and xG.
ESPN's public match feed already provides every result, so standings and bracket
progression can be derived automatically.

## Decision

Add `src/pipeline/update_standings.py`:

- Scans the ESPN scoreboard across the tournament window, computes each group
  table from match results, and sorts by the standard tie-breakers (points, goal
  difference, goals for).
- Resolves the knockout bracket (R32 → R16 → QF → SF → Final + third place)
  against the fixed 2026 slot topology, propagating winners/losers up the tree;
  unplayed ties stay as placeholder role names with `null` scores.
- Writes only the dynamic keys of `grid_state.json` (`groups`, `rounds`,
  `third_place`, and the flat `r32`/`r16`/`qf`/`sf`/`final`/`third` arrays the
  React bracket reads), preserving `tournament` and `top_scorer`.

Wired into `.github/workflows/matchday-refresh.yml` after the scorer step, run
with `|| true`. The frontend (`StandingsTab.tsx`) reads the flat arrays and falls
back to the nested `rounds`, so there is no regression.

## Consequences

- The Standings & Brackets tab refreshes itself every matchday; the last
  hand-typed dataset on the dashboard is now source-derived.
- The bracket topology (which group winners/runners-up/third-place feed which R32
  slot) is hardcoded. This is fixed tournament structure, not stale-prone data —
  only scores and qualified teams come from ESPN.
- **Caveat to validate when the group stage ends (~2026-06-26):** the
  third-place-qualifier → R32 assignment uses an allowed-groups heuristic, which
  may not perfectly match FIFA's official third-place combination table once the
  eight qualifying third-place teams are known. The bracket shows placeholders
  until then, so this only matters at knockout time.

## Verification

- `python3 -m src.pipeline.update_standings --write` → 104 matches, 72 group
  fixtures processed; group tables and bracket written.
- `python3 -m compileall -q src`; `npm --prefix src/frontend run build` pass.
- `/api/standings` returns `groups` (12) + flat `r32` (16) and the nested
  `rounds`; `StandingsTab.tsx` renders both.
