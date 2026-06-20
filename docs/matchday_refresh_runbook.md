# Matchday Refresh Runbook (Automated AI Routine)

Last updated: 2026-06-20
Owner: Orchestrator / Data Pipeline Engineer
Purpose: One repeatable procedure the scheduled AI agent (and any operator)
runs each matchday so the dashboard self-updates. No ad-hoc research per day.

## Why this exists

The live feed (`worldcup26.ir`) auto-updates schedule and standings on Cloud Run,
but the *curated research caches* — real venues/kickoff times, probable XIs, and
squad/style metrics — are not in any live feed. Those are filled by AI web
research. This runbook makes that research a single, identical daily job instead
of a manual scramble each new matchday.

## When

Run once per day during the tournament, in the morning Edmonton time
(13:00 UTC ≈ 07:00 MT), before the day's first kickoff. Re-run after lineups are
confirmed (~1h before kickoff) if a fresh pass is wanted.

## Inputs to determine first

1. Active date = today (`America/Edmonton`).
2. The day's real World Cup fixtures: for each match, the two teams, group,
   real stadium + city, and kick-off time. Source: a current schedule
   (ESPN/Olympics/Wikipedia "2026 FIFA World Cup match schedule"). Convert each
   kickoff to UTC for `kickoff_utc`.

## Steps

1. **Fixtures.** For each of today's matches, ensure a folder
   `data/matches/{team1}_{team2}_2026/` exists (slugs via
   `src.common.team_identity.canonical_team_slug`). If missing, create
   `summary.json` (baseline-stub `metadata` + `ai_summary` + `data_quality`) and
   `metrics.json` (baseline stub). Set `metadata.date` = today `MM/DD/YYYY`,
   `metadata.venue` = "Stadium, City", and `metadata.kickoff_utc` = ISO UTC.
2. **Lineups.** For each team playing today, research the probable XI (formation,
   manager, 11 players ordered GK→DF→MF→FW, clubs where known). Write to
   `data/source_cache/lineups/latest.json` keyed by team slug. Set the formation
   so its first two numbers match the DF/MF row counts.
3. **Squad & Style.** For each team, research and write to
   `data/source_cache/squad_style/latest_metrics.json`:
   - `squad_market_value_m` (Transfermarkt / planetfootball WC ranking).
   - The four radar metrics from the team's most recent match report(s):
     `possession_avg`, `shots_per_90`, `expected_goals_per_90`,
     `expected_goals_conceded_per_90`. Early in a group (1 game), per-game ≈
     per-90. **All four are required for the radar to render** — fill them for
     both teams in a fixture or the radar stays unavailable for that match.
   - Average age and other fields where readily sourced; leave the rest missing.
4. **Standings.** If `worldcup26.ir` is unreachable, refresh
   `data/bracket/grid_state.json` group standings from a current results source
   (CBS/Wikipedia); reconstruct W/D/L from MP/PTS/GD. (When the live feed is
   reachable, Cloud Run recomputes standings automatically and this step is a
   no-op safety net.)

## Honesty rules (do not violate)

- Only write source-backed values; label `web_researched`.
- Never invent metrics. Pass completion % and PPDA are not reliably published for
  national teams — leave them out (the radar requires only the 4 sourceable
  axes; see DEC024).
- Predicted XIs are point-in-time; mark them as probable, refresh per matchday.

## Verify (gates, in order)

```bash
python3 -m compileall -q src
npm --prefix src/frontend run build
# Local HTTP smoke (route-level, not just in-process):
python3 -m uvicorn src.api.main:app --host 127.0.0.1 --port 8090 &
curl -fsS "http://127.0.0.1:8090/api/schedule"                          # today fixtures + kickoff_utc
curl -fsS "http://127.0.0.1:8090/api/match/{a_today_match}/summary"     # rosters present (not the cache)
curl -fsS "http://127.0.0.1:8090/api/match/{a_today_match}/metrics?simulation_count=10000&seed=1"  # team_metrics + radar available
```

Confirm: today fixtures have `kickoff_utc`; summary has `rosters`/`player_clubs`;
metrics `data_quality.radar_metrics.status == "available"` for today's matches.

## Ship

```bash
git add -A && git commit -m "Matchday refresh: <date>" && git push origin main
gcloud builds submit --config cloudbuild.yaml .
```

Then live smoke the Cloud Run URL (`/api/schedule`, one summary, one metrics) and
confirm the new revision serves the day's fixtures with rosters + radar.

## Pointers

- Forecast is computed at runtime from World Football Elo (T-045) — no per-match
  forecast research needed.
- Data contracts: `docs/data_contracts.md`. Provenance: `docs/model_provenance.md`.
- Decision record: `docs/decisions/20260620_DEC024_runtime_match_analysis_contracts.md`.
