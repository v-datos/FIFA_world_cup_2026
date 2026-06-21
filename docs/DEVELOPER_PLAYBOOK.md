# Developer Playbook & SOP

## FIFA World Cup 2026 Dashboard

Last updated: 2026-06-19

This playbook describes the current local architecture and operating workflow.
Older Streamlit instructions are legacy/reference unless explicitly called out.

> **Superseded data pipelines:** matchday data now refreshes via the ESPN/FotMob
> pipeline suite documented in `docs/matchday_refresh_runbook.md`. The scripts
> `generate_match_previews.py`, `collect_match_research.py`,
> `collect_squad_style_sources.py`, and `update_live_standings.py` were removed;
> any commands referencing them below are historical. Use `collect_espn_matchday`,
> `update_standings`, `update_top_scorers`, `update_team_ages`, `update_team_xg`,
> and `generate_match_headlines` instead.

## 1. Current Architecture

### Active Application

- Frontend: React/Vite/TypeScript in `src/frontend/`.
- Backend: FastAPI in `src/api/main.py`.
- Container: `Dockerfile` builds the React app, copies `dist/` into
  `src/api/static`, and serves the SPA plus API from Uvicorn on port `8080`.
- Cloud deployment: `cloudbuild.yaml` builds and deploys the image to Cloud Run.

### Legacy Reference

- Streamlit code remains in `src/app/`.
- Treat it as reference/legacy code unless a new decision restores it as an
  active runtime.

## 2. Local Verification

Run from the repository root:

```bash
python3 -m compileall -q src
npm --prefix src/frontend run build
```

Combined verify command:

```bash
python3 -m compileall -q src && npm --prefix src/frontend run build
```

This verifies local Python syntax and frontend production build only. It does
not verify:

- BigQuery credentials.
- Cloud Run live state.
- `worldcup26.ir` freshness.
- Remote `accionar.xyz` static assets.

## 3. Running Locally

Frontend dev server:

```bash
npm --prefix src/frontend install
npm --prefix src/frontend run dev
```

Backend API server:

```bash
uvicorn src.api.main:app --host 0.0.0.0 --port 8080 --reload
```

The React app resolves `localhost` and `127.0.0.1` to
`http://localhost:8080`. Non-local hosts use the configured Cloud Run URL in
`src/frontend/src/App.tsx`.

## 4. Data Flows

### Schedule and Match Metadata

- Source files: `data/matches/{match_id}/summary.json`.
- API route: `/api/schedule`.
- UI consumers: Overview fixtures, Match Analysis dropdown/header.

Each active fixture folder ends in `_2026`. Numeric folders such as `1001`,
`1002`, and `1003` are legacy/stub data and are not included in `/api/schedule`.

`/api/schedule` augments local folders with live/cache lifecycle state:

- `finished`
- `today`
- `upcoming`
- `unresolved`
- `archived`

The default React Overview and Match Analysis views show only
`lifecycle=today` fixtures. Finished fixtures remain available as historical
records through direct summary/metrics routes, but they must not be used for
last-minute briefing research.

### Match Editorial Content

- Source files: `data/matches/{match_id}/summary.json`.
- API route: `/api/match/{match_id}/summary`.
- UI consumers: tactical headline, injury updates, coaching/tactics cards,
  pitch formation, key match insights.

Treat `ai_summary` as curated editorial content. Do not overwrite it with
generated output unless a dry-run/diff has been reviewed.

### Forecast and Team Profile Metrics

- Source files: `data/matches/{match_id}/metrics.json`.
- API route: `/api/match/{match_id}/metrics`.
- UI consumers: outcome probability, exact scores, team radar,
  Squad & Style Comparison.

Current active metric files contain:

- `dixon_coles_forecast`
- `score_probabilities`
- `team_metrics`

Runtime API augmentation adds:

- `elo_ratings`
- `monte_carlo_projections`
- `viz_proxies`

Important: active `metrics.json` files are not the older BigQuery event-frame
payloads. The old BigQuery-style schema appears in legacy numeric folders.

T-026 provenance truth:

- Current Elo ratings use the T-039 World Football Elo cache first, then fall
  back to local hardcoded defaults only when a cache value is absent.
- Current Dixon-Coles output is an Elo-derived Poisson forecast with low-score
  adjustment.
- Current `40/30/30` values are default fallback values.
- Current progression projections are seeded random-trial Monte Carlo outputs,
  with `web_researched` rating inputs when the World Football Elo cache is
  present and neutral fallback for teams missing any rating.
- See `docs/model_provenance.md` before changing labels or model claims.

Refresh no-cost rating cache:

```bash
python3 src/pipeline/collect_rating_sources.py --write
```

This command writes `data/source_cache/world_football_elo/latest_ratings.json`,
raw TSV snapshots under `data/source_cache/world_football_elo/raw/`, and the
T-039 source-spike report. The API should read this cache; it should not fetch
World Football Elo on each request.

### Standings and Bracket

- Static fallback: `data/bracket/grid_state.json`.
- Live sources:
  - `https://worldcup26.ir/get/groups`
  - `https://worldcup26.ir/get/games`
- API route: `/api/standings`.
- UI consumer: `StandingsTab`.

The API uses `curl -s -k` via subprocess because the external API has SSL
behavior that fails under normal Python HTTP clients.

### StatsBomb Proxy Visualizations

- API route: `/api/visualizations/{match_id}/{viz_type}`.
- Backing source: BigQuery historical StatsBomb proxy matches.
- UI disclosure: these are proxy/historical event plots, not live 2026 event
  data.

These routes need Google Cloud credentials locally. Build verification does not
prove they work.

## 5. Pipeline Procedures

### Update Local Standings Fallback

```bash
python3 src/pipeline/update_live_standings.py
```

Verify changes in:

```bash
data/bracket/grid_state.json
```

### Baseline Preview and Last-Minute Briefing Generation

Before a match can receive a briefing, it needs a baseline fixture folder:

```text
data/matches/{match_id}/summary.json
data/matches/{match_id}/metrics.json
```

For games that are not already in `data/matches/`, use the active fixture
discovery flow:

```bash
python3 src/pipeline/discover_active_fixtures.py --dry-run --window-hours 24
python3 src/pipeline/discover_active_fixtures.py --write --window-hours 24
```

The discovery flow skips finished fixtures in both dry-run and write mode.

Source order for baseline stubs:

- primary: `https://worldcup26.ir/get/games`
- fallback cache: `/tmp/games.json`
- existing local files: preserve existing `summary.json` and `metrics.json`
- team identity: shared registry from T-027 once implemented

Stub data rules:

- `summary.metadata` comes from the schedule source: teams, date, time, venue,
  and stage.
- `summary.ai_summary` uses explicit "preview pending" placeholders; it must
  not invent tactical news.
- `metrics.dixon_coles_forecast` uses the current-compatible default 40/30/30
  shape and must be labeled `default_forecast` in the manifest.
- `metrics.score_probabilities` uses the current-compatible six fallback
  scorelines and must be labeled `default_forecast` in the manifest.
- `metrics.team_metrics` contains the two team keys with empty objects until
  T-031 fills or labels them.
- Stubs must be labeled `baseline_stub`.

Current caution: do not run baseline preview generation blindly.

```bash
python3 src/pipeline/generate_match_previews.py
```

`summary.json` is the baseline curated preview layer. It is not the
last-minute briefing layer, and it must not be overwritten to create matchday
updates.

Before using `generate_match_previews.py` again, Phase 5 requires:

- dry-run mode
- diff preview
- explicit overwrite/preserve rules for curated `summary.json`
- validation output for missing Elo, empty `team_metrics`, and default forecasts

Last-minute matchday updates use a separate artifact:

```text
data/matches/{match_id}/briefing.json
```

The T-025/T-032 plan and implementation notes are documented in:

```bash
docs/last_minute_briefing_plan.md
```

Use the T-032 generator:

```bash
python3 src/pipeline/generate_match_briefings.py --dry-run --window-hours 3
python3 src/pipeline/generate_match_briefings.py --write --window-hours 3
python3 src/pipeline/generate_match_briefings.py --match-id england_croatia_2026 --dry-run
```

Required behavior:

- dry-run by default
- explicit write mode
- write only `briefing.json`
- preserve `summary.json` and `metrics.json`
- emit source/freshness/data-quality validation before writes
- skip finished fixtures and require `source_status=not_finished`
- treat fresh last-minute analysis as the 3-hour window before the first match of
  the daily `jornada`
- preserve existing fresh briefings unless `--force-refresh` is supplied

Current T-032 caution: this generator creates safe draft baseline-support
briefing artifacts and validation manifests. It does not yet collect fresh
web/news sources. T-036 owns source-backed research collection.

API/UI consumption added by T-033:

```text
GET /api/match/{match_id}/briefing
```

The route returns a valid `briefing.json` artifact when one exists, or a safe
`baseline_only` fallback when the artifact is missing. Match Analysis renders
that freshness status in the tactical headline area and falls back to
`summary.briefing_status` if the dedicated route is unreachable.

### Source-Backed Research Intake

The intended direction is AI-assisted source-backed matchday research. T-035 is
complete and approves browser automation/scraping with source metadata retained.

Before building scraping, browser automation, official API integration, or
paid-provider ingestion, follow:

- `docs/ai_research_source_policy.md`
- the 3-hour `jornada` freshness window
- source metadata fields and source-set retention rules
- review/publication gates
- the storage target for `web_researched` facts

Every current injury, lineup, roster, suspension, manager, tactical, or metric
claim produced by the future collector should carry a URL/path, source name,
retrieval time, status, and review state.

Use the T-036 prototype collector for one-fixture research-cache drafts:

```bash
python3 src/pipeline/collect_match_research.py --match-id canada_qatar_2026 --source-file /path/to/source.json --dry-run
python3 src/pipeline/collect_match_research.py --match-id canada_qatar_2026 --source-file /path/to/source.json --write
```

The collector writes only `data/matches/{match_id}/research_cache.json` by
default. It refuses `summary.json`, `metrics.json`, and production
`briefing.json` as output targets.

### Legacy BigQuery Static Compilation

`src/pipeline/compile_static_fixtures.py` writes the older BigQuery-heavy
metrics schema for numeric match IDs. It is not the current active fixture
pipeline for the 19 `_2026` match folders.

## 6. Deployment Procedures

The authoritative deployment procedures are now:

- `docs/deployment_operations_runbook.md`
- `docs/deployment_verification_checklist.md`

Use those documents for local build gates, Docker checks, Cloud Run deployment,
Cloud Run rollback, `accionar.xyz` checks, and live status snapshots.

T-029 live-status caveat from 2026-06-19:

- Cloud Run `/health` responded after a cold-start delay.
- Cloud Run `/api/schedule` was stale versus local code: 19 fixtures, no
  lifecycle/source-status fields, and no `brazil_haiti_2026`.
- Live metrics payloads did not yet expose the newer `data_quality` and source
  cache metadata.
- `accionar.xyz/dashboards/fifa-2026/` returned HTTP 200 but appeared to serve
  an older portfolio/static route.

Do not claim live users see current local behavior until Cloud Run is rebuilt,
redeployed, and both Cloud Run and `accionar.xyz` smoke checks pass.

### Cloud Run Summary

From the repository root:

```bash
gcloud builds submit --config cloudbuild.yaml .
```

This builds the Docker image, pushes it, and deploys Cloud Run service
`fifa-2026-dashboard` in `us-central1`.

After deploy, follow the full runbook. Minimum API smoke:

```bash
curl -s https://fifa-2026-dashboard-80399171028.us-central1.run.app/health
curl -s https://fifa-2026-dashboard-80399171028.us-central1.run.app/api/schedule
curl -s https://fifa-2026-dashboard-80399171028.us-central1.run.app/api/match/brazil_haiti_2026/summary
curl -s "https://fifa-2026-dashboard-80399171028.us-central1.run.app/api/match/brazil_haiti_2026/metrics?simulation_count=10000&seed=20260618"
```

Then manually smoke-check:

- Overview loads.
- Match Analysis loads at least one current fixture.
- Standings tab loads.
- A proxy visualization either renders or reports a clear credential/source
  failure.

### accionar.xyz

Always verify `accionar.xyz` separately from Cloud Run. Distinguish:

- Cloud Run application state.
- Static asset state under `accionar.xyz/dashboards/fifa-2026/`.
- Portfolio iframe/CSP state.

## 7. Common Pitfalls

- Docs may still contain old Streamlit assumptions. Trust `PROJECT_CHARTER.md`
  first.
- `summary.json` is curated editorial content; generation scripts can overwrite
  it if not made safe.
- Some active fixtures currently have empty `team_metrics`.
- Some active forecasts currently use default `40/30/30` fallback outputs.
- Do not create new team-name alias maps; use `data/reference/team_identity.json`
  and the shared helpers.
- Active FastAPI Monte Carlo projections are seeded random-trial simulations.
  Legacy Streamlit/reference code may still contain older deterministic helpers.
- BigQuery visualizations need credentials and use historical proxy matches.
- Historical decisions, handoffs, and old STATUS entries can contain superseded
  implementation descriptions. Current routing starts with `TASKS.md`,
  `STATUS.md`, `docs/phase_plan.md`, and `docs/documentation_clutter_audit.md`.
- The project should move toward source-backed AI research under the approved
  T-035 source policy.

## 8. Documentation Update Rule

For any change that affects architecture, schema, model interpretation, data
source provenance, deployment, or agent responsibility:

1. Update `TASKS.md`.
2. Update `STATUS.md`.
3. Update `docs/phase_plan.md` if phase scope or ownership changes.
4. Add a decision in `docs/decisions/` when the change is durable.
5. Add a handoff in `docs/handoffs/` when a phase boundary or specialist
   deliverable completes.
