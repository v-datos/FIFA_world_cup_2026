# STATUS

## 2026-07-04 - Correct Knockout Stage Metadata and Translation

Prepared by: Orchestrator / Frontend Engineer / Data Pipeline Engineer

### Current State

- **Knockout Stage Sourcing**: Fixed `collect_espn_matchday.py` which was incorrectly labeling knockout matches as "Group Stage" by relying solely on the team-to-group mapping. Sourced match stage types dynamically from the live simulation games index (e.g. Round of 32, Round of 16, Quarterfinal).
- **Match stage translation**: Implemented `translateStage` in `translations.ts` and integrated it in `MatchAnalysisTab.tsx` and `OverviewTab.tsx` to automatically render translated Spanish stage descriptions (e.g. *Dieciseisavos de final*, *Octavos de final*, *Fase de grupos - Grupo B*) when toggled to Spanish.
- **Data Remediation**: Executed a correction script that aligned existing match folders on disk (`brazil_japan_2026`, `germany_paraguay_2026`, `netherlands_morocco_2026`, `south_africa_canada_2026`) with their true Round of 32 knockout stage headers.
- **Verification**: Verified that both backend compilation and frontend build pass with zero errors.

---

## 2026-06-29 - Fix Last Major Standing Metadata Gaps

Prepared by: Orchestrator / Frontend Engineer

### Current State

- **Last Major Standing Metadata**: Populated the hardcoded `LAST_MAJOR_STANDING` dictionary in `teamData.ts` to cover all 48 teams in the tournament (adding Germany, Paraguay, South Korea, Canada, Qatar, Switzerland, Brazil, Turkey, Haiti, etc.).
- **Tournament Standings Translation**: Updated `translateStanding` in `translations.ts` to translate additional international tournaments: OFC Nations Cup ("Copa de Naciones de la OFC"), UEFA Nations League ("Liga de Naciones de la UEFA"), and CONCACAF Gold Cup ("Copa Oro de la CONCACAF").
- **Verification**: Verified that the frontend builds successfully with `npm --prefix src/frontend run build`.

---

## 2026-06-24 - Fix Match Analysis Dashboard Panels

Prepared by: Orchestrator / Data Pipeline Engineer / Frontend Engineer / QA / Reproducibility Engineer

### Current State

- **ELO Ratings Cache Recovery**: Restored `latest_ratings.json` and raw TSV snapshots from git history after the automated refresh pipeline collected a Cloudflare anti-bot challenge page and committed/wiped out the ratings cache.
- **Automated Refresh Safeguard**: Added a check in `rating_sources.py` to prevent writing to disk if the parsed ELO rows are empty, ensuring a failed fetch/Cloudflare block will log a warning and preserve the existing valid cache rather than overwriting it.
- **National Team Fallback ELO**: Added Qatar to the `default_elo_ratings` fallback dictionary in `soccerdata_client.py` with an ELO of `1430` to prevent any future `null` resolution.
- **Squad/Style Cache Match ID Bypass**: Modified `_fixture_matches` in `squad_style_sources.py` to return `True` unconditionally. This allows team-level profile metrics (squad value, age, and style metrics) in the cache to apply to all matches (such as Bosnia-Qatar) rather than being locked to a single `fixture_ids` entry. This fixes the empty columns in the Squad & Style Comparison and the empty Radar comparison chart.

### Verification

- Syntax compile: `python3 -m compileall -q src` (PASS)
- Frontend build: `npm --prefix src/frontend run build` (PASS)
- Local metrics check: Querying `/api/match/bosnia_and_herzegovina_qatar_2026/metrics` returns a complete Dixon-Coles forecast, correct ELO ratings, and fully populated team metrics (possession, shots, passes, age, market value) for both teams (PASS).

---

## 2026-06-22 - Top Scorers Sync & Bracket Label Abbreviations

Prepared by: Orchestrator / Data Pipeline Engineer / Frontend Engineer / QA / Reproducibility Engineer

### Current State

- **Dynamic Top Scorers Integration**: Updated the FastAPI backend (`main.py`) to parse `home_scorers` and `away_scorers` fields directly from the simulated games database (`worldcup26.ir/get/games`). Top scorers are now aggregated on the fly at runtime, ensuring the Overview tab's card displays live goals correctly and matches the standings/bracket.
- **Data Pipeline Correction**: Refactored `src/pipeline/update_top_scorers.py` to query `worldcup26.ir/get/games` instead of ESPN. This aligns the fallback `grid_state.json` file with the custom tournament data rather than real-world 2022 historical stats.
- **Bracket tape label abbreviations**: Added an abbreviation utility (`abbreviatePlaceholder`) in `StandingsTab.tsx` to condense long placeholder strings on the blue tapes (e.g. `Winner Group A` -> `W G: A`, `Winner Match R32-2` -> `W M: R32-2`, `Loser Match SF-1` -> `L M: SF-1`).

### Verification

- Syntax compile: `python3 -m compileall -q src` (PASS)
- Frontend build: `npm --prefix src/frontend run build` (PASS)
- Local script dry-run: `python3 -m src.pipeline.update_top_scorers --write` (PASS - successfully updated local `grid_state.json`)

---

## 2026-06-22 - Match Analysis 70/30 Row Layout Adjustment

Prepared by: Orchestrator / Frontend Engineer

### Current State

- **Match Analysis 70/30 Row Layout**: Refined the Match Analysis tab layout on desktop viewports to group the "Key Insights, Injuries & Last Major Standing" card and the "Comparación de Rendimiento" (Radar) card in a single row. The Insights card occupies 70% of the row width (`lg:col-span-7`), and the Radar card occupies 30% of the row width (`lg:col-span-3`). Below them, the combined predictions card (`MatchPredictionGraph`) and the squad style comparison card (`SquadStyleComparison`) split the remaining width 50/50.

### Verification

- Syntax compile: `python3 -m compileall -q src` (PASS)
- Frontend build: `npm --prefix src/frontend run build` (PASS)

---

## 2026-06-21 - Spanish Localization & Automated Tactical Philosophies

Prepared by: Orchestrator / Frontend Engineer / Data Pipeline Engineer

### Current State

- **Match Analysis Layout Refinement**: Reorganized the Match Analysis tab to optimize page layout. Moved the "Key Insights, Injuries & Last Major Standing" card to a full-width container directly below the tactical headline, internalizing it as a responsive 3-column layout. Merged the "Match Outcome Probability" (Dixon-Coles) and the "Monte Carlo Projections" into a single, unified predictions card, placing it underneath the "Comparación de Rendimiento" (radar) card.
- **Spanish as Default Dashboard Language**: Changed the default dashboard language state to `'Español'` so that the user interface loads in Spanish by default, with all tabs, headlines, predictions, and squad style tables showing localized Spanish data on initial page load. Users can still toggle back to English at any time.
- **Responsive Mobile Sidebar Drawer**: Optimized the layout for mobile and tablet viewports. Introduced a sticky mobile top bar with a hamburger menu button to trigger the sidebar navigation. The sidebar now acts as a sliding overlay drawer from the left on smaller screens, supported by a dark blur backdrop and auto-closing triggers.
- **GCP Project Resolution & Translation Permission Fix**: Resolved a 403 Permission Denied error on Cloud Run where Vertex AI translation calls failed because they defaulted to the developer's legacy project ID (`statsbomb-db`). The backend (`main.py`) and pipelines (`generate_match_headlines.py`, `generate_team_news.py`) now dynamically resolve the project ID (`GEMINI_PROJECT` or `GOOGLE_CLOUD_PROJECT` or fallback to `midyear-castle-328020`), granting the Cloud Run service account proper access to the Vertex AI service.
- **Sidebar Toggle Relocation**: Relocated the EN/ES toggle from the top-right corner of the screen into the navigation sidebar directly below 'Tabla y Llaves' ('Standings & Bracket'). Supports fully responsive layouts for both expanded and collapsed sidebar states.
- **GitHub Actions & Auto-Deploy Validation**: Verified the end-to-end scheduled `Matchday Refresh` pipeline. Both scheduled workflows today (06:35 UTC and 13:34 UTC) completed successfully, updating the Elo ratings, xG metrics, and lineups cache, and committing/pushing changes. The push automatically triggered Cloud Build auto-deployments, which succeeded in deploying the fresh dashboard state to Cloud Run.
- **Complete Spanish Localization**: The Match Analysis tab now fully translates headlines, tactical insights, and team philosophies when toggled to Spanish. The backend `/api/match/{match_id}/summary` endpoint accepts a `lang` parameter and dynamically translates the English content into Spanish using Gemini.
- **Disk Caching for Translations**: Translations are cached locally as `data/matches/{match_id}/summary_es.json`. Subsequent requests load the cached file if the translation timestamp matches the current English headline, preventing redundant API calls and conserving quota.
- **Automated Web-Grounded Tactical Philosophy**: Lineup philosophies in the cache are no longer generic placeholders. If the cache contains generic text (e.g., "Confirmed XI from ESPN match data."), the API dynamically queries Gemini with Google Search grounding to generate a punchy 20-word system description under the team's manager, and caches it back to `data/source_cache/lineups/latest.json`.
- **Wired React UI**: Refactored frontend components (`MatchAnalysisTab.tsx`, `BriefingFreshnessBadge.tsx`, `MatchPredictionGraph.tsx`, etc.) to pass the active language to the backend and handle Spanish outcomes cleanly.

### Verification

- Syntax compile: `python3 -m compileall -q src` (PASS)
- Frontend build: `npm --prefix src/frontend run build` (PASS)
- Live deployment verification: Confirmed Uruguay-Cape Verde and Spain-Saudi Arabia matches load localized Spanish headlines, insights, and dynamic tactical philosophies from the cached/grounded endpoints.
- GitHub Actions verification: `gh run list --limit 5` confirms schedule-triggered Matchday Refresh runs succeed and trigger Cloud Build webhooks (PASS).
- Mobile & Tablet layout verification: Verified sidebar transition to slide drawer, hamburger overlay interaction, and responsive grids/charts on mobile viewport simulations (PASS).

---

## 2026-06-21 - Grounded Web Search for AI Tactical Previews

Prepared by: Orchestrator / Data Pipeline Engineer

### Current State

- Migrated `src/pipeline/generate_match_headlines.py` to the modern `google-genai` SDK, eliminating deprecated legacy `vertexai` warnings.
- Upgraded the AI headlines and insights generator to execute web-grounded Google Search research in a two-step sequence:
  1. Use the Google Search grounding tool to gather real-time tactical matchups, news, manager quotes, and form.
  2. Parse the research results alongside local metrics into a structured JSON tactical preview.
- **Refined Storytelling Rules:** Improved prompt instructions to enforce specific real-world storylines (e.g. recent draws with Cape Verde/Uruguay, player matchups like Lamine Yamal or strike partnerships like Isak/Gyökeres, manager updates like Georgios Donis's block or Koeman's verticality) rather than repeating dry, generic statistics (like possession % or shot volume).
- Implemented robust exception handling to fall back to structured-only preview generation if the grounded search fails or is blocked.
- Successfully verified execution on `netherlands_sweden_2026` and `spain_saudi_arabia_2026`, resulting in `"headline_source": "ai_web_grounded"` and rich tactical insights in their respective `summary.json` files.

### Verification

- Syntax compile: `python3 -m compileall -q src` (PASS)
- Frontend build: `npm --prefix src/frontend run build` (PASS)
- Execution: `python3 -m src.pipeline.generate_match_headlines --match-id spain_saudi_arabia_2026 --write` (PASS)
- Execution: `python3 -m src.pipeline.generate_match_headlines --match-id netherlands_sweden_2026 --write` (PASS)

---

## 2026-06-20 - T-050 Deterministic ESPN Matchday Automation

Prepared by: Orchestrator / Data Pipeline Engineer

### Current State

- The dashboard now refreshes itself each matchday. A deterministic collector,
  `src/pipeline/collect_espn_matchday.py`, pulls fixtures, real venues, UTC
  kickoffs, team style metrics, and confirmed starting XIs from ESPN's public
  soccer API (no browser, no auth). FBref was rejected: it is Cloudflare-gated
  and `soccerdata`'s reader needs a headless Chrome.
- Ran across 06/14-06/21: all 48 teams have real style metrics + lineups, and
  every fixture carries its real ESPN venue + `kickoff_utc`.
- The radar now uses ESPN-provided metrics (possession, shots/90, shot accuracy
  %, pass accuracy %); xG/PPDA are not exposed by ESPN and stay missing.
- Automation: `.github/workflows/matchday-refresh.yml` runs the collector twice
  daily, commits, and pushes. A one-time Cloud Build push-to-`main` trigger
  (`docs/cloud_build_trigger_setup.md`) closes the loop to auto-deploy.

### Verification

- Live Cloud Run revision `fifa-2026-dashboard-00024-mdz`:
  `germany_ivory_coast_2026` metrics radar `status=available` (Germany 64.6%
  poss / 26 shots / 46.2% SoT / 87% pass), summary rosters 11+11, venue
  "BMO Field, Toronto".
- `python3 -m src.pipeline.collect_espn_matchday --date 20260620 --write`.
- `python3 -m compileall -q src`; `npm --prefix src/frontend run build`.

### Routing

- Next: the project owner completes the one-time Cloud Build trigger setup
  (`docs/cloud_build_trigger_setup.md`) so refreshes auto-deploy; then validate
  the first scheduled GitHub Action run end to end. Optional collector
  enhancements: player clubs + manager names from ESPN, multi-game averaging,
  and an xG source.

---

## 2026-06-20 - Phase 5 Completed & Task T-019 Dropped

Prepared by: Orchestrator / Frontend Engineer / Data Pipeline Engineer

### Current State

- Phase 5 exit criteria have been fully met. The React dashboard is validated, streamlined, and fully in sync with the FastAPI backend.
- Task T-019 (Player Career-Stats Hover Endpoint) has been dropped to maintain simplicity, avoid dead backend code, and prevent adding GCP/BigQuery credential requirements.
- Completed all visual layout, API resilience, and legacy cleanup tasks. The project code is committed and pushed to `origin/main`.

### Completed This Update

- **Approved Drop of T-019 (DEC026)**: Dropped T-019 after verifying the frontend lineup pitch (`InteractivePitch.tsx`) doesn't show hover stats and the backend has no corresponding route.
- **Streamlit Legacy Disposition (T-030)**: Stopped the running Streamlit server process locally. The legacy Streamlit code in `src/app/` is retired/archived.
- **Resilient Schedule Fallback Match IDs (T-043)**: Resolved Nestor API schedule fallbacks using a committed games cache and folder scanning.
- **Standings & Bracket UI Rebaseline (T-049)**: Re-aligned the React bracket view to match the legacy Streamlit wood-board and tape layout.
- **Local preview verified**: Symbolic link created locally between `src/frontend/dist` and `src/api/static` to enable local serves.

### Next Sprint Priorities

- Phase 5 is closed out. All planned sprint tasks are either completed or dropped. No active priorities.

---

## 2026-06-20 - Hotfix: Summary Route Decorator + Full Live Deploy

Prepared by: Orchestrator / Data Pipeline Engineer

### Current State

- All of this session's work is deployed and verified live on Cloud Run
  revision `fifa-2026-dashboard-00021-z9r`.

### Hotfix

- The T-046 lineup helpers were inserted directly above `get_match_summary`,
  which left the `@app.get("/api/match/{match_id}/summary")` decorator bound to
  `load_lineup_cache`. The summary endpoint therefore served the raw lineup
  cache for every match and `get_match_summary` was never registered as a route,
  breaking the entire Match Analysis summary (headline, tactics, injuries,
  lineups) over HTTP. In-process calls still worked, which is why the earlier
  API-only check missed it.
- Fix: moved the route decorator back onto `get_match_summary`;
  `load_lineup_cache`/`apply_lineup_cache` are plain helpers.
- Process note: verify route-affecting changes over real HTTP, not only via
  in-process function calls.

### Live Verification (revision 00021)

- `/api/match/brazil_haiti_2026/summary`: full payload with `rosters` (Brazil 11,
  Haiti 11), formation 4-3-3, 17 player clubs.
- `/api/schedule`: 4 today fixtures with real venue + `kickoff_utc`.
- `/api/standings`: 32 matches; Group D USA 6 / Australia 3 / Paraguay 3 /
  Turkey 0. Live total goals is 95 (Cloud Run reaches worldcup26.ir and serves a
  live-feed recompute, one goal off the researched grid_state estimate of 96).
- `/api/match/united_states_australia_2026/metrics`: forecast 30.5/28.0/41.5,
  available.

---

## 2026-06-20 - T-048 Overview Real Fixtures, Stadium Links, Edmonton Time

Prepared by: Orchestrator / Data Pipeline Engineer / Frontend Engineer

### Current State

- The Overview "Fixtures of the Day" now shows the day's real 2026-06-20
  fixtures with clickable stadium links and Edmonton (Mountain) kickoff times.
  Previously the day view was empty because no fixture was dated today.

### What Changed

- Added fixture folders for the day's real matches: `netherlands_sweden_2026`,
  `germany_ivory_coast_2026`, `ecuador_curacao_2026`, `tunisia_japan_2026`, each
  with a real venue and a `kickoff_utc` field (derived from the published ET
  kickoff). Forecasts use the World Football Elo path; squad/style and curated
  tactics remain baseline until researched.
- `/api/schedule` now passes `kickoff_utc` through to each match.
- `OverviewTab` renders the venue as a Google Maps search link and the kickoff
  in `America/Edmonton` (MT) via `Intl.DateTimeFormat`, with a fallback to the
  stored local time string when no UTC kickoff exists.

### Verification

- In-process `/api/schedule`: 4 today fixtures with real venue + `kickoff_utc`.
- Browser Overview: Maps links resolve and times show 11:00 / 14:00 / 18:00 /
  22:00 MT (DST-correct); `python3 -m compileall -q src`; `npm run build`.

### Known Limitations

- Historical fixtures keep placeholder `Stadium N` venues and tz-less times;
  only fixtures with a `kickoff_utc` get Edmonton conversion.
- The new fixtures' lineups render only for teams already in the lineup/legacy
  rosters; Germany, Curacao, and Tunisia lineups are not yet sourced.

---

## 2026-06-20 - Match Analysis Real-Data Population + Standings Refresh

Prepared by: Orchestrator / Data Pipeline Engineer / Football Data Scientist / Frontend Engineer

### Current State

- The Match Analysis sections that previously rendered blank now show real,
  source-backed data; the Standings & Bracket tab is refreshed to the live
  2026-06-20 group results. worldcup26.ir remains unreachable, so all live data
  is served from refreshed local caches/fallbacks.

### What Changed

- **T-045 Match Outcome Probability (real forecast):** `/api/match/{id}/metrics`
  now computes an Elo-derived Dixon-Coles forecast from the World Football Elo
  cache when the stored forecast is the 40/30/30 stub, and keeps the top-level
  `score_probabilities` in sync. Forecast/score quality is labelled with the Elo
  rating provenance (`web_researched`) instead of `default_forecast`.
- **T-045 Squad & Style values:** researched squad market values for the current
  fixtures (US, Australia, Scotland, Morocco, Turkey, Paraguay, Brazil, Haiti)
  plus average ages where sourced, written into
  `data/source_cache/squad_style/latest_metrics.json`. Advanced style metrics
  (xG, PPDA, field tilt, possession) remain explicitly `missing`.
- **T-046 Squad lineups:** added `data/source_cache/lineups/latest.json` with
  source-backed matchday XIs (formation, manager, philosophy, ordered players,
  clubs). `get_match_summary` merges it into `ai_summary.confirmed_tactics` and
  adds slug-keyed `rosters` + a `player_clubs` map. `MatchAnalysisTab` reads
  API rosters first (legacy hardcoded map is fallback); `InteractivePitch`
  accepts a `playerClubs` prop.
- **T-047 Standings refresh:** updated `data/bracket/grid_state.json` group
  standings to the researched 2026-06-20 results (all 12 groups; 32 matches
  played, 96 goals). `/api/standings` and Overview tournament stats follow.

### Verification

- In-process API smoke: real forecast (US 31/28/42, Brazil 78/15/7), Squad
  market values flow into `team_metrics`, rosters of 11 per team, standings
  `matches_played=32`/`total_goals=96`.
- Browser preview: Match Outcome Probability, Squad & Style, and Standings tab
  render the real values; no console errors.
- `python3 -m compileall -q src`; `npm --prefix src/frontend run build`.

### Known Limitations

- Team Performance radar still needs advanced style metrics (xG/PPDA/possession)
  that are not freely sourceable for national teams; it stays partial/unavailable.
- Lineups are not browser-visible on 2026-06-20 because no fixture is dated today
  (the day-view filter hides finished fixtures and the live feed is down).
- Top scorer in `grid_state.json` remains a curated field (`L. Messi`, 3).

### Routing

- Next: research and add the current day's real fixtures plus real venues and
  kickoff times, then add the Overview stadium map link and Edmonton (MDT) time
  display.

---

## 2026-06-19 - T-044 Live Overview Tournament Stats Completed

Prepared by: Orchestrator / Data Pipeline Engineer / Frontend Engineer

### Current State

- T-044 is complete locally and verified in a browser preview; it is not yet
  deployed to Cloud Run.
- The Overview tab's Matches Played, Total Goals, and Top Scorers cards were
  hardcoded constants frozen "as of June 17." They are now live.

### What Changed

- `/api/standings` now returns a `tournament_stats` object: `matches_played`
  (`sum(p)//2`), `total_matches` (104), `total_goals` (`sum(gf)`),
  `goals_per_game`, and `top_scorer`. The first two are derived from the same
  live group standings that render the bracket, so they update together.
- Added a curated `top_scorer` field to `data/bracket/grid_state.json`; it flows
  through `/api/standings` because `load_live_bracket_state()` preserves
  grid_state top-level keys. No live scorers feed exists yet.
- `OverviewTab` now fetches `/api/standings` like `StandingsTab`, renders
  `tournament_stats`, and shows `—` until loaded. `App` passes `serverUrl` to it.
- Documented the new field in `docs/data_contracts.md`.

### Verification

- In-process `/api/standings` returned `matches_played=20`, `total_goals=62`,
  `goals_per_game=3.1`, `top_scorer={"name":"L. Messi","goals":3}` (matching the
  previously hardcoded values, now derived).
- Browser preview at `localhost:8080` rendered the three cards with the live
  values and no console errors.
- `python3 -m compileall -q src`; `npm --prefix src/frontend run build`.

### Routing

- To make this visible to live users, T-044 must ship in the next Cloud Run
  redeploy (same `gcloud builds submit` path as T-042).
- T-030 Streamlit disposition remains queued/backlog.

---

## 2026-06-19 - T-042 Live Deployment Execution - Cloud Run Verified

Prepared by: Orchestrator

### Current State

- T-042 Cloud Run deployment is complete and verified. The current React/FastAPI
  code (T-027 through T-041) is now live; `accionar.xyz` needs a browser refresh
  to confirm the embedded view, and a schedule-fallback follow-up is filed below.
- This executed the live deployment that the T-029 runbook flagged as a separate
  operator task.
- Root cause of the live drift identified: Cloud Run was frozen at revision
  `fifa-2026-dashboard-00017-6z7` (deployed 2026-06-17), which predates the
  T-027 team identity contract (2026-06-18). Every deploy since T-027 was
  un-deployable, and none had been attempted until now.
- The first Cloud Build failed at the Docker `frontend-builder` stage. The
  frontend imports the repo-canonical `data/reference/team_identity.json` via
  `../../../../data/...` in `src/frontend/src/lib/teamIdentity.ts`. The Docker
  stage only copied `src/frontend/`, so `tsc -b` raised TS2307 and
  `npm run build` exited non-zero.
- The local `npm --prefix src/frontend run build` gate did not catch this
  because it runs in the real repo where `data/` is a sibling of `src/frontend/`.
- Fixed the Dockerfile to mirror the repo layout inside `frontend-builder`
  (DEC023). The rebuilt Cloud Build passed the frontend stage and proceeded to
  backend assembly, image push, and Cloud Run deploy.

### Deployment Result

- Cloud Build `88ef8a94` succeeded in 7m17s.
- New revision `fifa-2026-dashboard-00018-tm5` serves 100% of traffic
  (previous: `fifa-2026-dashboard-00017-6z7`, the recorded rollback anchor).
- Deploy step emitted one non-fatal warning: it could not re-apply the
  `allUsers` -> `roles/run.invoker` IAM binding (the deploy account lacks
  `run.setIamPolicy`). The service-level binding already existed, so public
  access persists, confirmed by an unauthenticated `/health` 200.

### Cloud Run Verification (revision 00018)

- `/health` -> HTTP 200 `{"status":"ok"}` (unauthenticated).
- `/api/schedule` -> 20 matches, `lifecycle` and full schedule keys present
  (`active_date`, `briefing_window`, `lifecycle_counts`, `schedule_source`);
  old revision returned 19 matches and only `['matches']`.
- `/api/match/brazil_haiti_2026/summary` -> HTTP 200 (old revision: 404).
- `/api/match/brazil_haiti_2026/metrics` -> HTTP 200 with full `data_quality`,
  `monte_carlo` `rating_source=world_football_elo` at 10,000 sims, and Brazil
  `squad_market_value_m` `source_label=web_researched` (T-037/T-038/T-039 live).
- `/api/standings` -> HTTP 200.

### Findings / Residual Risks

- Schedule fallback gap (filed as T-043): `worldcup26.ir/get/games` is currently
  unreachable (HTTP 000 from both Cloud Run and a local check), and no games
  cache ships in the image. In that state `/api/schedule` returns
  `schedule_source=unavailable` with every `matches[].match_id` null. The
  `default_match_id` still resolves from local folders (so the default fixture
  loads and per-fixture routes work), but the day-view selector listing loses its
  IDs. This is pre-existing T-040 fallback behavior, not a deploy regression from
  the Docker fix, but it degrades the live selector while the upstream API is
  down.
- `accionar.xyz/dashboards/fifa-2026/` returns HTTP 200 and serves the portfolio
  SPA shell (its own bundle `index-DhXZeTZ5.js`, single `#root`). The dashboard
  view is rendered client-side and is expected to embed the now-updated Cloud Run
  service via iframe, but the rendered content was not browser-confirmed in this
  pass. Recommend a hard-refresh/incognito browser check.
- BigQuery/StatsBomb visualization routes were not live-verified (credential
  dependent).

### What Changed

- Fixed `Dockerfile` `frontend-builder` stage to include the team identity
  contract at its repo-relative path.
- Added DEC023:
  `docs/decisions/20260619_DEC023_docker_frontend_data_context.md`.
- Added a Docker frontend build-context section and a "local gate does not prove
  the Docker frontend build" caveat to
  `docs/deployment_operations_runbook.md`.
- Corrected stale T-033/T-038 future-tense feature notes in `README.md`.
- Updated `TASKS.md`, `STATUS.md`, and `docs/phase_plan.md` for T-042.

### Routing

- Next project step: **T-043 - Schedule Fallback Match IDs When Live API Is
  Unavailable**. This is now the highest-value step because it affects the live
  day-view selector while `worldcup26.ir` is down.
- **T-030 - Streamlit Legacy Disposition** is now unblocked: the live
  React/FastAPI deployment is verified, which was its stated precondition.
- Remaining T-042 follow-up: browser-confirm `accionar.xyz` reflects revision
  `00018` (or re-upload the static bundle if it hosts its own copy rather than
  embedding Cloud Run).

---

## 2026-06-19 - T-031 Active Match Metrics Completion Completed

Prepared by: Orchestrator / Data Pipeline Engineer / Football Data Scientist

### Current State

- T-031 is complete as an explicit unavailable-state preservation pass.
- No broad scraping was performed, and no checked-in
  `data/matches/**/metrics.json` fixture payloads were rewritten.
- The Squad & Style source cache now includes explicit missing rows for all
  active empty `team_metrics` gap teams, so API consumers can distinguish
  "checked locally and unavailable" from "cache missing or unchecked."
- The only source-backed Squad & Style values remain Brazil
  `squad_market_value_m` and `average_age` for `brazil_haiti_2026`.
- Default 40/30/30 forecasts remain `default_forecast` and unavailable; the
  Switzerland vs Bosnia and Herzegovina fixture keeps its non-default stored
  forecast while its team metrics remain missing.
- Football Data Scientist methodology rule: unavailable Squad & Style fields
  are a valid T-031 outcome when no approved source-cache record exists; they
  must stay `missing` until replaced field by field by reviewed source records.

### What Changed

- Extended `src.analytics.squad_style_sources` to return per-team manifest
  metadata for rows that have no source-backed field records.
- Updated `/api/match/{id}/metrics.data_quality.team_metrics[*]` missing states
  to include row-level `source_cache_status`, `missing_reasons`, and
  `blocked_reasons`.
- Expanded `data/source_cache/squad_style/latest_metrics.json` from the T-038
  Brazil/Haiti sample into an 18-team T-031 manifest covering the active
  empty-metric gaps with explicit `missing` rows.
- Added DEC022:
  `docs/decisions/20260619_DEC022_active_metric_gap_preservation.md`.
- Added handoff:
  `docs/handoffs/2026-06-19_data_pipeline_t031_active_metric_gap_preservation.md`.

### Verification

- `python3 src/pipeline/collect_squad_style_sources.py`
- `python3 -m json.tool data/source_cache/squad_style/latest_metrics.json`
- Direct API smoke:
  - `canada_qatar_2026`: forecast `unavailable/default_forecast`; Canada and
    Qatar team metrics `missing` with
    `no_approved_local_squad_style_source_cache`.
  - `brazil_haiti_2026`: forecast `unavailable/default_forecast`; Brazil
    partial with 2 source-backed fields; Haiti explicitly missing.
  - `switzerland_bosnia_and_herzegovina_2026`: forecast
    `available/hardcoded_reference`; both team metric profiles missing.
  - `argentina_algeria_2026`: full local profiles remain
    `hardcoded_reference`.
- `python3 -m compileall -q src`
- `npm --prefix src/frontend run build`
- `git diff --check`

### Routing

- Next project step: **T-030 - Streamlit Legacy Disposition**.
- Future Squad & Style value completion should add reviewed field-level source
  records to the source cache or a documented collector; unsupported fields
  should stay `missing` rather than being inferred from local profile defaults.

---

## 2026-06-19 - T-033 Briefing API and Match Analysis Freshness UI Completed

Prepared by: Orchestrator / Data Pipeline Engineer / Frontend Engineer

### Current State

- T-033 is complete.
- Match Analysis now has a dedicated briefing API contract instead of relying
  only on the compact `summary.briefing_status` compatibility field.
- Missing `briefing.json` files are safe: the API returns a `baseline_only`
  response that points back to `summary.json` as static curated preview content.
- Invalid briefing artifacts are downgraded to an explicit invalid fallback, and
  fresh artifacts whose `valid_until_utc` has expired are returned as `stale`.
- The frontend renders briefing freshness as a compact badge near the tactical
  headline while preserving the baseline preview content.

### What Changed

- Added `GET /api/match/{match_id}/briefing`.
- Centralized briefing-status derivation in `src/api/main.py`.
- Kept `/api/match/{match_id}/summary` compatible by attaching the same
  `briefing_status` summary.
- Added `BriefingFreshnessBadge` and wired Match Analysis to fetch the dedicated
  briefing endpoint with summary fallback behavior.
- Added DEC021:
  `docs/decisions/20260619_DEC021_briefing_api_freshness_contract.md`.
- Added handoff:
  `docs/handoffs/2026-06-19_data_pipeline_frontend_t033_briefing_api_freshness.md`.

### Verification

- Direct API smoke check for `brazil_haiti_2026` returned
  `freshness_state=baseline_only`, `artifact_status=missing`, and
  `source_label=static_curated`.
- `/api/match/{match_id}/summary` returned matching `briefing_status`.
- Temp-data API smoke covered missing, fresh, expired-to-stale, and invalid
  briefing artifact states.
- `python3 -m compileall -q src`
- `npm --prefix src/frontend run build`
- `git diff --check`

### Routing

- Next project step: **T-031 - Active Match Metrics Completion**.
- T-031 should use the T-035 source policy and T-038 source-cache contract to
  replace or explicitly preserve unavailable states for the remaining active
  metric gaps.
- T-030 remains the Streamlit legacy disposition cleanup task.

---

## 2026-06-19 - T-029 Deployment and Operations Runbook Refresh Completed

Prepared by: Orchestrator / QA / Reproducibility Engineer

### Current State

- T-029 is complete.
- Added a current deployment and operations runbook for the React/Vite +
  FastAPI + Docker + Cloud Run + `accionar.xyz` architecture.
- Added a QA deployment verification checklist that separates local build,
  optional local API smoke, optional Docker smoke, Cloud Run verification, and
  `accionar.xyz` verification.
- No deploy was performed.

### What Changed

- Added `docs/deployment_operations_runbook.md`.
- Added `docs/deployment_verification_checklist.md`.
- Added DEC020:
  `docs/decisions/20260619_DEC020_deployment_operations_runbook.md`.
- Added handoff:
  `docs/handoffs/2026-06-19_orchestrator_qa_t029_deployment_runbook.md`.
- Updated `TASKS.md`, `docs/phase_plan.md`, `docs/data_contracts.md`, and
  `docs/DEVELOPER_PLAYBOOK.md` with T-029 routing and runbook pointers.

### Read-Only Live Finding

- Cloud Run `/health` returned HTTP 200 after a cold-start delay.
- Cloud Run `/api/schedule` returned HTTP 200 but only 19 fixtures and no
  lifecycle/source-status fields.
- Cloud Run does not currently have `brazil_haiti_2026`.
- Live older metrics payloads lack newer `data_quality` and source-cache
  metadata.
- `accionar.xyz/dashboards/fifa-2026/` returned HTTP 200, but appeared to serve
  an older portfolio/static route rather than a freshly deployed dashboard
  bundle.

### Verification

- `python3 -m compileall -q src`
- `npm --prefix src/frontend run build`
- `git diff --check`
- In-process API smoke checks
- Read-only Cloud Run and `accionar.xyz` HTTP checks

### Routing

- Next project step: **T-033 - Briefing API and Match Analysis Freshness UI**.
- A separate deployment execution task is needed before claiming live users see
  local T-037/T-038/T-039/T-040 behavior.
- T-031 remains the broad active metric coverage task.

---

## 2026-06-19 - T-038 Source-Backed Squad & Style Metrics Integration Completed

Prepared by: Orchestrator / Data Pipeline Engineer / Football Data Scientist / Frontend Engineer

### Current State

- T-038 is complete for the first source-backed Squad & Style integration pass.
- The API can now merge field-level squad/style source records from
  `data/source_cache/squad_style/latest_metrics.json` without rewriting
  checked-in `metrics.json` files.
- The first active sample is `brazil_haiti_2026`, not a finished fixture.
- Brazil has source-backed Transfermarkt profile-header values for
  `squad_market_value_m` and `average_age`.
- Haiti and unsupported style/performance fields remain explicitly `missing`
  until auditable sources are found.
- Existing local profile values without field source records are labeled
  `hardcoded_reference`, not live research.
- The Squad & Style UI now tags each displayed value as sourced, reference,
  approximate, missing, unsupported, or blocked, and uses T-039 World Football
  Elo provenance for the rating row.

### What Changed

- Added `src/analytics/squad_style_sources.py`.
- Added `src/pipeline/collect_squad_style_sources.py`.
- Added `data/source_cache/squad_style/latest_metrics.json`.
- Added `docs/squad_style_source_methodology.md`.
- Updated `/api/match/{id}/metrics` with `team_metric_source_cache`,
  `team_metric_sources`, and per-field quality metadata.
- Updated `SquadStyleComparison` and `MatchAnalysisTab` to consume field-level
  provenance and render missing/source/reference badges.
- Updated `docs/data_contracts.md`, `TASKS.md`, `docs/phase_plan.md`, and T-038
  decision/handoff records.

### Verification

- `python3 src/pipeline/collect_squad_style_sources.py`
- `python3 -m json.tool data/source_cache/squad_style/latest_metrics.json`
- Direct API smoke check for `brazil_haiti_2026`
- Direct API smoke check for a non-sample fixture
- `python3 -m compileall -q src`
- `npm --prefix src/frontend run build`

### Routing

- Superseded 2026-06-19: T-029 is now complete. Next project step is
  **T-033 - Briefing API and Match Analysis Freshness UI**.
- Remaining broad metric coverage is still T-031 territory: more teams and
  fields need actual source collectors before all Squad & Style values can be
  source-backed.
- T-033 remains queued for the dedicated briefing API and fuller Match Analysis
  freshness UI.

---

## 2026-06-19 - T-041 Documentation Clutter Audit Completed

Prepared by: Orchestrator

### Current State

- T-041 is complete.
- Added `docs/documentation_clutter_audit.md` as the current documentation map.
- Added DEC018 to make the documentation retention rule durable.
- Current-facing docs were corrected where they drifted after T-037/T-039.
- No decision or handoff records were deleted; they remain historical audit
  records and may contain facts superseded by newer tasks.

### What Changed

- Updated `README.md` to describe active seeded Monte Carlo and World Football
  Elo cache-backed ratings.
- Updated `docs/DEVELOPER_PLAYBOOK.md` to remove stale deterministic
  progression and multi-word parsing caveats.
- Updated `docs/data_contracts.md` next-step routing to T-038, T-033, and
  T-029.
- Marked `PROJECT_CONTEXT.md` as initial setup context, not current
  architecture.
- Updated `PROJECT_CHARTER.md`, `TASKS.md`, and `docs/phase_plan.md` with the
  documentation clutter audit and DEC018.
- Added handoff:
  `docs/handoffs/2026-06-19_orchestrator_t041_documentation_clutter_audit.md`.

### Audit Finding

The documentation set is large but usable if agents follow the current-first
reading order:

1. `PROJECT_CHARTER.md`
2. `AGENTS.md`
3. `TASKS.md`
4. `STATUS.md`
5. `docs/phase_plan.md`
6. `docs/data_contracts.md`
7. `docs/model_provenance.md`
8. `docs/DEVELOPER_PLAYBOOK.md`

Historical decisions and handoffs should be treated as dated records, not
current-state summaries.

### Verification

- `git diff --check`
- `python3 -m compileall -q src`
- `npm --prefix src/frontend run build`

### Routing

- Superseded 2026-06-19: T-038 and T-029 are now complete. Next project step is
  **T-033 - Briefing API and Match Analysis Freshness UI**.
- Documentation-adjacent queued work now remains T-030 Streamlit legacy
  disposition.

---

## 2026-06-19 - T-039 No-Cost Football Data Source Spike Completed

Prepared by: Orchestrator / Data Pipeline Engineer / Football Data Scientist

### Current State

- T-039 is complete for national-team rating replacement.
- World Football Elo is now the primary no-cost rating source for runtime Elo
  and Monte Carlo inputs.
- FIFA/Coca-Cola Men's World Ranking remains an official sanity check/fallback
  reference; the current public page is dynamic, so this spike records update
  metadata rather than using FIFA as the primary machine-readable rating feed.
- Runtime rating behavior is cache-first:
  `SoccerDataClient.fetch_club_elo_ratings()` reads
  `data/source_cache/world_football_elo/latest_ratings.json` before falling
  back to the old local Elo-style map.
- The T-039 source run parsed 244 World Football Elo ratings and matched 48/48
  current tournament teams through the shared team identity contract.
- Monte Carlo metadata and `/api/match/{id}/metrics.data_quality` now surface
  `web_researched` provenance when World Football Elo cache values are used.

### What Changed

- Added `src/analytics/rating_sources.py`.
- Added `src/pipeline/collect_rating_sources.py` with dry-run default and
  explicit `--write` for cache/report writes.
- Added audited source cache:
  `data/source_cache/world_football_elo/latest_ratings.json`.
- Added raw source snapshots:
  `data/source_cache/world_football_elo/raw/World.tsv` and
  `data/source_cache/world_football_elo/raw/en.teams.tsv`.
- Added spike reports:
  `docs/no_cost_football_data_source_spike.md` and
  `docs/source_spikes/t039_no_cost_rating_sources.md`.
- Updated API provenance so Monte Carlo `source_label` is `web_researched`
  while `rating_source` remains `world_football_elo`.

### Verification

- `python3 src/pipeline/collect_rating_sources.py --write`
  - World Football Elo status: `used`
  - parsed rows: `244`
  - FIFA metadata status: `metadata_only`
  - active tournament coverage: `48/48`
- Direct rating cache smoke check returned source-backed values for Canada,
  Mexico, United States, Ivory Coast, and Democratic Republic of the Congo.
- Direct metrics smoke check returned `source_label=web_researched` for Elo
  ratings and Monte Carlo projections.
- `python3 -m compileall -q src`
- `npm --prefix src/frontend run build` passed with the existing chunk-size
  warning only.

### Routing

- Superseded 2026-06-19: T-038 is now complete as a field-level source-cache
  contract plus one partial active sample. Broad `team_metrics` value
  completion remains T-031.
- Do not use ClubElo as the national-team rating source. Reserve it only for a
  later player-club-strength feature if that model is explicitly approved.
- Refresh the World Football Elo cache once per matchday or before the 3-hour
  jornada window, not per API request.

---

## 2026-06-18 - T-037 Real Monte Carlo Tournament Simulation Completed

Prepared by: Data Pipeline Engineer

### Current State

- T-037 is complete for the active FastAPI/React runtime.
- `/api/match/{match_id}/metrics` now runs a seeded random-trial tournament
  simulation instead of the previous deterministic progression curve.
- The endpoint defaults to `simulation_count=10000` and `seed=20260618`; callers
  may pass `simulation_count` and `seed` query parameters.
- Output keeps the existing frontend keys `r16`, `qf`, `sf`, `final`, and
  `win`, and adds `group_advancement`/`r32` for 2026 group-stage advancement.
- Team probabilities are exposed through `monte_carlo_projections`; simulation
  count, seed, generated time, model version, rating source, and missing-rating
  caveats are exposed through `monte_carlo_metadata`.
- Rating inputs were honest at T-037 closeout: Elo values used local
  `hardcoded_reference` defaults, and missing local ratings used a neutral
  `1500.0` fallback. This rating caveat was superseded by T-039 on
  2026-06-19; runtime ratings now prefer the World Football Elo cache.

### What Changed

- Added `src/analytics/monte_carlo_simulation.py`.
- Updated `src/api/main.py` to run the seeded fixture-aware simulation from
  `data/bracket/grid_state.json` plus the live/cached fixture list, and expose
  simulation quality metadata.
- Updated `src/frontend/src/components/MonteCarloProjections.tsx` to show
  simulation count, seed, and hardcoded-reference rating provenance when real
  trials are present.
- Updated `TASKS.md`, `docs/phase_plan.md`, `docs/data_contracts.md`,
  `docs/model_provenance.md`, and T-037 handoff/decision records.

### Verification

- Module reproducibility check passed for fixed `seed`.
- Direct metrics smoke check returned `status=simulation`, `simulation_count`,
  `seed`, `rating_source=hardcoded_reference`, and per-team probabilities.
- `python3 -m compileall -q src`
- `npm --prefix src/frontend run build` passed with the existing chunk-size
  warning only.

### Routing

- Superseded 2026-06-19: T-039 is complete and runtime ratings now prefer the
  World Football Elo cache.
- Superseded 2026-06-19: T-038 is complete; broad source coverage remains
  T-031.
- Legacy Streamlit code in `src/app/` still contains old reference-only
  progression logic and is not the production runtime.

---

## 2026-06-18 - T-036 Source-Backed Research Collector Prototype Completed

Prepared by: Data Pipeline Engineer

### Current State

- T-036 is complete as a prototype implementation.
- Added `src/pipeline/collect_match_research.py`.
- Default mode is dry-run; write mode requires `--write`.
- The collector reads fixture context from `summary.json` and `metrics.json`,
  but refuses to write `summary.json`, `metrics.json`, or production
  `briefing.json`.
- Default write target is `data/matches/{match_id}/research_cache.json`.
- Source-backed claims remain draft/review-gated; no production
  `research_cache.json` files were written during closeout.

### What Changed

- Added one-fixture CLI controls for `--match-id`, repeatable `--source-file`,
  repeatable `--source-url`, `--output-path`, `--window-hours`, `--now`,
  `--http-timeout`, and `--data-dir`.
- Offline source files can be structured JSON claims or HTML/text scanned with
  conservative matchday keywords.
- Every source record carries source id/name, URL/path, collection method,
  checked time, status, source label, warnings, blocked reasons, and claim
  scope.
- Every generated claim carries claim type, text, basis, source ids,
  confidence, and draft review status.
- The cache embeds a proposed briefing draft for Football Data Scientist review
  instead of mutating `briefing.json`.

### Verification

- Offline dry-run for `canada_qatar_2026` produced a valid manifest with two
  draft source-backed claims.
- Live URL dry-run against a public Canada vs Qatar match-news source succeeded
  after network approval and retained the URL as a `web_researched` source.
- Temp write-mode verification created only `research_cache.json` in a copied
  fixture folder.
- Copied `summary.json` and `metrics.json` remained byte-identical to the
  originals.
- Forbidden production `briefing.json` output path returned a blocked manifest.
- Python compile and frontend build passed.

---

## 2026-06-18 - T-032 Last-Minute Briefing Pipeline Completed

Prepared by: Orchestrator

### Current State

- T-032 is complete as an implementation task.
- Added `src/pipeline/generate_match_briefings.py`.
- The generator creates only `data/matches/{match_id}/briefing.json` when
  `--write` is explicit.
- Default mode is dry-run and writes nothing.
- The pipeline uses current fixture lifecycle/source status and skips finished
  fixtures.
- No production `briefing.json` files were written during closeout; write-mode
  verification used a temporary copy of `data/matches/`.

### What Changed

- Added dry-run/write support for the active `jornada` briefing window.
- Added `--window-hours`, `--match-id`, `--active-date`, `--force-refresh`,
  `--data-dir`, `--cache-path`, and `--now` controls.
- Added a machine-readable manifest with target path, source status, freshness,
  action, warnings, blocked reasons, and validation state.
- Added draft `briefing.json` payload construction with:
  - `metadata`
  - `fixture`
  - `team_keys`
  - `briefing`
  - `forecast_snapshot`
  - `data_quality`
  - `sources`
  - `review`
- Preserves existing fresh briefings unless `--force-refresh` is passed.
- Updated `/api/match/{id}/summary` compatibility so it reads
  `metadata.freshness` and source labels from generated briefing artifacts.

### Current Briefing Scope

As of the T-032 dry-run, the active day contains four not-finished fixtures:

- `czech_republic_south_africa_2026`
- `switzerland_bosnia_and_herzegovina_2026`
- `canada_qatar_2026`
- `mexico_south_korea_2026`

All four were reported as `would_create` but `freshness=blocked` because the
current stored team metrics are empty, and three also use the default
`40/30/30` forecast. This is expected: T-032 implements the safe briefing
artifact pipeline, while T-036 must add source-backed research content.

### Verification

- `python3 src/pipeline/generate_match_briefings.py --dry-run --window-hours 3`
  reported four current-day targets and wrote no files.
- Finished fixture dry-run for `england_croatia_2026` reported `skipped`.
- Future fixture dry-run for `brazil_haiti_2026` used the fixture's own
  `2026-06-19` jornada window.
- Temp write-mode verification for `canada_qatar_2026` created only
  `briefing.json`; copied `summary.json` and `metrics.json` remained
  byte-identical.
- Fresh-preservation verification reported `preserved` without
  `--force-refresh`.
- `python3 -m compileall -q src`
- `npm --prefix src/frontend run build` passed with the existing chunk-size
  warning only.

### Routing

- T-036 is now complete, so the next Orchestrator assignment should move to
  **T-037 - Real Monte Carlo Tournament Simulation** unless the project wants
  to prioritize the no-cost source spike T-039 first.
- T-033 remains the dedicated API/UI task for a full
  `/api/match/{match_id}/briefing` route and richer Match Analysis freshness UI.

---

## 2026-06-18 - T-040 Fixture Lifecycle Filter Completed

Prepared by: Orchestrator

### Current State

- T-040 is complete as an implementation task.
- `/api/schedule` now exposes fixture lifecycle and source status.
- React Overview and Match Analysis default to the current day's not-finished
  fixtures only.
- Finished fixtures remain stored as historical/post-match records, but they are
  no longer part of default Match Analysis selection or briefing/research scope.

### Current Fixture Lifecycle Counts

As of 2026-06-18 local runtime:

- `finished`: 12
- `today`: 4
- `upcoming`: 4

The visible day view contains only the 4 `today` fixtures:

- `czech_republic_south_africa_2026`
- `switzerland_bosnia_and_herzegovina_2026`
- `canada_qatar_2026`
- `mexico_south_korea_2026`

### What Changed

- Added lifecycle fields to `/api/schedule`:
  - `lifecycle`
  - `source_status`
  - `source_game_id`
  - `is_finished`
  - `is_today`
  - `is_upcoming_24h`
  - `is_briefing_candidate`
- Added schedule-level fields:
  - `active_date`
  - `default_match_id`
  - `lifecycle_counts`
  - `briefing_window`
- Past schedule dates are classified as `finished` even if the live/cache source
  is missing or stale.
- `discover_active_fixtures.py` now skips finished fixtures in dry-run and write
  mode.
- Overview no longer falls back to all matches when no hardcoded date matches.
- Match Analysis selector no longer shows finished or future fixtures by
  default.

### Routing

- T-032 must use the lifecycle contract and generate `briefing.json` only for
  `source_status=not_finished` fixtures in scope.
- Future historical/post-match UX should be a separate archive/results view, not
  part of the default last-minute analysis workflow.

---

## 2026-06-18 - T-034 Active Fixture Discovery Completed

Prepared by: Orchestrator

### Current State

- T-034 is complete as an implementation task.
- Added `src/pipeline/discover_active_fixtures.py`.
- Active fixture folders increased from 19 to 20 after creating
  `data/matches/brazil_haiti_2026`.
- The discovery command defaults to dry-run and requires explicit `--write` to
  create baseline files.

### What Changed

- The fixture discovery script fetches `worldcup26.ir/get/games` and falls back
  to `/tmp/games.json` when the live API is unavailable.
- Team names and match IDs are normalized through the T-027 identity helpers.
- The script emits a machine-readable JSON manifest for dry-run and write mode.
- Existing curated `summary.json` and `metrics.json` files are not overwritten.
- Unresolved fixtures such as knockout placeholders are blocked until the live
  schedule exposes real teams.
- Write mode for `--active-date 2026-06-19` created only:
  - `data/matches/brazil_haiti_2026/summary.json`
  - `data/matches/brazil_haiti_2026/metrics.json`

### Generated Stub State

- `summary.json` is labeled `baseline_stub` and contains fixture metadata plus
  explicit placeholder editorial copy.
- `metrics.json` preserves the current compatibility shape, including six exact
  scores and the default `40/30/30` forecast, but labels the payload as
  `baseline_stub`, `default_forecast`, and `empty_team_metrics`.
- T-028 runtime labels make the Brazil vs Haiti forecast and radar unavailable
  in the API/UI instead of presenting them as model-backed analysis.

### Verification

- Dry-run for June 18 wrote no files and reported four existing fixtures.
- Dry-run for June 19 reported three existing fixtures and one would-create
  fixture: `brazil_haiti_2026`.
- Re-running write mode for June 19 was idempotent and reported all four
  fixtures as existing.
- Stub schema assertions passed for `summary.json` and `metrics.json`.
- API smoke check passed: `/api/schedule` now returns 20 fixtures, and
  `/api/match/brazil_haiti_2026/metrics` marks forecast/radar output
  unavailable.

### Routing

- T-032 and T-036 are now complete. Source-backed research can be cached for
  review, but API/UI consumption still belongs to T-033.
- T-038 is now complete as the source-cache contract and first partial sample.
  T-031 still needs to replace empty stub metrics with source-backed values
  where coverage allows.

---

## 2026-06-18 - T-028 Incomplete Data and Fallback UI/API States Completed

Prepared by: Orchestrator

### Current State

- T-028 is complete as an implementation task.
- `/api/match/{id}/metrics` now adds a runtime `data_quality` block.
- `/api/match/{id}/summary` now adds `briefing_status`.
- Match Analysis now renders incomplete/default states visibly instead of
  presenting fallback values as model output.

### What Changed

- Default `40/30/30` forecasts are marked `default_forecast` and render as
  "forecast unavailable."
- Exact-score probabilities are hidden when the stored forecast is only the
  default fallback.
- Empty `team_metrics` are marked `missing`; complete static values are marked
  `static_curated`.
- Radar charts do not render missing values as neutral 50 scores.
- Squad & Style renders a missing-state panel when both teams lack metrics and a
  warning when fields are partial.
- Current progression values are labeled as deterministic fallback estimates,
  not true Monte Carlo simulations.
- StatsBomb visualization provenance is exposed as `proxy_historical`.
- Missing `briefing.json` now surfaces as `baseline_only` instead of silently
  implying a fresh last-minute briefing exists.

### Verification

- API data-quality check passed for `canada_qatar_2026` and
  `france_senegal_2026`.
- `python3 -m compileall -q src`
- `npm --prefix src/frontend run lint`
- `npm --prefix src/frontend run build` passed with the existing chunk-size
  warning only.

### Routing

- T-034 can now generate baseline stubs without the public UI presenting stub
  forecasts or empty metrics as authoritative.
- T-037 is now complete and replaced deterministic progression with real Monte
  Carlo output in the active FastAPI/React runtime.
- T-038/T-039 should populate real source-backed metrics where available; T-028
  only makes missing and static fallback states honest.

---

## 2026-06-18 - T-027 Team Identity Normalization Completed

Prepared by: Orchestrator

### Current State

- T-027 is complete as an implementation task.
- Canonical team identity now lives in `data/reference/team_identity.json`.
- Python consumers use `src/common/team_identity.py`.
- React consumers use `src/frontend/src/lib/teamIdentity.ts`.
- Runtime behavior changed for identity resolution only: provider aliases such
  as `Czechia`, `Turkiye` / `Türkiye`, `DR Congo`, `Curaçao`, and
  `Côte d'Ivoire` now normalize to the project display names and slugs.

### What Changed

- FastAPI metrics and visualization routes no longer split match IDs on every
  underscore to infer teams.
- Match Analysis no longer derives editorial keys with first-space-only string
  replacement.
- Live standings/bracket mutation and the offline bracket artifact use shared
  identity names.
- Preview generation now writes `summary.json` slugs with the shared helper.
- Existing local Elo fallback lookup now normalizes team aliases before reading
  defaults.

### Verification

- `python3 -m json.tool data/reference/team_identity.json`
- `python3 -m compileall -q src`
- Custom identity audit: all 20 active fixtures resolve by folder ID, metadata
  display names, injury slugs, and tactics slugs.
- `npm --prefix src/frontend run build` passed with the existing chunk-size
  warning only.

### Routing

- T-034, T-036, T-038, and T-039 should use the shared identity contract before
  writing any source-collected payloads.
- T-034 and T-032 are now complete; next Orchestrator assignment should be
  T-036.

---

## 2026-06-18 - T-035 AI Research Source Policy Completed

Prepared by: Orchestrator

### Current State

- T-035 is complete as a policy and intake-architecture task.
- Deliverable added: `docs/ai_research_source_policy.md`.
- Handoff added:
  `docs/handoffs/2026-06-18_orchestrator_t035_ai_research_source_policy.md`.
- Decision added:
  `docs/decisions/20260618_DEC011_ai_research_source_policy.md`.
- Runtime behavior was not changed.

### Accepted User Decisions

- Default `40/30/30` forecasts should render as "forecast unavailable."
- The progression panel should become a real Monte Carlo simulation.
- Online research should feed ratings, Squad & Style metrics, lineups, injuries,
  rosters, managers, and tactical news.
- Browser automation and scraping are allowed.
- Individual displayed AI claims do not require one-to-one URL citations, but the
  collection run should retain source metadata for audit.
- Fresh last-minute analysis uses a 3-hour window before the first game of the
  daily `jornada`.

### Recommended Source Stack

- Ratings: World Football Elo, with FIFA ranking as fallback/sanity check.
- Official facts: FIFA squad/ranking/tournament pages.
- Structured live/team data: Sportmonks as preferred provider, API-Football as
  fallback.
- Market value: Transfermarkt.
- Deep style metrics such as PPDA and field tilt: Wyscout, Opta/Stats Perform,
  or paid StatsBomb/event data if available.
- Last-minute injuries/tactical news: browser automation over official/team/news
  pages, with source snapshots or source records retained.

### Routing

- Added **T-037 - Real Monte Carlo Tournament Simulation**.
- Added **T-038 - Source-Backed Squad & Style Metrics Integration**.
- Added **T-039 - No-Cost Football Data Source Spike** after review comments
  identified a useful free/open-source path through `soccerdata`, FBref,
  Sofascore, WhoScored, Transfermarkt, and proxy formulas.
- Moved **T-036 - Source-Backed Research Collector Prototype** into the queued
  implementation path.
- T-028 is now complete and renders default forecasts as "forecast unavailable."
- T-032 now uses the 3-hour `jornada` freshness rule; T-033 should preserve it
  in the dedicated briefing API/UI.

### Review Comment Disposition

- Accepted: use `soccerdata` as the first Python no-cost extraction layer before
  paid APIs where coverage is adequate.
- Accepted: consider FBref/Sofascore/WhoScored-derived aggregate metrics for
  Squad & Style fields.
- Accepted with caveat: field tilt and PPDA can be approximated from aggregate
  columns only when the source columns exist, and must display as proxies.
- Rejected as primary model source: ClubElo should not replace World Football
  Elo for national teams. It may be useful later as a player-club-strength
  feature once roster and starting-XI club mapping exists.

### Verification Scope

- Documentation-only change. Local compile/build verification is run after the
  full documentation batch.

---

## 2026-06-18 - T-026 Model and Provenance Truth Review Completed

Prepared by: Orchestrator

### Current State

- T-026 is complete as a truth/provenance review.
- Owner: Football Data Scientist.
- Deliverable added: `docs/model_provenance.md`.
- Handoff added:
  `docs/handoffs/2026-06-18_football_data_scientist_t026_model_provenance.md`.
- Decision added:
  `docs/decisions/20260618_DEC010_model_provenance_truth_labels.md`.
- Runtime behavior was not changed.

### Key Findings

- Current Match Analysis is not yet an AI-research-first system. It is mostly
  static `summary.json`, static `metrics.json`, local hardcoded references,
  deterministic formulas, and historical proxy visualizations.
- The Dixon-Coles forecast is an Elo-derived Poisson score-grid calculation with
  a low-score adjustment, not a fitted broad-data model.
- At T-026 review time, Elo ratings were local hardcoded defaults, not live
  SoccerData or ClubElo reads. This rating caveat was superseded by T-039 on
  2026-06-19 for runtime cache-backed World Football Elo ratings.
- The default `40/30/30` forecast must be labeled as fallback, not as a model
  result.
- The current "Monte Carlo" panel is deterministic and should be renamed unless
  a real simulation is implemented.
- StatsBomb/BigQuery charts are historical proxies and do not cover the full
  match-intelligence problem, including missing competitions and teams outside
  the available sample.
- Rosters, clubs, and last major standings are hardcoded frontend references.

### Routing

- Added queued task **T-035 - AI Research Source Policy and Data Intake
  Architecture**.
- Added backlog task **T-036 - Source-Backed Research Collector Prototype**.
- T-032 source-backed briefing generation now depends on T-035 for any
  web-research collection.
- T-028 is now complete and exposes UI/API degraded states for default
  forecasts, local ratings, hardcoded references, and proxy visuals.

### Policy Questions Before Implementation

- Should default `40/30/30` ever be public, or should it render as forecast
  unavailable?
- Should the deterministic progression panel be renamed now, or replaced with a
  real tournament simulation?
- Which rating source should forecasts use?
- Which web sources and collection methods are allowed for injuries, lineups,
  rosters, managers, suspensions, tactical news, and team metrics?
- Must every AI-generated current claim have URL-backed source metadata?
- Should proxy charts fail closed instead of falling back to unrelated teams?

### Verification Scope

- Documentation-only change. Local compile/build verification is still run after
  the full documentation batch.

---

## 2026-06-17 - Active Fixture Discovery Gap Routed

Prepared by: Orchestrator

### Current State

- The tournament progression gap is now explicitly tracked.
- Owner: Data Pipeline Engineer, with QA / Reproducibility Engineer review.
- Deliverable added: `docs/active_fixture_discovery_plan.md`.
- Runtime behavior was not changed.

### Why This Matters

- The app currently lists analyzable matches from local
  `data/matches/*_2026` folders.
- If a future tournament game has no local folder, `/api/schedule` will not list
  it and `/api/match/{id}/summary` or `/metrics` will return 404.
- Last-minute `briefing.json` generation depends on a baseline fixture folder
  existing first.

### Planned Procedure

- Discover active-date or next-24-hour fixtures from
  `https://worldcup26.ir/get/games`.
- Fall back to `/tmp/games.json` if the live games API fails.
- Create missing baseline folders only with explicit `--write`.
- Generate minimal `summary.json` and `metrics.json` stubs labeled
  `baseline_stub`.
- Preserve all existing curated `summary.json` and `metrics.json` files.
- Run last-minute briefing generation only after the baseline folder exists.

### Routing

- Added queued task **T-034 - Active Fixture Discovery and Baseline Stub
  Generation**.
- Added decision record
  `docs/decisions/20260617_DEC009_active_fixture_discovery_stubs.md`.
- T-034 should run before T-032.
- T-027 is now complete; fixture discovery must use the shared team identity
  contract rather than fragile match ID parsing.
- T-028 is now complete and stops stub/default metrics from rendering as
  authoritative forecasts or radar charts.

### Verification Scope

- `python3 -m compileall -q src` passed.
- `npm --prefix src/frontend run build` passed with the existing Vite
  chunk-size warning only.

---

## 2026-06-17 - T-025 Re-scoped to Last-Minute Briefing Generation

Prepared by: Orchestrator

### Current State

- T-025 is complete as a planning task.
- Owner: Data Pipeline Engineer.
- Deliverable: `docs/last_minute_briefing_plan.md`.
- Runtime behavior was not changed.

### Completed This Update

- Re-scoped T-025 from generic safe preview regeneration into safe
  last-minute match briefing generation.
- Defined the product split between:
  - baseline preview: `summary.json`
  - matchday briefing: planned `briefing.json`
- Defined planned `briefing.json` fields for metadata, fixture copy, normalized
  team keys, briefing content, forecast snapshot, data quality, sources, and
  review status.
- Required generator safety rules:
  dry-run by default, explicit write mode, no `summary.json` or `metrics.json`
  overwrites, source/freshness validation, and review gates.
- Added implementation follow-ups:
  T-032 for the briefing pipeline and T-033 for API/UI freshness states.
- Added decision record
  `docs/decisions/20260617_DEC008_last_minute_briefing_scope.md`.

### Next Routing

- At the time, the next recommended Orchestrator assignment was **T-026 - Model
  and Provenance Truth Review**. T-026 is now complete; current routing is in the
  2026-06-18 entry above.
- T-032 should use the completed T-027 identity contract and the T-035 source
  policy for web-researched inputs.
- T-033 should coordinate with T-028 so briefing freshness and incomplete-data
  states are implemented consistently.

### Verification Scope

- `python3 -m compileall -q src` passed.
- `npm --prefix src/frontend run build` passed with the existing Vite
  chunk-size warning only.

---

## 2026-06-17 - Data Contract Audit Completed (T-024)

Prepared by: Orchestrator

### Current State

- T-024 is complete.
- QA / Reproducibility Engineer owned the audit, with Data Pipeline Engineer
  support for generator/API provenance.
- Deliverable: `docs/data_contracts.md`.
- No runtime code, JSON payloads, generation scripts, or deployment assets were
  changed.

### Completed This Update

- Documented the active contracts for `summary.json`, `metrics.json`,
  `grid_state.json`, `/api/schedule`, `/api/match/{id}/summary`,
  `/api/match/{id}/metrics`, `/api/standings`, `/api/forecast`, and
  `/api/visualizations/{match_id}/{viz_type}`.
- Separated stored JSON fields from runtime API augmentation:
  `elo_ratings`, `monte_carlo_projections`, and `viz_proxies`.
- Audited all 19 active `data/matches/*_2026` fixture folders.
- Classified legacy numeric folders `1001`, `1002`, and `1003` as old
  BigQuery-style stubs outside `/api/schedule`.
- Added a QA handoff at
  `docs/handoffs/2026-06-17_qa_data_contract_audit.md`.

### Audit Findings

- `summary.json`: all 19 active fixtures pass the required metadata/editorial
  schema checks.
- `metrics.json`: all 19 active fixtures have the required stored top-level
  keys and 6 exact-score probabilities.
- Empty `team_metrics`: 8 fixtures need completion or explicit fallback states:
  `canada_qatar_2026`, `czech_republic_south_africa_2026`,
  `mexico_south_korea_2026`, `scotland_morocco_2026`,
  `switzerland_bosnia_and_herzegovina_2026`, `turkey_paraguay_2026`,
  `united_states_australia_2026`, and `uzbekistan_colombia_2026`.
- Default stored forecast: 7 fixtures use the generator fallback
  `40/30/30` split: all empty-metrics fixtures except
  `switzerland_bosnia_and_herzegovina_2026`.
- T-034 addendum: active fixtures now total 20 after adding the
  `brazil_haiti_2026` baseline stub. Current empty metric profiles total 9 and
  current default forecasts total 8.
- At audit time, multi-word team names were a contract risk in frontend
  normalization and API fallback parsing. This is now resolved by T-027.
- Overview tournament totals are hardcoded in `OverviewTab.tsx`, not sourced
  from schedule or standings payloads.

### Next Routing

- T-025 was completed after this audit as the safe last-minute match briefing
  generation plan.
- At the time, the recommended Orchestrator assignment was **T-026 - Model and
  Provenance Truth Review**. T-026 is now complete; current routing is in the
  2026-06-18 entry above.
- T-027 is now complete and centralizes team identity plus multi-word/alias
  handling.
- T-028 is now complete and makes empty/default/fallback states visible in the
  UI/API.
- T-031 should complete or explicitly label the eight empty team metric
  profiles.

### Verification Scope

- `python3 -m compileall -q src` passed.
- `npm --prefix src/frontend run build` passed with the existing Vite
  chunk-size warning only.

---

## 2026-06-17 - Framework Rebaseline Batch 1

Prepared by: Orchestrator

### Current State

- The project is now treated as a **React/Vite + FastAPI** application.
- `src/app/` Streamlit code is legacy/reference unless a later decision says
  otherwise.
- Phase 5 is active: **Framework Rebaseline & Pipeline Hardening**.
- Batch 1 is docs-only and does not change runtime behavior.

### Completed This Update

- Rewrote `PROJECT_CHARTER.md` as the current operating contract.
- Updated `AGENTS.md` so the five framework agents map to the current
  React/FastAPI/static-data project.
- Replaced `docs/phase_plan.md` with Phase 5 batches and exit criteria.
- Rebuilt `TASKS.md` around the real current deficiencies:
  data contracts, last-minute briefing generation, model provenance, team
  identity, incomplete-data UI states, and deployment runbook refresh.
- Refreshed `docs/DEVELOPER_PLAYBOOK.md` for the current architecture.
- Refreshed `README.md` and `docs/domain/README.md` to stop pointing new
  readers at stale Streamlit/Antigravity assumptions.
- Added decision record `docs/decisions/20260617_DEC007_framework_rebaseline.md`.

### Known Local Findings Feeding Phase 5

- Active match folders: 19 `*_2026` fixture folders with `summary.json` and
  `metrics.json`.
- Legacy numeric folders: `1001`, `1002`, `1003` still contain old
  BigQuery-style metrics and are not part of `/api/schedule`.
- Several active fixtures have empty `team_metrics`.
- Several forecasts fall back to the default `40/30/30` outcome split because
  Elo/team profiles are missing for the exact team names in use.
- Current `summary.json` files may contain newer curated editorial copy than
  `generate_match_previews.py`; the generator must not be run again without a
  dry-run/diff/preserve plan.
- Multi-word team names and aliases are a known fragile path across generator,
  API, and frontend code.
- Some UI/model wording overstates current implementation details, especially
  static Elo defaults and deterministic "Monte Carlo" projections.

### Next Batch

- Completed after this entry: **T-024 - Data Contract Audit for Active JSON and
  API Payloads**.

### Verification Scope

- Local docs were updated only.
- Runtime behavior and live deployment were not changed in this batch.
- `python3 -m compileall -q src` passed.
- `npm --prefix src/frontend run build` passed with the existing Vite chunk-size
  warning only.

---

## 2026-06-17 - Match Analysis Deep Update, xG Distribution, Live Results Refresh

Prepared by: Orchestrator

### Completed This Update

- **Match Analysis restructure**: removed the redundant "Match Forecast" card; "Match
  Outcome Probability" moved up with **Top Exact Scores integrated**; radar fixed to
  read the real `team_metrics` fields (was always showing hardcoded defaults).
- **New sections** (real data): **Squad & Style Comparison (FBref & Club Elo)** beside
  the radar, **Monte Carlo Simulation Projections** (half-width, below the radar),
  **Coaching & Tactical Philosophies** and **Last Major Standing**.
- **xG Distribution Comparison** replaces the xG momentum timeline in the StatsBomb
  section (`get_cached_xg_distribution` — non-penalty KDE curves + shot strip plot).
- **Player tooltip** fixed (no longer clipped/behind; name tag sits below the dot;
  BigQuery cruft removed → clean name/position/club).
- **Language toggle** moved to the top-right corner; event plots labeled as proxy.
- **Live results refresh** (worldcup26.ir): group standings in `grid_state.json` and
  Overview totals updated — 19 matches played, 58 goals, top scorer L. Messi (3).

### Still pending

- Per-player stats/photos in the squad tooltips (large web curation) — not yet done.
- Cloud Run redeploy after merge.

---

## 2026-06-16 - UI Polish: Bracket Fit-to-Screen, Flags, Today-Only Selector, Sidebar/Ball Logo

Prepared by: Orchestrator

### Completed This Update

- **Bracket fits the screen**: `StandingsTab` scales the fixed-width board via a
  `ResizeObserver` so the entire bracket is always visible (no clipping/scroll);
  full-size in Full Screen.
- **Match Analysis selector decluttered**: dropdown shows only the current day's
  fixtures and auto-selects a today's match.
- **National flags** added to team names across Match Analysis (header, selector,
  forecast, injuries, squad lineups, StatsBomb labels). Flags were centralized
  in `src/frontend/src/lib/teamData.ts`; the later T-040 lifecycle contract
  removed the stale hardcoded `TODAY_DATE` filter.
- **Sidebar**: title → "FIFA 2026 / World Cup"; collapsible toggle; brand icon →
  official FIFA World Cup 26 match-ball logo (`ball-logo.png`, resized 7.7MB → 45KB,
  moved to `src/frontend/src/assets/`). Added `vite-env.d.ts` for typed image imports.

### Live Site

- Not yet redeployed with this round (Cloud Run rebuild pending after merge).

---

## 2026-06-16 - Bracket Wood-Board Port, Full-Screen & StatsBomb Viz Fixes

Prepared by: Orchestrator

### Current Objective

Make the React Standings & Bracket tab render the full Streamlit-style painter's-tape
board, add a full-screen option, and fix the broken Bespoke Match Event (StatsBomb)
visualizations.

### Completed This Update

- **Bracket renders fully**: `StandingsTab` now falls back to the seed nested
  `rounds[]` / `third_place` shape (and uses `data.tournament` for the title), so the
  whole knockout bracket renders even when the live API has no knockout games. Verbose
  seed labels (`Winner Group A`, `Runner-up …`, `3rd Group …`, `Winner Match …`,
  `Loser Match …`) restored in `grid_state.json`.
- **No longer clipped + full-screen**: the board is wrapped in a horizontally
  scrollable container (was `overflow-hidden`, which cut off the right half), plus a
  Full Screen toggle that prefers the native Fullscreen API and falls back to a CSS
  overlay (for iframe embeds without `allowfullscreen`); Esc exits.
- **StatsBomb visualizations fixed**: forced matplotlib's non-interactive `Agg`
  backend (GUI backend crashed in FastAPI worker threads — broke every viz locally),
  and renamed `get_cached_xg_timeline(client → _client)` so Streamlit's cache stops
  failing to hash the BigQuery client (this was the live `momentum` 500). All five viz
  endpoints verified returning PNGs locally.

### Live Site Status (accionar.xyz/dashboards/fifa-2026) — NOT up to date

- Cloud Run `metrics` is missing `elo_ratings` / `monte_carlo_projections` (T-018 not deployed).
- Cloud Run `momentum` viz returns HTTP 500; other viz types work.
- None of the changes above are deployed. Requires: rebuild + deploy Docker to Cloud
  Run, and upload `src/frontend/dist` to the accionar.xyz folder.

---

## 2026-06-16 - Interactive Analytics Sprint Finished & Build Restored

Prepared by: Orchestrator

### Current Objective

Finish, verify, and commit the uncommitted interactive-analytics feature batch
that had accumulated after the React/FastAPI migration and was breaking the
frontend build.

### Completed This Update

- **Elo & Monte Carlo projections**: `/api/match/{match_id}/metrics` now returns
  per-team Elo ratings and Monte Carlo tournament-progression probabilities
  through the then-current deterministic helper. Superseded by T-037 for the
  active FastAPI/React runtime.
- **xG Momentum visualization**: Added `get_cached_xg_timeline` and a `momentum`
  `viz_type`; wired the frontend momentum tab to it (it had been requesting
  `radar_chart`).
- **Build restored (exit 0)**: Removed unused imports and reconciled the
  `InteractivePitch` prop contract — the refactor to an internal `PLAYER_CLUBS_ALL`
  map dropped `playerClubs` and now requires `serverUrl`, but the committed
  `MatchAnalysisTab` caller still passed `playerClubs`. Updated the caller and
  removed the orphaned map.
- **Runtime bug fixed**: `get_cached_xg_timeline` read columns the momentum query
  never returns (`second`, `shot_statsbomb_xg`); now consumes `cumulative_xg`.
- **Efficiency**: Deduplicated a double Elo scrape in the metrics endpoint.

### Deferred

- **`/api/player/stats`** (T-019): `InteractivePitch` hover stats call an endpoint
  that was never built; tooltip degrades gracefully. Net-new BigQuery work with
  open data-model questions. See DEC006.

### Next Sprint Priorities

- Verify Cloud Run deployment and redeploy the rebuilt container.
- Upload compiled React static assets to the `accionar.xyz` folder structure.
- Decide on / implement T-019 if per-player hover stats are wanted.

---

## 2026-06-16 - Vite + React Client & FastAPI Decoupled Migration Completed

Prepared by: Orchestrator

### Current Objective

Migrate the dashboard from Streamlit to a decoupled architecture consisting of a FastAPI REST backend and a modern React client built with Vite and TailwindCSS, incorporating interactive vector charts and a dynamic lineup pitch.

### Completed This Update

- **REST API Backend**: Created `/src/api/main.py` using FastAPI, exposing REST endpoints for schedule, match summary, metrics, live standings, and dynamic StatsBomb matplotlib base64 visualizations.
- **Root Asset Serving**: Integrated FastAPI's `StaticFiles` mount at `/` to serve the compiled frontend single-page application directly from the unified python container.
- **Vite React Client**: Initialized client under `/src/frontend/` using Vite, React 19, TypeScript, and TailwindCSS v4.
- **Interactive Pitch Lineup**: Implemented the HTML5/CSS canvas pitch model in `InteractivePitch.tsx` that dynamically maps players based on formation (`4-3-3`, `4-1-4-1`, `3-5-2`) and displays player metadata and entity crosswalk IDs on hover.
- **Animated Charting**: Wired win probability shift curves and team radar comparisons utilizing interactive, responsive vector SVG components via **Recharts**.
- **Live standings & Bracket**: Built the live tournament center (`StandingsTab.tsx`) rendering standings for all 12 groups (A to L) and the live knockout tree (Round of 32 to Final).
- **Static Base Portability**: Set `base: './'` in Vite config to ensure compiled static bundles can be hosted seamlessly in a subfolder on `accionar.xyz/dashboards/fifa-2026/` or at the root path on Cloud Run.

### Next Sprint Priorities

- Verify Cloud Run deployment.
- Upload compiled React static assets to `accionar.xyz` folder structure.

---

## 2026-06-15 - Match Analysis Tab Bug Fixes & Previews Resiliency Completed

Prepared by: Orchestrator

### Current Objective

Ensure correct group standings sorting, dynamic knockout bracket updates from API, and fully automated, resilient match previews and tactical comparisons without crashes or empty views on the dashboard.

### Completed This Update

- **Standings Parsing & Sorting**: Corrected the parsing of groups from the API and sorted standings descending by points (`pts`), then goal difference (`gd`), then goals for (`gf`).
- **Dynamic API-Driven Bracket**: Configured bracket rounds mapping to the live `/get/games` schedule. Bracket advances teams and scores automatically in real time.
- **AI Match Previews & Resiliency**: Resolved the `KeyError: 'team_metrics'` crash in the Streamlit app. Configured the generation pipeline to write the `team_metrics` block containing ELO and FBref statistics for both teams.
- **New Team Profiles & Rosters**: Populated static rosters, club affiliations, and tournament standings for 8 new teams (Spain, Cape Verde, Belgium, Egypt, Saudi Arabia, Uruguay, Iran, New Zealand) and handled spelling normalization for Côte d'Ivoire.
- **Expanded upcoming games coverage**: Increased upcoming preview limits from 3 to 8 matches, resolving the missing **Iran vs New Zealand** fixture on June 15, 2026.
- **Cloud Run Deployment**: Rebuilt the Docker container and redeployed the live dashboard.
- **Tournament Board Standing Update Fix**: Installed `curl` inside the slim Docker container image to resolve the silent failure of runtime standings API calls, and updated the local `grid_state.json` fallback.
- **Portfolio Website Integration**: Synchronized the React routing changes and whitelisted the CSP `frame-src` in `.htaccess` on the remote server via SSH.
