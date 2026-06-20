# DEC025 - Deterministic ESPN Matchday Automation

Date: 2026-06-20

## Status

Accepted.

## Context

Match Analysis sections (radar, Squad & Style, lineups) went stale every new
matchday because the data was filled by ad-hoc manual research. The goal is for
the dashboard to refresh itself.

A deterministic Python scraper was evaluated (FBref/Transfermarkt/eloratings per
an external blueprint). FBref is Cloudflare-gated: `soccerdata`'s FBref reader
requires a headless Chrome (`SessionNotCreatedException` without a browser), and
plain `requests`/`pandas.read_html` returns 403. That path needs heavy, fragile
browser infrastructure.

ESPN's public soccer API (`site.api.espn.com/.../soccer/fifa.world`) returns the
same match data over plain HTTP — no browser, no auth, not Cloudflare-blocked:
scoreboard (fixtures, real venue, UTC kickoff, score) and per-event boxscore
(possession, shots, shots on target, passes, accurate passes) plus rosters
(confirmed XI + formation). It does not expose xG.

## Decision

- Add `src/pipeline/collect_espn_matchday.py` as the deterministic matchday
  collector. For a date it writes, for each played match:
  the squad/style cache (style metrics), the lineup cache (XI + formation), and
  fixture `summary.json` (real `venue` + `kickoff_utc`). Dry-run by default;
  `--write` to persist. Team names normalized via `src.common.team_identity`.
- Align the radar to ESPN-provided metrics: `possession_avg`, `shots_per_90`,
  `shots_on_target_pct`, `pass_completion_pct`. xG and PPDA are dropped from the
  radar (ESPN does not provide them; FBref requires a browser).
- Pass completion % is computed from accurate/total passes (ESPN's `passPct`
  display value is a coarse rounded ratio).
- Automate via a daily GitHub Action (`.github/workflows/matchday-refresh.yml`)
  that runs the collector and pushes; a one-time Cloud Build push-to-`main`
  trigger (`docs/cloud_build_trigger_setup.md`) makes it deploy automatically.

## Consequences

- The dashboard refreshes per matchday with no manual research; running the
  collector across 06/14–06/21 populated all 48 teams with real style metrics,
  confirmed XIs, and real venues/kickoffs.
- xG, PPDA, and field tilt remain missing until an event-data provider
  (StatsBomb/Opta) or a browser-based FBref scraper is added.
- Style metrics are averaged across every match a team has played in the
  tournament window (the source label records the match count). Player clubs and
  manager names are not in ESPN's match feed, so clubs fall back to the frontend
  player→club map and manager stays blank.
- The deploy half of the chain requires a one-time GCP setup (Cloud Build
  trigger or a `GCP_SA_KEY` GitHub secret) that needs the project owner.

## Verification

- `python3 -m src.pipeline.collect_espn_matchday --date 20260620 --write`.
- Live Cloud Run revision `fifa-2026-dashboard-00024-mdz`: radar
  `status="available"`, rosters populated, real venue, for today's fixtures.
- `python3 -m compileall -q src`; `npm --prefix src/frontend run build`.
