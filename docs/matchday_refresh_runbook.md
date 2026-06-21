# Matchday Refresh Runbook (Automated)

Last updated: 2026-06-20
Owner: Data Pipeline Engineer

The dashboard refreshes itself from a deterministic collector — no per-matchday
manual research. The collector pulls fixtures, venues, kickoff times, team style
metrics, and starting XIs from **ESPN's public soccer API**
(`site.api.espn.com`, no browser, no auth, not Cloudflare-blocked). FBref was
rejected because `soccerdata`'s FBref reader requires a headless Chrome and is
Cloudflare-gated; ESPN provides the same match stats over plain HTTP.

## One command

```bash
# dry-run (today)
python3 -m src.pipeline.collect_espn_matchday
# write caches for a date
python3 -m src.pipeline.collect_espn_matchday --date 20260620 --write
```

It writes, averaging each team's stats across all its tournament matches:

- `data/source_cache/squad_style/latest_metrics.json` — possession, shots/90,
  shots-on-target %, passes/90, pass completion %, goals/90, goals conceded/90,
  shots against/90 (averaged over the team's matches; the source label records
  the match count). ESPN does not expose xG, so xG/PPDA/field-tilt stay missing;
  the radar uses the four ESPN axes — possession, shots, shot accuracy, pass
  accuracy. `--season-start YYYYMMDD` sets the averaging window (default
  20260611).
- `data/source_cache/lineups/latest.json` — confirmed starting XI + formation.
- `data/matches/{match_id}/summary.json` — real `venue` + `kickoff_utc`.

Upcoming (not-yet-played) matches yield the fixture/venue/kickoff only; their
stats and lineups fill in once ESPN has the match data (≈kickoff onward), so a
re-run after kickoff refreshes them.

## Daily routine (what the scheduled agent runs)

```bash
cd <repo>
python3 -m src.pipeline.collect_espn_matchday --date $(date -u +%Y%m%d) --write
# (optional) also refresh the prior day in case late games finished
python3 -m src.pipeline.collect_espn_matchday --date $(date -u -d yesterday +%Y%m%d) --write
python3 -m src.pipeline.update_top_scorers --write     # Golden Boot leaders
python3 -m src.pipeline.update_standings --write       # group tables + bracket
python3 -m src.pipeline.update_team_ages --write       # squad average age
python3 -m src.pipeline.update_team_xg --write         # team xG (needs a browser)
# (optional) AI tactical headlines — needs Google Cloud credentials
python3 -m src.pipeline.generate_match_headlines --date $(date -u +%Y%m%d) --write
python3 -m compileall -q src && npm --prefix src/frontend run build
git add -A && git commit -m "Matchday refresh $(date -u +%F)" && git push origin main
gcloud builds submit --config cloudbuild.yaml .
```

## Pipeline suite (all ESPN/FotMob-derived, no manual research)

| Pipeline | Fills | Source | DEC |
|---|---|---|---|
| `collect_espn_matchday` | fixtures, venues, kickoffs, style metrics, lineups | ESPN | DEC025 |
| `update_top_scorers` | Golden Boot leaders (all tied) | ESPN keyEvents | — |
| `update_standings` | group tables + knockout bracket | ESPN scoreboard | DEC029 |
| `update_team_ages` | squad average age (48 teams) | ESPN athlete DOBs | — |
| `update_team_xg` | team xG/xGA per 90 (48 teams) | FotMob (headless) | DEC028 |
| `collect_rating_sources` | World Football Elo (forecast input) | eloratings.net | DEC017 |
| `generate_match_headlines` | AI tactical headline + insights | Gemini | DEC027 |

Each is dry-run by default, `--write` to persist, and runs in
`.github/workflows/matchday-refresh.yml`. The standings/scorers/age/xG writes are
surgical (they only touch their own keys/fields, so the others are preserved).

**On-demand (not in the daily Action — slow-changing):**
`update_team_market_value` writes squad market value (squad_style) and the
manager (lineups cache) from FotMob; the collector preserves the manager. Run it
periodically (e.g. weekly), not every matchday. See DEC030.

## AI tactical headlines (`generate_match_headlines.py`)

Replaces the "Baseline preview pending…" stub with a Gemini-written headline + 3
insights, grounded in each fixture's real data (Elo, win expectancy, ESPN
possession/shots/goals, formations). Low-cost model (`gemini-2.5-flash`,
override with `GEMINI_MODEL`); dry-run prints the assembled context, `--write`
calls the API and updates `summary.json` `ai_summary` (labelled
`headline_source: ai_generated`). Runs using ambient Google Cloud Application Default
Credentials (ADC) or a configured `GCP_SA_KEY` secret in GitHub Actions under the
`statsbomb-db` project. Without credentials the GitHub Action skips this step and
headlines stay as baseline stubs.

Group standings and the knockout bracket are now derived from ESPN by
`update_standings` into `grid_state.json` (see DEC029); the schedule view also
reflects the live feed at runtime.

## Verify (over HTTP, not just in-process)

```bash
python3 -m uvicorn src.api.main:app --host 127.0.0.1 --port 8090 &
curl -fsS "http://127.0.0.1:8090/api/match/{a_played_match}/summary"   # rosters present
curl -fsS "http://127.0.0.1:8090/api/match/{a_played_match}/metrics?simulation_count=10000&seed=1"
#   -> data_quality.radar_metrics.status == "available"; team_metrics populated
```

## Notes

- Team names are normalized via `src.common.team_identity` (handles ESPN's
  Türkiye / Curaçao / Côte d'Ivoire / Korea Republic spellings).
- Forecast is computed at runtime from World Football Elo (T-045) — no per-match
  forecast research.
- Pass % is computed from accurate/total passes (ESPN's `passPct` is a coarse
  rounded ratio).
- Decision record: `docs/decisions/20260620_DEC024_runtime_match_analysis_contracts.md`.
